from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

import run_suite
from conftest import plugin_available

REGISTRY = """
HANDLERS = {}
TIMEOUT = 30
LIMIT = 1000000
MODES = ["fast"]
COUNTER = 0


def lookup(name):
    return HANDLERS.get(name)


class Registry:
    items = []


class Form(dict):
    pass


class Builder:
    shared = Form()  # a class-level mutable default, shared by every instance
"""

TESTS = """
import os
import sys
import threading
from unittest import mock

import pytest

import leaky.registry as registry

STOP = threading.Event()


def test_registers_handler():
    registry.HANDLERS["csv"] = object()


def test_appends_to_class_attribute():
    registry.Registry.items.append(1)


def test_fills_shared_default():
    registry.Builder().shared["x"] = "1"


def test_changes_setting():
    registry.TIMEOUT = 0


def test_patches_without_stopping():
    mock.patch.object(registry, "lookup").start()


def test_sets_env():
    os.environ["LEAKY_MODE"] = "on"


def test_extends_sys_path():
    sys.path.append("/nonexistent/leaky")


def test_starts_thread():
    threading.Thread(target=STOP.wait, name="leaky-worker", daemon=True).start()


def test_clean_with_monkeypatch(monkeypatch, tmp_path):
    monkeypatch.setenv("LEAKY_MODE", "off")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(registry.HANDLERS, "json", object())
    monkeypatch.setattr(registry, "TIMEOUT", 5)
    assert registry.HANDLERS["json"] is not None


def test_restores_equal_copies():
    registry.MODES = list(registry.MODES)
    registry.LIMIT = int("1000000")


@pytest.mark.parametrize("n", range(6))
def test_counts(n):
    registry.COUNTER += 1


def test_reads_only():
    assert registry.HANDLERS.get("missing") is None
"""


@pytest.fixture
def leaky(tmp_path: Path) -> Path:
    project = tmp_path / "leaky-project"
    (project / "leaky").mkdir(parents=True)
    (project / "leaky" / "__init__.py").write_text("")
    (project / "leaky" / "registry.py").write_text(textwrap.dedent(REGISTRY))
    (project / "tests").mkdir()
    (project / "tests" / "test_leaks.py").write_text(textwrap.dedent(TESTS))
    (project / "pyproject.toml").write_text('[tool.pytest.ini_options]\npythonpath = ["."]\n')
    return project


@pytest.fixture
def audit(tmp_path, monkeypatch, leaky, capsys) -> Path:
    monkeypatch.setenv("TEST_SUITE_AUDIT_HOME", str(tmp_path / "home"))
    assert run_suite.main(["init", "--project", str(leaky)]) == 0
    return Path(capsys.readouterr().out.strip().splitlines()[-1])


def probe(audit: Path, project: Path, *extra: str) -> tuple[int, Path]:
    command = [sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-p", "no:cacheprovider", "-q", *extra]
    code = run_suite.main(["run", "--artifacts", str(audit), "--label", "leaks", "--cwd", str(project), "--leak-probe", "leaky", "--", *command])
    return code, sorted((audit / "runs").iterdir())[-1]


def test_names_the_test_that_changed_state(audit, leaky, capsys):
    code, run_dir = probe(audit, leaky, "-p", "no:xdist")
    out = capsys.readouterr().out
    assert code == 0, out
    report = json.loads((run_dir / "leaks.json").read_text())
    changes = {nodeid.rpartition("::")[2]: found for nodeid, found in report["changes"].items()}
    assert changes == {
        "test_registers_handler": ["leaky.registry.HANDLERS (contents changed)"],
        "test_appends_to_class_attribute": ["leaky.registry.Registry.items (contents changed)"],
        "test_fills_shared_default": ["leaky.registry.Builder.shared (contents changed)"],
        "test_changes_setting": ["leaky.registry.TIMEOUT (rebound)"],
        "test_patches_without_stopping": ["leaky.registry.lookup (rebound)", "unittest.mock patches started and not stopped"],
        "test_sets_env": ["os.environ: LEAKY_MODE"],
        "test_extends_sys_path": ["sys.path"],
        "test_starts_thread": ["threads"],
    }
    assert report["tests_checked"] == 17 and report["tests_with_changes"] == 8
    assert report["churn"] == {"leaky.registry.COUNTER (rebound)": {"tests": 6, "first": [f"tests/test_leaks.py::test_counts[{n}]" for n in range(3)]}}
    assert "leaks: 8 of 17 tests changed process-global state, and 1 place changed in more than 5 tests each" in out
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["instrumented"] == "profile" and manifest["complete"] is True
    assert not list(leaky.rglob("leaks.json")), "the report belongs in the run folder, not the project"


def test_without_packages_checks_only_process_state(audit, leaky, capsys):
    command = [sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-p", "no:cacheprovider", "-p", "no:xdist", "-q"]
    assert run_suite.main(["run", "--artifacts", str(audit), "--label", "leaks", "--cwd", str(leaky), "--leak-probe", "", "--", *command]) == 0
    report = json.loads((sorted((audit / "runs").iterdir())[-1] / "leaks.json").read_text())
    assert report["packages"] == [] and report["tests_with_changes"] == 4  # patch count, environ, sys.path, thread
    assert capsys.readouterr()


@pytest.mark.skipif(not plugin_available("xdist"), reason="needs pytest-xdist")
def test_refuses_xdist(audit, leaky, capsys):
    code, run_dir = probe(audit, leaky, "-n", "2")
    out = capsys.readouterr().out
    assert code == 4
    assert "WARNING: --leak-probe wrote no leaks.json" in out
    assert "run with -n 0" in (run_dir / "output.log").read_text()
