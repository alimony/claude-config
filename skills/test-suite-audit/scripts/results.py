#!/usr/bin/env python3
"""Summarise, compare, and cross-check test results from any runner.

Reads, in any mix:
  * JUnit XML from any language (pytest xunit1 and xunit2, xdist-merged, Django's
    XML runner, jest-junit, gotestsum, Surefire, and others);
  * pytest-reportlog JSON Lines (a truncated last line is tolerated);
  * pytest-json-report JSON;
  * pytest-split duration files (a flat JSON object of test ID to seconds);
  * `--durations` blocks in plain text output, such as run_suite.py's output.log;
  * per-test outcome lines of `pytest -v` (also xdist's and GitHub Actions' forms),
    for CI logs when the job uploads no reports; they give outcomes and reruns, not times.

Usage:
    results.py summary FILE... [--nodeids FILE] [--top N] [--depth N] [--repeats-are-reruns] [--json-out FILE]
    results.py flips FILE... [--same-commit] [--nodeids FILE] [--repeats-are-reruns] [--json-out FILE]
    results.py diff --before FILE... --after FILE... [--nodeids FILE] [--repeats-are-reruns] [--json-out FILE]
    results.py extrapolate SAMPLE_RUN --plan SAMPLE.json [--json-out FILE]
    results.py fixtures RUN_DIR [--top N] [--json-out FILE]

`summary` treats all its files as one run, such as the shards of one CI run.
`flips` treats each file as a separate run of the same suite. A test counts as
flaky only when it both failed and passed at the same commit: either every run
folder has a manifest with the same commit, or you pass --same-commit.
`diff` compares the median of the --before runs with the median of the --after
runs, and reports tests that disappeared, appeared, or changed outcome. It also
reads `--collect-only -q` output, to check that a change kept the collected set.
`extrapolate` estimates the whole suite's serial test time from a run of the
file sample that `run_suite.py sample` picked, with a bootstrap 90% range.

A run folder with both junit.xml and output.log is read as one run: JUnit gives
outcomes and totals, and a `--durations=0 --durations-min=0` block in the log
adds setup, call, and teardown times.

When a file sits in a run_suite.py run folder, its manifest.json supplies the
commit, wall time, workers, and instrumentation. Timing from instrumented runs
(coverage, mutation testing, profilers) is flagged and must not back timing
claims.

pytest-rerunfailures writes every attempt as a separate, passing <testcase>,
and deliberate repeats and ID collisions look the same. So a test ID repeated
within one JUnit file counts as a repeat, and as a rerun only when the run's
manifest says reruns were configured (--reruns in the command, PYTEST_ADDOPTS,
or the project's configuration) or when you pass --repeats-are-reruns, for
example for CI reports from a job that uses --reruns or @pytest.mark.flaky.

pytest's default JUnit family (xunit2) has no file attribute. Pass --nodeids
with the output of `pytest --collect-only -q` to map JUnit entries back to node
IDs, so results can be joined with other data.

Text output stays under about 60 lines. Use --json-out for everything.

Standard library only; runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

PHASES = ("setup", "call", "teardown")
FAIL_OUTCOMES = {"failed", "error"}
PASS_OUTCOMES = {"passed", "xfailed"}
DURATIONS_LINE_RE = re.compile(r"^\s*(?P<secs>[\d.]+)s\s+(?P<phase>setup|call|teardown)\s+(?P<id>\S.*?)\s*$")
DURATIONS_HEADER_RE = re.compile(r"=+ slowest (\d+ )?durations =+")
# Django's runner (5.0+ on Python 3.12+): "0.280s     test_name (package.module.Class.test_name)".
DJANGO_DURATION_RE = re.compile(r"^\s*(?P<secs>[\d.]+)s\s+(?P<name>\S+) \((?P<id>[\w.]+)\)\s*$")
UNITTEST_RAN_RE = re.compile(r"^Ran (\d+) tests? in ")
# The last line of `--collect-only -q`; a test run's "collected N items" header must not match.
COLLECTED_SUMMARY_RE = re.compile(r"^(?:=+ )?(?:(?:\d+/)?\d+ tests? collected|no tests collected)\b.* in [\d.]+s")
NODEID_LINE_RE = re.compile(r"^[\w./\\-]+\.py::\S")
# Per-test outcome lines of `pytest -v` (serial: ID first; xdist and -rA summaries: outcome first).
VERBOSE_OUTCOMES = {"PASSED": "passed", "FAILED": "failed", "ERROR": "error", "SKIPPED": "skipped", "XFAIL": "xfailed", "XPASS": "xpassed", "RERUN": "rerun"}
_WORDS = "|".join(VERBOSE_OUTCOMES)
VERBOSE_ID_FIRST_RE = re.compile(rf"^(?P<id>[\w./\\-]+\.py::.+?) (?P<outcome>{_WORDS})(?=\s|$)")
VERBOSE_OUTCOME_FIRST_RE = re.compile(rf"^(?:\[gw\d+\]\s+)?(?:\[\s*\d+%\]\s+)?(?P<outcome>{_WORDS}) (?P<id>[\w./\\-]+\.py::\S.*?)(?: - .*)?\s*$")
CI_TIMESTAMP_RE = re.compile(r"^\d{4}-\d\d-\d\dT[\d:.]+Z\s")  # GitHub Actions log lines
VERBOSE_SEVERITY = {"passed": 0, "xpassed": 0, "skipped": 1, "xfailed": 2, "failed": 3, "error": 4}


class Test:
    __slots__ = ("id", "outcome", "setup", "call", "teardown", "total", "reruns", "repeats", "file", "worker", "start", "stop")
    id: str
    outcome: str
    setup: float | None
    call: float | None
    teardown: float | None
    total: float
    reruns: int
    repeats: int
    file: str | None
    worker: str | None
    start: float | None
    stop: float | None

    def __init__(self, test_id: str, file: str | None = None):
        self.id = test_id
        self.outcome = "unknown"
        self.setup = self.call = self.teardown = None
        self.total = 0.0
        self.reruns = 0
        self.repeats = 0
        self.file = file
        self.worker = self.start = self.stop = None

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__slots__ if getattr(self, k) is not None}


class Run:
    def __init__(self, source: str, fmt: str):
        self.sources = [source]
        self.formats = {fmt}
        self.tests: dict[str, Test] = {}
        self.manifest: dict | None = None
        self.partial = fmt == "durations-text"
        self.warnings: list[str] = []

    def merge(self, other: "Run") -> None:
        self.sources += other.sources
        self.formats |= other.formats
        self.partial = self.partial or other.partial
        self.warnings += other.warnings
        for tid, test in other.tests.items():
            if tid in self.tests:
                self.warnings.append(f"duplicate test ID across inputs: {tid}")
            self.tests[tid] = test
        if self.manifest is None:
            self.manifest = other.manifest


# --------------------------------------------------------------------------- IDs


def classname_key(nodeid: str) -> tuple[str, str] | None:
    """Return the (classname, name) pair pytest's JUnit writer would emit for a node ID."""
    parts = nodeid.split("::")
    if len(parts) < 2 or not parts[0].endswith(".py"):
        return None
    module = parts[0][:-3].replace("/", ".").replace("\\", ".")
    return ".".join([module, *parts[1:-1]]), parts[-1]


