"""Guard tests for the AC-6 signal_tier frontmatter validator check.

Verifies that validate.sh and validate.ps1 correctly WARN when a governance
spec is missing signal_tier, and do NOT warn when the field is present (any
value) or when the spec is grandfathered (created < 2026-06-10).

Modelled exactly on tests/ci/test_validator_false_positives.py — same
bash_candidates/requires_bash/requires_powershell pattern; validators run
from repo ROOT with temp fixture files added then removed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Every test here shells out to real deploy.sh/validate.sh (fidelity by design).
pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# bash discovery (mirror test_validator_false_positives.py).
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
requires_powershell = pytest.mark.skipif(
    powershell is None, reason="PowerShell not available"
)
# validate.ps1 is the native Windows validator; running it under Linux pwsh
# mis-resolves $root (see test_validator_false_positives.py requires_windows —
# the Linux CI 'CI Structural Tests' job must NOT execute the native PS validator).
requires_windows = pytest.mark.skipif(
    sys.platform != "win32",
    reason="validate.ps1 parity is exercised on Windows only (Linux pwsh mis-resolves $root)",
)

# ---------------------------------------------------------------------------
# Fixture specs
# ---------------------------------------------------------------------------
# All written to an isolated deployed temp repo, never the source docs/specs/.
# Each is a plausible minimal spec with --- fences, title, status: draft.

_FIXTURES: dict[str, str] = {
    # Must WARN: primary_domain governance, created >= cutoff, no signal_tier.
    "zz-st-missing.md": (
        "---\n"
        "title: ZZ Signal Tier Missing Test Fixture\n"
        "status: draft\n"
        "primary_domain: governance\n"
        "created: 2026-06-15\n"
        "---\n\n"
        "# ZZ Signal Tier Missing\n\n"
        "Test fixture — must trigger WARN.\n\n"
        "## Domain Decisions\n\n"
        "- [DECISION] placeholder\n"
    ),
    # Must NOT warn: signal_tier: 2 present.
    "zz-st-tier2.md": (
        "---\n"
        "title: ZZ Signal Tier 2 Test Fixture\n"
        "status: draft\n"
        "primary_domain: governance\n"
        "created: 2026-06-15\n"
        "signal_tier: 2\n"
        "---\n\n"
        "# ZZ Signal Tier 2\n\n"
        "Test fixture — must NOT warn (tier declared).\n\n"
        "## Domain Decisions\n\n"
        "- [DECISION] placeholder\n"
    ),
    # Must NOT warn: signal_tier: none silences.
    "zz-st-none.md": (
        "---\n"
        "title: ZZ Signal Tier None Test Fixture\n"
        "status: draft\n"
        "primary_domain: governance\n"
        "created: 2026-06-15\n"
        "signal_tier: none\n"
        "---\n\n"
        "# ZZ Signal Tier None\n\n"
        "Test fixture — must NOT warn (signal_tier: none silences).\n\n"
        "## Domain Decisions\n\n"
        "- [DECISION] placeholder\n"
    ),
    # Must NOT warn: grandfathered (created < 2026-06-10).
    "zz-st-old.md": (
        "---\n"
        "title: ZZ Signal Tier Old Test Fixture\n"
        "status: draft\n"
        "primary_domain: governance\n"
        "created: 2026-01-01\n"
        "---\n\n"
        "# ZZ Signal Tier Old\n\n"
        "Test fixture — must NOT warn (grandfathered).\n\n"
        "## Domain Decisions\n\n"
        "- [DECISION] placeholder\n"
    ),
}

WARN_LINE = "governance spec missing signal_tier: zz-st-missing.md"
# Use a substring that avoids the multi-byte § character, which PowerShell may
# emit as replacement characters depending on console encoding.
WARN_SUMMARY = "governance specs missing signal_tier frontmatter"
SILENT_FILES = ["zz-st-tier2.md", "zz-st-none.md", "zz-st-old.md"]


def _make_validation_target(tmp_path: Path) -> Path:
    target = tmp_path / "proj"
    target.mkdir()
    proc = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"deploy failed:\n{proc.stdout}\n{proc.stderr}"
    return target


def _write_fixtures(spec_dir: Path) -> None:
    spec_dir.mkdir(parents=True, exist_ok=True)
    for name, content in _FIXTURES.items():
        (spec_dir / name).write_text(content, encoding="utf-8")


def _remove_fixtures(spec_dir: Path) -> None:
    for name in _FIXTURES:
        (spec_dir / name).unlink(missing_ok=True)


def _run_sh(cwd: Path) -> str:
    proc = subprocess.run(
        [bash, str(cwd / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _run_ps1(cwd: Path) -> str:
    proc = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cwd / ".agentcortex" / "bin" / "validate.ps1")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@requires_bash
def test_signal_tier_warn_bash(tmp_path: Path) -> None:
    """validate.sh: WARN names zz-st-missing.md; silent for tier/none/old."""
    target = _make_validation_target(tmp_path)
    spec_dir = target / "docs" / "specs"
    _write_fixtures(spec_dir)
    try:
        out = _run_sh(target)
    finally:
        _remove_fixtures(spec_dir)

    assert WARN_LINE in out, (
        f"Expected WARN line not found in validate.sh output.\n"
        f"Looking for: {WARN_LINE!r}\n"
        f"Output tail:\n{out[-600:]}"
    )
    assert WARN_SUMMARY in out, (
        f"Expected WARN summary not found.\nLooking for: {WARN_SUMMARY!r}"
    )
    for silent in SILENT_FILES:
        assert f"governance spec missing signal_tier: {silent}" not in out, (
            f"validate.sh must NOT warn for {silent} but it did."
        )


@requires_bash
@requires_powershell
@requires_windows
def test_signal_tier_warn_powershell(tmp_path: Path) -> None:
    """validate.ps1: same parity assertions as the bash test."""
    target = _make_validation_target(tmp_path)
    spec_dir = target / "docs" / "specs"
    _write_fixtures(spec_dir)
    try:
        out = _run_ps1(target)
    finally:
        _remove_fixtures(spec_dir)

    assert WARN_LINE in out, (
        f"Expected WARN line not found in validate.ps1 output.\n"
        f"Looking for: {WARN_LINE!r}\n"
        f"Output tail:\n{out[-600:]}"
    )
    assert WARN_SUMMARY in out, (
        f"Expected WARN summary not found.\nLooking for: {WARN_SUMMARY!r}"
    )
    for silent in SILENT_FILES:
        assert f"governance spec missing signal_tier: {silent}" not in out, (
            f"validate.ps1 must NOT warn for {silent} but it did."
        )
