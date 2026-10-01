from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

import run_suite
from conftest import SCRIPTS_DIR, plugin_available

pytestmark = [
    pytest.mark.skipif(shutil.which("git") is None, reason="needs git"),
    pytest.mark.skipif(not plugin_available("pytest_cov"), reason="needs pytest-cov"),
]

SCRIPT = SCRIPTS_DIR / "pseudo_tested.py"

PRICING = '''
def discount(total, is_member):
    """Members get 10% off orders of 100 or more."""
    if is_member and total >= 100:
        return round(total * 0.9, 2)
    return total


def audit_log(event):
    message = f"AUDIT: {event}"
    print(message)


def is_empty(items) -> bool:
    count = len(items)
    return count == 0


def shipping(weight):
    if weight <= 0:
        raise ValueError("weight must be positive")
    return 5 + weight * 2


def load_rate():
    rate = 0.25
    return rate
'''

QUEUE = '''
def first_ready(queue):
    item = queue[0] if queue else None
    return item
'''

TEST_PRICING = '''
import pytest

from shop.pricing import audit_log, discount, is_empty, load_rate

RATE = load_rate() * 2  # used at import time: the "return None" mutant breaks collection


def test_discount():
    assert discount(200, True) == 180
    assert discount(200, False) == 200


@pytest.mark.parametrize("event", ["a b", "x::y"])
def test_audit_log_runs(event):
    audit_log(event)  # no assertion: audit_log is pseudo-tested


def test_is_empty():
    assert is_empty([])  # only the empty case: "return True" survives


def test_rate():
    assert RATE == 0.5
    assert load_rate() == 0.25
'''

TEST_QUEUE = '''
import time

from shop.queue import first_ready


def test_first_ready():
    queue = ["job"]
    deadline = time.monotonic() + 60
    while first_ready(queue) is None and time.monotonic() < deadline:
        time.sleep(0.01)  # the "return None" mutant keeps this loop waiting
    assert first_ready(queue) == "job"
'''


def git(cwd: Path, *args: str) -> str:
    command = ["git", "-c", "user.email=audit@example.com", "-c", "user.name=audit", *args]
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def origin(tmp_path: Path) -> Path:
    project = tmp_path / "shop"
    (project / "src" / "shop").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "pyproject.toml").write_text('[tool.pytest.ini_options]\npythonpath = ["src"]\n')
    (project / "src" / "shop" / "__init__.py").write_text("")
    (project / "src" / "shop" / "pricing.py").write_text(textwrap.dedent(PRICING).lstrip())
    (project / "src" / "shop" / "queue.py").write_text(textwrap.dedent(QUEUE).lstrip())
    (project / "tests" / "test_pricing.py").write_text(textwrap.dedent(TEST_PRICING).lstrip())
    (project / "tests" / "test_queue.py").write_text(textwrap.dedent(TEST_QUEUE).lstrip())
    git(project, "init", "-q")
    git(project, "add", "-A")
    git(project, "commit", "-qm", "init")
    return project


@pytest.fixture
def audit(tmp_path, monkeypatch, origin, capsys) -> Path:
    monkeypatch.setenv("TEST_SUITE_AUDIT_HOME", str(tmp_path / "home"))
    assert run_suite.main(["init", "--project", str(origin)]) == 0
    return Path(capsys.readouterr().out.strip().splitlines()[-1])


@pytest.fixture
def copy(audit, origin) -> Path:
    """The disposable copy, made the way guardrail 6 says: git clone --local ROOT AUDIT/work/NAME."""
    target = audit / "work" / "shop"
    git(origin, "clone", "-q", "--local", str(origin), str(target))
    return target


def find(audit: Path, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    command = [sys.executable, str(SCRIPT), "--audit", str(audit), *args]
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)


def sources(project: Path) -> dict:
    return {p.relative_to(project).as_posix(): p.read_bytes() for p in sorted((project / "src").rglob("*.py"))}


