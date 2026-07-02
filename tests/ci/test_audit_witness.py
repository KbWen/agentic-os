"""Structural + parity tests for the INDEX.jsonl git append-only witness.

Spec: docs/specs/audit-chain-tamper-evidence.md (AC-4/5/6).
ADR-003 amendment. The witness itself is shell/PowerShell-native (zero-python
downstream), so behavioral verification is by documented sim (Work Log Evidence);
these tests guard against deletion and cross-platform parity DRIFT — the failure
mode that let the original tail-truncation gap ship unnoticed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

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


# ---------------------------------------------------------------------------
# Behavioral (slow, subprocess) — the git append-only witness actually renders
# the right VERDICT for each input. The string-presence tests above only prove
# the verdicts exist in the source; these three drive validate.sh over a real
# fixture repo (deployed framework + git repo + origin/main baseline) and assert
# the correct witness line fires. Bash validator only — behavioral sh↔ps1 parity
# is a Windows concern already guarded structurally by test_witness_verdict_parity.
#
# Fixture shape (mirrors test_validator_false_positives.py deploy + git helpers):
#   1. deploy the framework into a temp dir (empty archive/, no INDEX.jsonl);
#   2. build archive/INDEX.jsonl with N hash-chained entries via
#      append_chain_entry.py, and create each referenced log file on disk so the
#      D4 "referenced logs missing" WARN stays quiet;
#   3. git init -b main + commit, clone --bare as origin, remote add + fetch so
#      `git merge-base origin/main HEAD` resolves — the witness's precondition.
# The committed INDEX.jsonl is the baseline; each test then mutates the working
# copy (uncommitted) and asserts the resulting verdict.
# ---------------------------------------------------------------------------

DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# bash discovery (mirror test_validator_false_positives.py — avoid the
# WindowsApps bash stub, which is not a real POSIX shell).
_git_path = shutil.which("git")
_git_root = Path(_git_path).parent.parent if _git_path else None
_bash_candidates = [
    str(_git_root / "bin" / "bash.exe") if _git_root else None,
    str(_git_root / "usr" / "bin" / "bash.exe") if _git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (c for c in _bash_candidates if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")

# Witness verdict substrings — the same literals the string-presence tests pin.
WITNESS_PASS = "append-only invariant holds"
WITNESS_FAIL_TRUNCATION = "fewer than baseline"
WITNESS_FAIL_EDIT = "is not a prefix of local"

_ENTRY_TEMPLATE = (
    '{{"log": "{log}", "branch": "t", "classification": "quick-win", '
    '"shipped": "2026-07-02"}}'
)


def _run_validate(cwd: Path) -> str:
    proc = subprocess.run(
        [bash, str(cwd / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _witness_line(output: str) -> str:
    """Return only the witness verdict line, so assertions never trip over an
    unrelated line elsewhere in the (large) validator output."""
    for line in output.splitlines():
        if "append-only witness" in line:
            return line
    return ""


def _append_entry(target: Path, log_name: str) -> None:
    """Append one hash-chained INDEX.jsonl entry (prev_sha computed by the
    helper) and create the referenced log file on disk (quiets D4)."""
    idx = target / ".agentcortex" / "context" / "archive" / "INDEX.jsonl"
    proc = subprocess.run(
        [sys.executable,
         str(target / ".agentcortex" / "tools" / "append_chain_entry.py"),
         "append", "--path", str(idx),
         "--entry", _ENTRY_TEMPLATE.format(log=log_name)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, f"append_chain_entry failed:\n{proc.stderr}"
    (idx.parent / log_name).write_text(
        f"# archived log {log_name}\n", encoding="utf-8", newline="\n"
    )


def _build_witness_fixture(td: Path) -> Path:
    """Deploy the framework, seed a valid 3-entry chained INDEX.jsonl, and make
    it a git repo with a committed origin/main baseline (so the witness's
    merge-base precondition holds). Returns the deployed target dir."""
    target = td / "proj"
    target.mkdir()
    deployed = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert deployed.returncode == 0, f"deploy failed:\n{deployed.stderr}"

    for name in ("a.md", "b.md", "c.md"):
        _append_entry(target, name)

    # git repo + committed baseline reachable as origin/main.
    def _git(*args: str) -> subprocess.CompletedProcess:
        p = subprocess.run(
            ["git", "-C", str(target), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert p.returncode == 0, f"git {' '.join(args)} failed:\n{p.stderr}"
        return p

    _git("init", "-b", "main")
    _git("config", "user.email", "witness-fixture@example.com")
    _git("config", "user.name", "Witness Fixture")
    _git("add", "-A")
    _git("commit", "-q", "-m", "seed INDEX.jsonl baseline")

    origin = td / "origin.git"
    clone = subprocess.run(
        ["git", "clone", "--bare", "-q", str(target), str(origin)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert clone.returncode == 0, f"bare clone failed:\n{clone.stderr}"
    _git("remote", "add", "origin", str(origin))
    _git("fetch", "-q", "origin")

    # Precondition the witness depends on: merge-base must resolve.
    mb = _git("merge-base", "origin/main", "HEAD")
    assert mb.stdout.strip(), "fixture: git merge-base origin/main HEAD did not resolve"
    return target


@pytest.mark.slow
@requires_bash
def test_witness_pass_on_pure_append() -> None:
    """Appending one MORE chained entry (uncommitted) keeps the committed baseline
    a prefix of the working copy → PASS. Neither FAIL verdict may appear."""
    with tempfile.TemporaryDirectory() as td:
        target = _build_witness_fixture(Path(td))
        _append_entry(target, "d.md")  # pure append, uncommitted

        line = _witness_line(_run_validate(target))
        assert WITNESS_PASS in line, f"expected PASS witness verdict; got: {line!r}"
        assert WITNESS_FAIL_TRUNCATION not in line, f"unexpected truncation FAIL: {line!r}"
        assert WITNESS_FAIL_EDIT not in line, f"unexpected prefix FAIL: {line!r}"


@pytest.mark.slow
@requires_bash
def test_witness_fails_on_tail_truncation() -> None:
    """Deleting the LAST line of INDEX.jsonl (uncommitted) makes the local copy
    have fewer entries than the committed baseline → FAIL 'fewer than baseline'."""
    with tempfile.TemporaryDirectory() as td:
        target = _build_witness_fixture(Path(td))
        idx = target / ".agentcortex" / "context" / "archive" / "INDEX.jsonl"
        lines = idx.read_text(encoding="utf-8").splitlines(keepends=True)
        idx.write_text("".join(lines[:-1]), encoding="utf-8", newline="")

        line = _witness_line(_run_validate(target))
        assert WITNESS_FAIL_TRUNCATION in line, (
            f"expected tail-truncation FAIL verdict; got: {line!r}"
        )


@pytest.mark.slow
@requires_bash
def test_witness_fails_on_published_entry_edit() -> None:
    """Editing a field inside the FIRST (published) line, keeping the line count
    identical, makes the committed baseline no longer a prefix of local → FAIL
    'is not a prefix of local'."""
    with tempfile.TemporaryDirectory() as td:
        target = _build_witness_fixture(Path(td))
        idx = target / ".agentcortex" / "context" / "archive" / "INDEX.jsonl"
        lines = idx.read_text(encoding="utf-8").splitlines(keepends=True)
        assert '"branch": "t"' in lines[0], (
            f"fixture precondition: first entry should carry branch 't'; got {lines[0]!r}"
        )
        lines[0] = lines[0].replace('"branch": "t"', '"branch": "EDITED"')
        idx.write_text("".join(lines), encoding="utf-8", newline="")

        line = _witness_line(_run_validate(target))
        assert WITNESS_FAIL_EDIT in line, (
            f"expected published-entry-edit FAIL verdict; got: {line!r}"
        )
