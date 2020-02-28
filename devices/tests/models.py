from unittest import mock

from django.test import TestCase, override_settings
from ..models import PLC


class DummyReader:
    pass


class PLCModelTest(TestCase):
    def test_str(self):
        plc = PLC(ip="some ip", variable="some var")
        expected = "some ip"
        self.assertEquals(expected, str(plc))

    @override_settings(PLC_READER_CLASS="devices.tests.models.DummyReader")
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
