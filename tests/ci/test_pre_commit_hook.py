"""Regression tests for the optional Agentic OS pre-commit hook sample.

spec_ref: docs/specs/pre-commit-local-validation.md
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HOOK_SAMPLE = ROOT / ".githooks" / "pre-commit.guard-ssot.sample"
README = ROOT / "README.md"

git = shutil.which("git")
git_root = Path(git).parent.parent if git else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (
        candidate
        for candidate in bash_candidates
        if candidate and "WindowsApps" not in candidate and Path(candidate).exists()
    ),
    None,
)
requires_git_bash = pytest.mark.skipif(
    git is None or bash is None,
    reason="git and bash are required for pre-commit hook tests",
)


def _make_repo(tmp_path: Path, validate_exit: int) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run([git, "init"], cwd=root, check=True, capture_output=True, text=True)

    hooks_dir = root / ".githooks"
    hooks_dir.mkdir()
    hook = hooks_dir / "pre-commit"
    hook.write_text(HOOK_SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    hook.chmod(hook.stat().st_mode | stat.S_IXUSR)

    validator_dir = root / ".agentcortex" / "bin"
    validator_dir.mkdir(parents=True)
    validator = validator_dir / "validate.sh"
    validator.write_text(
        "#!/usr/bin/env bash\n"
        "echo stub-validator\n"
        f"exit {validate_exit}\n",
        encoding="utf-8",
    )
    validator.chmod(validator.stat().st_mode | stat.S_IXUSR)
    return root


def _run_hook(repo: Path, cwd: Path | None = None, hook_path: str = ".githooks/pre-commit") -> subprocess.CompletedProcess:
    env = {**os.environ, "LC_ALL": "C.UTF-8"}
    return subprocess.run(
        [bash, hook_path],
        cwd=cwd or repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


@requires_git_bash
def test_ac1_pre_commit_hook_blocks_when_validator_fails(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, validate_exit=7)
    result = _run_hook(repo)

    assert result.returncode != 0
    assert "stub-validator" in result.stdout
    assert "validator failed" in result.stdout


@requires_git_bash
def test_ac1_pre_commit_hook_passes_when_validator_passes(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, validate_exit=0)
    result = _run_hook(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "validator passed" in result.stdout


@requires_git_bash
def test_ac1_pre_commit_hook_runs_from_subdirectory(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, validate_exit=0)
    nested = repo / "nested"
    nested.mkdir()

    result = _run_hook(repo, cwd=nested, hook_path="../.githooks/pre-commit")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "validator passed" in result.stdout


@requires_git_bash
def test_adversarial_missing_validator_blocks_commit(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, validate_exit=0)
    (repo / ".agentcortex" / "bin" / "validate.sh").unlink()

    result = _run_hook(repo)

    assert result.returncode != 0
    assert "missing .agentcortex/bin/validate.sh" in result.stdout


def test_ac2_hook_prefers_powershell_validator_on_windows() -> None:
    text = HOOK_SAMPLE.read_text(encoding="utf-8")

    assert "is_windows_git_shell" in text
    assert "validate.ps1" in text
    assert "validate.sh" in text


@requires_git_bash
def test_ac3_guard_receipt_warning_is_advisory_only(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, validate_exit=0)
    guarded_file = repo / "AGENTS.md"
    guarded_file.write_text("# local governance\n", encoding="utf-8")
    subprocess.run([git, "add", "AGENTS.md"], cwd=repo, check=True)

    result = _run_hook(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "GUARD WARN: AGENTS.md" in result.stdout


@pytest.mark.docs_pin
def test_ac4_ac5_readme_documents_pre_commit_hook_setup() -> None:
    # The pre-commit hook setup moved from the README to the dedicated install
    # guide (docs/INSTALL.md) when the README was slimmed to a landing page; the
    # README links to it. AC4/AC5 require the setup to be documented and
    # reachable, not that it live in the README file specifically.
    readme = README.read_text(encoding="utf-8")
    install = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")

    assert "docs/INSTALL.md" in readme
    assert "cp .githooks/pre-commit.guard-ssot.sample .githooks/pre-commit" in install
    assert "git config core.hooksPath .githooks" in install
    assert "Copy-Item .githooks\\pre-commit.guard-ssot.sample .githooks\\pre-commit" in install
