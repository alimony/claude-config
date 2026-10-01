# Framework runtime and I/O isolation

This page covers the framework settings and external input and output (I/O) that make tests slow or nondeterministic. The topics are password hashers, logging, caches, storage, test clients, async runners, network and Domain Name System (DNS) lookups, clocks, randomness, Hypothesis, background jobs, command-line interface (CLI) tests, and browsers. Load it in phase 7 when the baseline, a profile, or the test settings point at any of these. Database setup and test data belong to [database-and-data.md](database-and-data.md), and flakiness root causes to [flakiness.md](flakiness.md). Numbers cited to [1] are micro-benchmarks on one shared machine: read them as orders of magnitude, not as predictions for continuous integration (CI) runners.

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| 1. Production-strength password hashing | M1 settings snapshot; key-derivation functions in a profile (M3) | The first test hasher is not MD5 and tests set passwords | `MD5PasswordHasher` first in test settings; low work factors in other stacks | 130 ms against 0.03 ms per hash [1]; 73% and 82.8% of runtime in two case studies [2, 3] |
| 2. Tests that reach real services | pytest-socket on a sample (M5); I/O audit (M4) | Any non-loopback connect or lookup outside a marked integration group | Block the network in CI; mock at the client; fake credentials | Trust breaker; each call costs a round trip, a failing one its full timeout |
| 3. Real sleeps and retry delays | `risk-sleep` in the static scan; `sleep_s` in M4 | Over 1 s of real sleep per 100 tests, or one test over 0.5 s | Inject the clock and the sleeper; wait on events; zero retry delays | At least the sleep total; about 7,000 async tests in 2 minutes with fake loop time [4] |
| 4. App factory or lifespan per test | `results.py fixtures` (M2) | A function-scoped app or client fixture costs 2% of wall time or more | Build once per session; reset state per test | 78 ms per FastAPI app with 200 routes, 13 minutes per 10,000 tests [1] |
| 5. CLI tests through a subprocess | `risk-subprocess`; `subprocess.Popen` counts in M4 | Many tests start the project's own CLI in a new process | `CliRunner` or `main(argv)` in process; one smoke test per entry point | 48 µs against 57–468 ms per call [1] |
| 6. Browser per test, recording every test | M2; CI flags | A browser launch per test, or `retain-on-failure` tracing or video in the main run | One browser per session, one context per test; trace in a rerun | 1,422 ms per launch against 1.3 ms per context; tracing +28% [1] |
| 7. freezegun in a large import graph | M7 cost times freezes per run | Freezes cost 2% of wall time or more (a few hundred freezes at least) | Migrate to time-machine; set `TZ=UTC` | 1.7–5.1 ms against 1.7 µs per freeze [1]; 41 ms at 16,259 modules [5] |
| 8. Debug and log capture turned up | Configuration search; run header | `--log-level=DEBUG`, `django_debug_mode`, or asyncio debug in the main job | Default levels; `caplog.set_level` per test; debug in one scheduled job | 165 ms against 1.8 ms per 20,000 records; asyncio debug 25–27 times slower [1] |
| 9. Shared or remote backends | M1 | Redis, Memcached, object storage, manifest static storage, or a toolbar in test settings | `LocMemCache` cleared per test; `InMemoryStorage`; `StaticFilesStorage` | Determinism across tests and workers; no general effect size |
| 10. Hidden DNS latency | `dns_s` in M4 | A lookup of 1 s or more, or a host with seconds of total lookup time | IP literals or `/etc/hosts` names; patch `socket.getfqdn` | Up to 5 s per lookup (5,002 ms for a `.local` name on macOS) [1] |
| 11. Expensive Hypothesis tests | M8; profile code | One property test dominates its file's time, or a conftest overrides the `ci` profile | Cheaper bodies; explicit profiles plus a nightly run | About `max_examples` times the body time: 0.68 s for 100 × 6 ms [1] |
| 12. HTTP mocks that do not guard | Client and mock pairing; decorator defaults | A mock for a client the code does not use, or `@responses.activate` without the assertion | Assert in both directions; match on payloads | Effectiveness, not speed |
| 13. Cassettes, emulators, containers | Record mode; container fixture scope (M2) | vcrpy's default `once` in CI, or a container per test | `--record-mode=none --block-network`; session-scoped containers | Stops live calls and leaked secrets; 1 s default readiness poll [6] |
| 14. Eager mode as the only task test | Settings search | `task_always_eager` and no test with a real worker | Task bodies as functions; a small real-worker group | Escaped defects, not time |
| 15. Unseeded randomness and IDs | Seed in the run header; `risk-random` | No seed in CI logs, or tests that assert on generated IDs | pytest-randomly; an injected ID factory | Failures you can replay |
| 16. Event-loop and test-client errors | Run header; search for `event_loop` and `TestClient(` | "attached to a different loop", "Event loop is closed", or hangs | `loop_scope`; the client in a `with` block; resources in lifespan | Correctness; the loop itself costs about 20 µs per test [1] |

### Changes that do not pay

Do not recommend these. Each one is a common belief that a measurement or the source code contradicts.

- Widening the event-loop scope for speed. A new loop per test cost about 20 µs more than a reused one, 0.2 s per 10,000 tests [1]. The saving comes only from sharing an expensive async fixture, and a shared loop also shares state.
- Moving from `TestClient` to `httpx.AsyncClient` for speed. The difference was 0.1–0.4 ms per request [1]. Recommend it for event-loop correctness instead.
- Setting `EMAIL_BACKEND` to locmem in Django test settings. `setup_test_environment()` already forces it [7]; look for code that escapes it.
- Setting `DEBUG = False` in Django test settings. Both Django's runner and pytest-django already force it, unless `django_debug_mode` says otherwise [8, 9].
- `DummyCache` as the test cache. It removes behaviour that code may rely on for correctness [10]; use `LocMemCache` and clear it.
- "Eager mode hides serialization bugs." `delay()` and `apply_async()` round-trip their arguments in eager mode, since at least Celery 4.4.7 [11]. The real gaps are the caller's transaction, immediate retries, and worker behaviour.
- A green `--disable-socket` run as proof of isolation. C clients such as libpq bypass it [1].
- `--tracing retain-on-failure` as free. It records and writes a trace for every test [12].
- One whole-suite timing as proof of a speed-up. Identical runs varied from 3.5 s to 20.8 s on a loaded machine [1]; compare medians of at least 3 runs.

## Signals

### 1. Production-strength password hashing

- **Detect:** Run M1 and read `PASSWORD_HASHERS`. A `###` prefix means Django's default, which is PBKDF2 at 1,500,000 iterations in Django 6.1 [13]. Count the password work with `rg -c "create_user\(|create_superuser\(|set_password\(|make_password\(|\.login\(" tests`: `client.force_login()` does not hash, but `client.login()` does. In other stacks, run `rg -n "generate_password_hash|bcrypt\.(hashpw|gensalt)|CryptContext|PasswordHasher\(|scrypt" src` and check whether tests lower the work factor. Confirm with M3: `_hashlib.pbkdf2_hmac`, `_hashlib.scrypt`, bcrypt, or argon2 above 5% of the profile's total time.
- **False positives:** Tests of the authentication code need the production hasher, for example for hash upgrades and legacy hashes. Fixtures that store PBKDF2 hashes stop logging in if PBKDF2 leaves the list; Django says to include every algorithm that fixtures use [8]. Suites that log in with `force_login()` or token fixtures gain nothing.
- **Fix:** Put `"django.contrib.auth.hashers.MD5PasswordHasher"` first in the test settings' `PASSWORD_HASHERS`, and keep the production hasher second only when fixtures need it [8]. Sentry's test plugin does this because "pbkdf2 is by design, slow" [14]. Advice that names `UnsaltedMD5PasswordHasher` fails on Django 6.1, which no longer ships it [13]. Use `client.force_login(user)` where login is not under test. In other stacks, read the work factor from configuration and lower it in tests: bcrypt `gensalt(rounds=4)`, Werkzeug `generate_password_hash(pw, method="pbkdf2:sha256:1")`, argon2-cffi `PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)`. Trade-off: most tests stop exercising the production hasher, so keep one module or CI job on the production configuration.
- **Effect:** Django 6.1.1's PBKDF2 took 130 ms per `make_password` and 128 ms per `check_password`, against 0.027 ms and 0.002 ms for MD5 [1]. Werkzeug's default scrypt took 50 ms, bcrypt at 12 rounds 188 ms (0.8 ms at 4 rounds), and argon2-cffi's defaults 27 ms [1]. Two case studies found 73% and 82.8% of runtime in PBKDF2 (see [Evidence](#evidence)). Django raises the iteration count in every feature release, from 600,000 in 4.2 to 1,500,000 in 6.1 [15]. A suite without the override therefore gets about 2.5 times slower at hashing through upgrades alone.
- **Verify:** Run M6 with the fast hasher: the same tests and outcomes, and a lower median. Run the authentication tests once with the production hasher. In a disposable copy, make password checking always succeed and confirm that a test fails.

