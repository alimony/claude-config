# CI history and telemetry

This page covers harvesting test results from continuous integration (CI) systems and test analytics services, reading them without miscounting reruns, and the statistics that turn that history into findings. Load it in phase 3, "Harvest existing artifacts", before you run anything. One local run of a 60-minute suite costs an hour and gives one sample per test. By contrast, 30–90 days of CI history gives hundreds of samples per test from the real runners, with reruns and shard assignment. Root causes and fixes for flaky tests are in [flakiness.md](flakiness.md).

## Quick reference

Thresholds are starting points unless a source is cited. Tune them to the suite's size and run frequency.

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| Retries hide flakiness | Rerun settings in the configuration; "tests with reruns" in `results.py summary`, with `--repeats-are-reruns` for pytest JUnit XML from CI | Any test that passed on a rerun; any rerun rate above 0 | Make reruns visible and fail on them, one directory at a time; fix the top offenders | Google spent 2–16% of its test compute re-running flaky tests [1] |
| Same-commit flips | `results.py flips --same-commit` once per commit and configuration; flip rate across commits as a weak candidate | One flip or more, ranked by expected red builds; flip rate 0.05 or more over 30 or more runs at low confidence | Root cause in [flakiness.md](flakiness.md), most frequent first | GitHub: flaky builds fell from 1 in 11 commits to 1 in 200 [2] |
| Jobs retried to green | Jobs of every attempt (`filter=all`) | Any job whose last attempt passed after an earlier one failed | Take the failed tests from the failed attempt's log, then treat them as same-commit flips | Atlassian: about 150,000 developer hours a year lost to reruns [3] |
| Missing or unreliable history | No report artifacts; no reports from failed runs; retention under 30 days; test counts that drop | Fewer than about 100 recoverable runs of the main test job; a count drop over 1% | Upload xunit1 JUnit XML and a report log from every job and attempt, also after failures | Enables every other signal; 5,000 tests cost 16 KB of gzipped JUnit XML per run [4] |
| Queueing or setup dominates | Job and step timestamps against the sum of test times | 95th percentile (p95) of queue time over 10% of run p95; non-test steps over 30% of job time | More runners or fewer jobs; caches; [fixed-costs.md](fixed-costs.md) | Shopify: 68% of CI time passed before any test ran [5] |
| Slow tests and duration regressions | `results.py summary` per run; `results.py diff` between windows | Median (p50) over 10 s, or over 1 s in unit tests; p95 over 3 × p50; a median up 1.5 times and 0.5 s | Fix hanging tests first; wider fixture scopes; bisect regressions | Shopify: taking a few tests out temporarily, one of which often hung, cut p95 CI time from 44 to 34 minutes [5] |
| Co-failing clusters and outages | Jaccard similarity of failing-run sets | 2 or more tests sharing 3 or more failing runs at Jaccard 0.8 or more | Fix the shared cause once | 75% of flaky tests in 24 Java projects sat in clusters, mean size 13.5 [6] |
| Failures concentrated on one shard, worker, runner, platform, or time | One-sided Fisher's exact test per value | p < 0.01 after correction, with 3 or more failures | Order dependence to [flakiness.md](flakiness.md); resources; platform bugs to the issue tracker | 59% of 7,571 flaky Python tests were order-dependent [7] |
| Quarantine rot and permanent failures | Skip, xfail, and flaky marks over time; vendor quarantine lists | A rising count; entries with no owner or exit rule; tests failing in every run | An owner and an exit rule per entry | Flaky tests revealed over a third of Chromium's regression faults [8] |
| Never fail, never run, always skipped | Union of all jobs and schedules against node IDs | Any never-run or always-skipped test; never-failing tests only as input | Fix collection; review skip reasons | 91.3% of Google's test targets never failed in a month [9] |

## Signals

### Retries hide flakiness

- **Detect:** Search the configuration for retries ("Inventory" below): `--reruns`, `reruns =`, `@pytest.mark.flaky`, pytest-retry, `rerunFailingTestsCount`, gotestsum `--rerun-fails`, Playwright `retries:`, `jest.retryTimes`, GitLab `retry:`, and GitHub runs with `attempt` above 1. Then count reruns in the reports. `results.py summary` prints "tests with reruns" for report logs, Surefire, and run_suite.py runs whose manifest has `reruns_configured`. run_suite.py sets it when `--reruns` is in the command or `PYTEST_ADDOPTS`, or when the project's pytest configuration has a `reruns` option. For other pytest JUnit XML, such as CI reports, `summary` prints "tests with repeated JUnit entries" instead, because a repeated ID can also be a duplicate. When the inventory shows reruns in CI and the dialect check shows more elements than declared tests, pass `--repeats-are-reruns` to `summary`, `flips`, and `diff`. A passed rerun is a flip at that commit. Report each such test, the suite rerun rate (extra attempts ÷ test executions), and the CI minutes spent in failed attempts. Set `trust_breaker` only when history shows a retry hiding a real failure, for example a first-attempt failure rate that jumped at one commit while builds stayed green ([findings.md](findings.md)).
- **False positives:** A test that failed on every attempt is a consistent failure, not a flake. A repeated ID can also come from a test collected twice (`--keep-duplicates`) or from reports merged into one file, so run the dialect check ("Read JUnit dialects correctly" below) before you count repeats as reruns. A test imported into a second module also repeats `file` and `name`, because xunit1's `file` names the defining file. The skill's results.py takes the module from `classname` instead, so it keeps imports apart, but tools that key on `file` merge them [10].
- **Fix:** Keep retries only as a visible stopgap, and disclose the protection they cost ([traps.md](traps.md)). pytest-rerunfailures 16.7 has `--fail-on-flaky`, which exits with code 7 when a test passes on a rerun [11]. Its `--max-suite-reruns N` caps reruns for the whole suite, and `--only-rerun REGEX` limits them to known infrastructure errors. Surefire has `failOnFlakeCount` [12], and Playwright has `failOnFlakyTests` since 1.52 [13]. Fail-on-flaky turns the build red while the backlog is large, so roll it out one directory at a time. Publish the passed-on-rerun list with owners, and route the top entries to [flakiness.md](flakiness.md).
- **Effect:** Google spent 2–16% of its test compute re-running flaky tests [1]. Shopify's retries raised an Android pipeline's pass rate from 31% to almost 90%, which shows how much failure retries can hide [14].
- **Verify:** Over the next weeks, the rerun rate and passed-on-rerun counts fall, and first-attempt failures on the default branch do not rise.

### Same-commit flips

