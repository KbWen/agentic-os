#!/usr/bin/env python3
"""Lifecycle tests: verify skills auto-trigger correctly per classification and phase.

Tests simulate the full lifecycle for each classification (tiny-fix, quick-win,
feature, hotfix, architecture-change) and assert that:
  1. The correct skills are recommended per the bootstrap §3.6 rule table.
  2. Phase-entry skill loading only loads skills relevant to that phase.
  3. Skills not in the rule table for a classification are NOT activated.
  4. Load policies (always, phase-entry, on-match, on-failure) are respected.
  5. triggered_skills are always a subset of candidate_skills.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

# --- Bootstrap §3.6 rule table encoded as test expectations ---

MANDATORY_SKILLS = {
    "writing-plans": {"phases": ["plan"], "skip": ["tiny-fix"]},
    "executing-plans": {"phases": ["implement"], "skip": []},
    "verification-before-completion": {"phases": ["implement", "test", "ship"], "skip": ["tiny-fix"]},
    "systematic-debugging": {"phases": ["implement", "review", "test", "hotfix"], "skip": []},
    "red-team-adversarial": {"phases": ["review", "test"], "skip": ["tiny-fix", "quick-win"]},
}

SCOPE_DETECTED_SKILLS = {
    "test-driven-development": {"phases": ["implement", "test"], "classifications": ["feature", "architecture-change"]},
    "api-design": {"phases": ["implement", "review", "test"], "classifications": ["feature", "architecture-change", "hotfix"]},
    "database-design": {"phases": ["implement", "review", "test"], "classifications": ["feature", "architecture-change", "hotfix"]},
    "frontend-patterns": {"phases": ["implement", "review", "test"], "classifications": ["feature", "architecture-change"]},
    "auth-security": {"phases": ["implement", "review", "test"], "classifications": ["feature", "architecture-change", "hotfix", "quick-win", "tiny-fix"]},
}

PHASE_TRIGGERED_SKILLS = {
    "finishing-a-development-branch": {"phases": ["ship", "handoff"]},
    "receiving-code-review": {"phases": ["review"]},
    "requesting-code-review": {"phases": ["review", "handoff"]},
}

COMPLEXITY_CONDITIONAL_SKILLS = {
    "dispatching-parallel-agents": {"phases": ["implement"], "classifications": ["feature", "architecture-change"]},
    "subagent-driven-development": {"phases": ["implement"], "classifications": ["feature", "architecture-change"]},
    "using-git-worktrees": {"phases": ["bootstrap", "implement"], "classifications": ["feature", "architecture-change"]},
}

CLASSIFICATION_PHASE_ORDER = {
    "feature": ["bootstrap", "plan", "implement", "review", "test", "handoff", "ship"],
    "architecture-change": ["bootstrap", "plan", "implement", "review", "test", "handoff", "ship"],
    "hotfix": ["bootstrap", "implement", "review", "test", "ship"],
    "quick-win": ["bootstrap", "plan", "implement", "test", "ship"],
    "tiny-fix": [],  # no formal phases
}

LOAD_POLICY_VALID = {"always", "phase-entry", "on-match", "on-failure"}

EXPECTED_SCENARIO_SKILLS = {
    "quick-win-single-module": {
        "candidate": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "systematic-debugging",
            "finishing-a-development-branch",
        },
        "triggered": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "finishing-a-development-branch",
        },
    },
    "feature-core-logic-tdd": {
        "candidate": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "test-driven-development",
            "systematic-debugging",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
        "triggered": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "test-driven-development",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
    },
    "feature-api-auth-db": {
        "candidate": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "test-driven-development",
            "api-design",
            "database-design",
            "auth-security",
            "doc-lookup",
            "systematic-debugging",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
        "triggered": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "test-driven-development",
            "api-design",
            "database-design",
            "auth-security",
            "doc-lookup",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
    },
    "hotfix-debug-loop": {
        "candidate": {
            "executing-plans",
            "verification-before-completion",
            "systematic-debugging",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
        "triggered": {
            "executing-plans",
            "verification-before-completion",
            "systematic-debugging",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
    },
    "architecture-multi-agent": {
        "candidate": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "api-design",
            "database-design",
            "frontend-patterns",
            "auth-security",
            "doc-lookup",
            "dispatching-parallel-agents",
            "subagent-driven-development",
            "using-git-worktrees",
            "systematic-debugging",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
        "triggered": {
            "writing-plans",
            "executing-plans",
            "verification-before-completion",
            "api-design",
            "database-design",
            "frontend-patterns",
            "auth-security",
            "doc-lookup",
            "dispatching-parallel-agents",
            "subagent-driven-development",
            "using-git-worktrees",
            "red-team-adversarial",
            "requesting-code-review",
            "finishing-a-development-branch",
        },
    },
    "post-review-feedback-loop": {
        "candidate": {
            "receiving-code-review",
            "requesting-code-review",
            "executing-plans",
            "verification-before-completion",
            "systematic-debugging",
            "red-team-adversarial",
            "finishing-a-development-branch",
        },
        "triggered": {
            "receiving-code-review",
            "requesting-code-review",
            "executing-plans",
            "verification-before-completion",
            "red-team-adversarial",
            "finishing-a-development-branch",
        },
    },
}

EXPECTED_SCENARIO_SIGNALS = {
    "quick-win-single-module": {
        "scope": [],
        "failure": [],
    },
    "feature-core-logic-tdd": {
        "scope": ["testable logic", "core logic"],
        "failure": [],
    },
    "feature-api-auth-db": {
        "scope": ["api endpoint", "migration", "login", "framework API", "auth", "core logic"],
        "failure": [],
    },
    "hotfix-debug-loop": {
        "scope": [],
        "failure": ["test-failure", "unexpected-behavior"],
    },
    "architecture-multi-agent": {
        "scope": [
            "api endpoint",
            "migration",
            "ui component",
            "login",
            "framework API",
            "dependency",
            "3+ independent subtasks",
            "4+ files",
            "parallel branch isolation",
        ],
        "failure": [],
    },
    "post-review-feedback-loop": {
        "scope": ["review comments"],
        "failure": [],
    },
}


def load_json(path: Path) -> dict[str, Any]:
    import sys

    sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
    from _yaml_loader import load_data

    return load_data(path)


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = [part.strip() for part in re.split(r",(?![^\[]*\])", inner)]
        return [parse_scalar(part) for part in parts]
    if value.isdigit():
        return int(value)
    return value


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data: dict[str, Any] = {}
    for raw_line in parts[1].splitlines():
        if not raw_line.strip():
            continue
        key, _, value = raw_line.partition(":")
        if not _:
            continue
        data[key.strip()] = parse_scalar(value)
    return data


def load_registry() -> dict[str, Any]:
    return load_json(ROOT / ".agentcortex/metadata/trigger-registry.yaml")


def load_scenarios() -> dict[str, Any]:
    return load_json(ROOT / ".agentcortex/metadata/lifecycle-scenarios.json")


def resolve_runtime_contract_for_scenario(
    scenario_id: str,
    scenario: dict[str, Any],
    registry_entries: dict[str, dict[str, Any]],
    *,
    platform: str = "codex",
) -> tuple[set[str], dict[str, set[str]]]:
    import sys

    sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
    from trigger_runtime_core import resolve_runtime_contract

    scenario_signals = EXPECTED_SCENARIO_SIGNALS[scenario_id]
    scope_signals = scenario_signals["scope"]
    failure_signals = scenario_signals["failure"]

    activated_union: set[str] = set()
    activated_by_phase: dict[str, set[str]] = {}
    for phase in dict.fromkeys(scenario["phases"]):
        result = resolve_runtime_contract(
            ROOT,
            classification=scenario["classification"],
            phase=phase,
            platform=platform,
            manual_skills=[],
            scope_signals=scope_signals,
            failure_signals=failure_signals,
        )
        phase_activated = set(result["activated_skills"])
        activated_union.update(phase_activated)
        activated_by_phase[phase] = phase_activated
    return activated_union, activated_by_phase


def load_skill_metadata() -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    skills_dir = ROOT / ".agent" / "skills"
    for skill_file in sorted(skills_dir.iterdir()):
        if skill_file.is_file() and not skill_file.name.startswith("."):
            meta = parse_frontmatter(skill_file)
            name = meta.get("name", skill_file.name)
            skills[name] = meta
    return skills


class TestSkillActivationPerClassification(unittest.TestCase):
    """Verify that the bootstrap §3.6 rule table produces correct skill recommendations."""

    def setUp(self) -> None:
        self.registry = load_registry()
        self.registry_entries = {e["id"]: e for e in self.registry["entries"]}
        self.scenarios = load_scenarios()
        self.skill_metadata = load_skill_metadata()

    def test_mandatory_skills_activate_for_feature(self) -> None:
        """Feature tasks must activate all mandatory skills (except those skipped or on-failure)."""
        # systematic-debugging is mandatory but load_policy=on-failure — it's a candidate
        # but only triggered when bugs actually occur. Check candidates instead.
        expected_triggered = {s for s, cfg in MANDATORY_SKILLS.items()
                             if "feature" not in cfg["skip"] and s != "systematic-debugging"}
        feature_scenario = next(s for s in self.scenarios["scenarios"] if s["id"] == "feature-core-logic-tdd")
        triggered = set(feature_scenario["triggered_skills"])
        candidates = set(feature_scenario["candidate_skills"])
        for skill in expected_triggered:
            self.assertIn(skill, triggered, f"mandatory skill {skill} missing from feature triggered_skills")
        # systematic-debugging should at least be a candidate
        self.assertIn("systematic-debugging", candidates,
                       "systematic-debugging should be a candidate in feature scenario")

    def test_mandatory_skills_activate_for_hotfix(self) -> None:
        """Hotfix tasks must activate systematic-debugging and other applicable mandatory skills."""
        # writing-plans requires a /plan phase; hotfix scenario skips plan → not triggered
        # Check that hotfix-specific mandatory skills are present
        hotfix_scenario = next(s for s in self.scenarios["scenarios"] if s["id"] == "hotfix-debug-loop")
        triggered = set(hotfix_scenario["triggered_skills"])
        candidates = set(hotfix_scenario["candidate_skills"])
        # systematic-debugging is THE hotfix mandatory skill
        self.assertIn("systematic-debugging", triggered)
        # verification-before-completion should be triggered (non-tiny-fix)
        self.assertIn("verification-before-completion", triggered)
        # executing-plans should be triggered (never skipped)
        self.assertIn("executing-plans", triggered)
        # writing-plans is only for /plan phase — hotfix scenario has no plan, so not expected
        if "plan" not in hotfix_scenario["phases"]:
            self.assertNotIn("writing-plans", triggered)

    def test_red_team_skipped_for_quick_win(self) -> None:
        """Quick-win must NOT activate red-team-adversarial (per skip rule)."""
        qw_scenario = next(s for s in self.scenarios["scenarios"] if s["id"] == "quick-win-single-module")
        triggered = set(qw_scenario["triggered_skills"])
        self.assertNotIn("red-team-adversarial", triggered)

    def test_quick_win_has_minimal_skill_set(self) -> None:
        """Quick-win should have fewer skills than feature scenarios."""
        qw = next(s for s in self.scenarios["scenarios"] if s["id"] == "quick-win-single-module")
        feature = next(s for s in self.scenarios["scenarios"] if s["id"] == "feature-core-logic-tdd")
        self.assertLess(
            len(qw["triggered_skills"]),
            len(feature["triggered_skills"]),
            "quick-win should have fewer triggered skills than feature",
        )

    def test_architecture_change_activates_complexity_skills(self) -> None:
        """Architecture-change should activate complexity-conditional skills."""
        arch = next(s for s in self.scenarios["scenarios"] if s["id"] == "architecture-multi-agent")
        triggered = set(arch["triggered_skills"])
        for skill in COMPLEXITY_CONDITIONAL_SKILLS:
            self.assertIn(skill, triggered, f"complexity skill {skill} missing from architecture scenario")

    def test_scope_detected_skills_in_api_auth_db_scenario(self) -> None:
        """Feature with API+auth+DB should activate all three scope-detected skills."""
        scenario = next(s for s in self.scenarios["scenarios"] if s["id"] == "feature-api-auth-db")
        triggered = set(scenario["triggered_skills"])
        for skill in ["api-design", "database-design", "auth-security"]:
            self.assertIn(skill, triggered, f"scope-detected skill {skill} missing from api-auth-db scenario")


class TestPhaseEntrySkillLoading(unittest.TestCase):
    """Verify that skills load at the correct phase, not too early."""

    def setUp(self) -> None:
        self.registry = load_registry()
        self.registry_entries = {e["id"]: e for e in self.registry["entries"]}
        self.skill_metadata = load_skill_metadata()

    def test_writing_plans_only_relevant_in_plan_phase(self) -> None:
        entry = self.registry_entries["writing-plans"]
        self.assertEqual(entry["phase_scope"], ["plan"])
        self.assertEqual(entry["load_policy"], "phase-entry")

    def test_executing_plans_only_relevant_in_implement_phase(self) -> None:
        entry = self.registry_entries["executing-plans"]
        self.assertEqual(entry["phase_scope"], ["implement"])
        self.assertEqual(entry["load_policy"], "phase-entry")

    def test_verification_loads_at_phase_entry(self) -> None:
        entry = self.registry_entries["verification-before-completion"]
        self.assertEqual(entry["load_policy"], "phase-entry")
        self.assertIn("implement", entry["phase_scope"])
        self.assertIn("test", entry["phase_scope"])
        self.assertIn("ship", entry["phase_scope"])

    def test_tdd_loads_on_match_not_always(self) -> None:
        """TDD is contextual — should only load when scope signals match, not always."""
        entry = self.registry_entries["test-driven-development"]
        self.assertEqual(entry["load_policy"], "on-match")
        self.assertEqual(entry["trigger_priority"], "contextual")

    def test_systematic_debugging_loads_on_failure(self) -> None:
        """Debugging should only load when failures are detected."""
        entry = self.registry_entries["systematic-debugging"]
        self.assertEqual(entry["load_policy"], "on-failure")

    def test_all_skill_load_policies_are_valid(self) -> None:
        for entry in self.registry["entries"]:
            if entry["kind"] == "skill":
                self.assertIn(
                    entry["load_policy"],
                    LOAD_POLICY_VALID,
                    f"{entry['id']}: invalid load_policy {entry['load_policy']}",
                )

    def test_phase_scope_matches_metadata(self) -> None:
        """Registry phase_scope must match the .agent/skills/ frontmatter phases."""
        for entry in self.registry["entries"]:
            if entry["kind"] != "skill":
                continue
            meta = self.skill_metadata.get(entry["id"])
            if meta is None:
                continue
            meta_phases = meta.get("phases", [])
            if isinstance(meta_phases, str):
                meta_phases = [meta_phases]
            self.assertEqual(
                entry["phase_scope"],
                meta_phases,
                f"{entry['id']}: registry phase_scope != metadata phases",
            )


class TestTriggeredSubsetOfCandidates(unittest.TestCase):
    """Verify scenario invariant: triggered_skills is always a subset of candidate_skills."""

    def setUp(self) -> None:
        self.scenarios = load_scenarios()

    def test_all_scenarios_triggered_subset(self) -> None:
        for scenario in self.scenarios["scenarios"]:
            triggered = set(scenario["triggered_skills"])
            candidates = set(scenario["candidate_skills"])
            extra = triggered - candidates
            self.assertFalse(
                extra,
                f"{scenario['id']}: triggered skills {extra} not in candidate_skills",
            )


class TestScenarioGoldenExpectations(unittest.TestCase):
    """Lock the lifecycle scenarios to explicit candidate/triggered skill sets."""

    def setUp(self) -> None:
        self.scenarios = {s["id"]: s for s in load_scenarios()["scenarios"]}

    def test_all_expected_scenarios_are_present(self) -> None:
        self.assertEqual(set(self.scenarios), set(EXPECTED_SCENARIO_SKILLS))

    def test_candidate_skill_sets_match_goldens(self) -> None:
        for scenario_id, expected in EXPECTED_SCENARIO_SKILLS.items():
            actual = set(self.scenarios[scenario_id]["candidate_skills"])
            self.assertEqual(
                actual,
                expected["candidate"],
                f"{scenario_id}: candidate_skills drifted from the expected lifecycle contract",
            )

    def test_triggered_skill_sets_match_goldens(self) -> None:
        for scenario_id, expected in EXPECTED_SCENARIO_SKILLS.items():
            actual = set(self.scenarios[scenario_id]["triggered_skills"])
            self.assertEqual(
                actual,
                expected["triggered"],
                f"{scenario_id}: triggered_skills drifted from the expected lifecycle contract",
            )


class TestRuntimeResolutionAgainstScenarioContracts(unittest.TestCase):
    """Resolve runtime activation phase-by-phase and compare it with scenario contracts."""

    def setUp(self) -> None:
        self.registry = load_registry()
        self.registry_entries = {e["id"]: e for e in self.registry["entries"]}
        self.scenarios = {s["id"]: s for s in load_scenarios()["scenarios"]}

    def test_runtime_resolution_matches_triggered_skills_for_all_scenarios(self) -> None:
        for scenario_id, scenario in self.scenarios.items():
            activated, _ = resolve_runtime_contract_for_scenario(scenario_id, scenario, self.registry_entries)
            self.assertEqual(
                activated,
                set(scenario["triggered_skills"]),
                f"{scenario_id}: runtime activation drifted from scenario triggered_skills",
            )

    def test_runtime_resolution_never_activates_non_candidates(self) -> None:
        for scenario_id, scenario in self.scenarios.items():
            _, activated_by_phase = resolve_runtime_contract_for_scenario(scenario_id, scenario, self.registry_entries)
            candidates = set(scenario["candidate_skills"])
            for phase, activated in activated_by_phase.items():
                self.assertTrue(
                    activated.issubset(candidates),
                    f"{scenario_id}/{phase}: activated skills {activated - candidates} exceed candidate_skills",
                )

    def test_each_triggered_skill_activates_in_a_declared_phase(self) -> None:
        for scenario_id, scenario in self.scenarios.items():
            _, activated_by_phase = resolve_runtime_contract_for_scenario(scenario_id, scenario, self.registry_entries)
            for skill_id in scenario["triggered_skills"]:
                phases = [
                    phase for phase, activated in activated_by_phase.items()
                    if skill_id in activated
                ]
                self.assertTrue(
                    phases,
                    f"{scenario_id}: triggered skill {skill_id} never activated in any runtime phase",
                )


class TestClassificationPhaseOrder(unittest.TestCase):
    """Verify scenarios follow the correct phase order per classification."""

    def setUp(self) -> None:
        self.scenarios = load_scenarios()

    def _unique_ordered_phases(self, phases: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for p in phases:
            if p not in seen:
                seen.add(p)
                result.append(p)
        return result

    def test_feature_scenarios_follow_phase_order(self) -> None:
        """Feature scenarios starting from bootstrap must follow the canonical phase order.
        Mid-lifecycle scenarios (e.g. post-review-feedback-loop) may start at a later phase
        and loop back — these are exempt from strict ordering since they model re-entry."""
        expected = CLASSIFICATION_PHASE_ORDER["feature"]
        for scenario in self.scenarios["scenarios"]:
            if scenario["classification"] != "feature":
                continue
            # Skip mid-lifecycle scenarios that don't start from bootstrap
            if scenario["phases"][0] != "bootstrap":
                continue
            unique = self._unique_ordered_phases(scenario["phases"])
            for i, phase in enumerate(unique):
                if phase in expected:
                    idx = expected.index(phase)
                    for prev_phase in unique[:i]:
                        if prev_phase in expected:
                            self.assertLess(
                                expected.index(prev_phase),
                                idx,
                                f"{scenario['id']}: phase {prev_phase} should come before {phase}",
                            )

    def test_hotfix_scenario_follows_phase_order(self) -> None:
        expected = CLASSIFICATION_PHASE_ORDER["hotfix"]
        for scenario in self.scenarios["scenarios"]:
            if scenario["classification"] != "hotfix":
                continue
            unique = self._unique_ordered_phases(scenario["phases"])
            for phase in unique:
                self.assertIn(
                    phase,
                    expected,
                    f"{scenario['id']}: hotfix has unexpected phase {phase}",
                )

    def test_quick_win_scenario_has_no_handoff(self) -> None:
        for scenario in self.scenarios["scenarios"]:
            if scenario["classification"] != "quick-win":
                continue
            self.assertNotIn(
                "handoff",
                scenario["phases"],
                f"{scenario['id']}: quick-win must not include handoff phase",
            )

    def test_quick_win_scenario_has_no_spec_phase(self) -> None:
        for scenario in self.scenarios["scenarios"]:
            if scenario["classification"] != "quick-win":
                continue
            self.assertNotIn(
                "spec",
                scenario["phases"],
                f"{scenario['id']}: quick-win must not include spec phase",
            )


class TestLoadPolicyTokenImpact(unittest.TestCase):
    """Verify load policies are correctly assigned to minimize token consumption."""

    def setUp(self) -> None:
        self.registry = load_registry()
        self.entries = {e["id"]: e for e in self.registry["entries"]}

    def test_hard_triggers_never_use_on_failure(self) -> None:
        """Hard-priority triggers must always be available — on-failure is too late."""
        for entry in self.registry["entries"]:
            if entry["trigger_priority"] == "hard":
                self.assertNotEqual(
                    entry["load_policy"],
                    "on-failure",
                    f"{entry['id']}: hard trigger must not use on-failure load policy",
                )

    def test_advisory_triggers_never_use_always(self) -> None:
        """Advisory-priority triggers should not waste tokens with 'always' load."""
        for entry in self.registry["entries"]:
            if entry["trigger_priority"] == "advisory" and entry["kind"] == "skill":
                self.assertNotEqual(
                    entry["load_policy"],
                    "always",
                    f"{entry['id']}: advisory skill should not use 'always' load policy",
                )

    def test_high_cost_skills_use_deferred_loading(self) -> None:
        """Skills marked high cost_risk should use on-match or on-failure, not always."""
        for entry in self.registry["entries"]:
            if entry["kind"] == "skill" and entry["cost_risk"] == "high":
                self.assertIn(
                    entry["load_policy"],
                    {"on-match", "on-failure", "phase-entry"},
                    f"{entry['id']}: high-cost skill should use deferred loading",
                )

    def test_low_cost_skills_can_use_phase_entry(self) -> None:
        """Low cost_risk skills can safely use phase-entry without concern."""
        for entry in self.registry["entries"]:
            if entry["kind"] == "skill" and entry["cost_risk"] == "low":
                self.assertIn(
                    entry["load_policy"],
                    {"phase-entry", "on-match", "always"},
                    f"{entry['id']}: low-cost skill has unexpected load policy",
                )


class TestWorkflowPhaseHooks(unittest.TestCase):
    """Verify that workflow files contain the skill loading hooks."""

    def setUp(self) -> None:
        self.workflow_dir = ROOT / ".agent" / "workflows"

    def _read_workflow(self, name: str) -> str:
        path = self.workflow_dir / f"{name}.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def test_implement_has_skill_overrides_section(self) -> None:
        text = self._read_workflow("implement")
        self.assertIn("Skill Execution Overrides", text)
        # Skill Notes cache contract is canonical in AGENTS.md §Shared Phase Contracts
        self.assertIn("AGENTS.md", text)

    def test_test_has_skill_aware_section(self) -> None:
        text = self._read_workflow("test")
        self.assertIn("Skill-Aware", text)
        # Skill Notes cache contract is canonical in AGENTS.md §Shared Phase Contracts
        self.assertIn("AGENTS.md", text)

    def test_ship_has_skill_aware_checks(self) -> None:
        text = self._read_workflow("ship")
        self.assertIn("Skill-Aware", text)

    def test_implement_mentions_tdd(self) -> None:
        text = self._read_workflow("implement")
        self.assertIn("test-driven-development", text)

    def test_implement_mentions_auth_security(self) -> None:
        text = self._read_workflow("implement")
        self.assertIn("auth-security", text)

    def test_implement_mentions_systematic_debugging(self) -> None:
        text = self._read_workflow("implement")
        self.assertIn("systematic-debugging", text)

    def test_test_mentions_auth_mandatory_cases(self) -> None:
        text = self._read_workflow("test")
        self.assertIn("auth-security", text)

    def test_ship_mentions_verification_before_completion(self) -> None:
        text = self._read_workflow("ship")
        self.assertIn("verification-before-completion", text)

    def test_ship_mentions_finishing_branch(self) -> None:
        text = self._read_workflow("ship")
        self.assertIn("finishing-a-development-branch", text)

    def test_review_mentions_red_team(self) -> None:
        text = self._read_workflow("review")
        self.assertIn("red-team", text.lower())
        # Skill Notes cache contract is canonical in AGENTS.md §Shared Phase Contracts
        self.assertIn("AGENTS.md", text)

    def test_plan_mentions_writing_plans(self) -> None:
        text = self._read_workflow("plan")
        self.assertIn("writing-plans", text)
        # Skill Notes cache contract is canonical in AGENTS.md §Shared Phase Contracts
        self.assertIn("AGENTS.md", text)

    def test_handoff_mentions_requesting_code_review(self) -> None:
        text = self._read_workflow("handoff")
        self.assertIn("requesting-code-review", text)
        # Skill Notes cache contract is canonical in AGENTS.md §Shared Phase Contracts
        self.assertIn("AGENTS.md", text)

    def test_handoff_mentions_finishing_branch(self) -> None:
        text = self._read_workflow("handoff")
        self.assertIn("finishing-a-development-branch", text)

    def test_ship_mentions_skill_notes_cache(self) -> None:
        # Skill Notes cache contract is canonical in AGENTS.md §Shared Phase Contracts
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Skill Notes", agents_text)
        # Ship workflow references AGENTS.md for the shared contract
        ship_text = self._read_workflow("ship")
        self.assertIn("AGENTS.md", ship_text)


class TestSharedPhaseContracts(unittest.TestCase):
    """Verify that AGENTS.md contains both shared phase contracts and that
    workflows reference AGENTS.md instead of repeating the prose."""

    def setUp(self) -> None:
        self.agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.workflow_dir = ROOT / ".agent" / "workflows"

    def _read_workflow(self, name: str) -> str:
        path = self.workflow_dir / f"{name}.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def test_agents_md_has_shared_phase_contracts_section(self) -> None:
        self.assertIn("## Shared Phase Contracts", self.agents_text)

    def test_agents_md_has_phase_entry_skill_loading_contract(self) -> None:
        self.assertIn("### Phase-Entry Skill Loading", self.agents_text)
        self.assertIn("Skill Notes", self.agents_text)
        self.assertIn("config.yaml", self.agents_text)

    def test_agents_md_has_verification_before_completion_gates(self) -> None:
        self.assertIn("### Verification Before Completion (5-Gate Sequence)", self.agents_text)
        # The 5 gate labels must be present
        for label in ("Scope", "Quality", "Evidence", "Risk", "Communication"):
            self.assertIn(label, self.agents_text, f"5-gate sequence missing gate: {label}")

    def test_all_six_workflows_reference_agents_md(self) -> None:
        """After dedup, all phase workflows must reference AGENTS.md."""
        for phase in ("plan", "implement", "review", "test", "handoff", "ship"):
            text = self._read_workflow(phase)
            self.assertIn(
                "AGENTS.md", text,
                f"{phase}.md should reference AGENTS.md shared contracts",
            )

    def test_shared_contract_replaces_duplicate_workflow_prose(self) -> None:
        """Workflows must not repeat the full skill-loading numbered-list prose."""
        full_prose_marker = "Read `## Skill Notes` first for the current phase."
        prose_count = 0
        for phase in ("plan", "implement", "review", "test", "handoff", "ship"):
            text = self._read_workflow(phase)
            if full_prose_marker in text:
                prose_count += 1
        self.assertEqual(
            prose_count, 0,
            f"Found {prose_count} workflow file(s) repeating the full skill-loading prose — "
            "should be 0 after dedup into AGENTS.md §Shared Phase Contracts",
        )

    def test_verification_5gate_not_duplicated_in_workflows(self) -> None:
        """The 5-gate sequence must not be copy-pasted into implement/test/ship workflows."""
        five_gate_marker = "Scope Gate"  # phrasing used in the old per-workflow copy
        for phase in ("implement", "test", "ship"):
            text = self._read_workflow(phase)
            self.assertNotIn(
                five_gate_marker, text,
                f"{phase}.md should not contain the full 5-gate prose — "
                "reference AGENTS.md §Shared Phase Contracts instead",
            )


class TestConditionalLoadingRules(unittest.TestCase):
    """Verify CLAUDE.md conditional loading strategy is correctly defined."""

    def setUp(self) -> None:
        self.claude_md = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    def test_tiny_fix_skips_ssot(self) -> None:
        self.assertIn("tiny-fix", self.claude_md)
        self.assertIn("skip", self.claude_md.lower())

    def test_quick_win_skips_guardrails(self) -> None:
        self.assertIn("quick-win", self.claude_md)
        self.assertIn("skip Step 4", self.claude_md)

    def test_conditional_loading_explanation_present(self) -> None:
        self.assertIn("conditional loading", self.claude_md.lower())

    def test_token_savings_documented(self) -> None:
        self.assertIn("5,000 tokens", self.claude_md)
        self.assertIn("3,500 tokens", self.claude_md)


class TestAllSkillsCoveredInRegistry(unittest.TestCase):
    """Verify every skill in .agent/skills/ has a matching registry entry."""

    def setUp(self) -> None:
        self.registry = load_registry()
        self.registry_skill_ids = {e["id"] for e in self.registry["entries"] if e["kind"] == "skill"}
        self.skill_metadata = load_skill_metadata()

    def test_every_metadata_skill_has_registry_entry(self) -> None:
        for skill_name in self.skill_metadata:
            self.assertIn(
                skill_name,
                self.registry_skill_ids,
                f"skill {skill_name} in .agent/skills/ has no registry entry",
            )

    def test_every_registry_skill_has_metadata_file(self) -> None:
        for skill_id in self.registry_skill_ids:
            self.assertIn(
                skill_id,
                self.skill_metadata,
                f"registry skill {skill_id} has no .agent/skills/ metadata file",
            )

    def test_skill_count_matches(self) -> None:
        self.assertEqual(
            len(self.registry_skill_ids),
            len(self.skill_metadata),
            "registry skill count != metadata skill count",
        )


class TestManualSkipEnforcement(unittest.TestCase):
    """Manual skill activation MUST respect classification skip rules."""

    def _resolve(self, classification: str, phase: str, manual: list[str]) -> list[str]:
        import sys
        sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
        from trigger_runtime_core import resolve_runtime_contract

        result = resolve_runtime_contract(
            ROOT, classification=classification, phase=phase,
            platform="claude", manual_skills=manual,
            scope_signals=[], failure_signals=[],
        )
        return result["activated_skills"]

    def test_red_team_blocked_for_quick_win_even_when_manual(self) -> None:
        activated = self._resolve("quick-win", "review", ["red team"])
        self.assertNotIn("red-team-adversarial", activated)

    def test_red_team_blocked_for_tiny_fix_even_when_manual(self) -> None:
        activated = self._resolve("tiny-fix", "review", ["red team"])
        self.assertNotIn("red-team-adversarial", activated)

    def test_tdd_blocked_for_quick_win_even_when_manual(self) -> None:
        activated = self._resolve("quick-win", "implement", ["用 TDD"])
        self.assertNotIn("test-driven-development", activated)

    def test_tdd_allowed_for_feature_when_manual(self) -> None:
        activated = self._resolve("feature", "implement", ["用 TDD"])
        self.assertIn("test-driven-development", activated)


if __name__ == "__main__":
    unittest.main()