### 2. Tests that reach real external services

- **Detect:** Cheapest first. Statically, the `risk-network` check covers test files; for product code, run `rg -n "requests\.(get|post|request)|httpx\.(Client|AsyncClient|get|post)|urlopen\(|boto3\.(client|resource)|smtplib|redis\.Redis\(" src`, then check which call sites tests reach without a mock. To enforce, M5 fails every test in a sample that opens an internet socket or resolves a name. To observe, M4 lists non-loopback `socket.connect` and `socket.getaddrinfo` events per test, including import time. If the suite already blocks the network, judge the mode: `--allow-hosts` guards only `connect`, and when both flags are set, only that guard applies, so DNS lookups pass [1, 16].
- **False positives:** Loopback connections to the test database, a local HTTP server, or a container that the suite starts are legitimate. Tests in a marked integration or end-to-end group may need the network by design: count them, but do not report them.
- **Fix:** For unit jobs, use `--disable-socket --allow-unix-socket`. For jobs with local services, use `--allow-hosts=127.0.0.1,::1,localhost` instead, because the two modes do not stack [16]. Mark each exception with `@pytest.mark.enable_socket`, so reviewers see it. Mock at the HTTP-client layer (signal 12), and move the remaining real calls to a marked integration group that a separate CI job still runs. For clients that pytest-socket cannot see, add a guard at the library boundary. Zulip's tests do this for HTTP libraries: `requests.request` and similar functions raise "Outgoing network requests are not allowed in the Zulip tests." [17]. Set fake cloud credentials and a region for the whole session, so a missed mock fails instead of reaching a real account.
- **Effect:** A test that reaches a real service is a trust breaker ([findings.md](findings.md)). Each call also costs a round trip, and a failing call costs its full timeout. Zulip ties its network ban to avoiding nondeterministic failures [17].
- **Verify:** The enforcing run passes with only the marked exceptions, and M4 shows no non-loopback events outside them. A green run does not prove isolation: psycopg 3 (libpq) made a real connection attempt to an IP address with sockets disabled [1]. Treat libpq, mysqlclient, gRPC's C core, librdkafka, and curl-based clients as invisible to both pytest-socket and audit hooks. pytest-socket also guards only from fixture setup to the end of the test body, so calls at import time or in teardown escape it [1].

### 3. Real sleeps, polling loops, and retry delays

- **Detect:** The `risk-sleep` check skips `sleep(0)` and shows constant durations. For retry delays that tests reach, run `rg -n "tenacity|backoff|Retry\(|wait_exponential|countdown=" src`. At run time, M4 sums the real sleep per test; the `time.sleep` audit event needs Python 3.13 or later [18]. asyncio sleeps raise no event, so look for async tests with long `call` times in the baseline. Report more than 1 s of real sleep per 100 tests, or one test above 0.5 s (judgment thresholds).
- **False positives:** `sleep(0)` only yields to other threads. Tests of timing behaviour, such as rate limiters, need a controllable clock, not a removed sleep. A static hit is a hypothesis until M4 or the durations show that it runs.
- **Fix:** Inject the clock and the sleeper (`def __init__(self, sleep=time.sleep, clock=time.monotonic)`), and pass fakes in tests. Wait on a condition with a deadline (`threading.Event.wait(timeout)`, `asyncio.wait_for`) instead of a fixed sleep. Set retry delays to zero in test configuration, for example tenacity's `wait_none()`. For asyncio timers, looptime fakes the loop's clock, so `await asyncio.sleep(100)` takes about 0.01 s; it does not change `time.time()`, threads, or executors [4]. Trio's `MockClock(autojump_threshold=0)` jumps to the next timeout when all tasks block [19]. Patch `time.sleep` globally only as a last resort: tests that coordinate threads through sleeps then race or deadlock.
- **Effect:** The saving is at least the sleep total from M4. Kopf runs about 7,000 asyncio unit tests in about 2 minutes with looptime, and adopted it to stabilise time-based tests [4, 20]. The same change often removes timing flakiness ([flakiness.md](flakiness.md)).
- **Verify:** M4's sleep total falls, and phase 9's before-and-after runs show a lower median. In a disposable copy, remove a backoff and confirm that the timing tests fail.

### 4. App factory or lifespan per test

- **Detect:** M2 ranks fixtures by total setup time and shows their scope. A function-scoped `app`, `client`, or `api` fixture with one setup per test is the signal. Time one construction in the project with `python -c "import time; from app import create_app; t = time.perf_counter(); create_app(); print(time.perf_counter() - t)"`; it runs project code, so agree on it as you would on collection. In FastAPI suites, look for `app.openapi()` calls in tests.
- **False positives:** Tests that change app configuration, register routes, or depend on app-level singletons need a fresh app, or a reset of those parts. Under pytest-xdist, session scope means once per worker, which is still cheap.
- **Fix:** Build the app once per session, and run lifespan once: `with TestClient(app) as client` inside the session fixture, or `asgi_lifespan.LifespanManager` for async clients. Reset per-test state explicitly: `app.dependency_overrides.clear()`, database rollback ([database-and-data.md](database-and-data.md)), and configuration fixtures. Trade-off: a shared app can leak state between tests.
- **Effect:** FastAPI 0.142 with 200 routes that use Pydantic models took 78 ms to build, and its first `app.openapi()` call took 99 ms. Flask 3.1 with 200 routes took 21.5 ms, and an empty lifespan added about 1 ms per `TestClient` context [1]. At 10,000 tests, 78 ms per test is 13 minutes of setup. Real apps add connection pools, clients, and model loading.
- **Verify:** M2 shows one setup per worker, `results.py diff` shows a lower median, and two runs in random order pass.

### 5. CLI tests through a subprocess

- **Detect:** The `risk-subprocess` check, and `subprocess.Popen` counts per test in M4. Also look for pytest-console-scripts with `script_launch_mode = subprocess` or `both`; `both` runs every script test twice [21].
- **False positives:** Tests of packaging, entry points, signal handling, `os._exit` codes, terminal behaviour, or environment inheritance need a real process. Keep them, but keep them few.
- **Fix:** Call the command in process with Click's or Typer's `CliRunner`, or call `main(argv)`. Keep one subprocess smoke test per installed entry point, so packaging stays covered. `CliRunner.invoke` "redirects the process-global standard streams", so run CLI tests in pytest-xdist processes, not threads [22]. Click 8.5 deprecates `isolated_filesystem` because it uses `os.chdir`, and `CliRunner(capture="fd")` (Click 8.4 and later) also catches output that bypasses `sys.stdout` [22].
- **Effect:** With Click 8.5, `CliRunner.invoke` took 48 µs. A subprocess of a minimal CLI took 57 ms, and one of a CLI that imports a typical web stack took 468 ms: 1,200 to 9,800 times slower [1].
- **Verify:** Exit-code and output assertions pass in process, the smoke tests still run the installed script, and `results.py diff` shows a lower median.

### 6. Browsers launched per test, and recording on every test

