# Coverage and test adequacy

This page covers how to measure coverage so that the numbers can be trusted, what coverage can and cannot show, and how to find untested risky code and weak oracles (an oracle is the check that decides whether a test passes). Load it in phase 7 when tests seem to execute code without checking it or risky code seems untested, and before any per-test coverage run. Treat coverage as a negative signal: uncovered code is untested, but covered code is not known to be tested, so `coverage` evidence supports claims about what ran and nothing more. coverage.py measures with one of three cores: `ctrace` (the C tracer), `sysmon` (Python's `sys.monitoring`, the default on CPython 3.14 and later) and `pytrace` (a slow pure-Python fallback). Mutation testing is in [mutation-testing.md](mutation-testing.md), and acting on overlap between tests is in [redundancy.md](redundancy.md).

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Oracles that cannot fail, or no oracle | `static_scan.py` (`tautology`, `assert-in-except`, `no-assertion`); ruff `B015`, `B018` (M7) | Any instance; oracles that cannot fail are trust breakers; over 5% of tests is systemic (heuristic) | Add value assertions; never delete the test | Assertion count tracks mutation score, τ 0.78–0.97 with size controlled [36] |
| Untested hotspots | Churn × bug-fix commits × complexity × uncovered share (M6) | Top decile; or 2+ fix commits in 12 months and 30%+ uncovered (heuristic) | Behaviour tests for the top ten; mutation testing where coverage is dense | Relative churn found fault-prone binaries with 89% accuracy [40] |
| Timing taken from coverage runs | `--cov` in `addopts`; a `.coverage` file in a run folder; continuous integration (CI) durations from the coverage job | Any speed claim that rests on them | `--no-cov` in every timing run | Coverage moved the duration ratio of two tests from 1.69 to 4.46 [51] |
| Broken measurement | Health check (M2); shard file count; warnings in logs | A process-only module at 0%, a lost shard, `pytrace`, per-test coverage on `sysmon` | `patch = ["subprocess"]`, `[paths]`, `COVERAGE_CORE=ctrace` | Process-only module 0% → 92% [52]; `pytrace` about 10.8 times the run time [51] |
| Configuration distorts the number | Tracked against measured files; honest report (M3) | A production module missing, tests in the total, excluded lines over 2% (heuristic) | `source_dirs`, a separate test-code report, `exclude_also` | One lab run read 78%, 42% or 40% by source setting [52] |
| Weak or mock-only oracles | `rg` patterns (M7) | Over 10% of a directory, or a hotspot guarded only by weak tests (heuristic) | Exact values, `assert_called_once_with`, state checks | Suboptimal asserts in 70.6% of 248 Python projects [37] |
| Broad or swallowed exceptions | ruff `PT011`, `PT012`, `PT017`, `B017`, `BLE001`, `S110` | Any in tests | Specific type with `match=` or `check=` | Exception handling inside tests in 64.9% of Python projects [37] |
| Uncovered error handling | Handler finder (M5) | Any in a hotspot; over half of a package's handlers (heuristic) | Fault injection plus specific assertions | About 15% of real faults escape every coverage criterion [32] |
| No patch-coverage gate (coverage of changed lines) | CI configuration lacks `diff-cover` or a patch status | Only a global `fail_under` | Gate changed lines at 90% (M8) | Patch and overall coverage uncorrelated, τ −0.01 [39] |
| Coverage used as a target | Threshold and pragma history (M3); oracle trends (M7) | Threshold raised while pragmas or tests without oracles grow | Gate changed lines and oracles; keep a floor | Size-controlled correlation low to moderate [28] |
| Coverage flapping | Two runs, compare executed lines (M10) | Any line covered in one run only | Hand to flakiness.md | One line flipped 128 times [39] |
| Dead or untested code | 0% functions, vulture, references | 0% code with no references and no runtime use | Review for deletion before writing tests | Meta deleted over 100 million lines [47] |

## Signals

### Oracles that cannot fail, or no oracle

- **Detect:** Phase 4's `static_scan.py` reports `tautology`, `self-comparison`, `assert-in-except`, `unreachable-assert` and `no-assertion` (no `assert`, `pytest.raises` or `warns`, `assert*` call, mock assertion, snapshot comparison, or call to a helper whose name starts with `assert`, `check`, `verify` or `expect`). Add ruff `B015` (a bare comparison: the forgotten `assert`) and `B018` (a useless expression) from M7. A test that returns a value, such as `return result == expected`, passes with only a `PytestReturnNotNoneWarning`: pytest 8.4.0 failed such tests, but 8.4.1 restored the warning [15], and 9.1.1 still passes them [52]. Search the baseline log for that warning. Oracles that cannot fail are trust breakers with `static` evidence; tests without an oracle are `adequacy` findings.
- **False positives:** Deliberate smoke tests; oracles in fixtures, finalizers or helpers with other names; benchmarks. `static_scan.py` already skips `@given` tests and skipped tests. `self-comparison` can be a deliberate test of a custom `__eq__`. Read two examples of each check before you report it.
- **Fix:** Add assertions on return values, persisted state and emitted events. Replace `try`/`except`/`assert` with `pytest.raises`, and `return a == b` with `assert a == b`. Where the smoke intent is real, name it and assert one meaningful property, such as a status code. To make the return mistake fail, add `-W error::pytest.PytestReturnNotNoneWarning` [52]. Never delete a test without an oracle: suites with every assertion removed still detected 54% of the mutants that the originals caught, mostly through crashes [35].
- **Effect:** With suite size controlled, assertion count correlated with mutation score at Kendall τ 0.78–0.97 across five Java projects [36]. In 248 Python projects, 81.5% had at least one test without an assertion [37].
- **Verify:** Mutants in the covered code survive before the change and die after it. Run them in a disposable copy ([mutation-testing.md](mutation-testing.md)). `static_scan.py diff` shows more assertions and no removed tests.

### Untested hotspots

- **Detect:** A hotspot is code that changes often, has bug-fix history and is complex. Rank functions by churn × bug-fix commits × complexity × uncovered share (M6). Report functions in the top decile, and any function with two or more bug-fix commits in 12 months and at least 30% of its statements and branches uncovered (heuristic). Cite `coverage` and `history` evidence; [findings.md](findings.md) rates untested code in the top decile of churn × complexity as high impact.
- **False positives:** Mass reformatting inflates churn, so discount commits that touch hundreds of files. The bug-fix regex misses teams that cite issue IDs instead of words, so ask how the team marks fixes. Another CI job, such as integration tests, may cover the code, so combine all jobs first (M9).
- **Fix:** For the top ten functions, write behaviour tests that reach the missing lines and branches and assert on outputs, errors and side effects ([generating-tests.md](generating-tests.md)). Where coverage is already dense, run mutation testing on those functions instead ([mutation-testing.md](mutation-testing.md)). Deliver a short ranked list of concrete tests, not a dashboard: a bug-prediction list deployed at Google changed no developer behaviour [41], while ranked, reviewable coverage comments did [43].
- **Effect:** Relative code churn separated fault-prone binaries in Windows Server 2003 with 89.0% accuracy [40]. At Google, positively rated ranked coverage comments were followed by better coverage more than 50% of the time, against an 8% baseline [43]. Vendor data: hotspots were 1.2% of one codebase and held 45% of its bugs [45].
- **Verify:** The targeted mutation score on the ranked functions rises, patch coverage of the new tests is high, and the new tests pass repeatedly.

### Timing taken from coverage runs

- **Detect:** Search for `--cov` in `addopts` and tox commands (`grep -n -- '--cov' pyproject.toml pytest.ini setup.cfg tox.ini`), in `PYTEST_ADDOPTS`, and in the CI job that writes duration files or slowest-test lists. `run_suite.py` detects coverage only in the command line and `PYTEST_ADDOPTS`: with `--cov` in `addopts`, it recorded `instrumented: none` for a covered run [52]. A `.coverage` file in a run folder proves that coverage ran, because `run_suite.py` points `COVERAGE_FILE` there: `find AUDIT/runs -maxdepth 2 -name '.coverage*'`. Also note tests that fail or time out only in the coverage job.
- **False positives:** On Python 3.14 with `sysmon` and no contexts, the overhead can be small (+6% in the lab [51]). The slowdown is still uneven, so rankings still shift.
- **Fix:** Add `--no-cov` to every timing run, or pass `--instrumented coverage` to `run_suite.py` for a run that must keep coverage. Recommend that CI take durations from a job without coverage. Reproduce a coverage-only failure without coverage before you call it a product bug. A longer timeout in the coverage job alone loses no protection, because the uninstrumented job keeps the original. To size the coverage job's cost, compare medians of three `--no-cov` runs with three coverage runs per core, and report it as a `ci` finding, because `findings.py` rejects `speed` findings that cite instrumented runs.
- **Effect:** In the lab, branch coverage on `ctrace` slowed a pure-Python test 3.0 times and a regex-and-JSON test 1.14 times, so their duration ratio moved from 1.69 to 4.46 [51]. With the older cores, SlipCover's authors measured a median coverage.py overhead of 180% on CPython [26]. At Google, instrumentation slowdowns (timeouts, out-of-memory errors) and the flakiness they caused were the leading reasons that coverage runs failed [42].
- **Verify:** Every speed finding cites a run whose manifest says `instrumented: none` and whose folder holds no `.coverage` file.

### Broken measurement

- **Detect:** Run the health check (M2). Code that tests start as processes, such as command-line tools, workers and `multiprocessing` code, reads 0% when child processes are not measured. Before combining, count the `.coverage.*` files against the shards. Search the logs for the warnings `no-ctracer` and `no-sysmon-context`, and for the error "Can't combine statement coverage data with branch data" [52]. A file listed under two machines' paths means a missing `[paths]` mapping. Per-test coverage must come from `ctrace` ([traps.md](traps.md) explains why).
- **False positives:** `pytrace` is expected where coverage ships no wheel, including Python pre-releases, and coverage then suppresses `no-ctracer` [1]. A module at 0% may be dead code rather than unmeasured.
- **Fix:** Subprocesses: `[run] patch = ["subprocess"]` with `parallel = true` (coverage 7.10 and later). pytest-cov 7.0 removed its subprocess hook, so nothing else starts coverage in child processes [11]. Add `"_exit"` when children end with `os._exit()`, `"execv"` for exec chains and `"fork"` for forks; for `multiprocessing`, set `concurrency = ["multiprocessing"]` and `sigterm = true`, and close and join pools [9]. Shards: see M9. Tracer: install a platform wheel so that the C extension loads. Per-test coverage: `COVERAGE_CORE=ctrace`, or `[run] core = "ctrace"` (coverage 7.9 and later).
- **Effect:** A command-line interface (CLI) tested only through a subprocess went from 0% to 92% with the patch [52]. `pytrace` took about 10.8 times the uncovered run time, against 1.56 times for `ctrace` [51]. On `sysmon`, per-test contexts lose data: silently before coverage 7.15.3, and with a `no-sysmon-context` warning since [1] [13].
- **Verify:** Rerun, then check the core decision, the file list, the subprocess modules and the number of combined files.

### Configuration distorts the number

- **Detect:** Read the coverage settings and compare measured files with tracked source files (M3). With no `source`, `source_pkgs` or `source_dirs`, never-imported modules vanish and test files count in the total. `source_pkgs` naming a package that no test imports leaves one `module-not-imported` warning and no entry. `omit` may cover production packages. `exclude_lines` replaces the default exclusions, so it often stands where `exclude_also` was meant. Broad exclusion regexes, such as `except` or `raise`, hide error paths. `# pragma: no cover` on a line that opens a block (`except`, `else`, `def`, a decorator) excludes the whole block [8]. Report with `config` and `coverage` evidence when a production module is missing, `omit` covers production code, tests exceed 20% of the statements in the total, or excluded lines exceed 2% of statements (heuristic).
- **False positives:** Generated code, migrations, vendored code and `__main__` shims are often omitted on purpose. Legitimate exclusions include `if TYPE_CHECKING:` and `...` bodies (defaults since coverage 7.10 [1]), `raise NotImplementedError`, abstract methods, and the version and platform pragmas that covdefaults adds [25]. A missing module may run only in a subprocess (previous signal).
- **Fix:** Measure with `source_dirs = ["src"]` (coverage 7.8 and later; it stops with a clear error on a missing directory) or `--cov=src`. Move `exclude_lines` entries to `exclude_also`, require a reason next to each pragma, and list omissions explicitly. Measure test code too (`--cov=TEST_ROOTS`), but report it on its own with `--include='TEST_ROOTS/*'`: an uncovered line inside a `def test_` body is a test that never ran, which confirms `static_scan.py`'s `shadowed-test` and `not-collected` candidates at runtime [27]. [redundancy.md](redundancy.md) covers what to do with them. The honest number is usually lower, so warn the team before a gate uses it.
- **Effect:** One lab run of the same tests read 78% with no source setting (test files counted, three production modules missing), 42% with `source_pkgs` (one never-imported package absent), and 40% with `source_dirs` [52]. One pragma on `except ValueError:` hid two lines and moved a file from 97% to 95% [51]. The total is (covered lines + covered branches) ÷ (statements + branches) [10], so turning on branch coverage changes the number without any change in the tests. Never compare a branch number with a line-only history.
- **Verify:** The measured file list equals the tracked list, and the honest and normal numbers (M3) differ by a small, documented amount.

### Weak or mock-only oracles

- **Detect:** Run the weak-oracle search (M7): bare truthiness (`assert result`), `is not None`, `len(x) > 0`, `isinstance`, bare `assert_called()` or `assert_called_once()`, and unittest's `assertTrue(name)`, `assertIsNotNone` and `assertIsInstance`. `static_scan.py` counts every `assert` statement and mock assertion as an oracle, so its `no-assertion` check misses these. Its `weak-assertions` check lists the narrowest case with few false positives: tests that end on an assertion and check only that results exist (`is not None`, `hasattr`, `len(x) > 0`, `assertIsNotNone`). It skips `isinstance` and bare truthiness, which are often the behaviour under test, so the search (M7) and the per-test `strong_asserts` count still give the wider, noisier candidate list. A test is weak-only when all of its oracles match. Report when weak-only or mock-only tests exceed 10% of a directory, or when a hotspot is guarded only by weak tests (heuristic).
- **False positives:** A weak check followed by a strong one is fine. `isinstance` is right when the type is the contract. A mock-call assertion is the right oracle when the interaction is the behaviour, such as sending an email, if it checks the arguments.
- **Fix:** Assert exact values or structures, check call arguments with `assert_called_once_with(...)`, and assert on observable state rather than internal calls. Consider a property-based test for invariants. Large snapshots that change with every commit are weak oracles too ([techniques.md](techniques.md)).
- **Effect:** `assertNull` and `assertNotNull` were the least effective assertion methods in five Java projects [36]. PyNose found suboptimal asserts in 70.6% of 248 Python projects [37]. A test that never checks its result reached 83% statement coverage with 0% checked coverage [35].
- **Verify:** A mutant that changes a returned value, such as an off-by-one or a wrong field, now fails a test.

### Broad or swallowed exceptions

- **Detect:** The ruff run in M7 lists `PT011` (`pytest.raises` on a broad type without `match=`), `PT012` (several statements inside `raises`), `PT017` (an assert inside `except`), `B017` (asserting a blind `Exception`), and `BLE001` and `S110` (broad and silent handlers). `S110` ignores `except SpecificError: pass`, so also read the `try` blocks in tests that `static_scan.py` lists under `no-assertion`. Report every instance in tests.
- **False positives:** A contract that really is "raises some error"; `try`/`finally` for cleanup; a retry wrapper whose swallowing is the behaviour under test.
- **Fix:** Name the specific exception with `match=` (a regex on the message) or `check=` (a predicate; pytest 8.4 and later [15]), keep one statement inside `raises`, and replace `try`/`except`/`assert` with `pytest.raises`.
- **Effect:** No quantitative study exists. The mechanism is direct: `pytest.raises(Exception)` also passes on a `TypeError` from a wrong call, so the test cannot fail for the reason it was written. PyNose found exception handling inside tests in 64.9% of Python projects [37].
- **Verify:** Make the code under test raise a different type or message; the test now fails.

### Uncovered error handling

- **Detect:** With branch coverage on, list every `except` clause and `raise` that no test ran (M5). In the text report, `29->31` is a branch never taken, and `13->exit` is a path out of the function from line 13 that was never taken [6] [52]. Report any uncovered handler inside a hotspot, and packages where more than half of the `raise` and `except` lines are uncovered (heuristic).
- **False positives:** Defensive handlers for impossible states, platform-specific errors, and re-raise wrappers that only add context. These may justify a commented pragma rather than a test.
- **Fix:** Inject the fault at the boundary: `mock.patch.object(client, "send", side_effect=TimeoutError)`, `monkeypatch.setattr`, or a fake that raises. Then assert the specific outcome: `pytest.raises(PaymentError, match="declined")`, the log record (`caplog`), the fallback value, or the retry count. A test that only checks that no exception escaped has a weak oracle.
- **Effect:** No study isolates error-path tests. In five projects, about 15% of real faults escaped every control-flow and data-flow criterion, mostly missing logic (abstract only) [32], which argues for behavioural checks on these paths.
- **Verify:** A mutant that empties the handler body or changes the exception type now fails a test.

### No patch-coverage gate

- **Detect:** Search the CI configuration for `diff-cover`, `diff-quality`, Codecov's `coverage.status.patch` or an equivalent. A global `fail_under` alone is the finding, with `config` evidence. If a gate exists, judge it instead: the median patch coverage of merged changes, how often it blocks, and whether pragmas grow. Take that history from Codecov, Coveralls or CI artifacts.
- **False positives:** Moved code reads as new lines. Generated code and configuration changes. Lines that run only in subprocesses or other shards read as uncovered until the measurement is fixed.
- **Fix:** Gate patch coverage with diff-cover (M8), or with Codecov's patch status: set `target` and `threshold`, and `codecov.notify.after_n_builds` for sharded uploads [21]. Run it as informational for two weeks, then enforce it (heuristic). Keep the global threshold only as a floor.
- **Effect:** Across 7,816 builds of 47 projects, patch coverage did not correlate with overall coverage (Kendall τ −0.01), and every project had changes where the covered set changed but the percentage did not [39]. Google's voluntary levels pair 60%, 75% and 90% project coverage with 70%, 80% and 90% changelist coverage [42]. Its testing blog calls 90% per commit a good floor and 99% a reasonable goal (quoted in search results; page not read) [44].
- **Verify:** After a month, compare the median patch coverage, the number of blocked changes and the pragma count.

### Coverage used as a target

- **Detect:** Read the threshold and pragma history (M3) and the trend in tests without an oracle and weak-only tests (M7). Report pragmas added in the same commit as a threshold increase, and tests whose names mention coverage (`rg -n 'def test_.*cover' TEST_ROOTS`).
- **False positives:** A 100% policy can be healthy in a small library that pairs it with strong oracles and mutation testing. Judge the oracles and mutation results, not the policy.
- **Fix:** Move enforcement to changed lines and oracle quality, keep the global threshold as a floor that only rises, and report the honest number next to the gated one. Never recommend a higher global threshold as a quality fix: it adds cost without adding detection.
- **Effect:** With suite size held constant, correlation between coverage and mutant detection was usually low to moderate across 31,000 suites [28]. Correlations from random pseudo-suites run 0.21–0.39 Kendall points higher than from real suites (abstract only) [33]. Raising coverage takes disproportionate effort, with an optimum "well short of 100%" (Mockus et al., as summarised in [43] and [39]). Tests generated by large language models (LLMs) reached coverage while detecting almost no faults (preprint) [38].
- **Verify:** Mutation score and assertion density on changed code rise, and the pragma count does not. `static_scan.py diff` cannot see pragmas or coverage thresholds, so recheck them with M3's history commands.

### Coverage flapping

- **Detect:** Run one commit twice with the same settings and compare executed lines per file (M10). A line covered in only one run points to nondeterminism: timing, order, randomness, network or threads.
- **False positives:** Random ordering and property-based tests change paths by design. Fix the order (`-p no:randomly`) and seeds (`--hypothesis-seed=0` where Hypothesis is installed) first.
- **Fix:** Hand the tests that reach the flapping lines to [flakiness.md](flakiness.md), seed randomness, and replace sleeps with explicit synchronisation. Treat a small coverage drop on one pull request as possible noise.
- **Effect:** In 47 projects, lines flipped between covered and uncovered, one of them 128 times, often in health checks, scheduled jobs and network-state checks [39].
- **Verify:** Two consecutive runs give identical executed-line sets.

### Dead or untested code

- **Detect:** Take functions at 0% from the JSON report (M5). Then run `uvx vulture SRC --sort-by-size`, search for references (`rg -n '\bNAME\b'`), and check entry points (`[project.scripts]`, URL routes, task and plugin registries) and runtime evidence (logs, traces, feature flags). vulture rates unused functions, classes and attributes at 60% confidence, so `--min-confidence 80` hides them [52]; 80 keeps only unused imports (90%), unused arguments and unreachable code (100%) [17]. Referenced, reachable code is untested; unreferenced code with no runtime use is dead.
- **False positives:** Dynamic use (`getattr`, decorators, framework discovery, task queues, pytest hooks), library functions that other repositories call, and seasonal or feature-flagged code. A function that only tests call looks unused when vulture scans `SRC` alone, which can itself mean that it is dead in production.
- **Fix:** Propose deleting dead code as a review candidate in its own change, citing both the coverage and the reference evidence. Record confirmed dynamic uses in a vulture whitelist (`--make-whitelist`). Write tests only for live code, in hotspot order.
- **Effect:** Meta's SCARF system deleted more than 100 million lines in more than 370,000 change requests over five years [47].
- **Verify:** After deletion, the suite passes, the coverage denominator shrinks, and staging and production logs show no new errors.

## Measuring

Run every test command through `run_suite.py`, and run the other commands from `ROOT` with the project's Python for `python -m coverage`. `SRC` is the product source directory, `TEST_ROOTS` the test directories, `TEST_DIR` one test directory, and `NN-label` the run folder that `run_suite.py` prints. The inline snippets need Python 3.9 or later. Every block was run on a toy project for this page [52].

### M1. Baseline coverage run

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label coverage --timeout SECONDS --cwd ROOT -- \
    CI_TEST_COMMAND --cov=SRC --cov-branch --cov-report=term-missing:skip-covered \
    --cov-report=json:{RUN_DIR}/coverage.json --cov-report=xml:{RUN_DIR}/coverage.xml
python -m coverage report --data-file=AUDIT/runs/NN-coverage/.coverage --sort=-miss --show-missing --skip-covered
```

- A directory in `--cov=`, like `source_dirs`, also reports files that no test imports [52].
- The data file lands in the run folder, because `run_suite.py` sets `COVERAGE_FILE`, which overrides the project's `data_file` setting. pytest-cov deletes `.coverage*` files in that folder when it starts, unless you pass `--cov-append`, so never point `COVERAGE_FILE` at harvested CI data [52].
- `Missing` lists lines (`24-25`), branches never taken (`29->31`) and exits never taken (`13->exit`); `BrPart` counts partly taken branches [6]. `--format=total` prints only the number, `--format=markdown` prints a table, and `--fail-under` exits with status 2. Say whether you report a branch or a line-only number.
- Cost: one full run, +6% (`sysmon`, Python 3.14) to +120% (branch coverage on `ctrace`) in the lab [51]. The manifest marks the run `instrumented: coverage`, so it never backs a timing claim.

### M2. Measurement health check

```sh
python -m coverage debug sys | grep -E 'coverage_version|core:|CTracer'
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label core-check --timeout 600 --cwd ROOT \
    --env COVERAGE_DEBUG=core --env COVERAGE_DEBUG_FILE=AUDIT/coverage-debug.txt -- \
    CI_TEST_COMMAND --cov=SRC --cov-report= TEST_DIR
grep 'Using core' AUDIT/coverage-debug.txt | sort | uniq -c
grep -o -E '\((no-ctracer|no-sysmon-context|module-not-imported|module-not-measured|no-data-collected|couldnt-parse)\)' \
    AUDIT/runs/NN-coverage/output.log | sort | uniq -c
```

- `CTracer: available from …` means that the C extension loads. The `core:` line reads `-none-` outside a run, so read the decision from the debug file. pytest-cov hides coverage's debug output from the console; `COVERAGE_DEBUG_FILE` collects it from every process, including xdist workers [52].
- Typical decisions: `Using sysmon because SYSMON_DEFAULT is set` (CPython 3.14 and later), `Defaulting to ctrace core` (older Pythons, or coverage's own `dynamic_context`), and `Falling back to pytrace because C tracer not available` [52].
- If tests start product code as a process and it reads 0%, measure it with an audit-only rc file that repeats the project's coverage settings and adds `patch = subprocess` and `parallel = True`. Pass it with `--cov-config=AUDIT/audit.coveragerc` (verified: 0% → 92% [52]). Never edit the project's configuration during the audit.
- Cost: seconds for `debug sys`, and one short run for the core check.

### M3. Configuration audit and the honest number

```sh
grep -H -n -E 'source|omit|include|exclude_lines|exclude_also|branch|fail_under|core|patch|parallel|relative_files|timid|plugins' \
    pyproject.toml setup.cfg tox.ini .coveragerc .coveragerc.toml 2>/dev/null
git ls-files 'SRC/*.py' | sort > AUDIT/tracked.txt
python3 -c "import json, sys; print(*sorted(json.load(open(sys.argv[1]))['files']), sep='\n')" \
    AUDIT/runs/NN-coverage/coverage.json > AUDIT/measured.txt
comm -23 AUDIT/tracked.txt AUDIT/measured.txt                    # tracked source files the report never lists
python -m coverage debug data AUDIT/runs/NN-coverage/.coverage | head -5    # relative or absolute paths?
printf '[run]\nrelative_files = True\n[report]\nexclude_lines =\n    a^\n' > AUDIT/honest.coveragerc
python -m coverage report --data-file=AUDIT/runs/NN-coverage/.coverage --rcfile=AUDIT/honest.coveragerc --include='SRC/*' --format=total
python -m coverage report --data-file=AUDIT/runs/NN-coverage/.coverage --include='SRC/*' --format=total
git log -G'fail_under' --format='%h %ad %s' --date=short -- pyproject.toml setup.cfg .coveragerc tox.ini
git log -S'pragma: no cover' --format='%h %ad %an %s' --date=short -- SRC | head -20
```

- `exclude_lines` replaces every default, including `# pragma: no cover`, and the regex `a^` never matches, so the honest report also counts excluded code [8].
- Keep `relative_files = True` in the honest file only when `debug data` lists relative paths. A mismatch in either direction reports every file at 0% with exit status 0 [52].
- In `--include` and `--omit`, a trailing `/*` matches everything below a directory, but a `*` elsewhere does not cross `/`: `src/*pricing*` matched nothing [52].
- Excluded share: `python3 -c "import json, sys; j = json.load(open(sys.argv[1])); x = sum(f['summary']['excluded_lines'] for f in j['files'].values()); s = j['totals']['num_statements']; print(x, s, f'{100 * x / (x + s):.1f}% excluded')" AUDIT/runs/NN-coverage/coverage.json`.
- Cost: seconds. Every command reuses existing data.

### M4. Per-test coverage for coverage_redundancy.py

Record one directory at a time, on the C tracer:

```sh
grep '^TEST_DIR/' AUDIT/nodeids.txt > AUDIT/nodeids-DIR.txt
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label ctx-DIR --timeout SECONDS --cwd ROOT \
    --env COVERAGE_CORE=ctrace -- CI_TEST_COMMAND --cov=SRC --cov-report= --cov-context=test TEST_DIR
grep -c no-sysmon-context AUDIT/runs/NN-ctx-DIR/output.log         # expect 0
python3 ${CLAUDE_SKILL_DIR}/scripts/coverage_redundancy.py AUDIT/runs/NN-ctx-DIR/.coverage \
    --nodeids AUDIT/nodeids-DIR.txt --json-out AUDIT/results/redundancy-DIR.json
```

- Set `COVERAGE_CORE=ctrace` on every Python version ([traps.md](traps.md)). `coverage_redundancy.py` refuses data in which no line has two tests. Under xdist, though, each worker records a line once, so `sysmon` data from `-n 2` passed that check with 11 of 17 tests recorded [52]. Confirm `COVERAGE_CORE` in the manifest's `env`, and compare the script's "tests with contexts" with the size of the selection.
- pytest-cov 7.1.0 does not choose `ctrace` for `--cov-context=test` by itself [13] [52]. coverage's own `dynamic_context = "test_function"` does, but it names contexts `module.Class.test`, merges parametrised cases, and has failed under xdist [14]. Prefer `--cov-context=test`.
- Contexts are named `<node ID>|setup`, `|run` and `|teardown`, with parametrisation IDs [12]. A phase appears only if measured code ran during it. Import-time code (module-level, `def` and `class` lines) goes to the empty context `""`, and so does code that runs in a child process, so a test that drives a CLI through a subprocess shows under `no-product` [52]. Session and module fixture code goes only to the `|setup` context of the first test that requested it [52], so it depends on test order. For these reasons, `coverage_redundancy.py` compares only `|run` contexts and skips test files.
- Line mode is cheaper: on 1,000 synthetic tests, branch mode with contexts stored 350,201 arc rows (12.8 MB), against 1,001 line rows (0.4 MB) [51]. If the project turns on `branch`, an audit-only rc file with `branch = False` and `core = ctrace` records lines [52]. It replaces the project's coverage settings, so copy its `source` and `omit` lines into it.
- Storage: `.coverage` is an SQLite database, schema version 7 [3]. `meta(key, value)` holds `version` and `has_arcs`; `file(id, path)` and `context(id, context)` name files and contexts. Line mode writes `line_bits(file_id, context_id, numbits)`: one row per file and context, with the executed lines as one bitmap. Branch mode writes `arc(file_id, context_id, fromno, tono)`, where negative numbers mark entry and exit. The schema can change without a major version [3], so query through the API [4]:

```python
import re
from coverage import CoverageData

data = CoverageData("AUDIT/runs/NN-ctx-DIR/.coverage")
data.read()
path = next(p for p in data.measured_files() if p.endswith("pkg/module.py"))
by_line = data.contexts_by_lineno(path)                   # {line: [context, ...]}
data.set_query_contexts([re.escape("tests/test_x.py::test_y[a-1]|run")])
print(sorted(data.lines(path)))                           # the lines that one test ran
```

- Escape node IDs: `[` opens a character class (`ConfigError: … bad character range`), and `|` means "or", so an unescaped `test_heavy|run` matched 22 lines instead of 6 [52]. The same applies to `coverage report --contexts=`. For large files, `coverage.numbits.register_sqlite_functions(con)` adds `num_in_numbits` and related functions to plain `sqlite3` queries [5].
- Cost: one run per directory, with roughly double the coverage overhead. Contexts add about 1.5–2.5 ms per test, which multiplied the overhead two to five times on many short tests [51]. Combine many context-heavy files only with coverage 7.10.6 or later [1].

### M5. Uncovered handlers and functions at 0%

```sh
python3 - AUDIT/runs/NN-coverage/coverage.json <<'PY'
import ast, json, sys
for name, f in sorted(json.load(open(sys.argv[1]))["files"].items()):
    missing = set(f["missing_lines"])
    for node in ast.walk(ast.parse(open(name, encoding="utf-8").read())) if missing else []:
        if isinstance(node, ast.ExceptHandler) and node.body[0].lineno in missing:
            print(f"{name}:{node.lineno}: uncovered handler: except {ast.unparse(node.type) if node.type else ''}")
        elif isinstance(node, ast.Raise) and node.lineno in missing:
            print(f"{name}:{node.lineno}: uncovered raise: {ast.unparse(node)[:60]}")
    for fn_name, fn in f.get("functions", {}).items():
        if fn_name and fn["summary"]["num_statements"] and not fn["summary"]["covered_lines"]:
            print(f"{name}:{fn.get('start_line', '?')}: function at 0%: {fn_name}")
PY
```

- It prints each `except` clause whose first statement never ran, each `raise` that never ran, and each function at 0%. Per-function regions need coverage 7.6, and `start_line` needs 7.13.1 [1] [7].
- Many missing lines in one function usually mean an untested feature; one missing line in many functions usually means untested error paths.
- Cost: seconds, with no test run. Use the project's Python when its syntax is newer than `python3`'s.

### M6. Hotspot ranking

Run from `ROOT`, or from a sub-project root in a monorepo: the snippet passes `--relative`, so git paths match coverage paths. First check which commits the bug-fix regex matches, and ask the team if it misses their convention.

```sh
git log --since=12.months --no-merges -i -E --grep='(^|[^a-z])(fix(e[sd])?|bug|defect|regression|hotfix)([^a-z]|$)' --format='%h %s' | head -20
uvx ruff check --isolated --no-cache --exit-zero --select C901 --config 'lint.mccabe.max-complexity = 0' \
    --output-format json SRC > AUDIT/complexity.json
python3 - AUDIT/runs/NN-coverage/coverage.json AUDIT/complexity.json <<'PY'
import json, math, os, re, subprocess, sys
from collections import Counter
FIX = r"(^|[^a-z])(fix(e[sd])?|bug|defect|regression|hotfix)([^a-z]|$)"
def log(*args):
    cmd = ["git", "log", "--since=12.months", "--no-merges", "--no-renames", "--relative", "--format=", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines()
churn, fixes = Counter(), Counter(p for p in log("-i", "-E", "--grep=" + FIX, "--name-only") if p)
for line in log("--numstat"):
    added, deleted, path = (line.split("\t") + ["", ""])[:3]
    if added.isdigit() and deleted.isdigit():
        churn[path] += int(added) + int(deleted)
rel = lambda p: os.path.relpath(p) if os.path.isabs(p) else p
ccn = {(rel(r["filename"]), r["location"]["row"]): int(re.search(r"\((\d+) >", r["message"])[1])
       for r in json.load(open(sys.argv[2]))}
rows = []
for path, f in json.load(open(sys.argv[1]))["files"].items():
    path = rel(path)
    for name, fn in f.get("functions", {}).items():
        s = fn["summary"]
        miss, units = s["missing_lines"] + s.get("missing_branches", 0), s["num_statements"] + s.get("num_branches", 0)
        if name and miss:
            c = next((v for (p, n), v in ccn.items() if p == path and abs(n - fn.get("start_line", -9)) <= 2), 1)
            score = (math.log1p(churn[path]) + 1) * (fixes[path] + 1) * c * miss / units
            rows.append((round(score, 1), c, churn[path], fixes[path], miss, f"{path}::{name}", fn["missing_lines"][:6]))
print("score  complexity  churn  fixes  missing  function  missing lines")
for row in sorted(rows, reverse=True)[:30]:
    print(*row, sep="  ")
PY
```

- Score: (ln(1 + file churn) + 1) × (bug-fix commits + 1) × complexity × uncovered share, where the uncovered share is (missing statements + missing branches) ÷ (statements + branches). This is a heuristic: the evidence supports each factor separately [40] [45] [43], not this product.
- ruff with `max-complexity = 0` reports the McCabe complexity of every function; for the lab's `discount` function it gave 5, the same as lizard [51] [52]. Without `start_line` (coverage before 7.13.1), every function gets complexity 1. For other languages, use `uvx lizard --csv SRC`, which writes no header row (NLOC, CCN, tokens, parameters, length, location, file, function, long name, start, end) [18].
- `--no-renames` keeps rename lines out of the churn counts, and the anchored regex keeps words such as "prefix" out of the fix counts [52].
- Cost: seconds to minutes, with no test run once `coverage.json` exists.

### M7. Oracle audit

Phase 4 already produced `AUDIT/static.json`. Its ruff run uses `--statistics`, which prints counts per rule but no locations, so rerun the oracle rules for file and line evidence:

```sh
uvx ruff check --isolated --no-cache --select PT011,PT012,PT017,B015,B017,B018,BLE001,S110 --output-format concise TEST_ROOTS
rg -n --type py -e '^\s*assert\s+[\w.]+\s*$' -e 'assert .+ is not None\s*$' -e 'assert len\(.+\)\s*(>|>=|!=)\s*[01]\b' \
    -e '^\s*assert isinstance\(' -e '\.assert_called(_once)?\(\)' -e 'self\.assertTrue\([\w.]+\)' \
    -e 'self\.assert(IsNotNone|IsInstance)\(' TEST_ROOTS
python3 - AUDIT/static.json <<'PY'
import json, sys
from collections import defaultdict
by_dir = defaultdict(list)
for test_id, t in json.load(open(sys.argv[1]))["tests"].items():
    by_dir[test_id.split("::")[0].rpartition("/")[0]].append(t)
for d, ts in sorted(by_dir.items(), key=lambda kv: sum(t["assertions"] for t in kv[1]) / len(kv[1])):
    a = [t["assertions"] for t in ts]
    weak = sum(1 for t in ts if t["assertions"] and not t.get("strong_asserts"))
    print(f"{sum(a) / len(a):5.2f} oracles per test  {a.count(0):4d} with none  {weak:4d} without a strong assert  {len(ts):5d} tests  {d}")
PY
```

- Each `rg` line is a candidate. A test is weak-only when all of its oracles match, so read the test before you count it. On the lab suite, the patterns found all four planted weak oracles [52].
- `strong_asserts` in `static.json` counts only plain `assert` statements that check more than existence or type. Tests that rely on `pytest.raises`, unittest `assert*` methods or mock assertions also show "without a strong assert": 4 of the 9 lab tests in that column were fine [52].
- The density table ranks directories by oracles per test. With suite size controlled, assertion count tracks mutation score [36], so the lowest rows are where mutation testing pays off first.
- Cost: seconds for thousands of files, with no test run.

### M8. Patch coverage

```sh
uvx diff-cover AUDIT/runs/NN-coverage/coverage.xml --compare-branch=origin/main --fail-under=90 \
    --format markdown:AUDIT/results/diff-cover.md,json:AUDIT/results/diff-cover.json
```

- Run it from `ROOT`, with the project's default branch. diff-cover compares against the merge base (`origin/main...HEAD`), includes staged and unstaged changes, prints `file (pct): Missing lines …`, and exits with status 1 below `--fail-under` [20] [51]. It reads Cobertura, Clover or JaCoCo XML, or LCOV, and needs the base branch in the clone, so shallow CI clones must fetch it.
- On the default branch itself the diff is empty. To judge an existing gate, read its history from Codecov, Coveralls or CI artifacts. Recomputing patch coverage for past changes needs one coverage run per commit, in a disposable copy.
- Codecov settings: `coverage.status.patch.default.target` (a percentage or `auto`) and `threshold`; with sharded uploads, `codecov.notify.after_n_builds` [21].
- Cost: one coverage run with XML output, then seconds.

### M9. Combining parallel and sharded data

```sh
mkdir -p AUDIT/coverage-ci && cp DOWNLOADED_SHARDS/.coverage.* AUDIT/coverage-ci/
python -m coverage combine --data-file=AUDIT/coverage-ci/.coverage        # deletes the copies once combined
python -m coverage report --data-file=AUDIT/coverage-ci/.coverage --format=markdown
```

- Each shard needs `parallel = true` and `relative_files = true`, and uploads its `.coverage.*` files as an artifact named per matrix cell, with hidden files included (`include-hidden-files: true` in `actions/upload-artifact` 4.4 and later) [24].
- Since coverage 7.14, `report`, `json` and `xml` also combine parallel files implicitly, then delete them unless you pass `--keep-combined` [1] [52]. A `report` after `combine --keep` combined the kept files again and deleted them [52], so combine once, on copies.
- All shards must share the `branch` setting, or combining stops with "Can't combine statement coverage data with branch data" [52]. When shards stored different absolute paths, add a `[paths]` section to an audit rc file, with the local path as the first entry [2].
- Codecov: upload every shard and set `after_n_builds` to the shard count [21]. Coveralls: set `COVERALLS_PARALLEL=true`, then close the build with the parallel webhook [22].
- Cost: seconds to minutes. Before coverage 7.5.3, combining 700+ files could take more than 3 hours [1].

### M10. Coverage flapping

```sh
for n in 1 2; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label flap-$n --timeout SECONDS --cwd ROOT -- \
      CI_TEST_COMMAND -p no:randomly --cov=SRC --cov-report=json:{RUN_DIR}/coverage.json
done
python3 - AUDIT/runs/NN-flap-1/coverage.json AUDIT/runs/NN-flap-2/coverage.json <<'PY'
import json, sys
a, b = (json.load(open(p))["files"] for p in sys.argv[1:3])
for f in sorted(set(a) | set(b)):
    x, y = (set(d.get(f, {}).get("executed_lines", [])) for d in (a, b))
    if x ^ y:
        print(f, "only first:", sorted(x - y)[:10], "only second:", sorted(y - x)[:10])
PY
```

- Cost: two full runs. Any output deserves a follow-up in [flakiness.md](flakiness.md).

## Tools

Versions and dates are from PyPI and release pages, fetched on 2026-09-30. "Lab" means run on Python 3.14.0 with pytest 9.1.1.

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| coverage.py | Line and branch coverage, contexts, reports | 7.16.2, 2026-09-27, maintained; lab | `sysmon` is the default core on CPython 3.14+ and supports no dynamic contexts; `sysmon` measures branches only on 3.14+ [1] |
| pytest-cov | pytest integration, xdist combining, `--cov-context=test` | 7.1.0, 2026-03-21, maintained; lab | No subprocess hook since 7.0 [11]; does not select `ctrace` for contexts (issue 755, open) [13] |
| pytest-xdist | Parallel runs; pytest-cov combines worker data | 3.8.0, 2025-07-01, maintained; lab [23] | Classifiers stop at 3.13, but it worked on 3.14; per-test coverage on `sysmon` under xdist passes `coverage_redundancy.py`'s check [52] |
| diff-cover | Coverage and lint on changed lines | 10.6.0, 2026-09-22, maintained; lab [46] | Needs XML or LCOV input and the merge base in the clone [20] |
| Codecov | Hosted project and patch statuses | Hosted service | Statuses depend on complete uploads (`after_n_builds`) [21] |
| ruff | Oracle, exception and complexity rules | 0.16.9, 2026-09-24, maintained (about weekly); lab | Static only: it cannot see weak oracles [16] |
| lizard | Per-function complexity for 25+ languages | 1.24.0, 2026-08-19, maintained; lab | CSV has no header row; default warning at complexity 15 [18] |
| radon | Complexity and maintainability index | 6.0.1, 2023-03-26, unmaintained | Classifiers stop at Python 3.9; prefer ruff `C901` or lizard [19] |
| vulture | Dead-code candidates | 2.16, 2026-03-25, maintained; lab | Unused functions sit at 60% confidence [17] |
| covdefaults | Opinionated coverage settings plugin | 2.3.0, 2023-03-05, stable with no recent release; lab | Sets `fail_under = 100` and branch coverage, which invites pragmas; does not force `ctrace` [25] |

For JaCoCo, c8, Vitest, Go, coverlet and SimpleCov, see [runners-and-ecosystems.md](runners-and-ecosystems.md). In three of them, a setting silently drops code from the report [50]. Go measures integration binaries only when you build them with `go build -cover` and run them with `GOCOVERDIR` (Go 1.20 and later). coverlet's collector and MSBuild drivers do not work on Microsoft Testing Platform, which needs `coverlet.MTP`. SimpleCov misses every file loaded before `SimpleCov.start`.

## Evidence

- Inozemtseva and Holmes, ICSE 2014: 31,000 suites from five Java programs; with suite size held constant, the coverage–effectiveness correlation was usually low to moderate (Joda Time fell from 0.80–0.85 to about zero), and coverage types correlated with one another at τ 0.91–0.92 [28].
- Gopinath, Jensen and Groce, ICSE 2014: across 729 Maven projects with tests, statement coverage predicted mutation kills best (R² 0.94, τ 0.82 for developer suites), without size control [29].
- Kochhar et al., SANER 2015 and IEEE Transactions on Reliability 2017 (abstracts only): for generated suites, coverage correlated moderately to strongly with detecting 159 real bugs in two projects [30], but in 100 large Java projects its correlation with post-release bugs was insignificant at project level and absent at file level [31].
- Hemmati, QRS 2015 (abstract only): statement coverage guaranteed detection of 10% of faults; about 15% escaped every criterion, mostly missing logic [32].
- Zhang et al., ICST 2019 (abstract only): correlations from random pseudo-suites were 0.21–0.39 Kendall points higher than from the original suites of 123 projects [33].
- Chen et al., ASE 2020: on 231 Defects4J faults, reducing a suite by coverage lost substantial fault detection, while reducing it by mutants kept it [34].
- Schuler and Zeller, STVR 2013: checked coverage was always below statement coverage (XStream 94% against 28%); suites with every assertion removed still found 54% of the mutants [35].
- Zhang and Mesbah, FSE 2015: with suite size controlled, assertion count correlated with mutation score at Kendall 0.781–0.970; with assertion coverage controlled, statement coverage correlated at 0.01–0.63 [36].
- Wang et al. (PyNose), ASE 2021: in 248 Python projects, tests without assertions in 81.5%, suboptimal asserts in 70.6%, exception handling inside tests in 64.9% [37].
- Hamidi et al., 2026 preprint: on more than 6,000 faulty programs written by LLMs, coverage and mutation criteria with generated oracles gave "extremely low, often near zero" fault detection [38].
- Hilton, Bell and Marinov, ASE 2018: 7,816 builds of 47 projects; patch coverage against overall coverage τ −0.01; one line flipped 128 times [39].
- Nagappan and Ball, ICSE 2005 (abstract): relative churn identified fault-prone binaries in Windows Server 2003 with 89.0% accuracy [40].
- Lewis et al., ICSE 2013 (abstract): a bug-prediction list deployed at Google changed no developer behaviour [41].
- Google, FSE 2019: daily coverage for one billion lines, no company-wide threshold, voluntary project and changelist levels of 60/70, 75/80 and 90/90; failed coverage runs came mostly from instrumentation slowdowns and the flakiness they caused [42]. Google's 2020 testing blog (figures quoted in search results) calls 60% acceptable, 75% commendable and 90% exemplary, with 90% per commit a floor and 99% a goal [44].
- Google, ICSE SEIP 2024: hiding coverage in 29,149 changelists left the median coverage change at 0% (baseline above 90%); showing it cut median review time by 5% (active time by 11%); positively rated ranked comments led to better coverage more than 50% of the time, against 8% [43].
- Mockus et al., 2009 (secondary summary in [43] and [39]): raising coverage reduced field defects at Microsoft and Avaya, but the effort grew disproportionately, and the optimum was "well short of 100%".
- CodeScene (vendor) [45]: hotspots at 1.2% of a codebase received 12.5% of development effort and held 45% of bugs; across 39 codebases, low-quality code had 15 times more defects.
- Meta SCARF, 2023: more than 100 million lines deleted in more than 370,000 change requests over five years [47].
- SlipCover, ISSTA 2023: median coverage.py overhead of 180% on CPython and 1,300% on PyPy with the cores that predate `sysmon` [26].
- Python 3.14 alpha community timings (informal): Pillow line coverage about 80 s on `ctrace` against 38 s on `sysmon`; inifix overhead fell from about 275% to about 25% [49].
- PyVista, 2026: dropping `--cov-context=test` cut three test files from 30–35 s to 20 s, with identical totals [48].
- Research lab: 80 compute-bound tests, 2.32 s uncovered; line coverage +56% on `ctrace`, +6% on `sysmon`, +979% on `pytrace`; branch coverage +120% on `ctrace`, +6% on `sysmon`, +133% on `ctrace` with contexts; noisy shared machine, so order of magnitude only [51].
- Verification for this page: 78%, 42% and 40% under three source settings; `sysmon` under `-n 2` kept 11 of 17 tests and passed `coverage_redundancy.py`; the subprocess patch took a CLI from 0% to 92%; a `relative_files` mismatch read 0% with exit status 0; vulture rated unused functions at 60% [52].

## Sources

1. https://coverage.readthedocs.io/en/latest/changes.html – coverage.py changelog: the version of every feature named here.
2. https://coverage.readthedocs.io/en/latest/config.html – coverage.py configuration: `core`, `patch`, `source_dirs`, `[paths]`.
3. https://coverage.readthedocs.io/en/latest/dbschema.html – data file schema, version 7.
4. https://coverage.readthedocs.io/en/latest/api_coveragedata.html and https://raw.githubusercontent.com/coveragepy/coveragepy/main/coverage/sqldata.py – `CoverageData` API and query contexts.
5. https://raw.githubusercontent.com/coveragepy/coveragepy/main/coverage/numbits.py – numbits helpers and SQL functions.
6. https://coverage.readthedocs.io/en/latest/commands/cmd_report.html – report options and missing-branch notation.
7. https://coverage.readthedocs.io/en/latest/commands/cmd_json.html – JSON report format.
8. https://coverage.readthedocs.io/en/latest/excluding.html – default exclusions, `exclude_also`, block exclusion.
9. https://coverage.readthedocs.io/en/latest/subprocess.html – subprocess and `multiprocessing` measurement.
10. https://coverage.readthedocs.io/en/latest/faq.html – how the total percentage is computed.
11. https://pytest-cov.readthedocs.io/en/latest/changelog.html – pytest-cov changelog: 7.0 removed the subprocess hook.
12. https://pytest-cov.readthedocs.io/en/latest/contexts.html – `--cov-context=test` naming.
13. https://github.com/pytest-dev/pytest-cov/issues/755 – contexts on the `sysmon` core.
14. https://github.com/pytest-dev/pytest-cov/issues/604 – `dynamic_context` failure under xdist.
15. https://docs.pytest.org/en/stable/changelog.html – pytest changelog: `raises(check=)` in 8.4.0, the return warning restored in 8.4.1.
16. https://docs.astral.sh/ruff/rules/ – ruff rules `PT`, `B`, `BLE`, `S110`, `F811`, `C901`.
17. https://github.com/jendrikseipp/vulture – vulture confidence levels and options.
18. https://github.com/terryyin/lizard – lizard options and CSV output.
19. https://radon.readthedocs.io/en/latest/commandline.html and https://pypi.org/pypi/radon/json – radon options and release data.
20. https://github.com/Bachmann1234/diff_cover – diff-cover usage.
21. https://docs.codecov.com/docs/commit-status and https://docs.codecov.com/docs/codecovyml-reference – Codecov statuses and `after_n_builds`.
22. https://docs.coveralls.io/parallel-builds – Coveralls parallel builds.
23. https://pypi.org/project/pytest-xdist/ – pytest-xdist release data.
24. https://hynek.me/articles/ditch-codecov-python/ – combining coverage across a GitHub Actions matrix (practitioner).
25. https://pypi.org/project/covdefaults/ – covdefaults settings.
26. https://arxiv.org/abs/2305.02886 – SlipCover, ISSTA 2023.
27. https://nedbatchelder.com/blog/202008/you_should_include_your_tests_in_coverage.html – why to measure test code.
28. https://cs.ubc.ca/~rtholmes/papers/icse_2014_inozemtseva.pdf – Inozemtseva and Holmes, ICSE 2014.
29. https://agroce.github.io/icse14.pdf – Gopinath, Jensen and Groce, ICSE 2014.
30. https://ieeexplore.ieee.org/document/7081877 – Kochhar, Thung and Lo, SANER 2015 (abstract).
31. https://www.microsoft.com/en-us/research/publication/code-coverage-and-post-release-defects-a-large-scale-study-on-open-source-projects/ – Kochhar et al., 2017 (abstract).
32. https://www.semanticscholar.org/paper/How-Effective-Are-Code-Coverage-Criteria-Hemmati/ca5f123ed696bc4892637690dfe8b7da660f7a7c – Hemmati, QRS 2015 (abstract).
33. https://discovery.ucl.ac.uk/id/eprint/10075196/ – Zhang et al., pseudo test suites, ICST 2019 (abstract).
34. https://www.cs.ubc.ca/~rtholmes/papers/ase_2020_chen.pdf – Chen et al., ASE 2020.
35. https://www.st.cs.uni-saarland.de/publications/files/schuler-stvr-2013.pdf – Schuler and Zeller, checked coverage, STVR 2013.
36. https://people.ece.ubc.ca/amesbah/resources/papers/fse15.pdf – Zhang and Mesbah, assertions and effectiveness, FSE 2015.
37. https://arxiv.org/abs/2108.04639 – Wang et al., PyNose, ASE 2021.
38. https://arxiv.org/abs/2609.09315 – Hamidi et al., test criteria on LLM-generated code, 2026 (preprint).
39. https://par.nsf.gov/servlets/purl/10081351 – Hilton, Bell and Marinov, ASE 2018.
40. https://www.microsoft.com/en-us/research/publication/use-of-relative-code-churn-measures-to-predict-system-defect-density/ – Nagappan and Ball, ICSE 2005 (abstract).
41. https://research.google/pubs/does-bug-prediction-support-human-developers-findings-from-a-google-case-study/ – Lewis et al., ICSE 2013 (abstract).
42. https://homes.cs.washington.edu/~rjust/publ/google_coverage_fse_2019.pdf – Ivanković et al., "Code Coverage at Google", FSE 2019.
43. https://homes.cs.washington.edu/~rjust/publ/productive_coverage_icse_2024.pdf – Ivanković et al., "Productive Coverage", ICSE SEIP 2024.
44. https://testing.googleblog.com/2020/08/code-coverage-best-practices.html – Google Testing Blog, "Code Coverage Best Practices" (figures via quotations).
45. https://codescene.io/docs/guides/technical/hotspots.html and https://arxiv.org/abs/2203.04374 – CodeScene hotspots, and Tornhill and Borg, "Code Red" (vendor).
46. https://pypi.org/project/diff-cover/ – diff-cover release data.
47. https://engineering.fb.com/2023/10/24/data-infrastructure/automating-dead-code-cleanup/ – Meta, SCARF dead-code removal.
48. https://github.com/pyvista/pyvista/pull/9355 – PyVista drops per-test contexts, with timings.
49. https://hackers.pub/@hugovk@mastodon.social/0195a9d7-f222-74f1-969c-a34e2ac32292 – Pillow and inifix timings from their maintainers (informal).
50. https://go.dev/doc/build-cover, https://github.com/coverlet-coverage/coverlet and https://github.com/simplecov-ruby/simplecov – Go coverage for binaries, coverlet drivers, and SimpleCov start order.
51. Research lab for report 08 (`lab08`): Python 3.14.0, coverage 7.16.2, pytest 9.1.1, pytest-cov 7.1.0; noisy shared machine (own measurement).
52. Verification for this page, 2026-09-30: the same versions plus pytest-xdist 3.8.0, ruff 0.16.9 and vulture 2.16 (own measurement).
