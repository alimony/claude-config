# pytest: Fixtures
Based on pytest 9.0.x documentation.

## Why Fixtures Exist

Fixtures replace xUnit-style `setUp`/`tearDown` with **dependency injection**. Instead of implicit shared state, tests declare exactly what they need by naming fixtures as function parameters. pytest resolves the dependency graph automatically.

**Advantages over setUp/tearDown:**
- Tests declare dependencies explicitly (no hidden shared state)
- Fixtures compose — each fixture can depend on other fixtures
- Fixtures have configurable scope (function, class, module, package, session)
- Teardown is colocated with setup (via `yield`)
- Fixtures are reusable across modules via `conftest.py`

```python
# setUp/tearDown style — implicit, monolithic
class TestUser(TestCase):
    def setUp(self):
        self.db = connect_db()
        self.user = create_user(self.db)

    def tearDown(self):
        self.db.close()

    def test_user_name(self):
        assert self.user.name == "default"

# Fixture style — explicit, composable
@pytest.fixture
def db():
    conn = connect_db()
    yield conn
    conn.close()

@pytest.fixture
def user(db):
    return create_user(db)

def test_user_name(user):
    assert user.name == "default"
```

---

## Defining Fixtures

### Basic Fixture

```python
@pytest.fixture
def smtp_connection():
    return smtplib.SMTP("smtp.gmail.com", 587)
```

A test requests it by naming it as a parameter:

```python
def test_ehlo(smtp_connection):
    response, _ = smtp_connection.ehlo()
    assert response == 250
```

### Fixture with Teardown (yield)

Code before `yield` is setup. Code after `yield` is teardown. The yielded value is passed to the test.

```python
@pytest.fixture
def db_connection():
    conn = create_connection()
    yield conn          # <-- test receives this
    conn.rollback()     # <-- runs after test finishes
    conn.close()
```

**Critical:** If setup code (before `yield`) raises an exception, teardown code (after `yield`) does NOT run. For multi-step setup, use `addfinalizer` or try/finally:

```python
# Safe: teardown always runs for completed setup steps
@pytest.fixture
def db_connection():
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()
```

### addfinalizer (Alternative Teardown)

Use `request.addfinalizer` when you need multiple independent teardown steps or conditional cleanup:

```python
@pytest.fixture
def resource(request):
    conn = connect()
    request.addfinalizer(conn.disconnect)  # always runs

    table = create_table(conn)
    request.addfinalizer(table.drop)       # runs only if create_table succeeded

    return table
```

Finalizers run in LIFO order (last registered, first executed). If `create_table` raises, only `conn.disconnect` runs because `table.drop` was never registered.

| Approach | Use When |
|----------|----------|
| `yield` | Single setup/teardown pair, straightforward cleanup |
| `addfinalizer` | Multiple independent cleanup steps, conditional teardown |
| `yield` + `try/finally` | Single pair but setup might fail after partial work |

---

## Fixture Scope

Scope controls how long a fixture instance lives and how many tests share it.

```python
@pytest.fixture(scope="module")
def db():
    conn = create_connection()
    yield conn
    conn.close()
```

| Scope | Lifetime | Destroyed After |
|-------|----------|-----------------|
| `"function"` (default) | One test | Each test function |
| `"class"` | One test class | Last test in the class |
| `"module"` | One `.py` file | Last test in the module |
| `"package"` | One package directory | Last test in the package |
| `"session"` | Entire test run | End of the test session |

### Scope Rules

- Higher-scoped fixtures execute before lower-scoped ones within a test
- A fixture can depend on same-scope or broader-scope fixtures
- A fixture CANNOT depend on narrower-scope fixtures (causes `ScopeMismatch`)

```python
# GOOD: session-scoped depends on session-scoped
@pytest.fixture(scope="session")
def db(db_engine):  # db_engine must be session-scoped too
    ...

# BAD: session-scoped depends on function-scoped — ScopeMismatch error
@pytest.fixture(scope="session")
def db(tmp_path):  # tmp_path is function-scoped!
    ...

# FIX: use the session-scoped equivalent
@pytest.fixture(scope="session")
def db(tmp_path_factory):  # tmp_path_factory is session-scoped
    ...
```

