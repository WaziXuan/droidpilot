"""Measure observation latency of each backend on a running emulator.

Usage: python scripts/bench.py [--serial emulator-5554] [--grpc 127.0.0.1:8554] [-n 5]
"""
import argparse
import statistics
import subprocess
import time

import grpc
import uiautomator2 as u2

from droidpilot._proto import emulator_controller_pb2 as pb
from droidpilot._proto import emulator_controller_pb2_grpc as pb_grpc


def timed(fn, n):
    samples = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t) * 1000)
    return statistics.median(samples), min(samples), max(samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", default="emulator-5554")
    ap.add_argument("--grpc", default="127.0.0.1:8554")
    ap.add_argument("-n", type=int, default=5)
    args = ap.parse_args()

    channel = grpc.insecure_channel(args.grpc, options=[("grpc.max_receive_message_length", 64 << 20)])
    stub = pb_grpc.EmulatorControllerStub(channel)
    d = u2.connect(args.serial)
    d.info  # warm up the on-device server

    cases = {
        "grpc screenshot RGB888": lambda: stub.getScreenshot(pb.ImageFormat(format=pb.ImageFormat.RGB888)),
        "grpc screenshot PNG": lambda: stub.getScreenshot(pb.ImageFormat(format=pb.ImageFormat.PNG)),
        "grpc screenshot RGB888 540w": lambda: stub.getScreenshot(
            pb.ImageFormat(format=pb.ImageFormat.RGB888, width=540, height=1200)),
        "u2 dump_hierarchy": lambda: d.dump_hierarchy(compressed=True),
        "u2 screenshot": lambda: d.screenshot(),
        "adb uiautomator dump": lambda: subprocess.run(
            ["adb", "-s", args.serial, "exec-out", "uiautomator", "dump", "/dev/tty"],
            capture_output=True),
        "adb screencap": lambda: subprocess.run(
            ["adb", "-s", args.serial, "exec-out", "screencap", "-p"], capture_output=True),
    }
    print(f"{'case':32} {'median':>8} {'min':>8} {'max':>8}  (ms, n={args.n})")
    for name, fn in cases.items():
        med, lo, hi = timed(fn, args.n)
        print(f"{name:32} {med:8.0f} {lo:8.0f} {hi:8.0f}")


if __name__ == "__main__":
    main()
