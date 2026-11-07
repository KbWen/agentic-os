"""Guard the TDD method reference and workflow-owned phase contracts."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_REL = ".agents/skills/test-driven-development/SKILL.md"


class TestTddWorkflowDelegation(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def phase_block(self, path: str) -> str:
        text = self.read(path)
        return text.split("**IF `test-driven-development` is active:**", 1)[1].split("\n\n**IF ", 1)[0]

    def test_implement_links_canonical_method_and_keeps_compatibility_floor(self) -> None:
        block = self.phase_block(".agent/workflows/implement.md")
        match = re.search(r"\]\(([^)]+test-driven-development/SKILL\.md)\)", block)
        self.assertIsNotNone(match)
        target = ((ROOT / ".agent/workflows").resolve() / match.group(1)).resolve()  # type: ignore[union-attr]
        self.assertEqual(target, (ROOT / SKILL_REL).resolve())
        for invariant in (
            "Switch normal execution of the current plan step", "one planned behavior per cycle",
            "failing test before production code", "minimal passing code",
            "all tests green after refactoring", "repeat until the step is complete",
        ):
            self.assertIn(invariant, block)

    def test_test_phase_contract_stays_self_contained_in_workflow(self) -> None:
        block = self.phase_block(".agent/workflows/test.md")
        self.assertIn("every production piece written during `/implement` has a corresponding test", block)
        self.assertIn("write missing tests NOW before proceeding", block)
        self.assertIn("All tests MUST pass", block)
        self.assertIn("no known failures", block)
        self.assertNotIn("/test` Checklist", block)

    def test_skill_method_and_baseline_rules_remain_canonical(self) -> None:
        skill = self.read(SKILL_REL)
        self.assertIn("## Workflow", skill)
        self.assertIn("## Ironclad Rules", skill)
        self.assertNotIn("## Overview", skill)
        for invariant in (
            "Write a failing test describing the expected behavior",
            "Write the minimal code to make the test pass",
            "Focus on one small goal per cycle",
            "All tests MUST pass after refactoring",
        ):
            self.assertIn(invariant, skill)
        self.assertNotIn("### `/test`", skill)

    def test_generated_hash_matches_skill_and_activation_is_unchanged(self) -> None:
        index = json.loads(self.read(".agentcortex/metadata/trigger-compact-index.json"))
        entry = next(item for item in index["entries"] if item["id"] == "test-driven-development")
        self.assertEqual(entry["phase_scope"], ["implement", "test"])
        self.assertEqual(entry["load_policy"], "on-match")
        body = (ROOT / SKILL_REL).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(entry["content_hash"], hashlib.sha256(body).hexdigest()[:8])


if __name__ == "__main__":
    unittest.main()
