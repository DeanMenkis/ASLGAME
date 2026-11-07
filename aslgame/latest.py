"""A thread-safe slot that holds only the newest value."""

import threading


class Latest:
    def __init__(self):
        self._condition = threading.Condition()
        self._value = None
        self._version = 0

    def publish(self, value):
        with self._condition:
            self._value = value
            self._version += 1
            self._condition.notify_all()

    def get(self):
        """Return (version, value) without waiting."""
        with self._condition:
            return self._version, self._value

    def wait_newer(self, version, timeout_s):
        """Wait until a value newer than version arrives, or timeout. Return (version, value)."""
        with self._condition:
            self._condition.wait_for(lambda: self._version > version, timeout_s)
            return self._version, self._value
