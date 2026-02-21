# pytest: API Reference
Based on pytest 9.0.x documentation.

Generated from https://docs.pytest.org/en/stable/reference/reference.html on 2026-02-21.

## Top-Level Functions

### pytest.approx

```python
approx(expected, rel=None, abs=None, nan_ok=False)
```

Assert two numbers (or sequences/dicts of numbers) are equal within tolerance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expected` | number/sequence/dict | required | The expected value |
| `rel` | float | `1e-6` | Relative tolerance (fraction of expected) |
| `abs` | float | `1e-12` | Absolute tolerance |
| `nan_ok` | bool | `False` | If True, NaN == NaN |

```python
assert 0.1 + 0.2 == approx(0.3)
assert (0.1 + 0.2, 0.2 + 0.4) == approx((0.3, 0.6))
assert {"a": 0.1 + 0.2} == approx({"a": 0.3})
assert 1.0001 == approx(1, rel=1e-3)         # relative tolerance
assert 1.0001 == approx(1, abs=1e-3)         # absolute tolerance
```

**Tolerance rules:**
- If only `rel` specified: relative tolerance only
- If only `abs` specified: absolute tolerance only (relative ignored!)
- If both: either tolerance being met is sufficient
- Non-numeric types fall back to strict equality (useful for dicts with None values)

**Gotcha:** `approx` does NOT support `>`, `>=`, `<`, `<=` comparisons (raises TypeError).

### pytest.raises

```python
# Context manager form (preferred)
with pytest.raises(ExceptionType, match=r"regex") as exc_info:
    code_that_raises()

# With check callback (v8.4+)
with pytest.raises(OSError, check=lambda e: e.errno == errno.EACCES):
    raise OSError(errno.EACCES, "no permission")

# Callable form (legacy, discouraged)
result = pytest.raises(ZeroDivisionError, func, arg1, arg2)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `expected_exception` | type or tuple[type] | Exception type(s) to catch. Optional if using `match`/`check` alone |
| `match` | str or re.Pattern | Regex tested against str(exception) and `__notes__` via `re.search()` |
| `check` | Callable[[E], bool] | Custom validation callback (v8.4+). Must return True for match |

**The context manager yields `ExceptionInfo[E]`:**
```python
with pytest.raises(ValueError) as exc_info:
    raise ValueError("value must be 42")
assert exc_info.type is ValueError
assert exc_info.value.args[0] == "value must be 42"
assert exc_info.match(r"must be \d+")
```

**Important:** Code after the raising line inside the `with` block will NOT execute.

**Warning:** Avoid `pytest.raises(Exception)` — it catches everything and hides real bugs. Be specific.

### pytest.warns

```python
with pytest.warns(UserWarning, match=r"must be \d+$"):
    warnings.warn("value must be 42", UserWarning)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expected_warning` | type or tuple[type] | `Warning` | Warning class(es) to match |
| `match` | str or re.Pattern | None | Regex tested against warning message |

Produces a list of `warnings.WarningMessage` objects. Unmatched warnings are re-emitted when context closes (since pytest 8.0).

### pytest.deprecated_call

```python
with pytest.deprecated_call(match="use v3"):
    api_call_v2()  # must emit DeprecationWarning, PendingDeprecationWarning, or FutureWarning
```

### pytest.fail

```python
pytest.fail("reason for failure", pytrace=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reason` | str | required | Failure message |
| `pytrace` | bool | `True` | If False, suppress Python traceback |

### pytest.skip

```python
pytest.skip("reason")                              # skip during test execution
pytest.skip("reason", allow_module_level=True)     # skip entire module at collection
```

**Prefer `@pytest.mark.skipif` over imperative `pytest.skip()` when possible.**

### pytest.xfail

```python
pytest.xfail("known bug in library X")  # immediately marks test as xfail, no further code runs
```

**Prefer `@pytest.mark.xfail` over imperative `pytest.xfail()` when possible.**

### pytest.importorskip

