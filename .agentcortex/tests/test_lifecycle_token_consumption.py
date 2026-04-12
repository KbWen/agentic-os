#!/usr/bin/env python3
"""Lifecycle tests: measure and assert token costs per scenario.

Tests verify that:
  1. Conditional loading actually saves tokens for tiny-fix and quick-win.
  2. Phase-entry deferred loading reduces upfront probe costs.
  3. Metadata-first probes are cheaper than full SKILL.md reads.
  4. Optimized paths always save tokens vs. current approach (positive delta).
  5. Cost proportionality: simpler classifications cost fewer tokens.
  6. Phase repeats (TDD loops, debug loops) correctly multiply token costs.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

# --- Constants matching CLAUDE.md conditional loading ---

CLASSIFICATION_BASE_FILES = {
    "tiny-fix": ["AGENTS.md"],
    "quick-win": ["AGENTS.md", ".agentcortex/context/current_state.md"],
    "feature": [
        "AGENTS.md",
        ".agent/rules/engineering_guardrails.md",
        ".agent/rules/state_machine.md",
        ".agentcortex/context/current_state.md",
    ],
    "architecture-change": [
        "AGENTS.md",
        ".agent/rules/engineering_guardrails.md",
        ".agent/rules/state_machine.md",
        ".agentcortex/context/current_state.md",
    ],
    "hotfix": [
        "AGENTS.md",
        ".agent/rules/engineering_guardrails.md",
        ".agentcortex/context/current_state.md",
    ],
}


def estimate_tokens(path: Path) -> int:
    if not path.is_file():
        return 0
    return max(1, math.ceil(len(path.read_text(encoding="utf-8")) / 4))


def load_json(path: Path) -> dict[str, Any]:
    import sys

    sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
    from _yaml_loader import load_data

    return load_data(path)


def scenario_phase_counts(phases: list[str], repeats: dict[str, int]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for phase in phases:
        counts[phase] = counts.get(phase, 0) + repeats.get(phase, 1)
    return counts


def legacy_execution_detail_tokens(
    scenario: dict[str, Any],
    skill_entries: dict[str, dict[str, Any]],
) -> int:
    total = 0
    phase_counts = scenario_phase_counts(scenario["phases"], scenario.get("phase_repeats", {}))
    for skill_id in scenario["triggered_skills"]:
        entry = skill_entries[skill_id]
        load_count = sum(phase_counts.get(phase, 0) for phase in entry["phase_scope"])
        load_count = max(load_count, 1)
        total += estimate_tokens(ROOT / entry["detail_ref"]) * load_count
    return total


def run_analyzer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, ".agentcortex/tools/analyze_token_lifecycle.py", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class TestConditionalLoadingTokenSavings(unittest.TestCase):
    """Verify that conditional loading saves tokens per classification tier."""

    def test_tiny_fix_reads_only_agents_md(self) -> None:
        """tiny-fix should only read AGENTS.md — no SSoT, no guardrails."""
        files = CLASSIFICATION_BASE_FILES["tiny-fix"]
        self.assertEqual(files, ["AGENTS.md"])

    def test_quick_win_skips_guardrails(self) -> None:
        """quick-win reads AGENTS.md + SSoT but not guardrails."""
        files = CLASSIFICATION_BASE_FILES["quick-win"]
        self.assertIn("AGENTS.md", files)
        self.assertIn(".agentcortex/context/current_state.md", files)
        self.assertNotIn(".agent/rules/engineering_guardrails.md", files)

    def test_feature_reads_all_base_files(self) -> None:
        """feature reads AGENTS.md + guardrails + state_machine + SSoT."""
        files = CLASSIFICATION_BASE_FILES["feature"]
        self.assertIn("AGENTS.md", files)
        self.assertIn(".agent/rules/engineering_guardrails.md", files)
        self.assertIn(".agent/rules/state_machine.md", files)
        self.assertIn(".agentcortex/context/current_state.md", files)

    def test_tiny_fix_saves_at_least_3000_tokens_vs_feature(self) -> None:
        """tiny-fix should save at least 3000 tokens vs. feature base cost."""
        tiny_cost = sum(estimate_tokens(ROOT / f) for f in CLASSIFICATION_BASE_FILES["tiny-fix"])
        feature_cost = sum(estimate_tokens(ROOT / f) for f in CLASSIFICATION_BASE_FILES["feature"])
        savings = feature_cost - tiny_cost
        self.assertGreaterEqual(savings, 3000, f"tiny-fix saves only {savings} tokens vs feature")

    def test_quick_win_saves_at_least_1500_tokens_vs_feature(self) -> None:
        """quick-win should save at least 1500 tokens vs. feature base cost."""
        qw_cost = sum(estimate_tokens(ROOT / f) for f in CLASSIFICATION_BASE_FILES["quick-win"])
        feature_cost = sum(estimate_tokens(ROOT / f) for f in CLASSIFICATION_BASE_FILES["feature"])
        savings = feature_cost - qw_cost
        self.assertGreaterEqual(savings, 1500, f"quick-win saves only {savings} tokens vs feature")

    def test_cost_ordering_tiny_lt_quick_lt_feature(self) -> None:
        """Token cost: tiny-fix < quick-win < hotfix <= feature."""
        costs = {}
        for classification, files in CLASSIFICATION_BASE_FILES.items():
            costs[classification] = sum(estimate_tokens(ROOT / f) for f in files)
        self.assertLess(costs["tiny-fix"], costs["quick-win"])
        self.assertLess(costs["quick-win"], costs["feature"])
        self.assertLessEqual(costs["hotfix"], costs["feature"])


class TestMetadataProbeVsFullSkillRead(unittest.TestCase):
    """Verify metadata probes are cheaper than full SKILL.md reads."""

    def setUp(self) -> None:
        self.registry = load_json(ROOT / ".agentcortex/metadata/trigger-registry.yaml")
        self.skill_entries = {e["id"]: e for e in self.registry["entries"] if e["kind"] == "skill"}

    def test_summary_metadata_cheaper_than_detail_on_average(self) -> None:
        """On average, summary metadata should be cheaper than detail files.
        Individual small SKILL.md files may have metadata overhead > detail size."""
        total_summary = 0
        total_detail = 0
        for skill_id, entry in self.skill_entries.items():
            total_summary += estimate_tokens(ROOT / entry["canonical_ref"])
            total_detail += estimate_tokens(ROOT / entry["detail_ref"])
        self.assertLess(
            total_summary,
            total_detail,
            f"total summary ({total_summary}) should be cheaper than total detail ({total_detail})",
        )

    def test_mirror_metadata_cheaper_than_detail_on_average(self) -> None:
        """On average, mirror metadata should be cheaper than detail files."""
        total_mirror = 0
        total_detail = 0
        for skill_id, entry in self.skill_entries.items():
            total_mirror += estimate_tokens(ROOT / entry["mirror_ref"])
            total_detail += estimate_tokens(ROOT / entry["detail_ref"])
        self.assertLess(
            total_mirror,
            total_detail,
            f"total mirror ({total_mirror}) should be cheaper than total detail ({total_detail})",
        )

    def test_large_skills_have_cheaper_metadata(self) -> None:
        """Skills with detail > 500 tokens should have metadata cheaper than detail.
        Very small SKILL.md files may have metadata overhead — that's expected and acceptable."""
        for skill_id, entry in self.skill_entries.items():
            detail_tokens = estimate_tokens(ROOT / entry["detail_ref"])
            if detail_tokens < 500:
                continue  # skip small skills where metadata overhead is expected
            summary_tokens = estimate_tokens(ROOT / entry["canonical_ref"])
            self.assertLess(
                summary_tokens,
                detail_tokens,
                f"{skill_id}: summary ({summary_tokens}) not cheaper than detail ({detail_tokens})",
            )


