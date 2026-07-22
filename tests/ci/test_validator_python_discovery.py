"""Python-interpreter discovery by STARTABILITY, not existence (backlog #144).

Both validators previously selected an interpreter by mere existence on PATH:
`validate.sh` `command -v python3` / `validate.ps1` `Get-Command python3`. On
stock Windows, ``%LOCALAPPDATA%\\Microsoft\\WindowsApps\\python3.exe`` is an App
Execution Alias stub that EXISTS on PATH even with no Python installed — invoked
with args it prints "Python was not found" and exits 9009 (it does NOT open the
Store UI when given args). The existence-only check selected that broken stub and
shadowed a perfectly working ``python``, so every python-backed check spuriously
failed (and the PR #359 reduced-assurance labeling reads the same variable, so
honest labeling also depended on correct discovery).

The fix probes each candidate (``python3`` then ``python``) with a silent
``-c "import sys"`` and selects only the first that EXITS 0. These tests simulate
the broken stub with PATH-prepended shims — no reliance on the host actually
having a broken alias — following the deployed-fixture patterns in
``test_validator_false_positives.py``.

TDD note: against probe-less (existence-only) discovery the two "broken python3"
scenarios go RED — the stub is selected and every python check fails, so the
top-line is "integrity check failed" instead of the expected pass/reduced-
assurance line. The startability probe turns them green.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# bash discovery (mirror test_validator_false_positives.py — avoid the
# WindowsApps stub, which is itself the class of bug under test here).
_git_path = shutil.which("git")
_git_root = Path(_git_path).parent.parent if _git_path else None
_bash_candidates = [
    str(_git_root / "bin" / "bash.exe") if _git_root else None,
    str(_git_root / "usr" / "bin" / "bash.exe") if _git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (c for c in _bash_candidates if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")

powershell = shutil.which("pwsh") or shutil.which("powershell")
requires_powershell = pytest.mark.skipif(powershell is None, reason="PowerShell not available")
requires_windows = pytest.mark.skipif(
    sys.platform != "win32",
    reason="validate.ps1 is the native Windows validator, and the .bat "
    "App-Execution-Alias shim + PATHEXT resolution are a Windows concern. "
    "Behavioral sh<->ps1 parity for the probe is pinned structurally by the "
    "marker test below; the Linux CI 'CI Structural Tests' job must not run the "
    "native PS validator.",
)

# Final top-line variants (validate.sh:2905-2921 / validate.ps1:2743-2758).
PASSED_UNQUALIFIED = "Agentic OS integrity check passed"
REDUCED_ASSURANCE = (
    "Agentic OS integrity check passed (reduced assurance: python-dependent checks skipped)"
)
# run_python_check / Invoke-PythonCheck branch messages.
PY_UNAVAILABLE_WARN = "python unavailable (install Python 3.9+ for full validation)"
PY_DISABLED_SKIP_SH = "python checks disabled (--no-python)"
PY_DISABLED_SKIP_PS1 = "python checks disabled (--NoPython)"


def _posix(p: Path) -> str:
    """Windows path -> MSYS/Git-bash POSIX form (C:\\x -> /c/x)."""
    s = str(p)
    if len(s) >= 2 and s[1] == ":":
        return "/" + s[0].lower() + s[2:].replace("\\", "/")
    return s.replace("\\", "/")


def _deploy_fixture(td: Path) -> Path:
    target = td / "proj"
    target.mkdir()
    result = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"deploy failed:\n{result.stderr}"
    return target


def _sh_shim(shim_dir: Path, name: str, *, working: bool) -> None:
    """POSIX shim `name`. working=False exits nonzero on every call (the
    WindowsApps-stub simulation); working=True execs the real interpreter,
    forwarding args cleanly via "$@"."""
    shim_dir.mkdir(parents=True, exist_ok=True)
    p = shim_dir / name
    if working:
        real = _posix(Path(sys.executable))
        p.write_text(f'#!/bin/sh\nexec "{real}" "$@"\n', encoding="utf-8", newline="\n")
    else:
        p.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8", newline="\n")
    os.chmod(p, 0o755)


def _bat_shim(shim_dir: Path, name: str, *, working: bool) -> None:
    """Windows `<name>.bat` shim. working=False emits `@exit /b 9009` (the App
    Execution Alias exit code); working=True forwards all args to the real
    interpreter."""
    shim_dir.mkdir(parents=True, exist_ok=True)
    p = shim_dir / f"{name}.bat"
    body = f'@"{sys.executable}" %*\r\n' if working else "@exit /b 9009\r\n"
    p.write_text(body, encoding="utf-8", newline="")


def _run_sh_with_shim(target: Path, shim_dir: Path, *args: str) -> subprocess.CompletedProcess:
    """Run validate.sh with shim_dir GUARANTEED first on PATH.

    We prepend inside the shell (`export PATH=...; exec`) rather than via the
    subprocess env because the Git-for-Windows `bin\\bash.exe` launcher reorders
    an inherited PATH (prepending its own unix-tool dirs), which could push the
    shim below a bundled interpreter. Exporting at runtime is launcher-proof.
    """
    validate = _posix(target / ".agentcortex" / "bin" / "validate.sh")
    shim = _posix(shim_dir)
    inner = f'export PATH="{shim}:$PATH"; exec "{validate}" "$@"'
    return subprocess.run(
        [bash, "-c", inner, "acx", *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )


def _run_ps1_with_path(
    target: Path, path_dirs: list[Path], *args: str
) -> subprocess.CompletedProcess:
    """Run validate.ps1 with path_dirs prepended to PATH (PowerShell honors the
    inherited PATH order for Get-Command; no launcher munging as with Git bash)."""
    env = dict(os.environ)
    prefix = os.pathsep.join(str(d) for d in path_dirs)
    env["PATH"] = prefix + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(target / ".agentcortex" / "bin" / "validate.ps1"), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target), env=env,
    )


# ---------------------------------------------------------------------------
# Structural (fast) — the probe (not existence-only selection) is present in
# both validators.
# ---------------------------------------------------------------------------

def test_startability_probe_marker_present_in_both_validators() -> None:
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert "(#144)" in sh, "validate.sh missing the #144 startability-probe marker"
    assert "(#144)" in ps1, "validate.ps1 missing the #144 startability-probe marker (parity)"


def test_probe_actually_starts_candidate_in_both_validators() -> None:
    """Discovery must START a candidate (`-c import sys`), not merely test PATH
    existence — the whole point of #144."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert '-c "import sys"' in sh, "validate.sh must probe startability via `-c \"import sys\"`"
    assert "'-c' 'import sys'" in ps1, "validate.ps1 must probe startability via `-c 'import sys'`"
    # candidate order preserved: python3 then python.
    assert "for _py_candidate in python3 python" in sh
    assert "foreach ($_pyCandidate in @('python3', 'python'))" in ps1


