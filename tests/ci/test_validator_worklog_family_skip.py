"""Backlog #149: the active work-log check family must announce its own absence.

Eighteen checks in both validators are each guarded by `worklog_count -gt 0` /
`$worklogs.Count -gt 0`. With no active work log every one of them emitted
NOTHING — not a SKIP line, absent from the run — while the summary still printed
"integrity check passed". Measured on one commit 2026-07-27: `pass=99 warn=3`
with no logs, `pass=117 warn=3` with one. A fresh clone or a downstream install
therefore ran ~18 fewer governance checks and was told everything passed.

`.agentcortex/context/work/` ships only a dotfile placeholder (`.gitkeep.md`),
which the `*.md` glob does not match, so "no active logs" is the DEFAULT state of
every new install — not an edge case.

These tests pin the family-level SKIP that closes it. The native emission is
recorded in tests/ci/validator_native_baseline.json under the ADR-006 escape
hatch (the run_python_check / Invoke-PythonCheck wrappers map exit!=0 -> FAIL and
cannot express SKIP).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# The one string both validators emit. Kept identical on purpose — a drift here
# is a parity bug, and the assertion below is what catches it.
SKIP_MARKER = "active work-log checks -- no active work logs"

bash = shutil.which("bash")
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")


# ---------------------------------------------------------------------------
# Structural — cross-platform, runs in the Linux CI job
# ---------------------------------------------------------------------------

def test_sh_emits_family_skip_guarded_by_zero_count() -> None:
    text = VALIDATE_SH.read_text(encoding="utf-8")
    assert SKIP_MARKER in text, (
        "validate.sh lost the active work-log family SKIP (backlog #149) — with no "
        "active logs the 18-check family goes silent again"
    )
    # The guard has to be the zero case. A `-gt 0` here would emit the SKIP on
    # every run that HAS logs, i.e. exactly backwards.
    guard = re.search(
        r'if \[\[ "\$worklog_count" -eq 0 \]\]; then\s*\n\s*record_result SKIP',
        text,
    )
    assert guard, "validate.sh family SKIP must be guarded by `worklog_count -eq 0`"


def test_ps1_emits_family_skip_guarded_by_zero_count() -> None:
    text = VALIDATE_PS1.read_text(encoding="utf-8")
    assert SKIP_MARKER in text, (
        "validate.ps1 lost the active work-log family SKIP (backlog #149)"
    )
    guard = re.search(
        r"if \(\$worklogs\.Count -eq 0\) \{\s*\n\s*Add-Result -Level 'SKIP'",
        text,
    )
    assert guard, "validate.ps1 family SKIP must be guarded by `$worklogs.Count -eq 0`"


def test_both_validators_use_the_same_skip_text() -> None:
    """Parity: a reworded message on one side is a silent sh/ps1 divergence."""
    sh_hits = [ln.strip() for ln in VALIDATE_SH.read_text(encoding="utf-8").splitlines()
               if SKIP_MARKER in ln and "record_result" in ln]
    ps1_hits = [ln.strip() for ln in VALIDATE_PS1.read_text(encoding="utf-8").splitlines()
                if SKIP_MARKER in ln and "Add-Result" in ln]
    assert len(sh_hits) == 1, f"expected exactly one sh emission, got {sh_hits}"
    assert len(ps1_hits) == 1, f"expected exactly one ps1 emission, got {ps1_hits}"

    def _message(line: str) -> str:
        match = re.search(r"""["'](active work-log checks[^"']*)["']""", line)
        assert match, f"could not extract message from: {line}"
        return match.group(1)

    assert _message(sh_hits[0]) == _message(ps1_hits[0]), (
        "sh and ps1 family-SKIP messages diverged"
    )


def test_emission_is_family_level_not_per_check() -> None:
    """Anti-regression on the ADR-006 cost.

    The justification recorded in validator_native_baseline.json is explicitly
    that this is ONE emission, not one per check. If someone later expands it to
    a SKIP per check the native count grows by ~18 and the ratchet entry becomes
    a lie.
    """
    for path, token in ((VALIDATE_SH, "record_result SKIP"), (VALIDATE_PS1, "Add-Result -Level 'SKIP'")):
        text = path.read_text(encoding="utf-8")
        family_skips = [
            ln for ln in text.splitlines()
            if token in ln and "work-log" in ln
        ]
        assert len(family_skips) == 1, (
            f"{path.name} should carry exactly one work-log family SKIP, found "
            f"{len(family_skips)} — see the backlog #149 justification entry"
        )


# ---------------------------------------------------------------------------
# Behavioral — the real adopter scenario: a fresh install has no work logs
# ---------------------------------------------------------------------------

def _run_validate(cwd: Path) -> str:
    proc = subprocess.run(
        [bash, str(cwd / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _summary(output: str) -> dict:
    match = re.search(r"Summary:\s*pass=(\d+)\s+warn=(\d+)\s+fail=(\d+)\s+skip=(\d+)", output)
    assert match, f"no Summary line:\n{output[-400:]}"
    return {
        "pass": int(match.group(1)), "warn": int(match.group(2)),
        "fail": int(match.group(3)), "skip": int(match.group(4)),
    }


_WORKLOG = """# Work Log: fixture

