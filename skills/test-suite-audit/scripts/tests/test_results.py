from __future__ import annotations

import json
from pathlib import Path

import pytest

import results
from conftest import plugin_available, run_pytest

XUNIT1 = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="4">
  <testcase classname="tests.test_a" name="test_fast" file="tests/test_a.py" line="1" time="0.010"/>
  <testcase classname="tests.test_a.TestB" name="test_slow[2]" file="tests/test_a.py" line="9" time="4.500"/>
  <testcase classname="tests.test_a" name="test_broken" file="tests/test_a.py" line="20" time="0.200"><failure message="boom"/></testcase>
  <testcase classname="tests.test_a" name="test_xf" file="tests/test_a.py" line="30" time="0.001"><skipped type="pytest.xfail" message="known"/></testcase>
</testsuite></testsuites>
"""

XUNIT2 = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest">
  <testcase classname="pkg.tests.test_c" name="test_one" time="1.0"/>
  <testcase classname="pkg.tests.test_c.TestD" name="test_two" time="2.0"><skipped message="nope"/></testcase>
</testsuite></testsuites>
"""

SUREFIRE = """<testsuite name="com.example.FooTest" tests="1">
  <testcase classname="com.example.FooTest" name="retried" time="0.5"><flakyFailure message="first try"/></testcase>
</testsuite>
"""


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_junit_xunit1_ids_outcomes_and_tail(tmp_path):
    xml = write(tmp_path / "junit.xml", XUNIT1)
    run = results.load(str(xml), {})
    assert set(run.tests) == {
        "tests/test_a.py::test_fast",
        "tests/test_a.py::TestB::test_slow[2]",
        "tests/test_a.py::test_broken",
        "tests/test_a.py::test_xf",
    }
    summary = results.summarise(run, top=5, depth=2)
    assert summary["outcomes"] == {"failed": 1, "passed": 2, "xfailed": 1}
    assert summary["slowest"][0]["id"] == "tests/test_a.py::TestB::test_slow[2]"
    assert summary["long_tail_share_percent"]["top_1"] == pytest.approx(95.5, abs=0.1)
    assert summary["over_seconds"] == {"1": 1, "5": 0, "30": 0}


def test_junit_xunit2_maps_through_nodeids(tmp_path):
    xml = write(tmp_path / "junit.xml", XUNIT2)
    nodeids = write(tmp_path / "nodeids.txt", "pkg/tests/test_c.py::test_one\npkg/tests/test_c.py::TestD::test_two\n\n2 tests collected in 0.01s\n")
    run = results.load(str(xml), results.load_nodeid_map(str(nodeids)))
    assert set(run.tests) == {"pkg/tests/test_c.py::test_one", "pkg/tests/test_c.py::TestD::test_two"}
    # pytest names its suite "pytest", so class names convert to node IDs even without --nodeids.
    unmapped = results.load(str(xml), {})
    assert set(unmapped.tests) == {"pkg/tests/test_c.py::test_one", "pkg/tests/test_c.py::TestD::test_two"}


def test_surefire_flaky_reruns_are_counted(tmp_path):
    run = results.load(str(write(tmp_path / "TEST-foo.xml", SUREFIRE)), {})
    test = run.tests["com.example.FooTest::retried"]
    assert test.reruns == 1 and test.outcome == "passed"
    assert results.summarise(run, 5, 2)["reruns"][0]["id"] == "com.example.FooTest::retried"


def test_durations_file_and_text(tmp_path):
    split = write(tmp_path / ".test_durations", json.dumps({"tests/test_a.py::test_x": 3.0, "tests/test_a.py::test_y": 1.0}))
    run = results.load(str(split), {})
    assert results.summarise(run, 5, 2)["sum_seconds"] == 4.0
    assert any("no outcomes" in w for w in run.warnings)
    log = write(
        tmp_path / "output.log",
        "==== slowest 3 durations ====\n2.50s call     tests/test_a.py::test_x\n0.40s setup    tests/test_a.py::test_x\n1.00s call     tests/test_b.py::test_z\n",
    )
    text_run = results.load(str(log), {})
    assert text_run.partial
    assert text_run.tests["tests/test_a.py::test_x"].total == pytest.approx(2.9)
    assert text_run.tests["tests/test_a.py::test_x"].setup == pytest.approx(0.4)


