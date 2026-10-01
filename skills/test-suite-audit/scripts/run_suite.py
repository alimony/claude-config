#!/usr/bin/env python3
"""Run test commands for a test-suite audit, leaving the same evidence every time.

Every test run in an audit goes through this script. Each run gets its own
folder with the exact command, the commit, whether the tree was dirty, the time
box, the exit code, the collected and executed counts, and the full output.
Later steps (results.py, findings.py) read those folders, so every claim in the
report can point at the run that produced it.

Usage:
    run_suite.py init [--project DIR] [--new]
    run_suite.py run --artifacts DIR --label NAME [--timeout SECONDS]
                     [--cwd DIR] [--env KEY=VALUE ...] [--unset KEY ...]
                     [--instrumented auto|none|coverage|mutation|profile]
                     [--lock-wait SECONDS] [--no-redirect] [--timing-plugin]
                     [--leak-probe PACKAGES] [--db-probe] -- COMMAND ...
    run_suite.py list --artifacts DIR
    run_suite.py sample --nodeids FILE --out FILE [--fraction 0.1] [--depth 2] [--seed 1]

`sample` picks whole test files, stratified by directory, for a sample run of a
suite too slow to run in full. results.py extrapolate turns the sample run into
an estimate for the whole suite.

`init` prints the audit directory for the project: the newest unfinished audit
under ~/.cache/test-suite-audit/<project>/, or a new one. Set
TEST_SUITE_AUDIT_HOME to use another root.

`run` substitutes {RUN_DIR} in COMMAND and in --env values with the run folder, so a run can write
its reports next to its manifest, for example:
    run_suite.py run --artifacts "$A" --label baseline --timeout 1800 -- \\
        python -m pytest -q --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1

While a run is active, the script:
  * holds a per-project lock, so two runs never share test databases (it is an
    fcntl lock on .run.lock, so a leftover file from a dead process holds nothing);
  * closes stdin, so an interactive prompt fails instead of hanging;
  * drops an inherited FORCE_COLOR, which agent shells set and CI rarely does
    (pass --env FORCE_COLOR=1 when CI sets it);
  * points pytest's cache, COVERAGE_FILE, and Hypothesis's example database
    into the run folder, so the project's own --lf state, coverage data, and
    saved examples survive (--no-redirect disables);
  * stops the whole process group at the time box: SIGINT first, so pytest can
    still write its reports, then SIGTERM, then SIGKILL.

With --timing-plugin, pytest also loads pytest_plugin/pytest_audit_timing.py
through PYTHONPATH and PYTEST_ADDOPTS, without installing anything. It writes
timing.jsonl (full-precision phase times, with xdist workers) and
fixtures-<worker>.json (setup cost per fixture) into the run folder. Wrappers
such as tox 4 drop environment variables they do not pass through, so check
that those files appear.

With --leak-probe PACKAGES, pytest loads pytest_plugin/pytest_audit_leaks.py the
same way. It writes leaks.json: for each test, the process-global state that
changed while it ran (working directory, os.environ, sys.path, threads, started
mock patches, logging and signal handlers, sys.modules, and module-level
containers in PACKAGES). The run counts as instrumented, and it needs -n 0.

With --db-probe, pytest loads pytest_plugin/pytest_audit_db.py the same way, for
Django projects with pytest-django. It writes, into the run folder, each test's
database isolation mode and the statements it ran. The run counts as
instrumented.

The printed summary is at most 15 lines. The full output is in output.log.

Standard library only; runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import random
import re
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None  # type: ignore[assignment]

DEFAULT_TIMEOUT = 1200
GRACE_SECONDS = 30

# Environment variables whose values are safe and useful to record.
RECORDED_ENV = (
    "CI",
    "COVERAGE_CORE",
    "DJANGO_SETTINGS_MODULE",
    "HYPOTHESIS_STORAGE_DIRECTORY",
    "PYTEST_ADDOPTS",
    "PYTEST_XDIST_AUTO_NUM_WORKERS",
    "PYTHONHASHSEED",
    "PYTHONPATH",
    "TOX_ENV_NAME",
    "VIRTUAL_ENV",
)

# Mutation comes first: mutation tools often run coverage too, and a mutation run must show UNCHECKED.
INSTRUMENT_PATTERNS = {
    "mutation": re.compile(
        r"\b(mutmut|cosmic[-_]ray|mutatest|poodle|pseudo_tested|fest(-mutate)?|gremlins|stryker|pitest|cargo[- ]mutants|infection|go-mutesting)\b"
    ),
    "coverage": re.compile(r"(^|\s)(--cov\b|--cov=|coverage\s+run|-m\s+coverage|--testmon\b)"),
    "profile": re.compile(r"(-X\s*importtime|\bpyinstrument\b|\bcProfile\b|--profile\b|\bpy-spy\b|\bscalene\b|\bmemray\b)"),
}

PYTEST_EXIT = {
    0: "all tests passed",
    1: "some tests failed",
    2: "interrupted",
    3: "internal error",
    4: "usage error",
    5: "no tests collected",
}

# pytest's final summary line, e.g. "==== 2 failed, 120 passed, 3 skipped in 12.34s ====".
PYTEST_SUMMARY_RE = re.compile(r"^=+ (?P<body>.+?) in (?P<secs>[\d.]+)s(?: \([\d:.]+\))? =+\s*$")
PYTEST_QUIET_SUMMARY_RE = re.compile(r"^(?P<body>\d+ \w+(?:, \d+ \w+)*) in (?P<secs>[\d.]+)s(?: \([\d:.]+\))?\s*$")
PYTEST_COUNT_RE = re.compile(r"(\d+) (passed|failed|skipped|xfailed|xpassed|errors?|warnings?|rerun|deselected)")
PYTEST_HEADER_RE = re.compile(r"^platform \S+ -- Python (\S+), pytest-([^,\s]+)")
COLLECTED_RE = re.compile(r"collected (\d+) items?(?: / (\d+) deselected)?(?: / (\d+) selected)?")
# `pytest --collect-only -q` ends with "176 tests collected in 0.43s" or "90/100 tests collected (10 deselected) in 0.5s".
COLLECT_ONLY_RE = re.compile(r"^(?:=+ )?(?:(\d+)/)?(\d+) tests? collected(?: \((\d+) deselected\))?(?:, (\d+) errors?)? in ([\d.]+)s")
NO_TESTS_RAN_RE = re.compile(r"^(?:=+ )?no tests ran in ([\d.]+)s")  # -q drops the banner
NO_TESTS_COLLECTED_RE = re.compile(r"^(?:=+ )?no tests collected(?: \((\d+) deselected\))?(?:, (\d+) errors?)? in ([\d.]+)s")
XDIST_RE = re.compile(r"(\d+) workers? \[(\d+) items?\]")
COLLECTION_ERRORS_RE = re.compile(r"Interrupted: (\d+) errors? during collection")
UNITTEST_RAN_RE = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s")
UNITTEST_RESULT_RE = re.compile(r"^(OK|FAILED)(?: \((.*)\))?\s*$")
JEST_TESTS_RE = re.compile(r"^Tests:\s+(.*\d+ total)")
VITEST_TESTS_RE = re.compile(r"^\s*Tests\s+(\d+ \w+(?: \| \d+ \w+)*) \((\d+)\)")
GO_PACKAGE_RE = re.compile(r"^(ok|FAIL)\s+\S+\s+(?:([\d.]+)s|\(cached\))")
GO_TEST_RE = re.compile(r"^\s*--- (PASS|FAIL|SKIP): ")
CARGO_RE = re.compile(r"^test result: \w+\. (\d+) passed; (\d+) failed; (\d+) ignored")
RSPEC_RE = re.compile(r"^(\d+) examples?, (\d+) failures?(?:, (\d+) pending)?")
PHPUNIT_OK_RE = re.compile(r"^OK \((\d+) tests?, (\d+) assertions?\)")
PHPUNIT_RE = re.compile(r"^Tests: (\d+), Assertions: (\d+)(.*)")
SUREFIRE_RE = re.compile(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)")
DOTNET_RE = re.compile(r"^(?:Passed|Failed)!\s+-\s+Failed:\s+(\d+), Passed:\s+(\d+), Skipped:\s+(\d+), Total:\s+(\d+)")
SEED_RES = (
    re.compile(r"Using --randomly-seed=(\d+)"),
    re.compile(r"Using shuffle seed: (\d+)"),
    re.compile(r"random-order-seed=(\d+)"),
)


def audit_home() -> Path:
    return Path(os.environ.get("TEST_SUITE_AUDIT_HOME", Path.home() / ".cache" / "test-suite-audit"))


def git(args: list[str], cwd: Path) -> str | None:
    try:
        # GIT_OPTIONAL_LOCKS=0: `git status` must not take the index lock or rewrite .git/index.
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60, check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout if out.returncode == 0 else None


def project_root(start: Path) -> Path:
    top = git(["rev-parse", "--show-toplevel"], start)
    return Path(top.strip()) if top else start.resolve()


def project_slug(unit: Path, root: Path | None = None) -> str:
    """The audit unit's folder name: the repository's name, plus the unit's path inside it, plus a hash."""
    unit = unit.resolve()
    digest = hashlib.sha1(str(unit).encode()).hexdigest()[:8]
    parts = [unit.name]
    if root is not None and unit != root.resolve():
        try:
            parts = [root.name, *unit.relative_to(root.resolve()).parts]
        except ValueError:
            pass
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", "-".join(parts)) or "project"
    return f"{name}-{digest}"


