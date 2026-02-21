# pytest: Assertions
Based on pytest 9.0.x documentation.

## Core Concept: Plain `assert`

pytest uses Python's built-in `assert` statement. No special assertion methods needed.

```python
# pytest — plain assert
def test_something():
    assert result == expected

# unittest — method soup (DON'T do this in pytest)
def test_something(self):
    self.assertEqual(result, expected)
    self.assertIn(item, collection)
    self.assertIsNone(value)
```

pytest rewrites `assert` statements at import time to produce detailed failure messages. You get introspection for free — intermediate values, diffs, and context are all shown automatically.

### What introspection catches

| Expression | pytest shows on failure |
|------------|------------------------|
| `assert a == b` | Values of `a` and `b`, plus diff |
| `assert a in b` | Value of `a` and contents of `b` |
| `assert a is b` | Identity vs equality distinction |
| `assert not x` | Value of `x` |
| `assert f() == g()` | Return values of both calls |
| `assert a == b == c` | All intermediate values |

Compound expressions with `and`/`or` also get introspected per-operand.

---

## Custom Assertion Messages

Add a message as the second argument to `assert`:

```python
def test_even(n):
    assert n % 2 == 0, f"Expected even, got {n}"
```

The message prints **alongside** the introspection output, not instead of it. Use messages to add *business context* that the raw values don't convey.

