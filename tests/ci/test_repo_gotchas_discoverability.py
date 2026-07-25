"""Repo-gotchas discoverability guard.

`.agent/rules/repo-gotchas.md` is only useful if the next AI session finds it
without a human remembering it exists. Discovery rides on a SINGLE pointer in
`AGENTS.md §References`, which reaches every platform entry point:

  - `CLAUDE.md`  -> `@AGENTS.md` import
  - `GEMINI.md`  -> `@AGENTS.md` import
  - Codex        -> reads `AGENTS.md` directly (no adapter file of its own)
  - Copilot      -> `.github/copilot-instructions.md` names AGENTS.md as SoT

That one-line design is only sound while those four inheritance paths hold, so
this guard pins BOTH halves: the pointer itself, and the inheritance that makes
one pointer sufficient. If an adapter ever stops inheriting `AGENTS.md`, the
pointer silently stops reaching that platform — this test is what catches it.

It also pins the file's character: gotchas are KNOWLEDGE, not rules. Keeping it
free of hard-directive keywords is what keeps `engineering_guardrails.md §13`
ADD-Gate signal tiering inapplicable, so the surface cannot quietly grow into
unenforced honor-system directives.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOTCHAS_REL = ".agent/rules/repo-gotchas.md"
GOTCHAS_PATH = ROOT / ".agent" / "rules" / "repo-gotchas.md"
AGENTS_PATH = ROOT / "AGENTS.md"

# Canonical source: tests/ci/test_directive_count_ratchet.py::DIRECTIVE_PATTERN
# (and the `pattern` field of .agentcortex/metadata/directive-count-baseline.json).
# Duplicated deliberately — tests do not import each other.
_DIRECTIVE_RE = re.compile(r"MUST NOT|MUST|NEVER|PROHIBITED|STRICTLY|Gate FAIL")

# Platform entry points and the token each one uses to inherit AGENTS.md.
PLATFORM_ENTRIES = [
    ("CLAUDE.md", "@AGENTS.md"),
    ("GEMINI.md", "@AGENTS.md"),
    (".github/copilot-instructions.md", "AGENTS.md"),
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_gotchas_file_exists() -> None:
    assert GOTCHAS_PATH.is_file(), f"{GOTCHAS_REL} is missing"


def test_agents_md_points_at_gotchas() -> None:
    """The single pointer every platform inherits."""
    assert GOTCHAS_REL in read("AGENTS.md"), (
        f"AGENTS.md no longer references {GOTCHAS_REL}. That pointer is the ONLY "
        "discovery path for all four platform entry points — restore it, or add a "
        "per-adapter pointer and update PLATFORM_ENTRIES here."
    )


@pytest.mark.parametrize("entry,token", PLATFORM_ENTRIES)
def test_platform_entry_inherits_agents_md(entry: str, token: str) -> None:
    """Inheritance is the assumption that makes ONE pointer sufficient."""
    path = ROOT / entry
    assert path.is_file(), f"{entry} is missing"
    assert token in path.read_text(encoding="utf-8"), (
        f"{entry} no longer carries '{token}', so it stops inheriting AGENTS.md — "
        f"the {GOTCHAS_REL} pointer would silently stop reaching this platform."
    )


def test_gotchas_carries_no_hard_directives() -> None:
    """Knowledge, not rules — keeps §13 ADD-Gate tiering inapplicable."""
    hits = _DIRECTIVE_RE.findall(GOTCHAS_PATH.read_text(encoding="utf-8"))
    assert not hits, (
        f"{GOTCHAS_REL} gained hard-directive keyword(s) {sorted(set(hits))}. "
        "This file is a lookup table, not a rule surface: a directive here would be "
        "unenforced honor-system text. Move the rule to a surface that can enforce it."
    )