def load_nodeid_map(path: str | None) -> dict[tuple[str, str], str]:
    if not path:
        return {}
    mapping = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        line = line.strip()
        if "::" not in line or line.startswith(("=", "<")):
            continue
        key = classname_key(line)
        if key:
            mapping[key] = line
    return mapping


def junit_id(classname: str, name: str, file: str | None, nodeid_map: dict, pytest_report: bool = False) -> tuple[str, str | None]:
    mapped = nodeid_map.get((classname, name))
    if mapped:
        return mapped, mapped.split("::", 1)[0]
    if file and file.endswith(".py"):
        module = file[:-3].replace("/", ".").replace("\\", ".")
        if classname == module or classname.startswith(module + "."):
            rest = classname[len(module) + 1 :]
            return "::".join([file, *[p for p in rest.split(".") if p], name]), file
        # An inherited test method: `file` names the base class's file, so derive the module
        # from the class name instead (modules are lower case, classes capitalised by convention).
    parts = classname.split(".") if classname else []
    split = next((i for i, part in enumerate(parts) if part[:1].isupper()), len(parts))
    if parts and split > 0 and (pytest_report or (file or "").endswith(".py")):
        module_path = "/".join(parts[:split]) + ".py"
        return "::".join([module_path, *parts[split:], name]), module_path
    return (f"{classname}::{name}" if classname else name), file


# --------------------------------------------------------------------------- readers


SEVERITY = {"passed": 0, "skipped": 1, "xfailed": 2, "failed": 3, "error": 4}


def read_junit(path: Path, nodeid_map: dict) -> Run:
    run = Run(str(path), "junit")
    root = None
    pytest_report = False
    try:
        for event, elem in ET.iterparse(str(path), events=("start", "end")):
            if event == "start":
                root = root or elem.tag
                if elem.tag == "testsuite" and elem.get("name") == "pytest":
                    pytest_report = True
                continue
            if elem.tag != "testcase":
                continue
            tid, file = junit_id(elem.get("classname", ""), elem.get("name", ""), elem.get("file"), nodeid_map, pytest_report)
            test = run.tests.get(tid)
            if test is None:
                test = Test(tid, file)
            else:
                # A repeated ID within one report: pytest-rerunfailures writes each attempt as its own
                # passing <testcase>, but deliberate repeats and ID collisions look the same.
                test.repeats += 1
            try:
                test.total = float(elem.get("time") or 0)
            except ValueError:
                test.total = 0.0
            outcome = "passed"
            for child in elem:
                tag = child.tag.lower()
                found = None
                if tag == "failure":
                    found = "failed"
                elif tag == "error":
                    found = "error"
                elif tag == "skipped":
                    text = f"{child.get('type', '')} {child.get('message', '')}".lower()
                    found = "xfailed" if "xfail" in text else "skipped"
                elif "rerun" in tag or "flaky" in tag:
                    test.reruns += 1
                if found and SEVERITY[found] > SEVERITY[outcome]:
                    outcome = found
            test.outcome = outcome
            run.tests[tid] = test
            elem.clear()
    except ET.ParseError as exc:
        run.partial = True
        run.warnings.append(f"{path}: XML parse error ({exc}); results are partial")
    if not run.tests:
        run.warnings.append(f"{path}: no <testcase> elements (root element <{root}>); this is not JUnit XML, or the run wrote no results")
    return run


def outcome_from_reports(reports: list[dict]) -> str:
    outcome = "passed"
    for rep in reports:
        when, out = rep.get("when"), rep.get("outcome")
        xfail = "wasxfail" in rep
        if out == "failed":
            return "failed" if when == "call" else "error"
        if out == "skipped":
            if xfail:
                return "xfailed"
            if outcome == "passed":
                outcome = "skipped"
        if out == "passed" and when == "call" and xfail:
            outcome = "xpassed"
    return outcome


def read_reportlog(path: Path) -> Run:
    run = Run(str(path), "reportlog")
    per_test: dict[str, list[dict]] = defaultdict(list)
    lines = path.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            if i == len(lines) - 1:
                run.partial = True
                run.warnings.append(f"{path}: last line truncated; the run was probably stopped")
                continue
            run.warnings.append(f"{path}: skipped unreadable line {i + 1}")
            continue
        if rec.get("$report_type") == "TestReport" and rec.get("nodeid"):
            per_test[rec["nodeid"]].append(rec)
    for nodeid, reports in per_test.items():
        test = Test(nodeid, nodeid.split("::", 1)[0])
        final = [r for r in reports if r.get("outcome") != "rerun"]
        test.reruns = sum(1 for r in reports if r.get("outcome") == "rerun")
        for phase in PHASES:
            durations = [float(r.get("duration") or 0) for r in final if r.get("when") == phase]
            if durations:
                setattr(test, phase, round(sum(durations), 6))
        test.total = sum(getattr(test, p) or 0 for p in PHASES)
        test.outcome = outcome_from_reports(final)
        # The timing plugin writes "worker"; pytest-reportlog under xdist writes "worker_id".
        test.worker = next((r.get("worker") or r.get("worker_id") for r in final if r.get("worker") or r.get("worker_id")), None)
        starts = [r["start"] for r in final if isinstance(r.get("start"), (int, float))]
        stops = [r["stop"] for r in final if isinstance(r.get("stop"), (int, float))]
        test.start, test.stop = (min(starts) if starts else None), (max(stops) if stops else None)
        run.tests[nodeid] = test
    return run


