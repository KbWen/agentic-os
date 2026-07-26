"""Work Log risk section is named `## Known Risk` everywhere (backlog #145, S2).

The template, `AGENTS.md §Work Log Contract` and the validator all use `## Known Risk`.
Four workflow sites and one guide used `## Risks` instead — including
`handoff.md`, which named BOTH, seven lines apart: its preserve-list said
`## Known Risk` while its compaction step said keep "latest `## Risks`". An agent
following the template produced a section the compaction rule did not protect.

The naming is only half the point. The other half is *where* the drift hides:
`plan.md` carried `## Risks` as a **bare heading inside a fenced block that agents copy
verbatim**. A scanner that only looks for backticked `` `## X` `` citations cannot see that,
which is exactly the blind spot that let this survive. So this check reads fenced content too,
and `test_detector_sees_fenced_headings` pins that it keeps doing so.

Cap-at-zero: fails only when a new `## Risks` appears on a live governance surface.
Archived Work Logs under `.agentcortex/context/archive/` are excluded — archives are immutable
records of what was written at the time, not surfaces an agent reads for instructions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Live instruction surfaces an agent reads. Archives and work logs are deliberately absent.
SCAN_DIRS = (
    Path(".agent"),
    Path(".agentcortex/docs/guides"),
    Path(".claude/commands"),
)

WRONG = re.compile(r"^##\s+Risks\s*$|`##\s+Risks`", re.M)
CANONICAL = "## Known Risk"


def _surfaces() -> list[Path]:
    out: list[Path] = []
    for rel in SCAN_DIRS:
        base = ROOT / rel
        if base.is_dir():
            out.extend(sorted(base.rglob("*.md")))
    return out


def _offending_lines(text: str) -> list[int]:
    """Line numbers naming `## Risks`, counting fenced content as in scope.

    Deliberately does NOT skip ``` fences: a heading inside a template block is copied
    verbatim into a real Work Log, so it is exactly as binding as prose around it.
    """
    return [i for i, line in enumerate(text.splitlines(), 1) if WRONG.search(line)]


def test_no_stale_risks_section_on_live_surfaces() -> None:
    offenders: list[str] = []
    for path in _surfaces():
        for line in _offending_lines(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT).as_posix()}:{line}")

    assert not offenders, (
        "governance surface(s) name a Work Log `## Risks` section; the template, the "
        f"AGENTS.md Work Log Contract and the validator all use `{CANONICAL}`:\n  "
        + "\n  ".join(offenders)
    )


def test_detector_sees_fenced_headings() -> None:
    """The blind spot that let this drift survive — pin that it is closed."""
    fenced = "intro\n\n```markdown\n## Risks\n- x\n```\n"
    assert _offending_lines(fenced) == [4], "a bare heading inside a fence must be detected"


def test_detector_sees_backticked_citation() -> None:
    assert _offending_lines("write it to `## Risks` in the log\n") == [1]


def test_detector_does_not_flag_the_canonical_name() -> None:
    for sample in (f"{CANONICAL}\n", f"append to `{CANONICAL}`\n", "## Risks Assessment\n"):
        assert _offending_lines(sample) == [], f"false positive on: {sample!r}"


def test_scan_actually_reaches_the_surfaces() -> None:
    files = _surfaces()
    assert len(files) > 40, f"expected the governance tree, found only {len(files)} files"
    names = {p.name for p in files}
    assert {"plan.md", "handoff.md", "bootstrap.md"} <= names
    assert not any(
        "archive" in p.relative_to(ROOT).parts for p in files
    ), "immutable archives must stay out of scope"


@pytest.mark.parametrize("rel", ["\
.agent/workflows/plan.md", ".agent/workflows/handoff.md"])
def test_canonical_name_is_actually_present(rel: str) -> None:
    """Guard against 'fixing' this by deleting the section instead of renaming it."""
    assert CANONICAL in (ROOT / rel).read_text(encoding="utf-8"), (
        f"{rel} no longer references {CANONICAL} at all — the rename must not become a deletion"
    )
