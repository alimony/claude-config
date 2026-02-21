# pytest: Integration and Advanced Patterns
Based on pytest 9.0.x documentation.

## unittest Integration

### Running unittest Tests with pytest

pytest discovers `unittest.TestCase` subclasses in `test_*.py` / `*_test.py` files automatically:

```bash
pytest tests/
```

### Supported unittest Features

| Feature | Supported |
|---------|-----------|
| `setUp()` / `tearDown()` | Yes |
| `setUpClass()` / `tearDownClass()` | Yes |
| `setUpModule()` / `tearDownModule()` | Yes |
| `skip()` / `skipIf()` decorators | Yes |
| `subTest()` | Yes (since pytest 9.0) |
| `load_tests` protocol | No |

### Benefits of Running unittest via pytest

Without modifying existing code you get:
- Better tracebacks with assertion introspection
- stdout/stderr capturing
- `-k` and `-m` selection flags
- `--pdb` for debugging failures
- `pytest-xdist` parallel execution
- Plain `assert` instead of `self.assert*` (use `unittest2pytest` to convert)

### What Works in unittest.TestCase Subclasses

| pytest Feature | Works? |
|----------------|--------|
| `@pytest.mark.skip` / `skipif` / `xfail` | Yes |
| Autouse fixtures | Yes |
| Regular fixtures (as arguments) | No |
| Parametrization | No |
| Custom hooks | No |

### Mixing Fixtures into unittest.TestCase

Use `@pytest.mark.usefixtures` to attach fixtures to test classes. Fixtures set attributes via `request.cls`:

```python
# conftest.py
import pytest

@pytest.fixture(scope="class")
def db_class(request):
    class DummyDB:
        pass
    request.cls.db = DummyDB()

# test_example.py
import unittest
import pytest

@pytest.mark.usefixtures("db_class")
class MyTest(unittest.TestCase):
    def test_has_db(self):
        assert hasattr(self, "db")
```

### Autouse Fixtures in unittest.TestCase

Define autouse fixtures as methods on the test class. They can receive other pytest fixtures as arguments even though test methods cannot:

```python
import unittest
import pytest

class MyTest(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def initdir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        tmp_path.joinpath("data.txt").write_text("hello", encoding="utf-8")

    def test_reads_file(self):
        with open("data.txt", encoding="utf-8") as f:
            assert f.read() == "hello"
```

**Key limitation:** `unittest.TestCase` test methods cannot receive fixture arguments directly. Use `autouse=True` or `@pytest.mark.usefixtures()` instead.

**Timing note:** Setup and teardown for unittest-based tests runs during the *call* phase, not pytest's standard setup/teardown stages. Errors in unittest setUp appear as call-phase errors.

---

## xunit-style Setup/Teardown

Classic setup/teardown functions that run at module, class, method, or function scope. These are supported alongside pytest fixtures and can be mixed in the same file.

### Quick Reference

| Scope | Setup | Teardown | Runs |
|-------|-------|----------|------|
| Module | `setup_module(module)` | `teardown_module(module)` | Once per module |
| Class | `setup_class(cls)` (classmethod) | `teardown_class(cls)` (classmethod) | Once per class |
| Method | `setup_method(self, method)` | `teardown_method(self, method)` | Per test method |
| Function | `setup_function(function)` | `teardown_function(function)` | Per test function |

All parameters are optional (since pytest 3.0).

### Module Level

```python
def setup_module(module):
    """Called once before all tests in this module."""

def teardown_module(module):
    """Called once after all tests in this module."""
```

### Class Level

```python
class TestSomething:
    @classmethod
    def setup_class(cls):
        """Called once before all methods in this class."""

    @classmethod
    def teardown_class(cls):
        """Called once after all methods in this class."""
```

### Method Level (inside classes)

```python
class TestSomething:
    def setup_method(self, method):
        """Called before each test method."""

    def teardown_method(self, method):
        """Called after each test method."""
```

### Function Level (module-level tests)

```python
def setup_function(function):
    """Called before each test function in the module."""

def teardown_function(function):
    """Called after each test function in the module."""
```

### Important Rules

- Teardown is **not called** if the corresponding setup failed or was skipped.
- xunit-style functions now obey fixture scope rules (since pytest 4.2).
- **Prefer fixtures over xunit setup** for new code -- fixtures support dependency injection and are more composable.

---

## Existing Test Suite Migration

### Getting Started

```bash
cd <project>
pip install -e .          # install project in dev mode
pip install pytest
pytest tests/             # run existing tests
```

Development mode (`pip install -e .`) avoids reinstalling after every code change and is more reliable than `sys.path` manipulation.

### Incremental Migration Strategy

1. **Start by just running with pytest** -- most unittest suites work immediately.
2. **Use plain `assert`** -- replace `self.assertEqual(a, b)` with `assert a == b`. The `unittest2pytest` tool automates this.
3. **Add autouse fixtures** gradually alongside existing setUp/tearDown.
4. **Convert classes to plain functions** where inheritance isn't needed.
5. **Adopt parametrize** to replace loops or repeated test methods.

