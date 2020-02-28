from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Type

from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from devices.readers import ReaderBase


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

    def read(self) -> str:
        reader_class = self.get_reader_class()
        reader = reader_class(self.ip, self.variable)
        return reader.read()

    @property
    def is_online(self) -> Optional[bool]:
        last_alert = self.alerts.last()
        return last_alert.online if last_alert else None


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
