#!/usr/bin/env python3
"""Find tests whose coverage is identical to, or contained in, another test's.

Reads a coverage.py data file recorded with per-test contexts, for example:
    COVERAGE_CORE=ctrace python -m pytest --cov=SRC --cov-context=test tests/some_dir
or with `[run] dynamic_context = test_function` in the coverage configuration.

Record with COVERAGE_CORE=ctrace. The sys.monitoring core (coverage.py's
default on newer Pythons) records each line only for the first test that runs
it, so per-test data is silently wrong. This script refuses data whose
run_suite.py manifest shows another core, and data where no line is covered by
more than one test, which is that failure's fingerprint (under xdist, each
worker records first hits separately, so only the manifest check catches it).

Only the call phase of each test is compared ("|run" contexts from pytest-cov),
so shared fixture setup does not make tests look alike. Test files, conftest
files, and anything under a tests/ or test/ directory are left out by default,
because every test covers its own body and would otherwise look unique.

Reports, per scope (a directory by default):
  identical     tests from different test functions with exactly the same coverage
  subsumed      tests whose coverage is a strict subset of one other test's
  siblings      parametrised cases of one test that all hit the same code (trim or turn into a property)
  no-product    tests that execute no measured product code in their call phase

These are candidates, not verdicts. The same coverage does not mean the same
checks: compare the assertions, and confirm with mutation testing that a
candidate kills no mutant the other test misses, before proposing any change.
Never turn these numbers into a "percentage of removable tests".

Usage:
    coverage_redundancy.py DATA_FILE [--scope dir|module|all] [--nodeids FILE]
                           [--keep-test-files] [--max-group N] [--top N] [--json-out FILE]

Per-test contexts need coverage.py's default tracer on some Python versions;
check that the run recorded contexts (this script says so when it finds none).
Runs with contexts are slow: measure one directory at a time.

Standard library only (sqlite3); runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

TEST_FILE_RE = re.compile(r"(^|[/\\])(test_[^/\\]*\.py|[^/\\]*_test\.py|conftest\.py)$")
TEST_DIR_RE = re.compile(r"(^|[/\\])tests?[/\\]")


def popcount(x: int) -> int:
    return bin(x).count("1")


def family(nodeid: str) -> str:
    return nodeid.split("[", 1)[0]


def scope_of(nodeid: str, scope: str) -> str:
    path = nodeid.split("::", 1)[0]
    if scope == "all":
        return "(all)"
    if scope == "module":
        return path
    return str(Path(path).parent)


def load(data_file: Path, keep_test_files: bool) -> tuple[dict[str, int], dict]:
    con = sqlite3.connect(f"file:{data_file}?mode=ro", uri=True)
    meta = dict(con.execute("select key, value from meta").fetchall())
    has_arcs = str(meta.get("has_arcs", "0")).lower() in ("1", "true")
    files = {fid: path for fid, path in con.execute("select id, path from file")}
    kept = {fid for fid, path in files.items() if keep_test_files or not (TEST_FILE_RE.search(path) or TEST_DIR_RE.search(path))}
    contexts = dict(con.execute("select id, context from context"))
    phased = any("|" in c for c in contexts.values())
    tests: dict[int, str] = {}
    for cid, name in contexts.items():
        if not name:
            continue
        if phased:
            nodeid, _, phase = name.rpartition("|")
            if phase in ("run", "call"):
                tests[cid] = nodeid
        else:
            tests[cid] = name
    masks: dict[str, int] = defaultdict(int)
    if has_arcs:
        index: dict[tuple, int] = {}
        for fid, cid, fromno, tono in con.execute("select file_id, context_id, fromno, tono from arc"):
            if cid in tests and fid in kept:
                bit = index.setdefault((fid, fromno, tono), len(index))
                masks[tests[cid]] |= 1 << bit
        units = len(index)
    else:
        widths: dict[int, int] = defaultdict(int)
        for fid, length in con.execute("select file_id, max(length(numbits)) from line_bits group by file_id"):
            widths[fid] = (length or 0) * 8
        offsets, total = {}, 0
        for fid in sorted(widths):
            offsets[fid] = total
            total += widths[fid]
        for fid, cid, numbits in con.execute("select file_id, context_id, numbits from line_bits"):
            if cid in tests and fid in kept:
                masks[tests[cid]] |= int.from_bytes(numbits, "little") << offsets[fid]
        units = total
    for nodeid in tests.values():
        masks.setdefault(nodeid, 0)
    info = {
        "has_arcs": has_arcs,
        "phased_contexts": phased,
        "contexts": len(contexts),
        "tests": len(tests),
        "files": len(files),
        "files_kept": len(kept),
        "coverage_units": units,
        "coverage_version": meta.get("version"),
    }
    con.close()
    return dict(masks), info


def analyse(masks: dict[str, int], scope: str, max_group: int) -> dict:
    scopes: dict[str, list[str]] = defaultdict(list)
    for nodeid in masks:
        scopes[scope_of(nodeid, scope)].append(nodeid)
    identical, siblings, subsumed, skipped_scopes = [], [], [], []
    for key, members in scopes.items():
        by_mask: dict[int, list[str]] = defaultdict(list)
        for nodeid in members:
            if masks[nodeid]:
                by_mask[masks[nodeid]].append(nodeid)
        for mask, group in by_mask.items():
            if len(group) < 2:
                continue
            families = defaultdict(list)
            for nodeid in group:
                families[family(nodeid)].append(nodeid)
            if len(families) >= 2:
                shown = sorted(fam if len(cases) == 1 and cases[0] == fam else f"{fam}[{len(cases)} cases]" for fam, cases in families.items())
                identical.append({"scope": key, "units": popcount(mask), "tests": shown, "families": len(families)})
            for fam, cases in families.items():
                if len(cases) >= 3:
                    siblings.append({"scope": key, "test": fam, "cases": len(cases), "units": popcount(mask)})
        nonzero = sorted((n for n in members if masks[n]), key=lambda n: popcount(masks[n]))
        if len(nonzero) > max_group:
            skipped_scopes.append({"scope": key, "tests": len(nonzero)})
            continue
        sizes = {n: popcount(masks[n]) for n in nonzero}
        for i, a in enumerate(nonzero):
            ma = masks[a]
            for b in reversed(nonzero[i + 1 :]):
                if sizes[b] <= sizes[a]:
                    break
                if family(b) != family(a) and masks[b] & ma == ma:
                    subsumed.append({"scope": key, "test": a, "units": sizes[a], "contained_in": b, "container_units": sizes[b]})
                    break
    identical.sort(key=lambda g: (-len(g["tests"]), -g["units"]))
    siblings.sort(key=lambda s: -s["cases"])
    subsumed.sort(key=lambda s: (s["units"] / max(1, s["container_units"]), s["test"]))
    return {"identical": identical, "siblings": siblings, "subsumed": subsumed, "scopes_too_large_for_subset_check": skipped_scopes}


def write_out(path_text: str, text: str) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("data_file", help="coverage.py data file (.coverage) recorded with per-test contexts")
    parser.add_argument("--scope", choices=("dir", "module", "all"), default="dir", help="compare tests only within this scope (default dir)")
    parser.add_argument("--nodeids", help="`pytest --collect-only -q` output for the same selection that was measured, to list tests with no recorded coverage")
    parser.add_argument("--keep-test-files", action="store_true", help="include test files and tests/ directories in the comparison")
    parser.add_argument("--max-group", type=int, default=3000, help="skip the subset check in scopes larger than this (default 3000)")
    parser.add_argument("--trust-core", action="store_true", help="accept data whose run manifest does not show COVERAGE_CORE=ctrace")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    manifest_path = Path(args.data_file).resolve().parent / "manifest.json"
    if manifest_path.is_file() and not args.trust_core:
        try:
            core = (json.loads(manifest_path.read_text()).get("env") or {}).get("COVERAGE_CORE")
        except ValueError:
            core = "unknown"
        if core != "ctrace":
            print(
                f"refused: the run that wrote this data used COVERAGE_CORE={core or 'default'}. Per-test contexts need the C tracer: "
                "re-record with run_suite.py --env COVERAGE_CORE=ctrace, or pass --trust-core if the coverage configuration sets core = \"ctrace\""
            )
            return 2
    masks, info = load(Path(args.data_file), args.keep_test_files)
    if not info["tests"]:
        print("no per-test contexts in this data file; record it with --cov-context=test or dynamic_context = test_function")
        return 1
    union, total = 0, 0
    for mask in masks.values():
        union |= mask
        total += popcount(mask)
    if sum(1 for m in masks.values() if m) >= 5 and total == popcount(union):
        print(
            "refused: no line is covered by more than one test, so each line was recorded only once. "
            "This is what the sys.monitoring core does with contexts. Re-record with COVERAGE_CORE=ctrace."
        )
        return 2
    result = analyse(masks, args.scope, args.max_group)
    no_product = sorted(n for n, m in masks.items() if not m)
    if args.nodeids:
        known = set(masks)
        for line in Path(args.nodeids).read_text(errors="replace").splitlines():
            line = line.strip()
            if "::" in line and not line.startswith(("=", "<")) and line not in known:
                no_product.append(line)
    result["no_product"] = sorted(set(no_product))
    result["info"] = info

    print(
        f"tests with contexts: {info['tests']}   files kept: {info['files_kept']} of {info['files']}   "
        f"measure: {'arcs' if info['has_arcs'] else 'lines'}   scope: {args.scope}"
    )
    print(f"identical-coverage groups across different tests: {len(result['identical'])} ({sum(g['families'] for g in result['identical'])} test functions)")
    for g in result["identical"][: args.top]:
        print(f"  {len(g['tests'])} tests, {g['units']} units: {', '.join(g['tests'][:3])}{' …' if len(g['tests']) > 3 else ''}")
    print(f"tests whose coverage is contained in another test's: {len(result['subsumed'])}")
    for s in result["subsumed"][: args.top]:
        print(f"  {s['test']} ({s['units']}) inside {s['contained_in']} ({s['container_units']})")
    print(f"parametrised tests whose cases all hit identical code: {len(result['siblings'])}")
    for s in result["siblings"][: min(args.top, 5)]:
        print(f"  {s['test']}: {s['cases']} cases, {s['units']} units each")
    print(f"tests that execute no measured product code: {len(result['no_product'])}")
    for n in result["no_product"][: min(args.top, 5)]:
        print(f"  {n}")
    if result["scopes_too_large_for_subset_check"]:
        print(f"note: subset check skipped in {len(result['scopes_too_large_for_subset_check'])} large scopes; use --scope module or raise --max-group")
    print("caveat: candidates only. Same coverage is not the same checks. Compare assertions and confirm with mutation testing.")
    if args.json_out:
        write_out(args.json_out, json.dumps(result, indent=2))
        print(f"json: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
