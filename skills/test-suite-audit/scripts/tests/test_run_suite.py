from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import run_suite

fcntl = pytest.importorskip("fcntl")


@pytest.fixture
def home(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "audit-home"
    monkeypatch.setenv("TEST_SUITE_AUDIT_HOME", str(root))
    return root


def init(project: Path, capsys, *extra: str) -> Path:
    assert run_suite.main(["init", "--project", str(project), *extra]) == 0
    return Path(capsys.readouterr().out.strip().splitlines()[-1])


def run(artifacts: Path, cwd: Path, *command: str, extra: tuple[str, ...] = ()) -> int:
    return run_suite.main(["run", "--artifacts", str(artifacts), "--label", "t", "--cwd", str(cwd), *extra, "--", *command])


def manifest(artifacts: Path) -> dict:
    newest = sorted((artifacts / "runs").iterdir())[-1]
    return json.loads((newest / "manifest.json").read_text())


def test_init_reuses_unfinished_audit(home, tmp_path, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    first = init(project, capsys)
    assert (first / "STATE.md").is_file() and (first / "runs").is_dir()
    assert str(first).startswith(str(home))
    assert init(project, capsys) == first
    state = first / "STATE.md"
    state.write_text(state.read_text().replace("status: in progress", "status: finished"))
    assert init(project, capsys) != first


def test_init_keeps_one_audit_per_test_root(home, tmp_path, capsys):
    repo = tmp_path / "mono"
    (repo / "backend").mkdir(parents=True)
    (repo / "frontend").mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    backend, frontend = init(repo / "backend", capsys), init(repo / "frontend", capsys)
    assert backend != frontend
    assert backend.parent.name.startswith("mono-backend-") and frontend.parent.name.startswith("mono-frontend-")
    assert f"repository: {repo.resolve()}" in (backend / "STATE.md").read_text()


def test_run_records_a_complete_pytest_run(home, corpus, capsys):
    artifacts = init(corpus, capsys)
    code = run(artifacts, corpus, sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-q", "--junitxml={RUN_DIR}/junit.xml")
    out = capsys.readouterr().out
    assert code == 0, out
    m = manifest(artifacts)
    assert m["complete"] is True and m["runner"] == "pytest"
    assert {k: v for k, v in m["counts"].items() if k != "warnings"} == {"passed": 25, "skipped": 1, "xpassed": 1}
    assert m["instrumented"] == "none"
    assert "junit.xml" in m["reports"]
    run_dir = Path(m["run_dir"])
    assert (run_dir / "pytest-cache").is_dir(), "pytest's cache must go to the run folder"
    assert not (corpus / ".pytest_cache").exists()
    assert "COMPLETE" in out and len(out.strip().splitlines()) <= 15
    assert m["project_python"] == ".".join(map(str, sys.version_info[:3]))
    assert m["env"]["HYPOTHESIS_STORAGE_DIRECTORY"] == str(run_dir / "hypothesis")
    assert not (corpus / ".hypothesis").exists(), "Hypothesis's example database must go to the run folder"


def test_run_detects_instrumentation(home, corpus, capsys):
    artifacts = init(corpus, capsys)
    run(artifacts, corpus, sys.executable, "-c", "print('--cov=pkg would be here')", extra=("--instrumented", "auto"))
    assert manifest(artifacts)["instrumented"] == "none"
    run(artifacts, corpus, sys.executable, "-m", "coverage", "--version")
    assert manifest(artifacts)["instrumented"] == "coverage"


@pytest.mark.parametrize(
    ("command", "kind"),
    [
        ("python -m pytest --gremlins --cov=src", "mutation"),
        ("mutmut run", "mutation"),
        ("cosmic-ray exec cr.toml session.sqlite", "mutation"),
        ("python -m pytest tests/test_manifest.py tests/test_infection_model.py", "none"),
        ("python -X importtime -m pytest --collect-only", "profile"),
        ("python -m pytest --testmon", "coverage"),
        ("python -c 'import mutmut; print(mutmut.__version__)'", "none"),  # a version check runs no tool
        ("sh -c 'mutmut run'", "mutation"),
    ],
)
def test_instrumentation_patterns(command, kind):
    assert run_suite.detect_instrumentation(command, {}) == kind


def test_a_declared_mutation_run_is_never_complete(home, corpus, capsys):
    # A mutation tool that drives pytest prints pytest's summary line, which says nothing about the mutants.
    artifacts = init(corpus, capsys)
    command = (sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-q", "tests/test_slow.py")
    assert run(artifacts, corpus, *command, extra=("--instrumented", "mutation")) == 0
    assert "verdict: UNCHECKED" in capsys.readouterr().out
    assert manifest(artifacts)["complete"] is False and manifest(artifacts)["verdict"] == "UNCHECKED"
    assert run_suite.main(["list", "--artifacts", str(artifacts)]) == 0
    assert "UNCHECKED" in capsys.readouterr().out


def test_time_box_stops_the_process_group(home, tmp_path, capsys):
    artifacts = init(tmp_path, capsys)
    code = run(artifacts, tmp_path, sys.executable, "-c", "import time; time.sleep(60)", extra=("--timeout", "1", "--grace", "1"))
    m = manifest(artifacts)
    assert code == 124
    assert m["timed_out"] is True and m["complete"] is False and m["stop_signal"] == "SIGINT"
    assert m["wall_seconds"] < 20


def test_lock_blocks_a_second_run(home, tmp_path, capsys):
    artifacts = init(tmp_path, capsys)
    lock = run_suite.lock_path(artifacts)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit, match="holds the lock"):
            run(artifacts, tmp_path, sys.executable, "-c", "pass")
    assert not (artifacts / "runs").exists() or not any((artifacts / "runs").iterdir()), "no run folder when the lock is refused"


def test_inherited_force_color_is_dropped(home, tmp_path, monkeypatch, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    artifacts = init(project, capsys)
    monkeypatch.setenv("FORCE_COLOR", "3")
    show = (sys.executable, "-c", "import os; print('FORCE_COLOR=' + str(os.environ.get('FORCE_COLOR')))")
    run(artifacts, project, *show)
    newest = sorted((artifacts / "runs").iterdir())[-1]
    assert "FORCE_COLOR=None" in (newest / "output.log").read_text()
    assert manifest(artifacts)["env_dropped"] == ["FORCE_COLOR"]
    run(artifacts, project, *show, extra=("--env", "FORCE_COLOR=1"))
    newest = sorted((artifacts / "runs").iterdir())[-1]
    assert "FORCE_COLOR=1" in (newest / "output.log").read_text()
    assert manifest(artifacts)["env_dropped"] == []


def test_stdin_is_closed(home, tmp_path, capsys):
    artifacts = init(tmp_path, capsys)
    code = run(artifacts, tmp_path, sys.executable, "-c", "input('Type yes to continue: ')")
    assert code != 0
    assert "EOFError" in (Path(manifest(artifacts)["run_dir"]) / "output.log").read_text()


def test_reports_tracked_file_changes(home, tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
        subprocess.run(["git", *args], cwd=repo, check=True)
    (repo / "tracked.txt").write_text("one\n")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    artifacts = init(repo, capsys)
    run(artifacts, repo, sys.executable, "-c", "open('tracked.txt', 'a').write('two\\n'); open('new.txt', 'w').write('x')")
    m = manifest(artifacts)
    assert m["commit"] and m["dirty"] is False
    assert any("tracked.txt" in s for s in m["tracked_files_changed"])
    assert m["new_untracked_files"] == ["new.txt"]
    assert "WARNING" in capsys.readouterr().out


def test_parse_output_understands_other_runners(tmp_path):
    log = tmp_path / "output.log"
    log.write_text("....\n----------------------------------------------------------------------\nRan 4 tests in 0.321s\n\nFAILED (failures=1, skipped=1)\n")
    info = run_suite.parse_output(log)
    assert info["runner"] == "unittest" and info["executed"] == 4 and info["counts"]["failures"] == 1
    log.write_text("created: 4/4 workers\n4 workers [120 items]\n\n==== 118 passed, 2 skipped, 3 rerun in 9.10s ====\n")
    info = run_suite.parse_output(log)
    assert info["workers"] == 4 and info["collected"] == 120 and info["counts"]["rerun"] == 3
    assert run_suite.completeness(info, 0, False) == (True, "complete")
    log.write_text("collected 50 items / 1 error\n!!!! Interrupted: 1 error during collection !!!!\n==== 1 error in 0.50s ====\n")
    info = run_suite.parse_output(log)
    assert run_suite.completeness(info, 2, False)[0] is False
    log.write_text("tests/test_a.py::test_x\n\n90/100 tests collected (10 deselected) in 0.43s\n")
    info = run_suite.parse_output(log)
    assert info["collect_only"] and info["collected"] == 90 and info["reported_seconds"] == 0.43
    assert run_suite.completeness(info, 0, False) == (True, "complete")


@pytest.mark.parametrize(
    ("output", "exit_code", "complete"),
    [
        ("1 deselected, 1 warning in 0.09s\n", 5, True),  # -q run of an empty tier
        ("=== 3 deselected in 0.10s ===\n", 5, True),
        ("no tests ran in 0.10s\n", 5, False),  # -q run that collected nothing
        ("=== no tests ran in 0.10s ===\n", 5, False),
        ("no tests collected (418 deselected) in 0.50s\n", 5, True),  # --collect-only -q of an empty tier
        ("no tests collected in 0.50s\n", 5, False),
    ],
)
def test_empty_selections(tmp_path, output, exit_code, complete):
    log = tmp_path / "output.log"
    log.write_text(output)
    info = run_suite.parse_output(log)
    assert info["runner"] == "pytest"
    assert run_suite.completeness(info, exit_code, False)[0] is complete


def test_quiet_setup_plan_is_complete(tmp_path):
    log = tmp_path / "output.log"
    log.write_text("test_x.py \n        SETUP    F tmp_path\n        test_x.py::test_a (fixtures used: tmp_path)\nno tests ran in 0.09s\n")
    info = run_suite.parse_output(log)
    info["plan_only"] = True
    assert run_suite.completeness(info, 0, False) == (True, "complete")


def test_reruns_in_the_project_configuration_are_recorded(home, tmp_path, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "pytest.ini").write_text("[pytest]\naddopts = -ra --reruns 2\n")
    artifacts = init(project, capsys)
    run(artifacts, project, sys.executable, "-c", "print('hello')")
    assert manifest(artifacts)["reruns_configured"] is True
    (project / "pytest.ini").write_text("[pytest]\nreruns = 1\n")
    run(artifacts, project, sys.executable, "-c", "print('hello')")
    assert manifest(artifacts)["reruns_configured"] is True
    (project / "pytest.ini").write_text("[pytest]\naddopts = -ra\n")
    run(artifacts, project, sys.executable, "-c", "print('hello')")
    assert manifest(artifacts)["reruns_configured"] is False


def test_startup_gap_is_recorded(home, corpus, capsys):
    artifacts = init(corpus, capsys)
    run(artifacts, corpus, sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "--collect-only", "-q")
    m = manifest(artifacts)
    assert m["complete"] is True and m["collected"] == 27
    assert m["startup_gap_seconds"] > 0 and "outside the runner's clock" in capsys.readouterr().out


def test_requested_workers_are_read_from_the_command():
    assert run_suite.requested_workers(["pytest", "-n", "14"], {}) == "14"
    assert run_suite.requested_workers(["pytest", "-n4"], {}) == "4"
    assert run_suite.requested_workers(["pytest", "--numprocesses=auto"], {}) == "auto"
    assert run_suite.requested_workers(["pytest"], {"PYTEST_ADDOPTS": "-n logical -q"}) == "logical"
    assert run_suite.requested_workers(["pytest", "-q"], {}) is None


@pytest.mark.parametrize(
    ("output", "runner", "counts"),
    [
        (" Test Files  2 passed (2)\n      Tests  3 passed | 1 failed (4)\n", "vitest", {"passed": 3, "failed": 1}),
        ("--- PASS: TestA (0.00s)\n--- FAIL: TestB (0.01s)\nok  \texample.com/a\t0.012s\nFAIL\texample.com/b\t0.020s\n", "go",
         {"passed": 1, "failed": 1, "packages_ok": 1, "packages_fail": 1, "packages_cached": 0}),
        ("test result: ok. 5 passed; 0 failed; 1 ignored; 0 measured\ntest result: ok. 2 passed; 1 failed; 0 ignored; 0 measured\n", "cargo",
         {"passed": 7, "failed": 1, "ignored": 1}),
        ("Finished in 1.2 seconds\n12 examples, 1 failure, 2 pending\n", "rspec", {"examples": 12, "failures": 1, "pending": 2}),
        ("OK (5 tests, 10 assertions)\n", "phpunit", {"tests": 5, "assertions": 10}),
        ("[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0\n[INFO] Results:\n[INFO] Tests run: 9, Failures: 1, Errors: 0, Skipped: 2\n", "maven",
         {"run": 9, "failures": 1, "errors": 0, "skipped": 2}),
        ("Passed!  - Failed:     0, Passed:     5, Skipped:     1, Total:     6, Duration: 1 s\n", "dotnet", {"failed": 0, "passed": 5, "skipped": 1, "total": 6}),
    ],
)
def test_parse_output_other_ecosystems(tmp_path, output, runner, counts):
    log = tmp_path / "output.log"
    log.write_text(output)
    info = run_suite.parse_output(log)
    assert info["runner"] == runner and info["counts"] == counts


def test_cached_go_results_are_not_a_measurement(tmp_path):
    log = tmp_path / "output.log"
    log.write_text("ok  \texample.com/a\t(cached)\n")
    info = run_suite.parse_output(log)
    complete, reason = run_suite.completeness(info, 0, False)
    assert complete is False and "-count=1" in reason


def test_coverage_data_in_the_run_folder_marks_the_run_instrumented(home, tmp_path, capsys):
    artifacts = init(tmp_path, capsys)
    run(artifacts, tmp_path, sys.executable, "-c", "open(r'{RUN_DIR}/.coverage', 'w').write('x')")
    assert manifest(artifacts)["instrumented"] == "coverage"


def test_collection_summary_with_errors(tmp_path):
    log = tmp_path / "output.log"
    log.write_text("==== 25 tests collected, 1 error in 0.50s ====\n")
    info = run_suite.parse_output(log)
    assert info["collected"] == 25 and info["collection_errors"] == 1
    assert run_suite.completeness(info, 2, False)[0] is False


def test_cache_redirect_is_skipped_when_the_cache_plugin_is_off(home, corpus, capsys):
    # With filterwarnings = error, an unknown -o cache_dir would stop the run with an internal error.
    pyproject = corpus / "pyproject.toml"
    pyproject.write_text(pyproject.read_text() + 'filterwarnings = ["error"]\n')
    artifacts = init(corpus, capsys)
    code = run(artifacts, corpus, sys.executable, "-B", "-m", "pytest", "-p", "no:randomly", "-p", "no:cacheprovider", "-q", "tests/test_codec.py")
    assert code == 0, (Path(manifest(artifacts)["run_dir"]) / "output.log").read_text()[-1500:]
    assert "cache_dir" not in (manifest(artifacts)["env"].get("PYTEST_ADDOPTS") or "")


def test_lock_is_per_project_wherever_the_audit_home_was(home, tmp_path, capsys, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    artifacts = init(project, capsys)
    monkeypatch.delenv("TEST_SUITE_AUDIT_HOME")  # set only for init, as SKILL.md allows
    assert run_suite.lock_path(artifacts) == artifacts.parent / ".run.lock"
    assert run_suite.lock_path(tmp_path / "loose-folder") == tmp_path / "loose-folder" / ".run.lock"


def test_manifest_and_state_record_the_tools_version(home, tmp_path, capsys):
    project = tmp_path / "proj"
    project.mkdir()
    artifacts = init(project, capsys)
    version = run_suite.tools_version()
    assert len(version) == 10 and f"skill scripts {version}" in (artifacts / "STATE.md").read_text()
    run(artifacts, project, sys.executable, "-c", "print(1)")
    assert manifest(artifacts)["tools_version"] == version


def test_init_resumes_an_audit_named_after_the_repository(home, tmp_path, capsys):
    repo = tmp_path / "mono"
    (repo / "backend").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    old = home / run_suite.project_slug(repo.resolve()) / "20260101-000000"
    (old / "runs").mkdir(parents=True)
    (old / "STATE.md").write_text("# state\n- status: in progress\n")
    assert init(repo / "backend", capsys) == old
