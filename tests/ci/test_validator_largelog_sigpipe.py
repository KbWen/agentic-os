"""Regression test for #336 — validate.sh SIGPIPE (exit 141) on large Work Logs.

`validate.sh` runs with `set -euo pipefail`. Its Work Log classification parse
fed `$wl_content` through a pipe into a reader that exits on the first match:

    wl_class="$(printf '%s' "$wl_content" | "$PYTHON_BIN" -c "$_acx_wlclass_py")"

The embedded Python iterated `sys.stdin` line-by-line and `break`ed on the first
`Classification:` hit. When `$wl_content` exceeds the OS pipe buffer (64 KB on
Linux/MSYS), `printf` still has bytes to write after the reader is gone, takes
SIGPIPE, and exits 141. `pipefail` promotes 141 to the pipeline status and
`errexit` aborts the whole run — mid-loop, BEFORE the `Summary:` line prints. A
truncated run with earlier `[FAIL]` lines and no summary reads as "finished, no
failures", so a governance gate silently goes quiet. The Python-unavailable
fallback had the same shape via `... | head -n 1`.

Fix (#336): drain stdin fully before the early break (`sys.stdin.read()`), and in
the fallback capture all matches then take the first line in bash instead of
piping to `head -n 1`. Both make the writer complete before any early exit.

validate.ps1 parses classification with `[regex]::Match($content, ...)` over the
full in-memory string — no pipe, no SIGPIPE — so it was never affected and needs
no change (parity: both validators still classify correctly).
"""

from __future__ import annotations

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
# Structural — deterministic, no subprocess. Locks the SIGPIPE-safe form so a
# revert to the racy pipe pattern fails CI on every platform.
# ---------------------------------------------------------------------------

def test_336_wlclass_python_drains_stdin_before_break() -> None:
    """The Work Log classification helper must drain stdin (read()) before the
    early break — never iterate a bare `sys.stdin` and break (SIGPIPE hazard)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    assert "sys.stdin.read().splitlines()" in sh, (
        "validate.sh wlclass helper must drain stdin fully before break (#336)"
    )
    assert "for l in sys.stdin:" not in sh, (
        "validate.sh must NOT iterate a bare sys.stdin then break — printf takes "
        "SIGPIPE (141) on a >64 KB Work Log and pipefail aborts the run (#336)"
    )


def test_336_wlclass_fallback_does_not_head_close_the_pipe() -> None:
    """The Python-unavailable fallback must not pipe the classification match into
    `head -n 1` (early pipe close → SIGPIPE on a large log)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    assert "_wl_class_all=" in sh, (
        "validate.sh fallback must capture all matches then take the first line "
        "in bash rather than piping to head -n 1 (#336)"
    )
    assert (
        "Classification\\1\\?:[[:space:]]*//p' | head -n 1" not in sh
    ), "validate.sh fallback must not close the classification pipe early with head -n 1 (#336)"


def test_336_marker_present() -> None:
    assert "(#336)" in VALIDATE_SH.read_text(encoding="utf-8"), (
        "validate.sh must carry the (#336) fix marker for traceability"
    )


# ---------------------------------------------------------------------------
# Behavioral (slow) — a >64 KB current-branch Work Log must not abort the run.
# Pre-fix this aborts with exit 141 mid-loop and prints no Summary. Deterministic
# green post-fix on Linux (no MSYS fork limits); the non-required Windows pytest
# job may be noisier due to the separate MSYS fork-exhaustion issue (#336
# "Secondary issue"), which this fix intentionally does not address.
# ---------------------------------------------------------------------------

def _write_large_worklog(target: Path, name: str) -> int:
    """Write a valid quick-win Work Log padded past the 64 KB pipe buffer.

    Classification sits in the header (top of file) so the parser matches early
    and the maximal remainder is left unwritten — the exact SIGPIPE trigger. All
    padding is inert HTML comments appended after Evidence, so it neither adds
    gate receipts nor breaks section parsing. Returns the byte size written."""
    work_dir = target / ".agentcortex" / "context" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    gate_lines = "\n".join(
        f"- Gate: {g} | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-13T00:00:00Z"
        for g in ("bootstrap", "plan", "implement", "ship")
    )
    padding = "\n".join(f"<!-- pad line {i:05d} to exceed the 64KB pipe buffer -->" for i in range(2000))
    body = f"""# Work Log: {name}

## Header

- Branch: `test/{name}`
- Classification: `quick-win`
- Current Phase: `ship`
- Checkpoint SHA: `0000000000000000000000000000000000000000`

---

## Phase Summary

Large-log SIGPIPE regression fixture. ACX

---

## Gate Evidence

{gate_lines}

---

## Drift Log

- ADR Coverage Check: test fixture.

---

## Resume

none

---

## Evidence

- Fixture evidence.

{padding}
"""
    path = work_dir / name
    path.write_text(body, encoding="utf-8", newline="\n")
    return path.stat().st_size


@pytest.mark.slow
@requires_bash
def test_336_large_worklog_does_not_sigpipe_abort_sh(tmp_path: Path) -> None:
    target = tmp_path / "proj"
    target.mkdir()
    deployed = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert deployed.returncode == 0, f"deploy failed:\n{deployed.stderr}"

    size = _write_large_worklog(target, "big-quickwin.md")
    assert size > 64 * 1024, f"fixture must exceed the 64 KB pipe buffer, got {size} bytes"

    proc = subprocess.run(
        [bash, str(target / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )
    out = proc.stdout + proc.stderr
    # 141 = 128 + SIGPIPE(13): the exact abort signature this fix removes.
    assert proc.returncode != 141, (
        f"validate.sh aborted with SIGPIPE (141) on a {size}-byte Work Log (#336). "
        f"Tail:\n{out[-800:]}"
    )
    # The run must reach its end and print the Summary — a truncated run omits it.
    assert "Summary:" in out, (
        f"validate.sh produced no Summary line on a {size}-byte Work Log — the run "
        f"was truncated mid-loop (#336). Tail:\n{out[-800:]}"
    )
