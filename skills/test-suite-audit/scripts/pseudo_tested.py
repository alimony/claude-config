#!/usr/bin/env python3
"""Find pseudo-tested functions: covered code that no test notices when its whole body is gone.

A function is pseudo-tested when tests execute it, yet none of them fails when
its body is replaced by a trivial return (extreme mutation, Niedermayr et al.
2016). It is the cheapest mutation pass: 1 to 3 mutants per function, instead
of dozens for regular mutation operators.

It rewrites source files in place, so it runs only in a disposable copy under
the audit directory (guardrail 6): --audit must hold the STATE.md that
`run_suite.py init` writes, and the current directory and every --src path
must resolve inside it.

Usage (from the pytest rootdir of the disposable copy, with the project's interpreter):
    pseudo_tested.py --audit AUDIT --src SRC [--src SRC ...] --out FILE.jsonl
                     [--tests PATH ...] [--max-funcs N] [--seed 1] [--min-stmts 2]
                     [--timeout SECONDS] [--allow-dirty] [-- PYTEST_ARGS ...]

Run it through run_suite.py, which marks the run as mutation and shows UNCHECKED:
    run_suite.py run --artifacts AUDIT --label pseudo --timeout 3600 --cwd AUDIT/work/NAME -- \\
        PYTHON pseudo_tested.py --audit AUDIT --src src/pkg --out {RUN_DIR}/pseudo.jsonl \\
        --tests tests/unit -- -p no:xdist

Everything after `--` reaches every pytest run unchanged, so two-token flags
such as `-p no:xdist` work. Put test paths in --tests: mutant runs replace them
with the node IDs of the covering tests.

Steps:
  1. canary: the selected tests must pass on unmutated code;
  2. one run with per-test coverage contexts (pytest-cov, --cov-context=test).
     It sets COVERAGE_CORE=ctrace, because the sys.monitoring core records each
     line for only the first test that runs it, which breaks the mapping;
  3. a check that the covering node IDs run as given, the way mutant runs pass them;
  4. for each sampled covered function: replace the body with `return None`, plus
     constants that the return annotation allows (True and False, 0 and 1, "" and
     "A", empty containers); delete the module's cached bytecode; run only the
     tests that executed the body, with -x; then restore the file.

Verdicts: killed (pytest exit 1), survived (exit 0), and unknown (a timeout, or
exit 2, 3, 4, 5, or anything else, never counted as a kill). Function status:
pseudo-tested (every mutant survived), partially-tested (some killed and some
survived), tested (every mutant killed), or unknown (an unknown verdict leaves
it open).

Output: one JSON line per mutated function (file, function, line, status,
verdicts, exit codes, the first covering tests, seconds), flushed as it is
written, so a stopped run keeps its data. The printed summary is at most 15
lines, with a 95% Wilson interval for the pseudo-tested share of classified
functions.

Safety: SIGINT, SIGTERM, and SIGHUP restore the file before the script exits,
with exit code 128 + the signal number. SIGKILL cannot be caught and leaves the
mutant on disk, which is why the copy must be disposable. The script refuses a
tree with tracked changes, because a mutant left by an earlier, killed run
looks like one (--allow-dirty skips this check). At the end it checks that
every touched file has its original bytes.

Limits: it mutates module-level functions and methods only. It skips nested
functions, one-line bodies, generators, bodies of fewer than --min-stmts
statements, and __init__, __repr__, __str__, __hash__, __eq__, and __del__.
Each mutant starts a fresh pytest process, so start-up and conftest imports are
paid per mutant. Node IDs come from coverage contexts, so run it from the
pytest rootdir. pytest before 8.2 gets node IDs as arguments instead of an
@argfile. A passing result is a floor, not proof that the tests check results.

Exit codes: 0 finished; 1 finished, but a touched file did not match its
original bytes or the tree changed; 2 refused (usage, safety, dirty tree,
missing pytest-cov); 3 the canary, the coverage run, or the node-ID check
failed; 128 + N stopped by signal N.

Standard library only; runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import io
import json
import math
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tokenize
from pathlib import Path

ALTERNATES = {
    "bool": ["True", "False"],
    "int": ["0", "1"],
    "float": ["0.0", "1.0"],
    "str": ['""', '"A"'],
    "bytes": ['b""'],
    "list": ["[]"], "List": ["[]"], "Sequence": ["[]"], "Iterable": ["[]"],
    "dict": ["{}"], "Dict": ["{}"], "Mapping": ["{}"],
    "set": ["set()"], "Set": ["set()"], "frozenset": ["frozenset()"], "FrozenSet": ["frozenset()"],
    "tuple": ["()"], "Tuple": ["()"],
}
SKIP_NAMES = {"__init__", "__repr__", "__str__", "__hash__", "__eq__", "__del__"}
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
MARK = "  # extreme mutant"
STOP_SIGNALS = tuple(getattr(signal, name) for name in ("SIGINT", "SIGTERM", "SIGHUP") if hasattr(signal, name))

# Files with a mutant on disk, mapped to their original bytes.
_ACTIVE: dict = {}


class Refused(Exception):
    """The run must not start; exit code 2."""


class Failed(Exception):
    """A check on unmutated code failed; exit code 3."""


@contextlib.contextmanager
def signals_deferred():
    """Hold stop signals while a file is written, so a restore never interleaves with a write."""
    if not hasattr(signal, "pthread_sigmask"):
        yield
        return
    old = signal.pthread_sigmask(signal.SIG_BLOCK, set(STOP_SIGNALS))
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, old)


def drop_bytecode(path: Path) -> None:
    """Delete cached bytecode. Same-length edits within one second would otherwise reuse a stale .pyc."""
    for pyc in (path.parent / "__pycache__").glob(f"{path.stem}.*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass


def restore_active() -> list:
    restored = []
    for path, original in list(_ACTIVE.items()):
        path.write_bytes(original)
        drop_bytecode(path)
        _ACTIVE.pop(path, None)
        restored.append(path)
    return restored


def on_stop_signal(signum, frame):
    if hasattr(signal, "pthread_sigmask"):
        signal.pthread_sigmask(signal.SIG_BLOCK, set(STOP_SIGNALS))  # no second signal during the restore
    restored = restore_active()
    names = ", ".join(str(p) for p in restored) or "no file had a mutant on disk"
    sys.stderr.write(f"pseudo_tested: stopped by signal {signum}; restored: {names}\n")
    sys.stderr.flush()
    sys.exit(128 + signum)


def child_env(extra: dict | None = None) -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPYCACHEPREFIX", None)  # cached bytecode must live next to the source, where it is deleted
    env.update(extra or {})
    return env


def tail(run: subprocess.CompletedProcess, lines: int = 12) -> str:
    text = re.sub(r"\x1b\[[0-9;]*m", "", (run.stdout or "") + (run.stderr or "")).strip().splitlines()
    return "\n".join("    " + line for line in text[-lines:])


def tracked_changes(cwd: Path) -> list | None:
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=cwd,
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return [line for line in out.stdout.splitlines() if line.strip()]


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def own_nodes(func):
    """The nodes of a function's own body, without nested functions, lambdas, or classes."""
    stack = list(func.body)
    while stack:
        node = stack.pop()
        if isinstance(node, SCOPES):
            continue
        yield node
        stack.extend(ast.iter_child_nodes(node))


