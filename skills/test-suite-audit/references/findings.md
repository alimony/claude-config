# Findings: schema, scoring, and report

This page is the reference for `findings.json`. `scripts/findings.py` enforces every rule marked **enforced**, and it refuses to render a report while any finding breaks one.

## File layout

`findings.json` lives in the audit directory. The top level has these keys:

| Key | Required | Meaning |
| --- | --- | --- |
| `project` | yes | Project name for the report title. |
| `project_root` | yes | Absolute path of the checkout. File locations in evidence are relative to it. |
| `findings` | yes | The list of findings. |
| `not_measured` | no | Strings that say what you did not measure, and why. The report lists them. |

Put baseline metrics in `baseline.json` next to it. Use a flat object of metric name to value, for example `{"tests collected": 11873, "wall time, 4 workers (s)": 1843, "slowest 10% share of time": "61%", "tests with reruns in last 30 CI runs": 42}`. The report shows it as a table, and a later audit compares against it.

## Finding fields

| Field | Required | Values | Notes |
| --- | --- | --- | --- |
| `id` | yes | Unique string | Prefix by dimension: `TRU-`, `SPD-`, `FLK-`, `ADQ-`, `RED-`, `DES-`, `CI-`. **Enforced:** unique. |
| `title` | yes | Short phrase | Name the problem, not the fix. |
| `dimension` | yes | `trust`, `speed`, `flakiness`, `adequacy`, `redundancy`, `design`, `ci` | **Enforced.** |
| `claim` | yes | One falsifiable sentence | See "Writing the claim". |
| `trust_breaker` | no | `true` or `false` | Set it for tests that give false confidence. See "Trust breakers". |
| `scope` | no | `{"paths": [...], "tests_affected": N}` | `tests_affected` breaks ties. |
| `evidence` | yes | List, at least one item | **Enforced:** see "Evidence". |
| `impact` | yes, except for rejected findings | `{"level", "metric", "estimate", "range", "basis"}` | `level` is `high`, `medium`, or `low`. `basis` is `measured` (a run, or an exact count from the scan or the configuration), `extrapolated`, or `heuristic`. **Enforced.** |
| `effort` | yes | `S`, `M`, `L` | S is 2 hours or less, M is 2 days or less, L is more. **Enforced.** |
| `risk` | yes | `low`, `medium`, `high` | The risk that the change breaks something or loses protection. **Enforced.** |
| `confidence` | yes | `high`, `medium`, `low` | See "Confidence". **Enforced.** |
| `action` | no | `fix`, `speed-up`, `configure`, `add-tests`, `review-removal`, `merge`, `demote`, `investigate` | Removal-type actions need extra evidence. **Enforced.** |
| `recommendation` | yes | Text | Concrete: which file, which setting, which command. |
| `verification` | yes | Text | The command that proves the change worked, and the change you expect. |
| `status` | yes | `candidate`, `confirmed`, `rejected`, `done` | Keep rejected findings: the report lists them under "Checked and rejected". A rejected finding needs only `id`, `title`, `dimension`, `claim`, `evidence`, `status`, and `rejection_reason`. |

## Evidence

Each evidence item has a `kind` and cites at least one of `artifact`, `location`, or `test_id`. It can also carry `command`, `value`, `unit`, and `note`.

| Kind | Use it for |
| --- | --- |
| `measured` | A timing or an outcome from an uninstrumented `run_suite.py` run. **Enforced:** a speed finding cannot cite an instrumented run as `measured`. |
| `history` | CI reports, CI logs, or a test analytics service. |
| `static` | The scanner, ruff, or reading the code. |
| `coverage` | Coverage data, including per-test contexts. |
| `mutation` | Mutation testing results, including hand checks. |
| `config` | Configuration files: pytest, CI, tox, nox, or the project's settings. |
| `profile` | An instrumented run that ranks causes: a profiler, `-X importtime`, the leak probe, or the database probe. It never supplies a timing. **Enforced:** a speed finding whose impact `basis` is `measured` also needs `measured` or `history` evidence. |

| Kind | What it is | What it can support alone |
| --- | --- | --- |
| `measured` | A run you made through `run_suite.py` | Speed and outcome claims for that run's configuration |
| `history` | CI results or test analytics across many runs | Flakiness rates, duration trends, failure rates |
| `static` | Code or configuration read without running it | Structural facts: shadowed names, skip markers, missing asserts. Only hypotheses about runtime behaviour. |
| `coverage` | Coverage data, including per-test contexts | What code a test executes – never what it checks |
| `mutation` | Mutation testing results | Whether tests detect injected faults in the mutated code |
| `config` | Runner, CI, or tool configuration | Settings claims, such as "retries are on in CI" |

Rules, all **enforced**:

- An `artifact` path exists, relative to the audit directory or absolute.
- A `location` (`path:line`, relative to `project_root`) exists, and the line lies inside the file.
- A `test_id` appears in the audit's `nodeids.txt`, when that file exists. A parametrised ID matches its base name.
- A `speed` finding with `measured` evidence must not cite an instrumented run. That means coverage, mutation testing, a profiler, or `-X importtime`.
- A `flakiness` finding with only `static` or `config` evidence has `low` confidence.
- An `action` of `review-removal` or `merge` cites at least two different kinds among `coverage`, `mutation`, `history`, and `static`.
- An extrapolated impact cannot have `high` confidence.

## Confidence

