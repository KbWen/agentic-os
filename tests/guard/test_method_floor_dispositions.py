"""Workflow-owned phase floors stay self-contained.

Upgrades force-update workflows but preserve customized (scaffold) skill bodies
(ADR-005), so these caller floors must not be reduced to bare skill pointers.
"""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FLOORS = {
    ".agent/workflows/implement.md": {
        "api-design": ["Input validation at controller level", "Parameterized queries", "explicit `public` annotation"],
        "database-design": ["Migration file MUST exist", "forward-only migrations. Guardrails take precedence"],
        "frontend-patterns": ["loading, error, empty, success", "Disable form submit button"],
        "auth-security": ["bcrypt (cost 12+) or argon2id", "NOT localStorage", "httpOnly, secure, sameSite",
                          "5 failures", "never reveal which field is wrong"],
        "dispatching-parallel-agents": ["Definition of Done", "regression tests BEFORE final merge"],
        "using-git-worktrees": ["intended isolated worktree BEFORE modifying code", "Do NOT branch-switch"],
    },
    ".agent/workflows/test.md": {
        "auth-security": ["→ 401", "→ 403", "Manipulated token", "Password stored as hash"],
        "api-design": ["structured error response", "don't leak internals"],
        "database-design": ["skip if project uses forward-only migrations", "NOT NULL constraints enforced"],
        "frontend-patterns": ["all 4 states", "no double-submit"],
    },
}


class TestMethodFloorDispositions(unittest.TestCase):
    def block(self, path: str, skill: str) -> str:
        text = (ROOT / path).read_text(encoding="utf-8")
        start = text.index(f"**IF `{skill}`")
        return text[start:].split("\n\n", 1)[0]

    def test_caller_floors_retained(self) -> None:
        for path, skills in FLOORS.items():
            for skill, needles in skills.items():
                block = self.block(path, skill)
                for needle in needles:
                    with self.subTest(path=path, skill=skill, needle=needle):
                        self.assertIn(needle, block)

    def test_database_skill_carries_forward_only_exception(self) -> None:
        skill = (ROOT / ".agents/skills/database-design/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Migrations MUST be reversible", skill)
        self.assertIn("unless the project ADR picks forward-only (`engineering_guardrails.md` §12.3)", skill)
        self.assertIn("**Test rollback** (reversible strategy)", skill)
        self.assertIn("up → verify → down → verify → up (if reversible)", skill)
        guardrails = (ROOT / ".agent/rules/engineering_guardrails.md").read_text(encoding="utf-8")
        self.assertIn("### 12.3 Migration Safety", guardrails)
        self.assertIn("forward-only vs. reversible", guardrails)


if __name__ == "__main__":
    unittest.main()
