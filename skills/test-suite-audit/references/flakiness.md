# Flakiness and isolation

This page is the reference for flaky tests, which fail and pass at the same commit, and for order-dependent tests, whose outcome depends on which tests ran before them. It covers causes and their frequencies in Python, detection in cost order, polluter bisection, the leak census, retries and quarantine, fixes, and rerun statistics. Load it in phase 7 when a run or continuous integration (CI) history shows a failure and a pass at one commit. Also load it when you judge the project's retries, random order, or quarantine.

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Order-dependent test | Order sweep, `results.py flips`, then the classification table | Reproduced twice: trust breaker, `measured`, high confidence | The polluter undoes its change, or the victim builds its own state | 59% of Python flaky tests [1] |
| Retries that hide failures | Rerun settings in config and CI; rescued tests in `--timing-plugin` runs | A rescued test is flaky at that commit; trust breaker when history shows a hidden real failure | Retry, record, and fix the top offenders, each with an owner | 24% of flaky-test fixes changed product code, and 94% of those fixed a real bug [2] |
| Systemic cluster | CI history: many tests fail in one run with one error | Three or more tests with one error signature at one commit | Fix the shared cause once | Infrastructure caused 28% of Python flaky tests [1]; clusters average 13.5 tests [9] |
| Leaked process-global state | Leak census run; `rg` for direct mutation | A change survives teardown; a pair run confirms a victim | `monkeypatch`, yield fixtures, in-place restore | Cleanup removed the dependence in every studied fix [2] |
| Real network access | One run with sockets blocked | Any non-loopback connection: trust breaker | In-process fakes or recorded responses | 42 of 100 non-order Python flaky tests [1] |
| Random data and hash order | The failure follows a seed; `PYTHONHASHSEED` 0–9 | The outcome changes with a seed | Seed each test; compare sorted values | 37 of 100 non-order Python flaky tests [1] |
| Parallel-run conflict | `-n 0` against CI's `-n`; collection mismatch | Fails only with workers | Name resources per worker; port 0; `tmp_path` | 2% (processes) to 24% (threads) of tests failed in a Java study [8] |
| Resource leak | Strict warning filters | A test fails under them | `with` blocks, fixture teardown, joined threads | 2 of 100 [1]; also hides thread exceptions |
| Time and time zone | `risk-clock` hits, far time zones, boundary dates | Fails under a perturbation; a freeze never stopped | Inject or freeze the clock in a fixture | 4 of 100 [1], clustered on dates |
| Sleep-based wait | `risk-sleep` followed by an assert; contention runs | A flaky test sleeps, then asserts | Poll for the condition with a deadline | 0 of 20 sleep fixes worked; 23 of 42 polling fixes did [2] |
| Framework state | Django shuffle and reverse; async loop scope; Hypothesis profile | The documented leak reproduces | Clear caches; function-scoped loops; the "ci" profile | No published rate |
| Quarantine hygiene | Skips and xfails with flaky reasons, and their age | No owner, ticket, or exit rule; a passing non-strict xfail is a trust breaker | Fix with an owner; a kept quarantine keeps running | Slack's main-branch pass rate rose from about 20% to 96% [18] |
| Static risk signal | `static_scan.py` `risk-*` checks and `rg` | Never alone: low confidence | Choose the dynamic check | 2 of 75 registry-pattern hits were real (measured) |

## Signals

### Order-dependent tests

- **Detect**
  - Run the order sweep, then classify each candidate (see "Order sweep" and "Classify a failing test"). A victim passes alone and fails after a polluter. A brittle fails alone and passes after a state-setter [6].
  - `results.py flips` lists every test that both passed and failed in the sweep. On a 305-test synthetic suite, it listed the victim (5 of 8 runs failed), the brittle (3 of 8), and a random-data test (2 of 8) (verified). Classify every candidate before you report it.
  - Victims dominate: iFixFlakies found 100 victims among 110 order-dependent Java tests [6], and Gruber counted 3,168 victims against 738 brittles in Python [1].
  - Configuration: `-p no:randomly` in `addopts`; `@pytest.mark.order` or `@pytest.mark.dependency` markers, which couple tests on purpose; `--dist loadfile` or `loadscope` chosen because other modes fail. With `-q`, pytest-randomly prints no seed, so a CI log run with `-q` cannot replay its failures (verified).
- **False positives**: a random-data failure under pytest-randomly also fails with the same seed and `--randomly-dont-reorganize`, so it is a randomness finding. A failure that also occurs in file order is not an order effect. Deliberate order markers are a design note, not flakiness.
- **Fix**
  1. Make the polluter undo its change with `monkeypatch`, `tmp_path`, a yield fixture, or `request.addfinalizer`. In 14 of 19 order-dependency fixes, the fix set up or cleaned state, and each one removed the flakiness [2].
  2. Make the victim or brittle build its own state in a fixture. iFixFlakies patches were usually one statement copied from a cleaner or a state-setter [6].
  3. Remove the shared state: per-test instances, or injection instead of module globals. Merging dependent tests is a last resort (2 of 19 fixes [2]): it hurts readability and parallelism, and [findings.md](findings.md) treats `merge` as a removal-type action.

  For a registry that a base class fills (`__init_subclass__`, a metaclass, or a decorator), restore it in place. A `monkeypatch.setattr` copy fails when another module holds a reference to the original dict (verified).

  ```python
  @pytest.fixture(autouse=True)
  def _restore_plugin_registry():
      from myapp.plugins import _REGISTRY
      saved = dict(_REGISTRY)
      yield
      _REGISTRY.clear()
      _REGISTRY.update(saved)
  ```

- **Effect**: 59% of 7,571 flaky tests in 22,352 Python projects were order-dependent [1], and 50.5% in a Java sample [5]. Microsoft saw 0% among fixed flaky tests because its builds always ran one order [3]. A fixed order hides the dependency until test selection, sharding, or parallelism changes the order.
- **Verify**: rerun the failing orders (the same seeds, and reverse), then 5–10 new seeds. Run the pair both ways (see "Find the polluter"). Run the former polluter twice in one process with `--count=2` (pytest-repeat). When its registry rejects duplicate names, the unfixed polluter fails its second run (verified). Then run the tamper check from SKILL.md phase 9.

### Retries that hide failures

- **Detect**
  - Configuration: `rg -n "reruns|force-flaky|max-runs|--retries|only_rerun|rerun_except" pyproject.toml pytest.ini setup.cfg tox.ini .github .gitlab-ci.yml` and `rg -n "mark\.flaky|@flaky\b" TEST_ROOTS`. Also look for job retries in CI, such as GitLab's `retry:`.
  - Find the owner of `@pytest.mark.flaky`: pytest-rerunfailures, box/flaky, and pytest-retry all use that marker name, and pytest-rerunfailures is incompatible with box/flaky [24].
  - Measure rescued tests with one run of CI's command (see "Rerun rate and cost"). The timing plugin records each failed attempt as `"outcome": "rerun"`, also under xdist (verified).
  - Heuristic thresholds from the research, not from a study: a test rescued in more than 1 of the last 20 runs; more than 2% of pipelines green only after a rerun or a job retry; failed attempts above 5% of test time.
