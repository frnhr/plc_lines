from __future__ import annotations

import json
from typing import Optional

from django.conf import settings
from pylogix.eip import Response, PLC


class ReaderError(RuntimeError):
    """Failed to read PLC device."""


SUCCESS_STATUSES = ("Success", "Partial transfer")


class ReaderBase:
    def __init__(self, ip, variable) -> None:
        self.ip = ip
        self.variable = variable

    def read(self) -> Optional[str]:
        try:
            response = self._read()
        except NotImplementedError:
            raise
        except Exception as e:
            raise ReaderError() from e
        if response.Status not in SUCCESS_STATUSES:
            raise ReaderError(response.Status)
        # TODO Do we need to continue reading if get 0x06 Partial transfer?
        return str(response.Value) if response is not None else None

    def _read(self) -> Response:
        raise NotImplementedError()


class FakeReader(ReaderBase):
    """
    This is a dummy PLC reader, used for development (since the developer
    has zero experience with PLCs, let alone having one handy for tinkering).

    Edit FAKE_PLC.json file to change the value which is read.
    """
    def _read(self) -> Response:
        with open(settings.FAKE_READER_FILE) as fake_reader_file:
            fake_plcs = json.loads(fake_reader_file.read())
            response_kwargs = fake_plcs[self.ip]
        return Response(**response_kwargs)


class PLCReader(ReaderBase):
    """Real PLC reader."""
    def _read(self) -> Response:
        with PLC() as comm:
            comm.Micro800 = True
            comm.IPAddress = self.ip
            return comm.Read(self.variable)