STATE_TEMPLATE = """# Test suite audit state

- project: {project}
- repository: {repository}
- audit directory: {audit}
- created: {created} (skill scripts {tools})
- status: in progress (set it to finished when the user has the report)

## Scope and budget

- time budget: (agreed with the user)
- services: (which, and how they are started)
- runner command: (the exact command CI uses)

## Phases

- [ ] 1 scope and safety
- [ ] 2 reconnaissance
- [ ] 3 harvest existing artifacts
- [ ] 4 static scan
- [ ] 5 count parity
- [ ] 6 baseline measurement
- [ ] 7 deep dives
- [ ] 8 findings and report
- [ ] 9 approved changes

## Decisions and notes

## Planned runs awaiting the user's approval

## Next step
"""


def cmd_init(args: argparse.Namespace) -> int:
    # One audit unit per test root: in a monorepo, backend/ and frontend/ get separate audits.
    unit = Path(args.project).resolve()
    root = project_root(unit)
    base = audit_home() / project_slug(unit, root)
    # Earlier versions named every audit after the repository root; resume those too.
    bases = [base] + ([audit_home() / project_slug(root)] if unit != root.resolve() and not base.is_dir() else [])
    for folder in bases if not args.new else []:
        if not folder.is_dir():
            continue
        for existing in sorted((p for p in folder.iterdir() if p.is_dir()), reverse=True):
            state = existing / "STATE.md"
            if state.is_file() and "status: finished" not in state.read_text(errors="replace"):
                print(existing)
                return 0
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    audit = base / stamp
    suffix = 1
    while audit.exists():
        suffix += 1
        audit = base / f"{stamp}-{suffix}"
    (audit / "runs").mkdir(parents=True)
    (audit / "STATE.md").write_text(
        STATE_TEMPLATE.format(
            project=unit, repository=root, audit=audit, created=_dt.datetime.now().isoformat(timespec="seconds"), tools=tools_version()
        )
    )
    print(audit)
    return 0


