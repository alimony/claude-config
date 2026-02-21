# pytest: Configuration
Based on pytest 9.0.x documentation.

## Configuration Files

### Priority Order

pytest searches for configuration in this order (first match wins):

| File | Match Condition |
|------|----------------|
| `pytest.toml` / `.pytest.toml` | Always matches, highest precedence |
| `pytest.ini` / `.pytest.ini` | Always matches |
| `pyproject.toml` | Contains `[tool.pytest]` (9.0+) or `[tool.pytest.ini_options]` (6.0+) |
| `tox.ini` | Contains `[pytest]` section |
| `setup.cfg` | Contains `[tool:pytest]` section |

**Recommendation:** Use `pyproject.toml` with `[tool.pytest]` for new projects on pytest 9.0+.

### pyproject.toml: Two Styles

**Modern (pytest 9.0+) -- native TOML types:**
```toml
[tool.pytest]
minversion = "9.0"
addopts = ["-ra", "--showlocals", "--strict-markers", "--strict-config"]
testpaths = ["tests"]
filterwarnings = ["error"]
xfail_strict = true
log_level = "INFO"
```

**Legacy (pytest 6.0+) -- INI-style strings:**
```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra --showlocals --strict-markers --strict-config"
testpaths = ["tests", "integration"]
filterwarnings = ["error"]
```

Key difference: `[tool.pytest]` uses native TOML arrays for `addopts` (`["-ra", "-q"]`), while `[tool.pytest.ini_options]` uses a single string (`"-ra -q"`). Both work; the new section is the future direction.

**Do not use both sections.** If `[tool.pytest]` exists, `[tool.pytest.ini_options]` is ignored.

### pytest.ini (standalone)

```ini
[pytest]
minversion = 9.0
addopts = -ra --strict-markers
testpaths = tests
```

### conftest.py

Not a configuration file per se, but conftest.py files:
- Define fixtures shared across test modules in the same directory and below
- Register custom markers, hooks, and plugins
- Are collected automatically -- no imports needed
- Can exist at any level of the test directory tree

## Rootdir Discovery

pytest determines `rootdir` (the common ancestor for test collection) by:

1. Finding the common ancestor of all specified test paths (or cwd if none given)
2. Walking upward from there looking for config files
3. The directory containing the first matched config file becomes rootdir

`rootdir` is used for:
- Constructing node IDs (the `::` separated test identifiers)
- As the base for relative paths in output
- Storing the `.pytest_cache` directory

## Key Configuration Options

### Test Discovery

```toml
[tool.pytest]
# Where to look for tests (relative to rootdir)
testpaths = ["tests"]

# File glob patterns for test modules
python_files = ["test_*.py", "*_test.py", "*__test.py"]

# Class name prefixes for test classes
python_classes = ["Test"]

# Function/method name prefixes for test functions
python_functions = ["test_"]

# Directories to skip during collection
norecursedirs = [".git", "node_modules", "venv", "__pycache__", "migrations"]
```

### Strictness

```toml
[tool.pytest]
# Enable all strict modes at once (9.0+)
strict = true

# Or individually:
strict_config = true    # Error on unrecognized config options
strict_markers = true   # Error on unregistered markers
xfail_strict = true     # xfail tests that pass are failures, not xpass
```

**Recommended:** Always enable `strict_markers` and `strict_config`. Catches typos early.

### CLI Defaults

```toml
[tool.pytest]
# Options added to every pytest invocation
addopts = [
    "-ra",              # Show summary of all non-passing tests
    "--showlocals",     # Show local variables in tracebacks
    "--strict-markers",
    "--strict-config",
    "-v",               # Verbose output
]
```

### Warning Control

```toml
[tool.pytest]
filterwarnings = [
    "error",                                        # Treat all warnings as errors
    "ignore::DeprecationWarning:some_library.*",    # Except this library
    "ignore::PendingDeprecationWarning",            # And pending deprecations
]
```

### Markers

```toml
[tool.pytest]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: integration tests requiring external services",
    "e2e: end-to-end browser tests",
]
```

### Import Mode

```toml
[tool.pytest]
# How pytest imports test modules
# "prepend" (default) -- adds test dir to sys.path
# "importlib" (recommended for new projects) -- uses importlib, no sys.path changes
import_mode = "importlib"
```

**importlib mode benefits:** No sys.path pollution, test module names don't need to be unique.
**importlib mode limitation:** Test utility modules in test directories aren't directly importable by other tests. Place shared test helpers in the application package instead.

### Other Useful Options

```toml
[tool.pytest]
# Minimum pytest version required
minversion = "9.0"

# Plugins that must be installed
required_plugins = ["pytest-cov", "pytest-xdist"]

# Cache directory (default: .pytest_cache in rootdir)
cache_dir = ".pytest_cache"

# Console output style: "progress" (default), "classic", "count"
console_output_style = "progress"

# Temporary directory retention: "all", "failed", "none"
tmp_path_retention_policy = "failed"
tmp_path_retention_count = 3

# Log level for captured log output
log_level = "INFO"
```

## Recommended Starter Config

```toml
[tool.pytest]
minversion = "9.0"
addopts = ["-ra", "--strict-markers", "--strict-config"]
testpaths = ["tests"]
xfail_strict = true
filterwarnings = ["error"]
```