```python
docutils = pytest.importorskip("docutils")
np = pytest.importorskip("numpy", minversion="1.20")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `modname` | str | Module to import |
| `minversion` | str or None | Minimum `__version__` required |
| `reason` | str or None | Custom skip message |
| `exc_type` | type or None | Exception type to catch (default: ModuleNotFoundError). Pass `ImportError` to suppress warning on ImportError (v8.2+) |

### pytest.param

```python
@pytest.mark.parametrize("input,expected", [
    ("3+5", 8),
    pytest.param("6*9", 42, marks=pytest.mark.xfail, id="6x9"),
    pytest.param("2+2", 4, id=pytest.HIDDEN_PARAM),  # v8.4+: hidden from test name
])
def test_eval(input, expected):
    assert eval(input) == expected
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `*values` | object | Parameter values in order |
| `marks` | MarkDecorator or list | Mark(s) to apply to this parameter set |
| `id` | str or None | Custom test ID for this parameter set |

### pytest.exit

```python
pytest.exit("reason to stop", returncode=1)
```

### pytest.main

```python
exit_code = pytest.main(["test_module.py", "-v"])
```

### pytest.register_assert_rewrite

```python
pytest.register_assert_rewrite("mypackage.utils")  # call before importing the module
```

Register modules for assertion rewriting. Usually called in `__init__.py` of plugin packages.

## Marks (Decorators)

### Built-in Marks

| Mark | Signature | Description |
|------|-----------|-------------|
| `@pytest.mark.parametrize` | `(argnames, argvalues, ids=None, indirect=False, scope=None)` | Parametrize a test function |
| `@pytest.mark.skip` | `(reason=None)` | Unconditionally skip |
| `@pytest.mark.skipif` | `(condition, *, reason=None)` | Skip if condition is True |
| `@pytest.mark.xfail` | `(condition=False, *, reason=None, raises=None, run=True, strict=False)` | Expected failure |
| `@pytest.mark.usefixtures` | `(*names)` | Use named fixtures (for classes/modules) |
| `@pytest.mark.filterwarnings` | `(filter)` | Add warning filter to test |

### @pytest.mark.parametrize

Same signature as `Metafunc.parametrize()`:

```python
@pytest.mark.parametrize("x,y,expected", [
    (1, 2, 3),
    (0, 0, 0),
    pytest.param(-1, 1, 0, id="negative"),
])
def test_add(x, y, expected):
    assert x + y == expected
```

### @pytest.mark.xfail details

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `condition` | bool or str | `False` | When True (or truthy string), mark as xfail |
| `reason` | str | None | Why it's expected to fail |
| `raises` | type or tuple | None | Only xfail if this exception type is raised |
| `run` | bool | `True` | If False, don't run the test at all (useful for segfaults) |
| `strict` | bool | `False` | If True, xpass (unexpected pass) FAILS the test suite |

### @pytest.mark.filterwarnings

```python
@pytest.mark.filterwarnings("ignore:.*usage will be deprecated.*:DeprecationWarning")
def test_foo():
    ...
```

### Custom Marks

```python
@pytest.mark.timeout(10, "slow", method="thread")
def test_function():
    ...

# Access in fixtures/hooks:
for marker in item.iter_markers("timeout"):
    marker.args    # (10, "slow")
    marker.kwargs  # {"method": "thread"}
```

## @pytest.fixture

```python
@pytest.fixture(scope="function", params=None, autouse=False, ids=None, name=None)
def my_fixture(request):
    # setup
    value = create_thing()
    yield value
    # teardown (runs regardless of test outcome)
    cleanup(value)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | str or Callable | `"function"` | One of: `"function"`, `"class"`, `"module"`, `"package"`, `"session"` |
| `params` | Iterable | None | Parametrize the fixture; current param via `request.param` |
| `autouse` | bool | `False` | Auto-activate for all tests that can see it |
| `ids` | Sequence or Callable | None | Test IDs for each param |
| `name` | str | None | Override the fixture name (useful to avoid shadowing) |

**Yield fixtures:** Code after `yield` is teardown. Must yield exactly once.

**Dynamic scope:**
```python
@pytest.fixture(scope=lambda fixture_name, config: "session" if config.getoption("--reuse-db") else "function")
def db():
    ...
