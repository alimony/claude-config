# Redundant, dead, and low-value tests

This page covers tests that never run, checks that cannot fail, expected failures that pass, permanently skipped tests, duplicates, over-parametrisation, overlap between test levels, coverage-equivalent tests, tests of dead code, and unused fixtures. Load it for the static scan (phase 4), for redundancy deep dives, and before you write any finding with action `review-removal` or `merge`. Removal is never your fix: a removal candidate needs two independent kinds of evidence and the owner's review, because structural evidence alone loses real protection. Coverage-based reduction lost up to 20.5% of killed mutants [1], and reduced suites missed the fault in up to 52.2% of real failed builds [2].

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Tests that never run | `static_scan.py` collection checks, its `--nodeids` diff, one collection per continuous integration (CI) job | Every instance; trust breaker | Rename, move, or reconfigure so it runs; triage recovered failures | Restores lost checks; no published effect size |
| Checks that cannot fail | `static_scan.py` assert checks, ruff, `-W error::pytest.PytestReturnNotNoneWarning`, `no_product` | Every tautology, tuple assert, bare comparison, uncalled mock assert, or returned value; tests with no check are review items | Repair the check | No-assertion smell in 22.5% of unittest suites [3] |
| Expected failures that pass (XPASS) | `-rxX`, pytest-reportlog, or `-o strict_xfail=true`; JUnit XML hides them | Any XPASS; trust breaker | `strict_xfail = true`, `raises=` on each `xfail` | A hidden fix or broken test becomes a failure |
| Permanently skipped tests | `--setup-plan -q -rs`, marker ages, skipped in every CI report | Every job skips it for 30 days or 50 runs (heuristic) | Re-enable in an approved change, then fix or ticket | 6.3% of Google's test targets never passed or failed [4] |
| Exact and near-duplicate tests | `exact-duplicate-body`, `cross-file-duplicate-body`, `literal-only-body`, ruff `PT014` | Every exact copy with 2 or more statements; literal-only groups of 3 or more | Fix the copy-paste bug; merge literal-only groups into one parametrised test | Maintenance; little time |
| Over-parametrisation | Cases per function from node IDs, time per function, `siblings` | 50+ cases or 5%+ of suite time, with few distinct coverage sets (heuristic) | Covering arrays, Hypothesis with `@example` rows, a slower tier | Pairwise may miss 10–40% of bugs [5] |
| Overlap between test levels | `coverage_redundancy.py --scope all`, joined with durations | Slow higher-level test with 90%+ of its coverage unit-covered (heuristic) | Slim or demote the slow test; keep unit tests | Pseudo-tested methods: 35.48% for system tests, 11.41% for unit tests [6] |
| Coverage-equivalent or subsumed tests | `coverage_redundancy.py` on `ctrace` contexts | Leads only, ranked by duration | Differential mutation, then merge, demote, or review | Coverage reduction lost up to 20.5% of killed mutants [1] |
| Tests of dead production code | vulture, per-test contexts, production telemetry | Every test whose covered code is dead (applications) | Remove code and tests together after review | 91.4% of 7,326 deleted tests were obsolete [7] |
| Unused fixtures and helpers | `unused-fixtures`, fixture bodies without coverage | Every unused fixture in the project's `conftest.py` files | Removal review | Maintenance only |
| Tests that never failed | CI history ([ci-history.md](ci-history.md)) | Slow, and no genuine failure in 6–12 months | Demote to a tier that runs before release | 91.3% of Google's test targets never failed [4] |

## Signals

### Tests that never run

**Detect:**
- `static_scan.py` names the cause for `shadowed-test`, `uncollectable-class` (`__init__` or `__new__`, a `@dataclass` or attrs class, or `__init__` inherited from a class in the same file), `module-disabled` (a module-level `__test__ = False`), `disabled-class` (a class with `__test__ = False` that no scanned class inherits from), `in-norecursedirs` (tests under a directory that an explicit `norecursedirs` excludes), `misnamed-test` (a misspelt prefix such as `tset_`, or a method with asserts whose name misses the test pattern), `file-not-collected`, `imported-test`, and `yield-in-test`. With `--runner unittest`, `not-run-by-runner` covers module-level functions and classes that are not `TestCase` subclasses.
- The `--nodeids` diff (`not-collected`) finds causes outside the code. In a toy suite it found five: a test behind an import error, one with `yield`, one in `collect_ignore`, one under a module-level `__test__ = False`, and one in a class with `__new__` [toy]. It gives no reason, so read the collection errors and warnings in the run's `output.log` and every `conftest.py`.
- pytest reports "cannot collect test class 'X' because it has a `__init__` constructor" (also for `__new__`) only as a `PytestCollectionWarning`; `-W error::pytest.PytestCollectionWarning` turns each one into a collection error [toy].
- Tests that no CI job selects: compare a collection without selection against the union of every job's collection (see "Measuring"). [findings.md](findings.md) counts them as trust breakers unless a scheduled job runs them.
- Configuration: read `python_files`, `python_classes`, `python_functions`, `norecursedirs`, `testpaths`, and `addopts`, plus `collect_ignore`, `--ignore` and `--deselect` in CI scripts, and `pytest_collection_modifyitems` hooks. pytest 9 reads the first of `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml` (`[tool.pytest]` or `[tool.pytest.ini_options]`), `tox.ini`, and `setup.cfg`, and setting `norecursedirs` replaces the default list [8].
- Scan gaps: `static_scan.py` does not see classes that miss `python_classes`, or module-level functions named such as `should_x`, so its `--nodeids` diff misses them too [toy]. Grep for misnamed tests (helpers named `check_` or `verify_` also match): `grep -rn --include='*.py' -E '^\s*(async\s+)?def (tset|tst|tets|ttest|should|check|verify)_\w*\(' TEST_ROOTS`.
- Duplicate module basenames in directories without `__init__.py` cause a loud "import file mismatch" error under the default `--import-mode=prepend` [9] [toy]. They lose tests silently only when CI tolerates collection errors; `--continue-on-collection-errors` still exits with code 1 [toy].
- Since pytest 8.4, `yield` in a test is a collection error: "'yield' keyword is allowed in fixtures, but not in tests" [10] [toy]. Suites pinned to pytest 4.x–8.3 report such tests as xfail, and they never ran.
- Other runners: Maven Surefire runs only `**/Test*.java`, `**/*Test.java`, `**/*Tests.java`, and `**/*TestCase.java` by default [11]. A committed `.only` runs only the focused tests; Vitest fails in CI by default (`allowOnly` is `!process.env.CI`) [12].

