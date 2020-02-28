from django.conf import settings
from django.db import models
from django.utils.module_loading import import_string


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
    def get_reader_class():
        class_path = settings.PLC_READER_CLASS
        return import_string(class_path)

    def read(self):
        reader_class = self.get_reader_class()
        reader = reader_class(self.ip, self.variable)
        return reader.read()
