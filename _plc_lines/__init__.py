# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from admin_action_buttons.admin import ActionButtonsMixin

from .celery import app as celery_app

__all__ = ("celery_app",)

from django.contrib import admin

if ActionButtonsMixin not in admin.ModelAdmin.__bases__:
    admin.ModelAdmin.__bases__ = (
        ActionButtonsMixin,
    ) + admin.ModelAdmin.__bases__