def test_classifies_functions_and_keeps_unknown_verdicts_apart(audit, origin, copy, tmp_path):
    out = tmp_path / "pseudo.jsonl"
    # "-p no:cacheprovider" is a two-token flag: it must reach every pytest run unchanged.
    run = find(audit, copy, "--src", "src/shop", "--out", str(out), "--tests", "tests", "--timeout", "3", "--", "-p", "no:cacheprovider")
    assert run.returncode == 0, run.stdout + run.stderr
    records = {r["function"]: r for r in map(json.loads, out.read_text().splitlines())}
    assert {name: r["status"] for name, r in records.items()} == {
        "discount": "tested",
        "audit_log": "pseudo-tested",
        "is_empty": "partially-tested",
        "load_rate": "unknown",
        "first_ready": "unknown",
    }
    assert "shipping" not in records, "an uncovered function is a coverage finding, not a mutant"
    assert records["is_empty"]["verdicts"] == {"return None": "killed", "return True": "survived", "return False": "killed"}
    # A broken collection and a timeout are unknown verdicts, never kills.
    assert records["load_rate"]["verdicts"] == {"return None": "unknown"}
    assert records["load_rate"]["exit_codes"]["return None"] not in (0, 1, "timeout")
    assert records["first_ready"]["exit_codes"] == {"return None": "timeout"}
    # Node IDs with spaces and "::" reach the mutant runs intact; otherwise this mutant would be unknown.
    assert records["audit_log"]["tests"] == [
        "tests/test_pricing.py::test_audit_log_runs[a b]",
        "tests/test_pricing.py::test_audit_log_runs[x::y]",
    ]
    lines = run.stdout.strip().splitlines()
    assert len(lines) <= 15
    assert "pseudo_tested: complete: mutated 5 of 5 planned functions" in lines
    assert "pseudo-tested share: 1 of 3 classified functions = 33.3% (95% Wilson interval 6.1% to 79.2%)" in lines
    assert "skipped: 1 uncovered" in lines
    assert sources(copy) == sources(origin) and git(copy, "status", "--porcelain") == ""
    assert not (copy / ".pytest_cache").exists(), "the two-token flag did not reach every run"
    assert not list(copy.glob(".coverage*")), "coverage data belongs in the script's temporary directory"


def test_stops_when_the_canary_fails(audit, copy, tmp_path):
    test_file = copy / "tests" / "test_pricing.py"
    test_file.write_text(test_file.read_text().replace("== 180", "== 181"))
    git(copy, "commit", "-qam", "a failing test")
    out = tmp_path / "pseudo.jsonl"
    before = sources(copy)
    run = find(audit, copy, "--src", "src/shop", "--out", str(out), "--tests", "tests")
    assert run.returncode == 3
    assert "canary failed" in run.stdout and "test_discount" in run.stdout
    assert not out.exists() and sources(copy) == before


def test_refuses_to_mutate_outside_the_audit_directory(audit, origin, copy, tmp_path):
    out = tmp_path / "pseudo.jsonl"
    from_origin = find(audit, origin, "--src", "src/shop", "--out", str(out))
    assert from_origin.returncode == 2 and "outside the audit directory" in from_origin.stdout
    elsewhere = find(audit, copy, "--src", str(origin / "src" / "shop"), "--out", str(out))
    assert elsewhere.returncode == 2 and "outside the audit directory" in elsewhere.stdout
    no_state = find(tmp_path, copy, "--src", "src/shop", "--out", str(out))
    assert no_state.returncode == 2 and "no STATE.md" in no_state.stdout
    assert not out.exists() and git(origin, "status", "--porcelain") == ""


def test_refuses_a_tree_with_tracked_changes(audit, copy, tmp_path):
    queue = copy / "src" / "shop" / "queue.py"
    queue.write_text(queue.read_text().replace("return item", "return None  # extreme mutant"))
    run = find(audit, copy, "--src", "src/shop", "--out", str(tmp_path / "pseudo.jsonl"))
    assert run.returncode == 2 and "tracked files differ" in run.stdout


@pytest.mark.skipif(os.name != "posix", reason="needs POSIX signals")
def test_sigterm_restores_the_mutated_file(audit, copy, tmp_path):
    queue = copy / "src" / "shop" / "queue.py"
    original = queue.read_bytes()
    command = [sys.executable, str(SCRIPT), "--audit", str(audit), "--src", "src/shop/queue.py",
               "--out", str(tmp_path / "pseudo.jsonl"), "--tests", "tests/test_queue.py", "--timeout", "60"]
    proc = subprocess.Popen(command, cwd=copy, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 30
        while b"# extreme mutant" not in queue.read_bytes():  # the hanging mutant is on disk
            assert proc.poll() is None and time.monotonic() < deadline, "the mutant never appeared"
            time.sleep(0.02)
        proc.send_signal(signal.SIGTERM)
        _, err = proc.communicate(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert proc.returncode == 128 + signal.SIGTERM
    assert "restored: src/shop/queue.py" in err
    assert queue.read_bytes() == original and git(copy, "status", "--porcelain") == ""
