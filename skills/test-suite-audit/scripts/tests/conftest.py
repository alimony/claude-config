"""Shared helpers for the audit scripts' tests.

Run with any Python that has pytest (plus pytest-cov and pytest-reportlog for
the tests that exercise them), for example:
    python -m pytest -p no:cacheprovider skills/test-suite-audit/scripts/tests

The corpus/ folder is a tiny project with planted defects and decoys. It is
never collected here; tests copy it to a temporary directory before running it,
so nothing is written into the repository.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
CORPUS = TESTS_DIR / "corpus"
sys.path.insert(0, str(SCRIPTS_DIR))

collect_ignore = ["corpus"]


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """A private copy of the corpus project."""
    target = tmp_path / "corpus"
    shutil.copytree(CORPUS, target, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".coverage*"))
    return target


def run_pytest(project: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run the corpus suite in a fixed order, without writing bytecode or cache into the project."""
    command = [sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-p", "no:cacheprovider", *args]
    return subprocess.run(command, cwd=project, capture_output=True, text=True, env=env, timeout=300)


def plugin_available(name: str) -> bool:
    try:
        __import__(name)
    except ImportError:
        return False
    return True
