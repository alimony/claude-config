"""run_suite.py run --db-probe (pytest_plugin/pytest_audit_db.py) on a tiny Django project on SQLite."""
from __future__ import annotations

import json
import os
import sys
import textwrap
from pathlib import Path

import pytest

import run_suite
from conftest import SCRIPTS_DIR, plugin_available, run_pytest

pytest.importorskip("django")
pytest.importorskip("pytest_django")

PYPROJECT = """
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "dbsite.settings"
pythonpath = ["."]
"""

SETTINGS = """
SECRET_KEY = "db-probe-tests"
INSTALLED_APPS = ["shop"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
"""

MODELS = """
from django.db import models


class Org(models.Model):
    name = models.CharField(max_length=50)


class Account(models.Model):
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
"""

TESTS = """
import pytest
from django.test import TestCase, TransactionTestCase

from shop.models import Account, Org


@pytest.mark.django_db
def test_rollback_writes_rows():
    org = Org.objects.create(name="o")
    Account.objects.create(org=org)
    Account.objects.create(org=org)
    assert Account.objects.count() == 2


@pytest.mark.django_db(transaction=True)
def test_transactional():
    Org.objects.create(name="t")
    assert Org.objects.count() == 1


class TestRollbackClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Org.objects.create(name="class")

    def test_reads(self):
        assert Org.objects.filter(name="class").exists()

    def test_reads_again(self):
        assert Org.objects.count() == 1


class TestFlushClass(TransactionTestCase):
    def test_flushes(self):
        Org.objects.create(name="f")
        assert Org.objects.count() == 1


def test_no_database():
    assert 1 + 1 == 2


@pytest.mark.django_db
def test_bulk_create():
    Org.objects.bulk_create([Org(name=str(i)) for i in range(5)])
    assert Org.objects.count() == 5


@pytest.mark.django_db
def test_n_plus_one():
    org = Org.objects.create(name="n")
    Account.objects.bulk_create([Account(org=org) for _ in range(12)])
    assert [account.org.name for account in Account.objects.all()] == ["n"] * 12
"""

MODES = {
    "pytest:rollback": 3,
    "unittest:TestCase": 2,
    "pytest:transactional": 1,
    "unittest:TransactionTestCase": 1,
    "no-db": 1,
}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "db-project"
    for package in ("dbsite", "shop", "tests"):
        (root / package).mkdir(parents=True)
        (root / package / "__init__.py").write_text("")
    (root / "pyproject.toml").write_text(textwrap.dedent(PYPROJECT))
    (root / "dbsite" / "settings.py").write_text(textwrap.dedent(SETTINGS))
    (root / "shop" / "models.py").write_text(textwrap.dedent(MODELS))
    (root / "tests" / "test_modes.py").write_text(textwrap.dedent(TESTS))
    return root