@pytest.mark.skipif(not plugin_available("pytest_reportlog"), reason="needs pytest-reportlog")
def test_reportlog_from_a_real_run_and_truncation(corpus, tmp_path):
    log = tmp_path / "reportlog.jsonl"
    proc = run_pytest(corpus, "-q", f"--report-log={log}")
    assert proc.returncode == 0, proc.stdout[-2000:]
    run = results.load(str(log), {})
    summary = results.summarise(run, 5, 2)
    assert summary["tests"] == 27
    assert summary["slowest"][0]["id"] == "tests/test_slow.py::test_checkout_end_to_end"
    assert summary["phases"]["setup"] > 0.2  # the autouse fixture sleeps in every setup
    assert summary["outcomes"]["xpassed"] == 1 and summary["outcomes"]["skipped"] == 1
    lines = log.read_text().splitlines()
    truncated = write(tmp_path / "cut.jsonl", "\n".join(lines[:-1] + [lines[-1][: len(lines[-1]) // 2]]))
    cut = results.load(str(truncated), {})
    assert cut.partial and any("truncated" in w for w in cut.warnings)


@pytest.mark.skipif(not plugin_available("pytest_jsonreport"), reason="needs pytest-json-report")
def test_json_report_from_a_real_run(corpus, tmp_path):
    report = tmp_path / "report.json"
    proc = run_pytest(corpus, "-q", "--json-report", f"--json-report-file={report}")
    assert proc.returncode == 0, proc.stdout[-2000:]
    run = results.load(str(report), {})
    assert len(run.tests) == 27
    assert run.tests["tests/test_slow.py::test_checkout_end_to_end"].call >= 0.3


def make_run(tmp_path: Path, name: str, outcomes: dict[str, str], commit: str, wall: float = 10.0, times: dict[str, float] | None = None, instrumented: str = "none") -> Path:
    cases = []
    for test, outcome in outcomes.items():
        module, _, func = test.rpartition("::")
        classname = module[:-3].replace("/", ".")
        child = {"failed": '<failure message="x"/>', "skipped": '<skipped message="s"/>'}.get(outcome, "")
        cases.append(f'<testcase classname="{classname}" name="{func}" file="{module}" time="{(times or {}).get(test, 0.1)}">{child}</testcase>')
    folder = tmp_path / name
    write(folder / "junit.xml", "<testsuites><testsuite>" + "".join(cases) + "</testsuite></testsuites>")
    write(folder / "manifest.json", json.dumps({"commit": commit, "dirty": False, "wall_seconds": wall, "instrumented": instrumented, "command": ["pytest"], "workers": 4}))
    return folder / "junit.xml"


def test_flips_same_commit_is_flaky(tmp_path, capsys):
    runs = [
        make_run(tmp_path, "r1", {"tests/t.py::test_a": "passed", "tests/t.py::test_b": "passed"}, "abc"),
        make_run(tmp_path, "r2", {"tests/t.py::test_a": "failed", "tests/t.py::test_b": "passed"}, "abc"),
        make_run(tmp_path, "r3", {"tests/t.py::test_a": "passed", "tests/t.py::test_b": "passed"}, "abc"),
    ]
    out = tmp_path / "flips.json"
    assert results.main(["flips", *map(str, runs), "--json-out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["same_commit"] is True
    assert [f["id"] for f in data["flips"]] == ["tests/t.py::test_a"]
    assert "flaky at the same commit" in capsys.readouterr().out


def test_flips_across_commits_is_not_flakiness(tmp_path, capsys):
    runs = [
        make_run(tmp_path, "r1", {"tests/t.py::test_a": "passed"}, "abc"),
        make_run(tmp_path, "r2", {"tests/t.py::test_a": "failed"}, "def"),
    ]
    out = tmp_path / "flips.json"
    results.main(["flips", *map(str, runs), "--json-out", str(out)])
    assert json.loads(out.read_text())["same_commit"] is False
    assert "NOT evidence of flakiness" in capsys.readouterr().out


def test_diff_reports_speedup_and_changed_test_set(tmp_path, capsys):
    tests = {"tests/t.py::test_a": "passed", "tests/t.py::test_b": "passed"}
    before = [make_run(tmp_path, f"b{i}", tests, "abc", wall=20.0 + i, times={"tests/t.py::test_a": 5.0}) for i in range(3)]
    after = [make_run(tmp_path, f"a{i}", tests, "abd", wall=10.0 + i, times={"tests/t.py::test_a": 0.5}) for i in range(3)]
    out = tmp_path / "diff.json"
    assert results.main(["diff", "--before", *map(str, before), "--after", *map(str, after), "--json-out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["change_percent"] == pytest.approx(100 * (11 - 21) / 21, abs=0.1)
    assert data["same_tests_and_outcomes"] is True
    shrunk = [make_run(tmp_path, "s0", {"tests/t.py::test_a": "passed"}, "abd", wall=5.0)]
    assert results.main(["diff", "--before", str(before[0]), "--after", str(shrunk[0])]) == 1
    assert "disappeared: tests/t.py::test_b" in capsys.readouterr().out


def test_diff_ignores_run_folders_in_commands(tmp_path, capsys):
    tests = {"tests/t.py::test_a": "passed"}
    sides = []
    for name in ("b0", "a0"):
        xml = make_run(tmp_path, name, tests, "abc")
        manifest = json.loads((xml.parent / "manifest.json").read_text())
        manifest.update(run_dir=str(xml.parent), command=["pytest", f"--junitxml={xml.parent}/junit.xml"])
        (xml.parent / "manifest.json").write_text(json.dumps(manifest))
        sides.append(str(xml))
    assert results.main(["diff", "--before", sides[0], "--after", sides[1]]) == 0
    assert "runs differ in command" not in capsys.readouterr().out


def test_instrumented_runs_are_flagged(tmp_path):
    xml = make_run(tmp_path, "cov", {"tests/t.py::test_a": "passed"}, "abc", instrumented="coverage")
    run = results.load(str(xml), {})
    assert any("instrumented" in w for w in run.warnings)


DJANGO_LOG = """Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....
Slowest test durations
----------------------------------------------------------------------
0.280s     test_delete (app.tests.test_views.TestDeleteView.test_delete)
0.100s     test_list (app.tests.test_views.TestListView.test_list)

----------------------------------------------------------------------
Ran {ran} tests in 1.2s

OK
"""


def test_django_durations_block(tmp_path, capsys):
    partial = write(tmp_path / "partial.log", DJANGO_LOG.format(ran=5))
    run = results.load(str(partial), {})
    assert run.partial and set(run.tests) == {"app.tests.test_views.TestDeleteView.test_delete", "app.tests.test_views.TestListView.test_list"}
    assert run.tests["app.tests.test_views.TestDeleteView.test_delete"].file == "app/tests/test_views.py"
    results.print_summary(results.summarise(run, 5, 2), 5)
    assert "long tail" not in capsys.readouterr().out
    complete = write(tmp_path / "complete.log", DJANGO_LOG.format(ran=2))
    assert results.load(str(complete), {}).partial is False


INHERITED_XUNIT1 = """<testsuites><testsuite name="pytest">
  <testcase classname="tests.test_sub.TestSubA" name="test_shared" file="tests/test_base.py" time="0.1"/>
  <testcase classname="tests.test_sub.TestSubB" name="test_shared" file="tests/test_base.py" time="0.1"/>
  <testcase classname="tests.test_base" name="test_plain" file="tests/test_base.py" time="0.1"><skipped message="s"/><failure message="subtest failed"/></testcase>
</testsuite></testsuites>
"""


def test_inherited_methods_and_outcome_precedence(tmp_path):
    run = results.load(str(write(tmp_path / "junit.xml", INHERITED_XUNIT1)), {})
    assert set(run.tests) == {"tests/test_sub.py::TestSubA::test_shared", "tests/test_sub.py::TestSubB::test_shared", "tests/test_base.py::test_plain"}
    assert all(t.repeats == 0 for t in run.tests.values())
    assert run.tests["tests/test_base.py::test_plain"].outcome == "failed"


def test_non_junit_xml_is_reported(tmp_path):
    trx = write(tmp_path / "results.trx", '<?xml version="1.0"?><TestRun><Results><UnitTestResult testName="t" outcome="Passed"/></Results></TestRun>')
    run = results.load(str(trx), {})
    assert not run.tests and any("<TestRun>" in w for w in run.warnings)


REPEATED_XUNIT1 = """<testsuites><testsuite name="pytest">
  <testcase classname="tests.test_r" name="test_retry" file="tests/test_r.py" time="0.1"/>
  <testcase classname="tests.test_r" name="test_retry" file="tests/test_r.py" time="0.2"/>
  <testcase classname="tests.test_r" name="test_once" file="tests/test_r.py" time="0.1"/>
</testsuite></testsuites>
"""


def test_repeated_entries_count_as_reruns_only_when_reruns_were_on(tmp_path):
    xml = write(tmp_path / "plain" / "junit.xml", REPEATED_XUNIT1)
    test = results.load(str(xml), {}).tests["tests/test_r.py::test_retry"]
    assert (test.repeats, test.reruns) == (1, 0)
    test = results.load(str(xml), {}, repeats_are_reruns=True).tests["tests/test_r.py::test_retry"]
    assert (test.repeats, test.reruns) == (0, 1)
    configured = write(tmp_path / "configured" / "junit.xml", REPEATED_XUNIT1)
    write(configured.parent / "manifest.json", json.dumps({"command": ["pytest"], "reruns_configured": True}))
    test = results.load(str(configured), {}).tests["tests/test_r.py::test_retry"]
    assert (test.repeats, test.reruns) == (0, 1)


def test_reportlog_worker_id_is_read(tmp_path):
    lines = [
        {"$report_type": "TestReport", "nodeid": "tests/t.py::test_a", "when": "call", "outcome": "passed", "duration": 0.5, "worker_id": "gw1"},
        {"$report_type": "TestReport", "nodeid": "tests/t.py::test_b", "when": "call", "outcome": "passed", "duration": 0.5, "worker_id": "gw0"},
    ]
    log = write(tmp_path / "reportlog.jsonl", "\n".join(json.dumps(line) for line in lines) + "\n")
    run = results.load(str(log), {})
    assert {t.worker for t in run.tests.values()} == {"gw0", "gw1"}


def test_diff_compares_collect_only_runs(tmp_path, capsys):
    before = write(tmp_path / "before" / "output.log", "tests/t.py::test_a\ntests/t.py::test_b[1 2]\n\n2 tests collected in 0.05s\n")
    after = write(tmp_path / "after" / "output.log", "tests/t.py::test_a\n\n1 test collected in 0.04s\n")
    assert results.main(["diff", "--before", str(before), "--after", str(before)]) == 0
    assert results.main(["diff", "--before", str(before), "--after", str(after)]) == 1
    assert "disappeared: tests/t.py::test_b[1 2]" in capsys.readouterr().out


def test_a_test_run_log_is_not_read_as_collect_only(tmp_path):
    log = write(tmp_path / "run.log", "collected 2 items\n\ntests/t.py .F\nFAILED tests/t.py::test_b - assert 1 == 2\n=== 1 failed, 1 passed in 0.2s ===\n")
    with pytest.raises(SystemExit, match="no recognised test results"):
        results.load(str(log), {})


def test_extrapolate_counts_session_setup_once(tmp_path, capsys):
    def report(nodeid, when, duration, start):
        return {"$report_type": "TestReport", "nodeid": nodeid, "when": when, "outcome": "passed", "duration": duration, "start": start, "stop": start + duration}

    lines = [report("tests/test_a.py::t1", "setup", 5.0, 0.0), report("tests/test_a.py::t1", "call", 1.0, 5.0)]
    lines += [report(nodeid, "call", 1.0, 6.0 + i) for i, nodeid in enumerate(["tests/test_a.py::t2", "tests/test_b.py::t3", "tests/test_b.py::t4"])]
    write(tmp_path / "sample" / "timing.jsonl", "\n".join(json.dumps(line) for line in lines) + "\n")
    plan = {"strata": {"tests": {"files_total": 4, "tests_total": 8, "files": {"tests/test_a.py": 2, "tests/test_b.py": 2}}}}
    write(tmp_path / "plan.json", json.dumps(plan))
    out = tmp_path / "estimate.json"
    assert results.main(["extrapolate", str(tmp_path / "sample"), "--plan", str(tmp_path / "plan.json"), "--json-out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["estimate_seconds"] == pytest.approx(5.0 + 4.0 * 8 / 4)  # the 5 s session setup counts once
    assert data["first_test_setup_seconds"] == pytest.approx(5.0)
    assert "counted once, not scaled" in capsys.readouterr().out


VERBOSE_LOG = """2026-09-30T10:00:01.0000000Z ============================= test session starts ==============================
2026-09-30T10:00:02.0000000Z tests/test_a.py::test_one PASSED                                       [ 25%]
2026-09-30T10:00:02.1000000Z tests/test_a.py::test_two[a b] FAILED                                  [ 50%]
2026-09-30T10:00:02.2000000Z tests/test_a.py::TestK::test_inherited <- tests/base.py SKIPPED (no db)  [ 75%]
[gw1] [100%] RERUN tests/test_b.py::test_retry
[gw1] [100%] PASSED tests/test_b.py::test_retry
=========================== short test summary info ============================
FAILED tests/test_a.py::test_two[a b] - assert 1 == 2
==== 1 failed, 2 passed, 1 skipped, 1 rerun in 3.20s ====
"""


def test_verbose_ci_log_gives_outcomes_and_reruns(tmp_path):
    log = write(tmp_path / "job.txt", VERBOSE_LOG)
    run = results.load(str(log), {})
    outcomes = {tid: t.outcome for tid, t in run.tests.items()}
    assert outcomes == {
        "tests/test_a.py::test_one": "passed",
        "tests/test_a.py::test_two[a b]": "failed",
        "tests/test_a.py::TestK::test_inherited": "skipped",
        "tests/test_b.py::test_retry": "passed",
    }
    assert run.tests["tests/test_b.py::test_retry"].reruns == 1
    assert "verbose-log" in run.formats
