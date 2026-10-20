"""Brownfield deploy: say plainly when an entry file kept the project's own version.

When AGENTS.md / CLAUDE.md / GEMINI.md already exist, deploy keeps them and writes the
framework's version as <file>.acx-incoming (ADR-005). Until that is merged, agents load
none of the framework's rules, and validate fails on three checks whose names do not say
why. Deploy and both validators now name the cause (owner choice, 2026-10-20: diagnose,
do not modify the adopter's files).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
bash = next(
    (c for c in [
        str(git_root / "bin" / "bash.exe") if git_root else None,
        str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
        shutil.which("bash"),
    ] if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
powershell = shutil.which("pwsh") or shutil.which("powershell")
requires_bash = pytest.mark.skipif(bash is None or git_path is None, reason="bash/git not available")

NOTE = "NOTE: governance is not active:"
BANNER = "!! GOVERNANCE IS NOT ACTIVE YET:"


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")


def _project(tmp_path: Path, own_entries: tuple[str, ...]) -> Path:
    proj = tmp_path / "proj"
    proj.mkdir()
    _run(["git", "init", "-q"], proj)
    for name in own_entries:
        (proj / name).write_text(f"# project's own {name}\n", encoding="utf-8")
    return proj


@requires_bash
def test_brownfield_deploy_and_validators_name_the_unmerged_entry_files(tmp_path: Path) -> None:
    proj = _project(tmp_path, ("AGENTS.md", "CLAUDE.md"))
    deploy = _run([bash, str(DEPLOY_SH), str(proj)], tmp_path)
    assert deploy.returncode == 0, deploy.stderr[-2000:]
    assert f"{BANNER} AGENTS.md CLAUDE.md kept your own version." in deploy.stdout

    sh = _run([bash, str(proj / ".agentcortex" / "bin" / "validate.sh")], proj)
    assert f"{NOTE} AGENTS.md CLAUDE.md still hold your own version" in sh.stdout
    summary_sh = [l for l in sh.stdout.splitlines() if l.startswith("Summary:")]

    if powershell:
        ps = _run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(proj / ".agentcortex" / "bin" / "validate.ps1")], proj)
        assert f"{NOTE} AGENTS.md CLAUDE.md still hold your own version" in ps.stdout
        assert [l for l in ps.stdout.splitlines() if l.startswith("Summary:")] == summary_sh


@requires_bash
def test_clean_deploy_prints_no_governance_notice(tmp_path: Path) -> None:
    proj = _project(tmp_path, ())
    deploy = _run([bash, str(DEPLOY_SH), str(proj)], tmp_path)
    assert deploy.returncode == 0, deploy.stderr[-2000:]
    assert BANNER not in deploy.stdout
    sh = _run([bash, str(proj / ".agentcortex" / "bin" / "validate.sh")], proj)
    assert NOTE not in sh.stdout
