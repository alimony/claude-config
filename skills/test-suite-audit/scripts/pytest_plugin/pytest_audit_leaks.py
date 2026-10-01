"""pytest plugin: name the test during which process-global state changed. It observes only.

Load it with `run_suite.py run --leak-probe PACKAGES`, which adds this folder to
PYTHONPATH and passes:

    -p pytest_audit_leaks --audit-leaks-json={RUN_DIR}/leaks.json --audit-leaks-packages=PACKAGES

After each test, including its fixture setup and teardown, it snapshots the
working directory, os.environ, sys.path, live threads, unittest.mock patches
started and not stopped, root logging handlers, signal handlers, and removed or
replaced sys.modules entries, and compares the snapshot with the one taken
after the previous test. For the comma-separated package prefixes in PACKAGES,
it also records every module-level and class-level attribute:

  * "rebound" means the name now points at another object, for example a
    function patched and never restored, or a setting with a new value;
    "rebound, was None" often means lazy initialisation;
  * "contents changed" means a dict, list, or set changed size, or one of its
    first 200 entries changed its key text or its value.

Numbers, strings, bytes, and None compare by value, and anything else by
identity, so restoring an equal copy counts as no change.

The report has two parts. "changes" maps each test ID to what changed during
it. "churn" lists each change seen in more than 5 tests once, with the number
of tests and the first three. Churn is often a counter or a cache, but it can
also be a shared mutable default that many tests fill, so check each entry.
Known false positives: session and module fixtures are blamed on the first test that uses
them (setup) and on the last test in their scope (teardown), and a lazily
created singleton shows in the first test that uses it. It misses attributes
that a test adds or deletes, changes nested inside an unchanged object, changes
past a container's 200th entry, and state outside the process (databases,
files, services). Confirm every hit with a pair run before you report it.

It refuses to run under xdist, because workers' results never reach the
controller: use -n 0. Each snapshot walks every loaded module in PACKAGES, so
name the project's own packages, as narrowly as the question allows. The run is
instrumented and never backs timing claims.

Standard library and pytest only; runs on Python 3.8+ with pytest 7+.
"""
from __future__ import annotations

import json
import logging
import os
import signal
import sys
import threading

import pytest

CHURN_TESTS = 5
_SCALARS = frozenset((type(None), bool, int, str, bytes))
_CONTAINERS = (dict, list, set)
_QUICK = _SCALARS | {float, *_CONTAINERS}  # an exact-type test first; isinstance only for the rest
_SIGNALS = [s for s in (getattr(signal, n, None) for n in ("SIGINT", "SIGTERM", "SIGALRM", "SIGHUP")) if s is not None]
_LEAKS: dict[str, list[str]] = {}
_PACKAGES: tuple[str, ...] = ()
_CHECKED = 0
_LAST: dict | None = None


def _element(obj):
    """A comparable stand-in: the value of an immutable scalar, otherwise the object's identity."""
    kind = type(obj)  # exact types, so a subclass with an odd __eq__ falls back to identity
    if kind in _SCALARS:
        return obj
    if kind is float:
        return repr(obj)  # NaN never equals itself
    return ("id", id(obj))


def _fingerprint(obj) -> tuple:
    """Scalars by value; dicts, lists, and sets (and their subclasses) by identity plus contents."""
    kind = type(obj)
    if kind in _SCALARS:
        return ("v", obj)
    if kind is float:
        return ("v", repr(obj))
    try:
        if isinstance(obj, dict):
            return ("c", id(obj), len(obj), tuple((repr(k)[:80], _element(v)) for k, v in list(obj.items())[:200]))
        return ("c", id(obj), len(obj), tuple(_element(v) for v in list(obj)[:200]))
    except Exception:  # another thread changed it while it was read, or a key's repr failed
        return ("u", id(obj))


def _namespace(space: dict) -> tuple:
    """Names and identities in bulk (fast), plus fingerprints of the scalars and containers."""
    names = tuple(space)
    values = tuple(space.values())
    tracked = {
        k: _fingerprint(v)
        for k, v in zip(names, values)
        if (type(v) in _QUICK or isinstance(v, _CONTAINERS)) and not k.startswith("__")
    }
    return names, tuple(map(id, values)), tracked


def _package_state() -> dict[str, tuple]:
    state = {}
    for name, module in list(sys.modules.items()):
        if module is None or not name.startswith(_PACKAGES):
            continue
        try:
            space = vars(module)
        except TypeError:
            continue
        classes = {
            attr: (id(value), _namespace(dict(vars(value))))
            for attr, value in list(space.items())
            if isinstance(value, type) and getattr(value, "__module__", None) == name and not attr.startswith("__")
        }
        state[name] = (_namespace(dict(space)), classes)
    return state


