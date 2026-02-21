# pytest: Monkeypatch, Temporary Files, Logging & Warnings
Based on pytest 9.0.x documentation.

## Table of Contents

1. [Monkeypatch](#monkeypatch)
2. [Temporary Files](#temporary-files)
3. [Logging (caplog)](#logging-caplog)
4. [Warnings](#warnings)
5. [Doctests](#doctests)
6. [Monkeypatch vs unittest.mock](#monkeypatch-vs-unittestmock)
7. [Common Pitfalls](#common-pitfalls)

---

## Monkeypatch

The `monkeypatch` fixture safely patches attributes, dictionaries, environment variables, or `sys.path` for the duration of a test. All modifications are automatically undone when the test finishes.

### Quick Reference

| Method | Purpose |
|--------|---------|
| `monkeypatch.setattr(obj, name, value, raising=True)` | Replace attribute on object |
| `monkeypatch.delattr(obj, name, raising=True)` | Remove attribute from object |
| `monkeypatch.setitem(mapping, name, value)` | Set dictionary key |
| `monkeypatch.delitem(obj, name, raising=True)` | Delete dictionary key |
| `monkeypatch.setenv(name, value, prepend=None)` | Set environment variable |
| `monkeypatch.delenv(name, raising=False)` | Delete environment variable |
| `monkeypatch.syspath_prepend(path)` | Prepend to `sys.path` |
| `monkeypatch.chdir(path)` | Change working directory |
| `monkeypatch.context()` | Context manager for scoped patches |

The `raising` parameter controls whether `KeyError`/`AttributeError` is raised if the target doesn't exist.

### Patching Functions

```python
from pathlib import Path

def getssh():
    return Path.home() / ".ssh"

def test_getssh(monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: Path("/abc"))
    assert getssh() == Path("/abc/.ssh")
```

**Key rule:** Call `setattr` BEFORE calling the code that uses the patched function.

### Patching with Mock Classes

Build lightweight mock classes instead of relying on complex mock libraries:

```python
import requests
import app  # module containing get_json()

class MockResponse:
    @staticmethod
    def json():
        return {"mock_key": "mock_response"}

def test_get_json(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: MockResponse())
    result = app.get_json("https://fakeurl")
    assert result["mock_key"] == "mock_response"
```

### Sharing Patches via Fixtures

```python
@pytest.fixture
def mock_response(monkeypatch):
    """Mock requests.get to return a known response."""
    monkeypatch.setattr(requests, "get", lambda *a, **kw: MockResponse())

def test_get_json(mock_response):
    result = app.get_json("https://fakeurl")
    assert result["mock_key"] == "mock_response"
```

### Global Patch (autouse)

Prevent all HTTP requests in tests:

```python
# conftest.py
@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")
```

### Environment Variables

```python
def test_env_set(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key-123")
    assert os.getenv("API_KEY") == "test-key-123"

def test_env_missing(monkeypatch):
    monkeypatch.delenv("USER", raising=False)  # raising=False if var might not exist
    with pytest.raises(OSError):
        get_os_user_lower()

def test_path_prepend(monkeypatch):
    monkeypatch.setenv("PATH", "/custom/bin", prepend=os.pathsep)
```

### Dictionary Items

```python
import app

def test_connection(monkeypatch):
    monkeypatch.setitem(app.DEFAULT_CONFIG, "user", "test_user")
    monkeypatch.setitem(app.DEFAULT_CONFIG, "database", "test_db")
    result = app.create_connection_string()
    assert result == "User Id=test_user; Location=test_db;"

def test_missing_key(monkeypatch):
    monkeypatch.delitem(app.DEFAULT_CONFIG, "user", raising=False)
    with pytest.raises(KeyError):
        app.create_connection_string()
```

### Scoped Patching with `context()`

Use `monkeypatch.context()` when patching stdlib or pytest internals to limit the patch scope:

```python
import functools

def test_partial(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(functools, "partial", 3)
        assert functools.partial == 3
    # patch is reverted here, inside the test
```

### String-Based Patching

`setattr` and `delattr` accept dotted string paths:

```python
monkeypatch.delattr("requests.sessions.Session.request")
# equivalent to: delattr on the resolved object
```

---

## Temporary Files

### `tmp_path` Fixture (Function-Scoped)

Provides a unique `pathlib.Path` directory per test function:

```python
def test_create_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("content", encoding="utf-8")
    assert p.read_text(encoding="utf-8") == "content"
    assert len(list(tmp_path.iterdir())) == 1
```

### `tmp_path_factory` Fixture (Session-Scoped)

Use for expensive setup shared across tests:

```python
# conftest.py
@pytest.fixture(scope="session")
def image_file(tmp_path_factory):
    img = compute_expensive_image()
    fn = tmp_path_factory.mktemp("data") / "img.png"
    img.save(fn)
    return fn

# test_image.py
def test_histogram(image_file):
    img = load_image(image_file)
    # test against the shared image
```

### Directory Location and Retention

Default location: `{temproot}/pytest-of-{user}/pytest-{num}/{testname}/`

| Config Option | Purpose |
|---------------|---------|
| `--basetemp=mydir` | Custom base directory (cleared each run) |
| `tmp_path_retention_count` | Number of runs to retain (default: 3) |
| `tmp_path_retention_policy` | Retention policy |

**Do not use `tmpdir`/`tmpdir_factory`** -- these are legacy fixtures returning `py.path.local` objects. Disable them with `pytest -p no:legacypath`.

---

## Logging (caplog)

pytest captures log messages at WARNING or above by default and shows them for failed tests.

### caplog Fixture

```python
import logging

def test_log_capture(caplog):
    caplog.set_level(logging.INFO)  # capture INFO and above
    do_something()
    assert "expected message" in caplog.text
```

### Setting Log Level

```python
# Set on root logger
caplog.set_level(logging.DEBUG)

# Set on specific logger
caplog.set_level(logging.CRITICAL, logger="root.baz")

# Context manager (temporary)
with caplog.at_level(logging.INFO):
    do_something()

with caplog.at_level(logging.DEBUG, logger="myapp.db"):
    do_something()
```

Level is automatically restored at test end.

### Asserting Log Output

| Property | Returns | Use Case |
|----------|---------|----------|
| `caplog.text` | Full formatted log text | Substring matching |
| `caplog.records` | List of `logging.LogRecord` | Detailed inspection |
| `caplog.record_tuples` | List of `(logger, level, message)` | Exact matching |
| `caplog.messages` | List of message strings | Simple message checks |

```python
def test_log_records(caplog):
    caplog.set_level(logging.INFO)
    func_under_test()

    # Check no critical logs
    for record in caplog.records:
        assert record.levelname != "CRITICAL"

    # Substring check
    assert "wally" not in caplog.text

    # Exact tuple matching
    assert caplog.record_tuples == [("root", logging.INFO, "boo arg")]
```

### Clearing Captured Logs

```python
def test_with_clearing(caplog):
    setup_that_logs()
    caplog.clear()  # reset captured records
    function_under_test()
    assert ["Foo"] == [rec.message for rec in caplog.records]
```

### Stage-Specific Records

`caplog.records` contains only current-stage records. Use `caplog.get_records(when)` for other stages:

```python
@pytest.fixture
def window(caplog):
    window = create_window()
    yield window
    for when in ("setup", "call"):
        messages = [
            x.message for x in caplog.get_records(when)
            if x.levelno == logging.WARNING
        ]
        if messages:
            pytest.fail(f"warnings during testing: {messages}")
```

### Configuration Options

| CLI Option | Config Key | Purpose |
|------------|------------|---------|
| `--log-level` | `log_level` | Minimum capture level |
| `--log-format` | `log_format` | Log message format |
| `--log-date-format` | `log_date_format` | Date format |
| `--log-disable=NAME` | - | Disable specific loggers |
| `--log-cli-level` | `log_cli_level` | Live log level |
| `--log-file=PATH` | `log_file` | Log to file |
| `--log-file-level` | `log_file_level` | File log level |
| `--show-capture=no` | - | Suppress all captured output |

### Live Logging

Enable real-time log output to console:

```toml
# pyproject.toml
[tool.pytest.ini_options]
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s %(levelname)s %(message)s"
```

---

## Warnings

pytest automatically captures warnings and displays them in a summary section after the test session.

### Asserting Warnings with `pytest.warns`

```python
import warnings

def test_warning():
    with pytest.warns(UserWarning):
        warnings.warn("my warning", UserWarning)

# With message matching (regex)
def test_warning_match():
    with pytest.warns(UserWarning, match=r"must be \d+$"):
        warnings.warn("value must be 42", UserWarning)

# Match literal strings with special chars
import re
with pytest.warns(UserWarning, match=re.escape("issue with foo() func")):
    warnings.warn("issue with foo() func")
```

### Recording Warnings

```python
# Record and inspect
with pytest.warns(RuntimeWarning) as record:
    warnings.warn("another warning", RuntimeWarning)

assert len(record) == 1
assert record[0].message.args[0] == "another warning"

# Record without asserting type (generic Warning)
with pytest.warns() as record:
    warnings.warn("user", UserWarning)
    warnings.warn("runtime", RuntimeWarning)

assert len(record) == 2
```

### `recwarn` Fixture

Records warnings for the entire test function:

```python
def test_hello(recwarn):
    warnings.warn("hello", UserWarning)
    assert len(recwarn) == 1
    w = recwarn.pop(UserWarning)
    assert issubclass(w.category, UserWarning)
    assert str(w.message) == "hello"
```

### Deprecation Warnings

```python
def test_deprecated():
    with pytest.deprecated_call():
        myfunction(17)  # must issue DeprecationWarning or PendingDeprecationWarning
```

### Warning Filters

**Configuration file:**

```toml
# pyproject.toml
[tool.pytest.ini_options]
filterwarnings = [
    "error",                          # treat all warnings as errors
    "ignore::UserWarning",            # except UserWarning
    'ignore:function ham\(\) is deprecated:DeprecationWarning',
]
```

Last matching filter wins.

**Per-test with marks:**

```python
@pytest.mark.filterwarnings("ignore:api v1")
@pytest.mark.filterwarnings("error")  # decorators evaluated bottom-up, so "error" is base
def test_one():
    assert api_v1() == 1
```

**Per-module:**

```python
pytestmark = pytest.mark.filterwarnings("error")
```

### Common Warning Patterns

| Goal | Pattern |
|------|---------|
| At least one of several types | `pytest.warns((RuntimeWarning, UserWarning))` |
| Exactly N warnings | Use `recwarn` + `assert len(recwarn) == N` |
| No warnings at all | `with warnings.catch_warnings(): warnings.simplefilter("error")` |
| Suppress warnings | `with warnings.catch_warnings(): warnings.simplefilter("ignore")` |

---

## Doctests

pytest can discover and run doctests from text files and Python docstrings.

### Running Doctests

```bash
# From text files (default: test*.txt)
pytest

# Custom glob patterns
pytest --doctest-glob="*.rst" --doctest-glob="*.md"

# From Python docstrings
pytest --doctest-modules
```

Make permanent in config:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = ["--doctest-modules"]
```

### Doctest Options

```toml
# pyproject.toml
[tool.pytest.ini_options]
doctest_optionflags = ["NORMALIZE_WHITESPACE", "ELLIPSIS"]
```

Inline option directives also work:

```python
>>> something()  # doctest: +ELLIPSIS
[1, 2, ...]
```

**pytest-specific options:**

| Option | Purpose |
|--------|---------|
| `ALLOW_UNICODE` | Strip `u` prefix from expected output |
| `ALLOW_BYTES` | Strip `b` prefix from expected output |
| `NUMBER` | Fuzzy float comparison via `pytest.approx` precision |

### Using Fixtures in Doctests

```rst
# content of example.rst
>>> tmp = getfixture('tmp_path')
>>> (tmp / "test.txt").write_text("hello")
5
```

### `doctest_namespace` Fixture

Inject objects into the doctest namespace:

```python
# conftest.py
import numpy

@pytest.fixture(autouse=True)
def add_np(doctest_namespace):
    doctest_namespace["np"] = numpy
```

```python
# mymodule.py
def arange():
    """
    >>> a = np.arange(10)
    >>> len(a)
    10
    """
```

### Skipping in Doctests

```python
>>> random.random()  # doctest: +SKIP
0.156231223
```

### Other Options

| Option | Purpose |
|--------|---------|
| `--doctest-continue-on-failure` | Don't stop at first failure in a doctest |
| `--doctest-report=udiff` | Output format: `none`, `udiff`, `cdiff`, `ndiff` |
| `doctest_encoding = "latin1"` | Set file encoding (default: UTF-8) |

---

## Monkeypatch vs unittest.mock

| Criterion | `monkeypatch` | `unittest.mock.patch` |
|-----------|---------------|----------------------|
| **Scope** | Test/fixture duration (auto-cleanup) | Context manager or decorator (manual) |
| **Best for** | Env vars, `sys.path`, simple attr replacement | Call tracking, return sequences, side effects |
| **Call assertions** | No built-in call tracking | `assert_called_once_with`, `call_count`, etc. |
| **Lightweight replacement** | Preferred -- explicit, simple | Heavier API, more features |
| **Dict patching** | `setitem`/`delitem` built-in | Requires manual handling |
| **Env vars** | `setenv`/`delenv` built-in | `mock.patch.dict(os.environ, ...)` |
| **Combining** | Works well together | Works well together |

**Rule of thumb:**
- Use `monkeypatch` when you just need to replace a value or function and don't need call tracking.
- Use `unittest.mock` when you need to verify HOW something was called (arguments, call count, call order).
- Both auto-revert -- `monkeypatch` at fixture teardown, `mock.patch` at context exit.

---

## Common Pitfalls

### Monkeypatch

1. **Patching builtins** -- Do not monkeypatch `open`, `compile`, etc. It can break pytest internals. If unavoidable, pass `--tb=native --assert=plain --capture=no`.

2. **Patching stdlib used by pytest** -- Use `monkeypatch.context()` to limit scope:
   ```python
   def test_stdlib(monkeypatch):
       with monkeypatch.context() as m:
           m.setattr(functools, "reduce", my_reduce)
           # patch active only within this block
   ```

3. **Patch order matters** -- `setattr` must be called BEFORE the code that uses the patched target.

4. **String paths resolve at call time** -- `monkeypatch.setattr("module.Class.method", mock)` resolves the dotted path when called, not when the test runs the code.

### Temporary Files

5. **`--basetemp` clears the directory** -- Never point it at a directory with other data. It is wiped before each run.

6. **`tmp_path` is function-scoped** -- Use `tmp_path_factory` for session or module scope. Attempting to use `tmp_path` in a session-scoped fixture causes a `ScopeMismatch` error.

7. **Don't use `tmpdir`** -- It's a legacy fixture returning `py.path.local`. Use `tmp_path` (`pathlib.Path`) instead.

### Logging (caplog)

8. **Root logger modification** -- If test code calls `logging.config.dictConfig`, it may remove `caplog`'s handler. Ensure root logger configuration only ADDS handlers.

9. **`caplog.records` is stage-specific** -- In teardown, `caplog.records` contains only teardown logs. Use `caplog.get_records("call")` to inspect test-phase logs.

10. **Must set level explicitly** -- `caplog` captures WARNING+ by default. Call `caplog.set_level(logging.DEBUG)` to capture lower levels.

### Warnings

11. **Filter order differs between decorators and config** -- Decorators: earlier decorator wins (evaluated bottom-up). Config file: last matching filter wins.

12. **`pytest.warns()` with no type** -- Passing no argument defaults to generic `Warning`, capturing everything. Be specific when possible.

13. **`recwarn` vs `pytest.warns`** -- `recwarn` captures for the whole function. `pytest.warns` is a context manager with optional type assertion. Use `recwarn` when you want to inspect all warnings after the fact.

### Doctests

14. **Fixture discovery** -- `conftest.py` must be in the same directory tree as the doctest file. Sibling directories are not searched.

15. **`NUMBER` option is greedy** -- It matches floats anywhere in output, including inside strings. Don't enable globally; use inline `# doctest: +NUMBER` instead.