def next_run_dir(artifacts: Path, label: str) -> Path:
    runs = artifacts / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    numbers = [int(m.group(1)) for p in runs.iterdir() if (m := re.match(r"(\d+)-", p.name))]
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-") or "run"
    run_dir = runs / f"{max(numbers, default=0) + 1:02d}-{safe}"
    run_dir.mkdir()
    return run_dir


def lock_path(artifacts: Path) -> Path:
    # Lock per project, not per audit, so two audits of one project never overlap. An audit
    # directory from init sits in <home>/<project>-<hash>/, wherever TEST_SUITE_AUDIT_HOME pointed.
    artifacts = artifacts.resolve()
    if (artifacts / "STATE.md").is_file() and re.search(r"-[0-9a-f]{8}$", artifacts.parent.name):
        return artifacts.parent / ".run.lock"
    return artifacts / ".run.lock"


def tools_version() -> str:
    """A short hash of the skill's scripts, so manifests and STATE.md show which version made them."""
    digest = hashlib.sha1()
    for path in sorted(Path(__file__).resolve().parent.glob("*.py")) + sorted(Path(__file__).resolve().parent.glob("pytest_plugin/*.py")):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:10]


def acquire_lock(path: Path, wait: float, holder: str):
    if fcntl is None:
        return None, "no file locking on this platform; runs are not serialised"
    handle = open(path, "a+")
    deadline = time.monotonic() + wait
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.seek(0)
                current = handle.read().strip() or "unknown holder"
                handle.close()
                raise SystemExit(f"Another run holds the lock {path}: {current}")
            time.sleep(2)
    handle.seek(0)
    handle.truncate()
    handle.write(holder)
    handle.flush()
    return handle, None


def status_lines(cwd: Path) -> list[str] | None:
    out = git(["status", "--porcelain=v1", "--untracked-files=normal"], cwd)
    return None if out is None else [line for line in out.splitlines() if line.strip()]


def option_texts(command_text: str, env: dict[str, str], cwd: Path) -> list[str]:
    """The command, PYTEST_ADDOPTS, and the pytest configuration files in cwd, as raw text."""
    texts = [command_text, env.get("PYTEST_ADDOPTS", "")]
    for name in ("pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"):
        path = cwd / name
        if path.is_file():
            try:
                texts.append(path.read_text(errors="replace"))
            except OSError:
                pass
    return texts


def cache_plugin_disabled(texts: list[str]) -> bool:
    return any(re.search(r"no:\s*cacheprovider", t) for t in texts)


def reruns_configured(texts: list[str]) -> bool:
    """pytest-rerunfailures on through --reruns, or its `reruns` ini option (14.0+)."""
    return any(re.search(r"--reruns\b|^\s*reruns\s*=", t, re.M) for t in texts)


def requested_workers(command: list[str], env: dict[str, str]) -> str | None:
    """The xdist worker count asked for with -n or --numprocesses, in the command or PYTEST_ADDOPTS."""
    args = command + shlex.split(env.get("PYTEST_ADDOPTS", ""))
    for i, arg in enumerate(args):
        if arg in ("-n", "--numprocesses"):
            return args[i + 1] if i + 1 < len(args) else None
        if arg.startswith("--numprocesses="):
            return arg.split("=", 1)[1]
        if arg.startswith("-n") and (arg[2:].isdigit() or arg[2:] in ("auto", "logical")):
            return arg[2:]
    return None


