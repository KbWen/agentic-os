"""`deploy.sh --dry-run` deletes and moves nothing (found by the #215 review, 2026-09-27).

On an update, the dry run deleted every pending `*.acx-incoming` sidecar before its
preview. On a legacy install, it ran the path migration (moves, `rm -rf`, `rm -f`) first.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
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


def _deploy(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [bash, str(DEPLOY_SH), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )


def _tree(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


@requires_bash
@pytest.mark.slow
def test_dry_run_leaves_pending_sidecars_and_legacy_paths_alone(tmp_path: Path) -> None:
    target = tmp_path / "product"
    target.mkdir()
    install = _deploy(str(target))
    assert install.returncode == 0, install.stderr[-2000:]

    # An offer the adopter has not merged yet, and a legacy path a real run would migrate:
    # it deletes docs/context/work (already at .agentcortex/context/work). tools/validate.sh
    # is the project's own file, which no run touches (#220).
    (target / "CLAUDE.md.acx-incoming").write_text("offered version\n", encoding="utf-8")
    (target / "tools").mkdir()
    (target / "tools" / "validate.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (target / "docs" / "context" / "work").mkdir(parents=True)
    (target / "docs" / "context" / "work" / "old.md").write_text("# old log\n", encoding="utf-8")
    before = _tree(target)

    dry = _deploy("--dry-run", str(target))
    assert dry.returncode == 0, dry.stderr[-2000:]
    after = _tree(target)
    assert after == before, (
        f"the dry run changed the target: removed {sorted(set(before) - set(after))}, "
        f"added {sorted(set(after) - set(before))}"
    )
    assert "[DRY RUN] Legacy paths found" in dry.stdout, dry.stdout[-1500:]


# --- Argument handling (2026-10-19): a flag deploy.sh did not know used to become the
# target path, so `deploy.sh --help` tried to deploy into a directory named "--help", and
# `deploy.ps1 --help` dropped the flag and deployed into '.'.

def _run_in(cwd: Path, *cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(cmd), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(cwd),
    )


@requires_bash
@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_help_prints_usage_and_deploys_nothing(tmp_path: Path, flag: str) -> None:
    result = _run_in(tmp_path, bash, str(DEPLOY_SH), flag)
    assert result.returncode == 0, result.stderr[-1000:]
    assert "Usage:" in result.stdout
    assert list(tmp_path.iterdir()) == [], "help must not write anything"


@requires_bash
def test_unknown_flag_is_rejected_not_used_as_target(tmp_path: Path) -> None:
    result = _run_in(tmp_path, bash, str(DEPLOY_SH), "--no-python")
    assert result.returncode == 2, result.stdout[-1000:]
    assert "Unknown option '--no-python'" in result.stderr
    assert list(tmp_path.iterdir()) == [], "an unknown flag must not become a target directory"


powershell = shutil.which("pwsh") or shutil.which("powershell")


@requires_bash
@pytest.mark.skipif(powershell is None, reason="PowerShell not available")
@pytest.mark.parametrize("args", [("--dry-run", "product"), ("product", "--dry-run")])
def test_deploy_ps1_forwards_flags_and_keeps_the_target(tmp_path: Path, args: tuple[str, str]) -> None:
    (tmp_path / "product").mkdir()
    ps1 = DEPLOY_SH.with_name("deploy.ps1")
    result = _run_in(
        tmp_path, powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), *args,
    )
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
    assert "[DRY RUN] Would deploy" in result.stdout, result.stdout[-1500:]
    assert " to product" in result.stdout, result.stdout[-1500:]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["product"]
    assert list((tmp_path / "product").iterdir()) == [], "a dry run writes nothing"


@requires_bash
@pytest.mark.skipif(powershell is None, reason="PowerShell not available")
def test_deploy_ps1_help_does_not_deploy_into_cwd(tmp_path: Path) -> None:
    ps1 = DEPLOY_SH.with_name("deploy.ps1")
    result = _run_in(tmp_path, powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), "--help")
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
    assert "Usage:" in result.stdout
    assert list(tmp_path.iterdir()) == [], "deploy.ps1 --help must not deploy into the current directory"