```

## Built-in Fixtures

### capsys / capfd

Capture stdout/stderr writes.

```python
def test_output(capsys):
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == ""

    with capsys.disabled():
        print("this goes to real stdout")
```

| Fixture | Captures | Returns |
|---------|----------|---------|
| `capsys` | sys.stdout/stderr | str |
| `capfd` | file descriptors 1/2 | str |
| `capsysbinary` | sys.stdout/stderr | bytes |
| `capfdbinary` | file descriptors 1/2 | bytes |
| `capteesys` | sys.stdout/stderr + passes through | str |

**Key method:** `readouterr()` returns `CaptureResult(out, err)` namedtuple and resets buffer.

### caplog

Capture log output.

```python
def test_logging(caplog):
    import logging
    logging.warning("watch out")

    assert "watch out" in caplog.text               # formatted output
    assert caplog.messages == ["watch out"]          # just messages, no formatting
    assert caplog.records[0].levelname == "WARNING"  # LogRecord objects
    assert caplog.record_tuples == [("root", logging.WARNING, "watch out")]

    caplog.clear()  # reset
```

| Property/Method | Returns | Description |
|-----------------|---------|-------------|
| `.text` | str | Formatted log output |
| `.messages` | list[str] | Interpolated messages only (no timestamps/levels) |
| `.records` | list[LogRecord] | Full LogRecord objects |
| `.record_tuples` | list[tuple] | `(logger_name, level, message)` tuples |
| `.clear()` | None | Reset captured logs |
| `.set_level(level, logger=None)` | None | Set capture threshold for test duration |
| `.at_level(level, logger=None)` | context manager | Temporarily set level |
| `.filtering(filter_)` | context manager | Temporarily add a logging.Filter |
| `.get_records(when)` | list[LogRecord] | Get records for "setup", "call", or "teardown" phase |

### monkeypatch

Temporarily modify objects, dicts, env vars, and sys.path.

```python
def test_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.delenv("SECRET", raising=False)

def test_attr(monkeypatch):
    monkeypatch.setattr(os, "getcwd", lambda: "/fake")
    monkeypatch.setattr("os.getcwd", lambda: "/fake")   # string form

def test_dict(monkeypatch):
    monkeypatch.setitem(config, "debug", True)
    monkeypatch.delitem(config, "secret", raising=False)