def interpreter_version(command: list[str], env: dict[str, str], cwd: Path) -> str | None:
    """The Python version of the command's interpreter, when the command starts with one."""
    if not Path(command[0]).name.startswith(("python", "pypy")):
        return None
    try:
        out = subprocess.run(
            [command[0], "-c", "import platform; print(platform.python_version())"],
            cwd=cwd, env=env, capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def detect_instrumentation(command: list[str] | str, env: dict[str, str]) -> str:
    tokens = shlex.split(command) if isinstance(command, str) else list(command)
    # Code given to `python -c` is data: a version check that mentions a tool runs no tool.
    kept = [
        token for i, token in enumerate(tokens)
        if not (i >= 2 and tokens[i - 1] == "-c" and Path(tokens[i - 2]).name.startswith(("python", "pypy")))
    ]
    haystack = f"{shlex.join(kept)} {env.get('PYTEST_ADDOPTS', '')}"
    for kind, pattern in INSTRUMENT_PATTERNS.items():
        if pattern.search(haystack):
            return kind
    return "none"


def parse_output(log_path: Path) -> dict:
    """Extract counts, seeds, and collection facts from a run's output."""
    info: dict = {"runner": "unknown", "counts": {}}
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return info
    for line in lines:
        text = re.sub(r"\x1b\[[0-9;]*m", "", line).rstrip()
        if (m := PYTEST_HEADER_RE.match(text)):
            info["python"], info["pytest"] = m.group(1), m.group(2)
        if (m := COLLECTED_RE.search(text)):
            info["collected"] = int(m.group(1))
            if m.group(2):
                info["deselected"] = int(m.group(2))
            if m.group(3):
                info["selected"] = int(m.group(3))
        if (m := XDIST_RE.search(text)):
            info["workers"] = int(m.group(1))
            info["collected"] = int(m.group(2))
        if text.startswith("ERROR: usage:") or ": error: unrecognized arguments" in text:
            info["usage_error"] = True
        if (m := COLLECTION_ERRORS_RE.search(text)):
            info["collection_errors"] = int(m.group(1))
        if (m := NO_TESTS_RAN_RE.match(text)):
            info["runner"] = "pytest"
            info["reported_seconds"] = float(m.group(1))
            info.setdefault("counts", {})
        if (m := NO_TESTS_COLLECTED_RE.match(text)):
            # --collect-only that selected nothing, or a run that found no tests at all
            info["runner"] = "pytest"
            info["collect_only"] = True
            info["collected"] = 0
            info["reported_seconds"] = float(m.group(3))
            info["counts"] = {"collected": 0, **({"deselected": int(m.group(1))} if m.group(1) else {})}
            if m.group(2):
                info["collection_errors"] = int(m.group(2))
        if (m := COLLECT_ONLY_RE.match(text)):
            info["runner"] = "pytest"
            info["collect_only"] = True
            info["collected"] = int(m.group(1) or m.group(2))
            info["reported_seconds"] = float(m.group(5))
            info["counts"] = {"collected": info["collected"]}
            if m.group(4):
                info["collection_errors"] = int(m.group(4))
        for seed_re in SEED_RES:
            if (m := seed_re.search(text)):
                info["seed"] = m.group(1)
        m = PYTEST_SUMMARY_RE.match(text) or PYTEST_QUIET_SUMMARY_RE.match(text)
        if m and PYTEST_COUNT_RE.search(m.group("body")):
            info["runner"] = "pytest"
            info["reported_seconds"] = float(m.group("secs"))
            counts = {}
            for n, word in PYTEST_COUNT_RE.findall(m.group("body")):
                key = {"error": "errors", "warning": "warnings"}.get(word, word)
                counts[key] = counts.get(key, 0) + int(n)
            info["counts"] = counts
        if (m := UNITTEST_RAN_RE.match(text)):
            info["runner"] = "unittest"
            info["executed"] = int(m.group(1))
            info["reported_seconds"] = float(m.group(2))
        if info["runner"] == "unittest" and (m := UNITTEST_RESULT_RE.match(text)):
            counts = {"ran": info.get("executed", 0)}
            for part in (m.group(2) or "").split(","):
                if "=" in part:
                    key, _, value = part.strip().partition("=")
                    if value.isdigit():
                        counts[key] = int(value)
            info["counts"] = counts
        if (m := JEST_TESTS_RE.match(text)):
            info["runner"] = "jest"
            info["counts"] = {w: int(n) for n, w in re.findall(r"(\d+) (\w+)", m.group(1))}
        if (m := VITEST_TESTS_RE.match(text)):
            info["runner"] = "vitest"
            info["counts"] = {w: int(n) for n, w in re.findall(r"(\d+) (\w+)", m.group(1))}
        if (m := GO_PACKAGE_RE.match(text)):
            info["runner"] = "go"
            counts = info.setdefault("go_packages", {"ok": 0, "FAIL": 0, "cached": 0})
            counts[m.group(1)] += 1
            if "(cached)" in text:
                counts["cached"] += 1
        if (m := GO_TEST_RE.match(text)):
            key = {"PASS": "passed", "FAIL": "failed", "SKIP": "skipped"}[m.group(1)]
            info.setdefault("go_tests", {}).setdefault(key, 0)
            info["go_tests"][key] += 1
        if (m := CARGO_RE.match(text)):
            info["runner"] = "cargo"
            c = info["counts"] if info["counts"] and "ignored" in info["counts"] else {"passed": 0, "failed": 0, "ignored": 0}
            c["passed"] += int(m.group(1))
            c["failed"] += int(m.group(2))
            c["ignored"] += int(m.group(3))
            info["counts"] = c
        if (m := RSPEC_RE.match(text)):
            info["runner"] = "rspec"
            info["counts"] = {"examples": int(m.group(1)), "failures": int(m.group(2)), "pending": int(m.group(3) or 0)}
        if (m := PHPUNIT_OK_RE.match(text)):
            info["runner"] = "phpunit"
            info["counts"] = {"tests": int(m.group(1)), "assertions": int(m.group(2))}
        elif (m := PHPUNIT_RE.match(text)):
            info["runner"] = "phpunit"
            info["counts"] = {"tests": int(m.group(1)), "assertions": int(m.group(2)), **{k.lower(): int(v) for k, v in re.findall(r"(\w+): (\d+)", m.group(3))}}
        if (m := SUREFIRE_RE.search(text)):
            info["runner"] = "maven"
            info["counts"] = {"run": int(m.group(1)), "failures": int(m.group(2)), "errors": int(m.group(3)), "skipped": int(m.group(4))}
        if (m := DOTNET_RE.match(text)):
            info["runner"] = "dotnet"
            info["counts"] = {"failed": int(m.group(1)), "passed": int(m.group(2)), "skipped": int(m.group(3)), "total": int(m.group(4))}
    if info["runner"] == "go":
        info["counts"] = {**info.get("go_tests", {}), **{f"packages_{k.lower()}": v for k, v in info.pop("go_packages").items()}}
        info.pop("go_tests", None)
    if info["runner"] == "pytest" and not info.get("collect_only"):
        c = info["counts"]
        info["executed"] = sum(c.get(k, 0) for k in ("passed", "failed", "skipped", "xfailed", "xpassed"))
    return info


def completeness(info: dict, exit_code: int | None, timed_out: bool, instrumented: str = "none") -> tuple[bool, str]:
    if timed_out:
        return False, "stopped at the time box"
    if info.get("collection_errors"):
        return False, f"{info['collection_errors']} collection errors"
    if instrumented == "mutation":
        # A pytest summary line from a mutation tool describes one test run, not the mutants.
        return False, "mutation run: judge completeness from the tool's own results (no mutant left unchecked)"
    if info["runner"] == "unknown":
        if exit_code == 4 and info.get("usage_error"):
            return False, "pytest usage error (exit 4): an option the project's plugins do not provide?"
        return False, "no recognised summary line in the output"
    if info["runner"] == "pytest":
        if info.get("collect_only") or info.get("plan_only"):
            if exit_code == 5 and info["counts"].get("deselected"):
                return True, f"complete: no tests selected ({info['counts']['deselected']} deselected)"
            return (exit_code == 0), ("complete" if exit_code == 0 else f"exit code {exit_code}")
        if exit_code == 5 and info["counts"].get("deselected") and not info.get("executed"):
            # An empty tier: the selection matched nothing, and the run itself was fine.
            return True, f"complete: no tests selected ({info['counts']['deselected']} deselected)"
        if exit_code is None or exit_code not in (0, 1):
            meaning = PYTEST_EXIT.get(exit_code, "unknown") if exit_code is not None else "no exit code"
            return False, f"pytest exit code {exit_code} ({meaning})"
        expected = info.get("selected", info.get("collected"))
        if expected is not None and "deselected" in info and "selected" not in info:
            expected -= info["deselected"]
        if expected is not None and info.get("executed", 0) + info["counts"].get("errors", 0) < expected:
            return False, f"executed {info.get('executed', 0)} of {expected} selected tests"
        return True, "complete"
    if info["runner"] == "go" and info["counts"].get("packages_cached"):
        return False, f"{info['counts']['packages_cached']} Go packages reported cached results; rerun with -count=1 to measure"
    failure_codes = {"cargo": (0, 101)}.get(info["runner"], (0, 1))
    if exit_code not in failure_codes:
        return False, f"exit code {exit_code}"
    return True, "complete"


def stop_group(proc: subprocess.Popen, grace: float) -> str:
    """Stop the run's whole process group, giving the runner a chance to write reports."""
    steps = [(signal.SIGINT, grace), (signal.SIGTERM, 10.0)]
    if hasattr(signal, "SIGKILL"):
        steps.append((signal.SIGKILL, 5.0))
    for sig, wait in steps:
        try:
            if os.name == "posix":
                os.killpg(proc.pid, sig)
            else:
                proc.send_signal(sig)
        except (ProcessLookupError, PermissionError):
            return sig.name
        try:
            proc.wait(timeout=wait)
            return sig.name
        except subprocess.TimeoutExpired:
            continue
    return "SIGKILL"


def write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    tmp.replace(path)


def cmd_run(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("run: no command given after --")
    artifacts = Path(args.artifacts).expanduser().resolve()
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    started = _dt.datetime.now().isoformat(timespec="seconds")
    artifacts.mkdir(parents=True, exist_ok=True)
    lock_handle, lock_note = acquire_lock(
        lock_path(artifacts), args.lock_wait, f"pid {os.getpid()} label {args.label} since {started}"
    )
    run_dir = next_run_dir(artifacts, args.label)
    command = [part.replace("{RUN_DIR}", str(run_dir)) for part in command]
    command_text = shlex.join(command)

    env = dict(os.environ)
    # Agent shells often export FORCE_COLOR, which CI rarely sets. It changes captured output
    # (Python 3.14 colours argparse help and tracebacks) and fills logs with escape codes.
    # Pass --env FORCE_COLOR=... when CI does set it.
    dropped = [key for key in ("FORCE_COLOR",) if env.pop(key, None) is not None]
    for key in args.unset:
        env.pop(key, None)
    overrides = {}
    for item in args.env:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"--env needs KEY=VALUE, got {item!r}")
        env[key] = overrides[key] = value.replace("{RUN_DIR}", str(run_dir))
    def add_pytest_options(*options: str) -> None:
        # pytest splits PYTEST_ADDOPTS with shlex, so quote paths that may contain spaces.
        env["PYTEST_ADDOPTS"] = " ".join([env.get("PYTEST_ADDOPTS", ""), *map(shlex.quote, options)]).strip()

    if not args.no_redirect:
        # -o cache_dir is an unknown option when the cache plugin is off, and projects with
        # filterwarnings = error then stop with an internal error, so skip it in that case.
        if "pytest" in command_text and not cache_plugin_disabled(option_texts(command_text, env, cwd)):
            add_pytest_options("-o", f"cache_dir={run_dir / 'pytest-cache'}")
        env.setdefault("COVERAGE_FILE", str(run_dir / ".coverage"))
        # A fresh example database per run, as in a fresh CI checkout; the project's .hypothesis stays untouched.
        env.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", str(run_dir / "hypothesis"))
    if args.timing_plugin or args.leak_probe is not None or args.db_probe:
        plugin_dir = str(Path(__file__).resolve().parent / "pytest_plugin")
        env["PYTHONPATH"] = os.pathsep.join(p for p in (plugin_dir, env.get("PYTHONPATH", "")) if p)
    if args.timing_plugin:
        add_pytest_options("-p", "pytest_audit_timing")
        env["AUDIT_TIMING_DIR"] = str(run_dir)
    if args.leak_probe is not None:
        add_pytest_options("-p", "pytest_audit_leaks", f"--audit-leaks-json={run_dir / 'leaks.json'}", f"--audit-leaks-packages={args.leak_probe}")
    if args.db_probe:
        add_pytest_options("-p", "pytest_audit_db", f"--audit-db-dir={run_dir}")
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Without a terminal, pytest cuts summary lines at 80 columns.
    env.setdefault("COLUMNS", "200")
    instrumented = args.instrumented
    if instrumented == "auto":
        instrumented = detect_instrumentation(command, env)
    if (args.leak_probe is not None or args.db_probe) and instrumented == "none":
        # Snapshots and statement hooks around every test slow the run, so its timings never count.
        instrumented = "profile"

    head = git(["rev-parse", "HEAD"], cwd)
    before = status_lines(cwd)
    manifest = {
        "label": args.label,
        "run_dir": str(run_dir),
        "command": command,
        "cwd": str(cwd),
        "status": "running",
        "started": started,
        "timeout_seconds": args.timeout,
        "instrumented": instrumented,
        # pytest-rerunfailures writes each attempt as its own <testcase>; results.py needs to know.
        "reruns_configured": reruns_configured(option_texts(command_text, env, cwd)),
        "commit": head.strip() if head else None,
        "dirty": bool(before) if before is not None else None,
        "env": {k: env[k] for k in RECORDED_ENV if k in env},
        "env_overrides": sorted(overrides),
        "env_unset": sorted(args.unset),
        "env_dropped": [key for key in dropped if key not in overrides],
        "project_python": interpreter_version(command, env, cwd),
        "platform": sys.platform,
        "cpu_count": os.cpu_count(),
        "wrapper_python": sys.version.split()[0],
        "tools_version": tools_version(),
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)

    log_path = run_dir / "output.log"
    timed_out = False
    stop_signal = None
    start = time.monotonic()
    try:
        with open(log_path, "wb") as log:
            log.write(f"$ {command_text}\n".encode())
            log.flush()
            try:
                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=(os.name == "posix"),
                )
            except OSError as exc:
                manifest.update(status="failed-to-start", error=str(exc))
                write_json(manifest_path, manifest)
                print(f"Could not start the command: {exc}")
                return 127
            try:
                proc.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                stop_signal = stop_group(proc, args.grace)
            except KeyboardInterrupt:
                stop_signal = stop_group(proc, args.grace)
                raise
    finally:
        wall = time.monotonic() - start
        if lock_handle is not None:
            lock_handle.close()

    exit_code = proc.returncode
    after = status_lines(cwd)
    info = parse_output(log_path)
    if any(a in ("--setup-plan", "--setup-only") for a in command):
        info["plan_only"] = True
    if "workers" not in info:
        # Quiet runs (-q) omit xdist's "N workers" line; fall back to what the command asked for.
        asked = requested_workers(command, env)
        if asked and asked.isdigit() and int(asked) > 0:
            info["workers"] = int(asked)
        elif asked:
            info["workers_requested"] = asked
    complete, reason = completeness(info, exit_code, timed_out, instrumented)
    if complete:
        label = "COMPLETE"
    elif reason.startswith("mutation run"):
        label = "UNCHECKED"
    elif info["runner"] == "unknown" and not timed_out:
        label = "UNKNOWN"
    else:
        label = "PARTIAL"
    tracked_changed: list[str] = []
    new_untracked: list[str] = []
    if before is not None and after is not None:
        was = set(before)
        tracked_changed = [s for s in after if s not in was and not s.startswith("??")]
        new_untracked = [s[3:] for s in after if s not in was and s.startswith("??")]
    reports = sorted(p.name for p in run_dir.iterdir() if p.suffix in (".xml", ".json", ".jsonl") and p.name != "manifest.json")
    if instrumented == "none" and any(p.name.startswith(".coverage") for p in run_dir.iterdir()):
        # Coverage switched on by the project's own addopts or configuration still distorts timings.
        instrumented = "coverage"
        manifest["instrumented"] = instrumented
    manifest.update(
        status="finished",
        finished=_dt.datetime.now().isoformat(timespec="seconds"),
        wall_seconds=round(wall, 2),
        exit_code=exit_code,
        timed_out=timed_out,
        stop_signal=stop_signal,
        complete=complete,
        verdict=label,
        completeness_reason=reason,
        tracked_files_changed=tracked_changed,
        new_untracked_files=new_untracked,
        reports=reports,
        **info,
    )
    if info.get("reported_seconds") is not None:
        # Time outside the runner's own clock: interpreter start-up, plugin loading, initial conftest
        # imports, and for Django's runner, test database creation and migrations.
        manifest["startup_gap_seconds"] = round(wall - info["reported_seconds"], 2)
    write_json(manifest_path, manifest)

    counts = ", ".join(f"{v} {k}" for k, v in info.get("counts", {}).items()) or "no counts parsed"
    print(f"run: {run_dir}")
    meaning = PYTEST_EXIT.get(exit_code) if info["runner"] == "pytest" and exit_code is not None else None
    if info.get("collect_only") and exit_code == 0:
        meaning = "collection succeeded"
    print(f"exit: {exit_code}" + (f" ({meaning})" if meaning else ""))
    gap = manifest.get("startup_gap_seconds")
    print(
        f"wall: {wall:.1f}s   runner: {info['runner']}   instrumented: {instrumented}"
        + (f"   outside the runner's clock: {gap:.1f}s" if gap is not None else "")
    )
    collected = info.get("selected", info.get("collected"))
    print(f"counts: {counts}" + (f"   collected: {collected}" if collected is not None else ""))
    if info.get("workers"):
        print(f"workers: {info['workers']}")
    if info.get("seed"):
        print(f"seed: {info['seed']}")
    print(f"verdict: {label} – {reason}")
    if reports:
        print(f"reports: {', '.join(reports[:6])}")
    if lock_note:
        print(f"note: {lock_note}")
    if tracked_changed:
        print(f"WARNING: {len(tracked_changed)} tracked files changed during the run: {', '.join(tracked_changed[:5])}")
    if new_untracked:
        print(f"note: {len(new_untracked)} new untracked files in the project: {', '.join(new_untracked[:5])}")
    if not complete and info["runner"] == "unknown":
        print(f"output tail: see {log_path}")
    if args.timing_plugin and not (run_dir / "timing.jsonl").exists():
        print("WARNING: --timing-plugin wrote no timing.jsonl; a wrapper probably dropped PYTHONPATH or PYTEST_ADDOPTS")
    if args.leak_probe is not None:
        try:
            leaks = json.loads((run_dir / "leaks.json").read_text())
            churn = len(leaks.get("churn", {}))
            print(
                f"leaks: {leaks['tests_with_changes']} of {leaks['tests_checked']} tests changed process-global state"
                + (f", and {churn} place{'s' if churn > 1 else ''} changed in more than 5 tests each (check each once)" if churn else "")
                + "; see leaks.json"
            )
        except (OSError, ValueError, KeyError):
            print("WARNING: --leak-probe wrote no leaks.json; check output.log (it refuses -n > 0), or a wrapper dropped PYTHONPATH or PYTEST_ADDOPTS")
    return 124 if timed_out else (exit_code if exit_code is not None else 1)


