# pytest: Fundamentals
Based on pytest 9.0.x documentation.

## Core Concepts

### Anatomy of a Test (Arrange-Act-Assert)

Every test follows four phases:

| Phase | Purpose |
|-------|---------|
| **Arrange** | Set up preconditions: create objects, insert records, prepare state |
| **Act** | One state-changing action — typically a single function/method call |
| **Assert** | Verify the result matches expectations |
| **Cleanup** | Tear down (usually handled by fixtures automatically) |

The *act* and *assert* are the core of the test. *Arrange* provides context. Behavior lives between *act* and *assert*.

```python
def test_user_can_change_email(db, user_factory):
    # Arrange
    user = user_factory(email="old@example.com")

    # Act
    user.change_email("new@example.com")

    # Assert
    assert user.email == "new@example.com"
```

### Test Discovery Rules

pytest auto-discovers tests following these conventions:

| Element | Convention |
|---------|-----------|
| **Directories** | Recurses into all dirs except those matching `norecursedirs` |
| **Files** | `test_*.py` or `*_test.py` |
| **Functions** | `test_*` prefixed, outside or inside classes |
| **Classes** | `Test*` prefixed, **no `__init__` method** |
| **Methods** | `test_*` prefixed inside `Test*` classes |

Static methods and class methods decorated with `@staticmethod` / `@classmethod` are also collected.

pytest also discovers `unittest.TestCase` subclasses automatically.

### How Assertions Work

pytest rewrites `assert` statements to provide rich failure messages. No special assertion methods needed:

```python
def test_equality():
    result = compute()
    assert result == 42          # Shows both values on failure
    assert "hello" in result     # Shows the container contents
    assert result > 0            # Shows the actual value
```

On failure, pytest shows intermediate values:
```
E       assert 4 == 5
E        +  where 4 = func(3)
```

## How-To Patterns

### Writing Basic Tests

```python
# test_math.py — no imports needed for simple tests
def test_addition():
    assert 1 + 1 == 2

def test_string_contains():
    greeting = "hello world"
    assert "world" in greeting
```

### Grouping Tests in Classes

Classes group related tests and can share fixtures. Each test gets a **fresh class instance** (no shared state between tests):

```python
class TestUserValidation:
    def test_rejects_empty_name(self):
        with pytest.raises(ValueError):
            User(name="")

    def test_accepts_valid_name(self):
        user = User(name="Alice")
        assert user.name == "Alice"
```

**Pitfall — no shared mutable state:**
```python
class TestCounter:
    value = 0

    def test_one(self):
        self.value = 1
        assert self.value == 1  # passes

    def test_two(self):
        assert self.value == 1  # FAILS — self.value is 0, fresh instance
```

### Asserting Exceptions

```python
import pytest

# Basic: just check the exception type
def test_raises_value_error():
    with pytest.raises(ValueError):
        int("not_a_number")

# Check the exception message
def test_raises_with_message():
    with pytest.raises(ValueError, match="invalid literal"):
        int("not_a_number")

# Capture the exception for further inspection
def test_raises_inspect():
    with pytest.raises(KeyError) as exc_info:
        {}["missing"]
    assert exc_info.value.args[0] == "missing"
```

### Comparing Floating-Point Values

```python
import pytest

def test_floating_point():
    assert (0.1 + 0.2) == pytest.approx(0.3)

# Works with absolute/relative tolerance
def test_with_tolerance():
    assert 2.0001 == pytest.approx(2.0, abs=1e-3)
    assert 100.1 == pytest.approx(100, rel=1e-2)

# Works with sequences
def test_list_approx():
    assert [0.1 + 0.2, 0.2 + 0.4] == pytest.approx([0.3, 0.6])
```

### Using Temporary Directories

```python
def test_file_creation(tmp_path):
    # tmp_path is a pathlib.Path, unique per test invocation
    file = tmp_path / "output.txt"
    file.write_text("hello")
    assert file.read_text() == "hello"
```

### Requesting Fixtures

Fixtures are injected by naming them as function parameters:

```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Alice", "role": "admin"}

def test_user_is_admin(sample_user):
    assert sample_user["role"] == "admin"
```

### Custom Command-Line Options

Add options via `conftest.py` and expose them as fixtures:

```python
# conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False,
        help="run slow tests"
    )

@pytest.fixture
def runslow(request):
    return request.config.getoption("--runslow")
```

### Skipping Slow Tests via Marker + CLI

