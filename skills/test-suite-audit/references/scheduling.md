# Scheduling: parallelism, sharding, selection, and tiering

This page covers where, when, and in what order tests run: pytest-xdist workers on the runner's central processing units (CPUs), shards across continuous integration (CI) machines, test selection, tiers, merge queues, fail-fast ordering, and CI setup cost. It also gives the cost model that predicts a saving before any change, and the sampling workflow for a suite too slow to run in full. Load it in phase 7 when workers are imbalanced, shards are uneven, or CI runs too much, and in phase 6 when a full baseline does not fit the budget. When the project already parallelises, shards, or selects, judge how well that works instead of recommending it again (guardrail 12). Each of these practices has a fixed cost that can exceed its saving, so price a recommendation before you make it. Every recipe that runs tests needs the user's agreement from phase 1 and goes through `run_suite.py`; take timings only from uninstrumented runs, and compare medians of 3 runs.

## Quick reference

Thresholds are the research's heuristics unless a source is cited. `[toy]` marks a check on a toy suite or benchmark, run on Apple silicon under a load average of 4–16, with pytest 9.1.1, pytest-xdist 3.8.0, pytest-split 0.11.0, pytest-testmon 2.2.0, pytest-impacted 0.34.0, coverage 7.16.2, and CPython 3.14.0. The installer benchmark, the noise figures, the `worksteal` comparison, and the tach and pytest-impacted counts come from the research's own runs; the rest were checked again for this page, mostly through the skill's scripts.

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Serial suite on a multi-CPU runner | No `-n` in the CI command or `addopts`; the runner's CPU budget | Serial test phase over about 2 min, with 4+ usable CPUs | pytest-xdist, after per-worker resources | 3× on 32 cores [1]; little under 10 s of serial time [2] |
| A deselected tier never runs | Each `-m` expression in CI against registered markers; default-branch jobs | Any tier that no default-branch job runs; trust breaker | Full run in the merge queue or nightly, with alerts | Restores checks that stopped running |
| Selection in place but missing tests | Python version and `COVERAGE_CORE`; `no-sysmon-context` in CI logs; no full run | Any of these | `COVERAGE_CORE=ctrace`, fail-safe rules, a full backstop run | testmon ran 1 of 25 affected tests on the default core [toy] |
| Worker count does not match the CPU budget | xdist header `created: N/N workers` against the quota | Over 125% or under 50% of usable CPUs | `PYTEST_XDIST_AUTO_NUM_WORKERS` or `-n` from the quota | No published figure; sweep |
| Long tail: workers finish unevenly | `results.py summary` worker line; span and floor from its JSON | Test-phase efficiency under 70%, or one test longer than total ÷ workers | Longest-first ordering; split the longest tests | Span −22% [toy]; at most span − floor |
| Per-worker setup caps the gain | `results.py fixtures`: session fixtures paid once per worker | Per-worker fixed cost over 20% of per-worker test time | Share setup across workers; fewer workers | 3×, not 32×, on 32 cores [1] |
| Distribution mode fights fixtures | `--dist`, `xdist_group`, per-file time, fixture setup counts | One scope over total ÷ workers, or a costly module fixture on most workers | `load` with cheap or shared fixtures; small groups | `loadfile` 2.2× slower than `load` [toy] |
| CI setup dominates the test job | Step times from the CI's application programming interface (API) | Setup over 30% of the job or over 3 min | Lock file, fast installer, warm cache, prebuilt image | Warm install: pip 31.9 s, uv 0.4 s [toy] |
| Shards unbalanced or on stale durations | Per-shard test time; tests missing from `.test_durations` | Slowest ÷ mean shard over 1.2, or over 10% of tests without durations | `least_duration`, durations refreshed from the default branch | 10 → 4 min in a vendor example [3] |
| Shard count ignores fixed cost | Per-shard fixed cost F and test work W from CI step times | F over 40% of a shard's wall time, or W ÷ N under 2 × F | Cut F; bigger runners with xdist instead of more shards | Speed-up capped at (F + W) ÷ F |
| Runs that should not happen | Duplicate `push` and `pull_request` runs; no `cancel-in-progress` | Over 10% of runner minutes | Concurrency groups; `push` on the default branch only | No published figure |
| Failures surface late | First-failure position in failed runs; no `--ff`; cold `.pytest_cache` | Most failed runs fail in their last half | Recently failed first; a small fail-fast job | Machine learning needed about 60 cycles to match a simple sort [4] |
| Large suite runs everything on every change | Suite length, changed files per pull request, shadow-mode estimate | Suite over 15 min, and median selected share under 50% | File-level selection with fail-safes and a backstop | −19% to −32% end to end on average [5][6] |

### Changes that cost more than they save

| Change | When it loses | Evidence |
| --- | --- | --- |
| xdist on a small suite | Under about 10 s of serial test time | 981 tests: 3.4 → 2.8 s [2] |
| More workers when setup dominates | Per-worker imports and session setup do not parallelise | 3× on 32 cores [1]; one report: start-up grew from 3 min 25 s at 1 worker to 57 min 39 s at 8 [7] |
| `loadscope` or `loadfile` for fixture reuse | Slow tests sit in one file or class | 2.2× slower than `load` [toy] |
| Selection on a short suite | Full run under about a minute | STARTS slower than running everything in 6 of 21 such projects [6] |
| Method-level selection | Compared with file or class level | Slower end to end, and less safe [5][6] |
| Machine-learning prioritisation without history | The first weeks | About 60 CI cycles to match "recently failed first" [4] |
| More shards when F is large | W ÷ N falls below about 2 × F | Each minute saved costs F × N² ÷ W runner-minutes (model) |

## Signals

### Serial suite on a multi-CPU runner

**Detect:** Look for `-n` or `--numprocesses` in `addopts` and the CI command, and for pytest-xdist in the lock file: `grep -rnE -- '(-n|--numprocesses)[ =]?(auto|logical|[0-9]+)' pytest.ini pyproject.toml tox.ini setup.cfg noxfile.py Makefile .github .gitlab-ci.yml .circleci 2>/dev/null`. Check the runner's CPU budget, not the host's: GitHub's standard Linux runner has 2 virtual CPUs (vCPUs) for private repositories and 4 for public ones [8]. In a Linux container, `/sys/fs/cgroup/cpu.max` reads `max 100000` without a quota and `200000 100000` for 2 CPUs. The serial test phase is `sum of test time` from `results.py summary` on CI's JUnit files or on the baseline.

**False positives:** The tests wait on one external service that cannot be multiplied, or memory runs out first, because each worker is a full Python process with its own imports and fixtures. On sharded 2-vCPU machines, the two vCPUs may be hyperthreads of one core, so `-n 2` gains little (unverified for GitHub). Failures that appear only under `-n` come from shared state, such as fixed ports, one database name, or fixed paths; fix those first ([flakiness.md](flakiness.md)).

