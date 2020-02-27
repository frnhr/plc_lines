from django.db import models


class PLC(models.Model):
    ip = models.GenericIPAddressField(null=False, blank=False)
    variable = models.CharField(max_length=100, null=False, blank=False)
    expected_value = models.CharField(
        max_length=100, null=False, blank=True, default="")

    def __str__(self):
        return self.ip

    def read(self):
        raise NotImplementedError()