```python
# conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False)

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return  # run everything
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

# test_example.py
@pytest.mark.slow
def test_expensive_computation():
    ...
```

### Writing Assertion Helpers

Use `__tracebackhide__` to keep helpers out of failure tracebacks:

```python
def assert_valid_response(response):
    __tracebackhide__ = True
    if response.status_code != 200:
        pytest.fail(f"Expected 200, got {response.status_code}: {response.text}")

def test_api_call(client):
    response = client.get("/api/users")
    assert_valid_response(response)  # clean traceback on failure
```

### Package/Directory-Level Fixtures

Place fixtures in `conftest.py` at the appropriate directory level:

```
tests/
  conftest.py          # fixtures available to ALL tests
  unit/
    conftest.py        # fixtures available only to unit tests
    test_services.py
  integration/
    conftest.py        # fixtures available only to integration tests
    test_api.py
```

Fixtures in `conftest.py` are automatically discovered — no import needed.

### Profiling Slow Tests

```bash
pytest --durations=10          # show 10 slowest tests
pytest --durations=0           # show all durations
pytest --durations-min=1.0     # only show tests slower than 1s
```

## Project Layout & Imports

### Recommended Layout: src + importlib Mode

```
myproject/
  pyproject.toml
  src/
    mypkg/
      __init__.py
      app.py
  tests/
    test_app.py
    test_view.py
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
```

Install in editable mode: `pip install -e .`

### Import Modes

| Mode | sys.path | Unique names? | Recommended? |
|------|----------|---------------|-------------|
| `prepend` (default) | Inserts test dir at start | Yes, unless `__init__.py` in test dirs | Legacy default |
| `append` | Appends test dir at end | Yes, unless `__init__.py` in test dirs | Better for installed packages |
| `importlib` | **No changes** | No (auto-generates unique names) | **Recommended for new projects** |

**Key trade-offs of `importlib` mode:**
- Tests cannot import each other directly
- Test utility modules must live with application code (e.g., `app.testing.helpers`), not in test directories
- Fixtures belong in `conftest.py` (discovered automatically regardless of mode)

### pytest vs python -m pytest

| Invocation | Difference |
|-----------|-----------|
| `pytest [args]` | Does NOT add current directory to `sys.path` |
| `python -m pytest [args]` | Adds current directory to `sys.path` (standard Python behavior) |

Use `python -m pytest` when you need the current directory importable without an editable install.

### conftest.py Import Rules

- `conftest.py` files are imported **before** tests in the same directory
- In `prepend`/`append` modes, pytest walks up from `conftest.py` to find the package root (last dir with `__init__.py`)
- In `importlib` mode, `conftest.py` is imported directly without changing `sys.path`

## Configuration

### Setting Default Options

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = ["-ra", "-q", "--strict-markers"]
testpaths = ["tests"]
```

Or via environment variable:
```bash
export PYTEST_ADDOPTS="-v"
```

Resolution order: `<config addopts> $PYTEST_ADDOPTS <command-line args>` (last wins for conflicts).

### Strict Mode (v9.0+)

Enable all strictness options at once:

```toml
# pyproject.toml
[tool.pytest.ini_options]
strict = true
```

This enables:

| Option | Effect |
|--------|--------|
| `strict_config` | Error on unknown config keys |
| `strict_markers` | Error on undeclared markers |
| `strict_parametrization_ids` | Error on duplicate parametrize IDs |
| `strict_xfail` | Strict xfail behavior |

Override individual options if needed:
```toml
[tool.pytest.ini_options]
strict = true
strict_parametrization_ids = false
```

**Note:** New strictness options added in future pytest versions will auto-enable under `strict = true`. Pin your pytest version or enable options individually if you want stability.

## Essential CLI Reference

| Command | Purpose |
|---------|---------|
| `pytest` | Run all discovered tests |
| `pytest test_file.py` | Run tests in a specific file |
| `pytest test_file.py::TestClass` | Run all tests in a class |
| `pytest test_file.py::TestClass::test_method` | Run a single test |
| `pytest -k "expression"` | Run tests matching name expression |
| `pytest -m "marker"` | Run tests with specific marker |
| `pytest -x` | Stop on first failure |
| `pytest --maxfail=3` | Stop after 3 failures |
| `pytest -v` | Verbose output (show each test name) |
| `pytest -q` | Quiet output (minimal) |
| `pytest -s` | Show print output (disable capture) |
| `pytest --tb=short` | Shorter tracebacks (`short`, `long`, `line`, `no`) |
| `pytest --lf` | Re-run only last-failed tests |
| `pytest --ff` | Run last-failed tests first, then the rest |
| `pytest --co` | Collect tests only (don't run) — useful for debugging discovery |
| `pytest --fixtures` | List all available fixtures |
| `pytest --durations=N` | Show N slowest tests |

### Useful `-k` Expressions

```bash
pytest -k "test_user"                     # name contains "test_user"
pytest -k "test_user and not slow"        # contains "test_user" but not "slow"
pytest -k "test_user or test_admin"       # contains either
pytest -k "TestClass and test_method"     # specific class + method pattern
```

## Common Pitfalls

### 1. Test Classes with `__init__`

```python
# BAD — pytest will NOT discover these tests
class TestUsers:
    def __init__(self):
        self.db = setup_db()

    def test_create(self):
        ...

