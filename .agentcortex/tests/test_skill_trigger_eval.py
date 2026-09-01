"""Guards for the skill trigger-accuracy eval runner.

Spec: docs/specs/skill-trigger-accuracy-eval.md (backlog #165, issue #398)
Review that shaped this file: docs/reviews/2026-09-01-skill-trigger-eval-review.md

Two disciplines this file exists to hold, both learned the hard way in review:

1. **The ratchet is anchored HERE, not in the file it guards.** An earlier version
   read both the gap count and its baseline from `skills.yaml`, so a regression
   plus a one-character edit to that integer took the suite from red to green with
   every guard still passing. The expected counts below are the external anchor:
   lowering a baseline now requires editing two files in the same change.

2. **The no-second-matcher guard is a RUNTIME proof, not a grep.** The first
   version asserted only that two strings appeared in the source — and both live in
   docstrings, so a mutant that deleted the delegation and hand-rolled the matcher
   passed all five assertions and produced a byte-identical green run.
"""

from __future__ import annotations

import copy
import importlib.util
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
DEPLOY = ROOT / ".agentcortex" / "bin" / "deploy.sh"
GOLDEN = ROOT / "tests" / "ci" / "fixtures" / "deploy_manifest_golden.txt"

# --- External ratchet anchor (discipline 1 above). Lower these ONLY together with
# --- the matching baselines in skills.yaml, in the same change.
EXPECTED_KNOWN_GAPS = 19
EXPECTED_USER_VISIBLE_GAPS = 16
EXPECTED_SKILLS_WITH_PATTERNS = 13


def _run(cases_path: Path, extra=None):
    argv = [sys.executable, str(RUNNER), "--root", str(ROOT), "--cases", str(cases_path), "--format", "json"]
    argv.extend(extra or [])
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")


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