def annotation_names(ann) -> list:
    if ann is None:
        return []
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        try:
            ann = ast.parse(ann.value, mode="eval").body
        except SyntaxError:
            return []
    if isinstance(ann, ast.Name):
        return [ann.id]
    if isinstance(ann, ast.Attribute):
        return [ann.attr]
    if isinstance(ann, ast.Subscript):
        base = annotation_names(ann.value)
        if base == ["Optional"]:
            inner = ann.slice
            if type(inner).__name__ == "Index":  # Python 3.8 wraps the subscript
                inner = inner.value
            return annotation_names(inner)
        return base
    if isinstance(ann, ast.BinOp) and isinstance(ann.op, ast.BitOr):
        sides = [s for s in (ann.left, ann.right) if not (isinstance(s, ast.Constant) and s.value is None)]
        if len(sides) == 1:
            return annotation_names(sides[0])
    return []


def replacements(func) -> list:
    reps = ["return None"]
    if any(isinstance(n, ast.Return) and n.value is not None for n in own_nodes(func)):
        for name in annotation_names(func.returns):
            reps += [f"return {value}" for value in ALTERNATES.get(name, [])]
    return reps


def functions_in(tree):
    """Yield (qualified name, node) for module-level functions and methods, including nested classes."""
    def walk(body, prefix):
        for node in body:
            if isinstance(node, ast.ClassDef):
                yield from walk(node.body, f"{prefix}{node.name}.")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield f"{prefix}{node.name}", node
    yield from walk(tree.body, "")