def read_json_report(path: Path, data: dict) -> Run:
    run = Run(str(path), "json-report")
    for rec in data.get("tests", []):
        nodeid = rec.get("nodeid")
        if not nodeid:
            continue
        test = Test(nodeid, nodeid.split("::", 1)[0])
        for phase in PHASES:
            part = rec.get(phase)
            if isinstance(part, dict) and "duration" in part:
                setattr(test, phase, float(part["duration"] or 0))
        test.total = sum(getattr(test, p) or 0 for p in PHASES)
        outcome = rec.get("outcome", "unknown")
        test.outcome = "error" if outcome == "error" else outcome
        run.tests[nodeid] = test
    return run


def read_durations_map(path: Path, data: dict) -> Run:
    run = Run(str(path), "durations-file")
    for nodeid, secs in data.items():
        test = Test(nodeid, nodeid.split("::", 1)[0] if "::" in nodeid else None)
        test.total = float(secs)
        run.tests[nodeid] = test
    run.warnings.append(f"{path}: duration file has no outcomes, and it may be stale")
    return run


def read_durations_text(path: Path) -> Run:
    """Parse pytest's --durations block. It is complete only with --durations=0 --durations-min=0."""
    run = Run(str(path), "durations-text")
    header_all = hidden = False
    for line in path.read_text(errors="replace").splitlines():
        text = re.sub(r"\x1b\[[0-9;]*m", "", line)
        header = DURATIONS_HEADER_RE.search(text)
        if header:
            header_all = header.group(1) is None
            continue
        if "durations < " in text and "hidden" in text:
            hidden = True
        m = DURATIONS_LINE_RE.match(text)
        if not m:
            continue
        test = run.tests.get(m.group("id")) or Test(m.group("id"), m.group("id").split("::", 1)[0])
        setattr(test, m.group("phase"), float(m.group("secs")))
        test.total = sum(getattr(test, p) or 0 for p in PHASES)
        run.tests[test.id] = test
    if read_verbose_outcomes(path, run):
        run.formats.add("verbose-log")
    if not run.tests:
        read_django_durations(path, run)
        if not run.tests:
            read_collect_only(path, run)
        return run
    if "durations-text" in run.formats and not any(t.total for t in run.tests.values()):
        run.formats.discard("durations-text")
        return run  # outcomes only, from -v lines
    run.partial = not (header_all and not hidden)
    if run.tests and run.partial:
        run.warnings.append(f"{path}: the --durations block lists only the slowest entries; use --durations=0 --durations-min=0 for complete data")
    return run


def read_verbose_outcomes(path: Path, run: Run) -> bool:
    """Outcomes from `pytest -v` lines, plain or from CI logs. Adds tests without times; True when it read any.

    A log without a single PASSED line is not verbose: its short summary names only failures, and
    reading those alone would leave every other outcome unknown.
    """
    matches = []
    for line in path.read_text(errors="replace").splitlines():
        text = CI_TIMESTAMP_RE.sub("", re.sub(r"\x1b\[[0-9;]*m", "", line)).rstrip()
        m = VERBOSE_ID_FIRST_RE.match(text) or VERBOSE_OUTCOME_FIRST_RE.match(text)
        if m:
            matches.append(m)
    if not any(m.group("outcome") == "PASSED" for m in matches):
        return False
    for m in matches:
        test_id = re.sub(r" <- \S+$", "", m.group("id").strip())  # "<- base.py" marks an inherited test
        test = run.tests.get(test_id) or Test(test_id, test_id.split("::", 1)[0])
        run.tests[test_id] = test
        outcome = VERBOSE_OUTCOMES[m.group("outcome")]
        if outcome == "rerun":
            test.reruns += 1
        elif test.outcome == "unknown" or VERBOSE_SEVERITY.get(outcome, 0) > VERBOSE_SEVERITY.get(test.outcome, 0):
            test.outcome = outcome
    return True


def read_collect_only(path: Path, run: Run) -> None:
    """`pytest --collect-only -q` output: node IDs with outcome "collected", so diff can compare test sets."""
    lines = [re.sub(r"\x1b\[[0-9;]*m", "", line).rstrip() for line in path.read_text(errors="replace").splitlines()]
    if not any(COLLECTED_SUMMARY_RE.search(line) for line in lines):
        return
    for line in lines:
        if NODEID_LINE_RE.match(line):
            test = Test(line, line.split("::", 1)[0])
            test.outcome = "collected"
            run.tests[line] = test
    if run.tests:
        run.formats = {"collect-only"}


def read_django_durations(path: Path, run: Run) -> None:
    """Django's --durations block. It is complete only when it lists every test that ran (--durations 0)."""
    ran = None
    for line in path.read_text(errors="replace").splitlines():
        if (m := UNITTEST_RAN_RE.match(line)):
            ran = int(m.group(1))
        m = DJANGO_DURATION_RE.match(line)
        if not m or m.group("id").rsplit(".", 1)[-1] != m.group("name"):
            continue
        dotted_id = m.group("id")
        module = dotted_id.rsplit(".", 2)[0] if dotted_id.count(".") >= 2 else dotted_id
        test = Test(dotted_id, module.replace(".", "/") + ".py")
        test.total = test.call = float(m.group("secs"))
        run.tests[dotted_id] = test
    if run.tests:
        run.formats = {"django-durations"}
        run.partial = ran is None or len(run.tests) < ran
        if run.partial:
            run.warnings.append(
                f"{path}: Django's --durations block lists {len(run.tests)} of {ran or '?'} tests; use --durations 0 -v 2 "
                "(Django hides the fastest tests below verbosity 2)"
            )


