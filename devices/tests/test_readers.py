import json
import os
from unittest import mock
from unittest.mock import MagicMock

from django.conf import settings
from django.test import SimpleTestCase, override_settings

from devices.readers import FakeReader, ReaderError, ReaderBase, PLCReader

FAKE_READER_FILE = os.path.join(settings.BASE_DIR, "FAKE_PLC.test.json")
Undefined = object()


class ReaderBaseTest(SimpleTestCase):
    def test_reader_not_implemented(self):
        reader = ReaderBase("foo", "bar")
        with self.assertRaises(NotImplementedError):
            reader.read()

    def test_attrs(self):
        reader = ReaderBase("foo", "bar")
        self.assertEquals("foo", reader.ip)
        self.assertEquals("bar", reader.variable)


@override_settings(FAKE_READER_FILE=FAKE_READER_FILE)
class FakeReaderTest(SimpleTestCase):

    DEFAULT_RESPONSE_KWARGS = {
        "fake ip": {
            "tag_name": "TestFoo",
            "value": "42 and you",
            "status": 0x00,
        },
    }

    def setUp(self) -> None:
        super().setUp()
        self.response_kwargs = self.DEFAULT_RESPONSE_KWARGS.copy()
        self.update_response_kwargs()

    def update_response_kwargs(self, ip_kwargs=None):
        ip_kwargs = ip_kwargs or {}
        for ip, kwargs in ip_kwargs.items():
            if ip not in self.response_kwargs:
                self.response_kwargs[ip] = self.DEFAULT_RESPONSE_KWARGS[
                    "fake ip"
                ].copy()
            for attr in ("tag_name", "value", "status"):
                if attr in kwargs:
                    self.response_kwargs[ip][attr] = kwargs[attr]
        with open(FAKE_READER_FILE, "w") as fake_reader_file:
            print(json.dumps(self.response_kwargs), file=fake_reader_file)

    def tearDown(self) -> None:
        super().tearDown()
        os.unlink(FAKE_READER_FILE)

    def test_default_read(self):
        reader = FakeReader("fake ip", "TestFoo")
        expected = "42 and you"
        actual = reader.read()
        self.assertEquals(expected, actual)

    def test_wrong_ip(self):
        reader = FakeReader("this is not an IP!!", "TestFoo")
        with self.assertRaises(ReaderError):
            reader.read()

    def test_multiple_ips(self):
        self.update_response_kwargs({"another ip": {"value": "another foo"}})
        reader_1 = FakeReader("fake ip", "MyVar")
        reader_2 = FakeReader("another ip", "MyVar")
        value_1 = reader_1.read()
        value_2 = reader_2.read()
        self.assertEquals("42 and you", value_1)
        self.assertEquals("another foo", value_2)


class PLCReaderTest(SimpleTestCase):
    @mock.patch("devices.readers.PLC")
    def test_read_ok(self, p_PLC):
        variable = "MyTestVar"
        ip = "10.11.12.13"
        mock_manager = p_PLC.return_value
        mock_comm = mock_manager.__enter__.return_value
        mock_response = MagicMock(
            TagName="MyTag", Value="42", Status="Success"
        )
        mock_comm.Read.return_value = mock_response

        reader = PLCReader(ip, variable)
        value = reader.read()

        p_PLC.assert_called_once_with()
        mock_comm.Read.assert_called_once_with(variable)
        self.assertEquals("42", value)

    @mock.patch("devices.readers.PLC")
    def test_read_failed(self, p_PLC):
        variable = "MyTestVar"
        ip = "10.11.12.13"
        mock_manager = p_PLC.return_value
        mock_comm = mock_manager.__enter__.return_value
        mock_response = MagicMock(
            TagName="MyTag", Value="42", Status="KABOOOOM!!"
        )
        mock_comm.Read.return_value = mock_response

        reader = PLCReader(ip, variable)
        with self.assertRaises(ReaderError):
            reader.read()

        p_PLC.assert_called_once_with()
        mock_comm.Read.assert_called_once_with(variable)
