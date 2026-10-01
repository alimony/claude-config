from __future__ import annotations

import json
from pathlib import Path

import pytest

import static_scan
from conftest import CORPUS, run_pytest

# Every planted defect in the corpus, and how many times the scan must report it.
PLANTED = {
    "shadowed-test": 1,
    "tautology": 1,
    "no-assertion": 1,
    "assert-in-except": 1,
    "literal-only-body": 1,
    "exact-duplicate-body": 1,
    "uncollectable-class": 1,
    "file-not-collected": 1,
    "skip-unconditional": 1,
    "xfail-not-strict": 1,
    "autouse-fixtures": 1,
    "unused-fixtures": 1,
    "risk-sleep": 2,
    "risk-env-mutation": 1,
    "risk-global-state": 1,  # test_order.py writes the module-level STATE that a later test reads
    "risk-clock": 1,
    "risk-network": 1,
    "mock-density": 1,
    "pbt-candidates": 1,
}
DECOYS = ("test_discount_zero_percent", "test_posix_paths", "TestPlain")


def scan(project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *extra: str) -> dict:
    out = tmp_path / "scan.json"
    monkeypatch.chdir(project)
    assert static_scan.main(["--json-out", str(out), *extra]) == 0
    return json.loads(out.read_text())


def test_finds_every_planted_defect(tmp_path, monkeypatch):
    result = scan(CORPUS, tmp_path, monkeypatch)
    counts = {name: entry["count"] for name, entry in result["checks"].items()}
    assert {k: counts.get(k, 0) for k in PLANTED} == PLANTED
    assert set(counts) == set(PLANTED), f"unexpected checks: {set(counts) - set(PLANTED)}"


def test_flags_no_decoy(tmp_path, monkeypatch):
    result = scan(CORPUS, tmp_path, monkeypatch)
    for name, entry in result["checks"].items():
        text = " ".join(entry["examples"])
        for decoy in DECOYS:
            assert decoy not in text, f"{name} flagged decoy {decoy}"
    # The slow end-to-end test is only reported as a sleep, never as a duplicate or dead test.
    for name, entry in result["checks"].items():
        if name != "risk-sleep":
            assert "test_checkout_end_to_end" not in " ".join(entry["examples"]), name


def test_reads_pytest_config(tmp_path, monkeypatch):
    result = scan(CORPUS, tmp_path, monkeypatch)
    assert result["config"]["python_files"] == ["test_*.py"]
    assert result["config"]["source"].endswith("pyproject.toml")
    assert result["roots"] and result["roots"][0].endswith("tests")
    assert result["inventory"]["test_files"] == 8
    assert result["inventory"]["test_functions"] == 25
    assert result["parse_errors"] == []


def test_autouse_reach_counts_directory_tests(tmp_path, monkeypatch):
    result = scan(CORPUS, tmp_path, monkeypatch)
    example = result["checks"]["autouse-fixtures"]["examples"][0]
    assert "slow_setup" in example and "reaches about 25 tests" in example


def test_nodeids_match_when_run_from_rootdir(corpus, tmp_path, monkeypatch):
    collected = run_pytest(corpus, "--collect-only", "-q")
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text(collected.stdout)
    result = scan(corpus, tmp_path, monkeypatch, "--nodeids", str(nodeids))
    assert "not-collected" not in result["checks"]
    assert "not-collected-check-skipped" not in result["checks"]


def test_nodeids_mismatch_is_reported_not_guessed(tmp_path, monkeypatch):
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text("other/tests/test_x.py::test_a\nother/tests/test_x.py::test_b\n")
    result = scan(CORPUS, tmp_path, monkeypatch, "--nodeids", str(nodeids))
    assert "not-collected" not in result["checks"]
    assert result["checks"]["not-collected-check-skipped"]["count"] == 1


def test_unittest_runner_flags_pytest_style_tests(tmp_path, monkeypatch):
    result = scan(CORPUS, tmp_path, monkeypatch, "--runner", "unittest")
    not_run = result["checks"]["not-run-by-runner"]
    assert not_run["count"] == 26  # 24 module-level functions and 2 non-TestCase classes
    assert result["checks"]["file-not-collected"]["count"] == 1


