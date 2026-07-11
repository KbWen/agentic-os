"""Cross-workflow content-pin tests for external-executor safety (2026-07-11 audit).

Pins the write-capable external-executor safety contract so a careless edit cannot
silently drop any of the four elements the audit (F4/F5/F6) requires from the three
governing docs — Claude CLI, Codex CLI, and `engineering_guardrails.md` §8.2 (the canon):

  * F4 — abnormal-exit (timeout / nonzero / kill) state reconstruction + retry blocking.
  * F5 — pre-flight baseline capture and a dirty-baseline whole-file-revert prohibition.
  * F6 — Requested/Actual executor provenance + disclosure of an explicit-request fallback.

Enforcement teeth for the [enforcement] Global Lesson ("a MUST without a validator is
theatre"): these are the cross-workflow contract test the audit's acceptance asks for.
Pure-Python file reads (CI-safe on Linux); `docs_pin`-marked so docs-only PRs run them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_CLI = ROOT / ".agent" / "workflows" / "claude-cli.md"
CODEX_CLI = ROOT / ".agent" / "workflows" / "codex-cli.md"
GUARDRAILS = ROOT / ".agent" / "rules" / "engineering_guardrails.md"


def _guardrails_82() -> str:
    """Slice §8.2 out of engineering_guardrails.md (the canon) so anchors elsewhere in
    the file cannot mask a missing §8.2 contract element."""
    text = GUARDRAILS.read_text(encoding="utf-8")
    start = text.index("### 8.2 External Tool Delegation Protocol")
    end = text.index("## 9.", start)
    return text[start:end]


# Doc key -> loader. Keys stay ASCII so pytest parametrize IDs are clean on Windows.
DOCS = {
    "claude-cli": lambda: CLAUDE_CLI.read_text(encoding="utf-8"),
    "codex-cli": lambda: CODEX_CLI.read_text(encoding="utf-8"),
    "guardrails-82": _guardrails_82,
}

# The four contract elements, as case-insensitive anchor substrings that MUST appear in
# every governing doc. Each maps back to an audit finding.
CONTRACT_ANCHORS = {
    "baseline-capture (F5)": "git status --porcelain",
    "abnormal-exit branch (F4)": "abnormal exit",
    "abnormal-exit reconciliation verb (F4)": "reconcil",
    "dirty-baseline no-whole-file-revert (F5)": "dirty at baseline",
    "requested-executor provenance (F6)": "requested executor",
    "actual-executor provenance (F6)": "actual executor",
}


@pytest.mark.docs_pin
@pytest.mark.parametrize("doc_key", list(DOCS))
def test_external_executor_contract_anchors_present(doc_key: str) -> None:
    """All three governing docs must carry all four contract elements."""
    text = DOCS[doc_key]().lower()
    for label, anchor in CONTRACT_ANCHORS.items():
        assert anchor in text, (
            f"{doc_key} is missing external-executor contract element '{label}' "
            f"(anchor {anchor!r}) — F4/F5/F6 regression (2026-07-11 audit)."
        )


@pytest.mark.docs_pin
def test_codex_cli_has_no_unconditional_whole_file_revert() -> None:
    """F5 regression guard: the old blanket `Auto-revert via git checkout -- <file>`
    recommendation destroys pre-existing dirty work — it must never come back."""
    text = CODEX_CLI.read_text(encoding="utf-8")
    assert "Auto-revert via" not in text, (
        "codex-cli.md must not prescribe an unconditional whole-file revert "
        "(`Auto-revert via git checkout -- <file>`) — it erases user work that was dirty "
        "at baseline (F5). Use a dirty-baseline-guarded surgical revert instead."
    )


@pytest.mark.docs_pin
def test_abnormal_exit_blocks_retry_in_cli_workflows() -> None:
    """F4: both CLI workflows must block retries on abnormal exit — not merely name it."""
    for name, path in (("claude-cli.md", CLAUDE_CLI), ("codex-cli.md", CODEX_CLI)):
        text = path.read_text(encoding="utf-8").lower()
        assert "abnormal exit" in text and "do not retry" in text, (
            f"{name} must document 'do not retry' on abnormal exit (F4 retry-blocking)."
        )


@pytest.mark.docs_pin
def test_explicit_executor_request_discloses_fallback() -> None:
    """F6: an explicitly requested executor that falls back must DISCLOSE/SURFACE the
    substitution — never a silent swap."""
    for name, path in (("claude-cli.md", CLAUDE_CLI), ("codex-cli.md", CODEX_CLI)):
        text = path.read_text(encoding="utf-8").lower()
        assert "disclose" in text or "surface" in text, (
            f"{name} must require disclosing/surfacing an explicit-request fallback (F6)."
        )
    assert "disclose" in _guardrails_82().lower(), (
        "engineering_guardrails.md §8.2 must require fallback disclosure for explicit "
        "executor requests (F6 canon)."
    )


@pytest.mark.docs_pin
def test_guardrails_records_requested_executor_before_availability_probe() -> None:
    """F6 ordering canon: §8.2 records `Requested Executor` BEFORE probing availability
    (the ordering the audit found reversed in claude-cli.md)."""
    g = _guardrails_82().lower()
    assert g.index("requested executor") < g.index("availability"), (
        "§8.2 must record `Requested Executor` before the availability probe (F6 ordering)."
    )
