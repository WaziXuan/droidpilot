"""Thin client for the Android Emulator gRPC endpoint (start the emulator with `-grpc <port>`).

Used for the two things it does faster than anything running inside the guest:
grabbing frames straight from the emulator's framebuffer, and injecting touch
input (including multi-touch) as virtual touchscreen events.
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


class Emulator:
    def __init__(self, address: str = "127.0.0.1:8554"):
        self.address = address
        self._channel = grpc.insecure_channel(
            address, options=[("grpc.max_receive_message_length", 64 << 20)]
        )
        self._stub = pb_grpc.EmulatorControllerStub(self._channel)
        self._size: tuple[int, int] | None = None

    def available(self, timeout: float = 1.0) -> bool:
        try:
            grpc.channel_ready_future(self._channel).result(timeout=timeout)
            return True
        except grpc.FutureTimeoutError:
            return False

    @property
    def size(self) -> tuple[int, int]:
        """Display size in device pixels (portrait orientation as reported by the emulator)."""
        if self._size is None:
            self.screenshot()
        return self._size

    def screenshot(self, width: int | None = None) -> Image.Image:
        fmt = pb.ImageFormat(format=pb.ImageFormat.RGB888)
        if width and self._size:
            w, h = self._size
            fmt.width, fmt.height = width, round(h * width / w)
        img = self._stub.getScreenshot(fmt)
        size = (img.format.width, img.format.height)
        if not width:
            self._size = size
        frame = Image.frombytes("RGB", size, img.image)
        if width and self._size is None:
            # First call asked for a scaled frame before we knew the display size.
            self._size = size
            frame = frame.resize((width, round(size[1] * width / size[0])))
        return frame

    def _send(self, touches: list[tuple[int, int, int, int]]) -> None:
        self._stub.sendTouch(pb.TouchEvent(touches=[
            pb.Touch(x=int(x), y=int(y), identifier=ident, pressure=pressure)
            for x, y, ident, pressure in touches
        ]))

    def tap(self, x: int, y: int, hold_ms: int = 50) -> None:
        self._send([(x, y, 0, _DOWN_PRESSURE)])
        time.sleep(hold_ms / 1000)
        self._send([(x, y, 0, 0)])

    def long_press(self, x: int, y: int, hold_ms: int = 800) -> None:
        self.tap(x, y, hold_ms)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300,
              hold_ms: int = 0) -> None:
        """Press at (x1, y1), optionally hold (for drag), move to (x2, y2) over duration_ms, release."""
        self._send([(x1, y1, 0, _DOWN_PRESSURE)])
        if hold_ms:
            time.sleep(hold_ms / 1000)
        steps = max(2, round(duration_ms / 1000 / _FRAME_INTERVAL_S))
        for i in range(1, steps + 1):
            t = i / steps
            self._send([(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, 0, _DOWN_PRESSURE)])
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
