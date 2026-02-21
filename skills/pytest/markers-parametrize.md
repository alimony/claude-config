# pytest: Markers and Parametrize
Based on pytest 9.0.x documentation.

## Core Concepts

**Markers** are metadata you attach to test functions, classes, or modules. They serve two purposes:
1. **Built-in behavior** -- `skip`, `skipif`, `xfail`, `parametrize`, `usefixtures`, `filterwarnings`
2. **Custom selection** -- tag tests for filtering with `-m` expressions

**Parametrize** runs the same test function multiple times with different inputs, generating a separate test ID for each combination.

Markers only apply to tests, not to fixtures.

---

## Registering Custom Markers

Always register markers. Unregistered markers emit warnings; with `strict_markers` they cause errors.

```toml
# pyproject.toml
[pytest]
addopts = ["--strict-markers"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: requires external services",
    "serial",
]
```

Register programmatically in `conftest.py`:

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "env(name): mark test to run only on named environment"
    )
```

---

## Applying Markers

### To a function

```python
@pytest.mark.slow
def test_heavy_computation():
    ...
```

### To a class (applies to all methods)

```python
@pytest.mark.slow
class TestHeavyStuff:
    def test_one(self): ...
    def test_two(self): ...
```

### To an entire module

```python
import pytest
pytestmark = pytest.mark.slow

# or multiple:
pytestmark = [pytest.mark.slow, pytest.mark.integration]
```

### Markers with arguments

```python
@pytest.mark.device(serial="123")
def test_specific_device():
    ...
```

---

## Selecting Tests

### `-m` expressions (marker-based)

```bash
pytest -m slow                        # only slow tests
pytest -m "not slow"                  # everything except slow
pytest -m "slow and integration"      # both markers
pytest -m "slow or integration"       # either marker
pytest -m "device(serial='123')"      # marker with keyword args
```

`-m` supports `and`, `or`, `not`, and parentheses. Keyword argument matching uses `int`, `str`, `bool`, and `None` values only.

### `-k` expressions (name-based)

`-k` matches against test names, parent names (module, class), markers, and attributes. Case-insensitive.

```bash
pytest -k http                        # name contains "http"
pytest -k "not send_http"             # exclude by name
pytest -k "http or quick"             # either substring
pytest -k "TestClass and test_method" # combine
```

### Node IDs (exact selection)

```bash
pytest test_server.py::TestClass::test_method
pytest test_server.py::test_send_http
pytest test_file.py::test_eval[6*9-42]    # specific parametrized case
```

---

## Skip and Skipif

### Unconditional skip

```python
@pytest.mark.skip(reason="not implemented yet")
def test_future_feature():
    ...
```

### Conditional skip

```python
import sys

@pytest.mark.skipif(sys.version_info < (3, 13), reason="requires python 3.13+")
def test_new_feature():
    ...

@pytest.mark.skipif(sys.platform == "win32", reason="linux only")
class TestPosixCalls:
    def test_function(self): ...
```

### Imperative skip (inside test body)

```python
def test_function():
    if not valid_config():
        pytest.skip("unsupported configuration")
```

### Skip entire module

```python
import sys
import pytest

if not sys.platform.startswith("win"):
    pytest.skip("windows-only tests", allow_module_level=True)
```

### Skip on missing import

```python
docutils = pytest.importorskip("docutils")
docutils = pytest.importorskip("docutils", minversion="0.3")  # checks __version__
```

### Reusable skip conditions

```python
# conftest.py or shared module
import pytest
requires_linux = pytest.mark.skipif(sys.platform != "linux", reason="linux only")

# test file
@requires_linux
def test_linux_thing():
    ...
```

Multiple `skipif` decorators: test is skipped if **any** condition is true.

### Quick reference

| Pattern | Code |
|---------|------|
| Skip unconditionally | `@pytest.mark.skip(reason="...")` |
| Skip on condition | `@pytest.mark.skipif(condition, reason="...")` |
| Skip at runtime | `pytest.skip("reason")` |
| Skip whole module | `pytest.skip("reason", allow_module_level=True)` |
| Skip on missing import | `pytest.importorskip("module")` |

---

## XFail: Expected Failures

Mark tests you **expect** to fail. They run but don't count as failures.

### Basic xfail

```python
@pytest.mark.xfail
def test_known_bug():
    assert 1 == 2  # reports as XFAIL, not FAIL
```

### With condition and reason

```python
@pytest.mark.xfail(sys.platform == "win32", reason="bug in 3rd party lib")
def test_function():
    ...
```

### Strict xfail (XPASS = failure)

By default, a test marked `xfail` that unexpectedly passes (XPASS) does **not** fail the suite. Use `strict=True` to make XPASS a failure:

```python
@pytest.mark.xfail(strict=True)
def test_should_fail():
    ...  # if this passes, the test suite FAILS