- **Detect:** Group the reports by the code that ran and by configuration, and run `results.py flips --same-commit` once per group ("results.py summary, diff, and flips" below). The same code means the attempts of one run, or runs at one commit hash (SHA) for any event except `pull_request`. A `pull_request` run tests a merge commit of the branch into its base, not the run's `head_sha` [15]. Pair it only with its own attempts, which reuse the original commit [16]. Rank by commits with a flip × duration, and estimate the cost as reruns × duration plus red builds. Without a same-commit pair, a high flip rate is only a candidate at low confidence. The flip rate is outcome changes between consecutive default-branch runs ÷ (runs − 1), and the cross-run snippet prints it; report 0.05 or more over 30 or more runs. A breakage and its fix give two transitions, while flakiness gives many short streaks.
- **False positives:** Matrix cells at one commit are different code paths: a pass on Python 3.12 and a fail on 3.13 is a compatibility bug, so keep one configuration per group. A cancelled run can mark tests as errors, so the harvest skips cancelled runs. Many tests failing in the same runs is one infrastructure event (see "Co-failing clusters and infrastructure events"). A test that depends on the date can pass and fail at one commit on different days. Across commits, any single flip can be real ([traps.md](traps.md)), and at Google, selection by recent transitions did worse than how often a test runs and how many authors trigger it [17].
- **Fix:** Confirm flip-rate candidates with reruns at one commit first. Route to [flakiness.md](flakiness.md), most frequent first, because flakiness follows a Pareto distribution: at GitHub, 0.4% of flaky tests failed 100 times or more [2]. The ranked list is itself a lever: Spotify cut flakiness from 6% to 4% in two months by publishing a table of flaky tests, with no other change [18]. State how flaky a test is as a failure probability with an interval, as Meta's probabilistic flakiness score does [19], not as a yes-or-no label.
- **Effect:** GitHub's flaky builds fell from 1 in 11 commits to 1 in 200 [2]. Slack's main-branch stability rose from 19.82% to 96% after automated detection and suppression, and one suppressed test later hid a real failure that reached the main branch [20]. Apple ranked flaky tests by flip rate and entropy and cut flakiness by 44% with under 1% loss of fault detection; only the abstract was available [21].
- **Verify:** The fixed test shows no same-commit flip over enough runs to bound its rate: 300 clean runs put it below 1% at 95% confidence. The suite's green rate rises as Π(1 − pᵢ) predicts. A flip-rate candidate's rate over the next window falls by more than its interval's width.

### Jobs retried to green at one commit

- **Detect:** From the jobs of every attempt (`filter=all` [22]), flag each job whose last attempt succeeded after an earlier attempt failed ("Job attempts and logs" below). This needs no test reports. When the failed step is the test step, fetch that attempt's job log and extract its `FAILED` and `ERROR` lines. Those tests failed and then passed at one commit, provided the job ran the same tests. Report the count, the share of runs that needed a re-run, and the CI minutes in failed attempts.
- **False positives:** Aggregate status jobs, such as "All required checks pass", fail whenever another job fails; exclude them by name. An attempt that fails before the test step, or loses its runner, is an infrastructure event: report it under the `ci` dimension, not as a test flip.
- **Fix:** As for same-commit flips. For infrastructure failures, see [scheduling.md](scheduling.md) and [fixed-costs.md](fixed-costs.md).
- **Effect:** Each retried job costs its failed attempt's run time and a developer's wait. Atlassian estimated 150,000 developer hours a year lost to reruns [3].
- **Verify:** The share of runs that need a re-run falls over the next month, measured the same way.

### Missing or unreliable history

- **Detect:** No JUnit XML or report-log artifacts in the last 30 days of runs; no `--junitxml`, `--report-log`, or `junit_family` in the configuration; or retention under 30 days (`retention-days:`, `expire_in:`). GitHub applies `success()` to a step unless it says `if: ${{ !cancelled() }}` or `always()` [23], so an upload step without either leaves no report from the failed runs you need most. Report fewer than about 100 recoverable runs of the main test job, because fewer clean runs cannot rule out a 3% failure rate. Also flag test-count drops of more than 1% between consecutive default-branch runs, jobs without a report, and the share of tests seen in only part of the window.
- **Logs only:** when jobs upload no reports, the job logs are the record. `results.py summary` reads `pytest -v` outcome lines from a log, also in xdist's and GitHub's timestamped forms, and counts `RERUN` lines, but takes no times from them. A `-q` log has only its summary line and the failures, so count runs, items, reruns, and failures from those lines instead. Logs are about 126 KB each, and 3,046 took about 10 minutes to download one by one, so fetch them in parallel, for example with `xargs -P 8`. GitHub masks secrets in logs as `***`, including inside test IDs, and a module-level skip counts as one test in the summary, so allow for both before you compare IDs or counts with a local collection. A workflow that runs only on pull requests leaves no default-branch history, so flip rates between consecutive default-branch runs cannot be computed.
- **False positives:** The data may live in an analytics service; the inventory search finds their uploaders. Job logs keep failing test IDs for the whole retention window. pytest 9 subtests add to `tests` and `failures` without adding `<testcase>` elements, and reruns add elements without adding to `tests` [4]. Renames and parametrised IDs that depend on list order (`test_x[obj0]`) change node IDs without losing tests.
- **Fix:** Add `--junitxml=reports/junit.xml -o junit_family=xunit1 --report-log=reports/log.jsonl -rR` to the CI test command, and upload `reports/` from every job and attempt, as below. The name must be unique, because upload-artifact v4 and later reject a second upload with the same name [24]; the `-attempt-N` suffix lets the flips snippet pair attempts. `xunit1` keeps the `file` attribute that file-level tools need, and Codecov asks for it under its alias `legacy` [25]. The report log needs pytest-reportlog in the CI environment, and it keeps every attempt and the xdist `worker_id`, which JUnit XML drops [26]. For Django's runner, unittest-xml-reporting writes JUnit XML [27]. Fail the job when its report is missing, and treat a missing report as missing data, never as a pass.

  ```yaml
  - uses: actions/upload-artifact@v7
    if: ${{ !cancelled() }}
    with:
      name: test-reports-${{ strategy.job-index }}-attempt-${{ github.run_attempt }}
      path: reports/
      retention-days: 90
  ```

- **Effect:** It enables every other signal on this page. For 5,000 tests, a run's JUnit XML is 349 KB (16 KB gzipped) and its report log 6.45 MB (420 KB gzipped), with no measurable wall-time cost [4].
- **Verify:** A week later, every job has a report, failed ones included, and each report's count matches the pytest summary line within the number of subtests.

### Queueing or setup dominates feedback time

- **Detect:** From the jobs, queue time is `started_at − created_at` and run time is `completed_at − started_at` [22]; GitLab jobs expose `queued_duration` [28]. Step timestamps separate setup (checkout, dependency install, database build) from the test step. Report p95 queue time over 10% of p95 run time, and non-test steps over 30% of job time. Also report a sum of test times under 70% of test-step time × workers, which points to collection and imports ([fixed-costs.md](fixed-costs.md)). Without application programming interface (API) access, GitHub's Actions performance metrics page shows run time, queue time, and failure rate per workflow and job for up to 100 days [29].
- **False positives:** Self-hosted runners that boot on demand count boot time as queue time. Jobs that wait for an upstream job show an early `created_at`.
- **Fix:** For queueing: more or larger runners, fewer matrix cells on pull requests, or cancelling superseded runs. For setup: dependency and database caches, and containers started in parallel. When queue time dominates, faster tests do not shorten feedback. For worker balance, see [scheduling.md](scheduling.md).
- **Effect:** At Shopify, preparing agents took about 31% and building dependencies about 37% of CI time, so 68% passed before any test ran. Container start p95 fell from 90 s to 25 s after fixes [5].
- **Verify:** Compare job wall-time p95 and queue p95 over two weeks before and after the change.

### Slow tests and duration regressions