### Dynamic Scope

Pass a callable to `scope` to decide at collection time:

```python
def determine_scope(fixture_name, config):
    if config.getoption("--reuse-db"):
        return "session"
    return "function"

@pytest.fixture(scope=determine_scope)
def db():
    ...
```

---

## Autouse Fixtures

Autouse fixtures apply automatically to every test that can see them, without being explicitly requested.

```python
@pytest.fixture(autouse=True)
def reset_state():
    GlobalState.reset()
    yield
    GlobalState.reset()
```

### Autouse Scope

| Defined In | Applies To |
|------------|-----------|
| Test module | All tests in that module |
| `conftest.py` | All tests in that directory and subdirectories |
| Plugin | All tests (unless restricted) |

**Use autouse sparingly.** Explicit fixture requests are easier to understand. Autouse is appropriate for:
- Environment reset that every test needs
- Timing/logging that should be invisible
- Security context setup (like RLS in this project)

---

## conftest.py and Fixture Discovery

### How Discovery Works

pytest discovers fixtures by searching upward from the test file:

1. The test module itself
2. `conftest.py` in the same directory
3. `conftest.py` in parent directories (up to the rootdir)
4. Installed plugins

Tests can see fixtures from their own level and above, never from sibling or child directories.

```
tests/
    conftest.py          # fixtures available to ALL tests
    test_top.py
    subpackage/
        conftest.py      # fixtures available to subpackage only
        test_sub.py      # sees both conftest.py files
    other/
        test_other.py    # sees only top conftest.py, NOT subpackage/conftest.py
```

### Overriding Fixtures

A fixture with the same name in a narrower scope overrides the broader one:

```python
# tests/conftest.py
@pytest.fixture
def user():
    return User(role="viewer")

# tests/admin/conftest.py — overrides for admin tests
@pytest.fixture
def user():
    return User(role="admin")
```

You can also override at the test module or test class level. The override can even call the original via `request`:

```python
# tests/special/conftest.py
@pytest.fixture
def user(user):  # receives the parent fixture's value
    user.special_flag = True
    return user
```

---

## Parametrized Fixtures

Run the same test with different fixture values. Each parameter creates a separate test ID.

```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def db(request):
    conn = connect(request.param)
    yield conn
    conn.close()

def test_query(db):  # runs 3 times, once per DB
    assert db.execute("SELECT 1")
```

### Custom Test IDs

```python
@pytest.fixture(params=[
    pytest.param("sqlite", id="lite"),
    pytest.param("postgres", id="pg"),
])
def db(request):
    return connect(request.param)
```

Or pass `ids` directly:

```python
@pytest.fixture(params=["sqlite", "postgres"], ids=["lite", "pg"])
def db(request):
    return connect(request.param)
```

### Indirect Parametrization

Pass parameters to fixtures from `@pytest.mark.parametrize`:

```python
@pytest.fixture
def user(request):
    return create_user(role=request.param)

@pytest.mark.parametrize("user", ["admin", "viewer"], indirect=True)
def test_permissions(user):
    ...
```

When `indirect=True`, the parametrize values are passed to the fixture as `request.param` instead of directly to the test function.

For selective indirection (some params to fixtures, some to test):

```python
@pytest.mark.parametrize(
    "user, expected_status",
    [("admin", 200), ("viewer", 403)],
    indirect=["user"],  # only "user" goes through the fixture
)
def test_endpoint(user, expected_status):
    assert user.get("/admin").status_code == expected_status
```

---

## Fixture Composition

Fixtures can depend on other fixtures, forming a DAG (directed acyclic graph).

```python
@pytest.fixture
def db():
    return create_db()

@pytest.fixture
def user(db):
    return db.create_user("test@example.com")

@pytest.fixture
def authenticated_client(user):
    client = TestClient()
    client.login(user)
    return client

def test_dashboard(authenticated_client):
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 200
```

