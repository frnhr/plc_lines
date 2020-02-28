from __future__ import annotations

import logging
from typing import Optional, Type

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

from devices.readers import ReaderBase, ReaderError


logger = logging.getLogger(__name__)


class PLC(models.Model):
    ip = models.GenericIPAddressField(null=False, blank=False)
    variable = models.CharField(max_length=100, null=False, blank=False)
    expected_value = models.CharField(
        max_length=100, null=False, blank=True, default="")

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


class Alert(models.Model):
    """
    An alert os created whenever a PLC changes state.
    """
    plc = models.ForeignKey(
        PLC, models.CASCADE, related_name="alerts", null=True, editable=False)
    online = models.BooleanField(null=False, editable=False)
    timestamp = models.DateTimeField(
        null=False, auto_now_add=True, editable=False, db_index=True)

    class Meta:
        ordering = ("timestamp", "plc")

    def __str__(self) -> str:
        return f"{self.timestamp} {self.plc} {'UP' if self.online else 'DOWN'}"
