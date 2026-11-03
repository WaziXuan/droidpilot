"""MCP tool surface.

Action tools wait for the screen to settle and return the fresh UI tree by
default (observe_after=True), so a typical step is a single round trip.
"""
from __future__ import annotations

import os

import grpc
from mcp.server.mcpserver import Image, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from droidpilot.controller import Controller, TargetError

INSTRUCTIONS = """\
Drive an Android device. Call `observe` first: it lists on-screen elements as
`[eN] Class "label" #resource-id @(x,y) WxH flags`. Pass a handle like "e7" (valid
only for the latest element list) or "x,y" device pixels to action tools. Action
tools wait until the screen stops changing and return the updated element list,
so you rarely need a separate observe.

The header line says `loading` while a spinner or page-load bar is visible (call
`wait_idle`), and `keyboard: shown` when the on-screen keyboard covers the lower
screen; elements behind it are flagged `under-keyboard`. The keyboard's action
key (Search/Go/Send/Enter) is listed as a `Key` element; `press_key enter` taps it.
Lists scroll by ~60% of their height so consecutive pages overlap.
Use `screenshot` only when the element list is not enough (images, canvas, games,
web content without accessibility info).
"""

ctl = Controller(
    serial=os.environ.get("DROIDPILOT_SERIAL") or None,
    grpc_address=os.environ.get("DROIDPILOT_GRPC", "127.0.0.1:8554") or None,
    min_interval_ms=int(os.environ.get("DROIDPILOT_MIN_INTERVAL_MS", "300")),
    follow_rotation=os.environ.get("DROIDPILOT_FOLLOW_ROTATION", "1") != "0",
)
mcp = MCPServer("droidpilot", instructions=INSTRUCTIONS)


def _act(action, observe_after: bool, max_wait_ms: int, quiet_ms: int = 400) -> str:
    """Run an action; if observe_after, wait for the screen to settle and return the new element list.

    `action` returns None on success or a string explaining why nothing was done.
    """
    try:
        if observe_after:
            ctl.mark()
        failure = action()
    except TargetError as e:
        raise ToolError(str(e)) from e
    except grpc.RpcError as e:
        raise ToolError(f"emulator gRPC call failed ({e.code().name}); is the emulator still running "
                        f"with -grpc?") from e
    if failure:
        return failure
    if not observe_after:
        return "ok"
    snap = ctl.settle(max_wait_ms, quiet_ms)
    return f"ok (settled in {ctl.last_settle_ms} ms)\n{snap.render()}"


@mcp.tool()
def observe(screenshot: bool = False, width: int = 540) -> list:
    """List interactive and labelled elements on screen with handles. Optionally attach a screenshot."""
    out: list = [ctl.observe().render()]
    if screenshot:
        out.append(Image(data=ctl.screenshot(width), format="jpeg"))
    return out


@mcp.tool()
def screenshot(width: int = 540) -> Image:
    """Current screen as JPEG, scaled to `width` px wide (the device is usually 1080 wide; scale coordinates back)."""
    return Image(data=ctl.screenshot(width), format="jpeg")