| Level | Use it when |
| --- | --- |
| high | A full-suite measurement, a result reproduced at least twice, or a static fact confirmed at runtime (for example, a shadowed test absent from `nodeids.txt`). |
| medium | A single measurement, a measurement on a sample extrapolated to the suite, or a static fact not yet confirmed at runtime. |
| low | A pattern match or heuristic, such as a call to `datetime.now()` in a test. |

A low-confidence finding's recommendation is the cheapest step that would confirm or reject it. Do not recommend the fix itself.

## Impact

| Level | Speed | Reliability | Effectiveness |
| --- | --- | --- | --- |
| high | Saves at least 10% of wall time, or at least 10 minutes per CI run | Fails at least 1% of CI runs, or blocks merges weekly | Several surviving mutants in one function, a survivor in security or money logic, or no tests in the top decile of churn × complexity (with no usable history, such as a single commit, rank by complexity alone and say so) |
| medium | Saves 2–10% of wall time | Seen in history, less than 1% of runs | A single boundary survivor, or gaps in code that changes often |
| low | Less than 2% | Theoretical risk only | Gaps in stable or trivial code |

State the estimate in the unit the user cares about: minutes per CI run, CI minutes per week, or developer wait per push. Give a range when you extrapolated.

## Trust breakers

A trust breaker is a test, or a lack of one, that gives false confidence. Mark these with `"trust_breaker": true`:

- tests that never run: shadowed duplicate names, uncollectable classes, files the runner never collects, and tests behind a marker that every CI job excludes, with no scheduled job that runs them
- assertions that cannot fail: tautologies, asserts on non-empty tuples, asserts only inside `except`, and mock "assertions" that assert nothing
- tests that reach real external services, or production credentials in the test environment
- confirmed pollution: a test whose outcome depends on which tests ran before it
- a non-strict `xfail` test that currently passes (XPASS in a run), which hides a fixed bug or a broken test
- retries that hide a real failure, confirmed by history

An unconditional skip that CI reports as skipped is visible, so it is a stale-skip finding, not a trust breaker; a skip that hides tests from the skip count, such as a bare `@skip` or a skipping hook, is a trust breaker. For a trust breaker's impact, use high when the hidden tests guard security, money, or data integrity, or when they are more than 1% of the suite; otherwise medium. A test that fails and then passes on a rerun at one commit is flaky: report it under `flakiness`, with its failure rate. It becomes a trust breaker only when history shows that a retry hid a real failure.

## Priority

**Enforced**, and computed by `findings.py`:

1. **P0:** `trust_breaker` is true and confidence is `high` or `medium`.
2. For everything else, score = impact × confidence ÷ effort. Impact is high 3, medium 2, low 1. Confidence is high 1.0, medium 0.6, low 0.3. Effort is S 1, M 2, L 4.
3. **P1 (quick wins):** score of 1.5 or more, and confidence not `low`.
4. **P2:** score of 0.75 or more.
5. **P3:** everything else.

Within each priority, including P0, findings sort by the same score. Ties sort by lower risk, then by more tests affected. Rejected findings sort last and appear only under "Checked and rejected".

## Writing the claim

A claim is one sentence that a later measurement could prove false.

- Good: "The autouse fixture `reset_search_index` in `tests/conftest.py` adds about 0.4 s to each of 9,800 tests, about 65 minutes of the 110-minute serial run."
- Bad: "Fixtures are slow." There is no number and no location, and nothing could disprove it.
- Good: "`tests/test_api.py::test_refund` is defined twice, so the first definition (line 88) never runs."
- Bad: "There may be duplicate tests." Name them, or leave the finding out.

## Example

```json
{
  "id": "SPD-003",
  "title": "Function-scoped autouse fixture rebuilds the search index for every test",
  "dimension": "speed",
  "claim": "reset_search_index (tests/conftest.py:41) costs 0.41 s median per test and runs for all 9,812 tests, about 67 minutes of serial time.",
  "scope": {"paths": ["tests/"], "tests_affected": 9812},
  "evidence": [
    {"kind": "measured", "artifact": "runs/04-baseline/reportlog.jsonl", "command": "python3 scripts/results.py summary runs/04-baseline", "value": 4020, "unit": "s of setup time", "note": "setup is 38% of total test time"},
    {"kind": "static", "location": "tests/conftest.py:41", "note": "autouse=True, scope function"}
  ],
  "impact": {"level": "high", "metric": "minutes of serial test time per run", "estimate": 60, "range": [45, 67], "basis": "measured"},
  "effort": "M",
  "risk": "medium",
  "confidence": "high",
  "action": "speed-up",
  "recommendation": "Make the fixture session-scoped and reset only the documents a test writes, or opt in with a marker for the 300 tests that search.",
  "verification": "Run the baseline command 3 times before and after; results.py diff must show the same tests and outcomes and a lower median. Then run twice with -p randomly to catch new order dependence.",
  "status": "confirmed"
}
```

## The report

`findings.py report` renders `report.md` in this order:

1. Summary: counts per priority, the baseline table, and the first three P0 or P1 findings.
2. Trust breakers (P0), in full.
3. Quick wins (P1), in full.
4. Roadmap: a table of P2 and P3 findings, then their details.
5. Unverified candidates: the low-confidence findings, each with its cheapest check.
6. Not measured: from `not_measured`.
7. Checked and rejected.
8. Reproduce: every evidence command, once each.

Give the user the path to `report.md`, summarise the P0 and P1 findings in chat, and ask which ones to act on.