- **Detect:** M2 shows a function-scoped fixture that calls `webdriver.Chrome()`, `webdriver.Firefox()`, `chromium.launch()`, or `sync_playwright().start()`, with one setup per test. In the CI flags, look for `--tracing on|retain-on-failure`, `--video on|retain-on-failure`, `--headed`, and `--slowmo` [23]. Selenium Manager discovers, downloads, and caches drivers and browsers at run time, with a cache time to live of 3,600 s by default; `SE_OFFLINE=true` stops its network requests [24]. Look for fixed sleeps in page objects.
- **False positives:** Tests that need browser-level isolation, such as extensions or certificates, may need a fresh browser; group them under a marker. Traces that the team reads after failures have value; the question is whether every passing test pays for them.
- **Fix:** Launch one browser per session (per xdist worker), and create one context per test. pytest-playwright's `browser` fixture is session-scoped, and `context` and `page` are function-scoped [23]. For Selenium, reuse the driver per session, and clear cookies and storage between tests. Replace fixed sleeps with auto-waiting assertions such as `expect(locator).to_have_text(...)`. `--tracing retain-on-failure` records screenshots, snapshots, and sources for every test, writes each zip, and deletes it when the test passes [12]; `--video retain-on-failure` works the same way. Trade-off: with `--tracing off` in the main run, you need a second run of the failed tests with `--tracing on`. Count the first failure, so the rerun diagnoses it instead of hiding it. A custom `context` fixture that starts tracing with `sources=False` is a cheaper middle ground (not measured). In CI, `playwright install --only-shell` installs only the headless shell [25]. For Selenium, pre-install the drivers and set `SE_OFFLINE=true` [24].
- **Effect:** Playwright 1.63 with the Chromium headless shell took 1,422 ms per browser launch, 1.3 ms per new context, and 36 ms per new page [1]. Tracing raised a trivial test's median from 90 ms to 115 ms (+28%) [1].
- **Verify:** M2 shows one browser setup per worker, and two runs in random order pass. Shared browsers leak cookies and storage when contexts are not isolated.

### 7. Time control: freezegun cost and correctness

- **Detect:** Count freezes with `rg -c "freeze_time|freezer|mark.freeze_time" tests`. An autouse fixture that freezes time multiplies the cost by its reach, which the `autouse-fixtures` check shows. M7 prices one freeze in the project's import state, because the cost grows with the number of loaded modules. In a profile (M3), read the cumulative time of the `freezegun/api.py` functions. Correctness risks: freezegun freezes `time.monotonic` [26], so `await asyncio.sleep(...)` inside a frozen block never returned without `real_asyncio=True` [1]. freezegun also misses class attributes, default arguments, closures, and C extensions [5]. Python 3.14's `uuid.uuid7()` never goes backwards within a process [27]. After travel to the past, new version 7 universally unique identifiers (UUIDs) continue from the last real timestamp. pytest-freezegun (last release 2020) is abandoned, and pytest-freezer wraps freezegun and inherits its cost [28].
- **False positives:** A suite with few freezes gains little: at 5 ms per freeze, 200 freezes cost 1 s. As a judgment floor, do not recommend a migration below a few hundred freezes per run, unless the correctness gaps bite.
- **Fix:** Migrate to time-machine, which patches the C time functions once, so its cost does not grow with the module count [5]. On a branch, run `uvx --from 'time-machine[cli]' python -m time_machine migrate $(git grep -l freezegun -- '*.py')`. Its author warns that "the tool can leave a file in a broken state", so run the linter and the tests afterwards [5]. Set `TZ=UTC` for the test process. For timezone-aware destinations, time-machine sets `TZ` and calls `tzset()` on each travel [29]. That cost about 1.1 ms per travel on macOS, against 4 µs with `TZ=UTC` already set; the Linux cost was not measured [1]. time-machine does not mock `time.monotonic` or `time.perf_counter`, so asyncio keeps working, but it cannot fast-forward async timers [30]. If freezegun stays, extend its ignore list for heavy modules (`freezegun.configure(extend_ignore_list=[...])`), and pass `real_asyncio=True` in async tests [26]. In new code, inject a clock: mocked time is global, and "all concurrent threads or asynchronous functions are also affected" [30].
- **Effect:** freezegun 1.5.5 took 1.67 ms per freeze with 396 modules loaded, 2.72 ms with 811, and 5.12 ms with 1,387, against 1.7 µs for time-machine 3.5.1 [1]. With 16,259 modules, freezegun took 41 ms per freeze; the benchmark's author puts that at 82 s of overhead for a 2,000-test suite [5].
- **Verify:** M7 and phase 9's before-and-after runs show the drop. In a disposable copy, shift a frozen date by one day and confirm that the date tests fail.

### 8. Debug mode and verbose logging in CI

- **Detect:** Run `rg -n --hidden -g '!.git' -g '*.toml' -g '*.ini' -g '*.cfg' -g '*.yml' -g '*.yaml' -g 'conftest.py' -g '*settings*' "log_level|log_cli|--log-level|django_debug_mode|asyncio_debug|--asyncio-debug|PYTHONASYNCIODEBUG|PYTHONDEVMODE|-X dev|echo=True"`; the `-g` filters, not shell globs, keep zsh from failing on a pattern that matches nothing. Python's development mode (`-X dev`, `PYTHONDEVMODE=1`) turns on asyncio debug mode [31]. pytest-asyncio's header line shows its `debug=` value. Also look for error-reporting software development kits (SDKs) that tests initialise with a real data source name (DSN): `rg -n "sentry_sdk.init|SENTRY_DSN|dsn="`.
- **False positives:** `DEBUG = True` in a Django test settings module has no effect by default, because Django's runner and pytest-django force `DEBUG=False` [7, 8]. Only pytest-django's `django_debug_mode = true` or `keep`, or `manage.py test --debug-mode`, keeps it on [9]. Django logs SQL only while `DEBUG` is on or a debug cursor is forced [32], so a DEBUG-level `django.db.backends` logger costs nothing otherwise. A scheduled job with debug on is useful and should stay.
- **Fix:** Keep log capture at the default level in CI, and raise it per test with `caplog.set_level(logging.DEBUG, logger="app")`. Move asyncio debug and development mode to one scheduled job that reports never-awaited coroutines and slow callbacks. Trade-off: the main job stops catching those, so the scheduled job must stay green. Empty the DSN of error-reporting SDKs in test settings; Sentry's own plugin turns off its internal error collection in tests [14].
- **Effect:** With `--log-level=DEBUG`, 20,000 debug records cost 165 ms, against 1.8 ms at the default level, because pytest's capture handlers store and format every record [1]. An object-relational mapper (ORM) query on in-memory SQLite took 66 µs with `DEBUG=False`, 72 µs (+9%) with `DEBUG=True`, and 89 µs (+33%) with the SQL logger writing to a handler [1]. The share is smaller against a networked database. asyncio debug mode made 5,000 gathered tasks 25–27 times slower [1].
- **Verify:** M6 with `--log-level=WARNING` shows the same tests and outcomes and a lower median. Tests that use `caplog` still pass, and the scheduled job still reports never-awaited coroutines.

### 9. Shared or remote backends in test settings

- **Detect:** In M1's effective test settings, look for `CACHES` backends `RedisCache`, `PyMemcacheCache`, or `django_redis`. Look for `STORAGES["default"]` on Amazon S3 or Google Cloud Storage, or `FileSystemStorage` writing into the repository, and `STORAGES["staticfiles"]` set to a manifest storage. Look for `debug_toolbar` or silk in `INSTALLED_APPS` or `MIDDLEWARE`, and a custom template `loaders` list without the cached loader, which is on by default when `loaders` is not set [33]. In Flask and FastAPI apps, look for `CACHE_TYPE = "RedisCache"`, clients created at import time, and object-storage clients without an endpoint override.
- **False positives:** Tests of the cache or storage integration belong on the real backend, in a marked group that a CI job still runs. `LocMemCache` is private to each process [10], so it cannot test behaviour shared between a web process and a worker. Email is not a finding: `setup_test_environment()` already forces the locmem backend, including every alias of the new `MAILERS` setting [7]. Look instead for code that escapes it: `get_connection(backend=...)`, vendor SDK clients, and workers in another process.
- **Fix:** Use `CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}` and an autouse fixture that calls `cache.clear()` for every alias. Django does not clear caches between tests, and on a shared backend tests "can insert data from the tests into the cache of a live system" [8]. Use `django.core.files.storage.InMemoryStorage` for media (Django 4.2 and later) [34]. Use `django.contrib.staticfiles.storage.StaticFilesStorage` for static files, because manifest storage raises `ValueError` when `collectstatic` has not run [35]. Do not use `DummyCache`: it stores nothing, so code that relies on the cache for locks, rate limits, idempotency keys, or sessions passes vacuously [10]. Remove debug toolbars and profilers. django-debug-toolbar stops a test run by default, so a suite that sets `IS_RUNNING_TESTS = False` runs its middleware in every request for no test value [36]. For each fake, name the integration fault it could hide, and keep a marked test on the real backend.
- **Effect:** This research found no general effect size. The gain is determinism: with a cache shared by all tests and workers, one test's writes change another test's result. Network round trips to the backend also disappear.
- **Verify:** Two runs in random order and one parallel run pass with no new failures, and the marked integration tests still pass on the real backend.

