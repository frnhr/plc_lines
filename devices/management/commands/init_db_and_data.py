from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from freezegun import freeze_time

from devices.models import PLC


class Command(BaseCommand):
    help = 'Initialised DB and creates sample data'

    def handle(self, *args, **options):
        try:
            PLC.objects.all().count()
        except (OperationalError, ProgrammingError):
            self.stdout.write("Migrating!")
            self._migrate()
        else:
            self.stdout.write("Not migrating!")

        users_count = User.objects.all().count()
        if users_count:
            self.stdout.write("Not creating admin user.")
        else:
            self.stdout.write("Creating admin user.")
            self._create_admin_user()

        plcs_count = PLC.objects.all().count()
        if plcs_count:
            self.stdout.write("Not creating initial data.")
        else:
            self.stdout.write("Creating initial data.")
            self._create_plc_data()

        periodic_tasks = PeriodicTask.objects.all().count()
        if periodic_tasks:
            self.stdout.write("Not configuring Celery task.")
        else:
            self.stdout.write("Configuring Celery task.")
            self._create_celery_data()

    @staticmethod
    def _migrate():
        execute_from_command_line(["manage.py",  "migrate", "--noinput"])

    @staticmethod
    def _create_admin_user():
        execute_from_command_line([
            "manage.py",
            "createsuperuser",
            "--username",
            "admin",
            "--email",
            "admin@example.com",
            "--noinput",
        ])
        admin = User.objects.all().first()
        admin.set_password("admin")
        admin.save()

    @staticmethod
    def _create_plc_data():
        plc1 = PLC.objects.create(
            ip="10.0.0.11",
            variable="MyVar",
            expected_value="42",
        )
        plc2 = PLC.objects.create(
            ip="10.0.0.22",
            variable="MyVar",
            expected_value="42",
        )
        plc3 = PLC.objects.create(
            ip="10.0.0.33",
            variable="MyVar",
            expected_value="42",
        )
        now = timezone.now()
        days_ago_3_noon = (now - timedelta(days=3)).replace(
            hour=12, minute=0, second=0, microsecond=0)
        days_ago_3_afternoon = days_ago_3_noon.replace(hour=18, minute=30)
        days_ago_3_night = days_ago_3_noon.replace(hour=23, minute=30)

        days_ago_2_afternoon = days_ago_3_afternoon + timedelta(days=1)
        days_ago_2_night = days_ago_3_night + timedelta(days=1)

        days_ago_1_afternoon = days_ago_3_afternoon + timedelta(days=2)
        days_ago_1_night = days_ago_3_night + timedelta(days=2)

        with freeze_time(timedelta(days=-62)):
            plc1.alerts.create(online=1)
            plc2.alerts.create(online=1)
            plc3.alerts.create(online=1)
        with freeze_time(timedelta(days=-4)):
            plc1.alerts.create(online=0)
            plc2.alerts.create(online=0)
            plc3.alerts.create(online=0)

        with freeze_time(days_ago_3_noon):
            plc1.alerts.create(online=1)
            plc2.alerts.create(online=1)
            plc3.alerts.create(online=1)
        with freeze_time(days_ago_3_afternoon):
            plc1.alerts.create(online=0)
        with freeze_time(days_ago_3_night):
            plc1.alerts.create(online=1)

        with freeze_time(days_ago_2_afternoon):
            plc2.alerts.create(online=0)
        with freeze_time(days_ago_2_night):
            plc2.alerts.create(online=1)

        with freeze_time(days_ago_1_afternoon):
            plc3.alerts.create(online=0)
            plc1.alerts.create(online=0)
        with freeze_time(days_ago_1_night):
            plc3.alerts.create(online=1)

    @staticmethod
    def _create_celery_data():
        # TODO Ouch! This breaks parent interface! Liskov, anyone?
        interval, _ = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.SECONDS,
        )
        PeriodicTask.objects.create(
            name="Ping all PLCs",
            task="devices.tasks.fanout_read_all_plcs",
            interval=interval,
        )