```

Set globally:

```toml
# pyproject.toml
[pytest]
xfail_strict = true
```

### Specific exception type

```python
@pytest.mark.xfail(raises=RuntimeError)
def test_function():
    ...  # only XFAIL if it raises RuntimeError; other exceptions = real failure
```

### Don't even run the test

```python
@pytest.mark.xfail(run=False)
def test_crashes_interpreter():
    ...  # marked XFAIL without executing
```

### Imperative xfail

```python
def test_function():
    if not valid_config():
        pytest.xfail("failing configuration")
    # no code after pytest.xfail() executes
```

### Ignore all xfail markers

```bash
pytest --runxfail  # runs xfail tests as normal tests
```

### Viewing xfail/skip details

```bash
pytest -rxXs  # show details for xfailed (x), xpassed (X), and skipped (s)
```

---

## Parametrize

### Basic usage

```python
@pytest.mark.parametrize("input,expected", [
    ("3+5", 8),
    ("2+4", 6),
    ("6*9", 54),
])
def test_eval(input, expected):
    assert eval(input) == expected
```

Each tuple becomes a separate test: `test_eval[3+5-8]`, `test_eval[2+4-6]`, `test_eval[6*9-54]`.

### Multiple parameters as tuple of names

Both forms work:

```python
# String (comma-separated)
@pytest.mark.parametrize("a,b,expected", [...])

# Tuple/list of strings
@pytest.mark.parametrize(("a", "b", "expected"), [...])
```

### Custom test IDs

**Option 1: `ids` as list of strings**

```python
@pytest.mark.parametrize("a,b,expected", testdata, ids=["forward", "backward"])
def test_timedistance(a, b, expected):
    ...
```

**Option 2: `ids` as callable**

```python
def idfn(val):
    if isinstance(val, datetime):
        return val.strftime("%Y%m%d")
    # return None to use default representation

@pytest.mark.parametrize("a,b,expected", testdata, ids=idfn)
def test_timedistance(a, b, expected):
    ...
```

**Option 3: `pytest.param` with `id`**

```python
@pytest.mark.parametrize("a,b,expected", [
    pytest.param(datetime(2001, 12, 12), datetime(2001, 12, 11), timedelta(1), id="forward"),
    pytest.param(datetime(2001, 12, 11), datetime(2001, 12, 12), timedelta(-1), id="backward"),
])
def test_timedistance(a, b, expected):
    ...
```

### Stacking parametrize for combinations

```python
@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("y", [2, 3])
def test_foo(x, y):
    pass
# Generates: test_foo[2-0], test_foo[2-1], test_foo[3-0], test_foo[3-1]
```

This produces the **cartesian product** of all parameter sets.

### Parametrize on class (applies to all methods)

```python
@pytest.mark.parametrize("n,expected", [(1, 2), (3, 4)])
class TestClass:
    def test_simple(self, n, expected):
        assert n + 1 == expected

    def test_other(self, n, expected):
        assert (n * 1) + 1 == expected
```

### Parametrize on module

```python
pytestmark = pytest.mark.parametrize("n,expected", [(1, 2), (3, 4)])
```

---

## pytest.param: Marks and IDs on Individual Cases

`pytest.param` wraps parameter values to attach marks or IDs to specific cases.

```python
@pytest.mark.parametrize("test_input,expected", [
    ("3+5", 8),
    ("2+4", 6),
    pytest.param("6*9", 42, marks=pytest.mark.xfail),
    pytest.param("2**8", 256, id="power"),
    pytest.param(
        "os.getcwd()", None,
        marks=pytest.mark.skipif(sys.platform == "win32", reason="posix only"),
    ),
])
def test_eval(test_input, expected):
    assert eval(test_input) == expected
```

### Skip/xfail individual parametrized cases

```python
@pytest.mark.parametrize(("n", "expected"), [
    (1, 2),
    pytest.param(1, 0, marks=pytest.mark.xfail),
    pytest.param(1, 3, marks=pytest.mark.xfail(reason="some bug")),
    (2, 3),
    pytest.param(
        10, 11,
        marks=pytest.mark.skipif(sys.version_info >= (3, 0), reason="py2k"),
    ),
])
def test_increment(n, expected):
    assert n + 1 == expected
```

---

## Indirect Parametrize (via Fixtures)

Pass parametrized values **through a fixture** instead of directly to the test. The fixture receives the value as `request.param`.

### All arguments indirect

```python
@pytest.fixture
def fixt(request):
    return request.param * 3

@pytest.mark.parametrize("fixt", ["a", "b"], indirect=True)
def test_indirect(fixt):
    assert len(fixt) == 3  # "aaa", "bbb"
```

### Selective indirect (some args through fixtures, others direct)

```python
@pytest.fixture
def x(request):
    return request.param * 3