pytest resolves the full graph: `db` -> `user` -> `authenticated_client` -> test. Teardown runs in reverse order.

### Execution Order

1. Higher-scoped fixtures run first (session before function)
2. Within the same scope, order follows the dependency graph
3. Autouse fixtures run before non-autouse fixtures at the same scope
4. Fixtures that are dependencies of autouse fixtures effectively become autouse too

---

## Factory Pattern

When a test needs multiple instances from the same fixture, return a factory function:

```python
@pytest.fixture
def make_user(db):
    created = []

    def _make_user(name="default", role="viewer"):
        user = db.create_user(name=name, role=role)
        created.append(user)
        return user

    yield _make_user

    # Cleanup all created users
    for user in created:
        db.delete_user(user)

def test_transfer(make_user):
    sender = make_user("alice", role="admin")
    receiver = make_user("bob", role="viewer")
    assert transfer(sender, receiver, amount=100)
```

**When to use factories:**
- Test needs multiple instances of the same thing
- Each instance needs different configuration
- You want shared cleanup logic

---

## The `request` Object

The special `request` fixture provides context about the requesting test.

| Attribute | Description |
|-----------|-------------|
| `request.param` | Current parameter value (parametrized fixtures) |
| `request.fixturenames` | List of all fixture names active in this request |
| `request.node` | The underlying test collection node |
| `request.config` | The pytest `Config` object |
| `request.cls` | Test class (or `None` for function tests) |
| `request.instance` | Test class instance (or `None`) |
| `request.function` | The test function object |
| `request.fspath` | File system path of the test module |
| `request.scope` | Scope string of the current fixture |

### Using request for Conditional Behavior

```python
@pytest.fixture
def db(request):
    conn = connect()
    if request.cls and hasattr(request.cls, "db_seed"):
        conn.seed(request.cls.db_seed)
    yield conn
    conn.close()
```

---

## `@pytest.mark.usefixtures`

Apply fixtures to a class or module without receiving them as parameters:

```python
@pytest.mark.usefixtures("clean_db", "reset_cache")
class TestUserService:
    def test_create(self):
        ...

    def test_delete(self):
        ...
```

Useful when the test needs the fixture's side effect but not its return value.

Can also be applied at module level:

```python
pytestmark = pytest.mark.usefixtures("clean_db")
```

---

## Built-in Fixtures Reference

### Temporary Files and Directories

| Fixture | Scope | Description |
|---------|-------|-------------|
| `tmp_path` | function | `pathlib.Path` to a unique temp directory per test |
| `tmp_path_factory` | session | Factory to create temp directories (for broader scopes) |

```python
def test_write_file(tmp_path):
    p = tmp_path / "output.txt"
    p.write_text("hello")
    assert p.read_text() == "hello"

@pytest.fixture(scope="session")
def shared_data(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    # ... populate shared test data
    return d
```

### Output Capture

| Fixture | Captures | Format |
|---------|----------|--------|
| `capsys` | `sys.stdout` / `sys.stderr` | text (str) |
| `capsysbinary` | `sys.stdout` / `sys.stderr` | binary (bytes) |
| `capfd` | file descriptors 1 and 2 | text (str) |
| `capfdbinary` | file descriptors 1 and 2 | binary (bytes) |

```python
def test_print(capsys):
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == ""
```

Use `capfd` when the code writes directly to file descriptors (e.g., C extensions) rather than `sys.stdout`.

### Logging

```python
def test_logging(caplog):
    import logging
    logger = logging.getLogger(__name__)

    with caplog.at_level(logging.WARNING):
        logger.warning("watch out")
        logger.info("ignored")

    assert "watch out" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
```

| Property/Method | Returns |
|-----------------|---------|
| `caplog.text` | Formatted log output string |
| `caplog.messages` | List of format-interpolated message strings |
| `caplog.records` | List of `logging.LogRecord` instances |
| `caplog.record_tuples` | List of `(logger_name, level, message)` tuples |
| `caplog.clear()` | Reset captured records |
| `caplog.at_level(level, logger=None)` | Context manager to set log level |
| `caplog.set_level(level, logger=None)` | Set log level for the test |

