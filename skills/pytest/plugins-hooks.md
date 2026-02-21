# pytest: Plugins and Hooks
Based on pytest 9.0.x documentation.

## Plugin System Overview

pytest's functionality is built entirely on plugins. There are three types:

| Type | Location | Discovery |
|------|----------|-----------|
| **Built-in plugins** | pytest's internal `_pytest/` directory | Loaded automatically |
| **External plugins** | pip-installed packages | Via `pytest11` entry point |
| **conftest.py plugins** | `conftest.py` files in test directories | Auto-discovered by directory |

Every hook call is a 1:N function call -- N registered implementations for that hook specification. All hook functions use the `pytest_` prefix.

### Plugin Discovery Order (at startup)

1. `-p no:NAME` options scanned -- blocks named plugins (even built-ins)
2. Built-in plugins loaded
3. `-p NAME` options scanned -- loads named plugins
4. Third-party packages with `pytest11` entry points loaded (unless `PYTEST_DISABLE_PLUGIN_AUTOLOAD` is set)
5. `PYTEST_PLUGINS` environment variable plugins loaded
6. Initial `conftest.py` files loaded (from test paths upward to root, recursively processing `pytest_plugins` variables)

### Useful Commands

```bash
pytest --trace-config          # Show active plugins and conftest files
pytest -p no:NAME              # Disable a plugin by name
pytest --disable-plugin-autoload -p NAME  # Explicit plugin loading only
```

Permanently disable a plugin in config:
```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = ["-p", "no:NAME"]
```

---

## conftest.py: Local Per-Directory Plugins

conftest.py files are the most common way to extend pytest. They provide directory-scoped hook implementations -- hooks in a conftest.py only apply to tests in that directory and below.

### Scope and Discovery Rules

- A `conftest.py` applies to its directory and all subdirectories
- Multiple `conftest.py` files can exist at different levels; all applicable ones are loaded
- conftest.py files do NOT need `__init__.py` in their directory
- Never import from `conftest.py` directly -- it can be ambiguous

```
project/
    conftest.py          # applies to ALL tests
    tests/
        conftest.py      # applies to tests/ and below
        unit/
            conftest.py  # applies to unit/ only
            test_foo.py
        integration/
            test_bar.py  # sees project/ and tests/ conftest, NOT unit/
```

### Common conftest.py Patterns

**Shared fixtures:**
```python
# conftest.py
import pytest

@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()
```

**Registering custom markers:**
```python
# conftest.py
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: integration tests")
```

**Loading additional plugins:**
```python
# conftest.py (root only -- deprecated in non-root conftest files)
pytest_plugins = ["myapp.testsupport.myplugin", "other_plugin"]
```

**Modifying collected items:**
```python
# conftest.py
def pytest_collection_modifyitems(config, items):
    """Run slow tests last."""
    slow = [item for item in items if item.get_closest_marker("slow")]
    fast = [item for item in items if not item.get_closest_marker("slow")]
    items[:] = fast + slow
```

### conftest.py vs Plugin

| Use conftest.py when... | Use an installable plugin when... |
|-------------------------|-----------------------------------|
| Project-specific fixtures/hooks | Reusable across multiple projects |
| Directory-scoped behavior | Global behavior needed |
| No packaging/distribution needed | Distributing via pip |
| Simple hooks and fixtures | Complex hook interactions |

---

## Writing Hook Functions

Hook functions implement hook specifications defined by pytest. pytest validates argument names at registration -- you only need to declare the arguments you use.

```python
# Full signature: pytest_collection_modifyitems(session, config, items)
# You can omit args you don't need:
def pytest_collection_modifyitems(items):
    # pytest won't pass session or config -- that's fine
    items.sort(key=lambda item: item.name)
```

**Important:** Hook functions other than `pytest_runtest_*` must not raise exceptions. Doing so breaks the pytest run.

### Hook Wrappers

Hook wrappers execute around other hook implementations. They are generator functions that yield exactly once.

```python
import pytest

@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    # Code BEFORE the test runs
    start = time.time()

    res = yield  # Execute the actual test (and other hooks)

    # Code AFTER the test runs
    duration = time.time() - start
    if duration > 1.0:
        print(f"SLOW: {item.name} took {duration:.2f}s")

    return res  # Must return a result (or raise)
```

The simplest hook wrapper is `return (yield)` -- it just passes through.

**Error handling in wrappers:**
```python
@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except Exception:
        # Handle or suppress the exception
        raise  # or return a value to suppress
```

### Hook Ordering

Control execution order with `@pytest.hookimpl` options:

| Option | Effect |
|--------|--------|
| `tryfirst=True` | Run before other non-wrapper implementations |
| `trylast=True` | Run after other non-wrapper implementations |
| `wrapper=True` | Run around all non-wrapper implementations |

