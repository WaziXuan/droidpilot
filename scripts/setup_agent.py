"""One-time setup of the on-phone agent over USB adb. After this, no cable is needed, even after reboots.

Usage: python scripts/setup_agent.py [--serial SERIAL] [--apk PATH] [--check HOST]

1. installs agent/build/droidpilot-agent.apk (build it with scripts/build_agent.py)
2. turns on its accessibility service (Android restarts it after every reboot)
3. pre-approves screen capture (PROJECT_MEDIA) and rotation (WRITE_SETTINGS), exempts it from battery saving
4. reads the agent's token through an adb port forward and saves it to ~/.droidpilot/agent_token
5. optionally checks that HOST:8790 (e.g. the phone's Tailscale IP) answers with that token
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from droidpilot.agent import DEFAULT_PORT, TOKEN_FILE, AgentClient  # noqa: E402

PKG = "com.droidpilot.agent"
SERVICE = f"{PKG}/{PKG}.AgentService"
APK = Path(__file__).resolve().parent.parent / "agent" / "build" / "droidpilot-agent.apk"
LOCAL_PORT = 18790


def adb(serial: str | None, *args: str, check: bool = True) -> str:
    cmd = ["adb", *(["-s", serial] if serial else []), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        sys.exit(f"{' '.join(cmd)} failed:\n{r.stdout}{r.stderr}")
    return r.stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial")
    ap.add_argument("--apk", default=str(APK))
    ap.add_argument("--check", metavar="HOST", help="also check the agent answers at HOST:8790 (e.g. a Tailscale IP)")
    a = ap.parse_args()
    s = a.serial

    print("installing", a.apk)
    adb(s, "install", "-r", a.apk)

    print("enabling the accessibility service")
    current = adb(s, "shell", "settings", "get", "secure", "enabled_accessibility_services")
    services = [x for x in current.split(":") if x and x != "null"]
    if SERVICE not in services:
        services.append(SERVICE)
        adb(s, "shell", "settings", "put", "secure", "enabled_accessibility_services", ":".join(services))
    adb(s, "shell", "settings", "put", "secure", "accessibility_enabled", "1")

    print("granting screen capture, settings and battery exemptions")
    adb(s, "shell", "appops", "set", PKG, "PROJECT_MEDIA", "allow")
    adb(s, "shell", "appops", "set", PKG, "WRITE_SETTINGS", "allow")
    adb(s, "shell", "dumpsys", "deviceidle", "whitelist", f"+{PKG}", check=False)
    adb(s, "shell", "cmd", "appops", "set", PKG, "RUN_IN_BACKGROUND", "allow", check=False)

    print("reading the token")
    adb(s, "forward", f"tcp:{LOCAL_PORT}", f"tcp:{DEFAULT_PORT}")
    token = None
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{LOCAL_PORT}/token", timeout=3) as r:
                    token = json.loads(r.read())["token"]
                break
            except Exception:
                time.sleep(1)
        if not token:
            sys.exit("the agent did not answer on the phone; check Settings > Accessibility > DroidPilot Agent")
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token)
        print("token saved to", TOKEN_FILE)

        local = AgentClient(f"127.0.0.1:{LOCAL_PORT}", token)
        local._request("/capture", {})
        for _ in range(15):
            info = local.info
            if info["capture"]:
                break
            time.sleep(1)
        print("phone:", {k: info[k] for k in ("model", "sdk", "width", "height", "screen_on", "locked", "secure_lock", "capture")})
        if info["secure_lock"]:
            print("WARNING: the phone has a PIN/pattern lock. After a reboot Android starts no apps until it is "
                  "unlocked once, so the agent would stay down. Remove the lock for unattended use.")
        if not info["capture"]:
            print("WARNING: screen capture not granted yet; screenshots will retry asking for it")
    finally:
        adb(s, "forward", "--remove", f"tcp:{LOCAL_PORT}", check=False)

    if a.check:
        print(f"checking {a.check}:{DEFAULT_PORT} ...", AgentClient(a.check, token).ping())
    print("done")


if __name__ == "__main__":
    main()
