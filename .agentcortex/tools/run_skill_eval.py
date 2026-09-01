#!/usr/bin/env python3
"""Skill trigger-accuracy eval runner.

Measures whether registry `detect_by.intent_patterns` DATA discriminates: does a
natural phrasing reach the intended skill, and does a near-miss correctly fail to?

Scoring is static and delegates to the SHIPPED resolver
(`trigger_runtime_core.skill_is_candidate`). It MUST NOT carry a matcher of its
own — backlog #150 records what that costs: the old `resolve_runtime_contract.py`
had its own bidirectional-substring matcher which "masked the gap, so the
simulation CLI reported activations the runtime never performed".

This does NOT measure whether an agent routes correctly. That is a different
surface and stays in issue #254. Do not rename this "effectiveness".

Spec: docs/specs/skill-trigger-accuracy-eval.md (backlog #165, issue #398)
Run:  python .agentcortex/tools/run_skill_eval.py [--format json]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
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


def _load_core(root: Path) -> Any:
    """Load the canonical resolver. Never reimplement its matching here."""
    module_path = root / ".agentcortex" / "tools" / "trigger_runtime_core.py"
    spec = importlib.util.spec_from_file_location("_acx_trigger_runtime_core", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load canonical resolver: %s" % module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError:  # pragma: no cover - environment-dependent
        raise RuntimeError("pyyaml is required: pip install pyyaml")
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _git_sha(root: Path) -> str:
    """Best-effort commit SHA. Returns the literal 'unknown' when unavailable."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if proc.returncode != 0:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def _snapshot_digest(root: Path) -> str:
    """Skill-package snapshot digest, or the literal 'unknown'."""
    tool = root / ".agentcortex" / "tools" / "resolve_skill_lockfile.py"
    if not tool.is_file():
        return "unknown"
    try:
        proc = subprocess.run(
            [sys.executable, str(tool), "--root", str(root), "--snapshot-only"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    if proc.returncode != 0:
        return "unknown"
    try:
        return json.loads(proc.stdout).get("snapshot_digest") or "unknown"
    except (ValueError, AttributeError):
        return "unknown"


def score_case(core: Any, entry: dict, case: dict, platform: str) -> tuple:
    """Score one case. Returns (status, detail).

    The measured signal is `matches["manual"]` — the flag that reflects
    free-text-to-pattern resolution. It is NOT `is_candidate`: that is
    `manual or phase_ready`, so it is true for any case whose phase sits in the
    skill's phase_scope, which would make every positive trivially pass and
    every negative impossible.
    """
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
        # gates the entry out. The case then measures nothing at all, which must
        # be an error rather than a silent negative.
        return INERT, (
            "classification %r / platform %r is gated out by the registry entry -- "
            "this case measures nothing" % (case["classification"], platform)
        )

    actual = bool(matches.get("manual"))
    expected = bool(case["expect_activation"])
    if actual == expected:
        return PASS, ""
    detail = "expected activation=%s, got %s" % (expected, actual)
    if case.get("known_gap"):
        return KNOWN_GAP, detail
    return FAIL, detail


def _validate_case(case: Any, index: int, skill_ids: set) -> None:
    if not isinstance(case, dict):
        raise ValueError("case %d is not a mapping" % index)
    for field in ("id", "skill_id", "prompt", "classification", "phase"):
        if not isinstance(case.get(field), str) or not case[field].strip():
            raise ValueError("case %d: %r must be a non-empty string" % (index, field))
    if not isinstance(case.get("expect_activation"), bool):
        raise ValueError("case %r: expect_activation must be a boolean" % case.get("id"))
    if case["skill_id"] not in skill_ids:
        raise ValueError(
            "case %r: skill_id %r is not a kind:skill entry in the registry"
            % (case["id"], case["skill_id"])
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
        _validate_case(case, index, set(entries))
        if case["id"] in seen:
            raise ValueError("duplicate case id: %r" % case["id"])
        seen.add(case["id"])
        status, detail = score_case(core, entries[case["skill_id"]], case, platform)
        results.append(
            {
                "id": case["id"],
                "skill_id": case["skill_id"],
                "prompt": case["prompt"],
                "expect_activation": bool(case["expect_activation"]),
                "status": status,
                "detail": detail,
                "known_gap": case.get("known_gap") or None,
            }
        )

    covered = {case["skill_id"] for case in cases}
    baseline = document.get("known_gap_baseline")
    return {
        "run_identity": {
            "commit_sha": _git_sha(root),
            "skill_snapshot_digest": _snapshot_digest(root),
            "harness": harness or "unknown",
            "cases_file": str(cases_path.as_posix()),
            "registry": str(registry_path.as_posix()),
            "platform": platform,
        },
        "totals": {
            "cases": len(results),
            "passed": sum(1 for r in results if r["status"] == PASS),
            "failed": sum(1 for r in results if r["status"] == FAIL),
            "known_gaps": sum(1 for r in results if r["status"] == KNOWN_GAP),
            "inert": sum(1 for r in results if r["status"] == INERT),
            "skills_covered": len(covered),
            "skills_in_registry": len(entries),
            "known_gap_baseline": baseline if isinstance(baseline, int) else None,
        },
        "uncovered_skills": sorted(set(entries) - covered),
        "results": results,
    }


def _verdict(report: dict) -> tuple:
    """Return (exit_code, reasons). Deterministic scoring permits a hard exit."""
    totals = report["totals"]
    reasons = []
    if totals["failed"]:
        reasons.append("%d case(s) failed" % totals["failed"])
    if totals["inert"]:
        reasons.append("%d case(s) measured nothing (classification/platform gated)" % totals["inert"])
    if report["uncovered_skills"]:
        reasons.append("skills with no case: %s" % ", ".join(report["uncovered_skills"]))
    baseline = totals["known_gap_baseline"]
    if baseline is None:
        reasons.append("known_gap_baseline missing from the cases file")
    elif totals["known_gaps"] > baseline:
        reasons.append(
            "known gaps rose to %d against a baseline of %d -- the ratchet only goes down"
            % (totals["known_gaps"], baseline)
        )
    return (1 if reasons else 0), reasons


def _print_text(report: dict, reasons: list) -> None:
    totals = report["totals"]
    print(
        "skill trigger accuracy: %d case(s) -- %d pass, %d fail, %d known gap, %d inert"
        % (totals["cases"], totals["passed"], totals["failed"], totals["known_gaps"], totals["inert"])
    )
    print(
        "coverage: %d/%d kind:skill entries"
        % (totals["skills_covered"], totals["skills_in_registry"])
    )
    # Known gaps are printed on EVERY run, never silently skipped (spec §D-2).
    gaps = [r for r in report["results"] if r["status"] == KNOWN_GAP]
    if gaps:
        print(
            "known gaps (%d, baseline %s) -- asserted, not excused:"
            % (len(gaps), totals["known_gap_baseline"])
        )
        for result in gaps:
            print("  - %s [%s] %s: %s" % (result["id"], result["known_gap"], result["skill_id"], result["detail"]))
    for result in report["results"]:
        if result["status"] in (FAIL, INERT):
            print("  [%s] %s (%s): %s" % (result["status"].upper(), result["id"], result["skill_id"], result["detail"]))
    for reason in reasons:
        print("FAIL: %s" % reason)


def main() -> int:
    # Force UTF-8 stdout so the zh-TW case prompts survive a cp950 Windows
    # console (child processes default to the console codepage). Without this,
    # `--format json` emits cp950 bytes that no JSON parser can read -- measured,
    # not assumed. Same guard as check_ssot_caps.py / check_routing_actions.py.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--cases", default=None, help="Path to the eval cases YAML")
    parser.add_argument("--registry", default=None, help="Path to trigger-registry.yaml")
    parser.add_argument("--platform", default=DEFAULT_PLATFORM, help="Platform to score against")
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
