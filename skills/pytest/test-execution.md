# pytest: Test Execution
Based on pytest 9.0.x documentation.

## Exit Codes

| Code | Enum                      | Meaning                                    |
|------|---------------------------|--------------------------------------------|
| 0    | `ExitCode.OK`             | All tests collected and passed             |
| 1    | `ExitCode.TESTS_FAILED`   | Tests were collected and run, some failed  |
| 2    | `ExitCode.INTERRUPTED`    | Test execution interrupted by user (Ctrl+C)|
| 3    | `ExitCode.INTERNAL_ERROR` | Internal error during execution            |
| 4    | `ExitCode.USAGE_ERROR`    | Command line usage error                   |
| 5    | `ExitCode.NO_TESTS_COLLECTED` | No tests were collected               |

```python
from pytest import ExitCode
# Use in scripts: ExitCode.OK, ExitCode.TESTS_FAILED, etc.
```

## Invoking pytest

```bash
# Equivalent invocations
pytest
python -m pytest          # also adds cwd to sys.path
```

### Programmatic invocation

```python
import pytest
exit_code = pytest.main()                         # returns ExitCode, no SystemExit
exit_code = pytest.main(["-x", "tests/"])         # pass CLI args as list
exit_code = pytest.main(["-x", "tests/"], plugins=[MyPlugin()])
```

## Test Selection

### By path and node ID

```bash
pytest tests/                                 # directory
pytest tests/test_login.py                    # single file
pytest tests/test_login.py::TestLogin         # class within file
pytest tests/test_login.py::TestLogin::test_valid  # specific method
pytest tests/test_login.py::test_standalone   # specific function
```

### By keyword expression (`-k`)

Matches against test name, parent names (file, class), markers, and attributes. Case-insensitive. Supports `and`, `or`, `not`, parentheses.

```bash
pytest -k "login"                         # anything containing "login"
pytest -k "login and not slow"            # login tests, excluding slow
pytest -k "login or signup"               # either
pytest -k "TestLogin and valid"           # class + method name
pytest -k "not integration"               # exclude by name
```

### By marker (`-m`)

```bash
pytest -m slow                            # only @pytest.mark.slow
pytest -m "not slow"                      # everything except slow
pytest -m "slow or integration"           # either marker
```

### Dry run (list without executing)

```bash
pytest --collect-only                     # full collection tree
pytest --co                               # short alias
pytest --co -q                            # quiet: just test IDs
```

## Test Discovery

### Default rules

1. Start from `rootdir` (or `testpaths` if configured)
2. Recurse into directories (skip `norecursedirs` like `.git`, `venv`, `node_modules`)
3. Collect files matching `python_files` (default: `test_*.py` and `*_test.py`)
4. Collect classes matching `python_classes` (default: `Test*`, no `__init__`)
5. Collect functions matching `python_functions` (default: `test_*`)

### Configuration in `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
norecursedirs = [".git", "node_modules", "venv", "migrations"]
```

### Import modes

| Mode        | sys.path change | Unique names required | Notes                    |
|-------------|----------------|-----------------------|--------------------------|
| `prepend`   | Inserts at front | Yes                  | Default. Classic behavior.|
| `append`    | Appends to end | Yes                   | Tests run against installed package. |
| `importlib` | No change      | No (auto-generated)   | Can't cross-import test modules. |

```toml
[tool.pytest.ini_options]
importmode = "importlib"   # or "prepend" (default), "append"
```

**Pitfall:** With `prepend` (default), if two test files in different directories have the same name and directories lack `__init__.py`, you get import collisions. Fix: add `__init__.py` to test directories or use `importlib` mode.

### conftest.py

- Discovered automatically during collection
- Fixtures and hooks defined in `conftest.py` apply to all tests in the same directory and below
- No need to import them -- pytest handles discovery
- Use `collect_ignore` and `collect_ignore_glob` lists in `conftest.py` to skip files

## Controlling Failures

### Stop early

```bash
pytest -x                    # stop after first failure
pytest --maxfail=3           # stop after 3 failures
```

### Re-run failed tests (cache plugin)

```bash
pytest --lf                  # (--last-failed) only re-run previously failed tests
pytest --ff                  # (--failed-first) run failures first, then the rest
pytest --nf                  # (--new-first) run new tests first, then the rest
```

#### When no failures exist

```bash
pytest --lf --lfnf=all       # (default) run all tests
pytest --lf --lfnf=none      # run nothing, exit immediately
```

`--lfnf` is short for `--last-failed-no-failures`.

### Stepwise mode

Fix failures one at a time. Runs until first failure, stops. On next run, resumes from where it stopped.

```bash
pytest --sw                  # (--stepwise) stop at first failure, resume next run
pytest --sw --sw-skip        # (--stepwise-skip) skip the first failing test, stop at next
```

### Cache management

```bash
pytest --cache-show          # show cache contents (don't run tests)
pytest --cache-show "cache/lastfailed"  # show specific cache key
pytest --cache-clear         # clear all cache before running
```

Cache is stored in `.pytest_cache/` directory (committed to VCS is fine; add to `.gitignore` if not wanted).

### Cache API (for plugins and fixtures)

```python
# In a fixture or plugin:
def test_something(request):
    cache = request.config.cache
    val = cache.get("my_plugin/key", default=None)   # JSON-serializable values
    cache.set("my_plugin/key", {"count": 42})
    d = cache.mkdir("my_plugin")                       # returns Path object