## Header

- Branch: `fixture`
- Classification: `quick-win`
- Owner: `fixture`
- Current Phase: `ship`
- Diff Base SHA: `none`
- Checkpoint SHA: `none`

## Session Info

- Agent: `fixture`

## Task Description

fixture

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| ship | done | 2026-07-27 | — |

## Phase Summary

- ship: fixture

⚡ ACX

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T00:01:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T00:02:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T00:03:00Z

## External References

none

## Known Risk

none

## Conflict Resolution

none

## Drift Log

none

## Evidence

- fixture
"""


@pytest.mark.slow
@requires_bash
def test_fresh_install_announces_the_absent_family_and_regains_it() -> None:
    """Red/green in one run: SKIP present with no logs, gone once a log exists.

    Uses a real `deploy.sh` install rather than a hand-built tree, because the
    thing under test is precisely what a downstream adopter sees on day one.
    """
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        deployed = subprocess.run(
            [bash, str(DEPLOY_SH), str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT),
        )
        assert deployed.returncode == 0, f"deploy failed:\n{deployed.stderr}"

        work_dir = target / ".agentcortex" / "context" / "work"
        work_dir.mkdir(parents=True, exist_ok=True)
        # Mirror what the validators actually count. Both deliberately exclude
        # dotfiles — bash's `*.md` does not match a leading dot, and validate.ps1
        # filters with `Where-Object { $_.Name -notlike '.*' }`. Python's
        # pathlib.glob does NOT share that behaviour and happily returns
        # `.gitkeep.md`, so filtering here is required for the precondition to
        # mean what it says.
        active = [p for p in work_dir.glob("*.md") if not p.name.startswith(".")]
        assert not active, (
            f"precondition: a fresh install has no active work logs, found {active}"
        )

        absent = _run_validate(target)
        assert SKIP_MARKER in absent, (
            "a fresh install runs ~18 fewer checks and must say so — the family "
            "SKIP was not emitted"
        )
        absent_counts = _summary(absent)

        (work_dir / "fixture.md").write_bytes(_WORKLOG.encode("utf-8"))
        present = _run_validate(target)
        assert SKIP_MARKER not in present, (
            "with an active work log the family runs, so the SKIP must disappear"
        )
        present_counts = _summary(present)

        # The whole point: the family was silent, not skipped. Adding one log
        # brings a substantial block of checks back into the run.
        gained = present_counts["pass"] - absent_counts["pass"]
        assert gained >= 10, (
            f"expected the work-log family to add many checks, gained only {gained} "
            f"(absent={absent_counts}, present={present_counts}) — if this drops, "
            f"the family shrank or the guard changed"
        )
        assert present_counts["skip"] == absent_counts["skip"] - 1, (
            "the family SKIP should account for exactly one skip-count delta"
        )
