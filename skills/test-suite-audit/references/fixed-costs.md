# Fixed costs and profiling

This page covers where a test run's wall time goes before and around the tests. That means interpreter start-up, plugin loading, conftest imports, collection, assertion rewriting and its cache, output capture, logging and reporting, fixtures, coverage tracing, garbage collection (GC), and memory growth. It also covers profilers, known version regressions, and benchmarks whose before-and-after numbers hold. Load it in phase 6 to measure fixed costs, and in phase 7 when setup, fixtures, imports, or collection dominate. Database setup and test data are in [database-and-data.md](database-and-data.md), framework settings in [framework-runtime.md](framework-runtime.md), and worker counts and sharding in [scheduling.md](scheduling.md).

## Quick reference

Thresholds are the research's judgement unless a source is cited. "2%" and "10%" are the medium and high impact levels in [findings.md](findings.md). Numbers cited to [1] come from one shared Apple M4 Max laptop with macOS, so treat them as orders of magnitude and measure on the target machine.

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Coverage tracing in the timed job | `--cov` or `coverage run` in the continuous integration (CI) command or `addopts`; CI job times with and without coverage | The job that developers wait for pays 10% or more for coverage | Coverage in one job; the `sysmon` core where line coverage suffices | 58 → 27 s [2]; about 50 → 20–30 min [3] |
| Small fixture costs multiplied by many uses | `results.py fixtures`; autouse fan-out in `static_scan.py`; `--setup-plan` counts | A fixture's total over 2% of the run; an autouse mean over 1 ms in 10,000+ tests | Narrow autouse; wider scope where safe; cheaper construction | 1 ms × 220 uses, invisible to `--durations` [1] |
| In-test hotspots | Call times clustered at round numbers; `risk-*` checks; greps; a wall-clock profile | A pattern whose summed call time reaches 2% of the run | Event waits, cheap hashers, session-scoped keys, in-process calls | bcrypt: 189 ms → 0.8 ms per hash [1] |
| A known regression in the installed pytest | Installed versions; a class-heavy suite on 9.1.0–9.1.1 | 9.0.3 collects measurably faster | Pin `pytest<9.1` until a release has the fix | 303.6 → 30.2 s of collection [4] |
| Expensive session and module fixtures | `results.py fixtures`: few setups, large total, "paid once per worker" | 2 s or more per worker, or 2% of the run | Cache or prebuild; lazy setup; share across workers | 43 builds of about 60 s moved to a prebuild [5] |
| Capture, logging, and reporting overhead | `-rA`, `log_level = DEBUG`, or `junit_logging = "all"` in the configuration; runs with and without | Any of them in the shared configuration, or a 2% difference | `-ra`; the default log level; JUnit XML only where it is read | `-rA` +160%, DEBUG capture +53% of central processing unit (CPU) time [1] |
| Slow start-up before collection | `startup_gap_seconds`; runs with autoload off and with `--noconftest` | Over about 1 s, or 20% of a one-test run, times workers and invocations | Remove unused plugins; an explicit plugin list; a light root conftest | 0.80 → 0.25 s per invocation [1] |
| Heavy imports in conftest files and test modules | `importtime_summary.py` on a `-s` import-time run | A package over about 100 ms of self time, or imports over 1 s | Remove them; move them into fixtures; split the root conftest | 8 s before the first test [6]; 3.4% of a run [2] |
| Collection walks more of the tree than it needs | No `testpaths`; a replaced `norecursedirs`; directories in `nodeids.txt` | Warm collection over 2–3 s per 1,000 tests, or 10% of the run | `testpaths`; keep the defaults; start pytest at the rootdir | 7.84 → 2.60 s [2]; 23 min → 38 s [7] |
| Collection hooks, parametrization, and plugins dominate | A profile of `--collect-only`; collection hooks in conftest files | One package or hook dominates the profile | Upgrade the plugin; build parameters lazily; cheaper hooks | 2.5 of 3+ min in one plugin [8] |
| A cold assertion-rewrite cache in CI | Fresh checkouts; `PYTHONDONTWRITEBYTECODE`; the assert count | Asserts × 0.2–0.5 ms × workers reaches 2% of the job | Drop the variable; cache bytecode after the next pytest release | 30,000 asserts: 7.6 s cold, 0.6 s warm [1] |
| Garbage-collection overhead | The probe (M6); `gc.collect()` in autouse fixtures | GC over about 5% of the session | Remove per-test `gc.collect()`; raise threshold0 with memory checks | 4.8 → 1.9 s in a synthetic suite [1] |
| Memory growth across long runs | Peak resident set size (RSS); the probe's slope; exit code 137 or crashed workers | A steady rise after warm-up | Fix retention at the source; shard | 11 MB per 500 tests from a 20 KB leak [1] |
| Old interpreter or tool versions | `PYTHON -VV`; the CI matrix; plugin versions | CPython 3.10 or older, 3.14.0–3.14.4, old pytest-asyncio or coverage.py | Upgrade in a disposable copy and measure again | 3.11 is 1.25 times as fast as 3.10 [9] |

### Changes that do not pay

