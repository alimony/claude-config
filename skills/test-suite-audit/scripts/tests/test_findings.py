from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import findings
from conftest import CORPUS


def base_finding(**overrides) -> dict:
    finding = {
        "id": "X-1",
        "title": "A title",
        "dimension": "speed",
        "claim": "A claim.",
        "evidence": [{"kind": "measured", "artifact": "runs/01-baseline/junit.xml", "value": 12, "unit": "s"}],
        "impact": {"level": "high", "estimate": 60, "metric": "seconds per run", "basis": "measured"},
        "effort": "S",
        "risk": "low",
        "confidence": "high",
        "action": "speed-up",
        "recommendation": "Do the thing.",
        "verification": "results.py diff ...",
        "status": "confirmed",
    }
    finding.update(overrides)
    return finding


@pytest.fixture
def audit(tmp_path) -> Path:
    for name, instrumented in (("01-baseline", "none"), ("02-coverage", "coverage")):
        folder = tmp_path / "runs" / name
        folder.mkdir(parents=True)
        (folder / "junit.xml").write_text("<testsuites/>")
        (folder / "manifest.json").write_text(json.dumps({"instrumented": instrumented, "complete": True}))
    (tmp_path / "nodeids.txt").write_text("tests/test_pricing.py::test_discount\ntests/test_pricing.py::test_discount_zero_percent[10]\n")
    return tmp_path


def check(audit: Path, *items: dict) -> tuple[list[str], list[str]]:
    data = {"project": "corpus", "project_root": str(CORPUS), "findings": list(items)}
    return findings.validate(data, audit, CORPUS)


def test_valid_findings_pass(audit):
    trust = base_finding(
        id="TRU-1",
        dimension="trust",
        trust_breaker=True,
        evidence=[{"kind": "static", "location": "tests/test_pricing.py:10", "test_id": "tests/test_pricing.py::test_discount"}],
        action="fix",
    )
    errors, _ = check(audit, trust, base_finding(id="SPD-1"))
    assert errors == []


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"evidence": [{"kind": "measured", "artifact": "runs/02-coverage/junit.xml"}]}, "instrumented"),
        ({"evidence": [{"kind": "measured", "artifact": "runs/09-missing/junit.xml"}]}, "does not exist"),
        ({"evidence": [{"kind": "static", "location": "tests/test_pricing.py:9999"}], "dimension": "design"}, "only"),
        ({"evidence": [{"kind": "static", "location": "tests/nope.py:1"}], "dimension": "design"}, "does not exist"),
        ({"evidence": [{"kind": "static", "test_id": "tests/test_pricing.py::test_gone"}], "dimension": "design"}, "not in nodeids"),
        ({"dimension": "flakiness", "confidence": "medium", "evidence": [{"kind": "static", "location": "tests/test_env.py:1"}]}, "static evidence must have low confidence"),
        ({"dimension": "redundancy", "action": "review-removal", "evidence": [{"kind": "coverage", "artifact": "runs/01-baseline/junit.xml"}]}, "two different kinds"),
        ({"impact": {"level": "high", "basis": "extrapolated"}}, "extrapolated"),
        ({"effort": "XL"}, "effort"),
        ({"evidence": [{"kind": "hunch", "artifact": "runs/01-baseline/junit.xml"}]}, "kind"),
        ({"evidence": [{"kind": "measured"}]}, "cites no artifact"),
    ],
)
def test_invalid_findings_are_rejected(audit, overrides, message):
    errors, _ = check(audit, base_finding(**overrides))
    assert any(message in e for e in errors), errors


def test_removal_with_two_kinds_of_evidence_passes(audit):
    finding = base_finding(
        dimension="redundancy",
        action="review-removal",
        evidence=[
            {"kind": "coverage", "artifact": "runs/01-baseline/junit.xml"},
            {"kind": "mutation", "artifact": "runs/01-baseline/junit.xml"},
        ],
    )
    assert check(audit, finding)[0] == []