**Fix:**
1. Give each worker its own resources: names from the `worker_id` or `testrun_uid` fixtures or `PYTEST_XDIST_WORKER`, port 0, and `tmp_path_factory` [9]. See [database-and-data.md](database-and-data.md). Also make collection deterministic: xdist aborts with "Different tests were collected between gw0 and gw1", for example when `parametrize` iterates over a set [9].
2. Put `-n` in the CI command, not `addopts`, because under xdist `-s` cannot stream output and `--pdb` forces `-n 0` [9]. A command-line `-n` overrides the one in `addopts` [toy].

**Effect:** PyPI went from 191 s to 63 s on 32 cores: 3×, because per-worker database setup and start-up do not parallelise [1]. pandas went from 182 s to 61 s with `-n 8` (vendor benchmark, single runs) [2].

**Verify:** Run three times each at `-n 0` and `-n N` on the CI runner type. `results.py diff` must show the same tests and outcomes and a lower median. Then pass two runs in random order, because xdist changes order and co-location.

### A deselected tier never runs

**Detect:** Compare every `-m` expression in CI files, `tox.ini`, `noxfile.py`, and Makefiles with the configured `markers`. A typo selects all or nothing: `-m "not slwo"` ran every test, and `-m "slwo"` ran none, with exit code 5 [toy]. Look for `|| true` or other handling of exit code 5. Without `strict_markers`, a mistyped marker puts a slow test in the fast tier with only a warning; pytest 9.0.0–9.0.3 silently ignored `--strict-markers` in `addopts`, and 9.1.0 fixed it [10]. For each excluded tier, find the default-branch job that runs it (a schedule, the merge queue, or post-merge) and how its failures reach a person. For tests that no CI job selects, see [redundancy.md](redundancy.md).

**False positives:** A small, fast suite needs no tiers, because each tier is another place for failures to hide. A nightly tier with alerts works as designed.

**Fix:**
1. Register every marker and set `strict_markers = true`. pytest 9's `strict = true` also turns on `strict_xfail` and `strict_parametrization_ids` [toy], so passing non-strict xfails start to fail.
2. Run the full suite in the merge queue (`on: merge_group` [11]), or post-merge and nightly, with loud failures; a nightly run that fails silently equals deselection. GitLab runs a predictive subset before approval, and everything after approval and on CI-configuration changes [12].
3. Fail a tier job that unexpectedly collects zero tests, and check in CI that every `-m` name is registered. Tier by measured duration, not by folder, and check a slow test's failure history before you recommend `demote` ([ci-history.md](ci-history.md)).

**Effect:** It has no time effect; it restores checks that stopped running. A marker that every CI job excludes, with no scheduled job, is a trust breaker ([findings.md](findings.md)).

**Verify:** Collect each tier through `run_suite.py` (recipe "Tier and shard unions"). Complementary tiers add up to `nodeids.txt` without overlap, and the default branch runs every tier at least daily.

### Selection in place but missing tests

**Detect:**
- pytest-testmon on Python 3.14+. coverage.py defaults to its `sysmon` core there, which does not support the per-test contexts testmon records [13]. After a change to a function that 25 tests call, testmon 2.2.0 selected 1 of them on the default core, and all 25 with `COVERAGE_CORE=ctrace` [toy]. Grep CI logs for `no-sysmon-context`. A baseline with CI's `--testmon` command measures only the selected tests, under coverage, so drop `--testmon` (or override `addopts`) for the baseline. Wherever testmon runs through `run_suite.py`, pass `--env TESTMON_DATAFILE={RUN_DIR}/.testmondata`, so the project's own data file stays untouched.
- No full backstop run. Every production system reviewed keeps one: Meta runs all tests every few hours [14], Microsoft recommends periodic full runs [15], Develocity runs the rest in a later stage [16], and GitLab runs everything after approval [12].
- No fail-safe for changes the selector cannot see: templates, SQL, JSON fixtures, migrations, lock files, settings, CI configuration, `conftest.py`, and dynamic imports (`grep -rnE "import_module\(|__import__\(|entry_points\(|pytest_plugins" SRC TEST_ROOTS`). Microsoft runs all tests for any file type it cannot reason about [15]; testmon ignores static files and external services [17]. A selector error must not read as "nothing affected": pytest-impacted fails open without git, but its command-line tool exits 1 [18]. Watch for dependency data written by pull request (PR) runs, too: GitHub scopes those caches to the PR, so other PRs and the base branch cannot restore them [19].

**False positives:** A missed failure of a flaky test is not a selection miss, so classify misses first ([flakiness.md](flakiness.md)). Flaky failures also distort the miss rate [14].

**Fix:**
1. Restore the full backstop run and its alerts, and run everything on the file types above and on any selector error.
2. On Python 3.14+, set `COVERAGE_CORE=ctrace`, or `[run] core = ctrace`, in every job that writes `.testmondata`. A `sysmon` speed-up for coverage, such as PyPI's 58 s → 27 s [1], silently breaks testmon in the same repository.
3. Build dependency data and `.test_durations` on the default branch, and restore them read-only in PRs. Never cache secrets, because anyone who can open a PR can read base-branch caches [19]. Track the miss rate: default-branch failures that PR selection did not run.

**Effect:** The core fix restored all 25 affected tests [toy]. Meta held its selector to over 95% of individual failures and over 99.9% of faulty changes [14].

**Verify:** In a local clone outside the project, build the dependency data with CI's settings, change one function that many tests call, and count what the selector picks through `run_suite.py run --cwd CLONE`. The count must equal the number of tests that call the function; for testmon on Python 3.14+, run it with and without `COVERAGE_CORE=ctrace`. Do not add `-p no:cacheprovider`, which crashes testmon 2.2.0 (`KeyError: 'lf'`); `run_suite.py` already redirects the cache. `run_suite.py` records `--testmon` runs as `instrumented: coverage` [toy], so their timings cannot back a speed claim. Then track the miss rate for a month.

### Worker count does not match the CPU budget

**Detect:** Read the xdist header: `created: 4/4 workers` and `4 workers [418 items]`; with `-q`, only `bringing up nodes...` appears [toy]. pytest-xdist 3.8.0 resolves `-n auto` from `PYTEST_XDIST_AUTO_NUM_WORKERS` first. Next come psutil's physical cores, if psutil is installed (logical cores for `-n logical`), and otherwise the affinity mask or `os.cpu_count()` [9]. None of these, nor `os.process_cpu_count()`, reads control group (cgroup) quotas [20], so a 2-CPU container on a 64-core host starts 64 workers. xdist's unreleased main branch adds `PYTHON_CPU_COUNT` support and `--ramp`, which 3.8.0 lacks [9].

**False positives:** Suites that wait on input and output can gain from more workers than CPUs. A self-hosted runner that runs several jobs at once gives each job only a share.

