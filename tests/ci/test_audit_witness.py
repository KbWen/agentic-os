"""Structural + parity tests for the INDEX.jsonl git append-only witness.

Spec: docs/specs/audit-chain-tamper-evidence.md (AC-4/5/6).
ADR-003 amendment. The witness itself is shell/PowerShell-native (zero-python
downstream), so behavioral verification is by documented sim (Work Log Evidence);
these tests guard against deletion and cross-platform parity DRIFT — the failure
mode that let the original tail-truncation gap ship unnoticed.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"


def _sh() -> str:
    return VALIDATE_SH.read_text(encoding="utf-8")


def _ps1() -> str:
    return VALIDATE_PS1.read_text(encoding="utf-8")


# --- presence (AC-4): the witness exists in both validators ---

def test_witness_present_in_bash() -> None:
    s = _sh()
    assert "append-only witness" in s
    assert "merge-base origin/main HEAD" in s


def test_witness_present_in_powershell() -> None:
    s = _ps1()
    assert "append-only witness" in s
    assert "merge-base origin/main HEAD" in s


# --- AC-5: degrades to WARN (never silent PASS) on missing preconditions ---

def test_bash_witness_warn_degradation_paths() -> None:
    s = _sh()
    # git absent, no merge-base, baseline absent → all WARN, none silent.
    assert "git unavailable or not a git repo" in s
    assert "no merge-base with origin/main" in s
    assert "not present at merge-base" in s


def test_powershell_witness_warn_degradation_paths() -> None:
    s = _ps1()
    assert "git unavailable or not a git repo" in s
    assert "no merge-base with origin/main" in s
    assert "not present at merge-base" in s


# --- AC-4: the two FAIL verdicts (truncation + edited-published-entry) exist ---

def test_bash_witness_fail_verdicts() -> None:
    s = _sh()
    assert "tail-truncation?" in s
    assert "is not a prefix of local" in s


def test_powershell_witness_fail_verdicts() -> None:
    s = _ps1()
    assert "tail-truncation?" in s
    assert "is not a prefix of local" in s


# --- Windows CRLF-safety regression (the bug found during implementation) ---

def test_bash_witness_normalizes_cr() -> None:
    """The bash diff MUST strip CR; working copy is CRLF on Windows while
    `git show` emits LF, so an un-normalized diff false-FAILs every line."""
    s = _sh()
    assert "tr -d '\\r'" in s


def test_witness_blank_line_parity() -> None:
    """Both validators MUST drop blank lines before comparing, or a stray blank
    line would make bash and PowerShell disagree (spec AC-6 parity). bash uses
    `grep '.'` / `grep -c '.'`; PowerShell uses Where-Object { $_ -ne '' }."""
    s, p = _sh(), _ps1()
    assert "grep -c '.'" in s and "grep '.'" in s
    assert "-ne ''" in p


# --- AC-6: cross-platform parity — same verdict messages in both validators ---

def test_witness_verdict_parity() -> None:
    s, p = _sh(), _ps1()
    shared_verdicts = [
        "git unavailable or not a git repo",
        "no merge-base with origin/main",
        "not present at merge-base",
        "tail-truncation?",
        "is not a prefix of local",
        "append-only invariant holds",
    ]
    for v in shared_verdicts:
        assert v in s, f"bash validator missing witness verdict: {v!r}"
        assert v in p, f"powershell validator missing witness verdict: {v!r}"