- **Detect:** `results.py summary` on each run prints the per-test p50, p95, and maximum, the share of time in the slowest 1%, 5%, and 10% of tests, and counts over 1, 5, and 30 s. The cross-run snippet lists tests whose p95 exceeds 3 × p50, which points to waits and timeouts. `results.py diff` between the newest 10 runs and earlier runs lists per-test median increases: flag a rise of at least 1.5 times and 0.5 s. At suite level, plot the test count and job wall time per week.
- **False positives:** pytest's JUnit `time` includes setup and teardown by default (`junit_duration_report = total`) [30]. The first test that uses a session fixture therefore absorbs its setup, and its duration changes when the order changes. If CI runs with coverage (`--cov`, `coverage run`), its timings are instrumented: use them to pick candidates, and back timing claims with a `run_suite.py` run ([traps.md](traps.md)). When over about 10% of tests regress together, look at the runner image, caches, or dependencies instead. A few end-to-end tests make a heavy top 1% by design.
- **Fix:** Fix hanging and near-timeout tests first, because they dominate p95. Bisect a regression over its commit range with the single test, which costs one test per step. Then widen fixture scopes ([fixed-costs.md](fixed-costs.md), [database-and-data.md](database-and-data.md)), add a per-test timeout such as pytest-timeout for the worst offenders, and feed durations to the shard planner ([scheduling.md](scheduling.md)).
- **Effect:** Shopify cut p95 CI time from 45 to 18 minutes; taking a few tests out temporarily, one of which often hung, saved 10 minutes of p95 (44 to 34) [5]. Its core suite grew 20–30% a year [5]. A regressed test adds its increase to every run of its shard, and the slowest shard sets the job's time.
- **Verify:** Compare p50 and p95 of job wall time over at least 20 runs after the change with 20 runs before, at the same test count. A regressed test's median returns to within 20% of its old level.

### Co-failing clusters and infrastructure events

- **Detect:** The cross-run snippet groups tests with at least 3 failures whose failing-run sets have a Jaccard similarity of at least 0.8. Also look for runs where over 1% of tests failed at once. Group failure messages by a normalised signature, with numbers, addresses, and paths removed, to find a shared cause such as `ConnectionResetError`.
- **False positives:** Tests in one module fail together when their shared fixture or the code under test breaks; that is one real failure seen many times. A cluster that fails at every later commit is a breakage, not flakiness.
- **Fix:** Fix the shared cause once ([flakiness.md](flakiness.md)). Retrying infrastructure failures on another host, as Dropbox's Athena did [31], is a trade-off: it hides host problems, so keep counting those retries.
- **Effect:** In 24 Java projects run 10,000 times, 75% of flaky tests belonged to a co-failing cluster with a mean size of 13.5 [6]. One fix therefore often removes over ten flaky tests.
- **Verify:** The cluster's joint failures stop, and all members' flip counts fall together.

### Failures concentrated on one shard, worker, runner, platform, or time

- **Detect:** For each flaky test, count failures and executions per shard, runner (`runner_name`, `labels`), operating system, Python version, and time bucket: hour in Coordinated Universal Time (UTC), weekday, and month end. Test each value against all others with the one-sided Fisher's exact test in "Statistics for rare failures", and report p < 0.01 with at least 3 failures. For xdist, `results.py summary` on a report log shows each worker's busy time, the imbalance, and the finish spread. Rebuild a worker's test order for bisection from `worker_id` and `start` ("Logs and report logs" below).
- **False positives:** A test that always runs on shard 3 fails only there by construction, so it needs history on other shards. A runner effect can be a date effect when runner images change. Runs cluster in working hours, so compare rates, not counts. Many tests × many values means many comparisons: correct with Bonferroni or Benjamini–Hochberg.
- **Fix:** For order dependence, replay the failing worker's preceding tests and bisect ([flakiness.md](flakiness.md)). For resource limits, compare memory and processor use on that runner class. Platform bugs are real failures that belong in the issue tracker. For time dependence, freeze or inject the clock ([flakiness.md](flakiness.md)).
- **Effect:** Of 7,571 flaky tests in PyPI projects, 59% were order-dependent and 28% came from infrastructure [7]. Ruling out order dependence at 95% confidence takes about 31 random-order runs, against 170 runs for other flakiness [7].
- **Verify:** The same Fisher test over a new window shows no concentration.

### Quarantine rot and permanently failing tests

- **Detect:** Count skip, xfail, and flaky marks per commit (`rg -c '@pytest.mark.(skip|xfail|flaky)'`), and read vendor quarantine lists: Buildkite's muted tests [32], Trunk's quarantined tests [33], and Datadog's flaky test states [34]. Report the trend, the median age of entries, entries with no owner or exit rule, and tests that failed in every run of the window.
- **False positives:** A strict xfail with a linked issue documents a known bug on purpose.
- **Fix:** Give each entry an owner and an exit rule, such as re-enabling after N consecutive passes. Codecov expires a flake after 30 consecutive passes [25], and Datadog marks a test "Fixed" after 30 days without flaking [34]. Judge the existing quarantine; the skill never proposes a new quarantine or a removal (SKILL.md guardrail 10).
- **Effect:** Dropbox's automated quarantine doubled the number of quarantined tests and shrank its test cluster by about 8% [31]. The risk is real: flaky tests revealed over a third of Chromium's regression faults, and a filter with 99.2% precision would have hidden about 76% of them [8].
- **Verify:** The quarantine count and median age fall, and no escaped defect traces back to a quarantined test.

### Tests that never fail, never run, or are always skipped

- **Detect:** Take the union of test IDs over all jobs, shards, and schedules in the window, and compare it with `AUDIT/nodeids.txt` after phase 5, mapping JUnit entries with `--nodeids`. List tests absent from every report, tests skipped in every run, and tests that never failed, pull-request runs included. Report the share of each and the time spent on never-failing tests.
- **False positives:** "Never failed on main" is the normal state of a good regression test, because pre-merge runs catch the break first ([traps.md](traps.md)). A test skipped on one platform can run on another. A job that deselects a marker (`-m "not slow"`) can have a nightly job that runs it.
- **Fix:** Never-run tests are trust breakers: fix collection ([redundancy.md](redundancy.md)). For always-skipped tests, report the skip reason and whether its condition still holds. Never-failing tests are input to [mutation-testing.md](mutation-testing.md) and to tiering in [scheduling.md](scheduling.md), never removal candidates on history alone; running them less often delays detection, so disclose that loss.
- **Effect:** 91.3% of Google's test targets passed at least once and never failed in a month, and only 1.23% found a breakage [9].
- **Verify:** After a collection fix, the test count in history rises by the expected number.

## Measuring

Run the recipes in this order: inventory (seconds, no API cost), harvest (minutes to hours of API quota), summarise and group (seconds), then statistics. Everything here reads; nothing writes to the CI system or the repository. Keep harvests under `AUDIT/ci/` and never publish them, because logs and artifacts can contain secrets. Do not re-run CI jobs to create data without the user's approval: re-runs cost CI minutes and show up for the whole team.

### Inventory

```sh
rg -n --hidden -g '!.git' -e '--junit-?xml|junit_family|--report-log|--reruns|reruns\s*=|mark\.flaky|rerun-fails|rerunFailingTestsCount|retryTimes|retries:' \
   -e 'upload-artifact|store_test_results|reports:|artifacts:|retention-days|expire_in|if: .*(always|cancelled)|test_durations' \
   -e 'ddtrace|DD_CIVISIBILITY|test-results-action|report_type:\s*test_results|trunk|buildkite-test-collector|smart-tests|launchable|allure|reportportal|currents' ROOT
git -C ROOT log -1 --format='%cr %h' -- .test_durations    # age of a committed pytest-split timing file
gh api repos/OWNER/REPO/actions/permissions/artifact-and-log-retention    # {"days":90,...}; 403 without permission to read Actions settings
```

The output maps which sources exist, in seconds. The keys of `.test_durations` are node IDs, so before collection is allowed, `jq -r 'keys[]' ROOT/.test_durations > AUDIT/durations-nodeids.txt` gives a `--nodeids` file that maps JUnit entries to exact node IDs [10].

