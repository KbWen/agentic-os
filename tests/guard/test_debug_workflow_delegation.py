"""Guard the debugging method reference and workflow-owned phase floors."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_REL = ".agents/skills/systematic-debugging/SKILL.md"
GUARDRAILS_REL = ".agent/rules/engineering_guardrails.md"


class TestDebugWorkflowDelegation(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def phase_block(self, path: str) -> str:
        text = self.read(path)
        start = text.index("**IF `systematic-debugging` is active")
        return text[start:].split("\n\n", 1)[0]

    def assert_common_floor(self, block: str) -> None:
        for invariant in (
            "PAUSE", "Four-Phase Process", "MFR", "before any fix",
            "falsifiable hypotheses", "ONE variable at a time", "minimal fix",
            "failed patch", "`Patch Attempt [N]: <result>`", "§8.1", "2-Strike ESC", "STOP, defer to user",
        ):
            self.assertIn(invariant, block)
        # The copied step list is gone; the skill owns the detailed method.
        self.assertNotRegex(block, r"\n\s+\d\. (Observe|Hypothesize|Verify|Fix):")

    def test_implement_floor(self) -> None:
        block = self.phase_block(".agent/workflows/implement.md")
        self.assert_common_floor(block)
        self.assertIn("regression test", block)
        self.assertIn("Resume implementation only after root cause is confirmed with evidence.", block)

    def test_test_phase_floor(self) -> None:
        block = self.phase_block(".agent/workflows/test.md")
        self.assert_common_floor(block)
        self.assertIn("exact failure message, inputs, stack trace", block)
        self.assertIn("re-run all tests to confirm no regression", block)
        self.assertIn("Resume test implementation only after root cause is resolved with evidence.", block)

    def test_test_reverse_edge_unchanged(self) -> None:
        text = self.read(".agent/workflows/test.md")
        self.assertIn("if tests are still red after debugging, go back to `/implement`", text)
        self.assertIn("**`/review` MUST run again**", text)

    def test_skill_owns_four_phases(self) -> None:
        skill = self.read(SKILL_REL)
        self.assertIn("## Four-Phase Process", skill)
        for phase in ("Observe", "Hypothesize", "Verify", "Fix"):
            self.assertRegex(skill, rf"### Phase \d: {phase}")
        self.assertIn("Change one variable at a time", skill)

    def test_constitution_section_referenced_by_callers_exists(self) -> None:
        text = self.read(GUARDRAILS_REL)
        section = re.search(r"### 8\.1 Bug Fix Protocol\n(.*?)\n### ", text, re.S)
        self.assertIsNotNone(section)
        body = section.group(1)  # type: ignore[union-attr]
        self.assertIn("MFR (Minimal Reproducible Failure)", body)
        self.assertIn("2-Strike ESC", body)
        self.assertIn("Patch Attempt [N]", body)


if __name__ == "__main__":
    unittest.main()
