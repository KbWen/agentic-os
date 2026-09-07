"""End-to-end pre-commit hook credential simulation + python/no-python COMPARISON.

ADR-008 AC-S4 / AC-X5. Installs the opt-in hook in a throwaway repo and proves a staged
fake secret is BLOCKED on BOTH delivery paths — the Python path (scan_credentials.py)
AND the no-Python path (credential_floor.sh) — with the value never leaked, while a
benign commit passes. This is the "block before object history" guarantee restored on
hosts without Python (the verified dead-control fix).

Two further arms cover the states between "python works" and "python is absent", both
of which used to let the commit through with the floor never consulted:
  * a python that EXISTS on PATH but cannot start (the WindowsApps App-Execution-Alias
    stub -- the condition backlog #144 fixed in both validators but not in this hook);
  * a startable python whose scanner run fails (`scan_credentials.py` rc==3).
ADR-008 / AC-S4 makes the regex floor the canonical control, so neither state may end
in an unscanned commit.

git fires hooks with its own bundled bash, so no WSL-stub dance is needed here.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".githooks" / "pre-commit.guard-ssot.sample"
SCANNER = ROOT / ".agentcortex" / "tools" / "scan_credentials.py"
FLOOR = ROOT / ".agentcortex" / "tools" / "credential_floor.sh"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git required")

FAKE = "AKIA" + "IOSFODNN7" + "EXAMPLE"   # AKIA + 16, built by concat
# Discriminators: which control spoke, and whether the fallback branch was taken.
FLOOR_MSG = "ACX credential floor:"
FALLBACK = "falling back to the no-python floor"


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


def _shim(shim_dir: Path, body: str) -> Path:
    """POSIX `python`/`python3` shims in a fresh dir, returned for PATH prepending.

    Extensionless + shebang: git fires hooks through its own bundled bash on Windows
    too, so `command -v python` resolves these the same way on every platform.
    """
    shim_dir.mkdir(parents=True, exist_ok=True)
    for name in ("python", "python3"):
        p = shim_dir / name
        p.write_bytes(body.encode("utf-8"))
        os.chmod(p, 0o755)
    return shim_dir


def _path_with(shim_dir: Path) -> str:
    """Shim dir FIRST. A real python later on PATH is never reached: both the old
    existence check and the new probe stop at the first match for each name."""
    return str(shim_dir) + os.pathsep + os.environ.get("PATH", "")


def _stage_secret(repo):
    (repo / "leak.txt").write_text("token = " + FAKE + "\n", encoding="utf-8")
    _git(repo, "add", "leak.txt", check=True)


def test_hook_blocks_with_python(tmp_path):
    repo = _install(tmp_path)
    _stage_secret(repo)
    r = _git(repo, "commit", "-m", "x")
    assert r.returncode != 0, "python path: secret commit must be BLOCKED"
    out = r.stdout + r.stderr
    assert FAKE not in out, "value leaked into hook output"
    assert FALLBACK not in out, (
        "a real finding (rc=1) must not fall through to the floor -- that would "
        "double-report: " + out
    )
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


def test_hook_blocks_when_python_exists_but_cannot_start(tmp_path):
    """A python that resolves on PATH but exits nonzero must not shadow the floor.

    Pre-fix this selected the stub by existence alone, the scanner run returned a code
    that was neither 0 nor 1, and the hook printed "could not run ... continuing" --
    the commit landed with the floor never consulted.
    """
    repo = _install(tmp_path)
    _stage_secret(repo)
    shim = _shim(tmp_path.parent / "shim_stub", "#!/bin/sh\nexit 9\n")
    env = {**os.environ, "PATH": _path_with(shim)}
    r = _git(repo, "commit", "-m", "x", env=env)
    assert r.returncode != 0, (
        "non-startable python: secret commit must be BLOCKED by the floor, "
        f"got rc=0. output={r.stdout + r.stderr!r}"
    )
    out = r.stdout + r.stderr
    assert FAKE not in out, "value leaked into hook output"
    assert FLOOR_MSG in out, "the floor is what must have blocked it, not the scanner"
    assert FALLBACK not in out, (
        "the stub was SELECTED and only the fallback saved it -- the startability "
        "probe did not run: " + out
    )
    assert _git(repo, "rev-parse", "HEAD").returncode != 0, "no commit object may exist"


def test_hook_blocks_when_python_scanner_errors(tmp_path):
    """A startable python whose scanner run fails must fall through to the floor.

    `scan_credentials.py` returns 3 when the scan could not run (git/tooling failure).
    Pre-fix that landed in the `-ne 0` arm and continued unscanned; the floor is the
    canonical control (AC-S4) and has to get its turn.
    """
    repo = _install(tmp_path)
    _stage_secret(repo)
    real = Path(sys.executable).as_posix()
    shim = _shim(
        tmp_path.parent / "shim_scanfail",
        '#!/bin/sh\ncase "$*" in *scan_credentials.py*) exit 3 ;; esac\n'
        f'exec "{real}" "$@"\n',
    )
    env = {**os.environ, "PATH": _path_with(shim)}
    r = _git(repo, "commit", "-m", "x", env=env)
    assert r.returncode != 0, (
        "scanner execution error: secret commit must be BLOCKED by the floor, "
        f"got rc=0. output={r.stdout + r.stderr!r}"
    )
    out = r.stdout + r.stderr
    assert FAKE not in out, "value leaked into hook output"
    assert FALLBACK in out, "the scanner error must route to the floor: " + out
    assert FLOOR_MSG in out, "the floor is what must have blocked it"
    assert _git(repo, "rev-parse", "HEAD").returncode != 0, "no commit object may exist"


def test_hook_passes_benign_when_python_cannot_start(tmp_path):
    """The floor fallback must not turn a clean commit into a blocked one."""
    repo = _install(tmp_path)
    (repo / "ok.txt").write_text("just some normal text without secrets\n", encoding="utf-8")
    _git(repo, "add", "ok.txt", check=True)
    shim = _shim(tmp_path.parent / "shim_stub2", "#!/bin/sh\nexit 9\n")
    env = {**os.environ, "PATH": _path_with(shim)}
    r = _git(repo, "commit", "-m", "ok", env=env)
    assert r.returncode == 0, f"benign commit must PASS: {r.stdout + r.stderr!r}"


def test_hook_passes_benign_when_scanner_errors(tmp_path):
    """The fallback must not turn a clean commit into a blocked one.

    Without this the suite cannot tell 'the fallback blocks correctly' from 'the
    fallback blocks always' -- a hook whose fallback hardcoded rc=1 would pass
    every other test in this file."""
    repo = _install(tmp_path)
    (repo / "ok.txt").write_text("just some normal text without secrets\n", encoding="utf-8")
    _git(repo, "add", "ok.txt", check=True)
    real = Path(sys.executable).as_posix()
    shim = _shim(
        tmp_path.parent / "shim_scanfail_benign",
        '#!/bin/sh\ncase "$*" in *scan_credentials.py*) exit 3 ;; esac\n'
        f'exec "{real}" "$@"\n',
    )
    env = {**os.environ, "PATH": _path_with(shim)}
    r = _git(repo, "commit", "-m", "ok", env=env)
    out = r.stdout + r.stderr
    assert FALLBACK in out, "the fallback branch must actually have run: " + out
    assert r.returncode == 0, f"benign commit must PASS through the fallback: {out!r}"
    assert "REDUCED ASSURANCE" in out, (
        "a clean floor is NOT a clean full scan -- the floor screens 3 shapes and the "
        "scanner 7, so silence here reads as 'clean' and hides 4 shape families: " + out
    )


def test_hook_continues_when_scanner_errors_and_floor_absent(tmp_path):
    """With neither control usable the hook states reduced assurance and continues.

    Pins the `-f $CREDENTIAL_FLOOR` guard on the fallback and the message branch that
    must NOT blame a floor that was never consulted. Blocking here instead would make
    an opt-in hook unusable on a host that has no pre-screen at all."""
    repo = _install(tmp_path)
    (repo / ".agentcortex" / "tools" / "credential_floor.sh").unlink()
    _stage_secret(repo)
    real = Path(sys.executable).as_posix()
    shim = _shim(
        tmp_path.parent / "shim_scanfail_nofloor",
        '#!/bin/sh\ncase "$*" in *scan_credentials.py*) exit 3 ;; esac\n'
        f'exec "{real}" "$@"\n',
    )
    env = {**os.environ, "PATH": _path_with(shim)}
    r = _git(repo, "commit", "-m", "x", env=env)
    out = r.stdout + r.stderr
    assert FALLBACK not in out, "no floor on disk -- the fallback must be skipped: " + out
    assert "no-python floor was not available" in out, (
        "the message must say the floor was absent, not that it failed: " + out)
    assert FAKE not in out, "value leaked into hook output"
    assert r.returncode == 0, f"must continue, not block, with no pre-screen: {out!r}"
    assert _git(repo, "rev-parse", "HEAD").returncode == 0, "the commit must exist"
