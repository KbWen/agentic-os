"""Directive-count ratchet test (AC-11, docs/specs/directive-enforcement-audit.md).

Machine-checked GROWTH ratchet for hard-directive keyword hits on the four
phase-entry surfaces (AGENTS.md, engineering_guardrails.md,
security_guardrails.md, shared-contracts.md). Mirrors the repo's 355k
token-ceiling pattern (.agentcortex/tests/test_lifecycle_token_consumption.py
/ tests/ci/test_lifecycle_baseline_drift.py) but for directive DENSITY
instead of token volume.

Canonical pattern (case-sensitive, longest-match-first so "MUST NOT" is never
also double-counted as a bare "MUST" — Python's `re` alternation tries
alternatives left-to-right and uses the first one that matches at a given
position, so listing "MUST NOT" before "MUST" makes the longer phrase win):

    MUST NOT|MUST|NEVER|PROHIBITED|STRICTLY|Gate FAIL

This is the exact literal string recorded in the `pattern` field of the
committed baseline (`.agentcortex/metadata/directive-count-baseline.json`) —
that field IS this docstring's canonical pattern, not an independent copy.

NOT a fixed numeric target (spec Non-goals: "No numeric instruction-count
target / gate. No `target < 85`"). The ratchet FAILs ONLY when a file's live
count EXCEEDS its committed baseline. Equal or lower counts PASS; a lower
count additionally signals (advisory only — never fails) that the baseline
could be ratcheted down in the same change.

Accepted limitation (AC-11): keyword rewording can evade this ratchet — it
targets drift, not adversaries.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / ".agentcortex" / "metadata" / "directive-count-baseline.json"
ENUMERATION_PATH = (
    ROOT / "docs" / "reviews" / "2026-07-19-phase-entry-directive-enumeration.md"
)

# Order matters: "MUST NOT" MUST precede "MUST" (see module docstring).
DIRECTIVE_PATTERN = r"MUST NOT|MUST|NEVER|PROHIBITED|STRICTLY|Gate FAIL"
_DIRECTIVE_RE = re.compile(DIRECTIVE_PATTERN)

# The four phase-entry surfaces this ratchet covers (repo-relative, POSIX-style).
SURFACES = [
    "AGENTS.md",
    ".agent/rules/engineering_guardrails.md",
    ".agent/rules/security_guardrails.md",
    ".agent/workflows/shared-contracts.md",
]

# Baseline keys that are metadata, not one of the four counted surfaces.
_BASELINE_METADATA_KEYS = {"_doc", "pattern", "date", "note"}


def count_directives(text: str) -> int:
    """Count hard-directive keyword hits per DIRECTIVE_PATTERN.

    Normalizes CRLF/CR line endings to LF before counting so a Windows
    checkout (CRLF) and a Unix checkout (LF) of the same file always produce
    the identical count — line-ending style must never change the result.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return len(_DIRECTIVE_RE.findall(normalized))


def check_ratchet(count: int, baseline: int) -> tuple[bool, str]:
    """Cap-at-today ratchet check: FAIL only when count > baseline.

    Returns (passed, message). count == baseline passes with a neutral
    message; count < baseline passes AND the message advisory-signals that
    the baseline could be lowered (never fails — trimming is never punished).
    """
    if count > baseline:
        return False, f"count {count} exceeds baseline {baseline} (growth)"
    if count < baseline:
        return (
            True,
            f"count {count} is below baseline {baseline} — baseline could be lowered",
        )
    return True, f"count {count} matches baseline {baseline}"


def _load_baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


# --- 1. count_directives ------------------------------------------------


def test_count_function_counts_keywords() -> None:
    text = (
        "You MUST NOT do this. You MUST do that. NEVER do the other thing. "
        "This is STRICTLY PROHIBITED. Skipping this is a Gate FAIL."
    )
    # MUST NOT, MUST, NEVER, STRICTLY, PROHIBITED, Gate FAIL = 6 hits.
    # "MUST NOT" must NOT also register a separate bare "MUST" hit.
    assert count_directives(text) == 6
    assert count_directives("Nothing to see here, just plain prose.") == 0


# --- 2. check_ratchet: growth -------------------------------------------


def test_growth_fails() -> None:
    passed, message = check_ratchet(count=10, baseline=9)
    assert passed is False
    assert "10" in message and "9" in message


# --- 3. check_ratchet: equal / lower -------------------------------------


def test_equal_passes() -> None:
    passed, _ = check_ratchet(count=9, baseline=9)
    assert passed is True


def test_lower_passes() -> None:
    passed, message = check_ratchet(count=5, baseline=9)
    assert passed is True
    # Lower-than-baseline is advisory-signalled (never fails) so the baseline
    # can be ratcheted down in the same change.
    assert "could be lowered" in message


# --- 4. baseline schema ---------------------------------------------------


