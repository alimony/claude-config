# Design, smells, and architecture

This page is the reference for judging how a test suite is built: mocks, fixtures, conftest files, `unittest.TestCase` hierarchies, strictness and lint settings, type checking, suite shape, and contract tests. It also says which catalogue test smells are noise, so you do not report them. Load it in phase 4 when you sample static-scan hits, and in phase 7 when the hypothesis is that tests are hard to change. Tests that never run or cannot fail outrank everything on this page; [redundancy.md](redundancy.md) covers them. Report a static signal only after a sample shows that most of its hits are actionable (see [Signals](#signals)).

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Tests that never run or cannot fail | ruff F631, F811, B015, PGH005; `static_scan.py` | Every confirmed hit | See [redundancy.md](redundancy.md) | Trust breaker (P0) |
| Strictness settings off | Read the pytest configuration; strict probe | The probe shows errors, or `strict` and `filterwarnings = error` are unset | Pin pytest; `strict = true`; `filterwarnings = ["error", …]` | A misspelt marker escapes `-m` deselection; an unexpected pass (XPASS) goes unnoticed |
| Lint rules that find test bugs not enforced | Lint pass with and without `--isolated` | A rule fires that the project's configuration hides or does not select | Enable the rules for tests, one pull request per rule | Each hit can hide a broken check; 2 real B015 bugs in 5 mature projects [1] |
| Autouse fixture fan-out | `static_scan.py` autouse-fixtures; design probe; `results.py fixtures` | A root autouse fixture patches, touches the file system or network, or pulls in heavy fixtures, and setup is a large share of test time | Move it to the directory that needs it; request it explicitly | poetry: median 42 fixtures per test; setup 25% of test time [1] |
| Patches without a spec | Patch-spec counter; `mocks_without_spec` in `static_scan.py` | Most patches of changing first-party code have no spec | `autospec=True` on functions and methods; `spec_set` on classes | 67–94% unspecced in 5 projects; +0.2 ms per function patch, up to 19 ms per whole class [1] |
| Patches that never take effect | Unused-patch plugin (runtime) | Explicit-test patches with zero calls | Patch where the name is looked up | poetry: 7,040 of 8,333 mocks never called, about 73 in explicit tests [1] |
| Assertion helpers without rewriting | `grep` for `assert` in non-test modules | Helper asserts are real checks and not registered | `pytest.register_assert_rewrite(...)` | `assert 36 == 37` instead of a bare `AssertionError` |
| Over-mocking, interaction-only tests | `static_scan.py` mock-density; tests that only check calls | Many hits, and mutants survive in those modules | Real objects, then fakes; check state | Google: constant upkeep, rarely found bugs [2] |
| Mocking what you do not own | Patch-spec counter namespaces | Third-party targets outside a thin adapter | Adapter plus fake; purpose-built doubles | Expert consensus only [3] |
| Conftest sprawl and overrides | `conftest_files` and unused-fixtures in `static_scan.py`; `--fixtures -v` | Over about 500 lines or 30 fixtures, plus confusion or a wrong-fixture bug | Split into plugin modules | Root conftests of 809–1,133 lines; no published effect size [1] |
| Type checker skips tests | mypy with and without `--check-untyped-defs`; pyright | The two error counts differ widely | `check_untyped_defs = true` for tests, or pyright | Catches swapped arguments, not mock misuse |
| Suite shape | Count and time per tier | The largest tier by time is slow, flaky, and duplicates lower tiers | Move those checks down a tier | Ratios are not targets [4], [5] |
| Broad tests at service boundaries | Continuous integration (CI) history; tests that check only response shapes | Slow or flaky broad tests of another team's application programming interface (API) | Pact or Schemathesis, plus a few journeys | Schemathesis: 1.4–4.5× more unique defects than the next fuzzer [6] |
| `TestCase` hierarchies, mixed styles | Design probe class depth; ruff PT009 and PT027 | Chained `setUp` shares mutable state, or a migration is planned | pytest functions with fixtures; verified conversion | Django: 10 classes at depth 3 or more [1] |
| Catalogue smell counts | Do not run a detector for counts | Never as counts | Use the signals above | Flagged in 75–90% of projects; rarely real [7], [8] |

## Signals

Every signal below is a candidate until you sample it. Read a random sample of up to 5 hits, as [SKILL.md](../SKILL.md) phase 4 says, and classify each one as actionable, deliberate, or a tool error. Report the signal only when most sampled hits are actionable, and put the precision, such as "4 of 5 actionable", in the evidence note. Otherwise, keep it as a rejected finding with the sample as the reason.

The bar is strict because developers stop reading noisy reports, and the few tests that cannot fail get lost in the noise. Google keeps its code-review analyses below a 10% "effective false positive" rate, meaning reports that developers choose not to act on, and shows them only on changed lines [9]. For each finding, give 3–5 examples with `path:line`, the prevalence, the fix, and how to verify it. Use the `design` dimension for maintenance cost and `trust` for false confidence ([findings.md](findings.md)). Judge every candidate by one principle set: Kent Beck's Test Desiderata, especially "behavioral" and "structure-insensitive" [10], and Vladimir Khorikov's pillars: protection against regressions, resistance to refactoring, fast feedback, and maintainability [11]. Prefer state checks to interaction checks, real or fake collaborators to mocks, and descriptive and meaningful phrases (DAMP) to "don't repeat yourself" (DRY) in test bodies [2], [5].

### Strictness settings are off

- **Detect:** Read `[tool.pytest]` (pytest 9's native table in `pyproject.toml`), `[tool.pytest.ini_options]`, `pytest.toml`, `pytest.ini`, `tox.ini`, or `setup.cfg` for `strict`, `strict_markers`, `strict_config`, `strict_xfail` (alias `xfail_strict`), `strict_parametrization_ids`, `filterwarnings`, and `max_warnings`. Then run the strict probe (Measuring). A lab suite with a misspelt marker, an unknown configuration option, duplicate parametrize identifiers (IDs), a passing xfail, and a `Test*` class with `__init__` ran green by default ("6 passed, 1 xpassed, 3 warnings"). Each problem became an error under its option (verified with pytest 9.1.1).
- **False positives:** `strict = true` also turns on every strictness option that a later pytest adds, so on an unpinned pytest it can break CI at an upgrade [12]. `filterwarnings = error` without narrow ignores for third-party deprecations produces failures the team cannot fix. One duplicate parametrisation ID makes its whole module fail to collect, so a legacy suite adopts the options one at a time.
- **Fix:** Pin pytest and register every marker. Then set `strict = true`, or the four `strict_*` options one at a time. Add `filterwarnings = ["error", "ignore::DeprecationWarning:thirdparty.*"]` with narrow ignores, or start with pytest 9.1's `max_warnings = N` and lower N over time; a green run with more than N warnings exits with code 6 (verified) [12]. Add `"error::pytest.PytestCollectionWarning"` to `filterwarnings`, so a `Test*` class with `__init__` fails collection instead of vanishing.
- **Effect:** Without `strict_markers`, a mistyped mark such as `@pytest.mark.slwo` only warns, and the test escapes `-m "not slow"` deselection [12]. Without `strict_xfail`, a fixed bug stays marked as an expected failure ([redundancy.md](redundancy.md)). No prevalence study exists.
- **Verify:** The probe runs clean. A deliberately misspelt marker and an xfail test that passes each fail the run.

### Lint rules that find test bugs are not enforced

- **Detect:** Run the lint pass (Measuring) with and without `--isolated`. A command-line `--select` still honours the project's `per-file-ignores`, so a rule that fires only under `--isolated` is hidden by the configuration (verified with ruff 0.16.9). Ruff 0.16.0 enables 413 rules by default, including F631, F811, B015, B017, PGH005, PT014, and RUF018, but not B011, PT011, PT012, PT015, PT017, or PT018. A project with an explicit `select` list does not get the new defaults [13]. The rules that find real test bugs: F631, F811, B015, and PGH005 ([redundancy.md](redundancy.md)); B011 and PT015, because `assert False` disappears under `python -O`; RUF018, an assignment inside `assert`, which also disappears; PT017, an `assert` inside `except`; PT012, several statements inside `pytest.raises`, where an early one can raise the expected error; and B017 and PT011, a `pytest.raises` that is too broad: `Exception`, or a common exception with no `match`.
- **False positives:** Style rules dominate the counts and find no bugs: PT001, PT006, PT007, PT013, PT019, PT023, and PT018, whose composite asserts pytest's introspection already explains. pip had 198 PT006 hits [1]. S101 (use of `assert`) is noise in tests. B015 is often deliberate inside `pytest.raises(TypeError)`, to test that a comparison raises: 7 of 9 B015 hits in five mature projects were of this kind [1]. PT012 is harmless when the extra statements cannot raise. A bare `pytest.raises(ValueError)` is fine when the code can raise only one kind of `ValueError`.
- **Fix:** Ruff has per-file ignores but no per-file selects, so enable the rules project-wide and ignore them where they do not apply: `extend-select = ["PT", "B", "PGH005", "RUF018", "RUF043"]`, with `"tests/**" = ["S101", "PLR2004"]` under `[tool.ruff.lint.per-file-ignores]` [13]. Fix hits mechanically, one pull request per rule. When a legacy count is large, gate new code first.
- **Effect:** Each confirmed F631, F811, B015, or PGH005 hit is a test that can pass while the code is broken. Five mature projects that already run pyflakes-style checks had no F631, F811, or PGH005 hits. They had 9 B015 hits, of which 2 were real: a no-op `==` meant as `=`, and a no-op comparison that contradicts its comment. The four pytest-style projects had 10–92 PT011 hits each [1]. Less mature suites probably have more; nobody has measured it.
- **Verify:** CI enforces the rules on test paths, and the count stays at zero. For each fixed test, break the code in a disposable copy and confirm that the test fails.

### Autouse fixtures fan out to every test

- **Detect:** `static_scan.py`'s `autouse-fixtures` check lists each autouse fixture with its scope and about how many tests it reaches. An autouse fixture makes every fixture it requests effectively autouse too [12], so measure the closure (Measuring). The design probe prints fixtures per test and the fixtures that reach 90% or more of tests, without running tests. `results.py fixtures` prints setups per test and each fixture's setup cost from the baseline run. Report when a root-level autouse fixture patches, touches the file system or network, or pulls in more than a handful of fixtures, and setup is a large share of test time.
- **False positives:** Safety-net autouse fixtures are good design: environment isolation, network blocking, resetting global state, or a patch that stops real `git clone` calls, with an opt-out marker. The problem is cost and hidden dependencies, not autouse itself. Removing a safety net can bring back pollution between tests, so narrow it instead.
- **Fix:** In this order: move the fixture from the root conftest to the directory that needs it; make it request nothing heavy; turn "most tests need it" fixtures into explicit parameters or `@pytest.mark.usefixtures`, which document the dependency; and give each safety net an opt-out marker, for example `if request.node.get_closest_marker("real_git"): return` before `mocker.patch("myproj.vcs.clone", autospec=True)`. Scope and caching remedies are in [fixed-costs.md](fixed-costs.md).
- **Effect:** In poetry, six autouse fixtures in the root conftest pull 36 fixtures into at least 99.8% of tests. The median test sets up 42 fixtures (90th percentile 53, maximum 62), the longest dependency chain is 11 levels, and setup took 25% of test time in a 533-test sample [1]. The speed gain from narrowing depends on the setup cost.
- **Verify:** Rerun the probe and `results.py fixtures`: fixtures and setups per test fall. `results.py diff` shows the same tests and outcomes, and two runs in random order pass ([SKILL.md](../SKILL.md) phase 9).

### Patches and mocks without a specification

- **Detect:** The patch-spec counter (Measuring) counts `patch`, `patch.object`, and `mocker.patch` calls with no `autospec`, `spec`, `spec_set`, `new`, `new_callable`, or positional replacement. `static_scan.py` counts bare `Mock()` and `MagicMock()` calls without a spec as `mocks_without_spec` in its inventory. Report when most patches are unspecced and the patched collaborators are first-party code that changes. To find examples, sample tests whose collaborator's signature changed recently, with `git log -L :FUNCTION:PATH`.
- **False positives:** Patching a constant or an attribute with `new=` needs no spec. Autospec fails on attributes created in `__init__` unless you set them or give the class defaults, and it introspects the target, so properties with side effects can run [14]. Standard-library functions rarely change signature, so specs add little there.
- **Fix:** In this order: `autospec=True` on patched functions and methods, the cheapest fix, which catches renamed and removed parameters; `spec_set=Class` for class doubles, which also blocks setting attributes that do not exist; `unittest.mock.seal(m)`, which stops the automatic creation of child mocks; or a fake instead of the mock. With pytest-mock, use `mocker.patch(..., autospec=True)`: patches undo themselves, and using `mocker.patch` as a context manager warns [15]. Roll out one module at a time and run the suite after each batch, because autospec exposes latent test bugs.
- **Effect:** 67–94% of patch calls in five mature projects had no spec [1]. A plain `Mock` accepts any call, so a misspelt keyword such as `curency=` passes, while `autospec=True` raises `TypeError` (verified). No study measures the defects that autospec prevents; the mechanism is documented [14]. Measured cost of one patch start and stop on Python 3.14: plain 32 µs; autospec of a function 219 µs; method-level autospec 0.21 ms; `spec=Class` 0.43 ms; `create_autospec(instance=True)` 9.6 ms; autospec of a whole class, `argparse.ArgumentParser`, 18.9 ms [1]. Autospec does not catch swapped positional arguments of compatible types.
- **Verify:** In a disposable copy, rename a parameter of the collaborator and confirm that the mocked tests fail. Compare suite time before and after with `results.py diff`, 3 runs each.

### Patches that never take effect

- **Detect:** Detect this at runtime, not statically. The unused-patch plugin (Measuring) records every patch whose mock had no call during its test. Group the hits by target: targets that fixtures patch for every test show up as large counts. Report explicit-test patches with zero calls, after sampling: each is dead setup, a wrong target, or one of the false positives below. A static "the code imports this name, so you patched the wrong module" heuristic gave 13 leads and 0 real bugs in four projects, because it cannot see imports inside functions [1].
- **False positives:** A defensive patch in a parametrised test is legitimately unused for some parameters. A mock that stands in for an attribute that is only read records no call. A widely used standard-library name such as `os.path.exists` records calls from other code, including pytest itself, so "called" does not prove that the code under test used it.
- **Fix:** For a wrong target, patch where the name is looked up: `patch("pricing.fetch_rate")`, not `patch("rates.fetch_rate")`, when `pricing` did `from rates import fetch_rate` [14], [16]. Then assert on the mock or on the result, so that a wrong target fails the test. Better, inject the collaborator. Propose removing a dead patch only after you confirm that it is not mistargeted and that nothing reads it as an attribute; the tamper check still applies.
- **Effect:** In 1,596 poetry tests, 7,040 of 8,333 patch mocks were never called. Five targets that root-conftest fixtures patch for every test accounted for 6,967, and about 73 were leads in explicit tests [1]. In a lab suite, a test that patched the wrong module passed while the real function ran (verified).
- **Verify:** Rerun the plugin: the explicit-test count falls. For a retargeted patch, change the patched function's return value in a disposable copy and confirm that the test fails.

### Assertion helpers without assertion rewriting

- **Detect:** pytest rewrites `assert` only in test modules, conftest files, and modules registered with `pytest.register_assert_rewrite` or loaded through `pytest_plugins` [12]. List the other modules under the test roots that contain `assert`, then look for registrations. Both commands use only options that BSD and GNU grep share (verified on BSD grep); adjust the file pattern when the project sets `python_files`: `grep -rln --include='*.py' '^[[:space:]]*assert ' TEST_ROOTS | grep -v -E '(^|/)(test_[^/]*|[^/]*_test|conftest)\.py$'` and `grep -rn register_assert_rewrite ROOT`.
- **False positives:** Helpers that raise their own messages or call `pytest.fail(msg)` need no rewriting. Many helper asserts narrow types for the type checker, such as `assert x is not None`, rather than check behaviour.
- **Fix:** Call `pytest.register_assert_rewrite("tests.helpers")` in the root conftest before the helper is imported. Set `__tracebackhide__ = True` inside each helper, so failures point at the calling test.
- **Effect:** Without registration, a failing helper shows only `AssertionError`; with it, pytest shows `assert 36 == 37` and `where 36 = sum([12, 24])` (verified with pytest 9.1.1). This is the form Assertion Roulette takes under pytest.
- **Verify:** Make a helper assertion fail on purpose and read the failure report.

### Over-mocking and interaction-only tests

- **Detect:** `static_scan.py`'s `mock-density` check lists tests with five or more patches. That threshold is higher than Google's heuristic, which flags more than one or two mocked classes or stubbed methods [5]; in five mature projects, 0.2–3.7% of tests had three or more patches [1]. Also look for tests whose only checks are `assert_called*` or `mock_calls`, and for change-detector tests that assert the exact call sequence of collaborators [5]. Report when more than a few percent of tests match and mutation testing shows surviving mutants in those modules ([mutation-testing.md](mutation-testing.md)).
- **False positives:** Interaction checks are correct at boundaries between systems, such as sending an email or publishing a message; Khorikov calls these observable behaviour [17]. Command-style code with no return value may need them.
- **Fix:** In this order: use the real object for fast, deterministic first-party collaborators, because Google prefers "realism over isolation" [2]; use a fake that the collaborator's team owns, such as an in-memory repository; and assert on state or output rather than on calls. Google says change-detector tests "provide negative value" [5], but the fix is a rewrite; a removal is a `review-removal` candidate that needs two kinds of evidence ([traps.md](traps.md)).
- **Effect:** At Google, heavily mocked tests "required constant effort to maintain while rarely finding bugs", which led to `@DoNotMock` in Error Prone [2]. No controlled study measures the loss in defect detection. Global patching also blocks thread-parallel runs: pytest-run-parallel treats tests that use `monkeypatch`, and on some builds `unittest.mock`, as thread-unsafe [18].
- **Verify:** Run mutation testing on the module before and after the rewrite. The mutation score does not drop, and a pure refactor of the collaborator no longer breaks the test.

### Mocking what you do not own

- **Detect:** The patch-spec counter prints the top-level namespace of each string patch target. Anything outside the project's packages is standard library or third-party. In five mature projects, 4–22% of patch calls had such targets, mostly standard library: `os`, `sys`, `subprocess`, `builtins`, and `time` [1].
- **False positives:** Patching `time.sleep`, clocks, or randomness is usually fine, although `time-machine` or an injected clock is better. Patching your own thin wrapper around a library is the recommended pattern, not a smell.
- **Fix:** Follow "only mock types you own" [3]: write a thin adapter that expresses your abstraction, test it against the real library in a few integration tests, and fake the adapter everywhere else. For common libraries, use purpose-built doubles: `responses` (requests), `respx` (httpx), `pytest-httpserver`, `moto` (Amazon Web Services), and `time-machine` or `freezegun` (time); [framework-runtime.md](framework-runtime.md) covers them. Hynek Schlawack's worked example shows the business logic getting simpler, not only the tests [19].
- **Effect:** London-school test-driven development (TDD) and Google's classical style agree on this point, although they disagree about mocking first-party code [3], [2]. No quantitative study exists. Google notes that the engineer who writes a mock "usually did not write the thing being mocked and can be misinformed about its actual behavior" [2].
- **Verify:** In a disposable copy, upgrade the library or change its stub, and confirm that only the adapter's integration tests break.

### Conftest sprawl and fixture overrides

- **Detect:** `static_scan.py`'s output file lists `conftest_files` with their lines and fixtures, and its `unused-fixtures` check lists fixtures that nothing requests by name. `CI_TEST_COMMAND --fixtures -v`, run through `run_suite.py`, lists every fixture with its location; a name defined in several places is an override. Report when a conftest has more than about 500 lines or 30 fixtures, or overrides change behaviour by directory, and developers report confusion or you find a wrong-fixture bug.
- **False positives:** Overrides are a documented pytest feature [12]; a directory that overrides a plugin fixture on purpose is not sprawl. A fixture requested through `request.getfixturevalue()` is invisible to `--setup-plan`, `--fixtures-per-test`, pytest-deadfixtures, and the design probe; only `--setup-show`, which runs the tests, shows it (verified). pytest-deadfixtures reports such fixtures as unused [20]; unused fixtures are covered in [redundancy.md](redundancy.md).
- **Fix:** Split a large conftest by domain into plugin modules, loaded from the root conftest with `pytest_plugins = [...]`; those modules also get assertion rewriting [12]. Rename overrides that change meaning rather than configuration. Prefer explicit parameters, indirect parametrisation, or factory fixtures to `getfixturevalue()` [12].
- **Effect:** Measured root conftests: 1,133 lines and 58 fixtures (poetry), 1,076 lines and 30 fixtures (pip), and 809 lines and 19 fixtures (celery); poetry and celery each define 24–33 fixture names more than once [1]. No published effect size on maintenance cost exists. Since pytest 9.1, an overriding fixture resolves by its visibility in the collection tree before its registration order, which mainly affects plugins that register fixtures in code [12].
- **Verify:** After a split, `results.py diff` shows the same tests and outcomes.

### Test code the type checker skips

- **Detect:** Check whether the mypy configuration excludes tests or leaves `check_untyped_defs` at its default, false [21]. Then compare the error counts with and without `--check-untyped-defs` (Measuring): the difference is what mypy skips today. pyright checks unannotated functions by default (`analyzeUnannotatedFunctions`) [21].
- **False positives:** Mocks are `Any` to type checkers, so typing tests does not catch mock misuse: neither mypy nor pyright flagged a misspelt method on `Mock(spec=Gateway)` (verified). Many new errors in tests are missing stubs or untyped fixtures, not bugs.
- **Fix:** Set `check_untyped_defs = true` for tests in mypy, or run pyright on them. pytest's documentation names refactoring support as the main benefit of typing tests [12]. Record a baseline of existing errors and gate new code first.
- **Effect:** A test that calls `charge(500, "acct")` against `charge(account_id: str, amount_cents: int)` passed mypy 2.3.1 as "Success". With `--check-untyped-defs`, mypy reported two `arg-type` errors, and pyright 1.1.414 reported both by default (verified).
- **Verify:** The type checker runs on test paths in CI, and the error count trends to zero.

### Suite shape and test sizes

- **Detect:** Measure count and time per tier, and state the definition you used (Measuring). Tiers come from directories, from markers, or from the resources that a test's fixtures use. Google defines sizes by resources: small tests use no network, database, file system, threads, or sleep (60 s limit); medium tests may use localhost only (300 s); large tests may use anything (900 s and more) [5], [22]. To find tests that reach the network, run a sample with pytest-socket (`--disable-socket --allow-hosts=127.0.0.1`), installed only in an isolated environment [23].
- **False positives:** Shape depends on the definition. In poetry, marker and fixture rules put 100% of tests in the small tier, yet every test has `tmp_path` in its closure through autouse fixtures, so under Google's "no file system" rule all of them are medium [1]. Martin Fowler notes that "unit test" has many definitions and that the pyramid-versus-honeycomb debate is mostly about them [24]. Libraries and command-line tools naturally have few large tests.
- **Fix:** Report the definition, the counts, and the time per tier. Recommend a change only where the largest tier by time is slow and flaky and duplicates checks that a lower tier could make. Move those checks down, and keep the only end-to-end test of each behaviour. Present shape changes as programmes that take several quarters. Running a tier later or less often is covered in [scheduling.md](scheduling.md).
- **Effect:** Do not enforce 70/20/10 or 80/15/5 ratios. Google calls them rough guides [5], [2], and a study of 38,782 Java tests found no evidence that unit and integration tests detect different kinds of defect [4]. Microsoft replaced 27,000 legacy functional tests over 42 sprints, about 2.5 years, and now runs 60,000 unit tests in parallel in under 6 minutes, with L0 tests averaging under 60 ms and no unit test over 2 s; it calls this a "massive investment" [25]. Spotify's honeycomb for microservices accepted suites going "from milliseconds to a few seconds" [26]. Neither is a controlled comparison.
- **Verify:** Measure count and time per tier again. Use escaped-defect or incident data where the team has it, because a tier ratio is not an outcome.

### Broad integration tests at service boundaries

- **Detect:** Look for large-tier tests that start or call other services, share a staging environment, or fail when a partner service deploys ([ci-history.md](ci-history.md)), and for tests that check only the response shape of another team's API.
- **False positives:** Contract tests do not test side effects or functional behaviour [27]. Pact fits internal services whose teams talk to each other. It is a poor fit for public APIs, pass-through services, and test data you cannot control [27].
- **Fix:** Replace response-shape checks with consumer-driven contracts (pact-python) that the provider's pipeline verifies. Generate schema-conformance and server-error tests from OpenAPI or GraphQL schemas with Schemathesis (`schemathesis run SCHEMA_URL`), against a local instance only [6]. Keep a few end-to-end journeys. Each broad test stays until a contract check has caught a deliberate break.
- **Effect:** The Schemathesis paper reports 1.4× to 4.5× more unique defects than the second-best fuzzer across 16 services [6]. No published case study gives numbers for replacing end-to-end tests with contracts, and none says whether it reduces flakiness.
- **Verify:** A deliberate breaking change to a provider response, in a disposable copy, fails the contract check before deployment.

### `unittest.TestCase` hierarchies and mixed styles

- **Detect:** The design probe prints test classes by in-repository inheritance depth, with the three deepest (Measuring). Also look for chained `super().setUp()` calls and for files that mix `TestCase` classes with pytest fixtures; ruff PT009 and PT027 counts show how much unittest-style assertion remains. Do not flag depth alone: of Django's 18,132 test methods, only 10 classes are three or more levels deep [1].
- **False positives:** Inheritance that reruns a base class's tests against a subclass is a deliberate contract-test pattern. Framework base classes such as `django.test.TestCase` add transaction rollback and are not a smell.
- **Fix:** Report chained `setUp` methods that build shared mutable state, and mixins that add setup invisibly. For new tests, prefer pytest functions with explicit fixtures: pytest cannot inject fixtures into `TestCase` methods or parametrise them, and only autouse fixtures and `usefixtures` work there [12]. pytest 9.0 supports `TestCase.subTest()` [12]. Python 3.12 removed aliases such as `assertEquals` and `failUnless` [28]; ruff UP005 rewrites them. A migration buys plain `assert` with introspection, fixtures, `parametrize`, and pytest plugins; it costs review time and risks changes in meaning, and no case study gives numbers. If the team migrates, convert one directory per pull request and verify each conversion (Measuring).
- **Effect:** Django has 1,779 classes at depth 1, 218 at depth 2, 9 at depth 3, and 1 at depth 4; certbot has 150 and 5 [1]. Both converters left something broken in testing [29], [30]. unittest2pytest 0.5 from PyPI crashes on Python 3.13 and later, because `lib2to3` was removed; its `main` branch works and keeps `setUp`. pytestify 1.5.0 removed the `TestCase` base but left `self.assertRaisesRegex`, which then failed with `AttributeError`; in a lab suite it also renamed the class, which changes node IDs (verified). `assertAlmostEqual` checks 7 decimal places absolutely, while `pytest.approx` is relative (1e-6) by default: 1,000,000.5 against 1,000,000.0 fails the first and passes the second (verified). Dropping `django.test.TestCase` drops per-test transaction rollback, and `setUpClass`, `addCleanup`, and class-level `patch` decorators need manual handling. Ruff's PT009 and PT027 fixes are unsafe-only and keep the class.
- **Verify:** When you flatten a hierarchy, compare the collected node IDs. Inherited tests multiply test counts, so flattening can reduce them; check that each removed ID was a rerun, not a unique case.

### Catalogue smell counts

- **Detect:** Do not run a catalogue detector for counts. When the user asks about a catalogue smell, sample by hand and map it with the table below. Test names and structure are low priority: mention them only with a concrete example that confused a reader [2].
- **False positives:** Most flags are not real problems. Panichella et al. found Eager Test in about 80% of 49 developer-written suites, but 35 of the 39 flagged suites were semantically coherent, and they call Assertion Roulette "generally obsolete" [7]. PyNose's own later version disables Assertion Roulette, Conditional Test Logic, Magic Number Test, Obscure In-Line Setup, Lack of Cohesion, Redundant Print, Sleepy Test, and Test Maverick by default [31].
- **Fix:** Replace smell counts with the high-precision signals on this page, using the table below.
- **Effect:** Spadini et al. found smelly tests 1.47× more change-prone and 1.95× more defect-prone, and production code under smelly tests 1.71× more defect-prone, according to the authors' slides [32]. That is correlation only, and developers and later manual validation did not see most flagged smells as problems [7], [33]. Do not claim that smells cause flakiness: the two widely cited studies, with 54% and 75% co-occurrence, are retracted [34].
- **Verify:** Not applicable: the point is not to report them.

| Catalogue smell [35], [36] | Auditor action |
| --- | --- |
| General Fixture | Its pytest form is the autouse closure; a count per class is noise |
| Assertion Roulette | Noise under assertion rewriting, except in unregistered helper modules and bare `self.assertTrue(x)` |
| Eager Test, Lazy Test, Indirect Testing | Mostly noise [7]; report only a test that checks unrelated behaviours, with the example |
| Conditional Test Logic | Report only an `if` that can skip every check, a loop of asserts that should be `parametrize`, and a `try`/`except` that swallows `AssertionError` (ruff S110) [5] |
| Magic Number Test | Noise; literal expected values are the DAMP style [5] |
| Constructor Initialization, Unknown Test, Empty Test | Real problems: a `Test*` class with `__init__` never runs, and a test with no check verifies nothing ([redundancy.md](redundancy.md), [coverage.md](coverage.md)) |
| Mystery Guest, Sleepy Test, Erratic Test | Static detection is unreliable; detect them at runtime ([flakiness.md](flakiness.md)) |

## Measuring

### Sample hits before you report

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py --examples 100000 --json-out AUDIT/static-all.json
python3 - AUDIT/static-all.json mock-density <<'EOF'
import json, random, sys
check = json.load(open(sys.argv[1]))["checks"].get(sys.argv[2], {"count": 0, "examples": []})
random.seed(1)
print(f"{check['count']} hits; random sample:", *random.sample(check["examples"], min(5, len(check["examples"]))), sep="\n  ")
EOF
```

`--examples` keeps only the first N hits in scan order, so keep them all and sample from them; record the seed in the evidence note. Write to a new file, because `AUDIT/static.json` stays the "before" side of the tamper check. For ruff hits, list them with `--output-format concise` and sample the lines the same way. Cost: seconds; no project code runs.

### Lint pass on test code

```sh
uvx ruff check --isolated --no-cache --exit-zero --statistics --select F631,F811,B011,B015,B017,PGH005,RUF018,PT011,PT012,PT015,PT017 TEST_ROOTS
uvx ruff check --no-cache --exit-zero --statistics --select F631,F811,B011,B015,B017,PGH005,RUF018,PT011,PT012,PT015,PT017 TEST_ROOTS
```

Each output line is `count code name`. A rule that appears only in the first run is hidden by the project's `per-file-ignores`. `--isolated` also ignores the project's `exclude` setting, so drop hits in vendored or generated files. Then read the project's ruff configuration to see which rules it already enforces. Cost: 0.03–0.18 s on five mature suites of up to 18,132 tests [1].

### Strict probe

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label strict-probe --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND --strict --collect-only -q -W error::pytest.PytestCollectionWarning
```

Like every `run_suite.py` command on this page, it runs project code, so ask first ([SKILL.md](../SKILL.md) guardrail 2). `output.log` names each problem: an unknown marker ("'slwo' not found in `markers` configuration option"), "Duplicate parametrization IDs detected", "ERROR: Unknown config option: NAME" (exit code 4), and each uncollectable class. A module that fails on one check hides its other problems, so for a full list, repeat the probe with one option at a time: `-o strict_markers=true`, `-o strict_parametrization_ids=true`, or `-o strict_config=true`. When the probe finds problems, it exits non-zero and `run_suite.py` does not report it as COMPLETE; the errors in `output.log` are the evidence. On pytest 8 and older, `--strict` means only `--strict-markers` [12]. For XPASS counts, read the baseline: with `--timing-plugin`, `results.py summary` lists `xpassed` among the outcomes (verified), and [redundancy.md](redundancy.md) says what to do with them. Cost: one collection.

### Fixture fan-out, suite shape, and class depth

At runtime, from the baseline run's `fixtures-*.json` files, which `--timing-plugin` wrote ([SKILL.md](../SKILL.md) phase 6):

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py fixtures AUDIT/runs/NN-baseline --top 20 --json-out AUDIT/results/fixtures.json
```

It prints the total fixture setup time and "function-scoped fixture setups per test", a mean that root autouse fixtures inflate. For each fixture, it prints total, setups, mean, and maximum setup time, scope, and where the fixture is defined; a fixture's time excludes the fixtures it depends on. A function-scoped fixture whose setups equal the number of tests reaches every test. It also flags function-scoped fixtures set up 100 or more times at 20 ms or more each, and session fixtures that each worker pays for at 2 s or more. Parametrize arguments appear as pseudo-fixtures with no cost. Cost: nothing beyond the baseline run.

At collection, without running tests: save this as `AUDIT/plugins/design_probe.py`, and edit `TIERS` after you sample the project's markers and fixtures.

```python
# design_probe.py: fixture fan-out, size tiers, and test-class depth at collection time; runs no test
import json, os, re, statistics, sys
from collections import Counter
SKIP = {"request", "pytestconfig", "tmp_path_factory", "tmpdir_factory", "worker_id", "testrun_uid"}
TIERS = [  # first match wins; edit the markers and fixture patterns after sampling the project
    ("large", {"e2e", "browser", "system"}, re.compile(r"^(page|browser|selenium|driver|live_server)$")),
    ("medium", {"integration", "django_db", "db"}, re.compile(r"^(db|transactional_db|.*_container|httpserver)$")),
]
def pytest_collection_finish(session):
    root = str(session.config.rootpath)
    def own(cls):  # defined under the rootdir, and not in a virtual environment inside it
        path = getattr(sys.modules.get(cls.__module__), "__file__", None) or ""
        return path.startswith(root) and "site-packages" not in path
    sizes, fan_in, tier, depth = [], Counter(), {}, {}
    for item in session.items:
        params = getattr(getattr(item, "callspec", None), "params", {})
        names = set(getattr(item, "fixturenames", ())) - SKIP - set(params)
        marks = {m.name for m in item.iter_markers()}
        sizes.append(len(names))
        fan_in.update(names)
        tier[item.nodeid] = next((t for t, mk, fx in TIERS if marks & mk or any(map(fx.match, names))), "small")
        if getattr(item, "cls", None) is not None:  # in-repo classes in the MRO: 1 = no in-repo base class
            depth[f"{item.cls.__module__}.{item.cls.__qualname__}"] = sum(map(own, item.cls.__mro__))
    n, sizes = len(sizes) or 1, sorted(sizes) or [0]
    say = session.config.pluginmanager.get_plugin("terminalreporter").write_line
    say(f"probe: {len(tier)} tests; fixtures per test median {statistics.median(sizes)}, p90 {sizes[int(0.9 * (len(sizes) - 1))]}, max {sizes[-1]}")
    say("fixtures in >= 90% of tests: " + (", ".join(f for f, c in fan_in.most_common() if c / n >= 0.9) or "none"))
    say("tiers by count: " + ", ".join(f"{t} {c}" for t, c in Counter(tier.values()).most_common()))
    if os.environ.get("DESIGN_PROBE_TIMING"):  # a baseline run's timing.jsonl adds time per tier
        secs = Counter()
        for line in open(os.environ["DESIGN_PROBE_TIMING"]):
            row = json.loads(line)
            secs[tier.get(row["nodeid"], "not collected now")] += row["duration"]
        say("tiers by time: " + ", ".join(f"{t} {s:.1f}s" for t, s in secs.most_common()))
    deepest = sorted(depth.items(), key=lambda kv: -kv[1])[:3]
    say(f"test classes by in-repo depth: {dict(sorted(Counter(depth.values()).items()))}; deepest: {deepest}")
    if os.environ.get("DESIGN_PROBE_OUT"):
        with open(os.environ["DESIGN_PROBE_OUT"], "w") as fh:
            json.dump({"tier": tier, "fan_in": dict(fan_in.most_common()), "class_depth": depth}, fh)
```

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label design-probe --timeout 900 --cwd ROOT \
    --env PYTHONPATH=AUDIT/plugins --env DESIGN_PROBE_OUT=AUDIT/design-probe.json \
    --env DESIGN_PROBE_TIMING=AUDIT/runs/NN-baseline/timing.jsonl -- CI_TEST_COMMAND --collect-only -q -p design_probe
```

`output.log` gets five lines: fixtures per test (median, 90th percentile as p90, and maximum); the fixtures in 90% or more of tests, which are effectively global; tiers by count; tiers by time, from the baseline; and test classes by in-repository depth in the method resolution order (MRO), where 1 means no in-repository base class. `AUDIT/design-probe.json` holds each test's tier and each class's depth. Cost: one collection. On poetry it took 2.2 s and printed a median of 41 fixtures per test (verified). A version that also counts parametrize arguments and xdist's `worker_id` and `testrun_uid` printed the 42 quoted above, and `--setup-plan` took 84 s on the same suite [1]. If CI sets `PYTHONPATH`, add its value after a colon. The probe reads `item.fixturenames`, which plugins use widely but pytest's API reference does not list, so check it on the project's pytest version. It misses fixtures requested through `getfixturevalue()`. For one test's fixtures with their locations, run `CI_TEST_COMMAND --fixtures-per-test PATH::TEST` through `run_suite.py`, without `-q`, which hides the output.

When tiers map to directories, such as `tests/unit` and `tests/integration`, count and time them from existing files instead:

```sh
grep '::' AUDIT/nodeids.txt | cut -d: -f1 | cut -d/ -f1-2 | sort | uniq -c | sort -rn | head -20
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary AUDIT/runs/NN-baseline --depth 2 --top 20 --json-out AUDIT/results/shape.json
```

The first command counts collected tests per directory, two levels deep. The second prints "heaviest directories" with seconds, share of test time, and test count.

### Patch specs, patch targets, and autospec cost

Save this as `AUDIT/plugins/patch_specs.py`:

```python
# patch_specs.py TEST_ROOT...: patch calls with no spec or replacement, and top patch-target namespaces
import ast, sys
from collections import Counter
from pathlib import Path
SPEC = {"autospec", "spec", "spec_set", "new", "new_callable"}
dotted = lambda n: f"{dotted(n.value)}.{n.attr}" if isinstance(n, ast.Attribute) else getattr(n, "id", "")
calls, targets = Counter(), Counter()
for path in (p for root in sys.argv[1:] for p in Path(root).rglob("*.py")):
    try:
        tree = ast.parse(path.read_text(errors="replace"))
    except SyntaxError:
        calls["parse errors"] += 1
        continue
    for node in ast.walk(tree):
        name = dotted(node.func) if isinstance(node, ast.Call) else ""
        if name in ("patch", "patch.object") or name.endswith(("mock.patch", "mocker.patch", "mock.patch.object", "mocker.patch.object")):
            new_at = 2 if name.endswith("object") else 1  # a positional `new` argument replaces the mock
            calls["specced" if len(node.args) > new_at or any(k.arg in SPEC for k in node.keywords) else "no spec"] += 1
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                targets[node.args[0].value.split(".")[0]] += 1
print(dict(calls), "\ntop patch-target namespaces:", targets.most_common(12))
```

```sh
python3 AUDIT/plugins/patch_specs.py TEST_ROOTS
```

It prints the `no spec` and `specced` counts and the 12 most patched top-level namespaces. The project's own package usually leads; the rest are standard library or third-party. It parses the files as an abstract syntax tree (AST) and imports nothing. It also counts conftest files and helpers, so its share differs a little from a count over test functions only: 80% for pip, where a scan of test functions only found 81% [1]. Cost: about 1 s for 1,500–4,000 tests.

To measure what autospec costs for the project's own collaborators:

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label autospec-cost --timeout 300 --cwd ROOT -- \
    python -m timeit -s "from unittest import mock" "mock.patch('PKG.MODULE.NAME', autospec=True).start(); mock.patch.stopall()"
```

Run it with the project's Python, then again without `autospec=True` for the plain cost. `timeit` prints the best time per loop. It imports the target, which runs project code, so ask first, as for any run. `run_suite.py` finds no test summary in its output, so the verdict is not COMPLETE; take the number from `output.log`. On Python 3.14 it printed about 215 µs per loop for a function and 18.4 ms for `argparse.ArgumentParser` (verified), in line with the costs under [Patches and mocks without a specification](#patches-and-mocks-without-a-specification). Multiply by the number of patches per run, from the unused-patch plugin's total, before you recommend blanket autospec.

### Unused patches at runtime

Save this as `AUDIT/plugins/unused_patch.py`:

```python
# unused_patch.py: patches whose mock recorded no call during the test; relies on private mock._patch
import json, os, types
from collections import Counter
from unittest import mock
import pytest
current, found, total = {"id": None}, [], Counter()
enter0, exit0 = mock._patch.__enter__, mock._patch.__exit__
def enter(self):
    result = enter0(self)
    inner = getattr(result, "mock", None) if isinstance(result, types.FunctionType) else result  # autospec
    self._audit_mock = inner if isinstance(inner, mock.NonCallableMock) else None
    return result
def exit_(self, *exc):
    m = getattr(self, "_audit_mock", None)
    if m is not None and current["id"]:
        total["patches"] += 1
        if not m.mock_calls and not m.called:  # an awaited AsyncMock was called first
            found.append((current["id"], f"{getattr(self.target, '__name__', '?')}.{self.attribute}"))
    return exit0(self, *exc)
mock._patch.__enter__, mock._patch.__exit__ = enter, exit_
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    current["id"] = item.nodeid
    yield
    current["id"] = None
def pytest_terminal_summary(terminalreporter):
    if os.environ.get("UNUSED_PATCH_OUT"):
        with open(os.environ["UNUSED_PATCH_OUT"], "w") as fh:
            json.dump({"patches": total["patches"], "never_called": found}, fh, indent=1)
    terminalreporter.write_line(f"patch mocks: {total['patches']}; never called: {len(found)}")
    for target, n in Counter(t for _, t in found).most_common(10):
        terminalreporter.write_line(f"{n:6d}  {target}")
```

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label unused-patches --timeout SECONDS --cwd ROOT \
    --env PYTHONPATH=AUDIT/plugins --env UNUSED_PATCH_OUT=AUDIT/unused-patches.json -- CI_TEST_COMMAND -p unused_patch -n 0 TEST_DIR
```

It prints `patch mocks: N; never called: M` and the 10 most frequent never-called targets; `AUDIT/unused-patches.json` lists each (test ID, target) pair for sampling. It covers `mock.patch`, `patch.object`, `mocker.patch`, and autospecced functions and methods, and it ignores patches whose replacement is not a mock. Add `-n 0` when the command uses xdist: the workers keep the data, so the controller reports 0 patches (verified). It runs tests, so it needs the user's agreement like any run, and its timings are not evidence. It relies on the private `unittest.mock._patch` class, so use it only in audits. On a slow suite, run it one directory at a time.

### Type-checking probe

```sh
uvx mypy --python-executable PROJECT_PYTHON --cache-dir AUDIT/mypy-cache TEST_ROOTS | tail -1
uvx mypy --python-executable PROJECT_PYTHON --cache-dir AUDIT/mypy-cache --check-untyped-defs TEST_ROOTS | tail -1
uvx pyright --pythonpath PROJECT_PYTHON TEST_ROOTS | tail -1
```

`PROJECT_PYTHON` is the interpreter that `CI_TEST_COMMAND` uses. Type checkers read code without running it. `--python-executable` and `--pythonpath` let a checker from an isolated environment find the project's installed packages, and `--cache-dir` keeps mypy's cache out of the project. Run from ROOT, so mypy reads the project's own configuration. Each last line gives the error count; the difference between the two mypy counts is what mypy skips. Cost: seconds to minutes, depending on suite size.

### Verify a unittest-to-pytest conversion

Convert one directory at a time on a branch, as [SKILL.md](../SKILL.md) phase 9 requires, with the converter in a throwaway environment outside the project:

```sh
python3 -m venv AUDIT/u2p && AUDIT/u2p/bin/pip install git+https://github.com/pytest-dev/unittest2pytest@main
AUDIT/u2p/bin/unittest2pytest -w -n TEST_DIR
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label converted --timeout SECONDS --cwd ROOT -- \
    CI_TEST_COMMAND --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py diff --before AUDIT/runs/NN-baseline --after AUDIT/runs/MM-converted
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py --json-out AUDIT/static-after.json
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py diff AUDIT/static.json AUDIT/static-after.json
```

`-w` writes the files and `-n` skips backups. Accept the conversion only when `results.py diff` reports the same tests and outcomes, `static_scan.py diff` reports no weakening, and two runs in random order pass. Renamed test IDs hide outcome changes from the diff: in a lab suite, pytestify renamed a class, and `results.py diff` showed "4 disappeared, 4 appeared, 0 changed outcome" while 2 converted tests failed, so also read the converted run's own counts. A loosened check changes no outcome, so review each `pytest.approx` and `assertAlmostEqual` conversion by hand, or run mutation testing on the covered module ([mutation-testing.md](mutation-testing.md)). In the same lab suite, unittest2pytest's `main` branch kept every ID and outcome, and the tamper check was clean (verified).

## Tools

| Tool | Use it for | Status (version, date, maintained), checked on 2026-09-30 [37] | Notes |
| --- | --- | --- | --- |
| pytest built-ins | `--fixtures -v`, `--fixtures-per-test`, `--setup-plan`, `--setup-show`, `--strict`, `max_warnings` | 9.1.1, 2026-06-19, maintained | Static views miss `getfixturevalue()`; `--setup-plan` took 84 s on poetry |
| ruff | Lint rules for tests | 0.16.9, 2026-09-24, maintained | 0.16.0 changed the defaults to 413 rules; PT style rules are noisy |
| pytest-mock | `mocker.patch(..., autospec=True)`, `mocker.spy` | 3.16.0, 2026-09-27, maintained | Warns when `mocker.patch` is used as a context manager [15] |
| pytest-deadfixtures | Unused and duplicate fixtures | 3.1.0, 2026-01-15, maintained; works with pytest 9.1.1 on Python 3.14 | False positives for dynamic lookup and plugins; `--dup-fixtures` compares truthy return values only; exits with code 11 when it finds a dead fixture [20] |
| mypy | Type-check tests | 2.3.1, 2026-08-15, maintained | Skips unannotated function bodies unless `check_untyped_defs` is set |
| pyright | Type-check tests | 1.1.414, 2026-09-10, maintained | Checks unannotated functions by default; mocks are `Any` |
| unittest2pytest | Convert `self.assert*` calls | 0.5, 2024-12-11; dependency updates only | The PyPI release crashes on Python 3.13+; install `main`; keeps `setUp` [29] |
| pytestify | Convert classes, `setUp`, and asserts | 1.5.0, 2023-06-04; partly maintained | Renamed a class; left `assertRaisesRegex`; `approx` changes tolerance [30] |
| pytest-socket | Find tests that reach the network | 0.8.1, 2026-08-19, maintained | Works at socket level only [23] |
| pact-python | Consumer-driven contract tests | 3.4.1, 2026-09-17, maintained | Poor fit for public APIs [27] |
| Schemathesis | Tests generated from API schemas | 4.28.0, 2026-09-22, maintained | Needs an accurate schema; run against local instances only [6] |
| PyNose, TEMPY, pytest-smell, tsDetect, pytest-tidy | Smell detectors | Research tools with no activity since 2022; pytest-tidy 0.1.0 (2026-07-15) has one release | Do not base recommendations on them; ruff covers most of pytest-tidy [31], [35] |
| Other ecosystems | eslint-plugin-jest 29.16.6 (`valid-expect`, `no-standalone-expect`, `no-conditional-expect`, `no-identical-title`, `expect-expect`); Mockito `Strictness.STRICT_STUBS`, which fails a test with unused stubs; Error Prone `@DoNotMock`; RSpec `verify_partial_doubles` | Current documentation | JavaScript, Java virtual machine (JVM), and Ruby equivalents of the vacuous-check, unused-patch, over-mocking, and spec signals [38], [39], [2], [40] |

## Evidence

- Panichella et al. 2022: the older detector "misclassified over 70% of test smells"; in 49 developer-written suites, Eager Test recall was 0.39 and 35 of 39 flagged suites were coherent; "many test smells (as currently defined and detected) do not reflect real concerns" [7].
- Wang et al. 2021 (PyNose): 248 Python projects with 96,736 tests; 98% of projects had a smell; Assertion Roulette in 89.9% of projects, Conditional Test Logic 89.5%, Magic Number Test 79.8%, General Fixture 75.4% [8].
- Tufano et al. 2016: developers saw a design problem in 17 of 95 smell instances and no benefit in refactoring in 91%; a smell had an 80% chance of surviving 1,000 days [33].
- Spadini et al. 2018: 221 releases of 10 Java systems; smelly tests 1.47× more change-prone and 1.95× more defect-prone, from the authors' slides; observational, and it does not show that removing smells helps [32].
- Palomba and Zaidman's 2017 and 2019 papers on smells and flakiness are both retracted; do not repeat "54% of flaky tests contain a smell" or "75% co-occurrence" [34].
- Sadowski et al. 2015 (Tricorder): Google keeps analyses below 10% effective false positives and shows them only on changed lines [9].
- Software Engineering at Google: heavily mocked tests "required constant effort to maintain while rarely finding bugs"; Google now prefers real implementations, then fakes [2].
- Trautsch et al. 2020: 38,782 Java tests classified as unit or integration tests; no evidence that one type detects different kinds of defect [4].
- Microsoft Azure DevOps: legacy functional tests fell from 27,000 to 14,000 between sprints 78 and 101 and to zero by sprint 120; 60,000 unit tests run in under 6 minutes; a pull request takes about 30 minutes to merge [25].
- Hatfield-Dodds and Dygalo (Schemathesis): 1.4× to 4.5× more unique defects than the second-best fuzzer across 16 services [6].
- A vendor page claims "80% faster feedback, 70% lower testing costs, and 90% fewer production defects" for pyramid-shaped suites without a source; treat such numbers as folklore [41].
- Scans of pip, poetry, certbot, celery, and Django at fixed commits: patches without a spec 67–94%; tests with no recognisable check 0.3–6.5%; tests with three or more patches 0.2–3.7%; poetry's median test sets up 42 fixtures, and setup is 25% of test time; 7,040 of 8,333 poetry patch mocks never called; a static wrong-target heuristic gave 13 leads and 0 bugs [1].

## Sources

1. https://github.com/pypa/pip (a7002c9), https://github.com/python-poetry/poetry (d4fd21e), https://github.com/certbot/certbot (4856493), https://github.com/celery/celery (57cfb46), https://github.com/django/django (5a4511a) – five mature open-source suites, scanned and partly run at these commits for this skill's research; they are the source of the measured prevalence and cost numbers on this page.
2. https://abseil.io/resources/swe-book/html/ch11.html (Testing Overview), https://abseil.io/resources/swe-book/html/ch12.html (Unit Testing), https://abseil.io/resources/swe-book/html/ch13.html (Test Doubles), and https://abseil.io/resources/swe-book/html/ch14.html (Larger Testing) – Software Engineering at Google, chapters 11–14. Primary.
3. http://jmock.org/oopsla2004.pdf – Freeman et al., "Mock Roles, not Objects", OOPSLA 2004. Primary.
4. https://www.swe.informatik.uni-goettingen.de/node/2878 – Trautsch et al., "Are unit and integration test definitions still valid for modern Java projects?", JSS 2020 (abstract). Primary.
5. https://testing.googleblog.com/2010/12/test-sizes.html (test sizes), https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html (70/20/10), https://testing.googleblog.com/2013/05/testing-on-toilet-dont-overuse-mocks.html (mock overuse), https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html (change-detector tests), https://testing.googleblog.com/2014/07/testing-on-toilet-dont-put-logic-in.html (logic in tests), and https://testing.googleblog.com/2019/12/testing-on-toilet-tests-too-dry-make.html (DAMP versus DRY) – Google Testing Blog. Primary.
6. https://schemathesis.readthedocs.io/en/stable/ and https://arxiv.org/abs/2112.10328 – Schemathesis documentation and Hatfield-Dodds and Dygalo, "Deriving Semantics-Aware Fuzzers from Web API Schemas". Primary.
7. https://doi.org/10.1007/s10664-022-10207-5 (PDF https://pure.tudelft.nl/ws/portalfiles/portal/137994226/s10664_022_10207_5.pdf) – Panichella et al., "Test smells 20 years later", EMSE 2022. Primary.
8. https://arxiv.org/abs/2108.04639 – Wang et al., "PyNose: A Test Smell Detector For Python", ASE 2021. Primary.
9. https://research.google.com/pubs/archive/43322.pdf – Sadowski et al., "Tricorder: Building a Program Analysis Ecosystem", ICSE 2015. Primary.
10. https://testdesiderata.com/ – Kent Beck, Test Desiderata. Primary.
11. https://notesbylex.com/four-pillars-of-good-unit-tests – summary of Khorikov's four pillars. Secondary.
12. https://docs.pytest.org/en/stable/changelog.html (9.0 and 9.1 release notes), https://docs.pytest.org/en/stable/reference/reference.html (`strict`, `strict_*`, `filterwarnings`, `max_warnings`), https://docs.pytest.org/en/stable/how-to/fixtures.html (autouse, overrides, factories), https://docs.pytest.org/en/stable/how-to/unittest.html (unittest support and its limits), https://docs.pytest.org/en/stable/how-to/assert.html (assertion rewriting), https://docs.pytest.org/en/stable/how-to/mark.html and https://docs.pytest.org/en/stable/how-to/skipping.html (unknown marks, XPASS), and https://docs.pytest.org/en/stable/explanation/types.html (typing tests) – pytest documentation. Primary.
13. https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md and https://docs.astral.sh/ruff/rules/ – ruff 0.16.0 default-rule change and rule documentation. Primary.
14. https://docs.python.org/3.14/library/unittest.mock.html – unittest.mock documentation (autospec, where to patch, `unsafe`, `seal`). Primary.
15. https://pytest-mock.readthedocs.io/en/latest/usage.html and https://pytest-mock.readthedocs.io/en/latest/changelog.html – pytest-mock usage and releases. Primary.
16. https://nedbatchelder.com/blog/201908/why_your_mock_doesnt_work.html – Ned Batchelder, where to patch. Primary (practitioner).
17. https://enterprisecraftsmanship.com/posts/when-to-mock/ – Vladimir Khorikov, "When to Mock". Primary.
18. https://pypi.org/project/pytest-run-parallel/ – pytest-run-parallel thread-unsafe fixtures. Primary.
19. https://hynek.me/articles/what-to-mock-in-5-mins/ – Hynek Schlawack, "Don't Mock What You Don't Own in 5 Minutes", 2022. Primary (practitioner).
20. https://github.com/jllorencetti/pytest-deadfixtures – pytest-deadfixtures README and releases. Primary.
21. https://mypy.readthedocs.io/en/stable/config_file.html (`check_untyped_defs`) and https://github.com/microsoft/pyright/blob/main/docs/configuration.md (`analyzeUnannotatedFunctions`) – mypy and pyright configuration defaults. Primary.
22. https://bazel.build/reference/test-encyclopedia – Bazel test sizes and timeouts. Primary.
23. https://github.com/miketheman/pytest-socket – pytest-socket flags. Primary.
24. https://martinfowler.com/articles/2021-test-shapes.html – Martin Fowler, "On the Diverse And Fantastical Shapes of Testing". Primary (opinion).
25. https://learn.microsoft.com/en-us/devops/develop/shift-left-make-testing-fast-reliable – Microsoft, shift-left case study. Primary.
26. https://engineering.atspotify.com/2018/01/testing-of-microservices – Spotify, testing honeycomb. Primary.
27. https://docs.pact.io/getting_started/what_is_pact_good_for – Pact fit and non-fit. Primary.
28. https://docs.python.org/3/whatsnew/3.12.html – removal of unittest aliases in 3.12. Primary.
29. https://github.com/pytest-dev/unittest2pytest and https://github.com/pytest-dev/unittest2pytest/issues/82 – unittest2pytest and the `lib2to3` issue. Primary.
30. https://github.com/dannysepler/pytestify – pytestify. Primary.
31. https://github.com/JetBrains-Research/PyNose – PyNose repository and README (default-disabled inspections, last commit 2022-02-23). Primary.
32. https://www.slideshare.net/DavideSpadini/on-the-relation-of-test-smells-to-software-code-quality and https://research.tudelft.nl/en/publications/on-the-relation-of-test-smells-to-software-code-quality/ – Spadini et al., ICSME 2018 (author slides and record). Primary.
33. https://www.cs.wm.edu/~denys/pubs/ASE'16-TestSmells.pdf – Tufano et al., "An empirical investigation into the nature of test smells", ASE 2016. Primary.
34. https://api.crossref.org/works/10.1007/s10664-020-09821-y and https://doi.org/10.1109/ICSME.2017.12 – Crossref records of the retracted Palomba and Zaidman papers: "The smell of fear" (EMSE 2019) and "Does Refactoring of Test Smells Induce Fixing Flaky Tests?" (ICSME 2017). Primary.
35. https://testsmells.org/pages/testsmells.html and https://github.com/TestSmells/TestSmellDetector – tsDetect catalogue and repository. Primary.
36. http://xunitpatterns.com/Test%20Smells.html – Meszaros, xUnit Test Patterns smell catalogue and causes. Primary.
37. https://pypi.org/pypi/{name}/json – PyPI JSON API used for all version and date checks on 2026-09-30. Primary.
38. https://github.com/jest-community/eslint-plugin-jest – eslint-plugin-jest rule list (version from the npm registry). Primary.
39. https://javadoc.io/static/org.mockito/mockito-core/5.14.2/org/mockito/quality/Strictness.html – Mockito `Strictness` (STRICT_STUBS, unused stubs). Primary.
40. https://rspec.info/features/3-13/rspec-mocks/verifying-doubles/partial-doubles/ – RSpec verifying partial doubles. Primary.
41. https://www.virtuosoqa.com/post/what-is-the-testing-pyramid – vendor page with uncited pyramid statistics. Secondary (folklore example).