**Fix:** Set the count from the job's budget. For cgroup version 2:

```sh
read q p < /sys/fs/cgroup/cpu.max
if [ "$q" = max ]; then n=$(nproc); else n=$(( (q + p - 1) / p )); fi
export PYTEST_XDIST_AUTO_NUM_WORKERS=$n
```

Or pass `-n "$n"`, or implement the `pytest_xdist_auto_num_workers(config)` hook [9]. `nproc` is right only for a cpuset limit, and `--maxprocesses=N` caps `auto` on large developer machines [9]. When memory is the limit, divide the available memory by the peak per worker.

**Effect:** No published pytest measurement of oversubscription exists, so measure it.

**Verify:** Sweep `-n` over 1, 2, 4, and 8 with 3 runs each through `run_suite.py`, and compare medians with `run_suite.py list`; a command-line `-n` overrides the command's own. The chosen count sits at or near the knee, past which workers add setup and memory without speed. Sweep on the CI runner type, and on a long suite sweep a file sample and say so.

### Long tail: workers finish unevenly

**Detect:** `results.py summary` on a `--timing-plugin` run prints, for example, `workers: 4 seen, busiest/mean busy time 2.42, last worker finished 12.1s after the first` [toy]. Its JSON holds each worker's busy seconds under `workers_seen`. The recipe "Worker balance from a baseline run" adds the test-phase span, the floor (max(longest test, total ÷ workers)), and the most that rebalancing can save. `results.py` reads the worker from the plugin's `timing.jsonl` or from a pytest-reportlog file's `worker_id`, so a report log harvested from CI shows the line too [toy]. JUnit XML has no workers or start times.

**False positives:** On a busy machine, identical runs vary. A toy suite spanned 5.3–6.7 s, and one single `worksteal` run looked 60% slower than `load` from noise alone [toy]. Compare medians of 3 runs.

**Fix:**
1. Start the longest tests first. xdist's `load` hands out tests in collection order [9], so a slow test collected last runs alone at the end. Sort by pytest-split's `.test_durations` in a deterministic `conftest.py` hook, because every worker runs it and must get the same order; unknown tests get the median:

   ```python
   import json, pathlib

   def pytest_collection_modifyitems(session, config, items):
       path = pathlib.Path(config.rootpath, ".test_durations")
       if not path.exists():
           return
       durations = json.loads(path.read_text())
       known = sorted(durations.values())
       default = known[len(known) // 2] if known else 0.0
       items.sort(key=lambda item: (-durations.get(item.nodeid, default), item.nodeid))
   ```

   The sort breaks module grouping, so module- and class-scoped fixtures may run more often. It also conflicts with random-order plugins and with `duration_based_chunks`. The plugins pytest-slow-first and pytest-slowest-first did this, but are unmaintained. Also split any test longer than total ÷ workers, because no scheduler can beat that floor.
2. Try `--dist worksteal` (xdist 3.2.0+) when durations vary unpredictably [9]; it matched `load` within noise in toy suites [toy]. `--maxschedchunk 1` sends tests one at a time, which trades fixture reuse for balance.

**Effect:** The saving is at most span − floor. With one 6 s test collected last behind 400 fast tests on 4 workers, the hook cut the median test-phase span from 8.8 s to 6.9 s (−22%), against a 6 s floor [toy]. Median wall time moved only from 10.2 s to 9.9 s, because start-up varied by over a second on the loaded machine [toy].

**Verify:** `results.py diff` over 3 runs each shows the same tests and outcomes and a lower median. The finish spread shrinks, and `results.py fixtures` shows no large rise in module fixture setups.

### Per-worker setup caps the parallel gain

**Detect:** Session fixtures run once per xdist worker [9]. On a timing-plugin run, `results.py fixtures` names "session fixtures paid once per worker, 2 s or more each". From one run, compare the manifest's `startup_gap_seconds`, collection time (each worker collects everything), the largest setup (`slowest setup` in `results.py summary`), and the test-phase span. Report when per-worker fixed cost exceeds 20% of per-worker test time, or when doubling `-n` gains under 15%.

**False positives:** A large first setup can belong to a fixture that only one module uses, so check its scope. A service started once outside pytest does not grow with workers.

**Fix:**
1. Build expensive session setup once: a file lock on `tmp_path_factory.getbasetemp().parent`, as the xdist docs show [9], or a CI step that builds a template database for each worker to clone ([database-and-data.md](database-and-data.md)).
2. Cut import and collection cost ([fixed-costs.md](fixed-costs.md)); PyPI cut collection from 7.84 s to 2.60 s with `testpaths` [1]. Or use fewer workers, and find the knee with the worker model in "Estimating a saving before the change".

**Effect:** PyPI paid about 1 s of migrations per worker and gained 3× on 32 cores. It declined to squash 400+ migrations for another 13% [1].

**Verify:** Session setups per run equal the worker count or fewer, and `results.py diff` shows the same tests and outcomes with a lower median.

### Distribution mode fights the fixture structure

**Detect:** `--dist loadscope` or `loadfile` sends a whole module or class to one worker, and `loadgroup` does so for each `xdist_group` [9]. One heavy scope then becomes a single-worker tail. Take per-file time from `files` in `results.py summary --top 50 --json-out FILE`. Under `--dist load`, every worker that gets a test from a module repeats that module's fixtures; count setups with `results.py fixtures`.

**False positives:** `loadscope` or `loadgroup` can be a correctness requirement, such as a class whose tests share state, or a group that needs one external resource. Fix those tests before you change the mode.

**Fix:** Prefer `load` or `worksteal` with cheap or shared module fixtures, such as a locked session fixture or a template database, over pinning modules to workers. Keep `xdist_group` groups small, and split huge modules or classes that must stay together. Decide with numbers: duplicated setup under `load` (setups × mean setup) against idle time under `loadscope` (span − floor). For the reverse case, see [runners-and-ecosystems.md](runners-and-ecosystems.md). Since xdist 3.5.0, `loadscope` sorts scopes by test count, and `--no-loadscope-reorder` (3.8.0) keeps the original order [9].

**Effect:** With 8 slow tests in one file, 4 workers, and a 1 s session fixture, `loadfile` took 16.5 s and `load` 7.5 s. `loadfile` had an efficiency of 0.37 and a 12.1 s finish spread [toy].

**Verify:** Compare per-file time and fixture setup counts before and after, and run `results.py diff` over 3 runs each.

### CI setup dominates the test job

**Detect:** Take per-step times over 10–20 green runs from the CI's API, with the recipe "Setup and test time per CI job". Setup share = (job time − test step time) ÷ job time. Configuration smells: installs without a cache or lock file, `docker build` without `cache-from`, a fixed `sleep` after `docker compose up`, downloads on every run, and installation repeated in every shard.