def enrich_with_phases(run: Run, log: Path) -> None:
    """Add setup, call, and teardown times from a --durations block to JUnit results of the same run."""
    phases = read_durations_text(log)
    matched = 0
    for tid, test in run.tests.items():
        source = phases.tests.get(tid)
        if source:
            test.setup, test.call, test.teardown = source.setup, source.call, source.teardown
            matched += 1
    if matched:
        run.formats.add("durations-text")
        if phases.partial:
            run.warnings.append(f"{log}: phase times cover only the slowest entries")


def attach_manifest(run: Run, path: Path) -> None:
    for candidate in (path.parent / "manifest.json", path.parent.parent / "manifest.json"):
        if candidate.is_file():
            try:
                run.manifest = json.loads(candidate.read_text())
            except ValueError:
                pass
            return


def load(path_text: str, nodeid_map: dict, repeats_are_reruns: bool = False) -> Run:
    path = Path(path_text)
    folder_log = None
    if path.is_dir():
        for name in ("timing.jsonl", "reportlog.jsonl", "report.json", "junit.xml", "output.log"):
            if (path / name).is_file():
                if name == "junit.xml" and (path / "output.log").is_file():
                    folder_log = path / "output.log"
                path = path / name
                break
        else:
            raise SystemExit(f"{path}: no junit.xml, reportlog.jsonl, report.json, or output.log in this folder")
    if not path.is_file():
        raise SystemExit(f"{path}: not found")
    head = path.read_bytes()[:2048].lstrip()
    if head.startswith(b"<"):
        run = read_junit(path, nodeid_map)
    elif head.startswith(b"{") and path.suffix != ".jsonl":
        try:
            data = json.loads(path.read_text(errors="replace"))
        except ValueError:
            run = read_reportlog(path)
        else:
            if isinstance(data, dict) and "tests" in data and isinstance(data["tests"], list):
                run = read_json_report(path, data)
            elif isinstance(data, dict) and data and all(isinstance(v, (int, float)) for v in data.values()):
                run = read_durations_map(path, data)
            else:
                raise SystemExit(f"{path}: JSON in an unknown shape")
    elif head.startswith(b"{"):
        run = read_reportlog(path)
    else:
        run = read_durations_text(path)
        if not run.tests:
            raise SystemExit(f"{path}: no recognised test results")
    if folder_log is not None:
        enrich_with_phases(run, folder_log)
    attach_manifest(run, path)
    manifest = run.manifest or {}
    asked_reruns = repeats_are_reruns or manifest.get("reruns_configured") or (
        "--reruns" in " ".join(manifest.get("command", [])) + " " + str((manifest.get("env") or {}).get("PYTEST_ADDOPTS", ""))
    )
    if asked_reruns:
        for test in run.tests.values():
            test.reruns += test.repeats
            test.repeats = 0
    zero = sum(1 for t in run.tests.values() if t.total == 0)
    if len(run.tests) > 10 and zero > len(run.tests) / 2 and run.formats & {"junit"}:
        run.warnings.append(
            f"{path}: {zero} of {len(run.tests)} tests report 0 s; the reporter may not record times "
            "(Django's XML runner under --parallel does this); use the runner's --durations output instead"
        )
    if run.manifest and run.manifest.get("instrumented", "none") not in ("none", None):
        run.warnings.append(
            f"{path}: run was instrumented ({run.manifest['instrumented']}); do not use its timings for timing claims"
        )
    return run


# --------------------------------------------------------------------------- stats


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, max(0, int(round(q * (len(sorted_values) - 1)))))
    return sorted_values[index]


def group_key(test: Test, depth: int, by: str) -> str:
    base = test.file or test.id.split("::", 1)[0]
    if by == "file":
        return base
    parts = re.split(r"[/\\]", base)
    return "/".join(parts[: max(1, min(depth, len(parts) - 1))]) if len(parts) > 1 else base


SESSION_TEARDOWN_MIN = 1.0  # seconds; below this, the last test keeps its teardown
GROUP_SHARE_MAX = 60.0  # percent; auto depth goes deeper while one directory holds more


def session_teardowns(tests: list[Test]) -> dict[str, float]:
    """The teardown of each worker's last test, which also runs the session's finalizers."""
    last: dict[str | None, Test] = {}
    for test in tests:  # insertion order is run order for serial reports
        earlier = last.get(test.worker)
        if earlier is None or (test.stop is not None and earlier.stop is not None and test.stop >= earlier.stop) or test.stop is None:
            last[test.worker] = test
    return {t.id: t.teardown for t in last.values() if (t.teardown or 0) >= SESSION_TEARDOWN_MIN}


def auto_depth(tests: list[Test], weight: dict[str, float], total: float) -> int:
    """The shallowest grouping depth, from 2, at which no directory holds over GROUP_SHARE_MAX percent."""
    depth = 2
    while depth < 8 and total:
        groups: dict[str, float] = defaultdict(float)
        for t in tests:
            groups[group_key(t, depth, "dir")] += weight[t.id]
        if max(groups.values(), default=0) * 100 / total <= GROUP_SHARE_MAX:
            break
        deeper: dict[str, float] = defaultdict(float)
        for t in tests:
            deeper[group_key(t, depth + 1, "dir")] += weight[t.id]
        if len(deeper) == len(groups):
            break  # no directory splits any further
        depth += 1
    return depth


