"""Build agent/ into a signed APK with the plain Android SDK tools (no Gradle).

Usage: python scripts/build_agent.py   ->  agent/build/droidpilot-agent.apk

Needs ANDROID_HOME (or the default SDK path) with one build-tools and one
platform installed, and a JDK on PATH (javac, keytool). The signing key is
created on first run in agent/build/agent.keystore and reused afterwards;
keep it, or updates must be installed after uninstalling the old APK.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "agent"
OUT = ROOT / "build"
WIN = os.name == "nt"


def sdk_path() -> Path:
    for env in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(env):
            return Path(os.environ[env])
    return Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"


def newest(d: Path) -> Path:
    items = sorted(d.iterdir(), key=lambda p: [int(x) if x.isdigit() else 0 for x in p.name.replace("-", ".").split(".")])
    if not items:
        sys.exit(f"nothing installed in {d}")
    return items[-1]


def tool(bt: Path, name: str) -> str:
    for suffix in ((".exe", ".bat") if WIN else ("",)):
        if (bt / (name + suffix)).exists():
            return str(bt / (name + suffix))
    sys.exit(f"{name} not found in {bt}")


def run(*cmd: str) -> None:
    print("+", " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd)))
    subprocess.run(cmd, check=True)


def main() -> None:
    sdk = sdk_path()
    bt = newest(sdk / "build-tools")
    android_jar = newest(sdk / "platforms") / "android.jar"
    if OUT.exists():
        for p in OUT.iterdir():
            if p.name != "agent.keystore":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(exist_ok=True)
    (OUT / "res").mkdir()
    (OUT / "classes").mkdir()

    # 1. Resources and manifest.
    run(tool(bt, "aapt2"), "compile", "--dir", str(ROOT / "res"), "-o", str(OUT / "res.zip"))
    run(tool(bt, "aapt2"), "link", "-I", str(android_jar), "--manifest", str(ROOT / "AndroidManifest.xml"),
        "-o", str(OUT / "base.apk"), "--java", str(OUT / "gen"), str(OUT / "res.zip"))

    # 2. Java -> class files -> dex.
    sources = [str(p) for p in (ROOT / "src").rglob("*.java")] + [str(p) for p in (OUT / "gen").rglob("*.java")]
    run("javac", "-source", "8", "-target", "8", "-nowarn", "-Xlint:-options", "-encoding", "UTF-8",
        # core-lambda-stubs provides LambdaMetafactory, which android.jar lacks; d8 desugars lambdas.
        "-bootclasspath", os.pathsep.join([str(android_jar), str(bt / "core-lambda-stubs.jar")]), "-d", str(OUT / "classes"), *sources)
    classes = [str(p) for p in (OUT / "classes").rglob("*.class")]
    run(tool(bt, "d8"), "--release", "--min-api", "24", "--lib", str(android_jar), "--output", str(OUT), *classes)

    # 3. Add the dex, align, sign.
    shutil.copy(OUT / "base.apk", OUT / "unsigned.apk")
    with zipfile.ZipFile(OUT / "unsigned.apk", "a") as z:
        z.write(OUT / "classes.dex", "classes.dex")
    run(tool(bt, "zipalign"), "-f", "4", str(OUT / "unsigned.apk"), str(OUT / "aligned.apk"))
    keystore = OUT / "agent.keystore"
    if not keystore.exists():
        run("keytool", "-genkeypair", "-keystore", str(keystore), "-storepass", "droidpilot", "-keypass", "droidpilot",
            "-alias", "agent", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-dname", "CN=droidpilot agent")
    apk = OUT / "droidpilot-agent.apk"
    run(tool(bt, "apksigner"), "sign", "--ks", str(keystore), "--ks-pass", "pass:droidpilot",
        "--out", str(apk), str(OUT / "aligned.apk"))
    print(f"built {apk} ({apk.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