**False positives:** A cache restore can cost as much as it saves. uv's docs say that re-downloading pre-built wheels is often faster in CI, and recommend `uv cache prune --ci` [21].

**Fix:**
1. Use a lock file and a fast installer with a warm cache: setup-uv's `enable-cache: true` keyed on the lock file [21], a virtual environment cached on the lock file's hash, or a CI image rebuilt when the lock file changes. Install once per pipeline, so that each shard only restores the environment, and start services with health checks during installation (`docker compose up --wait`) instead of fixed sleeps.
2. uv skips bytecode compilation by default, so the first import pays for it. A Django service stack imported in 6.9 s without `.pyc` files and in 1.1–2.2 s with them, and every xdist worker imports at once [toy]. Set `UV_COMPILE_BYTECODE=1` for cached environments and images, and compare whole-job time.

**Effect:** With 53 packages, a warm cache, and a fresh virtual environment (median of 3), pip took 31.9 s, Poetry 6.6 s, and uv 0.4 s; uv in copy link mode took 18.1 s [toy]. Multiply the saving by shards and runs per day.

**Verify:** Compare per-step medians over 10 runs before and after, the cache hit rate, and total job time.

### Shards unbalanced or balanced on stale durations

**Detect:** Find the mechanism: `grep -rnE -- '--splits|--group|--shard-id|--num-shards|circleci tests (split|run)|parallelism:|CI_NODE_(INDEX|TOTAL)|BUILDKITE_PARALLEL_JOB' .github .circleci .gitlab-ci.yml .buildkite 2>/dev/null`. Count- or hash-based splits ignore durations: pytest-shard (last release 2020) [22], CircleCI's default split by name [23], and Buildkite's alphabetical fallback when its service is unavailable [3]. CircleCI timing splits need `-o junit_family=xunit1`, because the default `xunit2` omits the `file` attribute and the split falls back silently [23]. Per-shard test time comes from `results.py summary` on each shard's JUnit file, over 10–20 runs; imbalance = slowest ÷ mean. For pytest-split, count tests missing from `.test_durations` (recipe "Duration-file staleness and shard preview"). Unknown tests get the average known duration, and with no match it splits by count [24]. Its per-group estimate needs only collection: `[pytest-split] Running group 1/4 (estimated duration: 6.66s)` [toy].

**False positives:** Setup variance, such as a cold cache or a slow image pull, also spreads shards, so separate setup from test time. pytest-split's durations include setup and teardown [24], so a module split across two shards pays its fixture twice.

**Fix:**
1. Split with `--splitting-algorithm least_duration`, a greedy longest-first assignment [24]. The default, `duration_based_chunks`, keeps collection order: better fixture locality, worse balance, and broken under random order unless all shards share a seed [24]. In the toy suite, `least_duration` estimated 6.66–6.68 s per group, and `duration_based_chunks` 4.55–7.86 s [toy].
2. Refresh durations from the default branch with `pytest --store-durations --durations-path .test_durations`, which works under `-n`; `--clean-durations` drops deleted tests [24]. Shards record only their own tests, so merge the files: `jq -s add shard-*/.test_durations > .test_durations`. GitHub evicts caches unused for 7 days [19]. Write a path outside the project as `--durations-path=PATH`: with a space, pytest 9.1.1 treated the existing file as a path argument and moved the rootdir, so no node ID matched and pytest-split split by count without an error [toy].
3. Dynamic splitting adapts at run time: Buildkite Test Engine supports pytest [3], and Knapsack Pro has no official Python client [25]. Run xdist inside each shard as well.

**Effect:** In Buildkite's illustration, 16 minutes of tests on 4 shards took 10 minutes split by count and about 4 split by timing (vendor) [3].

**Verify:** Over the next 10 runs, slowest ÷ mean falls towards 1.0–1.1. The shard union equals the full collection, with no test in two shards (recipe "Tier and shard unions").

### Shard count ignores per-shard fixed cost

**Detect:** From CI step times, F is a shard's queue time plus setup (checkout, install, services, collection), and W is the test time summed over shards. Wall time ≈ F + W ÷ N plus the tail, and the bill ≈ N × F + W runner-minutes. GitHub rounds each job up to a whole minute [26].

**False positives:** Waiting developers and merge-queue throughput often matter more than the bill. Queue time on a busy runner pool can make more shards slower than the model says.

**Fix:** Cut F first (see "CI setup dominates the test job"). When F is large, prefer bigger runners with xdist over more small shards. GitHub's Linux x64 price is nearly flat per core-minute, from $0.006 per minute for 2 cores to $0.082 for 32 [26], and one 16-core job pays F once instead of eight times. Present the wall-time-optimal N and the cost-optimal N with the waiting time, and let the team choose.

**Effect:** The speed-up cannot exceed (F + W) ÷ F: Amdahl's law with F as the serial part. Each minute saved costs F × N² ÷ W runner-minutes. With assumed W = 60 and F = 3 minutes, N = 4 gives 18 minutes for 72 runner-minutes, N = 12 gives 8 for 96, and N = 30 gives 5 for 150. The price passes 10 runner-minutes per minute saved near N = 14.

**Verify:** Compare median pipeline wall time and billed minutes over 20 runs, before and after.

### Runs that should not happen

**Detect:** `push` and `pull_request` triggers on all branches run each PR commit twice. This shows them as `pull_request,push` lines: `gh run list -L 200 --json headSha,event,workflowName -q 'group_by(.headSha + .workflowName)[] | select(length>1) | "\(length) \(.[0].workflowName) \(map(.event) | unique | join(","))"'`. Also look for PR workflows without a `concurrency` group that has `cancel-in-progress: true` [11], the full suite on documentation-only changes, and the full version matrix on every push.

**False positives:** Workflow-level `paths` filters leave required checks pending and block merges, while a job skipped with `if:` reports success. Path filters also see only the first 3,000 changed files [11]. Cancelling runs on the default branch loses the post-merge signal.

**Fix:** Give PR workflows a `concurrency` block with `group: ${{ github.workflow }}-${{ github.head_ref || github.run_id }}` and `cancel-in-progress: true`; the group falls back to the run ID for other events [11]. Trigger `push` only on the default branch, skip heavy jobs for documentation-only diffs with a job-level `if:`, and move the full version matrix to the merge queue or nightly.

**Effect:** No published figure exists.

**Verify:** Compare runner minutes per merged PR over two weeks, before and after.

### Failures surface late

**Detect:** In failed CI runs, find the position of the first failure in execution order, from timing-plugin start times. If most failed runs fail in their last half, ordering costs feedback time. PR jobs without `--ff` and a restored per-PR `.pytest_cache` reach the failed test last on a rerun [10]. GitHub's matrix `fail-fast` defaults to `true` and cancels the other jobs at the first failure [11].

**False positives:** Reordering can hide order dependence ([flakiness.md](flakiness.md)), and it breaks `duration_based_chunks`. `-x` or `--maxfail` on the reporting job hides later failures and costs extra fix-and-push cycles.

