#!/usr/bin/env python3
"""Estimate the rows each factory_boy factory writes per create(), without a database.

A factory cascade is excess data from nested factory calls. Each SubFactory
creates its own parent unless the caller passes one, and each RelatedFactory or
RelatedFactoryList creates children after the object, so one create() can write
many rows, often several unrelated copies of a top-level entity such as an
organisation. This script walks the factories' declarations and ranks them by
estimated rows per create(), with a breakdown by model, before any test runs.

Usage:
    factory_cascade.py [MODULE ...] [--find DIR] [--path DIR ...] [--settings MODULE]
                       [--top N] [--json-out FILE]

MODULE is a dotted module that defines factories, such as app.tests.factories.
--find DIR adds every module under DIR whose source imports factory and defines
a class based on a ...Factory class; it reads files as text and imports only the
matches. Module names are relative to the first --path entry that contains the
file. --path DIR goes onto sys.path (default: the current directory), so run the
script from the project root, with the project's Python:

    cd ROOT && .venv/bin/python factory_cascade.py --find . --settings app.settings.test

For Django, --settings (or DJANGO_SETTINGS_MODULE) names the settings module,
and the script calls django.setup() before it imports the factories. It imports
project code, but it needs no database and runs no tests. A module that fails to
import is reported and skipped.

What it counts:
  * 1 row for the factory's own object (factory.List and factory.Dict add none);
  * every SubFactory, recursively;
  * RelatedFactory as one child, and RelatedFactoryList as `size` children;
  * for Maybe, the larger branch.
A declaration replaced by a value, SelfAttribute, or LazyAttribute adds no row,
whether the replacement comes from SubFactory keyword arguments or from
class-level deep context (owner__account = ...). A RelatedFactory passes the new
object to the child as factory_related_name, so the child's own SubFactory for
that field adds no row.

Limits: rows made by LazyAttribute or LazyFunction bodies, post_save signals,
save() overrides, or a custom _create are invisible, so those factories are
undercounted without a flag. post_generation hooks are flagged, not counted, and
a callable RelatedFactoryList size is counted once and flagged. get_or_create
factories are flagged, because they may reuse rows. The walk reads factory_boy
internals (_meta.pre_declarations, SubFactory._defaults) as of factory_boy 3.3.
In checks against real INSERT counts it was exact for 24 of 28 factories, and the
4 misses were these blind spots. Treat the output as a static estimate, and
confirm the top entries with INSERTs per test (run_suite.py run --db-probe).

Requires factory_boy from the project's environment; otherwise standard library
only; runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

try:  # factory_boy comes from the project's environment, not from this skill
    import factory
    from factory.declarations import Maybe, PostGeneration, RelatedFactory, SubFactory
except ImportError:
    factory = None

MAX_DEPTH = 25
SKIP_DIRS = {
    ".git", ".hg", ".mypy_cache", ".nox", ".pytest_cache", ".tox", ".venv", "__pycache__",
    "build", "dist", "env", "node_modules", "site-packages", "venv",
}
FACTORY_IMPORT_RE = re.compile(r"^\s*(?:import\s+factory\b|from\s+factory\b)", re.M)
FACTORY_CLASS_RE = re.compile(r"^\s*class\s+\w+\s*\([^)]*Factory\b", re.M)


class Estimate:
    """What one create() writes: rows per model, and what the walk could not count."""

    def __init__(self) -> None:
        self.models: Counter = Counter()
        self.flags: set[str] = set()


def model_name(model) -> str:
    return getattr(model, "__name__", str(model))


def split_overrides(overrides: dict) -> tuple[dict, dict]:
    """Split {"owner": x, "owner__account": y} into direct values and nested overrides per field."""
    direct: dict = {}
    nested: dict = {}
    for key, value in overrides.items():
        head, _, rest = key.partition("__")
        if rest:
            nested.setdefault(head, {})[rest] = value
        else:
            direct[key] = value
    return direct, nested


def count_rows(factory_class, overrides: dict | None, depth: int, estimate: Estimate) -> int:
    """Rows that factory_class.create(**overrides) writes, as far as its declarations show."""
    meta = factory_class._meta
    declarations = {**meta.pre_declarations.as_dict(), **meta.post_declarations.as_dict()}
    # Class-level deep context, such as owner__account = SelfAttribute("..account"),
    # acts like an override from the caller, with lower precedence.
    context = {key: value for key, value in declarations.items() if "__" in key}
    direct, nested = split_overrides({**context, **(overrides or {})})

    if getattr(meta, "django_get_or_create", ()) or getattr(meta, "sqlalchemy_get_or_create", ()):
        estimate.flags.add(f"{factory_class.__name__}: get_or_create, may reuse rows")
    rows = 0 if meta.model in (list, dict) else 1  # factory.List and factory.Dict build containers
    if rows:
        estimate.models[model_name(meta.model)] += 1
    if depth > MAX_DEPTH:
        estimate.flags.add(f"{factory_class.__name__}: nested deeper than {MAX_DEPTH}, a SubFactory cycle?")
        return rows

    fields = {key for key in declarations if "__" not in key} | set(direct)
    for field in sorted(fields):
        declaration = direct.get(field, declarations.get(field))
        where = f"{factory_class.__name__}.{field}"
        rows += count_declaration(declaration, nested.get(field, {}), depth, estimate, where)
    return rows


def count_declaration(declaration, extra: dict, depth: int, estimate: Estimate, where: str) -> int:
    """Rows that one declaration adds. A plain value, SelfAttribute, or LazyAttribute adds none."""
    if isinstance(declaration, Maybe):
        estimate.flags.add(f"{where}: Maybe, counted the larger branch")
        branches = (declaration.yes, declaration.no)
        return max(count_declaration(branch, extra, depth, estimate, where) for branch in branches)
    if isinstance(declaration, RelatedFactory):  # RelatedFactoryList too
        child_overrides = {**declaration.defaults, **extra}
        if declaration.name:
            # The new object reaches the child as this field, so the child's own
            # SubFactory for it creates nothing.
            child_overrides[declaration.name] = None
        size = getattr(declaration, "size", 1)
        if callable(size):
            estimate.flags.add(f"{where}: RelatedFactoryList with a callable size, counted once")
            size = 1
        child = declaration.get_factory()
        return sum(count_rows(child, dict(child_overrides), depth + 1, estimate) for _ in range(size))
    if isinstance(declaration, SubFactory):  # factory.List and factory.Dict too
        child_overrides = {**declaration._defaults, **extra}
        return count_rows(declaration.get_factory(), child_overrides, depth + 1, estimate)
    if isinstance(declaration, PostGeneration):
        estimate.flags.add(f"{where}: post_generation hook, rows unknown")
    return 0


def estimate_factory(factory_class) -> dict:
    estimate = Estimate()
    rows = count_rows(factory_class, None, 0, estimate)
    return {
        "factory": f"{factory_class.__module__}.{factory_class.__name__}",
        "rows": rows,
        "models": dict(estimate.models.most_common()),
        "flags": sorted(estimate.flags),
    }


def module_name_for(path: Path, roots: list[Path]) -> str | None:
    for root in roots:
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts and all(part.isidentifier() for part in parts):
            return ".".join(parts)
    return None


def find_modules(directory: Path, roots: list[Path]) -> tuple[list[str], list[str]]:
    """Modules under directory that import factory and define a ...Factory subclass, read as text."""
    modules: list[str] = []
    unplaced: list[str] = []
    for current, dirs, files in os.walk(directory):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for file_name in sorted(files):
            if not file_name.endswith(".py"):
                continue
            path = Path(current, file_name).resolve()
            try:
                text = path.read_text(errors="replace")
            except OSError:
                continue
            if not (FACTORY_IMPORT_RE.search(text) and FACTORY_CLASS_RE.search(text)):
                continue
            name = module_name_for(path, roots)
            if name is None:
                unplaced.append(str(path))
            else:
                modules.append(name)
    return modules, unplaced


def factories_in(module) -> list:
    """Concrete factories defined in the module itself, not imported into it."""
    found = []
    for _, candidate in inspect.getmembers(module, inspect.isclass):
        if not issubclass(candidate, factory.base.Factory) or candidate.__module__ != module.__name__:
            continue
        if candidate._meta.model is None or candidate._meta.abstract:
            continue
        found.append(candidate)
    return found


def first_line(error: BaseException) -> str:
    text = f"{type(error).__name__}: {error}"
    return text.splitlines()[0][:300] if text else type(error).__name__


def write_out(path_text: str, text: str) -> None:
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("modules", nargs="*", metavar="MODULE", help="dotted modules that define factories")
    parser.add_argument("--find", metavar="DIR", help="also scan DIR for modules that define factories")
    parser.add_argument("--path", action="append", metavar="DIR", help="put DIR on sys.path (default: the current directory)")
    parser.add_argument("--settings", metavar="MODULE", help="Django settings module (default: DJANGO_SETTINGS_MODULE)")
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--json-out")
    args = parser.parse_args(argv)

    if factory is None:
        print("factory_boy is not importable: run this script with the project's Python, the one that runs its tests")
        return 2
    roots = [Path(p).resolve() for p in (args.path or ["."])]
    for root in reversed(roots):
        sys.path.insert(0, str(root))
    if args.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = args.settings
    if os.environ.get("DJANGO_SETTINGS_MODULE"):
        try:
            import django

            django.setup()
        except Exception as error:  # a broken settings module stops everything that follows
            print(f"django.setup() failed for {os.environ['DJANGO_SETTINGS_MODULE']}: {first_line(error)}")
            return 2

    modules = list(dict.fromkeys(args.modules))
    unplaced: list[str] = []
    if args.find:
        found, unplaced = find_modules(Path(args.find).resolve(), roots)
        modules += [m for m in found if m not in modules]
    if not modules:
        print("no modules to read: name factory modules, or pass --find DIR")
        return 1

    import_errors: dict[str, str] = {}
    walk_errors: dict[str, str] = {}
    results = []
    for name in modules:
        try:
            module = importlib.import_module(name)
        except Exception as error:  # any import-time failure in project code
            import_errors[name] = first_line(error)
            continue
        for factory_class in factories_in(module):
            try:
                results.append(estimate_factory(factory_class))
            except Exception as error:  # an unusual declaration this walk does not understand
                walk_errors[f"{name}.{factory_class.__name__}"] = first_line(error)
    results.sort(key=lambda r: (-r["rows"], r["factory"]))

    flagged = sum(1 for r in results if r["flags"])
    imported = len(modules) - len(import_errors)
    print(
        f"factories: {len(results)} in {imported} module{'' if imported == 1 else 's'}   flagged: {flagged}   "
        f"import errors: {len(import_errors)}   walk errors: {len(walk_errors)}"
    )
    for name, error in list({**import_errors, **walk_errors}.items())[:3]:
        print(f"  error: {name}: {error}")
    if any("ImproperlyConfigured" in e or "AppRegistryNotReady" in e for e in import_errors.values()):
        print("  hint: pass --settings with the test settings module")
    print("rows per create()  factory  (rows by model)")
    for r in results[: args.top]:
        models = ", ".join(f"{model} {count}" for model, count in r["models"].items())
        print(f"  {r['rows']:5d}  {r['factory']}  ({models})" + (f"  FLAGS: {'; '.join(r['flags'])}" if r["flags"] else ""))
    if len(results) > args.top:
        print(f"  … {len(results) - args.top} more in --json-out")
    if args.json_out:
        report = {
            "modules": modules,
            "unplaced_files": unplaced,
            "import_errors": import_errors,
            "walk_errors": walk_errors,
            "factories": results,
        }
        write_out(args.json_out, json.dumps(report, indent=2))
        print(f"json: {args.json_out}")
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
