"""Regression tests for #288 — Work Log enforcement audit (two WARN-tier checks).

Two governance MUSTs previously relied on agent self-attestation with no machine
enforcement; #288 adds artifact-presence audits in BOTH validators (bash↔ps1):

- Gap 1: `security_guardrails.md` §Work Log requires security findings under a
  `## Security Findings` heading. Feature-tier logs (feature/architecture-change/
  hotfix) carrying a review or ship receipt now WARN if the heading is absent.
- Gap 2: `engineering_guardrails.md` bootstrap MUST echo a `Guardrails loaded:`
  receipt in `## Session Info`. The CURRENT-branch, non-tiny-fix log now WARNs if
  the receipt line is absent. Scoped to the current branch (mirrors the AC-6
  `is_current_branch` gate) so historical logs that predate the convention do not
  flood WARNs.

Both are WARN-tier (presence, not proof) with no gate-logic change.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (c for c in bash_candidates if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")
powershell = shutil.which("pwsh") or shutil.which("powershell")
requires_powershell = pytest.mark.skipif(powershell is None, reason="PowerShell not available")
requires_windows = pytest.mark.skipif(
    sys.platform != "win32",
    reason="validate.ps1 is the native Windows validator; running it under Linux "
    "pwsh mis-resolves $root.",
)

SECURITY_WARN = "missing ## Security Findings section"
GUARDRAILS_WARN = "missing 'Guardrails loaded:' receipt"


def _run_validate(cwd: Path) -> str:
    proc = subprocess.run(
        [bash, str(cwd / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _run_validate_ps1(cwd: Path) -> str:
    proc = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(cwd / ".agentcortex" / "bin" / "validate.ps1")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _deploy(td: Path) -> Path:
    target = td / "proj"
    target.mkdir()
    res = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    assert res.returncode == 0, f"deploy failed:\n{res.stderr}"
    return target


def _deploy_with_git_branch(td: Path, branch: str) -> Path:
    """Deploy + git-init with a named branch so the validator sees a current branch."""
    target = _deploy(td)
    res = subprocess.run(
        ["git", "init", "-b", branch, str(target)],
        capture_output=True, text=True, encoding="utf-8",
    )
    if res.returncode != 0:
        subprocess.run(["git", "init", str(target)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(target), "symbolic-ref", "HEAD", f"refs/heads/{branch}"],
            check=True, capture_output=True,
        )
    else:
        verify = subprocess.run(
            ["git", "-C", str(target), "symbolic-ref", "--short", "HEAD"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if verify.returncode != 0 or verify.stdout.strip() != branch:
            subprocess.run(
                ["git", "-C", str(target), "symbolic-ref", "HEAD", f"refs/heads/{branch}"],
                check=True, capture_output=True,
            )
    return target


def _write_worklog(
    target: Path,
    name: str,
    *,
    classification: str,
    phase: str,
    gates: tuple[str, ...],
    security_findings: bool = True,
    guardrails_receipt: bool = True,
) -> None:
    work_dir = target / ".agentcortex" / "context" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    gate_lines = "\n".join(
        f"- Gate: {g} | Verdict: PASS | Classification: {classification} | Timestamp: 2026-07-13T00:00:00Z"
        for g in gates
    )
    session_info = (
        "- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core)\n"
        if guardrails_receipt else "- Session started.\n"
    )
    sec_section = "\n## Security Findings\n\nnone\n\n---\n" if security_findings else ""
    (work_dir / name).write_text(
        f"""# Work Log: {name}

## Header

- Branch: `test/{name}`
- Classification: `{classification}`
- Current Phase: `{phase}`
- Checkpoint SHA: `0000000000000000000000000000000000000000`

---

## Session Info

{session_info}
---

## Phase Summary

Enforcement-audit fixture. ACX

---

## Gate Evidence

{gate_lines}

---
{sec_section}
## Drift Log

- ADR Coverage Check: test fixture.

---

## Resume

none

---

## Evidence