**Fix:**
1. Run recently failed tests first. With `--ff` [10], the header shows `run-last-failure: rerun previous N failures first` [toy]. testmon's `--testmon-noselect` reorders by likelihood of failure without deselecting [17]. Leave machine learning for later: a reinforcement-learning prioritiser needed about 60 CI cycles to match a sort by recent verdicts [4].
2. Add a small job beside the full suite that runs the tests most related to the change and cancels the pipeline on failure. GitLab's version becomes a no-op above 10 related test files, so it never outlasts the full job [12]. Keep `-x` for local loops and that early job, and set `fail-fast: false` on a matrix to keep the full failure list and every shard's uploads.

**Effect:** For most breakages, time to the first failure falls to about the early job's duration. No published Python measurement exists.

**Verify:** Compare the median time to the first failure on failed runs, before and after ([ci-history.md](ci-history.md)). Green runs still finish the full job.

### Large suite runs everything on every change

**Detect:** The PR job runs the full suite, which takes over about 15 minutes, while typical PRs touch little code: `gh pr list --state merged -L 100 --json files -q '.[].files | length'` gives the changed files per PR. Estimate the prize with the recipe "Shadow-mode estimate for selection" before you name a tool.

**False positives:** Code that every test touches, such as models, settings, `conftest.py`, or a base class, makes most changes affect everything; the shadow estimate shows this. Monorepos on Pants or Bazel may already skip unaffected targets through their test cache [27].

**Fix:** Selection is a trade-off, not a fix (guardrail 11). A missed failure surfaces later, in the merge queue or nightly run, and costs a revert, so state that loss. Always add the fail-safes and the backstop from "Selection in place but missing tests". In order of safety:
1. File- or module-level static selection from the import graph: pytest-impacted (beta) [18], tach's pytest plugin [28], or a script on grimp. Class-level static selection matched dynamic savings "but at the risk of being unsafe sometimes", and method-level static selection performed poorly [6].
2. Coverage-based selection with pytest-testmon [17]. It is more precise, but needs `ctrace` on Python 3.14+ and fresh default-branch data.
3. Build-system caching, where Pants or Bazel already exists [27]; adopting one only for selection is a large project. Consider commercial selection only where the organisation already pays for the platform. CloudBees Smart Tests (formerly Launchable) subsets to a target such as `--target 20%` [29]. Datadog Test Impact Analysis skips tests whose covered and tracked files are unchanged since a pass, with documented gaps under pytest-cov and xdist [30]. Develocity Predictive Test Selection does not support Python [16].

**Effect:** Research tools on Java cut end-to-end time by 19% (STARTS) to 32% (Ekstazi) on average, and Ekstazi by 54% on longer suites [5][6]. Meta halved its testing infrastructure cost [14], and Mozilla ran 70% fewer test tasks than its earlier heuristic [31]. Instawork halved the median time of about 35,000 pytest tests with testmon (unverified) [32].

**Verify:** Use shadow mode first. tach's plugin without `--tach` runs everything and warns when a failing test would have been skipped [28], and CloudBees has `--observation` [29]. Otherwise, a CI job runs the subset, then everything, and compares failures, as Microsoft recommends [15]. Report the miss rate over 2–4 weeks before any test is skipped.

## Measuring

### Worker balance from a baseline run

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label baseline --timeout SECONDS --cwd ROOT --timing-plugin -- \
    CI_TEST_COMMAND --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary AUDIT/runs/NN-baseline --json-out AUDIT/results/baseline-summary.json
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py fixtures AUDIT/runs/NN-baseline
python3 - AUDIT/results/baseline-summary.json <<'EOF'
import json, sys
s = json.load(open(sys.argv[1]))
busy = s["workers_seen"]["busy_seconds"]
tests = [t for t in s["all_tests"] if t.get("start") and t.get("stop")]
span = max(t["stop"] for t in tests) - min(t["start"] for t in tests)
floor = max(s["distribution"]["max"], s["sum_seconds"] / len(busy))
print(f"span {span:.1f}s  floor {floor:.1f}s  max saving {span - floor:.1f}s  test-phase efficiency {s['sum_seconds'] / (len(busy) * span):.0%}")
EOF
```

`summary` prints `efficiency` as sum of test time ÷ (wall × workers), which charges start-up and collection to the workers. The snippet divides by the test-phase span instead, so compare its figure with the 70% threshold. `workers_seen` exists only when the input records 2 or more workers: `timing.jsonl` and pytest-reportlog files do, and JUnit XML does not. For a report log harvested from CI, run `summary` on the `.jsonl` file; on a 4-worker `loadfile` run, the snippet gave a 14.9 s span, a 6.1 s floor, and 41% efficiency [toy]. Cost: the baseline run, plus seconds.

### Setup and test time per CI job

For GitHub Actions, with an authenticated `gh`, save this as `ci_step_times.py` and run it as `python3 ci_step_times.py OWNER/REPO WORKFLOW_FILE BRANCH TEST_STEP_REGEX [RUNS]`. List the step names first (`gh api repos/OWNER/REPO/actions/runs/ID/jobs -q '.jobs[0].steps[].name'`), and pass a pattern that matches only the test steps.

```python
import collections, datetime, json, re, statistics, subprocess, sys
repo, wf, branch, test_re, n = *sys.argv[1:4], re.compile(sys.argv[4], re.I), int(sys.argv[5]) if len(sys.argv) > 5 else 10
gh = lambda path: json.loads(subprocess.check_output(["gh", "api", path], text=True))
secs = lambda a, b: (datetime.datetime.fromisoformat(b.rstrip("Z")) - datetime.datetime.fromisoformat(a.rstrip("Z"))).total_seconds()
runs = gh(f"repos/{repo}/actions/workflows/{wf}/runs?branch={branch}&per_page=100")["workflow_runs"]
runs = sorted((r for r in runs if r["conclusion"] == "success"), key=lambda r: r["created_at"], reverse=True)[:n]
if not runs: sys.exit("no green runs returned; the endpoint is inconsistent, so retry")
print(f"{len(runs)} green runs, {runs[-1]['created_at'][:10]} to {runs[0]['created_at'][:10]}")
agg = collections.defaultdict(lambda: collections.defaultdict(list))
for run in runs:
    for job in gh(f"repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100")["jobs"]:
        steps = [s for s in job["steps"] if s.get("started_at") and s.get("completed_at")]
        if steps and job["started_at"] and job["completed_at"]:  # skips skipped jobs and expired step data
            total = secs(job["started_at"], job["completed_at"])
            test = sum(secs(s["started_at"], s["completed_at"]) for s in steps if test_re.search(s["name"]))
            name = re.sub(r"\s*\(.*\)$", "", job["name"])  # merges matrix variants
            for key, value in (("queue", secs(job["created_at"], job["started_at"])), ("test", test), ("setup", total - test), ("total", total)):
                agg[name][key].append(value)