### Monkeypatch

Temporarily modify objects, environment, and paths. All changes are undone after the test.

```python
def test_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    assert os.environ["API_KEY"] == "test-key"

def test_patch(monkeypatch):
    monkeypatch.setattr("mymodule.expensive_call", lambda: "mocked")
    assert mymodule.expensive_call() == "mocked"
```

| Method | Purpose |
|--------|---------|
| `setattr(target, name, value, raising=True)` | Replace attribute on object |
| `delattr(target, name, raising=True)` | Delete attribute from object |
| `setitem(mapping, key, value)` | Set dictionary item |
| `delitem(mapping, key, raising=True)` | Delete dictionary item |
| `setenv(name, value, prepend=None)` | Set environment variable |
| `delenv(name, raising=True)` | Delete environment variable |
| `syspath_prepend(path)` | Prepend to `sys.path` |
| `chdir(path)` | Change working directory |
| `context()` | Context manager returning a fresh `MonkeyPatch` |

**`setattr` string form** (patches by import path):

```python
# These are equivalent:
monkeypatch.setattr(mymodule, "func", mock_func)
monkeypatch.setattr("mymodule.func", mock_func)
```

The `raising=True` default means it raises `AttributeError`/`KeyError` if the target doesn't exist — protecting against typos.

### Warnings

```python
def test_deprecation(recwarn):
    warnings.warn("old api", DeprecationWarning)
    assert len(recwarn) == 1
    w = recwarn.pop(DeprecationWarning)
    assert "old api" in str(w.message)
```

Alternative: `pytest.warns` context manager is often more readable:

```python
def test_deprecation():
    with pytest.warns(DeprecationWarning, match="old api"):
        deprecated_function()
```

### Configuration and Metadata

| Fixture | Purpose |
|---------|---------|
| `pytestconfig` | Access to the `Config` object (command-line options, ini settings) |
| `cache` | Persist values across test runs (`cache.get`/`cache.set`) |
| `record_property` | Add `(name, value)` properties to the test (shows in JUnit XML) |
| `record_testsuite_property` | Add properties to the test suite (JUnit XML `<testsuite>`) |
| `doctest_namespace` | Dict injected into doctest namespace |

```python
def test_with_metadata(record_property):
    record_property("priority", "high")
    ...

def test_caching(cache):
    val = cache.get("my/key", default=None)
    if val is None:
        val = expensive_computation()
        cache.set("my/key", val)
    assert val > 0
```

---

## Common Patterns

### Fixture Returning None (Side-Effect Only)

```python
@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Prevent all tests from making real HTTP requests."""
    monkeypatch.delattr("urllib3.HTTPConnectionPool.urlopen")
```

No `return` or `yield` needed. The fixture exists for its side effect only.

### Conditional Skip in Fixture

```python
@pytest.fixture
def redis_client():
    try:
        client = redis.Redis()
        client.ping()
    except redis.ConnectionError:
        pytest.skip("Redis not available")
    yield client
    client.flushdb()
```

### Fixture with Marks

```python
@pytest.fixture(params=[
    pytest.param("fast", marks=pytest.mark.fast),
    pytest.param("slow", marks=pytest.mark.slow),
])
def backend(request):
    return create_backend(request.param)
```

### Shared Fixture Across Test Classes

```python
# conftest.py
@pytest.fixture(scope="class")
def db_class(request):
    conn = create_db()
    request.cls.db = conn     # attach to the class
    yield
    conn.close()

@pytest.mark.usefixtures("db_class")
class TestQuery:
    def test_select(self):
        self.db.execute("SELECT 1")  # accesses class attribute
```

---

## Common Pitfalls

### 1. ScopeMismatch

A broader-scoped fixture depending on a narrower-scoped fixture causes an error.

```python
# ERROR: session-scoped fixture uses function-scoped tmp_path
@pytest.fixture(scope="session")
def shared_dir(tmp_path):       # ScopeMismatch!
    return tmp_path / "shared"

# FIX: use session-scoped equivalent
@pytest.fixture(scope="session")
def shared_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("shared")
```