### Retention and rate limits

| System | Keeps | Limits |
| --- | --- | --- |
| GitHub Actions | Artifacts and logs 90 days by default; 1–90 days for public and up to 400 for private repositories [35]; re-runs up to 30 days after a run [16] | Personal token 5,000 requests per hour; `GITHUB_TOKEN` 1,000 per hour per repository; 100 concurrent requests and 900 points per minute [36]; filtered run listings stop at 1,000 results [37] |
| GitLab.com | Job artifacts 30 days unless `expire_in` says otherwise [38] | 500,000 test cases per report; JUnit files 30 MB each and 100 MB per job [38][39] |
| CircleCI Insights | Daily data for 90 days [40] | Test metrics cover the 10 most recent runs [40] |
| Codecov Test Analytics | 60 days [25] | JUnit XML only; private repositories need a paid plan [25] |

Harvesting costs about 2–3 API calls per run plus 1 per artifact, and about 6 s per run serially [4]. So 1,000 runs cost about 2,500–3,000 calls, 35 minutes of a 5,000-per-hour quota, and 100 minutes serially. Run at most 4 date windows in parallel. Never harvest from inside CI with `GITHUB_TOKEN`, whose quota other workflows share [36]. A one-week window of python/cpython's build workflow returned exactly 1,000 runs and silently lost its oldest day and a half [10], so halve any window that returns exactly 1,000 runs.

### Harvest GitHub runs, jobs, and artifacts

```sh
mkdir -p AUDIT/ci/logs AUDIT/results
# 1. Runs, one week per call; drop --branch to include pull-request runs
gh run list -R OWNER/REPO --workflow WORKFLOW --branch main --status completed --created 2026-09-01..2026-09-07 \
  --limit 1000 --json databaseId,attempt,headSha,event,conclusion,createdAt,headBranch > AUDIT/ci/runs-2026-09-01.json
# 2. Jobs of every attempt, with timing, runner, and steps
for id in $(jq -r '.[].databaseId' AUDIT/ci/runs-*.json); do
  gh api --paginate "repos/OWNER/REPO/actions/runs/$id/jobs?filter=all&per_page=100" --jq ".jobs[] | {run_id: $id, id, name,
    run_attempt, conclusion, created_at, started_at, completed_at, runner_name, labels, steps: [.steps[]? | {name, conclusion, started_at, completed_at}]}"
done > AUDIT/ci/jobs.jsonl
# 3. Report artifacts of runs that were not cancelled, one folder per artifact, with the run's commit and event
jq -c '.[] | select(.conclusion != "cancelled")' AUDIT/ci/runs-*.json | while read -r run; do
  id=$(jq -r .databaseId <<<"$run")
  gh run download "$id" -R OWNER/REPO -p 'ARTIFACT_GLOB' -D "AUDIT/ci/$id" 2>> AUDIT/ci/download-errors.log || continue
  jq '{run_id: .databaseId, sha: .headSha, event, attempt, created_at: .createdAt}' <<<"$run" > "AUDIT/ci/$id/meta.json"
done
```

Each matching artifact lands in `AUDIT/ci/RUN_ID/ARTIFACT_NAME/`, and a run without a match logs "no artifact matches any of the names or patterns provided". Artifacts past retention report `expired: true` and cannot be recovered [37]. Artifact names can contain spaces, so quote paths or use `find -print0 | xargs -0`. `gh run view` and `gh run download` can prompt interactively when you omit the run ID, so always pass one. This recipe ran end to end on real home-assistant/core runs [10].

### Job attempts and logs

```sh
python3 - AUDIT/ci/jobs.jsonl 'required checks' <<'EOF'
import collections, datetime as dt, json, re, sys
skip = re.compile(sys.argv[2], re.I) if len(sys.argv) > 2 else None       # aggregate status jobs
t = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
secs = lambda j, a="started_at", b="completed_at": (t(j[b]) - t(j[a])).total_seconds()
jobs = [j for j in {j["id"]: j for j in map(json.loads, open(sys.argv[1]))}.values()
        if j["started_at"] and j["completed_at"] and not (skip and skip.search(j["name"]))]
tries = collections.defaultdict(dict)                                     # (run, job name) -> {attempt: job}
for j in jobs:
    tries[(j["run_id"], j["name"])][j["run_attempt"]] = j
green = [a for a in tries.values() if a[max(a)]["conclusion"] == "success" and any(j["conclusion"] == "failure" for j in a.values())]
failed = [j for a in green for j in a.values() if j["conclusion"] == "failure"]
print(f"runs {len({r for r, _ in tries})}, jobs retried to green {len(green)} in {len({j['run_id'] for j in failed})} runs, "
      f"{sum(map(secs, failed)) / 60:.0f} CI minutes in their failed attempts")
for j in failed[:15]:
    steps = [s["name"] for s in j.get("steps", []) if s["conclusion"] == "failure"]
    print(f"  run {j['run_id']} job {j['id']} attempt {j['run_attempt']}: {j['name']}, failed step {steps}")
done = [j for j in jobs if j["conclusion"] not in ("skipped", None)]
for label, v in (("queue", sorted(secs(j, "created_at", "started_at") for j in done)), ("run", sorted(map(secs, done)))):
    print(f"{label} p50 {v[len(v) // 2]:.0f}s, p95 {v[int(0.95 * (len(v) - 1))]:.0f}s")
EOF
gh api repos/OWNER/REPO/actions/jobs/JOB_ID/logs > AUDIT/ci/logs/JOB_ID.log    # JOB_ID of the failed attempt
perl -pe 's/^\xEF\xBB\xBF//; s/\r$//; s/^[0-9-]{10}T[0-9:.]+Z //; s/\e\[[0-9;]*m//g' AUDIT/ci/logs/JOB_ID.log > AUDIT/ci/logs/JOB_ID.txt
grep -oE '(FAILED|ERROR|RERUN) [^ ]+::[^ ]+' AUDIT/ci/logs/JOB_ID.txt | sort -u
grep -E '[0-9]+ (passed|failed|errors?|skipped)[ ,].* in [0-9.]+s' AUDIT/ci/logs/JOB_ID.txt | tail -1
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary AUDIT/ci/logs/JOB_ID.txt    # reads the slowest-durations block
```

- The snippet's second argument is a regular expression for aggregate jobs to leave out. On 12 python/cpython runs, it found 8 jobs retried to green, 112 CI minutes in failed attempts, and the failed step of each, in seconds [10]. Fetch the log of each failed attempt by its job ID, right away, because the log's redirect URL expires after one minute [22]. Raw job logs start with a byte-order mark, prefix each line with a timestamp, can end lines with a carriage return, and carry colour codes when the job forces colour (`FORCE_COLOR`). The `perl` line removes all four; with colour codes left in, the `grep` lines return IDs with escape codes and miss the summary line [10]. `gh run view --log` also adds job and step columns, which `cut -f3-` removes. In an uncleaned log, results.py misses the durations block and misreads the lines as `--collect-only` output [10].
- `FAILED` and `ERROR` lines appear by default (`-r fE`). `RERUN` lines appear only with `-rR` or `-v`; without them, the summary line counts reruns but does not name them [10]. A log without a summary line may come from a project that writes pytest's output to a file, so look for that file among the artifacts. `--durations` lists every phase and rerun attempt separately, and results.py reads a complete block only from `--durations=0 --durations-min=0`.