def test_tamper_diff_catches_weakening_and_matches_moves(corpus, tmp_path, monkeypatch):
    before = scan(corpus, tmp_path, monkeypatch)
    pricing = corpus / "tests" / "test_pricing.py"
    text = pricing.read_text()
    # Weaken: drop an assertion, skip a test, delete a test, and move one test to a new file.
    text = text.replace("    assert total(cart) == 6.75\n", "    total(cart)\n")
    text = text.replace("def test_format_price_runs():", "@pytest.mark.skip(reason='later')\ndef test_format_price_runs():")
    text = text.replace('def test_parse_price_spaces():\n    value = parse_price(" 7.00 ")\n    assert value == 7.0\n', "")
    moved = 'def test_parse_price_plain():\n    value = parse_price("4.25")\n    assert value == 4.25\n'
    assert moved in text
    pricing.write_text(text.replace(moved, ""))
    (corpus / "tests" / "test_moved.py").write_text("from shop.pricing import parse_price\n\n\n" + moved)
    out = tmp_path / "after.json"
    monkeypatch.chdir(corpus)
    assert static_scan.main(["--json-out", str(out)]) == 0
    before_path = tmp_path / "before.json"
    before_path.write_text(json.dumps(before))
    diff_out = tmp_path / "diff.json"
    assert static_scan.main(["diff", str(before_path), str(out), "--json-out", str(diff_out)]) == 1
    diff = json.loads(diff_out.read_text())
    assert diff["removed"] == ["tests/test_pricing.py::test_parse_price_spaces"]
    assert diff["moved"] == {"tests/test_pricing.py::test_parse_price_plain": "tests/test_moved.py::test_parse_price_plain"}
    assert diff["newly_skipped"] == ["tests/test_pricing.py::test_format_price_runs"]
    assert diff["fewer_assertions"] == [{"test": "tests/test_pricing.py::test_total", "before": 1, "after": 0}]
    assert diff["weakened"] is True


def test_tamper_diff_accepts_an_unchanged_suite(tmp_path, monkeypatch):
    first = scan(CORPUS, tmp_path, monkeypatch)
    (tmp_path / "a.json").write_text(json.dumps(first))
    assert static_scan.main(["diff", str(tmp_path / "a.json"), str(tmp_path / "a.json")]) == 0


EDGE_CASES = '''
import dataclasses
import unittest

import pytest


def test_yields():
    yield 1


def test_nested_generator_is_fine():
    def gen():
        yield 1
    assert list(gen()) == [1]


def test_returns_comparison():
    return 1 == 2


def test_returns_none_is_fine():
    assert True is not None
    return None


@pytest.mark.parametrize("x", [])
def test_empty_params(x):
    assert x


@pytest.mark.parametrize("x", [1])
def test_non_empty_params_is_fine(x):
    assert x


def test_only_loop_asserts(items=()):
    for item in items:
        assert item


def test_loop_plus_outer_assert_is_fine(items=(1,)):
    assert items
    for item in items:
        assert item


class Base:
    def __init__(self):
        self.v = 1


class TestInherits(Base):
    def test_v(self):
        assert self.v == 1


@dataclasses.dataclass
class TestData:
    v: int = 1

    def test_v(self):
        assert self.v == 1


class CaseTest(unittest.TestCase):
    def test_two_args(self):
        self.assertTrue(len("ab"), 2)

    def test_message_is_fine(self):
        self.assertTrue(len("ab"), "length must be positive")
'''