**False positives:** Abstract base classes with `__test__ = False` are fine when subclasses run the inherited methods [13]. Another runner or CI job may collect the code: doctests, `--pyargs` runs, benchmark files, or jobs with other paths. Exclude vendored and generated files. A node-ID file from a collection with `-m` or `-k` makes deselected tests look uncollected. When more than half the defined tests are missing, the scan reports `not-collected-check-skipped`: run it from the pytest rootdir.

**Fix:**
- Report each one as a trust breaker with action `fix`. A static fact confirmed by the collection has high confidence ([findings.md](findings.md)). Cite it by `location`, because findings.py checks every `test_id` against `nodeids.txt`, where an uncollected test cannot appear.
- Rename shadowed tests so both run. Read both first: the shadowed copy may be the test the author meant to add.
- Rename misnamed files and functions rather than widening `python_files`, which can collect helper modules. Replace `__init__` in test classes with fixtures or `setup_method`. Move tests out of `norecursedirs` directories, or add their paths to `testpaths` or the CI command.
- Set `collect_imported_tests = false` (pytest 8.4 and later) and remove the imports [toy].
- Expect some recovered tests to fail, because the code changed while they did not run. Fix each one that guards a live behaviour; one whose production code is gone becomes a removal candidate. Developers delete failing tests more often than they repair them (1,594 against 1,121), and over 92% of those failed to compile against changed production code [14].

**Effect:** No published effect size exists for Python suites. Each recovered test restores a lost check or exposes dead code. Report how many you recovered and how many of them fail.

**Verify:** The collected count grows by the number of recovered tests, and the diff reports zero. Keep it there with ruff `F811` in the lint job, `error::pytest.PytestCollectionWarning` in `filterwarnings`, and a scheduled `static_scan.py --nodeids` run.

### Checks that cannot fail

**Detect:**
- `static_scan.py` reports `no-assertion`, `tautology` (truthy constants, non-empty tuples and literals), `self-comparison`, `assert-in-except`, `unreachable-assert`, `returns-value`, `assert-true-two-args` (`assertTrue(a, b)` treats `b` as the message), and `assert-only-in-loop`.
- ruff adds `F631` (assert on a tuple), `B015` (comparison without `assert`), `B018` (useless expression), `PGH005` (mock assertion never called), `PT017` (assert in `except`), `PLR0124` (`x == x`), `PLR0133` (constant comparison), `B017`, `PT011`, and `PT012` (broad or multi-statement `pytest.raises`), and `S110` and `BLE001` (swallowing `except`) [15]. Run `uvx ruff check --isolated --no-cache --select F811,F631,B011,B015,B017,B018,PGH005,PLR0124,PLR0133,S110,BLE001,PT --statistics TEST_ROOTS`; `--isolated` ignores user and project ruff settings [toy]. Prefer `F631` to pytest's "assertion is always true" warning, which cached bytecode hides [toy].
- `-W error::pytest.PytestReturnNotNoneWarning` fails each test that returns its comparison instead of asserting it [16] [toy]. pytest 8.4.0 failed such tests, but 8.4.1 reverted that change, so pytest only warns [10].
- `coverage_redundancy.py` lists tests that execute no product code (`no_product`). In the toy, it caught an early-return guard that the static checks missed [toy].
- `static_scan.py` reports `mock-typo` for calls such as `.called_once_with()` that lack the `assert_` prefix. On Python 3.12 and later, `Mock` raises `AttributeError` for these names [17]. On 3.11 and older, the call passes silently, so check the Python version CI uses.
- Scan gaps: neither the scan nor ruff finds a `return` guard before the first check, an `assert` in a `try` whose broad `except` swallows the failure, or checks that run only inside `if` blocks. `S110` and `BLE001` flag the swallowing pattern without knowing that it hides an assert.

**False positives:** "Does not raise" smoke tests are legitimate; ask for a name that says so. The scan counts calls whose names start with `assert`, `check`, `verify`, or `expect`, and same-file helpers that contain `assert`. Read tests that use other helpers, snapshot tools, or custom assertion libraries. `self-comparison` can be a deliberate test of a custom `__eq__`. A loop over a constant, non-empty list is fine; the risk is a computed collection.

**Fix:**
- Report each one as a trust breaker with action `fix`, never as a removal. Repair the check: `assert x, "message"` instead of a tuple, add the missing `assert`, call `assert_called()`, use `pytest.raises(SomeError, match=...)` around one statement, assert the expected length before a loop, and use `assertEqual` instead of `assertTrue(a, b)`.
- For an early-return guard, make the check run, for example by providing the precondition in CI. Do not add a skip yourself. If the owner keeps the guard, a `skipif` marker with a reason at least counts as a skip instead of a pass.
- Expect repaired tests to fail. Each failure is a hidden bug or a wrong expectation to triage.

**Effect:** In 248 Python projects that use unittest, the no-assertion smell appeared in 81.5% of projects and 22.5% of test suites. Exception handling in the test body appeared in 64.9% and 8.6%, and empty tests in 17.7% and 0.7% [3]. These are smell counts, not confirmed defects [18].

**Verify:** Inject a fault into the code under test, by hand or with a mutation tool, and confirm that the repaired test fails. Under differential mutation, it now kills mutants it did not kill before. `static_scan.py diff` shows no test with fewer assertions.

### Expected failures that pass

**Detect:**
- `static_scan.py` reports `xfail-not-strict` for `@pytest.mark.xfail` without `strict=True` when the configuration sets neither `strict_xfail` (alias `xfail_strict`) nor `strict` [toy].
- A run shows the outcome: `-rxX` prints XFAIL and XPASS lines, and pytest-reportlog records a `wasxfail` flag, which `results.py summary` counts as `xpassed`. JUnit XML records a non-strict XPASS as a plain pass, so harvested CI reports cannot show it [toy].
- `-o strict_xfail=true` turns each XPASS into a failure, `[XPASS(strict)]`, which JUnit XML does record [toy]. `--runxfail` runs `xfail` tests as normal tests [19].
- `static_scan.py` reports `xfail-never-runs` for `xfail(run=False)`, which never runs the test (`XFAIL [NOTRUN]`) [toy]. Also list markers without `raises=`, which hide a different failure.