# GOOD — use fixtures instead
class TestUsers:
    def test_create(self, db):
        ...
```

### 2. Assuming Shared State Between Tests in a Class

Each test method gets a **new instance** of the class. Do not rely on `self.something` set in another test. Use fixtures for shared setup.

### 3. Duplicate Test Module Names (prepend/append mode)

```
tests/
  api/
    test_users.py      # imported as test_users
  web/
    test_users.py      # COLLISION — also imported as test_users
```

Fix options:
- Add `__init__.py` to make them packages (`tests.api.test_users` vs `tests.web.test_users`)
- Switch to `--import-mode=importlib` (auto-generates unique names)

### 4. Modifying sys.path Manually

Don't add `sys.path.insert(0, ...)` hacks to test files. Instead:
- Use `--import-mode=importlib`
- Or configure `pythonpath` in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["src"]
  ```

### 5. Running Tests Against Wrong Code

With `prepend` mode, local source can shadow the installed package. Use `src` layout + editable install to prevent this. Or use `--import-mode=append` which prefers installed packages.

### 6. conftest.py Scope Confusion

A `conftest.py` fixture is only available to tests **in the same directory and below**. A fixture in `tests/api/conftest.py` is NOT available to `tests/web/test_something.py`.

### 7. Forgetting pytest Captures stdout

By default, `print()` output is captured and only shown on failure. Use `-s` flag to see it:
```bash
pytest -v -s                # show all stdout
```

Or just rely on the fact that captured output appears automatically in failure reports.

## Best Practices

### Do This

- **Use plain `assert`** — pytest's introspection makes custom assertion methods unnecessary
- **Use `pytest.approx()`** for float comparison instead of manual tolerance checks
- **Use `conftest.py`** for shared fixtures — automatic discovery, no imports needed
- **Use `tmp_path`** (not `tmpdir`) for temporary files — returns `pathlib.Path`
- **Use `--strict-markers`** to catch typos in marker names
- **Use `--import-mode=importlib`** for new projects
- **Use `src` layout** to avoid import confusion between local and installed code
- **Keep test functions short** — one act, one assert (or closely related asserts)
- **Name tests descriptively** — `test_expired_token_returns_401` not `test_token_3`
- **Use markers** (`@pytest.mark.slow`, etc.) to categorize tests

### Don't Do This

- **Don't use `setup.py test`** — deprecated and insecure
- **Don't put `__init__.py`** in test class bodies
- **Don't share mutable state** between test methods via class attributes
- **Don't import `conftest.py`** directly — it's auto-loaded by pytest
- **Don't use `unittest.TestCase` assertion methods** when writing pytest-style tests — plain `assert` is better
- **Don't add `sys.path` hacks** — configure import mode and `pythonpath` instead
- **Don't rely on test execution order** — tests should be independent

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `PYTEST_ADDOPTS` | Extra CLI options merged into every run |
| `PYTEST_CURRENT_TEST` | Set by pytest during run — contains `nodeid (phase)` |
| `PYTEST_VERSION` | Set during test session — can detect if running under pytest |

## Relationships to Other pytest Topics

| Topic | Connection |
|-------|-----------|
| **Fixtures** | Dependency injection via function parameters; `conftest.py` for sharing; scopes control lifecycle |
| **Markers** | `@pytest.mark.*` for categorizing tests; register in config or `conftest.py` |
| **Parametrize** | `@pytest.mark.parametrize` for running same test with different inputs |
| **Plugins** | `conftest.py` is a local plugin; hooks like `pytest_collection_modifyitems` customize behavior |
| **Configuration** | `pyproject.toml` `[tool.pytest.ini_options]` or `pytest.toml` `[pytest]` |
