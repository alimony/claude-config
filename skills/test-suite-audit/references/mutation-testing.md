# Mutation testing

This page is the reference for measuring whether tests detect faults, not only whether they run code. Mutation testing injects small faults (mutants) into product code and runs the tests that reach each one. A mutant that no test fails on is a survivor: code that tests execute but do not check. Load this page when phase 7 picks "tests execute code without checking it", when the user asks whether to try mutation testing, or when [redundancy.md](redundancy.md) or [generating-tests.md](generating-tests.md) needs mutation evidence. Writing tests that kill survivors is covered in [generating-tests.md](generating-tests.md).

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Pseudo-tested functions | Extreme mutation: replace each covered function's body with `return None` or a constant, and run its covering tests (M3) | Any in core logic; over about 10% of covered functions in a unit-test suite | A test that asserts the function's result or effect | 6–53% of covered methods, mean 11.4% for unit tests [1]; about 30% worth a test [2] |
| Survivors in covered code | Scoped, sampled mutmut run on hotspots (M4–M7) | 30% or more of a function's mutants survive, or a `return None` or statement-removal mutant survives where callers use the result | Assert exact values and side effects | Mutant detection tracks real-fault detection with coverage held constant [3] |
| Misreported verdicts | Timeouts with 0.0 s durations, 100% scores, empty test maps, stale caches, macOS-only survivors; hand checks (M9) | Always, before you report any number | Fix the configuration, then hand-check 10 kills and 10 survivors | 148 of 1,352 verdicts on one library were crashes counted as timeouts; one tool "killed" 499 of 499 (verified) |
| Boundary survivors | Survivors that change `<` to `<=`, a number by ±1, or `and` to `or` | Any in business rules: limits, prices, dates, permissions | Parametrised cases at, below, and above the boundary | Relational-operator mutants were productive 84.1% of the time at Google [4] |
| Cost beyond the budget | Estimate before the run (M5) | The estimate exceeds the pass budget, for example 2 hours | Scope, sample 400 mutants, limit `max_stack_depth`, mutate only changes | Google cut the median from 820 to 7 mutants per changelist [4] |
| No mutation testing, or a score gate | Continuous integration (CI) configuration: mutation steps and score thresholds | A threshold blocks merges; or critical code has 70%+ coverage and no mutation testing | Survivors as review comments, plus a periodic sample; never a merge gate | Score correlation with real-fault detection is weak once suite size is controlled [5] |
| Unproductive-mutant noise | Survivors in logging, messages, timeouts, caches, `__repr__` | Over 20% of survivors fall in these categories | Suppression rules before you show any survivor | Suppression raised useful mutants from 15–20% to 80–89% at Google [4][6] |
| Equivalent mutants | No input can tell the mutant from the original | Before you count a survivor as a gap | Record it with a reason, and keep it out of the score | About 45% of undetected Java mutants were equivalent, at about 15 minutes each [7] |

## Signals

### Pseudo-tested functions

- **Detect:** Run the extreme-mutation pass (M3). It replaces each covered function's body with `return None`, plus constants the return annotation allows, and runs only the tests that execute the function. A function is pseudo-tested when every extreme mutant survives, and partially tested when some survive. Report every pseudo-tested function in core logic, and a share above about 10% of covered functions in a unit-test suite.
- **False positives:** Developers judged only 30 of 101 pseudo-tested methods worth a test [2]. They rejected generated code, debug and log helpers, exception-message helpers, rarely used features, code being migrated, trivial methods, interface placeholders, and thin wrappers whose delegate is what matters. A function whose side effect an integration test outside the scope checks is also a false positive.
- **Fix:** Add a test that asserts the function's result or effect ([generating-tests.md](generating-tests.md)). A function with no callers outside tests is dead code: report it as a review candidate ([redundancy.md](redundancy.md)).
- **Effect:** The pseudo-tested share of covered methods ranged from 6% to 53%, with means of 11.4% for unit tests and 35.5% for system tests [1]; a replication found 1–46% [2]. So expect about 1 in 9 covered functions in unit-tested code, and about a third of those to deserve a test. Extreme mutation needs 1–3 mutants per function: Descartes took under 2.5 hours where PIT's default engine took over 56 hours on the same project [8].
- **Verify:** Re-run the pass on the function. Every extreme mutant is killed, and the new test passes on the original code.

### Survivors in covered code

- **Detect:** Run a scoped, sampled mutmut pass on modules with at least 70% line coverage (M4–M7). Report a function when at least 30% of its mutants survive, or when a `return None` or statement-removal mutant survives in code whose result callers use. To choose where to spend the budget, use the oracle audit in [coverage.md](coverage.md) (its M7): tests with no assertion, `pytest.raises` without `match=`, and asserts only on truthiness or `is not None`. Survivors confirm those static hits; the hits alone prove nothing.
- **False positives:** The mutant is equivalent. Tests outside the mutmut test selection, or deeper than `max_stack_depth`, check the behaviour. The mutant changes a log or message string. The function exists for side effects that integration tests outside the scope check.
- **Fix:** Assert exact values instead of truthiness; this takes minutes and kills most `return None` and arithmetic survivors. Assert side effects, such as `assert_called_once_with(...)`, rows written, or events emitted. Add `match=` to `pytest.raises` only where the message is part of the contract. For code with invariants, add a property-based test ([techniques.md](techniques.md)). A test written only to kill one mutant can become a change-detector test, and code review at Google rejected such tests [4][9].
- **Effect:** Mutant detection correlated with real-fault detection even with coverage held constant [3]. At Google, the median changelist changed 1 test hunk when mutants were shown and 0 with coverage alone [9].
- **Verify:** Re-run the named mutants (M11). Confirm by hand that the new test fails on the mutant and passes on the original (M9).

### Misreported verdicts

- **Detect:** Check every symptom in this table before you read a score.

| Symptom | Cause |
| --- | --- |
| Every mutant is "no tests", or mutmut says it "could not find any test case for any mutant" | xdist's `-n` in `addopts` or an earlier `mutmut print-time-estimates` (verified), or tests that import code from outside COPY [10] |
| Timeouts with 0.0 s durations or exit code 255, clustered in a few functions | Crashed workers recorded as timeouts: 148 of 1,352 on humanize with the default forkserver warmup (verified) |
| Timeouts rise with `--max-children` | Contention on a shared database or processor [11] |
| Async tests time out after fork | Workers inherit dead thread or connection pools [12] |
| Orphaned processes pile up | Process pools started by tests outlive each mutant: 8,359 orphans and 120 GB of memory in one report [13] |
| A 100% score, or a jump of more than 10 percentage points (pp) between runs without test changes | False kills: pytest-gremlins 1.9.0 reported 499 of 499 humanize mutants killed, yet two of them pass the full suite when applied by hand (verified, [14]) |
| Functions vanish on re-runs with `mutate_only_covered_lines = true` | Stale line numbers drop mutants silently [15] |
| A coverage-guided tool on Python 3.14 or later without `COVERAGE_CORE=ctrace` | Under-selected tests create false survivors: one toy scored 43% instead of 67% (verified; [traps.md](traps.md)) |
| A plain `mutmut run` after test-only changes reports nothing new | mutmut re-tests only mutants whose function changed, so old survivors stay (verified) |
| cosmic-ray kills with pytest exit code 2, 4, or 5 | cosmic-ray counts any non-zero exit, including collection errors, as a kill [16] |
| Survivors in path case, locale, time zone, or platform code, found on macOS | Environment-dependent verdicts: 2 of 30 humanize survivors, `"locale"` to `"LOCALE"` and `"humanize"` to `"HUMANIZE"`, survived only on a case-insensitive file system (verified) |