This gives you: summary of failures (`-ra`), strict marker/config checking, tests only in `tests/`, xfail enforcement, and warnings-as-errors.

## Exit Codes

| Code | Enum | Meaning |
|------|------|---------|
| 0 | `ExitCode.OK` | All collected tests passed |
| 1 | `ExitCode.TESTS_FAILED` | Some tests failed |
| 2 | `ExitCode.INTERRUPTED` | Execution interrupted (Ctrl+C) |
| 3 | `ExitCode.INTERNAL_ERROR` | Internal error during execution |
| 4 | `ExitCode.USAGE_ERROR` | Command line usage error |
| 5 | `ExitCode.NO_TESTS_COLLECTED` | No tests were collected |

Access programmatically:
```python
from pytest import ExitCode

# In conftest.py or plugins
def pytest_sessionfinish(session, exitstatus):
    if exitstatus == ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = ExitCode.OK  # Treat no-tests as success
```

## Type Annotations

### Typing Fixtures

Annotate fixture parameters in tests with the fixture's **return type**, not the fixture function type:

```python
import pytest

@pytest.fixture
def db_connection() -> Connection:
    conn = create_connection()
    yield conn
    conn.close()

# In tests: annotate with the return type
def test_query(db_connection: Connection) -> None:
    result = db_connection.execute("SELECT 1")
    assert result is not None
```

### Typing Built-in Fixtures

```python
import pytest
from pathlib import Path

def test_with_builtins(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    ...
```

### Typing Parametrize

```python
@pytest.mark.parametrize("input_val, expected", [
    (1, 2),
    (5, 6),
])
def test_increment(input_val: int, expected: int) -> None:
    assert input_val + 1 == expected
```

### Why Type Tests?

Type checking tests catches refactoring breakage without running the full suite. When a function signature changes, the type checker flags all affected tests immediately.

## Deprecations (pytest 9.0)

In pytest 9.0, `PytestRemovedIn9Warning` deprecation warnings become **errors by default**. The features will be fully removed in 9.1.

### fspath Argument to Node Constructors

**Deprecated since 7.0. Errors in 9.0. Removed in 9.1.**

```python
# Don't: py.path.local via fspath
node = MyCollector.from_parent(parent, fspath=py.path.local("/some/path"))

# Do: pathlib.Path via path
from pathlib import Path
node = MyCollector.from_parent(parent, path=Path("/some/path"))
```

### pytest_cmdline_preparse Hook

**Deprecated. Use `pytest_load_initial_conftests` instead.**

```python
# Don't
def pytest_cmdline_preparse(config, args):
    args.append("--verbose")

# Do
def pytest_load_initial_conftests(early_config, parser, args):
    args.append("--verbose")
```

### pytest.importorskip Exception Type

**Changed in 9.0.** `importorskip()` now only catches `ModuleNotFoundError` by default (not all `ImportError`).

```python
# If you need to catch ImportError (not just ModuleNotFoundError):
mod = pytest.importorskip("somemodule", exc_type=ImportError)
```

### --strict Flag Behavior

**Changed in 9.0.** `--strict` now sets the `strict` config option, which enables *all* strictness options (`strict_markers`, `strict_config`, `strict_parametrization_ids`, `strict_xfail`). Previously it only set `strict_markers`.

### py.path.local Usage

The `py` library is legacy. All pytest APIs that accepted `py.path.local` now prefer `pathlib.Path`. Migrate any custom nodes, plugins, or conftest code that uses `py.path.local` to `pathlib.Path`.

### Other Notable Deprecations

| What | Since | Replacement |
|------|-------|-------------|
| `Node.fspath` property | 7.0 | `Node.path` (returns `pathlib.Path`) |
| `pytest.warns(None)` | 7.0 | No warning expected? Don't use `pytest.warns` at all |
| Nose-style `setup`/`teardown` | 7.2 | Use pytest fixtures or `setup_method`/`teardown_method` |
| `--no-header` flag | 8.0 | Use `-q` or configure via plugin |

## CLI Quick Reference

| Flag | Config Equivalent | Purpose |
|------|-------------------|---------|
| `-v` / `--verbose` | N/A | Increase verbosity |
| `-q` / `--quiet` | N/A | Decrease verbosity |
| `-x` / `--exitfirst` | N/A | Stop on first failure |
| `--maxfail=N` | N/A | Stop after N failures |
| `-k EXPR` | N/A | Run tests matching expression |
| `-m EXPR` | N/A | Run tests matching marker expression |
| `--strict-markers` | `strict_markers = true` | Error on unknown markers |
| `--strict-config` | `strict_config = true` | Error on unknown config keys |
| `-s` | N/A | Disable output capture (show prints) |
| `--tb=short\|long\|line\|no` | N/A | Traceback style |
| `--lf` / `--last-failed` | N/A | Re-run only last failures |
| `--ff` / `--failed-first` | N/A | Run failures first, then rest |
| `-p no:PLUGIN` | N/A | Disable a plugin |
| `--co` / `--collect-only` | N/A | Show collected tests without running |
| `--import-mode=MODE` | `import_mode = "importlib"` | Import strategy |
| `--rootdir=DIR` | N/A | Override rootdir detection |
| `-ra` | Via `addopts` | Show summary for all non-passing |
