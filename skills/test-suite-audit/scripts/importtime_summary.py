#!/usr/bin/env python3
"""Rank the slowest imports from `python -X importtime` output.

Collection time in a large suite is often import time: every test module and
conftest file is imported, with everything they import at module level. This
script turns the raw importtime log into three short rankings:

  * top-level imports by cumulative time (what each import costs, children included);
  * root packages by total self time (for example "django", "pandas", "boto3");
  * single modules by self time.

Usage:
    python -X importtime -m pytest --collect-only -q -s 2> importtime.log >/dev/null
    importtime_summary.py importtime.log [--top N] [--json-out FILE]

Keep -s: without it, pytest captures stderr during collection, and the log
loses every import that conftest files and test modules make.

Import times are measured on one run and include cold-cache effects on the first
run. Take the ranking from a second, warm run, and treat absolute numbers as
approximate: -X importtime adds some overhead of its own.

Standard library only; runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

LINE_RE = re.compile(r"^import time:\s+(\d+) \|\s+(\d+) \|( *)(\S.*?)\s*$")


def parse(path: Path) -> list[dict]:
    entries = []
    for line in path.read_text(errors="replace").splitlines():
        m = LINE_RE.match(line)
        if m:
            entries.append({"self_us": int(m.group(1)), "cumulative_us": int(m.group(2)), "depth": (len(m.group(3)) - 1) // 2, "module": m.group(4)})
    return entries


def write_out(path_text: str, text: str) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("log", help="stderr captured from a `python -X importtime ...` run")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    entries = parse(Path(args.log))
    if not entries:
        print("no importtime lines found; capture stderr of `python -X importtime ...`")
        return 1
    total_s = sum(e["self_us"] for e in entries) / 1e6
    top_level = sorted((e for e in entries if e["depth"] == 0), key=lambda e: -e["cumulative_us"])
    by_root: dict[str, int] = defaultdict(int)
    for e in entries:
        by_root[e["module"].split(".", 1)[0]] += e["self_us"]
    roots = sorted(by_root.items(), key=lambda kv: -kv[1])
    by_self = sorted(entries, key=lambda e: -e["self_us"])

    print(f"modules imported: {len(entries)}   total import time: {total_s:.2f}s")
    print(f"top-level imports by cumulative time:")
    for e in top_level[: args.top]:
        print(f"  {e['cumulative_us'] / 1e6:>8.3f}s  {e['module']}")
    print(f"root packages by self time:")
    for name, us in roots[: min(args.top, 12)]:
        print(f"  {us / 1e6:>8.3f}s  {100 * us / 1e6 / total_s:>5.1f}%  {name}")
    print(f"single modules by self time:")
    for e in by_self[: min(args.top, 8)]:
        print(f"  {e['self_us'] / 1e6:>8.3f}s  {e['module']}")
    if args.json_out:
        write_out(args.json_out, 
            json.dumps(
                {
                    "total_seconds": round(total_s, 3),
                    "modules": len(entries),
                    "top_level": [{"module": e["module"], "cumulative_seconds": e["cumulative_us"] / 1e6} for e in top_level[:100]],
                    "root_packages": [{"package": n, "self_seconds": us / 1e6} for n, us in roots[:100]],
                },
                indent=2,
            )
        )
        print(f"json: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
