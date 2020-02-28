from django.db import models


class PLC(models.Model):
    ip = models.GenericIPAddressField(null=False, blank=False)
    variable = models.CharField(max_length=100, null=False, blank=False)
    expected_value = models.CharField(
        max_length=100, null=False, blank=True, default="")

    class Meta:
        verbose_name = "PLC"

    def __str__(self) -> str:
        return self.ip

    def read(self):
        raise NotImplementedError()
