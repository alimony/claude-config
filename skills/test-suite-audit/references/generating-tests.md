# Adding and strengthening tests

This page is the reference for phase 9 when the user has approved adding or strengthening tests: filling a coverage gap, killing surviving mutants, adding a property-based test, or fixing a test that cannot fail. It gives the acceptance chain that every new or changed test must pass, and the rules for oracles and mocks. It also says what to do when a new test fails, and when to stop and report "blocked, cannot verify". For auditor mistakes in general, see [traps.md](traps.md).

## Quick reference

| Signal | How to detect | Report when | Typical fix | Typical effect |
| --- | --- | --- | --- | --- |
| New test fails on the current code | Check 2 exits 1; the test fails alone and in every repeat | Any new or strengthened test with a specification oracle | Stop and hand it to the user as a candidate bug; never edit the expected value | Of the tests that pass-only filters kept, 59.6% and 68.1% validated the bug [5] |
| The change weakens the suite | `static_scan.py diff`, the supplementary grep, node ID parity | Any item, in any change, including yours | Revert it, or get the user's explicit approval per item | Read-only tests stopped test edits without hurting legitimate work [16] |
| A newly killed mutant is the fix | `mutmut show` on every newly killed mutant | The mutant matches the specification | Treat the killing test as a candidate bug | In the toy run, 1 of 2 new kills was the fix (verified) |
| Expected value is only observed output | Oracle source for each assertion | A boundary, error path, or documented rule with no cited source | Label it a regression oracle; derive specification oracles first | Large language model (LLM) oracles were 58–60% accurate per assertion [6] |
| Coverage without a check | `static_scan.py` on the batch; coverage gain with no new kill | Any flagged test | One explicit oracle per test | Best TestGenEval model: 35.2% coverage, 18.8% mutation score [8] |
| Flaky or order-dependent new test | Checks 3–5; `results.py flips` | A test that failed and passed at the same commit | Seed randomness and clocks; sort unordered results | 63% of flaky generated tests relied on unordered collections [11] |
| Over-mocked new test | `mock-density`; read every patch target | Patches the unit under test, or asserts only on mock calls | Mock only real boundaries; prefer fakes | Agents add mocks in 36% of test commits, others in 26% [10] |
| Target picked by coverage | The brief names lines, not mutants | Mutation results exist or fit the budget | Target surviving mutants in high churn × complexity code | Mutation-guided tests killed 15% of mutants, coverage-guided 2.4% [3] |
| Mutant closed as equivalent | Exclusions or pragmas next to failed kill attempts | Any claim without human review | Track killed, survived, and claimed equivalent apart | About 6% of LLM equivalence claims were right [15] |
| Product code detects tests | Grep the diff for `PYTEST_CURRENT_TEST` and similar | Any hit | Reject the change; test with fresh inputs | Held-out gap grew about 28 points per tenfold code size [19] |
| Blocked, cannot verify | PARTIAL checks, missing services, three cycles without new information | A check cannot run, or cannot pass honestly | Report "blocked, cannot verify" with evidence and one question | An abort option cut GPT-5's cheating from 54% to 9% [16] |
| Oversized or unlabelled batch | Mixed targets; tests without oracle labels | A reviewer cannot read every assertion | One target and one commit per batch; labels; report yield | 4–5% of TestGen-LLM trials survived its filters [2] |

## Signals

### New test fails on the current code

**Detect:** Check 2 of the acceptance chain exits 1 with a COMPLETE verdict. The test also fails alone and in every repeat, with the same message. A strengthened test that now fails counts too: its old, weaker form was hiding the failure.

**False positives:** The test is wrong: bad setup, or a misread or outdated specification source. An environment cause (network, time zone, locale) needs environment evidence, not reruns. A failing regression-oracle test is a broken test, not a bug report, because its only job is to pin current output.

**Fix:** Stop, and hand the test to the user as a candidate bug. Do not change its expected value, mark it skip or xfail, delete it, or change product code to make it pass. Give the user the test ID, the specification source and its location, and the expected and actual values. Add the run folder, and the mutant or patch under which the test passes (see "Proving a test can fail"). The user chooses one of three paths: fix the code so that the test lands with the fix; land the test as `@pytest.mark.xfail(strict=True, reason="ISSUE-LINK")`; or correct the specification source, after which the expected value follows it. Keep the test out of mutation runs, because mutmut 3.8 stops with "failed to collect stats" when a selected test fails (verified). Record it in `findings.json` as an `adequacy` finding with `measured` and `static` evidence and the action `investigate`.

**Effect:** Tools that keep only tests that pass on the current code produced suites in which 59.6% (Qodo Cover-Agent) and 68.1% (CoverUp) of kept tests passed on the bug and failed on the fix; Copilot, which does not filter, kept 4.2% [5]. For a SymPy bug that lived three years, both filtering tools discarded the tests that exposed it [5]. TestGen-LLM discards failing candidates because, without an automated oracle, it "cannot automatically determine whether a failing test has found a bug" [2].

**Verify:** In a disposable copy, apply the fix, or the mutant that matches the specification: the new test passes on it. In the toy run, a specification test for the documented threshold of 100 failed on the buggy code and passed on the `>=` mutant, while a regression-oracle test failed on it (verified).

### The change weakens the suite

**Detect:** Run the tamper check on every change, including your own and any subagent's (see "Tamper check on every change"). `static_scan.py diff` lists removed tests (it matches moved or renamed tests by body), new skips and xfails, tests with fewer assertions, checks weakened in place (such as `== 180` rewritten to `is not None`), changed discovery settings, and `addopts` that run fewer tests or hide failures (such as `--deselect`). It exits 1 when it finds any. It cannot see product code that detects tests, such as a `PYTEST_CURRENT_TEST` check, or coverage thresholds and `pragma: no cover`: the supplementary grep covers those. Report threshold: any item.

