from typing import Optional

from django.contrib import admin

from .models import PLC, Alert


@admin.register(PLC)
class PLCAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_online")

    def is_online(self, obj) -> Optional[bool]:
        return obj.is_online

    is_online.boolean = True


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "plc", "online")
    list_filter = ("timestamp", "online")
    search_fields = ("plc__ip",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
