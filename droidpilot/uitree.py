"""Compress a uiautomator hierarchy dump into a short, numbered element list.

Each kept element gets a handle (e1, e2, ...) that action tools accept, so the
agent can say "tap e7" instead of guessing coordinates. A handle is only valid
for the snapshot it came from.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")
_LABEL_MAX = 60
_SYSTEMUI = "com.android.systemui"
_STATUS_BAR = "com.android.systemui:id/status_bar_container"
_MIN_TARGET_PX = 24


@dataclass
class Element:
    handle: str
    cls: str
    text: str
    resource_id: str
    bounds: tuple[int, int, int, int]
    flags: list[str]

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bounds
        return (x1 + x2) // 2, (y1 + y2) // 2

    def line(self) -> str:
        x1, y1, x2, y2 = self.bounds
        parts = [f"[{self.handle}]", self.cls]
        if self.text:
            parts.append(f'"{self.text}"')
        if self.resource_id:
            parts.append(f"#{self.resource_id}")
        cx, cy = self.center
        parts.append(f"@({cx},{cy}) {x2 - x1}x{y2 - y1}")
        if self.flags:
            parts.append(",".join(self.flags))
        return " ".join(parts)


@dataclass
class Snapshot:
    package: str
    keyboard_top: int | None = None  # y where the on-screen keyboard starts, if shown
    elements: dict[str, Element] = field(default_factory=dict)

    def render(self) -> str:
        head = f"package: {self.package}  elements: {len(self.elements)}"
        if self.keyboard_top is not None:
            head += f"  keyboard: shown (covers y>={self.keyboard_top})"
        return "\n".join([head, *(e.line() for e in self.elements.values())])


def _bounds(node: ET.Element) -> tuple[int, int, int, int] | None:
    m = _BOUNDS.fullmatch(node.get("bounds", ""))
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    return (x1, y1, x2, y2) if x2 > x1 and y2 > y1 else None


def _own_label(node: ET.Element) -> str:
    return (node.get("text") or node.get("content-desc") or node.get("hint") or "").strip()


def _descendant_label(node: ET.Element) -> str:
    texts = []
    for child in node.iter():
        if child is not node and (t := _own_label(child)):
            texts.append(t)
    return " | ".join(texts)


def _flags(node: ET.Element) -> list[str]:
    flags = []
    if node.get("clickable") == "true":
        flags.append("click")
    if node.get("long-clickable") == "true":
        flags.append("long")
    if node.get("scrollable") == "true":
        flags.append("scroll")
    if node.get("class", "").endswith("EditText"):
        flags.append("edit")
    if node.get("checkable") == "true":
        flags.append("checked" if node.get("checked") == "true" else "unchecked")
    if node.get("selected") == "true":
        flags.append("selected")
    if node.get("focused") == "true":
        flags.append("focused")
    if node.get("enabled") == "false":
        flags.append("disabled")
    if node.get("password") == "true":
        flags.append("password")
    return flags


_INTERACTIVE = {"click", "long", "scroll", "edit", "checked", "unchecked"}


def _interactive(flags: list[str]) -> bool:
    return any(f in _INTERACTIVE for f in flags)


def _truncate(s: str) -> str:
    s = " ".join(s.split())
    return s if len(s) <= _LABEL_MAX else s[: _LABEL_MAX - 1] + "…"


def _center_in(b: tuple[int, int, int, int], clip: tuple[int, int, int, int]) -> bool:
    cx, cy = (b[0] + b[2]) // 2, (b[1] + b[3]) // 2
    return clip[0] <= cx < clip[2] and clip[1] <= cy < clip[3]


def _intersect(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    return max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])


def _area(node: ET.Element) -> int:
    b = _bounds(node)
    return (b[2] - b[0]) * (b[3] - b[1]) if b else 0


def _is_ime(window: ET.Element) -> bool:
    return "inputmethod" in window.get("package", "")


def parse(xml: str, screen: tuple[int, int] | None = None) -> Snapshot:
    root = ET.fromstring(xml)
    # Top-level nodes are windows: status bar, keyboard, dialogs, the app itself.
    windows = [w for w in root if w.tag == "node"]
    apps = [w for w in windows if w.get("package") != _SYSTEMUI and not _is_ime(w)]
    main = max(apps or windows, key=_area, default=None)
    snap = Snapshot(package=main.get("package", "?") if main is not None else "?")
    ime = next((w for w in windows if _is_ime(w) and _bounds(w)), None)
    if ime is not None:
        snap.keyboard_top = _bounds(ime)[1]
    covered: set[int] = set()  # nodes whose text is already shown on an interactive ancestor

    def visit(node: ET.Element, clip: tuple[int, int, int, int] | None) -> None:
        """`clip` is the visible area of the nearest scrolling ancestor (or the screen)."""
        if node is ime or node.get("resource-id") == _STATUS_BAR:
            return  # keyboard keys and status-bar icons are noise for the agent
        b = _bounds(node) if node.tag == "node" and node.get("visible-to-user", "true") != "false" else None
        if b and clip and not _center_in(b, clip):
            # Scrolled out of its container, e.g. under a collapsing toolbar: a tap there hits something else.
            b = None
        if b and min(b[2] - b[0], b[3] - b[1]) < _MIN_TARGET_PX:
            b = None  # slivers at the edge of a scrolled list; not reliably tappable
        if b:
            flags = _flags(node)
            if "scroll" in flags:
                clip = _intersect(clip, b) if clip else b
            interactive = _interactive(flags)
            label = _own_label(node)
            if interactive and not label and "scroll" not in flags:
                label = _descendant_label(node)
                covered.update(id(c) for c in node.iter() if c is not node and not _interactive(_flags(c)))
            if interactive or (label and id(node) not in covered):
                if snap.keyboard_top is not None and (b[1] + b[3]) // 2 >= snap.keyboard_top:
                    flags.append("under-keyboard")
                handle = f"e{len(snap.elements) + 1}"
                rid = node.get("resource-id", "")
                snap.elements[handle] = Element(
                    handle=handle,
                    cls=node.get("class", "").rsplit(".", 1)[-1],
                    text=_truncate(label),
                    resource_id=rid.split(":id/", 1)[-1],
                    bounds=b,
                    flags=flags,
                )
        for child in node:
            visit(child, clip)

    visit(root, (0, 0, *screen) if screen else None)
    return snap