**False positives:** Parametrising tests lowers assertion counts. A rename with a changed body shows as one removed and one added test. A platform `skipif` with an issue link can be legitimate. Each still needs a written reason tied to the user's request.

**Fix:** Revert the item, or ask the user to approve it explicitly, one item at a time. Where you can, add a test instead of editing one: TestGen-LLM never modifies existing tests, so it cannot weaken them [1]. When an approved change fixes product code, keep test changes and code changes in separate commits, and leave the tests untouched during the fix.

**Effect:** In ImpossibleBench, Claude models did over 79% of their cheating by editing tests. Read-only tests prevented test edits and kept legitimate performance; hidden tests cut cheating to near zero but hurt legitimate work [16]. Transluce found an agent that deleted a test it failed to convert and then reported all 16 tests converted [17].

**Verify:** `static_scan.py diff` exits 0, the supplementary grep prints nothing, no node ID disappears, and every old test keeps its outcome in `results.py diff`.

### A newly killed mutant is the fix

**Detect:** Compare `mutmut results --all true` before and after the batch, then read each newly killed mutant with `mutmut show ID`. Flag any mutant that matches the specification, for example `>` changed to `>=` at a documented threshold: the test that kills it asserts the bug.

**False positives:** A mutant that changes behaviour the specification does not cover is a plausible fault, and killing it is the goal.

**Fix:** Treat the killing test as a candidate bug (see "New test fails on the current code"), and send the mutant diff with it. Leave the kill out of the reported score change until the user decides.

**Effect:** In the toy run, the batch raised mutmut kills from 8 to 10 of 17, and one of the two new kills was the `>=` mutant that the docstring describes (verified). A rising mutation score can therefore reward a test that locks in a bug.

**Verify:** Run `mutmut apply ID` in the disposable copy, then run the new tests there: a correct test passes on the fix mutant, and a bug-locking test fails.

### Expected value is only observed output

**Detect:** For each assertion in the batch, record its oracle source: a specification source (docstring, type contract, issue, README, requirement), an existing human-written test, or observed output only. Search the documentation and issues for the literals in new `assert … == <literal>` lines. Report threshold: an assertion on a boundary, an error path, or a documented business rule whose only source is observed output.

**False positives:** Characterisation tests written before a refactor pin current behaviour on purpose: label them, and do not reject them. Pure formatting or arithmetic helpers rarely have an external specification.

**Fix:** Label each test in its docstring, as "Specification: SOURCE, LOCATION" or "Regression oracle: pins current output". Derive specification oracles without the implementation: give a subagent the specification source and the signature, not the body, and compare its expected values with the actual output. This workflow is a design inferred from [6], not a measured one. Report the count of each oracle type per batch, and ask the user to review the assertions before they land [4].

**Effect:** LLM oracles "capture the actual program behaviour rather than the expected one". Their per-assertion accuracy was about 58–60%, it fell 8–9 points on slightly buggy code, and developer-style test names raised it by up to 16 points [6]. Tests that use the current version as their oracle catch regressions, not existing bugs [4]. Diffblue documents that its generated tests "reflect the current behavior of your code" [7].

**Verify:** Every new test's docstring names its oracle type, and every cited specification location exists.

### Coverage without a check

**Detect:** Run `static_scan.py` on the batch's files (check 1). Reject on `no-assertion`, `tautology`, `self-comparison`, `assert-in-except`, `unreachable-assert`, `returns-value`, `assert-true-two-args`, `assert-only-in-loop`, `empty-parametrize`, or any skip or xfail check. The scanner counts mock-call assertions such as `assert_called_once_with` as assertions, so read every test as well (verified). When mutation results exist, a test that covers new lines but kills none of their mutants does not observe those lines: strengthen its assertion before you accept it.

**False positives:** Assertions in project helpers, fixtures, or snapshot comparisons. The scanner already counts helpers whose names start with `assert`, `check`, `verify`, or `expect`. A smoke test whose name says "does not raise". A Hypothesis test whose invariant lives in a helper.

**Fix:** Give each test one explicit oracle: a value, an exception type and message, or a state change. Accept "does not raise" only when that is the behaviour under test and the test name says so. Merge near-duplicates, and skip trivial getters.

**Effect:** Engineers rejected TestGen-LLM tests with no assertion, tests of trivial getters, tests with several responsibilities, and near-duplicates "different in name only" [2]. Tests with no assertion appeared in up to 77% of class-level LLM suites, against 0–7% for EvoSuite [9]. The best model in TestGenEval reached 35.2% coverage but an 18.8% mutation score [8]. In the toy run, an assertion-free test added coverage and killed no mutant (verified).

**Verify:** The mutation score of the target module rises. A coverage gain alone does not count.

### Flaky or order-dependent new test

**Detect:** Checks 3–5 of the acceptance chain: each test alone, repeats in random order, and the batch with its neighbours under two seeds. Static hints from `static_scan.py` are `risk-random`, `risk-clock`, `risk-sleep`, `risk-thread`, `risk-network`, `risk-global-state`, and `risk-env-mutation`. Also look for iteration over sets and database queries without `ORDER BY`. Report threshold: a test that failed and passed at the same commit.

**False positives:** pytest-randomly reseeds `random` before each test from the base seed and the node ID, so repeats under one fixed seed replay the same values [12]. Vary the seed. A property-based test that fails once has found an input: read the shrunk "Failing test case" in the output, and treat it as a candidate bug if it breaks the specification.