| Change | Why it loses | Evidence |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1` for speed | It only stops cache writes, so a clean tree compiles and rewrites on every run | 6.0 s against 1.05 s of CPU to collect 10,500 tests [1] |
| Moving conftest code into `pytest_plugins` modules | pytest imports those modules as soon as the conftest loads | No deferral [1]; deprecated outside the root conftest [10] |
| `PYTHON_LAZY_IMPORTS=all` on Python 3.15 | pytest 9.1.1 crashes at start-up | [11] |
| Disabling GC for a whole suite | Memory can explode, and swapping or out-of-memory (OOM) kills cost more than GC | 98 MB → 2.75 GB of peak RSS with cyclic garbage [1] |
| `gc.freeze()` without a check on the exact version | It helps on one version and hurts on another | GC time 2.9 → 1.2 s on 3.13.5, but 3.3 → 8.0 s on 3.14.0 [1] |
| `--max-worker-restart` against leaks | It replaces only crashed workers, and it fails the running test | [12] |
| More pytest-xdist workers when fixed costs dominate | Every worker repeats start-up, imports, and collection | 96 s before the first test with 48 workers, 78 s with 16 [13]; see [scheduling.md](scheduling.md) |

## Signals

### Coverage tracing in the timed job

- **Detect:** Read the CI command, `addopts`, and the coverage configuration for `--cov`, `coverage run`, `branch = true`, and dynamic contexts. Take the overhead from CI history: a job with coverage against a comparable job without it (`history` evidence). `findings.py` rejects `measured` evidence from runs marked `instrumented: coverage` in speed findings (guardrail 7). Without such a pair of jobs, give the impact a `heuristic` basis from the effects below. Check the active core with the health check in [coverage.md](coverage.md).
- **False positives:** The job that measures coverage needs the tracing. On Python 3.12 and 3.13, the `sysmon` core cannot measure branches, so coverage.py 7.16.2 warns and falls back to CTracer: setting `COVERAGE_CORE=sysmon` does not prove that the fast core runs [1][14]. `sysmon` also records per-test contexts wrongly, so jobs that feed per-test contexts, pytest-testmon, or coverage-guided mutation testing stay on `COVERAGE_CORE=ctrace` (SKILL.md phase 7).
- **Fix:** Measure coverage in one CI job, not in every matrix entry or in the job that developers wait for. Upgrade coverage.py: 7.9.1 and later default to `sysmon` on 3.14 [14]. On 3.12 and 3.13, use `COVERAGE_CORE=sysmon` where line coverage is enough, and move dynamic contexts to a less frequent job.
- **Effect:** Warehouse went from 58 s to 27 s (−53%) with `sysmon` [2]. scikit-learn's slowest job went from about 50 to 20–30 minutes with `sysmon` and no branch coverage [3]. The classic tracer made CPU-bound code 3 times slower with line coverage and 5 times slower with branch coverage [15].
- **Verify:** CI job durations before and after; total coverage and the missed lines match between cores within a small tolerance [1].

### Small fixture costs multiplied by many uses

- **Detect:** `results.py fixtures` on the baseline ranks fixtures by total setup time, with setups, mean, and maximum (M4). A high "function-scoped fixture setups per test" points at root autouse fixtures, and `static_scan.py` lists each autouse fixture with its scope and roughly how many tests it reaches. Its `unread-fixture` check lists tests that request a fixture that returns a value and never read it: they pay its setup for its side effects only, or for nothing. For a suite too slow to run in full, multiply `--setup-plan` counts by means from a sample run. Report a fixture whose total exceeds 2% of the run, or an autouse fixture with a mean above 1 ms in a suite of over 10,000 tests. At 50,000 tests, 5 ms each is about 4 minutes of serial time.
- **False positives:** A wider scope shares one object between tests, so a test that mutates it breaks later tests, depending on order. The table times setup only: code after `yield` lands in the teardown phase of `results.py summary`. Its times exclude dependencies, while `--durations` includes them, so never add the two. A first setup can carry first-use costs, so compare the maximum with the mean.
- **Fix:** Drop `autouse=True` where most tests do not need the fixture, request it with `@pytest.mark.usefixtures` where they do, and move it out of the root conftest ([design-and-smells.md](design-and-smells.md)). Widen the scope only for immutable resources or resources reset per test; otherwise, split the fixture into a wide-scoped expensive part and a cheap function-scoped reset. Build data once per session, and hand out immutable views, such as tuples, frozen dataclasses, or `types.MappingProxyType`, instead of `copy.deepcopy`. Database fixtures are in [database-and-data.md](database-and-data.md).
- **Effect:** A 1 ms autouse fixture used 220 times cost 0.28 s and never showed in `--durations`, whose default minimum is 5 ms [1][16]. `copy.deepcopy` of 50,000 nested rows took 129 ms, against 23 ms to parse them from JSON [1]. Ruby's TestProf reports 27–50% shorter suites from the same cost × uses profiling (vendor-reported) [17].
- **Verify:** The fixture's total falls over 3 runs each; `results.py diff` shows the same tests and outcomes; after a scope change, two runs in random order pass (SKILL.md phase 9).

### In-test hotspots

- **Detect:** Start with the durations. Call times clustered at round numbers, such as 0.5, 1, 5, or 30 s, point at sleeps and timeouts: the first line below counts them in the baseline's `timing.jsonl`. `static_scan.py` reports sleeps, subprocesses, threads, and network use as `risk-*` checks. Grep test files, conftest files, helpers, and factories for the rest, then profile only the tests that the durations single out (M5).
- **False positives:** A grep hit costs nothing until the durations confirm it: mocked paths never run, and a key built in a session fixture is paid once. Some tests exist to check a timeout, a retry schedule, or the production hasher, so shrink their parameters and keep at least one test on each real policy (guardrail 10).
- **Fix:** Use the table's fixes. Each fast replacement stops checking something, such as the production hasher or the real schedule, so disclose that loss (guardrail 11).
- **Effect:** Multiply the cost per use by the number of uses in the durations. In flashinfer, each kernel took about 60 s to compile on first use [5].
- **Verify:** The affected call times fall, and the round-number spikes leave the histogram; outcomes are unchanged; each real policy keeps a test.

```sh
python3 -c "import collections,json,sys; h=collections.Counter(round(r['duration'],1) for r in map(json.loads,open(sys.argv[1])) if r.get('when')=='call' and r['duration']>=0.2); print(h.most_common(15))" AUDIT/runs/NN-baseline/timing.jsonl
grep -rnE 'bcrypt|argon2|scrypt|pbkdf2|make_password|set_password|passlib|generate_private_key|RSA\.generate|ssh-keygen|trustme' TEST_ROOTS
grep -rnE 'tenacity|@retry|backoff\.on_|Retry\(|max_retries|wait_exponential|stop_after_attempt' TEST_ROOTS
grep -rnE 'read_csv|read_parquet|json\.load\(|np\.load\(|pickle\.load\(|yaml\.(safe_)?load\(|deepcopy\(|model_copy\(deep=True' TEST_ROOTS
grep -rnE 'jinja2\.Environment\(|re\.compile\(|numba|@jit|\.jit\(|\.join\(timeout=|\.wait\([0-9.]+\)|\.result\(timeout=|wait_for\(' TEST_ROOTS
```

| Hotspot | Extra signal | Cost per use [1] | Fix |
| --- | --- | --- | --- |
| Sleeps and polling | `risk-sleep`; fixed poll intervals | The whole sleep, plus up to one poll interval | Wait on an event or future; inject a clock ([framework-runtime.md](framework-runtime.md)) |
| Retry and backoff | Error-path tests of clients with retries | A whole schedule, for example 1 + 2 + 4 s | Zero wait or a patched sleep; keep one test on the real schedule |
| Subprocesses | `risk-subprocess`; `multiprocessing` spawn re-imports the application | `python -c pass` 36 ms; `import pytest` 100–200 ms | Call the code in process where the boundary is not under test ([framework-runtime.md](framework-runtime.md)) |
| Password hashing | User factories that call `set_password` | bcrypt 189 ms at 12 rounds, 0.8 ms at 4; argon2-cffi defaults 24 ms; PBKDF2-SHA256 at 600,000 iterations 50 ms | A cheap hasher in test settings ([framework-runtime.md](framework-runtime.md)) |
| Keys and certificates | Per-test Transport Layer Security (TLS) or JSON Web Token (JWT) fixtures | RSA-2048 86 ms, RSA-4096 1.07 s, Ed25519 0.07 ms | Session-scoped or pre-generated test keys |
| Data loads and deep copies | Function-scoped fixtures that read files or return `copy.deepcopy(BIG)` | `json.loads` of 3.1 MB 23 ms; `deepcopy` of 50,000 rows 129 ms | Session scope with read-only sharing; smaller files; copy only what a test mutates |
| First-use compilation | Templates, schemas, regular expressions, or kernels compiled in tests | A new Jinja environment and compile 9.4 ms, against 0.33 ms to render | Build once per session; cache compiled artefacts |
| Elapsing joins and timeouts | Round-number call times | The whole timeout; `Event.wait(0.2)` plus `join`: 205 ms | Signal completion; short, configurable timeouts |
| Real network and Domain Name System (DNS) lookups | Failures under pytest-socket; `getaddrinfo` or `connect` in profiles | Milliseconds up to a whole connect timeout | Fakes at the boundary ([framework-runtime.md](framework-runtime.md)) |

### A known regression in the installed pytest

- **Detect:** Read the installed versions from `PYTHON -m pip list` or from the header of a run without `-q`, and compare them with the table below. For the 9.1 regression, collect with pytest 9.0.3 in a disposable copy with its own environment at a new path, installed from the project's test dependencies plus `pytest==9.0.3`. Run `CI_TEST_COMMAND --collect-only -q` through `run_suite.py` with that interpreter, 3 times on each side.
- **False positives:** Plugins pinned to one pytest line can fail to import on the other, so keep plugin versions equal where you can. A downgrade can lose fixes, so read the changelog between the two versions [18].
- **Fix:** Pin `pytest<9.1` until a release contains pull request (PR) 14984, then measure again [19]. Benchmark collection after every pytest upgrade.
- **Effect:** One private suite collected 30,406 tests in 30.22 s on 9.0.3 and in 303.61 s on 9.1.1. A minimal reproducer with 4,000 sibling classes went from 2.57 s to 9.12 s [4].
- **Verify:** `results.py diff` between the two versions' collection runs shows the same collected set, and the median returns to the 9.0.3 level.

| Version | Problem | Who is hit |
| --- | --- | --- |
| pytest before 8.4.0 | Collection with many explicit file arguments from outside the rootdir: 23 minutes against 38 s [7] | CI jobs that pass file lists |
| 9.0.0–9.0.2 | Quadratic handling of unittest subtests on Python 3.10, fixed in 9.0.3 [18] | unittest-style suites with subtests |
| 9.1.0–9.1.1 | Quadratic fixture registration makes collection up to 10 times slower [4] | Many test classes that inherit fixtures from a base class |
| 9.1.1 and earlier | The rewrite cache is validated by mtime and size [20]; descriptor capture costs milliseconds per test on macOS [1][21] | CI checkouts; macOS machines |
| Unreleased main on 2026-09-30 | Source-hash rewrite cache, capture fast path, and the 9.1 fix, merged 2026-09-14 [22][21][19] | Everyone: measure again after the next release |

### Expensive session and module fixtures

- **Detect:** In `results.py fixtures`, look for a large total with few setups. Its line "session fixtures paid once per worker" names fixtures of 2 s or more that every pytest-xdist worker repeats. `results.py summary`'s "slowest setup" names the first test that requested a fixture, not the fixture ([traps.md](traps.md)). A `run_suite.py` run of `CI_TEST_COMMAND --setup-show -n 0 ONE_DIR` prints each SETUP and TEARDOWN with its scope.
- **False positives:** A large setup can belong to a fixture that only one module uses, so check its scope and users. A resource that CI starts once, outside pytest, does not grow with workers.
- **Fix:** Cache the artefact between runs, such as compiled assets or a pre-migrated database template ([database-and-data.md](database-and-data.md)). Build it in a CI step before pytest. Make it lazy, so subsets that do not need it do not pay. Build independent parts in parallel. Sharing one build across workers is in [scheduling.md](scheduling.md).
- **Effect:** flashinfer moved 43 kernel builds of about 60 s each into a parallel prebuild in its conftest [5].
- **Verify:** The fixture's total and setups fall; `results.py diff` shows the same tests and outcomes.

### Capture, logging, and reporting overhead

- **Detect:** Read `addopts` and the logging settings for `-rA` or `-rP`, which print the captured output of passing tests, `log_level` or `log_cli` at DEBUG or INFO, `junit_logging = "all"`, and `--showlocals` with `--tb=long`. Compare one large directory with the CI flags against `--capture=sys`, `-o log_level=WARNING`, or `-rfE`, which overrides `-rA` from `addopts`, 3 runs each, by CPU time (M8).
- **False positives:** `--capture=sys` misses output that C extensions and child processes write to file descriptors 1 and 2, so tests that use `capfd` can change. A lower log level breaks tests that assert on DEBUG records without `caplog.set_level`. `-p no:logging` disables `caplog`, so use it only to measure. The descriptor-capture cost was measured on macOS only [1].
- **Fix:** Replace `-rA` and `-rP` in the default `addopts` with `-ra` or `-rfE`. Keep `log_level` as high as the suite allows, and let the tests that need DEBUG call `caplog.set_level(logging.DEBUG)` ([framework-runtime.md](framework-runtime.md)). Write JUnit XML only in the job that reads it, without `junit_logging = "all"`. On macOS developer machines, use `--capture=sys` until a pytest release contains PR 14687 [21].
- **Effect:** 10,000 tests that each log 20 DEBUG records and print a line, CPU medians: 5.6 s by default, `-v` +4%, `--junitxml` +22%, `-o log_level=DEBUG` +53%, and `-rA` +160% [1]. On macOS, 2,000 tests that print nothing took 5.4 s of wall time with `fd`, 0.70 s with `sys`, and 0.82 s on pytest main, mostly in waiting rather than CPU [1]. PR 14687 cut pypa/packaging's 62,000-test run by about 8% [21].
- **Verify:** CPU and wall medians before and after; unchanged outcomes; failure reports still show the logs that developers use.

### Slow start-up before collection

- **Detect:** `startup_gap_seconds` in a manifest is the time outside pytest's clock: interpreter start-up, plugin loading, and initial conftest imports (M1). M3 splits it into plugin and conftest shares. The `plugins:` header line of a run without `-q` lists what loaded. Report a gap above about 1 s, or 20% of a one-test run, multiplied by the workers and by the pytest invocations per CI job.
- **False positives:** A cold operating-system file cache inflates the first run after a checkout: 21 s of wall time with 6 s of CPU, against 2.4 s later [1]. A plugin that the suite needs is not overhead; with autoload off, a missing one shows as "fixture 'X' not found" or unknown-marker errors. For Django's runner, the gap also holds test database creation ([database-and-data.md](database-and-data.md)).
- **Fix:** Remove unused plugins from the test environment, for example with a dedicated dependency group. Disable one plugin with `-p no:NAME`, using its entry-point name [10]. From pytest 8.4, disable autoload and name what the suite needs: `addopts = ["--disable-plugin-autoload", "-p", "xdist", "-p", "pytest_cov"]` [18]. A plugin added later then silently does not load. Lighten the initial conftest files (next signal).
- **Effect:** 16 autoloaded plugin packages took a one-test run from 0.17 s to 0.80 s, and the explicit list above brought it to 0.25 s. Of those plugins, faker (80 ms) and hypothesis (71 ms) had the largest self times [1]. pytest-xdist starts workers one after another at 0.04–0.05 s each, about 2 s at `-n 32` [23].
- **Verify:** `results.py diff` over 3 collection runs per side shows the same collected set and a lower median; the full suite keeps its outcomes.

### Heavy imports in conftest files and test modules

- **Detect:** Rank the imports of collection with M2. The conftest and test modules are absent from the log, because pytest loads them with its own import hook, but everything they import appears [1]. Scan conftest files with `grep -rnE --include=conftest.py '^(import|from) ' TEST_ROOTS`. Look for heavy stacks at module level, such as pandas, numpy, scipy, torch, tensorflow, scikit-learn, matplotlib, boto3, google.cloud, azure, kubernetes, openai, or transformers. Look also for side effects at import: client construction, `create_app(`, `django.setup()`, `glob` or `os.walk` over data, and large file reads. Report a package above about 100 ms of summed self time, or imports above about 1 s or 20% of a one-test run.
- **False positives:** A lazy import removes cost only from runs that never import the module, and elsewhere it moves the cost to the first test that uses it. Collection imports every collected test module, also under `-k` and `-m`, so while any test module imports the package at module level, every `-k` run still pays for it. Only runs that name other files or directories skip it: on the skill's benchmark, removing a 1.5 s conftest import cut a run that named one file from 2.0 s to 0.5 s, and left a `-k` run at 2.1 s, because the time moved into collection (measured, 3 runs each). Sum self times, because cumulative times count nested imports twice. A large self time can be a side effect, such as a network call at import, which needs a different fix.
- **Fix:** Remove unused imports and dependencies. Move heavy imports and client construction into the fixture that needs them: with `import boto3` inside a session-scoped `s3` fixture, only the tests that request it pay. Split a heavy root conftest: pytest imports only the conftest files between the rootdir and the collected tests [1], so domain fixtures belong in their own directory's conftest. On Python 3.15, write `lazy import pandas`, or declare `__lazy_modules__ = ["pandas"]`, which older versions ignore [24]. Import errors and side effects then move to first use: at Hudson River Trading, decorator registration, `__init_subclass__` hooks, global overrides, and implicit submodule access broke [25].
- **Effect:** One team traced 8 s before the first test to a boto3 client that contacted Amazon Web Services (AWS) at import, a 2 s glob that generated tests, and two 500 ms parser imports [6]. `import stripe` took 761 ms, against 14.5 ms for an empty script [26]. Removing `ddtrace` from Warehouse's test imports saved 3.4% [2]. Expect the gain mainly in the edit-run loop, in subset runs, and in per-worker start-up.
- **Verify:** The package leaves the ranking or moves under a fixture; `results.py diff` on collection runs shows the same collected set; the suite passes in default and random order; the median wall time of a run that names one test file falls. Do not verify with `-k`, which collects every module.

### Collection walks more of the tree than it needs

- **Detect:** Look for a missing `testpaths`, for `norecursedirs` set at all, for broad `python_files` such as `*.py`, and for `--doctest-modules` or `--pyargs` in `addopts`. Setting `norecursedirs` replaces the defaults `*.egg`, `.*`, `_darcs`, `build`, `CVS`, `dist`, `node_modules`, `venv`, and `{arch}` [16]. Count tests per directory with `cut -d: -f1 AUDIT/nodeids.txt | cut -d/ -f1-2 | sort | uniq -c | sort -rn`. Check how CI starts pytest: with many explicit files from outside the rootdir, pytest 8.3.4 collected for 23 minutes, against 38 s from the root [7]. Report warm collection above about 2–3 s per 1,000 tests, 10% of the run, or 5 s for a one-file run. For scale, 10,500 trivial tests in 500 modules collected in about 1 s of CPU with a warm cache [1].
- **False positives:** Narrower collection can drop real tests, such as tests under `src/` or doctests, so compare collection runs with `results.py diff`, which names every test that disappeared. pytest already skips directories that contain `pyvenv.cfg` or `conda-meta/history` [27]. The usual culprits are `node_modules`, build output, and data or documentation directories.
- **Fix:** Set `testpaths` to the real test roots. If you set `norecursedirs`, repeat the defaults and add to them. Keep `python_files` narrow, and run doctests in their own job with explicit paths. Set `collect_imported_tests = false` (pytest 8.4 and later), so that `Test*` classes imported from production code are not collected [16]. Start pytest from the rootdir in CI.
- **Effect:** Warehouse's collection fell from 7.84 s to 2.60 s with `testpaths`, 2 s of a 50 s run [2].
- **Verify:** `results.py diff` over 3 collection runs per side: the same collected set and a lower median.

### Collection hooks, parametrization, and plugins dominate

- **Detect:** Profile collection with pyinstrument (M5), and read the tree under `Session.perform_collect`: pytest's collectors, conftest hooks, and plugin packages. In conftest files, look for `pytest_collection_modifyitems`, `pytest_generate_tests`, `pytest_pycollect_makeitem`, or `pytest_itemcollected`. Look for `parametrize` values built from files or from large `itertools.product` calls at import, and for `ids=` callables that format large objects. `static_scan.py`'s `parametrize-size` lists matrices of 50 or more cases.
- **False positives:** cProfile inflates code with many small calls, and it made a cold collection 3–4 times slower [1]. Use profiles for shares, and confirm the effect with plain collection runs.
- **Fix:** Upgrade the plugin first: pytest-asyncio 0.25.1 and 1.0 cut its collection overhead [8]. Put cheap checks before expensive ones in hooks. Build expensive parameters in fixtures (`indirect=True`), and cache computed parameter lists. Whether to cut parametrized cases is a question for [redundancy.md](redundancy.md).
- **Effect:** pytest-asyncio took about 2.5 of more than 3 minutes of one suite's collection, and a fork with inlined checks collected in 1 minute [8]. An open pytest PR cut collection by 16.8% for 35,000 generated unittest methods and by 3.4% for PyTorch's `test_ops.py`, whose 34,525 items collect in 14.8 s [28].
- **Verify:** `results.py diff` over 3 collection runs per side: the same collected set and a lower median.

### A cold assertion-rewrite cache in CI

- **Detect:** Look for a CI checkout without a cache step for `__pycache__`, `PYTHONDONTWRITEBYTECODE` in the environment, a read-only tree, or `sys.dont_write_bytecode = True` in a conftest, which the pytest documentation suggests against stale files [29]. Each makes pytest rewrite every test module on every run. pytest 9.1.1 and earlier validate the cache by mtime and size, so a restored cache is stale after a checkout [20]. Count the asserts (below), and multiply by 0.2–0.5 ms and by the worker count, because every worker rewrites a cold cache [1]. Measure cold and warm collection with M7.
- **False positives:** On a developer machine the cache is warm, so the cost falls on CI and on first runs. `--assert=plain` removes the cost and also the compared values in failure messages [29]: a trade-off, not a fix.
- **Fix:** Remove `PYTHONDONTWRITEBYTECODE=1` from jobs that run pytest more than once in one workspace, such as several tox environments or reruns. After an upgrade to a pytest release with the source-hash cache, which costs "roughly 15 microseconds per file" [22], cache `__pycache__` between CI runs, or point `PYTHONPYCACHEPREFIX` at a cached directory. For pytest 9.1.1, resetting mtimes with `git restore-mtime` is untested.
- **Effect:** 10,500 tests in 500 modules took 5.9 s of CPU to collect cold and 1.05 s warm. 6,000 tests with 30,000 asserts took 7.6 s against 0.6 s, and without asserts 0.8 s against 0.6 s. With every source file touched, as after a checkout, pytest 9.1.1 needed 7.3 s and pytest main 0.6 s [1].
- **Verify:** After a second run, rewritten files (`*-pytest-*.pyc`) exist in the cache, and the CPU time of collection falls to the warm value.

```sh
grep -rEc '^\s*assert\b' --include='test_*.py' --include='*_test.py' --include='conftest.py' TEST_ROOTS | awk -F: '{s+=$2} END {print s}'
```

### Garbage-collection overhead

- **Detect:** Load the probe (M6), and compare the GC total with the session time; tune only above about 5%. Check `PYTHON -VV` for 3.14.0–3.14.4. Grep conftest files for `gc.collect(`, `gc.disable(`, and `gc.set_threshold(`. A `gc.collect()` in an autouse fixture walks the whole heap for every test: 2.6 ms at 0.1 million tracked objects, 34 ms at 1 million, and 104 ms at 3 million [1].
- **False positives:** The effects below come from a deliberately allocation-heavy suite and overstate a typical one. Weak-reference callbacks, `__del__` finalizers, `ResourceWarning` checks, and pytest's unraisable-exception reporting depend on prompt collection, so later collection moves their warnings or failures to later tests. A library can also call `gc.collect()` itself.
- **Fix:** Remove per-test `gc.collect()` calls, or limit them to the tests that need them. Upgrade 3.14.0–3.14.4 to 3.14.5 or later, which restores the 3.13 collector [30][31]. Raise threshold0 in the root conftest's `pytest_configure`, for example `gc.set_threshold(50_000, 20, 20)`, and record peak RSS on both sides; the default threshold0 is 700 up to 3.12 and 2,000 from 3.13 [32]. Try `gc.collect(); gc.freeze()` in `pytest_collection_finish` only on the exact version in use. Never disable GC for a long suite. Each change trades memory for time, so report peak RSS with it (guardrail 11).
- **Effect:** In 4,000 tests that each allocate 6,000 containers on a 3-million-object heap, on 3.13.5, GC took 2.9 s of a 4.8 s session. threshold0 = 50,000 cut the session to 1.9 s, and `gc.freeze()` after collection cut GC to 1.2 s. On 3.14.0, `gc.freeze()` raised GC time from 3.3 s to 8.0 s. With cyclic garbage, threshold0 = 50,000 took 2.4 s instead of 4.5 s, at 90 MB instead of 98 MB of peak RSS; disabling GC took 1.6 s and 2.75 GB [1].
- **Verify:** The probe's GC total falls, peak RSS stays acceptable, and outcomes are unchanged, including the number of warnings.

### Memory growth across long runs

- **Detect:** Read peak RSS from `/usr/bin/time -l` (macOS) or `-v` (Linux) inside `run_suite.py`, per-worker RSS from `ps` during an xdist run, and exit code 137 or "worker 'gw3' crashed while running" in CI logs. The probe's slope (M6) separates retention, a steady rise after warm-up, from a normal plateau, because the allocator rarely returns memory. Attribute growth on one directory with the probe's tracemalloc mode, or with pytest-memray: `--memray --most-allocations=20`, or `@pytest.mark.limit_leaks("1 MB")`; `limit_leaked_objects` needs Python 3.13.3 or later [33]. Look for module-level registries that tests append to, `functools.lru_cache` on unique arguments, and query or log recording that keeps everything. Look also for session fixtures that hold large data, large parametrize values, which live for the whole session [34], mocks with millions of recorded calls, and threads or servers that never stop. Budget 3–5 KB per collected item on pytest 9.1.1, paid again by every worker [1].
- **False positives:** pytest keeps each failure's traceback and locals for the report, so a run with many failures grows by design; one team found 120 GB not enough [34]. tracemalloc grouped by `"lineno"` spreads a leak over many lines: a 20 KB-per-test leak did not appear in its top entries at all, so group by `"filename"` [1].
- **Fix:** Fix retention at the source: clear caches in fixture teardown, bound query and log recording, narrow the scope of large data, and generate large parameter sets lazily. Shard a huge run ([scheduling.md](scheduling.md)). pytest-xdist cannot recycle healthy workers: `--max-worker-restart` replaces only crashed ones, up to 4 × the worker count by default, and fails the running test [12].
- **Effect:** A module-level list that kept 20 KB per test showed as a steady 11 MB per 500 tests. tracemalloc grouped by file named each test module, at about 3.9 MB per 1,000 tests [1]. The cryptography project's 149,150 tests used about 1.26 GB after collection on CPython 2.7, about 8 KB each [34].
- **Verify:** A flat RSS slope after warm-up; lower peak RSS; unchanged outcomes.

### Old interpreter or tool versions

- **Detect:** Read `PYTHON -VV`, the versions of pytest, pytest-asyncio, pytest-xdist, and coverage.py, and the CI matrix. Compare them with the table below and with the pytest table above.
- **False positives:** An upgrade can bring its own regression, as pytest 9.1 did, so measure rather than assume.
- **Fix:** Upgrade in a disposable copy with its own environment, and benchmark with M8.
- **Effect:** CPython 3.11 runs 1.25 times as fast as 3.10 on average, 10–60% faster by workload, and starts 10–15% faster [9].
- **Verify:** Medians of both sides with M8, and identical outcomes.

| Version | Change that affects run time | What it means for the audit |
| --- | --- | --- |
| CPython 3.12 | Coverage runs with the classic tracer take about twice as long as on 3.11 [35][3] | Check the coverage core |
| 3.13 | GC threshold0 raised from 700 to 2,000 [32]; the free-threaded build is experimental, with "a substantial single-threaded performance hit" [36] | Measure GC advice from older versions again |
| 3.14.0–3.14.4 | An incremental GC, reverted in 3.14.5 because it used up to 5 times the memory in core benchmarks [31] | Upgrade before you tune GC |
| 3.14 | Opt-in tail-calling interpreter (Clang 19 and later), 3–5% faster; free-threading supported, with a 5–10% single-threaded penalty; `-X importtime=2` [30]; coverage.py 7.9.1 and later default to `sysmon` [14] | A free-threaded build slows a single-process suite; per-test coverage needs `ctrace` |
| 3.15 (final due 2026-10-01) | `lazy import` (Python Enhancement Proposal (PEP) 810), the Tachyon sampling profiler, and frame pointers on by default [24][37] | pytest 9.1.1 crashes under `PYTHON_LAZY_IMPORTS=all` [11] |

## Measuring

Run every command that imports project code through `run_suite.py` (guardrail 3). Here `PYTHON` is the project's interpreter, as in SKILL.md phase 6, `python3` runs the skill's scripts, `CI_ARGS` is the pytest arguments of `CI_TEST_COMMAND`, and `NN` is the run number that `run_suite.py` prints. Instrumented runs rank causes; timing claims come only from uninstrumented runs whose manifests match (guardrail 7).

### Wall-time anatomy from run manifests (M1)

The phase 5 collection run and the phase 6 baseline give most buckets. Add two runs that select one fast, uniquely named test with `-k`, so that every worker still collects the whole suite. A run that selects nothing counts as COMPLETE when it runs serially, but stays PARTIAL under pytest-xdist, whose output does not show that tests were deselected. Without pytest-xdist, skip one-workers and drop `-n 0`.

```sh
/usr/bin/time -p PYTHON -c pass      # interpreter and .pth start-up only
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label one-serial --timeout 900 --cwd ROOT -- CI_TEST_COMMAND -n 0 -k UNIQUE_FAST_TEST
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label one-workers --timeout 900 --cwd ROOT -- CI_TEST_COMMAND -k UNIQUE_FAST_TEST
python3 -c "import json,sys; [print(d.rsplit('/',1)[-1], *(json.load(open(d+'/manifest.json')).get(k) for k in ('wall_seconds','reported_seconds','startup_gap_seconds','workers'))) for d in sys.argv[1:]]" AUDIT/runs/NN-collect AUDIT/runs/NN-one-serial AUDIT/runs/NN-one-workers AUDIT/runs/NN-baseline
```

| Bucket | Read it as |
| --- | --- |
| Start-up | `startup_gap_seconds` of the collection run: interpreter, plugins, and initial conftest imports. Under xdist it covers only the main process. |
| Collection | `reported_seconds` of the collection run. `--collect-only` starts no xdist workers [1]. |
| Per-worker fixed cost | `wall_seconds` of one-workers minus one-serial: each worker starts, imports, and collects before its first test. |
| Test phase | `reported_seconds` of the baseline minus collection. Under xdist, it also holds each worker's start-up and collection. `results.py summary` splits test time into setup, call, and teardown. |
| Between-test overhead | Serial runs only: the test phase minus the summary's "sum of test time". |

For CI runs that exist only as JUnit XML, `testsuite/@time` spans the session, so it includes collection but not start-up [38]. In a serial run, it minus the summed `testcase/@time` estimates collection plus between-test overhead:

```sh
python3 -c "import sys,xml.etree.ElementTree as E; r=E.parse(sys.argv[1]).getroot(); s=r if r.tag=='testsuite' else r.find('testsuite'); t=sum(float(c.get('time',0)) for c in s.iter('testcase')); print(f'suite {float(s.get(\"time\")):.1f}s tests {t:.1f}s gap {float(s.get(\"time\"))-t:.1f}s')" JUNIT.xml
```

Cost: two runs of start-up plus one collection each.

### Import profile of collection (M2)

This is the phase 6 recipe: `run_suite.py` writes stderr into the run's `output.log`, and `importtime_summary.py` reads that log directly. Keep the CI arguments, and keep `-s` ([traps.md](traps.md)). If `CI_ARGS` already has `-q`, leave out the extra one: `-qq` makes the collection print counts per file, and the run gets the verdict UNKNOWN.

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label importtime --timeout 900 --cwd ROOT -- PYTHON -X importtime -m pytest CI_ARGS --collect-only -q -s
python3 ${CLAUDE_SKILL_DIR}/scripts/importtime_summary.py AUDIT/runs/NN-importtime/output.log --top 15 --json-out AUDIT/results/importtime.json
```

The output ranks top-level imports by cumulative time, root packages by self time, and single modules by self time; rank by self time. Take the ranking from a second, warm run, because the first also compiles bytecode. `-X importtime=2` (3.14 and later) adds `cached` lines that show repeat imports, and the script skips them. Cost: one collection. The manifest marks the run `instrumented: profile`, so use it to rank, not to time.

### Plugin and conftest shares (M3)

```sh
PYTHON -c "from importlib.metadata import entry_points; print(sorted(e.name for e in entry_points(group='pytest11')))"
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label collect-noautoload --timeout 900 --cwd ROOT --env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 -- CI_TEST_COMMAND --collect-only -q -p NAME
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label collect-noconftest --timeout 900 --cwd ROOT -- CI_TEST_COMMAND --collect-only -q --noconftest
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py diff --before RUN_A RUN_B RUN_C --after RUN_D RUN_E RUN_F   # plain collection runs, then one variant's
```

The first line lists the installed plugins' entry-point names. With autoload off, pass `-p NAME` for each plugin that `addopts` needs, such as `-p xdist` for `-n` or `-p pytest_cov` for `--cov`; without them, the run fails with "unrecognized arguments". Run each variant 3 times, and compare it with the plain collection runs. `results.py diff` prints both medians and checks that the collected set is unchanged, because conftest files and plugins can add tests and collection hooks. It warns that the commands differ, which is expected here. Cost: a few collection runs.

### Fixture cost × uses (M4)

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py fixtures AUDIT/runs/NN-baseline --top 20 --json-out AUDIT/results/fixtures.json
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label setup-plan --timeout 900 --cwd ROOT -- CI_TEST_COMMAND --setup-plan -n 0
grep -E '^\s*SETUP' AUDIT/runs/NN-setup-plan/output.log | awk '{print $2, $3}' | sort | uniq -c | sort -rn | head -20
```

`results.py fixtures` needs a `--timing-plugin` run. Per fixture, it prints the total setup time, setups, mean, maximum, scope, and where the fixture is defined. The times are self times, without the fixtures it depends on. Its "setup phase" line splits the setup phase into fixture functions and the rest: fixture resolution, setup hooks, GC, and contention between workers. It also flags function-scoped fixtures set up 100 or more times at 20 ms or more each, and session fixtures paid once per worker at 2 s or more.

The plan prints each setup with a scope letter: S session, P package, M module, C class, F function. Keep `-n 0`, because xdist hides the plan. Session lines have no indent, so the pattern allows none. Setups through `request.getfixturevalue()` do not appear. For a suite too slow to run in full, multiply each count by the mean from a sample run. For one file's full fixture closure, with each definition's file and line, use `--fixtures-per-test -q path/to/test_file.py`. Cost: the table comes with the baseline; the plan costs one collection.

### Profilers (M5)

Every profiler instruments the run. `run_suite.py` marks pyinstrument, cProfile, py-spy, Scalene, memray, and `-X importtime` runs as `instrumented: profile` by itself. Declare `--instrumented profile` for any profiler that it cannot see, such as the probe's tracemalloc mode (M6). Profile collection, one slow directory, or a sample, never the whole suite.

| Profiler | How it measures | Fits | Limits |
| --- | --- | --- | --- |
| pyinstrument | Wall-clock samples, in process | Collection; one slow directory; sleeps and waits stay visible | One process only, so run with `-n 0` |
| cProfile (standard library) | Every call, in process | Call counts; shares of hooks and collectors | Inflates many small calls: cold collection 3–4 times slower [1] |
| py-spy | Samples from outside the process; `--idle` keeps waiting threads; `--subprocesses` follows workers | Whole runs with xdist on Linux, where it needs no root if it starts the process | Needs root on macOS, which guardrail 4 rules out [39] |
| Tachyon (`python -m profiling.sampling`, 3.15) | Samples from outside the process, wall-clock mode by default, "virtually zero" overhead | Suites on Python 3.15 | Same minor version as the target; root or a debugger entitlement on macOS; untested without root on Linux [40] |
| Scalene | CPU and memory per line | Line-level hotspots in one directory | "typically no more than 10-20%" overhead, 35% in one comparison [41] |
| tracemalloc, pytest-memray | Allocations | Leaks in one directory | 7–74 times slower (tracemalloc), about 475 times (pytest-memray) on allocation-heavy code [1] |

Install an in-process profiler into `AUDIT/tools` with the project's interpreter, and load it with `--env PYTHONPATH=AUDIT/tools` (guardrail 4). If CI sets `PYTHONPATH`, append its value. Prefer `--no-deps`, because `PYTHONPATH` puts the folder ahead of the project's own packages. Before you install a tool that needs dependencies, list them with a dry run, and check with `pip show` that the project's environment has none of them. pytest-memray's dry run, for example, lists pytest and pluggy, so install only its missing packages, each with `--no-deps`.

```sh
PYTHON -m pip install --no-deps --target AUDIT/tools pyinstrument
PYTHON -m pip install --dry-run --target AUDIT/tools TOOL | grep '^Would install'   # a tool's dependencies; writes nothing
PYTHON -m pip show NAME…                                                            # every name it finds would be shadowed
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label prof-collect --timeout 900 --cwd ROOT --env PYTHONPATH=AUDIT/tools -- PYTHON -m pyinstrument -r text -o {RUN_DIR}/profile.txt -m pytest CI_ARGS --collect-only -q
head -60 AUDIT/runs/NN-prof-collect/profile.txt
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label prof-run --timeout 1800 --cwd ROOT -- pipx run py-spy record --idle --subprocesses --format raw -o {RUN_DIR}/stacks.txt -- PYTHON -m pytest CI_ARGS SLOW_DIR   # Linux only
```

`--format raw` writes collapsed stacks as text, one per line with its sample count, so you can sort them. Read the profiles for time in `time.sleep`, `select`, `poll`, `socket.connect`, `getaddrinfo`, subprocess waits, hashing and key-generation libraries, `copy.deepcopy`, template compilation, and logging formatters. Cost: one instrumented run per target.

### GC and memory probe (M6)

Save as `AUDIT/probes/auditprobe.py`. It sums GC pauses through `gc.callbacks`, and it logs peak RSS every `PROBE_EVERY` tests. Lines go to a file, one set per xdist worker, because pytest captures output during tests. `GC_THRESHOLD`, `GC_FREEZE`, and `PROBE_TRACEMALLOC` are experiments that leave the project unchanged.

```python
import gc, os, resource, sys, time, tracemalloc
E = os.environ.get
WORKER, OUT, EVERY = E("PYTEST_XDIST_WORKER", "main"), E("PROBE_OUT", "probe.log"), int(E("PROBE_EVERY", "500"))
_gc, _mem = {"t": 0.0, "n": [0, 0, 0], "start": None}, {"n": 0, "snap": None}
def _write(line):
    with open(OUT, "a") as f:
        f.write(f"{line} worker={WORKER}\n")
def _cb(phase, info):
    if phase == "start":
        _gc["start"] = time.perf_counter()
    elif _gc["start"] is not None:
        _gc["t"] += time.perf_counter() - _gc["start"]
        _gc["n"][min(info["generation"], 2)] += 1
def pytest_configure(config):
    gc.callbacks.append(_cb)
    if E("GC_THRESHOLD"):
        gc.set_threshold(*map(int, E("GC_THRESHOLD").split(",")))
    if E("PROBE_TRACEMALLOC") == "1":
        tracemalloc.start(10)
        _mem["snap"] = tracemalloc.take_snapshot()
def pytest_collection_finish(session):
    if E("GC_FREEZE"):
        gc.collect(); gc.freeze()
def pytest_runtest_logfinish(nodeid, location):
    _mem["n"] += 1
    if _mem["n"] % EVERY:
        return
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (2**20 if sys.platform == "darwin" else 1024)  # MB
    line = f"MEM tests={_mem['n']} peak_rss_mb={rss:.1f}"
    if _mem["snap"] is not None:
        snap = tracemalloc.take_snapshot()
        top = snap.compare_to(_mem["snap"], "filename")[:4]
        line += " growth=" + ";".join(f"{s.traceback[0].filename.rsplit('/', 1)[-1]}:{s.size_diff // 1024:+}KiB" for s in top)
        _mem["snap"] = snap
    _write(line)
def pytest_sessionfinish(session):
    _write(f"GC total_s={_gc['t']:.3f} by_gen={_gc['n']} frozen={gc.get_freeze_count()}")
```

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label probe --timeout 1800 --cwd ROOT --env PYTHONPATH=AUDIT/probes --env PROBE_OUT={RUN_DIR}/probe.log -- /usr/bin/time -l CI_TEST_COMMAND -p auditprobe
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label probe-gc50k --timeout 1800 --cwd ROOT --env PYTHONPATH=AUDIT/probes --env GC_THRESHOLD=50000,20,20 --env PROBE_OUT={RUN_DIR}/probe.log -- /usr/bin/time -l CI_TEST_COMMAND -p auditprobe
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label probe-trace --timeout 1800 --cwd ROOT --instrumented profile --env PYTHONPATH=AUDIT/probes --env PROBE_TRACEMALLOC=1 --env PROBE_OUT={RUN_DIR}/probe.log -- PYTHON -m pytest -n 0 SUSPECT_DIR -p auditprobe
grep -h 'maximum resident' AUDIT/runs/NN-probe*/output.log; grep -h '^GC' AUDIT/runs/NN-probe*/probe.log
```

Use `-v` instead of `-l` on Linux. Compare each worker's GC `total_s` with the session time, and read the RSS slope per worker; under xdist, `worker=main` is the controller. On 3.14.0, the incremental collector reports its steps as generation 1. The GC timer adds two clock reads per collection, and both sides of a comparison load the probe, so their timings compare. It misses collections before `pytest_configure`, such as those during initial conftest imports. Cost: one run per setting; the traced variant is 7–74 times slower [1], so run it on one directory.

### Cache state (M7)

State the cache state of every timing, and hold it equal on both sides of a comparison.

- pytest's cache: `run_suite.py` points `cache_dir` into each run folder, so every run starts with an empty `.pytest_cache`, and the project's own cache survives.
- Bytecode and the rewrite cache: pytest writes its rewritten files under `sys.pycache_prefix` when it is set [20]. `--env PYTHONPYCACHEPREFIX={RUN_DIR}/pycache` gives a cold cache and keeps new `__pycache__` folders out of the project. It also makes the standard library and installed packages cold, which overstates a CI checkout, where installed packages already have bytecode. `--env PYTHONPYCACHEPREFIX=AUDIT/pycache`, reused across runs, goes warm after the first run; discard that run.
- A cold start like CI's: the first run in a fresh disposable clone (M8), where only the project's files are cold.
- `.hypothesis`: Hypothesis replays saved failing examples first, so the example database changes run time. Keep it the same on both sides.

### Benchmark protocol (M8)

1. Fix the inputs: the commit on each side, the lock file, the Python patch version, and the environment variables. Pin the worker count (`-n 8`, never `-n auto` across machines of different sizes) and the test order (`-p no:randomly`, or a fixed `--randomly-seed`). Use one quiet machine.
2. Control the cache state (M7). Report cold and warm numbers when the change touches imports or collection.
3. Alternate the two sides, so that drift affects both. Run them from two disposable clones of commits A and B under the audit directory, made with `git clone --local`, because `git worktree add` writes to the project's `.git` (guardrail 6). A branch switch in the project gives changed files new mtimes, which makes their caches cold [20], and guardrail 4 forbids it anyway. An editable install resolves imports to one checkout, so give each clone its own environment. A fresh clone also lacks untracked generated files, such as a `_version.py` ([mutation-testing.md](mutation-testing.md)).

   ```sh
   git clone --quiet --local ROOT AUDIT/work/bench-a && git -C AUDIT/work/bench-a checkout --quiet --detach A
   git clone --quiet --local ROOT AUDIT/work/bench-b && git -C AUDIT/work/bench-b checkout --quiet --detach B
   for i in 1 2 3; do
     python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label bench-a --timeout 1800 --cwd AUDIT/work/bench-a -- /usr/bin/time -p CI_TEST_COMMAND -p no:randomly --junitxml={RUN_DIR}/junit.xml
     python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label bench-b --timeout 1800 --cwd AUDIT/work/bench-b -- /usr/bin/time -p CI_TEST_COMMAND -p no:randomly --junitxml={RUN_DIR}/junit.xml
   done
   grep -H -E '^(user|sys) ' AUDIT/runs/*-bench-*/output.log
   ```

4. Use at least 3 runs per side (guardrail 7), and 5 on a shared machine. Report the median and the range, and treat a difference as real only when it exceeds the spread of both sides. On a shared machine, compare CPU time (`user` + `sys`): identical 10,000-test runs varied from 14.4 s to 25.9 s of wall time, while CPU medians agreed within about 10% [1]. On a quiet machine, 5 alternating collection runs of PyTorch's `test_ops.py` spread about 2–4% [28].
5. Compare the sides with `results.py diff --before RUN_A RUN_B RUN_C --after RUN_D RUN_E RUN_F`. It compares median `wall_seconds`, warns when commands, workers, instrumentation, or CPU counts differ, and lists tests that disappeared, appeared, or changed outcome. It also reads collection-only runs, with the outcome "collected", so it confirms that a change kept the collected set; it exits with 1 when the set changed. For the range, `run_suite.py list --artifacts AUDIT` prints each run's wall time.
6. Check that the tests still detect faults: `results.py diff` reports SAME TESTS AND OUTCOMES, and, after fixture or isolation changes, two runs in random order pass. Then delete the clones with `rm -rf AUDIT/work/bench-a AUDIT/work/bench-b`. Cost: 6 or more full runs; for a slow suite, alternate runs of one file sample instead ([scheduling.md](scheduling.md)).

## Tools

Prefer the skill's scripts (see Measuring); these tools fill gaps. Versions and dates come from the Python Package Index (PyPI) and GitHub on 2026-09-30 [42]. Install each one only in an isolated environment (guardrail 4).

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| pytest built-ins | `--setup-plan`, `--setup-show`, `--fixtures-per-test`, `--durations`, `--collect-only` | 9.1.1, 2026-06-19, maintained; main is 9.2.0.dev | `--durations` hides entries under 5 ms and charges wide-scoped fixtures to their first user |
| `python -X importtime` | Import time per module | CPython 3.7 and later; `=2` from 3.14 | Needs `-s` under pytest; output breaks with threads |
| pytest-durations | Fixture totals, medians, and percentiles | 1.9.0, 2026-08-14, maintained (one main maintainer) | Supports xdist and pytest 9; check whether a table includes dependent fixtures |
| pytest-collect-profile | Ranking collectors and collection hooks | 0.4.0, 2026-09-17, new (repository created 2026-09-10) | Collection only; leaves out initial conftest imports |
| pyinstrument | Wall-clock sampling | 5.1.3, 2026-07-29, maintained | One process only |
| py-spy | Sampling from outside the process | 0.4.2, 2026-04-24, maintained | Root always on macOS; `--idle` for waits; free-threaded builds unverified [39] |
| Tachyon (`profiling.sampling`) | Built-in sampling profiler | CPython 3.15, final due 2026-10-01 | `--mode wall` (the default), `cpu`, or `gil`; `--subprocesses` [40] |
| Scalene | CPU and memory line profiling | 2.3.0, 2026-05-12, maintained | 10–35% overhead [41] |
| memray and pytest-memray | Allocation tracking; leak and memory limits per test [33] | 1.20.0, 2026-08-07, and 1.11.0, 2026-09-17, maintained | Linux and macOS only [43]; about 475 times slower on allocation-heavy code [1] |
| hyperfine | Benchmarking short commands that run no project code | 1.20.0, 2025-11-18, maintained | Install with brew or cargo, because the PyPI package of that name is unrelated; it does not alternate commands [44] |
| pytest-xdist | Parallel runs, where each worker repeats fixed costs | 3.8.0, 2025-07-01, maintained | No recycling of healthy workers [12] |

## Evidence

- Warehouse, the code behind PyPI (Trail of Bits, 2025): 163 s → 30 s (−81%) while the suite grew from 3,900 to 4,734 tests. Steps: pytest-xdist 191 → 63 s, `COVERAGE_CORE=sysmon` 58 → 27 s, `testpaths` 7.84 → 2.60 s of collection, and `ddtrace` removal −3.4%. Squashing migrations (13% in a prototype) was rejected as too costly to maintain [2].
- pypa/packaging (pytest PR 14687, merged 2026-08-12): descriptor capture did seek, read, seek, and truncate about six times per test, even with no output. Skipping empty reads saved about 8% of a 62,000-test run, and the author put pytest's own overhead at about 25% of that suite [21].
- pytest 9.1 regression (issue 14942): 30,406 class-heavy tests collected in 30.22 s on 9.0.3 and 303.61 s on 9.1.1, from a quadratic scan in fixture registration. PR 14984 fixed it on 2026-09-14, unreleased on 2026-09-30 [4][19].
- Collection from outside the tree (issue 13420): 1,000 explicit files took 23 minutes from a sibling directory and 38 s from the root. The cause was 206 million `commonpath` calls, and pytest 8.4.0 fixed it [7].
- PyTorch collection (PR 15060, open): `test_ops.py` collects 34,525 items in 14.8 s. A fixture-closure change saved 3.4% there and 16.8% on 35,000 generated unittest methods; imports and dynamic test generation remain the main costs [28].
- pytest-asyncio (issue 720): about 2.5 of more than 3 minutes of collection, in a suite with hundreds of thousands of fixture arguments; improved in 0.25.1 and 1.0 [8].
- Coverage on 3.12 (coveragepy issues 1665, 1812, and 1916): CI took nearly twice as long as on 3.8–3.11, and scikit-learn went from 50 to 20–30 minutes with `sysmon`. Scrapy removed a 2× slowdown with `sysmon`, and CPU-bound code ran 3× (line) and 5× (branch) slower [35][3][15].
- Start-up: 8 s before the first test came from an AWS client created at import, a 2 s glob, and two 500 ms parser imports [6]. `import stripe` took 761 ms, against 14.5 ms for an empty script [26].
- Workers: OpenTranscribe spent 96 s of a 154 s run before the first test with 48 workers, 78 s with 16, and 44.5 s for a single-process collection (issue 778, open on 2026-09-30) [13]. openpilot found that pytest-xdist starts workers one after another, at 0.04–0.05 s each [23].
- Lazy imports: Hudson River Trading made them the default across the firm and found side-effect imports the hardest part [25]; PEP 810 was accepted for Python 3.15 [24].
- Memory (pytest issue 619): the cryptography project's 149,150 tests used about 1.26 GB after collection, about 8 KB each on CPython 2.7; runs with many failures exhausted 120 GB [34].
- GC: pytest's own CI saved 9.1% of wall time when 9.1.0 cut its GC passes per configuration cleanup from 5 to 1, because that suite creates many in-process pytest sessions [45]. The 3.14.0–3.14.4 incremental collector used up to 5 times the memory in core-developer benchmarks [31].
- Shared setup: flashinfer moved 43 kernel builds of about 60 s each into a parallel prebuild [5]. Ruby's TestProf reports savings of 27% (Discourse), 39% (GitLab API tests), and 50% (Whop CI time) from profiling factories and shared setup, vendor-reported [17].
- This page's own measurements: one shared Apple M4 Max with macOS, Python 3.13.5 and 3.14.0, pytest 9.1.1 and main (9.2.0.dev349). Identical runs varied from 14.4 to 25.9 s of wall time, while CPU medians agreed within about 10% [1].

## Sources

1. Measurements for this skill's research, 2026-09-30: synthetic suites, microbenchmarks, and tool checks on one shared Apple M4 Max with macOS, Python 3.13.5 and 3.14.0, and pytest 9.1.1 and 9.2.0.dev349. No public URL.
2. https://blog.trailofbits.com/2025/05/01/making-pypis-test-suite-81-faster/ – Trail of Bits: Warehouse case study.
3. https://github.com/coveragepy/coveragepy/issues/1812 – `sysmon` with branch coverage; scikit-learn and Scrapy results.
4. https://github.com/pytest-dev/pytest/issues/14942 – pytest 9.1.1 collection regression, 30 s to 303 s.
5. https://github.com/flashinfer-ai/flashinfer/pull/3601 – a parallel kernel prebuild in a conftest.
6. https://jmduke.com/posts/slow-pytests-2.html – an 8 s start-up delay before the first test (engineering blog).
7. https://github.com/pytest-dev/pytest/issues/13420 – 23-minute collection from outside the test tree.
8. https://github.com/pytest-dev/pytest-asyncio/issues/720 – collection dominated by one plugin.
9. https://docs.python.org/3/whatsnew/3.11.html – What's New in Python 3.11: 1.25 times faster on average, 10–15% faster start-up.
10. https://docs.pytest.org/en/stable/how-to/plugins.html – disabling plugins, autoload, and `pytest_plugins` semantics and deprecation.
11. https://github.com/pytest-dev/pytest/issues/14632 and https://github.com/pytest-dev/pytest/pull/14844 – pytest crash under `PYTHON_LAZY_IMPORTS=all`, and a proposed fix.
12. https://github.com/pytest-dev/pytest-xdist/blob/master/src/xdist/dsession.py – `--max-worker-restart` semantics and default.
13. https://github.com/attevon-llc/OpenTranscribe/issues/778 – per-worker collection cost with 48 workers.
14. https://github.com/coveragepy/coveragepy/blob/main/CHANGES.rst – coverage.py changes: `sysmon` default on 3.14 (7.9.1) and core selection.
15. https://github.com/coveragepy/coveragepy/issues/1916 – 3–5 times coverage overhead on CPU-bound code.
16. https://docs.pytest.org/en/stable/reference/reference.html – pytest reference: `norecursedirs` defaults, `collect_imported_tests`, and `--durations-min`.
17. https://test-prof.evilmartians.io/ – Ruby's TestProf and its reported speed-ups (vendor-reported).
18. https://docs.pytest.org/en/stable/changelog.html – pytest changelog through 9.1.1: autoload, version support, and performance entries.
19. https://github.com/pytest-dev/pytest/pull/14984 – fix for the fixture-registration regression, merged 2026-09-14.
20. https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/assertion/rewrite.py – rewrite-cache validation by mtime and size, and `sys.pycache_prefix` support.
21. https://github.com/pytest-dev/pytest/pull/14687 – capture fast path; about 8% on pypa/packaging's 62,000 tests.
22. https://github.com/pytest-dev/pytest/blob/main/changelog/11418.improvement.rst – the unreleased source-hash rewrite cache.
23. https://github.com/commaai/openpilot/pull/35817 – pytest-xdist starts workers one after another.
24. https://peps.python.org/pep-0810/ – explicit lazy imports, accepted for Python 3.15.
25. https://www.hudsonrivertrading.com/hrtbeat/inside-hrts-python-fork – lazy imports in production, and the migration problems.
26. https://jackevans.bearblog.dev/profiling-slow-imports-in-python/ – the cost of `import stripe` (engineering blog).
27. https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/main.py – virtual-environment detection during collection.
28. https://github.com/pytest-dev/pytest/pull/15060 – fixture-closure optimisation, with PyTorch measurements and a benchmark method.
29. https://docs.pytest.org/en/stable/how-to/assert.html – assertion rewriting, its cache, `sys.dont_write_bytecode`, and `--assert=plain`.
30. https://docs.python.org/3/whatsnew/3.14.html – What's New in Python 3.14: tail-calling interpreter, free-threading penalty, incremental GC and its revert, `-X importtime=2`.
31. https://discuss.python.org/t/reverting-the-incremental-gc-in-python-3-14-and-3-15/107014 – the decision and benchmarks behind the GC revert.
32. https://github.com/python/cpython/blob/3.13/Include/internal/pycore_runtime_init.h – default GC thresholds in 3.13.
33. https://pytest-memray.readthedocs.io/en/latest/usage.html – pytest-memray options and markers.
34. https://github.com/pytest-dev/pytest/issues/619 – memory use of very large suites.
35. https://github.com/coveragepy/coveragepy/issues/1665 – coverage slowdown on Python 3.12.
36. https://docs.python.org/3/whatsnew/3.13.html – What's New in Python 3.13: the experimental free-threaded build.
37. https://docs.python.org/3.15/whatsnew/3.15.html – What's New in Python 3.15: lazy imports, Tachyon, and frame pointers.
38. https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/junitxml.py – time semantics of `testcase` and `testsuite`.
39. https://github.com/benfred/py-spy – py-spy options, root requirements, and idle detection.
40. https://docs.python.org/3.15/library/profiling.sampling.html – Tachyon: usage, permissions, overhead, and caveats.
41. https://github.com/plasma-umass/scalene – Scalene usage and its overhead claims.
42. https://pypi.org/pypi/NAME/json and the GitHub releases API – tool versions and dates, queried on 2026-09-30.
43. https://github.com/bloomberg/memray – memray, including platform support.
44. https://github.com/sharkdp/hyperfine – hyperfine flags and behaviour.
45. https://github.com/pytest-dev/pytest/pull/14441 – fewer unraisable-exception GC passes; 9.1% of pytest's own CI time.