### 10. Hidden DNS latency

- **Detect:** M4 reports the lookup time per test (`dns_s`). Check hosts in test configuration that may not resolve on a laptop or a runner, such as `db`, `redis`, `*.local`, and internal names. Look for `socket.getfqdn()`: Django's `DNS_NAME` calls it once per process when it builds the first email, and the source says it "can take a couple of seconds" [37].
- **False positives:** The first lookup is slower than later, cached ones. One slow lookup per worker is noise, unless it hits a timeout.
- **Fix:** Use IP literals such as `127.0.0.1`, or names from `/etc/hosts`, for local services. Patch `socket.getfqdn` or set `DNS_NAME` for the test session, as Sentry's plugin does [14]. Avoid `.local` names on macOS.
- **Effect:** From zero to seconds per lookup. A failing lookup of a `.local` name took 5,002 ms on macOS [1]. With glibc, an unreachable name server costs the default 5 s timeout per attempt, with 2 attempts [38].
- **Verify:** M4's lookup time for unit tests falls to near zero, and the remaining lookups are loopback names.

### 11. Expensive Hypothesis property tests

- **Detect:** M8 ranks property tests by phase time. The `hypothesis-settings` check lists `@settings` overrides such as `max_examples`, `deadline`, and suppressed health checks. Find profile code with `rg -n "register_profile|load_profile|HYPOTHESIS_PROFILE|hypothesis-profile" conftest.py tests pyproject.toml setup.cfg`. Report a conftest that calls `load_profile` unconditionally: it replaces the built-in `ci` profile, which Hypothesis loads when it detects CI variables [39]. A global `deadline=None` or a suppressed `HealthCheck.too_slow` hides slow strategies.
- **False positives:** A slow property test can be the most valuable test in the suite. When a test runs from several threads, Hypothesis turns off the deadline and `too_slow` checks, because it cannot time threads [39].
- **Fix:** First make the body cheap: move database or HTTP work out of `@given`, or test the pure function underneath. Fix strategies that `too_slow` flags, such as filters that reject most draws, instead of suppressing the check. Then choose profiles explicitly in the root conftest: `settings.register_profile("dev", max_examples=10)`, `settings.register_profile("nightly", max_examples=2000, derandomize=False)`, and `settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "ci" if os.getenv("CI") else "dev"))`. Run the nightly profile in a scheduled job. Trade-off: the `dev` profile's 10 examples find fewer bugs in local runs. The built-in `ci` profile's `derandomize=True` repeats the same examples on every run [39], so only the nightly run explores new inputs.
- **Effect:** The cost is about `max_examples` times the body time. 100 examples of a 6 ms body took 0.68 s, so 10 examples take about 0.07 s [1]. Without a `.hypothesis/` directory, the first `st.text()` test paid about 0.9 s to build a Unicode table cache [1].
- **Verify:** M8 shows the new phase times. In a disposable copy, plant a bug in the code under the property, and confirm that the `ci` and nightly profiles still find it.

### 12. HTTP mocks that do not guard

- **Detect:** Pair each HTTP client that the code uses with the mock library that the tests use. `responses` [40] and requests-mock mock `requests` only, respx and pytest-httpx mock httpx only [41, 42], and aioresponses mocks aiohttp. A mismatch means the mock never intercepts. `@responses.activate` defaults to `assert_all_requests_are_fired=False`, while `responses.RequestsMock()` defaults to `True` [40]; count decorated tests with `rg -c "@responses.activate$" tests`. Look for pass-through escapes: `add_passthru`, respx's `pass_through`, and pytest-httpx's `should_mock`. Tests that patch the project's own client wrapper never exercise serialization, headers, or error mapping ([design-and-smells.md](design-and-smells.md)).
- **False positives:** In a parametrized test, a stub can be unused in some cases by design; configure the assertion per test there.
- **Fix:** Turn on the assertion in both directions: `@responses.activate(assert_all_requests_are_fired=True)`, or a `responses.RequestsMock()` fixture. pytest-httpx already fails a test on unused responses and unmatched requests [42]. Treat each unused stub as a review candidate, because the test may no longer reach the path that its name claims. Match on request bodies or queries where they matter (`responses.matchers.json_params_matcher`). Keep a scheduled contract or sandbox test per external API, because mocks cannot see API drift. httpx has had no release since 0.28.1 (December 2024) [43], Starlette 1.2 and later prefer Pydantic's fork `httpx2` [44], and respx and pytest-httpx do not support httpx2 yet [41]. With any move to httpx2, add network blocking (signal 2), because httpx mocks stop intercepting.
- **Effect:** The gain is effectiveness more than speed: dead stubs often mean that a test no longer covers what its name claims. The speed gain is fewer accidental real calls.
- **Verify:** In a disposable copy, change a URL or a payload field in the code under test, and confirm that a test fails.

### 13. Cassettes, cloud emulators, and containers

- **Detect:** vcrpy's default record mode `once` records "if there is no cassette file" [45], so a renamed test makes a live call in a CI job with credentials. pytest-recording defaults to `none` [46], and pytest-vcr (last release 2019) is abandoned [28]. Find the configuration with `rg -n "record_mode|vcr_config|use_cassette|mark.vcr" tests`, cassette age with `git log -1 --format=%cs -- CASSETTE`, and secrets with `rg -n -i "authorization|api[_-]?key|token|set-cookie" tests/cassettes`. httpx 0.28 made JSON request bodies compact, so cassettes that match raw bodies can stop matching [43]. moto does not mock clients created before the mock starts, and it is "not designed for multithreaded access/multiprocessing" [47]. testcontainers-python 4.15 has no container reuse and polls readiness every 1 s by default (`TC_POOLING_INTERVAL`), up to 120 tries [6]; M2 shows function-scoped container fixtures.
- **False positives:** A cassette that never changes is fine for a frozen, versioned API. Container-backed tests are the right tool for database- or broker-specific behaviour; do not replace them with fakes.
- **Fix:** In CI, run cassette tests with `--record-mode=none --block-network` (pytest-recording), or set `record_mode="none"` in `vcr_config`. Filter secrets with `filter_headers`, `filter_query_parameters`, and `before_record_request` [45]. Re-record on a schedule in a job with credentials, and review the diff. For Amazon Web Services (AWS), set fake credentials and a region for the session, and use one `mock_aws` fixture that yields clients created inside it [47]. LocalStack's open-source repository was archived on 2026-03-23 in favour of a unified image with a free non-commercial plan, so check its licence before you recommend it [48]. For containers, use session scope with one container per service per worker, isolate tests by database, key prefix, or topic, and lower `TC_POOLING_INTERVAL` when readiness is fast [6].
- **Effect:** Removes live calls and their variance. This research did not measure container start-up. The 1 s default poll adds up to about 1 s to each readiness check that does not pass at once [6].
- **Verify:** In a disposable copy, delete one cassette, and confirm that the test fails instead of recording. Count container starts during a run with `docker events --filter type=container --filter event=start`.

### 14. Background jobs: eager mode as the only task test