if not agg: sys.exit("no job had step times: these runs are too old, so retry until the dates are recent")
for name, d in sorted(agg.items()):
    m = {k: statistics.median(v) for k, v in d.items()}
    print(f"{name[:40]:40} jobs={len(d['total']):3} queue={m['queue']:.0f}s setup={m['setup']:.0f}s test={m['test']:.0f}s setup_share={m['setup'] / max(m['total'], 1):.0%}")
```

On pytest's own `test.yml`, with the pattern `'^test '`, three green runs gave the matrix job 5 s of queue, 28 s of setup, and 128 s of tests: a 17% setup share [toy]. Identical calls to the runs endpoint, and to `gh run list`, returned different pages, even with a date filter, and old runs had no step times, so check the printed date range and retry until it is recent [toy]. Cost: one API call per run. For other CI systems, see [ci-history.md](ci-history.md).

### Duration-file staleness and shard preview

```sh
comm -23 <(grep '::' AUDIT/nodeids.txt | sort -u) <(jq -r 'keys[]' ROOT/.test_durations | sort -u) | wc -l   # collected, no duration
comm -13 <(grep '::' AUDIT/nodeids.txt | sort -u) <(jq -r 'keys[]' ROOT/.test_durations | sort -u) | wc -l   # stored, gone
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary ROOT/.test_durations --top 20
for g in 1 2 3 4; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label shard-$g --timeout 900 --cwd ROOT -- \
      CI_TEST_COMMAND --collect-only -q --splits 4 --group $g --splitting-algorithm least_duration
done
grep -h 'estimated duration' AUDIT/runs/*-shard-*/output.log
```

Over 10% of collected tests without a duration, or a last commit (`git -C ROOT log -1 --format=%cs -- .test_durations`) older than the last big reshuffle of tests, means rebalance. `results.py summary` on the durations file shows the long tail and the heaviest files without a run. If every group's estimate equals its test count in seconds, pytest-split matched no durations. Cost: one collection per group.

### Tier and shard unions

```sh
for m in "not slow" "slow"; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label "tier-${m// /-}" --timeout 900 --cwd ROOT -- \
      CI_TEST_COMMAND --collect-only -q -m "$m"
done
cat AUDIT/runs/*-tier-*/output.log | grep '::' | sort | uniq -d | head                                     # in two tiers
cat AUDIT/runs/*-tier-*/output.log | grep '::' | sort -u | comm -13 - <(sort AUDIT/nodeids.txt) | head   # in no tier
```

Run the same two lines on the `shard-*` runs from the previous recipe. For shards and complementary tiers, both lists must be empty [toy]. A tier that selects nothing exits with code 5. `run_suite.py` counts a run that deselects every test as complete (`no tests selected (N deselected)`), both as a test run and under `--collect-only -q`, which prints `no tests collected (N deselected)` [toy]. Under pytest-xdist, an empty selection stays PARTIAL, because xdist's output does not show that tests were deselected. `nodeids.txt` must come from a collection without `-m` or `-k`. Cost: one collection per tier.

### Shadow-mode estimate for selection

Work in a local clone outside the project, never in its working tree, and run the selector from an isolated environment that can import the project. For each of the last 30 default-branch commits, record what pytest-impacted would select, then the share of test time it covers:

```sh
cd CLONE && mkdir -p AUDIT/shadow
for c in $(git log --first-parent -30 --format=%H); do
  git checkout -q "$c"
  impacted-tests --module=PKG --tests-dir=tests --git-mode=branch --base-branch="$c~1" > AUDIT/shadow/$c.txt 2>/dev/null \
    || echo ALL > AUDIT/shadow/$c.txt       # a selector error counts as run-all
done
python3 - ROOT/.test_durations CLONE AUDIT/shadow <<'EOF'
import json, sys
from pathlib import Path
durations, root, shares = json.load(open(sys.argv[1])), Path(sys.argv[2]).resolve(), []
for sel in Path(sys.argv[3]).glob("*.txt"):
    lines = [l.strip() for l in sel.read_text().splitlines() if l.strip()]
    files = {str(Path(l).resolve().relative_to(root)) for l in lines if l != "ALL"}
    shares.append(1.0 if "ALL" in lines else sum(v for k, v in durations.items() if k.split("::", 1)[0] in files) / sum(durations.values()))