In a pytest-reportlog file, rerun attempts have `outcome: "rerun"`, and xdist adds `worker_id` [4]. `results.py summary` reads both, so it counts those reruns and shows per-worker busy time, imbalance, and finish spread, also for report logs harvested from CI [10]. These commands add failures per worker and one worker's test order, the input for order-dependence bisection in [flakiness.md](flakiness.md):

```sh
jq -r 'select(."$report_type" == "TestReport" and (.outcome == "failed" or .outcome == "rerun")) | [.worker_id // "main", .outcome, .nodeid] | @tsv' LOG.jsonl | sort | uniq -c
jq -r 'select(."$report_type" == "TestReport" and .when == "setup" and .worker_id == "gw1") | [.start, .nodeid] | @tsv' LOG.jsonl | sort -n | cut -f2
```

### Other CI systems

| System | Endpoints, from each vendor's API documentation and not called in the source research | Notes |
| --- | --- | --- |
| GitLab | `/api/v4/projects/ID/pipelines?ref=main&updated_after=DATE` (keep failed pipelines), `.../pipelines/P/test_report_summary`, `.../pipelines/P/jobs?include_retried=true`, `.../jobs/J/artifacts` [28] | `PRIVATE-TOKEN` header. The parsed report keeps only the first `<testcase>` of a duplicate name [39], and pytest-rerunfailures writes failed attempts first, so read the raw artifact when reruns are on (inferred, not reproduced) |
| CircleCI | `/api/v2/insights/gh/ORG/REPO/flaky-tests`, `.../workflows/W/test-metrics?branch=main`, `/api/v2/project/gh/ORG/REPO/JOB/tests` [40] | `Circle-Token` header |
| Buildkite Test Engine | `/v2/analytics/organizations/ORG/suites/S/tests?period=28days&sort_by=reliability&order=asc&min_executions=20`, `.../tests/muted` [32] | Bearer token; `reliability` is passed ÷ (passed + failed) [32] |
| Jenkins JUnit plugin | `/job/JOB/N/testReport/api/json?tree=suites[cases[className,name,duration,status,age,failedSince]]` [41] | User and API token; not tested against a live server |

### Read JUnit dialects correctly

| Producer | How it writes reruns and identity | What results.py does |
| --- | --- | --- |
| pytest-rerunfailures | Every attempt is its own `<testcase>`; failed attempts have no `<failure>` child and come first; `tests` counts each test once (`tests="6"` for 9 elements) [10] | Counts a repeated ID in one file as a repeat, and as a rerun with `--repeats-are-reruns` or when a run_suite.py manifest has `reruns_configured`; keeps the last attempt's outcome and time |
| pytest xunit2, the default since 6.0 | No `file` or `line` [30] | Derives `path.py::Class::name` from `classname` in pytest reports, so mixed families join [10]; pass `--nodeids` when module names contain capitals |
| pytest xunit1 | `file` names the defining file, so a test imported into another module repeats `file` and `name` with another `classname` [10] | Takes the module from `classname`, so imports stay apart (checked on 11,831 real test cases) [10] |
| pytest-xdist | One merged file, no worker, and a test's attempts not adjacent [10] | Finds repeats wherever they are; reads workers from the report log instead |
| Maven Surefire | `flakyFailure`, `flakyError`: failed, then passed; `rerunFailure`, `rerunError`: failed every rerun; `time` from one attempt [12] | Counts reruns; outcome from `<failure>` |
| gotestsum `--rerun-fails` | A failed and a passed `<testcase>` with one name, failed first (read from source, not run) [42] | Rerun, final pass |
| jest-junit, unittest-xml-reporting | jest-junit omits `file` unless `addFileAttribute="true"` [43]; unittest-xml-reporting drops successful subtests [27] | `classname::name` IDs |

Run this check before you count JUnit repeats as reruns:

```sh
python3 - REPORT.xml... <<'EOF'
import collections, sys, xml.etree.ElementTree as ET
for path in sys.argv[1:]:
    root, seen = ET.parse(path).getroot(), collections.defaultdict(list)
    for tc in root.iter("testcase"):
        seen[(tc.get("file") or tc.get("classname"), tc.get("name"))].append(tc.get("classname"))
    repeats = [c for c in seen.values() if len(c) > 1]
    print(f"{path}: declared {sum(int(s.get('tests') or 0) for s in root.iter('testsuite'))}, elements {sum(map(len, seen.values()))}, "
          f"repeated IDs {len(repeats)}, in several classnames {sum(len(set(c)) > 1 for c in repeats)}")
EOF
```

More elements than declared tests, with repeats in one classname, means reruns. Equal counts with repeats in one classname means duplicate collection, and repeats in several classnames means imported tests. Fewer elements than declared tests means subtests.

### results.py summary, diff, and flips

```sh
for d in AUDIT/ci/*/*/; do
  run=$(basename "$(dirname "$d")"); cfg=$(basename "$d" | tr ' ' '_')
  find "$d" -name '*.xml' -print0 | xargs -0 python3 ${CLAUDE_SKILL_DIR}/scripts/results.py summary \
    --json-out "AUDIT/results/ci-$run-$cfg.json" > /dev/null
done
jq -r '[.tests, (.reruns | length), (.repeats | length), .sum_seconds, input_filename] | @tsv' AUDIT/results/ci-*.json | sort -n | head
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py diff --before OLDER_REPORTS... --after NEWEST_10_REPORTS... \
  --json-out AUDIT/results/window-diff.json
```

- The loop writes one JSON file per run and artifact, with every test's outcome, time, reruns, and repeats under `all_tests`; the `jq` line lists test counts, lowest first. Two shards with 26,358 tests took 0.3 s [10]. When CI reruns failed tests and the dialect check shows reruns, add `--repeats-are-reruns` to the `summary` call; `diff` and `flips` take the same flag. `summary` treats its inputs as one run. To summarise a whole run, pass all shards of one configuration in one call, and never mix matrix cells, which overwrite each other ("duplicate test ID across inputs"). After phase 5, add `--nodeids AUDIT/nodeids.txt` for exact node IDs.
- In `diff`, "largest regressions" are per-test median increases. Apply the 1.5-times and 0.5 s rule, because a 30 s test drifted by 1 s through noise alone on the synthetic history [10]. `passed -> failed` lines are tests that failed only in the newer window, and exit code 1 for a changed test set is normal between windows. The snippet below runs `flips --same-commit` once per group of the same code and configuration, so the flag is correct by construction. It passes any arguments after the script path on to `flips`, so add `--repeats-are-reruns` there under the same rule.

```sh
python3 - AUDIT/ci "${CLAUDE_SKILL_DIR}/scripts/results.py" <<'EOF'
import collections, json, pathlib, re, subprocess, sys
ci, results, extra = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3:]   # extra: flags for flips
(out_dir := ci.parent / "results" / "flips").mkdir(parents=True, exist_ok=True)
groups, flipped = collections.defaultdict(list), collections.defaultdict(set)
for meta_file in ci.glob("*/meta.json"):
    meta = json.loads(meta_file.read_text())
    code = f'run {meta["run_id"]}' if meta["event"] == "pull_request" else meta["sha"]   # a pull_request run tests a merge commit
    for xml in meta_file.parent.rglob("*.xml"):
        config = re.sub(r"-attempt-\d+$", "", xml.relative_to(meta_file.parent).parts[0])  # artifact = matrix cell
        groups[(code, config)].append(str(xml))
for n, ((code, config), files) in enumerate(sorted(groups.items())):
    out = out_dir / f"{n:05d}.json"
    subprocess.run([sys.executable, results, "flips", "--same-commit", *extra, *files, "--json-out", str(out)],
                   stdout=subprocess.DEVNULL, check=True)
    for row in json.loads(out.read_text())["flips"]:
        flipped[(row["id"], config)].add(code)
print(f"groups {len(groups)}, tests that flipped at one commit {len(flipped)}")
for (test, config), codes in sorted(flipped.items(), key=lambda kv: -len(kv[1]))[:25]:
    print(f"{len(codes):5} commits  {config}  {test}")
EOF
```

