"""Cap-at-today size ratchet for `.agent/workflows/shared-contracts.md` (backlog #163).

Why this file is special: `AGENTS.md §Shared Phase Contracts` mandates loading it
at EVERY non-`tiny-fix` phase entry, yet `analyze_token_lifecycle.py`'s
`PHASE_WORKFLOW_MAP` maps only the 8 per-phase workflow files — so text placed
here carries ZERO weight in the 355k lifecycle aggregate while still costing its
real ~6x-per-task runtime load. The 2026-08-08 govern-audit tenth-man pass
explicitly reached for that hole ("host the sentence in shared-contracts, it's
free"), and the #158 fix knowingly used it with #163 cited for honest
accounting. The exclusion from the aggregate is deliberate (recorded in
`token-governance.md §5.1`); THIS test is what keeps it from being a free-
hosting loophole: any growth is a visible, deliberate, cap-bumping edit.

Discipline when this fails after a legitimate edit: bump CAP_CHARS minimally
(current size + small slack) in the SAME commit and record why in the commit
message — never pad it for headroom (mirror of the 355k ceiling discipline in
`.agentcortex/tests/test_lifecycle_token_consumption.py`).

Baseline audit trail:
  2026-08-08  6906 chars measured -> cap 7306 (+400 slack, ~100 tokens)
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / ".agent" / "workflows" / "shared-contracts.md"

CAP_CHARS = 7306


def test_shared_contracts_exists() -> None:
    """Anti-vacuity: the ratchet must be measuring a real, loaded file."""
    assert TARGET.is_file(), f"{TARGET} missing — the phase-entry contract file moved?"


def test_shared_contracts_size_within_cap() -> None:
    size = len(TARGET.read_text(encoding="utf-8"))
    assert size <= CAP_CHARS, (
        f"shared-contracts.md is {size} chars > cap {CAP_CHARS}. This file is "
        f"loaded at every non-tiny-fix phase entry but is EXCLUDED from the 355k "
        f"lifecycle aggregate (deliberate — token-governance.md §5.1, backlog "
        f"#163), so growth here is invisible to the lifecycle ratchet. If this "
        f"addition is deliberate, bump CAP_CHARS minimally in the same commit "
        f"and say why; if not, the text belongs in a counted phase doc or a "
        f"tool/test where the existing instruments see it."
    )
