import argparse
import logging
import os
import sys


def main() -> None:
    ap = argparse.ArgumentParser(prog="droidpilot", description="MCP server for driving an Android emulator.")
    ap.add_argument("--serial", help="adb serial (default: the only connected device)")
    ap.add_argument("--grpc", help="emulator gRPC address, '' to disable (default 127.0.0.1:8554)")
    ap.add_argument("--min-interval-ms", type=int, help="minimum gap between actions (default 300)")
    ap.add_argument("--no-follow-rotation", action="store_true",
                    help="don't turn the emulator window to match the display rotation")
    ap.add_argument("--transport", default="stdio", choices=["stdio", "sse", "streamable-http"])
    ap.add_argument("--port", type=int, default=8765, help="port for the HTTP transports (default 8765)")
    args = ap.parse_args()

    # The server reads its config from the environment at import time.
    if args.serial:
        os.environ["DROIDPILOT_SERIAL"] = args.serial
    if args.grpc is not None:
        os.environ["DROIDPILOT_GRPC"] = args.grpc
    if args.min_interval_ms is not None:
        os.environ["DROIDPILOT_MIN_INTERVAL_MS"] = str(args.min_interval_ms)
    if args.no_follow_rotation:
        os.environ["DROIDPILOT_FOLLOW_ROTATION"] = "0"

    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    from droidpilot.server import mcp

    if args.transport == "stdio":
        mcp.run("stdio")
    else:
        mcp.run(args.transport, port=args.port)


if __name__ == "__main__":
    main()
