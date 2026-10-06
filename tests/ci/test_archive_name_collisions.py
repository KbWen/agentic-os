"""Archive name collisions: the archive directory is the type.

Spec: docs/specs/archive-name-collisions.md. Final Work Logs live in the
archive ROOT (`/ship §3`); `archive/work/` holds `/handoff §6` compaction
fragments, which may share a final log's basename.

- AC-1: D4 resolves an INDEX.jsonl `log` against the archive root only, so a
  same-named fragment cannot stand in for a missing final log.
- AC-2: D4 records WARN when its child did not run and SKIP without Python --
  never a PASS, and never an aborted run.
- AC-3: the D4 Python embedded in validate.sh and validate.ps1 is identical.
- AC-5: the archived-Work-Log Phase-Summary scan reads the archive root only (#186).
"""

from __future__ import annotations

import json
import re
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

# bash discovery (mirror test_validator_false_positives.py -- avoid the WindowsApps stub).
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
    reason="validate.ps1 is the native Windows validator (see test_validator_false_positives.py)",
)

D4_DANGLING = "INDEX.jsonl referenced logs missing on disk"
D4_NOT_IN_ROOT = "INDEX.jsonl referenced logs not in the archive root"
D4_DID_NOT_RUN = "INDEX.jsonl referenced-file check did not run"
D4_SKIP_SH = "INDEX.jsonl referenced-file check -- python checks disabled (--no-python)"
D4_SKIP_PS1 = "INDEX.jsonl referenced-file check -- python checks disabled (--NoPython)"
EMPTY_SUMMARY = "empty Phase Summary:"

FRAG = "fragonly-20261006.md"       # in INDEX, exists only under archive/work/
PAIR = "paired-20261006.md"         # in INDEX, final log in root + same-named fragment
CONTROL = "nosummary-20261006.md"   # root log with an empty Phase Summary


def _sh_snippet() -> str:
    text = VALIDATE_SH.read_text(encoding="utf-8")
    m = re.search(r"_acx_index_refs_py=\$\(cat <<'PYEOF'\n(.*?)\nPYEOF\n", text, re.S)
    assert m, "validate.sh: D4 heredoc (_acx_index_refs_py) not found"
    return m.group(1)


def _ps1_snippet() -> str:
    text = VALIDATE_PS1.read_text(encoding="utf-8")
    m = re.search(r"\$indexRefsOut = \(& \$script:PythonCommand\.Source -c @'\n(.*?)\n'@", text, re.S)
    assert m, "validate.ps1: D4 here-string not found"
    return m.group(1)


def _write_index(archive: Path, *logs: object) -> None:
    lines = [json.dumps({"log": log, "branch": "t", "shipped": "2026-10-06"}) for log in logs]
    (archive / "INDEX.jsonl").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def _d4(archive: Path) -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-c", _sh_snippet(), str(archive / "INDEX.jsonl")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == "", f"D4 child wrote to stderr:\n{proc.stderr}"
    return proc.stdout.splitlines()


@pytest.fixture()
def archive(tmp_path: Path) -> Path:
    a = tmp_path / "archive"
    (a / "work").mkdir(parents=True)
    return a


# ---------------------------------------------------------------------------
# Fast -- the shared D4 logic and the twin structure
# ---------------------------------------------------------------------------

def test_d4_python_is_identical_in_both_validators() -> None:
    """AC-3: one resolution rule, embedded twice; the copies must not drift."""
    assert _sh_snippet() == _ps1_snippet(), (
        "the D4 Python in validate.sh and validate.ps1 must be byte-identical"
    )


def test_d4_same_named_fragment_does_not_mask_missing_final_log(archive: Path) -> None:
    """AC-1: the bug. A fragment with the final log's name used to satisfy D4."""
    _write_index(archive, FRAG)
    (archive / "work" / FRAG).write_bytes(b"# compaction fragment\n")
    out = _d4(archive)
    assert out[-1].startswith("WARN|"), out
    assert f"{D4_NOT_IN_ROOT}: 1" in out[-1], out
    assert any(FRAG in line and "archive/work/" in line for line in out[:-1]), out


def test_d4_root_log_passes_alongside_same_named_fragment(archive: Path) -> None:
    """AC-1: the 11 historical root+fragment pairs stay green."""
    _write_index(archive, PAIR)
    (archive / PAIR).write_bytes(b"# final\n")
    (archive / "work" / PAIR).write_bytes(b"# compaction fragment\n")
    assert _d4(archive) == ["PASS|INDEX.jsonl referenced logs all present on disk (1 checked)"]