def body_span(func, lines: list) -> tuple | None:
    """(first line, last line, statements) of the body without its docstring, or None for a one-line body."""
    body = list(func.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body:
        return None
    first, last = body[0].lineno, max(getattr(n, "end_lineno", n.lineno) for n in body)
    if first == func.lineno or lines[first - 1].encode("utf-8")[: body[0].col_offset].strip():
        return None
    return first, last, len(body)


def read_source(path: Path) -> tuple:
    original = path.read_bytes()
    encoding, _ = tokenize.detect_encoding(io.BytesIO(original).readline)
    # Split only where the tokenizer does (\n, \r\n, \r), keeping each ending, so line numbers match the AST.
    return original, encoding, io.StringIO(original.decode(encoding), newline="").readlines()


def mutant_bytes(lines: list, encoding: str, first: int, last: int, replacement: str) -> bytes | None:
    start = lines[first - 1]
    indent = start[: len(start) - len(start.lstrip())]
    ending = lines[last - 1][len(lines[last - 1].rstrip("\r\n")):] or "\n"
    text = "".join(lines[: first - 1] + [f"{indent}{replacement}{MARK}{ending}"] + lines[last:])
    try:
        ast.parse(text)
    except SyntaxError:
        return None
    return text.encode(encoding)


def pytest_base(pytest_args: list, *, stop_first: bool = False) -> list:
    # The caller's arguments come last, so they can override these defaults.
    return [sys.executable, "-m", "pytest", *(["-x"] if stop_first else []), "-q", "--color=no", "-p", "no:randomly", *pytest_args]


def run_nodeids(nodeids: list, pytest_args: list, workdir: Path, argfile: bool, timeout: float | None,
                capture: bool = False):
    if argfile:
        path = workdir / "nodeids.txt"
        path.write_text("\n".join(nodeids) + "\n")
        selection = [f"@{path}"]
    else:
        selection = list(nodeids)
    out = subprocess.PIPE if capture else subprocess.DEVNULL
    return subprocess.run(pytest_base(pytest_args, stop_first=True) + selection, env=child_env(), stdout=out,
                          stderr=out, text=True, timeout=timeout)


def verdict_of(nodeids: list, pytest_args: list, workdir: Path, argfile: bool, timeout: float) -> tuple:
    try:
        run = run_nodeids(nodeids, pytest_args, workdir, argfile, timeout)
    except subprocess.TimeoutExpired:
        return "unknown", "timeout"
    if run.returncode == 0:
        return "survived", 0
    if run.returncode == 1:
        return "killed", 1
    return "unknown", run.returncode  # 2 interrupted, 3 internal error, 4 usage error, 5 no tests, or a signal


def status_of(verdicts: dict) -> str:
    values = list(verdicts.values())
    killed, survived, unknown = values.count("killed"), values.count("survived"), values.count("unknown")
    if killed and survived:
        return "partially-tested"
    if unknown:
        return "unknown"
    return "tested" if killed else "pseudo-tested"


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    p, d = k / n, 1 + z * z / n
    mid = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, mid - half), min(1.0, mid + half)


def preflight() -> bool:
    """Check pytest-cov in this interpreter; return True when pytest reads @argfiles (8.2 or later)."""
    probe = "import pytest, pytest_cov; print(pytest.__version__)"
    run = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, env=child_env())
    if run.returncode != 0:
        raise Refused(f"{sys.executable} cannot import pytest and pytest-cov. Use an interpreter that has the project's "
                      "dependencies plus pytest-cov, installed in an isolated environment (guardrail 4).")
    parts = run.stdout.strip().split(".")
    try:
        return (int(parts[0]), int(parts[1])) >= (8, 2)
    except (IndexError, ValueError):
        return True


def canary(tests: list, pytest_args: list) -> float:
    started = time.monotonic()
    run = subprocess.run(pytest_base(pytest_args) + tests, env=child_env(), capture_output=True, text=True)
    if run.returncode != 0:
        meaning = {1: "tests failed", 2: "interrupted or collection errors", 4: "usage error", 5: "no tests collected"}
        raise Failed(f"canary failed: the selected tests do not pass on unmutated code (pytest exit {run.returncode}, "
                     f"{meaning.get(run.returncode, 'unexpected')}). Fix or deselect them first; no file was mutated.\n{tail(run)}")
    return time.monotonic() - started