def test_scoped(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(os, "getcwd", lambda: "/")
        # patching undone at end of `with` block
```

| Method | Description |
|--------|-------------|
| `setattr(target, name, value, raising=True)` | Patch attribute (object or dotted string) |
| `delattr(target, name, raising=True)` | Remove attribute |
| `setitem(dic, name, value)` | Set dict entry |
| `delitem(dic, name, raising=True)` | Delete dict entry |
| `setenv(name, value, prepend=None)` | Set env var |
| `delenv(name, raising=True)` | Delete env var |
| `syspath_prepend(path)` | Prepend to sys.path |
| `chdir(path)` | Change working directory |
| `context()` | Context manager for scoped patching |

**All changes are undone after the test.** The `raising` parameter controls whether missing targets raise errors.

**Where to patch:** Patch the name as imported by the code under test, not where it's defined. Same rule as `unittest.mock.patch`.

### tmp_path / tmp_path_factory

```python
def test_create_file(tmp_path):
    # tmp_path is a pathlib.Path unique to this test invocation
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("content")
    assert p.read_text() == "content"

def test_session_scope(tmp_path_factory):
    # session-scoped: use for shared temp dirs
    base = tmp_path_factory.mktemp("data")  # creates data0, data1, etc.
```

`tmp_path_factory` methods: `mktemp(basename, numbered=True)`, `getbasetemp()`.

**Note:** `tmpdir` and `tmpdir_factory` are legacy equivalents returning `py.path.local`. Prefer `tmp_path`.

### request (FixtureRequest)

Special fixture providing info about the requesting test.

```python
@pytest.fixture
def db(request):
    request.param          # current param (if parametrized)
    request.scope          # "function", "class", "module", "package", "session"
    request.fixturenames   # list of all active fixture names
    request.node           # underlying collection node
    request.config         # pytest Config
    request.function       # test function object (function scope only)
    request.cls            # test class (can be None)
    request.module         # test module
    request.path           # Path where test was collected
    request.keywords       # keywords/markers dict
    request.session        # pytest Session

    request.addfinalizer(cleanup_fn)          # register teardown
    request.applymarker("slow")               # apply marker dynamically
    request.getfixturevalue("other_fixture")  # get fixture value dynamically
```

### recwarn

```python
def test_warnings(recwarn):
    warnings.warn("hello", UserWarning)
    assert len(recwarn) == 1
    w = recwarn.pop(UserWarning)
    assert str(w.message) == "hello"
    recwarn.clear()
```

### pytestconfig

```python
def test_option(pytestconfig):
    if pytestconfig.get_verbosity() > 0:
        ...  # verbose mode
    val = pytestconfig.getoption("--my-option")
```

### config.cache

Persist values across test runs (stored as JSON).

```python
def test_with_cache(pytestconfig):
    cache = pytestconfig.cache
    val = cache.get("my_plugin/last_run", default=None)
    cache.set("my_plugin/last_run", "2024-01-01")
    cache.mkdir("my_plugin")  # returns Path to a persistent directory
```

### subtests (v8.0+)

```python
def test_with_subtests(subtests):
    for i in range(5):
        with subtests.test("evenness check", i=i):
            assert i % 2 == 0  # failures reported individually, all subtests run
```

## ExceptionInfo

Returned by `pytest.raises()` context manager.

| Property/Method | Returns | Description |
|-----------------|---------|-------------|
| `.type` | type[E] | The exception class |
| `.value` | E | The exception instance |
| `.tb` | TracebackType | Raw traceback |
| `.typename` | str | Type name as string |
| `.traceback` | Traceback | Traceback wrapper |
| `.exconly(tryshort=False)` | str | Exception as string |
| `.errisinstance(exc)` | bool | isinstance check (prefer `isinstance(excinfo.value, exc)`) |
| `.match(regexp)` | bool | Assert regex matches str(exception) via `re.search()` |
| `.group_contains(exc, match=None, depth=None)` | bool | Check exception group contains matching exception (v8.0+) |
| `.getrepr(showlocals, style, ...)` | str-able | Formatted representation |

`getrepr()` style options: `"long"`, `"short"`, `"line"`, `"no"`, `"native"`, `"value"`.

Class methods for creating ExceptionInfo:
- `ExceptionInfo.from_exception(exception)` -- from an existing exception
- `ExceptionInfo.from_current()` -- from current traceback (inside except block)
- `ExceptionInfo.for_later()` + `.fill_unfilled(exc_info)` -- deferred creation

## Collection Tree (Node Classes)

### Hierarchy

```
Node (ABC)
  +-- Collector (ABC) -- internal nodes
  |     +-- FSCollector (ABC) -- filesystem-based
  |     |     +-- File (ABC) -- collects from a file
  |     |     |     +-- Module -- Python test module
  |     |     +-- Directory (ABC) -- collects from a directory
  |     |           +-- Dir
  |     |           +-- Package -- directory with __init__.py
  |     +-- Session -- root collector
  |     +-- Class -- test class within a module
  +-- Item (ABC) -- leaf nodes (actual tests)
        +-- Function -- Python test function/method
```

### Node (base class)

| Attribute/Method | Description |
|------------------|-------------|
| `.name` | Unique name within parent scope |
| `.parent` | Parent collector node |
| `.config` | pytest Config object |
| `.session` | pytest Session |
| `.path` | pathlib.Path where collected from |
| `.nodeid` | `::` -separated collection address (e.g. `test_mod.py::TestClass::test_method`) |
| `.keywords` | Keywords/markers from all scopes |
| `.own_markers` | Markers belonging to this node only |
| `.stash` | Plugin storage (type-safe dict) |
| `.iter_markers(name=None)` | Iterate over markers (closest first) |
| `.get_closest_marker(name)` | First matching marker from closest scope |
| `.add_marker(marker, append=True)` | Dynamically add a marker |
| `.addfinalizer(fn)` | Register teardown function |
| `.getparent(cls)` | Get closest parent of given type (including self) |
| `.listchain()` | List of all parents from root to self |
| `Node.from_parent(parent, **kw)` | Public constructor (classmethod) |

### Item (test node)

Inherits from Node. Additional:

| Attribute/Method | Description |
|------------------|-------------|
| `.user_properties` | list of (name, value) tuples for test properties |
| `.runtest()` | Execute the test (abstract) |
| `.add_report_section(when, key, content)` | Add custom report section |
| `.reportinfo()` | Returns `(path, lineno, testname)` tuple |
| `.location` | `(relfspath, lineno, testname)` property |

### Function

Inherits from Item. Represents a Python test function.

| Attribute/Method | Description |
|------------------|-------------|
| `.originalname` | Function name without parametrization decoration |
| `.function` | Underlying Python function object |
| `.instance` | Bound instance (None for standalone functions) |

### Module, Class

- **Module** -- Collector for test classes and functions in a `.py` file
- **Class** -- Collector for test methods (and nested classes) in a test class

## TestReport

Created for each setup/call/teardown phase of a test item.

| Attribute | Type | Description |
|-----------|------|-------------|
| `.nodeid` | str | Collection node ID |
| `.outcome` | `"passed"` / `"failed"` / `"skipped"` | Test outcome |
| `.when` | `"setup"` / `"call"` / `"teardown"` | Runtest phase |
| `.longrepr` | various or None | Failure representation |
| `.duration` | float | Test duration in seconds |
| `.start` / `.stop` | float | System time (epoch seconds) |
| `.keywords` | Mapping[str, Any] | Keywords and markers |
| `.sections` | list[tuple[str, str]] | Extra `(heading, content)` sections |
| `.user_properties` | list[tuple] | User-defined properties |
| `.location` | tuple[str, int, str] | `(filepath, lineno, testname)` |

| Property | Returns | Description |
|----------|---------|-------------|
| `.passed` | bool | Whether outcome is passed |
| `.failed` | bool | Whether outcome is failed |
| `.skipped` | bool | Whether outcome is skipped |
| `.capstdout` | str | Captured stdout |
| `.capstderr` | str | Captured stderr |
| `.caplog` | str | Captured log lines |
| `.longreprtext` | str | Full string repr of longrepr |
| `.head_line` | str or None | Heading for failure output |

Class method: `TestReport.from_item_and_call(item, call)` -- create from Item and CallInfo.

## CallInfo

Wraps the result/exception of a function invocation during test protocol.

| Attribute | Type | Description |
|-----------|------|-------------|
| `.excinfo` | ExceptionInfo or None | Captured exception, if raised |
| `.result` | TResult | Return value (only if excinfo is None) |
| `.start` / `.stop` | float | System time |
| `.duration` | float | Duration in seconds |
| `.when` | `"collect"` / `"setup"` / `"call"` / `"teardown"` | Invocation context |

## Config

Access to configuration values, plugin manager, and hooks.

| Attribute/Method | Description |
|------------------|-------------|
| `.option` | `argparse.Namespace` with CLI options |
| `.rootpath` | Path to rootdir |
| `.inipath` | Path to config file (or None) |
| `.pluginmanager` | PytestPluginManager |
| `.stash` | Stash for plugin data |
| `.getoption(name, default=NOTSET, skip=False)` | Get CLI option value |
| `.getini(name)` | Get config file value |
| `.addinivalue_line(name, line)` | Append to a config option |
| `.get_verbosity(verbosity_type=None)` | Get verbosity level |

## ExitCode

| Code | Name | Value |
|------|------|-------|
| OK | `ExitCode.OK` | 0 |
| Tests failed | `ExitCode.TESTS_FAILED` | 1 |
| Interrupted | `ExitCode.INTERRUPTED` | 2 |
| Internal error | `ExitCode.INTERNAL_ERROR` | 3 |
| Usage error | `ExitCode.USAGE_ERROR` | 4 |
| No tests collected | `ExitCode.NO_TESTS_COLLECTED` | 5 |

## Hooks

### Decorators

```python
@pytest.hookimpl      # mark function as hook implementation
@pytest.hookspec      # mark function as hook specification (for plugins defining new hooks)
```

### Lifecycle Phases

**Bootstrapping** (internal/early plugins only):
- `pytest_load_initial_conftests(early_config, parser, args)`
- `pytest_cmdline_parse(pluginmanager, args) -> Config`
- `pytest_cmdline_main(config) -> ExitCode`

**Initialization:**
- `pytest_addoption(parser, pluginmanager)` -- register CLI options and ini values
- `pytest_configure(config)` -- initial configuration
- `pytest_sessionstart(session)` -- after Session created, before collection
- `pytest_sessionfinish(session, exitstatus)` -- after all tests, before exit
- `pytest_unconfigure(config)` -- before process exit

**Collection:**
- `pytest_collection(session)` -- perform collection phase
- `pytest_ignore_collect(collection_path, config) -> bool|None` -- ignore path?
- `pytest_collect_directory(path, parent) -> Collector|None` -- create directory collector
- `pytest_collect_file(file_path, parent) -> Collector|None` -- create file collector
- `pytest_pycollect_makemodule(module_path, parent) -> Module|None` -- create Module
- `pytest_pycollect_makeitem(collector, name, obj) -> Item|Collector|None` -- create items from Python objects
- `pytest_generate_tests(metafunc)` -- generate parametrized test calls
- `pytest_make_parametrize_id(config, val, argname) -> str|None` -- custom param IDs
- `pytest_collection_modifyitems(session, config, items)` -- filter/reorder items (in-place)
- `pytest_collection_finish(session)` -- after collection complete

**Test Running:**
- `pytest_runtestloop(session)` -- main test loop
- `pytest_runtest_protocol(item, nextitem)` -- full protocol for one item
- `pytest_runtest_logstart(nodeid, location)` -- before test
- `pytest_runtest_setup(item)` -- setup phase
- `pytest_runtest_call(item)` -- call phase (runs `item.runtest()`)
- `pytest_runtest_teardown(item, nextitem)` -- teardown phase
- `pytest_runtest_makereport(item, call) -> TestReport` -- create report for each phase
- `pytest_runtest_logfinish(nodeid, location)` -- after test
- `pytest_pyfunc_call(pyfuncitem)` -- call underlying test function

**Reporting:**
- `pytest_collectstart(collector)` -- collector starts
- `pytest_itemcollected(item)` -- item collected
- `pytest_collectreport(report)` -- collector finished
- `pytest_deselected(items)` -- items deselected (e.g. by -k)
- `pytest_runtest_logreport(report)` -- process TestReport for each phase
- `pytest_report_header(config, start_path) -> str|list[str]` -- add header info
- `pytest_report_collectionfinish(config, start_path, items) -> str|list[str]` -- after "collected X items"
- `pytest_report_teststatus(report, config) -> (category, letter, word)` -- customize status display
- `pytest_terminal_summary(terminalreporter, exitstatus, config)` -- add section to summary
- `pytest_assertrepr_compare(config, op, left, right) -> list[str]|None` -- custom assertion explanations
- `pytest_assertion_pass(item, lineno, orig, expl)` -- called on passing assertions (opt-in)

**Fixture hooks:**
- `pytest_fixture_setup(fixturedef, request) -> object|None` -- fixture setup
- `pytest_fixture_post_finalizer(fixturedef, request)` -- after fixture teardown

**Warning hooks:**
- `pytest_warning_recorded(warning_message, when, nodeid, location)` -- process captured warning

**Debugging:**
- `pytest_internalerror(excrepr, excinfo)` -- internal errors
- `pytest_keyboard_interrupt(excinfo)` -- Ctrl+C
- `pytest_exception_interact(node, call, report)` -- interactive exception handling
- `pytest_enter_pdb(config, pdb)` -- entering debugger
- `pytest_leave_pdb(config, pdb)` -- leaving debugger

### Hook Wrapper Pattern

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    # code before the hook runs
    outcome = yield
    # code after the hook runs
    result = outcome.get_result()  # or outcome.excinfo for exceptions
```

### conftest.py Scope Rules

- Hooks in conftest.py apply to tests in that directory and subdirectories
- Exception: `pytest_collection_modifyitems` always receives ALL items regardless of conftest location
- Some hooks are "initial conftests only" (bootstrap/initialization phase)

## Metafunc

Available in `pytest_generate_tests` hook and used by `@pytest.mark.parametrize`.

```python
def pytest_generate_tests(metafunc):
    if "db" in metafunc.fixturenames:
        metafunc.parametrize("db", ["sqlite", "postgres"], indirect=True)
```

| Attribute/Method | Description |
|------------------|-------------|
| `.fixturenames` | list of fixture names requested by the test |
| `.module` | The module object |
| `.config` | The pytest Config |
| `.function` | The underlying test function |
| `.cls` | The class object (or None) |
| `.definition` | The Function node |
| `.parametrize(argnames, argvalues, indirect=False, ids=None, scope=None)` | Add parametrized calls |

## Stash (Type-Safe Storage)

```python
# Define keys at module level
my_key = pytest.StashKey[str]()

# Store and retrieve
config.stash[my_key] = "value"
value = config.stash[my_key]        # type-safe: str
config.stash.get(my_key, "default") # with default
del config.stash[my_key]
my_key in config.stash              # membership test
len(config.stash)                   # number of entries
```

Available on `Config.stash`, `Node.stash` (and all subclasses).

## conftest.py Conventions

- **Fixture sharing:** Fixtures in conftest.py are available to all tests in that directory and below
- **Hook implementations:** Any hook can be implemented in conftest.py
- **Plugin loading:** `pytest_plugins = ["myapp.fixtures"]` to load plugin modules
- **Scope:** conftest.py files are directory-scoped; pytest walks up from test file to rootdir

## Quick Reference: Common Patterns

### Parametrize with conditional xfail

```python
@pytest.mark.parametrize("x,expected", [
    (1, 2),
    pytest.param(0, None, marks=pytest.mark.xfail(raises=ZeroDivisionError)),
])
def test_division(x, expected):
    assert 1 / x == expected
```

### Fixture requesting another fixture

```python
@pytest.fixture
def db_session(tmp_path):
    db_file = tmp_path / "test.db"
    conn = connect(db_file)
    yield conn
    conn.close()
```

### Dynamic fixture selection

```python
@pytest.fixture
def data(request):
    return request.getfixturevalue(request.param)
```

### Custom assertion messages

```python
# In conftest.py
def pytest_assertrepr_compare(config, op, left, right):
    if isinstance(left, MyClass) and isinstance(right, MyClass) and op == "==":
        return ["Comparing MyClass instances:", f"  left:  {left}", f"  right: {right}"]
```

### Modify test collection order

```python
# In conftest.py
def pytest_collection_modifyitems(session, config, items):
    items.sort(key=lambda item: item.get_closest_marker("slow") is not None)
```
