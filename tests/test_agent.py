"""Controller driving a fake on-phone agent over real HTTP."""
from __future__ import annotations

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PIL import Image

from droidpilot.agent import AgentClient
from droidpilot.controller import Controller, TargetError

TOKEN = "secret"
XML = (
    '<?xml version="1.0" encoding="UTF-8"?><hierarchy rotation="0">'
    '<node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example" '
    'content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false" '
    'focused="false" scrollable="false" long-clickable="false" password="false" selected="false" '
    'visible-to-user="true" bounds="[0,0][720,1280]">'
    '<node index="0" text="Search" resource-id="com.example:id/q" class="android.widget.EditText" '
    'package="com.example" content-desc="" hint="Search" checkable="false" checked="false" clickable="true" '
    'enabled="true" focusable="true" focused="true" scrollable="false" long-clickable="false" password="false" '
    'selected="false" visible-to-user="true" bounds="[40,100][680,200]" />'
    '</node></hierarchy>'
)


class FakeAgent(BaseHTTPRequestHandler):
    calls: list = []

    def log_message(self, *a):
        pass

    def _reply(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle(self) -> None:
        if self.headers.get("X-Token") != TOKEN:
            return self._reply(401, b'{"error":"bad token"}')
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n)) if n else None
        path = self.path.split("?")[0]
        FakeAgent.calls.append((path, body))
        if path == "/info":
            return self._reply(200, json.dumps({"ok": True, "width": 720, "height": 1280, "rotation": 0,
                                                "screen_on": True, "capture": True}).encode())
        if path == "/dump":
            return self._reply(200, XML.encode(), "text/xml")
        if path == "/screenshot":
            buf = io.BytesIO()
            Image.new("RGB", (360, 640), "red").save(buf, "JPEG")
            return self._reply(200, buf.getvalue(), "image/jpeg")
        if path == "/key" and body["key"] not in ("4", "3"):
            return self._reply(400, b'{"error":"key not available"}')
        if path == "/current":
            return self._reply(200, b'{"ok":true,"package":"com.example","activity":"com.example.Main"}')
        return self._reply(200, b'{"ok":true}')

    do_GET = do_POST = _handle


@pytest.fixture()
def agent():
    FakeAgent.calls = []
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeAgent)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def make(addr: str) -> Controller:
    ctl = Controller(agent=addr, min_interval_ms=0)
    ctl.device._token = TOKEN
    assert ctl.emu is None
    return ctl


def test_observe_and_tap(agent):
    ctl = make(agent)
    snap = ctl.observe()
    el = next(e for e in snap.elements.values() if e.resource_id == "q")
    ctl.tap(el.handle)
    assert ("/tap", {"x": 360, "y": 150}) in FakeAgent.calls


def test_swipe_keeps_holds(agent):
    ctl = make(agent)
    ctl.observe()
    ctl.swipe("10,900", "10,300", 300, hold_ms=0, end_hold_ms=120)
    path, body = FakeAgent.calls[-1]
    assert path == "/swipe" and body["end_hold_ms"] == 120 and body["y2"] == 300


def test_type_text_sends_hint(agent):
    ctl = make(agent)
    ctl.observe()
    ctl.type_text("hello", clear=True)
    assert FakeAgent.calls[-1] == ("/set_text", {"text": "hello", "clear": True, "hint": "Search"})


def test_keys(agent):
    ctl = make(agent)
    ctl.press("back")
    assert FakeAgent.calls[-1] == ("/key", {"key": "4"})
    with pytest.raises(TargetError):
        ctl.press("camera")


def test_screenshot_and_current(agent):
    ctl = make(agent)
    jpg = ctl.screenshot(width=360)
    assert Image.open(io.BytesIO(jpg)).size == (360, 640)
    assert ctl.app_current() == {"package": "com.example", "activity": "com.example.Main"}


def test_bad_token_is_a_connection_error(agent):
    with pytest.raises(ConnectionError):
        AgentClient(agent, "wrong").window_size()