### 2. Yield Teardown Skipped on Setup Failure

If setup raises before `yield`, teardown never runs:

```python
# DANGEROUS: if step_one fails, cleanup for step_two never registered
@pytest.fixture
def resource():
    a = step_one()       # if this raises...
    b = step_two(a)      # ...this never runs
    yield b
    cleanup_b(b)         # ...and neither does this
    cleanup_a(a)

# SAFE: use addfinalizer for independent steps
@pytest.fixture
def resource(request):
    a = step_one()
    request.addfinalizer(lambda: cleanup_a(a))
    b = step_two(a)
    request.addfinalizer(lambda: cleanup_b(b))
    return b
```

### 3. Mutating Shared Fixtures

A session-scoped fixture shared across tests can be mutated by one test, affecting others:

```python
# DANGEROUS: tests share and mutate the same list
@pytest.fixture(scope="session")
def config():
    return {"plugins": ["base"]}

def test_add_plugin(config):
    config["plugins"].append("extra")  # mutates shared fixture!

def test_base_only(config):
    assert config["plugins"] == ["base"]  # FAILS — "extra" is still there
```

**Fix:** Return fresh copies, or use function scope, or use a factory.

### 4. Forgetting conftest.py Scope

Fixtures in `conftest.py` are visible to all tests in that directory and below. Putting test-specific fixtures in a shared conftest makes them available where they shouldn't be.

**Rule of thumb:** Put fixtures in the narrowest `conftest.py` that covers their actual users.

### 5. Autouse + Broad Scope = Surprise

An autouse session-scoped fixture in the top-level `conftest.py` runs for every test in your entire suite, even if most don't need it.

```python
# conftest.py at project root — affects EVERYTHING
@pytest.fixture(autouse=True, scope="session")
def seed_database():
    ...  # every test in the project triggers this
```

### 6. Parametrized Fixture Ordering

When a test uses multiple parametrized fixtures, pytest generates the cartesian product:

```python
@pytest.fixture(params=["a", "b"])
def x(request):
    return request.param

@pytest.fixture(params=[1, 2])
def y(request):
    return request.param

def test_combo(x, y):
    ...  # runs 4 times: (a,1), (a,2), (b,1), (b,2)
```

This can cause unexpected test explosion. Be intentional about combining parametrized fixtures.

---

## Quick Reference

### @pytest.fixture Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `scope` | `"function"` | Fixture lifetime: function, class, module, package, session, or callable |
| `params` | `None` | List of parameter values; creates one test per value |
| `autouse` | `False` | Auto-apply to all tests in scope without explicit request |
| `ids` | `None` | List of string IDs for parametrized values, or a callable |
| `name` | fixture function name | Override the fixture name (useful when the function name collides) |

### Fixture Function Signatures

```python
# Basic
@pytest.fixture
def thing():
    return Thing()

# With teardown
@pytest.fixture
def thing():
    t = Thing()
    yield t
    t.cleanup()

# With scope and params
@pytest.fixture(scope="module", params=["a", "b"])
def thing(request):
    return Thing(request.param)

# Factory
@pytest.fixture
def make_thing():
    def _make(**kwargs):
        return Thing(**kwargs)
    return _make

# Autouse
@pytest.fixture(autouse=True)
def reset():
    State.reset()
```

### conftest.py Cheatsheet

```
project/
    conftest.py              # session/package fixtures, shared utilities
    tests/
        conftest.py          # test-wide fixtures (db, client)
        unit/
            conftest.py      # unit-specific fixtures (mocks, stubs)
            test_service.py
        integration/
            conftest.py      # integration-specific (real DB, API client)
            test_api.py
```

- No imports needed — pytest auto-discovers fixtures from conftest.py
- Fixtures in parent conftest.py are available to child directories
- Same-name fixtures in child conftest.py override parent definitions
- conftest.py must NOT be in a directory with an `__init__.py` that would make it a regular package import (though this is rarely an issue in practice)