# ---------------------------------------------------------------------------
# Behavioral — validate.sh (Git bash)
# ---------------------------------------------------------------------------

@pytest.mark.slow
@requires_bash
def test_broken_python3_falls_through_to_working_python_sh() -> None:
    """A broken `python3` earlier on PATH must be rejected and discovery must
    fall through to a working `python` (RED against existence-only discovery,
    which selects the stub and fails every python check)."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        target = _deploy_fixture(tdp)
        shim = tdp / "shims"
        _sh_shim(shim, "python3", working=False)   # WindowsApps-style stub
        _sh_shim(shim, "python", working=True)      # python.org-style install
        proc = _run_sh_with_shim(target, shim)
        out = proc.stdout + proc.stderr
        assert PASSED_UNQUALIFIED in out and REDUCED_ASSURANCE not in out, (
            "probe must select the working `python` -> python-backed checks run "
            f"-> unqualified pass. Output tail:\n{out[-1000:]}"
        )
        assert PY_UNAVAILABLE_WARN not in out, out[-600:]
        assert proc.returncode == 0, out[-600:]


@pytest.mark.slow
@requires_bash
def test_no_startable_python_enters_reduced_assurance_sh() -> None:
    """When NEITHER candidate is startable, PYTHON_BIN stays empty and the run
    degrades exactly like the python-unavailable path (WARN + reduced-assurance
    top-line, PR #359) — no crash."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        target = _deploy_fixture(tdp)
        shim = tdp / "shims"
        _sh_shim(shim, "python3", working=False)
        _sh_shim(shim, "python", working=False)
        proc = _run_sh_with_shim(target, shim)
        out = proc.stdout + proc.stderr
        assert REDUCED_ASSURANCE in out, (
            f"no startable python -> reduced-assurance top-line. Output tail:\n{out[-1000:]}"
        )
        assert PY_UNAVAILABLE_WARN in out, (
            "the python-unavailable WARN (not the --no-python SKIP) must fire when "
            f"the probe rejects every candidate. Output tail:\n{out[-1000:]}"
        )
        assert proc.returncode == 0, out[-600:]  # deployed fixture is fail=0


@pytest.mark.slow
@requires_bash
def test_no_python_flag_short_circuits_before_probe_sh() -> None:
    """--no-python must short-circuit BEFORE any probe: even with a broken
    python3 shim first on PATH the result is the SKIP (disabled) message, never
    the WARN (unavailable) message a probe-rejection would produce."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        target = _deploy_fixture(tdp)
        shim = tdp / "shims"
        _sh_shim(shim, "python3", working=False)
        _sh_shim(shim, "python", working=True)
        proc = _run_sh_with_shim(target, shim, "--no-python")
        out = proc.stdout + proc.stderr
        assert PY_DISABLED_SKIP_SH in out, out[-800:]
        assert PY_UNAVAILABLE_WARN not in out, out[-800:]
        assert REDUCED_ASSURANCE in out, out[-600:]


# ---------------------------------------------------------------------------
# Behavioral — validate.ps1 (Windows / pwsh). Deploy needs bash too.
# ---------------------------------------------------------------------------

@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_broken_python3_falls_through_to_working_python_ps1() -> None:
    """Parity: a broken `python3.bat` (store-alias exit 9009) must be rejected
    and discovery must fall through to the real `python.exe`."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        target = _deploy_fixture(tdp)
        shim = tdp / "shims"
        _bat_shim(shim, "python3", working=False)  # store-alias stub
        # The real `python` (this interpreter's dir) is the working fallback; the
        # shim shadows only `python3`.
        py_dir = Path(sys.executable).parent
        proc = _run_ps1_with_path(target, [shim, py_dir])
        out = proc.stdout + proc.stderr
        assert PASSED_UNQUALIFIED in out and REDUCED_ASSURANCE not in out, (
            f"probe must reject python3.bat and select real python. Output tail:\n{out[-1000:]}"
        )
        assert PY_UNAVAILABLE_WARN not in out, out[-600:]
        assert proc.returncode == 0, out[-600:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_no_startable_python_enters_reduced_assurance_ps1() -> None:
    """Parity: both candidates shadowed by broken .bat stubs -> $PythonCommand
    $null -> reduced-assurance top-line + python-unavailable WARN, no crash."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        target = _deploy_fixture(tdp)
        shim = tdp / "shims"
        _bat_shim(shim, "python3", working=False)
        _bat_shim(shim, "python", working=False)
        proc = _run_ps1_with_path(target, [shim])
        out = proc.stdout + proc.stderr
        assert REDUCED_ASSURANCE in out, out[-1000:]
        assert PY_UNAVAILABLE_WARN in out, out[-1000:]
        assert proc.returncode == 0, out[-600:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_no_python_flag_short_circuits_before_probe_ps1() -> None:
    """Parity: -NoPython short-circuits before any probe (SKIP-disabled message,
    not the WARN-unavailable a probe rejection would emit)."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        target = _deploy_fixture(tdp)
        shim = tdp / "shims"
        _bat_shim(shim, "python3", working=False)
        proc = _run_ps1_with_path(target, [shim], "-NoPython")
        out = proc.stdout + proc.stderr
        assert PY_DISABLED_SKIP_PS1 in out, out[-800:]
        assert PY_UNAVAILABLE_WARN not in out, out[-800:]
        assert REDUCED_ASSURANCE in out, out[-600:]
