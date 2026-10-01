"""pytest plugin: per-phase test timings and per-fixture setup cost, with no installation.

Load it from this folder, which holds nothing else, so it cannot shadow the
project's own imports:

    PYTHONPATH=<this folder> python -m pytest -p pytest_audit_timing ...

`run_suite.py run --timing-plugin` does this through PYTHONPATH and
PYTEST_ADDOPTS, and points AUDIT_TIMING_DIR at the run folder.

It writes into AUDIT_TIMING_DIR (default: the current directory):

  timing.jsonl            one line per test phase in pytest-reportlog's shape, with full-precision
                          durations, start and stop times, and the xdist worker. Only the main
                          process writes it: under xdist the controller receives every report.
  fixtures-<worker>.json  per fixture definition: setups, total and maximum seconds, teardowns
                          and teardown seconds, scope, and where it is defined. Both times exclude
                          the fixtures it depends on. Teardown is timed by wrapping pytest's
                          FixtureDef.finish (pytest 7 to 9), which only observes; if that method
                          is missing, teardown fields stay at zero.

Each line is flushed as it is written, so a stopped run keeps its data. The
overhead is a few microseconds per phase and per fixture setup.

Standard library and pytest only; runs on Python 3.8+ with pytest 7+.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

_WORKER = os.environ.get("PYTEST_XDIST_WORKER", "main")
_DIR = Path(os.environ.get("AUDIT_TIMING_DIR", "."))
_stats: dict[str, dict] = {}
_log = None
_finishing: list[float] = []  # nested teardown seconds per open FixtureDef.finish call


def _entry(fixturedef) -> dict:
    key = f"{fixturedef.baseid}::{fixturedef.argname}"
    entry = _stats.get(key)
    if entry is None:
        entry = _stats[key] = {
            "name": fixturedef.argname,
            "scope": fixturedef.scope,
            "defined_in": fixturedef.baseid or "(plugin or root conftest)",
            "setups": 0,
            "total_seconds": 0.0,
            "max_seconds": 0.0,
            "teardowns": 0,
            "teardown_seconds": 0.0,
        }
    return entry


def _time_teardowns() -> None:
    try:
        from _pytest.fixtures import FixtureDef
    except ImportError:
        return
    original = getattr(FixtureDef, "finish", None)
    if original is None or getattr(original, "_audit_timed", False):
        return

    def finish(self, request):
        # A fixture's finish also finishes the fixtures that depend on it; subtract those.
        was_set_up = getattr(self, "cached_result", None) is not None  # finish() resets it
        _finishing.append(0.0)
        start = time.perf_counter()
        try:
            return original(self, request)
        finally:
            elapsed = time.perf_counter() - start
            nested = _finishing.pop()
            if _finishing:
                _finishing[-1] += elapsed
            if was_set_up:
                entry = _entry(self)
                entry["teardowns"] += 1
                entry["teardown_seconds"] += max(0.0, elapsed - nested)

    finish._audit_timed = True  # type: ignore[attr-defined]
    FixtureDef.finish = finish


def pytest_configure(config):
    global _log
    _DIR.mkdir(parents=True, exist_ok=True)
    _time_teardowns()
    if _WORKER == "main":
        _log = open(_DIR / "timing.jsonl", "a", buffering=1)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    entry = _entry(fixturedef)
    entry["setups"] += 1
    entry["total_seconds"] += elapsed
    entry["max_seconds"] = max(entry["max_seconds"], elapsed)


def pytest_runtest_logreport(report):
    if _log is None:
        return
    record = {
        "$report_type": "TestReport",
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
        "duration": report.duration,
        "start": getattr(report, "start", None),
        "stop": getattr(report, "stop", None),
    }
    if hasattr(report, "wasxfail"):
        record["wasxfail"] = report.wasxfail
    gateway = getattr(getattr(report, "node", None), "gateway", None)
    if gateway is not None:
        record["worker"] = getattr(gateway, "id", None)
    _log.write(json.dumps(record) + "\n")


def pytest_sessionfinish(session):
    # An xdist controller sets up no fixtures, so it writes no fixtures file.
    if _stats:
        rows = sorted(_stats.values(), key=lambda s: -s["total_seconds"])
        for row in rows:
            row["total_seconds"] = round(row["total_seconds"], 6)
            row["max_seconds"] = round(row["max_seconds"], 6)
            row["teardown_seconds"] = round(row["teardown_seconds"], 6)
        (_DIR / f"fixtures-{_WORKER}.json").write_text(json.dumps(rows, indent=1))
    if _log is not None:
        _log.close()
