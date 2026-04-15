"""Regression test: lifecycle scenarios MUST align with AGENTS.md hard rules."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_PATH = ROOT / ".agentcortex" / "metadata" / "lifecycle-scenarios.json"

# Hard rules from AGENTS.md / CLAUDE.md:
REQUIRED_PHASES = {
    "quick-win": ["bootstrap", "plan", "implement", "ship"],
    "feature": ["bootstrap", "plan", "implement", "review", "test", "handoff", "ship"],
    "architecture-change": ["bootstrap", "plan", "implement", "review", "test", "handoff", "ship"],
    "hotfix": ["bootstrap", "implement", "review", "test", "ship"],
}

# Phases that are NOT required gates for quick-win
QUICK_WIN_FORBIDDEN_REQUIRED = {"review", "test", "handoff"}


class LifecycleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))["scenarios"]
        self.agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    def test_agents_supports_direct_phase_execution_on_explicit_intent(self) -> None:
        """Explicit phase requests should execute in the same turn after gate pass."""
        self.assertIn("Direct phase execution on explicit user intent", self.agents_text)
        self.assertIn("A passing gate MUST NOT introduce a second", self.agents_text)

    def test_phase_output_compression_contract_is_canonical(self) -> None:
        """AGENTS.md should define the shared compression contract used by phase workflows."""
        self.assertIn("### Phase Output Compression", self.agents_text)
        self.assertIn("`/plan` \u2192 gate + plan", self.agents_text)
        self.assertIn("`/review` \u2192 burden-of-proof table", self.agents_text)
        self.assertIn("`/test` \u2192 commands + pass/fail + coverage delta", self.agents_text)

    def test_plan_workflow_does_not_require_extra_wait_after_explicit_request(self) -> None:
        """Plan should proceed directly when the user explicitly asked for planning."""
        plan_text = (ROOT / ".agent" / "workflows" / "plan.md").read_text(encoding="utf-8")
        self.assertIn("explicitly requested planning", plan_text)
        self.assertNotIn("Awaiting your confirmation to proceed with planning.", plan_text)

    def test_implement_workflow_does_not_require_extra_wait_after_explicit_request(self) -> None:
        """Implement should proceed directly when implementation was explicitly requested."""
        implement_text = (ROOT / ".agent" / "workflows" / "implement.md").read_text(encoding="utf-8")
        self.assertIn("explicitly requested implementation", implement_text)
        self.assertNotIn("Awaiting your confirmation to proceed with implementation.", implement_text)

    def test_ship_workflow_does_not_require_extra_wait_after_explicit_request(self) -> None:
        """Ship should proceed directly when shipping was explicitly requested."""
        ship_text = (ROOT / ".agent" / "workflows" / "ship.md").read_text(encoding="utf-8")
        self.assertIn("explicitly requested shipping", ship_text)
        self.assertNotIn("Awaiting your confirmation to proceed with shipping.", ship_text)

    def test_review_and_test_workflows_reference_output_compression(self) -> None:
        """Review/test should keep delta-only output guidance instead of re-expanding prose."""
        review_text = (ROOT / ".agent" / "workflows" / "review.md").read_text(encoding="utf-8")
        test_text = (ROOT / ".agent" / "workflows" / "test.md").read_text(encoding="utf-8")
        self.assertIn("Phase Output Compression", review_text)
        self.assertIn("Do not reprint the full task description", review_text)
        self.assertIn("Output Compression Rule", test_text)
        self.assertIn("Do not reprint the full test skeleton", test_text)

    def test_quick_win_phases_exclude_review_and_test(self) -> None:
        """Quick-win required phases MUST NOT include review/test per hard rules."""
        for scenario in self.scenarios:
            if scenario["classification"] != "quick-win":
                continue
            for phase in scenario["phases"]:
                self.assertNotIn(
                    phase, QUICK_WIN_FORBIDDEN_REQUIRED,
                    f"{scenario['id']}: quick-win phases must not include '{phase}' as required. "
                    f"Use optional_coverage instead."
                )

    def test_quick_win_optional_coverage_not_in_required_phases(self) -> None:
        """optional_coverage items MUST NOT appear in required phases."""
        for scenario in self.scenarios:
            if scenario["classification"] != "quick-win":
                continue
            optional = set(scenario.get("optional_coverage", []))
            required = set(scenario["phases"])
            overlap = optional & required
            self.assertFalse(
                overlap,
                f"{scenario['id']}: optional_coverage {sorted(overlap)} must not "
                f"also appear in required phases"
            )

    def test_feature_full_lifecycle_has_all_required_phases(self) -> None:
        """Feature scenarios starting from bootstrap MUST include all hard-rule phases."""
        required = set(REQUIRED_PHASES["feature"])
        for scenario in self.scenarios:
            if scenario["classification"] != "feature":
                continue
            # Skip mid-lifecycle continuation scenarios (don't start at bootstrap)
            if scenario["phases"][0] != "bootstrap":
                continue
            phases = set(scenario["phases"])
            missing = required - phases
            self.assertFalse(
                missing,
                f"{scenario['id']}: feature missing required phases {sorted(missing)}"
            )

    def test_hotfix_has_required_phases(self) -> None:
        """Hotfix scenarios MUST include all hard-rule phases."""
        required = set(REQUIRED_PHASES["hotfix"])
        for scenario in self.scenarios:
            if scenario["classification"] != "hotfix":
                continue
            phases = set(scenario["phases"])
            missing = required - phases
            self.assertFalse(
                missing,
                f"{scenario['id']}: hotfix missing required phases {sorted(missing)}"
            )


if __name__ == "__main__":
    unittest.main()