def test_d4_explicit_work_prefix_resolves_as_written(archive: Path) -> None:
    """AC-1: a `log` value that names its directory resolves through the join."""
    _write_index(archive, "work/legacy-prefixed.md")
    (archive / "work" / "legacy-prefixed.md").write_bytes(b"# legacy final\n")
    assert _d4(archive)[-1].startswith("PASS|"), _d4(archive)


def test_d4_log_found_nowhere_is_dangling(archive: Path) -> None:
    _write_index(archive, "never-written-20261006.md")
    out = _d4(archive)
    assert out[-1].startswith("WARN|") and f"{D4_DANGLING}: 1" in out[-1], out
    assert D4_NOT_IN_ROOT not in out[-1], out


def test_d4_ignores_entries_without_a_string_log(archive: Path) -> None:
    (archive / "INDEX.jsonl").write_bytes(
        b'{"log": 5}\n{"type": "lesson_archive"}\nnot json\n[1, 2]\n'
    )
    assert _d4(archive) == ["PASS|INDEX.jsonl referenced logs all present on disk (0 checked)"]


def test_d4_undecodable_index_reports_error_not_traceback(archive: Path) -> None:
    """AC-2: a child failure must surface as the 'error' token, not a traceback
    (under `set -e` a nonzero child aborted validate.sh before its Summary)."""
    (archive / "INDEX.jsonl").write_bytes(b'\xff\xfe{"log": "x.md"}\n')
    assert _d4(archive) == ["error"]


def test_d4_cannot_run_branches_present_in_both_validators() -> None:
    """AC-2 structure (the ps1 behavior is only exercised on Windows)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    for text, skip in ((sh, D4_SKIP_SH), (ps1, D4_SKIP_PS1)):
        assert D4_DID_NOT_RUN in text
        assert skip in text
    assert re.search(r'index_refs_result="\$\("\$PYTHON_BIN" -c [^\n]*\)" \|\| index_refs_rc=\$\?', sh), (
        "validate.sh D4 must not let a failing child abort the run under set -e"
    )
    assert '[[ "$index_refs_rc" -eq 0 ]] || index_refs_verdict=' in sh, (
        "validate.sh D4 must not take a verdict from a child that exited nonzero"
    )
    block = ps1[ps1.index("$indexRefsOut = "):ps1.index("Add-Result -Level $indexRefsLevel")]
    assert "$indexRefsRc -eq 0 -and" in block, "validate.ps1 D4 must gate the verdict on the exit code"
    assert "$ErrorActionPreference = 'Continue'" in ps1[ps1.index("D4: INDEX.jsonl"):ps1.index("$indexRefsOut = ")], (
        "validate.ps1 D4 must run the child under Continue: PS 5.1 aborts on redirected stderr under Stop"
    )


def test_validate_ps1_keeps_utf8_bom() -> None:
    """Windows PowerShell 5.1 decodes a BOM-less script in the ANSI code page, and the
    em dashes in validate.ps1's strings then break its parser (#90 added the BOM)."""
    assert VALIDATE_PS1.read_bytes().startswith(b"\xef\xbb\xbf")


