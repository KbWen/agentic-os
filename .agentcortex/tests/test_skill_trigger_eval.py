"""Guards for the skill trigger-accuracy eval runner.

Spec: docs/specs/skill-trigger-accuracy-eval.md (backlog #165, issue #398)

Every guard below is mutation-proved: the fixture is derived from the LIVE cases
file and one invariant is broken at a time, so a guard that stopped guarding
turns red here rather than passing quietly. The live suite is also exercised
directly — a generated fixture cannot reproduce states only the real tree has.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="pyyaml not installed -- pip install pyyaml")

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / ".agentcortex" / "tools" / "run_skill_eval.py"
CASES = ROOT / ".agentcortex" / "eval" / "skills.yaml"
REGISTRY = ROOT / ".agentcortex" / "metadata" / "trigger-registry.yaml"


def _run(cases_path: Path, extra=None):
    argv = [sys.executable, str(RUNNER), "--root", str(ROOT), "--cases", str(cases_path), "--format", "json"]
    argv.extend(extra or [])
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc


def _report(proc):
    assert proc.stdout.strip(), "runner produced no stdout; stderr=%s" % proc.stderr[-400:]
    return json.loads(proc.stdout)


def _load_cases():
    with CASES.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _write(tmp_path: Path, document) -> Path:
    target = tmp_path / "skills.yaml"
    target.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# The live tree, not a fixture.
# ---------------------------------------------------------------------------

def test_live_suite_passes_and_covers_every_skill() -> None:
    proc = _run(CASES)
    report = _report(proc)
    totals = report["totals"]
    assert proc.returncode == 0, "live suite is red: %s" % report["verdict"]["reasons"]
    assert totals["failed"] == 0
    assert totals["inert"] == 0
    assert report["uncovered_skills"] == []
    assert totals["skills_covered"] == totals["skills_in_registry"], (
        "every kind:skill entry needs at least one case (AC-1)"
    )


def test_live_known_gaps_are_at_or_below_baseline() -> None:
    """The ratchet only goes down. A new gap must be fixed or explicitly re-baselined."""
    report = _report(_run(CASES))
    totals = report["totals"]
    assert isinstance(totals["known_gap_baseline"], int), "cases file must declare known_gap_baseline"
    assert totals["known_gaps"] <= totals["known_gap_baseline"]


def test_every_skill_with_patterns_has_a_near_miss_negative() -> None:
    """AC-2: 13 of the 14 skills carry non-empty intent_patterns and need a negative.

    verification-before-completion is the single exclusion -- its intent_patterns
    is empty by design and activation is phase_scope-driven, so a 'near-miss
    paraphrase' is undefined for it.
    """
    with REGISTRY.open(encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)
    with_patterns = {
        entry["id"]
        for entry in registry["entries"]
        if entry.get("kind") == "skill" and (entry.get("detect_by") or {}).get("intent_patterns")
    }
    assert len(with_patterns) == 13, (
        "expected 13 skills with intent_patterns, found %d -- update AC-2 and the case file together"
        % len(with_patterns)
    )
    negatives = {
        case["skill_id"]
        for case in _load_cases()["cases"]
        if case["expect_activation"] is False
    }
    assert with_patterns <= negatives, "skills missing a near-miss negative: %s" % sorted(
        with_patterns - negatives
    )


def test_runner_defines_no_matcher_of_its_own() -> None:
    """AC-8. A second matcher is the failure backlog #150 already paid for."""
    source = RUNNER.read_text(encoding="utf-8")
    assert "trigger_runtime_core" in source, "the runner must delegate to the shipped resolver"
    assert "skill_is_candidate" in source
    for forbidden in ("def values_match", "def normalize_text", "issubset("):
        assert forbidden not in source, (
            "run_skill_eval.py must not reimplement matching (%r found) -- import the core instead"
            % forbidden
        )


def test_json_report_carries_run_identity() -> None:
    """AC-4: identity fields are present, and absent values say 'unknown' explicitly."""
    report = _report(_run(CASES, ["--harness", "pytest-guard"]))
    identity = report["run_identity"]
    for field in ("commit_sha", "skill_snapshot_digest", "harness", "cases_file", "registry", "platform"):
        assert identity.get(field), "run identity is missing %r" % field
    assert identity["harness"] == "pytest-guard"
    report_default = _report(_run(CASES))
    assert report_default["run_identity"]["harness"] == "unknown", (
        "an unsupplied harness must be an explicit 'unknown', never an empty string"
    )


# ---------------------------------------------------------------------------
# Mutations: each breaks exactly one invariant and must turn the runner red.
# ---------------------------------------------------------------------------

def test_flipped_expectation_is_a_hard_failure(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    target = next(c for c in document["cases"] if c["id"] == "sysdebug-pos")
    target["expect_activation"] = False
    proc = _run(_write(tmp_path, document))
    report = _report(proc)
    assert proc.returncode == 1
    assert report["totals"]["failed"] == 1
    entry = next(r for r in report["results"] if r["id"] == "sysdebug-pos")
    assert entry["status"] == "fail"


def test_new_known_gap_trips_the_ratchet(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document["cases"].append(
        {
            "id": "ratchet-probe",
            "skill_id": "api-design",
            "prompt": "這個功能的API設計要怎麼做",
            "classification": "feature",
            "phase": "implement",
            "expect_activation": True,
            "known_gap": "PROBE",
        }
    )
    proc = _run(_write(tmp_path, document))
    report = _report(proc)
    assert proc.returncode == 1, "a 14th known gap against a baseline of 13 must fail"
    assert any("ratchet only goes down" in reason for reason in report["verdict"]["reasons"])


def test_missing_baseline_is_a_failure(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document.pop("known_gap_baseline")
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert any("baseline missing" in r for r in _report(proc)["verdict"]["reasons"])


def test_uncovered_skill_is_a_failure(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document["cases"] = [c for c in document["cases"] if c["skill_id"] != "doc-lookup"]
    proc = _run(_write(tmp_path, document))
    report = _report(proc)
    assert proc.returncode == 1
    assert report["uncovered_skills"] == ["doc-lookup"]


def test_gated_case_reports_inert_not_a_silent_negative(tmp_path: Path) -> None:
    """The platform literal is 'claude', not 'claude-code'.

    skill_is_candidate returns (False, {}) on a platform miss, so a case with the
    wrong literal would otherwise read as a passing negative while measuring
    nothing at all.
    """
    document = copy.deepcopy(_load_cases())
    document["cases"] = [c for c in document["cases"] if c["id"] == "sysdebug-neg"]
    document["known_gap_baseline"] = 0
    proc = _run(_write(tmp_path, document), ["--platform", "claude-code"])
    report = _report(proc)
    assert proc.returncode == 1
    assert report["totals"]["inert"] == 1
    assert report["totals"]["passed"] == 0, "a gated case must never be scored as a pass"


def test_duplicate_case_id_is_rejected(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document["cases"].append(copy.deepcopy(document["cases"][0]))
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "duplicate case id" in proc.stderr


def test_unknown_skill_id_is_rejected(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document["cases"][0]["skill_id"] = "no-such-skill"
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "not a kind:skill entry" in proc.stderr


def test_non_boolean_expectation_is_rejected(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document["cases"][0]["expect_activation"] = "true"
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "must be a boolean" in proc.stderr