def summarise(run: Run, top: int, depth: int | None) -> dict:
    tests = list(run.tests.values())
    # Each worker's session finalizers run in its last test's teardown: count them apart.
    session = session_teardowns(tests)
    weight = {t.id: t.total - (session.get(t.id) or 0) for t in tests}
    durations = sorted(weight.values())
    total = sum(t.total for t in tests)
    test_total = sum(durations)  # shares are of test time, without the session teardown
    outcomes: dict[str, int] = defaultdict(int)
    for t in tests:
        outcomes[t.outcome] += 1
    ranked = sorted(tests, key=lambda t: weight[t.id], reverse=True)
    if depth is None:
        depth = auto_depth(tests, weight, test_total)

    def share(fraction: float) -> float:
        n = max(1, int(len(ranked) * fraction)) if ranked else 0
        return round(100 * sum(weight[t.id] for t in ranked[:n]) / test_total, 1) if test_total else 0.0

    phases = {}
    if any(t.setup is not None for t in tests):
        for phase in PHASES:
            phases[phase] = round(sum(getattr(t, phase) or 0 for t in tests), 2)
    groups: dict[str, list[float]] = defaultdict(list)
    files: dict[str, list[float]] = defaultdict(list)
    for t in tests:
        groups[group_key(t, depth, "dir")].append(weight[t.id])
        files[group_key(t, depth, "file")].append(weight[t.id])

    def top_groups(source: dict[str, list[float]]) -> list[dict]:
        rows = [
            {"group": k, "tests": len(v), "seconds": round(sum(v), 2), "share": round(100 * sum(v) / test_total, 1) if test_total else 0}
            for k, v in source.items()
        ]
        return sorted(rows, key=lambda r: r["seconds"], reverse=True)[:top]

    manifest = run.manifest or {}
    result = {
        "sources": run.sources,
        "formats": sorted(run.formats),
        "partial": run.partial,
        "warnings": run.warnings,
        "tests": len(tests),
        "outcomes": dict(sorted(outcomes.items())),
        "sum_seconds": round(total, 2),
        "wall_seconds": manifest.get("wall_seconds"),
        "workers": manifest.get("workers"),
        "commit": manifest.get("commit"),
        "instrumented": manifest.get("instrumented"),
        "distribution": {
            "p50": round(percentile(durations, 0.50), 3),
            "p90": round(percentile(durations, 0.90), 3),
            "p95": round(percentile(durations, 0.95), 3),
            "p99": round(percentile(durations, 0.99), 3),
            "max": round(durations[-1], 3) if durations else 0,
        },
        "long_tail_share_percent": {"top_1": share(0.01), "top_5": share(0.05), "top_10": share(0.10)},
        "over_seconds": {str(s): sum(1 for d in durations if d > s) for s in (1, 5, 30)},
        "phases": phases,
        "slowest": [{"id": t.id, "seconds": round(weight[t.id], 3), "outcome": t.outcome} for t in ranked[:top]],
        "session_teardown": [{"last_test": tid, "seconds": round(sec, 3)} for tid, sec in sorted(session.items(), key=lambda kv: -kv[1])],
        "group_depth": depth,
        "slowest_setup": [
            {"id": t.id, "seconds": round(t.setup or 0, 3)}
            for t in sorted(tests, key=lambda t: t.setup or 0, reverse=True)[:top]
            if (t.setup or 0) > 0
        ],
        "slowest_teardown": [
            {"id": t.id, "seconds": round(t.teardown or 0, 3)}
            for t in sorted((t for t in tests if t.id not in session), key=lambda t: t.teardown or 0, reverse=True)[:top]
            if (t.teardown or 0) > 0
        ],
        "groups": top_groups(groups),
        "files": top_groups(files),
        "reruns": sorted(({"id": t.id, "reruns": t.reruns, "outcome": t.outcome} for t in tests if t.reruns), key=lambda r: -r["reruns"]),
        "repeats": sorted(({"id": t.id, "repeats": t.repeats, "outcome": t.outcome} for t in tests if t.repeats), key=lambda r: -r["repeats"]),
    }
    if result["wall_seconds"] and result["workers"]:
        result["parallel_efficiency"] = round(total / (result["wall_seconds"] * result["workers"]), 2)
    busy: dict[str, float] = defaultdict(float)
    finish: dict[str, float] = {}
    for t in tests:
        if t.worker:
            busy[t.worker] += t.total
            stop = t.stop
            if stop is not None:
                finish[t.worker] = max(finish.get(t.worker, stop), stop)
    if len(busy) >= 2 and not result["workers"] and result["wall_seconds"]:
        result["parallel_efficiency"] = round(total / (result["wall_seconds"] * len(busy)), 2)
    if len(busy) >= 2:
        mean = sum(busy.values()) / len(busy)
        result["workers_seen"] = {
            "busy_seconds": {w: round(s, 1) for w, s in sorted(busy.items())},
            "imbalance_max_over_mean": round(max(busy.values()) / mean, 2) if mean else None,
            "finish_spread_seconds": round(max(finish.values()) - min(finish.values()), 1) if len(finish) >= 2 else None,
        }
    return result


