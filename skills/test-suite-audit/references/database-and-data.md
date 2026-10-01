# Database and test data

This page covers how database-backed tests spend time and how you measure it: isolation modes (rollback or flush), test data creation (factories, fixture files, class-level data), test database creation (reuse, migrations, templates, per-worker databases, containers), server settings, and SQLAlchemy sessions. Load it in phase 7 when database setup or teardown dominates the baseline, when the first test on each worker pays seconds of setup, or when factories and transactions sit in the hot path. Every recipe that runs tests needs the user's agreement from phase 1, goes through `run_suite.py`, and uses a local, disposable database server. Framework settings unrelated to the database are in [framework-runtime.md](framework-runtime.md), and workers and shards in [scheduling.md](scheduling.md). Numbers marked [1] come from the skill's research benchmark and from checks for this page, on PostgreSQL 16 and a shared, noisy laptop. Trust their ratios more than their absolute times, and measure on the continuous integration (CI) runner type before you estimate a saving.

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Transactional tests where rollback would do | `transactional-tests` in `AUDIT/static.json`, then tests and seconds per mode (M2) | Over 5% of database tests or 10% of their time, or a base class makes it the default | `TestCase` or plain `django_db`; `captureOnCommitCallbacks`; `available_apps` for the rest | 375 → 120 s for one suite [2]; a full flush cost 90–160× a rollback test [1] |
| Factory cascades | M6 estimate, then inserts per table (M3, M4) | 5+ rows per `create()`, or a table's inserts over 3× the tests that use it | Shared parents with `SelfAttribute`; opt-in related factories | 19 → 6 INSERTs per test [1]; 50 → 12 min in a Ruby suite [3] |
| Shared data created per test | `setUp` or function fixtures that insert (M1); identical inserts per test (M3) | (tests in class − 1) × setup time over 1 s | `setUpTestData`; a class-scoped atomic fixture | "3x ... or more" [4]; 5× locally [1] |
| Test database or server built from scratch every run or worker | `--create-db` in `addopts`; no reuse flag; container fixtures below session scope; M5 | Creation over 10% of a local run or 30 s per CI job | Reuse locally; in CI, a database cached by migration hash; session-scoped containers | Preparation with migrations was 37% of Shopify's CI time [5]; 3.8 s per run locally [1] |
| Factory work the test does not need | Password hashing, `create()` in pure-logic tests, Faker, signals (M1, M3) | Default password hasher in factories; modules of pure-logic tests that save rows | Fast test hasher; `build()` or `prepare()`; static values | 125 ms against 0.026 ms per hash; `build()` 1.34 ms against 7.5 ms [1] |
| SQLite standing in for the production engine | Test `ENGINE` or address differs from production | Always | Run tests on the production engine | Fidelity: the suite tests a different system |
| SQLAlchemy schema churn per test | `create_all`, `drop_all`, or `TRUNCATE` in function-scoped fixtures | Any per-test schema build beyond a few tables | Outer transaction with `join_transaction_mode="create_savepoint"` | About 35× locally [1] |
| N+1 and excess queries | M3: `max_repeat_select`, `statements` | 10+ repeats of one `SELECT`, or 100+ statements per test | Eager loading; lock counts with query assertions | Fewer statements; guards the product's query count |
| Commit-heavy phases on durable storage | `SHOW fsync`; commits per test after subtracting setup (M4) | Disposable test server with `fsync` on, and commit-heavy phases | `fsync`, `synchronous_commit`, `full_page_writes` off; memory-backed data directory | About 30% on one Django suite [6]; 0 on rollback tests [1] |

## Signals

### Transactional tests where rollback would do

**Detect:** Django's `TestCase` rolls each test back. `TransactionTestCase` and its live-server subclasses flush every table after each test, emit `post_migrate` again unless `available_apps` is set, and close every connection [7, 8]. In pytest-django, `transaction=True`, `reset_sequences=True`, and the `transactional_db` and `live_server` fixtures behave the same way [9]. Start from `transactional-tests` in `AUDIT/static.json`. It follows project base classes, module-level and class-level `pytestmark`, positional `django_db(True)`, `reset_sequences=True`, and the transactional fixtures, and in checks it found all 9 transactional constructs in a corpus and all 4 transactional tests in a project copy [1]. It counts constructs, not tests, and it cannot see a mark built at run time, such as `pytestmark = MARKS[MODE]`, so count tests per mode, and their share of time, with M2. Report when transactional tests exceed 5% of database tests or 10% of their time, or when one base class makes them the default; `git log -S TransactionTestCase` shows when it arrived. Report every `serialized_rollback=True` and `reset_sequences=True` with the number of tests it covers.

**False positives:** Some tests need real commits: `on_commit` callbacks without `captureOnCommitCallbacks`, `select_for_update` and other locks, code with its own connection or thread (a live server, Channels, Celery on another connection), code that calls `connection.close()`, and `TEST['MIRROR']` replica tests [7, 10]. `live_server` implies `transactional_db`, so browser tests stay transactional [9]. `serialized_rollback` restores rows from data migrations, so tests that read those rows break without it [10]. Converting a commit test to rollback can let it pass without exercising the commit, which weakens it.