- **False positives**: retries limited to named infrastructure errors (`--only-rerun ConnectionResetError`), with rescues logged and triaged, are a sound policy. End-to-end tests against real services are nondeterministic by design; Meta computes a probabilistic flakiness score for them instead of forbidding retries [20].
- **Fix**: recommend "retry, record, and fix the top offenders", not a ban on retries.
  1. Record: publish per-test rescue counts from every CI run, with `--report-log` or from JUnit reports read by `results.py`. Recorded retries are a detector: at Atlassian, they caught 81% of flaky failures for some products [21]. Visibility alone cut Spotify's flakiness from 6% to 4% in two months [19].
  2. Narrow and cap: `--only-rerun` for infrastructure exceptions, `--rerun-except AssertionError`, `--max-suite-reruns N`, and `--rerun-show-tracebacks` to keep the evidence. A non-blocking monitoring job can add `--fail-on-flaky`, which exits with code 7 when a test passes only on a rerun.
  3. Fix the top offenders by rescue count and reach, each with a named owner and a deadline. GitHub scored flaky tests by the failures, branches, developers, and deploys they affected, and assigned owners from git blame [17].

  State the lost protection (guardrail 11): a retry turns an intermittent product bug green. In Luo's study, 24% of flaky-test fixes changed the code under test, and 94% of those fixed a real bug [2]; at Microsoft, 12% of fixes touched source code [3]. Name the counter-argument too: in a 30-developer industrial project, flaky tests took at least 2.5% of productive developer time. There, an automatic rerun cost 0.02 cents, while a failed pipeline's manual investigation cost 5.67 (the abstract gives no unit). The team therefore moved effort from repair to reruns [11].
- **Effect**: GitHub cut commits with a flaky red build from 1 in 11 to under 1 in 200 with detection, cause-classifying retries, and ownership [17]. After a restart, 47% of failing Travis builds passed, and projects that restarted builds merged pull requests 11 times more slowly (Durieux et al., cited in [8]). A flaky mark that reports failure only after three consecutive failures delays detection of a real break threefold [15].
- **Verify**: compare rescued tests and the failed-attempt share of test time over the same number of CI runs before and after. A known-bad commit must stay red.

### Systemic and infrastructure clusters

- **Detect**: in harvested CI history ([ci-history.md](ci-history.md)), group failures by run. Many unrelated tests that fail in one run with one error point at infrastructure, for example `ConnectionError`, `ModuleNotFoundError` after a failed install, or "No space left on device". Report a cluster of three or more tests with one error signature at one commit. Size predicts flakiness: at Google, 0.5% of small, 1.6% of medium, and 14% of large tests were flaky in a week [16].
- **False positives**: one real regression also fails many tests at once, and it persists when the same commit runs again.
- **Fix**: fix the shared cause once. Retry the dependency installation, pre-pull images, or check service health before the suite; this "look before you leap" fix was the most common one for clusters [9]. Move large end-to-end tests out of the gating job.
- **Effect**: infrastructure caused 28% of Python flaky tests [1]. In Java, 75% of 810 flaky tests failed in clusters of 13.5 tests on average, so one fix removes many flaky tests [9].
- **Verify**: the cluster's error signature disappears from CI history.

### Leaked process-global state

- **Detect**
  - Run the leak census once (see "Leak census"). It names the test during which each process-global change happened, including fixture setup and teardown.
  - Search for mutations that `static_scan.py` does not flag. Its `risk-env-mutation`, `risk-chdir`, and `risk-global-state` checks cover `os.environ[...] =`, `os.chdir`, `global` statements, writes to the test module's own module-level containers, and attributes of imported modules set without `monkeypatch`:

    ```sh
    rg -n "\.start\(\)" TEST_ROOTS | rg -i "patch|freeze|travel"
    rg -n "sys\.path\.(insert|append)|importlib\.reload|signal\.signal\(|logging\.basicConfig|addHandler\(|locale\.setlocale|time\.tzset|socket\.setdefaulttimeout|warnings\.simplefilter" TEST_ROOTS
    rg -n "__init_subclass__|metaclass=|lru_cache|functools\.cache" SRC_ROOTS
    ```

  - Python leak sources: `mock.patch(...).start()` without `stop()`; module-level containers in tests and conftest files; subclass registries that tests fill; `lru_cache` values that depend on settings or the environment. Session and module fixtures often mutate directly, because `monkeypatch` is function-scoped and requesting it there raises a ScopeMismatch error.
  - `-p no:warnings` in `addopts` stops pytest from restoring `warnings.filters` after each test. A test that called `warnings.simplefilter("ignore")` then broke the next test (verified). Treat every `-p no:<builtin>` in `addopts` as an isolation change.
  - CPython's own test runner reports "environment altered" for the same resources after each test; use its list as a checklist [39].
- **False positives**: the first test that uses a session fixture is blamed for the threads, handlers, or files that the fixture creates. A fixture's teardown is blamed on the last test in its scope (both verified). New `sys.modules` entries are lazy imports; only removed or replaced modules matter. Caches that fill up are normal unless the cached value depends on something a test changed.
- **Fix**
  1. Replace direct mutation with undo-aware tools: `monkeypatch.setenv`, `chdir`, `syspath_prepend`, `setattr`, `setitem`, and `tmp_path`. For broader scopes, use `pytest.MonkeyPatch.context()`.
  2. Use patchers as decorators, as context managers, or through pytest-mock's `mocker`. If `start()` is unavoidable, register the stop at once with `addCleanup(patcher.stop)` or a yield fixture.
  3. Join threads, stop servers, and restore signal and logging handlers in the fixture that created them.
  4. Restore registries in place (see "Order-dependent tests"), and clear keyed caches in an autouse fixture, for example `get_settings.cache_clear()` before and after `yield`.
- **Effect**: cleanup fixes removed the order dependence in every case Luo studied [2]. The skill's leak census (measured 2026-10-01) flagged 1 of arrow's 1,902 tests, and it was the real polluter [43]. In werkzeug's development branch, its churn list named `EnvironBuilder._form` and `_files`: class-level mutable defaults that two builder instances shared, filled by 12 and 9 tests [44]. In urllib3, it named the two tests whose timezone helper restores `TZ` to the zone's abbreviation, such as `CEST`, instead of unsetting it, which leaves later tests in UTC [49]. It flagged nothing in click [45].
- **Verify**: the census no longer lists the test, the order sweep passes, and the former polluter passes `--count=2`.

### Real network access

