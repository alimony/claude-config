"""pytest plugin for Django suites: each test's database isolation mode and the SQL it runs. It observes only.

Load it with `run_suite.py run --db-probe`, which adds this folder to PYTHONPATH
and passes:

    -p pytest_audit_db --audit-db-dir={RUN_DIR}

It needs pytest-django. It refuses an --audit-db-dir inside the project, and it
writes nowhere else.

Isolation modes. At collection, it classifies every selected test the way
Django and pytest-django decide how to reset the database after it:

  unittest:TestCase             django.test.TestCase: a rollback, with class data from setUpTestData
  unittest:TransactionTestCase  TransactionTestCase and the live-server classes: a flush of every table
  pytest:rollback               the django_db mark, or the db fixture
  pytest:transactional          django_db(transaction=True) or (reset_sequences=True), or the
                                transactional_db, live_server, or django_db_reset_sequences fixture
  no-db                         none of these, so the test cannot use the database

"+serialized" marks serialized_rollback, and "+available_apps" a flush limited to
some apps. A --collect-only run gives the counts without touching any database.
--audit-db-times=FILE, a `results.py summary --json-out` file from an
uninstrumented run of the same tests, adds the seconds each mode took there.

Statements. For each test that runs, from the start of its setup to the end of
its teardown, it wraps every database connection with
connection.execute_wrapper() and records statements by verb, INSERT statements
by table, the most repeated SELECT with IN lists collapsed (10 or more repeats
suggests an N+1 query), and the seconds spent inside the database. This works
with DEBUG=False, unlike connection.queries. It counts statements, not rows: one
bulk_create is one INSERT.

It writes into --audit-db-dir, after removing db-*.json files left by an earlier
run there:

  db-<worker>.json  per process that collected or ran tests: "modes" for every test it
                    collected, and "tests", the statement record of every test it ran.
                    Under xdist each worker writes its own file.
  db-summary.json   from the main process, or the xdist controller once every worker
                    has finished: tests (and seconds) per mode, INSERTs per table, and
                    the top tests by INSERTs, statements, and repeats of one SELECT.

The terminal summary stays within 15 lines; every line but the title starts with "db-".

Known gaps: setup is counted in the test that triggers it. The first database
test in each process carries the test database's creation, so warm it with
--reuse-db before you measure, and the first test of a class or module carries
setUpTestData and the class or module fixtures. Statements on other threads,
such as a live server's, and on other connections, such as a second engine or a
raw driver connection, are not seen. Every statement passes through one more
Python call, so the run is instrumented and never backs timing claims.

Standard library, pytest, and pytest-django only; runs on Python 3.8+ with pytest 7+.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path

import pytest

SUMMARY_LINES = 15
MODE_LINES = 7
TOP_TESTS = 20

_WORKER = os.environ.get("PYTEST_XDIST_WORKER", "main")
_MARK_ARGUMENTS = ("transaction", "reset_sequences", "databases", "serialized_rollback", "available_apps")
_TRANSACTIONAL_FIXTURES = {"transactional_db", "live_server", "django_db_reset_sequences"}
_DATABASE_FIXTURES = {"db", "django_db_serialized_rollback"} | _TRANSACTIONAL_FIXTURES
_INSERT_RE = re.compile(r'^\s*INSERT\s+INTO\s+[`"\[]?([^\s`"\[\]()]+)', re.I)
_IN_LIST_RE = re.compile(r"(?:%s,\s*)+%s")

_dir: Path | None = None
_times_file: str | None = None
_times: dict[str, float] = {}
_modes: dict[str, str] = {}
_tests: dict[str, dict] = {}
_summary: dict | None = None


def pytest_addoption(parser):
    group = parser.getgroup("audit-db")
    group.addoption("--audit-db-dir", help="folder for db-<worker>.json and db-summary.json, outside the project")
    group.addoption(
        "--audit-db-times",
        help="a results.py summary --json-out file from an uninstrumented run, for seconds per isolation mode",
    )


def pytest_configure(config):
    global _dir, _times, _times_file
    directory = config.getoption("--audit-db-dir")
    if not directory:
        raise pytest.UsageError("pytest_audit_db: pass --audit-db-dir=DIR, a folder outside the project")
    directory = Path(directory).resolve()
    root = Path(str(config.rootpath)).resolve()
    if directory == root or root in directory.parents:
        raise pytest.UsageError(f"pytest_audit_db: --audit-db-dir must be outside the project ({root})")
    if not config.pluginmanager.hasplugin("django"):
        raise pytest.UsageError("pytest_audit_db: needs pytest-django, which this run does not load")
    if _WORKER == "main":
        _times_file = config.getoption("--audit-db-times")
        if _times_file:
            _times = _read_times(_times_file)
        directory.mkdir(parents=True, exist_ok=True)
        for stale in directory.glob("db-*.json"):
            stale.unlink()
    _dir = directory


def _read_times(path: str) -> dict[str, float]:
    try:
        tests = json.loads(Path(path).read_text())["all_tests"]
        return {test["id"]: float(test.get("total") or 0.0) for test in tests}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise pytest.UsageError(f"pytest_audit_db: cannot read per-test times from {path}: {error}")


def isolation_mode(item) -> str:
    """How the database is reset after this test, as Django and pytest-django decide it."""
    try:
        from django.test import TestCase, TransactionTestCase
    except Exception:  # Django cannot be imported in this process
        return "unknown"
    cls = getattr(item, "cls", None)
    if cls is not None and issubclass(cls, TransactionTestCase):
        mode = "unittest:TestCase" if issubclass(cls, TestCase) else "unittest:TransactionTestCase"
        if getattr(cls, "serialized_rollback", False):
            mode += "+serialized"
        if getattr(cls, "available_apps", None) is not None:
            mode += "+available_apps"
        return mode

    marker = item.get_closest_marker("django_db")
    fixtures = set(getattr(item, "fixturenames", ()))
    if marker is None and not fixtures & _DATABASE_FIXTURES:
        return "no-db"
    options = {}
    if marker is not None:
        options.update(zip(_MARK_ARGUMENTS, marker.args))
        options.update(marker.kwargs)
    flushes = options.get("transaction") or options.get("reset_sequences") or fixtures & _TRANSACTIONAL_FIXTURES
    mode = "pytest:transactional" if flushes else "pytest:rollback"
    if options.get("serialized_rollback") or "django_db_serialized_rollback" in fixtures:
        mode += "+serialized"
    if options.get("available_apps"):
        mode += "+available_apps"
    return mode


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    # trylast: after -k, -m, and other plugins have deselected tests.
    _modes.update((item.nodeid, isolation_mode(item)) for item in items)


class _Recorder:
    """Counts what one test sends to the database, through connection.execute_wrapper()."""

    def __init__(self) -> None:
        self.verbs: Counter = Counter()
        self.inserts: Counter = Counter()
        self.selects: Counter = Counter()
        self.db_seconds = 0.0

    def __call__(self, execute, sql, params, many, context):
        verb = (sql.split(None, 1) or ["?"])[0].upper()
        self.verbs[verb] += 1
        if verb == "INSERT":
            match = _INSERT_RE.match(sql)
            if match:
                self.inserts[match.group(1)] += 1
        elif verb == "SELECT":
            self.selects[_IN_LIST_RE.sub("%s", sql)] += 1
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            self.db_seconds += time.perf_counter() - start

    def attach(self) -> list:
        try:
            from django.db import connections

            wrapped = [connections[alias] for alias in connections]
        except Exception:  # Django is not configured in this run
            return []
        for connection in wrapped:
            connection.execute_wrappers.append(self)
        return wrapped

    def detach(self, wrapped: list) -> None:
        for connection in wrapped:
            if self in connection.execute_wrappers:
                connection.execute_wrappers.remove(self)

    def record(self, seconds: float) -> dict:
        sql, repeats = (self.selects.most_common(1) or [("", 0)])[0]
        return {
            "statements": sum(self.verbs.values()),
            "inserts": self.verbs["INSERT"],
            "by_verb": dict(self.verbs),
            "inserts_by_table": dict(self.inserts),
            "max_repeat_select": repeats,
            "max_repeat_sql": sql[:200],
            "db_seconds_instrumented": round(self.db_seconds, 6),
            "seconds_instrumented": round(seconds, 6),
        }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    recorder = _Recorder()
    wrapped = recorder.attach()
    start = time.perf_counter()
    yield
    recorder.detach(wrapped)
    _tests[item.nodeid] = recorder.record(time.perf_counter() - start)


def _summarise(directory: Path) -> dict:
    modes: dict[str, str] = {}
    tests: dict[str, dict] = {}
    files = []
    for path in sorted(directory.glob("db-*.json")):
        if path.name == "db-summary.json":
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        files.append(path.name)
        modes.update(data.get("modes", {}))
        tests.update(data.get("tests", {}))

    per_mode: dict[str, dict] = {}
    timed = 0
    for nodeid, mode in modes.items():
        entry = per_mode.setdefault(mode, {"tests": 0, "seconds": 0.0})
        entry["tests"] += 1
        if nodeid in _times:
            entry["seconds"] += _times[nodeid]
            timed += 1
    order = sorted(per_mode, key=lambda m: (-per_mode[m]["seconds"], -per_mode[m]["tests"], m))
    for mode in order:
        per_mode[mode]["share"] = round(100 * per_mode[mode]["tests"] / max(len(modes), 1), 1)
        per_mode[mode]["seconds"] = round(per_mode[mode]["seconds"], 3)

    inserts: Counter = Counter()
    for record in tests.values():
        inserts.update(record.get("inserts_by_table", {}))
    seconds = sum(record.get("seconds_instrumented", 0.0) for record in tests.values())
    db_seconds = sum(record.get("db_seconds_instrumented", 0.0) for record in tests.values())

    def top(key: str) -> list[dict]:
        ranked = sorted(tests.items(), key=lambda kv: (-kv[1].get(key, 0), kv[0]))
        rows = []
        for nodeid, record in ranked[:TOP_TESTS]:
            if not record.get(key):
                break
            row = {"test": nodeid, "count": record[key], "mode": modes.get(nodeid, "unknown")}
            if key == "max_repeat_select":
                row["sql"] = record.get("max_repeat_sql", "")
            rows.append(row)
        return rows

    return {
        "files": files,
        "tests_collected": len(modes),
        "seconds_from": _times_file,
        "tests_with_seconds": timed,
        "modes": {mode: per_mode[mode] for mode in order},
        "tests_run": len(tests),
        "statements": sum(record.get("statements", 0) for record in tests.values()),
        "database_share_instrumented": round(100 * db_seconds / seconds, 1) if seconds else 0.0,
        "inserts_by_table": dict(inserts.most_common()),
        "top_inserts": top("inserts"),
        "top_statements": top("statements"),
        "top_repeated_selects": top("max_repeat_select"),
    }


def pytest_sessionfinish(session):
    global _summary
    if _dir is None:
        return
    if _modes or _tests:
        payload = {"worker": _WORKER, "modes": _modes, "tests": _tests}
        (_dir / f"db-{_WORKER}.json").write_text(json.dumps(payload))
    if _WORKER == "main":
        # Under xdist, every worker has written its file before it reports itself finished.
        _summary = _summarise(_dir)
        (_dir / "db-summary.json").write_text(json.dumps(_summary, indent=1))


def pytest_terminal_summary(terminalreporter, config):
    if _summary is None:
        return
    lines = []
    modes = list(_summary["modes"].items())
    with_seconds = bool(_summary["seconds_from"])
    for mode, entry in modes[:MODE_LINES]:
        seconds = f"{entry['seconds']:9.1f} s  " if with_seconds else ""
        lines.append(f"db-mode {entry['tests']:7d} {entry['share']:5.1f}%  {seconds}{mode}")
    if len(modes) > MODE_LINES:
        lines.append(f"db-mode … {len(modes) - MODE_LINES} more modes in db-summary.json")
    run = _summary["tests_run"]
    if run:
        lines.append(
            f"db-sql {run} tests ran {_summary['statements']} statements; "
            f"{_summary['database_share_instrumented']:.0f}% of their time was in the database (instrumented)"
        )
        tables = list(_summary["inserts_by_table"].items())[:3]
        if tables:
            lines.append("db-sql INSERTs per test: " + ", ".join(f"{table} {count / run:.2f}" for table, count in tables))
        for key, label in (("top_inserts", "INSERTs"), ("top_statements", "statements"), ("top_repeated_selects", "repeats of one SELECT")):
            if _summary[key]:
                lines.append(f"db-sql most {label}: {_summary[key][0]['count']} in {_summary[key][0]['test']}")
    timed = f"; seconds for {_summary['tests_with_seconds']} of {_summary['tests_collected']} tests" if with_seconds else ""
    lines.append(f"db-probe details: {_dir / 'db-summary.json'}{timed}")
    terminalreporter.write_sep("-", "database probe")
    for line in lines[: SUMMARY_LINES - 1]:
        terminalreporter.write_line(line)