**Fix:**
1. On a branch, switch the base class or marker to rollback isolation, run the suite, and restore the transactional mode only for tests that fail for a reason above. Django prefers `TestCase` in most situations because it runs faster [7].
2. For `on_commit` callbacks, use `TestCase.captureOnCommitCallbacks(execute=True)` or pytest-django's `django_capture_on_commit_callbacks`, but not in `transaction=True` tests [7, 9].
3. For tests that must flush, set `available_apps`: a class attribute, or `django_db(transaction=True, available_apps=[...])`, which pytest-django marks experimental. It limits the flushed tables and skips the per-test `post_migrate` [8, 9]. A test that touches a model outside the listed apps then fails.
4. Replace `serialized_rollback` with explicit data, and `reset_sequences` with assertions on returned objects instead of literal primary keys. `static_scan.py diff` lists changed assertions, so each needs the user's approval. In custom cleanup code, clean only the tables a test wrote. On PostgreSQL, Django's flush is one `TRUNCATE` over every table [8], which is slow for many small tables. `DELETE` fires delete triggers and does not reset sequences.

**Effect:** ev.energy went from 375 s to 120 s by changing one base class [2]. `available_apps` cut Django's own PostgreSQL transaction tests from 55 s to 4.5 s [11]. On 164 tables, a rollback test cost about 5 ms, a full flush 473–773 ms, and an `available_apps` flush of 15 tables 62–78 ms; each full flush re-inserted 805 content type and permission rows [1]. Django documents `serialized_rollback` as about 3× slower [10]; locally it added 0–7%, because little data needed serialising, and `reset_sequences=True` added 164 sequence queries to one test [1]. `DELETE` on 164 nearly empty tables took 12–16 ms against about 300 ms for `TRUNCATE` [1], and Carbon Health cut CI time by about 30% by cleaning only written tables [12].

**Verify:** Converted tests pass twice in random order (`-p randomly`, or `manage.py test --shuffle`), because the flush can hide isolation bugs ([flakiness.md](flakiness.md)). Outcomes and the mutation score of converted modules do not change ([mutation-testing.md](mutation-testing.md)). M2's time per mode falls, and `results.py diff` over 3 runs each shows the same tests with a lower median.

### Factory cascades

**Detect:** A factory cascade is excess data from nested factory calls [3]. In factory_boy, each `SubFactory` creates its own parent unless the caller passes one, and each `RelatedFactory` or `RelatedFactoryList` creates children after the object [13]. Run M6 for estimated rows per `create()` with a per-model breakdown, then confirm the top entries with inserts per table (M3 or M4). Report factories with 5 or more rows per `create()`, and tables whose inserts exceed 3× the tests that use them. Several rows of one top-level entity, such as 5 organisations for one comment, are also a correctness smell: objects that should share a tenant land in different ones [14, 15].

**False positives:** Some tests need the full graph, such as permission checks across tenants. A shared default parent changes a test that relies on two distinct parents, so TestProf limits defaults to top-level entities such as tenants [15]. `django_get_or_create` hides a cascade and ignores new values for an existing row [13].

**Fix:** Share parents with `SelfAttribute`, for example `owner = SubFactory(MemberFactory, account=SelfAttribute("..account"))` and `assignee = SelfAttribute("project.owner")`. Make `RelatedFactory` and `RelatedFactoryList` children opt-in, with size 0 by default and a trait that adds them, and set `skip_postgeneration_save = True` in `class Meta`, because post-generation declarations otherwise save the object a second time [13]. Pass shared parents explicitly from class-level data (next signal), which also documents the relationship in the test.

**Effect:** Shared parents cut `CommentFactory()` from 19 INSERTs to 6, and the mean test from 7.5 ms to 4.1 ms, on a local database [1]. A remote CI database pays a round trip for every INSERT. GitLab found a factory that created 208 projects in 9.5 s, about a third of them used [14]. Evil Martians saw one `create(:comment)` make 10 records, and a suite went from 50 to 12 minutes after factory work [3].

**Verify:** INSERTs per test (M3) and per table (M4) drop, and so does the M6 estimate. Outcomes do not change; for a test that relied on distinct parents, pass explicit parents rather than reverting the factory.

### Shared data created per test

**Detect:** A `setUp()` method or function-scoped fixture that inserts the same rows repeats the work for every test. Find `TestCase` classes whose `setUp` creates rows (M1), and start with classes of 5 or more tests; in M3, every test of such a class shows the same inserts. A `fixtures = [...]` list loads once per class on `TestCase` but before every test on `TransactionTestCase` [7, 8], and a function-scoped fixture that calls `call_command("loaddata", ...)` reloads per test. Report when (tests in the class − 1) × setup time per test exceeds 1 s.

**False positives:** Since Django 3.2, `setUpTestData` deep-copies class attributes on first access in each test, so objects that cannot be copied fail, and large object graphs make every access slow; store primary keys instead [7, 8]. On a database without transactions, it runs before every test and saves nothing [7]. Suite-wide seeded data is a trap. Data written through `django_db_blocker.unblock()` is committed and never restored [9], so it survives into the next `--reuse-db` run. Discourse abandoned such a data set, because many tests assume a blank database [16].

**Fix:** In a Django `TestCase`, move the creation from `setUp` to `setUpTestData`, and change `self.` to `cls.` [4]. Load large read-only reference data once per session in a `django_db_setup` override [9], keep it immutable, and make count assertions relative. Replace large fixture files with factories or `bulk_create` in `setUpTestData`; `bulk_create` skips `save()` and signals. pytest-django has no class-scoped database fixture [9]. Write the class as a `django.test.TestCase` subclass, or use the fixture below. It passed with pytest-django 4.14.0 and Django 6.1.1, serially and under pytest-xdist, and left the database empty [1]. Each test's own `db` fixture then runs in a savepoint. The class must contain no `transaction=True` test, whose flush would wipe the class data. Nothing deep-copies the objects, so tests re-fetch them rather than mutate them:

```python
from django.db import transaction
@pytest.fixture(scope="class")
def class_orders(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        atomic = transaction.atomic()
        atomic.__enter__()
        try:
            yield OrderFactory.create_batch(50)
        finally:
            transaction.set_rollback(True)
            atomic.__exit__(None, None, None)
```

