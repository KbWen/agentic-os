"""Regression test for #336 — validate.sh wrong verdicts / SIGPIPE on large Work Logs.

`validate.sh` runs with `set -euo pipefail` and fed `$wl_content` through pipes
into readers that exit on the first match: the classification parse
(`printf … | python … <break>`), plus ~27 sibling `printf '%s' "$wl_content" |
grep -q` / `grep -m1` audit checks. When `$wl_content` exceeds the OS pipe buffer
(64 KB on Linux/MSYS), `printf` still has bytes to write after the reader exits,
takes SIGPIPE, and the pipeline returns 141.

Two failure modes result:
- The classification parse is a bare `$(…)` assignment, so `errexit` promoted the
  141 and ABORTED the whole run mid-loop — no `Summary:` line (the reported #336).
- The sibling readers live inside `if`/`if !` conditions, so `errexit` is
  suppressed, but `pipefail` still returns 141 instead of grep's real 0 — which
  INVERTS the check. A valid >64 KB Work Log then produced fabricated FAILs
  (missing Current Phase / Gate Evidence / Phase Summary) AND hid real violations
  (shipped-not-archived reported as "none found"). Silent wrong verdicts are the
  worse failure mode.

Fix (#336): feed every `$wl_content` reader from a leading here-string
(`<<< "$wl_content" reader …`) instead of `printf '%s' "$wl_content" | reader`.
A here-string reads from a temp file — there is no writer process to SIGPIPE, so
an early-exiting reader can neither abort nor invert. This mirrors the file's own
`<<< "$wl_content"` / "NOT `printf | awk`" precedents. The classification parse
also drains stdin before its break as belt-and-suspenders.

validate.ps1 parses over an in-memory string (`[regex]::Match`), no pipe, so it
was never affected and needs no change (parity preserved).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# bash discovery (mirror test_validator_false_positives.py — avoid WindowsApps stub).
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


# ---------------------------------------------------------------------------
# Structural — deterministic, no subprocess. Lock the SIGPIPE-safe form so a
# revert to a `printf | reader` pipe over $wl_content fails CI on every platform.
# ---------------------------------------------------------------------------

def test_336_no_printf_pipe_over_wl_content() -> None:
    """No `$wl_content` reader may use `printf '%s' "$wl_content" | …` — that pipe
    SIGPIPEs an early-exiting reader on a >64 KB log. All must feed from a leading
    here-string (`<<< "$wl_content" …`)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    offenders = [
        i + 1 for i, line in enumerate(sh.splitlines())
        if 'printf \'%s\' "$wl_content" |' in line
    ]
    assert not offenders, (
        f"validate.sh still pipes $wl_content into a reader (SIGPIPE hazard on >64 KB "
        f"logs) at lines {offenders} — convert to `<<< \"$wl_content\" reader` (#336)"
    )
    # The safe idiom must actually be in use.
    assert '<<< "$wl_content"' in sh, "validate.sh must feed $wl_content readers via here-strings (#336)"


def test_336_wlclass_python_drains_stdin_before_break() -> None:
    """The classification helper must drain stdin (read()) before the early break —
    never iterate a bare `sys.stdin` and break (belt-and-suspenders for #336)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    assert "sys.stdin.read().splitlines()" in sh, (
        "validate.sh wlclass helper must drain stdin fully before break (#336)"
    )
    assert "for l in sys.stdin:" not in sh, (
        "validate.sh must NOT iterate a bare sys.stdin then break (#336)"
    )


def test_336_marker_present() -> None:
    assert "(#336)" in VALIDATE_SH.read_text(encoding="utf-8"), (
        "validate.sh must carry the (#336) fix marker for traceability"
    )


# ---------------------------------------------------------------------------
# Behavioral (slow). Two guarantees on a >64 KB Work Log:
#   A) the run does not SIGPIPE-abort (exit 141) and prints its Summary;
#   B) with the compaction size gate disabled, a large log validates IDENTICALLY
#      to a byte-for-byte-smaller copy of the same content — no fabricated FAILs,
#      no hidden violations (the sibling-reader inversion this fix removes).
# ---------------------------------------------------------------------------

_GATES = ("bootstrap", "plan", "implement", "ship")


def _worklog_text(pad_lines: int) -> str:
    gate_lines = "\n".join(
        f"- Gate: {g} | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-13T00:00:00Z"
        for g in _GATES
    )
    padding = "\n".join(f"<!-- pad {i:05d} -->" for i in range(pad_lines))
    return f"""# Work Log: t