- **False positives:** A mutant that turns a `while` condition into `True` really hangs, so its timeout is a real kill. Some tests legitimately take longer than the tool's estimate. Behaviour that really differs by platform is a product finding.
- **Fix:** Apply the matching guard from M4. Then delete `mutants/` in the disposable copy and run again, because a resumed run replays old timeout verdicts [11]. For cosmic-ray, run a canary: mutants from its `NoOp` operator must survive [16]. Re-run environment-dependent survivors in the CI container image. Report a tool bug to the user with its reproduction; never file it upstream yourself.
- **Effect:** On humanize, one warmup setting changed 148 of 1,352 verdicts (11%) and revealed 10 hidden survivors, at 36% more run time (verified). The pytest-gremlins score for humanize was unusable (verified).
- **Verify:** Hand-check 10 kills and 10 survivors (M9). The hand verdicts must match the tool's: mutmut matched in 5 of 5 kills and 3 of 3 survivors on humanize (verified).

### Boundary survivors

- **Detect:** Filter survivors by diff: a relational-operator change (`<` to `<=`, `>=` to `>`), a number changed by ±1, `and` to `or`, `break` to `continue`, or a singular-or-plural message branch. Grep `mutmut show` output for these. In 30 sampled humanize survivors, 4 were boundaries and 5 were untested singular-form branches (verified).
- **False positives:** The domain cannot reach the boundary: for integer input, `> 0` and `>= 1` are equivalent. An early exit that only saves time changes speed, not results; go-mutesting's documentation calls these false positives [17].
- **Fix:** Add parametrised cases at the boundary, one step below it, and one step above it. This takes minutes per rule.
- **Effect:** Conditional-operator, relational-operator, and statement-deletion mutants were the ones most often coupled to real faults [3]. At Google, developers found relational-operator mutants productive 84.1% of the time [4].
- **Verify:** Re-run the named mutants (M11); each one is killed.

### Cost beyond the budget

- **Detect:** Estimate the wall time before any run (M5). Flag functions with more than 200 covering tests in `mutmut-stats.json`: that is incidental coverage. cosmic-ray runs the whole test command for every mutant, so its cost is mutants × command time. Report when the estimate exceeds the pass budget, for example 2 hours.
- **False positives:** mutmut runs pytest with `-x`, so a killed mutant stops at its first failing test and costs less than the estimate.
- **Fix:** In this order: scope with `only_mutate` and `pytest_add_cli_args_test_selection`; sample about 400 mutants (M7); set `max_stack_depth`, for example 8; mutate only changes (M8); cache `mutants/` between CI runs; shard across CI machines with identical arguments. A lower `max_stack_depth` runs faster but creates more survivors, so report its value with the results.
- **Effect:** At Google, one mutant per line cut the median from 820 to 77 mutants per changelist, and suppression cut it to 7 [4]. On humanize, a change-scoped run tested 299 mutants in 1 minute 49 seconds, against 1,352 in 5 minutes 31 seconds for the full run (verified). A full run of 50,000 mutants at 5 s of covering tests on 16 workers takes about 4.3 hours, plus two serial runs of the tests.
- **Verify:** Compare the printed "mutations/second" and the wall time with the estimate. Keep the kill rate on a fixed sample stable, to show that scoping kept detection.

### No mutation testing, or a score gate