def coverage_contexts(cov_sources: list, tests: list, pytest_args: list, workdir: Path) -> dict:
    """Map resolved file path -> line -> set of node IDs whose test executed the line."""
    env = child_env({"COVERAGE_CORE": "ctrace", "COVERAGE_FILE": str(workdir / ".coverage")})
    command = pytest_base(pytest_args) + [f"--cov={s}" for s in cov_sources] + ["--cov-context=test", "--cov-report="] + tests
    run = subprocess.run(command, env=env, capture_output=True, text=True)
    if run.returncode != 0:
        raise Failed(f"the run with coverage contexts failed (pytest exit {run.returncode}) although the canary passed.\n{tail(run)}")
    report = workdir / "coverage.json"
    run = subprocess.run([sys.executable, "-m", "coverage", "json", "--show-contexts", "-q", "-o", str(report)],
                         env=env, capture_output=True, text=True)
    if run.returncode != 0 or not report.is_file():
        raise Failed(f"coverage json failed (exit {run.returncode}).\n{tail(run)}")
    result: dict = {}
    for name, data in json.loads(report.read_text()).get("files", {}).items():
        lines = {}
        for line, contexts in (data.get("contexts") or {}).items():
            tests_here = {c.rsplit("|", 1)[0] for c in contexts if c}
            if tests_here:
                lines[int(line)] = tests_here
        result[str(Path(name).resolve())] = lines
    return result


def collect_candidates(sources: list, contexts: dict, min_stmts: int) -> tuple:
    candidates, skipped = [], {"uncovered": 0, "short body": 0, "generator": 0, "special method": 0, "unparsable": 0}
    for path in sources:
        try:
            original, encoding, lines = read_source(path)
            tree = ast.parse(original.decode(encoding), filename=str(path))
        except (SyntaxError, UnicodeDecodeError, ValueError):
            skipped["unparsable"] += 1
            continue
        line_tests = contexts.get(str(path.resolve()), {})
        for qualname, func in functions_in(tree):
            if func.name in SKIP_NAMES:
                skipped["special method"] += 1
                continue
            if any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in own_nodes(func)):
                skipped["generator"] += 1
                continue
            span = body_span(func, lines)
            if span is None or span[2] < min_stmts:
                skipped["short body"] += 1
                continue
            tests = set()
            for number in range(span[0], span[1] + 1):
                tests |= line_tests.get(number, set())
            if not tests:
                skipped["uncovered"] += 1
                continue
            candidates.append({"path": path, "qualname": qualname, "func": func, "span": span, "tests": sorted(tests)})
    return candidates, skipped


def source_files(srcs: list, audit: Path) -> list:
    files = []
    for src in srcs:
        files += [src] if src.is_file() else sorted(p for p in src.rglob("*.py") if "__pycache__" not in p.parts)
    outside = [str(p) for p in files if not inside(p.resolve(), audit)]
    if outside:
        raise Refused(f"{len(outside)} source files resolve outside the audit directory, for example {outside[0]}: "
                      "mutate only a disposable copy under it (guardrail 6).")
    return files


def mutate_function(cand: dict, pytest_args: list, workdir: Path, argfile: bool, timeout: float) -> dict:
    path, (first, last, _) = cand["path"], cand["span"]
    original, encoding, lines = read_source(path)
    verdicts, codes = {}, {}
    started = time.monotonic()
    for replacement in replacements(cand["func"]):
        mutated = mutant_bytes(lines, encoding, first, last, replacement)
        if mutated is None:
            verdicts[replacement], codes[replacement] = "unknown", "invalid mutant"
            continue
        try:
            with signals_deferred():
                _ACTIVE[path] = original
                path.write_bytes(mutated)
                drop_bytecode(path)
            verdicts[replacement], codes[replacement] = verdict_of(cand["tests"], pytest_args, workdir, argfile, timeout)
        finally:
            with signals_deferred():
                path.write_bytes(original)
                drop_bytecode(path)
                _ACTIVE.pop(path, None)
    return {
        "file": str(path), "function": cand["qualname"], "line": cand["func"].lineno, "status": status_of(verdicts),
        "verdicts": verdicts, "exit_codes": codes, "covering_tests": len(cand["tests"]), "tests": cand["tests"][:5],
        "seconds": round(time.monotonic() - started, 2),
    }


