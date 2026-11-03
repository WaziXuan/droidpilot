"""Trace how the screen changes after a tap, to tune settle().

Usage: python scripts/settle_trace.py "x,y" [seconds] [--tree]
Taps the point, then every ~30 ms logs elapsed time and the thumbnail difference
from the previous poll and from the pre-tap frame. With --tree it also dumps the
UI tree each poll (slow while the app animates, which is itself informative).
"""
import hashlib
import sys
import time

from PIL import ImageChops, ImageStat

from droidpilot.controller import Controller


def diff(a, b):
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target, seconds = args[0], float(args[1]) if len(args) > 1 else 3
    with_tree = "--tree" in sys.argv
    ctl = Controller()
    ctl.observe()
    before = ctl._thumb()
    ctl.tap(target)
    start = time.monotonic()
    last = before
    while time.monotonic() - start < seconds:
        frame = ctl._thumb()
        line = (f"{(time.monotonic() - start) * 1000:6.0f} ms  vs prev {diff(frame, last):5.2f}"
                f"  vs before {diff(frame, before):5.2f}")
        if with_tree:
            xml = ctl._dump()
            line += f"  tree {hashlib.md5(xml.encode()).hexdigest()[:6]} {ctl.observe(xml).package}"
        print(line)
        last = frame
        time.sleep(0.03)


if __name__ == "__main__":
    main()
