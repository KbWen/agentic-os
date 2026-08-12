"""End-to-end pre-commit hook credential simulation + python/no-python COMPARISON.

ADR-008 AC-S4 / AC-X5. Installs the opt-in hook in a throwaway repo and proves a staged
fake secret is BLOCKED on BOTH delivery paths — the Python path (scan_credentials.py)
AND the no-Python path (credential_floor.sh) — with the value never leaked, while a
benign commit passes. This is the "block before object history" guarantee restored on
hosts without Python (the verified dead-control fix).

git fires hooks with its own bundled bash, so no WSL-stub dance is needed here.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".githooks" / "pre-commit.guard-ssot.sample"
SCANNER = ROOT / ".agentcortex" / "tools" / "scan_credentials.py"
FLOOR = ROOT / ".agentcortex" / "tools" / "credential_floor.sh"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git required")

FAKE = "AKIA" + "IOSFODNN7" + "EXAMPLE"   # AKIA + 16, built by concat


def _git(repo, *args, env=None, check=False):
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                          encoding="utf-8", errors="replace", env=env, check=check)


def _install(tmp_path):
    repo = tmp_path
    _git(repo, "init", "-q", check=True)
    _git(repo, "config", "user.email", "t@example.com", check=True)
    _git(repo, "config", "user.name", "t", check=True)
    tools = repo / ".agentcortex" / "tools"
    tools.mkdir(parents=True)
    shutil.copy(SCANNER, tools / "scan_credentials.py")
    shutil.copy(FLOOR, tools / "credential_floor.sh")
    # stub validator (the hook also runs validate.sh; keep it green so the credential
    # check determines the outcome, not a missing validator)
    binp = repo / ".agentcortex" / "bin"
    binp.mkdir(parents=True)
    (binp / "validate.sh").write_bytes(b"#!/usr/bin/env bash\nexit 0\n")
    hooks = repo / ".githooks"
    hooks.mkdir()
    shutil.copy(HOOK, hooks / "pre-commit")
    os.chmod(hooks / "pre-commit", 0o755)
    _git(repo, "config", "core.hooksPath", ".githooks", check=True)
    return repo


def _path_without_python():
    """A PATH with every dir that holds a python executable removed (no-python sim)."""
    kept = []
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if not p:
            continue
        if any((Path(p) / exe).exists() for exe in ("python.exe", "python3.exe", "python", "python3")):
            continue
        kept.append(p)
    return os.pathsep.join(kept)


def _stage_secret(repo):
    (repo / "leak.txt").write_text("token = " + FAKE + "\n", encoding="utf-8")
    _git(repo, "add", "leak.txt", check=True)


def test_hook_blocks_with_python(tmp_path):
    repo = _install(tmp_path)
    _stage_secret(repo)
    r = _git(repo, "commit", "-m", "x")
    assert r.returncode != 0, "python path: secret commit must be BLOCKED"
    assert FAKE not in (r.stdout + r.stderr), "value leaked into hook output"
    assert _git(repo, "rev-parse", "HEAD").returncode != 0, "no commit object may exist"


def test_hook_blocks_without_python_via_floor(tmp_path):
    repo = _install(tmp_path)
    _stage_secret(repo)
    env = {**os.environ, "PATH": _path_without_python()}
    # On systems where python shares a dir with git (e.g. /usr/bin on Linux CI),
    # stripping python's dir also removes git -> this simulation can't run cleanly.
    # The floor's no-python behavior is covered by test_credential_floor_shell.py.
    if shutil.which("git", path=env["PATH"]) is None:
        pytest.skip("git is co-located with python in PATH; no-python sim unavailable here")
    r = _git(repo, "commit", "-m", "x", env=env)
    assert r.returncode != 0, "no-python floor path: secret commit must be BLOCKED"
    assert FAKE not in (r.stdout + r.stderr), "value leaked into hook output"


def test_hook_passes_benign(tmp_path):
    repo = _install(tmp_path)
    (repo / "ok.txt").write_text("just some normal text without secrets\n", encoding="utf-8")
    _git(repo, "add", "ok.txt", check=True)
    r = _git(repo, "commit", "-m", "ok")
    assert r.returncode == 0, f"benign commit must PASS: {r.stdout + r.stderr!r}"
