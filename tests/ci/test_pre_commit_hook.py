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
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"
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
    subprocess.run([git, "init"], cwd=root, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")

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


def _commit_all(repo: Path) -> None:
    subprocess.run([git, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "x"],
                   cwd=repo, check=True, capture_output=True)


@requires_git_bash
def test_ac3_guard_receipt_warning_is_advisory_only(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path, validate_exit=0)
    guarded_file = repo / "AGENTS.md"
    guarded_file.write_text("# local governance\n", encoding="utf-8")
    subprocess.run([git, "add", "AGENTS.md"], cwd=repo, check=True)

    # #211(c): adding the file is the install, not an SSoT edit that bypassed the guard.
    added = _run_hook(repo)
    assert added.returncode == 0, added.stdout + added.stderr
    assert "GUARD WARN" not in added.stdout

    _commit_all(repo)
    guarded_file.write_text("# local governance, edited\n", encoding="utf-8")
    subprocess.run([git, "add", "AGENTS.md"], cwd=repo, check=True)
    result = _run_hook(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "GUARD WARN: AGENTS.md" in result.stdout

    _commit_all(repo)
    subprocess.run([git, "rm", "-q", "AGENTS.md"], cwd=repo, check=True)
    (repo / ".agentcortex" / "context" / ".guard_receipts").mkdir(parents=True)  # reach the receipt lookup
    deleted = _run_hook(repo)
    assert "GUARD WARN: AGENTS.md" in deleted.stdout, "a deletion is an SSoT edit too"
    assert "No such file" not in deleted.stdout + deleted.stderr


@requires_git_bash
def test_hook_finds_a_framework_installed_in_a_monorepo_package(tmp_path: Path) -> None:
    """#208: with core.hooksPath pkg/.githooks, git runs the hook from the repository
    root. The hook used to cd there and block every commit on a missing validator."""
    outer = tmp_path / "mono"
    outer.mkdir()
    subprocess.run([git, "init", "-q"], cwd=outer, check=True)
    pkg = _make_repo(outer, validate_exit=0)  # creates mono/repo with .githooks + stub
    shutil.rmtree(pkg / ".git")  # a package directory, not a nested repository

    result = _run_hook(outer, hook_path=f"{pkg.name}/.githooks/pre-commit")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "stub-validator" in result.stdout and "validator passed" in result.stdout

    guarded = pkg / "AGENTS.md"
    guarded.write_text("# pkg governance\n", encoding="utf-8")
    subprocess.run([git, "add", "-A"], cwd=outer, check=True)
    _commit_all(outer)
    guarded.write_text("# pkg governance, edited\n", encoding="utf-8")
    subprocess.run([git, "add", "-A"], cwd=outer, check=True)
    edited = _run_hook(outer, hook_path=f"{pkg.name}/.githooks/pre-commit")
    assert "GUARD WARN: AGENTS.md" in edited.stdout, edited.stdout


@requires_git_bash
@pytest.mark.slow
def test_deploy_banner_gives_the_monorepo_hooks_path(tmp_path: Path) -> None:
    """#208: `git config core.hooksPath .githooks` is resolved from the repository root,
    so for a package inside a larger repository the banner names the path from there."""
    outer = tmp_path / "mono"
    (outer / "pkg").mkdir(parents=True)
    subprocess.run([git, "init", "-q"], cwd=outer, check=True)

    def deploy(target: Path) -> str:
        r = subprocess.run([bash, str(DEPLOY_SH), str(target)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        assert r.returncode == 0, r.stderr
        return r.stdout

    assert "git config core.hooksPath pkg/.githooks" in deploy(outer / "pkg")
    assert "sub-directory" not in deploy(outer), "a top-level install keeps the plain command"


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
