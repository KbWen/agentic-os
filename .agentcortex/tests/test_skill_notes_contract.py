from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def normalize_for_compare(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def extract_markdown_sections(text: str, level: int) -> dict[str, str]:
    normalized = text.replace("\r\n", "\n")
    matches = list(re.finditer(rf"^(#{{{level}}})\s+(.*?)\s*$", normalized, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = len(normalized)
        for next_match in matches[index + 1 :]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        sections[match.group(2).strip()] = normalized[start:end]
    return sections


def skill_phase_note_is_valid(skill_notes_text: str, skill_id: str, phase: str) -> bool:
    skill_blocks = extract_markdown_sections(skill_notes_text, 3)
    skill_block = skill_blocks.get(skill_id)
    if not skill_block:
        return False
    phase_blocks = extract_markdown_sections(skill_block, 4)
    phase_block = phase_blocks.get(phase)
    if not phase_block:
        return False
    lines = [line.strip() for line in phase_block.splitlines() if line.strip()]
    checklist_count = sum(line.startswith("- Checklist:") for line in lines)
    constraint_count = sum(line.startswith("- Constraint:") for line in lines)
    body = "\n".join(
        line.replace("- Checklist:", "", 1).replace("- Constraint:", "", 1).strip()
        for line in lines
        if line.startswith("- Checklist:") or line.startswith("- Constraint:")
    )
    body = "".join(body.split())
    return checklist_count >= 2 and constraint_count >= 1 and len(body) >= 50


def extract_section(text: str, heading: str) -> str:
    sections = extract_markdown_sections(text, 2)
    return sections[heading]


def compact_worklog_fixture(text: str) -> str:
    protected = [
        "Session Info",
        "Evidence",
        "Conflict Resolution",
        "Skill Notes",
        "Resume",
    ]
    extracted = [extract_section(text, heading) for heading in protected]
    return "\n\n".join(
        [
            "# Work Log: compacted-fixture",
            "Compacted: 2026-03-25, archive: .agentcortex/context/archive/work/fixture-20260325.md",
            *extracted,
        ]
    )


class SkillNotesContractTests(unittest.TestCase):
    def test_valid_skill_phase_note_is_cache_hit(self) -> None:
        skill_notes = """
## Skill Notes

### test-driven-development
- Content Hash: a3f8c2e1
- First Loaded Phase: implement
- Applies To: implement, test

#### implement
- Checklist: Write the failing test before changing production code.
- Checklist: Keep the implementation minimal until the target assertion passes.
- Constraint: Do not batch multiple behaviors into one Red to Green cycle because review needs step-level evidence.
        """
        self.assertTrue(skill_phase_note_is_valid(skill_notes, "test-driven-development", "implement"))

    def test_missing_constraint_is_cache_miss(self) -> None:
        skill_notes = """
## Skill Notes

### test-driven-development
- First Loaded Phase: implement
- Applies To: implement, test

#### implement
- Checklist: Write the failing test before changing production code.
- Checklist: Keep the implementation minimal until the target assertion passes.
- Checklist: Re-run the focused suite before moving to the next behavior.
"""
        self.assertFalse(skill_phase_note_is_valid(skill_notes, "test-driven-development", "implement"))

    def test_short_note_is_cache_miss(self) -> None:
        skill_notes = """
## Skill Notes

### executing-plans
- First Loaded Phase: implement
- Applies To: implement

#### implement
- Checklist: Do one step.
- Checklist: Verify right away.
- Constraint: Stay small.
"""
        self.assertFalse(skill_phase_note_is_valid(skill_notes, "executing-plans", "implement"))

    def test_phase_entry_contract_is_capability_by_presence(self) -> None:
        """Capability-by-presence: AGENTS.md §Shared Phase Contracts keeps the detailed
        conditional. Phase workflows reference AGENTS.md instead of repeating the prose."""
        # AGENTS.md retains the detailed conditional text in §Shared Phase Contracts
        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        # Capability-by-presence: metadata is checked first, with an explicit
        # fallback clause so missing metadata files MUST NOT block skill loading.
        self.assertIn(
            "`.agentcortex/metadata/trigger-compact-index.json`",
            agents_text,
            "AGENTS.md: Phase-Entry Skill Loading must reference the compact-index metadata path",
        )
        self.assertIn(
            "If neither metadata file exists",
            agents_text,
            "AGENTS.md: Phase-Entry Skill Loading must carry the capability-by-presence fallback",
        )
        # AGENTS.md §Shared Phase Contracts has the canonical config.yaml reference
        self.assertIn(
            "## Shared Phase Contracts",
            agents_text,
            "AGENTS.md: must have a ## Shared Phase Contracts section",
        )
        self.assertIn(
            "config.yaml",
            agents_text,
            "AGENTS.md Shared Phase Contracts: must reference config.yaml skill_cache_policy",
        )
        # CLAUDE.md is intentionally simplified to @import AGENTS.md (commit 95ceafb); it must
        # NOT duplicate the skill_cache_policy reference that already lives in AGENTS.md above.
        # Phase workflow files reference AGENTS.md instead of repeating the skill-loading prose
        phase_workflows = [
            ROOT / ".agent/workflows/plan.md",
            ROOT / ".agent/workflows/implement.md",
            ROOT / ".agent/workflows/review.md",
            ROOT / ".agent/workflows/test.md",
            ROOT / ".agent/workflows/handoff.md",
            ROOT / ".agent/workflows/ship.md",
        ]
        for path in phase_workflows:
            text = path.read_text(encoding="utf-8")
            self.assertIn(
                "AGENTS.md",
                text,
                f"{path.name}: should reference AGENTS.md shared contract instead of repeating skill-loading prose",
            )

    def test_bootstrap_keeps_embedded_rule_table_as_canonical_trigger_source(self) -> None:
        text = (ROOT / ".agent/workflows/bootstrap.md").read_text(encoding="utf-8")
        self.assertIn("embedded rule table is the canonical low-token trigger source", text)


class HandoffCompactionContractTests(unittest.TestCase):
    def test_handoff_workflow_mentions_protected_sections(self) -> None:
        text = (ROOT / ".agent/workflows/handoff.md").read_text(encoding="utf-8")
        self.assertIn("## Skill Notes", text)
        self.assertIn("## Conflict Resolution", text)
        self.assertIn("## Evidence", text)
        self.assertIn("latest `## Resume`", text)
        self.assertIn("`## Session Info`", text)

    def test_compaction_fixture_preserves_protected_sections(self) -> None:
        original = """
# Work Log: fixture

## Session Info
- Agent: Codex GPT-5
- Session: 2026-03-25T12:00:00+08:00
- Platform: Codex App

## Conflict Resolution
- tdd > parallel dispatch for shared logic.

## Skill Notes

### test-driven-development
- First Loaded Phase: implement
- Applies To: implement, test

#### implement
- Checklist: Write the failing test before changing production code.
- Checklist: Keep the implementation minimal until the target assertion passes.
- Constraint: Do not batch multiple behaviors into one Red to Green cycle because review needs step-level evidence.

#### test
- Checklist: Confirm every production change has a corresponding test before completion.
- Checklist: Re-run the focused suite after adding any missing regression coverage.
- Constraint: Test completion is invalid if critical paths still rely on narrative confidence instead of passing output.

### verification-before-completion
- First Loaded Phase: implement
- Applies To: implement, test, ship

#### implement
- Checklist: Verify scope against the approved target files before claiming completion.
- Checklist: Capture the command and result immediately after each implementation step.
- Constraint: Never claim implementation complete without reproducible terminal evidence tied to this turn.

#### ship
- Checklist: Re-run required checks after syncing with mainline.
- Checklist: Confirm rollback strategy and known risks are present in the completion summary.
- Constraint: Shipping is blocked when any verification gate is unresolved or evidence is stale.

### red-team-adversarial
- First Loaded Phase: review
- Applies To: review, test

#### review
- Checklist: Enumerate boundary abuse cases before declaring the review ready.
- Checklist: Record any high-risk finding with an explicit accept or fix decision.
- Constraint: Red-team output cannot be reduced to a generic security note because the phase needs attack-specific evidence.

#### test
- Checklist: Turn realistic abuse paths into executable adversarial checks when possible.
- Checklist: Record which scenarios were skipped and why if environment limits execution.
- Constraint: Test evidence must distinguish standard regressions from adversarial stress cases.

## Evidence
Command: python -m pytest .agentcortex/tests -q
Result: pass
Summary: fixture evidence

## Resume
- State: REVIEWED
- Completed: implement, review
- Next: run ship gate
- Context: keep protected sections intact during compaction.

## Delta Log
- very long historical entry 1
- very long historical entry 2
"""
        compacted = compact_worklog_fixture(original)
        for heading in ("Session Info", "Conflict Resolution", "Skill Notes", "Evidence", "Resume"):
            self.assertEqual(
                normalize_for_compare(extract_section(compacted, heading)),
                normalize_for_compare(extract_section(original, heading)),
                f"{heading} should survive compaction unchanged after normalization",
            )


class ShipWorkflowContractTests(unittest.TestCase):
    def test_ship_workflow_includes_mandatory_archive_checklist(self) -> None:
        text = (ROOT / ".agent/workflows/ship.md").read_text(encoding="utf-8")
        self.assertIn("## Ship Checklist (mandatory — skip = ship fail)", text)
        self.assertIn("Evidence recorded in Work Log", text)
        self.assertIn("`current_state.md` updated", text)
        self.assertIn("Active Work Log archived to `.agentcortex/context/archive/`", text)


if __name__ == "__main__":
    unittest.main()