**False positives:** An `xfail` that documents a known upstream bug is fine. Make it strict, so that the fix is noticed.

**Fix:**
- Report each XPASS as a trust breaker ([findings.md](findings.md)). Set `strict_xfail = true`; `xfail_strict` still works as an alias [8]. `strict = true` also turns on `strict_config`, `strict_markers`, and `strict_parametrization_ids` [8]. In a legacy suite, adopt them one at a time, because a duplicate parametrisation ID makes the whole module fail to collect [toy].
- Add `raises=SomeError` to each `xfail`, so that a different exception fails the test [toy]. Treat `xfail(run=False)` as a skip.

**Effect:** "Both XFAIL and XPASS don't fail the test suite by default" [19]. Each XPASS is a fixed bug or a broken test that nobody sees.

**Verify:** With strict xfail on, the XPASS count is zero, and each former XPASS either fails or has lost its marker in an approved change.

### Permanently skipped tests

**Detect:**
- `static_scan.py` reports `skip-unconditional` for skip markers on functions, methods, and classes, a module-level `pytestmark` skip, and `pytest.skip(..., allow_module_level=True)` [toy]. It also reports `skip-inside-test` and `empty-parametrize`, and counts conditional skips. `--blame` dates each example's marker line with `git blame -w -C`, which ignores whitespace and follows moved lines. The loop in "Measuring" also covers conditional markers.
- `--setup-plan -q -rs` evaluates `skip` and `skipif` markers without running test bodies or fixtures. It misses `pytest.skip()` inside tests and fixtures, `importorskip` inside functions, and `unittest.skip` [toy]. Run it in the CI image, because conditions depend on platform, Python version, packages, and environment variables.
- History: list tests that every run of every CI job skipped (see "Measuring"). Group them by message: "got empty parameter set" means a parametrize over nothing, and "could not import" means an `importorskip` of a package that no job installs. By default, a `parametrize` over an empty computed list becomes one skipped test; `-o empty_parameter_set_mark=fail_at_collect` makes it a collection error [toy].
- Hidden mechanisms: skip lists in `conftest.py` hooks, deselection in CI scripts, and expectation files outside the test source [20]. A grep of test files therefore undercounts.
- Threshold (auditor's heuristic): every job skips the test for 30 days or 50 consecutive runs, or an `xfail(run=False)` is older than 90 days.

**False positives:** Another job may run a platform skip, for example on Windows or macOS runners: only the union over all jobs counts. A nightly job may run skips that need external services, and a separate job may install an optional dependency. Quarantined flaky tests follow [flakiness.md](flakiness.md).

**Fix:**
- Recommend an approved change that removes the marker and runs the test in CI several times. If it passes, keep it. If it fails, fix it, or file a ticket with an owner and an expiry date. If its production code is gone, it becomes a removal candidate.
- Re-enabled tests can bring back flaky failures. Route those through [flakiness.md](flakiness.md) instead of forcing them green.
- For an `importorskip` of a package that no job installs, add a job that installs it. If nobody supports that integration, its tests become removal candidates.
- Set `empty_parameter_set_mark = fail_at_collect` [8], and require a reason with a ticket reference on every skip.

**Effect:** Of 5,562,881 test targets at Google, 6.3% never passed or failed in the study period and were "most likely skipped" [4]. The Ignored Test smell appeared in 29.4% of Python unittest projects and 3.0% of their suites [3].

**Verify:** The skipped count in CI reports drops. Each re-enabled test passes in several consecutive CI runs, which rules out flakiness. `static_scan.py diff` shows no new skips.

### Exact and near-duplicate tests

**Detect:**
- `static_scan.py` reports `exact-duplicate-body` (identical bodies of 2 or more statements in one file), `cross-file-duplicate-body` (weaker), and `literal-only-body` (3 or more tests whose bodies differ only in literals). For exact duplicates it hashes the body together with the signature and decorators, so identical bodies under different parametrisation are not reported. `literal-only-body` hashes the body only.
- Duplicate parametrize rows: ruff `PT014`, and `strict_parametrization_ids = true`, which fails on duplicate IDs [8].
- jscpd 5 with `--ignore-literals` finds token clones across files and labels literal-only clones `renamed` [21]. pylint `R0801` and `symilar` missed a same-file copy and a literal-only clone in the toy, so a clean pylint result means little [toy].

**False positives:** A fixture name can resolve to different fixtures, because a lower `conftest.py` overrides a higher one; compare them with `pytest --fixtures-per-test PATH::TEST` [toy]. Identical bodies with different parametrisation or fixture arguments test different inputs, and the scan does not compare those. Contract tests reused on purpose, generated tests, and deliberate repeats at another test level are fine. Parametrised cases of one test are never duplicates of each other ([traps.md](traps.md)).

**Fix:**
- Treat an exact duplicate first as a probable copy-paste bug: the author usually meant to change a value. Ask what the copy should test, and fix it. A copy that adds nothing is a removal candidate (see "Removal review").
- Merge a literal-only group into one `@pytest.mark.parametrize` test with readable `ids=`. The action is `merge`, which needs two kinds of evidence, for example `static` plus `coverage`.
- Extract a helper or fixture when near-duplicates share long setup. When the literals sample a value domain, consider a property-based test ([techniques.md](techniques.md)).

**Effect:** Removing fast duplicates saves little time; the gain is maintenance. No study with effect sizes exists for duplicates in Python suites.

**Verify:** After a merge, the collected case count is unchanged: N functions become one function with N cases. Coverage and the mutation score of the module under test are unchanged. `static_scan.py diff` lists the merged names as removed and exits with 1 [toy]. That is expected: attach the mapping from old names to new cases to the approval request.

### Over-parametrisation

**Detect:**
- Count cases per function from a collection: `sed 's/\[.*//' AUDIT/nodeids.txt | sort | uniq -c | sort -rn | head -20` [toy].
- `static_scan.py` reports `parametrize-size` for literal matrices of 50 or more cases, including stacked decorators. It does not count generated value lists or parametrised fixtures (`@pytest.fixture(params=...)`), which multiply every test that requests them; the node-ID count includes both.
- Sum the time of all cases of each function (see "Measuring"). One function can dominate a suite without any single case looking slow.
- `coverage_redundancy.py` reports `siblings`: parametrised tests whose cases all hit identical code. The toy's 27-case matrix hit one coverage set [toy].
- Threshold (auditor's heuristic): 50 or more cases, or 5% or more of suite time in one function, with distinct coverage sets for 10% of the cases or fewer.

**False positives:** Boundary values, locale tables, and parser corpora execute the same lines by design. Each row may be the regression test for a past bug, so check with `git log -L` or `git blame` whether rows arrived with bug-fix commits. Compatibility matrices, such as databases or Python versions, run the same lines in environments that coverage cannot tell apart. Hypothesis is not free: it runs 100 examples per test by default [22].

**Fix:**
- Remove duplicate rows first (`PT014`, `strict_parametrization_ids`).
- For configuration matrices, run a pairwise or 3-way covering array in pull requests and the full product nightly. allpairspy cut a 3 × 3 × 3 × 2 matrix of 54 cases to 9 [toy]. Disclose the loss: pairwise testing may miss 10–40% or more of system bugs [5], so keep 3-way for critical logic.
- For a large literal table over a value domain, write a Hypothesis property and keep each known regression as an `@example`. Explicit examples always run, do not count towards `max_examples`, and are not shrunk [22].
- Mark heavy rows with `pytest.param(..., marks=pytest.mark.slow)` for a slower tier, or narrow fixture parametrisation with `indirect`, so that only the tests that need the matrix get it.

**Effect:** Case studies reached the fault detection of exhaustive testing with 20 to 700 times fewer tests [23]. In the data of the US National Institute of Standards and Technology (NIST), one parameter triggered 67% of NASA application failures, two 93%, and three 98% [5].

**Verify:** The mutation score of the module under test is unchanged, and every row from a bug fix survives as an explicit case. The function's total time drops in uninstrumented runs (`results.py diff`, medians of 3).

### Overlap between test levels

**Detect:**
- Record per-test contexts for all levels in one run, or merge per-level data files with `coverage combine`. `coverage_redundancy.py --scope all` then reports subsets across levels. In the toy, 12 unit tests had coverage inside one integration test's coverage [toy]. For each slow higher-level test, compute the share of its covered arcs that unit tests also cover, and join it with the test's duration.
- Do not trust directory names as level labels. In 10 Python projects, developers believed they wrote more unit tests than they did [24].
- Threshold (auditor's heuristic): a slow integration or end-to-end test with 90% or more of its coverage inside unit-covered code. It is a candidate for slimming or demotion only.

**False positives:** Executing code is not checking it. The mean share of pseudo-tested methods (covered, but no test fails when the body is removed) was 11.41% for unit tests and 35.48% for system tests [6]. Unit tests with mocks do not check wiring, such as serialisation, configuration, SQL, and transactions. Unit tests also localise failures and run fast, which coverage does not show.

**Fix:**
- Never propose removing unit tests because a higher level covers the same lines.
- Cut repeated logic assertions from integration and end-to-end tests, and keep those tests on the integration points [25]. First move pure-logic checks that live only in slow tests down to unit tests.
- Demote overlapping slow tests to a nightly tier (action `demote`), and keep one smoke path per critical user journey in pull-request runs. Disclose the cost: a demoted test catches regressions later. The only test of a behaviour stays.

**Effect:** No controlled study with numbers exists; the published guidance is qualitative [25].

**Verify:** Compare pull-request pipeline time before and after, from uninstrumented runs. Check the unit-level mutation score on the affected modules, and escaped defects in the affected area over one release.

### Coverage-equivalent and subsumed tests

**Detect:**
- Record per-test contexts with `COVERAGE_CORE=ctrace` and run `coverage_redundancy.py` (see "Measuring"). It compares only the call phase (`|run` contexts) of tests in one directory by default. `identical` lists different test functions with exactly the same coverage, and `subsumed` lists tests whose coverage is a strict subset of one other test's. Use pytest-cov's `--cov-context=test` [26]. coverage.py's own `dynamic_context = test_function` does not separate parametrised cases, or setup from the test body [27].
- Threshold: groups of different test functions in one directory, and strict subsets in one directory, as leads only. "Covers nothing unique" is not a finding: 52 of 54 toy tests covered nothing unique [toy].

**False positives:** Same coverage is not the same checks ([traps.md](traps.md)): `add(1, 2)` and `add(-1, -2)` cover the same line. Every test of a one-line function looks equivalent. Coverage misses C extensions, SQL in the database, templates, subprocesses without configuration, and configuration files. A test whose fixture does the work shows little `|run` coverage, so look at its `|setup` context. With `--nodeids`, `no_product` also lists skipped tests, which record no context [toy].

**Fix:**
- Rank each group by the tests' duration and churn. Removing a fast unit test saves milliseconds.
- Run differential mutation on the covered modules (see "Measuring"). A test with zero unique kills, a second kind of evidence, and the owner's agreement is a candidate for merging or removal.
- Prefer demotion to a nightly tier for slow subsumed tests. Never run a reduction algorithm and propose its output as one batch.

**Effect:** Statement-coverage reduction cut 18 Java projects' suites by 62.9% on average and lost up to 20.5% of killed mutants [1]. On 1,478 failed builds, reduced suites missed the fault in 12.1–52.2% of builds [2].

**Verify:** Run differential mutation on the whole batch, and diff per-file coverage before and after. Where CI history exists, replay the last N failing builds and check that the reduced suite still fails each one [2].

### Tests of dead production code

**Detect:**
- In applications, run `vulture src/` without the test directories to list production code that nothing in production calls [28]. `coverage json --show-contexts` on the contexts data maps each covered line to the tests that ran it [toy]. A test whose `|run` coverage lies entirely inside dead functions is a candidate.
- Confirm deadness with production telemetry, logs, or profiles, because test runs cannot prove that code is live [29].
- Leftovers: tests that fail at import after their module was deleted, and tests that import modules deleted in history. List those with `git log --diff-filter=D --name-only --format= -- src/`, then grep the test tree for their names.

**False positives:** In a library, the public API looks unused inside the repository, so whitelist it. Dynamic use, such as entry points, plugin registries, route tables, task names, `getattr`, and serializers, gets reported at 60% confidence; build a whitelist with `vulture src --make-whitelist` [28].

**Fix:** Recommend deleting the dead code and its tests in one change, after the owners confirm that the code is dead. The candidate carries `static` (vulture) and `coverage` (contexts) evidence, plus the production telemetry.

**Effect:** Obsolete tests are the largest category that developers really delete: 91.4% of 7,326 deleted tests in Java projects. 38% of them outlived their production code, by a median of 1 day and up to 31 days [7]. At Google, deleting dead code together with its tests has removed nearly 5% of all C++ code [29].

**Verify:** Production logs show no use for a full business cycle, including monthly and yearly jobs. CI stays green after the code and its tests go in one change.

### Unused fixtures and helpers

**Detect:**
- `static_scan.py` reports `unused-fixtures`: fixtures that nothing requests by name. It counts parameters, `usefixtures`, `getfixturevalue` with a literal name, and `indirect` parametrisation, and it skips autouse and common plugin fixtures.
- When the contexts run also measures the test tree (`--cov=TEST_ROOT`), `coverage report --include='*/conftest.py' -m` shows fixture bodies that never ran [toy].
- pytest-unused-fixtures records real use during a full run, and it reported only the truly unused fixture in the toy [30] [toy]. pytest-deadfixtures is static and reported a fixture requested through `getfixturevalue` as unused [31] [toy]. It relies on a private pytest attribute that pytest 9.2 removes, and the fix is still an open pull request [31]. `vulture tests/` finds unused helper functions; in the toy, it also flagged a dynamically requested fixture and a `TestCase` subclass [28] [toy].

**False positives:** Code can request a fixture with a computed name, in `pytest_generate_tests`, through lazy-fixture plugins, or from another repository that loads a shared conftest plugin. A fixture may serve only tests that this run skipped or deselected, so check the union of CI jobs. Autouse fixtures always count as used; unneeded autouse work is a speed finding ([fixed-costs.md](fixed-costs.md)).

**Fix:** Report every unused fixture in the project's own `conftest.py` files as a removal candidate with `static` plus `coverage` evidence, which findings.py accepts. Merge duplicated fixtures; `pytest --dup-fixtures` from pytest-deadfixtures compares only fixtures that return truthy values [31].

**Effect:** Maintenance only, unless the unused fixture is expensive and autouse or session-scoped.

**Verify:** The full CI run is green in every job, and `static_scan.py diff` shows no removed tests.

### Tests that never failed

**Detect:** From CI history ([ci-history.md](ci-history.md)), compute per test the runs, genuine failures (not infrastructure errors or flaky failures), the date of the last genuine failure, and the duration. Flag slow tests with no genuine failure in 6–12 months.

**False positives:** See [traps.md](traps.md) first. CI history also misses failures that developers fixed before they pushed, and retries and quarantines mask failures. "Never failed" mostly measures distance from churn: the few test targets that fail at Google are generally "closer" to the code they test [4].

**Fix:** Recommend demotion (action `demote`) to a less frequent tier that is guaranteed to run before release, or change-based test selection ([scheduling.md](scheduling.md)). History is one kind of evidence, never the only one for a removal.

**Effect:** At Google, 91.3% of 5,562,881 test targets never failed, and only 1.23% found a breakage or a fix [4]. Microsoft's THEO skipped 35–50% of test executions and still ran every test before release [32]. None of these organisations deleted the quiet tests.

**Verify:** After demotion, count the defects that the slower tier catches later, which is the cost, and measure pull-request pipeline time.

## Measuring

### Defined versus collected

```sh
# NN is the run number that run_suite.py prints. Run static_scan.py from ROOT, the pytest rootdir.
# Drop -m and -k from CI_TEST_COMMAND for this collection; add -m "" if addopts sets -m.
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label collect-all --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND --collect-only -q
grep '::' AUDIT/runs/NN-collect-all/output.log | grep -v '^\$ ' > AUDIT/nodeids-all.txt
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py --nodeids AUDIT/nodeids-all.txt --json-out AUDIT/static.json
```

`not-collected` lists each defined test that the collection lacks, as file and qualified name, with no reason. With collection errors, `run_suite.py` labels the run PARTIAL, but `--collect-only -q` still lists every other test, and a later `-m ""` overrides a `-m` in `addopts` [toy]. Cost: the scan takes seconds and runs no project code; the collection imports every test module, so it needs the user's agreement like any run.

### Tests that no CI job selects

```sh
# Repeat for each CI job, with that job's command and environment (--env KEY=VALUE):
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label collect-JOB --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND --collect-only -q
grep '::' AUDIT/runs/NN-collect-JOB/output.log | grep -v '^\$ ' >> AUDIT/nodeids-ci-union.txt
comm -23 <(sort -u AUDIT/nodeids-all.txt) <(sort -u AUDIT/nodeids-ci-union.txt)
```

Each output line is a test that no CI job runs [toy]. Check scheduled and nightly jobs before you report it.

### Probes that make silent problems fail

Run each probe as its own labelled run, never as the baseline, because it changes outcomes. The probe collection turns each problem into a collection error, so take node IDs from the plain collection. On a large suite, pass only the files that the static scan flagged.

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label probe --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND -rsxX -o strict_xfail=true -W error::pytest.PytestReturnNotNoneWarning FILES
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label probe-collect --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND --collect-only -q -W error::pytest.PytestCollectionWarning -o empty_parameter_set_mark=fail_at_collect
```

| Option | Makes this visible | Verified output [toy] |
| --- | --- | --- |
| `-o strict_xfail=true` | Expected failures that pass | `[XPASS(strict)] bug 7` as a failure |
| `-W error::pytest.PytestReturnNotNoneWarning` | Tests that return instead of assert | `FAILED tests/unit/test_calc.py::test_returns_bool` |
| `-rsxX` | Skip reasons, XFAIL, and XPASS | `XPASS tests/unit/test_classskip.py::test_xfail_nonstrict_passes - bug 8` |
| `-W error::pytest.PytestCollectionWarning` | Test classes pytest cannot collect | `ERROR tests/unit/test_calc.py::TestWithInit - pytest.PytestCollectionWarning` |
| `-o empty_parameter_set_mark=fail_at_collect` | Parametrize over an empty list | `Empty parameter set in 'test_every_fixture_file_parses' at line 6` |

### Skip and expected-failure inventory

```sh
# The age of every marker line, oldest first (read-only git):
git grep -n -E '@pytest\.mark\.(skip|skipif|xfail)([^a-z_]|$)|pytest\.(skip|xfail|importorskip)\(|@unittest\.(skip|skipIf|skipUnless|expectedFailure)([^A-Za-z_]|$)|pytestmark *=' -- '*.py' |
while IFS=: read -r f n rest; do
  ts=$(git blame -w -C -L "$n,$n" --porcelain -- "$f" | awk '/^author-time/{print $2}')
  printf '%5d days  %s:%s  %s\n' $(( ($(date +%s) - ts) / 86400 )) "$f" "$n" "$(echo "$rest" | sed 's/^ *//' | cut -c1-80)"
done | sort -rn
# Markers that are true in this environment; no test bodies or fixtures run:
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label setup-plan --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND --setup-plan -q -rs
grep '^SKIPPED' AUDIT/runs/NN-setup-plan/output.log
```

`git blame` dates the last change to a line, so a reformat resets the age. `-w -C` ignores whitespace and follows moved lines, and `.git-blame-ignore-revs` skips bulk reformat commits. `git log -S'MARKER TEXT' --reverse --format='%ad %h'` finds the commit that first added a marker.

For history, summarise each harvested report on its own, one per job and run. `results.py summary` merges its inputs into one run, so a later file would overwrite an earlier job's outcome:

```sh
n=0; for f in AUDIT/ci/*/*.xml; do n=$((n+1))
  python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary "$f" --nodeids AUDIT/nodeids.txt --json-out AUDIT/results/skips-$n.json > /dev/null
done
python3 - AUDIT/results/skips-*.json <<'EOF'
import collections, json, sys
seen, skipped = collections.Counter(), collections.Counter()
for path in sys.argv[1:]:
    for t in json.load(open(path))["all_tests"]:
        seen[t["id"]] += 1
        skipped[t["id"]] += t["outcome"] == "skipped"
print("\n".join(f"{seen[k]} reports: {k}" for k in sorted(seen) if skipped[k] == seen[k]))
EOF
```

The output lists the tests that every report skipped [toy]. `results.py` keeps no skip messages, so read the reason from a `<skipped message=...>` element in one report. Cover 30 days of every CI job.

### Per-test coverage contexts

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label contexts-DIR --timeout SECONDS --cwd ROOT \
    --env COVERAGE_CORE=ctrace -- \
    CI_TEST_COMMAND -p no:randomly --cov=PKG --cov=TEST_ROOT --cov-branch --cov-context=test --cov-report= DIR
grep '^DIR' AUDIT/nodeids.txt > AUDIT/nodeids-DIR.txt
python3 ${CLAUDE_SKILL_DIR}/scripts/coverage_redundancy.py AUDIT/runs/NN-contexts-DIR/.coverage \
    --nodeids AUDIT/nodeids-DIR.txt --json-out AUDIT/redundancy-DIR.json
```

- `run_suite.py` points `COVERAGE_FILE` at the run folder and marks the run as instrumented, so its timings never back a speed claim.
- `COVERAGE_CORE=ctrace` is required ([traps.md](traps.md)). In the toy, the default `sysmon` core on Python 3.14 recorded 6 `|run` contexts instead of 56, and the script refused the data with exit code 2 [toy].
- `--cov=TEST_ROOT` gives every executed test a context, so "tests with contexts" in the first output line roughly equals the executed count, and it measures fixture bodies. `-p no:randomly` keeps the order fixed and is harmless when the plugin is absent [toy].
- Pass `--nodeids` only for the selection you measured, or every other test appears in `no_product`.
- Output: `identical`, `subsumed`, `siblings`, and `no_product`. `--scope module` narrows the comparison, and `--scope all` crosses directories and test levels. Above 3,000 tests in one scope (`--max-group`), the script skips the subset check and says so.
- Cost, on a synthetic 2,000-test suite: 11.0–15.1 s with contexts on `ctrace` against 5.6–6.0 s without coverage, roughly twice. The data file grew from 0.15 MB to 1.9 MB with branch contexts, or 0.73 MB with lines only [toy]. Compute-heavy suites pay more, so measure one directory or one CI shard at a time, and drop `--cov-branch` unless branches matter. pytest-xdist works: `-n 2` recorded the same contexts as a serial run [toy].

### Time per parametrised function

```sh
python3 - AUDIT/results/baseline-summary.json <<'EOF'
import collections, json, sys
secs, cases = collections.Counter(), collections.Counter()
for t in json.load(open(sys.argv[1]))["all_tests"]:
    base = t["id"].split("[", 1)[0]
    secs[base], cases[base] = secs[base] + t.get("total", 0), cases[base] + 1
print("\n".join(f"{s:9.1f}s {cases[b]:6d} cases  {b}" for b, s in secs.most_common(20)))
EOF
```

The output ranks base functions by the summed time of their cases in the uninstrumented baseline summary from phase 6 [toy].

### Differential mutation: unique kills

A unique kill is a mutant that only the candidate kills. Run mutation testing only in a disposable copy, COPY ([mutation-testing.md](mutation-testing.md)), on the modules the candidates cover. With mutmut 3.8.0 [33], in the copy's `pyproject.toml`:

```toml
[tool.mutmut]
source_paths = ["src/pkg"]
pytest_add_cli_args_test_selection = ["tests/"]
```

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mutants-base --timeout SECONDS --cwd COPY -- mutmut run
(cd COPY && mutmut results --all true) | awk -F': ' '/killed/{gsub(/^ +/,"",$1); print $1}' | sort > AUDIT/killed-base.txt
# Deselect the candidates in pytest_add_cli_args_test_selection, delete COPY/mutants/, and run again:
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label mutants-without --timeout SECONDS --cwd COPY -- mutmut run
(cd COPY && mutmut results --all true) | awk -F': ' '/killed/{gsub(/^ +/,"",$1); print $1}' | sort > AUDIT/killed-without.txt
comm -23 AUDIT/killed-base.txt AUDIT/killed-without.txt   # mutants that only the deselected tests kill
```

- Empty output means no unique kills. In a toy module with 15 killed mutants, two tests with identical coverage each had zero unique kills, yet deselecting both left 14: together they were the only killers of one mutant [toy]. So check each candidate alone to rank them, then the whole batch together.
- `--deselect` takes a node-ID prefix, so `--deselect PATH::test_x` also drops `test_x_again` and every case of `test_x` [toy]. Before each run, check the deselected count with `--collect-only -q` and the same arguments. To drop exactly one test, use `-k`, for example `"-k", "not test_x or test_x_again"` [toy].
- `run_suite.py` marks mutation runs UNCHECKED, so judge completeness from mutmut's results: no mutant left unchecked [toy]. Cost: one mutation run per candidate or batch. Restrict `source_paths`, or name functions, for example `mutmut run "pkg.module.x_function*"`. mutmut 3 needs `fork` (on Windows, use the Windows Subsystem for Linux) and mutates only code inside functions [33].
- Other ecosystems: PIT's `fullMutationMatrix` with XML output records every killing test instead of the first [34]. StrykerJS reports `killedBy` and `coveredBy` per mutant, and `disableBail` records every killing test [35].

### Removal review

Follow these steps for every `review-removal` or `merge` finding. The audit proposes, the owner decides, and you report individual candidates, never a headline share of "redundant" tests ([traps.md](traps.md)).

1. Build one row per candidate: node ID or location, median duration from an uninstrumented baseline, owner (CODEOWNERS or `git log`), last change, and evidence.
2. Require two different kinds among `coverage`, `mutation`, `history`, and `static`; findings.py enforces this. Make one of them behavioural (zero unique kills) or a proof that the production code is dead, because a duplicate abstract syntax tree and identical coverage both describe structure only. With one kind, recommend a demotion or an investigation instead.
3. For never-run and permanently skipped tests, recommend re-enabling first. Only those that fail because their production code is gone become removal candidates.
4. Save the candidates' coverage map (`coverage json --show-contexts`) as an artifact before anything is removed. It is the map for monitoring.
5. Offer the alternatives first, in this order: merge into a parametrised test, demote to a nightly or pre-release tier, convert to a property-based test, or slim an end-to-end test to its integration points.
6. Propose small batches, for example 20–50 tests per change grouped by owner and area (heuristic), and re-run differential mutation on the whole batch.
7. After an approved change, `static_scan.py diff` of scans before and after must list exactly the approved tests. For one release cycle, map escaped defects to the saved coverage, and restore a removed test when a defect overlaps it.

## Tools

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| pytest | Collection, `--setup-plan`, `-rsxX`, `--runxfail`, strictness options | 9.1.1, 2026-06-19, maintained [36] | "assertion is always true" appears only on a cold bytecode cache [toy] |
| coverage.py | Per-test contexts, `json --show-contexts`, `report --include` | 7.16.2, 2026-09-27, maintained [36] | The `sysmon` core records incomplete contexts; it warns since 7.15.3 [37] |
| pytest-cov | `--cov-context=test`: node ID plus phase | 7.1.0, 2026-03-21, maintained [36] | Needs coverage 7.10.6 or later; same core caveat |
| ruff | Shadowed tests and checks that cannot fail | 0.16.9, 2026-09-24, maintained [36] | `--isolated` fixes the rule set; no rule for early returns or `called_once_with` (`static_scan.py` reports `mock-typo`) |
| vulture | Dead production code, unused helpers | 2.16, 2026-03-25, maintained [36] | False positives for dynamic use and library APIs [28] |
| pytest-unused-fixtures | Unused fixtures, recorded during a real run | 0.3.1, 2025-12-23, beta [36] | Sees only what ran [30] |
| pytest-deadfixtures | Static unused and duplicate fixtures | 3.1.0, 2026-01-15, revived in 2025, 18 open issues [31] | `getfixturevalue` false positives; pytest 9.2 needs open pull request #61 [31] |
| jscpd | Token clones across files, any language | 5.3.3, 2026-09-28, very active [21] | Fixture-blind; its command line changes quickly, so pin the version |
| mutmut | Differential mutation | 3.8.0, 2026-09-12, maintained [36] | Needs `fork`; mutates code inside functions only [33] |
| allpairspy | Pairwise case generation | 2.5.1, 2023-07-08, no release in three years [36] | 2-way only; works on Python 3.14 [toy] |

## Evidence

- Shi et al. 2014, 18 Java projects, 261,235 tests: statement-coverage reduction cut suites by 62.9% on average and lost up to 20.5% of killed mutants. Reduction by killed mutants lost none, at 11.9 percentage points more tests [1].
- Shi et al. 2018, 1,478 failed builds in 32 projects: suites reduced by coverage or by mutants kept 51.9% or 61.1% of tests. They lost only 2.7% or 2.2% of the other measure, yet missed the fault in 12.1–52.2% of builds. Size reduction predicted the loss poorly (R² at most 0.45): automated reduction is "more risky than suggested by prior research" [2].
- Shi et al. 2015, 4,793 commits of 17 projects: test selection ran 40.15 percentage points fewer tests than reduction and lost nothing, while reduction lost change-related mutants (per-project median up to 5.93%) [38].
- Rothermel et al. saw fault detection fall by more than 50% for over half of 1,000 reduced suites. Wong et al. saw 0–1.45% on other programs, so losses do not transfer between projects [39].
- Bhatta et al. 2025: 91.4% of 7,326 deleted tests were obsolete, 7% redundant, and 1.6% failing. Of 518 tests deleted as redundant, 20% reduced line or branch coverage, and 66 reduced the mutation score (median 12%, up to 26%) [7].
- Pinto et al. 2012, six Java programs: 75.2% of 947 deleted passing tests did not reduce branch coverage, and 55.9% of 1,664 added passing tests did not increase it [14].
- Niedermayr et al.: pseudo-tested methods averaged 11.41% in unit tests and 35.48% (range 6–72%) in system tests [6].
- PyNose, 248 Python unittest projects: no-assertion in 81.5% of projects and 22.5% of suites; Ignored Test in 29.4% and 3.0%; empty tests in 17.7% and 0.7% [3].
- NIST: one parameter triggered 67% of NASA application failures, two 93%, and three 98%, and pairwise testing may miss 10–40% or more of system bugs [5]. Its case studies matched exhaustive testing with 20 to 700 times fewer tests [23].
- Google, 5,562,881 test targets: 91.3% never failed, 6.3% never passed or failed, and 1.23% found a breakage or a fix; the aim was to run quiet targets less often [4].
- Microsoft THEO: 35–50% fewer test executions in a simulation over 26 months and 37 million executions, with every test still run before release [32].
- Google Sensenmann: more than 1,000 deletion changes per week and nearly 5% of all C++ code deleted; tests share the fate of the code they test [29].

## Sources

1. https://mir.cs.illinois.edu/gyori/pubs/fse14reduction.pdf – Shi, Gyori, Gligoric, Zaytsev, Marinov, "Balancing trade-offs in test-suite reduction", FSE 2014.
2. https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf – Shi, Gyori, Mahmood, Zhao, Marinov, "Evaluating test-suite reduction in real software evolution", ISSTA 2018.
3. https://arxiv.org/abs/2108.04639 – Wang et al., "PyNose: a test smell detector for Python", ASE 2021.
4. https://research.google/pubs/taming-google-scale-continuous-testing/ – Memon et al., "Taming Google-scale continuous testing", ICSE-SEIP 2017.
5. https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-142.pdf – Kuhn, Kacker, Lei, "Practical combinatorial testing", NIST SP 800-142, 2010.
6. https://arxiv.org/abs/1611.07163 – Niedermayr, Juergens, Wagner, "Will my tests tell me if I break this code?", CSED 2016.
7. https://hifromajay.github.io/papers/msr25.pdf – Bhatta, Kendemah, Jha, "Understanding test deletion in Java applications", MSR 2025.
8. https://docs.pytest.org/en/stable/reference/reference.html and https://docs.pytest.org/en/stable/reference/customize.html – pytest configuration options and configuration-file lookup.
9. https://docs.pytest.org/en/stable/explanation/pythonpath.html – pytest import modes; `prepend` stays the default.
10. https://docs.pytest.org/en/stable/changelog.html – pytest changelog: the 8.4 `yield` error, the 8.4.0 return-value change and its 8.4.1 reversal, and 9.0 strict mode.
11. https://maven.apache.org/surefire/maven-surefire-plugin/examples/inclusion-exclusion.html – Maven Surefire default inclusion patterns.
12. https://vitest.dev/config/allowonly – Vitest `allowOnly`.
13. https://docs.pytest.org/en/stable/example/pythoncollection.html – pytest collection customisation, `__test__`, and `collect_ignore`.
14. https://web.archive.org/web/2020/https://faculty.cc.gatech.edu/~orso/papers/pinto.sinha.orso.ICSE12.pdf – Pinto, Sinha, Orso, "Understanding myths and realities of test-suite evolution", FSE 2012.
15. https://docs.astral.sh/ruff/rules/ – ruff rule reference.
16. https://docs.pytest.org/en/stable/how-to/assert.html#return-not-none – pytest on tests that return a value.
17. https://github.com/python/cpython/issues/100690 – CPython 3.12: `Mock` rejects assertion names without the `assert_` prefix.
18. https://doi.org/10.1007/s10664-022-10207-5 – Panichella et al., "Test smells 20 years later: detectability, validity, and reliability", EMSE 2022.
19. https://docs.pytest.org/en/stable/how-to/skipping.html – pytest skip and xfail, including `strict`, `raises`, `run`, and `--runxfail`.
20. https://chromium.googlesource.com/chromium/src/+/main/docs/testing/on_disabling_tests.md – Chromium, the ways tests get disabled.
21. https://github.com/kucherenko/jscpd – jscpd repository and releases.
22. https://hypothesis.readthedocs.io/en/latest/reference/api.html – Hypothesis API reference: `@example`, `max_examples`, and phases.
23. https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software – NIST automated combinatorial testing project.
24. https://doi.org/10.1109/ICST.2017.26 – Trautsch and Grabowski, "Are there any unit tests? An empirical study on unit testing in open source Python projects", ICST 2017.
25. https://docs.gitlab.com/development/testing_guide/testing_levels/ – GitLab testing levels guidance.
26. https://pytest-cov.readthedocs.io/en/latest/contexts.html – pytest-cov per-test contexts.
27. https://coverage.readthedocs.io/en/latest/contexts.html – coverage.py measurement contexts.
28. https://github.com/jendrikseipp/vulture – vulture documentation.
29. https://testing.googleblog.com/2023/04/sensenmann-code-deletion-at-scale.html – "Sensenmann: code deletion at scale", Google Testing Blog, 2023.
30. https://github.com/mikicz/pytest-unused-fixtures – pytest-unused-fixtures repository.
31. https://github.com/jllorencetti/pytest-deadfixtures – pytest-deadfixtures repository, issues #28 and #39, and pull request #61 for pytest 9.2.
32. https://www.microsoft.com/en-us/research/wp-content/uploads/2015/05/The-Art-of-Testing-Less-without-Sacrificing-Quality.pdf – Herzig, Greiler, Czerwonka, Murphy, "The art of testing less without sacrificing quality" (THEO), ICSE 2015.
33. https://github.com/boxed/mutmut – mutmut README and configuration.
34. https://pitest.org/quickstart/maven/ – PIT Maven quickstart: `fullMutationMatrix`.
35. https://stryker-mutator.io/docs/stryker-js/configuration/ – StrykerJS configuration: `disableBail` and `coverageAnalysis`.
36. https://pypi.org/pypi/PACKAGE/json – PyPI metadata (version, upload date, classifiers), read on 2026-09-30.
37. https://coverage.readthedocs.io/en/latest/changes.html – coverage.py changelog, including the 7.15.3 warning for `sysmon` and dynamic contexts.
38. https://mir.cs.illinois.edu/gyori/pubs/fse15.pdf – Shi, Yung, Gyori, Marinov, "Comparing and combining test-suite reduction and regression test selection", ESEC/FSE 2015.
39. https://doi.org/10.1002/stvr.430 – Yoo and Harman, survey of regression test minimisation, selection, and prioritisation, STVR 2012 (preprint: https://www.cse.chalmers.se/~feldt/advice/yoo_2010_regression_testing_survey.pdf).

[toy] Planted-defect toy suites run on 2026-09-30 with pytest 9.1.1, pytest-cov 7.1.0, coverage.py 7.16.2, ruff 0.16.9, pylint 4.1.1, vulture 2.16, mutmut 3.8.0, jscpd 5.3.3, and allpairspy 2.5.1 on CPython 3.14.0: the research behind this page, and the checks of its commands. Reproducible; not a primary source.
