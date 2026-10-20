"""record_test_run.py: a recorded test run is tied to the code it tested.

spec_ref: docs/specs/test-evidence-freshness.md
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
TOOL = ROOT / ".agentcortex" / "tools" / "record_test_run.py"
BRANCH = "feat/demo-x"
KEY = "feat-demo-x"

requires_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not available")

LOG = """# Work Log: feat/demo-x

## Header
- Branch: `feat/demo-x`
- Classification: `feature`

---

## Gate Evidence
{receipts}

---

## Test Gate Results
none

---

## Evidence
none
"""


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=str(repo),
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert out.returncode == 0, out.stderr
    return out.stdout


def _repo(tmp_path: Path, receipts: str = "none") -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (repo / ".gitignore").write_text(".agentcortex/context/work/\nbuild/\n", encoding="utf-8")
    work = repo / ".agentcortex" / "context" / "work"
    work.mkdir(parents=True)
    (repo / ".agentcortex" / "context" / "current_state.md").write_text("# SSoT\n", encoding="utf-8")
    log = work / f"{KEY}.md"
    log.write_text(LOG.format(receipts=receipts), encoding="utf-8")
    _git(repo, "init", "-q", "-b", BRANCH)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")
    return repo, log


def _tool(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=str(repo),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def _run(repo: Path, log: Path, code: str) -> subprocess.CompletedProcess:
    return _tool(repo, "run", "--worklog", str(log), "--root", str(repo), "--", sys.executable, "-c", code)


def _runs(log: Path) -> list[str]:
    return [l for l in log.read_text(encoding="utf-8").splitlines() if l.startswith("- Test run: ")]


@requires_git
def test_ac1_run_returns_exit_code_and_appends_one_line(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    ok = _run(repo, log, "print('fine')")
    assert ok.returncode == 0, ok.stderr
    bad = _run(repo, log, "import sys; sys.exit(3)")
    assert bad.returncode == 3
    runs = _runs(log)
    assert len(runs) == 2
    assert re.match(r"- Test run: `.+` \| exit: 0 \| tree: [0-9a-f]{40} \| at: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$", runs[0])
    assert "| exit: 3 |" in runs[1]
    body = log.read_text(encoding="utf-8").split("## Test Gate Results")[1].split("---")[0]
    assert "none" not in body, "the lone 'none' placeholder is replaced, not kept beside the runs"


@requires_git
def test_ac1_command_runs_without_a_shell(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    result = _tool(repo, "run", "--worklog", str(log), "--root", str(repo), "--",
                   sys.executable, "-c", "import sys; print(sys.argv[1])", "a;echo INJECTED")
    assert result.returncode == 0
    assert "a;echo INJECTED" in result.stdout and "\nINJECTED" not in result.stdout


@requires_git
def test_ac2_fingerprint_ignores_runtime_state_and_ignored_files_but_not_code(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    index = repo / ".git" / "index"
    before_index = index.read_bytes()
    _run(repo, log, "pass")
    tree = _runs(log)[-1].split("tree: ")[1].split(" ")[0]
    assert index.read_bytes() == before_index, "the real index must not be written"

    (repo / ".agentcortex" / "context" / "current_state.md").write_text("# SSoT\nseq 2\n", encoding="utf-8")
    (repo / "build").mkdir()
    (repo / "build" / "out.bin").write_bytes(b"\x00")
    assert _tool(repo, "check", "--root", str(repo)).stdout.find("code changed") == -1

    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    assert "code changed after the latest recorded test run" in _tool(repo, "check", "--root", str(repo)).stdout
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "src" / "new.py").write_text("y = 1\n", encoding="utf-8")
    assert "code changed" in _tool(repo, "check", "--root", str(repo)).stdout, "an untracked file counts"
    (repo / "src" / "new.py").unlink()
    (repo / "src" / "app.py").unlink()
    assert "code changed" in _tool(repo, "check", "--root", str(repo)).stdout, "a deletion counts"
    assert re.fullmatch(r"[0-9a-f]{40}", tree)


@requires_git
def test_ac3_code_changed_during_the_run_is_unstable(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "open('src/app.py','w').write('x = 99\\n')")
    assert "| tree: unstable |" in _runs(log)[-1]
    assert "unstable" in _tool(repo, "check", "--root", str(repo)).stdout


@requires_git
def test_ac4_failed_run_followed_by_a_test_pass_receipt_fails(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "import sys; sys.exit(1)")
    text = log.read_text(encoding="utf-8").replace(
        "## Gate Evidence\nnone",
        "## Gate Evidence\n- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    log.write_text(text, encoding="utf-8")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 1, result.stdout
    assert "exited 1 but a later test PASS receipt exists" in result.stdout


@requires_git
def test_ac4_code_changed_after_the_run_with_a_ship_receipt_fails(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "pass")
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    text = log.read_text(encoding="utf-8").replace(
        "## Gate Evidence\nnone",
        "## Gate Evidence\n- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    log.write_text(text, encoding="utf-8")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 1, result.stdout
    assert "before ship" in result.stdout


@requires_git
def test_ac5_before_ship_a_stale_run_only_warns(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "pass")
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 0
    assert result.stdout.startswith("WARN: ")


@requires_git
def test_ac5_a_tested_tier_log_without_a_recorded_run_warns_but_never_fails(tmp_path: Path) -> None:
    """AC-5 as updated 2026-10-20: feature/architecture-change/hotfix + a test/ship PASS
    receipt + no recorded run is reported (WARN), still never a FAIL."""
    repo, _log = _repo(tmp_path, receipts="- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 0
    assert "no test run was recorded" in result.stdout and result.stdout.startswith("WARN: ")


@requires_git
@pytest.mark.parametrize("cls, receipt, warns", [
    ("quick-win", "ship", False),   # tier where tests are optional stays silent
    ("hotfix", "test", True),
    ("feature", "implement", False),  # no test/ship PASS yet
])
def test_ac5_unrecorded_warning_follows_tier_and_receipt(tmp_path: Path, cls: str, receipt: str, warns: bool) -> None:
    repo, log = _repo(tmp_path, receipts=f"- Gate: {receipt} | Verdict: PASS | Classification: {cls} | Timestamp: 2999-01-01T00:00:00Z")
    log.write_text(log.read_text(encoding="utf-8").replace("Classification: `feature`", f"Classification: `{cls}`"), encoding="utf-8")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 0
    assert ("no test run was recorded" in result.stdout) is warns, result.stdout


@requires_git
def test_check_ignores_another_branchs_log_whose_key_ends_the_same(tmp_path: Path) -> None:
    """`fix-feat-demo-x.md` belongs to branch fix/feat-demo-x, not to feat/demo-x."""
    repo, log = _repo(tmp_path)
    other = log.parent / f"fix-{KEY}.md"
    other.write_text(LOG.replace("feat/demo-x", "fix/feat-demo-x").format(receipts="none")
                     .replace("## Test Gate Results\nnone",
                              "## Test Gate Results\n- Test run: `x` | exit: 1 | tree: unstable | at: 2020-01-01T00:00:00Z"),
                     encoding="utf-8")
    result = _tool(repo, "check", "--root", str(repo))
    assert "nothing checked" in result.stdout, result.stdout


def test_ac6_both_validators_wire_the_same_check() -> None:
    sh = (ROOT / ".agentcortex" / "bin" / "validate.sh").read_text(encoding="utf-8")
    ps1 = (ROOT / ".agentcortex" / "bin" / "validate.ps1").read_text(encoding="utf-8-sig")
    label = "test evidence freshness (current-branch work log)"
    assert re.search(rf'run_python_check "{re.escape(label)}" WARN "\$ROOT/\.agentcortex/tools/record_test_run\.py" check --root "\$ROOT"', sh)
    assert re.search(rf"Invoke-PythonCheck -Label '{re.escape(label)}' -MissingPythonLevel 'WARN' .*record_test_run\.py'\) -Arguments @\('check', '--root', \$root\)", ps1)


def test_ac7_the_tool_ships_downstream() -> None:
    deploy = (ROOT / ".agentcortex" / "bin" / "deploy.sh").read_text(encoding="utf-8")
    assert deploy.count("record_test_run.py") == 2, "both runtime-tool whitelist sites"
    golden = (ROOT / "tests" / "ci" / "fixtures" / "deploy_manifest_golden.txt").read_text(encoding="utf-8")
    assert "core .agentcortex/tools/record_test_run.py" in golden.splitlines()


def test_ac8_readme_states_what_it_does_not_catch() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "record_test_run.py" in readme
    assert "a hand-typed" in readme


# --- review fixes (2026-10-20) --------------------------------------------------------

def _with_receipt(log: Path, receipt: str) -> None:
    text = log.read_text(encoding="utf-8")
    log.write_text(text.replace("## Gate Evidence\nnone", "## Gate Evidence\n" + receipt), encoding="utf-8")


def _set_run_at(log: Path, at: str) -> None:
    text = re.sub(r"\| at: \S+$", f"| at: {at}", log.read_text(encoding="utf-8"), flags=re.M)
    log.write_text(text, encoding="utf-8")


@requires_git
@pytest.mark.parametrize("ts, fails", [
    ("2026-10-20T08:30:00+08:00", False),   # 00:30Z, before the 01:00Z run
    ("2026-10-19T20:30:00-05:00", True),    # 01:30Z, after the run
    ("2026-10-20T01:30Z", True),            # minute precision
    ("2026-10-21", True),                   # date only, after
])
def test_receipt_times_are_compared_as_instants(tmp_path: Path, ts: str, fails: bool) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "import sys; sys.exit(1)")
    _set_run_at(log, "2026-10-20T01:00:00Z")
    _with_receipt(log, f"- Gate: test | Verdict: PASS | Classification: feature | Timestamp: {ts}")
    result = _tool(repo, "check", "--root", str(repo))
    assert (result.returncode == 1) is fails, result.stdout


@requires_git
def test_receipt_phase_and_verdict_are_case_insensitive(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "pass")
    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    _with_receipt(log, "- Gate: Ship | Verdict: Pass | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    assert _tool(repo, "check", "--root", str(repo)).returncode == 1


@requires_git
def test_unstable_latest_run_fails_once_shipped(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "open('src/app.py','w').write('x = 99\\n')")
    _with_receipt(log, "- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 1 and "unstable" in result.stdout


@requires_git
def test_detached_head_is_reported_not_silently_skipped(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "pass")
    _git(repo, "checkout", "-q", "--detach")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 0 and "detached HEAD" in result.stdout


@requires_git
def test_same_size_edit_right_after_indexing_is_seen(tmp_path: Path) -> None:
    """copyfile reset the temp index mtime and git trusted stale stat data (review R1)."""
    for _ in range(5):
        repo, log = _repo(tmp_path / f"r{_}")
        _run(repo, log, "pass")
        (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")  # same size as x = 1
        assert "code changed" in _tool(repo, "check", "--root", str(repo)).stdout


@requires_git
@pytest.mark.skipif(os.name != "nt", reason="Windows .cmd shim resolution")
def test_windows_cmd_shim_runs_without_a_shell(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "fake-suite.cmd").write_text("@echo SUITE-RAN\r\n@exit /b 0\r\n", encoding="utf-8")
    env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run([sys.executable, str(TOOL), "run", "--worklog", str(log), "--root", str(repo), "--", "fake-suite"],
                            cwd=str(repo), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SUITE-RAN" in result.stdout
    assert "| exit: 0 |" in _runs(log)[-1]


@requires_git
def test_a_command_with_a_newline_is_still_one_record(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "x = 1\nprint(x)")
    runs = _runs(log)
    assert len(runs) == 1 and "| exit: 0 |" in runs[0]
    assert "1 log(s) current" in _tool(repo, "check", "--root", str(repo)).stdout


@requires_git
@pytest.mark.parametrize("sep", [" ", " ", "\x85"])
def test_unicode_line_separators_cannot_hide_a_failed_run(tmp_path: Path, sep: str) -> None:
    repo, log = _repo(tmp_path)
    _tool(repo, "run", "--worklog", str(log), "--root", str(repo), "--",
          sys.executable, "-c", "import sys; sys.exit(1)", f"a{sep}b")
    _with_receipt(log, "- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    assert len(_runs(log)) == 1
    assert _tool(repo, "check", "--root", str(repo)).returncode == 1


@requires_git
def test_unfingerprintable_tree_warns_and_never_fails_ship(tmp_path: Path) -> None:
    """An untracked, empty nested repo makes `git add -A` fail: report it, don't block forever."""
    repo, log = _repo(tmp_path)
    nested = repo / "vendor" / "empty"
    nested.mkdir(parents=True)
    _git(nested, "init", "-q")
    _run(repo, log, "pass")
    assert "| tree: none |" in _runs(log)[-1]
    _with_receipt(log, "- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2999-01-01T00:00:00Z")
    result = _tool(repo, "check", "--root", str(repo))
    assert result.returncode == 0 and "could not be fingerprinted" in result.stdout


@requires_git
def test_date_only_receipt_on_the_run_day_counts_as_later(tmp_path: Path) -> None:
    repo, log = _repo(tmp_path)
    _run(repo, log, "import sys; sys.exit(1)")
    _set_run_at(log, "2026-10-20T15:00:00Z")
    _with_receipt(log, "- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-10-20")
    assert _tool(repo, "check", "--root", str(repo)).returncode == 1