def print_summary(s: dict, top: int) -> None:
    print(f"inputs: {len(s['sources'])} ({', '.join(s['formats'])}){'  PARTIAL' if s['partial'] else ''}")
    print(f"tests: {s['tests']}   outcomes: " + ", ".join(f"{v} {k}" for k, v in s["outcomes"].items()))
    line = f"sum of test time: {s['sum_seconds']:.1f}s"
    if s.get("wall_seconds"):
        line += f"   wall: {s['wall_seconds']:.1f}s"
    if s.get("workers"):
        line += f"   workers: {s['workers']}"
    if "parallel_efficiency" in s:
        line += f"   efficiency: {s['parallel_efficiency']:.2f}"
    print(line)
    d = s["distribution"]
    if s["partial"]:
        print("partial input: only the listed tests are known, so the distribution and long-tail shares are not shown")
    else:
        print(f"per test: p50 {d['p50']}s  p90 {d['p90']}s  p95 {d['p95']}s  p99 {d['p99']}s  max {d['max']}s")
        lt = s["long_tail_share_percent"]
        print(f"long tail: slowest 1% = {lt['top_1']}% of time, 5% = {lt['top_5']}%, 10% = {lt['top_10']}%")
    o = s["over_seconds"]
    print(f"tests over 1s: {o['1']}, over 5s: {o['5']}, over 30s: {o['30']}")
    if s["phases"]:
        print("phases: " + ", ".join(f"{k} {v:.1f}s" for k, v in s["phases"].items()))
    shown = min(top, 10)
    print(f"slowest {shown}:")
    for row in s["slowest"][:shown]:
        print(f"  {row['seconds']:>9.3f}s  {row['outcome']:<8} {row['id']}")
    if s["slowest_setup"]:
        print("slowest setup (fixture cost):")
        for row in s["slowest_setup"][:5]:
            print(f"  {row['seconds']:>9.3f}s  {row['id']}")
    if s["phases"] and s["phases"].get("teardown", 0) > 0.2 * max(s["sum_seconds"], 1e-9) and s["slowest_teardown"]:
        print("slowest teardown (teardown is over 20% of test time):")
        for row in s["slowest_teardown"][:5]:
            print(f"  {row['seconds']:>9.3f}s  {row['id']}")
    if s.get("session_teardown"):
        seconds = sum(r["seconds"] for r in s["session_teardown"])
        print(f"session teardown: {seconds:.1f}s on {len(s['session_teardown'])} worker(s), in each one's last test; left out of the slowest list and shares")
    print(f"heaviest directories at depth {s['group_depth']} (top {min(top, 8)} of {len(s['groups'])}; the full lists are in --json-out):")
    for row in s["groups"][: min(top, 8)]:
        print(f"  {row['seconds']:>9.1f}s  {row['share']:>5.1f}%  {row['tests']:>6} tests  {row['group']}")
    if s.get("workers_seen"):
        ws = s["workers_seen"]
        print(
            f"workers: {len(ws['busy_seconds'])} seen, busiest/mean busy time {ws['imbalance_max_over_mean']}"
            + (f", last worker finished {ws['finish_spread_seconds']}s after the first" if ws["finish_spread_seconds"] is not None else "")
        )
    if s["reruns"]:
        print(f"tests with reruns: {len(s['reruns'])} (flaky at this commit if they finally passed)")
        for row in s["reruns"][:5]:
            print(f"  {row['reruns']} reruns, final {row['outcome']}: {row['id']}")
    if s["repeats"]:
        print(
            f"tests with repeated JUnit entries: {len(s['repeats'])}: pytest-rerunfailures reruns, deliberate repeats, or ID "
            "collisions. If CI retries failed tests, pass --repeats-are-reruns (a run_suite.py manifest does this for you)"
        )
    for warning in s["warnings"][:6]:
        print(f"warning: {warning}")


# --------------------------------------------------------------------------- commands


def cmd_summary(args: argparse.Namespace) -> int:
    nodeid_map = load_nodeid_map(args.nodeids)
    runs = [load(p, nodeid_map, args.repeats_are_reruns) for p in args.files]
    run = runs[0]
    for other in runs[1:]:
        run.merge(other)
    summary = summarise(run, args.top, args.depth)
    print_summary(summary, args.top)
    if args.json_out:
        summary["all_tests"] = [t.as_dict() for t in run.tests.values()]
        write_out(args.json_out, json.dumps(summary, indent=2))
        print(f"json: {args.json_out}")
    return 0


def cmd_flips(args: argparse.Namespace) -> int:
    nodeid_map = load_nodeid_map(args.nodeids)
    runs = [load(p, nodeid_map, args.repeats_are_reruns) for p in args.files]
    commits = {(r.manifest or {}).get("commit") for r in runs}
    dirty = any((r.manifest or {}).get("dirty") for r in runs)
    same_commit = args.same_commit or (None not in commits and len(commits) == 1 and not dirty)
    history: dict[str, list[str]] = defaultdict(list)
    for r in runs:
        for tid, test in r.tests.items():
            history[tid].append(test.outcome)
            if test.reruns and test.outcome in PASS_OUTCOMES:
                history[tid].append("failed(rerun)")
    flips = []
    for tid, outcomes in history.items():
        failed = sum(1 for o in outcomes if o in FAIL_OUTCOMES or o == "failed(rerun)")
        passed = sum(1 for o in outcomes if o in PASS_OUTCOMES)
        if failed and passed:
            flips.append({"id": tid, "passed": passed, "failed": failed, "runs": len(outcomes)})
    flips.sort(key=lambda f: (-min(f["passed"], f["failed"]), f["id"]))
    verdict = "flaky at the same commit" if same_commit else "outcome changes across different or unknown commits – NOT evidence of flakiness"
    print(f"runs: {len(runs)}   tests seen: {len(history)}   tests with both passes and failures: {len(flips)}")
    print(f"commits: {', '.join(sorted(str(c)[:10] for c in commits))}{' (dirty tree)' if dirty else ''}")
    print(f"classification: {verdict}")
    for row in flips[:25]:
        print(f"  pass {row['passed']} / fail {row['failed']}  {row['id']}")
    if len(flips) > 25:
        print(f"  … {len(flips) - 25} more in --json-out")
    missing = [tid for tid, o in history.items() if len(o) < len(runs)]
    if missing:
        print(f"note: {len(missing)} tests are missing from some runs (different selection, sharding, or crashes)")
    if args.json_out:
        write_out(args.json_out, json.dumps({"same_commit": same_commit, "commits": sorted(map(str, commits)), "flips": flips}, indent=2))
        print(f"json: {args.json_out}")
    return 0


def median_side(files: list[str], nodeid_map: dict, repeats_are_reruns: bool = False) -> tuple[dict[str, float], dict[str, str], list[float], list[Run]]:
    runs = [load(p, nodeid_map, repeats_are_reruns) for p in files]
    per_test: dict[str, list[float]] = defaultdict(list)
    outcome: dict[str, str] = {}
    totals = []
    for r in runs:
        totals.append((r.manifest or {}).get("wall_seconds") or sum(t.total for t in r.tests.values()))
        for tid, t in r.tests.items():
            per_test[tid].append(t.total)
            if outcome.get(tid) not in FAIL_OUTCOMES:
                outcome[tid] = t.outcome
    return {k: statistics.median(v) for k, v in per_test.items()}, outcome, totals, runs


