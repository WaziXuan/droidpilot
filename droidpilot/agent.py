"""Wireless backend: talks to the on-phone accessibility agent (agent/) over HTTP.

Android restarts an accessibility service by itself after a reboot, so unlike
adb-over-TCP this keeps working with nobody next to the phone. The agent needs
a token, which only processes on the phone can read (GET /token from loopback);
`scripts/setup_agent.py` fetches it once and stores it in ~/.droidpilot/agent_token.

AgentClient mimics the small part of the uiautomator2 Device API that
Controller uses, plus a few agent-only calls (set_text, key, current_app).
"""
from __future__ import annotations

import io
import json
import logging
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

log = logging.getLogger(__name__)

DEFAULT_PORT = 8790
TOKEN_FILE = Path.home() / ".droidpilot" / "agent_token"


class AgentError(RuntimeError):
    """The agent understood the request but refused it (no focused field, unsupported key...)."""


def load_token() -> str:
    token = os.environ.get("DROIDPILOT_AGENT_TOKEN")
    if token:
        return token.strip()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    raise RuntimeError(f"no agent token: set DROIDPILOT_AGENT_TOKEN or run scripts/setup_agent.py (writes {TOKEN_FILE})")


class AgentClient:
    def __init__(self, address: str, token: str | None = None, timeout: float = 15):
        host, _, port = address.rpartition(":") if ":" in address else (address, "", "")
        self.base = f"http://{host or address}:{port or DEFAULT_PORT}"
        self.token = token or load_token()
        self.timeout = timeout

    # -- transport ------------------------------------------------------------

    def _request(self, path: str, body: dict | None = None, raw: bool = False, timeout: float | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method="POST" if data is not None else "GET",
                                     headers={"X-Token": self.token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                payload = resp.read()
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", str(e))
            except Exception:
                msg = str(e)
            if e.code in (400, 404, 409, 503):
                raise AgentError(msg) from None
            raise ConnectionError(f"agent {e.code}: {msg}") from None
        except urllib.error.URLError as e:
            raise ConnectionError(f"agent at {self.base} unreachable: {e.reason}") from None
        return payload if raw else json.loads(payload)

    def ping(self) -> dict:
        return self._request("/ping")

    # -- uiautomator2-compatible surface ---------------------------------------

    @property
    def info(self) -> dict:
        i = self._request("/info")
        return {"displayRotation": i["rotation"], "displayWidth": i["width"], "displayHeight": i["height"],
                "screenOn": i["screen_on"], **i}

    def window_size(self) -> tuple[int, int]:
        i = self._request("/info")
        return i["width"], i["height"]

    def dump_hierarchy(self, compressed: bool = True) -> str:
        return self._request("/dump", raw=True).decode("utf-8")

    def screenshot(self, width: int = 0) -> Image.Image:
        jpg = self._request(f"/screenshot?width={width}&quality=85", raw=True, timeout=20)
        return Image.open(io.BytesIO(jpg))

    def click(self, x: int, y: int) -> None:
        self._request("/tap", {"x": int(x), "y": int(y)})

    def long_click(self, x: int, y: int, duration: float = 0.8) -> None:
        self._request("/long_press", {"x": int(x), "y": int(y), "hold_ms": int(duration * 1000)})

    def swipe(self, x1, y1, x2, y2, duration: float = 0.3) -> None:
        self.swipe_ex(x1, y1, x2, y2, int(duration * 1000))

    def drag(self, x1, y1, x2, y2, duration: float = 0.5) -> None:
        self.swipe_ex(x1, y1, x2, y2, 300, hold_ms=max(0, int(duration * 1000) - 300))

    def set_orientation(self, value: str) -> None:
        self._request("/rotate", {"rotation": {"n": 0, "l": 1, "u": 2, "r": 3}[value]})

    def app_start(self, package: str, wait: bool = False) -> None:
        self._request("/launch", {"package": package})

    def app_stop(self, package: str) -> None:
        self._request("/stop", {"package": package})

    def app_list(self) -> list[str]:
        return self._request("/apps")["packages"]

    def stop_uiautomator(self) -> None:
        pass

    # -- agent-only -------------------------------------------------------------

    def swipe_ex(self, x1, y1, x2, y2, duration_ms: int, hold_ms: int = 0, end_hold_ms: int = 0) -> None:
        total = duration_ms + hold_ms + end_hold_ms
        self._request("/swipe", {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2), "duration_ms": duration_ms,
                                 "hold_ms": hold_ms, "end_hold_ms": end_hold_ms}, timeout=self.timeout + total / 1000)

    def pinch(self, cx: int, cy: int, start: int, end: int, duration_ms: int) -> None:
        self._request("/pinch", {"cx": cx, "cy": cy, "start": start, "end": end, "duration_ms": duration_ms})

    def key(self, key: str | int) -> None:
        self._request("/key", {"key": str(key)})

    def set_text(self, text: str, clear: bool = False, hint: str | None = None) -> None:
        self._request("/set_text", {"text": text, "clear": clear, "hint": hint})

    def current_app(self) -> dict:
        r = self._request("/current")
        return {"package": r.get("package") or None, "activity": r.get("activity") or None}

    def wake(self) -> None:
        self._request("/wake", {})


class AgentDevice:
    """Same role as device.Device (call / reset / serial), backed by the agent."""

    def __init__(self, address: str, token: str | None = None):
        self.serial = f"agent:{address}"
        self._address = address
        self._token = token
        self._client: AgentClient | None = None
        self._lock = threading.Lock()

    @property
    def client(self) -> AgentClient:
        with self._lock:
            if self._client is None:
                self._client = AgentClient(self._address, self._token)
            return self._client

    u2 = client  # what Controller code written for uiautomator2 reaches for

    def reset(self) -> None:
        with self._lock:
            self._client = None

    def call(self, fn):
        """Run fn(client); retry once on a dropped connection (Wi-Fi blips, the agent restarting)."""
        try:
            return fn(self.client)
        except (ConnectionError, TimeoutError, OSError) as e:
            log.warning("agent request failed (%s); retrying once", e)
            self.reset()
            return fn(self.client)