def test_never_run_and_cannot_fail_patterns(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_edge.py").write_text(EDGE_CASES)
    (tests / "test_importer.py").write_text("from tests.test_edge import test_returns_comparison\n\n\ndef test_own():\n    assert 1\n")
    result = scan(tmp_path, tmp_path, monkeypatch, "tests")
    counts = {name: entry["count"] for name, entry in result["checks"].items()}
    assert counts["yield-in-test"] == 1
    assert counts["returns-value"] == 1
    assert counts["empty-parametrize"] == 1
    assert counts["assert-only-in-loop"] == 1
    assert counts["assert-true-two-args"] == 1
    assert counts["uncollectable-class"] == 2
    assert counts["imported-test"] == 1
    reasons = " ".join(result["checks"]["uncollectable-class"]["examples"])
    assert "inherits __init__ from Base" in reasons and "dataclass" in reasons


def test_pytest9_config_and_module_level_skips(tmp_path, monkeypatch):
    (tmp_path / "pytest.toml").write_text('[pytest]\nstrict_xfail = true\ntestpaths = ["tests"]\npython_files = ["check_*.py"]\n')
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "check_marks.py").write_text(
        "import pytest\n\npytestmark = [pytest.mark.skip(reason='whole module')]\n\n\n"
        "@pytest.mark.xfail(reason='strict by config')\ndef test_xfail():\n    assert 1 == 1\n\n\n"
        "@pytest.mark.skip(reason='whole class')\nclass TestSkipped:\n    def test_x(self):\n        assert 1 == 1\n\n\n"
        "def tset_misspelt():\n    assert 1 == 1\n"
    )
    (tests / "check_disabled.py").write_text("__test__ = False\n\n\ndef test_never():\n    assert 1 == 1\n")
    result = scan(tmp_path, tmp_path, monkeypatch)
    assert result["config"]["source"].endswith("pytest.toml") and result["config"]["xfail_strict"] is True
    assert result["config"]["python_files"] == ["check_*.py"]
    checks = result["checks"]
    assert "xfail-not-strict" not in checks
    skips = " ".join(checks["skip-unconditional"]["examples"])
    assert "module-level pytestmark" in skips and "class TestSkipped" in skips
    assert checks["module-disabled"]["count"] == 1
    assert checks["misnamed-test"]["count"] == 1


