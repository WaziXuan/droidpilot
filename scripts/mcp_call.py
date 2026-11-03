"""Drive the droidpilot MCP server over stdio, the same way an agent client does.

Usage:
  python scripts/mcp_call.py                        # list tools
  python scripts/mcp_call.py observe                # call a tool with no args
  python scripts/mcp_call.py tap target=e5          # key=value args (JSON values allowed)
  python scripts/mcp_call.py --script steps.jsonl   # one {"tool": ..., "args": {...}} per line

Prints each result's text, saves images to shots/, and reports wall time per call.
"""
import asyncio
import base64
import json
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "shots"


def parse_args(pairs):
    args = {}
    for p in pairs:
        k, _, v = p.partition("=")
        try:
            args[k] = json.loads(v)
        except json.JSONDecodeError:
            args[k] = v
    return args


async def run(calls):
    params = StdioServerParameters(command=sys.executable, args=["-m", "droidpilot"], cwd=str(ROOT))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if not calls:
                for t in (await session.list_tools()).tools:
                    print(f"{t.name}: {t.description.splitlines()[0] if t.description else ''}")
                return
            for i, (tool, args) in enumerate(calls):
                t = time.perf_counter()
                res = await session.call_tool(tool, args)
                ms = (time.perf_counter() - t) * 1000
                print(f"=== {tool} {json.dumps(args, ensure_ascii=False)}  [{ms:.0f} ms]{'  ERROR' if res.is_error else ''}")
                for c in res.content:
                    if c.type == "text":
                        print(c.text)
                    elif c.type == "image":
                        SHOTS.mkdir(exist_ok=True)
                        path = SHOTS / f"{int(time.time())}_{i}_{tool}.jpg"
                        path.write_bytes(base64.b64decode(c.data))
                        print(f"<image saved to {path}>")


def main():
    argv = sys.argv[1:]
    if argv[:1] == ["--script"]:
        lines = Path(argv[1]).read_text(encoding="utf-8").splitlines()
        calls = [(s["tool"], s.get("args", {})) for s in map(json.loads, filter(str.strip, lines))]
    elif argv:
        calls = [(argv[0], parse_args(argv[1:]))]
    else:
        calls = []
    asyncio.run(run(calls))


if __name__ == "__main__":
    main()