def _attribute_change(was: tuple | None, now: tuple | None, rebound: bool) -> str | None:
    """Label one attribute whose identity or contents changed, or None if it holds an equal value."""
    if was is not None and now is not None:
        if was == now:
            return None
        if was[0] == now[0] == "c":
            if was[1] == now[1]:
                return "contents changed"
            if was[2:] == now[2:]:
                return None  # an equal copy
        elif "u" in (was[0], now[0]) and was[1] == now[1]:
            return None  # unreadable at one end, same object at both
        elif was[0] == now[0] == "v" and not rebound:
            return None
    elif not rebound:
        return None
    return "rebound, was None" if was == ("v", None) else "rebound"


def _namespace_changes(prefix: str, before: tuple, after: tuple) -> list[str]:
    names, ids, tracked = before
    now_names, now_ids, now_tracked = after
    if names == now_names:
        if ids == now_ids:
            moved = set()
        else:
            moved = {k for k, a, b in zip(names, ids, now_ids) if a != b and not k.startswith("__")}
    else:
        now_map = dict(zip(now_names, now_ids))
        moved = {k for k, a in zip(names, ids) if k in now_map and now_map[k] != a and not k.startswith("__")}
    changed = []
    for key in moved | {k for k, fp in tracked.items() if fp[0] == "c" and now_tracked.get(k, fp) != fp}:
        label = _attribute_change(tracked.get(key), now_tracked.get(key), key in moved)
        if label:
            changed.append(f"{prefix}{key} ({label})")
    return changed


def _snapshot() -> dict:
    mock = sys.modules.get("unittest.mock")
    return {
        "globals": {
            "cwd": os.getcwd(),
            # pytest sets and removes PYTEST_CURRENT_TEST itself; an inherited value would look like a leak.
            "os.environ": {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"},
            "sys.path": list(sys.path),
            "threads": sorted(t.name for t in threading.enumerate()),
            "unittest.mock patches started and not stopped": len(getattr(getattr(mock, "_patch", None), "_active_patches", ())),
            "root logging handlers": [id(h) for h in logging.getLogger().handlers],
            "signal handlers": [id(signal.getsignal(s)) for s in _SIGNALS],
        },
        "modules": {name: id(module) for name, module in list(sys.modules.items())},
        "packages": _package_state() if _PACKAGES else {},
    }


def _changes(before: dict, after: dict) -> list[str]:
    changed = []
    for key, was in before["globals"].items():
        now = after["globals"][key]
        if now == was:
            continue
        if isinstance(was, dict):
            names = sorted(k for k in set(was) | set(now) if was.get(k) != now.get(k))
            key = f"{key}: {', '.join(names[:5])}" + (f" and {len(names) - 5} more" if len(names) > 5 else "")
        changed.append(key)
    if any(after["modules"].get(name) != ident for name, ident in before["modules"].items()):
        changed.append("sys.modules: an entry was removed or replaced")
    for module, (space, classes) in before["packages"].items():
        if module not in after["packages"]:
            continue
        now_space, now_classes = after["packages"][module]
        changed += _namespace_changes(module + ".", space, now_space)
        for attr, (class_id, class_space) in classes.items():
            now_class = now_classes.get(attr)
            if now_class is not None and now_class[0] == class_id:
                changed += _namespace_changes(f"{module}.{attr}.", class_space, now_class[1])
    return sorted(changed)


def pytest_addoption(parser):
    group = parser.getgroup("audit-leaks")
    group.addoption("--audit-leaks-json", help="where to write the leak report (outside the project)")
    group.addoption("--audit-leaks-packages", default="", help="comma-separated package prefixes to check")


def pytest_configure(config):
    global _PACKAGES
    if getattr(config.option, "numprocesses", None):
        raise pytest.UsageError("pytest_audit_leaks: run with -n 0; under xdist the workers' results never reach the controller")
    if not config.getoption("--audit-leaks-json"):
        raise pytest.UsageError("pytest_audit_leaks: pass --audit-leaks-json=PATH")
    _PACKAGES = tuple(p.strip() for p in config.getoption("--audit-leaks-packages").split(",") if p.strip())


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    # Nothing runs between two tests' protocols, so the previous snapshot serves as this one's "before".
    global _CHECKED, _LAST
    before = _LAST if _LAST is not None else _snapshot()
    yield
    _LAST = _snapshot()
    _CHECKED += 1
    changed = _changes(before, _LAST)
    if changed:
        _LEAKS[item.nodeid] = changed


def pytest_sessionfinish(session):
    seen: dict[str, list[str]] = {}
    for nodeid, changed in _LEAKS.items():
        for change in changed:
            seen.setdefault(change, []).append(nodeid)
    churn = {change: {"tests": len(ids), "first": ids[:3]} for change, ids in seen.items() if len(ids) > CHURN_TESTS}
    changes = {nodeid: kept for nodeid, changed in _LEAKS.items() if (kept := [c for c in changed if c not in churn])}
    report = {
        "tests_checked": _CHECKED,
        "tests_with_changes": len(changes),
        "packages": list(_PACKAGES),
        "changes": changes,
        "churn": dict(sorted(churn.items(), key=lambda item: -item[1]["tests"])),
    }
    with open(session.config.getoption("--audit-leaks-json"), "w") as handle:
        json.dump(report, handle, indent=1)