def _import_runner():
    spec = importlib.util.spec_from_file_location("_acx_run_skill_eval_under_test", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    assert totals["skills_covered"] == totals["skills_in_registry"], "AC-1: every skill needs a case"


def test_every_skill_has_a_positive_case() -> None:
    """AC-1's '>=1 positive each' -- coverage alone would pass on negatives only."""
    report = _report(_run(CASES))
    assert report["skills_without_positive"] == [], (
        "skills with no positive case: %s" % report["skills_without_positive"]
    )


def test_gap_counts_match_the_external_anchor() -> None:
    """The ratchet's anchor lives here, outside the file it guards."""
    totals = _report(_run(CASES))["totals"]
    assert totals["known_gaps"] == EXPECTED_KNOWN_GAPS, (
        "known gaps moved to %d; if that is a real fix, lower BOTH this constant and "
        "skills.yaml's known_gap_baseline in the same change"
        % totals["known_gaps"]
    )
    assert totals["user_visible_gaps"] == EXPECTED_USER_VISIBLE_GAPS
    assert totals["known_gap_baseline"] == EXPECTED_KNOWN_GAPS, "baseline drifted from the anchor"
    assert totals["user_visible_gap_baseline"] == EXPECTED_USER_VISIBLE_GAPS


def test_every_skill_with_patterns_has_a_near_miss_negative() -> None:
    """AC-2. verification-before-completion is the single exclusion (empty patterns)."""
    with REGISTRY.open(encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)
    with_patterns = {
        entry["id"]
        for entry in registry["entries"]
        if entry.get("kind") == "skill" and (entry.get("detect_by") or {}).get("intent_patterns")
    }
    assert len(with_patterns) == EXPECTED_SKILLS_WITH_PATTERNS
    negatives = {c["skill_id"] for c in _load_cases()["cases"] if c["expect_pattern_match"] is False}
    assert with_patterns <= negatives, "missing a near-miss negative: %s" % sorted(with_patterns - negatives)


def test_runner_actually_calls_the_shipped_resolver() -> None:
    """AC-8 as a RUNTIME proof.

    A source grep cannot do this job: the identifying strings also appear in
    docstrings, so a hand-rolled-matcher mutant passes a grep and produces a
    byte-identical green run. Here the real core is wrapped in a spy and the run is
    driven in-process, so the assertion fails unless the delegation actually happens.
    """
    module = _import_runner()
    real_core = module._load_core(ROOT)
    calls = {"candidate": 0, "activated": 0}

    class Spy:
        VALID_PHASES = real_core.VALID_PHASES

        @staticmethod
        def skill_is_candidate(*args, **kwargs):
            calls["candidate"] += 1
            return real_core.skill_is_candidate(*args, **kwargs)

        @staticmethod
        def skill_is_activated(*args, **kwargs):
            calls["activated"] += 1
            return real_core.skill_is_activated(*args, **kwargs)

    original = module._load_core
    module._load_core = lambda root: Spy
    try:
        report = module.run(ROOT, CASES, REGISTRY, "claude", "spy")
    finally:
        module._load_core = original

    assert calls["candidate"] == report["totals"]["cases"], (
        "the runner must delegate every case to trigger_runtime_core.skill_is_candidate; "
        "saw %d call(s) for %d case(s)" % (calls["candidate"], report["totals"]["cases"])
    )
    assert calls["activated"] > 0, "activation cross-check must consult skill_is_activated"


def test_runner_is_source_only() -> None:
    """D-5. Re-shipping it without trigger_runtime_core.py hands adopters a dead tool."""
    assert "run_skill_eval" not in DEPLOY.read_text(encoding="utf-8"), (
        "run_skill_eval.py must stay out of deploy.sh: its only import, "
        "trigger_runtime_core.py, is itself source-only, so a deployed runner cannot start"
    )
    assert "run_skill_eval" not in GOLDEN.read_text(encoding="utf-8")


def test_json_report_carries_run_identity() -> None:
    """AC-4: identity fields present, and absent values say 'unknown' explicitly."""
    identity = _report(_run(CASES, ["--harness", "pytest-guard"]))["run_identity"]
    for field in ("commit_sha", "skill_snapshot_digest", "harness", "cases_file", "registry", "platform"):
        assert identity.get(field), "run identity is missing %r" % field
    assert identity["harness"] == "pytest-guard"
    assert _report(_run(CASES))["run_identity"]["harness"] == "unknown"


# ---------------------------------------------------------------------------
# Mutations: each breaks exactly one invariant and must turn the runner red.
# ---------------------------------------------------------------------------

def test_flipped_expectation_is_a_hard_failure(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    next(c for c in document["cases"] if c["id"] == "sysdebug-pos")["expect_pattern_match"] = False
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert _report(proc)["totals"]["failed"] == 1


def test_new_known_gap_trips_the_ratchet(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document["cases"].append(
        {
            "id": "ratchet-probe",
            "skill_id": "api-design",
            "prompt": "這個功能的API設計要怎麼做",
            "classification": "feature",
            "phase": "implement",
            "expect_pattern_match": True,
            "known_gap": "DEFECT-1",
        }
    )
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert any("cap at today" in r for r in _report(proc)["verdict"]["reasons"])


def test_fixing_a_gap_without_lowering_the_baseline_also_fails(tmp_path: Path) -> None:
    """The ratchet is exact, not '<='. Silent headroom is how a real failure hides."""
    document = copy.deepcopy(_load_cases())
    document["cases"] = [c for c in document["cases"] if c["id"] != "tdd-pos-zhtw"]
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert any("cap at today" in r for r in _report(proc)["verdict"]["reasons"])


def test_missing_baseline_is_a_failure(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    document.pop("user_visible_gap_baseline")
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert any("user_visible_gap_baseline missing" in r for r in _report(proc)["verdict"]["reasons"])


def test_undeclared_activates_anyway_is_a_hard_failure(tmp_path: Path) -> None:
    """H-2. A lexical negative for a skill that loads regardless must say so."""
    document = copy.deepcopy(_load_cases())
    next(c for c in document["cases"] if c["id"] == "karpathy-neg").pop("activates_anyway")
    proc = _run(_write(tmp_path, document))
    report = _report(proc)
    assert proc.returncode == 1
    entry = next(r for r in report["results"] if r["id"] == "karpathy-neg")
    assert entry["status"] == "fail"
    assert "even without one" in entry["detail"]


def test_stale_activates_anyway_annotation_is_a_hard_failure(tmp_path: Path) -> None:
    document = copy.deepcopy(_load_cases())
    next(c for c in document["cases"] if c["id"] == "tdd-neg")["activates_anyway"] = True
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "stale annotation" in next(
        r for r in _report(proc)["results"] if r["id"] == "tdd-neg"
    )["detail"]


def test_gated_case_reports_inert_not_a_silent_negative(tmp_path: Path) -> None:
    """The platform literal is 'claude', not 'claude-code'."""
    document = copy.deepcopy(_load_cases())
    document["cases"] = [c for c in document["cases"] if c["id"] == "sysdebug-neg"]
    document["known_gap_baseline"] = 0
    document["user_visible_gap_baseline"] = 0
    proc = _run(_write(tmp_path, document), ["--platform", "claude-code"])
    report = _report(proc)
    assert proc.returncode == 1
    assert report["totals"]["inert"] == 1
    assert report["totals"]["passed"] == 0, "a gated case must never be scored as a pass"


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    """M-3. A typo'd key silently ignored is the suite's own trap, one level up."""
    document = copy.deepcopy(_load_cases())
    document["cases"][0]["expect_pattern_matchh"] = False
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "unknown key" in proc.stderr


def test_free_text_known_gap_is_rejected(tmp_path: Path) -> None:
    """AC-7. Otherwise any failure can be excused by typing a word."""
    document = copy.deepcopy(_load_cases())
    next(c for c in document["cases"] if c["id"] == "tdd-pos-zhtw")["known_gap"] = "wip"
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "must name a defect or backlog row" in proc.stderr


def test_invalid_phase_is_rejected(tmp_path: Path) -> None:
    """M-4. phase drives the activation cross-check, so it cannot be free text."""
    document = copy.deepcopy(_load_cases())
    document["cases"][0]["phase"] = "not-a-real-phase"
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "is not one of" in proc.stderr


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
    document["cases"][0]["expect_pattern_match"] = "true"
    proc = _run(_write(tmp_path, document))
    assert proc.returncode == 1
    assert "must be a boolean" in proc.stderr


def test_missing_resolver_fails_with_a_message_not_a_traceback(tmp_path: Path) -> None:
    """C-1. The tool is source-only; run from a tree without the core it must say so."""
    fake_root = tmp_path / "deployed"
    (fake_root / ".agentcortex" / "tools").mkdir(parents=True)
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--root", str(fake_root), "--cases", str(CASES),
         "--registry", str(REGISTRY)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 1
    assert "Traceback" not in proc.stderr, "a missing resolver must be a message, not a crash"
    assert "canonical resolver not found" in proc.stderr