```python
# Execution order for pytest_collection_modifyitems:
#
# 1. Wrappers execute (outermost to innermost) until yield
# 2. tryfirst=True implementations
# 3. Normal implementations
# 4. trylast=True implementations
# 5. Wrappers resume after yield (innermost to outermost)

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
    # Runs early among non-wrappers
    ...

@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    # Runs late among non-wrappers
    ...

@pytest.hookimpl(wrapper=True)
def pytest_collection_modifyitems(items):
    # Wraps ALL non-wrappers
    return (yield)
```

`tryfirst` and `trylast` also work on wrappers to control wrapper ordering relative to other wrappers.

### firstresult Hooks

Some hooks use `firstresult=True` -- execution stops at the first non-None return value. Remaining implementations are NOT called. These hooks are noted in the API reference.

---

## Common Hooks Reference

### Initialization & Configuration

```python
def pytest_addoption(parser, pluginmanager):
    """Add CLI options and config values. Called once at startup.
    Cannot be a hook wrapper. Only works in initial conftest files."""
    parser.addoption("--slow", action="store_true", help="Run slow tests")
    parser.addini("base_url", "Base URL for tests")

def pytest_configure(config):
    """Initial configuration. Cannot be a hook wrapper.
    Called for every conftest after CLI parsing."""
    config.addinivalue_line("markers", "slow: slow tests")

def pytest_unconfigure(config):
    """Called before test process exits."""

def pytest_sessionstart(session):
    """After Session created, before collection. Initial conftests only."""

def pytest_sessionfinish(session, exitstatus):
    """After entire test run, before exit."""
```

### Collection

```python
def pytest_collect_file(file_path, parent):
    """Create a Collector for a file, or None to skip. firstresult."""

def pytest_ignore_collect(collection_path, config):
    """Return True to ignore path, None to defer, False to force collect. firstresult."""

def pytest_collection_modifyitems(session, config, items):
    """Modify collected items in-place (reorder, filter, etc.).
    Works in ANY conftest -- always receives ALL items."""

def pytest_generate_tests(metafunc):
    """Generate parametrized test calls. Also discovered in test modules."""

def pytest_make_parametrize_id(config, val, argname):
    """Custom string repr for parametrize values. firstresult."""
```

### Test Execution

```python
def pytest_runtest_protocol(item, nextitem):
    """Full test protocol (setup + call + teardown). firstresult."""

def pytest_runtest_setup(item):
    """Setup phase for a test item."""

def pytest_runtest_call(item):
    """Call phase -- runs the actual test."""

def pytest_runtest_teardown(item, nextitem):
    """Teardown phase for a test item."""

def pytest_runtest_makereport(item, call):
    """Create TestReport for setup/call/teardown phases. firstresult."""
```

### Reporting

```python
def pytest_runtest_logreport(report):
    """Process a TestReport from setup/call/teardown."""

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add a section to terminal summary."""

def pytest_report_header(config, start_path):
    """Return string(s) to display in the test session header."""
```

---

## Storing Data Across Hooks

Use `pytest.StashKey` and `item.stash` instead of setting private attributes -- it's type-safe and avoids conflicts with other plugins.

```python
# Define keys at module level
phase_key = pytest.StashKey[str]()
timing_key = pytest.StashKey[float]()

def pytest_runtest_setup(item):
    item.stash[phase_key] = "setup"
    item.stash[timing_key] = time.time()

def pytest_runtest_teardown(item):
    elapsed = time.time() - item.stash[timing_key]
    print(f"{item.name}: {elapsed:.3f}s")
```

Stashes are available on all node types (`Item`, `Class`, `Module`, `Session`) and on `Config`.

---

## Writing Installable Plugins

### Package Structure

```
pytest-myproject/
    pyproject.toml
    pytest_myproject/
        __init__.py
        plugin.py
        helper.py
```

### Entry Point Registration

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pytest-myproject"
classifiers = ["Framework :: Pytest"]

[project.entry-points.pytest11]
myproject = "pytest_myproject.plugin"
```

pytest discovers plugins via the `pytest11` entry point. Confirm with `pytest --trace-config`.

### Assertion Rewriting

pytest only rewrites assertions in test modules and registered plugin entry points. If your plugin package has helper modules with assertions:

```python
# pytest_myproject/__init__.py
import pytest
pytest.register_assert_rewrite("pytest_myproject.helper")
```

Call this BEFORE the module is imported.

### Accessing Other Plugins

```python
def pytest_configure(config):
    other = config.pluginmanager.get_plugin("name_of_plugin")
    if other is not None:
        # Collaborate with the other plugin
        ...
```

### Conditionally Using Third-Party Plugin Hooks

Avoid import errors when optional plugins aren't installed:

```python
class DeferPlugin:
    """Implements hooks from an optional dependency."""
    def pytest_testnodedown(self, node, error):
        # xdist hook -- only relevant when xdist is installed
        ...

