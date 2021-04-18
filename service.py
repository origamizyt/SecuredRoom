import logging, time, sys
from typing import Any, Callable, Optional, Dict

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

def wait_forever() -> None:
    'Blocks the thread until interruption.'
    try:
        while True: time.sleep(0xFFFF)
    except KeyboardInterrupt: pass

class ArgumentMap(Dict[str, str]):
    'An argument mapping.'
    def choices(self, *choices: str, default: Optional[str]=None) -> Optional[str]:
        'Acts like "get" but accepts multiple keys.'
        for choice in choices:
            value = self.get(choice)
            if value is not None:
                return value
        return default
    def anyIn(self, *keys: str) -> bool:
        'Tests whether any of the keys provided is in the map.'
        return any(k in self for k in keys)

def parse_args() -> ArgumentMap:
    'Parses the command line arguments.'
    value = {}
    last = ''
    nextis = False
    for item in sys.argv:
        if nextis:
            if item.startswith('-'):
                value[last] = ''
                last = item.lstrip('-')
            else:
                value[last] = item
                nextis = False
        else:
            if item.startswith('-'):
                last = item.lstrip('-')
                nextis = True
    if nextis:
        value[last] = ''
    return ArgumentMap(value)

def format_config(c: dict) -> str:
    'Formats the configuration into a string.'
    return ', '.join('{}={}'.format(k, v) for k, v in c.items())