Within one report, `flips` counts a passed rerun as a flip when results.py sees it as a rerun: in report logs, Surefire output, run_suite.py runs with `reruns_configured`, and pytest JUnit XML with `--repeats-are-reruns`. Tests that flip in the same runs are one infrastructure event. On the source report's synthetic 60-run history, the snippet found the order-dependent test and the four-test outage cluster and skipped the real breakage. With `--repeats-are-reruns`, it also found the retry-masked test. Each pass took 3–4 s for 31 groups [10].

### Cross-run statistics

```sh
python3 - AUDIT/results/ci-*-CELL*.json <<'EOF'
import collections, json, statistics, sys
seq, secs, fails = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(set)
for path in sorted(sys.argv[1:]):                      # ci-RUNID-CONFIG.json names sort in run order
    for t in json.load(open(path)).get("all_tests", []):
        bad = t.get("outcome") in ("failed", "error")
        seq[t["id"]].append("F" if bad else "R" if t.get("reruns") else "P")
        secs[t["id"]].append(t.get("total", 0.0))
        if bad:
            fails[t["id"]].add(path)
for tid, s in sorted(seq.items(), key=lambda kv: kv[1].count("P") - len(kv[1]))[:15]:
    if s.count("P") < len(s):
        print(f"failed {s.count('F')}, passed on rerun {s.count('R')}, runs {len(s)}, "
              f"flip rate {sum(a != b for a, b in zip(s, s[1:])) / max(1, len(s) - 1):.2f}  {tid}")
spread = sorted(((statistics.median(v), sorted(v)[int(0.95 * (len(v) - 1))], k) for k, v in secs.items() if len(v) >= 20), key=lambda r: r[0] - r[1])
for p50, p95, tid in [r for r in spread if r[1] > 3 * r[0] and r[1] - r[0] >= 0.5][:10]:
    print(f"p50 {p50:.2f}s, p95 {p95:.2f}s  {tid}")
many, seen = {k: v for k, v in fails.items() if len(v) >= 3}, set()
for a in sorted(many, key=lambda k: -len(many[k])):
    group = [b for b in many if b not in seen and len(many[a] & many[b]) / len(many[a] | many[b]) >= 0.8]
    if len(group) > 1:
        seen.update(group)
        print(f"co-failing cluster: {len(group)} tests, {len(many[a])} failing runs, for example {group[:3]}")
EOF
```

It computes what results.py does not: flip rate, passed-on-rerun counts, p95 spread, and co-failing clusters. It takes reruns from the per-run JSON files, so pytest JUnit repeats count only when the summary loop used `--repeats-are-reruns`. Replace `CELL` with the artifact-name prefix of one matrix cell, so that all its shards are included and other cells are not. On the synthetic history, it gave the real breakage a flip rate of 0.02 and each flaky test 0.17, and it found the outage cluster. From summaries made with `--repeats-are-reruns`, it also counted the retry-masked test's 5 passed reruns [10]. Every harvested attempt counts as a run, and developers retry red runs, so failing commits contribute extra attempts: compute rates on first attempts, and use later attempts only for flips.

### Query analytics services

| Service | "Flaky" means | How to query |
| --- | --- | --- |
| CircleCI Insights | Failed and passed on the same commit within 14 days [40] | `/insights/.../flaky-tests` |
| Buildkite Test Engine | Passed on retry at one commit, or a transition score over a window [32] | `/v2/analytics/.../tests?sort_by=reliability` |
| Datadog Test Optimization | Flaky until 30 days pass without a flake, then "Fixed" [34] | Flaky-test and test-event endpoints [34], or read-only Model Context Protocol (MCP) tools |
| Codecov Test Analytics | A flake expires after 30 consecutive passes [25] | `/api/v2/github/OWNER/repos/REPO/test-analytics/?branch=main` [25] |
| Trunk Flaky Tests | Pass-on-retry, failure-rate, and failure-count monitors [33] | `/v1/tests/unhealthy`, `/v1/tests/quarantined`; parameters not verified [33] |
| Currents (Playwright and Cypress) | Did not pass on the first attempt; keeps aggregated metrics for 12 months [13] | `/v1/tests/PROJECT_ID?order=flakiness&min_executions=20` [13] |

- Copy each service's raw per-test counts, not only its "flaky" label, because the definitions above differ.
- An MCP server can expose the same data. A Datadog server, for example, has `get_datadog_flaky_tests` (sort by `failure_rate` or `pipelines_failed`), `search_datadog_test_events`, and `aggregate_datadog_test_events`, such as a count of `@test.is_retry:true` grouped by `@test.name`. Use read tools only; never call a tool that changes flaky-test states or retries jobs.
- Datadog's Auto Test Retries (5 per test) and Early Flake Detection (up to 10 retries of new tests) change job outcomes [34]. Trunk's `test` command rewrites exit codes for quarantined failures [33]. Account for both before you read job conclusions.

### Suite health metrics

| Metric | How to compute | Why it predicts pain |
| --- | --- | --- |
| First-attempt green rate | Runs whose first attempt passed ÷ runs, per workflow | What developers wait on; retries hide its drop |
| Retried-to-green share | Runs that needed a re-run to pass ÷ runs | Hidden flakiness, plus a full job's wait per retry |
| Rerun rate | Extra test attempts ÷ test executions | Retries turn red builds into slow builds [1] |
| Predicted green rate | Π(1 − pᵢ) over first-attempt failure rates, outage runs removed | 2,000 tests at 0.05% each give 37% (computed [4]), near Shopify's worked example of 35% [14]; a gap to the observed rate points at non-test causes |
| Flaky concentration | Share of flaky failures from the top 1% of flaky tests | A Pareto list tells you where to start [2] |
| Queue, overhead, and growth | Queue p95 ÷ run p95; non-test steps ÷ job time; tests and wall time per week | Faster tests cannot help when queueing or setup dominates; wall time growing faster than tests means tests get slower [5] |

### Statistics for rare failures

| Question | Formula | Answers (computed [4], rechecked [10]) |
| --- | --- | --- |
| Upper bound on the failure rate after n clean runs, 95% | `1 - 0.05 ** (1 / n)`, about 3/n | n = 30: 9.5%; 100: 2.95%; 170: 1.75%; 300: 0.99%; 1,000: 0.30% |
| Runs to see 1 failure with 95% / 99% probability | `ceil(log(1 - conf) / log(1 - p))` | Rate 5%: 59 / 90; 1%: 299 / 459; 0.1%: 2,995 / 4,603 |
| Interval for k failures in n runs | Wilson 95%: `(p + z²/2n ± z·sqrt(p(1 - p)/n + z²/4n²)) / (1 + z²/n)`, z = 1.96 | 1 in 50: 0.35–10.5%; 2 in 100: 0.55–7.0%; 10 in 1,000: 0.54–1.83% |
| Runs per side to show a drop (α 0.05, power 0.8) | Two-proportion sample size | 5% to 1%: 285; 2% to 0.5%: 861; 1% to 0.1%: 1,059 |
| Do x of f failures concentrate on a value with h of n runs? | One-sided Fisher: `sum(comb(h, k) * comb(n - h, f - k) for k in range(x, min(h, f) + 1)) / comb(n, f)` | All 5 of 5 failures on a shard with 20 of 60 runs: p = 0.0028, the same as SciPy; 4 of 5 gives 0.038, which misses p < 0.01 |
| What reruns find in Python [7] | Measured on 876,186 tests run 400 times | 10 reruns find at most 33% of flaky tests that are not order-dependent and 54% of order-dependent ones; finding 80% of the former takes 110 reruns on average, or 472 for 95% confidence; after a failure, 1 rerun checks at 95% confidence whether it was such a flake |

