from datetime import datetime, time, timedelta
from unittest import mock

from django.test import TestCase, override_settings
from freezegun import freeze_time
from model_mommy import mommy
from pytz import UTC

from ..models import PLC, Alert
from ..readers import ReaderError


class DummyReader:
    pass


class PLCModelTest(TestCase):
    def test_str(self):
        plc = PLC(ip="some ip", variable="some var")
        expected = "some ip"
        self.assertEquals(expected, str(plc))

    @override_settings(
        PLC_READER_CLASS="devices.tests.test_models.DummyReader")
    def test_get_reader_class(self):
        reader_class = PLC.get_reader_class()
        self.assertTrue(issubclass(reader_class, DummyReader))
        # note: every class is a subclass of itself

    @mock.patch("devices.models.PLC.get_reader_class")
    def test_read(self, p_get_reader_class):
        mock_reader_class = p_get_reader_class.return_value
        mock_reader = mock_reader_class.return_value
        mock_read_value = mock_reader.read.return_value

        plc = PLC(ip="some ip", variable="some var")
        value = plc.read()

        mock_reader_class.assert_called_once_with("some ip", "some var")
        expected = mock_read_value
        self.assertEquals(expected, value)

    @mock.patch("devices.models.PLC.get_reader_class")
    def test_read_fails_as_none(self, p_get_reader_class):
        mock_reader_class = p_get_reader_class.return_value
        mock_reader = mock_reader_class.return_value
        mock_reader.read.side_effect = ReaderError

        plc = PLC(ip="some ip", variable="some var")
        value = plc.read()

        mock_reader_class.assert_called_once_with("some ip", "some var")
        self.assertIsNone(value)

    def test_online_true(self):
        plc = mommy.make(PLC)
        mommy.make(Alert, plc=plc, online=True)
        self.assertTrue(plc.is_online)

    def test_online_false(self):
        plc = mommy.make(PLC)
        mommy.make(Alert, plc=plc, online=False)
        self.assertFalse(plc.is_online)

    def test_online_none(self):
        plc = mommy.make(PLC)
        self.assertIsNone(plc.is_online)

    def test_process_status_first_true(self):
        plc = mommy.make(PLC)
        plc.process_status(True)
        self.assertEquals(1, plc.alerts.all().count())
        self.assertTrue(plc.alerts.all().last().online)

    def test_process_status_first_false(self):
        plc = mommy.make(PLC)
        plc.process_status(False)
        self.assertEquals(1, plc.alerts.all().count())
        self.assertFalse(plc.alerts.all().last().online)

    def test_process_status_needed_false(self):
        plc = mommy.make(PLC)
        mommy.make(Alert, plc=plc, online=True)
        plc.process_status(False)
        self.assertEquals(2, plc.alerts.all().count())
        self.assertFalse(plc.alerts.all().last().online)

    def test_process_status_needed_true(self):
        plc = mommy.make(PLC)
        mommy.make(Alert, plc=plc, online=False)
        plc.process_status(True)
        self.assertEquals(2, plc.alerts.all().count())
        self.assertTrue(plc.alerts.all().last().online)

    def test_process_status_not_needed_false(self):
        plc = mommy.make(PLC)
        mommy.make(Alert, plc=plc, online=False)
        plc.process_status(False)
        self.assertEquals(1, plc.alerts.all().count())
        self.assertFalse(plc.alerts.all().last().online)

    def test_process_status_not_needed_true(self):
        plc = mommy.make(PLC)
        mommy.make(Alert, plc=plc, online=True)
        plc.process_status(True)
        self.assertEquals(1, plc.alerts.all().count())
        self.assertTrue(plc.alerts.all().last().online)


class AlertTest(TestCase):
    def setUp(self) -> None:
        self.plc = mommy.make(PLC, ip="myip")

    def test_str_up(self):
        alert = mommy.make(Alert, plc=self.plc, online=True)
        value = str(alert)
        self.assertIn("UP", value)
        self.assertIn("myip", value)

    def test_str_down(self):
        alert = mommy.make(Alert, plc=self.plc, online=False)
        value = str(alert)
        self.assertIn("DOWN", value)
        self.assertIn("myip", value)


class UptimeTest(TestCase):
    def test_multiple_1(self):
        day = datetime(2011, 12, 13, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        with freeze_time("2011-12-12 12:00"):  # previous alert
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-13 12:00"):  # at 50%
            mommy.make(
                Alert,
                plc=plc,
                online=0,
            )
        with freeze_time("2011-12-13 16:48"):  # at 70%
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-13 21:36"):  # at 90%
            mommy.make(
                Alert,
                plc=plc,
                online=0,
            )
        value = list(plc.get_uptimes(day, day))
        expected = [(day, 0.7)]
        self.assertEquals(expected, value)

    def test_multiple_wo_previous(self):
        day = datetime(2011, 12, 13, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        with freeze_time("2011-12-13 12:00"):  # at 50%
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-13 16:48"):  # at 70%
            mommy.make(
                Alert,
                plc=plc,
                online=0,
            )
        with freeze_time("2011-12-13 21:36"):  # at 90%
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        value = list(plc.get_uptimes(day, day))
        expected = [(day, 0.3)]
        self.assertEquals(expected, value)

    def test_no_alerts(self):
        day = datetime(2011, 12, 13, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        value = list(plc.get_uptimes(day, day))
        expected = [(day, 0.0)]
        self.assertEquals(expected, value)

    def test_only_previous(self):
        day = datetime(2011, 12, 13, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        with freeze_time("2011-12-12 12:00"):  # previous alert
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        value = list(plc.get_uptimes(day, day))
        expected = [(day, 1.0)]
        self.assertEquals(expected, value)

    def test_redundant_alerts(self):
        day = datetime(2011, 12, 13, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        with freeze_time("2011-12-12 12:00"):  # previous alert
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-13 12:00"):  # at 50%
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        value = list(plc.get_uptimes(day, day))
        expected = [(day, 1.0)]
        self.assertEquals(expected, value)

    def test_two_days(self):
        day1 = datetime(2011, 12, 13, tzinfo=UTC)
        day2 = datetime(2011, 12, 14, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        with freeze_time("2011-12-12 12:00"):  # previous alert
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-13 12:00"):  # at 50% day 1
            mommy.make(
                Alert,
                plc=plc,
                online=0,
            )
        with freeze_time("2011-12-14 21:36"):  # at 90% day 2
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        value = list(plc.get_uptimes(day1, day2))
        expected = [(day1, 0.5), (day2, 0.1)]
        self.assertEquals(expected, value)

    def test_four_days(self):
        day1 = datetime(2011, 12, 13, tzinfo=UTC)
        day2 = datetime(2011, 12, 14, tzinfo=UTC)
        day3 = datetime(2011, 12, 15, tzinfo=UTC)
        day4 = datetime(2011, 12, 16, tzinfo=UTC)
        plc: PLC = mommy.make(PLC)
        with freeze_time("2011-12-12 12:00"):  # previous alert
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-13 12:00"):  # at 50% day 1
            mommy.make(
                Alert,
                plc=plc,
                online=0,
            )
        with freeze_time("2011-12-14 21:36"):  # at 90% day 2
            mommy.make(
                Alert,
                plc=plc,
                online=1,
            )
        with freeze_time("2011-12-16 16:48"):  # at 70% day 4
            mommy.make(
                Alert,
                plc=plc,
                online=0,
            )
        value = list(plc.get_uptimes(day1, day4))
        expected = [(day1, 0.5), (day2, 0.1), (day3, 1.0), (day4, 0.7)]
        self.assertEquals(expected, value)