```

Values must be JSON-serializable. Use namespaced keys (`plugin_name/key`) to avoid collisions.

## Debugging Failures

```bash
pytest --pdb                 # drop into PDB on every failure
pytest -x --pdb              # drop into PDB on first failure, then stop
pytest --pdb --maxfail=3     # PDB for first 3 failures
pytest --trace               # drop into PDB at the START of every test
```

Using `breakpoint()` (Python 3.7+) or `import pdb; pdb.set_trace()` in code works automatically -- pytest disables output capture for that test.

## Output Control

### Verbosity

```bash
pytest -v                    # show individual test names + PASSED/FAILED
pytest -vv                   # more detail in diffs and output
pytest -q                    # quiet -- minimal output
pytest -q --no-header        # even quieter -- no header line
```

### Traceback style (`--tb`)

| Flag           | Output                                                    |
|----------------|-----------------------------------------------------------|
| `--tb=auto`    | **(default)** Long for first+last failure, short for rest |
| `--tb=long`    | Full, detailed tracebacks for all                         |
| `--tb=short`   | Shorter traceback format                                  |
| `--tb=line`    | One line per failure                                      |
| `--tb=native`  | Python stdlib formatting                                  |
| `--tb=no`      | No tracebacks at all                                      |
| `--full-trace` | Even longer than `--tb=long` (no truncation)              |

**Tip:** `--tb=short` is excellent for CI where you want failures visible but not overwhelming. `--tb=line` is useful for getting a quick count of what broke.

### Summary report (`-r`)

Controls the "short test summary info" section at the end. Pass character codes:

| Char | Meaning            |
|------|--------------------|
| `f`  | Failed             |
| `E`  | Error              |
| `s`  | Skipped            |
| `x`  | Xfailed (expected) |
| `X`  | Xpassed (unexpected) |
| `w`  | Warnings           |
| `p`  | Passed             |
| `P`  | Passed with output |
| `a`  | All except `p` and `P` |
| `A`  | All                |
| `N`  | None (disable)     |

Default is `fE`. Most useful:

```bash
pytest -ra              # show summary for everything except passed
pytest -rfs             # show failed + skipped summaries
pytest -rN              # disable short summary entirely
```

### Show captured output

```bash
pytest --show-capture=no       # hide captured stdout/stderr/log on failure
pytest --show-capture=stdout   # show only stdout
pytest --show-capture=stderr   # show only stderr
pytest --show-capture=log      # show only log
pytest --show-capture=all      # (default) show everything
```

### JUnit XML output

```bash
pytest --junitxml=report.xml                 # generate JUnit XML
pytest --junitxml=report.xml -o junit_suite_name=my_suite
```

#### Adding metadata to XML reports

```python
def test_something(record_property):
    record_property("example_key", 1)          # adds <property> child element
    assert True

def test_with_attr(record_xml_attribute):
    record_xml_attribute("assertions", "REQ-1234")  # adds XML attribute to <testcase>
    assert True

def test_suite_info(record_testsuite_property):
    record_testsuite_property("AGENT", "CI")   # adds to root <testsuite>
```

**Note:** `record_property` may break strict JUnit XML schema validation. `record_xml_attribute` is experimental.

## Stdout/Stderr Capture

### Capture methods

| Flag               | Level         | Captures                                          |
|--------------------|---------------|---------------------------------------------------|
| `--capture=fd`     | File descriptor | **(default)** OS-level FD 1 and 2. Catches C libs, subprocesses. |
| `--capture=sys`    | Python        | Only `sys.stdout` and `sys.stderr`.               |
| `--capture=tee-sys`| Python + pass-through | Captures sys-level AND echoes to real terminal. |
| `--capture=no`     | None          | No capture. Same as `-s`.                         |

```bash
pytest -s                  # shortcut for --capture=no
pytest --capture=tee-sys   # see output live AND capture it for failure reports
```

**Default behavior:** Output is captured. If a test fails, captured stdout/stderr is shown in the failure report. If a test passes, output is suppressed.

### Capture fixtures

Use these to inspect output programmatically within tests:

| Fixture           | Level     | Returns  | Use when                            |
|-------------------|-----------|----------|-------------------------------------|
| `capsys`          | sys       | `str`    | Testing print() output              |
| `capfd`           | fd        | `str`    | Testing fd-level writes (C extensions) |
| `capsysbinary`    | sys       | `bytes`  | Binary output on sys.stdout         |
| `capfdbinary`     | fd        | `bytes`  | Binary output on fd level           |

```python
def test_output(capsys):
    print("hello")
    captured = capsys.readouterr()     # returns namedtuple(out, err)
    assert captured.out == "hello\n"
    assert captured.err == ""

    print("world")
    captured = capsys.readouterr()     # resets buffer each call
    assert captured.out == "world\n"