- **Detect**: run CI's command once with pytest-socket's `--disable-socket --allow-unix-socket`, which also blocks Domain Name System (DNS) lookups. If tests reach local services, such as a database on 127.0.0.1, use `--allow-hosts=127.0.0.1,::1` instead. The two modes do not stack: with `--allow-hosts`, lookups still leave the machine, and only connections to other hosts are blocked (pytest-socket 0.8.1, verified). Tests that reach the network fail with `SocketBlockedError` or `SocketConnectBlockedError`, which names the host. What the guard cannot see is in [traps.md](traps.md).
- **False positives**: service containers reached by host name. Add those hosts to `--allow-hosts`, or mark the tests as integration tests.
- **Fix**: use in-process fakes (`responses`, `respx`, or `pytest-httpserver`), or recorded responses (`vcrpy` or `pytest-recording`) for complex third-party APIs. Keep real-network tests in a separate non-blocking job that retries only connection errors. See [framework-runtime.md](framework-runtime.md).
- **Effect**: network access caused 42 of 100 sampled non-order Python flaky tests [1] and 55.6% of co-failing clusters in Java [9]. [findings.md](findings.md) lists tests that reach real external services as trust breakers.
- **Verify**: the suite passes with sockets blocked, and the fake still fails when the code sends a wrong request.

### Random data and unordered collections

- **Detect**
  - With pytest-randomly, a failure that reproduces with its seed, also under `--randomly-dont-reorganize`, and disappears under other seeds comes from random data. The plugin reseeds `random`, Faker, factory_boy, NumPy's legacy global state, Model Bakery, and Polyfactory before each test, from the seed and the test ID [25].
  - Hash order: rerun the suspect subset under `PYTHONHASHSEED` 0–9 (see "Perturbation runs"). A test that asserted the joined order of a four-string set passed under 2 of 10 seeds (verified).
  - Unsorted listings: `os.listdir`, `glob.glob`, and `Path.iterdir` results compared as lists.
  - The xdist error "Different tests were collected between gw0 and gw1" means parametrisation over a set, because each worker gets its own hash seed [29]. pytest-randomly hides this error by making collection order the same on every worker (verified).
- **False positives**: dicts keep insertion order; sets of small integers iterate in a stable order; random values that never reach an assertion are harmless.
- **Fix**: seed each test, and register other generators through the `pytest_randomly.random_seeder` entry point [25]. Compare `sorted()` values or sets instead of sequences, sort file listings, and fix the boundary that a random value can hit.
- **Effect**: randomness caused 37 of 100 sampled non-order Python flaky tests [1].
- **Verify**: the test passes under 10 hash seeds and 10 pytest-randomly seeds.

### Parallel-run conflicts (pytest-xdist)

- **Detect**
  - Compare failures under `-n 0` and under CI's `-n` over several runs. Put `-n 0` on the command line, where it overrides `addopts`; `-p no:xdist` makes pytest reject the `-n` still in `addopts` with "unrecognized arguments: -n" (verified).
  - Look for fixed external names, such as `/tmp/test.db`, `localhost:8000`, or fixed database and queue names, and for the session fixtures that create them. A session fixture runs once per worker, not once per run [30].
  - Record each worker's order with pytest-replay's `--replay-record-dir={RUN_DIR}/replay` [27].
- **False positives**: order dependence also appears under xdist, because each worker runs a different subset of tests. Replay the failing worker's order before you blame parallelism.
- **Fix**: name resources after the `worker_id` or `testrun_uid` fixture or `PYTEST_XDIST_WORKER`; use `tmp_path` and `tmp_path_factory`; bind to port 0 and read the port back; use the file-lock pattern for once-per-run setup [30]. `--dist loadgroup` with `@pytest.mark.xdist_group` is a stopgap that keeps the coupling. pytest-django already adds a per-worker suffix to the test database name [38].
- **Effect**: in a Java study, process-level parallelism left about 2% of tests failing and thread-level parallelism up to 24%, for speedups of 1.9 and 12.7 times (Candido et al., cited in [8]). A process per test removes in-memory coupling but hides the leak: it cost 618% extra time in Java (cited in [8]), and pytest-forked added about 17 ms per test (measured).
- **Verify**: `-n 0` and CI's `-n` give the same failures over several runs, and each replayed worker file passes.

### Resource leaks and thread exceptions

- **Detect**: run CI's command with `-W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning -W error::pytest.PytestUnhandledThreadExceptionWarning`. pytest then fails and names the test that dropped an unclosed file or whose thread died with an exception. By default, both tests passed with one summary warning (verified). Add `--env PYTHONTRACEMALLOC=20` for allocation tracebacks. For file descriptors with paths, `-p pytester --lsof` suits small subsets only: it runs lsof twice per test, and 300 trivial tests went from 0.7 s to 53 s (measured).
- **False positives**: third-party libraries that leak at interpreter shutdown, and files that the first importing test opens lazily.
- **Fix**: use `with` blocks or fixture teardown for files, sockets, servers, and clients. Join threads and propagate their exceptions, as `concurrent.futures` does. Close event loops and executors in fixtures.
- **Effect**: leaks caused 2 of 100 non-order Python flaky tests [1] and 5–7% in the Java and Mozilla studies [2][3][4]. Their larger cost is swallowed thread exceptions, which hide bugs.
- **Verify**: the strict-warnings run passes.

### Time and time zones

- **Detect**: take `static_scan.py`'s `risk-clock` hits, which skip tests that freeze the clock. Rerun the time-touching subset in the zones farthest from Coordinated Universal Time (UTC), `--env TZ=Pacific/Kiritimati` (UTC+14) and `--env TZ=Etc/GMT+12` (UTC−12). Also run it at boundary dates with time-machine: month end, 29 February, and daylight-saving changes. Look for `freeze_time(...).start()` or `time_machine.travel(...).start()` without a stop: a leaked freeze made pytest report the session as "18254 days", and run_suite.py could not parse that summary line, so its verdict was UNKNOWN (verified).
- **False positives**: `time.monotonic()` in timeout helpers. Code that needs local time should get a pinned zone in the test, not a switch to UTC.
- **Fix**: inject a clock, or freeze it with a decorator, a context manager, or a yield fixture that ends the freeze at teardown. Prefer time-machine in large projects, because freezegun rewrites references in every loaded module, which is slow and misses references inside objects and C extensions [32]. Pin `TZ` for the test process when the code uses local time, and compare aware datetimes.
- **Effect**: a small share (4 of 100 Python tests [1], 5 of 161 in Luo [2], 4% at Microsoft [3]), but the failures cluster on dates and zones. GitHub's detector retries failures with a shifted clock for this reason [17].
- **Verify**: the subset passes in both zones and at each boundary date.

### Sleep-based waits, timeouts, and hangs