def cmd_diff(args: argparse.Namespace) -> int:
    nodeid_map = load_nodeid_map(args.nodeids)
    before, before_out, before_totals, before_runs = median_side(args.before, nodeid_map, args.repeats_are_reruns)
    after, after_out, after_totals, after_runs = median_side(args.after, nodeid_map, args.repeats_are_reruns)
    b_total, a_total = statistics.median(before_totals), statistics.median(after_totals)
    change = 100 * (a_total - b_total) / b_total if b_total else 0.0
    print(f"before: median {b_total:.1f}s over {len(before_totals)} runs   after: median {a_total:.1f}s over {len(after_totals)} runs   change: {change:+.1f}%")
    if min(len(before_totals), len(after_totals)) < 3:
        print("warning: fewer than 3 runs on a side; noise may exceed the change")
    def setting(run: Run, key: str) -> str:
        manifest = run.manifest or {}
        value = str(manifest.get(key))
        if key == "command" and manifest.get("run_dir"):
            value = value.replace(manifest["run_dir"], "{RUN_DIR}")  # each run writes into its own folder
        return value

    keys = ("command", "workers", "commit", "instrumented", "cpu_count")
    for key in keys:
        vals = {setting(r, key) for r in before_runs + after_runs}
        if key != "commit" and len(vals) > 1:
            print(f"warning: runs differ in {key}: {', '.join(sorted(vals))[:120]}")
    if any((r.manifest or {}).get("instrumented") not in (None, "none") for r in before_runs + after_runs):
        print("warning: at least one run was instrumented; timing comparison is not valid")
    gone = sorted(set(before) - set(after))
    new = sorted(set(after) - set(before))
    changed = sorted(
        (tid, before_out[tid], after_out[tid])
        for tid in set(before) & set(after)
        if before_out[tid] != after_out[tid]
    )
    print(f"tests: {len(before)} before, {len(after)} after, {len(gone)} disappeared, {len(new)} appeared, {len(changed)} changed outcome")
    for tid in gone[:5]:
        print(f"  disappeared: {tid}")
    for tid in new[:5]:
        print(f"  appeared: {tid}")
    for tid, b, a in changed[:10]:
        print(f"  {b} -> {a}: {tid}")
    deltas = sorted(((after[t] - before[t], t) for t in set(before) & set(after)), key=lambda x: x[0])
    if deltas:
        print("largest improvements:")
        for delta, tid in deltas[:5]:
            print(f"  {delta:+.3f}s  {tid}")
        print("largest regressions:")
        for delta, tid in reversed(deltas[-5:]):
            if delta > 0:
                print(f"  {delta:+.3f}s  {tid}")
    verdict_ok = not gone and not new and not changed
    print(f"verdict: {'SAME TESTS AND OUTCOMES' if verdict_ok else 'TEST SET OR OUTCOMES CHANGED – review before accepting'}")
    if args.json_out:
        write_out(args.json_out, 
            json.dumps(
                {
                    "before_median_seconds": b_total,
                    "after_median_seconds": a_total,
                    "change_percent": round(change, 2),
                    "disappeared": gone,
                    "appeared": new,
                    "changed": [{"id": t, "before": b, "after": a} for t, b, a in changed],
                    "same_tests_and_outcomes": verdict_ok,
                },
                indent=2,
            )
        )
        print(f"json: {args.json_out}")
    return 0 if verdict_ok else 1


def cmd_fixtures(args: argparse.Namespace) -> int:
    """Rank fixtures by total setup cost from pytest_audit_timing's fixtures-*.json files."""
    folder = Path(args.run)
    files = sorted(folder.glob("fixtures-*.json")) if folder.is_dir() else [folder]
    if not files:
        print(f"{folder}: no fixtures-*.json; run with run_suite.py --timing-plugin")
        return 1
    merged: dict[tuple[str, str], dict] = {}
    for path in files:
        for row in json.loads(path.read_text()):
            key = (row["defined_in"], row["name"])
            entry = merged.setdefault(
                key, {**row, "setups": 0, "total_seconds": 0.0, "max_seconds": 0.0, "teardowns": 0, "teardown_seconds": 0.0, "workers": 0}
            )
            entry["setups"] += row["setups"]
            entry["total_seconds"] += row["total_seconds"]
            entry["teardowns"] += row.get("teardowns", 0)
            entry["teardown_seconds"] += row.get("teardown_seconds", 0.0)
            entry["max_seconds"] = max(entry["max_seconds"], row["max_seconds"])
            entry["workers"] += 1
    rows = sorted(merged.values(), key=lambda r: -(r["total_seconds"] + r["teardown_seconds"]))
    total = sum(r["total_seconds"] for r in rows)
    teardown = sum(r["teardown_seconds"] for r in rows)
    print(f"fixture setup time: {total:.1f}s and teardown time: {teardown:.1f}s across {len(rows)} fixtures, from {len(files)} process(es)")
    if folder.is_dir():
        try:
            tests = len(load(str(folder), {}).tests)
        except SystemExit:
            tests = 0
        function_setups = sum(r["setups"] for r in rows if r["scope"] == "function")
        if tests:
            print(f"function-scoped fixture setups per test: {function_setups / tests:.1f} (mean over {tests} tests); root autouse fixtures inflate this")
            try:
                phase = sum(t.setup or 0 for t in load(str(folder), {}).tests.values())
            except SystemExit:
                phase = 0.0
            if phase:
                print(
                    f"setup phase: {phase:.1f}s in total, of which fixture functions took {total:.1f}s; the other {max(0.0, phase - total):.1f}s "
                    "is fixture resolution, setup hooks, garbage collection, and contention"
                )
    print(f"{'setup':>9} {'setups':>7} {'mean':>8} {'max':>8} {'teardown':>9}  scope     fixture (defined in)")
    for r in rows[: args.top]:
        mean = r["total_seconds"] / r["setups"] if r["setups"] else 0
        print(
            f"{r['total_seconds']:>8.1f}s {r['setups']:>7} {mean:>7.3f}s {r['max_seconds']:>7.3f}s {r['teardown_seconds']:>8.1f}s  "
            f"{r['scope']:<9} {r['name']} ({r['defined_in']})"
        )
    costly = [r for r in rows if r["scope"] == "function" and r["setups"] >= 100 and r["total_seconds"] / r["setups"] >= 0.02]
    if costly:
        print(f"function-scoped fixtures set up 100+ times at 20 ms or more each: {', '.join(r['name'] for r in costly[:6])}")
    replicated = [r for r in rows if r["scope"] == "session" and r["workers"] > 1 and r["max_seconds"] >= 2]
    if replicated:
        print(f"session fixtures paid once per worker, 2 s or more each: {', '.join(r['name'] for r in replicated[:6])}")
    if args.json_out:
        write_out(args.json_out, json.dumps(rows, indent=2))
        print(f"json: {args.json_out}")
    return 0