def summary(records: list, planned: int, skipped: dict, canary_seconds: float, n_tests: int, touched: dict,
            out: Path, tree_note: str) -> list:
    verdicts = [v for r in records for v in r["verdicts"].values()]
    codes = [c for r in records for c in r["exit_codes"].values()]
    status = {s: [r for r in records if r["status"] == s] for s in ("pseudo-tested", "partially-tested", "tested", "unknown")}
    timeouts = sum(c == "timeout" for c in codes)
    errors = verdicts.count("unknown") - timeouts
    lines = [
        f"pseudo_tested: {'complete' if len(records) == planned else 'incomplete'}: mutated {len(records)} of {planned} planned functions",
        f"canary: the selected tests passed on unmutated code in {canary_seconds:.1f} s; contexts from {n_tests} tests (COVERAGE_CORE=ctrace)",
        "skipped: " + ", ".join(f"{n} {reason}" for reason, n in skipped.items() if n) if any(skipped.values()) else "skipped: none",
        f"mutants: {len(verdicts)} run: {verdicts.count('killed')} killed, {verdicts.count('survived')} survived, "
        f"{verdicts.count('unknown')} unknown ({timeouts} timed out, {errors} ended with an error exit or were invalid)",
        f"functions: {len(status['pseudo-tested'])} pseudo-tested, {len(status['partially-tested'])} partially tested, "
        f"{len(status['tested'])} tested, {len(status['unknown'])} unknown",
    ]
    classified = len(records) - len(status["unknown"])
    if classified:
        k = len(status["pseudo-tested"])
        lo, hi = wilson(k, classified)
        lines.append(f"pseudo-tested share: {k} of {classified} classified functions = {k / classified:.1%} "
                     f"(95% Wilson interval {lo:.1%} to {hi:.1%})")
    for label, key in (("pseudo-tested", "pseudo-tested"), ("partially tested", "partially-tested"), ("unknown", "unknown")):
        if status[key]:
            shown = []
            for r in status[key][:3]:
                note = ""
                if key == "partially-tested":
                    note = " (survived: " + ", ".join(m for m, v in r["verdicts"].items() if v == "survived") + ")"
                elif key == "unknown":
                    note = " (" + ", ".join(str(c) for c in r["exit_codes"].values() if c not in (0, 1)) + ")"
                shown.append(f"{r['file']}:{r['line']} {r['function']}{note}")
            more = f" … and {len(status[key]) - 3} more" if len(status[key]) > 3 else ""
            lines.append(f"{label}: " + "; ".join(shown) + more)
    lines.append(f"files: {len(touched)} touched; {tree_note}")
    lines.append(f"output: {out}")
    return lines


def parse_args(argv: list):
    if "--" in argv:
        cut = argv.index("--")
        own, pytest_args = argv[:cut], argv[cut + 1:]
    else:
        own, pytest_args = argv, []
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audit", required=True, help="the audit directory from run_suite.py init")
    parser.add_argument("--src", required=True, action="append", help="package directory or file to mutate, inside the audit directory (repeatable)")
    parser.add_argument("--out", required=True, help="JSON Lines output file, for example {RUN_DIR}/pseudo.jsonl")
    parser.add_argument("--tests", action="append", default=[], help="test path for the canary and the coverage run (repeatable; default: the configured testpaths)")
    parser.add_argument("--max-funcs", type=int, default=0, help="random sample of covered functions (0 = all)")
    parser.add_argument("--seed", type=int, default=1, help="seed for the sample (default 1)")
    parser.add_argument("--min-stmts", type=int, default=2, help="skip bodies with fewer statements (default 2)")
    parser.add_argument("--timeout", type=float, default=300.0, help="seconds per mutant run; a timeout is an unknown verdict (default 300)")
    parser.add_argument("--allow-dirty", action="store_true", help="skip the clean-tree checks (for a copy that is not a git work tree)")
    args = parser.parse_args(own)
    return args, pytest_args


def main(argv: list | None = None) -> int:
    args, pytest_args = parse_args(sys.argv[1:] if argv is None else argv)
    for sig in STOP_SIGNALS:
        signal.signal(sig, on_stop_signal)
    workdir = Path(tempfile.mkdtemp(prefix="pseudo-tested-"))
    try:
        return run(args, pytest_args, workdir)
    except Refused as exc:
        print(f"refused: {exc}")
        return 2
    except Failed as exc:
        print(f"stopped: {exc}")
        return 3
    finally:
        restore_active()
        shutil.rmtree(workdir, ignore_errors=True)