- **Detect:** Run `rg -n "task_always_eager|CELERY_TASK_ALWAYS_EAGER|task_eager_propagates|celery_worker|celery_session_worker|is_async=False|StubBroker"`. Look for tests that depend on `countdown`, `eta`, time limits, routing, or `acks_late`. M2 shows a function-scoped `celery_worker`, which starts and stops a worker thread for every test.
- **False positives:** Eager mode is a reasonable way to test "the view enqueues the task, and the task does X" in one test. The problem is eager mode as the only test of task behaviour. Do not report that eager mode skips serialization: `delay()` and `apply_async()` round-trip their arguments through the serializer in eager mode since at least Celery 4.4.7, and only direct `task.apply()` calls skip it [11].
- **Fix:** Unit-test task bodies as plain functions (`my_task.run(...)`), and test enqueueing with a mock or by inspecting the broker. Keep a small integration group with a real worker: `celery_session_worker` on the in-memory transport, or pytest-celery containers for broker-specific behaviour. pytest-celery's API is not compatible with `celery.contrib.pytest` [49]. In Dramatiq, call `stub_broker.join(queue_name)` and then `stub_worker.join()`. `join()` re-raises actor errors only after retries run out, so set `max_retries=0` where tests expect failures [50]. In RQ, `Queue(is_async=False)` runs jobs in the calling thread, and `SimpleWorker(...).work(burst=True)` processes the queued jobs and stops [51].
- **Effect:** The cost of eager mode is escaped defects, not time; Celery's documentation calls it "by definition not suitable for unit tests" [49]. In eager mode, tasks run in the caller's thread and database transaction, so `transaction.on_commit` ordering differs, and retries run at once with `countdown` ignored [11]. Routing, rate limits, prefetching, and pool time limits never run (inference from the execution path).
- **Verify:** In a disposable copy, break the retry configuration or the routing, and confirm that the integration group fails.

### 15. Uncontrolled randomness and identifiers

- **Detect:** A run header with `Using --randomly-seed=N` shows that pytest-randomly is active. Without it, `random`, Faker, and factory_boy seeds differ per run, unless the suite seeds them. The `risk-random` check lists `random.*` and `uuid4()` calls. No plugin reseeds `uuid.uuid4()`, `uuid.uuid7()`, `secrets`, `os.urandom`, an unseeded NumPy `default_rng()`, or `random.Random()` instances created at import time [27, 52]. Look for tests that compare generated IDs, and for snapshots that contain UUIDs or timestamps.
- **False positives:** Random data is fine when the assertion does not depend on the value; do not replace every `uuid4()` with a constant. A static hit is a hypothesis: a test is flaky only when it failed and passed at the same commit ([flakiness.md](flakiness.md)).
- **Fix:** pytest-randomly 5.0 reseeds `random`, Faker, factory_boy, Model Bakery, NumPy's legacy global generator, and Polyfactory before each test phase, from the base seed and the test ID [52]. Print the seed in CI logs, and replay a failure with `-p randomly --randomly-seed=N`. Inject an ID factory where tests assert on IDs, seed NumPy `Generator` objects from the test's seed, and replace UUIDs and timestamps in snapshots with placeholders. If the suite already uses pytest-randomly, judge it: check that CI logs the seed and that the team replays failures. The plugin also shuffles test order, and `--randomly-dont-reorganize` keeps the order [52].
- **Effect:** Turns "cannot reproduce" failures into failures that you can replay with one seed.
- **Verify:** Two runs with the same seed give identical outcomes, and three runs with different seeds give no new failures.

### 16. Async tests: event-loop scope and test clients

- **Detect:** pytest-asyncio's header line (`asyncio: mode=..., debug=..., asyncio_default_fixture_loop_scope=...`) shows its configuration. Look for overrides of the `event_loop` fixture (`rg -n "def event_loop\b" tests conftest.py`), which pytest-asyncio 1.0.0 removed; 1.4.0 also deprecates overriding `event_loop_policy` in favour of the `pytest_asyncio_loop_factories` hook [53]. Look for async fixtures whose `scope` is wider than their `loop_scope`, which show up as "attached to a different loop" or "Event loop is closed" errors. pytest-asyncio in `auto` mode does not work together with AnyIO's plugin [54], and pytest-trio's last release was in 2022 [28]. `TestClient(app)` without `with` (`rg -n "TestClient\(" tests | rg -v "with "`) starts a new thread and event loop per request and never runs lifespan [55]. httpx 0.28 removed `httpx.AsyncClient(app=app)` [43], and `AsyncClient` does not run lifespan events either [56].
- **False positives:** Function-scoped loops are the safe default, and pytest-asyncio recommends that "neighboring tests use the same event loop scope" [57]. A synchronous suite that uses `TestClient` inside a `with` block works; do not push it towards async tests.
- **Fix:** Remove `event_loop` overrides, and use `loop_scope` on markers and fixtures, for example `@pytest_asyncio.fixture(loop_scope="session", scope="session")`. Set `asyncio_default_fixture_loop_scope = "function"` explicitly [58]. Use one async plugin; the AnyIO plugin also runs Trio. Create the client once per session inside `with TestClient(app)`, or use `httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")` with `LifespanManager`. Create async resources inside lifespan, so they live on the app's loop [55].
- **Effect:** Small for speed (see "Changes that do not pay"). A request took 503 µs without a `with` block, 219 µs inside one, 1,029 µs with a new `with` block per test, and 106 µs through `AsyncClient` [1]. The value is fewer loop-affinity errors and hangs. pytest-asyncio 1.0 also creates scoped loops once, which "speeds up collection time, especially for large test suites" [53].
- **Verify:** Two runs in random order pass with no loop errors, and no `ResourceWarning` reports an unclosed loop.

## Measuring

These rules apply to every recipe:

- Run it on a sample first: the slowest files from the baseline summary, or a stratified sample from `run_suite.py sample`. `SAMPLE_PATHS` stands for the chosen files, and `NN` for the run number that `run_suite.py` prints.
- Keep plugins and settings modules in `AUDIT/plugins`, outside the project, and pass `--env PYTHONPATH=AUDIT/plugins`. If CI sets `PYTHONPATH`, append its entries.
- Profiles (M3) and audit hooks (M4) are instrumented. They rank culprits, but only uninstrumented before-and-after runs (M6, or phase 9) can back a speed finding; `findings.py` rejects speed findings that cite instrumented runs.
- `-q` hides the run header. Read header lines, such as the pytest-randomly seed or pytest-asyncio's mode, from a run without `-q`, for example the baseline.
- The `risk-*`, `autouse-fixtures`, and `hypothesis-settings` checks come from phase 4's `AUDIT/static.json`. Rerun `static_scan.py` with `--examples 50` for more examples per check.

### M1. Snapshot the effective test configuration

```sh
python manage.py diffsettings --settings=TEST_SETTINGS --all | grep -E "^(### )?(PASSWORD_HASHERS|CACHES|STORAGES|EMAIL_BACKEND|MAILERS|LOGGING|MIDDLEWARE|INSTALLED_APPS|TEMPLATES|DEBUG|CELERY_[A-Z_]+) ="
python manage.py diffsettings --settings=TEST_SETTINGS --default=PROD_SETTINGS --output=unified
grep -E "^(plugins:|Using --randomly-seed|asyncio:|django:|hypothesis profile)" AUDIT/runs/NN-baseline/output.log
```

`--all` prints every setting, and a `###` prefix marks a value that is still Django's default. The unified diff shows only what the test settings change from production, so an unchanged hasher does not appear in it. The header shows the active plugins, the seed, pytest-asyncio's mode and loop scopes, and the Django settings module with its source; the Hypothesis profile appears only at `-v`. For Flask or FastAPI, print the configuration object that the test fixture builds. Also read `PYTHONASYNCIODEBUG`, `PYTHONDEVMODE`, `TZ`, `HYPOTHESIS_PROFILE`, `SE_OFFLINE`, and `TC_*` in the CI configuration. Cost: seconds, but `diffsettings` imports project code, so agree on it as you would on collection. This recipe often finds signals 1, 8, and 9 on its own.

### M2. Price per-test setup

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label setup --timeout SECONDS --cwd ROOT --timing-plugin -- \
    CI_TEST_COMMAND SAMPLE_PATHS
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py fixtures AUDIT/runs/NN-setup
```

Each row shows a fixture's total setup time, setups, mean, maximum, scope, and where the fixture is defined. A function-scoped app, client, browser, worker, or container fixture with one setup per test is a candidate. Session scope would save about (setups − workers) × mean. Scale the sample's setups to the suite by the ratio of collected tests, and mark the estimate as extrapolated. Cost: one sample run; the timing plugin adds a few microseconds per phase.

### M3. Rank known culprits in a profile

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label profile --timeout SECONDS --cwd ROOT -- \
    python -m cProfile -o {RUN_DIR}/suite.prof -m pytest -n0 -q SAMPLE_PATHS
python -c "import pstats, sys; pstats.Stats(sys.argv[1]).sort_stats('tottime').print_stats(30)" AUDIT/runs/NN-profile/suite.prof
python -c "import pstats, sys; pstats.Stats(sys.argv[1]).sort_stats('cumulative').print_stats('pbkdf2|scrypt|hashpw|argon2|getaddrinfo|gethostby|getfqdn|sleep|tzset|Popen|launch|freezegun', 25)" AUDIT/runs/NN-profile/suite.prof
```