def test_pyproject_native_pytest_table(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[tool.pytest]\nstrict = true\ntestpaths = ["tests"]\n')
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("import pytest\n\n\n@pytest.mark.xfail\ndef test_x():\n    assert 1 == 1\n")
    result = scan(tmp_path, tmp_path, monkeypatch)
    assert result["config"]["xfail_strict"] is True and "xfail-not-strict" not in result["checks"]


def test_tamper_diff_catches_weaker_asserts_and_narrowing_addopts(tmp_path, monkeypatch):
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = tests\naddopts = -q\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    test_file = tests / "test_price.py"
    test_file.write_text("def test_total():\n    total = 90 * 2\n    assert total == 180\n")
    before = scan(tmp_path, tmp_path, monkeypatch)
    test_file.write_text("def test_total():\n    total = 90 * 2\n    assert total is not None\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = tests\naddopts = -q --deselect tests/test_other.py::test_slow\n")
    after = scan(tmp_path, tmp_path, monkeypatch)
    diff = static_scan.tamper_diff(before, after)
    assert diff["weaker_assertions"] == [{"test": "tests/test_price.py::test_total", "strong_before": 1, "strong_after": 0}]
    assert diff["narrowing_addopts"] == ["--deselect"]
    assert diff["weakened"] is True


GAPS = '''
from unittest import mock

import pytest


class TestBaseChecks:
    __test__ = False

    def test_shared(self):
        assert self.value > 0


class TestUsesBase(TestBaseChecks):
    __test__ = True
    value = 1


class TestOrphanChecks:
    __test__ = False

    def test_never(self):
        assert 1 == 1


class TestWithNew:
    def __new__(cls):
        return super().__new__(cls)

    def test_x(self):
        assert 1 == 1


class TestHelpers:
    def verify_total(self):
        assert 2 + 2 == 4

    def test_real(self):
        assert 1 == 1


def test_mock_typo():
    m = mock.Mock()
    m()
    m.called_once_with()
    assert m.called


@pytest.mark.parametrize("n", [1])
def test_same_body_a(n):
    value = n * 2
    assert value > 0


@pytest.mark.parametrize("n", [2])
def test_same_body_b(n):
    value = n * 2
    assert value > 0


@pytest.mark.xfail(run=False, reason="hangs")
def test_hangs():
    assert 1 == 1
'''


def test_closed_scanner_gaps(tmp_path, monkeypatch):
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = tests\nnorecursedirs = legacy\n")
    tests = tmp_path / "tests"
    (tests / "legacy").mkdir(parents=True)
    (tests / "legacy" / "test_old.py").write_text("def test_old():\n    assert 1 == 1\n")
    (tests / "test_gaps.py").write_text(GAPS)
    result = scan(tmp_path, tmp_path, monkeypatch)
    checks = {k: v for k, v in result["checks"].items()}
    assert checks["in-norecursedirs"]["count"] == 1 and "legacy" in checks["in-norecursedirs"]["examples"][0]
    assert checks["disabled-class"]["count"] == 1 and "TestOrphanChecks" in checks["disabled-class"]["examples"][0]
    assert any("TestWithNew" in e for e in checks["uncollectable-class"]["examples"])
    assert checks["misnamed-test"]["count"] == 1 and "verify_total" in checks["misnamed-test"]["examples"][0]
    assert checks["mock-typo"]["count"] == 1
    assert checks["xfail-never-runs"]["count"] == 1
    # Identical bodies under different parametrisation test different inputs, so they are not exact duplicates.
    assert "exact-duplicate-body" not in checks


DJANGO_BASES = '''
from django.test import LiveServerTestCase, TransactionTestCase


class BaseLiveTest(LiveServerTestCase):
    pass


class FlushBase(TransactionTestCase):
    pass
'''

DJANGO_TESTS = '''
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from tests.bases import BaseLiveTest, FlushBase

pytestmark = [pytest.mark.django_db(transaction=True)]

settings.register_profile("ci", max_examples=1000, deadline=None)
settings.load_profile("ci")


class TestBrowser(BaseLiveTest):
    def test_home(self):
        assert self.live_server_url


class TestFlushing(FlushBase):
    def test_flush(self):
        assert True is not False


class TestMarked:
    pytestmark = pytest.mark.django_db(reset_sequences=True)

    def test_ids(self):
        assert 1


@pytest.mark.django_db(True)
def test_positional():
    assert 1


@pytest.mark.usefixtures("live_server")
def test_uses_live_server():
    assert 1


def test_requests_fixture(transactional_db):
    assert 1


@pytest.fixture(autouse=True)
def flush_everything(transactional_db):
    yield


@pytest.mark.django_db
def test_plain_db():
    assert 1


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=5)
@given(st.integers())
def test_property(n):
    assert n == n
'''


def test_transactional_and_hypothesis_settings(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "__init__.py").write_text("")
    (tests / "bases.py").write_text(DJANGO_BASES)
    (tests / "test_django.py").write_text(DJANGO_TESTS)
    result = scan(tmp_path, tmp_path, monkeypatch, "--examples", "20")
    transactional = " | ".join(result["checks"]["transactional-tests"]["examples"])
    for expected in (
        "every test in tests/test_django.py (pytestmark) uses django_db(transaction=True)",
        "TestBrowser inherits BaseLiveTest (1 test methods)",
        "TestFlushing inherits FlushBase (1 test methods)",
        "every test in TestMarked (pytestmark) uses django_db(reset_sequences=True)",
        "test_positional uses django_db(True)",
        "test_uses_live_server uses the live_server fixture",
        "test_requests_fixture requests transactional_db",
        "fixture flush_everything (autouse) requests transactional_db",
    ):
        assert expected in transactional, expected
    assert "test_plain_db" not in transactional and result["checks"]["transactional-tests"]["count"] == 8
    hypothesis = " | ".join(result["checks"]["hypothesis-settings"]["examples"])
    assert "settings.register_profile('ci', max_examples=1000, deadline=None)" in hypothesis
    assert "suppress_health_check=[HealthCheck.too_slow]" in hypothesis


SHARED_STATE = """
import pytest
import shop.registry as registry

CACHE = {}
SEEN = []


@pytest.fixture
def cart():
    return {"items": []}


@pytest.fixture
def clean_db():
    yield


def encode_order(order):
    return order


def decode_order(data):
    return data


def test_round_trip():
    assert decode_order(encode_order({"id": 1})) == {"id": 1}


def test_writes_cache():
    CACHE["k"] = 1
    SEEN.append(2)
    registry.HANDLERS["x"] = object()
    registry.timeout = 0
    assert CACHE


def test_local_shadow_is_fine():
    CACHE = {}
    CACHE["k"] = 1
    assert CACHE


def test_unread(cart, clean_db, tmp_path):
    assert tmp_path.exists()


def test_read(cart):
    assert cart["items"] == []


@pytest.mark.parametrize("cart", [1])
def test_parametrized_name(cart):
    assert True is not False
"""


def test_shared_state_round_trips_and_unread_fixtures(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_shared.py").write_text(SHARED_STATE)
    result = scan(tmp_path, tmp_path, monkeypatch, "--examples", "20")
    checks = result["checks"]
    shared = " | ".join(checks["risk-global-state"]["examples"])
    assert "test_writes_cache changes module-level CACHE" in shared and "SEEN" in shared
    assert "registry.HANDLERS" in shared and "registry.timeout (set without monkeypatch)" in shared
    assert "test_local_shadow_is_fine" not in shared
    pbt = " ".join(checks["pbt-candidates"]["examples"])
    assert "encode_order()" in pbt and "decode_order()" in pbt
    unread = checks["unread-fixture"]["examples"]
    assert len(unread) == 1 and "test_unread requests cart" in unread[0]  # clean_db yields nothing; tmp_path is read


WEAK = """
def total(x):
    return x


def test_only_exists():
    result = total(3)
    assert result is not None
    assert len([result]) > 0


def test_type_is_the_behaviour():
    assert isinstance(total(3), int)


def test_guard_then_call():
    assert total is not None
    total(3)


def test_value():
    assert total(3) is not None
    assert total(3) == 3
"""


def test_weak_assertions(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_weak.py").write_text(WEAK)
    result = scan(tmp_path, tmp_path, monkeypatch, "--examples", "20")
    examples = result["checks"]["weak-assertions"]["examples"]
    assert len(examples) == 1 and "test_only_exists" in examples[0]


COLLECTION_EDGES = '''
import unittest

import pytest

pytest.importorskip("module_that_is_not_installed")
'''

INHERITED = '''
import unittest
from unittest import skip

from parameterized import parameterized


class BaseChecks:
    def test_shared(self):
        assert 1 + 1 == 2


class TestConcrete(BaseChecks):
    pass


class TestExpanded(unittest.TestCase):
    @parameterized.expand([(1,), (2,)])
    def test_value(self, n):
        self.assertEqual(n, n * 1)

    def test_message_forms(self):
        reason = "explains the failure"
        self.assertTrue(1 == 1, reason)
        self.assertTrue(1 == 1, "%s failed" % "x")
        self.assertTrue(1 == 1, str(1))
        self.assertTrue(1, 1)


@skip
class TestForgotten(unittest.TestCase):
    def test_never(self):
        self.assertEqual(1, 1)


def test_really_missing():
    assert 2 * 2 == 4
'''


def test_not_collected_explains_inheritance_renames_and_module_skips(tmp_path, monkeypatch):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_optional.py").write_text(COLLECTION_EDGES + "\n\ndef test_needs_it():\n    assert 3 == 3\n")
    (tests / "test_edges.py").write_text(INHERITED)
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text("\n".join([
        "tests/test_edges.py::TestConcrete::test_shared",
        "tests/test_edges.py::TestExpanded::test_value_0",
        "tests/test_edges.py::TestExpanded::test_value_1",
        "tests/test_edges.py::TestExpanded::test_message_forms",
    ]) + "\n")
    result = scan(tmp_path, tmp_path, monkeypatch, "--nodeids", str(nodeids), "--examples", "20")
    checks = result["checks"]
    assert checks["not-collected"]["examples"] == ["tests/test_edges.py – test_really_missing"]
    assert "TestForgotten" in checks["bare-skip-decorator"]["examples"][0]
    two_args = checks["assert-true-two-args"]["examples"]
    assert len(two_args) == 1 and "test_message_forms" in two_args[0]  # only assertTrue(1, 1)


def test_autouse_reach_counts_collected_cases_with_nodeids(corpus, tmp_path, monkeypatch):
    collected = run_pytest(corpus, "--collect-only", "-q")
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text(collected.stdout)
    result = scan(corpus, tmp_path, monkeypatch, "--nodeids", str(nodeids))
    example = result["checks"]["autouse-fixtures"]["examples"][0]
    assert "slow_setup" in example and "reaches 27 collected tests" in example