def run(args, pytest_args: list, workdir: Path) -> int:
    audit = Path(args.audit).expanduser().resolve()
    if not (audit / "STATE.md").is_file():
        raise Refused(f"{audit} is not an audit directory from run_suite.py init (no STATE.md in it).")
    cwd = Path.cwd().resolve()
    if not inside(cwd, audit):
        raise Refused(f"the current directory {cwd} is outside the audit directory {audit}: "
                      "run from the disposable copy, made with git clone --local ROOT AUDIT/work/NAME (guardrail 6).")
    srcs = []
    for src in args.src:
        path = Path(src).expanduser()
        if not path.exists():
            raise Refused(f"--src {src} does not exist.")
        if not inside(path.resolve(), audit) or path.resolve() == audit:
            raise Refused(f"--src {src} resolves to {path.resolve()}, outside the audit directory {audit}: "
                          "mutate only a disposable copy under it (guardrail 6).")
        srcs.append(path)
    files = source_files(srcs, audit)
    before = tracked_changes(cwd)
    if not args.allow_dirty:
        if before is None:
            raise Refused("the current directory is not a git work tree, so a mutant left behind could go unnoticed. "
                          "Make the copy with git clone --local (guardrail 6), or pass --allow-dirty.")
        if before:
            raise Refused(f"{len(before)} tracked files differ from the commit, for example '{before[0].strip()}'. "
                          "A mutant left by an earlier, stopped run looks like this: inspect git diff in the copy, "
                          "or pass --allow-dirty.")
    argfile = preflight()

    canary_seconds = canary(args.tests, pytest_args)
    cov_sources = sorted({str(s if s.is_dir() else s.parent) for s in srcs})
    contexts = coverage_contexts(cov_sources, args.tests, pytest_args, workdir)
    n_tests = len({t for lines in contexts.values() for ts in lines.values() for t in ts})
    candidates, skipped = collect_candidates(files, contexts, args.min_stmts)
    candidates.sort(key=lambda c: (str(c["path"]), c["func"].lineno))
    random.Random(args.seed).shuffle(candidates)
    if args.max_funcs:
        candidates = candidates[: args.max_funcs]
    if candidates:
        first = candidates[0]
        check = run_nodeids(first["tests"], pytest_args, workdir, argfile, None, capture=True)
        if check.returncode == 1:
            raise Failed(f"the {len(first['tests'])} tests that cover {first['qualname']} fail when they run alone by node ID, "
                         "on unmutated code (pytest exit 1). Either a test depends on other tests, which would turn into "
                         "false kills (see flakiness.md), or the pytest arguments break a run that names node IDs. "
                         f"The output shows which.\n{tail(check)}")
        if check.returncode != 0:
            raise Failed(f"the covering node IDs do not run as given (pytest exit {check.returncode}). Run from the "
                         f"pytest rootdir, where the node IDs in coverage contexts start.\n{tail(check)}")

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    records, touched = [], {}
    with open(out, "w") as handle:
        for cand in candidates:
            touched.setdefault(cand["path"], cand["path"].read_bytes())
            record = mutate_function(cand, pytest_args, workdir, argfile, args.timeout)
            records.append(record)
            handle.write(json.dumps(record) + "\n")
            handle.flush()

    changed_files = [str(p) for p, original in touched.items() if p.read_bytes() != original]
    for p, original in touched.items():
        if p.read_bytes() != original:
            p.write_bytes(original)
    after = tracked_changes(cwd)
    tree_changed = not args.allow_dirty and after is not None and after != before
    if changed_files:
        tree_note = f"WARNING: {len(changed_files)} did not match their original bytes and were rewritten: {changed_files[0]}"
    elif tree_changed:
        tree_note = f"WARNING: tracked files changed during the run: {after[0].strip()}"
    else:
        tree_note = "all hold their original bytes"
    if not candidates:
        skipped_note = " If tests ran, they may import the code from outside the copy, for example through an editable install."
        print(f"pseudo_tested: no covered function with at least {args.min_stmts} statements in {', '.join(args.src)}.{skipped_note}")
    for line in summary(records, len(candidates), skipped, canary_seconds, n_tests, touched, out, tree_note):
        print(line)
    return 1 if changed_files or tree_changed else 0


if __name__ == "__main__":
    sys.exit(main())