shares.sort()
print(f"{len(shares)} changes; median selected share of test time {shares[len(shares) // 2]:.0%}; worst {shares[-1]:.0%}")
EOF
```

`impacted-tests` prints one absolute test-file path per line [toy]. For commits whose CI failed, check that the failing tests fall inside the selection; a failing test outside it is a miss. Cost: one checkout and one graph analysis per commit. The loop was checked on a toy repository only.

### Sampling a suite too slow to run in full

First take W, the serial test work, from CI data (`CI_REPORTS` below): the sum of test time across shard JUnit files, or `results.py summary ROOT/.test_durations`. Sample only when that data is missing or untrustworthy.

1. Pick a census of the files that each hold at least 2% of the known test time (pass `--nodeids AUDIT/nodeids.txt` for JUnit without file attributes; with no timing data, leave it empty). If the census covers most of the time, run the full suite instead. Otherwise sample the rest, and run the census and the sample serially, so that each pays a session fixture once:

   ```sh
   python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary CI_REPORTS --top 200 --json-out AUDIT/results/ci-files.json
   jq -r '.files[] | select(.share >= 2) | .group' AUDIT/results/ci-files.json > AUDIT/census.txt
   awk -F'::' 'NR == FNR {census[$0]; next} !($1 in census)' AUDIT/census.txt AUDIT/nodeids.txt > AUDIT/nodeids-rest.txt
   python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py sample --nodeids AUDIT/nodeids-rest.txt --out AUDIT/sample.txt --fraction 0.1 --seed 1
   python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label census --timeout SECONDS --cwd ROOT --timing-plugin -- \
       CI_TEST_COMMAND -n 0 @AUDIT/census.txt
   python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label sample --timeout SECONDS --cwd ROOT --timing-plugin -- \
       CI_TEST_COMMAND -n 0 @AUDIT/sample.txt
   python3 ${CLAUDE_SKILL_DIR}/scripts/results.py extrapolate AUDIT/runs/NN-sample --plan AUDIT/sample.json --json-out AUDIT/results/extrapolated.json
   ```

2. `extrapolate` counts the setup of each worker's first test once, unscaled, because it holds the session fixtures. It prints that amount, `--json-out` adds it as `first_test_setup_seconds`, and it warns when the run has no setup times; the timing plugin, a report log, or a `--durations` block provides them. Both runs paid the session setup, so the serial total is the census's `sum of test time` + the estimate − `first_test_setup_seconds`.
3. A session fixture that is not autouse is paid by the first test that requests it, so `extrapolate` still scales it [toy]. Find that test under `slowest setup` in `results.py summary`, and subtract its setup × (its stratum's `tests_total` ÷ the stratum's sampled tests in `sample.json` − 1). W for the worker model excludes session setup, so subtract `first_test_setup_seconds` once more. For wall time, add start-up, collection, and one session setup per process.

Read the 90% range before the point estimate. When it spans more than a factor of 2, raise `--fraction` or enlarge the census instead of deciding on the estimate; a narrow range from one or two files per stratum still means unknown, not certain. In the toy suite, a plain 30% sample estimated 54 s (range 9–149 s) against a true 21.9 s, because one sampled file held most of the time. With a census, two draws gave totals of 21.2 s and 21.1 s without any manual correction. A session fixture that was not autouse put the estimate for the non-census files at 9.1 s against a true 7.7 s [toy]. Mark the result as extrapolated, with medium confidence at most. `pytest @FILE` needs pytest 8.2+. Cost: the census plus the sampled share of a serial run.

### Estimating a saving before the change

Collect W, the longest test L, and the per-shard fixed cost F. Also collect runs per day R, shards N, the runner price per minute P [26], and how many runs a developer waits on.

- **Workers on one machine:** wall(N) ≈ X + S + max(L, W ÷ N). X is the time outside the test phase (wall − span of a parallel run), and S is the per-worker session setup from `results.py fixtures`. Fitted on one 4-worker toy run (X 1.4 s, S 1.0 s, L 1.5 s, W 20.0 s), it predicted 12.4 s at 2 workers and 4.9 s at 8, against three-run medians of 12.3 s and 5.2 s [toy]. X grows with N, so the model flatters large N.
- **Shards:** use the model in "Shard count ignores per-shard fixed cost". Runner cost per day ≈ R × (N × F + W) × P, so cutting W by a share s saves about R × W × s × P, and cutting F by ΔF saves R × N × ΔF × P.
- **Selection:** the saving per run ≈ W × (1 − the median selected share), minus the selector's analysis time on every run and the cost of the backstop runs. Each miss adds a later failure in the merge queue or nightly run.
- **Ordering:** it saves time only on failing runs, so multiply the drop in time to the first failure by the share of PR runs that fail.

Example with assumed inputs: 120 PR runs per day, N = 8, F = 4 minutes, W = 80 minutes, P = $0.006. The cost is about 120 × (32 + 80) × 0.006 ≈ $81 per day, and the wall time about 4 + 10 = 14 minutes. Halving F saves about $11.5 per day and 2 minutes per run. A selector that runs 30% of W saves about $40 per day and cuts the wall time to about 7 minutes, before the backstop's cost. State developer waiting in hours per week, let the team price it, and never invent an hourly rate. Record the impact's basis as `heuristic` or `extrapolated`. Cost: arithmetic on numbers from the recipes above.

## Tools

Versions and dates are from PyPI and GitHub, read on 2026-09-30 [33]. "Toy" means checked for this page.

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| pytest-xdist | Worker processes on one machine | 3.8.0, 2025-07-01; maintained | Session fixtures run per worker; `auto` ignores cgroup quotas; no `-s` or `--pdb`. Works on pytest 9.1.1 and Python 3.14 (toy) [9] |
| pytest-split | Timing-based shards | 0.11.0, 2026-02-03; maintained | `least_duration` balances best; unknown tests get the average; write `--durations-path=` with `=` (toy) [24] |
| Buildkite Test Engine (bktec) | Timing-based and dynamic shards | bktec 3.1.0, 2026-09-24; Python collector 1.9.0; maintained | Falls back to an alphabetical split when the service is unavailable [3] |
| pytest-testmon | Coverage-based selection and ordering | 2.2.0, 2025-12-01; one maintainer | Needs `COVERAGE_CORE=ctrace` on Python 3.14+ (toy); crashes under `-p no:cacheprovider`; ignores static files and services [17] |
| pytest-impacted | Static import-graph selection from a git diff | 0.34.0, 2026-09-28; beta, three releases in three days | Reports unselected tests as skipped, which inflates skip counts; `--invalidate-all PATTERN` forces a full run [18] |
| tach | Module boundaries, with an impact-analysis pytest plugin | 0.35.1, 2026-09-14; community maintainer | Selects at declared-module granularity: one module for the package ran all 520 toy tests, and one module per file skipped 494. Loads when installed (`-p no:tach`) [28] |
| grimp | Import graph for a custom selector | 3.17, 2026-09-04; maintained | `find_downstream_modules`; static imports only |
| Datadog Test Impact Analysis | Hosted per-test coverage selection | ddtrace 4.15.3, 2026-09-30; maintained | Documented gaps with pytest-cov and xdist [30] |
| CloudBees Smart Tests (formerly Launchable) | Hosted predictive subsets | smart-tests-cli 2.15.1, 2026-09-29; maintained | Start in `--observation` mode [29] |
| pytest-run-parallel, pytest-threadpool | Threads on free-threaded Python | 0.10.0, 2026-08-04; 0.4.0 beta, 2026-03-19 | run-parallel stresses thread safety and is "not an alternative to pytest-xdist", and threadpool pins `pytest<=9.0.2` [34]. Keep xdist as the default |

## Evidence

- PyPI Warehouse, pytest: 163 s → 30 s (−81%) while tests grew from 3,900 to 4,734. xdist gave 191 s → 63 s on 32 cores, the `sysmon` coverage core 58 s → 27 s, and `testpaths` cut collection from 7.84 s to 2.60 s. A migration change worth 13% was rejected for its upkeep [1].
- Meta's predictive test selection ran under a third of the tests that build-dependency selection picks, and halved infrastructure cost. It still reported over 95% of individual failures and over 99.9% of faulty changes, with all tests run every few hours [14].
- Ekstazi, dynamic file-level selection on Java: end-to-end time −32% on average and −54% on longer suites; coarse dependencies beat method-level ones [5].
- Static selection on 985 revisions of 22 projects: class-level matched Ekstazi's savings but was sometimes unsafe, and method-level performed poorly [6].
- STARTS selected 35.2% of tests. End-to-end time was 81.0% of running everything (68.2% for suites over a minute), and it was slower in 6 of 21 short projects [6].
- Mozilla Firefox: a model on failure history ran 70% fewer test tasks than the previous heuristic, with periodic full runs [31].
- GitLab runs a predictive subset before approval and the full suite after it [12]. Microsoft runs all tests for unknown file types, and recommends periodic full runs [15].
- RETECS: reinforcement-learning prioritisation needed about 60 CI cycles to match a sort by recent verdicts [4].
- Instawork: about 35,000 pytest tests over 20 minutes; testmon halved the median, with full runs before deployment. Unverified: read from a search summary [32].
- xdist issue #850: time before the first test grew from 3 min 25 s at 1 worker to 57 min 39 s at 8 after a Python upgrade; an anecdote with no root cause [7].
- Vendor figures, not independent: Buildkite's 10 → 4 minutes [3]; rstest's single runs with `-n 8`: pandas 182 → 61 s, aiohttp 197 → 160 s, django-allauth 22 → 8 s, and rich 3.4 → 2.8 s [2].

## Sources

1. https://blog.trailofbits.com/2025/05/01/making-pypis-test-suite-81-faster/ – PyPI's test suite speed-up, with numbers per step.
2. https://python-rstest.readthedocs.io/en/stable/reference/benchmarks/ – rstest benchmark table with pytest-xdist timings (vendor, single runs).
3. https://buildkite.com/docs/test-engine/test-splitting and https://github.com/buildkite/test-engine-client – Buildkite Test Engine splitting and its example (vendor), and bktec's fallback split.
4. https://arxiv.org/abs/1811.04122 – Spieker et al., "Reinforcement Learning for Automatic Test Case Prioritization and Selection in Continuous Integration" (RETECS), ISSTA 2017.
5. https://users.ece.utexas.edu/~gligoric/papers/GligoricETAL15Ekstazi.pdf – Gligoric et al., "Practical Regression Test Selection with Dynamic File Dependencies" (Ekstazi), ISSTA 2015.
6. https://www.cs.cornell.edu/~legunsen/pubs/LegunsenETAL17STARTS.pdf and https://www.cs.cornell.edu/~legunsen/pubs/LegunsenETAL16StaticRTSStudy.pdf – Legunsen et al., "STARTS: STAtic Regression Test Selection", ASE 2017, and "An Extensive Study of Static Regression Test Selection in Modern Software Evolution", FSE 2016.
7. https://github.com/pytest-dev/pytest-xdist/issues/850 – a report of start-up time growing with the worker count (anecdote).
8. https://docs.github.com/en/actions/reference/runners/github-hosted-runners – GitHub-hosted runner sizes.
9. https://pytest-xdist.readthedocs.io/en/latest/ – pytest-xdist documentation: distribution modes and worker counts (`distribution.html`), `worker_id` and the file-lock pattern (`how-to.html`), known limitations, and the changelog. Source at https://github.com/pytest-dev/pytest-xdist: v3.8.0 worker-count detection and `load` scheduling, and unreleased changes on main.
10. https://docs.pytest.org/en/stable/changelog.html and https://docs.pytest.org/en/stable/how-to/cache.html – pytest 9.0–9.1 changes (strict mode, the `addopts` strict-flag regression), and `--lf`, `--ff`, `--nf`, `--sw` with the cache.
11. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue, https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations, and https://docs.github.com/en/actions (source: https://github.com/github/docs) – GitHub Actions: the merge queue and `merge_group`, matrix `fail-fast`, workflow triggers, path filters, skipped-job status, and concurrency groups.
12. https://docs.gitlab.com/development/pipelines/ – GitLab's predictive tests, full-suite rules, and fail-fast job.
13. https://coverage.readthedocs.io/en/latest/config.html and https://coverage.readthedocs.io/en/latest/messages.html – coverage.py's `[run] core`, the `sysmon` default on Python 3.14+, and the `no-sysmon-context` warning.
14. https://arxiv.org/abs/1810.05286 – Machalica et al., "Predictive Test Selection", ICSE-SEIP 2019.
15. https://learn.microsoft.com/en-us/azure/devops/pipelines/test/test-impact-analysis – Azure DevOps Test Impact Analysis: safe fallback and periodic full runs.
16. https://docs.develocity.ai/predictive-test-selection/ – Develocity Predictive Test Selection: supported build tools and the remaining-tests stage.
17. https://testmon.org/ and https://github.com/tarpas/pytest-testmon – testmon options and what it does not track.
18. https://github.com/promptromp/pytest-impacted – pytest-impacted git modes, dependency-file invalidation, and fail-open behaviour.
19. https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching – cache scope, eviction, size limit, and cache poisoning.
20. https://docs.python.org/3/library/os.html#os.process_cpu_count – `os.cpu_count()` and `os.process_cpu_count()`.
21. https://docs.astral.sh/uv/concepts/cache/ and https://github.com/astral-sh/setup-uv/blob/main/docs/caching.md – uv caching in CI, `uv cache prune --ci`, and setup-uv cache keys.
22. https://github.com/AdamGleave/pytest-shard – hash-based sharding that ignores run time.
23. https://circleci.com/docs/guides/optimize/parallelism-faster-jobs/ and https://support.circleci.com/hc/en-us/articles/360056636191 – CircleCI test splitting, and the `junit_family=xunit1` requirement for pytest (support article read through a search summary).
24. https://jerry-git.github.io/pytest-split/ and https://github.com/jerry-git/pytest-split – pytest-split algorithms, missing durations, and the random-order limit; source: durations include setup and teardown, `--clean-durations`.
25. https://docs.knapsackpro.com/overview/ – Knapsack Pro's supported languages (no Python client).
26. https://docs.github.com/en/billing/reference/actions-runner-pricing – runner prices per minute and rounding to whole minutes.
27. https://www.pantsbuild.org/stable/docs/python/goals/test and https://bazel.build/reference/test-encyclopedia – Pants pytest integration and test caching, and Bazel's test sharding protocol.
28. https://github.com/gauge-sh/tach/blob/main/docs/usage/commands.md – `tach test` and the tach pytest plugin.
29. https://help.launchableinc.com/features/predictive-test-selection/requesting-and-running-a-subset-of-tests/choosing-a-subset-optimization-target/ and https://help.launchableinc.com/features/predictive-test-selection/observing-subset-behavior/ – CloudBees Smart Tests (formerly Launchable) subset targets and observation mode.
30. https://docs.datadoghq.com/tests/test_impact_analysis/setup/python/ and https://docs.datadoghq.com/tests/test_impact_analysis/how_it_works/ – Datadog Test Impact Analysis for Python, its limits, and its skipping rule.
31. https://hacks.mozilla.org/2020/07/testing-firefox-more-efficiently-with-machine-learning/ – Mozilla's machine-learning test selection for Firefox.
32. https://engineering.instawork.com/test-impact-analysis-the-secret-to-faster-pytest-runs-e44021306603 – Instawork's testmon case study; unreadable (HTTP 403), numbers from a search summary.
33. https://pypi.org/pypi/{package}/json – the PyPI JSON API, used for versions and dates; GitHub releases for Pants, Bazel, and bktec.
34. https://github.com/Quansight-Labs/pytest-run-parallel and https://pypi.org/project/pytest-threadpool/ – pytest-run-parallel, a thread-safety stress tool rather than a speed-up, and pytest-threadpool with its `pytest<=9.0.2` pin.