### Do This / Don't Do This

```python
# Do: plain assert (pytest gives rich diffs automatically)
assert result == expected

# Don't: unittest assertion methods (less informative outside unittest runner)
self.assertEqual(result, expected)

# Do: pytest.raises context manager
with pytest.raises(ValueError, match="invalid"):
    parse(bad_input)

# Don't: unittest assertRaises (less expressive)
self.assertRaises(ValueError, parse, bad_input)
```

---

## CI/CD Patterns

### CI Detection

pytest detects CI environments via these environment variables:

| Variable | Used By |
|----------|---------|
| `CI` | Most CI systems (GitHub Actions, GitLab CI, etc.) |
| `BUILD_NUMBER` | Jenkins |

When CI is detected, short test summary info is **not truncated** to terminal width.

### JUnit XML Output

Generate JUnit XML for CI tools (Jenkins, GitHub Actions, Azure Pipelines, etc.):

```bash
# Basic JUnit XML
pytest --junit-xml=results.xml

# With custom test suite name
pytest --junit-xml=results.xml -o junit_suite_name=my_suite

# Include system-out/system-err capture
pytest --junit-xml=results.xml -o junit_logging=system-out
```

### Parallel Execution with pytest-xdist

```bash
pip install pytest-xdist

# Auto-detect CPU count
pytest -n auto

# Specific worker count
pytest -n 4

# With JUnit XML (each worker writes its own, merged automatically)
pytest -n auto --junit-xml=results.xml

# Load balancing strategy
pytest -n auto --dist=loadscope    # group by module/class
pytest -n auto --dist=loadfile     # group by file
pytest -n auto --dist=worksteal    # work-stealing (best for uneven test times)
```

### GitHub Actions Example

```yaml
- name: Run tests
  run: |
    pytest --junit-xml=test-results.xml -n auto -v
  env:
    CI: true

- name: Publish test results
  uses: dorny/test-reporter@v1
  if: always()
  with:
    name: Test Results
    path: test-results.xml
    reporter: java-junit
```

### Useful CI Flags

| Flag | Purpose |
|------|---------|
| `--junit-xml=FILE` | JUnit XML report for CI ingestion |
| `-n auto` | Parallel execution (needs pytest-xdist) |
| `--tb=short` | Shorter tracebacks in CI logs |
| `-q` | Quieter output |
| `--strict-markers` | Fail on unknown markers (catches typos) |
| `-x` or `--maxfail=N` | Fail fast |
| `--timeout=N` | Per-test timeout (needs pytest-timeout) |
| `-p no:cacheprovider` | Disable cache (useful in ephemeral CI) |

---

## Flaky Tests

### What Makes Tests Flaky

A flaky test passes sometimes and fails sometimes with no code change. Common causes:

| Cause | Example |
|-------|---------|
| **Shared state** | Test relies on data left by another test |
| **Test ordering** | Passes alone, fails in suite (or vice versa) |
| **Timing/races** | Thread safety, network timeouts, `time.sleep` |
| **Floating point** | `assert 0.1 + 0.2 == 0.3` fails |
| **Global state** | Environment variables, singletons, module-level caches |

### Identifying Flaky Tests

```bash
# Run tests in random order to expose ordering dependencies
pip install pytest-randomly
pytest -p randomly

# Find the current test that is stuck
# Check: PYTEST_CURRENT_TEST environment variable is set during test execution

# Repeat tests to expose intermittent failures
pip install pytest-flakefinder
pytest --flake-finder --flake-runs=10
```

### Managing Flaky Tests

```python
# Quarantine: mark as expected failure (won't break CI)
@pytest.mark.xfail(strict=False, reason="Flaky: intermittent timeout")
def test_external_api():
    ...

# Auto-retry (pip install pytest-rerunfailures)
@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_sometimes_fails():
    ...
```

**Command-line retry:**
```bash
pip install pytest-rerunfailures
pytest --reruns 3 --reruns-delay 1
```

### Fixing Flaky Tests

| Strategy | How |
|----------|-----|
| **Use `pytest.approx()`** | `assert result == pytest.approx(3.14, abs=1e-6)` |
| **Isolate state** | Use fixtures with proper teardown, avoid module-level state |
| **Mock time** | Use `freezegun` or `time-machine` instead of real delays |
| **Mock external services** | Don't hit real APIs in unit tests |
| **Make thread tests deterministic** | Use events/barriers instead of sleeps |
| **Split test suites** | Separate fast unit tests from slow integration tests |

### Useful Plugins for Flakiness

| Plugin | Purpose |
|--------|---------|
| `pytest-rerunfailures` | Auto-retry failed tests |
| `pytest-randomly` | Randomize test order to expose dependencies |
| `pytest-flakefinder` | Repeat tests N times to find intermittent failures |
| `pytest-replay` | Reproduce exact test ordering from CI runs |
| `pytest-timeout` | Kill tests that hang |

---

## Custom Test Discovery