Add CI's markers and options to the pytest part. `-n0` keeps all work in the profiled process; drop it when pytest-xdist is not installed. `run_suite.py` labels the run `instrumented: profile` by itself. The first listing ranks functions by self time (`tottime`) under a header with the total seconds; the second keeps only known culprits. A built-in such as `_hashlib.pbkdf2_hmac`, `time.sleep`, or `_socket.getaddrinfo` above about 5% of the total is a candidate. For freezegun, read the cumulative column of the `freezegun/api.py` functions. cProfile slows every Python call, so trust the ranking more than the absolute times. Read the file with the same Python that wrote it. Cost: one sample run, with profiler overhead.

### M4. Record real I/O per test with audit hooks

Save as `AUDIT/plugins/io_audit.py`:

```python
import collections, json, os, socket, sys, threading, time
import pytest

WATCH = {"socket.connect", "socket.sendto", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "subprocess.Popen", "os.system", "time.sleep"}
state = {"test": "<outside tests>"}  # collection, session setup and teardown
events = collections.defaultdict(collections.Counter)
secs = collections.defaultdict(lambda: {"sleep_s": 0.0, "dns_s": 0.0})
lock = threading.Lock()
real_getaddrinfo = socket.getaddrinfo

def hook(event, args):
    if event in WATCH:
        detail = repr(args[1]) if event in ("socket.connect", "socket.sendto") else str(args[0])
        with lock:
            events[state["test"]][f"{event} {detail[:60]}"] += 1
            if event == "time.sleep":
                secs[state["test"]]["sleep_s"] += float(args[0])

def timed_getaddrinfo(*args, **kwargs):
    start = time.perf_counter()
    try:
        return real_getaddrinfo(*args, **kwargs)
    finally:
        with lock:
            secs[state["test"]]["dns_s"] += time.perf_counter() - start

socket.getaddrinfo = timed_getaddrinfo
sys.addaudithook(hook)

def pytest_addoption(parser):
    parser.addoption("--io-audit-dir", help="folder for io-audit-<worker>.jsonl; pass {RUN_DIR}")

@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    state["test"] = item.nodeid
    try:
        return (yield)
    finally:
        state["test"] = "<outside tests>"

def pytest_sessionfinish(session):
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    with open(os.path.join(session.config.getoption("io_audit_dir"), f"io-audit-{worker}.jsonl"), "w") as f:
        for test in sorted(set(events) | set(secs)):
            f.write(json.dumps({"test": test, **{k: round(v, 3) for k, v in secs[test].items()}, "events": dict(events[test])}) + "\n")
```

Run it, then summarise:

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label io-audit --timeout SECONDS --cwd ROOT \
    --instrumented profile --env PYTHONPATH=AUDIT/plugins -- CI_TEST_COMMAND -p io_audit --io-audit-dir={RUN_DIR} SAMPLE_PATHS
python3 - AUDIT/runs/NN-io-audit <<'PY' | head -40
import glob, json, sys
rows = [json.loads(line) for p in glob.glob(f"{sys.argv[1]}/io-audit-*.jsonl") for line in open(p)]
local = ("'127.", "'::1'", "'localhost'", "'/", " localhost", " 127.", " ::1", " None")
print(f"real sleep {sum(r['sleep_s'] for r in rows):.1f} s, DNS {sum(r['dns_s'] for r in rows):.1f} s")
for r in sorted(rows, key=lambda r: -(r["sleep_s"] + r["dns_s"]))[:10]:
    print(f"{r['sleep_s']:8.2f} s sleep {r['dns_s']:7.2f} s DNS  {r['test']}")
for r in rows:
    for key, n in r["events"].items():
        if key.startswith("socket.") and not any(m in key for m in local):
            print(f"non-loopback x{n}: {r['test']}  {key}")
PY
```

The summary prints the total real sleep and lookup time, the ten tests with the most, and non-loopback socket events such as `non-loopback x1: tests/test_x.py::test_y  socket.getaddrinfo api.example.com`. Read the sleep total as the least wall time you can recover, and `subprocess.Popen` counts as CLI or tool launches. `<outside tests>` holds import time and session setup and teardown; under pytest-xdist, it also holds the worker launches. A fixture's events count for the test whose setup ran it, so the first test on each worker carries the session fixtures. Declare `--instrumented profile`, because `run_suite.py` cannot detect a plugin that loads through `PYTHONPATH`. Without `--io-audit-dir`, the plugin fails when the run ends, so always pass it. The hook observes and does not block, so keep the baseline's deselection of live tests. Limits: C extensions such as libpq, librdkafka, and gRPC raise no events, asyncio sleeps raise none, and `time.sleep` events need Python 3.13 or later [18]. Audit hooks cannot be removed [59] and are "not suitable for implementing a sandbox" [60], so load this plugin only in diagnostic runs. Cost: one sample run, plus one Python call per audit event; without a hook, the overhead is negligible [59].

### M5. Enforce network isolation on a sample

```sh
python3 -m pip install --no-deps --target AUDIT/plugins pytest-socket==0.8.1
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label no-network --timeout SECONDS --cwd ROOT \
    --env PYTHONPATH=AUDIT/plugins --env COLUMNS=250 -- CI_TEST_COMMAND -p socket --disable-socket --allow-unix-socket SAMPLE_PATHS
grep -hE "^E +pytest_socket\." AUDIT/runs/NN-no-network/output.log | sort | uniq -c | sort -rn | head
grep -E "^(FAILED|ERROR) .*Socket(Connect)?BlockedError" AUDIT/runs/NN-no-network/output.log
```

`--target` puts the pure-Python package in the audit directory, not in any environment. For suites that need local services, replace the last two flags with `--allow-hosts=127.0.0.1,::1,localhost`, which fails only connections to other hosts and lets lookups through. The messages read `A test tried to use socket.getaddrinfo.` or `A test tried to use socket.socket.connect() with host "..."`. `COLUMNS=250` stops pytest from cutting off the `FAILED` lines. Load the plugin as `-p socket`, its entry-point name: `-p pytest_socket` fails with "Plugin already registered under a different name" when plugin autoload is on. Under `--disable-socket` without `--allow-unix-socket`, creating an asyncio event loop can fail, because the loop opens a socket pair [61]. Cost: one sample run, plus false failures from legitimate local services until you allow them. A green run does not prove isolation for C clients (signal 2).

### M6. Compare settings before and after, without changing the project

Save the changed settings as `AUDIT/plugins/audit_settings.py`; prepending MD5 keeps fixture hashes valid. Run each side at least 3 times, then compare:

```python
from django.conf import global_settings
from PROJECT.settings.test import *  # noqa: F403 – the settings module the tests use now

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher",
                    *globals().get("PASSWORD_HASHERS", global_settings.PASSWORD_HASHERS)]
```

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label before --timeout SECONDS --cwd ROOT -- \
    CI_TEST_COMMAND --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1 SAMPLE_PATHS
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label after --timeout SECONDS --cwd ROOT \
    --env PYTHONPATH=AUDIT/plugins -- CI_TEST_COMMAND --ds=audit_settings --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1 SAMPLE_PATHS
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py diff --before RUN_A RUN_B RUN_C --after RUN_D RUN_E RUN_F
```

pytest-django's `--ds` wins over the `DJANGO_SETTINGS_MODULE` variable and the ini file, and the run header shows `settings: audit_settings (from option)`. Django's own runner takes `--settings=audit_settings`. For other changes, use flags and variables: `--log-level=WARNING`, `--env TZ=UTC`, or `--unset PYTHONASYNCIODEBUG`. `results.py diff` warns that the commands differ, which is expected. Accept the result only when it reports the same tests and outcomes; a changed outcome means the experiment changed behaviour, for example fixture hashes that no longer verify. These runs are uninstrumented, so they can back a speed finding; extrapolated from a sample, it has medium confidence at most. Cost: six sample runs.

