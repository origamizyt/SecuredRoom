import logging
from typing import Any, Callable

class Signal:
    'Represents a signal with callbacks.'
    def __init__(self):
        'Initializes a new instance.'
        self._callbacks = set()
    def __call__(self, *args: Any) -> None:
        'Calls the callbacks with specific argument.'
        for callback in self._callbacks:
            callback(*args)
    def register(self, callback: Callable[..., None]) -> None:
        'Adds a callback.'
        self._callbacks.add(callback)
    def deregister(self, callback: Callable[..., None]) -> None:
        'Removes a callback.'
        self._callbacks.remove(callback)

def log_init() -> None:
    'Initializes the logging services.'
    logging.basicConfig(level=logging.DEBUG, format='[%(threadName)s:%(levelname)s] %(message)s')

def log(text: str) -> None:
    'Logs the text to standard output.'
    logging.info(text)

def hexdump(h: str) -> str:
    'Dumps the hex value.'
    parts = [h[i:i+2] for i in range(0, len(h), 2)]
    value = ''
    count = 0
    while parts:
        value += '{}: '.format(str(count*8).zfill(4))
        count += 1
        value += ' '.join(parts[:8])
        parts = parts[8:]
        if parts: value += '\n'
    return value