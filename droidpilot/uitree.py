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
    elements: dict[str, Element] = field(default_factory=dict)

    def render(self) -> str:
        head = f"package: {self.package}  elements: {len(self.elements)}"
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


def parse(xml: str, screen: tuple[int, int] | None = None) -> Snapshot:
    root = ET.fromstring(xml)
    packages = [n.get("package") for n in root.iter("node") if n.get("package")]
    snap = Snapshot(package=packages[0] if packages else "?")
    covered: set[int] = set()  # nodes whose text is already shown on an interactive ancestor

    def visit(node: ET.Element) -> None:
        if node.tag == "node" and node.get("visible-to-user", "true") != "false":
            b = _bounds(node)
            if b and screen:
                w, h = screen
                if b[2] <= 0 or b[3] <= 0 or b[0] >= w or b[1] >= h:
                    b = None
            if b:
                flags = _flags(node)
                interactive = _interactive(flags)
                label = _own_label(node)
                if interactive and not label and "scroll" not in flags:
                    label = _descendant_label(node)
                    covered.update(id(c) for c in node.iter() if c is not node and not _interactive(_flags(c)))
                if interactive or (label and id(node) not in covered):
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
            visit(child)

    visit(root)
    return snap
