"""Routes each operation to the fastest backend that can do it.

Observation: UI tree from uiautomator2, frames from emulator gRPC.
Touch: emulator gRPC when reachable, otherwise uiautomator2.
Everything else (text entry, keys, app management, selectors): uiautomator2.
"""
from __future__ import annotations

import io
import logging
import time

from PIL import Image

from droidpilot import uitree
from droidpilot.device import Device
from droidpilot.emulator import Emulator

log = logging.getLogger(__name__)


class TargetError(ValueError):
    pass


class Pacer:
    """Enforces a minimum gap between consecutive actions.

    Keeps an agent from acting faster than apps can render, which otherwise
    shows up as taps landing on half-drawn screens.
    """

    def __init__(self, min_interval_ms: int):
        self.min_interval = min_interval_ms / 1000
        self._last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self._last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last = time.monotonic()


class Controller:
    def __init__(self, serial: str | None = None, grpc_address: str | None = "127.0.0.1:8554",
                 min_interval_ms: int = 300):
        self.device = Device(serial)
        self._emu = Emulator(grpc_address) if grpc_address else None
        self._emu_checked = False
        self.pacer = Pacer(min_interval_ms)
        self.snapshot: uitree.Snapshot | None = None
        self._screen: tuple[int, int] | None = None

    # -- backends ---------------------------------------------------------

    @property
    def emu(self) -> Emulator | None:
        if self._emu is not None and not self._emu_checked:
            self._emu_checked = True
            if not self._emu.available():
                log.warning("emulator gRPC at %s unreachable; using uiautomator2 only", self._emu.address)
                self._emu = None
        return self._emu

    @property
    def screen(self) -> tuple[int, int]:
        if self._screen is None:
            self._screen = self.device.call(lambda d: d.window_size())
        return self._screen

    def backends(self) -> dict:
        return {
            "uiautomator2": self.device.serial or "auto",
            "emulator_grpc": self.emu.address if self.emu else None,
            "screen": self.screen,
            "min_interval_ms": round(self.pacer.min_interval * 1000),
        }

    # -- observation ------------------------------------------------------

    def observe(self) -> uitree.Snapshot:
        xml = self.device.call(lambda d: d.dump_hierarchy(compressed=True))
        self.snapshot = uitree.parse(xml, self.screen)
        return self.snapshot

    def screenshot(self, width: int = 540, quality: int = 70) -> bytes:
        if self.emu:
            frame = self.emu.screenshot(width)
        else:
            frame = self.device.call(lambda d: d.screenshot())
            w, h = frame.size
            if width and width < w:
                frame = frame.resize((width, round(h * width / w)), Image.BILINEAR)
        buf = io.BytesIO()
        frame.convert("RGB").save(buf, "JPEG", quality=quality)
        return buf.getvalue()

    def resolve(self, target: str) -> tuple[int, int]:
        """Accepts an element handle from the latest observe ("e7") or "x,y" in device pixels."""
        target = target.strip()
        if "," in target:
            try:
                x, y = (int(float(v)) for v in target.split(","))
            except ValueError:
                raise TargetError(f"bad coordinates {target!r}; expected 'x,y'") from None
            return x, y
        if self.snapshot is None:
            raise TargetError("no snapshot yet; call observe first")
        el = self.snapshot.elements.get(target)
        if el is None:
            raise TargetError(f"unknown handle {target!r}; handles come from the latest observe")
        return el.center

    def element_bounds(self, target: str) -> tuple[int, int, int, int] | None:
        if self.snapshot and (el := self.snapshot.elements.get(target.strip())):
            return el.bounds
        return None

    # -- touch ------------------------------------------------------------

    def tap(self, target: str) -> None:
        x, y = self.resolve(target)
        self.pacer.wait()
        if self.emu:
            self.emu.tap(x, y)
        else:
            self.device.call(lambda d: d.click(x, y))

    def long_press(self, target: str, hold_ms: int = 800) -> None:
        x, y = self.resolve(target)
        self.pacer.wait()
        if self.emu:
            self.emu.long_press(x, y, hold_ms)
        else:
            self.device.call(lambda d: d.long_click(x, y, hold_ms / 1000))

    def swipe(self, start: str, end: str, duration_ms: int = 300, hold_ms: int = 0) -> None:
        (x1, y1), (x2, y2) = self.resolve(start), self.resolve(end)
        self.pacer.wait()
        if self.emu:
            self.emu.swipe(x1, y1, x2, y2, duration_ms, hold_ms)
        elif hold_ms:
            self.device.call(lambda d: d.drag(x1, y1, x2, y2, (hold_ms + duration_ms) / 1000))
        else:
            self.device.call(lambda d: d.swipe(x1, y1, x2, y2, duration_ms / 1000))

    def scroll(self, direction: str, target: str | None = None, distance: float = 0.6,
               duration_ms: int = 300) -> None:
        """Scroll content; direction is where the content moves into view ("down" reveals what's below)."""
        w, h = self.screen
        x1, y1, x2, y2 = (self.element_bounds(target) if target else None) or (0, 0, w, h)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        half_w, half_h = (x2 - x1) * distance / 2, (y2 - y1) * distance / 2
        vectors = {
            "down": (cx, cy + half_h, cx, cy - half_h),
            "up": (cx, cy - half_h, cx, cy + half_h),
            "right": (cx + half_w, cy, cx - half_w, cy),
            "left": (cx - half_w, cy, cx + half_w, cy),
        }
        if direction not in vectors:
            raise TargetError(f"direction must be one of {sorted(vectors)}")
        sx, sy, ex, ey = (int(v) for v in vectors[direction])
        self.swipe(f"{sx},{sy}", f"{ex},{ey}", duration_ms)

    def pinch(self, zoom: str, target: str | None = None, duration_ms: int = 400) -> None:
        if not self.emu:
            raise TargetError("pinch needs the emulator gRPC endpoint (start the emulator with -grpc)")
        w, h = self.screen
        cx, cy = self.resolve(target) if target else (w // 2, h // 2)
        near, far = w // 8, w // 2
        start, end = (near, far) if zoom == "in" else (far, near)
        self.pacer.wait()
        self.emu.pinch(cx, cy, start, end, duration_ms)

    # -- uiautomator2-only operations -------------------------------------

    def tap_text(self, text: str, exact: bool = False, timeout: float = 3) -> bool:
        self.pacer.wait()
        sel = {"text": text} if exact else {"textContains": text}

        def click(d):
            obj = d(**sel)
            if not obj.wait(timeout=timeout):
                obj = d(**({"description": text} if exact else {"descriptionContains": text}))
                if not obj.exists:
                    return False
            obj.click()
            return True

        return self.device.call(click)

    def type_text(self, text: str, clear: bool = False) -> None:
        self.pacer.wait()
        self.device.call(lambda d: d.send_keys(text, clear=clear))

    def press(self, key: str) -> None:
        self.pacer.wait()
        self.device.call(lambda d: d.press(key))

    def wait_for(self, text: str | None = None, resource_id: str | None = None,
                 description: str | None = None, timeout: float = 5) -> bool:
        sel = {}
        if text:
            sel["textContains"] = text
        if resource_id:
            sel["resourceIdMatches"] = f".*{resource_id}$"
        if description:
            sel["descriptionContains"] = description
        if not sel:
            raise TargetError("give text, resource_id or description")
        return self.device.call(lambda d: d(**sel).wait(timeout=timeout))

    def app_launch(self, package: str) -> None:
        self.pacer.wait()
        self.device.call(lambda d: d.app_start(package, wait=True))

    def app_stop(self, package: str) -> None:
        self.device.call(lambda d: d.app_stop(package))

    def app_current(self) -> dict:
        return self.device.call(lambda d: d.app_current())

    def app_list(self, contains: str = "") -> list[str]:
        pkgs = self.device.call(lambda d: d.app_list())
        return sorted(p for p in pkgs if contains.lower() in p.lower())