def test_scoring_rule():
    assert findings.score(base_finding(trust_breaker=True, confidence="medium"))[0] == "P0"
    assert findings.score(base_finding(trust_breaker=True, confidence="low"))[0] != "P0"
    assert findings.score(base_finding()) == ("P1", 3.0)
    assert findings.score(base_finding(effort="M", confidence="medium")) == ("P2", 0.9)
    assert findings.score(base_finding(effort="L", confidence="low", impact={"level": "low"}))[0] == "P3"
    assert findings.score(base_finding(effort="S", confidence="low"))[0] == "P2"


def test_report_renders_sections_in_priority_order(audit):
    items = [
        base_finding(id="SPD-2", effort="L", confidence="medium", impact={"level": "medium", "basis": "measured"}),
        base_finding(id="TRU-1", dimension="trust", trust_breaker=True, action="fix",
                     evidence=[{"kind": "static", "location": "tests/test_pricing.py:10", "command": "static_scan.py"}]),
        base_finding(id="SPD-1"),
        base_finding(id="OLD-1", status="rejected", rejection_reason="measured no gain"),
    ]
    source = audit / "findings.json"
    source.write_text(json.dumps({"project": "corpus", "project_root": str(CORPUS), "not_measured": ["Mutation testing: out of budget"], "findings": items}))
    (audit / "baseline.json").write_text(json.dumps({"tests collected": 26, "wall seconds": 1.2}))
    assert findings.main(["report", str(source)]) == 0
    report = (audit / "report.md").read_text()
    order = [report.index(h) for h in ("## Trust breakers (P0)", "## Quick wins (P1)", "## Roadmap (P2 and P3)", "## Not measured", "## Checked and rejected", "## Reproduce")]
    assert order == sorted(order)
    assert "| tests collected | 26 |" in report
    assert "OLD-1: A title – measured no gain" in report
    scored = json.loads((audit / "findings.scored.json").read_text())
    assert [f["id"] for f in scored["findings"]][:2] == ["TRU-1", "SPD-1"]


def test_report_refuses_invalid_findings(audit):
    source = audit / "findings.json"
    source.write_text(json.dumps({"findings": [base_finding(evidence=[])]}))
    assert findings.main(["report", str(source)]) == 1
    assert not (audit / "report.md").exists()


def test_validation_does_not_mutate_input(audit):
    item = base_finding()
    before = copy.deepcopy(item)
    check(audit, item)
    assert item == before


def test_profile_evidence_ranks_but_never_times(audit):
    profile = [{"kind": "profile", "artifact": "runs/02-coverage/junit.xml", "note": "import-time ranking"}]
    errors, _ = check(audit, base_finding(id="SPD-2", evidence=profile))
    assert any("needs measured or history evidence" in e for e in errors)
    both = profile + [{"kind": "measured", "artifact": "runs/01-baseline/junit.xml", "value": 3, "unit": "s"}]
    errors, _ = check(audit, base_finding(id="SPD-3", evidence=both))
    assert errors == []
    errors, _ = check(audit, base_finding(id="SPD-4", evidence=profile, impact={"level": "medium", "basis": "heuristic"}))
    assert errors == []


def test_p0_findings_sort_by_impact():
    small = findings.score(base_finding(trust_breaker=True, confidence="medium", impact={"level": "low"}, effort="M"))
    large = findings.score(base_finding(trust_breaker=True, confidence="high", impact={"level": "high"}, effort="S"))
    assert small[0] == large[0] == "P0" and large[1] > small[1]


def test_rejected_findings_need_only_what_was_checked(audit):
    rejected = {
        "id": "RED-9", "title": "Tests without assertions", "dimension": "redundancy", "status": "rejected",
        "claim": "78 tests have no assertion.", "rejection_reason": "0 of 5 sampled were real: does-not-raise tests.",
        "evidence": [{"kind": "static", "location": "tests/test_pricing.py:10"}],
    }
    errors, _ = check(audit, rejected)
    assert errors == []
    errors, _ = check(audit, {**rejected, "rejection_reason": ""})
    assert any("rejection_reason" in e for e in errors)
