"""Routes each operation to the fastest backend that can do it.

Observation: UI tree from uiautomator2, frames from emulator gRPC.
Touch: emulator gRPC when reachable, otherwise uiautomator2.
Everything else (text entry, keys, app management, selectors): uiautomator2.
"""
from __future__ import annotations

import io
import logging
import re
import time
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageStat

from droidpilot import uitree
from droidpilot.device import Device
from droidpilot.emulator import Emulator

log = logging.getLogger(__name__)

_RESUMED = re.compile(r"ActivityRecord\{\S+ \S+ ([\w.]+)/([\w.$]+)")
_THUMB_WIDTH = 108
# Mean absolute grey-level difference (0-255) above which two thumbnails count as
# different; a blinking text cursor stays well below it, a tap ripple does not.
_FRAME_DIFF_THRESHOLD = 0.4
# Friendly names for `input keyevent`; anything else is tried as KEYCODE_<NAME> or a number.
_KEYS = {
    "home": 3, "back": 4, "call": 5, "endcall": 6, "up": 19, "down": 20, "left": 21, "right": 22,
    "center": 23, "volume_up": 24, "volume_down": 25, "power": 26, "camera": 27, "tab": 61,
    "space": 62, "enter": 66, "delete": 67, "backspace": 67, "menu": 82, "search": 84,
    "escape": 111, "forward_delete": 112, "recent": 187, "recents": 187, "app_switch": 187,
}


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

    def _dump(self) -> str:
        return self.device.call(lambda d: d.dump_hierarchy(compressed=True))

    def observe(self, xml: str | None = None) -> uitree.Snapshot:
        self._last_xml = xml or self._dump()
        self.snapshot = uitree.parse(self._last_xml, self.screen)
        return self.snapshot

    def _thumb(self) -> Image.Image | None:
        """Tiny greyscale frame for change detection (~8 ms over gRPC); None without gRPC."""
        if not self.emu:
            return None
        return self.emu.screenshot(_THUMB_WIDTH).convert("L")

    @staticmethod
    def _frames_differ(a: Image.Image | None, b: Image.Image | None) -> bool:
        if a is None or b is None or a.size != b.size:
            return False
        return ImageStat.Stat(ImageChops.difference(a, b)).mean[0] > _FRAME_DIFF_THRESHOLD

    def mark(self) -> None:
        """Record the pre-action state that `settle` compares against (a frame with gRPC, else the tree)."""
        frame = self._thumb()
        self._before = (None if frame is not None else self._dump(), frame)

    def settle(self, max_wait_ms: int = 3000, quiet_ms: int = 400, stable_ms: int = 250,
               poll_ms: int = 30) -> uitree.Snapshot:
        """Wait for the screen to react to the last action and stop changing, then observe.

        With gRPC this polls tiny frames (~2 ms each) and reads the UI tree once at
        the end: dumping the tree blocks while the app animates (0.5 s per dump
        during a transition), so polling it would both slow us down and blur the
        timing. Without gRPC it falls back to polling the tree.

        Returns once the screen differs from the state recorded by `mark` and has
        then been unchanged for `stable_ms` (long enough to ride out the brief
        pause while a recreated screen reloads its content), or, if nothing changes
        within `quiet_ms`, assumes the action had no visible effect. Gives up after
        `max_wait_ms` (spinners, video, carousels never settle).
        """
        (before_xml, before_frame), self._before = getattr(self, "_before", (None, None)), (None, None)
        use_frames = before_frame is not None
        start = time.monotonic()
        last, still_since, changed = None, None, False
        while True:
            if use_frames:
                cur = self._thumb()
                changed = changed or self._frames_differ(cur, before_frame)
                same = last is not None and not self._frames_differ(cur, last)
            else:
                cur = self._dump()
                changed = changed or cur != before_xml
                same = cur == last
            now = time.monotonic()
            still_since = (still_since or now) if same else None
            elapsed = (now - start) * 1000
            if still_since and (now - still_since) * 1000 >= stable_ms and (changed or elapsed >= quiet_ms):
                break
            if elapsed >= max_wait_ms:
                break
            last = cur
            time.sleep(poll_ms / 1000)
        self.last_settle_ms = round((time.monotonic() - start) * 1000)
        return self.observe(None if use_frames else cur)

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

    def find_text(self, text: str, exact: bool = False) -> uitree.Element | None:
        """Best element in a fresh snapshot whose label matches `text` (case-insensitive)."""
        needle = text.casefold()
        best, best_rank = None, None
        for el in self.observe().elements.values():
            label = el.text.casefold()
            if label == needle:
                match = 0
            elif not exact and needle in label:
                match = 1
            else:
                continue
            # Prefer exact matches, tappable elements, things not hidden by the keyboard, then smaller targets.
            rank = (match, "click" not in el.flags, "under-keyboard" in el.flags,
                    (el.bounds[2] - el.bounds[0]) * (el.bounds[3] - el.bounds[1]))
            if best_rank is None or rank < best_rank:
                best, best_rank = el, rank
        return best

    def tap_text(self, text: str, exact: bool = False, timeout: float = 3) -> bool:
        deadline = time.monotonic() + timeout
        while (el := self.find_text(text, exact)) is None:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)
        self.tap(el.handle)
        return True

    def type_text(self, text: str, clear: bool = False) -> None:
        """Set the focused field's text via the accessibility API.

        Unlike uiautomator2's send_keys this touches neither the clipboard (which
        pops the system clipboard overlay on Android 13+) nor the user's input
        method, works for any Unicode text, and still fires the app's text watchers.
        """
        root = ET.fromstring(self._dump())
        field = next((n for n in root.iter("node") if n.get("focused") == "true"
                      and n.get("class", "").endswith(("EditText", "AutoCompleteTextView"))), None)
        if field is None:
            raise TargetError("no focused text field; tap the field first")
        current = field.get("text", "")
        if clear or current == field.get("hint"):
            current = ""
        self.pacer.wait()
        self.device.call(lambda d: d(focused=True).set_text(current + text))

    def press(self, key: str) -> None:
        # uiautomator2's press() waits for the UI to idle and takes 0.1-1 s;
        # a raw keyevent returns in ~50 ms and settle() does the waiting.
        name = key.strip().lower()
        code = _KEYS.get(name) or (name if name.isdigit() else "KEYCODE_" + name.upper())
        self.pacer.wait()
        self.device.call(lambda d: d.shell(["input", "keyevent", str(code)]))

    def wait_for(self, text: str | None = None, resource_id: str | None = None,
                 timeout: float = 5) -> bool:
        """Poll until an element whose label contains `text` and/or whose resource id is `resource_id` appears.

        Leaves the matching snapshot in self.snapshot, so its handles are usable.
        """
        if not (text or resource_id):
            raise TargetError("give text or resource_id")
        needle = text.casefold() if text else None
        rid = resource_id.split(":id/", 1)[-1] if resource_id else None
        deadline = time.monotonic() + timeout
        while True:
            for el in self.observe().elements.values():
                if (needle is None or needle in el.text.casefold()) and (rid is None or el.resource_id == rid):
                    return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)

    def app_launch(self, package: str) -> None:
        self.pacer.wait()
        # wait=True polls d.app_current(), which is slow; callers settle on the UI tree instead.
        self.device.call(lambda d: d.app_start(package, wait=False))

    def app_stop(self, package: str) -> None:
        self.device.call(lambda d: d.app_stop(package))

    def app_current(self) -> dict:
        # uiautomator2's app_current() takes ~5 s on recent images; dumpsys takes ~35 ms.
        out = self.device.call(lambda d: d.shell(
            "dumpsys activity activities | grep -m1 -E 'topResumedActivity|mResumedActivity'").output)
        m = _RESUMED.search(out)
        if not m:
            return {"package": None, "activity": None, "raw": out.strip()}
        package, activity = m.groups()
        if activity.startswith("."):
            activity = package + activity
        return {"package": package, "activity": activity}

    def app_list(self, contains: str = "") -> list[str]:
        pkgs = self.device.call(lambda d: d.app_list())
        return sorted(p for p in pkgs if contains.lower() in p.lower())