@pytest.fixture
def audit(tmp_path, monkeypatch, project, capsys) -> Path:
    monkeypatch.setenv("TEST_SUITE_AUDIT_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
    assert run_suite.main(["init", "--project", str(project)]) == 0
    return Path(capsys.readouterr().out.strip().splitlines()[-1])


def probe(audit: Path, project: Path, *extra: str) -> tuple[int, Path]:
    command = [sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-p", "no:cacheprovider", "-q", *extra]
    code = run_suite.main(["run", "--artifacts", str(audit), "--label", "db", "--cwd", str(project), "--db-probe", "--", *command])
    return code, sorted((audit / "runs").iterdir())[-1]


def summary_lines(run_dir: Path) -> list[str]:
    lines = (run_dir / "output.log").read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if "database probe" in line)
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if not line.startswith("db-"):
            break
        block.append(line)
    return block


def by_test(records: dict) -> dict:
    return {nodeid.split("::", 1)[1]: record for nodeid, record in records.items()}


def test_counts_modes_inserts_and_repeated_selects(audit, project, capsys):
    code, run_dir = probe(audit, project, "-p", "no:xdist")
    out = capsys.readouterr().out
    assert code == 0, out + (run_dir / "output.log").read_text()

    summary = json.loads((run_dir / "db-summary.json").read_text())
    assert {mode: entry["tests"] for mode, entry in summary["modes"].items()} == MODES
    assert summary["tests_collected"] == summary["tests_run"] == 8
    assert summary["files"] == ["db-main.json"]
    assert summary["inserts_by_table"] == {"shop_org": 6, "shop_account": 3}

    tests = by_test(json.loads((run_dir / "db-main.json").read_text())["tests"])
    assert tests["test_rollback_writes_rows"]["inserts_by_table"] == {"shop_org": 1, "shop_account": 2}
    assert tests["test_bulk_create"]["inserts_by_table"] == {"shop_org": 1}  # statements, not rows
    assert tests["TestRollbackClass::test_reads"]["inserts_by_table"] == {"shop_org": 1}  # setUpTestData
    assert tests["TestRollbackClass::test_reads_again"]["inserts"] == 0
    assert tests["test_no_database"]["statements"] == 0

    worst = summary["top_repeated_selects"][0]
    assert worst["test"].endswith("::test_n_plus_one") and worst["count"] == 12 and worst["mode"] == "pytest:rollback"
    assert 'FROM "shop_org"' in worst["sql"]

    block = summary_lines(run_dir)
    assert 3 <= len(block) <= 15
    assert any(line.startswith("db-mode") and line.endswith("pytest:rollback") for line in block)
    assert any(line.startswith("db-sql most repeats of one SELECT: 12 in tests/test_modes.py::test_n_plus_one") for line in block)

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["instrumented"] == "profile" and manifest["complete"] is True
    assert not list(project.rglob("db-*.json")), "the probe's files belong in the run folder, not the project"


def test_collect_only_counts_modes_and_adds_baseline_seconds(audit, project, tmp_path, capsys):
    times = tmp_path / "baseline-summary.json"
    times.write_text(json.dumps({"all_tests": [
        {"id": "tests/test_modes.py::test_transactional", "total": 0.75},
        {"id": "tests/test_modes.py::TestFlushClass::test_flushes", "total": 0.5},
        {"id": "tests/test_modes.py::test_bulk_create", "total": 0.01},
    ]}))
    code, run_dir = probe(audit, project, "--collect-only", f"--audit-db-times={times}")
    assert capsys.readouterr()
    assert code == 0, (run_dir / "output.log").read_text()

    summary = json.loads((run_dir / "db-summary.json").read_text())
    assert summary["tests_run"] == 0 and summary["tests_collected"] == 8
    assert {mode: entry["tests"] for mode, entry in summary["modes"].items()} == MODES
    assert summary["modes"]["pytest:transactional"]["seconds"] == 0.75
    assert summary["modes"]["unittest:TransactionTestCase"]["seconds"] == 0.5
    assert list(summary["modes"])[:2] == ["pytest:transactional", "unittest:TransactionTestCase"]  # ranked by seconds
    assert summary["tests_with_seconds"] == 3
    block = summary_lines(run_dir)
    assert not any(line.startswith("db-sql") for line in block)
    assert block[-1].endswith("seconds for 3 of 8 tests")


@pytest.mark.skipif(not plugin_available("xdist"), reason="needs pytest-xdist")
def test_xdist_writes_one_file_per_worker(audit, project, capsys):
    # loadscope keeps TestRollbackClass on one worker. Under --dist load its two tests can
    # land on both workers, and setUpTestData then inserts its row twice.
    code, run_dir = probe(audit, project, "-n", "2", "--dist", "loadscope")
    assert capsys.readouterr()
    assert code == 0, (run_dir / "output.log").read_text()
    summary = json.loads((run_dir / "db-summary.json").read_text())
    assert summary["files"] == ["db-gw0.json", "db-gw1.json"]  # the controller collects nothing
    assert summary["tests_run"] == summary["tests_collected"] == 8
    assert {mode: entry["tests"] for mode, entry in summary["modes"].items()} == MODES
    assert summary["inserts_by_table"] == {"shop_org": 6, "shop_account": 3}


def test_refuses_to_write_into_the_project_or_without_pytest_django(project, tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}
    env["PYTHONPATH"] = str(SCRIPTS_DIR / "pytest_plugin")
    cases = [
        ([], "pass --audit-db-dir"),
        ([f"--audit-db-dir={project / 'out'}"], "must be outside the project"),
        ([f"--audit-db-dir={tmp_path / 'out'}", "-p", "no:django"], "needs pytest-django"),
    ]
    for options, message in cases:
        result = run_pytest(project, "-p", "pytest_audit_db", *options, "--collect-only", "-q", env=env)
        assert result.returncode == 4, result.stdout + result.stderr
        assert message in result.stdout + result.stderr
    assert not (project / "out").exists()