def pytest_configure(config):
    if config.pluginmanager.hasplugin("xdist"):
        config.pluginmanager.register(DeferPlugin())
```

---

## Declaring Custom Hooks

Plugins can define new hooks that other plugins implement.

```python
# hooks.py -- hook specifications (do-nothing functions with docstrings)
def pytest_my_custom_hook(config, items):
    """Called after items are processed with the config and items."""

# plugin.py -- register the hooks
def pytest_addhooks(pluginmanager):
    from . import hooks
    pluginmanager.add_hookspecs(hooks)
```

Call custom hooks from fixtures or other hooks:

```python
@pytest.fixture
def processed_items(pytestconfig):
    result = pytestconfig.hook.pytest_my_custom_hook(
        config=pytestconfig, items=[]
    )
    return result
```

Hooks receive parameters using **keyword arguments only**.

### Custom Hook with firstresult

```python
# hooks.py
from pluggy import HookspecMarker
hookspec = HookspecMarker("pytest")

@hookspec(firstresult=True)
def pytest_default_value():
    """Return a default value. First non-None wins."""
```

---

## Testing Plugins with pytester

The `pytester` fixture creates isolated test environments for testing plugin code.

### Enable pytester

```python
# conftest.py in your test directory
pytest_plugins = ["pytester"]
```

Or run with `pytest -p pytester`.

### Writing Plugin Tests

```python
def test_my_plugin_modifies_collection(pytester):
    """Test that our plugin reorders items."""
    # Create a conftest with the plugin
    pytester.makeconftest("""
        def pytest_collection_modifyitems(items):
            items.sort(key=lambda item: item.name)
    """)

    # Create test files
    pytester.makepyfile("""
        def test_b(): pass
        def test_a(): pass
    """)

    # Run pytest and check results
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)

    # Check output order
    result.stdout.fnmatch_lines([
        "*test_a*",
        "*test_b*",
    ])
```

### pytester Key Methods

| Method | Purpose |
|--------|---------|
| `pytester.makepyfile(**kw)` | Create test `.py` files |
| `pytester.makeconftest(source)` | Create a `conftest.py` |
| `pytester.makefile(ext, *args, **kw)` | Create files with given extension |
| `pytester.copy_example(name)` | Copy from `pytester_example_dir` |
| `pytester.runpytest(*args)` | Run pytest, return `RunResult` |
| `pytester.runpytest_subprocess(*args)` | Run in subprocess (full isolation) |
| `result.assert_outcomes(passed=N)` | Assert test counts |
| `result.stdout.fnmatch_lines(lines)` | Assert output patterns |

### Testing CLI Options

```python
def test_custom_option(pytester):
    pytester.makeconftest("""
        def pytest_addoption(parser):
            parser.addoption("--greet", default="World")
    """)
    pytester.makepyfile("""
        def test_greeting(pytestconfig):
            assert pytestconfig.getoption("greet") == "Alice"
    """)
    result = pytester.runpytest("--greet=Alice")
    result.assert_outcomes(passed=1)
```

---

## Practical Recipes

### Skip tests unless a CLI flag is passed

```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", default=False)

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
```

### Add custom info to test reports

```python
# conftest.py
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if report.when == "call" and report.failed:
        report.sections.append(("Custom Info", f"Failed: {item.name}"))
    return report
```

### Measure and report test durations

```python
# conftest.py
import time

durations_key = pytest.StashKey[float]()

def pytest_runtest_setup(item):
    item.stash[durations_key] = time.time()

def pytest_runtest_teardown(item):
    duration = time.time() - item.stash[durations_key]
    if duration > 2.0:
        print(f"\nWARNING: {item.name} took {duration:.1f}s")

def pytest_terminal_summary(terminalreporter):
    terminalreporter.write_sep("=", "Custom Duration Report")
    # Access reports via terminalreporter.stats
```

### Add a section to the session header

```python
# conftest.py
def pytest_report_header(config):
    return ["Project: myapp", f"Database: {config.getini('db_url')}"]
```

---

## Quick Reference: @pytest.hookimpl Options

| Option | Type | Effect |
|--------|------|--------|
| `wrapper` | `bool` | Make this a hook wrapper (generator that yields once) |
| `tryfirst` | `bool` | Execute before other non-wrapper implementations |
| `trylast` | `bool` | Execute after other non-wrapper implementations |

```python
@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    # Outermost wrapper, executes first among wrappers
    return (yield)
```

## Quick Reference: pytest_plugins

```python
# Root conftest.py ONLY (deprecated in non-root conftest files)
pytest_plugins = ["myapp.testsupport.fixtures"]

# Single plugin
pytest_plugins = "myapp.testsupport.fixtures"

# Plugins loaded via pytest_plugins get assertion rewriting automatically
```