```

### Temporarily disabling capture

```python
def test_with_debug_output(capsys):
    # Normal captured output
    print("this is captured")

    with capsys.disabled():
        # This prints to terminal even without -s flag
        print("this always shows (for debugging)")

    # Back to captured
    print("captured again")
    assert capsys.readouterr().out == "this is captured\ncaptured again\n"
```

### Pitfall: capsys vs capfd

- `capsys` only captures Python-level `sys.stdout`/`sys.stderr` writes
- `capfd` captures at the OS file descriptor level (catches output from C extensions, subprocesses)
- Use `capsys` for normal Python `print()` testing (most common)
- Use `capfd` only when you need to capture non-Python output

## Subtests (pytest 9.0+)

Subtests group multiple checks within a single test. Unlike parametrize, subtests are dynamic -- determined at runtime, not collection time. A failing subtest does NOT stop the rest of the test.

### Using the `subtests` fixture

```python
def test_even_numbers(subtests):
    for i in range(5):
        with subtests.test(msg=f"checking {i}", i=i):
            assert i % 2 == 0
# Reports: 3 passed, 2 failed (i=1 and i=3) -- all 5 run regardless
```

### With `unittest.TestCase.subTest()`

```python
import unittest

class TestArithmetic(unittest.TestCase):
    def test_even(self):
        for i in range(5):
            with self.subTest(i=i):
                self.assertEqual(i % 2, 0)
```

Pytest 9.0+ supports `unittest.TestCase.subTest()` natively. Previously this required the `pytest-subtests` plugin.

### Subtests vs parametrize

| Feature       | `@pytest.mark.parametrize` | `subtests`                     |
|---------------|----------------------------|--------------------------------|
| Known at collection | Yes                  | No (runtime only)              |
| Shows in `--co`     | Yes (separate items) | No                             |
| Can select with `-k` | Yes                 | No                             |
| Dynamic values | No (must be static)        | Yes                            |
| Failure isolation | Each is independent test | Subtest failure doesn't stop others |

**Use parametrize** when values are known upfront and you want independent test items.
**Use subtests** when values are computed dynamically or you want grouped assertions.

## Disabling Plugins

```bash
pytest -p no:cacheprovider   # disable cache plugin
pytest -p no:doctest         # disable doctest collection
pytest -p no:warnings        # disable warnings plugin
```

## Quick Reference: Most Useful Flag Combos

| Scenario                               | Command                              |
|----------------------------------------|--------------------------------------|
| Run one test, verbose                  | `pytest path/to/test.py::test_name -v` |
| Re-run only failures                   | `pytest --lf`                        |
| Re-run failures first                  | `pytest --ff`                        |
| Stop on first failure                  | `pytest -x`                          |
| Debug first failure                    | `pytest -x --pdb`                    |
| Fix failures one by one                | `pytest --sw`                        |
| Quiet CI output                        | `pytest -q --tb=short -ra`           |
| See all output live                    | `pytest -s`                          |
| See output live + capture for report   | `pytest --capture=tee-sys`           |
| See print output on failure only       | (default behavior, no flags needed)  |
| List tests without running             | `pytest --co -q`                     |
| Run with JUnit XML for CI              | `pytest --junitxml=report.xml`       |
| Clear cache and run all                | `pytest --cache-clear`               |
| Show what's in cache                   | `pytest --cache-show`                |

## Common Pitfalls

1. **Duplicate test file names without `__init__.py`:** With default `prepend` import mode, `tests/a/test_utils.py` and `tests/b/test_utils.py` collide. Fix: add `__init__.py` to each directory, or use `importmode = "importlib"`.

2. **Tests not discovered:** Check `python_files`, `python_classes`, `python_functions` in config. Class-based tests must not have `__init__`. Functions must start with `test_`.

3. **`capsys` doesn't capture subprocess output:** Use `capfd` instead -- it captures at the OS file descriptor level.

4. **`--lf` runs everything:** If cache has no recorded failures (first run, or after `--cache-clear`), `--lf` defaults to running all tests. Use `--lfnf=none` to change this.

5. **`-s` disables ALL capture:** This means failure reports won't include captured output either. Prefer `--capture=tee-sys` if you want both live output and captured failure reports.

6. **`readouterr()` resets the buffer:** Each call returns output since the last call (or test start). Call it at the right moment, and know that calling it twice gives different results.

7. **`--tb=auto` hides middle tracebacks:** In long chains of failures, only first and last get full tracebacks. Use `--tb=long` if you need them all.