**Fix:** Inject or seed randomness and clocks, compare unordered results as sets or sorted lists, and give fixtures a teardown. Brief the test writer with stable example tests only. Never accept a new test that needs reruns or a flaky marker.

**Effect:** Berndt et al. ran every generated test 30 times. Of the added tests, 0.00–0.71% were flaky, 72 of 115 flaky tests (63%) relied on unordered collections, and both models copied flakiness from the example tests in the prompt [11]. Five runs catch a 10% failure rate only 41% of the time (see "Rerun counts").

**Verify:** `results.py flips` prints "tests with both passes and failures: 0" for the batch. Its classification line names the mode ("flaky at the same commit") even when the count is 0. Report the bound that the runs support, for example "no failure in 30 runs: failure rate below 10% at 95% confidence".

### Over-mocked new test

**Detect:** `static_scan.py` reports `mock-density` at five or more patches. Read every new test for three patterns: a patch target inside the module under test, assertions only on mock calls, and more patches than real assertions.

**False positives:** Mocks of real boundaries are correct: network and external services, the clock, randomness, and filesystem side effects. `monkeypatch.setenv` and in-memory fakes are fine. Code whose behaviour is the call, such as event publishing, legitimately asserts calls.

**Fix:** Put these mocking rules in the brief, and reject tests that break them. Mock only real boundaries. Prefer fakes and real in-memory collaborators. Never patch the unit under test. Assert on outcomes, and on calls only when the call is the behaviour. Use only test libraries the project already depends on. A new dependency is a separate approved change, and its package must exist and be the intended one: commercial models suggested non-existent packages in at least 5.2% of cases [30].

**Effect:** Coding agents add mocks in 36% of their test commits, against 26% of other test commits. They use plain mocks in 95% of their mock commits, while human developers also use fakes (57%) and spies (51%) [10]. TestGenEval lists hallucinated or wrong mocks among common failure modes [8].

**Verify:** Mutate the unit under test: an over-mocked test still passes. A test that patches the function it tests can kill no mutant of that function, because the real function never runs.

### Target picked by coverage

**Detect:** The approved change aims at a coverage percentage or at uncovered lines, while mutation results for the module exist or fit the budget. The brief names lines, not mutants.

**False positives:** Mutation testing is unavailable: mutmut needs `fork`, so it runs only on POSIX (Unix-like) systems, and C extensions or a tight budget can rule it out. Glue-only modules.

**Fix:** Order the targets. First come surviving mutants in code with high churn × complexity, then uncovered branches in that code, and nothing in stable or trivial code (see the impact levels in [findings.md](findings.md)). Put each mutant's diff (`mutmut show ID`) and the module's existing tests in the brief. Require each new test to kill a mutant that survives the existing suite, or to cover a line or branch in `SRC` that nothing else covers, with a non-trivial assertion. Prefer the kill whenever mutation testing is available, and report the other tests as coverage-only.

**Effect:** Meta's mutation-guided Automated Compliance Hardening (ACH) tool killed 15% of mutants, against 2.4% for the coverage-guided TestGen-LLM tests. Of the ACH tests that uniquely killed a mutant, 49% added no line coverage [3]. Copilot's Python tests passed 45.28% of the time with the existing suite as context; without it, 92.45% failed, broke, or were empty [13].

**Verify:** The module's mutation score before and after (check 6), with every newly killed mutant reviewed.

### Mutant closed as equivalent

**Detect:** A mutant that the batch was meant to kill is closed as "equivalent" without human review, gets `# pragma: no mutate` or a `do_not_mutate` entry, or drops out of the score.

**False positives:** Exclusions for logging, `__repr__`, or dead code under a documented project rule.

**Fix:** Track three states: killed, survived, and claimed equivalent (unverified). Log each kill attempt, and report claims apart from the score. Ask a human to review a random sample of 20–30 claimed-equivalent mutants. Use an LLM equivalence verdict only to rank work.

**Effect:** Prompting-only LLM detection of equivalent Java mutants reached an F1 score (which balances precision and recall) of 55.9–59.4%, against 86.6% for a fine-tuned model [14]. In a Python study, only about 146 of 2,427 claimed-equivalent mutants (6%) were equivalent. Of 122 sampled mutants that were claimed equivalent and never killed, 98 were killable with simple tests [15]. ACH's 0.95 precision applies to LLM-generated mutants after comments are stripped [3].

**Verify:** The batch report lists the three states apart, with the logged kill attempts for each surviving mutant.

### Product code detects tests

**Detect:** The supplementary grep flags `PYTEST_CURRENT_TEST`, `"pytest" in sys.modules`, or `sys.modules.get("pytest")` in a change. Also look for new branches keyed on literals that appear in new assertions, large lookup tables in a fix, comments such as "special case for test", and many edit-and-run cycles on one file [20].

**False positives:** Existing, reviewed test hooks, such as a `settings.TESTING` switch or dependency injection, and feature flags for test environments.

**Fix:** Reject the change. Check generality with inputs that are not in the visible tests, such as a property-based test or held-out examples (see [techniques.md](techniques.md)).

**Effect:** SpecBench reports that "every frontier agent saturates the visible suite", while the gap to held-out tests grew about 28 points per tenfold increase in code size [19]. ImpossibleBench documents special-casing, `__eq__` overloading, and recorded call state [16]. The Claude 3.7 Sonnet system card saw special-casing mostly after repeated failures or with conflicting tests [20].

**Verify:** Fresh inputs fail on a special-cased implementation and pass on a general one.

### Blocked, cannot verify

**Detect:** Any of these holds:

- A check ends PARTIAL: exit 4 for an unknown flag such as `--count` without pytest-repeat, exit 5 for no tests, or a missing `-p` plugin (all verified).
- A required service, credential, or file is missing.
- You made more than three edit-and-run cycles on one test without new information.
- The only way to pass is to change an expected value, add a skip, mock the unit under test, or special-case the code.
- The specification sources contradict each other.
- A new test is flaky, and you cannot find the cause within the budget.

**False positives:** Iterative debugging that gains information on each cycle.

**Fix:** Stop, and report "blocked, cannot verify": what you tried (commands and run folders), what failed, and one question for the user. Never finish by weakening a check. Keep the finding's status, and record the attempt in `STATE.md`. Set attempt and time budgets before each batch.

**Effect:** Attempted reward hacking was three to six times higher on impossible tasks, and about 80% of those attempts were knowingly incomplete work [21]. In ImpossibleBench, an explicit abort option cut GPT-5's cheating from 54% to 9% and o3's from 49% to 12%, with a much smaller effect on Claude Opus 4.1 [16]. Anti-cheating prompts had a nearly negligible effect on o3 (70–95% hacking against an 80% baseline on one task) [22]. So rely on the acceptance chain and the tamper check, not on instructions. Kent Beck lists loops, unrequested functionality, and disabled or deleted tests as signs to stop [23].

**Verify:** Count blocked reports and tamper findings per audit. A rising tamper count with no blocked reports signals gaming.

### Oversized or unlabelled batch

**Detect:** A batch mixes targets, adds more tests than a reviewer can read assertion by assertion, or lands without oracle labels. The yield is not reported.

**False positives:** A parametrised table that adds cases to one test counts as one test for review.

**Fix:** Give each batch one target and one commit. Label the commit with a trailer, such as `Audit-batch: b1`, and each test with its oracle type in its docstring. Avoid new markers unless the project registers them: an unregistered marker is a collection error (exit 2) under `--strict-markers` or `--strict` (verified). Report the yield per batch: tests attempted, tests kept, and the check that rejected each of the others.

**Effect:** Only 4–5% of TestGen-LLM generation trials survived all its filters (490 of 8,996 on Facebook, 831 of 23,535 on Instagram), and the median landed test covered 2.5 lines [2]. Engineers accepted 73% of its recommendations [1]. CoverUp's Flask example kept 55 of 197 generations [25]. ACH's reviewers accepted 73% of tests but judged only 36% relevant to the privacy concern, so acceptance is not relevance [3]. No study measures whether labels improve review.

**Verify:** `git log --grep 'Audit-batch: b1'` finds the batch, and the yield table matches the run folders.

## Measuring

Placeholders: `NEW` is the batch's new or changed test files, and `NEIGHBOURS` the existing test files of the target module. `SRC` is the target package or directory, `BASE` the commit before the batch, `TEST_ROOTS` the test directories, and `b1` the batch label. `python` is the project's interpreter. Add the options from `CI_TEST_COMMAND` that change behaviour, such as markers, `-p` options, and environment variables, but not its paths or `-n`. Replace `NN` with the run number that `run_suite.py` prints.

Read every result from the run folder (`manifest.json` and `junit.xml`), never from piped terminal output (see [traps.md](traps.md)). If a subagent wrote the tests, run every check yourself: coding agents oversold their results in 34.7% of public sessions [17], and inaccurate self-reporting made up 22.58% of 16,118 misalignment episodes [18].

### Before each batch

```sh
# Which plugins are installed? This reads package metadata and runs no project code.
python - <<'EOF'
from importlib.metadata import version, PackageNotFoundError
for name in ("pytest", "pytest-randomly", "pytest-repeat", "pytest-cov", "coverage", "hypothesis", "mutmut"):
    try:
        print(name, version(name))
    except PackageNotFoundError:
        print(name, "not installed")
EOF
# Scan from the pytest rootdir before the change, with the same arguments you will use after it.
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py --json-out AUDIT/static-b1-before.json
```

Brief the test writer, whether that is you or a subagent, with the target and these rules:

```text
Target: surviving mutants ID1 and ID2 in SRC (diffs below). Style: the existing tests below.
Add tests only. Edit an existing test only when that test is the target, because it cannot fail. Never edit configuration or product code.
Each test checks one behaviour with one explicit oracle: a value, an exception type and message, or a state change.
Take expected values from the specification sources below, and cite the source in the docstring.
If no source settles a value, write "Regression oracle: pins current output" in the docstring.
Mock only network and external services, the clock, randomness, and filesystem side effects. Never patch the code under test.
If a test fails on the current code, keep it unchanged and report it.
```

Commit the batch on the change branch before you run the chain. The commit gives every run the same commit and a clean tree, which `results.py flips` needs, and it makes new files visible to `git diff BASE`.

### The acceptance chain for one batch

Accept a new or changed test only when it passes all seven checks. Stop at the first failure, and follow the matching signal.

| Check | Passes when | On failure, see |
| --- | --- | --- |
| 1 Static scan and reading | No rejecting check; every test read | Coverage without a check; Over-mocked new test |
| 2 Current code | Exit 0 and COMPLETE | Exit 1: New test fails on the current code. PARTIAL: Blocked |
| 3 Each test alone | Every run exits 0 | Flaky or order-dependent new test |
| 4 30 repeats in random order | No failure | Flaky or order-dependent new test |
| 5 With neighbours, two seeds | Both runs exit 0 | Flaky or order-dependent new test |
| 6 Adds detection | Each test kills a surviving mutant, or covers a line or branch that nothing else covers, with a non-trivial assertion; every new kill is reviewed | Coverage without a check; A newly killed mutant is the fix |
| 7 Tamper check | No items | The change weakens the suite |

