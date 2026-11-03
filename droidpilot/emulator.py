"""Thin client for the Android Emulator gRPC endpoint (start the emulator with `-grpc <port>`).

Used for the two things it does faster than anything running inside the guest:
grabbing frames straight from the emulator's framebuffer, and injecting touch
input (including multi-touch) as virtual touchscreen events.

Both work in the display's natural (unrotated) orientation, while uiautomator
reports coordinates for the current rotation. This class takes and returns
display coordinates and does the conversion using `rotation`.
"""
from __future__ import annotations

import math
import time

import grpc
from PIL import Image

from droidpilot._proto import emulator_controller_pb2 as pb
from droidpilot._proto import emulator_controller_pb2_grpc as pb_grpc

# Pressure must be non-zero while a contact is down; 0 lifts it.
_DOWN_PRESSURE = 1
_FRAME_INTERVAL_S = 1 / 60


def to_natural(x: float, y: float, rotation: int, natural: tuple[int, int]) -> tuple[float, float]:
    """Map a point from display coordinates (what uiautomator reports for the current
    rotation) to the emulator's natural, unrotated coordinates (what gRPC frames and
    touch events use). `rotation` is Android's Surface.ROTATION_* (0-3)."""
    w, h = natural
    rotation %= 4
    if rotation == 1:
        return w - 1 - y, x
    if rotation == 2:
        return w - 1 - x, h - 1 - y
    if rotation == 3:
        return y, h - 1 - x
    return x, y


class Emulator:
    def __init__(self, address: str = "127.0.0.1:8554"):
        self.address = address
        self._channel = grpc.insecure_channel(
            address, options=[("grpc.max_receive_message_length", 64 << 20)]
        )
        self._stub = pb_grpc.EmulatorControllerStub(self._channel)
        self._natural: tuple[int, int] | None = None
        # Current display rotation (Surface.ROTATION_*); the controller updates it from each UI dump.
        self.rotation = 0

    def available(self, timeout: float = 1.0) -> bool:
        try:
            grpc.channel_ready_future(self._channel).result(timeout=timeout)
            return True
        except grpc.FutureTimeoutError:
            return False

    @property
    def natural_size(self) -> tuple[int, int]:
        """Display size in its natural (unrotated) orientation; gRPC frames always come this way up."""
        if self._natural is None:
            img = self._stub.getScreenshot(pb.ImageFormat(format=pb.ImageFormat.RGB888))
            self._natural = (img.format.width, img.format.height)
        return self._natural

    def screenshot(self, width: int | None = None) -> Image.Image:
        """Frame turned to match the current rotation, scaled to `width` px wide if given."""
        nw, nh = self.natural_size
        fmt = pb.ImageFormat(format=pb.ImageFormat.RGB888)
        if width:
            display_w = nh if self.rotation % 2 else nw
            scale = width / display_w
            fmt.width, fmt.height = round(nw * scale), round(nh * scale)
        img = self._stub.getScreenshot(fmt)
        frame = Image.frombytes("RGB", (img.format.width, img.format.height), img.image)
        # PIL rotates counter-clockwise; turning the natural frame by 90° per rotation step
        # matches what the user sees (verified against uiautomator2 screenshots for 1 and 3).
        return frame.rotate(90 * self.rotation, expand=True) if self.rotation % 4 else frame

    def _send(self, touches: list[tuple[int, int, int, int]]) -> None:
        natural = self.natural_size
        points = [(*to_natural(x, y, self.rotation, natural), ident, pressure)
                  for x, y, ident, pressure in touches]
        self._stub.sendTouch(pb.TouchEvent(touches=[
            pb.Touch(x=int(x), y=int(y), identifier=ident, pressure=pressure)
            for x, y, ident, pressure in points
        ]))

    def tap(self, x: int, y: int, hold_ms: int = 50) -> None:
        self._send([(x, y, 0, _DOWN_PRESSURE)])
        time.sleep(hold_ms / 1000)
        self._send([(x, y, 0, 0)])

    def long_press(self, x: int, y: int, hold_ms: int = 800) -> None:
        self.tap(x, y, hold_ms)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300,
              hold_ms: int = 0, end_hold_ms: int = 0) -> None:
        """Press at (x1, y1), optionally hold (for drag), move to (x2, y2) over duration_ms, release.

        end_hold_ms keeps the finger still at (x2, y2) before lifting, so the
        release velocity is zero and lists stop where the finger stopped instead
        of flinging on.
        """
        self._send([(x1, y1, 0, _DOWN_PRESSURE)])
        if hold_ms:
            time.sleep(hold_ms / 1000)
        steps = max(2, round(duration_ms / 1000 / _FRAME_INTERVAL_S))
        for i in range(1, steps + 1):
            t = i / steps
            self._send([(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, 0, _DOWN_PRESSURE)])
            time.sleep(_FRAME_INTERVAL_S)
        for _ in range(round(end_hold_ms / 1000 / _FRAME_INTERVAL_S)):
            self._send([(x2, y2, 0, _DOWN_PRESSURE)])
            time.sleep(_FRAME_INTERVAL_S)
        self._send([(x2, y2, 0, 0)])

    def pinch(self, cx: int, cy: int, start_dist: int, end_dist: int,
              duration_ms: int = 400, angle_deg: float = 90) -> None:
        """Two-finger pinch around (cx, cy); end_dist > start_dist zooms in."""
        dx, dy = math.cos(math.radians(angle_deg)) / 2, math.sin(math.radians(angle_deg)) / 2

        def fingers(dist: float, pressure: int):
            return [(cx - dx * dist, cy - dy * dist, 0, pressure),
                    (cx + dx * dist, cy + dy * dist, 1, pressure)]

        self._send(fingers(start_dist, _DOWN_PRESSURE))
        steps = max(2, round(duration_ms / 1000 / _FRAME_INTERVAL_S))
        for i in range(1, steps + 1):
            self._send(fingers(start_dist + (end_dist - start_dist) * i / steps, _DOWN_PRESSURE))
            time.sleep(_FRAME_INTERVAL_S)
        self._send(fingers(end_dist, 0))