### Changing Naming Conventions

Override default `test_*.py` / `Test*` / `test_*` patterns in config:

```toml
# pyproject.toml
[tool.pytest.ini_options]
python_files = ["check_*.py", "test_*.py"]
python_classes = ["Check", "Test"]
python_functions = ["*_check", "test_*"]
```

**Note:** `python_functions` and `python_classes` have no effect on `unittest.TestCase` discovery -- pytest delegates that to unittest.

### Ignoring Paths

```bash
# Command line
pytest --ignore=tests/legacy/ --ignore=tests/slow/

# Glob-based ignore
pytest --ignore-glob='*_legacy.py'
```

### Deselecting Individual Tests

```bash
pytest --deselect=tests/test_api.py::test_slow_endpoint
```

### Controlling Directory Recursion

```toml
# pyproject.toml
[tool.pytest.ini_options]
norecursedirs = [".svn", "_build", "tmp*", "node_modules", ".venv"]
```

### Dynamic Ignore via conftest.py

```python
# conftest.py
import sys

collect_ignore = ["setup.py"]
if sys.version_info < (3, 10):
    collect_ignore.append("tests/py310_only/")
```

### Collecting from All Python Files

```toml
# pyproject.toml
[tool.pytest.ini_options]
python_files = ["*.py"]
```

Combine with `collect_ignore` in `conftest.py` to exclude non-test files.

### Interpreting Arguments as Packages

```bash
# Run tests from an installed package
pytest --pyargs mypackage.tests.test_core
```

### Inspecting the Collection Tree

```bash
pytest --collect-only           # show what would be collected
pytest --collect-only -q        # compact listing
```

---

## Custom Collectors

### Non-Python Test Files (e.g., YAML)

Create custom `pytest.File` and `pytest.Item` subclasses in `conftest.py`:

```python
# conftest.py
import pytest
import yaml

def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml" and file_path.name.startswith("test"):
        return YamlFile.from_parent(parent, path=file_path)

class YamlFile(pytest.File):
    def collect(self):
        raw = yaml.safe_load(self.path.open(encoding="utf-8"))
        for name, spec in sorted(raw.items()):
            yield YamlItem.from_parent(self, name=name, spec=spec)

class YamlItem(pytest.Item):
    def __init__(self, *, spec, **kwargs):
        super().__init__(**kwargs)
        self.spec = spec

    def runtest(self):
        for name, value in sorted(self.spec.items()):
            if name != value:
                raise YamlException(self, name, value)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, YamlException):
            return f"spec failed: {excinfo.value.args[1]!r}: {excinfo.value.args[2]!r}"
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, 0, f"usecase: {self.name}"

class YamlException(Exception):
    pass
```

Key methods to implement on `pytest.Item`:
- `runtest()` -- execute the test
- `repr_failure(excinfo)` -- format failure output
- `reportinfo()` -- return `(path, lineno, description)` for test location

### Custom Directory Collector

Override how directories are traversed using `pytest_collect_directory`:

```python
# conftest.py
import json
import pytest

class ManifestDirectory(pytest.Directory):
    def collect(self):
        manifest = json.loads(
            (self.path / "manifest.json").read_text(encoding="utf-8")
        )
        for file in manifest["files"]:
            yield from self.ihook.pytest_collect_file(
                file_path=self.path / file, parent=self
            )

@pytest.hookimpl
def pytest_collect_directory(path, parent):
    if path.joinpath("manifest.json").is_file():
        return ManifestDirectory.from_parent(parent=parent, path=path)
    return None  # fall back to default behavior
```

Default collectors: `pytest.Package` (directories with `__init__.py`), `pytest.Dir` (other directories).

---

## Session-Scoped Fixtures Inspecting Collected Tests

A session-scoped fixture can access all collected test items via `request.node.items`:

```python
# conftest.py
import pytest

@pytest.fixture(scope="session", autouse=True)
def call_class_setup(request):
    """Call .callme() on any test class that defines it, before tests run."""
    seen = {None}
    session = request.node
    for item in session.items:
        cls = item.getparent(pytest.Class)
        if cls not in seen:
            if hasattr(cls.obj, "callme"):
                cls.obj.callme()
            seen.add(cls)
```

Use cases:
- Pre-flight checks before the suite runs
- Dynamic test configuration based on collected items
- Reporting/logging which tests will execute
- Conditional setup based on which test classes are present

---

## Quick Reference: Config Options for Discovery

| Option | Default | Purpose |
|--------|---------|---------|
| `python_files` | `test_*.py` | File glob patterns |
| `python_classes` | `Test` | Class name prefixes |
| `python_functions` | `test` | Function/method name prefixes |
| `norecursedirs` | `.* build dist CVS _darcs {arch} *.egg venv` | Directories to skip |
| `testpaths` | (root) | Directories to search for tests |
| `collect_ignore` | (none) | Paths to ignore (set in conftest.py) |
| `collect_ignore_glob` | (none) | Glob patterns to ignore (set in conftest.py) |