- Fixture evidence.
""",
        encoding="utf-8", newline="\n",
    )


# ---------------------------------------------------------------------------
# Structural — deterministic, no subprocess (all platforms).
# ---------------------------------------------------------------------------

def test_288_security_findings_check_parity() -> None:
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert "## Security Findings" in sh and SECURITY_WARN in sh, "validate.sh missing #288 Security Findings audit"
    assert "## Security Findings" in ps1 and SECURITY_WARN in ps1, "validate.ps1 missing #288 Security Findings audit (parity)"


def test_288_guardrails_receipt_check_parity() -> None:
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert "Guardrails loaded:" in sh and GUARDRAILS_WARN in sh, "validate.sh missing #288 Loaded-Sections receipt audit"
    assert "Guardrails loaded:" in ps1 and GUARDRAILS_WARN in ps1, "validate.ps1 missing #288 Loaded-Sections receipt audit (parity)"


def test_288_marker_present_in_both() -> None:
    assert "(#288)" in VALIDATE_SH.read_text(encoding="utf-8")
    assert "(#288)" in VALIDATE_PS1.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Behavioral — Gap 1 (Security Findings). No git needed (historical logs).
# ---------------------------------------------------------------------------

@pytest.mark.slow
@requires_bash
def test_288_feature_at_ship_without_security_findings_warns_sh(tmp_path: Path) -> None:
    target = _deploy(tmp_path)
    _write_worklog(
        target, "feat-no-secfindings.md",
        classification="feature", phase="ship",
        gates=("bootstrap", "plan", "implement", "review", "test", "ship"),
        security_findings=False,
    )
    out = _run_validate(target)
    assert SECURITY_WARN in out, f"feature log at ship without ## Security Findings must WARN (#288):\n{out[-800:]}"


@pytest.mark.slow
@requires_bash
def test_288_feature_at_ship_with_security_findings_no_warn_sh(tmp_path: Path) -> None:
    target = _deploy(tmp_path)
    _write_worklog(
        target, "feat-with-secfindings.md",
        classification="feature", phase="ship",
        gates=("bootstrap", "plan", "implement", "review", "test", "ship"),
        security_findings=True,
    )
    out = _run_validate(target)
    assert SECURITY_WARN not in out, f"feature log WITH ## Security Findings must not WARN (#288):\n{out[-800:]}"


@pytest.mark.slow
@requires_bash
def test_288_quickwin_without_security_findings_no_warn_sh(tmp_path: Path) -> None:
    """Gap 1 is scoped to feature-tier — a quick-win log without Security Findings
    must NOT WARN (the security scan is not auto-enforced for quick-win)."""
    target = _deploy(tmp_path)
    _write_worklog(
        target, "quickwin-no-secfindings.md",
        classification="quick-win", phase="ship",
        gates=("bootstrap", "plan", "implement", "ship"),
        security_findings=False,
    )
    out = _run_validate(target)
    assert SECURITY_WARN not in out, f"quick-win must be exempt from the Security Findings audit (#288):\n{out[-800:]}"


# ---------------------------------------------------------------------------
# Behavioral — Gap 2 (Loaded-Sections receipt). Needs a current-branch git fixture.
# ---------------------------------------------------------------------------

@pytest.mark.slow
@requires_bash
def test_288_current_branch_without_guardrails_receipt_warns_sh(tmp_path: Path) -> None:
    branch = "feat/gap2-test"
    target = _deploy_with_git_branch(tmp_path, branch)
    _write_worklog(
        target, "feat-gap2-test.md",  # slash→dash worklog key of the current branch
        classification="feature", phase="implement",
        gates=("bootstrap", "plan", "implement"),
        guardrails_receipt=False,
    )
    out = _run_validate(target)
    assert GUARDRAILS_WARN in out, (
        f"current-branch log without 'Guardrails loaded:' receipt must WARN (#288):\n{out[-800:]}"
    )


@pytest.mark.slow
@requires_bash
def test_288_current_branch_with_guardrails_receipt_no_warn_sh(tmp_path: Path) -> None:
    branch = "feat/gap2-test"
    target = _deploy_with_git_branch(tmp_path, branch)
    _write_worklog(
        target, "feat-gap2-test.md",
        classification="feature", phase="implement",
        gates=("bootstrap", "plan", "implement"),
        guardrails_receipt=True,
    )
    out = _run_validate(target)
    assert GUARDRAILS_WARN not in out, (
        f"current-branch log WITH 'Guardrails loaded:' receipt must not WARN (#288):\n{out[-800:]}"
    )


@pytest.mark.slow
@requires_bash
def test_288_quickwin_without_guardrails_receipt_no_warn_sh(tmp_path: Path) -> None:
    """Gap 2 is scoped to Full-Mode tiers (feature/architecture-change/hotfix):
    quick-win runs Quick Mode and never loads Full-Mode guardrails, so a
    current-branch quick-win log without the receipt must NOT WARN."""
    branch = "fix/gap2-quickwin"
    target = _deploy_with_git_branch(tmp_path, branch)
    _write_worklog(
        target, "fix-gap2-quickwin.md",
        classification="quick-win", phase="implement",
        gates=("bootstrap", "plan", "implement"),
        guardrails_receipt=False,
    )
    out = _run_validate(target)
    assert GUARDRAILS_WARN not in out, (
        f"quick-win (Quick Mode) must be exempt from the Guardrails-loaded receipt audit (#288):\n{out[-800:]}"
    )


@pytest.mark.slow
@requires_bash
def test_288_historical_log_without_guardrails_receipt_no_warn_sh(tmp_path: Path) -> None:
    """No git repo → no current-branch log → Gap 2 must NOT fire (historical logs
    predate the receipt convention and must not flood WARNs)."""
    target = _deploy(tmp_path)
    _write_worklog(
        target, "old-feature.md",
        classification="feature", phase="ship",
        gates=("bootstrap", "plan", "implement", "review", "test", "ship"),
        guardrails_receipt=False,
    )
    out = _run_validate(target)
    assert GUARDRAILS_WARN not in out, (
        f"historical (non-current-branch) log must be exempt from the receipt audit (#288):\n{out[-800:]}"
    )


# ---------------------------------------------------------------------------
# Behavioral parity — validate.ps1 (Windows only).
# ---------------------------------------------------------------------------

@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_288_feature_at_ship_without_security_findings_warns_ps1(tmp_path: Path) -> None:
    target = _deploy(tmp_path)
    _write_worklog(
        target, "feat-no-secfindings.md",
        classification="feature", phase="ship",
        gates=("bootstrap", "plan", "implement", "review", "test", "ship"),
        security_findings=False,
    )
    out = _run_validate_ps1(target)
    assert SECURITY_WARN in out, f"[ps1] feature at ship without ## Security Findings must WARN (#288):\n{out[-800:]}"


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_288_current_branch_without_guardrails_receipt_warns_ps1(tmp_path: Path) -> None:
    branch = "feat/gap2-test"
    target = _deploy_with_git_branch(tmp_path, branch)
    _write_worklog(
        target, "feat-gap2-test.md",
        classification="feature", phase="implement",
        gates=("bootstrap", "plan", "implement"),
        guardrails_receipt=False,
    )
    out = _run_validate_ps1(target)
    assert GUARDRAILS_WARN in out, (
        f"[ps1] current-branch log without 'Guardrails loaded:' receipt must WARN (#288):\n{out[-800:]}"
    )
