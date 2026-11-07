"""Guard the workflow adapters' retained doc-lookup obligations."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ".agents/skills/doc-lookup/SKILL.md"


class TestDocLookupWorkflowDelegation(unittest.TestCase):
    def read(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_workflows_delegate_to_existing_skill_sections(self) -> None:
        skill = self.read(SKILL)
        for heading in (
            "### Hard Rule", "#### When to Fetch", "#### When You May Skip",
            "#### Platform Awareness", "## Doc URL Registry", "## Fetch Protocol",
            "### Trust Boundary", "### Failure Handling", "## Checklist",
        ):
            self.assertIn(heading, skill)
        for path in (".agent/workflows/implement.md", ".agent/workflows/review.md"):
            text = self.read(path)
            self.assertIn(f"[doc-lookup](../../{SKILL})", text)
            self.assertIn("Doc URL Registry", text)
            self.assertIn("Fetch Protocol", text)
            self.assertIn("shared phase-entry metadata/cache protocol", text)
            self.assertIn("partial, or stale", text)

    def test_implement_preserves_only_the_four_workflow_skip_cases(self) -> None:
        text = self.read(".agent/workflows/implement.md")
        clause = text.split("**IF `doc-lookup` is active:**", 1)[1].split("**IF `using-git-worktrees`", 1)[0]
        for expected in (
            "standard-library-only", "same page fetched this session",
            "local typed source covering the exact API", "non-code changes without framework APIs",
            "trivial-config", "stable-API",
        ):
            self.assertIn(expected, clause)
        self.assertIn("do not apply", clause)
        for expected in (
            "Before any framework/library API use", "signature", "parameter names",
            "return type", "defaults", "against official docs", "Ref: [URL]", "in the Work Log",
        ):
            self.assertIn(expected, clause)

    def test_review_keeps_work_log_trace_and_unverified_fallback(self) -> None:
        text = self.read(".agent/workflows/review.md")
        clause = text.split("**IF `doc-lookup` is active during review:**", 1)[1].split("## Minimum Checks", 1)[0]
        for expected in (
            "parameter order", "return types", "deprecations/migration",
            "pinned versions", "`Ref:` traces in the Work Log",
            "remains unverified", "does not resolve caveats",
        ):
            self.assertIn(expected, clause)


if __name__ == "__main__":
    unittest.main()
