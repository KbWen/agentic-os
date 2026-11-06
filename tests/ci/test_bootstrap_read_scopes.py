"""Structural branch protection; not evidence of model behavior or token savings."""
from pathlib import Path
import re

import pytest


BOOTSTRAP = Path(__file__).resolve().parents[2] / ".agent/workflows/bootstrap.md"
START = "<!-- SCOPE: Steps 3-6 are conditional"
END = "<!-- END conditional steps -->"
REQUIRED = {
    3: (
        "when present", "IF `.agentcortex/context/private/` exists",
        "SCAN for local-only instructions", "research-*.md",
        "multiple matches", "ask which to resume",
    ),
    4: (
        "migration tasks only", ".agentcortex/docs/guides/migration.md",
        "MUST output migration plan and await user `OK` before ANY move/rename",
    ),
    5: (
        "when present", "read ONLY the Feature Inventory table",
        "Pending → In Progress", "Pending → Shipped", "invalid",
        "Kind & Priority assignment", "Label cluster check", "never ask again",
    ),
    6: (
        "when provided", "If user provided a spec", "/spec-intake",
        "Do NOT proceed past Step 6", "External authority rule",
        "Domain Doc L1", "Orphaned", "Never ask user to restructure input",
    ),
}


def _steps(text: str) -> dict[int, str]:
    """Test-only extraction: each step has an unambiguous retrieval boundary."""
    start = text.index(START)
    region = text[start:text.index(END, start)]
    headings = list(re.finditer(r"(?m)^### Step (\d+): .+$", region))
    if [int(m[1]) for m in headings] != [3, 4, 5, 6]:
        raise ValueError("expected exactly one ordered heading for each conditional step")
    return {
        int(m[1]): region[m.start():headings[i + 1].start() if i + 1 < len(headings) else len(region)]
        for i, m in enumerate(headings)
    }


def _validate(text: str) -> dict[int, str]:
    blocks = _steps(text)
    for step, obligations in REQUIRED.items():
        for obligation in obligations:
            if " ".join(obligation.split()) not in " ".join(blocks[step].split()):
                raise ValueError(f"step {step} lost: {obligation}")
    return blocks


def _source() -> str:
    return BOOTSTRAP.read_text(encoding="utf-8")


def test_all_conditional_branches_retain_required_operations() -> None:
    assert set(_validate(_source())) == {3, 4, 5, 6}


def test_migration_scope_can_be_read_without_backlog_or_raw_intake() -> None:
    migration = _validate(_source())[4]
    assert "Feature Inventory" not in migration
    assert "Orphaned" not in migration


def test_allows_benign_body_line_wrapping() -> None:
    text = _source().replace("await user `OK` before", "await user\n  `OK` before", 1)
    assert set(_validate(text)) == {3, 4, 5, 6}


@pytest.mark.parametrize("step", [3, 4, 5, 6])
def test_rejects_missing_branch(step: int) -> None:
    text = _source()
    block = _validate(text)[step]
    with pytest.raises(ValueError):
        _validate(text.replace(block, "", 1))


def test_rejects_duplicate_heading() -> None:
    text = _source()
    heading = _validate(text)[3].splitlines()[0]
    with pytest.raises(ValueError):
        _validate(text.replace(heading, heading + "\n" + heading, 1))


def test_rejects_unplanned_conditional_branch() -> None:
    text = _source()
    _validate(text)
    with pytest.raises(ValueError):
        _validate(text.replace(END, "### Step 7: Unplanned branch\n" + END, 1))


@pytest.mark.parametrize("step,obligation", [
    (3, "ask which to resume"),
    (4, "await user `OK` before ANY move/rename"),
    (5, "read ONLY the Feature Inventory table"),
    (5, "Pending → In Progress"),
    (6, "Do NOT proceed past Step 6"),
    (6, "Domain Doc L1"),
])
def test_rejects_lost_operation(step: int, obligation: str) -> None:
    text = _source()
    block = _validate(text)[step]
    mutated = text.replace(block, block.replace(obligation, "omitted", 1), 1)
    with pytest.raises(ValueError):
        _validate(mutated)
