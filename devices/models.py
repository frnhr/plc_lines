from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, time
from typing import Optional, Type, Dict, Iterator, Tuple, Iterable

import pytz
from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from devices.readers import ReaderBase, ReaderError


logger = logging.getLogger(__name__)

SECONDS_IN_DAY = 24 * 60 * 60


class PLC(models.Model):
    ip = models.GenericIPAddressField(null=False, blank=False)
    variable = models.CharField(max_length=100, null=False, blank=False)
    expected_value = models.CharField(
        max_length=100, null=False, blank=True, default=""
    )

    class Meta:
        verbose_name = "PLC"

    def __str__(self) -> str:
        return self.ip

    @staticmethod
    def get_reader_class() -> Type[ReaderBase]:
        class_path = settings.PLC_READER_CLASS
        return import_string(class_path)

    def read(self) -> Optional[str]:
        reader_class = self.get_reader_class()
        reader = reader_class(self.ip, self.variable)
        try:
            return reader.read()
        except ReaderError:
            return None

    @property
    def is_online(self) -> Optional[bool]:
        last_alert = self.alerts.last()
        return last_alert.online if last_alert else None

    def process_status(self, online: bool) -> None:
        """Create new Alert instance if needed."""
        logger.debug(f"{self=}, {online=}")
        if online != self.is_online:
            logger.warning(f"Changing {self} to {online=}")
            self.alerts.create(online=online)

    def get_uptimes(
            self, date_min: date, date_max: date
    ) -> Iterator[Tuple[date, float]]:
        tzinfo = pytz.timezone(settings.TIME_ZONE)
        datetime_min = datetime.combine(
            date_min, time(0, 0, 0), tzinfo=tzinfo)
        datetime_max = datetime.combine(
            date_max + timedelta(days=1),
            time(0, 0, 0),
            tzinfo=tzinfo,
        )
        alerts = list(self.alerts.filter(
            timestamp__gte=datetime_min, timestamp__lt=datetime_max))
        previous_alert = self.alerts.filter(timestamp__lt=datetime_min).last()
        last_online = previous_alert.online if previous_alert else False
        day = date_min
        while day <= date_max:
            start_of_next_day = datetime.combine(
                day + timedelta(days=1), time(0, 0, 0), tzinfo=tzinfo)
            uptime_fraction = float(last_online)  # bools are ints :)
            while alerts and alerts[0].timestamp < start_of_next_day:
                alert = alerts.pop(0)
                remaining_slice_of_day = start_of_next_day - alert.timestamp
                remaining_fraction_of_day = (
                    remaining_slice_of_day.total_seconds() / SECONDS_IN_DAY)
                if alert.online != last_online:
                    if alert.online:
                        uptime_fraction += remaining_fraction_of_day
                    else:
                        uptime_fraction -= remaining_fraction_of_day
                last_online = alert.online
            yield day, round(uptime_fraction, 4)
            day += timedelta(days=1)

    @classmethod
    def get_multiple_uptimes(
            cls, plc_ids: Iterable[int], date_min: date, date_max: date):
        plcs = cls.objects.all()

        return {
            plc.id: (
                dict(plc.get_uptimes(date_min, date_max))
                if plc.id in plc_ids else {}
            )
            for plc in plcs
        }


class Alert(models.Model):
    """
    An alert os created whenever a PLC changes state.
    """

    plc = models.ForeignKey(
        PLC, models.CASCADE, related_name="alerts", null=True, editable=False
    )
    online = models.BooleanField(null=False, editable=False)
    timestamp = models.DateTimeField(
        null=False, auto_now_add=True, editable=False, db_index=True
    )

    class Meta:
        ordering = ("timestamp", "plc")

    def __str__(self) -> str:
        return f"{self.timestamp} {self.plc} {'UP' if self.online else 'DOWN'}"