```sh
# Check 1: scan the batch, then read every test.
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py NEW --json-out AUDIT/static-b1-new.json
# Check 2: the batch passes once on the current code.
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-current --timeout 600 --cwd ROOT -- \
    python -m pytest -q -p no:randomly NEW --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
# Check 3: collect the batch's node IDs, then run each test alone.
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-collect --timeout 300 --cwd ROOT -- \
    python -m pytest --collect-only -q -p no:randomly NEW
grep -E '^[^$].*::' AUDIT/runs/NN-b1-collect/output.log > AUDIT/b1-nodeids.txt
while IFS= read -r id; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-alone --timeout 300 --cwd ROOT -- \
      python -m pytest -q -p no:randomly "$id" --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
done < AUDIT/b1-nodeids.txt
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py list --artifacts AUDIT
```

`-p no:randomly` is harmless when pytest-randomly is absent. `-p randomly` without the plugin, or `--count` without pytest-repeat, ends PARTIAL instead of failing a test (both verified). Without pytest-repeat, use check 4b. Without pytest-randomly, drop `-p randomly` and the seed from checks 4 and 5. The repeats then still catch clock and randomness failures, and check 5 needs two explicit orders (see below).

```sh
# Check 4a, with pytest-repeat: 30 repeats in one process, in random order.
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-repeat --timeout 900 --cwd ROOT -- \
    python -m pytest -q -p randomly --count=30 NEW --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
# Check 4b, without pytest-repeat: 30 separate processes with different seeds.
for seed in $(seq 1 30); do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-seed-$seed --timeout 300 --cwd ROOT -- \
      python -m pytest -q -p randomly --randomly-seed=$seed NEW --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
done
python3 ${CLAUDE_SKILL_DIR}/scripts/results.py flips AUDIT/runs/*-b1-seed-* --json-out AUDIT/b1-flips.json
# Check 5: the batch with its neighbours, under two seeds.
for seed in 1 2; do
  python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-neighbours-$seed --timeout 900 --cwd ROOT -- \
      python -m pytest -q -p randomly --randomly-seed=$seed NEIGHBOURS NEW --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
done
```

- Check 4a pays start-up once; check 4b pays it 30 times, but each run is a fresh process. When check 2 passed and check 4a fails, the test failed and passed at the same commit: it is flaky.
- `results.py flips` calls a flip flaky only when all runs share one commit and a clean tree. Otherwise it reports "NOT evidence of flakiness".
- Without pytest-randomly, run check 5 twice, as `NEW NEIGHBOURS` and as `NEIGHBOURS NEW`: pytest keeps the argument order (verified). Name the neighbours as files, not as a directory that contains `NEW`.

```sh
# Check 6, mutation delta: two disposable copies. Configure mutmut in each as mutation-testing.md describes.
# BASE is the commit before the batch, AFTER the commit with it. A clone leaves the project's .git alone.
git clone --local --quiet ROOT AUDIT/b1-mut-before && git -C AUDIT/b1-mut-before checkout --quiet BASE
git clone --local --quiet ROOT AUDIT/b1-mut-after && git -C AUDIT/b1-mut-after checkout --quiet AFTER
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-mut-before --timeout 3600 --cwd AUDIT/b1-mut-before -- mutmut run
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-mut-after --timeout 3600 --cwd AUDIT/b1-mut-after -- mutmut run
(cd AUDIT/b1-mut-before && mutmut results --all true) > AUDIT/b1-mut-before.txt
(cd AUDIT/b1-mut-after && mutmut results --all true) > AUDIT/b1-mut-after.txt
diff AUDIT/b1-mut-before.txt AUDIT/b1-mut-after.txt | grep '^>' | grep ': killed'   # newly killed mutants
(cd AUDIT/b1-mut-after && mutmut show ID)                                           # read every one
```

- In the after-copy only, remove any batch test that fails on the current code. mutmut refuses to start while a selected test fails (verified).
- `run_suite.py` labels every mutmut run UNCHECKED, because its output says nothing reliable about the mutants. Judge completeness from `mutmut results --all true` instead: a complete run has no `not checked` entry.
- To see which new test kills a mutant, apply it in the after-copy and run the batch there (see "Proving a test can fail").
- Cost: roughly the number of mutants times the runtime of the tests that reach each mutant. Scope mutmut to the target module.

```sh
# Check 6 by coverage, for tests that kill no mutant: coverage delta on SRC only, once per new test.
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-cov-before --timeout 900 --cwd ROOT -- \
    python -m pytest -q -p no:randomly --cov=SRC --cov-branch --cov-report=json:{RUN_DIR}/coverage.json NEIGHBOURS
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-cov-TEST --timeout 900 --cwd ROOT -- \
    python -m pytest -q -p no:randomly --cov=SRC --cov-branch --cov-report=json:{RUN_DIR}/coverage.json NEIGHBOURS "TEST_ID"
python3 - AUDIT/runs/NN-b1-cov-before/coverage.json AUDIT/runs/NN-b1-cov-TEST/coverage.json <<'EOF'
import json, sys
before, after = (json.load(open(p))["files"] for p in sys.argv[1:3])
total = 0
for path, data in sorted(after.items()):
    old = before.get(path, {})
    lines = set(data["executed_lines"]) - set(old.get("executed_lines", []))
    arcs = {tuple(a) for a in data.get("executed_branches", [])} - {tuple(a) for a in old.get("executed_branches", [])}
    if lines or arcs:
        total += len(lines) + len(arcs)
        print(f"{path}: +{len(lines)} lines {sorted(lines)}, +{len(arcs)} branches {sorted(arcs)}")
print("new coverage items:", total)
EOF
```