- **Detect**: read `static_scan.py`'s `risk-sleep` hits. A sleep followed by an assertion is risky; a sleep inside a polling loop with a deadline is fine. Other signs are timeouts barely above typical durations, failing runs much slower than passing ones (22.3 s against 9.4 s in one Microsoft project [3]), and failures on slow runners. Run suspects under contention, with more workers than cores or fewer processors: in a 52-project study, 46.5% of flaky tests were resource-affected, and fewer resources exposed them cost-effectively [10]. For hangs, `-o faulthandler_timeout=300` dumps every thread's stack without stopping the test (verified).
- **False positives**: sleeps inside polling helpers, and tests of rate limiters.
- **Fix**
  1. Wait for the condition, not for time: poll with `time.monotonic()` and a deadline, or wait on an event or a future. In Luo's study, 23 of 42 fixes that waited for a condition removed the flakiness, and none of 20 sleep fixes did [2].
  2. Remove the asynchrony from unit tests: call the handler directly, use a synchronous executor, or mock the asynchronous boundary (15% of Microsoft's async-wait fixes mocked the call [3]).
  3. Adjust timeouts last, and state the lost protection. Raised waits were Microsoft's most common async fix (31%). Yet its timeout-tuning tool cut the run time of five such tests by up to 78% without changing their failure rates [3].
- **Effect**: async waits caused 45% of flaky-test fixes in Apache projects [2], 22% at Mozilla [4], and 78% at Microsoft [3]. In Python, they caused only 3 of 100 non-order flaky tests [1], so check network access and randomness first.
- **Verify**: run the fixed test under contention as many times as the old failure rate requires (see "Repeated runs").

### Framework state: Django, pytest-asyncio, and Hypothesis

- **Detect**
  - Django: caches are not cleared between tests [36]. `setUpTestData` objects must survive `copy.deepcopy`, and `override_settings` cannot reach settings copied into module constants [37]. Hard-coded primary keys depend on sequence state [38]. Signal receivers connected in tests need a `disconnect`. Django's runner has `--shuffle [SEED]` and `--reverse`, and it runs `TestCase` classes first, which can hide dependencies [36].
  - pytest-asyncio: 1.0.0 removed the `event_loop` fixture, and 1.1.0 cancels leftover tasks at the end of a loop scope. Broad `loop_scope` values let tasks cross test boundaries [35].
  - Hypothesis: since 6.116.0, a detected CI applies the built-in "ci" profile (`derandomize=True`, `deadline=None`, `database=None`, `print_blob=True`) [34]. A project profile loaded in CI replaces it. A runner without a `CI` or known vendor variable keeps random exploration and the 200 ms deadline (verified on 6.168.3) [33]. `FlakyFailure` means that one input failed and then passed.
- **False positives**: a Hypothesis failure that replays from its database or from `@reproduce_failure` is a real bug. `TransactionTestCase` tests that rely on flushed tables are normal.
- **Fix**: for Django, use an autouse `cache.clear()` or a per-test local-memory cache, read settings at call time, connect receivers in fixtures with teardown, and randomise sequence starts in `django_db_setup` [38]. Use pytest-randomly 5.0.0 or later with pytest-django, so the shuffle happens before database grouping [25]. Use function-scoped event loops by default. Keep the "ci" profile in the gating job, and run random exploration in a separate job.
- **Effect**: no study gives a rate. These are documented framework behaviours, so confirm each one with a shuffled or reversed run before you report it.
- **Verify**: shuffled, reversed, and sequence-randomised runs pass, and repeated CI runs show no `DeadlineExceeded` or `FlakyFailure`.

### Quarantine hygiene

- **Detect**: `rg -n "mark\.(skip|skipif|xfail)\(.*(flak|intermittent|random|race|timing)" TEST_ROOTS`, ticket references in skip reasons, marker age from `git log -L` or blame, and `static_scan.py`'s `xfail-not-strict` and `skip-unconditional` checks. Under pytest 9's `strict = true`, `strict_xfail` is on, so a quarantined xfail that passes fails the run unless it says `strict=False` [23]. Report quarantines without an owner, a ticket, or an exit rule, and any older than 30 days.
- **False positives**: platform skips, such as `skipif(sys.platform == "win32")`, are not quarantine.
- **Fix**: the audit never quarantines a test (guardrail 10). Recommend fixing the cause, with a named owner and a deadline. If the team keeps a quarantine, it must keep running the test: a `quarantine(reason, owner, until)` marker, `-m "not quarantine"` in the gating job, and `-m quarantine --reruns 2 --report-log=quarantine.jsonl` in a non-blocking job. Services can run the test and ignore its result, with an exit rule: Datadog marks a test fixed after 30 days without flaking [40], and Trunk overrides the exit code after reading the uploaded results [41]. State the loss: the gating job no longer protects that behaviour, and Google warns that automatic quarantine "could easily mask a real race condition" [15]. A skip gives no signal at all, and the pytest documentation calls a non-strict xfail "rather dangerous to use permanently" [22].
- **Effect**: Slack raised its main-branch pass rate from about 20% to 96% with automatic detection, disabling, and tickets. Its first design suppressed results, let real failures reach the main branch, and was rolled back [18].
- **Verify**: every quarantined test has an owner and a ticket, the quarantine job runs, and the number of quarantined tests falls over time.

### Static risk signals

- **Detect**: `static_scan.py`'s `risk-*` checks cover sleeps, clocks, randomness, network calls, subprocesses, threads, `chdir`, environment writes, and global state. Use them and the `rg` searches above only to choose subsets for dynamic checks. [findings.md](findings.md) caps flakiness findings with only static evidence at low confidence.
- **False positives**: most hits. In three open-source suites, 2 of 75 "class defined inside a test" hits were a real polluter (measured). The sleeps sat in polling loops, and a time library's 36 wall-clock calls were legitimate. See [traps.md](traps.md).
- **Fix**: refine each pattern with context, such as a sleep followed by an assertion, a subclass of a registering base, or `start()` without `stop()`. Then confirm it dynamically.
- **Effect**: learned predictors need labelled reruns, which an audit lacks. FlakeFlagger raised precision from 11% to 60% with dynamic features [12], Flakify reached F1 scores of 79% and 73% [13], and vocabulary-based classifiers score lower under stricter validation [14].
- **Verify**: report the share of hits that dynamic checks confirmed, as SKILL.md phase 4 asks.

## Measuring

Run every command through `run_suite.py run` (guardrail 3). Put the plugins that each recipe needs in an audit environment outside the project (guardrail 4): `uv run --with PLUGIN`, or a new throwaway virtual environment with the project's locked dependencies. `CI_TEST_COMMAND` runs with that environment's interpreter. Targeted runs use its `python -m pytest` with CI's options but without CI's path arguments.

- Override options instead of unloading plugins. The commands add `-n 0` for projects that use pytest-xdist; drop it otherwise. Add `--no-cov` when `addopts` passes `--cov`, because `-p no:pytest_cov` fails the same way as `-p no:xdist` (verified).
- Pass every seed explicitly with `-p randomly --randomly-seed=N`, which also overrides `-p no:randomly` in `addopts`. With `-q`, pytest-randomly prints no seed for run_suite.py to record, and `--randomly-seed=last` silently picks a new seed, because each run gets its own cache directory (all verified).
- Do not add `-p no:cacheprovider`. run_suite.py already keeps the cache out of the project, and pytest-leak-finder 0.3.0 crashes without the cache whenever it is installed (verified).
- Reproduce a CI seed only with CI's plugin versions: pytest-randomly 5.0.0 changed its hook order, and 4.0.0 changed the per-test seeds [25].

### Order sweep

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label order-file --timeout SECONDS --cwd ROOT --timing-plugin -- \
    CI_TEST_COMMAND -p no:randomly -n 0
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label order-reverse --timeout SECONDS --cwd ROOT --timing-plugin -- \
    CI_TEST_COMMAND -p no:randomly --reverse -n 0
for s in 1 2 3 4 5 6; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label order-seed-$s --timeout SECONDS --cwd ROOT --timing-plugin -- \
      CI_TEST_COMMAND -p randomly --randomly-seed=$s -n 0
done
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py flips AUDIT/runs/*-order-* --json-out AUDIT/results/order-flips.json
```

- Output: `pass P / fail F  TEST_ID` for each test that both passed and failed, and "classification: flaky at the same commit" when every manifest shows one commit and a clean tree. An untracked file makes the tree dirty; pass `--same-commit` only after you check that nothing the tests import changed.
- Cost: 2 + K serial runs for K seeds. When runs are expensive, start with the reverse run: on arrow's 1,902 tests, one 8-second reverse run failed both victims, and 3 of 6 seeds did (measured). Reverse order can miss dependencies that random order finds [25].
- When serial runs do not fit the budget, keep CI's `-n` and add `--replay-record-dir={RUN_DIR}/replay`, so that each worker's order stays replayable.

### Classify a failing test

| Check | Command | Reading |
| --- | --- | --- |
| Alone | `python -m pytest -p no:randomly "TEST_ID"` | Fails: a brittle, or a real failure. Passes: continue. |
| Failing order again | The same seed or `--reverse`; for one worker, `python -m pytest -p no:randomly -n 0 --replay=REPLAY_FILE` | Fails again: order-dependent. Passes: not order-dependent. |
| Same seed, order kept | `CI_TEST_COMMAND -p randomly --randomly-seed=N --randomly-dont-reorganize -n 0` | Still fails: random data, not order. |
| Same order, repeated | `python -m pytest -p no:randomly --count=30 "TEST_ID"` | Mixed results: not order-dependent; the failure rate is failures ÷ runs. |
| Perturbed environment | See "Perturbation runs" | The perturbation that flips the result names the cause. |

This follows iDFlakies, which reruns the failing order and a passing order to separate order-dependent tests from other flaky tests [5].

### Find the polluter

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label bisect-1 --timeout SECONDS --cwd ROOT \
    --env "PYTEST_ADDOPTS=-n 0" -- detect-test-pollution --failing-test "VICTIM_ID" --tests TEST_DIR
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label pair-polluter-first --timeout 600 --cwd ROOT -- \
    python -m pytest -p no:randomly -n 0 "POLLUTER_ID" "VICTIM_ID"
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label pair-victim-first --timeout 600 --cwd ROOT -- \
    python -m pytest -p no:randomly -n 0 "VICTIM_ID" "POLLUTER_ID"
```

- detect-test-pollution runs `sys.executable -m pytest -p no:randomly` and passes no other options. Install it in the audit environment, which holds the project's dependencies, not with `uvx`, and pass options through `PYTEST_ADDOPTS` [26]. It checks that the victim passes alone and fails after all candidates, then halves the candidates; it assumes one polluter.
- Output: the last line of `output.log` reads `-> the polluting test is: TEST_ID`. run_suite.py's verdict is UNKNOWN, because the tool prints no pytest summary. The manifest's exit code is 0 when the tool found a polluter. For a brittle, it stops with "-> test failed!" and exit code 1 (verified).
- The pair runs are the COMPLETE runs to cite: the victim fails after the polluter and passes before it. pytest runs node IDs in command-line order, even within one file (verified).
- Cost: about log2(N) halving steps, roughly two runs of the candidate set. It took 9 steps and 6 s on a 305-test suite, and 11 steps and 37 s on a 1,902-test suite that runs in 7–10 s (measured).
- Under xdist, bisect only the tests that ran before the victim on its worker. Find that worker's file with `grep -lF 'VICTIM_ID' AUDIT/runs/NN-LABEL/replay/.pytest-replay-gw*.txt`, write the candidate list with this command, and pass `--testids-file AUDIT/before-victim.txt` instead of `--tests`. The command fails with `ValueError` when the victim did not run on that worker (verified):

  ```sh
  python3 -c "import json,sys; v=sys.argv[2]; ids=[r['nodeid'] for r in map(json.loads, open(sys.argv[1])) if 'finish' in r]; print('\n'.join(ids[:ids.index(v) + 1]))" \
      AUDIT/runs/NN-LABEL/replay/.pytest-replay-gwN.txt "VICTIM_ID" > AUDIT/before-victim.txt
  ```

- For a brittle, bisect by hand. Run each half of the tests that preceded it in a passing order, then the brittle, and keep the half that makes it pass.
- Alternatives: pytest-bisect-tests passes options with `--run-options` but calls `pytest` from `PATH` [47]. pytest-find-dependencies runs forward and backward and then bisects, at about 1.5 times the suite time per dependency, and reports brittles only as "failing permanently" [46]. Do not rely on pytest-leak-finder 0.3.0 alone: it skips the alone-check and named an unrelated test for a brittle (measured) [48].

### Leak census

`run_suite.py run --leak-probe PACKAGES` loads the skill's `pytest_audit_leaks` plugin through `PYTHONPATH` and `PYTEST_ADDOPTS`, without installing anything. It observes only and restores nothing.

- **What it checks:** after each test, including the test's fixture setup and teardown, it compares process state with the state after the previous test. The process state is the working directory, `os.environ`, `sys.path`, live thread names, mock patches started and not stopped, root logging handlers, signal handlers, and removed or replaced `sys.modules` entries.
- **With PACKAGES:** for each comma-separated package prefix, it also checks every module-level and class-level attribute. "Rebound" means the name points at another object, such as a patch never undone or a changed setting. "Rebound, was None" often means lazy initialisation. "Contents changed" means a dict, list, or set, or a subclass of one, changed in its first 200 entries. Numbers, strings, and None compare by value, so an equal copy counts as no change.
- **Order:** run it first with `--leak-probe ''`, which checks process state only and costs almost nothing. Then name the project's own packages, as narrowly as the question allows. Test modules in folders without `__init__.py` import under their bare file names, such as `test_inventory`, so add `test_` to PACKAGES to check their module-level state.

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label leak-census --timeout SECONDS --cwd ROOT \
    --leak-probe PACKAGES -- CI_TEST_COMMAND -p no:randomly -n 0
```

- Add `-n 0` when the command or `addopts` passes `-n`; without pytest-xdist installed, `-n 0` is an unknown option. Under xdist the plugin stops with a usage error, because the workers' results never reach the controller, and run_suite.py warns that it wrote no `leaks.json`. `-p no:randomly` keeps the order reproducible for the pair runs that follow.
- **Output:** `leaks.json` in the run folder. "changes" maps each test ID to what changed during it. "churn" lists each change seen in more than 5 tests once, with the number of tests and the first three. Churn is often a counter or a cache, but it can be a shared mutable default that many tests fill, so check each entry. The run counts as instrumented, so its timings never support a speed finding.
- **Triage:** discount the false-positive patterns in "Leaked process-global state", then confirm each remaining hit with a pair run or `--count=2`. A hit without a victim is a latent risk: low impact, medium confidence.
- **Cost (measured, 2026-10-01):**

  | Suite | Tests | Plain | `--leak-probe ''` | With PACKAGES |
  | --- | --- | --- | --- | --- |
  | arrow 2224255 | 1,902 | 7.6 s | – | 11.6 s (`arrow`) |
  | click 06b2a67 | 2,266 | 9.9 s | – | 12.6 s (`click`) |
  | urllib3 8b05e57, unit tests | 1,629 | 21.4 s | – | 27.1 s (`urllib3`) |
  | SymPy 2d283a8, `sympy/core/tests` | 2,084 | 20.5 s | 21.4 s | 29.6 s (`sympy.core`), 95.1 s (`sympy`) |

- **Limits:** it sees only in-process state, not databases, files, or services. It misses attributes that a test adds or deletes, a change nested inside an unchanged object, and a change past a container's 200th entry.
- **Evidence:** the plugin's tests catch eight planted leak types and nothing from equivalents that use `monkeypatch` or restore an equal copy. On real suites, see "Leaked process-global state".

### Repeated runs

To see at least one failure with confidence c when a run fails with probability p, you need n = ⌈ln(1 − c) ÷ ln(1 − p)⌉ runs:

| Failure rate p | 50% | 90% | 95% | 99% |
| --- | --- | --- | --- | --- |
| 20% | 4 | 11 | 14 | 21 |
| 10% | 7 | 22 | 29 | 44 |
| 5% | 14 | 45 | 59 | 90 |
| 1% | 69 | 230 | 299 | 459 |
| 0.1% | 693 | 2,302 | 2,995 | 4,603 |

- After N clean runs, the 95% upper bound on p is 1 − 0.05^(1/N), close to 3/N: 26% after 10 runs, 5.8% after 50, 3.0% after 100, and 1.0% after 300. Never accept a fix on a handful of green runs; some fixes claimed at Microsoft did not change the failure rate [3].
- Gruber needed 170 reruns for 95% confidence that a Python test has no non-order flakiness, and 10 reruns found at most 33% of such tests [1]. At Microsoft, 500 reruns reproduced only 17–43% of known flaky tests [3]. One pass after a failure proves a test flaky; no practical run count proves it healthy.
- Suite level: with independent per-test probability p, T tests all pass with probability (1 − p)^T. At p = 10⁻⁴, that is 90.5% for 1,000 tests and 36.8% for 10,000; at p = 10⁻⁵, it is 90.5% for 10,000 and 36.8% for 100,000. A 99% green rate at 10,000 tests needs p ≈ 10⁻⁶, which takes about 3 million runs to confirm for one test. So set any flakiness budget at suite level, and fix the worst tests first.
- Independence is an assumption. Polluter and infrastructure failures correlate within a session or on one machine, so spread reruns over fresh sessions.

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label count-TEST --timeout SECONDS --cwd ROOT -- \
    python -m pytest -p no:randomly -n 0 --count=N "TEST_ID"
```

- pytest-repeat gives each repetition its own test ID, so the summary line gives the failure count, and pytest-randomly gives each repetition new random data (verified). Same-process repeats share state. For a rate across fresh sessions, run the call K times without `--count`, with `--timing-plugin` and labels `repeat-1` to `repeat-K`, then run `results.py flips AUDIT/runs/*-repeat-*`.
- Cost: N times the test's own time for `--count=N`, and K runs of the selection for fresh sessions.

### Rerun rate and cost

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label ci-reruns --timeout SECONDS --cwd ROOT --timing-plugin -- CI_TEST_COMMAND
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary AUDIT/runs/NN-ci-reruns --json-out AUDIT/results/ci-reruns.json
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py flips AUDIT/runs/NN-ci-reruns
python3 -c "import json,sys; r=[json.loads(l) for l in open(sys.argv[1])]; t=sum(x['duration'] for x in r); u=sum(x['duration'] for x in r if x['outcome']=='rerun'); print(f'failed attempts: {100*u/t:.1f}% of recorded test time')" AUDIT/runs/NN-ci-reruns/timing.jsonl
```

- Keep CI's own rerun options, because you measure what they rescue. Do not add `--fail-on-flaky` (see the traps table).
- `summary` prints "tests with reruns" with each test's final outcome. `flips` counts a rescued test as one failure and one pass, so one run shows that it is flaky at that commit (verified).
- The time share counts only the failed phase of each attempt, so it is a lower bound when setup is expensive.
- In CI artifacts, pytest-rerunfailures writes each attempt as a separate `<testcase>` without a failure, and `results.py` counts the repeats (see [traps.md](traps.md)). Terminal logs show `N rerun` (pytest-rerunfailures) or `N retried` (pytest-retry); box/flaky's summary line shows no reruns (measured). For rates across CI runs, see [ci-history.md](ci-history.md).

### Perturbation runs

Each is one run of the chosen subset. Add `--timing-plugin`, so that `results.py flips` can compare the runs.

```sh
for s in 0 1 2 3 4 5 6 7 8 9; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label hash-$s --timeout SECONDS --cwd ROOT --timing-plugin \
      --env PYTHONHASHSEED=$s -- python -m pytest -p no:randomly -n 0 SUBSET
done
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py flips AUDIT/runs/*-hash-*
```

| Cause | Change to the run | Note |
| --- | --- | --- |
| Time zone | `--env TZ=Pacific/Kiritimati`, then `--env TZ=Etc/GMT+12` | "Today" differs from UTC for most of the day |
| Network | `--disable-socket --allow-unix-socket`, or `--allow-hosts=127.0.0.1,::1` for local services | The modes do not stack; with `--allow-hosts`, DNS lookups still leave the machine |
| Resource leaks | The three `-W error::` filters from "Resource leaks and thread exceptions" | Add `--env PYTHONTRACEMALLOC=20` for tracebacks |
| Contention | `-n` with more workers than cores | On the suspect subset only |
| Hangs | `-o faulthandler_timeout=300` | Dumps stacks without stopping the test |
| Locale | `--env LC_ALL=tr_TR.UTF-8` | Falls back to `C` silently when the locale is not installed |

Check that each perturbation applied before you conclude that a test does not depend on it.

### Traps in these tools

| Trap | Effect | Guard |
| --- | --- | --- |
| pytest-randomly's per-test reseeding | A random-data failure follows the seed: a same-seed rerun fails again ("1 failed, 3 rerun"), and the next CI seed passes | Record the seed with every failure, and use CI's plugin versions |
| pytest-randomly under xdist | Hides the set-parametrisation collection error | Check collection once with `-p no:randomly -n 2` |
| pytest-timeout's `thread` method | Calls `os._exit`: no JUnit XML, no teardown, and an UNKNOWN verdict; under xdist, "worker 'gw0' crashed" | The `signal` method on Linux and macOS (it clashes with code that uses `SIGALRM`) [28], or `faulthandler_timeout` for stack dumps |
| `--fail-on-flaky` in an audit run | Exit code 7 makes run_suite.py label the run PARTIAL | Count rescues in `timing.jsonl` |
| Same-process reruns | Class-scoped and broader fixtures are not rebuilt; before pytest-rerunfailures 16.5, the test-class instance was reused [24] | Measure rates in fresh sessions |
| pytest-rerunfailures with box/flaky or pytest-forked | The plugins are incompatible, and three plugins use the `flaky` marker | Find the marker's owner first |
| detect-test-pollution through `uvx` | Its `sys.executable` lacks the project's dependencies, so the alone-check fails | Install it in the audit environment |
| A leaked clock freeze | pytest reports "18254 days", and run_suite.py cannot parse the summary (UNKNOWN) | Find the unstopped freeze |
| pytest-replay files | Dotfiles, so `ls` and `*` globs miss them | Glob `.pytest-replay-gw*.txt` |
| A leak census under xdist | The plugin stops with a usage error, and run_suite.py warns that it wrote no `leaks.json` | Run it with `-n 0` |

## Tools

Versions and dates come from the PyPI JSON API on 2026-09-30 [42]. The research installed every tool below with pytest 9.1.1 on CPython 3.14.0. For random order and retries in other runners, see [runners-and-ecosystems.md](runners-and-ecosystems.md).

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| pytest | Strict warning filters, `faulthandler_timeout`, `-p pytester --lsof`, `strict` | 9.1.1, 2026-06-19, yes | `strict = true` turns on `strict_xfail` [23] |
| pytest-randomly | Random order with a seed, and per-test reseeding | 5.0.0, 2026-09-01, yes | Active once installed; `--randomly-dont-reorganize` keeps the order [25] |
| pytest-reverse | One reverse-order run | 1.9.0, 2025-09-09, yes | `--reverse` |
| detect-test-pollution | Bisecting a victim's polluter | 1.2.0, 2023-09-28; repository active 2026-09 | One polluter; refuses brittles; `--fuzz` shuffles until a failure [26] |
| pytest-bisect-tests | Bisection with pytest options | 0.3.0, 2024-06-09, partly | Calls `pytest` from `PATH` [47] |
| pytest-find-dependencies | Forward and backward runs, then bisection | 0.6.0, 2025-07-16, yes | About 1.5 times the suite time per dependency [46] |
| pytest-leak-finder | Step-wise bisection across invocations | 0.3.0, 2025-12-19, partly | No alone-check; breaks `-p no:cacheprovider` [48] |
| pytest-replay | Recording and replaying each worker's order | 1.7.1, 2025-12-23, yes | Keep the files as CI artifacts [27] |
| pytest-rerunfailures | Reruns, the practice you measure | 16.7, 2026-09-17, yes | `--only-rerun`, `--rerun-except`, `--max-suite-reruns`, `--fail-on-flaky` [24] |
| flaky (box) | Rerun decorator | 3.8.1, 2024-03-12, partly | Its summary line hides reruns |
| pytest-retry | Reruns with delays | 1.7.0, 2025-01-19, partly | Prints `N retried`; reuses the `flaky` marker |
| pytest-repeat | Repeating a test in one session | 0.9.4, 2025-04-07, yes | `--count=N`, `--repeat-scope` |
| pytest-timeout | Per-test time limits | 2.4.0, 2025-05-05, yes | Choose the `signal` method [28] |
| pytest-socket | Blocking network access | 0.8.1, 2026-08-19, yes | Blind spots in [traps.md](traps.md) [31] |
| pytest-xdist | Parallel workers | 3.8.0, 2025-07-01, yes | Per-worker hash seeds; `worker_id`, `testrun_uid` [30] |
| pytest-forked | A process per test | 1.7.5, 2026-08-08, yes | About 17 ms per test; hides leaks |
| pytest-reportlog | JSON-lines log with rerun outcomes, for CI | 1.0.0, 2025-11-11, yes | The timing plugin covers audit runs |
| time-machine | Fast clock control | 3.5.1, 2026-09-08, yes | C extension [32] |
| freezegun | Clock control | 1.5.5, 2025-08-09, partly | Slow with many modules; `start()` without `stop()` leaks |
| pytest-asyncio | Asynchronous tests | 1.4.0, 2026-05-26, yes | 1.0 removed `event_loop` [35] |
| Hypothesis | Property-based tests | 6.168.3, 2026-09-28, yes | The "ci" profile needs a CI variable [33] |

## Evidence

Claims marked (measured) or (verified) come from runs made for this skill on 2026-09-30 with pytest 9.1.1 on CPython 3.14.0.

- Gruber et al. 2021: 876,186 tests in 22,352 Python projects, 400 runs each; 7,571 flaky tests (0.86%) in 4.5% of projects; 59% order-dependent, 28% infrastructure, 13% other; of 100 non-order tests, network 42, randomness 37, input and output 7, time 4, async wait 3, concurrency 3, resource leak 2 [1].
- Luo et al. 2014: 161 classified fixes in 51 Apache projects; async wait 45%, concurrency 20%, order 12%; 0 of 20 sleep fixes and 23 of 42 condition waits removed flakiness; 24% of fixes changed the code under test, and 94% of those fixed a real bug [2].
- Lam et al. 2020, Microsoft: 2,089 flaky tests; async wait 78% of fixes, and order 0% under a fixed order; 12% of fixes touched source code; 500 reruns reproduced 17–43% [3].
- Eck et al. 2019, Mozilla: 200 fixed flaky tests; concurrency 26%, async wait 22%, order 11%, resource leak 7%; 73% of 121 developers stop trusting a flaky test [4].
- Lam et al. 2019, iDFlakies: 422 flaky tests in 82 Java projects, 50.5% order-dependent [5].
- Shi et al. 2019, iFixFlakies: 100 victims and 10 brittles among 110 order-dependent tests; patches were usually one statement [6].
- Wang, Chen, and Lam 2022, iPFlakies: only 64% of the affected Python suites reran without errors, and 57% of known order-dependent tests reproduced, so do not expect every CI flake to reproduce locally [7].
- Parry et al. 2022 survey: 47% of restarted failing builds then passed, with merges 11 times slower; parallelism left 2% to 24% of Java tests failing; a process per test cost 618% extra time [8].
- Parry et al. 2025: 75% of 810 flaky Java tests failed in clusters of 13.5 on average; networking caused 55.6% of clusters [9].
- Silva et al. 2023: 46.5% of flaky tests in 52 Java, JavaScript, and Python projects were resource-affected [10].
- Leinen et al. 2024: flaky tests took at least 2.5% of productive developer time; a rerun cost 0.02 cents, and a manual investigation 5.67 without a stated unit [11].
- Learned predictors, all needing labelled reruns: FlakeFlagger 60% precision [12]; Flakify F1 scores of 79% and 73% [13]; vocabulary classifiers lower under stricter validation, on 837 Python flaky tests [14].
- Google 2016: 1.5% of test runs flaky; 84% of pass-to-fail transitions involved a flaky test [15].
- Google 2017: 0.5%, 1.6%, and 14% of small, medium, and large tests flaky in a week [16].
- GitHub 2020: flaky red builds fell from 9% to under 0.5% of commits; three retry modes classified 90% of flaky failures [17].
- Slack: main-branch pass rate from about 20% to 96%, and test-job failures from 57% to 3.85% [18].
- Spotify 2019: flakiness from 6% to 4% in two months, from a visible table of flaky tests [19].
- Atlassian: 7,000 unique flaky tests; flakiness behind up to 21% of one product's main-branch failures; retries detected 81% of flaky failures for some products [21].
- Measured: arrow at commit 2224255 had one polluter and two victims, found by one reverse run, 3 of 6 seeds, bisection in 11 steps, and one census hit [43]. Werkzeug at f7e37f0 had no order dependence and one shared-state defect flagged through 17 tests [44]. Click at 06b2a67 had neither [45].

## Sources

1. https://arxiv.org/pdf/2101.09077 – Gruber et al. 2021, "An Empirical Study of Flaky Tests in Python" (ICST).
2. https://huang.isis.vanderbilt.edu/cs8395/paper/flakytest.pdf – Luo et al. 2014, "An Empirical Analysis of Flaky Tests" (FSE).
3. https://people.cs.gmu.edu/~winglam/publications/2020/LamETAL20FaTB.pdf – Lam et al. 2020, "A Study on the Lifecycle of Flaky Tests" (ICSE), Microsoft.
4. https://arxiv.org/pdf/1907.01466 – Eck et al. 2019, "Understanding Flaky Tests: The Developer's Perspective" (FSE).
5. https://people.cs.gmu.edu/~winglam/publications/2019/LamETAL19iDFlakies.pdf – Lam et al. 2019, iDFlakies (ICST).
6. https://people.cs.gmu.edu/~winglam/publications/2019/ShiETAL19iFixFlakies.pdf – Shi et al. 2019, iFixFlakies (FSE): victims, brittles, polluters, cleaners, and state-setters.
7. https://people.cs.gmu.edu/~winglam/publications/2022/WangETAL22iPFlakies.pdf – Wang, Chen, and Lam 2022, iPFlakies (ICSE demo).
8. https://eprints.whiterose.ac.uk/id/eprint/230095/1/parry2021.pdf – Parry et al., "A Survey of Flaky Tests" (TOSEM 2022).
9. https://arxiv.org/html/2504.16777v1 – Parry et al. 2025, "Systemic Flakiness" (EASE).
10. https://arxiv.org/abs/2310.12132 – Silva et al. 2023, computational resources and flaky tests, abstract.
11. https://portal.fis.tum.de/en/publications/cost-of-flaky-tests-in-continuous-integration-an-industrial-case-/ – Leinen et al. 2024, "Cost of Flaky Tests in Continuous Integration" (ICST), abstract.
12. https://2021.icse-conferences.org/details/icse-2021-papers/115/FlakeFlagger-Predicting-Flakiness-Without-Rerunning-Tests – Alshammari et al. 2021, FlakeFlagger, abstract.
13. https://arxiv.org/abs/2112.12331 – Fatima, Ghaleb, and Briand, Flakify (TSE 2022), abstract.
14. https://arxiv.org/abs/2103.12670 – Haben et al. 2021, vocabulary-based flakiness prediction with Python data (MSR), abstract.
15. https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html – Google Testing Blog 2016, flaky tests at Google.
16. https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html – Google Testing Blog 2017, where flaky tests come from.
17. https://github.blog/engineering/reducing-flaky-builds-by-18x/ – GitHub engineering, reducing flaky builds 18 times.
18. https://slack.engineering/handling-flaky-tests-at-scale-auto-detection-suppression – Slack engineering, flaky-test detection and suppression.
19. https://engineering.atspotify.com/2019/11/test-flakiness-methods-for-identifying-and-dealing-with-flaky-tests – Spotify engineering, test flakiness.
20. https://engineering.fb.com/2020/12/10/developer-tools/probabilistic-flakiness/ – Meta engineering, probabilistic flakiness.
21. https://www.atlassian.com/blog/atlassian-engineering/taming-test-flakiness-how-we-built-a-scalable-tool-to-detect-and-manage-flaky-tests – Atlassian engineering, flaky-test detection at scale.
22. https://docs.pytest.org/en/stable/explanation/flaky.html – pytest documentation, flaky tests.
23. https://docs.pytest.org/en/stable/changelog.html – pytest changelog, 9.0.0 strict mode.
24. https://github.com/pytest-dev/pytest-rerunfailures – pytest-rerunfailures README and changelog, 16.7.
25. https://github.com/pytest-dev/pytest-randomly – pytest-randomly README and changelog, 5.0.0 and 4.0.0.
26. https://github.com/asottile/detect-test-pollution – detect-test-pollution README and source, 1.2.0.
27. https://github.com/ESSS/pytest-replay – pytest-replay README, 1.7.1.
28. https://github.com/pytest-dev/pytest-timeout – pytest-timeout README, 2.4.0.
29. https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html – pytest-xdist known limitations: collection order.
30. https://pytest-xdist.readthedocs.io/en/stable/how-to.html – pytest-xdist how-to: `worker_id`, `testrun_uid`, once-per-run fixtures.
31. https://github.com/miketheman/pytest-socket – pytest-socket README, 0.8.1.
32. https://time-machine.readthedocs.io/en/latest/comparison.html – time-machine comparison with freezegun.
33. https://hypothesis.readthedocs.io/en/latest/reference/api.html – Hypothesis settings, the "ci" profile, and flaky errors.
34. https://hypothesis.readthedocs.io/en/latest/changelog.html – Hypothesis changelog, CI detection in 6.116.0.
35. https://pytest-asyncio.readthedocs.io/en/stable/reference/changelog.html – pytest-asyncio changelog, 1.0.0 to 1.4.0.
36. https://docs.djangoproject.com/en/stable/topics/testing/overview/ – Django testing overview: order, caches, `--shuffle`, `--reverse`.
37. https://docs.djangoproject.com/en/stable/topics/testing/tools/ – Django testing tools: `setUpTestData`, `override_settings`.
38. https://pytest-django.readthedocs.io/en/latest/database.html – pytest-django database setup: per-worker names, randomised sequences.
39. https://github.com/python/cpython/blob/main/Lib/test/libregrtest/save_env.py – CPython's saved test environment resources.
40. https://docs.datadoghq.com/tests/flaky_management/ – Datadog flaky test management states and policies.
41. https://docs.trunk.io/flaky-tests/quarantining – Trunk quarantine mechanism.
42. https://pypi.org/pypi/{package}/json – PyPI JSON API, source of every version and date in the tools table.
43. https://github.com/arrow-py/arrow – arrow repository, measured at commit 2224255.
44. https://github.com/pallets/werkzeug – werkzeug repository, measured at commit f7e37f0.
45. https://github.com/pallets/click/blob/main/pyproject.toml – click repository, measured at commit 06b2a67.
46. https://github.com/mrbean-bremen/pytest-find-dependencies – pytest-find-dependencies README, 0.6.0.
47. https://github.com/maciej-gol/pytest-bisect-tests – pytest-bisect-tests README, 0.3.0.
48. https://github.com/mgaitan/pytest-leak-finder – pytest-leak-finder README, 0.3.0.
49. https://github.com/urllib3/urllib3/blob/main/test/tz_stub.py – urllib3's `stub_timezone_ctx`, measured at commit 8b05e57.
