"""No-python credential FLOOR (credential_floor.sh) tests — ADR-008 AC-S4/S6.

The floor is a narrow FP-free SUBSET (AKIA / PEM / ghp_) for hosts WITHOUT Python:
it scans staged content and prints REDACTED `path:line: name`, exit 1 on hit / 0 clean
/ 3 on git failure. Fakes are built by concatenation so no full literal sits in the repo.
The floor is pure bash + grep — it never invokes Python (the no-python guarantee).
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FLOOR = ROOT / ".agentcortex" / "tools" / "credential_floor.sh"

# Resolve a REAL bash (Git Bash), excluding the WindowsApps WSL placeholder that
# emits a UTF-16 "install <Distro>" stub and never runs the script (per the
# [windows-install] lesson; mirrors tests/ci/test_deploy_tiering.py).
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
BASH = next(
    (c for c in bash_candidates if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
pytestmark = pytest.mark.skipif(BASH is None, reason="real bash (Git Bash) required for the shell floor")


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                   encoding="utf-8", errors="replace", check=True)


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def _run(cwd):
    return subprocess.run([BASH, str(FLOOR)], cwd=str(cwd), capture_output=True, encoding="utf-8", errors="replace")


_FAKES = {
    "aws-access-key-id": "AKIA" + "IOSFODNN7" + "EXAMPLE",   # AKIA + 16
    "pem-private-key": "-----BEGIN " + "RSA PRIVATE KEY" + "-----",
    "github-token": "ghp_" + "A" * 36,
}

# benign content that MUST stay clean — the exact near-miss shapes for these 3 patterns
_BENIGN = [
    "the AKIA prefix marks an AWS access key id",
    "ghp_short and github_pat_short are not real",
    "use sk-123 as a short placeholder",
    "https://github.com/KbWen/agentic-os",
    "git_sha da39a3ee5e6b4b0d3255bfef95601890afd80709",
    "class sk-loading-spinner-component {}",
]


def test_floor_catches_subset_redacted(tmp_path):
    repo = _repo(tmp_path)
    for name, fake in _FAKES.items():
        (repo / "f.txt").write_text("x = " + fake + "\n", encoding="utf-8")
        _git(repo, "add", "f.txt")
        r = _run(repo)
        assert r.returncode == 1, f"{name} not blocked (rc={r.returncode}, err={r.stderr!r})"
        assert name in r.stderr, f"{name} pattern-name missing from output"
        out = r.stdout + r.stderr
        assert not any(fake[i:i + 8] in out for i in range(len(fake) - 7)), \
            f"{name}: floor leaked >=8 chars of the value"
        _git(repo, "reset", "-q")


def test_floor_no_false_positive(tmp_path):
    repo = _repo(tmp_path)
    for i, benign in enumerate(_BENIGN):
        (repo / f"b{i}.txt").write_text(benign + "\n", encoding="utf-8")
    _git(repo, "add", ".")
    r = _run(repo)
    assert r.returncode == 0, f"false positive: {r.stderr!r}"


def test_floor_clean_repo_exits_0(tmp_path):
    repo = _repo(tmp_path)
    (repo / "ok.txt").write_text("just some normal text without secrets\n", encoding="utf-8")
    _git(repo, "add", ".")
    assert _run(repo).returncode == 0


def test_floor_allowlist_pragma(tmp_path):
    repo = _repo(tmp_path)
    fake = "AKIA" + "IOSFODNN7" + "EXAMPLE"
    (repo / "doc.md").write_text(f"example: {fake}  # pragma: allowlist secret\n", encoding="utf-8")
    _git(repo, "add", ".")
    assert _run(repo).returncode == 0, "allowlist pragma must suppress the hit"


def test_floor_git_failure_exits_3(tmp_path):
    """Not a git repo → fail-CLOSED exit 3 (never 0 'clean')."""
    r = subprocess.run([BASH, str(FLOOR)], cwd=str(tmp_path), capture_output=True, encoding="utf-8", errors="replace")
    assert r.returncode == 3

def _floor_patterns():
    """The floor's OWN patterns, parsed from its source.

    Never re-declare them here: a second matcher is the defect backlog #165 forbids
    and #150 records the cost of."""
    src = FLOOR.read_text(encoding="utf-8")
    block = re.search(r"PATTERNS='(.*?)'", src, re.S)
    assert block, "could not read PATTERNS out of credential_floor.sh"
    out = []
    for line in block.group(1).splitlines():
        if "|" in line:
            name, ere = line.split("|", 1)
            out.append((name.strip(), ere.strip()))
    return out


def test_repo_ships_no_shape_its_own_floor_would_block():
    """This module's docstring promises no full literal sits in the repo. Enforce it.

    That promise had no verifier, and it had already broken: `scan_credentials.py`
    carried AWS's canonical example key in the docstring that documents the allowlist
    escape hatch. Because the floor reads each WHOLE staged blob and has no
    self-exclusion, a no-Python adopter following the deploy banner's own
    `git add .agentcortex/ ...` had their FIRST framework commit blocked and was told
    to rotate a secret out of a core-tier file the framework had just force-written.
    The scanner passed the same staged set -- only the floor saw it."""
    patterns = _floor_patterns()
    assert patterns, "the floor declares no patterns -- parse failed"
    hits = []
    for name, ere in patterns:
        r = subprocess.run(
            ["git", "grep", "-nE", "-e", ere],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        for line in r.stdout.splitlines():
            if "pragma: allowlist secret" in line.lower():
                continue
            hits.append(name + " -> " + line[:160])
    assert not hits, (
        "tracked files carry a shape the floor blocks on; build it by concatenation "
        "or abbreviate the prose:" + chr(10) + chr(10).join(hits)
    )

def test_reduced_assurance_message_matches_the_real_pattern_counts():
    """The hook's REDUCED ASSURANCE line quotes two counts. Pin them to their sources.

    A quantified claim shipped in a file with no verifier decays silently -- the same
    advertised-but-unenforced defect this change was written to fix, so it applies to
    the fix too. Counts are read from the two tools; never re-declared here.
    """
    hook = (ROOT / ".githooks" / "pre-commit.guard-ssot.sample").read_text(encoding="utf-8")
    m = re.search(
        r"the floor screens (\d+) credential shapes, "
        r"the python scanner screens (\d+)", hook)
    assert m, "the REDUCED ASSURANCE line is gone or reworded -- update this pin"
    scanner = ROOT / ".agentcortex" / "tools" / "scan_credentials.py"
    spec = importlib.util.spec_from_file_location("scan_credentials_for_count", scanner)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    assert (int(m.group(1)), int(m.group(2))) == (
        len(_floor_patterns()), len(mod._PATTERNS)), (
        "the hook tells the developer how much assurance the fallback gives up; "
        "that number is now wrong"
    )
