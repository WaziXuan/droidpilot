"""Regenerate droidpilot/_proto from proto/ (run after updating the .proto from a newer emulator)."""
from pathlib import Path

from grpc_tools import protoc

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    rc = protoc.main([
        "protoc",
        f"-I{ROOT / 'proto'}",
        f"--python_out={ROOT}",
        f"--pyi_out={ROOT}",
        f"--grpc_python_out={ROOT}",
        str(ROOT / "proto/droidpilot/_proto/emulator_controller.proto"),
    ])
    raise SystemExit(rc)