@pytest.mark.parametrize("x, y", [("a", "b")], indirect=["x"])
def test_indirect(x, y):
    assert x == "aaa"  # went through fixture
    assert y == "b"    # passed directly
```

### Deferred setup pattern

Use indirect to defer expensive resource creation to test runtime instead of collection time:

```python
# conftest.py
@pytest.fixture
def db(request):
    if request.param == "postgres":
        return PostgresDB()
    elif request.param == "sqlite":
        return SqliteDB()

# test file
@pytest.mark.parametrize("db", ["postgres", "sqlite"], indirect=True)
def test_db_initialized(db):
    assert db.is_connected()
```

---

## pytest_generate_tests Hook

For dynamic parametrization based on command-line options or other runtime state:

```python
# conftest.py
def pytest_addoption(parser):
    parser.addoption("--all", action="store_true", help="run all combinations")

def pytest_generate_tests(metafunc):
    if "param1" in metafunc.fixturenames:
        end = 5 if metafunc.config.getoption("all") else 2
        metafunc.parametrize("param1", range(end))
```

```python
# test_compute.py
def test_compute(param1):
    assert param1 < 4
```

```bash
pytest -q test_compute.py          # runs 2 tests (param1=0,1)
pytest -q --all test_compute.py    # runs 5 tests (param1=0..4)
```

The hook can live in `conftest.py`, directly in a test module, or inside a test class.

---

## Scenario-Based Testing

Use `pytest_generate_tests` to parametrize from class-level scenario definitions:

```python
def pytest_generate_tests(metafunc):
    idlist = []
    argvalues = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append([x[1] for x in items])
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")

class TestSampleWithScenarios:
    scenarios = [
        ("basic", {"attribute": "value"}),
        ("advanced", {"attribute": "value2"}),
    ]

    def test_demo1(self, attribute):
        assert isinstance(attribute, str)

    def test_demo2(self, attribute):
        assert isinstance(attribute, str)
```

---

## Reading Markers in Fixtures and Plugins

Access markers on the current test item via `request.node`:

```python
@pytest.fixture
def my_fixture(request):
    marker = request.node.get_closest_marker("env")
    if marker is None:
        env_name = "default"
    else:
        env_name = marker.args[0]
    # use env_name...
```

---

## Common Pitfalls

### 1. Unregistered markers silently ignored

Without `strict_markers`, a typo like `@pytest.mark.slo` (missing `w`) silently does nothing. Always enable strict mode.

### 2. Parameter values are shared references (not copied)

```python
# If test_a mutates `data`, test_b sees the mutation
data = [1, 2, 3]

@pytest.mark.parametrize("d", [data])
def test_a(d):
    d.append(4)  # mutates the original list!
```

### 3. Empty parameter sets

If parametrize receives an empty list, the test is **skipped** by default. Control this with:

```toml
# pyproject.toml
[pytest]
empty_parameter_set_mark = "fail"  # or "skip" (default) or "xfail"
```

### 4. Duplicate parameter names across multiple parametrize calls

```python
# This raises an error -- parameter names cannot overlap
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("x", [3, 4])  # ERROR: duplicate "x"
def test_foo(x):
    ...
```

### 5. Marker inheritance on classes

Markers on a class apply to **all** test methods in that class. There is no way to "un-mark" a method. If you need some methods without the marker, use separate classes.

### 6. `pytest.xfail()` vs `@pytest.mark.xfail`

- `pytest.xfail()` (imperative) immediately stops test execution -- no code after it runs
- `@pytest.mark.xfail` (decorator) lets the test run to completion and evaluates the outcome

---

## Quick Reference

| What you want | How |
|---------------|-----|
| Skip a test | `@pytest.mark.skip(reason="...")` |
| Conditional skip | `@pytest.mark.skipif(cond, reason="...")` |
| Expected failure | `@pytest.mark.xfail` |
| Strict expected failure | `@pytest.mark.xfail(strict=True)` |
| Run with multiple inputs | `@pytest.mark.parametrize("a,b", [(1,2), (3,4)])` |
| Name parametrized cases | `pytest.param(1, 2, id="case_name")` |
| Mark one parametrized case | `pytest.param(1, 2, marks=pytest.mark.xfail)` |
| Cartesian product | Stack multiple `@pytest.mark.parametrize` |
| Parametrize via fixture | `@pytest.mark.parametrize("f", [...], indirect=True)` |
| Custom marker | `@pytest.mark.my_tag` (register it!) |
| Select by marker | `pytest -m "slow and not integration"` |
| Select by name | `pytest -k "test_login or test_logout"` |
| Dynamic parametrize | `pytest_generate_tests` hook |
| See all registered markers | `pytest --markers` |
| Strict marker checking | `addopts = ["--strict-markers"]` in config |
| View skip/xfail details | `pytest -rxXs` |
