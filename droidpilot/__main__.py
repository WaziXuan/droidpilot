import argparse
import logging
import os
import sys


def main() -> None:
    ap = argparse.ArgumentParser(prog="droidpilot", description="MCP server for driving an Android emulator.")
    ap.add_argument("--serial", help="adb serial (default: the only connected device)")
    ap.add_argument("--grpc", help="emulator gRPC address, '' to disable (default 127.0.0.1:8554)")
    ap.add_argument("--min-interval-ms", type=int, help="minimum gap between actions (default 300)")
    ap.add_argument("--transport", default="stdio", choices=["stdio", "sse", "streamable-http"])
    args = ap.parse_args()

    # The server reads its config from the environment at import time.
    if args.serial:
        os.environ["DROIDPILOT_SERIAL"] = args.serial
    if args.grpc is not None:
        os.environ["DROIDPILOT_GRPC"] = args.grpc
    if args.min_interval_ms is not None:
        os.environ["DROIDPILOT_MIN_INTERVAL_MS"] = str(args.min_interval_ms)

    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    from droidpilot.server import mcp

    mcp.run(args.transport)


if __name__ == "__main__":
    main()