**Effect:** Adam Johnson reports that `setUpTestData` "often" gives "a 3x speedup, or more", and sometimes 10× (opinion with examples) [4]. 50 tests that each needed about 250 rows took 0.8–1.06 s with a class-scoped fixture, against 4.6–4.9 s with a function-scoped one [1]. Under pytest-xdist, `--dist load` and `worksteal` repeat class setup on every worker that receives a test of the class: `results.py fixtures` counted 2 setups on 2 workers, and 1 with `loadscope` [1, 17]. Weigh that against idle workers with [scheduling.md](scheduling.md).

**Verify:** The class passes in random order, and each test passes alone (`PATH::Class::test`). After a change to seeded data, run twice with `--reuse-db` and once with `--create-db`, and compare.

### Test database or server built from scratch every run or worker

**Detect:** Django's runner creates and destroys the test database on every run unless you pass `--keepdb`, and pytest-django does the same without `--reuse-db` [9, 10]. Creation runs every migration: count them with `find . -path '*/migrations/*.py' ! -name '__init__.py' | wc -l`. Look for `--create-db` in `addopts`, no reuse flag in contributor instructions, and CI jobs that migrate once per shard. Under pytest-xdist, pytest-django migrates a separate `test_NAME_gwN` database for each worker, while Django's `--parallel` migrates once and clones it per process [8, 9]. Containers count too: `grep -rnE "PostgresContainer|MySqlContainer|DockerContainer|postgresql_proc|docker compose up" --include='*.py' .`, then check each fixture's scope. Measure creation with M5. Report when creation exceeds 10% of a local run or 30 s per CI job, when every worker and shard pays it, or when a container fixture below session scope serves more than one test.

**False positives:** `--reuse-db` and `--keepdb` do not re-run edited migrations, so a branch switch needs `--create-db` [9, 10]. A reused database exists per worker, so a new `-n` value builds new ones. Tests that change server configuration or crash the server can need their own container.

**Fix:**
1. Reuse the database locally, and document when to pass `--create-db`. This costs no fidelity.
2. In CI, cache a migrated database keyed by a hash of the migration files and anything else that shapes the schema, as Shopify and Zulip do [5, 18]. Restore it as a dump or a PostgreSQL template.
3. Session-scope containers, one per worker or one shared with a database per worker. testcontainers-python has no container reuse in its core, unlike Testcontainers for Java, so a long-lived compose service is the local alternative [19]. pytest-postgresql starts one server per session and clones a template database for each test [20].
4. Clone a template per worker only after you time clones on the CI runner (M7). Terminate other sessions on the template first, because `CREATE DATABASE` fails while any exist [21]; Mergify traced 20-minute CI timeouts to stranded connections on a template [22]. Put a `django_db_setup` override in the root `conftest.py`: loaded with `-p`, pytest-django's own fixture won without an error [1].
5. Squash migrations when there are hundreds; `RunPython` operations are only optimised away when marked `elidable` [10]. Skip migrations (`--no-migrations`, or `TEST['MIGRATE'] = False`) only in local loops. Keep a CI job that migrates from scratch and runs `makemigrations --check`, plus dedicated migration tests with django-test-migrations or pytest-alembic. Without migrations, pytest-django builds tables from the models [9]. Data migrations and `RunSQL` objects, such as triggers and views, are then missing, and a model change without a migration passes, as reproduced locally [1]. Never reuse one database across migrated and unmigrated runs: it failed with `DuplicateTable` [1].

**Effect:** Shopify's preparation, migrations included, was about 37% of CI time before they cached it [5]. With 310 migrations and 164 tables, creation cost 3.8 s with migrations and 1.7–1.9 s without; a run on a reused database paid none of it [1]. pgtestdb reports about 10 ms per clone and IntegreSQL 11 ms on average [23, 24], but local clones of a 13 MB database took 0.4–1.7 s. With 4 workers on 16 cores, per-worker clones (8.8–10.2 s) were slower than concurrent migration (6.2–7.8 s), because clones of one template run one at a time [1]. Cloning should win when workers outnumber cores or migrations are slow (reasoning, not measured). Container start-up was not measured: the research could not run Docker, and published figures conflict.

**Verify:** The same tests and outcomes on a fresh and a reused database, and a scheduled CI job that creates from migrations. During a parallel run, `SELECT datname, count(*) FROM pg_stat_activity GROUP BY 1` shows one database per worker, and `docker events --filter event=start` one container start per worker. An override of `django_db_setup` or `django_db_modify_db_settings`, or an SQLAlchemy address without the worker's name, makes workers share one database [9], so derive every name from `worker_id` or `PYTEST_XDIST_WORKER`.

### Factory work the test does not need

**Detect:** Factories run Python for every object, and cascades multiply it. Grep factories for password hashing, `post_generation`, and signals (M1), and check the test settings' hasher ([framework-runtime.md](framework-runtime.md)). In M3's per-test records (`by_verb` in `db-<worker>.json`), a test with INSERTs but no `SELECT`, `UPDATE`, or `DELETE` likely tests Python logic on saved objects. Report a user factory that hashes with the default hasher, and modules of pure-logic tests that save rows.

**False positives:** Unsaved objects lack database-generated values: primary keys, `auto_now`, database defaults, and triggers. Related managers such as `obj.children.all()`, `refresh_from_db()`, and `full_clean()` uniqueness checks need saved objects, and Django refuses to save an object whose foreign key points to an unsaved one.

**Fix:** Put a fast hasher first in the test settings, and keep one test on the real hasher; details are in [framework-runtime.md](framework-runtime.md). For tests of pure Python logic, use `Factory.build()`, whose strategy propagates to every `SubFactory`, or model_bakery's `prepare()` [13, 25]. Remove the database mark, or use `SimpleTestCase`, so an accidental query fails loudly [7, 9], and confirm with mutation testing that converted tests still catch faults, because they stop exercising constraints. Use `Sequence` or static values where the content does not matter, and mute expensive signals with `factory.django.mute_signals` where the test does not need them [13].

**Effect:** Django 6.1.1's default PBKDF2 hasher took 125 ms per `make_password`, against 0.026 ms for MD5 [1]. `CommentFactory.build()` took 1.34 ms, against 7.5 ms per test with `create()` [1]. Faker cost 0.3 ms per `Faker()` and 6–73 µs per provider call, against about 0.2 ms per local INSERT, so fix isolation, cascades, and hashing first [1].

**Verify:** The same tests and outcomes, fewer INSERTs per test (M3), and a lower median over 3 runs. Converted tests fail when you break the logic under test ([mutation-testing.md](mutation-testing.md)).

### SQLite standing in for the production engine

**Detect:** The test settings use `django.db.backends.sqlite3`, or an `sqlite://` address, while production uses PostgreSQL or MySQL; `connection.vendor == "sqlite"` branches are another sign. Report it every time. Guardrail 5 forbids you to make this swap, and the same reasons apply to the project's own settings.

**False positives:** None when the code uses backend-specific fields or Structured Query Language (SQL), such as array fields, JavaScript Object Notation (JSON) lookups, full-text search, `DISTINCT ON`, or extensions; raw SQL; constraints or triggers that enforce business rules; `select_for_update`; isolation semantics; or `RunSQL` migrations. A pure object-relational mapper (ORM) loop is acceptable only with a CI job on the production engine.

**Fix:** Run the suite on the production engine. Rollback isolation and the server settings below remove most of its per-test cost.

**Effect:** SQLite stores 2,000-character strings in `VARCHAR(50)` columns, keeps foreign keys off by default, and allows "dubious SQL ... without any error or warning". Under Django, `select_for_update()` has no effect, and `contains` ignores case [26]. No rigorous benchmark of the speed gap to a tuned PostgreSQL was found.

**Verify:** Run on the production engine and compare outcomes: each difference is a bug that the SQLite run hid or invented.

### SQLAlchemy schema churn per test

**Detect:** `grep -rnE "metadata\.(create_all|drop_all)|TRUNCATE|alembic.*upgrade" --include='*.py' TEST_ROOTS`, then check the scope of each fixture that calls them: function scope, or no scope, means per test. Report any per-test schema build beyond a few tables.

**False positives:** Code under test that opens its own connection or engine (background workers, a second engine, raw driver connections) sees none of the uncommitted data and escapes the rollback. Those tests need a database per test, such as a template clone, or explicit cleanup.

**Fix:** Create the schema once in a session-scoped engine fixture. In the function-scoped session fixture, open `conn = engine.connect()` and `trans = conn.begin()`, yield `Session(bind=conn, join_transaction_mode="create_savepoint")`, then close the session, call `trans.rollback()`, and close the connection; even a `session.commit()` inside the test is rolled back [27]. The async form uses `create_async_engine`, `await conn.begin()`, and `AsyncSession(bind=conn, join_transaction_mode="create_savepoint")`. It needs `greenlet`, and the engine and the tests must share one session-scoped event loop [1, 27].

**Effect:** 100 tests on 60 tables took 1.9–2.3 s, against 69–71 s with `create_all` and `drop_all` per test: about 35× [1].

**Verify:** A first assertion that a table is empty passes in random order, and a deliberate `session.commit()` inside a test is rolled back.

### N+1 and excess queries

**Detect:** N+1 queries are one query per row of an earlier result. M3 records statements per test and the most repeated `SELECT`, with `IN` lists normalised. Report tests with 100 or more statements, or 10 or more repeats of one `SELECT`, in the code under test or in setup. Never read `connection.queries`: Django runs tests with `DEBUG=False`, so it stays empty [10]. In SQLAlchemy, `lazy="raise"` or `raiseload("*")` turns unplanned lazy loads into errors [28]; django-zeal raises on N+1 patterns and claims 3–5% overhead [29].

**False positives:** Bulk import tests can intend high counts. On a small sample, the first database test on each worker also carries the migration check (26 repeats of one content type `SELECT` locally), and a transactional test carries its own flush [1].

**Fix:** Load eagerly: `select_related` or `prefetch_related` in Django, or loader options in SQLAlchemy. Then lock the count with `django_assert_max_num_queries`, or with inline-snapshot-django, which django-perf-rec's author now recommends [9, 29]. Fix N+1 in setup with `bulk_create` or shared parents.

**Effect:** Fewer statements and less database time per test (M3), and a guard on the product's query count.

**Verify:** In a disposable copy, remove the eager load: the new assertion or snapshot must fail.

### Commit-heavy phases on durable storage

**Detect:** On the test server, run `SHOW fsync; SHOW synchronous_commit; SHOW full_page_writes;`, and read the CI service definition for `-c fsync=off` or a memory-backed (tmpfs) data directory. In M4, subtract a one-test run's commits before you divide by tests: setup alone made 62 commits, whether the run had 1 or 100 rollback tests [1]. Rollback tests then add about one `xact_rollback` each, while transactional tests added about 90 commits each [1]. The settings speed up whatever commits: creation, migrations, flushes, `FILE_COPY` clones, and fixture loads. Rollback tests never commit, so they gain little.

**False positives:** A server with data anyone needs: never change it. PostgreSQL on macOS syncs with `open_datasync` by default, so local gains understate Linux CI gains [1].

**Fix:** Start only the disposable test server with `postgres -c fsync=off -c synchronous_commit=off -c full_page_writes=off` and a tmpfs data directory, for example `docker run --tmpfs /var/lib/postgresql/data`, or `with_tmpfs_mount()` in testcontainers [19, 21]. `synchronous_commit` also works per session, through `"OPTIONS": {"options": "-c synchronous_commit=off"}` [1]. For MySQL, the levers are the doublewrite buffer, `innodb_flush_log_at_trx_commit`, `sync_binlog`, and `--skip-log-bin` [30]. Tests lose no protection: a crash destroys only test data.

**Effect:** OpenHEXA's Django suite went from about 180 s to 123–150 s, about 30% [6]. pythonspeed measured 28% on 10,000 autocommit INSERTs, despite a "10×" title [31]. Locally, full flushes got about 8% faster and rollback tests not at all, while creation on PostgreSQL 14 roughly halved [1]. A 60 → 10 minute gain on containerised storage reflects that storage, not PostgreSQL [32].

**Verify:** Compare one commit with only the server settings changed (M7), 3 or more runs each, on the CI runner type.

## Measuring

- `run_suite.py run --db-probe` loads the skill's database plugin for pytest-django without installing it. It writes `db-<worker>.json` per process and `db-summary.json` into the run folder, prints `db-` lines at the end of `output.log`, and refuses a folder inside the project. A wrapper that drops `PYTHONPATH` or `PYTEST_ADDOPTS` drops the plugin too, so check that `db-summary.json` appears.
- The probe wraps every statement, so `run_suite.py` marks its runs `instrumented: profile`: their counts are evidence, and their times only rank.
- `--create-db` drops and recreates the test database: ask first ([traps.md](traps.md)).
- The first database test on each worker carries database creation, and the last test carries teardown. Warm the databases with one run at the same `-n` and then measure with `--reuse-db`, or discount both tests.
- `NN` is the run number that `run_suite.py` prints, `SAMPLE_PATHS` the sampled test files, `TEST_SETTINGS` the test settings module, `TEMPLATE_DB` a migrated test database, and `CREATE_RUN_DIRS` and `REUSE_RUN_DIRS` the run folders of each set.

### M1. Static inventory (seconds, no project code)

```sh
python3 -c "import json; print(json.load(open('AUDIT/static.json'))['checks'].get('transactional-tests'))"
grep -rnE "TransactionTestCase|LiveServerTestCase|(transaction|reset_sequences|serialized_rollback)\s*=\s*True|\b(transactional_db|live_server)\b" --include='*.py' . | wc -l
grep -rn -A15 "def setUp(self" --include='test*.py' . | grep -cE "\.create\(|Factory\(|create_batch|baker\.make|loaddata"
grep -rnE "SubFactory|RelatedFactory|post_generation|django_get_or_create|set_password|make_password|factory\.django\.Password|mute_signals" --include='*.py' . | wc -l
grep -rnE "\-\-(create-db|reuse-db|no-migrations|keepdb)|\bMIGRATE\b" pytest.ini pyproject.toml setup.cfg tox.ini .github .gitlab-ci.yml Makefile 2>/dev/null
grep -rnE "sqlite3|sqlite://" --include='*.py' . | grep -v /migrations/ | head
```

The hits are candidates, because comments and dead code match too: read a sample of each.

### M2. Isolation mode per test (one collection run, no database)

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label db-modes --timeout 900 --cwd ROOT --db-probe -- \
    CI_TEST_COMMAND --collect-only -q --audit-db-times=AUDIT/results/baseline-summary.json
grep '^db-' AUDIT/runs/NN-db-modes/output.log
```

Lines read `db-mode 13 46.4% 5.3 s  pytest:transactional`: the tests, their share of the collected tests, the seconds they took in the baseline, and the mode. `db-summary.json` holds the same per mode. Rank modes by seconds: the transactional share of database-test time sets the first signal's threshold. Give `--audit-db-times` only the summary of an uninstrumented run of the same tests. The last line says for how many tests it found a time, and in a check every collected test matched [1]. A collection run touches no database, and pytest-xdist does not distribute it, so CI's `-n` can stay. The plugin needs pytest-django; for Django's own runner, use M1 and M4.

### M3. SQL per test (one instrumented run of a sample)

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label dbprof --timeout 1800 --cwd ROOT --db-probe -- \
    CI_TEST_COMMAND SAMPLE_PATHS --reuse-db
grep '^db-' AUDIT/runs/NN-dbprof/output.log
```

The `db-sql` lines give the statements, the database's share of the instrumented time, INSERTs per test for the top tables, and the worst test by INSERTs, by statements, and by repeats of one `SELECT`. `db-summary.json` holds the top 20 of each, and `db-<worker>.json` every test's record, with statements by verb. A cascade shows as tables with more inserts per test than the tests need: in a check, the organisation and account tables had 5.00 each, as the M6 estimate predicted [1]. A repeat count of 10 or more is a likely N+1. The database share bounds what database work can save, but it comes from an instrumented run. The probe counts statements, not rows: one `bulk_create` is one INSERT, so take row counts from M4. Setup counts in the test that triggers it, so `setUpTestData` rows appear in the first test of their class, and statements on other threads or connections are not seen [1]. For SQLAlchemy, count in a `before_cursor_execute` listener on the engine, and reset the counter in a function-scoped fixture [28].

### M4. Server statistics for a whole run (PostgreSQL)

```sql
SELECT pg_stat_reset();  -- in each test database (each test_NAME_gwN), before a run on a reused database
-- after the run, from a new session:
SELECT relname, n_tup_ins, n_live_tup FROM pg_stat_user_tables ORDER BY n_tup_ins DESC LIMIT 20;
SELECT xact_commit, xact_rollback, tup_inserted FROM pg_stat_database WHERE datname = current_database();
```

PostgreSQL counts inserts "regardless of commit/abort", so rolled-back tests show up: locally, `n_tup_ins` matched M3 with `n_live_tup` at 0 [1, 33]. Statistics reach the views only when a backend goes idle, at most once per second [33]. Subtract a one-test run's commits before you compute commits per test. This works with any runner. `pg_stat_statements` needs `shared_preload_libraries`, and before PostgreSQL 17 it fills with Django's uniquely named savepoints, so set `pg_stat_statements.track_utility = off` [33].

### M5. Database creation cost (six short runs)

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label create-db --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND ONE_DB_TEST --reuse-db --create-db -p no:randomly --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label reuse-db --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND ONE_DB_TEST --reuse-db -p no:randomly --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py diff --before CREATE_RUN_DIRS --after REUSE_RUN_DIRS
```

Run each command 3 times, with CI's command minus `-n` and one database test as `ONE_DB_TEST`. The difference of the medians is the creation cost: in a check, 4.4 s against 1.0 s, with the test's own time 3.3 s lower [1]. For the cost without migrations, run `--create-db --no-migrations` without `--reuse-db`, so that pytest-django drops that database afterwards. For Django's runner, run `manage.py test LABEL --timing` with and without `--keepdb` [10].

### M6. Factory cascade estimate (seconds, no database)

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label factory-cascade --timeout 300 --cwd ROOT -- \
    python ${CLAUDE_SKILL_DIR}/scripts/factory_cascade.py --find . --settings TEST_SETTINGS --json-out {RUN_DIR}/factory-cascade.json
```

Run it with the project's Python (`python` above), because it imports factory_boy and the factory modules. It needs no database and runs no tests, but importing project code executes it, so ask first, as for collection. `--find .` reads files as text and imports only modules that import factory and define a `...Factory` class; name the modules instead when an import has side effects. `run_suite.py` shows the verdict UNKNOWN, because the output has no test summary: take the exit code from the manifest and the ranking from `output.log`. Lines read `19  app.factories.CommentFactory  (Account 5, Org 5, Member 3, Tag 3, ...)`, with any flags at the end. The estimate matched real INSERTs for 24 of 28 factories in three checks: Django edge cases, the research's factories, and SQLAlchemy [1]. The script's own tests repeat the Django and SQLAlchemy checks. It cannot see rows that `LazyAttribute` or `LazyFunction` bodies, signals, `save()` overrides, or a custom `_create` make, and it flags post-generation hooks and callable sizes instead of counting them. Record its output as `static` evidence, and confirm the top entries with M3.

### M7. Clone timing and durability comparison (local, disposable server only)

```sql
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'TEMPLATE_DB' AND pid <> pg_backend_pid();
CREATE DATABASE bench_clone TEMPLATE TEMPLATE_DB STRATEGY = WAL_LOG;  -- PostgreSQL 15+; repeat with FILE_COPY
DROP DATABASE bench_clone;
ALTER SYSTEM SET fsync = off;  -- also full_page_writes and synchronous_commit; undo with ALTER SYSTEM RESET ALL
SELECT pg_reload_conf();
```

Take the median of 5 clones per strategy. `FILE_COPY` forces a checkpoint before and after, while `WAL_LOG`, the default since PostgreSQL 15, writes the copy to the write-ahead log [21]. The reload is asynchronous, so check `SHOW fsync` from a new session: the old session still showed `on` [1]. Then time creation (M5), one transactional module, and one rollback module, with the settings on and off.

## Tools

Versions and dates are from PyPI and GitHub, read on 2026-09-30 [34]. "Verified" means it ran in the research benchmark on Python 3.14.0 and pytest 9.1.1 [1].

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| pytest-django | Test database, isolation markers, query assertions | 4.14.0, 2026-08-10; maintained | Verified with Django 6.1.1 and 5.2.17. No class-scoped database fixture; each worker migrates its own database; `available_apps` is experimental [9] |
| Django test runner | `--keepdb`, `--parallel`, `--timing`, `--shuffle` | 6.1.1, 2026-09-02 (5.2.17 long-term support); maintained | Django 6.1 needs PostgreSQL 15 or later; `--parallel` clones the database per process [8] |
| pytest-xdist | Workers and `--dist` modes | 3.8.0, 2025-07-01; maintained | `load` and `worksteal` split classes across workers; `loadscope` and `loadfile` keep them together [17] |
| factory_boy | Model factories | 3.3.3, 2025-02-03; no release since, and a May 2026 status issue has no maintainer reply | Verified on Python 3.14 and Django 6.1.1; extra `save()` after post-generation unless `skip_postgeneration_save` [13] |
| model_bakery | Factories without factory classes | 1.24.1, 2026-09-22; maintained | `prepare()` saves nothing; `_bulk_create=True` still saves foreign-key targets one by one [25] |
| pytest-randomly | Random order and reseeding | 5.0.0, 2026-09-01; maintained | Reseeds `random`, factory_boy, Faker, and model_bakery before each test [35] |
| SQLAlchemy | External-transaction test fixture | 2.1.1, 2026-09-25 (2.0.54); maintained | Verified sync and async; 2.1 needs Python 3.11 or later; asyncio needs `greenlet` [27] |
| pytest-postgresql; testcontainers-python | A server per session and a template clone per test; containers from tests | 9.1.0, 2026-09-04; 4.15.0, 2026-07-24; maintained | pytest-postgresql needs PostgreSQL 14 or later and psycopg 3 [20]. testcontainers has `with_command("-c fsync=off")` and `with_tmpfs_mount()`, but no reuse in core [19] |
| pytest-alembic; django-test-migrations | Dedicated migration tests | 0.13.0, 2026-09-25; 1.7.0, 2026-09-23; maintained | Keep migrations tested when the rest of the suite skips them |
| django-zeal; inline-snapshot-django | N+1 detection; query snapshots | 2.2.4, 2026-08-28; 1.4.0, 2026-02-12; maintained | django-perf-rec 4.31.0 is in maintenance mode [29] |
| nplusone, testing.postgresql, pytest-pgsql, pytest-flask-sqlalchemy, django-testdata | Older helpers | Last releases 2016–2022; abandoned | Use django-zeal, `lazy="raise"`, pytest-postgresql, or Django's own `setUpTestData` copying |

## Evidence

- ev.energy, Django with `--parallel`: the base class `TransactionTestCase` → `TestCase` took the suite from 375 s to 120 s (3.1×); one class stayed, because its code called `connection.close()` [2].
- Django ticket #20483: `available_apps` cut PostgreSQL transaction tests from 55 s to 4.5 s, MySQL from 70 s to 3.6 s, and the full SQLite suite from 560 s to 213 s; each transactional test had inserted about 4,000 content type and permission rows [11].
- Adam Johnson: `setUp` → `setUpTestData` "often" gives "a 3x speedup, or more", "sometimes as much as 10x" (opinion with examples) [4]. Discourse, Rails: per-group creation (`fab!`) was about 10% faster at first; a suite-wide pre-built data set was abandoned, because "a significant number of the tests assume they are starting with a blank slate" [16].
- Shopify, Rails: preparation including migrations took about 37% of CI time, and 68% of CI time passed before tests ran; the preparation job fell from 5 to about 3 minutes [5]. Zulip, Django: a template database rebuilt only when a hash of migrations, `uv.lock`, and selected settings changes, cloned per process; the documentation says the backend suite "can finish in under 30s on a fast machine" [18].
- GitLab, Rails: FactoryProf found a factory that created 208 projects in 9.5 s, about a third of them referenced [14]. Evil Martians, Rails: one `create(:comment)` created 10 records; factories took 85% of time in one example; PowerHRG went from 50 to 12 minutes [3].
- OpenHEXA, Django: CI-only durability flags and tmpfs took the suite from about 180 s to 123–150 s [6]. pythonspeed: `fsync=off` took 10,000 autocommit INSERTs from 1.8 s to 1.294 s [31]. Nikitochkin, Rails: a tmpfs data directory took a suite from about 60 to 10 minutes on unusually slow container storage [32].
- Carbon Health, Scala with 400+ tables: cleaning only written tables replaced 150–200 ms of cleanup per test and cut CI time by about 30% [12]. Lob: `DELETE` instead of `TRUNCATE` took 20–200 ms per test down to 1–3 ms; unverified, from a search snippet [36].
- pgtestdb: "~10ms to clone a template", and about 500 ms to prepare a template of about 1,000 migrations [23]. IntegreSQL: 11 ms average and 445 ms maximum per ready database in a 50-test suite [24]. Mergify, SQLAlchemy: stranded connections to a template caused 20-minute CI timeouts until the setup terminated them before cloning [22].

## Sources

1. Benchmarks and checks for this skill's research and for this page, 2026-09-30 and 2026-10-01: Apple M4 Max, macOS, PostgreSQL 16.2 and 14.18 on localhost, SQLite for the shipped scripts' tests, Python 3.14.0, Django 6.1.1, pytest 9.1.1, pytest-django 4.14.0, pytest-xdist 3.8.0, factory_boy 3.3.3, SQLAlchemy 2.1.1, on a shared machine; medians or minimums of 3–5 runs. No public URL.
2. https://adamj.eu/tech/2019/07/15/djangos-test-case-classes-and-a-three-times-speed-up/ – ev.energy case study: one base class changed, 375 s → 120 s.
3. https://evilmartians.com/chronicles/testprof-2-factory-therapy-for-your-ruby-tests-rspec-minitest and https://evilmartians.com/chronicles/testprof-a-good-doctor-for-slow-ruby-tests – factory cascades and TestProf case studies (Ruby).
4. https://adamj.eu/tech/2021/04/12/how-to-convert-a-testcase-from-setup-to-setuptestdata/ and https://2021.djangocon.eu/cfp/talk/NS9S7N/index.html – converting `setUp` to `setUpTestData`; "as much as 10x".
5. https://shopify.engineering/faster-shopify-ci – Shopify CI: migration caching by hash, preparation share of CI time.
6. https://github.com/BLSQ/openhexa-app/pull/2050 – OpenHEXA (Django): CI-only durability flags and tmpfs, about 30%.
7. https://docs.djangoproject.com/en/dev/topics/testing/tools/ – Django testing tools: `TestCase`, `TransactionTestCase`, `setUpTestData`, fixtures, `captureOnCommitCallbacks`, `SimpleTestCase`.
8. https://github.com/django/django/blob/main/django/test/testcases.py, https://github.com/django/django/blob/main/django/db/backends/postgresql/operations.py, and https://github.com/django/django/blob/main/django/db/backends/postgresql/creation.py – Django source: flush and `post_migrate`, `available_apps`, connection closing, `TestData` deep copy, one `TRUNCATE` on PostgreSQL, clones for `--parallel`.
9. https://pytest-django.readthedocs.io/en/latest/database.html, https://pytest-django.readthedocs.io/en/latest/helpers.html, and https://github.com/pytest-dev/pytest-django/blob/main/pytest_django/fixtures.py – pytest-django database access, flags, `django_db` parameters, fixtures, worker suffixes, and the `django_db_blocker` warning.
10. https://docs.djangoproject.com/en/dev/topics/testing/overview/, https://docs.djangoproject.com/en/dev/ref/django-admin/, https://docs.djangoproject.com/en/dev/ref/settings/, https://docs.djangoproject.com/en/dev/topics/migrations/, and https://docs.djangoproject.com/en/dev/faq/models/ – Django docs: the test database, `--keepdb`, `serialized_rollback` "approximately 3x", `test` options, `DATABASES['TEST']`, squashing, and `connection.queries` needing `DEBUG=True`.
11. https://code.djangoproject.com/ticket/20483 – `available_apps` ticket, with before-and-after timings.
12. https://carbonhealth.com/blog-post/cleaning-postgresql-db-between-integration-tests-efficiently – Carbon Health: clean only written tables, about 30% less CI time.
13. https://factoryboy.readthedocs.io/en/stable/reference.html, https://factoryboy.readthedocs.io/en/stable/orms.html, https://factoryboy.readthedocs.io/en/stable/changelog.html, and https://github.com/FactoryBoy/factory_boy/issues/1153 – factory_boy strategies, `SubFactory`, `RelatedFactory`, `django_get_or_create`, `skip_postgeneration_save`, `mute_signals`, and the May 2026 project-status issue.
14. https://docs.gitlab.com/development/testing_guide/best_practices/ – GitLab test speed guide: `let_it_be`, `create_default`, a FactoryProf example.
15. https://github.com/test-prof/test-prof/blob/master/docs/profilers/factory_prof.md, https://github.com/test-prof/test-prof/blob/master/docs/recipes/factory_default.md, and https://github.com/test-prof/test-prof/blob/master/docs/playbook.md – TestProf FactoryProf, FactoryDefault, and playbook (Ruby).
16. https://github.com/discourse/discourse/pull/7414 – Discourse `fab!` and the abandoned suite-wide data set.
17. https://pytest-xdist.readthedocs.io/en/stable/distribution.html – pytest-xdist `--dist` modes.
18. https://zulip.readthedocs.io/en/latest/testing/testing-with-django.html and https://github.com/zulip/zulip/blob/main/zerver/lib/test_fixtures.py – Zulip's hash-keyed template database.
19. https://github.com/testcontainers/testcontainers-python/blob/main/src/testcontainers/core/container.py and https://java.testcontainers.org/features/reuse/ – testcontainers-python core (tmpfs, no reuse), and reusable containers in Testcontainers for Java.
20. https://github.com/dbfixtures/pytest-postgresql – pytest-postgresql: a server per session, a template database cloned per test.
21. https://www.postgresql.org/docs/current/non-durability.html and https://www.postgresql.org/docs/current/sql-createdatabase.html – PostgreSQL non-durable settings; `CREATE DATABASE` with `TEMPLATE` and `STRATEGY`, and no other sessions on the template.
22. https://mergify.com/blog/postgres-database-per-test-sqlalchemy – per-test clones with SQLAlchemy, and the stranded-connection incident.
23. https://github.com/peterldowns/pgtestdb – Go library: a template per migration hash, a clone per test, with timings.
24. https://github.com/allaboutapps/integresql – IntegreSQL: pools of template clones, with a benchmark.
25. https://model-bakery.readthedocs.io/en/latest/basic_usage.html – model_bakery `make`, `prepare`, `_bulk_create`, `_save_related`.
26. https://www.sqlite.org/quirks.html and https://docs.djangoproject.com/en/dev/ref/databases/ – SQLite quirks, and Django's notes on SQLite.
27. https://docs.sqlalchemy.org/en/21/orm/session_transaction.html, https://docs.sqlalchemy.org/en/20/orm/session_api.html, and https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html – joining a session into an external transaction, `join_transaction_mode`, and `AsyncSession`.
28. https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html and https://docs.sqlalchemy.org/en/20/core/events.html – SQLAlchemy raise loading and cursor events.
29. https://github.com/taobojlen/django-zeal and https://github.com/adamchainz/django-perf-rec – django-zeal N+1 detection; django-perf-rec, in maintenance mode, points to inline-snapshot-django.
30. https://dev.mysql.com/doc/refman/8.4/en/mysql-acid.html and https://dev.mysql.com/doc/refman/8.4/en/binary-log.html – MySQL durability settings, and the binary log default.
31. https://pythonspeed.com/articles/faster-db-tests/ – `fsync` off on 10,000 autocommit INSERTs: 28%.
32. https://dev.to/miry/speeding-up-postgresql-in-containers-1eeg – a Rails suite from 60 to 10 minutes with tmpfs.
33. https://www.postgresql.org/docs/current/monitoring-stats.html, https://github.com/postgres/postgres/blob/master/src/backend/utils/activity/pgstat_relation.c, https://www.postgresql.org/docs/current/pgstatstatements.html, and https://www.postgresql.org/docs/17/release-17.html – statistics views and their delay, inserts counted "regardless of commit/abort", `pg_stat_statements`, and savepoint names normalised in PostgreSQL 17.
34. https://pypi.org/pypi/{package}/json – PyPI JSON API for versions, dates, and classifiers (read 2026-09-30).
35. https://github.com/pytest-dev/pytest-randomly – pytest-randomly: random order, and reseeding before each test.
36. https://lob.com/blog/truncate-vs-delete-efficiently-clearing-data-from-a-postgres-table – `TRUNCATE` against `DELETE` in a test suite (figures from a search snippet; the page was not retrieved).
