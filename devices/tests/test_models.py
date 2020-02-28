from unittest import mock

from django.test import TestCase, override_settings
from model_mommy import mommy

from ..models import PLC, Alert


class DummyReader:
    pass


class PLCModelTest(TestCase):
    def test_str(self):
        plc = PLC(ip="some ip", variable="some var")
        expected = "some ip"
        self.assertEquals(expected, str(plc))

    @override_settings(PLC_READER_CLASS="devices.tests.test_models.DummyReader")
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
