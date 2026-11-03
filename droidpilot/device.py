"""uiautomator2 connection that heals itself."""
from __future__ import annotations

import logging
import threading

import uiautomator2 as u2

log = logging.getLogger(__name__)


class Device:
    """Lazily connects to the device and reconnects once if a call fails.

    The uiautomator2 on-device server occasionally dies (app crash, OOM, a
    second automation client); restarting it is cheaper than surfacing the
    error to the agent.
    """

    def __init__(self, serial: str | None = None):
        self.serial = serial
        self._d: u2.Device | None = None
        self._lock = threading.Lock()

    def _connect(self) -> u2.Device:
        d = u2.connect(self.serial)
        d.info  # fails fast if the on-device server can't start
        return d

    @property
    def u2(self) -> u2.Device:
        with self._lock:
            if self._d is None:
                self._d = self._connect()
            return self._d

    def reset(self) -> None:
        with self._lock:
            if self._d is not None:
                try:
                    self._d.stop_uiautomator()
                except Exception:  # already dead is fine
                    pass
            self._d = None

    def call(self, fn):
        """Run fn(u2_device); on failure restart the on-device server and retry once."""
        try:
            return fn(self.u2)
        except Exception as e:
            log.warning("uiautomator2 call failed (%s); reconnecting", e)
            self.reset()
            return fn(self.u2)
