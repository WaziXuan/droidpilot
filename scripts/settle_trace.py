"""Trace what keeps changing after an action, to tune settle().

Usage: python scripts/settle_trace.py "x,y" [seconds]
Taps the point, then logs every poll: elapsed ms, whether the UI tree changed,
the thumbnail difference from the previous poll, and the element count.
"""
import hashlib
import sys
import time

from PIL import ImageChops, ImageStat

from droidpilot.controller import Controller


def main():
    target = sys.argv[1]
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 3
    ctl = Controller()
    ctl.observe()
    ctl.tap(target)
    start = time.monotonic()
    last_xml, last_frame = None, None
    while time.monotonic() - start < seconds:
        xml, frame = ctl._dump(), ctl._thumb()
        diff = ImageStat.Stat(ImageChops.difference(frame, last_frame)).mean[0] if last_frame else 0
        n = len(ctl.observe(xml).elements)
        h = hashlib.md5(xml.encode()).hexdigest()[:6]
        print(f"{(time.monotonic() - start) * 1000:6.0f} ms  tree {h} {'CHANGED' if xml != last_xml else '       '}"
              f"  frame diff {diff:5.2f}  elements {n}")
        last_xml, last_frame = xml, frame
        time.sleep(0.04)


if __name__ == "__main__":
    main()
