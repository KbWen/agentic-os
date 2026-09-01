#!/usr/bin/env python3
"""Skill trigger-accuracy eval runner.

Measures whether registry `detect_by.intent_patterns` DATA discriminates: does a
natural phrasing lexically reach the intended skill, and does a near-miss not?

Scoring is static and delegates to the SHIPPED resolver
(`trigger_runtime_core.skill_is_candidate`). It MUST NOT carry a matcher of its
own — backlog #150 records what that costs: the old `resolve_runtime_contract.py`
had its own bidirectional-substring matcher which "masked the gap, so the
simulation CLI reported activations the runtime never performed".

TWO DIFFERENT QUESTIONS, BOTH REPORTED:
  * `expect_pattern_match` -- did the phrase reach the skill's patterns? This is
    what the suite asserts. It is a LEXICAL claim, not an activation claim.
  * activation -- does the skill actually load? A skill with `load_policy:
    phase-entry`, or one whose `phase_conditions` fire, loads regardless of the
    prompt. A lexical negative for such a skill is true but says nothing about
    what the user gets, so the case MUST declare `activates_anyway: true`.
    An undeclared mismatch is a hard failure: it is how a suite ends up
    asserting "the near-miss was correctly rejected" about a skill that loaded.

This does NOT measure whether an agent routes correctly. That is a different
surface and stays in issue #254. Do not rename this "effectiveness".

SOURCE-ONLY (spec §D-5). This tool is deliberately NOT deployed: its only import,
`trigger_runtime_core.py`, is itself source-only, as is the whole resolver
toolchain. Shipping the runner alone hands adopters a tool that cannot start.

Spec: docs/specs/skill-trigger-accuracy-eval.md (backlog #165, issue #398)
Run:  python .agentcortex/tools/run_skill_eval.py [--format json]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CASES = ".agentcortex/eval/skills.yaml"
DEFAULT_REGISTRY = ".agentcortex/metadata/trigger-registry.yaml"
DEFAULT_PLATFORM = "claude"

# Case statuses.
PASS = "pass"
FAIL = "fail"
KNOWN_GAP = "known_gap"
INERT = "inert"

# Fail-closed: a typo'd key must be an error, never a silently ignored field.
ALLOWED_KEYS = frozenset(
    {
        "id",
        "skill_id",
        "prompt",
        "classification",
        "phase",
        "platform",
        "expect_pattern_match",
        "activates_anyway",
        "known_gap",
        "note",
    }
)

# A known gap must name a defect or a backlog row, never free text (AC-7).
KNOWN_GAP_RE = re.compile(r"^(DEFECT-\d+|#\d+)$")


def _load_core(root: Path) -> Any:
    """Load the canonical resolver. Never reimplement its matching here."""
    module_path = root / ".agentcortex" / "tools" / "trigger_runtime_core.py"
    if not module_path.is_file():
        raise RuntimeError(
            "canonical resolver not found: %s -- this tool is source-only and cannot "
            "run against a deployed tree (spec D-5)" % module_path
        )
    spec = importlib.util.spec_from_file_location("_acx_trigger_runtime_core", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load canonical resolver: %s" % module_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except OSError as exc:
        raise RuntimeError("cannot load canonical resolver: %s (%s)" % (module_path, exc))
    return module


def _load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError:  # pragma: no cover - environment-dependent
        raise RuntimeError("pyyaml is required: pip install pyyaml")
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _probe(argv: list, timeout: int) -> str:
    """Run a best-effort identity probe. Returns stdout, or '' on any failure."""
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def _git_sha(root: Path) -> str:
    return _probe(["git", "-C", str(root), "rev-parse", "HEAD"], 10).strip() or "unknown"


def _snapshot_digest(root: Path) -> str:
    tool = root / ".agentcortex" / "tools" / "resolve_skill_lockfile.py"
    if not tool.is_file():
        return "unknown"
    out = _probe([sys.executable, str(tool), "--root", str(root), "--snapshot-only"], 60)
    try:
        return json.loads(out).get("snapshot_digest") or "unknown"
    except (ValueError, AttributeError):
        return "unknown"


def score_case(core: Any, entry: dict, case: dict, default_platform: str) -> dict:
    """Score one case against the shipped resolver.

    The lexical signal is `matches["manual"]`. It is NOT `is_candidate`, which is
    `manual or phase_ready` and would make every positive trivially pass and every
    negative impossible. Activation is read separately from `skill_is_activated`,
    the real runtime decision, and cross-checked against the case's own claim.
    """
    platform = case.get("platform") or default_platform
    _is_candidate, matches = core.skill_is_candidate(
        entry,
        classification=case["classification"],
        phase=case["phase"],
        platform=platform,
        manual_skills=[case["prompt"]],
        scope_signals=[],
        failure_signals=[],
    )
    if not matches:
        # skill_is_candidate returns (False, {}) when classification or platform
        # gates the entry out. The case then measures nothing, which must be an
        # error rather than a silent negative.
        return {
            "status": INERT,
            "detail": "classification %r / platform %r is gated out by the registry entry -- "
            "this case measures nothing" % (case["classification"], platform),
            "activated": None,
            "user_visible_gap": False,
        }

    actual = bool(matches.get("manual"))
    expected = bool(case["expect_pattern_match"])
    activated = bool(
        core.skill_is_activated(
            entry, classification=case["classification"], phase=case["phase"], matches=matches
        )
    )
    # The question that matters is not "does it activate" but "would it activate
    # even if this phrase had not matched". Otherwise a spurious load caused by an
    # over-triggering pattern reads as "it loads anyway", hiding the very harm.
    without_match = bool(
        core.skill_is_activated(
            entry,
            classification=case["classification"],
            phase=case["phase"],
            matches=dict(matches, manual=False),
        )
    )
    declared = bool(case.get("activates_anyway"))

    # A lexical negative for a skill that loads anyway says nothing about what the
    # user gets. Force the case to say so out loud, and reject a stale annotation.
    if not expected and without_match and not declared:
        return {
            "status": FAIL,
            "detail": "expects no pattern match, but the skill loads in this phase even without "
            "one (load_policy=%r) -- declare activates_anyway: true or re-site the case"
            % entry.get("load_policy"),
            "activated": activated,
            "user_visible_gap": False,
        }
    if declared and not without_match:
        return {
            "status": FAIL,
            "detail": "declares activates_anyway but the skill does not load here without a match -- stale annotation",
            "activated": activated,
            "user_visible_gap": False,
        }

    if actual == expected:
        return {"status": PASS, "detail": "", "activated": activated, "user_visible_gap": False}

    detail = "expected pattern_match=%s, got %s" % (expected, actual)
    if case.get("known_gap"):
        # A gap the user never feels (the skill loads by another path) is real but
        # not user-visible. Both counts are reported; both are ratcheted.
        return {
            "status": KNOWN_GAP,
            "detail": detail,
            "activated": activated,
            "user_visible_gap": not without_match,
        }
    return {"status": FAIL, "detail": detail, "activated": activated, "user_visible_gap": False}


def _validate_case(case: Any, index: int, skill_ids: set, valid_phases: set) -> None:
    if not isinstance(case, dict):
        raise ValueError("case %d is not a mapping" % index)
    unknown = sorted(set(case) - ALLOWED_KEYS)
    if unknown:
        raise ValueError(
            "case %r: unknown key(s) %s -- a typo must be an error, not a silently "
            "ignored field" % (case.get("id", index), ", ".join(repr(k) for k in unknown))
        )
    for field in ("id", "skill_id", "prompt", "classification", "phase"):
        if not isinstance(case.get(field), str) or not case[field].strip():
            raise ValueError("case %d: %r must be a non-empty string" % (index, field))
    if not isinstance(case.get("expect_pattern_match"), bool):
        raise ValueError("case %r: expect_pattern_match must be a boolean" % case["id"])
    if "activates_anyway" in case and not isinstance(case["activates_anyway"], bool):
        raise ValueError("case %r: activates_anyway must be a boolean" % case["id"])
    if case["phase"] not in valid_phases:
        raise ValueError(
            "case %r: phase %r is not one of %s"
            % (case["id"], case["phase"], ", ".join(sorted(valid_phases)))
        )
    if case["skill_id"] not in skill_ids:
        raise ValueError(
            "case %r: skill_id %r is not a kind:skill entry in the registry"
            % (case["id"], case["skill_id"])
        )
    gap = case.get("known_gap")
    if gap is not None and not (isinstance(gap, str) and KNOWN_GAP_RE.match(gap)):
        raise ValueError(
            "case %r: known_gap %r must name a defect or backlog row (DEFECT-<n> or #<n>) -- "
            "free text would let any failure be excused" % (case["id"], gap)
        )


def run(root: Path, cases_path: Path, registry_path: Path, platform: str, harness: str) -> dict:
    core = _load_core(root)
    registry = _load_yaml(registry_path) or {}
    entries = {
        entry["id"]: entry
        for entry in (registry.get("entries") or [])
        if entry.get("kind") == "skill"
    }
    if not entries:
        raise ValueError("registry %s contains no kind:skill entries" % registry_path)

    document = _load_yaml(cases_path) or {}
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("%s contains no cases" % cases_path)

    seen = set()
    results = []
    for index, case in enumerate(cases):
        _validate_case(case, index, set(entries), set(core.VALID_PHASES))
        if case["id"] in seen:
            raise ValueError("duplicate case id: %r" % case["id"])
        seen.add(case["id"])
        scored = score_case(core, entries[case["skill_id"]], case, platform)
        results.append(
            {
                "id": case["id"],
                "skill_id": case["skill_id"],
                "prompt": case["prompt"],
                "expect_pattern_match": bool(case["expect_pattern_match"]),
                "known_gap": case.get("known_gap") or None,
                **scored,
            }
        )

    covered = {case["skill_id"] for case in cases}
    positives = {c["skill_id"] for c in cases if c["expect_pattern_match"]}
    gaps = [r for r in results if r["status"] == KNOWN_GAP]
    return {
        "run_identity": {
            "commit_sha": _git_sha(root),
            "skill_snapshot_digest": _snapshot_digest(root),
            "harness": harness or "unknown",
            "cases_file": cases_path.as_posix(),
            "registry": registry_path.as_posix(),
            "platform": platform,
        },
        "totals": {
            "cases": len(results),
            "passed": sum(1 for r in results if r["status"] == PASS),
            "failed": sum(1 for r in results if r["status"] == FAIL),
            "known_gaps": len(gaps),
            "user_visible_gaps": sum(1 for r in gaps if r["user_visible_gap"]),
            "inert": sum(1 for r in results if r["status"] == INERT),
            "skills_covered": len(covered),
            "skills_with_positive": len(positives),
            "skills_in_registry": len(entries),
            "known_gap_baseline": document.get("known_gap_baseline"),
            "user_visible_gap_baseline": document.get("user_visible_gap_baseline"),
        },
        "uncovered_skills": sorted(set(entries) - covered),
        "skills_without_positive": sorted(set(entries) - positives),
        "results": results,
    }


def _verdict(report: dict) -> tuple:
    """Return (exit_code, reasons). Deterministic scoring permits a hard exit.

    Coverage completeness is deliberately NOT here. It is an invariant of THIS
    repo's case file, asserted by the guard test -- putting it in the runner made
    the tool reject any other case file, which is the opposite of reusable.
    """
    totals = report["totals"]
    reasons = []
    if totals["failed"]:
        reasons.append("%d case(s) failed" % totals["failed"])
    if totals["inert"]:
        reasons.append("%d case(s) measured nothing (classification/platform gated)" % totals["inert"])
    for key, label in (
        ("known_gap_baseline", "known_gaps"),
        ("user_visible_gap_baseline", "user_visible_gaps"),
    ):
        baseline = totals[key]
        if not isinstance(baseline, int):
            reasons.append("%s missing from the cases file" % key)
        elif totals[label] != baseline:
            reasons.append(
                "%s is %d against a declared baseline of %d -- cap at today: fix the gap and "
                "lower the baseline in the same change" % (label, totals[label], baseline)
            )
    return (1 if reasons else 0), reasons


def _print_text(report: dict, reasons: list) -> None:
    totals = report["totals"]
    print(
        "skill trigger accuracy: %d case(s) -- %d pass, %d fail, %d known gap, %d inert"
        % (totals["cases"], totals["passed"], totals["failed"], totals["known_gaps"], totals["inert"])
    )
    print(
        "coverage: %d/%d kind:skill entries (%d with a positive case)"
        % (totals["skills_covered"], totals["skills_in_registry"], totals["skills_with_positive"])
    )
    gaps = [r for r in report["results"] if r["status"] == KNOWN_GAP]
    if gaps:
        # Known gaps are printed on EVERY run, never silently skipped (spec D-2).
        print(
            "known gaps: %d (baseline %s), of which %d are user-visible (baseline %s):"
            % (
                totals["known_gaps"],
                totals["known_gap_baseline"],
                totals["user_visible_gaps"],
                totals["user_visible_gap_baseline"],
            )
        )
        for result in gaps:
            print(
                "  - %s [%s] %s%s: %s"
                % (
                    result["id"],
                    result["known_gap"],
                    result["skill_id"],
                    "" if result["user_visible_gap"] else " (skill loads anyway -- not user-visible)",
                    result["detail"],
                )
            )
    for result in report["results"]:
        if result["status"] in (FAIL, INERT):
            print("  [%s] %s (%s): %s" % (result["status"].upper(), result["id"], result["skill_id"], result["detail"]))
    for reason in reasons:
        print("FAIL: %s" % reason)


def main() -> int:
    # Force UTF-8 stdout so the zh-TW case prompts survive a cp950 Windows console
    # (child processes default to the console codepage). Without this, --format json
    # emits cp950 bytes that no JSON parser can read -- measured, not assumed. Same
    # guard as check_ssot_caps.py / check_routing_actions.py.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--cases", default=None, help="Path to the eval cases YAML")
    parser.add_argument("--registry", default=None, help="Path to trigger-registry.yaml")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM, help="Default platform when a case omits one")
    parser.add_argument(
        "--harness",
        default="",
        help="Caller-supplied model/harness identity for the run header; 'unknown' when omitted",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    cases_path = Path(args.cases) if args.cases else root / DEFAULT_CASES
    registry_path = Path(args.registry) if args.registry else root / DEFAULT_REGISTRY

    for path, label in ((cases_path, "cases file"), (registry_path, "registry")):
        if not path.is_file():
            print("FAIL: %s not found: %s" % (label, path), file=sys.stderr)
            return 1

    try:
        report = run(root, cases_path, registry_path, args.platform, args.harness)
    except (RuntimeError, ValueError) as exc:
        print("FAIL: %s" % exc, file=sys.stderr)
        return 1

    exit_code, reasons = _verdict(report)
    if args.format == "json":
        report["verdict"] = {"exit_code": exit_code, "reasons": reasons}
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        _print_text(report, reasons)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