**When to use custom messages:**
- The assertion values don't explain the "why"
- Domain-specific context helps debugging
- Computed values lose their meaning (e.g., `assert score == 42` — what's 42?)

**When to skip them:**
- The assertion is self-explanatory: `assert user.is_active is True`
- The introspection output is already clear

---

## Asserting Exceptions: `pytest.raises`

### Basic usage (context manager)

```python
import pytest

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0
```

### Inspecting the exception

```python
def test_value_error_message():
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("invalid input: 42")

    assert "invalid input" in str(exc_info.value)
    assert exc_info.type is ValueError
```

`exc_info` is an `ExceptionInfo` instance. Access `.value`, `.type`, `.tb`, `.traceback`.

### Matching exception messages with `match`

```python
def test_error_message():
    with pytest.raises(ValueError, match=r"invalid .* 42"):
        raise ValueError("invalid input: 42")
```

`match` takes a **regex** pattern, matched with `re.search` (not fullmatch). This means partial matches work.

### Common pitfall: testing the wrong scope

```python
# BAD — too much code inside the with block
def test_something():
    with pytest.raises(ValueError):
        user = create_user("bad_email")     # might raise
        send_welcome_email(user)            # might ALSO raise
        log_event(user)                     # unclear what's tested

# GOOD — narrow scope
def test_something():
    user = create_user("bad_email")
    with pytest.raises(ValueError, match="invalid email"):
        validate_email(user.email)
```

### `pytest.raises` as a callable (less common)

```python
# Useful when you want to test a callable directly
pytest.raises(ValueError, int, "not_a_number")
```

### Expected exceptions that DON'T fire

If the code inside `pytest.raises` does NOT raise, pytest fails with:
```
Failed: DID NOT RAISE <class 'ValueError'>
```

---

## Asserting Warnings: `pytest.warns`

```python
import warnings
import pytest

def test_deprecation_warning():
    with pytest.warns(DeprecationWarning, match="old_function"):
        old_function()
```

Same pattern as `pytest.raises` — context manager, optional `match`.

---

## Floating Point: `pytest.approx`

Never compare floats with `==`. Use `pytest.approx`:

```python
# GOOD
assert 0.1 + 0.2 == pytest.approx(0.3)

# Also works with collections
assert [0.1 + 0.2, 0.2 + 0.4] == pytest.approx([0.3, 0.6])

# And dicts
assert {"a": 0.1 + 0.2} == pytest.approx({"a": 0.3})

# Custom tolerance
assert 2.0 == pytest.approx(2.02, abs=0.05)       # absolute tolerance
assert 2.0 == pytest.approx(2.02, rel=0.02)       # relative tolerance (2%)
```

**Default tolerance**: `1e-6` relative and `1e-12` absolute. The larger tolerance wins.

```python
# Comparing against zero — relative tolerance doesn't help
assert 0.0 == pytest.approx(0.0)           # passes (absolute kicks in)
assert 1e-10 == pytest.approx(0.0)         # passes (within 1e-12? no — FAILS)
assert 1e-10 == pytest.approx(0.0, abs=1e-9)  # passes
```

**Gotcha with zero**: When expected value is `0.0`, relative tolerance is meaningless (any% of 0 is 0). Always specify `abs` when comparing near zero.

---

## Comparing Collections

pytest provides rich diffs for collection comparisons. No special methods needed.

### Lists

```python
def test_list_comparison():
    assert [1, 2, 3] == [1, 2, 4]
```

Failure output:
```
E       assert [1, 2, 3] == [1, 2, 4]
E         At index 2 diff: 3 != 4
```

For long lists, pytest shows only the differing elements with indices.

### Dicts

```python
def test_dict_comparison():
    assert {"a": 1, "b": 2} == {"a": 1, "b": 3, "c": 4}
```

Failure output highlights:
- Keys with differing values
- Missing keys (left vs right)
- Extra keys

### Sets

```python
def test_set_comparison():
    assert {1, 2, 3} == {1, 2, 4}
```

Failure output shows set operations:
```
E         Extra items in the left set:
E         3
E         Extra items in the right set:
E         4
```

### Strings

```python
def test_long_string():
    assert "hello world foo" == "hello world bar"
```

Failure output shows a character-level diff, including the position of the first difference. For multiline strings, pytest uses a unified diff format.

---

## Assertion Rewriting Details

### How it works

pytest rewrites `assert` statements at import time (via an import hook). This is why:

1. **It works automatically** — no configuration needed
2. **It only affects test files** — production code is untouched
3. **`assert` in helper modules** is NOT rewritten by default

### Enabling rewriting in helper modules

If you have assertion helpers in non-test files, register them:

```python
# conftest.py
import pytest
pytest.register_assert_rewrite("myproject.testing.helpers")
```

Call this **before** the module is imported. Best place is `conftest.py`.

### When rewriting is disabled

`python -O` (optimize flag) strips assert statements entirely. Never run tests with `-O`.

---

## Writing Assertion Helpers

### The `__tracebackhide__` trick

When assertions fail inside helper functions, the traceback includes the helper internals, which is noise. Hide it:

```python
def assert_valid_email(email):
    __tracebackhide__ = True
    assert "@" in email, f"Invalid email: {email}"
    assert "." in email.split("@")[1], f"Invalid domain in: {email}"
```

Now failures point to the **caller**, not the helper internals.

`__tracebackhide__` can also be a callable for conditional hiding:

```python
__tracebackhide__ = lambda info: "AssertionError" in str(info.excrepr)
```

### Pattern: domain-specific assertion helpers

```python
# testing/assertions.py
def assert_donor_active(donor):
    """Assert a donor is in active state with clear failure message."""
    __tracebackhide__ = True
    assert donor.status == "active", (
        f"Expected donor {donor.id} to be active, "
        f"but status is '{donor.status}'"
    )

# In tests
def test_reactivation(self):
    donor = self.gen.crms.donor(status="inactive")
    reactivate(donor)
    assert_donor_active(donor)
```

---

## Failure Report Patterns

How pytest formats failures for different comparison types. Knowing this helps you write assertions that produce the best diagnostics.

### Equality with context

```python
# Test
def test_eq():
    assert 1 + 1 == 3

# Output
E       assert 2 == 3
E        +  where 2 = 1 + 1
```

pytest traces sub-expressions and shows "where" lines.

### Attribute/method chains

```python
class Foo:
    value = 42

def test_attr():
    foo = Foo()
    assert foo.value == 43

# Output shows:
E       assert 42 == 43
E        +  where 42 = <Foo>.value
```

### Long sequences — truncated diff

```python
def test_long_list():
    a = list(range(100))
    b = list(range(100))
    b[50] = 999
    assert a == b

# Output: shows index 50 difference, truncates the rest
E         At index 50 diff: 50 != 999
E         Full diff too long, showing first 10 entries...
```

### Multiline strings — unified diff

```python
def test_multiline():
    expected = "line1\nline2\nline3"
    actual   = "line1\nLINE2\nline3"
    assert actual == expected

# Output: unified diff format
E         - line1
E         - line2
E         + line1
E         + LINE2
```

### `in` operator

```python
def test_membership():
    assert "xyz" in "hello world"

# Output
E       assert 'xyz' in 'hello world'
```

### `not` expressions

```python
def test_negation():
    items = [1, 2, 3]
    assert not items

# Output
E       assert not [1, 2, 3]
```

---

## Quick Reference

| I want to... | Use this |
|---------------|----------|
| Compare values | `assert a == b` |
| Check truthiness | `assert result` |
| Check falsiness | `assert not result` |
| Check membership | `assert item in collection` |
| Check identity | `assert a is b` / `assert a is None` |
| Check type | `assert isinstance(obj, MyClass)` |
| Compare floats | `assert val == pytest.approx(expected)` |
| Expect exception | `with pytest.raises(ExcType):` |
| Expect exception + msg | `with pytest.raises(ExcType, match=r"pattern"):` |
| Inspect exception | `with pytest.raises(ExcType) as exc_info:` |
| Expect warning | `with pytest.warns(WarnType):` |
| Add context to failure | `assert x == y, "explanation"` |
| Hide helper traceback | `__tracebackhide__ = True` |
| Enable rewriting in helpers | `pytest.register_assert_rewrite("module")` |

---

## Common Pitfalls

### 1. Asserting on mutable state too early or too late

```python
# BAD — list mutated after assertion setup
items = get_items()
process(items)         # modifies items in place!
assert items == [1, 2, 3]  # comparing post-mutation
```

### 2. `pytest.raises` with too broad a scope

Keep the `with` block as narrow as possible. Only the line that should raise belongs inside.

### 3. Forgetting `match` is a regex

```python
# This matches — re.search, not re.fullmatch
with pytest.raises(ValueError, match="bad"):
    raise ValueError("very bad input")  # "bad" found via search

# Parentheses need escaping
with pytest.raises(ValueError, match=r"func\(\)"):
    raise ValueError("func() failed")
```

### 4. Comparing floats without `approx`

```python
# FAILS
assert 0.1 + 0.2 == 0.3

# PASSES
assert 0.1 + 0.2 == pytest.approx(0.3)
```

### 5. Using `assert` in non-test modules without registering

pytest only rewrites `assert` in test files and `conftest.py`. Assertions in your helper modules will produce Python's default (unhelpful) `AssertionError` unless you call `pytest.register_assert_rewrite`.

### 6. Catching too-broad exception types

```python
# BAD — catches any Exception, hides real bugs
with pytest.raises(Exception):
    do_something()

# GOOD — specific exception type
with pytest.raises(ConnectionError):
    do_something()
```

### 7. Asserting exception type without `pytest.raises`

```python
# BAD — manual try/except is verbose and error-prone
def test_error():
    try:
        do_something()
        assert False, "should have raised"
    except ValueError:
        pass

# GOOD
def test_error():
    with pytest.raises(ValueError):
        do_something()
```

---

## `pytest.raises` Gotcha: Group vs Match

`pytest.raises` has a `match` parameter but does NOT have a `message` parameter. The `match` argument is always a regex passed to `re.search()`.

```python
# re.search means partial match — this PASSES even though
# the message is "connection refused: host=example.com"
with pytest.raises(ConnectionError, match="connection refused"):
    ...

# To anchor, use ^ and $
with pytest.raises(ConnectionError, match=r"^connection refused$"):
    ...
```

---

## `ExceptionInfo` Reference

When using `pytest.raises` as a context manager, the `as` variable is an `ExceptionInfo`:

| Attribute | Type | Description |
|-----------|------|-------------|
| `.value` | `Exception` | The exception instance |
| `.type` | `type` | The exception class |
| `.tb` | `traceback` | The traceback object |
| `.match(pattern)` | method | Assert message matches regex |
| `str(exc_info)` | `str` | String representation of the exception |

```python
with pytest.raises(ValueError) as exc_info:
    validate(data)

# All of these work
assert exc_info.type is ValueError
assert "invalid" in str(exc_info.value)
exc_info.match(r"invalid field: \w+")
```