Write "not flaky" only as "failure rate below X at 95% confidence, from n clean runs". The formulas assume independent runs, so remove outage runs and co-failing clusters before you compute per-test rates, as Gruber et al. did [7]. When CI cannot produce enough runs of a test in reasonable time, prefer same-commit reruns ([flakiness.md](flakiness.md)) to waiting for history.

### What history can and cannot prove

| Claim | History supports it when | Evidence and confidence ([findings.md](findings.md)) |
| --- | --- | --- |
| Test X is flaky | It failed and passed at one commit and configuration, a passed rerun included | `history`; high at 2 or more commits, medium at one |
| Test X fails in about p of runs | You give the Wilson interval from first attempts | `history`; compare the interval with the 1% impact line |
| Test X is not flaky | Never; give "below 3/n at 95%" from n clean runs | – |
| Test X depends on order | Never alone; a shard or worker concentration is a hypothesis until reproduced | `history` at low confidence, then `measured` |
| Test X is slow | CI timings came from uninstrumented jobs | `history`; back timing claims with a `run_suite.py` run |
| Test X is useless because it never fails | Never ([traps.md](traps.md)) | Needs `mutation` and `coverage` evidence |
| An outcome change across commits is flakiness | Never ([traps.md](traps.md)) | – |
| The fix worked | Enough runs per side for the rates, or same-commit reruns; claimed fixes often fail this test [44] | `history` or `measured` |

## Tools

Versions and dates were checked on 2026-09-30 against PyPI's JSON API and GitHub releases [45].

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| GitHub CLI (`gh`) [46] | Runs, jobs, logs, artifacts, raw API calls | v2.102.0, 2026-09-30, maintained | Default `--limit` is 20; can prompt interactively without a run ID |
| pytest JUnit XML [30] | Per-test results in any CI | pytest 9.1.1, 2026-06-19, maintained | `xunit2` default omits `file`; reruns appear as pseudo-passes |
| pytest-reportlog [26] | Every report as JSON lines, with reruns and `worker_id` | 1.0.0, 2025-11-11, maintained | About 1.3 KB per test raw, 84 bytes gzipped |
| pytest-rerunfailures [11] | Retries; its output is telemetry | 16.7, 2026-09-17, maintained | `--fail-on-flaky`, `--max-suite-reruns`, `--only-rerun`, `-rR` |
| pytest-split [47] | `.test_durations`, a free timing source | 0.11.0, 2026-02-03, maintained (beta) | Stale files unbalance shards; keys are node IDs |
| Datadog Test Optimization [34] | Test events, flaky management, retries | ddtrace 4.15.3, 2026-09-30; datadog-ci v5.24.1, 2026-09-11; maintained | Paid; pytest 9 support not verified |
| Codecov Test Analytics [25] | Failure rate, flake rate, duration per test | codecov-cli 11.3.1, 2026-07-09, maintained | 60-day retention; JUnit XML only |
| Trunk Flaky Tests [33] | Flake detection and quarantine | trunk-analytics-cli 0.16.0, 2026-09-29, maintained | Paid; `test` rewrites exit codes |
| Buildkite Test Engine [32] | Reliability, duration, monitors | buildkite-test-collector 1.9.0, 2026-08-24, maintained | Paid; window capped by plan |
| Currents [13] | Playwright and Cypress analytics | @currents/cmd v1.11.0, 2026-09-24, maintained | Browser tests only; has its own MCP server |

## Evidence

- Google: 1.5% of test runs were flaky, 16% of tests showed some flakiness, 84% of pass-to-fail transitions involved flaky tests, and 2–16% of compute went to reruns [1][48]. A "fails three times in a row" rule turned a 15-minute signal into a 45-minute one [48].
- Google, Memon et al.: of 5.5 million test targets in a month, 91.3% never failed and 1.23% found a breakage; only 63,000 ever failed [9].
- GitHub: flaky builds fell from 1 in 11 commits to 1 in 200. Plain retries identified 25% of flaky failures, and three targeted retries identified 90%. Only 0.4% of flaky tests failed 100 times or more [2].
- Slack: main-branch stability rose from 19.82% to 96% and job failures fell from 56.76% to 3.85%; a suppressed test hid a real failure that reached main [20].
- Shopify: with 99.95% per-test pass rates, the Android suite passed 35% of the time, and retries raised a pipeline's pass rate from 31% to almost 90% [14]. In the core monolith, p95 CI time fell from 45 to 18 minutes, 68% of CI time was overhead, and the suite grew 20–30% a year [5].
- Spotify: publishing a flaky test table cut flakiness from 6% to 4% in two months [18].
- Dropbox: automated quarantine doubled quarantines and shrank the test cluster by about 8% [31].
- Atlassian: about 150,000 developer hours a year lost to reruns [3].
- Apple: flip-rate and entropy ranking cut flakiness 44% with under 1% loss of fault detection (abstract only) [21].
- Microsoft: several fixes that developers claimed did not reduce failure frequency when measured [44].
- Chromium: flaky tests revealed over a third of regression faults; a 99.2%-precision flakiness filter would have hidden about 76% of them [8].
- Python, Gruber et al.: 7,571 flaky tests (0.86%) in 22,352 projects; 59% order-dependent and 28% infrastructure; 170 runs for 95% confidence [7].
- Java, Parry et al.: 75% of flaky tests belonged to co-failing clusters with a mean size of 13.5 [6].

## Sources