def test_phase_summary_scan_reads_archive_root_only_in_both_validators() -> None:
    """AC-5 structure: fragments under archive/work/ are not Work Logs (#186)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert re.search(r"find \"\$ARCHIVE_DIR\" -maxdepth 1 -name '\*\.md'[^\n]*-not -iname 'ship-history-\*'", sh)
    m = re.search(r"\$archivedLogs = Get-ChildItem -Path \$archiveDir[^\n]*", ps1)
    assert m and "-Recurse" not in m.group(0), m.group(0) if m else "not found"


# ---------------------------------------------------------------------------
# Slow -- real deploy + validator runs
# ---------------------------------------------------------------------------

def _deploy(td: Path) -> Path:
    target = td / "proj"
    target.mkdir()
    proc = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"deploy failed:\n{proc.stderr}"
    return target


def _seed(target: Path) -> Path:
    archive = target / ".agentcortex" / "context" / "archive"
    (archive / "work").mkdir(parents=True, exist_ok=True)
    _write_index(archive, FRAG, PAIR)
    (archive / PAIR).write_bytes(b"# final\n\n## Phase Summary\n\n- shipped. ACX\n")
    (archive / CONTROL).write_bytes(b"# final\n\n## Phase Summary\n\nnone\n")
    for name in (FRAG, PAIR):
        (archive / "work" / name).write_bytes(b"# compaction fragment\n")
    return archive


def _run_sh(target: Path, *args: str) -> str:
    proc = subprocess.run(
        [bash, str(target / ".agentcortex" / "bin" / "validate.sh"), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )
    return proc.stdout + proc.stderr


def _run_ps1(target: Path, *args: str, shell: str | None = None) -> str:
    proc = subprocess.run(
        [shell or powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(target / ".agentcortex" / "bin" / "validate.ps1"), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )
    return proc.stdout + proc.stderr


def _assert_directory_is_the_type(out: str) -> None:
    assert f"[WARN] {D4_NOT_IN_ROOT}: 1" in out, out[-1500:]
    assert any(FRAG in line and "archive/work/" in line for line in out.splitlines()), out[-1500:]
    empty = [line for line in out.splitlines() if EMPTY_SUMMARY in line]
    assert any(CONTROL in line for line in empty), f"root scan must still run:\n{out[-1500:]}"
    assert not any(FRAG in line or PAIR in line for line in empty), (
        f"fragments under archive/work/ are not Work Logs:\n{empty}"
    )


@pytest.mark.slow
@requires_bash
def test_archive_directory_is_the_type_sh() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = _deploy(Path(td))
        archive = _seed(target)
        _assert_directory_is_the_type(_run_sh(target))
        assert f"[SKIP] {D4_SKIP_SH}" in _run_sh(target, "--no-python")
        (archive / "INDEX.jsonl").write_bytes(b'\xff\xfe not utf-8\n')
        out = _run_sh(target)
        assert f"[WARN] {D4_DID_NOT_RUN}" in out, out[-1500:]
        assert "Summary: pass=" in out, "a failing D4 child must not abort validate.sh"
        # A child that prints a verdict and then exits nonzero did not finish: no PASS.
        _write_index(archive, PAIR)
        shim = Path(td) / "shim"
        shim.mkdir()
        (shim / "python3").write_bytes(
            b'#!/bin/sh\n'
            b'if [ "$1" = "-c" ] && [ "$2" = "import sys" ]; then exit 0; fi\n'
            b'echo "PASS|INDEX.jsonl referenced logs all present on disk (1 checked)"\n'
            b'exit 3\n'
        )
        (shim / "python3").chmod(0o755)
        out = _run_sh_with_path(target, shim)
        assert f"[WARN] {D4_DID_NOT_RUN}" in out, out[-1500:]


def _posix(p: Path) -> str:
    """Windows path -> Git-bash POSIX form (C:\\x -> /c/x)."""
    s = str(p)
    return "/" + s[0].lower() + s[2:].replace("\\", "/") if len(s) >= 2 and s[1] == ":" else s


def _run_sh_with_path(target: Path, shim_dir: Path) -> str:
    """validate.sh with shim_dir first on PATH, prepended inside the shell because the
    Git-for-Windows bash launcher reorders an inherited PATH (see
    test_validator_python_discovery.py)."""
    inner = f'export PATH="{_posix(shim_dir)}:$PATH"; exec "{_posix(target / ".agentcortex" / "bin" / "validate.sh")}"'
    proc = subprocess.run(
        [bash, "-c", inner],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )
    return proc.stdout + proc.stderr


# Windows PowerShell 5.1 and pwsh 7 parse and run validate.ps1 differently (encoding,
# native stderr under Stop), and CI runs only pwsh -- so the twin runs under both.
_PS_SHELLS = [s for s in (shutil.which("pwsh"), shutil.which("powershell")) if s]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
@pytest.mark.parametrize("shell", _PS_SHELLS, ids=[Path(s).stem for s in _PS_SHELLS])
def test_archive_directory_is_the_type_ps1(shell: str) -> None:
    with tempfile.TemporaryDirectory() as td:
        target = _deploy(Path(td))
        archive = _seed(target)
        _assert_directory_is_the_type(_run_ps1(target, shell=shell).replace("\\", "/"))
        assert f"[SKIP] {D4_SKIP_PS1}" in _run_ps1(target, "-NoPython", shell=shell)
        (archive / "INDEX.jsonl").write_bytes(b'\xff\xfe not utf-8\n')
        out = _run_ps1(target, shell=shell)
        assert f"[WARN] {D4_DID_NOT_RUN}" in out, out[-1500:]
        assert "Summary: pass=" in out
