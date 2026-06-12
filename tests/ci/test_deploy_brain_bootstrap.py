"""deploy_brain.sh bootstrap cache-trust tests.

Downstream incident (agent-virtual-office, 2026-06-11): the .agentcortex-src
cache had been cloned from a pre-migration repo; the bootstrap path did
`if cache exists -> git pull` without checking the cache's origin URL against
the manifest's source_repo, and nearly deployed 457 commits of the wrong repo.

These tests shell out to the real installers/deploy_brain.sh (fidelity by
design, matching test_deploy_tiering.py) against tiny local git repos:
  - a cache whose origin does NOT match the resolved source is re-cloned
  - a matching cache takes the normal pull path (no spurious re-clone)
  - trailing-slash / .git URL variants are normalized, not treated as mismatch
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_BRAIN_SH = ROOT / "installers" / "deploy_brain.sh"

git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (
        candidate for candidate in bash_candidates
        if candidate and "WindowsApps" not in candidate and Path(candidate).exists()
    ),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")
requires_git = pytest.mark.skipif(git_path is None, reason="git not available")

STUB_MARKER = "STUB DEPLOY OK"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@test", "-c", "user.name=test", *args],
        cwd=str(cwd), check=True, capture_output=True,
    )


def _make_source_repo(path: Path, marker: str) -> str:
    """Create a minimal Agentic OS 'source repo' whose canonical deploy.sh is a stub.

    Returns the URL form (posix path) used for both cloning and the manifest.
    """
    canonical = path / ".agentcortex" / "bin"
    canonical.mkdir(parents=True)
    (canonical / "deploy.sh").write_text(
        f'#!/usr/bin/env bash\necho "{marker}"\n', encoding="utf-8", newline="\n"
    )
    _git("init", "-b", "main", cwd=path)
    _git("add", "-A", cwd=path)
    _git("commit", "-m", "stub source", cwd=path)
    return path.as_posix()


def _make_project(path: Path, source_url: str) -> Path:
    """Create an 'installed downstream project': installers/ + manifest."""
    installers = path / "installers"
    installers.mkdir(parents=True)
    shutil.copy2(DEPLOY_BRAIN_SH, installers / "deploy_brain.sh")
    (path / ".agentcortex-manifest").write_text(
        f"source_repo: {source_url}\n", encoding="utf-8", newline="\n"
    )
    return path


def _run_deploy_brain(project: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "ACX_SOURCE"}
    return subprocess.run(
        [bash, str(project / "installers" / "deploy_brain.sh"), "."],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(project), env=env,
    )


def _cache_origin(project: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(project / ".agentcortex-src"), "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


@requires_bash
@requires_git
def test_mismatched_cache_origin_is_recloned(tmp_path: Path) -> None:
    right = _make_source_repo(tmp_path / "right-repo", STUB_MARKER)
    wrong = _make_source_repo(tmp_path / "wrong-repo", "WRONG REPO DEPLOY")
    project = _make_project(tmp_path / "proj", right)
    # Pre-seed a stale cache cloned from the WRONG repo (the incident shape).
    _git("clone", wrong, str(project / ".agentcortex-src"), cwd=tmp_path)

    result = _run_deploy_brain(project)

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "does not match" in combined
    assert STUB_MARKER in combined, "must deploy from the configured source after re-clone"
    assert "WRONG REPO DEPLOY" not in combined, "must never deploy from the mismatched cache"
    assert _cache_origin(project) == right


@requires_bash
@requires_git
def test_matching_cache_origin_takes_pull_path(tmp_path: Path) -> None:
    right = _make_source_repo(tmp_path / "right-repo", STUB_MARKER)
    project = _make_project(tmp_path / "proj", right)
    _git("clone", right, str(project / ".agentcortex-src"), cwd=tmp_path)

    result = _run_deploy_brain(project)

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "Updating cached Agentic OS source" in combined
    assert "does not match" not in combined
    assert STUB_MARKER in combined


@requires_bash
@requires_git
def test_source_flag_overrides_manifest_for_origin_check(tmp_path: Path) -> None:
    """deploy_brain.ps1 -Source forwards --source; the origin check must honor it.

    Manifest and cache both point at the OLD repo; the user overrides with
    --source <new>. The origin check must compare against the override and
    re-clone — not happily pull the manifest-matching stale cache.
    """
    right = _make_source_repo(tmp_path / "right-repo", STUB_MARKER)
    wrong = _make_source_repo(tmp_path / "wrong-repo", "WRONG REPO DEPLOY")
    project = _make_project(tmp_path / "proj", wrong)  # manifest says WRONG
    _git("clone", wrong, str(project / ".agentcortex-src"), cwd=tmp_path)

    env = {k: v for k, v in os.environ.items() if k != "ACX_SOURCE"}
    result = subprocess.run(
        [bash, str(project / "installers" / "deploy_brain.sh"), "--source", right, "."],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(project), env=env,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "does not match" in combined
    assert STUB_MARKER in combined, "--source override must drive both check and deploy"
    assert "WRONG REPO DEPLOY" not in combined
    assert _cache_origin(project) == right


@requires_bash
@requires_git
def test_source_equals_flag_overrides_manifest_for_origin_check(tmp_path: Path) -> None:
    """The bash wrapper must honor deploy.sh's equivalent --source=<url> form.

    Otherwise direct bash users can still deploy from a stale cache while the
    canonical deploy.sh implementation would have used the override correctly.
    """
    right = _make_source_repo(tmp_path / "right-repo", STUB_MARKER)
    wrong = _make_source_repo(tmp_path / "wrong-repo", "WRONG REPO DEPLOY")
    project = _make_project(tmp_path / "proj", wrong)
    _git("clone", wrong, str(project / ".agentcortex-src"), cwd=tmp_path)

    env = {k: v for k, v in os.environ.items() if k != "ACX_SOURCE"}
    result = subprocess.run(
        [bash, str(project / "installers" / "deploy_brain.sh"), f"--source={right}", "."],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(project), env=env,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "does not match" in combined
    assert STUB_MARKER in combined, "--source=<url> must drive both check and deploy"
    assert "WRONG REPO DEPLOY" not in combined
    assert _cache_origin(project) == right


@requires_bash
@requires_git
def test_manifest_source_repo_preserves_spaces(tmp_path: Path) -> None:
    """source_repo can be a local path; spaces must not be truncated."""
    source = _make_source_repo(tmp_path / "source repo with spaces", STUB_MARKER)
    project = _make_project(tmp_path / "proj", source)

    result = _run_deploy_brain(project)

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert STUB_MARKER in combined
    assert _cache_origin(project) == source


@requires_bash
@requires_git
def test_origin_url_normalization_is_not_a_mismatch(tmp_path: Path) -> None:
    right = _make_source_repo(tmp_path / "right-repo", STUB_MARKER)
    project = _make_project(tmp_path / "proj", right)
    _git("clone", right, str(project / ".agentcortex-src"), cwd=tmp_path)
    # Same repo, trailing-slash URL variant: must compare equal, not re-clone.
    _git("remote", "set-url", "origin", right + "/", cwd=project / ".agentcortex-src")

    result = _run_deploy_brain(project)

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "does not match" not in combined
    assert STUB_MARKER in combined
