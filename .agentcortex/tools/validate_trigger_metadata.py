#!/usr/bin/env python3
"""Validate Stage 1 trigger registry, compact index, and resolver parity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from trigger_runtime_core import (
    DEFAULT_COMPACT_INDEX,
    DEFAULT_REGISTRY,
    VALID_CLASSIFICATIONS,
    VALID_PHASES,
    build_compact_index,
    load_skill_package_manifest,
    load_json,
    load_registry,
    parse_frontmatter,
    parse_simple_yaml,
    resolve_runtime_contract,
    validate_skill_manifest_authority,
    validate_skill_package_manifest,
)


REQUIRED_ENTRY_FIELDS = {
    "id",
    "kind",
    "canonical_ref",
    "platforms",
    "phase_scope",
    "trigger_priority",
    "detect_by",
    "load_policy",
    "cost_type",
    "cost_risk",
    "runtime_anchor",
    "block_if_missed",
    "fallback_behavior",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate trigger registry, compact index, and selected skill metadata.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Path to the trigger registry file, relative to --root")
    parser.add_argument("--compact-index", default=DEFAULT_COMPACT_INDEX, help="Path to the compact index file, relative to --root")
    parser.add_argument(
        "--scenarios",
        default=".agentcortex/metadata/lifecycle-scenarios.json",
        help="Path to the lifecycle scenario file, relative to --root",
    )
    return parser.parse_args()


def ensure(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_skill_entry(root: Path, entry: dict[str, Any], errors: list[str]) -> None:
    summary_path = root / entry["canonical_ref"]
    mirror_path = root / entry["mirror_ref"]
    detail_path = root / entry["detail_ref"]
    skill_dir = detail_path.parent

    path_errors: list[str] = []
    ensure(summary_path.is_file(), f"missing summary metadata: {entry['canonical_ref']}", path_errors)
    ensure(mirror_path.is_file(), f"missing mirror metadata: {entry['mirror_ref']}", path_errors)
    ensure(detail_path.is_file(), f"missing detailed skill file: {entry['detail_ref']}", path_errors)
    if path_errors:
        errors.extend(path_errors)
        return

    summary = parse_frontmatter(summary_path)
    mirror = parse_simple_yaml(mirror_path.read_text(encoding="utf-8"))
    mirror_meta = mirror.get("agentcortex", {})

    ensure(summary.get("name") == entry["id"], f"{entry['id']}: summary name mismatch", errors)
    ensure(summary.get("phases") == entry["phase_scope"], f"{entry['id']}: summary phases mismatch", errors)
    ensure(summary.get("trigger_priority") == entry["trigger_priority"], f"{entry['id']}: summary trigger_priority mismatch", errors)
    ensure(summary.get("load_policy") == entry["load_policy"], f"{entry['id']}: summary load_policy mismatch", errors)
    ensure(summary.get("cost_type") == entry["cost_type"], f"{entry['id']}: summary cost_type mismatch", errors)
    ensure(summary.get("cost_risk") == entry["cost_risk"], f"{entry['id']}: summary cost_risk mismatch", errors)
    ensure(summary.get("runtime_anchor") == entry["runtime_anchor"], f"{entry['id']}: summary runtime_anchor mismatch", errors)

    ensure(mirror_meta.get("summary_ref") == entry["canonical_ref"], f"{entry['id']}: mirror summary_ref mismatch", errors)
    ensure(mirror_meta.get("detail_ref") == entry["detail_ref"], f"{entry['id']}: mirror detail_ref mismatch", errors)
    ensure(mirror_meta.get("trigger_priority") == entry["trigger_priority"], f"{entry['id']}: mirror trigger_priority mismatch", errors)
    ensure(mirror_meta.get("phase_scope") == entry["phase_scope"], f"{entry['id']}: mirror phase_scope mismatch", errors)
    ensure(mirror_meta.get("load_policy") == entry["load_policy"], f"{entry['id']}: mirror load_policy mismatch", errors)
    ensure(mirror_meta.get("cost_type") == entry["cost_type"], f"{entry['id']}: mirror cost_type mismatch", errors)
    ensure(mirror_meta.get("cost_risk") == entry["cost_risk"], f"{entry['id']}: mirror cost_risk mismatch", errors)
    ensure(mirror_meta.get("runtime_anchor") == entry["runtime_anchor"], f"{entry['id']}: mirror runtime_anchor mismatch", errors)

    manifest = load_skill_package_manifest(skill_dir)
    if manifest is None:
        return

    if manifest.get("id") != entry["id"]:
        errors.append(f"{entry['id']}: manifest id mismatch")

    for manifest_error in validate_skill_package_manifest(skill_dir, manifest):
        errors.append(manifest_error)
    for authority_error in validate_skill_manifest_authority(
        entry=entry,
        summary=summary,
        mirror=mirror,
        manifest=manifest,
        detail_path=detail_path,
    ):
        errors.append(authority_error)


def validate_entry(root: Path, entry: dict[str, Any], errors: list[str]) -> None:
    missing = REQUIRED_ENTRY_FIELDS - set(entry)
    if missing:
        errors.append(f"{entry.get('id', '<unknown>')}: missing fields {sorted(missing)}")
        return

    ensure(entry["kind"] in {"workflow", "policy", "skill"}, f"{entry['id']}: invalid kind", errors)
    ensure((root / entry["canonical_ref"]).exists(), f"{entry['id']}: missing canonical_ref {entry['canonical_ref']}", errors)
    if entry.get("mirror_ref"):
        ensure((root / entry["mirror_ref"]).exists(), f"{entry['id']}: missing mirror_ref {entry['mirror_ref']}", errors)
    if entry.get("detail_ref"):
        ensure((root / entry["detail_ref"]).exists(), f"{entry['id']}: missing detail_ref {entry['detail_ref']}", errors)

    ensure(bool(entry["runtime_anchor"]), f"{entry['id']}: runtime_anchor must not be empty", errors)
    ensure(isinstance(entry["phase_scope"], list), f"{entry['id']}: phase_scope must be a list", errors)
    ensure(all(phase in VALID_PHASES or phase == "hotfix" for phase in entry["phase_scope"]), f"{entry['id']}: invalid phase_scope", errors)
    ensure(isinstance(entry["platforms"], list), f"{entry['id']}: platforms must be a list", errors)
    ensure(isinstance(entry["detect_by"], dict), f"{entry['id']}: detect_by must be an object", errors)

    if entry["kind"] == "skill":
        validate_skill_entry(root, entry, errors)


def validate_scenario_file(path: Path, registry: dict[str, Any], errors: list[str]) -> None:
    ensure(path.is_file(), f"missing scenario file: {path}", errors)
    if errors:
        return

    scenarios = load_json(path)
    entries = scenarios.get("scenarios", [])
    ensure(isinstance(entries, list) and entries, "scenario file must contain a non-empty scenarios list", errors)

    valid_skill_ids = {entry["id"] for entry in registry.get("entries", []) if entry.get("kind") == "skill"}

    for scenario in entries:
        scenario_id = scenario.get("id", "<unknown>")
        required = {"id", "title", "classification", "phases", "probe_strategy", "phase_repeats", "candidate_skills", "triggered_skills", "notes"}
        missing = required - set(scenario)
        if missing:
            errors.append(f"{scenario_id}: missing scenario fields {sorted(missing)}")
            continue

        ensure(scenario["classification"] in VALID_CLASSIFICATIONS, f"{scenario_id}: invalid classification", errors)

        # Quick-win lifecycle contract: required phases MUST NOT include review or test
        if scenario["classification"] == "quick-win":
            for forbidden in ("review", "test"):
                ensure(
                    forbidden not in scenario["phases"],
                    f"{scenario_id}: quick-win required phases must not include '{forbidden}' "
                    f"(use optional_coverage instead per AGENTS.md hard rules)",
                    errors,
                )
        ensure(isinstance(scenario["phases"], list) and scenario["phases"], f"{scenario_id}: phases must be a non-empty list", errors)
        ensure(scenario["probe_strategy"] in {"platform-only", "slice+platform"}, f"{scenario_id}: invalid probe_strategy", errors)
        ensure(isinstance(scenario["phase_repeats"], dict), f"{scenario_id}: phase_repeats must be an object", errors)
        ensure(isinstance(scenario["candidate_skills"], list) and scenario["candidate_skills"], f"{scenario_id}: candidate_skills must be a non-empty list", errors)
        ensure(isinstance(scenario["triggered_skills"], list) and scenario["triggered_skills"], f"{scenario_id}: triggered_skills must be a non-empty list", errors)

        for phase, repeat in scenario["phase_repeats"].items():
            ensure(phase in scenario["phases"], f"{scenario_id}: phase_repeats contains unknown phase {phase}", errors)
            ensure(isinstance(repeat, int) and repeat >= 1, f"{scenario_id}: repeat count for {phase} must be >= 1", errors)

        for skill_id in scenario["candidate_skills"]:
            ensure(skill_id in valid_skill_ids, f"{scenario_id}: unknown candidate skill {skill_id}", errors)
        for skill_id in scenario["triggered_skills"]:
            ensure(skill_id in valid_skill_ids, f"{scenario_id}: unknown triggered skill {skill_id}", errors)
            ensure(skill_id in scenario["candidate_skills"], f"{scenario_id}: triggered skill {skill_id} must also be a candidate", errors)


def validate_compact_index(root: Path, compact_index_path: Path, registry_rel: str, errors: list[str]) -> None:
    ensure(compact_index_path.is_file(), f"missing compact index file: {compact_index_path}", errors)
    if errors:
        return

    expected_index = build_compact_index(root, registry_rel=registry_rel)
    actual_index = load_json(compact_index_path)
    if actual_index != expected_index:
        errors.append(
            "compact index is stale: regenerate .agentcortex/metadata/trigger-compact-index.json "
            "from the current registry and SKILL.md hashes"
        )


def validate_resolver_parity(root: Path, registry: dict[str, Any], errors: list[str]) -> None:
    sample_cases = [
        {
            "classification": "feature",
            "phase": "implement",
            "manual_skills": [],
            "scope_signals": ["testable logic", "api endpoint", "token"],
            "failure_signals": [],
            "expected": {"executing-plans", "verification-before-completion", "test-driven-development", "api-design", "auth-security"},
        },
        {
            "classification": "feature",
            "phase": "review",
            "manual_skills": [],
            "scope_signals": ["token", "dependency"],
            "failure_signals": [],
            "expected": {"red-team-adversarial", "requesting-code-review", "auth-security", "production-readiness"},
        },
        {
            "classification": "hotfix",
            "phase": "implement",
            "manual_skills": [],
            "scope_signals": [],
            "failure_signals": ["test-failure"],
            "expected": {"executing-plans", "systematic-debugging", "verification-before-completion"},
        },
    ]

    valid_skill_ids = {entry["id"] for entry in registry["entries"] if entry["kind"] == "skill"}
    for case in sample_cases:
        outputs = []
        for platform in ("claude", "codex", "antigravity"):
            payload = resolve_runtime_contract(
                root,
                classification=case["classification"],
                phase=case["phase"],
                platform=platform,
                manual_skills=case["manual_skills"],
                scope_signals=case["scope_signals"],
                failure_signals=case["failure_signals"],
            )
            if payload["blockers"]:
                errors.append(f"resolver blockers for {case['classification']}/{case['phase']}/{platform}: {payload['blockers']}")
                continue
            outputs.append(payload)

        if not outputs:
            continue

        first = outputs[0]
        for payload in outputs[1:]:
            if payload["resolved_workflow"] != first["resolved_workflow"]:
                errors.append(f"resolver workflow mismatch across platforms for {case['classification']}/{case['phase']}")
            if payload["activated_skills"] != first["activated_skills"]:
                errors.append(f"resolver activated skill mismatch across platforms for {case['classification']}/{case['phase']}")

        expected = case["expected"]
        activated = set(first["activated_skills"])
        missing = expected - activated
        unknown = activated - valid_skill_ids
        if missing:
            errors.append(f"resolver missing expected skills for {case['classification']}/{case['phase']}: {sorted(missing)}")
        if unknown:
            errors.append(f"resolver returned unknown skills for {case['classification']}/{case['phase']}: {sorted(unknown)}")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    registry_path = root / args.registry
    compact_index_path = root / args.compact_index
    scenario_path = root / args.scenarios
    errors: list[str] = []

    ensure(registry_path.is_file(), f"missing registry file: {registry_path}", errors)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    registry = load_registry(root, args.registry)
    entries = registry.get("entries", [])
    ensure(isinstance(entries, list) and entries, "registry entries must be a non-empty list", errors)
    for entry in entries:
        validate_entry(root, entry, errors)
    validate_scenario_file(scenario_path, registry, errors)
    validate_compact_index(root, compact_index_path, args.registry, errors)
    validate_resolver_parity(root, registry, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    scenarios = load_json(scenario_path)
    print(
        f"Trigger metadata validation passed for {len(entries)} entries, "
        f"{len(scenarios.get('scenarios', []))} lifecycle scenarios, and fresh compact index parity"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