def cmd_sample(args: argparse.Namespace) -> int:
    """Pick whole test files, stratified by directory, so a sample run keeps realistic fixture costs."""
    tests_per_file: dict[str, int] = {}
    for line in Path(args.nodeids).read_text(errors="replace").splitlines():
        line = line.strip()
        if "::" in line and not line.startswith(("=", "<")):
            path = line.split("::", 1)[0]
            tests_per_file[path] = tests_per_file.get(path, 0) + 1
    if not tests_per_file:
        raise SystemExit(f"{args.nodeids}: no node IDs found")
    strata: dict[str, list[str]] = {}
    for path in sorted(tests_per_file):
        key = "/".join(Path(path).parent.parts[: args.depth]) or "."
        strata.setdefault(key, []).append(path)
    rng = random.Random(args.seed)
    plan: dict = {"seed": args.seed, "fraction": args.fraction, "depth": args.depth, "strata": {}}
    chosen: list[str] = []
    for key, files in sorted(strata.items()):
        k = min(len(files), max(args.min_files, round(args.fraction * len(files))))
        pick = sorted(rng.sample(files, k))
        chosen += pick
        plan["strata"][key] = {
            "files_total": len(files),
            "tests_total": sum(tests_per_file[f] for f in files),
            "files": {f: tests_per_file[f] for f in pick},
        }
    out = Path(args.out)
    out.write_text("\n".join(chosen) + "\n")
    out.with_suffix(".json").write_text(json.dumps(plan, indent=2))
    total = sum(tests_per_file.values())
    sampled = sum(sum(s["files"].values()) for s in plan["strata"].values())
    print(f"sampled {len(chosen)} of {len(tests_per_file)} files in {len(strata)} strata: {sampled} of {total} tests ({100 * sampled / total:.1f}%), seed {args.seed}")
    print(f"file list: {out}")
    print(f"plan: {out.with_suffix('.json')}")
    print(f"pass the files to the test command, for example: pytest @{out}   (pytest 8.2+ reads arguments from @files)")
    print(f"then estimate the full suite: results.py extrapolate RUN_DIR --plan {out.with_suffix('.json')}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    runs = Path(args.artifacts).expanduser() / "runs"
    if not runs.is_dir():
        print("no runs yet")
        return 0
    for run_dir in sorted(p for p in runs.iterdir() if p.is_dir()):
        try:
            m = json.loads((run_dir / "manifest.json").read_text())
        except (OSError, ValueError):
            print(f"{run_dir.name}: no readable manifest")
            continue
        counts = ",".join(f"{v}{k[0]}" for k, v in m.get("counts", {}).items() if k in ("passed", "failed", "skipped", "errors"))
        print(
            f"{run_dir.name}: {m.get('status')} exit={m.get('exit_code')} wall={m.get('wall_seconds')}s "
            f"{m.get('verdict') or ('COMPLETE' if m.get('complete') else 'PARTIAL')} instrumented={m.get('instrumented')} "
            f"commit={(m.get('commit') or '?')[:10]}{'+dirty' if m.get('dirty') else ''} {counts}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="create or reuse the audit directory and print its path")
    p_init.add_argument("--project", default=".", help="project directory (default: current directory)")
    p_init.add_argument("--new", action="store_true", help="always start a new audit directory")
    p_init.set_defaults(func=cmd_init)

    p_run = sub.add_parser("run", help="run one command and record it")
    p_run.add_argument("--artifacts", required=True, help="audit directory from `init`")
    p_run.add_argument("--label", required=True, help="short name for the run, such as baseline or sample-a")
    p_run.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"time box in seconds (default {DEFAULT_TIMEOUT})")
    p_run.add_argument("--grace", type=float, default=GRACE_SECONDS, help="seconds to wait after SIGINT before SIGTERM")
    p_run.add_argument("--cwd", help="directory to run in (default: current directory)")
    p_run.add_argument("--env", action="append", default=[], metavar="KEY=VALUE", help="set an environment variable")
    p_run.add_argument("--unset", action="append", default=[], metavar="KEY", help="remove an environment variable")
    p_run.add_argument(
        "--instrumented",
        default="auto",
        choices=("auto", "none", "coverage", "mutation", "profile"),
        help="declare instrumentation; instrumented runs never support timing claims",
    )
    p_run.add_argument("--lock-wait", type=float, default=0, help="seconds to wait for another run's lock")
    p_run.add_argument("--no-redirect", action="store_true", help="leave pytest's cache and COVERAGE_FILE alone")
    p_run.add_argument(
        "--timing-plugin",
        action="store_true",
        help="load pytest_audit_timing (no installation) for full-precision phase and fixture timings",
    )
    p_run.add_argument(
        "--leak-probe",
        metavar="PACKAGES",
        help="load pytest_audit_leaks (no installation): name the test during which process-global state changed. "
        "PACKAGES is a comma-separated list of package prefixes whose module-level containers it also checks, or '' for none. Needs -n 0",
    )
    p_run.add_argument(
        "--db-probe",
        action="store_true",
        help="load pytest_audit_db (no installation; needs pytest-django): database isolation mode per test and statements per test",
    )
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="the command, after --")
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list", help="print one line per recorded run")
    p_list.add_argument("--artifacts", required=True)
    p_list.set_defaults(func=cmd_list)

    p_sample = sub.add_parser("sample", help="pick a stratified sample of whole test files")
    p_sample.add_argument("--nodeids", required=True, help="output of `pytest --collect-only -q`")
    p_sample.add_argument("--fraction", type=float, default=0.1, help="share of files per stratum (default 0.1)")
    p_sample.add_argument("--depth", type=int, default=2, help="directory depth that defines a stratum (default 2)")
    p_sample.add_argument("--min-files", type=int, default=1, help="minimum files per stratum (default 1)")
    p_sample.add_argument("--seed", type=int, default=1)
    p_sample.add_argument("--out", required=True, help="file list to write; the plan goes next to it as .json")
    p_sample.set_defaults(func=cmd_sample)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