- **Detect:** Look for `[tool.mutmut]` in `pyproject.toml`, `[mutmut]` in `setup.cfg`, a cosmic-ray TOML file, `fest.toml`, and `[tool.pytest-gremlins]`. Look for CI steps that run `mutmut run`, `cosmic-ray exec`, `stryker`, `pitest`, `cargo mutants`, or `infection`, and for thresholds such as `--min-msi`, `--fail-under`, or `cr-rate --fail-over`. When the project already runs mutation testing, judge its setup against "Misreported verdicts" (guardrail 12).
- **False positives:** Low coverage: every mutant in uncovered code is "no tests" or survives, so report coverage gaps first; Google makes coverage a prerequisite [4]. Flaky tests make verdicts random, so fix them first ([flakiness.md](flakiness.md)).
- **Fix:** Recommend a one-module pilot with mutmut, about an hour, when critical modules have at least 70% line coverage, few flaky tests, and module tests that run in minutes. Then recommend a CI job on changes that posts survivors as review comments: at most one per line and about 7 per changed file (Google's cap [4]). Add a weekly sampled run over the hotspots, because 81% of the mutants relevant to a commit lie outside its diff [18]. Never gate merges on the score: a gate rewards change-detector tests [4].
- **Effect:** Once suite size was controlled, correlations between mutation score and real-fault detection were weak. Yet suites in the top 10% by score still found 11% (Java) to 46% (C) more faults [5]. Google never shows developers a score [4]. Its diff-based mutation testing served 6,000 engineers, and reported usefulness rose from 20% to 80% [6].
- **Verify:** During a pilot, count actionable survivors per hour of reviewer time.

### Unproductive-mutant noise

- **Detect:** Classify survivors by diff. Look for logger, `log.`, and `print` calls; string literals wrapped in `XX` or changed in case; `raise X("message")`; sleep, timeout, retry, and backoff values; caches and memoisation; capacity hints; `__repr__` and `__str__`; `if __name__ == "__main__"`; and `sys.version_info` checks. mutmut mutates single-quoted docstrings but skips all triple-quoted strings. Report when more than 20% of survivors fall in these categories.
- **False positives:** Messages are part of the contract for command-line output, error payloads, and translations: a mutated `ngettext` message ID breaks the lookup.
- **Fix:** In mutmut, set `do_not_mutate_patterns`, use `# pragma: no mutate`, `# pragma: no mutate block`, or a `# pragma: no mutate start` and `end` pair, and list files in `do_not_mutate` [19]. In cosmic-ray, use `cr-filter-pragma`, `cr-filter-operators`, and `cr-filter-lines` [16]. Configure suppression in the disposable copy; pragmas in the project are an approved change.
- **Effect:** String-literal mutants were about 14% of 10,080 mutmut mutants of 10 standard-library modules (verified). At Google, suppressing logging, time, and flag code raised the share of useful mutants from about 15–20% to 80%, and over 100 rules later reached 89% [4][6]. The logging rule was right for 99 of 100 sampled nodes [4].
- **Verify:** Diff the mutant lists before and after suppression. No mutant in business logic disappears.

### Equivalent mutants

- **Detect:** A survivor is equivalent when no input can tell it from the original, for example `"SECONDS"` changed to `"seconds"` before an `.upper()` call. Deciding this is undecidable in general, so classify each survivor by hand, at about 15 minutes each [7].
- **False positives:** Many survivors that look equivalent are killable. Never accept an unreviewed equivalence claim, including a language model's ([generating-tests.md](generating-tests.md), "Mutant closed as equivalent").
- **Fix:** Record the mutant as equivalent in the triage table (M10) with its reason, keep it out of the score, and report the count. `# pragma: no mutate` with the reason is an approved change. Do not build a Trivial Compiler Equivalence (TCE) filter for Python. Only 0.63% of 10,080 mutmut mutants compiled to bytecode identical to the original, and 63 of those 64 were docstring edits (verified). TCE pays off in compiled languages, where it found 21% duplicate mutants in C and 5.4% in Java [20].
- **Effect:** In Java studies, about 45% of undetected mutants were equivalent [7], and 8 of 20 in an earlier sample [21]. On humanize, 3 of 30 sampled survivors were equivalent and 2 more were environment-dependent (verified). So report triaged survivors, not raw counts.
- **Verify:** The user or a second reviewer agrees with each reason in a random sample of your equivalence calls.

## Measuring

`COPY` is the disposable copy, `AUDIT/work/NAME` (M2), `SRC` the package directory under test (for example `src/pkg`), `PKG` its import name, and `SCOPE_TESTS` the tests for that scope. `PYTHON` is the interpreter of an isolated environment, at a new path outside the project, that holds the project's dependencies and the mutation tool (guardrail 4). Every mutation run is instrumented (guardrail 7): mutmut's trampolines made a call-bound test 18 times slower (verified).

### M1. Decide whether to run it

| Condition | Action |
| --- | --- |
| The user did not agree to mutation testing in a disposable copy (phase 1) | Record it under "not measured", and use static and coverage evidence only |
| Critical modules have under 70% line coverage | Report the coverage gaps first ([coverage.md](coverage.md)) |
| Tests in scope fail or flake | Leave them out of the mutation run's selection, and report them: mutmut runs pytest with `-x` and stops when a selected test fails, and flaky tests make verdicts random |
| Tests in scope have side effects, such as email or payments | Leave them out of `pytest_add_cli_args_test_selection`: a mutation run executes them once per mutant ([traps.md](traps.md)) |
| Otherwise | Run M3 on the hotspot modules, then a scoped mutmut sample (M4–M7) on the top hotspots; without `fork`, as on native Windows, use Windows Subsystem for Linux (WSL) or a Linux container |

Run the cheapest pass first. Extreme mutation (M3) needs 1–3 mutants per function; a sample of 400 mutants (M7) gives ±5 pp; a full run suits only small modules. Take hotspots from the ranking in [coverage.md](coverage.md) (its M6). On humanize, the top five functions by churn × complexity held 61% of mutants and 63% of survivors, but had no higher survivor density than the rest (verified). So hotspots show where effort matters, not where survivors are.

### M2. Make the disposable copy and guard it

```sh
git clone --local ROOT COPY                              # guardrail 6; never git worktree add
git -C COPY status --porcelain --untracked-files=no      # prints nothing: the clone holds ROOT's last commit
EXCLUDE="$(git -C COPY rev-parse --path-format=absolute --git-path info/exclude)"
mkdir -p "$(dirname "$EXCLUDE")" && printf 'mutants/\n.coverage*\n' >> "$EXCLUDE"
(cd COPY && PYTHONPATH=SRC_DIRS PYTHON -c 'import PKG; print(PKG.__file__)')   # must print a path inside COPY
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mut-baseline --timeout 900 --cwd COPY -- \
    PYTHON -m pytest -x -q -p no:randomly SCOPE_TESTS
```

- **Why a local clone:** the clone has its own `.git`, so the exclude entry and your commits never reach ROOT (verified). `git worktree add` writes into ROOT's `.git` (guardrail 6). A clone made without git's templates has no `.git/info/`, hence `mkdir -p` (verified).
- **What the clone lacks:** ROOT's uncommitted changes and its untracked generated files (verified). A fresh clone of humanize lacked its generated `_version.py`, so it could not import (verified). Copy such files from ROOT into COPY, or run the project's build step in COPY. Then check the import, because an editable install can make tests import the original code instead of the mutated copy [10]. `SRC_DIRS` is what pytest's `pythonpath` setting adds, such as `src` for a src layout that is not installed. When the project's environment has the project installed in editable mode, set it to `COPY/src` (or the copy's package root), so the copy wins over the original checkout; leave it empty when the project needs neither.
- **Commit in COPY:** commit your mutation configuration there, so each run starts from a clean tree and a mutant left behind shows up.
- **Stopping:** `run_suite.py`'s time box sends SIGINT, waits 30 seconds (`--grace`), then sends SIGTERM and SIGKILL. SIGINT matters for tools that edit source files in place. cosmic-ray restored its file after SIGINT in 3 of 3 trials, but left it mutated after SIGTERM in 3 of 3 and after SIGKILL in 6 of 6 (verified). The extreme-mutation pass restores its file on SIGINT, SIGTERM, and SIGHUP, but no tool survives SIGKILL (verified). `timeout` and most CI cancellations send SIGTERM, so never let them stop cosmic-ray, and keep the time box shorter than any outer time limit. mutmut never edits the source tree, so stopping it loses only unfinished results.
- **After every run:** `run_suite.py` compares `git status` in COPY before and after, and prints `WARNING: N tracked files changed during the run` when a mutant was left behind. Then discard COPY and start again. Never copy anything from COPY into ROOT: tests run hundreds of times there, and on humanize a translation test rewrote `.po` files inside `mutants/` (verified).

### M3. Find pseudo-tested functions first

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label pseudo --timeout 3600 --cwd COPY -- \
    PYTHON ${CLAUDE_SKILL_DIR}/scripts/pseudo_tested.py --audit AUDIT --src SRC --out {RUN_DIR}/pseudo.jsonl \
    --tests SCOPE_TESTS --max-funcs 300 --seed 1 --timeout 300 -- -p no:xdist
tail -15 AUDIT/runs/NN-pseudo/output.log            # the script's summary
```

- **How it works:** a canary runs first: the selected tests must pass on unmutated code, or the script stops with exit 3 before it writes anything. One pytest run then records per-test coverage contexts with pytest-cov, under `COVERAGE_CORE=ctrace`, which the script sets itself. A check runs the first function's covering tests by node ID, the way mutant runs do. Then, for up to `--max-funcs` covered functions chosen at random with `--seed`, it writes each extreme mutant into the file, deletes the module's cached bytecode, runs only the covering tests with `-x`, and restores the file.
- **Verdicts:** killed (pytest exit 1), survived (exit 0), and unknown: a timeout (`--timeout`, default 300 s) or exit 2, 3, 4, or 5, never counted as a kill. A function is pseudo-tested when every mutant survived, partially tested when some were killed and some survived, tested when all were killed, and unknown otherwise.
- **Output:** a summary of at most 15 lines at the end of `output.log`, with a 95% Wilson interval for the pseudo-tested share of classified functions. The JSON Lines file holds one line per mutated function, with its verdicts, exit codes, and first covering tests, flushed as written. On a toy project with 5 covered functions, it found 1 pseudo-tested, 1 partially tested (`is_empty`, where `return True` survived), 1 tested, and 2 unknown (a timeout and a broken collection) in about 7 seconds (verified).
- **Safety:** it refuses to start (exit 2) unless `--audit` holds the audit's `STATE.md`, and the current directory and every `--src` path resolve inside it. It also refuses a tree with tracked changes, which is what a mutant left by a killed run looks like. It exits 1 when a touched file does not match its original bytes afterwards.
- **It skips:** uncovered functions (a coverage finding), bodies under 2 statements (`--min-stmts 1` includes them), one-line definitions, nested functions, generators, and `__init__`, `__repr__`, `__str__`, `__hash__`, `__eq__`, and `__del__`.
- **Arguments:** everything after `--` reaches every pytest run unchanged, so two-token flags work (verified). Give each test path its own `--tests`: mutant runs replace those paths with the covering node IDs. When `addopts` holds `-n`, pass `-n 0` instead of `-p no:xdist`, which then fails with exit 4.
- **Suspect a clean result:** zero pseudo-tested functions in a sample of 100 or more is unlikely, because the lowest shares in the studies were about 1–2% [1][2]. Hand-check a few kills (M9) before you report it. Even a true clean result proves little: Descartes scored above 83% on projects where standard mutation scores were medium to low [8], so follow it with M4–M7 on the hotspots.
- **Cost:** two runs of the selected tests, the canary and the coverage run, plus one to three pytest processes per function. Each process pays pytest start-up and conftest imports, so multiply the time of one trivial test ([fixed-costs.md](fixed-costs.md)) by about twice the number of functions.

### M4. Configure a scoped mutmut run

Add this to COPY's `pyproject.toml`, and commit it in COPY:

```toml
[tool.mutmut]
source_paths = ["src/"]
only_mutate = ["src/pkg/billing/*"]                # a hotspot or a critical module
pytest_add_cli_args_test_selection = ["tests/unit/billing"]
pytest_add_cli_args = ["-n", "0"]                  # only when pytest-xdist is installed and -n is in addopts
also_copy = ["conftest.py", "tests/fixtures/"]     # a root conftest and non-Python files the tests need
max_stack_depth = 8                                # ignores callers deep in the stack; report the value
process_isolation = "forkserver"                   # tests use database pools, grpc, torch, gevent, or threads
forkserver_warmup = "none"                         # timeouts show 0.0 s durations or exit code 255
do_not_mutate_patterns = ['logger\.\w+', 'logging\.\w+', 'log\.\w+']
```

| Trap | Guard |
| --- | --- |
| xdist's `-n` in `addopts` makes the stats phase find no tests, and `-p no:xdist` fails with exit code 4 | `pytest_add_cli_args = ["-n", "0"]` (verified) |
| The clean run fails under mutmut, but the same tests pass alone in `mutants/` | State leaks between repeated in-process pytest runs: `process_isolation = "forkserver"` (verified) |
| A test needs a file outside the source tree | List it in `also_copy`: humanize needed `scripts/` (verified) |
| The suite is database-bound | mutmut cannot give each worker its own database [22], so use `--max-children` 1–2 [11] |
| Django | A root `conftest.py` that calls `django.setup()` once, listed in `also_copy`, run without pytest-django: about 83% on service modules in one report [23] |

In mutmut 3.8.0's source, `process_isolation` is `fork` (the default) or `forkserver`, and `forkserver_warmup` is `collect` (the default), `import`, or `none` (verified). mutmut mutates only code inside functions, runs only pytest, and needs `fork`: Linux, macOS, or WSL [19][24]. mutmut 3.8.0 made no mutants for the methods of a class that subclasses `typing.NamedTuple`, such as urllib3's `Url` (verified 2026-10-01), so check the mutant count per function before you read a high score as strong tests.

### M5. Estimate the cost before the run

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mut-generate --timeout 3600 --cwd COPY -- \
    PYTHON -m mutmut run zzz_no_such_mutant          # builds mutants and the test map, then exits 1: expected
(cd COPY && PYTHON - <<'PY'
import glob, json, statistics
n = sum(len(json.load(open(m))["exit_code_by_key"]) for m in glob.glob("mutants/**/*.py.meta", recursive=True))
st = json.load(open("mutants/mutmut-stats.json"))
tests, dur = st["tests_by_mangled_function_name"], st["duration_by_test"]
assert tests, "empty test map: fix the configuration before you continue"
per_fn = [sum(dur.get(t, 0) for t in ts) for ts in tests.values()]
print(f"{n} mutants; {len(tests)} functions with tests; median covering-test time {statistics.median(per_fn):.3f} s")
print("functions with more than 200 covering tests:", sum(len(ts) > 200 for ts in tests.values()))
PY
)
```

- **Reading it:** wall time ≈ 2 × serial time of the selected tests + mutants × (median covering-test time + 1.5 s) ÷ workers. mutmut runs the selected tests serially twice, a stats run and a clean run, before any mutant. The 1.5 s overhead is humanize's with `forkserver` and warmup `none`; default fork mode costs less (verified).
- **The dummy name is a workaround:** mutmut ends with "Filtered for specific mutants, but nothing matches". In one of two trials the test map came back empty, so never skip the assertion (verified).
- **Cost:** one serial run of the selected tests with trampolines. That took seconds on humanize (746 tests, 8.7 s serial), but it can take hours for tests that need 60 minutes on 16 xdist workers.

### M6. Run mutmut and read the results

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mut-billing --timeout 7200 --cwd COPY -- \
    PYTHON -m mutmut run --max-children 4
tr '\r' '\n' < AUDIT/runs/NN-mut-billing/output.log | grep -E 'mutations/second|Error' | tail -3
(cd COPY && PYTHON -m mutmut results --all true) > AUDIT/mut-billing-results.txt     # every mutant, as "name: status"
(cd COPY && PYTHON -m mutmut show pkg.billing.x_apply_discount__mutmut_7)            # the diff of one mutant
(cd COPY && PYTHON -m mutmut tests-for-mutant pkg.billing.x_apply_discount__mutmut_7)
python3 - COPY/mutants <<'PY'                     # add a names file, such as AUDIT/sample.txt, for a sampled run
import glob, json, math, sys
from collections import Counter
CODE = {0: "survived", 1: "killed", 3: "killed", 5: "no tests", 33: "no tests", 34: "skipped", 37: "type check", 24: "timeout",
        -24: "timeout", 36: "timeout", 152: "timeout", 255: "timeout", -9: "segfault", -11: "segfault", None: "not checked"}
names = set(open(sys.argv[2]).read().split()) if len(sys.argv) > 2 else None
c = Counter(CODE.get(v, f"exit {v}") for m in glob.glob(f"{sys.argv[1]}/**/*.py.meta", recursive=True)
            for key, v in json.load(open(m))["exit_code_by_key"].items() if names is None or key in names)
print(dict(c))
k, n, z = c["killed"], c["killed"] + c["survived"], 1.96
if n:
    p, d = k / n, 1 + z * z / n
    mid, half = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    print(f"score {k}/{n} = {p:.1%}, 95% Wilson interval {mid - half:.1%} to {mid + half:.1%}")
PY
```

- **Completeness:** `run_suite.py` shows UNCHECKED for a mutation run (guardrail 8). A full run is complete when the counts show no `not checked`; a sampled run, when none of its names is `not checked`. The wrapper detects mutmut, cosmic-ray, mutatest, poodle, the extreme-mutation pass, fest, pytest-gremlins, Stryker, PIT, cargo-mutants, Infection, and go-mutesting; pass `--instrumented mutation` for any other tool. Every declared or detected mutation run shows UNCHECKED, even when its output has a pytest summary line. Run long passes in the background and wait with Monitor (SKILL.md); the progress spinner stays in `output.log`, out of your context.
- **Verdicts:** read them from `exit_code_by_key` in `mutants/**/*.py.meta`, never from the spinner [24]. The score is killed ÷ (killed + survived), with timeouts, "no tests", and errors listed apart. `mutmut export-cicd-stats` writes the counts to `mutants/mutmut-cicd-stats.json`, but mutmut's badge counts timeouts as kills.
- **Names:** `module.x_func__mutmut_N` for functions, and `module.xǁClassǁmethod__mutmut_N` for methods.
- **Comparability:** scores compare only within one tool, version, operator set, and `max_stack_depth`. On identical code, mutmut made 1,352 mutants and pytest-gremlins 499 (verified).
- **Example:** on humanize, 1,190 killed, 161 survived, and 1 timeout gave 88.1% (95% interval 86.2–89.7%) in 5 minutes 31 seconds on 8 workers (verified).

| Command | Problem | Use instead |
| --- | --- | --- |
| `mutmut browse` | An interactive terminal interface that blocks you | `mutmut results --all true` and `mutmut show NAME` |
| `mutmut apply NAME`, `cosmic-ray apply` | They write the mutant into source files | A second disposable copy (M9) |
| `mutmut print-time-estimates` | In 3.8.0 it cut the test map from 10 links to 0, and later runs said "no tests" (verified) | M5; if it happened, delete `mutants/` |
| `mutmut results --all` | It fails: the flag needs a value | `--all true` |
| `mutmut --help` outside a project | It fails when mutmut cannot find the source (verified) | Run it in COPY with `source_paths` set |
| A plain `mutmut run` after test changes | It re-tests nothing and keeps stale survivors (verified) | Named mutants (M11) |
| `xargs mutmut run` on an empty file | GNU `xargs` then runs mutmut once without names, which tests every mutant | Guard with `[ -s FILE ]`; macOS `xargs` runs nothing (verified) |
| `cosmic-ray new-config` | It prompts, and aborts without a terminal (verified) | Write the TOML by hand (M7) |

### M7. Sample mutants with a confidence interval

```sh
(cd COPY && PYTHON - > AUDIT/sample.txt <<'PY'
import glob, json, random
names = sorted(k for m in glob.glob("mutants/**/*.py.meta", recursive=True) for k in json.load(open(m))["exit_code_by_key"])
random.seed(20260930)
print("\n".join(random.sample(names, min(400, len(names)))))
PY
)
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mut-sample --timeout 7200 --cwd COPY -- \
    sh -c '[ -s AUDIT/sample.txt ] && xargs PYTHON -m mutmut run --max-children 4 < AUDIT/sample.txt'
```

Run M5 first, so the `.meta` files exist, and M6's snippet with `AUDIT/sample.txt` afterwards. Record the seed.

| Sample size | 95% half-width at a 50% score | At an 80% score |
| --- | --- | --- |
| 100 | ±9.8 pp | ±7.8 pp |
| 200 | ±6.9 pp | ±5.5 pp |
| 385 | ±5.0 pp | ±4.0 pp |
| 1,000 | ±3.1 pp | ±2.5 pp |

- **Finite populations** need slightly fewer: 323 of 2,000 mutants, or 370 of 10,000, for ±5 pp.
- **Comparing runs:** two samples of 400 near a 70% score differ by up to ±6.4 pp from chance alone. Claim a change only when the intervals do not overlap, or when a two-proportion test says so.
- **Stratify:** take equal numbers per module to compare modules, and weight by module size for an overall score.
- **Biased samples:** never estimate from an interrupted mutmut run, because mutmut runs the fastest mutants first [24]. Never estimate from `cargo mutants --shard k/n` with the default `slice` algorithm, which takes contiguous blocks [25].
- **Periodic runs:** repeat the sample weekly over the hotspots, with the same size and a recorded seed, so that intervals compare over time.
- **cosmic-ray alternative:** `exec` takes pending jobs in random order, so a time-boxed session is a random sample, and `cr-rate --estimate` prints the survival rate's interval [16]. The time box stops `exec` with SIGINT, which restores the source (M2). It runs the whole test command for every mutant, sequentially: 1.6 mutants per second on a toy, against 70–125 for mutmut (verified). Write `cr.toml` by hand:

```toml
[cosmic-ray]
module-path = "src/pkg/billing.py"
timeout = 30.0
excluded-modules = []
test-command = "PYTHON -m pytest -x -q tests/unit/billing"

[cosmic-ray.distributor]
name = "local"
```

```sh
(cd COPY && cosmic-ray init cr.toml cr.sqlite)     # scans the code; runs no tests
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label cr-baseline --timeout 900 --cwd COPY -- cosmic-ray baseline cr.toml
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label cr-exec --timeout 3600 --cwd COPY -- cosmic-ray exec cr.toml cr.sqlite
(cd COPY && cr-rate --estimate --confidence 95.0 cr.sqlite && cr-report --surviving-only cr.sqlite)
```

A partial session of 20 of 81 mutants estimated 50.0% survival (39.0–61.0%) against a final 44.4% (verified). For fewer than about 100 mutants, compute a Wilson interval yourself: `cr-rate` uses a normal approximation with a non-standard finite-population factor [16].

### M8. Mutate only a change

For a pull request, or for the last few merged changes, run only the mutants of the changed functions:

```sh
git -C COPY diff -U0 BASE...HEAD -- SRC                  # the changed lines; find the function around each hunk
printf '%s\n' 'pkg.billing.x_apply_discount__mutmut_*' 'pkg.billing.xǁInvoiceǁtotal__mutmut_*' > AUDIT/changed.txt
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mut-change --timeout 3600 --cwd COPY -- \
    sh -c '[ -s AUDIT/changed.txt ] && xargs PYTHON -m mutmut run --max-children 4 < AUDIT/changed.txt'
(cd COPY && PYTHON -m mutmut results) | grep -F -f <(sed 's/\*$//' AUDIT/changed.txt)   # survivors in the changed functions
```

- **Names:** one glob per changed function: `MODULE.x_FUNC__mutmut_*`, or `MODULE.xǁCLASSǁMETHOD__mutmut_*` for a method, where `MODULE` is the dotted path below the source root in `source_paths`. Count decorators as part of the function. `BASE` is the change's base: in the clone, ROOT's local branches appear as `origin/NAME`, such as `origin/main` (verified).
- **Granularity:** whole functions. On humanize, a one-token change and a comment re-ran 299 mutants in 1 minute 49 seconds (verified). cosmic-ray works per line: `cr-filter-git --config cr.toml cr.sqlite`, with `branch = "main"` under `[cosmic-ray.filters.git-filter]`, because the default branch is `master` [16].
- **In CI:** cache `mutants/` from the main branch. A plain `mutmut run` then re-tests only functions whose code changed, but not functions whose tests changed (verified).
- **Surfacing:** post at most one survivor per line and about 7 per changed file, as review comments [4]. In more than 90% of lines, all of a line's mutants were killed or none were, so one per line loses little [9].
- **Limits:** a change to tests only produces no mutants [25], and 81% of the mutants relevant to a commit lie outside its changed lines [18]. So pair change-scoped runs with the periodic sample (M7).

### M9. Hand-check kills and survivors

For a random sample of 10 kills and 10 survivors, and for every survivor you report:

```sh
git clone --local ROOT COPY2                               # a second disposable copy, AUDIT/work/hand
(cd COPY && PYTHON -m mutmut show NAME) > AUDIT/mutant.diff
python3 - AUDIT/mutant.diff COPY2 <<'EOF'                 # apply the hunk as text: see "Applying a mutant"
import sys
from pathlib import Path
lines = Path(sys.argv[1]).read_text().splitlines()[1:]     # drop the mutant's name
target = Path(sys.argv[2], lines[0][4:].strip())           # from "--- src/pkg/module.py"
body = [l for l in lines[2:] if not l.startswith(("@@", "\\"))]
old = "\n".join(l[1:] for l in body if l[:1] in (" ", "-", "")) + "\n"
new = "\n".join(l[1:] for l in body if l[:1] in (" ", "+", "")) + "\n"
text = target.read_text()
assert text.count(old) == 1, f"the original lines occur {text.count(old)} times in {target}"
target.write_text(text.replace(old, new))
EOF
git -C COPY2 diff
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label hand-NAME --timeout 900 --cwd COPY2 -- \
    PYTHON -m pytest -q -p no:randomly COVERING_TESTS --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
git -C COPY2 checkout -- .                                 # restores COPY2 only; never run this in ROOT
```

- **Reading it:** add generated files as in M2, and take `COVERING_TESTS` from `mutmut tests-for-mutant NAME`. A failing run confirms a kill, and a passing run confirms a survivor. The hand verdicts must match the tool's.
- **Applying a mutant:** `mutmut show` numbers hunk lines from the start of the function, not the file. When the mutated line ends the function, the hunk has less trailing than leading context, so `patch` must match it at the end of the file: macOS's patch then reports "1 out of 1 hunks failed" and leaves `.orig` and `.rej` files (verified 2026-10-01). The snippet replaces the hunk's original lines as text instead, and stops when they do not occur exactly once. Check that `git diff` shows the intended line. Rebuild `mutants/` after the code in COPY changes: two humanize survivors could not be applied after `mutants/` came from another branch (verified).
- **`mutmut apply`:** it writes the mutant into the source files of the disposable copy it runs in, where a later `mutmut run` would mutate mutated code. Use it only in COPY2, or restore at once as [generating-tests.md](generating-tests.md) shows.
- **Linux check:** re-run survivors in a Linux container like CI's before you report them.
- **Your own on-disk scripts:** two same-length edits within one second reuse the old `.pyc` and give a wrong verdict (verified). Set `PYTHONDONTWRITEBYTECODE=1` and delete the module's `__pycache__` entries before each run; cosmic-ray and the extreme-mutation pass already do this.

### M10. Triage survivors into findings

For each sampled survivor, read `mutmut show` and `mutmut tests-for-mutant`, confirm it by hand (M9), and classify it:

| Category | Test | Action | 30 humanize survivors |
| --- | --- | --- | --- |
| Missing input or boundary | A realistic input makes the mutant misbehave, but no test uses it | Add a parametrised case | 22: 4 boundaries, 5 singular forms, 6 locale paths, 7 other inputs |
| Weak oracle | Tests reach the code but assert too little | Strengthen the assertion | 2 |
| Equivalent | No input can tell the mutant from the original | Record the reason; keep it out of the score | 3 |
| Environment-dependent | Equivalent only on your machine or locale | Re-run on Linux in the CI image | 2 |
| Unproductive | Log, message, timing, or caching code | Add a suppression rule | 0 |
| Dead code | Nothing outside tests calls the function | A review candidate for removal | – |
| Unclear | It needs domain knowledge | Ask the maintainers | 1 |

Report at most the 10–20 most valuable survivors, each as one `adequacy` finding ([findings.md](findings.md)):

```json
{"id": "ADQ-003", "title": "No test checks the member-discount threshold", "dimension": "adequacy",
 "claim": "Changing `total >= 100` to `total > 100` at src/pkg/billing.py:41 passes all 3 covering tests, so an off-by-one in the discount rule would ship.",
 "evidence": [
  {"kind": "mutation", "artifact": "mut-billing-results.txt", "command": "mutmut show pkg.billing.x_apply_discount__mutmut_7", "location": "src/pkg/billing.py:41", "note": "survived; confirmed by hand in runs/12-hand-mutmut_7"},
  {"kind": "coverage", "test_id": "tests/unit/billing/test_discount.py::test_member_discount", "note": "a covering test from mutmut tests-for-mutant; it checks only totals far above 100"}],
 "impact": {"level": "high", "metric": "survivors in top-decile hotspots", "estimate": 1, "basis": "measured"},
 "effort": "S", "risk": "low", "confidence": "high", "action": "add-tests",
 "recommendation": "Add parametrised member cases for totals of 99, 100, and 101 to tests/unit/billing/test_discount.py.",
 "verification": "In a fresh copy of the change branch, mutmut run 'pkg.billing.x_apply_discount*' reports the mutant killed, and the new cases pass the acceptance chain in generating-tests.md.",
 "status": "confirmed"}
```

- **Evidence:** the `mutation` kind supports "no test detects this fault". Add `coverage` for the covering tests, or `static` for the weak assertion's line. Copy results and diffs from COPY into AUDIT before you delete COPY, because `findings.py` checks that each artifact exists. Cite locations and test IDs as they are in ROOT; COPY has the same paths.
- **Confidence:** medium for a tool verdict alone, high once a hand check reproduces it, and low for a static hit without a run.
- **Impact:** follow [findings.md](findings.md): survivors in the top decile of churn × complexity are high, in often-changed code medium, and in stable or trivial code low.
- **Trust breakers:** set `trust_breaker` only when the covering test is itself one, such as an assertion that cannot fail. Budget about 15 minutes per survivor [7].
- **Scores:** a score goes in the report only with its interval, scope, tool, version, and `max_stack_depth`, as context. Few survivors do not mean few bugs: 17% of real faults were coupled to no mutant [3]. For removal candidates, mutation evidence is one of two required kinds: see "Differential mutation: unique kills" in [redundancy.md](redundancy.md).

### M11. Verify a fix

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mut-verify --timeout 3600 --cwd COPY -- \
    PYTHON -m mutmut run "pkg.billing.x_apply_discount*"
(cd COPY && PYTHON -m mutmut results --all true) | grep "x_apply_discount"   # each target mutant now says killed
```

- Name the mutants: a plain `mutmut run` re-tests nothing after test-only changes and keeps stale survivors (verified).
- The fix holds when the targeted mutants flip to killed, the other verdicts in the module stay the same, and the selected tests still pass on the original code.
- Read every newly killed mutant: one that matches the specification means the new test locks in a bug ([generating-tests.md](generating-tests.md), "A newly killed mutant is the fix"). Put new tests through the acceptance chain on that page, and compare sampled scores by their intervals (M7).

## Tools

Versions checked on 2026-09-30. For test runners and coverage in other ecosystems, see [runners-and-ecosystems.md](runners-and-ecosystems.md).

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| mutmut | The default Python tool: scoped, sampled, and change-scoped runs | 3.8.0, 2026-09-12, maintained [24] | Same verdicts on CPython 3.14.0 and free-threaded 3.14.7t with pytest 9.1.1 (verified). Needs `fork`, runs only pytest, mutates only code inside functions, and skips triple-quoted strings. Open correctness bugs: [10][11][12][13][15]. |
| cosmic-ray | Resumable, randomly ordered, time-boxed sessions with an interval; a line-level git filter | 8.7.0, 2026-08-09, maintained [16] | Edits files in place. No per-mutant test selection, and the local distributor is sequential. Re-run `init` after code changes. Ran on Python 3.14.0 (verified). |
| pytest-gremlins | Nothing yet: do not trust its verdicts | 1.9.0, 2026-07-01, alpha, maintained [26] | False kills on humanize (verified). Its lightweight runner calls test functions directly, so parametrised, async, and fixture tests never run [14]. Needs `COVERAGE_CORE=ctrace`. |
| fest-mutate; poodle | Nothing until verified | fest-mutate 0.1.3, 2026-03-14, new [27]; poodle 1.3.4, 2026-04-05, partly maintained (previous release 2024) [28] | Neither was run in the research. fest's speed figures are the vendor's own; its subprocess backend overwrites source files, and its plugin backend falls back to it on errors. |
| mutatest; MutPy | Avoid | 3.1.0 (2022-02-20); 0.6.1 (2019-11-17); not maintained [28] | Classifiers end at Python 3.8 and 3.7. |
| mutahunter | Mutants generated by a large language model (LLM) | 1.3.2, 2025-04-17, maintenance unclear [28] | LLM cost and nondeterminism. |
| coverage.py | Per-test contexts for the extreme-mutation pass and coverage-guided tools | 7.16.2, maintained [29] | On Python 3.14 its default `sysmon` core drops dynamic contexts: set `COVERAGE_CORE=ctrace`, with `run_suite.py --env COVERAGE_CORE=ctrace` for your own tools. |
| PIT with Descartes | Java virtual machine (JVM) mutation, and extreme mutation for pseudo-tested methods | PIT 1.30.0, 2026-08-27; Descartes 1.3.4, 2025-09-19; maintained [30] | `-DwithHistory` for incremental runs. Descartes' README names version 1.3.34, which is not on Maven Central. |
| StrykerJS; Stryker.NET | JavaScript and TypeScript; C# | 10.0.0, 2026-08-14; 5.0.0, 2026-09-11; maintained [31] | `npx stryker run --incremental`, which ignores changes outside mutated and test files; `dotnet stryker --since:main --with-baseline`. |
| cargo-mutants | Rust | 27.1.0, 2026-06-02, maintained [25] | Copies the tree to a scratch directory. `cargo mutants --in-diff FILE`; shards need identical arguments and at least 10 mutants each. |
| gremlins; go-mutesting | Go | 0.6.0, 2025-12-06; 2.3.1, 2025-12-26 [17][32] | `gremlins unleash --diff origin/main`; big modules can take hours. go-mutesting replaces the original file while it tests. |
| mutant | Ruby | 0.17.0, 2026-09-17, maintained [33] | `mutant run --since main`; private code needs a commercial licence. |
| Infection | PHP | 0.35.5, 2026-09-27, maintained [34] | `infection --git-diff-lines --git-diff-base=origin/main`. |
| Mull | C and C++, through an LLVM plugin | 0.34.1, 2026-09-13, maintained [35] | `gitDiffRef` in `mull.yml`; tied to supported LLVM versions. |

## Evidence

- Just et al., 2014: of 357 real faults in 5 programs, 73% were coupled to mutants from common operators, 10% needed a new or stronger operator, and 17% were coupled to none. Mutant detection correlated with real-fault detection independently of coverage [3].
- Papadakis et al., 2018: correlations between mutation score and real-fault detection were weak once suite size was controlled. The top 25% and 10% of suites by score still found 8% and 11% more faults on Defects4J (Java), and 18% and 46% more on CoreBench (C) [5].
- Petrović et al., 2021, on fault coupling: 70% of 1,502 high-priority Google bugs would have had a reported, fault-coupled mutant on their bug-introducing changes. 14 of 50 uncoupled bugs traced to weak operators [9].
- Petrović et al., 2021, on practice at scale: 16,935,148 mutants on 776,740 changelists, 2,110,489 surfaced. 82% of mutants with feedback were productive: Java 87.2%, Python 70.6%. More than 100 suppression rules [4].
- Petrović and Ivanković, 2018: 6,000 engineers, over 70,000 diffs, 1.1 million mutants, and 150,000 findings. Python had 11% of mutants and the highest survival rate, 14.7% [6].
- Niedermayr et al., 2016: 14 Java projects; pseudo-tested shares of 6–53%, with means of 11.41% for unit tests and 35.48% for system tests [1].
- Vera-Pérez et al.: more than 28,000 methods; pseudo-tested methods in every project, from 1% to 46%. Coverage and pseudo-tested share correlated at −0.67. All 7 pull requests with new tests were merged [2].
- Vera-Pérez et al., 2018 (Descartes): under 2.5 hours against over 56 hours with PIT's default engine on Spoon. It took 1.5 against 16 hours on JGit, and under 2 against about 25 minutes on Jaxen. The two scores correlated at Spearman 0.6 [8].
- Schuler and Zeller, 2010: about 45% of undetected Java mutants were equivalent, at about 15 minutes each to classify [7]. Grün et al., 2009: 8 of 20 [21].
- Ojdanic et al.: more than 10 million mutants over 288 commits. 81% of commit-relevant mutants lay outside the changed code, and simple features did not predict which mutants were relevant [18].
- Papadakis et al., 2019 survey: TCE found 21% duplicate mutants in C and 5.4% in Java. The best selection strategy beats random sampling by at most about 13%, so prefer random samples with an interval [20].
- mutmut issue reports: a database-bound Django suite on 6 cores had 616 spurious timeouts at default parallelism [11]. A FastAPI suite with asyncpg timed out on 15 of 15 mutants after fork [12]. A PyTorch project left 8,359 orphaned processes and exhausted 120 GB of memory [13].
- Hands-on runs for this page, 2026-09-30 and 2026-10-01, on macOS on Apple silicon with Python 3.14.0, pytest 9.1.1, mutmut 3.8.0, and cosmic-ray 8.7.0, marked "(verified)" above: the humanize library [36] (1,725 source lines, 746 tests, 8.7 s serial) scored 88.1% (86.2–89.7%) with mutmut. pytest-gremlins reported 499 of 499 killed on the same code. `COVERAGE_CORE=ctrace` raised a toy score from 43% to 67%. cosmic-ray left mutants in the source after every SIGTERM and SIGKILL.

## Sources

1. https://arxiv.org/abs/1611.07163 – Niedermayr et al. 2016, "Will my tests tell me if I break this code?"
2. https://arxiv.org/abs/1807.05030 – Vera-Pérez et al., "A comprehensive study of pseudo-tested methods"
3. https://homes.cs.washington.edu/~mernst/pubs/mutation-effectiveness-fse2014.pdf – Just et al. 2014, "Are mutants a valid substitute for real faults in software testing?"
4. https://arxiv.org/abs/2102.11378 – Petrović et al. 2021, "Practical mutation testing at scale: a view from Google"
5. https://orbilu.uni.lu/bitstream/10993/34950/1/ICSE-main18b%20%281%29.pdf – Papadakis et al. 2018, "Are mutation scores correlated with real fault detection?"
6. https://storage.googleapis.com/gweb-research2023-media/pubtools/4203.pdf – Petrović and Ivanković 2018, "State of mutation testing at Google"
7. https://www.st.cs.uni-saarland.de/publications/files/schuler-icst-2010.pdf – Schuler and Zeller 2010, "(Un-)covering equivalent mutants"
8. https://arxiv.org/abs/1811.03045 – Vera-Pérez et al. 2018, "Descartes: a PITest engine to detect pseudo-tested methods"
9. https://arxiv.org/abs/2103.07189 – Petrović et al. 2021, "Does mutation testing improve testing practices?"
10. https://github.com/boxed/mutmut/issues/486 – editable installs import unmutated code
11. https://github.com/boxed/mutmut/issues/545 – mutmut timeouts under parallelism on a database-bound Django suite (practitioner report)
12. https://github.com/boxed/mutmut/issues/578 – forked workers inherit dead pools, and async tests time out
13. https://github.com/boxed/mutmut/issues/584 – process pools outlive mutants: 8,359 orphaned processes
14. https://github.com/mikelane/pytest-gremlins/issues/486 – pytest-gremlins 1.9.0's lightweight runner calls test functions directly (practitioner report citing source lines)
15. https://github.com/boxed/mutmut/issues/555 – `mutate_only_covered_lines` drops mutants on re-runs
16. https://pypi.org/pypi/cosmic-ray/json and https://github.com/sixty-north/cosmic-ray – cosmic-ray release history, and the 8.7.0 source: random job order, `cr-rate`, the git filter, exit-code handling, and the NoOp operator
17. https://github.com/avito-tech/go-mutesting – go-mutesting README: in-place file replacement and known false positives
18. https://arxiv.org/abs/2112.14566 – Ojdanic et al., "Mutation testing in evolving systems: studying the relevance of mutants to code evolution"
19. https://github.com/boxed/mutmut/blob/main/README.rst – mutmut configuration keys, pragmas, and process isolation
20. https://mutationtesting.uni.lu/survey.pdf – Papadakis et al. 2019, "Mutation testing advances: an analysis and survey"
21. https://www.st.cs.uni-saarland.de/publications/files/gruen-mutation-2009.pdf – Grün, Schuler, and Zeller 2009, "The impact of equivalent mutants"
22. https://github.com/boxed/mutmut/issues/474 – no per-worker databases for parallel mutants
23. https://github.com/boxed/mutmut/issues/504 – a working mutmut recipe for Django (practitioner report)
24. https://pypi.org/pypi/mutmut/json and https://pypi.org/project/mutmut/3.8.0/#files – mutmut release history and classifiers, and the 3.8.0 wheel whose source was read (verdict codes, mutant order, schemata)
25. https://github.com/sourcefrog/cargo-mutants/tree/main/book/src – cargo-mutants book: `--in-diff`, tree copying, timeouts, and sharding
26. https://github.com/mikelane/pytest-gremlins – pytest-gremlins README and flags (vendor)
27. https://github.com/sakost/fest – fest README, backends, and self-reported benchmark (vendor)
28. https://pypi.org/pypi/{name}/json for poodle, mutatest, MutPy, and mutahunter – versions, release dates, and classifiers
29. https://coverage.readthedocs.io/en/7.16.2/messages.html#warning-no-sysmon-context – coverage.py's warning that the sysmon core does not support dynamic contexts
30. https://pitest.org/quickstart/maven/ and https://github.com/STAMP-project/pitest-descartes – PIT options and Descartes usage; versions from https://repo1.maven.org/maven2/org/pitest/pitest/maven-metadata.xml and https://repo1.maven.org/maven2/eu/stamp-project/descartes/maven-metadata.xml
31. https://stryker-mutator.io/docs/stryker-js/incremental/ and https://stryker-mutator.io/docs/stryker-net/configuration/ – StrykerJS incremental mode and Stryker.NET `--since`; version from https://registry.npmjs.org/@stryker-mutator/core
32. https://github.com/go-gremlins/gremlins – gremlins (Go) README and `unleash --diff`
33. https://github.com/mbj/mutant – mutant README, licensing, and incremental mode (`--since`)
34. https://infection.github.io/guide/command-line-options.html – Infection command-line options
35. https://github.com/mull-project/mull – Mull README
36. https://github.com/python-humanize/humanize – the research runs' case-study library, at commit 392aef7