### M7. Price a freeze in the project's import state

Run from `ROOT` with the project's interpreter. Outside Django, replace `django.setup()` with imports of what the tests import:

```sh
DJANGO_SETTINGS_MODULE=TEST_SETTINGS python -c "import sys, timeit, django; django.setup(); import freezegun; f = freezegun.freeze_time('2020-01-01'); print(f'modules={len(sys.modules)}', f'{timeit.timeit(lambda: (f.start(), f.stop()), number=200) / 200 * 1e3:.2f} ms per freeze')" > AUDIT/freeze-cost.txt
```

Multiply the cost by the freezes per run: the call sites that run in each test, and each autouse freeze times the tests it reaches. Mark the product as extrapolated. A test run loads more modules than this script, so treat the result as a lower bound. Cost: seconds, but it imports project code, so it needs the same agreement as collection.

### M8. Rank property tests by Hypothesis phase time

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label hypothesis --timeout SECONDS --cwd ROOT -- \
    CI_TEST_COMMAND -n0 --hypothesis-show-statistics SAMPLE_PATHS
awk '/^[^ ].*::.*:$/ {t = $0} /during .* phase/ {gsub(/[()]/, ""); print $5, $3, t}' AUDIT/runs/NN-hypothesis/output.log | sort -rn | head -20
```

The `awk` line prints seconds, phase, and test, for example `0.29 generate tests/test_prop.py::test_slow_body:`. For each test, the statistics show lines such as `- during generate phase (0.29 seconds):`, `- Typical runtimes: ~ 2ms, of which < 1ms in data generation`, and `- Stopped because settings.max_examples=100`. A long phase with little time in data generation means a slow body, so move I/O out of `@given`. A large share in data generation means a slow strategy. In CI, the built-in `ci` profile is active unless a conftest loads another one, so check which profile ran (M1). Cost: one run of the property tests.

## Tools

Versions and dates come from the PyPI JSON API and GitHub repository metadata on 2026-09-30 [28].

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| pytest-django | Django settings, database, and `mailoutbox` fixtures | 4.14.0, 2026-08-10, maintained | `--ds` overrides the settings module; `django_debug_mode` defaults to false |
| pytest-asyncio | asyncio tests and fixtures | 1.4.0, 2026-05-26, maintained | `event_loop` removed in 1.0; pytest 9 since 1.3.0; conflicts with AnyIO's auto mode |
| AnyIO pytest plugin | Tests on asyncio and Trio backends | anyio 4.15.1, 2026-09-05, maintained | Prefer it to pytest-trio for Trio |
| pytest-trio | Trio test runner | 0.8.0, 2022-11-01, partly maintained | Classifiers up to Python 3.11 |
| looptime | Fake asyncio loop time | 0.7, 2026-01-03, maintained | asyncio time only; no effect on `time.time()`, threads, or executors |
| responses | Mock `requests` | 0.26.3, 2026-08-26, maintained | The decorator does not assert unused stubs by default |
| requests-mock | Mock `requests` through a transport adapter | 1.12.1, 2024-03-29, partly maintained | Little activity since 2024 |
| respx | Mock httpx | 0.23.1, 2026-04-08, maintained | No httpx2 support yet (issues #316, #317, #324) |
| pytest-httpx | Mock httpx | 0.36.2, 2026-04-09, maintained | Pins `httpx==0.28.*`; asserts in both directions by default |
| pytest-httpserver | Real local HTTP server | 1.1.5, 2026-02-14, maintained | Real sockets; allow loopback when you block the network |
| vcrpy | Record and replay HTTP | 8.3.0, 2026-07-04, maintained | Default `once` records when a cassette is missing |
| pytest-recording | pytest front end for vcrpy | 0.13.4, 2025-05-08, maintained | Defaults to `--record-mode=none`; offers `--block-network`; replaces pytest-vcr, abandoned since 2019 |
| moto | In-process AWS mock | 5.2.3, 2026-08-22, maintained | Create clients inside the mock; not for multithreaded use |
| LocalStack | AWS emulator in a container | CLI 2026.8.2, 2026-09-28, partly maintained: open-source repository archived 2026-03-23 | Check the licence terms first |
| testcontainers | Throwaway Docker containers | 4.15.0, 2026-07-24, maintained | No reuse; 1 s default readiness poll; needs Docker |
| pytest-socket | Block or restrict network access | 0.8.1, 2026-08-19, maintained | Python's `socket` module only; load with `-p socket` |
| freezegun | Freeze time | 1.5.5, 2025-08-09, partly maintained (171 open issues) | Cost grows with loaded modules; freezes `monotonic`; pytest-freezer 0.4.9 (2024-12-12) wraps it, and pytest-freezegun (2020) is abandoned |
| time-machine | Move time | 3.5.1, 2026-09-08, maintained | Constant cost; leaves `monotonic` alone; migration tool in the `cli` extra |
| pytest-randomly | Shuffle order and reseed generators | 5.0.0, 2026-09-01, maintained | Does not reseed `uuid4`, `secrets`, or NumPy `Generator` objects |
| Hypothesis | Property-based testing | 6.168.3, 2026-09-28, maintained | The built-in `ci` profile loads in CI |
| `celery.contrib.pytest` | In-process Celery app and worker fixtures | celery 5.6.3, 2026-03-26, maintained | Prefer `celery_session_worker` |
| pytest-celery | Docker-based Celery tests | 1.3.0, 2026-03-02, maintained | Not compatible with `celery.contrib.pytest` |
| RQ | Redis job queue | 2.12.0, 2026-08-30, maintained | `is_async=False` runs jobs in the calling thread |
| Dramatiq | Task queue | 2.2.1, 2026-09-02, maintained | `StubBroker`; actor errors surface after retries run out |
| Click and Typer `CliRunner` | In-process CLI tests | click 8.5.0, 2026-08-26; typer 0.27.2, 2026-08-28; maintained | Redirects process-global streams; `isolated_filesystem` deprecated in Click 8.5 |
| pytest-console-scripts | Console scripts in process or in a subprocess | 1.4.1, 2023-05-31, partly maintained | `both` mode runs each test twice |
| pytest-playwright | Playwright browser tests | 0.9.0, 2026-08-10 (Playwright 1.63.0, 2026-09-15), maintained | `retain-on-failure` still records every test |
| Selenium | Browser automation | 4.49.0, 2026-09-09, maintained | Selenium Manager downloads unless cached or `SE_OFFLINE=true` |
| Starlette `TestClient` | Synchronous client for Starlette and FastAPI apps | starlette 1.7.0, 2026-09-23, maintained | New portal per request without `with`; prefers httpx2 since 1.2 |
| httpx | HTTP client and `ASGITransport` | 0.28.1, 2024-12-06, partly maintained | No release since 2024; `app=` removed in 0.28 |
| httpx2 | Pydantic's httpx fork | 2.13.1, 2026-09-23, maintained | Mock libraries have not caught up |
| asgi-lifespan | Lifespan for async clients | 2.1.0, 2023-03-28, partly maintained | Little release activity |
| pytest-timeout | Stop hung tests | 2.4.0, 2025-05-05, maintained | A guard, not a fix; alone, it hides the cause |

## Evidence

- Django password hashing, about 2,500 tests: 447 s of a 610 s run (73%) went to PBKDF2 across about 2,200 test-user creations. After the switch to a fast hasher, CI fell from about 30 minutes to under 8, and a local run from about 3 minutes to under 45 s [2].
- Django password hashing, 355 tests: `pbkdf2_hmac` took 82.8% of the runtime (26,470 ms), and a fast-hasher fixture took the suite from about 30 s to about 3 s. The author profiled with cProfile and sorted by `tottime` [3].
- freezegun against time-machine, 2026: about 1.4 ms plus 2.5 µs per loaded module, and 41 ms against 1.5 µs at 16,259 modules [5]. The author maintains time-machine, which is a caveat; this skill's micro-benchmarks reproduce the shape [1].
- Kopf, an open-source Kubernetes operator framework: about 7,000 asyncio unit tests run in about 2 minutes with looptime, adopted to stabilise time-based tests; no before-and-after timing is published [4, 20].
- Zulip, a large Django project: outgoing network requests raise in tests, and the backend suite with about 98% coverage runs "in under a minute on a fast laptop". Webhook tests, excluded from the default run, "would otherwise account for about 25% of the total runtime" [17]; selection is in [scheduling.md](scheduling.md).
- This skill's micro-benchmarks: every number cited to [1], measured on one Apple M4 Max with macOS and CPython 3.14.0, as the minimum or median of repeated runs. Identical whole-suite runs on that shared machine varied from 3.5 s to 20.8 s [1].

## Sources

1. Micro-benchmarks and experiments for this skill's research, 2026-09-30: Apple M4 Max, macOS, CPython 3.14.0, a shared machine; minimum or median of repeated runs. No public URL.
2. https://dschaefer.substack.com/p/django-password-hashing-speed-up – 73% of runtime in PBKDF2; CI from about 30 to under 8 minutes.
3. https://belderbos.dev/blog/profile-django-test-suite-10x-faster/ – 82.8% of runtime in `pbkdf2_hmac`; 30 s to 3 s.
4. https://github.com/nolar/looptime – looptime: fake loop time; Kopf's test count and runtime.
5. https://adamj.eu/tech/2026/08/03/python-time-machine-o1-freezegun-on/ – 2026 benchmark, correctness gaps, and the migration tool.
6. https://github.com/testcontainers/testcontainers-python/blob/main/src/testcontainers/core/config.py – polling interval and retry defaults; no reuse option.
7. https://github.com/django/django/blob/main/django/test/utils.py – `setup_test_environment()` source: locmem email backend and `MAILERS`.
8. https://docs.djangoproject.com/en/dev/topics/testing/overview/ – Django testing overview: fast hashers, `DEBUG=False` in tests, caches not cleared between tests.
9. https://pytest-django.readthedocs.io/en/latest/usage.html – `django_debug_mode` and its default.
10. https://docs.djangoproject.com/en/dev/topics/cache/ – `DummyCache` and per-process `LocMemCache`.
11. https://github.com/celery/celery/blob/main/celery/app/task.py – eager `apply_async` serialization and immediate retries.
12. https://github.com/microsoft/playwright-pytest/blob/main/pytest-playwright/pytest_playwright/pytest_playwright.py – tracing and video for every test under `retain-on-failure`.
13. https://github.com/django/django/blob/main/django/contrib/auth/hashers.py – hashers and PBKDF2 iterations in Django 6.1.
14. https://github.com/getsentry/sentry/blob/master/src/sentry/testutils/pytest/sentry.py – Sentry's test settings: hasher, caches, broker, `getfqdn` patch, task stubs.
15. https://github.com/django/django/tree/main/docs/releases – release notes 4.2 to 6.1: PBKDF2 iteration increases.
16. https://github.com/miketheman/pytest-socket – what pytest-socket patches, and when.
17. https://zulip.readthedocs.io/en/latest/testing/testing.html – Zulip's network ban, suite runtime, and webhook-test exclusion.
18. https://docs.python.org/3/library/time.html#time.sleep – `time.sleep` audit event since Python 3.13.
19. https://trio.readthedocs.io/en/stable/reference-testing.html – `MockClock` and `autojump_threshold`.
20. https://github.com/nolar/kopf/pull/881 – Kopf's move to looptime to stabilise time-based tests.
21. https://github.com/kvas-it/pytest-console-scripts – in-process default and `script_launch_mode`.
22. https://github.com/pallets/click/blob/main/CHANGES.md – `CliRunner` changes in 8.2, 8.4, and 8.5.
23. https://playwright.dev/python/docs/test-runners – pytest-playwright options and fixture scopes.
24. https://www.selenium.dev/documentation/selenium_manager/ – driver and browser downloads, cache lifetime, and `SE_OFFLINE`.
25. https://playwright.dev/python/docs/browsers – headless shell and `--only-shell`.
26. https://github.com/spulec/freezegun – freezegun: patched functions including `monotonic`, `real_asyncio`, and the ignore list.
27. https://github.com/python/cpython/blob/3.14/Lib/uuid.py – `uuid4()` from `os.urandom`; `uuid7()` monotonic counter.
28. https://pypi.org/pypi/{package}/json – PyPI JSON API and GitHub repository metadata: versions, release dates, and archive status.
29. https://github.com/adamchainz/time-machine/blob/main/src/time_machine/__init__.py – `TZ` and `tzset()` handling for aware destinations.
30. https://time-machine.readthedocs.io/en/latest/usage.html – mocked functions and global-state caveats.
31. https://docs.python.org/3/library/devmode.html – development mode turns on asyncio debug mode.
32. https://github.com/django/django/blob/main/django/db/backends/base/base.py – `queries_limit` and `queries_logged`.
33. https://docs.djangoproject.com/en/dev/ref/templates/api/ – cached template loader on when `loaders` is not set.
34. https://docs.djangoproject.com/en/dev/ref/files/storage/ – `InMemoryStorage` and the `STORAGES` setting.
35. https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/ – `ManifestStaticFilesStorage` warning for tests.
36. https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html – `IS_RUNNING_TESTS`.
37. https://github.com/django/django/blob/main/django/core/mail/utils.py – `CachedDnsName` and the `socket.getfqdn()` comment.
38. https://man7.org/linux/man-pages/man5/resolv.conf.5.html – resolver `timeout` and `attempts` defaults.
39. https://github.com/HypothesisWorks/hypothesis/blob/master/hypothesis/docs/changelog.rst – `ci` profile auto-loading, thread handling (with `_settings.py` in 6.168.3).
40. https://github.com/getsentry/responses – responses defaults for `assert_all_requests_are_fired`.
41. https://github.com/lundberg/respx/issues/317 – respx releases and open httpx2 support issues.
42. https://colin-b.github.io/pytest_httpx/ – pytest-httpx defaults for unused and unexpected requests.
43. https://github.com/encode/httpx/blob/master/CHANGELOG.md – 0.28.0 removed `app=` and made JSON bodies compact; 0.28.1 on 2024-12-06.
44. https://github.com/Kludex/starlette/pull/3291 – `TestClient` prefers httpx2 (Starlette 1.2.0).
45. https://vcrpy.readthedocs.io/en/latest/usage.html – vcrpy record modes and filters.
46. https://github.com/kiwicom/pytest-recording – `--record-mode` default `none` and `--block-network`.
47. https://docs.getmoto.org/en/latest/docs/getting_started.html – `mock_aws`, fake credentials, client order, and thread limits (with the FAQ).
48. https://github.com/localstack/localstack – archived repository notice and the unified image.
49. https://docs.celeryq.dev/en/stable/userguide/testing.html – eager mode "not suitable for unit tests", `celery.contrib.pytest`, and pytest-celery.
50. https://dramatiq.io/guide.html – unit testing with `StubBroker` and `join()`.
51. https://python-rq.org/docs/testing/ – `is_async=False` and `SimpleWorker`.
52. https://github.com/pytest-dev/pytest-randomly – reseeded libraries and per-test seeds.
53. https://pytest-asyncio.readthedocs.io/en/latest/reference/changelog.html – changes from 1.0.0 to 1.4.0.
54. https://anyio.readthedocs.io/en/stable/testing.html – AnyIO's pytest plugin and its conflict with pytest-asyncio's auto mode.
55. https://github.com/encode/starlette/blob/master/starlette/testclient.py – `TestClient` portal per request without `with`, lifespan, and event-loop warning (with `docs/testclient.md`).
56. https://fastapi.tiangolo.com/advanced/async-tests/ – `AsyncClient` with `ASGITransport`; lifespan not triggered.
57. https://pytest-asyncio.readthedocs.io/en/latest/concepts.html – event-loop scopes and modes.
58. https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/migrate_from_0_23.html – migration to `loop_scope`.
59. https://peps.python.org/pep-0578/ – audit hooks cannot be removed; negligible overhead without hooks.
60. https://docs.python.org/3/library/sys.html#sys.addaudithook – audit hooks are "not suitable for implementing a sandbox".
61. https://github.com/miketheman/pytest-socket/issues/66 – asyncio's socket pair blocked under `--disable-socket`.
