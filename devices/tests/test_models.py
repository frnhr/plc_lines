from unittest import mock

from django.test import TestCase, override_settings
from model_mommy import mommy

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