## Header

- Branch: `t`
- Classification: `quick-win`
- Current Phase: `ship`
- Checkpoint SHA: `0000000000000000000000000000000000000000`

---

## Session Info

- Guardrails loaded: §1

---

## Phase Summary

Large-log fixture. ACX

---

## Gate Evidence

{gate_lines}

---

## Drift Log

- ADR Coverage Check: fixture.

---

## Resume

none

---

## Evidence

- real evidence line.

{padding}
"""


def _deploy(td: Path) -> Path:
    target = td / "proj"
    target.mkdir()
    res = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    assert res.returncode == 0, f"deploy failed:\n{res.stderr}"
    return target


def _write_worklog(target: Path, pad_lines: int) -> int:
    wd = target / ".agentcortex" / "context" / "work"
    wd.mkdir(parents=True, exist_ok=True)
    p = wd / "w.md"
    p.write_text(_worklog_text(pad_lines), encoding="utf-8", newline="\n")
    return p.stat().st_size


def _run(target: Path, *, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [bash, str(target / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target), env=env,
    )


def _summary(out: str) -> str | None:
    m = re.search(r"Summary: pass=\d+ warn=\d+ fail=\d+ skip=\d+", out)
    return m.group(0) if m else None


@pytest.mark.slow
@requires_bash
def test_336_large_worklog_does_not_sigpipe_abort_sh(tmp_path: Path) -> None:
    target = _deploy(tmp_path)
    size = _write_worklog(target, pad_lines=4000)
    assert size > 64 * 1024, f"fixture must exceed the 64 KB pipe buffer, got {size} bytes"
    proc = _run(target)
    out = proc.stdout + proc.stderr
    # 141 = 128 + SIGPIPE(13): the abort signature this fix removes.
    assert proc.returncode != 141, f"validate.sh SIGPIPE-aborted on a {size}-byte log (#336):\n{out[-800:]}"
    assert "Summary:" in out, f"no Summary line — run truncated mid-loop (#336):\n{out[-800:]}"


@pytest.mark.slow
@requires_bash
def test_336_large_worklog_verdict_parity_with_small_sh(tmp_path: Path) -> None:
    """A >64 KB log must validate IDENTICALLY to a small copy of the same content.
    The compaction size gate (legitimately) fails an oversized log, so it is raised
    out of the way here to isolate the SIGPIPE-inversion regression: any remaining
    difference is a fabricated FAIL or hidden violation from a sibling reader."""
    no_compaction = {"WORKLOG_MAX_KB": "1000000", "WORKLOG_MAX_LINES": "1000000"}

    target = _deploy(tmp_path)
    small_size = _write_worklog(target, pad_lines=5)
    small = _run(target, env_extra=no_compaction)
    small_summary = _summary(small.stdout + small.stderr)

    big_size = _write_worklog(target, pad_lines=4000)
    big = _run(target, env_extra=no_compaction)
    big_out = big.stdout + big.stderr
    big_summary = _summary(big_out)

    assert small_size < 64 * 1024 < big_size, f"sizes: small={small_size} big={big_size}"
    assert big_summary is not None, f"large-log run printed no Summary (#336):\n{big_out[-800:]}"
    assert big_summary == small_summary, (
        f"large log ({big_size} B) validated DIFFERENTLY from an identical-content small "
        f"copy ({small_size} B): small=[{small_summary}] big=[{big_summary}] — a sibling "
        f"$wl_content reader still SIGPIPE-inverts on a >64 KB log (#336).\n{big_out[-1200:]}"
    )
    # Explicit: none of the SIGPIPE-inverted false negatives may appear for the large log.
    for false_verdict in (
        "missing Current Phase field",
        "missing gate evidence receipts",
        "missing Phase Summary section",
    ):
        assert false_verdict not in big_out, (
            f"fabricated verdict {false_verdict!r} on a valid large log (#336):\n{big_out[-800:]}"
        )
