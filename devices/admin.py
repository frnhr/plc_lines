from django.contrib import admin

from .models import PLC


@admin.register(PLC)
class PLCAdmin(admin.ModelAdmin):
    pass