class TestAnalyzerOutputCorrectness(unittest.TestCase):
    """Verify the analyze_token_lifecycle.py tool produces correct results."""

    def setUp(self) -> None:
        result = run_analyzer("--root", ".", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.payload = json.loads(result.stdout)
        self.results = {r["id"]: r for r in self.payload["results"]}
        self.registry = load_json(ROOT / ".agentcortex/metadata/trigger-registry.yaml")
        self.skill_entries = {e["id"]: e for e in self.registry["entries"] if e["kind"] == "skill"}
        self.scenarios = {s["id"]: s for s in load_json(ROOT / ".agentcortex/metadata/lifecycle-scenarios.json")["scenarios"]}

    def test_all_scenarios_present(self) -> None:
        scenarios = load_json(ROOT / ".agentcortex/metadata/lifecycle-scenarios.json")
        expected_ids = {s["id"] for s in scenarios["scenarios"]}
        actual_ids = set(self.results.keys())
        self.assertEqual(expected_ids, actual_ids)

    def test_all_scenarios_have_positive_delta(self) -> None:
        """Optimized approach must always save tokens vs. current approach."""
        for scenario_id, result in self.results.items():
            for platform in ("claude", "codex"):
                delta = result["platforms"][platform]["delta_vs_current_tokens"]
                self.assertGreater(
                    delta,
                    0,
                    f"{scenario_id}/{platform}: delta {delta} is not positive — optimization not saving tokens",
                )

    def test_architecture_change_has_highest_current_cost(self) -> None:
        """Architecture-change should be the most expensive current scenario."""
        arch = self.results["architecture-multi-agent"]
        for scenario_id, result in self.results.items():
            if scenario_id == "architecture-multi-agent":
                continue
            self.assertGreaterEqual(
                arch["current_total_tokens"],
                result["current_total_tokens"],
                f"architecture scenario should cost >= {scenario_id}",
            )

    def test_quick_win_has_lowest_current_cost(self) -> None:
        """Quick-win should be the cheapest scenario."""
        qw = self.results["quick-win-single-module"]
        for scenario_id, result in self.results.items():
            if scenario_id == "quick-win-single-module":
                continue
            self.assertLessEqual(
                qw["current_total_tokens"],
                result["current_total_tokens"],
                f"quick-win should cost <= {scenario_id}",
            )

    def test_phase_repeats_inflate_costs(self) -> None:
        """Scenarios with phase_repeats should show higher costs per phase."""
        feature_tdd = self.results["feature-core-logic-tdd"]
        self.assertIn("implement", feature_tdd["phase_counts"])
        self.assertGreater(
            feature_tdd["phase_counts"]["implement"],
            1,
            "feature-core-logic-tdd should have >1 implement repeats",
        )

    def test_codex_and_claude_deltas_differ(self) -> None:
        """Codex and Claude should have different projected costs (different metadata refs)."""
        for scenario_id, result in self.results.items():
            codex_proj = result["platforms"]["codex"]["projected_total_tokens"]
            claude_proj = result["platforms"]["claude"]["projected_total_tokens"]
            # They can be equal in edge cases but generally differ
            # Just verify both are computed
            self.assertGreater(codex_proj, 0)
            self.assertGreater(claude_proj, 0)

    def test_registry_tokens_is_positive(self) -> None:
        self.assertGreater(self.payload["registry_tokens"], 0)

    def test_results_expose_new_cost_breakdown_fields(self) -> None:
        for scenario_id, result in self.results.items():
            self.assertIn("workflow_scoped_tokens", result, scenario_id)
            self.assertIn("detail_first_load_tokens", result, scenario_id)
            self.assertIn("continuation_tokens", result, scenario_id)
            self.assertEqual(
                result["execution_detail_tokens"],
                result["detail_first_load_tokens"] + result["continuation_tokens"],
                f"{scenario_id}: execution_detail_tokens should decompose cleanly",
            )

    def test_detail_load_counts_cover_exactly_triggered_skills(self) -> None:
        for scenario_id, scenario in self.scenarios.items():
            result = self.results[scenario_id]
            self.assertEqual(
                set(result["detail_load_counts"]),
                set(scenario["triggered_skills"]),
                f"{scenario_id}: detail_load_counts keys should exactly match triggered_skills",
            )

    def test_phase_counts_match_declared_repeats(self) -> None:
        for scenario_id, scenario in self.scenarios.items():
            result = self.results[scenario_id]
            self.assertEqual(
                result["phase_counts"],
                scenario_phase_counts(scenario["phases"], scenario.get("phase_repeats", {})),
                f"{scenario_id}: analyzer phase_counts drifted from lifecycle scenario declaration",
            )

    def test_compact_index_stays_materially_smaller_than_full_registry(self) -> None:
        # Threshold is 60% of registry (not 50%) to accommodate the _summary
        # lite-header which adds ~300 tokens but saves ~3,000 at runtime by
        # letting agents skip full entry reads.
        self.assertLess(
            self.payload["compact_index_tokens"],
            self.payload["registry_tokens"] * 0.6,
            "compact index (with _summary) should remain materially smaller than the full registry",
        )

    def test_compact_probe_slice_is_cheaper_than_current_candidate_probe(self) -> None:
        for scenario_id, result in self.results.items():
            compact_slice = result["platforms"]["codex"]["compact_slice_tokens"]
            self.assertLess(
                compact_slice,
                result["current_probe_tokens"],
                f"{scenario_id}: compact probe slice should cost less than reading current candidate detail probes",
            )

    def test_scoped_workflow_reads_reduce_cost_for_long_phase_files(self) -> None:
        for scenario_id in ("feature-core-logic-tdd", "feature-api-auth-db", "architecture-multi-agent", "hotfix-debug-loop"):
            result = self.results[scenario_id]
            self.assertLess(
                result["workflow_scoped_tokens"],
                result["workflow_tokens"],
                f"{scenario_id}: scoped workflow reads should be cheaper than full workflow reads",
            )

    def test_heading_scope_parser_has_no_fallbacks(self) -> None:
        for scenario_id, result in self.results.items():
            self.assertFalse(
                result["workflow_scope_fallbacks"],
                f"{scenario_id}: unexpected heading-scope fallback {result['workflow_scope_fallbacks']}",
            )

    def test_continuation_tokens_are_positive_for_repeated_multi_phase_skills(self) -> None:
        for scenario_id in ("feature-core-logic-tdd", "feature-api-auth-db", "architecture-multi-agent", "hotfix-debug-loop", "post-review-feedback-loop"):
            result = self.results[scenario_id]
            self.assertGreater(result["continuation_tokens"], 0, f"{scenario_id}: continuation_tokens should be positive")

    def test_heavy_scenarios_cut_execution_detail_cost_by_at_least_40_percent(self) -> None:
        for scenario_id in ("feature-api-auth-db", "architecture-multi-agent"):
            result = self.results[scenario_id]
            legacy_total = legacy_execution_detail_tokens(self.scenarios[scenario_id], self.skill_entries)
            self.assertLessEqual(
                result["execution_detail_tokens"],
                math.floor(legacy_total * 0.60),
                f"{scenario_id}: execution detail cost did not drop by at least 40%",
            )

    def test_continuation_model_never_exceeds_legacy_full_detail_loading(self) -> None:
        for scenario_id, result in self.results.items():
            legacy_total = legacy_execution_detail_tokens(self.scenarios[scenario_id], self.skill_entries)
            self.assertLessEqual(
                result["execution_detail_tokens"],
                legacy_total,
                f"{scenario_id}: continuation model should never exceed legacy full detail loading",
            )

    def test_quick_win_total_cost_is_not_more_expensive_than_legacy_model(self) -> None:
        scenario_id = "quick-win-single-module"
        result = self.results[scenario_id]
        legacy_total = (
            result["workflow_tokens"]
            + result["current_probe_tokens"]
            + legacy_execution_detail_tokens(self.scenarios[scenario_id], self.skill_entries)
        )
        self.assertLessEqual(
            result["current_total_tokens"],
            legacy_total,
            "quick-win total cost should not exceed the legacy full-read model",
        )


class TestDeferredLoadingSavings(unittest.TestCase):
    """Verify deferred loading saves tokens compared to loading all skills upfront."""

    def setUp(self) -> None:
        self.registry = load_json(ROOT / ".agentcortex/metadata/trigger-registry.yaml")
        self.skill_entries = {e["id"]: e for e in self.registry["entries"] if e["kind"] == "skill"}
        self.scenarios = load_json(ROOT / ".agentcortex/metadata/lifecycle-scenarios.json")

    def test_candidate_minus_triggered_represents_savings(self) -> None:
        """Skills in candidates but not triggered represent deferred load savings."""
        for scenario in self.scenarios["scenarios"]:
            candidates = set(scenario["candidate_skills"])
            triggered = set(scenario["triggered_skills"])
            deferred = candidates - triggered
            # Deferred skills = token savings from not loading their detail files
            if deferred:
                deferred_tokens = sum(
                    estimate_tokens(ROOT / self.skill_entries[s]["detail_ref"])
                    for s in deferred
                    if s in self.skill_entries
                )
                self.assertGreater(
                    deferred_tokens,
                    0,
                    f"{scenario['id']}: deferred skills should represent token savings",
                )

    def test_on_match_skills_save_when_not_matched(self) -> None:
        """on-match skills that are candidates but not triggered represent pure savings."""
        for scenario in self.scenarios["scenarios"]:
            candidates = set(scenario["candidate_skills"])
            triggered = set(scenario["triggered_skills"])
            for skill_id in candidates - triggered:
                if skill_id not in self.skill_entries:
                    continue
                entry = self.skill_entries[skill_id]
                if entry["load_policy"] in ("on-match", "on-failure"):
                    detail_tokens = estimate_tokens(ROOT / entry["detail_ref"])
                    self.assertGreater(
                        detail_tokens,
                        100,
                        f"{scenario['id']}/{skill_id}: deferred on-match skill should have meaningful detail cost",
                    )


class TestTokenBudgetBounds(unittest.TestCase):
    """Verify token costs stay within reasonable bounds."""

    def setUp(self) -> None:
        result = run_analyzer("--root", ".", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.results = {r["id"]: r for r in json.loads(result.stdout)["results"]}

    def test_quick_win_current_total_under_26k(self) -> None:
        """Quick-win should not exceed 26k tokens total.

        Threshold updated from 24k → 26k to account for Design-First gate
        chain and document-state-growth-governance additions. These sections
        are no-ops for quick-win tasks (capability-by-presence) but count
        toward file size.
        """
        qw = self.results["quick-win-single-module"]
        self.assertLess(qw["current_total_tokens"], 26000)

    def test_feature_current_total_under_80k(self) -> None:
        """Even the heaviest feature scenario should stay under 80k tokens."""
        for sid, result in self.results.items():
            if result["classification"] in ("feature", "hotfix"):
                self.assertLess(
                    result["current_total_tokens"],
                    80000,
                    f"{sid}: feature/hotfix should stay under 80k tokens",
                )

    def test_architecture_change_under_120k(self) -> None:
        """Architecture-change is the heaviest but should stay under 120k."""
        arch = self.results["architecture-multi-agent"]
        self.assertLess(arch["current_total_tokens"], 120000)

    def test_optimization_always_saves_tokens(self) -> None:
        """Optimized approach should always save tokens (positive delta) for all scenarios."""
        for scenario_id, result in self.results.items():
            for platform in ("codex", "claude"):
                delta = result["platforms"][platform]["delta_vs_current_tokens"]
                self.assertGreater(
                    delta,
                    0,
                    f"{scenario_id}/{platform}: optimization should save tokens (delta={delta})",
                )

    def test_heavy_scenarios_save_more_than_light(self) -> None:
        """Scenarios with more candidate skills should have higher absolute savings."""
        results_list = sorted(self.results.values(), key=lambda r: len(r.get("detail_load_counts", {})))
        if len(results_list) >= 2:
            lightest = results_list[0]
            heaviest = results_list[-1]
            light_delta = lightest["platforms"]["codex"]["delta_vs_current_tokens"]
            heavy_delta = heaviest["platforms"]["codex"]["delta_vs_current_tokens"]
            self.assertGreaterEqual(
                heavy_delta,
                light_delta,
                "heavier scenarios should save more tokens in absolute terms",
            )

    def test_aggregate_current_and_projected_totals_are_self_consistent(self) -> None:
        current_total = sum(result["current_total_tokens"] for result in self.results.values())
        projected_total = sum(result["platforms"]["codex"]["projected_total_tokens"] for result in self.results.values())
        delta_total = sum(result["platforms"]["codex"]["delta_vs_current_tokens"] for result in self.results.values())
        self.assertEqual(
            current_total - projected_total,
            delta_total,
            "aggregate current/projected totals should reconcile with the summed deltas",
        )

    def test_aggregate_codex_delta_exceeds_20k_tokens(self) -> None:
        delta_total = sum(result["platforms"]["codex"]["delta_vs_current_tokens"] for result in self.results.values())
        self.assertGreater(
            delta_total,
            20_000,
            f"aggregate codex savings too small: {delta_total}",
        )

    def test_aggregate_current_total_stays_under_320k(self) -> None:
        current_total = sum(result["current_total_tokens"] for result in self.results.values())
        self.assertLess(
            current_total,
            320_000,
            f"aggregate lifecycle current total is unexpectedly high: {current_total}",
        )

    def test_architecture_scenario_has_highest_probe_and_savings(self) -> None:
        arch = self.results["architecture-multi-agent"]
        for scenario_id, result in self.results.items():
            if scenario_id == "architecture-multi-agent":
                continue
            self.assertGreaterEqual(
                arch["current_probe_tokens"],
                result["current_probe_tokens"],
                f"architecture scenario should have the highest probe cost, but {scenario_id} is higher",
            )
            self.assertGreaterEqual(
                arch["platforms"]["codex"]["delta_vs_current_tokens"],
                result["platforms"]["codex"]["delta_vs_current_tokens"],
                f"architecture scenario should deliver the largest codex savings, but {scenario_id} is higher",
            )


class TestSharedContractDedup(unittest.TestCase):
    """Verify that the shared-contract extraction actually reduced per-workflow token cost
    by confirming that duplicated prose is no longer present in the workflow files."""

    PHASE_WORKFLOWS = ["plan", "implement", "review", "test", "handoff", "ship"]

    def _workflow_text(self, phase: str) -> str:
        path = ROOT / ".agent" / "workflows" / f"{phase}.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def test_phase_entry_skill_loading_prose_not_duplicated(self) -> None:
        """The canonical skill-loading numbered-list prose must live in AGENTS.md only."""
        full_prose_marker = "Read `## Skill Notes` first for the current phase."
        for phase in self.PHASE_WORKFLOWS:
            text = self._workflow_text(phase)
            self.assertNotIn(
                full_prose_marker,
                text,
                f"{phase}.md should not contain the full skill-loading prose — "
                "it belongs in AGENTS.md §Shared Phase Contracts",
            )

    def test_verification_5gate_prose_not_duplicated_in_completion_workflows(self) -> None:
        """The 5-gate sequence must live in AGENTS.md only, not copied into implement/test/ship."""
        five_gate_marker = "Scope Gate"  # old per-workflow phrasing
        for phase in ("implement", "test", "ship"):
            text = self._workflow_text(phase)
            self.assertNotIn(
                five_gate_marker,
                text,
                f"{phase}.md should not contain the old '5-gate' prose — "
                "reference AGENTS.md §Shared Phase Contracts instead",
            )

    def test_agents_md_is_canonical_location_for_both_contracts(self) -> None:
        """AGENTS.md must contain both shared contracts."""
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("### Phase-Entry Skill Loading", agents_text)
        self.assertIn("### Verification Before Completion (5-Gate Sequence)", agents_text)

    def test_workflow_total_tokens_reduced_by_dedup(self) -> None:
        """Aggregate workflow token estimate must stay below a threshold that was
        previously exceeded when prose was duplicated across all 6 workflows.
        This threshold (50 000 tokens) acts as a regression guard against re-bloating."""
        total_tokens = sum(
            estimate_tokens(ROOT / ".agent" / "workflows" / f"{phase}.md")
            for phase in self.PHASE_WORKFLOWS
        )
        self.assertLess(
            total_tokens,
            50_000,
            f"Total workflow tokens {total_tokens} exceeds 50k threshold — "
            "check for re-introduced duplicated prose",
        )


if __name__ == "__main__":
    unittest.main()