1. https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/45880.pdf – Micco, "The State of Continuous Integration Testing @Google" (2017): 2–16% of compute on reruns.
2. https://github.blog/engineering/infrastructure/reducing-flaky-builds-by-18x/ – GitHub: an 18-fold reduction in flaky builds.
3. https://www.atlassian.com/blog/atlassian-engineering/taming-test-flakiness-how-we-built-a-scalable-tool-to-detect-and-manage-flaky-tests – Atlassian Flakinator (company numbers only).
4. Local experiments in the source research, 2026-09-30: Python 3.14.0, pytest 9.1.1, pytest-rerunfailures 16.7, pytest-xdist 3.8.0, pytest-split 0.11.0, and pytest-reportlog 1.0.0; report output with reruns and xdist, subtest counts, a 5,000-test size benchmark, computed statistics, and a live python/cpython harvest.
5. https://shopify.engineering/faster-shopify-ci – Shopify: p95 from 45 to 18 minutes, 68% overhead, the long tail.
6. https://arxiv.org/abs/2504.16777 – Parry et al., 2025: systemic flakiness and co-failure clusters.
7. https://arxiv.org/abs/2101.09077 – Gruber et al., ICST 2021: flaky tests in Python and rerun statistics.
8. https://arxiv.org/abs/2302.10594 – Haben et al., 2023: flaky tests reveal over a third of Chromium's regression faults.
9. https://research.google/pubs/taming-google-scale-continuous-testing/ – Memon et al., ICSE-SEIP 2017: 91.3% of targets never failed, 1.23% found breakages.
10. Checks made for this page, 2026-09-30 and 2026-10-01: pytest 9.1.1 with pytest-rerunfailures 16.7, pytest-xdist 3.8.0, pytest-reportlog 1.0.0, and pytest-split 0.11.0; gh 2.88.1; the skill's results.py and run_suite.py as of 2026-10-01, including a run_suite.py run with `reruns = 1` in pytest.ini; coloured and plain job logs; rerun, duplicate, imported-test, and mixed-family JUnit output; log formats; and every snippet on this page, run on the source research's synthetic 60-run history and on read-only harvests of python/cpython and home-assistant/core.
11. https://github.com/pytest-dev/pytest-rerunfailures – pytest-rerunfailures: `--fail-on-flaky`, `--max-suite-reruns`, `--only-rerun`.
12. https://maven.apache.org/surefire/maven-surefire-plugin/examples/rerun-failing-tests.html – Surefire reruns: `flakyFailure`, `rerunFailure`, timing rules, `failOnFlakeCount`.
13. https://docs.currents.dev/dashboard/tests/flaky-tests, https://docs.currents.dev/api/resources/tests-explorer, and https://docs.currents.dev/resources/data-privacy/data-retention – Currents flaky definition, Playwright `failOnFlakyTests`, test metrics API, and retention.
14. https://shopify.engineering/unreasonable-effectiveness-test-retries-android-monorepo-case-study – Shopify: retry arithmetic and pass-rate gains.
15. https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows – For `pull_request`, `GITHUB_SHA` is the last merge commit on `refs/pull/N/merge`.
16. https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs – Re-runs use the original `GITHUB_SHA` and `GITHUB_REF`, up to 30 days after the run.
17. https://research.google/pubs/assessing-transition-based-test-selection-algorithms-at-google/ – Leong et al., ICSE-SEIP 2019: transition-based selection underperforms.
18. https://engineering.atspotify.com/2019/11/test-flakiness-methods-for-identifying-and-dealing-with-flaky-tests/ – Spotify: Odeneye, Flakybot, 6% to 4%.
19. https://engineering.fb.com/2020/12/10/developer-tools/probabilistic-flakiness/ – Meta: probabilistic flakiness score.
20. https://slack.engineering/handling-flaky-tests-at-scale-auto-detection-suppression/ – Slack: automated flaky test detection and suppression.
21. https://2020.icse-conferences.org/details/icse-2020-Software-Engineering-in-Practice/2/Modeling-and-Ranking-Flaky-Tests-at-Apple – Kowalczyk et al., Apple, ICSE-SEIP 2020 (abstract): entropy and flip rate, 44% reduction.
22. https://docs.github.com/en/rest/actions/workflow-jobs – GitHub REST API for jobs: `filter=all`, timing and runner fields, and a job-log redirect that expires after one minute.
23. https://docs.github.com/en/actions/reference/workflows-and-actions/expressions – Status check functions: `success()` is the default; `if: ${{ !cancelled() }}` runs a step after failures.
24. https://github.com/actions/upload-artifact – upload-artifact: immutable artifacts since v4, `retention-days`; latest v7.0.1 (2026-04-10).
25. https://docs.codecov.com/docs/test-analytics and https://github.com/codecov/umbrella – Codecov Test Analytics setup (`junit_family=legacy`, 60-day retention) and source (`test-analytics` API, flake expiry after 30 consecutive passes).
26. https://github.com/pytest-dev/pytest-reportlog – pytest-reportlog.
27. https://github.com/xmlrunner/unittest-xml-reporting – unittest-xml-reporting and its Django runner.
28. https://docs.gitlab.com/api/pipelines/ and https://docs.gitlab.com/api/jobs/ – GitLab pipelines API (test report and summary) and jobs API (`include_retried`, `queued_duration`).
29. https://docs.github.com/en/actions/concepts/metrics – GitHub Actions performance metrics: run time, queue time, and failure rate for ranges of up to 100 days.
30. https://github.com/pytest-dev/pytest/blob/main/src/_pytest/junitxml.py and https://docs.pytest.org/en/stable/changelog.html – pytest's JUnit XML writer (families, `junit_duration_report`) and changelog (`xunit2` default since 6.0).
31. https://dropbox.tech/tech/2019/05/athena-our-automated-build-health-management-system – Dropbox Athena.
32. https://api.buildkite.com/v2/analytics/openapi.yaml and https://buildkite.com/docs/pipelines/configure/tests/workflows/monitors – Buildkite Test Engine API (reliability, muted tests) and monitors (transition count, passed on retry).
33. https://docs.trunk.io/flaky-tests/detection, https://docs.trunk.io/flaky-tests/reference/api-reference, and https://docs.trunk.io/flaky-tests/uploader – Trunk monitors, API endpoints, and the analytics CLI (`upload`, `validate`, `test`).
34. https://docs.datadoghq.com/api/latest/test-optimization/, https://docs.datadoghq.com/api/latest/ci-visibility-tests/, https://docs.datadoghq.com/tests/flaky_management/, https://docs.datadoghq.com/tests/flaky_test_management/early_flake_detection/, and https://docs.datadoghq.com/tests/flaky_test_management/auto_test_retries/ – Datadog flaky-test and test-event APIs, flaky test states and the 30-day "Fixed" rule, Early Flake Detection (up to 10 retries of new tests), and Auto Test Retries (5 per test).
35. https://docs.github.com/en/organizations/managing-organization-settings/configuring-the-retention-period-for-github-actions-artifacts-and-logs-in-your-organization – Artifact and log retention: 90 days by default, 1–90 for public and up to 400 for private repositories.
36. https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api – GitHub primary and secondary rate limits.
37. https://docs.github.com/en/rest/actions/workflow-runs and https://docs.github.com/en/rest/actions/artifacts – GitHub REST API for workflow runs (filters, attempts, the 1,000-result cap on filtered listings) and artifacts (per-run listings, `expired`).
38. https://docs.gitlab.com/user/gitlab_com/ – GitLab.com settings: 30-day artifact expiry and 500,000 test cases per report.
39. https://docs.gitlab.com/ci/testing/unit_test_reports/ – GitLab JUnit reports: size limits and the first-duplicate rule.
40. https://circleci.com/docs/api/v2/index.html and https://circleci.com/docs/guides/insights/insights-tests/ – CircleCI API v2 (flaky tests, test metrics from the 10 most recent runs, 90 days of insights) and Test Insights (flaky means failed and passed on one commit within 14 days).
41. https://plugins.jenkins.io/junit/ and https://javadoc.jenkins.io/plugin/junit/ – Jenkins JUnit plugin: latest version and `CaseResult` fields such as `age` and `failedSince`.
42. https://github.com/gotestyourself/gotestsum – gotestsum and its JUnit writer (`internal/junitxml/report.go`).
43. https://github.com/jest-community/jest-junit – jest-junit options and defaults.
44. https://www.microsoft.com/en-us/research/publication/a-study-on-the-lifecycle-of-flaky-tests/ – Lam et al., ICSE 2020: lifecycle of flaky tests at Microsoft.
45. https://pypi.org/pypi/PACKAGE/json – PyPI JSON API, used for every Python package version and date.
46. https://cli.github.com/manual/gh_run_list, https://cli.github.com/manual/gh_run_view, and https://cli.github.com/manual/gh_run_download – `gh run` flags and JSON fields.
47. https://github.com/jerry-git/pytest-split – pytest-split and its durations file.
48. https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html – Google: 1.5% of runs flaky, 16% of tests, 84% of transitions, the "three in a row" rule.
