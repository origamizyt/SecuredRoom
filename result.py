from enum import IntEnum
from typing import Any
import msgpack

class StatusCode(IntEnum):
    'The status code returned by the server.'
    SC_OK = 0
    SC_NEW_MESSAGE = 1
    SC_KEY_INVALID = 2
    SC_INVALID_CMD = 3
    SC_NEEDS_LOGIN = 4
    SC_WANDER_ROOM = 5
    SC_DUPLICATE_USER = 6
    SC_UNAUTHORIZED = 7
    SC_TOO_FREQUENT = 8

class Status:
    'The status returned by server.'
    def __init__(self, code: StatusCode, data: Any=None):
        'Initializes an instance with specific code and data.'
        self._code = code
        self._data = data
    @property
    def code(self) -> StatusCode:
        'The code of the status.'
        return self._code
    @property
    def data(self) -> Any:
        'The data of the status.'
        return self._data
    @staticmethod
    def ok(data: Any=None) -> 'Status':
        'Shortcut for status code SC_OK.'
        return Status(StatusCode.SC_OK, data)
    @staticmethod
    def message(data: Any=None) -> 'Status':
        'Shortcut for status code SC_NEW_MESSAGE.'
        return Status(StatusCode.SC_NEW_MESSAGE, data)
    def pack(self) -> bytes:
        'Packs this status to bytes.'
        return msgpack.packb({
            'code': self._code.value,
            'data': self._data
        })
    @staticmethod
    def unpack(data: bytes) -> 'Status':
        'Unpacks an instance from bytes.'
        data = msgpack.unpackb(data)
        code = StatusCode(data['code'])
        return Status(code, data['data'])
    @property
    def success(self) -> bool:
        'Whether this status is a successful one.'
        return self._code in [StatusCode.SC_OK, StatusCode.SC_NEW_MESSAGE]