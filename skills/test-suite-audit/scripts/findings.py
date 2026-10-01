#!/usr/bin/env python3
"""Validate audit findings against their evidence, score them, and render the report.

Findings live in one JSON file, normally findings.json in the audit directory:

    {
      "project": "name",
      "project_root": "/path/to/checkout",
      "not_measured": ["What was not measured, and why"],
      "findings": [
        {
          "id": "SPD-001",
          "title": "Short title",
          "dimension": "trust | speed | flakiness | adequacy | redundancy | design | ci",
          "claim": "One falsifiable sentence.",
          "trust_breaker": false,
          "scope": {"paths": ["tests/api/"], "tests_affected": 4120},
          "evidence": [
            {"kind": "measured | history | static | coverage | mutation | config | profile",
             "artifact": "runs/03-baseline/junit.xml",
             "command": "results.py summary runs/03-baseline",
             "location": "tests/api/conftest.py:41",
             "test_id": "tests/api/test_orders.py::test_refund",
             "value": 212, "unit": "s", "note": "..."}
          ],
          "impact": {"level": "high | medium | low", "metric": "wall seconds per CI run",
                     "estimate": 210, "range": [150, 260], "basis": "measured | extrapolated | heuristic"},
          "effort": "S | M | L",
          "risk": "low | medium | high",
          "confidence": "high | medium | low",
          "action": "fix | speed-up | configure | add-tests | review-removal | merge | demote | investigate",
          "recommendation": "What to do.",
          "verification": "The command that proves it, and the expected change.",
          "status": "candidate | confirmed | rejected | done"
        }
      ]
    }

Rules enforced (errors block the report; warnings are printed):
  * every finding has the required fields with allowed values, and a unique id;
  * every evidence item cites an artifact, a file location, or a test ID, and each one exists:
    artifacts relative to the audit directory, locations relative to project_root
    (with the line inside the file), and test IDs in the audit's nodeids.txt when present;
  * a speed finding cannot rest on timings from an instrumented run (manifest "instrumented");
  * an extrapolated impact cannot have high confidence;
  * a flakiness finding with only static evidence must have low confidence;
  * a removal or merge (action review-removal or merge) needs two different kinds of
    evidence among coverage, mutation, history, and static.

Priority:
  P0  trust breakers (tests that give false confidence) at medium or high confidence
  otherwise score = impact (high 3, medium 2, low 1) x confidence (high 1.0, medium 0.6, low 0.3)
                    / effort (S 1, M 2, L 4)
  P1  score >= 1.5 (quick wins)    P2  score >= 0.75    P3  everything else
  Ties sort by lower risk, then by more tests affected. Rejected findings are listed apart.

Usage:
    findings.py validate FINDINGS_JSON [--audit DIR] [--project DIR]
    findings.py report FINDINGS_JSON [--audit DIR] [--project DIR] [--out FILE]

`report` writes report.md (or --out) and findings.scored.json next to the input.
It reads baseline.json from the audit directory when present.

Standard library only; runs on Python 3.8+.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

DIMENSIONS = {"trust", "speed", "flakiness", "adequacy", "redundancy", "design", "ci"}
EVIDENCE_KINDS = {"measured", "history", "static", "coverage", "mutation", "config", "profile"}
LEVELS = {"high", "medium", "low"}
EFFORTS = {"S", "M", "L"}
STATUSES = {"candidate", "confirmed", "rejected", "done"}
ACTIONS = {"fix", "speed-up", "configure", "add-tests", "review-removal", "merge", "demote", "investigate"}
BASES = {"measured", "extrapolated", "heuristic"}
REMOVAL_ACTIONS = {"review-removal", "merge"}
REMOVAL_EVIDENCE = {"coverage", "mutation", "history", "static"}
IMPACT_W = {"high": 3, "medium": 2, "low": 1}
CONF_W = {"high": 1.0, "medium": 0.6, "low": 0.3}
EFFORT_W = {"S": 1, "M": 2, "L": 4}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
PRIORITY_TITLES = {
    "P0": "Trust breakers (P0)",
    "P1": "Quick wins (P1)",
    "P2": "Worth doing (P2)",
    "P3": "Later (P3)",
}


def load_nodeids(audit: Path) -> set[str] | None:
    path = audit / "nodeids.txt"
    if not path.is_file():
        return None
    ids = set()
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if "::" in line and not line.startswith(("=", "<")):
            ids.add(line)
            ids.add(line.split("[", 1)[0])
    return ids


def check_location(location: str, project: Path) -> str | None:
    path_text, sep, line_text = location.rpartition(":")
    if not sep or not line_text.isdigit():
        path_text, line_text = location, ""
    path = Path(path_text) if Path(path_text).is_absolute() else project / path_text
    if not path.exists():
        return f"location {location!r}: {path} does not exist"
    if line_text and path.is_file():
        try:
            lines = path.read_text(errors="replace").count("\n") + 1
        except OSError as exc:
            return f"location {location!r}: cannot read ({exc})"
        if int(line_text) > lines:
            return f"location {location!r}: the file has only {lines} lines"
    return None


def manifest_for(artifact: Path) -> dict | None:
    for candidate in (artifact / "manifest.json", artifact.parent / "manifest.json", artifact.parent.parent / "manifest.json"):
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text())
            except ValueError:
                return None
    return None


def validate(data: dict, audit: Path, project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    findings = data.get("findings")
    if not isinstance(findings, list) or not findings:
        return ["no findings list"], warnings
    nodeids = load_nodeids(audit)
    seen = set()
    for i, f in enumerate(findings):
        fid = f.get("id") or f"#{i + 1}"
        where = f"{fid}"

        def need(key: str, allowed: set | None = None, container: dict | None = None, label: str | None = None) -> object:
            source = f if container is None else container
            value = source.get(key) if isinstance(source, dict) else None
            name = label or key
            if value in (None, "", []):
                errors.append(f"{where}: missing {name}")
            elif allowed is not None and value not in allowed:
                errors.append(f"{where}: {name} {value!r} is not one of {sorted(allowed)}")
            return value

        if fid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(fid)
        # A rejected finding records what was checked and why it failed: no fix, effort, or impact.
        rejected = f.get("status") == "rejected"
        for key in ("title", "claim") + (("rejection_reason",) if rejected else ("recommendation", "verification")):
            need(key)
        dimension = need("dimension", DIMENSIONS)
        if rejected:
            confidence = f.get("confidence") or "low"
        else:
            need("effort", EFFORTS)
            need("risk", LEVELS)
            confidence = need("confidence", LEVELS)
        need("status", STATUSES)
        action = f.get("action")
        if action is not None and action not in ACTIONS:
            errors.append(f"{where}: action {action!r} is not one of {sorted(ACTIONS)}")
        impact = f.get("impact") if isinstance(f.get("impact"), dict) else {}
        if not impact and not rejected:
            errors.append(f"{where}: missing impact")
        if not rejected:
            need("level", LEVELS, impact, "impact.level")
        basis = impact.get("basis")
        if basis is not None and basis not in BASES:
            errors.append(f"{where}: impact.basis {basis!r} is not one of {sorted(BASES)}")
        if basis == "extrapolated" and confidence == "high":
            errors.append(f"{where}: an extrapolated impact cannot have high confidence")

        evidence = f.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{where}: no evidence")
            continue
        kinds = set()
        for j, ev in enumerate(evidence):
            label = f"{where} evidence {j + 1}"
            kind = ev.get("kind")
            if kind not in EVIDENCE_KINDS:
                errors.append(f"{label}: kind {kind!r} is not one of {sorted(EVIDENCE_KINDS)}")
            kinds.add(kind)
            if not any(ev.get(k) for k in ("artifact", "location", "test_id")):
                errors.append(f"{label}: cites no artifact, location, or test_id")
            if ev.get("artifact"):
                artifact = Path(ev["artifact"])
                artifact = artifact if artifact.is_absolute() else audit / artifact
                if not artifact.exists():
                    errors.append(f"{label}: artifact {ev['artifact']!r} does not exist under {audit}")
                elif dimension == "speed" and kind == "measured":
                    manifest = manifest_for(artifact)
                    if manifest and manifest.get("instrumented") not in (None, "none"):
                        errors.append(f"{label}: timing from an instrumented run ({manifest.get('instrumented')}) cannot back a speed finding")
                    if manifest and manifest.get("complete") is False:
                        warnings.append(f"{label}: the cited run was partial ({manifest.get('completeness_reason')})")
            if ev.get("location"):
                problem = check_location(str(ev["location"]), project)
                if problem:
                    errors.append(f"{label}: {problem}")
            if ev.get("test_id") and nodeids is not None and ev["test_id"] not in nodeids and ev["test_id"].split("[", 1)[0] not in nodeids:
                errors.append(f"{label}: test_id {ev['test_id']!r} is not in nodeids.txt")
        basis = (f.get("impact") or {}).get("basis")
        if dimension == "speed" and basis == "measured" and not kinds & {"measured", "history"}:
            errors.append(f"{where}: a measured speed impact needs measured or history evidence; a profile only ranks causes")
        if dimension == "flakiness" and kinds <= {"static", "config"} and confidence != "low":
            errors.append(f"{where}: flakiness backed only by static evidence must have low confidence")
        if action in REMOVAL_ACTIONS and len(kinds & REMOVAL_EVIDENCE) < 2:
            errors.append(f"{where}: {action} needs two different kinds of evidence among {sorted(REMOVAL_EVIDENCE)}")
        if confidence == "high" and kinds <= {"static"} and not f.get("trust_breaker"):
            warnings.append(f"{where}: high confidence on static evidence only; confirm it at runtime")
        if f.get("trust_breaker") and dimension not in ("trust", "adequacy", "redundancy", "flakiness"):
            warnings.append(f"{where}: trust_breaker is set on a {dimension} finding")
    return errors, warnings


def score(f: dict) -> tuple[str, float]:
    confidence = f.get("confidence", "low")
    value = IMPACT_W.get(f.get("impact", {}).get("level", "low"), 1) * CONF_W.get(confidence, 0.3) / EFFORT_W.get(f.get("effort", "L"), 4)
    if f.get("trust_breaker") and confidence in ("high", "medium"):
        return "P0", round(value, 2)  # the score orders findings within P0
    if value >= 1.5 and confidence != "low":
        return "P1", round(value, 2)
    if value >= 0.75:
        return "P2", round(value, 2)
    return "P3", round(value, 2)


def sort_key(f: dict) -> tuple:
    return (
        f.get("status") == "rejected",
        f["priority"],
        -f["score"],
        RISK_ORDER.get(f.get("risk", "high"), 2),
        -int((f.get("scope") or {}).get("tests_affected") or 0),
        f.get("id", ""),
    )


def render_finding(f: dict) -> list[str]:
    impact = f.get("impact", {})
    est = impact.get("estimate")
    rng = impact.get("range")
    impact_text = impact.get("level", "?")
    if est is not None:
        impact_text += f" – about {est} {impact.get('metric', '')}".rstrip()
        if rng:
            impact_text += f" (range {rng[0]}–{rng[1]})"
    if impact.get("basis"):
        impact_text += f", {impact['basis']}"
    out = [f"### {f['id']}: {f['title']}", "", f"**Claim:** {f['claim']}", "", "**Evidence:**", ""]
    for ev in f.get("evidence", []):
        cited = ", ".join(f"`{ev[k]}`" for k in ("artifact", "location", "test_id") if ev.get(k))
        value = f" – {ev['value']} {ev.get('unit', '')}".rstrip() if ev.get("value") is not None else ""
        note = f" – {ev['note']}" if ev.get("note") else ""
        out.append(f"- {ev.get('kind')}: {cited}{value}{note}")
    scope = f.get("scope") or {}
    out += [
        "",
        f"**Impact:** {impact_text}",
        f"**Effort, risk, confidence:** {f.get('effort')}, {f.get('risk')}, {f.get('confidence')}"
        + (f" – affects about {scope['tests_affected']} tests" if scope.get("tests_affected") else ""),
        "",
        f"**Recommendation:** {f['recommendation']}",
        "",
        f"**Verify:** {f['verification']}",
        "",
    ]
    return out


def render(data: dict, findings: list[dict], audit: Path) -> str:
    live = [f for f in findings if f.get("status") != "rejected"]
    rejected = [f for f in findings if f.get("status") == "rejected"]
    counts = {p: sum(1 for f in live if f["priority"] == p) for p in ("P0", "P1", "P2", "P3")}
    lines = [
        f"# Test suite audit: {data.get('project', audit.name)}",
        "",
        f"Generated {_dt.date.today().isoformat()} from `{audit}`.",
        "",
        "## Summary",
        "",
        f"- {len(live)} findings: " + ", ".join(f"{n} {p}" for p, n in counts.items()) + ".",
    ]
    baseline_path = audit / "baseline.json"
    if baseline_path.is_file():
        try:
            baseline = json.loads(baseline_path.read_text())
        except ValueError:
            baseline = {}
        if baseline:
            lines += ["", "| Baseline metric | Value |", "| --- | --- |"]
            lines += [f"| {k} | {v} |" for k, v in baseline.items() if not isinstance(v, (dict, list))]
    top = [f for f in live if f["priority"] in ("P0", "P1")][:3]
    if top:
        lines += ["", "Start with:", ""]
        lines += [f"{n}. {f['id']}: {f['title']} ({f['priority']})" for n, f in enumerate(top, 1)]
    for priority in ("P0", "P1"):
        group = [f for f in live if f["priority"] == priority]
        if group:
            lines += ["", f"## {PRIORITY_TITLES[priority]}", ""]
            for f in group:
                lines += render_finding(f)
    later = [f for f in live if f["priority"] in ("P2", "P3")]
    if later:
        lines += ["", "## Roadmap (P2 and P3)", "", "| ID | Title | Dimension | Impact | Effort | Risk | Confidence | Priority |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        lines += [
            f"| {f['id']} | {f['title']} | {f['dimension']} | {f['impact'].get('level')} | {f['effort']} | {f['risk']} | {f['confidence']} | {f['priority']} |"
            for f in later
        ]
        lines += ["", "Details:", ""]
        for f in later:
            lines += render_finding(f)
    candidates = [f for f in live if f.get("confidence") == "low"]
    if candidates:
        lines += ["", "## Unverified candidates", "", "These rest on weak evidence. Each one lists the cheapest check that would confirm or reject it.", ""]
        lines += [f"- {f['id']}: {f['title']} – check: {f['verification']}" for f in candidates]
    if data.get("not_measured"):
        lines += ["", "## Not measured", ""]
        lines += [f"- {item}" for item in data["not_measured"]]
    if rejected:
        lines += ["", "## Checked and rejected", ""]
        lines += [f"- {f['id']}: {f['title']} – {f.get('rejection_reason') or f.get('recommendation', '')}" for f in rejected]
    commands = []
    for f in live:
        for ev in f.get("evidence", []):
            if ev.get("command") and ev["command"] not in commands:
                commands.append(ev["command"])
    if commands:
        lines += ["", "## Reproduce", "", "```sh"] + commands + ["```"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("validate", "report"))
    parser.add_argument("findings", help="findings JSON file")
    parser.add_argument("--audit", help="audit directory (default: the findings file's directory)")
    parser.add_argument("--project", help="project root for file locations (default: project_root in the JSON, or .)")
    parser.add_argument("--out", help="report path (default: report.md in the audit directory)")
    args = parser.parse_args(argv)

    path = Path(args.findings)
    data = json.loads(path.read_text())
    audit = Path(args.audit) if args.audit else path.resolve().parent
    project = Path(args.project or data.get("project_root") or ".").expanduser()
    errors, warnings = validate(data, audit, project)
    for w in warnings[:20]:
        print(f"warning: {w}")
    for e in errors[:30]:
        print(f"error: {e}")
    if len(errors) > 30:
        print(f"… {len(errors) - 30} more errors")
    findings = data.get("findings") or []
    print(f"{len(findings)} findings, {len(errors)} errors, {len(warnings)} warnings")
    if errors:
        return 1
    for f in findings:
        f["priority"], f["score"] = ("rejected", 0.0) if f.get("status") == "rejected" else score(f)
    findings.sort(key=sort_key)
    counts = {p: sum(1 for f in findings if f["priority"] == p and f.get("status") != "rejected") for p in ("P0", "P1", "P2", "P3")}
    print("priorities: " + ", ".join(f"{p} {n}" for p, n in counts.items()))
    if args.command == "report":
        out = Path(args.out) if args.out else audit / "report.md"
        out.write_text(render(data, findings, audit))
        scored = path.with_name(path.stem + ".scored.json")
        scored.write_text(json.dumps(data, indent=2))
        print(f"report: {out}")
        print(f"scored: {scored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