@mcp.tool()
def tap(target: str, observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Tap an element handle ("e7") or device coordinates ("540,1200")."""
    return _act(lambda: ctl.tap(target), observe_after, max_wait_ms)


@mcp.tool()
def tap_text(text: str, exact: bool = False, observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Tap the first element whose text (or content description) contains `text`."""
    return _act(lambda: None if ctl.tap_text(text, exact) else f"no element matching {text!r}",
                observe_after, max_wait_ms)


@mcp.tool()
def long_press(target: str, hold_ms: int = 800, observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Press and hold an element handle or "x,y"."""
    return _act(lambda: ctl.long_press(target, hold_ms), observe_after, max_wait_ms)


@mcp.tool()
def swipe(start: str, end: str, duration_ms: int = 300, hold_ms: int = 0,
          observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Swipe from `start` to `end` (handles or "x,y"). Set hold_ms > 0 to press first, i.e. drag."""
    return _act(lambda: ctl.swipe(start, end, duration_ms, hold_ms), observe_after, max_wait_ms)


@mcp.tool()
def scroll(direction: str, target: str | None = None, distance: float = 0.6, fling: bool = False,
           duration_ms: int = 300, observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Scroll "down" (reveal content below), "up", "left" or "right", within a scrollable handle or the whole
    screen, by about `distance` of its height/width so consecutive pages overlap. fling=True lets the list
    coast further (faster for long lists, but items can be skipped)."""
    return _act(lambda: ctl.scroll(direction, target, distance, duration_ms, fling), observe_after, max_wait_ms)


@mcp.tool()
def pinch(zoom: str, target: str | None = None, observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Two-finger pinch: zoom "in" or "out", centred on a handle/"x,y" or the screen centre. Emulator gRPC only."""
    return _act(lambda: ctl.pinch(zoom, target), observe_after, max_wait_ms)


@mcp.tool()
def rotate(orientation: str, observe_after: bool = True, max_wait_ms: int = 4000) -> str:
    """Turn the device to "portrait", "landscape", "reverse_portrait" or "reverse_landscape", like a person
    turning the phone. The display only follows if auto-rotate is on and the app allows it; check the
    `orientation` in the returned header."""
    return _act(lambda: ctl.rotate(orientation), observe_after, max_wait_ms)


@mcp.tool()
def type_text(text: str, clear: bool = False, observe_after: bool = True, max_wait_ms: int = 2000) -> str:
    """Type into the focused field (tap the field first). Unicode is fine. clear=True replaces existing text."""
    return _act(lambda: ctl.type_text(text, clear), observe_after, max_wait_ms)


@mcp.tool()
def press_key(key: str, observe_after: bool = True, max_wait_ms: int = 3000) -> str:
    """Press a key: back, home, recent, delete, tab, volume_up, volume_down, power, or any KEYCODE_ name.
    "enter" (also "search"/"go"/"send"/"done") presses the on-screen keyboard's action key when the
    keyboard is shown, which is what submits most search boxes and chat inputs."""
    return _act(lambda: ctl.press(key), observe_after, max_wait_ms)


@mcp.tool()
def wait_for(text: str | None = None, resource_id: str | None = None, timeout: float = 5,
             observe_after: bool = True) -> str:
    """Wait until an element whose label (text or content description) contains `text`, and/or with
    resource id `resource_id`, appears."""
    try:
        found = ctl.wait_for(text, resource_id, timeout)
    except TargetError as e:
        raise ToolError(str(e)) from e
    note = "found" if found else f"not found after {timeout}s"
    return f"{note}\n{ctl.snapshot.render()}" if observe_after else note


@mcp.tool()
def wait_idle(max_wait_ms: int = 8000) -> str:
    """Wait until the screen stops changing and nothing is loading (use when the element list says
    `loading`, e.g. a web page still coming in), then return the element list."""
    snap = ctl.settle(max_wait_ms, quiet_ms=0, loading_grace_ms=None)
    return f"ok (idle after {ctl.last_settle_ms} ms)\n{snap.render()}"


@mcp.tool()
def app_launch(package: str, observe_after: bool = True, max_wait_ms: int = 6000) -> str:
    """Launch an app by package name (see app_list)."""
    # Cold starts can take a couple of seconds before the first frame changes.
    return _act(lambda: ctl.app_launch(package), observe_after, max_wait_ms, quiet_ms=2500)


@mcp.tool()
def app_stop(package: str) -> str:
    """Force-stop an app."""
    ctl.app_stop(package)
    return "ok"


@mcp.tool()
def app_current() -> dict:
    """Foreground package and activity."""
    return ctl.app_current()


@mcp.tool()
def app_list(contains: str = "") -> list[str]:
    """Installed packages, optionally filtered by substring."""
    return ctl.app_list(contains)


@mcp.tool()
def status() -> dict:
    """Which backends are in use, screen size and pacing."""
    return ctl.backends()