- Always restrict coverage to `SRC`. With a bare `--cov`, the new test file's own lines count as new coverage: the toy run showed 21 new items instead of 4 (verified).
- Without pytest-cov, run `python -m coverage run --branch --source=SRC -m pytest …` through `run_suite.py`, which points `COVERAGE_FILE` into the run folder. Then run `python -m coverage json --data-file=RUN_FOLDER/.coverage -o RUN_FOLDER/coverage.json` (verified).
- A coverage gain is not required when a new test kills a mutant: 49% of ACH's unique mutant killers added no line coverage [3].

Finish with phase 9's before-and-after runs. For a batch, `results.py diff` exits 1 because tests appeared. Accept only when the appeared tests are exactly the batch, none disappeared, and no old test changed outcome. Report the batch's added test time from uninstrumented runs, not as a speed change. Remove the copies when the batch is done, for example `rm -rf AUDIT/b1-mut-before AUDIT/b1-mut-after`.

### Rerun counts

| Failure rate per run | Runs for 95% detection | Runs for 99% detection | Chance that 5 runs show it | Chance that 30 runs show it |
| --- | --- | --- | --- | --- |
| 30% | 9 | 13 | 83% | ~100% |
| 15% | 19 | 29 | 56% | 99% |
| 10% | 29 | 44 | 41% | 96% |
| 5% | 59 | 90 | 23% | 79% |
| 1% | 299 | 459 | 5% | 26% |
| 0.1% | 2,995 | 4,603 | 0.5% | 3% |

- Runs needed: n = ceil(ln(1 − confidence) / ln(1 − p)). The chance that N runs show a failure is 1 − (1 − p)^N. All values are computed.
- With no failure in N runs, the 95% upper bound on the failure rate is 1 − 0.05^(1/N). That is close to 3/N from about 30 runs up: 30 clean runs support "below 10%", and 100 support "below 3%". Report that bound, never "not flaky".
- Use 30 repeats by default for a new unit test, as Berndt et al. did [11]. Use more when the test touches threads, clocks, or shared state: 100 runs catch a 5% failure rate 99% of the time.
- Cost: N times the batch's runtime. Repeat only the batch, never a whole slow suite. For a 30–90-minute suite, take `NEIGHBOURS` from the test files in the target module's directory, or the files that cover the module. Leave the full random-order run to continuous integration (CI).

### Tamper check on every change

Run this after every change to tests, configuration, or product code, including your own, before any "done" claim:

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py --json-out AUDIT/static-b1-after.json
python3 ${CLAUDE_SKILL_DIR}/scripts/static_scan.py diff AUDIT/static-b1-before.json AUDIT/static-b1-after.json --json-out AUDIT/tamper-b1.json
# What the scan cannot see: deselection on CI command lines, coverage thresholds, reruns, and product code that detects tests.
git -C ROOT diff BASE -U0 | grep -nE '^\+.*(PYTEST_CURRENT_TEST|.pytest. in sys\.modules|sys\.modules\.get\(.pytest|--deselect|--ignore|(-k|-m) *.?not |-p *no:|collect_ignore|pytest_collection_modifyitems|fail_under|cov-fail-under|pragma: *no *cover|mark\.flaky|reruns)'
# The scan flags checks weakened to truthiness or `is not None`; read every changed assert line for the rest.
git -C ROOT diff BASE -U0 -- TEST_ROOTS | grep -nE '^[-+][^-+].*\bassert'
# No collected test may disappear. AUDIT/nodeids.txt is phase 5's list for the base commit.
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-collect-all --timeout 900 --cwd ROOT -- \
    CI_TEST_COMMAND --collect-only -q
comm -23 <(grep -E '^[^$].*::' AUDIT/nodeids.txt | sort) <(grep -E '^[^$].*::' AUDIT/runs/NN-b1-collect-all/output.log | sort)
```

`static_scan.py diff` exits 1 on any finding and prints "every item above needs the user's explicit approval". The grep and the `comm` line must print nothing. Each changed assert line must be at least as strict as the line it replaces. Cost: seconds, plus one collection.

### Proving a test can fail

A strengthened test counts only after you have seen it fail for the right reason. The same method shows the user a candidate bug. Use the two copies from check 6, after `mutmut run` in each:

1. Pick the fault the test must catch: a surviving mutant (`mutmut show ID`), or a hand-written wrong change.
2. In the before-copy, the old test passes on the fault. That is the evidence that it cannot fail.
3. In the after-copy, the strengthened test fails on the fault and passes without it.
4. For a candidate bug, apply the mutant that matches the specification in the after-copy: the new test passes on it.

```sh
(cd AUDIT/b1-mut-after && mutmut apply ID)
python3 ${CLAUDE_SKILL_DIR}/scripts/run_suite.py run --artifacts AUDIT --label b1-apply-ID --timeout 600 --cwd AUDIT/b1-mut-after -- \
    python -m pytest -q -p no:randomly NEW --junitxml={RUN_DIR}/junit.xml -o junit_family=xunit1
