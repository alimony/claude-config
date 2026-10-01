from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import results
import run_suite
from conftest import plugin_available, run_pytest


@pytest.fixture
def audit(tmp_path, monkeypatch, corpus, capsys) -> Path:
    monkeypatch.setenv("TEST_SUITE_AUDIT_HOME", str(tmp_path / "home"))
    assert run_suite.main(["init", "--project", str(corpus)]) == 0
    return Path(capsys.readouterr().out.strip().splitlines()[-1])


def newest_run(audit: Path) -> Path:
    return sorted((audit / "runs").iterdir())[-1]


def pytest_command(*extra: str) -> list[str]:
    return [sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-q", *extra]


@pytest.mark.skipif(not plugin_available("xdist"), reason="needs pytest-xdist")
def test_timing_plugin_under_xdist(audit, corpus, capsys):
    # --dist loadfile keeps the corpus's order-dependent pair on one worker; with plain
    # load distribution it fails, which is the planted defect doing its job.
    code = run_suite.main(
        ["run", "--artifacts", str(audit), "--label", "timed", "--cwd", str(corpus), "--timing-plugin", "--", *pytest_command("-n", "2", "--dist", "loadfile")]
    )
    assert code == 0, capsys.readouterr().out
    run_dir = newest_run(audit)
    assert (run_dir / "timing.jsonl").is_file()
    assert sorted(p.name for p in run_dir.glob("fixtures-*.json")) == ["fixtures-gw0.json", "fixtures-gw1.json"]
    run = results.load(str(run_dir), {})
    assert len(run.tests) == 27
    assert {t.worker for t in run.tests.values()} == {"gw0", "gw1"}
    summary = results.summarise(run, 5, 2)
    assert set(summary["workers_seen"]["busy_seconds"]) == {"gw0", "gw1"}
    out = run_dir / "fixtures.json"
    capsys.readouterr()
    assert results.main(["fixtures", str(run_dir), "--json-out", str(out)]) == 0
    rows = {r["name"]: r for r in json.loads(out.read_text())}
    assert rows["slow_setup"]["setups"] == 26  # every test except the skipped one
    assert rows["slow_setup"]["scope"] == "function" and rows["slow_setup"]["workers"] == 2
    assert rows["cart"]["setups"] == 3
    assert "slow_setup" in capsys.readouterr().out


def test_timing_plugin_without_xdist(audit, corpus):
    assert run_suite.main(["run", "--artifacts", str(audit), "--label", "timed", "--cwd", str(corpus), "--timing-plugin", "--", *pytest_command("-p", "no:xdist")]) == 0
    run_dir = newest_run(audit)
    assert (run_dir / "fixtures-main.json").is_file()
    run = results.load(str(run_dir), {})
    slow = run.tests["tests/test_slow.py::test_checkout_end_to_end"]
    assert slow.call == pytest.approx(0.3, abs=0.1) and slow.setup and slow.setup >= 0.01
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["complete"] is True and manifest["instrumented"] == "none"
    assert not list(corpus.rglob("timing.jsonl")), "the plugin must write into the run folder, not the project"


def test_durations_block_completeness(corpus, tmp_path):
    full = tmp_path / "full.log"
    full.write_text(run_pytest(corpus, "-q", "--durations=0", "--durations-min=0").stdout)
    assert results.load(str(full), {}).partial is False
    top = tmp_path / "top.log"
    top.write_text(run_pytest(corpus, "-q", "--durations=5").stdout)
    assert results.load(str(top), {}).partial is True


def test_run_folder_merges_junit_and_phases(audit, corpus):
    command = pytest_command("--junitxml={RUN_DIR}/junit.xml", "-o", "junit_family=xunit1", "--durations=0", "--durations-min=0")
    assert run_suite.main(["run", "--artifacts", str(audit), "--label", "base", "--cwd", str(corpus), "--", *command]) == 0
    run = results.load(str(newest_run(audit)), {})
    assert "junit" in run.formats and "durations-text" in run.formats
    assert run.tests["tests/test_slow.py::test_checkout_end_to_end"].call >= 0.29


def test_sample_and_extrapolate(audit, corpus, tmp_path, capsys):
    nodeids = tmp_path / "nodeids.txt"
    nodeids.write_text(run_pytest(corpus, "--collect-only", "-q").stdout)
    sample = tmp_path / "sample.txt"
    assert run_suite.main(["sample", "--nodeids", str(nodeids), "--fraction", "0.5", "--depth", "1", "--seed", "3", "--out", str(sample)]) == 0
    files = sample.read_text().split()
    plan = json.loads(sample.with_suffix(".json").read_text())
    assert len(files) == 4 and plan["strata"]["tests"]["files_total"] == 8
    capsys.readouterr()
    assert run_suite.main(["run", "--artifacts", str(audit), "--label", "sample", "--cwd", str(corpus), "--timing-plugin", "--", *pytest_command(f"@{sample}")]) == 0
    out = tmp_path / "estimate.json"
    assert results.main(["extrapolate", str(newest_run(audit)), "--plan", str(sample.with_suffix(".json")), "--json-out", str(out)]) == 0
    estimate = json.loads(out.read_text())
    low, high = estimate["range_90"]
    assert estimate["missing_files"] == []
    assert low <= estimate["estimate_seconds"] <= high and estimate["basis"] == "extrapolated"


@pytest.mark.skipif(not plugin_available("pytest_rerunfailures"), reason="needs pytest-rerunfailures")
def test_reruns_are_visible_through_the_timing_plugin(audit, tmp_path, capsys):
    project = tmp_path / "flaky"
    (project / "tests").mkdir(parents=True)
    marker = tmp_path / "attempted"
    (project / "tests" / "test_flaky.py").write_text(
        "from pathlib import Path\n\n\n"
        f"def test_fails_first_time():\n    marker = Path({str(marker)!r})\n"
        "    if not marker.exists():\n        marker.write_text('x')\n        assert False, 'first attempt'\n"
    )
    code = run_suite.main(["run", "--artifacts", str(audit), "--label", "reruns", "--cwd", str(project), "--timing-plugin", "--",
                           *pytest_command("--reruns", "1", "--junitxml={RUN_DIR}/junit.xml", "-o", "junit_family=xunit1")])
    assert code == 0, capsys.readouterr().out
    run_dir = newest_run(audit)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["counts"].get("rerun") == 1
    test = results.load(str(run_dir), {}).tests["tests/test_flaky.py::test_fails_first_time"]
    assert test.reruns == 1 and test.outcome == "passed"
    # pytest-rerunfailures writes each attempt as a separate, passing <testcase>. On its own, that is a
    # repeat; with the manifest showing --reruns, load() counts it as a rerun.
    junit_only = results.read_junit(run_dir / "junit.xml", {})
    assert junit_only.tests["tests/test_flaky.py::test_fails_first_time"].repeats == 1
    with_manifest = results.load(str(run_dir / "junit.xml"), {})
    assert with_manifest.tests["tests/test_flaky.py::test_fails_first_time"].reruns == 1


TEARDOWN_PROJECT = '''
import time

import pytest


@pytest.fixture(scope="session")
def server():
    yield "server"
    time.sleep(0.3)


@pytest.fixture
def client(server):
    yield server
    time.sleep(0.05)


def test_one(client):
    assert client == "server"


def test_two(client):
    assert client == "server"
'''


def test_timing_plugin_times_fixture_teardown(audit, tmp_path, capsys):
    project = tmp_path / "teardowns"
    project.mkdir()
    (project / "test_teardown.py").write_text(TEARDOWN_PROJECT)
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:xdist", "-p", "no:cacheprovider"]
    assert run_suite.main(["run", "--artifacts", str(audit), "--label", "teardown", "--cwd", str(project), "--timing-plugin", "--", *command]) == 0
    run_dir = newest_run(audit)
    rows = {r["name"]: r for r in json.loads((run_dir / "fixtures-main.json").read_text())}
    assert rows["client"]["teardowns"] == 2 and rows["client"]["teardown_seconds"] == pytest.approx(0.1, abs=0.05)
    # The session fixture's own teardown, without the client teardowns nested in it.
    assert rows["server"]["teardowns"] == 1 and rows["server"]["teardown_seconds"] == pytest.approx(0.3, abs=0.1)
    capsys.readouterr()
    assert results.main(["fixtures", str(run_dir)]) == 0
    assert "teardown time:" in capsys.readouterr().out
    summary = results.summarise(results.load(str(run_dir), {}), 5, None)
    assert [r["last_test"] for r in summary["session_teardown"]] == []  # 0.35 s is under the 1 s threshold


def test_summary_separates_session_teardown_and_deepens_groups(tmp_path, capsys):
    def report(nodeid, when, duration, start, worker):
        return {"$report_type": "TestReport", "nodeid": nodeid, "when": when, "outcome": "passed", "duration": duration,
                "start": start, "stop": start + duration, "worker": worker}

    lines = []
    for worker in ("gw0", "gw1"):
        for i in range(3):
            app = "orders" if i < 2 else "billing"
            nodeid = f"proj/apps/{app}/tests/test_{worker}_{i}.py::test_x"
            lines.append(report(nodeid, "call", 1.0, 10.0 * i, worker))
            lines.append(report(nodeid, "teardown", 30.0 if i == 2 else 0.01, 10.0 * i + 1, worker))
    log = tmp_path / "timing.jsonl"
    log.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    summary = results.summarise(results.load(str(log), {}), 5, None)
    assert {r["last_test"] for r in summary["session_teardown"]} == {
        "proj/apps/billing/tests/test_gw0_2.py::test_x", "proj/apps/billing/tests/test_gw1_2.py::test_x"}
    assert summary["slowest"][0]["seconds"] < 2  # the 30 s session teardowns are not test time
    assert summary["group_depth"] == 3 and {g["group"] for g in summary["groups"]} == {"proj/apps/orders", "proj/apps/billing"}
    results.print_summary(summary, 5)
    assert "session teardown: 60.0s on 2 worker(s)" in capsys.readouterr().out
