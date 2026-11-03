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
_PAGE_FRACTION = 0.5  # clickable containers bigger than this share of the screen get no aggregated label
# Labels keyboards give their editor-action key (Gboard, in English and Chinese UIs).
_IME_ACTION_LABELS = {
    "enter", "return", "search", "go", "send", "done", "next", "previous",
    "搜索", "搜尋", "发送", "傳送", "前往", "完成", "下一步", "下一个", "確定", "确定", "换行", "換行",
}


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
    rotation: int = 0  # Surface.ROTATION_*; odd values are landscape
    keyboard_top: int | None = None  # y where the on-screen keyboard starts, if shown
    elements: dict[str, Element] = field(default_factory=dict)
    ime_action: Element | None = None  # the keyboard's Enter/Search/Go/Send key, if exposed
    # Visible progress bars as (bounds, value text). Indeterminate ones (spinners,
    # browser page-load bars) report no value; static gauges (storage, battery) do.
    progress: list[tuple[tuple[int, int, int, int], str]] = field(default_factory=list)

    @property
    def loading(self) -> bool:
        return any(value == "" for _, value in self.progress)

    def partial_progress(self) -> bool:
        """A determinate bar below 100%: may be a moving download/page bar or a static gauge."""
        for _, value in self.progress:
            try:
                if float(value) < 100:
                    return True
            except ValueError:
                pass
        return False

    def render(self) -> str:
        head = f"package: {self.package}  elements: {len(self.elements)}"
        if self.rotation % 2:
            head += "  orientation: landscape"
        if self.loading:
            head += "  loading"
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
        if child is not node and (t := _own_label(child)) and t not in texts:
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


def _box_area(b: tuple[int, int, int, int]) -> int:
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def _duplicate(snap: "Snapshot", label: str, b: tuple[int, int, int, int]) -> bool:
    """Nested clickable wrappers (frequent in web content) repeat their child's label and box."""
    label = _truncate(label)
    for el in snap.elements.values():
        if el.text == label:
            overlap = _box_area(_intersect(el.bounds, b))
            if overlap >= 0.85 * max(_box_area(el.bounds), _box_area(b)):
                return True
    return False


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
    try:
        snap.rotation = int(root.get("rotation", "0")) % 4
    except ValueError:
        pass
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
        if b and node.get("class", "").endswith("ProgressBar"):
            # Recorded before the size filter: page-load bars are a few px tall.
            snap.progress.append((b, node.get("text", "")))
        if b and min(b[2] - b[0], b[3] - b[1]) < _MIN_TARGET_PX:
            b = None  # slivers at the edge of a scrolled list; not reliably tappable
        if b:
            flags = _flags(node)
            if "scroll" in flags:
                clip = _intersect(clip, b) if clip else b
            interactive = _interactive(flags)
            label = _own_label(node)
            if interactive and label:
                # Children that only repeat part of this label (a tile's caption, say) add nothing.
                covered.update(id(c) for c in node.iter() if c is not node and not _interactive(_flags(c))
                               and (t := _own_label(c)) and t in label)
            if interactive and not label and "scroll" not in flags:
                if screen and _box_area(b) > _PAGE_FRACTION * screen[0] * screen[1]:
                    # A page-sized click target (common at the root of web pages) says nothing
                    # useful; list its children individually instead.
                    interactive = False
                else:
                    label = _descendant_label(node)
                    covered.update(id(c) for c in node.iter() if c is not node and not _interactive(_flags(c)))
            if (interactive or (label and id(node) not in covered)) and not _duplicate(snap, label, b):
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

    # Of the keyboard, list only its action key: it is what submits a search or
    # message, and apps often ignore a plain KEYCODE_ENTER.
    if ime is not None and (key := _ime_action_key(ime)) is not None:
        handle = f"e{len(snap.elements) + 1}"
        snap.ime_action = Element(handle=handle, cls="Key", text=_own_label(key), resource_id="",
                                  bounds=_bounds(key), flags=["click", "ime-action"])
        snap.elements[handle] = snap.ime_action
    return snap


def _ime_action_key(ime: ET.Element) -> ET.Element | None:
    keys = [n for n in ime.iter("node") if n.get("clickable") == "true" and _bounds(n)
            and _own_label(n).casefold() in _IME_ACTION_LABELS]
    # The action key sits at the right end of the bottom row of keys.
    return max(keys, key=lambda n: (_bounds(n)[3], _bounds(n)[2]), default=None)