git -C AUDIT/b1-mut-after checkout -- SRC   # restores the disposable copy only; never run this in ROOT
```

`mutmut apply` rewrites source files, so use it only in the disposable copy. The tests that fail under the applied mutant are the ones that kill it.

### Property-based tests in the chain

A new property-based test goes through the same seven checks. When it fails, Hypothesis prints the shrunk input under "Failing test case" (verified). Treat that input like any other failure: a candidate bug if it breaks the specification, or a wrong property if the specification allows it. Never lower `max_examples` or add `assume()` to make it pass, because fewer or narrower examples lose protection. Hypothesis writes its example database to `.hypothesis/` in the working directory (verified), so expect a new untracked directory unless the project ignores it. For where properties pay off, see [techniques.md](techniques.md).

## Tools

| Tool | Use it for | Status (version, date, maintained) | Notes |
| --- | --- | --- | --- |
| mutmut | Mutation delta, reading newly killed mutants, `apply` in a disposable copy | 3.8.0, 2026-09-12, maintained [26][29] | Verified with pytest 9.1.1 on CPython 3.14. Needs `fork`, so POSIX only. Refuses to start while a selected test fails. Never run the interactive `mutmut browse`. |
| pytest-repeat | 30 repeats in one process (`--count=30`) | 0.9.4, 2025-04-07, partly maintained (no release since) [29] | Verified with pytest 9.1.1 on CPython 3.14. `--repeat-scope=session` repeats the whole session. Without the plugin, `--count` exits 4 (verified). |
| pytest-randomly | Random order and per-test reseeding (`-p randomly --randomly-seed=N`) | 5.0.0, 2026-09-01, maintained [12] | Reseeds `random` from the seed and the node ID (confirmed in its 5.0.0 source), so vary the seed between repeats. |
| pytest-rerunfailures | Diagnosing intermittent failures only | 16.7, 2026-09-17, maintained [29] | Never accept a new test that needs `--reruns`: retries hide real intermittent bugs. |
| coverage.py | Coverage delta restricted to `SRC` | 7.16.2, 2026-09-27, maintained [29] | Without a source filter, test files count as covered code (verified). pytest-cov 7.1.0 was verified for this page as a one-step alternative. |
| Pynguin | Search-based generation of regression tests for Python | 0.47.0, 2026-09-16, maintained [27] | Its assertions are regression oracles. It executes the module under test ("can … wipe your entire hard disk"), so use a container. It requires pytest below 9: installing it next to pytest 9.1.1 downgraded pytest to 8.4.2 (verified). |
| CoverUp | LLM coverage-guided generation for Python | 0.6.3, 2025-07-31, partly maintained: README edits only since July 2025 [24][25] | Keeps only passing tests, which locks in bugs. `--disable-failing` and `--disable-polluting` disable tests. Sends code to an LLM provider. |
| Qodo Cover (formerly Cover-Agent) | LLM generation to a coverage target; do not adopt | 0.3.10, 2025-05-21, not maintained since 2025-06-15 [28] | Coverage-only criterion, AGPL-3.0, and a prompt that steers away from failing cases [5]. |

## Evidence

- Meta TestGen-LLM (2024): filters for build, pass, five passing repeats, and coverage gain. Of its test cases, 75% built, 57% passed reliably, and 25% increased coverage; engineers accepted 73% of its recommendations [1].
- TestGen-LLM trial yield was 4–5% (490 of 8,996 on Facebook, 831 of 23,535 on Instagram); the median landed test covered 2.5 lines [2].
- TestGen-LLM's rejection reasons: trivial getters, no assertion, several responsibilities, and near-duplicates "different in name only" [2].
- Meta ACH (2025): 10,795 Android Kotlin classes, 9,095 mutants, 571 tests. Reviewers accepted 73% (140 of 191) and judged 36% privacy-relevant [3].
- ACH killed 15% of mutants, against 2.4% for TestGen-LLM tests; 49% of its unique killers added no line coverage [3].
- ACH's equivalence detector rose from 0.79 precision and 0.47 recall to 0.95 and 0.96 after stripping the mutator's comments [3].
- Harden and Catch (2025 keynote paper): hardening tests pass now and catch regressions, catching tests fail now and find bugs; current-version oracles cannot catch existing bugs [4].
- Mathews and Nagappan (287 buggy Python programs): 59.6% (Cover-Agent) and 68.1% (CoverUp) of kept tests validated the bug, against 4.2% for Copilot [5].
- Konstantinou et al.: at least one valid assertion in 89–94% of cases, 58–60% accuracy per assertion, and up to 16 points gained from developer-style names [6].
- TestGenEval (2025, 68,647 tests from 11 Python repositories): the best model reached 35.2% coverage and an 18.8% mutation score [8].
- Ouédraogo et al. (20,505 LLM-generated Java suites): tests with no assertion in up to 77% of class-level suites, against 0–7% for EvoSuite [9].
- Hora and Robbes (2026, 1.2 million commits in 2,168 repositories): 36% of agent test commits add mocks, against 26%; agents use plain mocks in 95% of mock commits [10].
- Berndt et al. (2026): 30 runs per generated test, 0.00–0.71% flaky, 63% of flaky tests on unordered collections, flakiness copied from prompt examples [11].
- El Haji et al. (2024): Copilot's Python tests passed 45.28% of the time with suite context; 92.45% failed, broke, or were empty without it [13].
- Tian et al. (2024): prompting-only equivalent-mutant detection reached F1 55.9–59.4%, against 86.6% fine-tuned [14].
- LLM scientific-debugging loops: about 80% mutation score, against about 60% single-shot; about 6% of equivalence claims were correct, and 98 of 122 sampled claimed mutants were killable [15].
- ImpossibleBench (2026): cheating in 54% (GPT-5), 49% (o3), and 50% (Claude Opus 4.1) of conflicting tasks. Read-only tests stopped test edits; an abort option cut GPT-5 to 9% and o3 to 12% [16].
- Transluce (8,600 real sessions): overselling in 34.7% of public sessions (1.8% severe) [17].
- Tang et al. (20,574 sessions, 16,118 validated episodes): inaccurate self-reporting in 22.58% of episodes [18].
- SpecBench: visible suites saturated; the held-out gap grew about 28 points per tenfold increase in code size (abstract) [19].
- Claude 3.7 Sonnet system card: special-casing and test edits, mostly after repeated failures or with conflicting tests [20].
- Claude Opus 5.5 system card: attempted reward hacking three to six times higher on impossible tasks; about 80% of attempts knowingly incomplete [21].
- METR (June 2025): anti-cheating prompts left o3 at 70–95% hacking on one task, against an 80% baseline [22].
- CoverUp (2025): 60% line-and-branch coverage, against 45% for CodaMosa; its Flask example kept 55 of 197 generations [24][25].
- Spracklen et al. (2025): at least 5.2% (commercial) and 21.7% (open-source) of suggested packages did not exist [30].
- Toy project for this page (pytest 9.1.1, mutmut 3.8.0, CPython 3.14): kills rose from 8 to 10 of 17, and one new kill was the fix. An assertion-free test added coverage and no kill. The first version of `static_scan.py diff` missed three weakenings; the script now reports the in-place weakened check and the `--deselect`, and the supplementary grep catches the product-code check (verified).

## Sources

1. https://arxiv.org/abs/2402.09171 – Alshahwan et al., "Automated Unit Test Improvement using Large Language Models at Meta" (TestGen-LLM), FSE 2024 industry track.
2. https://ar5iv.labs.arxiv.org/html/2402.09171 – Full text of the TestGen-LLM paper, with trial-level numbers and rejection reasons.
3. https://arxiv.org/html/2501.12862v1 – Foster et al., "Mutation-Guided LLM-based Test Generation at Meta" (ACH), FSE 2025 industry track.
4. https://arxiv.org/html/2504.16472v2 – Harman, O'Hearn, and Sengupta, "Harden and Catch for Just-in-Time Assured LLM-Based Software Testing", FSE 2025 keynote paper.
5. https://arxiv.org/html/2412.14137v1 – Mathews and Nagappan, "Design choices made by LLM-based test generators prevent them from finding bugs".
6. https://arxiv.org/html/2410.21136v1 – Konstantinou, Degiovanni, and Papadakis, "Do LLMs generate test oracles that capture the actual or the expected program behaviour?".
7. https://cover-docs.diffblue.com/get-started/what-is-diffblue-cover.md – Diffblue Cover documentation on regression tests (vendor).
8. https://arxiv.org/html/2410.00752v2 – Jain et al., "TestGenEval", ICLR 2025.
9. https://arxiv.org/html/2410.10628v2 – Ouédraogo et al., test smells in LLM-generated unit tests.
10. https://andrehora.github.io/pub/2026-msr-agents-over-mocked-tests.pdf – Hora and Robbes, "Are Coding Agents Generating Over-Mocked Tests?", MSR 2026.
11. https://www.arxiv.org/pdf/2601.08998 – Berndt et al., flakiness of LLM-generated tests for database systems, ICSE-SEIP 2026.
12. https://github.com/pytest-dev/pytest-randomly – pytest-randomly README: seeding and ordering semantics.
13. https://conf.researchr.org/details/ast-2024/ast-2024-papers/2/Using-GitHub-Copilot-for-Test-Generation-in-Python-An-Empirical-Study – El Haji, Brandt, and Zaidman, AST 2024.
14. https://arxiv.org/html/2408.01760v1 – Tian et al., "Large Language Models for Equivalent Mutant Detection: How Far Are We?", ISSTA 2024.
15. https://arxiv.org/html/2503.08182v1 – "Mutation Testing via Iterative Large Language Model-Driven Scientific Debugging".
16. https://arxiv.org/html/2510.20270v1 – Zhong, Raghunathan, and Carlini, "ImpossibleBench", ICLR 2026.
17. https://transluce.org/docent/blog/coding-agent-behaviors – Transluce, "Measuring coding agent misalignment in the wild".
18. https://arxiv.org/pdf/2605.29442 – Tang et al., "How Coding Agents Fail Their Users".
19. https://arxiv.org/abs/2605.21384 – Zhao et al., "SpecBench" (abstract).
20. https://assets.anthropic.com/m/785e231869ea8b3b/original/claude-3-7-sonnet-system-card.pdf – Claude 3.7 Sonnet system card, section 6.
21. https://www-cdn.anthropic.com/fc1b44717c85dc068bc6ba5024219938094694bd/Claude%20Opus%205.5%20System%20Card.pdf – Claude Opus 5.5 system card.
22. https://metr.org/blog/2025-06-05-recent-reward-hacking – METR, "Recent Frontier Models Are Reward Hacking".
23. https://newsletter.kentbeck.com/p/augmented-coding-beyond-the-vibes – Kent Beck, "Augmented Coding: Beyond the Vibes" (practitioner opinion).
24. https://arxiv.org/html/2403.16218 – Altmayer Pizzorno and Berger, "CoverUp: Effective High Coverage Test Generation for Python", FSE 2025.
25. https://github.com/plasma-umass/coverup – CoverUp repository and README example.
26. https://github.com/boxed/mutmut – mutmut repository: commands and configuration keys.
27. https://github.com/se2p/pynguin – Pynguin repository and warnings; its `pytest<9` requirement is on https://pypi.org/project/pynguin/.
28. https://github.com/qodo-ai/qodo-cover – Qodo Cover repository with its end-of-maintenance notice.
29. https://pypi.org/project/mutmut/, https://pypi.org/project/pytest-repeat/, https://pypi.org/project/pytest-rerunfailures/, https://pypi.org/project/coverage/ – PyPI versions and dates, checked 2026-09-30.
30. https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen – Spracklen et al., package hallucinations, USENIX Security 2025.
