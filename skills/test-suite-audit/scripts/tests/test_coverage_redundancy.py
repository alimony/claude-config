from __future__ import annotations

import json
import os
import sys

import pytest

import coverage_redundancy
from conftest import plugin_available, run_pytest

pytestmark = pytest.mark.skipif(not plugin_available("pytest_cov"), reason="needs pytest-cov")


@pytest.fixture
def measured(corpus, tmp_path):
    data = tmp_path / ".coverage"
    env = dict(os.environ, COVERAGE_FILE=str(data), COVERAGE_CORE="ctrace")
    proc = run_pytest(corpus, "-q", "--cov=shop", "--cov-context=test", "--cov-report=", env=env)
    assert proc.returncode == 0, proc.stdout[-2000:]
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text(run_pytest(corpus, "--collect-only", "-q").stdout)
    return data, nodeids


def analyse(tmp_path, *args):
    out = tmp_path / "redundancy.json"
    assert coverage_redundancy.main([*map(str, args), "--json-out", str(out)]) == 0
    return json.loads(out.read_text())


def test_finds_identical_subsumed_and_sibling_tests(measured, tmp_path):
    data, nodeids = measured
    result = analyse(tmp_path, data, "--nodeids", nodeids)
    groups = [set(g["tests"]) for g in result["identical"]]
    assert {"tests/test_codec.py::test_dumps_sorted", "tests/test_codec.py::test_dumps_sorted_copy"} in groups
    assert {"tests/test_pricing.py::test_parse_price_dollars", "tests/test_pricing.py::test_parse_price_plain", "tests/test_pricing.py::test_parse_price_spaces"} in groups
    subsumed = {(s["test"], s["contained_in"]) for s in result["subsumed"]}
    assert ("tests/test_codec.py::test_dumps_sorted", "tests/test_codec.py::test_round_trip") in subsumed
    assert any(s["test"] == "tests/test_pricing.py::test_discount_zero_percent" and s["cases"] == 4 for s in result["siblings"])
    assert "tests/test_mocks.py::test_unspecced_mock" in result["no_product"]


def test_decoy_end_to_end_test_is_only_ever_a_candidate(measured, tmp_path):
    data, _ = measured
    result = analyse(tmp_path, data)
    # The slow end-to-end test covers the same lines as unit tests: coverage alone
    # cannot tell them apart, which is why removal needs a second kind of evidence.
    together = [g for g in result["identical"] if "tests/test_slow.py::test_checkout_end_to_end" in g["tests"]]
    assert together and "tests/test_pricing.py::test_total" in together[0]["tests"]


def test_parametrised_siblings_are_not_reported_as_duplicates_of_each_other(measured, tmp_path):
    data, _ = measured
    result = analyse(tmp_path, data)
    for group in result["identical"]:
        families = {t.split("[", 1)[0] for t in group["tests"]}
        assert len(families) == len(group["tests"]), group


def test_scope_module_keeps_files_apart(measured, tmp_path):
    data, _ = measured
    result = analyse(tmp_path, data, "--scope", "module")
    for group in result["identical"]:
        assert len({t.split("::", 1)[0] for t in group["tests"]}) == 1


@pytest.mark.skipif(sys.version_info < (3, 12), reason="sys.monitoring needs Python 3.12+")
def test_first_hit_only_data_is_refused(corpus, tmp_path, capsys):
    data = tmp_path / ".coverage-sysmon"
    env = dict(os.environ, COVERAGE_FILE=str(data), COVERAGE_CORE="sysmon")
    assert run_pytest(corpus, "-q", "--cov=shop", "--cov-context=test", "--cov-report=", env=env).returncode == 0
    assert coverage_redundancy.main([str(data)]) == 2
    assert "COVERAGE_CORE=ctrace" in capsys.readouterr().out


def test_data_without_contexts_is_refused(corpus, tmp_path):
    data = tmp_path / ".coverage-plain"
    env = dict(os.environ, COVERAGE_FILE=str(data))
    assert run_pytest(corpus, "-q", "--cov=shop", "--cov-report=", env=env).returncode == 0
    assert coverage_redundancy.main([str(data)]) == 1


def test_manifest_without_ctrace_is_refused(measured, tmp_path, capsys):
    data, _ = measured
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / ".coverage").write_bytes(data.read_bytes())
    (run_dir / "manifest.json").write_text(json.dumps({"env": {}}))
    assert coverage_redundancy.main([str(run_dir / ".coverage")]) == 2
    assert "COVERAGE_CORE" in capsys.readouterr().out
    assert coverage_redundancy.main([str(run_dir / ".coverage"), "--trust-core"]) == 0
    (run_dir / "manifest.json").write_text(json.dumps({"env": {"COVERAGE_CORE": "ctrace"}}))
    assert coverage_redundancy.main([str(run_dir / ".coverage")]) == 0