def test_baseline_schema() -> None:
    data = _load_baseline()
    assert data["pattern"] == DIRECTIVE_PATTERN, (
        "baseline pattern field must be byte-identical to the canonical "
        "DIRECTIVE_PATTERN this module documents and enforces"
    )
    assert isinstance(data["date"], str) and data["date"]
    # Exactly the four surfaces (repo-relative paths) plus known metadata keys —
    # no more, no fewer.
    assert set(data) == set(SURFACES) | _BASELINE_METADATA_KEYS
    for rel_path in SURFACES:
        count = data[rel_path]
        assert isinstance(count, int) and not isinstance(count, bool), (
            f"{rel_path}: baseline count must be an int, got {type(count).__name__}"
        )


# --- 5. real surfaces vs. baseline (the durable live gate) ---------------


def test_real_surfaces_within_baseline() -> None:
    data = _load_baseline()
    failures: list[str] = []
    for rel_path in SURFACES:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        live_count = count_directives(text)
        baseline_count = data[rel_path]
        passed, message = check_ratchet(live_count, baseline_count)
        if not passed:
            failures.append(f"{rel_path}: {message}")
    assert not failures, (
        "directive count grew beyond the committed baseline — either revert "
        "the wording that added directives, or if the growth is intentional, "
        "update .agentcortex/metadata/directive-count-baseline.json in the "
        "same change:\n" + "\n".join(failures)
    )


# --- 6. enumeration table structure (parallel workstream, not yet landed) --

_ENUMERATION_HEADER = (
    "| # | surface | section | directive | keywords | read-moment | ordinal "
    "| tier | backing | disposition | note |"
)
_VALID_TIERS = {"T1", "T2", "T3", "NONE"}
_VALID_DISPOSITIONS = {
    "keep",
    "delete",
    "merge",
    "add-enforcement",
    "keep-honest-unenforced",
    "EXCLUDED",
    "FLAG",
}


def _strip_fenced_code(lines: list[str]) -> list[str]:
    """Drop lines that fall inside ``` fences (toggled by fence-open lines)."""
    kept: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return kept


def _is_separator_row(row: str) -> bool:
    """True for a markdown table separator row, e.g. `| --- | :--- | ---: |`."""
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)


@pytest.mark.skipif(
    not ENUMERATION_PATH.exists(),
    reason="enumeration table not yet committed (parallel workstream)",
)
def test_enumeration_table_structure() -> None:
    text = ENUMERATION_PATH.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = _strip_fenced_code(normalized.split("\n"))
    table_lines = [ln for ln in lines if ln.strip().startswith("|")]
    assert table_lines, "no markdown table found in enumeration doc"
    assert table_lines[0].strip() == _ENUMERATION_HEADER, (
        f"header row mismatch: {table_lines[0].strip()!r}"
    )

    data_rows = [ln for ln in table_lines[1:] if not _is_separator_row(ln)]
    assert data_rows, "no data rows found in enumeration table"

    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 11, f"malformed row (expected 11 cells): {row!r}"
        _, _surface, _section, _directive, _keywords, _read_moment, _ordinal, tier, _backing, disposition, note = cells

        assert tier in _VALID_TIERS, f"invalid tier {tier!r} in row: {row!r}"
        assert disposition in _VALID_DISPOSITIONS, (
            f"invalid disposition {disposition!r} in row: {row!r}"
        )
        if tier == "NONE":
            assert disposition != "keep", (
                "tier=NONE rows must not use disposition=keep — "
                f"use keep-honest-unenforced instead: {row!r}"
            )
        if disposition == "delete":
            assert "observability-only" in note, (
                f"disposition=delete row must cite observability-only in its "
                f"note column: {row!r}"
            )


# --- 7. adversarial counting-semantics pins (documented limitations) ------


def test_adversarial_counting_semantics() -> None:
    """Pin the ratchet's DOCUMENTED limitations (/test Step 4 adversarial
    cases, red-team Full) so any semantic change to the counting function is
    a conscious, reviewed edit rather than silent drift. Honest-limitation
    pins, not aspirations: the ratchet targets drift, not adversaries (AC-11).
    """
    # Lowercase evades the case-sensitive pattern (rewording escape hatch).
    assert count_directives("you must not do this, never ever") == 0
    # No word boundary: substrings count. The baseline is captured with the
    # same semantics, so this can only loosen the cap, never false-FAIL it.
    assert count_directives("MUSTARD") == 1
    assert count_directives("UNPROHIBITED") == 1
    # Fenced code is NOT excluded — raw grep-style counting on both sides
    # (live count and baseline include fenced examples identically).
    assert count_directives("```\nMUST\n```") == 1
    # CRLF and LF checkouts count identically across a keyword boundary.
    assert count_directives("Gate FAIL\r\nMUST") == count_directives(
        "Gate FAIL\nMUST"
    )