def cmd_extrapolate(args: argparse.Namespace) -> int:
    """Estimate the full suite's serial test time from a run of a stratified file sample."""
    plan = json.loads(Path(args.plan).read_text())
    run = load(args.run, load_nodeid_map(args.nodeids))
    per_file: dict[str, float] = defaultdict(float)
    first_on_worker: dict[str | None, Test] = {}
    for test in run.tests.values():
        per_file[test.file or test.id.split("::", 1)[0]] += test.total
        earlier = first_on_worker.get(test.worker)
        if earlier is None or (test.start is not None and earlier.start is not None and test.start < earlier.start):
            first_on_worker[test.worker] = test
    # Session fixtures are set up during the first test on each worker: count that setup once, unscaled.
    fixed = 0.0
    for test in first_on_worker.values():
        if test.setup:
            per_file[test.file or test.id.split("::", 1)[0]] -= test.setup
            fixed += test.setup
    has_phases = any(t.setup is not None for t in run.tests.values())
    strata = plan["strata"]
    planned = {f for s in strata.values() for f in s["files"]}
    missing = sorted(planned - set(per_file))

    def estimate(choose) -> float:
        total = 0.0
        for s in strata.values():
            files = choose(list(s["files"]))
            tests = sum(s["files"][f] for f in files)
            if tests:
                total += sum(per_file.get(f, 0.0) for f in files) * s["tests_total"] / tests
        return total

    point = estimate(lambda files: files) + fixed
    rng = random.Random(args.seed)
    boots = sorted(estimate(lambda files: [rng.choice(files) for _ in files]) + fixed for _ in range(args.bootstrap))
    low, high = boots[int(0.05 * len(boots))], boots[max(0, int(0.95 * len(boots)) - 1)]
    single = sum(1 for s in strata.values() if len(s["files"]) == 1)
    sampled_tests = sum(sum(s["files"].values()) for s in strata.values())
    total_tests = sum(s["tests_total"] for s in strata.values())
    print(f"sample: {len(planned)} files, {sampled_tests} of {total_tests} tests; measured {sum(per_file.get(f, 0) for f in planned):.1f}s")
    print(f"estimated serial test time for the whole suite: {point:.0f}s, 90% range {low:.0f}–{high:.0f}s")
    if has_phases:
        print(
            f"the setup of the first test on each of {len(first_on_worker)} worker(s), {fixed:.1f}s, is counted once, not scaled: "
            "it holds the session fixtures"
        )
    else:
        print("warning: no setup times, so session fixtures inside the first test are scaled with its stratum; rerun with --timing-plugin")
    print("this excludes startup and collection; measure those separately and add them")
    if run.manifest and run.manifest.get("workers"):
        print(f"note: the sample ran with {run.manifest['workers']} workers, so per-test times include contention")
    if missing:
        print(f"warning: {len(missing)} sampled files have no results (crashed, deselected, or renamed), e.g. {missing[0]}")
    if single:
        print(f"warning: {single} strata have one sampled file, so the range understates their uncertainty")
    for w in run.warnings[:3]:
        print(f"warning: {w}")
    if args.json_out:
        write_out(args.json_out, 
            json.dumps(
                {"estimate_seconds": round(point, 1), "range_90": [round(low, 1), round(high, 1)], "first_test_setup_seconds": round(fixed, 2), "missing_files": missing, "basis": "extrapolated"},
                indent=2,
            )
        )
        print(f"json: {args.json_out}")
    return 0


def write_out(path_text: str, text: str) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("summary", help="hotspots and distribution for one run (files are merged)")
    p.add_argument("files", nargs="+")
    p.add_argument("--nodeids", help="output of `pytest --collect-only -q`, to map JUnit entries to node IDs")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--depth", type=int, default=None, help="directory depth for grouping (default: from 2, deeper until no directory holds over 60%% of time)")
    p.add_argument("--repeats-are-reruns", action="store_true", help="count a test ID repeated in one JUnit file as a rerun")
    p.add_argument("--json-out")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("flips", help="tests that both passed and failed across runs")
    p.add_argument("files", nargs="+", help="one file or run folder per run")
    p.add_argument("--same-commit", action="store_true", help="assert that all runs used the same commit")
    p.add_argument("--nodeids")
    p.add_argument("--repeats-are-reruns", action="store_true", help="count a test ID repeated in one JUnit file as a rerun")
    p.add_argument("--json-out")
    p.set_defaults(func=cmd_flips)

    p = sub.add_parser("diff", help="compare runs before and after a change")
    p.add_argument("--before", nargs="+", required=True)
    p.add_argument("--after", nargs="+", required=True)
    p.add_argument("--nodeids")
    p.add_argument("--repeats-are-reruns", action="store_true", help="count a test ID repeated in one JUnit file as a rerun")
    p.add_argument("--json-out")
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("fixtures", help="rank fixtures by setup cost (needs run_suite.py --timing-plugin)")
    p.add_argument("run", help="a run folder with fixtures-*.json files, or one such file")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--json-out")
    p.set_defaults(func=cmd_fixtures)

    p = sub.add_parser("extrapolate", help="estimate the whole suite from a sample run")
    p.add_argument("run", help="the sample run's folder or report")
    p.add_argument("--plan", required=True, help="the .json plan written by run_suite.py sample")
    p.add_argument("--bootstrap", type=int, default=1000, help="bootstrap resamples for the range (default 1000)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--nodeids")
    p.add_argument("--json-out")
    p.set_defaults(func=cmd_extrapolate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
