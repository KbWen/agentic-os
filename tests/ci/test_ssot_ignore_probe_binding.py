r"""The persistent-SSoT ignore guard must ask git, not `.gitignore`.

Reported by a downstream fork on 2026-08-24: its `.gitignore` carried
`.agentcortex/context/archive/*.md`, so every archived Work Log stopped being
committed -- and the validator's `.gitignore preserves persistent SSoT artifacts`
check still reported PASS, because it compared whole `.gitignore` lines against a
fixed list of directory paths and that pattern never spells one.

Reproduced here before the fix: appending that single line to a freshly deployed
tree left `validate.sh` at `fail=0` while `git check-ignore` confirmed the archived
log was ignored. Two arms below are therefore RED on the pre-fix tree -- the FAIL
arm because it passed, and the probe-list arms because the probes did not exist.

**Why a file inside the directory.** `docs/specs/*.md` ignores the contents without
naming the directory; a directory-only probe reproduces the original blindness.
Probing a representative file inside subsumes the directory case, since ignoring a
directory also ignores what is in it.

**Honest ceiling.** `CI Structural Tests` and `Pytest (Windows)` are non-required
contexts, so neither arm can block a merge today; that is a branch-protection
setting, not something this file can reach. The behavioural arms need bash, so on
a bash-less host only the structural arms run -- `validate.ps1` is pinned by the
probe-list parity assertion rather than by its own behavioural run, in the style
`tests/ci/test_validator_twin_parity.py` already sanctions.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# Candidate order and the WindowsApps exclusion are the shape pinned by
# tests/ci/test_bash_resolver_parity.py: `%LOCALAPPDATA%\Microsoft\WindowsApps\bash.exe`
# answers which("bash") and starts, but with no WSL distro it exits 1 on any shipped
# .sh script -- a red that has nothing to do with the code under test.
_bash_candidates = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (
        candidate for candidate in _bash_candidates
        if candidate and "WindowsApps" not in candidate and Path(candidate).exists()
    ),
    None,
)
git = shutil.which("git")
pwsh = shutil.which("pwsh")
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")
requires_git = pytest.mark.skipif(git is None, reason="git not available")
requires_pwsh = pytest.mark.skipif(
    sys.platform != "win32" or pwsh is None,
    reason="validate.ps1 is the native Windows validator; Normalize-PathString "
    "mis-resolves $root under Linux pwsh (same skip reason as "
    "test_validator_false_positives.py::requires_windows)",
)

PASS_LINE = "[PASS] .gitignore preserves persistent SSoT artifacts"
FAIL_LINE = "[FAIL] .gitignore blocks persistent SSoT artifacts"
SKIP_LINE = "[SKIP] persistent SSoT artifacts vs .gitignore"

# The accident shape: ignores the contents, never names the directory.
ACCIDENT_PATTERN = ".agentcortex/context/archive/*.md"
# The ordinary "ignore the directory, keep the markdown" idiom. git does NOT ignore
# the probe here -- but `check-ignore -v` still exits 0 because a pattern MATCHED.
# Reading that as "ignored" fails an adopter whose tree is correct, and names their
# protective `!` line as the thing to delete.
NEGATION_IDIOM = "docs/adr/*\n!docs/adr/*.md\n"
# A tracked file named outright. `check-ignore` skips tracked paths unless --no-index,
# so without that flag this is invisible -- and the old literal matcher caught it.
TRACKED_ARTIFACT = ".agentcortex/context/current_state.md"

SH_LITERAL_MATCHER = 'grep -x -F -q -- "$must_track"'
PS_LITERAL_MATCHER = "$gitignoreContent -contains"


# --------------------------------------------------------------------------
# Structural arms (cheap, and the only cover the PowerShell twin gets here)
# --------------------------------------------------------------------------

def _probe_list(text: str) -> list[str]:
    """Extract the single-quoted probe paths from either validator's probe array."""
    block = re.search(r"gitignore_?[Pp]robes\s*=\s*@?\((.*?)\)", text, re.DOTALL)
    assert block is not None, "probe array not found"
    return re.findall(r"'([^']+)'", block.group(1))


def test_both_validators_declare_the_same_probe_paths() -> None:
    sh_probes = _probe_list(VALIDATE_SH.read_text(encoding="utf-8"))
    ps_probes = _probe_list(VALIDATE_PS1.read_text(encoding="utf-8-sig"))
    assert sh_probes == ps_probes, (
        "validate.sh and validate.ps1 must probe the same paths; a divergence here is "
        f"twin drift on a FAIL-tier guard.\nsh:  {sh_probes}\nps1: {ps_probes}"
    )
    assert len(sh_probes) >= 6, sh_probes


def test_every_probe_targets_a_file_not_a_bare_directory() -> None:
    """A directory-only probe is what the old matcher effectively did."""
    for probe in _probe_list(VALIDATE_SH.read_text(encoding="utf-8")):
        assert not probe.endswith("/"), (
            f"{probe} is a directory probe; `<dir>/*.md` would ignore its contents "
            "without matching it. Probe a file inside instead."
        )
        assert probe.endswith(".md"), probe


def test_neither_validator_matches_gitignore_lines_literally() -> None:
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps = VALIDATE_PS1.read_text(encoding="utf-8-sig")
    assert SH_LITERAL_MATCHER not in sh, (
        "validate.sh is back to whole-line matching against .gitignore"
    )
    assert PS_LITERAL_MATCHER not in ps, (
        "validate.ps1 is back to exact-element matching against .gitignore"
    )
    # `git -C <root> check-ignore ...` -- assert on the verb, not the full line.
    for name, text in (("validate.sh", sh), ("validate.ps1", ps)):
        assert "check-ignore -q --no-index" in text, (
            f"{name} must take the VERDICT from `-q`: `-v` exits 0 on a negation match "
            "too, which means the path is NOT ignored"
        )
        assert "check-ignore -v --no-index" in text, (
            f"{name} must still run `-v` for the diagnostic line"
        )
        assert "check-ignore -v" not in text.replace("check-ignore -v --no-index", ""), (
            f"{name} has a `-v` call without --no-index; tracked files would be skipped"
        )


def test_both_validators_separate_the_outer_repo_cause() -> None:
    """A tree deployed under a `vendor/`-style ignore must not be diagnosed per-probe."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps = VALIDATE_PS1.read_text(encoding="utf-8-sig")
    for name, text in (("validate.sh", sh), ("validate.ps1", ps)):
        assert "check-ignore -q --no-index -- ." not in text, (
            f"{name} discriminates on `check-ignore -- .`, which a blank CRLF line in "
            ".gitignore makes exit 0 on a healthy tree -- every core.autocrlf clone"
        )
        assert "rev-parse --show-prefix" in text, (
            f"{name} must use the nesting prefix, not a `.` probe, to tell an outer-repo "
            "ignore from an ordinary one"
        )
        assert "inside a larger repository" in text, name
        assert "do NOT delete that rule blindly" in text, (
            f"{name}'s outer-repo message must not tell the reader to remove the rule"
        )


def test_both_validators_keep_the_did_not_run_verdict() -> None:
    """Exit >=2 (no git, or not a work tree) must never be reported as assurance."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps = VALIDATE_PS1.read_text(encoding="utf-8-sig")
    assert 'record_result SKIP "persistent SSoT artifacts vs .gitignore' in sh
    assert '-Level \'SKIP\' -Message "persistent SSoT artifacts vs .gitignore' in ps


# --------------------------------------------------------------------------
# Behavioural arms (slow: a real deploy plus a real validator run)
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def deployed(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if bash is None or git is None:
        pytest.skip("bash and git are both required")
    target = tmp_path_factory.mktemp("acx") / "proj"
    target.mkdir()
    subprocess.run([git, "-C", str(target), "init", "-q"], check=True)
    proc = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"deploy failed:\n{proc.stderr}"
    return target


def _validate(target: Path) -> str:
    proc = subprocess.run(
        [bash, str(target / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )
    return proc.stdout + proc.stderr


def _validate_ps1(target: Path) -> str:
    proc = subprocess.run(
        [pwsh, "-NoProfile", "-File",
         str(target / ".agentcortex" / "bin" / "validate.ps1")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(target),
    )
    return proc.stdout + proc.stderr


@pytest.mark.slow
@requires_bash
@requires_git
def test_a_clean_downstream_tree_reports_pass(deployed: Path) -> None:
    """Without this arm the FAIL arm below is satisfiable by a check that always fails."""
    out = _validate(deployed)
    assert PASS_LINE in out, out[-2000:]


@pytest.mark.slow
@requires_bash
@requires_git
def test_a_contents_only_ignore_is_caught_and_named(deployed: Path) -> None:
    """RED before the fix: the old matcher reported PASS on exactly this tree."""
    gitignore = deployed / ".gitignore"
    original = gitignore.read_bytes()
    try:
        with gitignore.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\n" + ACCIDENT_PATTERN + "\n")
        hidden = subprocess.run(
            [git, "-C", str(deployed), "check-ignore", "-q", "--",
             ".agentcortex/context/archive/some-worklog.md"],
        )
        assert hidden.returncode == 0, "fixture is wrong: the log is not actually ignored"

        out = _validate(deployed)
        assert FAIL_LINE in out, f"guard did not catch {ACCIDENT_PATTERN}:\n{out[-2000:]}"
        assert PASS_LINE not in out
        assert ACCIDENT_PATTERN in out, (
            "the FAIL must name the offending .gitignore line, or the adopter cannot act on it"
        )
    finally:
        gitignore.write_bytes(original)


@pytest.mark.slow
@requires_bash
@requires_git
def test_an_exclude_file_hides_specs_with_no_gitignore(deployed: Path) -> None:
    """`.gitignore` is not the only ignore source, so the check must not be gated on it.

    The branch this replaced emitted `.gitignore absent -- no persistent SSoT artifacts
    are ignored`: a PASS asserted without looking at anything. `.git/info/exclude` hides
    files just as effectively.
    """
    gitignore = deployed / ".gitignore"
    original = gitignore.read_bytes()
    exclude = deployed / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude_original = exclude.read_bytes() if exclude.exists() else None
    try:
        gitignore.unlink()
        with exclude.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\ndocs/specs/*.md\n")

        out = _validate(deployed)
        assert FAIL_LINE in out, (
            "no .gitignore, but .git/info/exclude hides docs/specs -- the guard must still "
            f"catch it:\n{out[-2000:]}"
        )
        assert PASS_LINE not in out
    finally:
        gitignore.write_bytes(original)
        if exclude_original is None:
            exclude.unlink(missing_ok=True)
        else:
            exclude.write_bytes(exclude_original)


@pytest.mark.slow
@requires_bash
@requires_git
def test_the_negation_idiom_is_not_read_as_ignored(deployed: Path) -> None:
    """`-v` exits 0 on a negation match, which means the path is NOT ignored.

    Taking the verdict from `-v` reds an adopter whose tree git tracks fine, and the
    diagnostic then names their protective `!` line as the pattern to remove --
    following that advice would delete the artifact from git. Verdict comes from `-q`.
    """
    gitignore = deployed / ".gitignore"
    original = gitignore.read_bytes()
    try:
        with gitignore.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\n" + NEGATION_IDIOM)
        probe = "docs/adr/ADR-000-acx-ignore-probe.md"
        not_ignored = subprocess.run([git, "-C", str(deployed), "check-ignore", "-q",
                                      "--no-index", "--", probe])
        assert not_ignored.returncode == 1, "fixture is wrong: git does ignore the probe"
        verbose = subprocess.run([git, "-C", str(deployed), "check-ignore", "-v",
                                  "--no-index", "--", probe], capture_output=True)
        assert verbose.returncode == 0, (
            "precondition gone: `-v` no longer exits 0 on a negation, so this arm no "
            "longer guards anything -- re-derive before deleting it"
        )

        out = _validate(deployed)
        assert PASS_LINE in out, f"negation idiom misreported as ignored:\n{out[-2000:]}"
        assert FAIL_LINE not in out
    finally:
        gitignore.write_bytes(original)


@pytest.mark.slow
@requires_bash
@requires_git
def test_a_tracked_artifact_named_outright_is_caught(deployed: Path) -> None:
    """`check-ignore` skips TRACKED files unless --no-index; the old matcher caught this."""
    gitignore = deployed / ".gitignore"
    original = gitignore.read_bytes()
    for args in (["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "fixture"]):
        subprocess.run([git, "-C", str(deployed), *args], capture_output=True)
    tracked = subprocess.run([git, "-C", str(deployed), "ls-files", "--error-unmatch",
                              TRACKED_ARTIFACT], capture_output=True)
    assert tracked.returncode == 0, "fixture is wrong: the artifact is not tracked"
    try:
        with gitignore.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\n" + TRACKED_ARTIFACT + "\n")
        out = _validate(deployed)
        assert FAIL_LINE in out, (
            "a tracked artifact named outright in .gitignore was not caught -- the probe "
            f"call is missing --no-index:\n{out[-2000:]}"
        )
        assert PASS_LINE not in out
    finally:
        gitignore.write_bytes(original)


@pytest.mark.slow
@requires_pwsh
@requires_bash
@requires_git
def test_the_powershell_twin_reaches_the_same_verdicts(deployed: Path) -> None:
    """Without this, nothing here exercises validate.ps1's verdict logic at all.

    Mutating the PS twin so it can never emit FAIL left the rest of this file green,
    and `count_parity_on_framework` cannot see it either: on a healthy tree no probe is
    ignored, so the mutant is behaviourally identical there.
    """
    gitignore = deployed / ".gitignore"
    original = gitignore.read_bytes()
    try:
        assert PASS_LINE in _validate_ps1(deployed), "PS twin fails on a clean tree"
        with gitignore.open("a", encoding="utf-8", newline="") as fh:
            fh.write("\n" + ACCIDENT_PATTERN + "\n")
        out = _validate_ps1(deployed)
        assert FAIL_LINE in out, f"PS twin missed {ACCIDENT_PATTERN}:\n{out[-2000:]}"
        assert PASS_LINE not in out
        assert ACCIDENT_PATTERN in out, "PS twin's FAIL must name the offending line too"
    finally:
        gitignore.write_bytes(original)


@pytest.mark.slow
@requires_bash
@requires_git
def test_a_crlf_gitignore_is_still_a_healthy_tree(deployed: Path) -> None:
    """CRLF is what Git for Windows checks out by default (`core.autocrlf=true`).

    A blank CRLF line is not blank to git: it is the pattern `\\r`, which git strips to
    the empty string, and the empty pattern matches the pathspec `.`. An earlier version
    of the outer-repo branch used `check-ignore -- .` as its discriminator and therefore
    FAILed every Windows clone -- including this repository's own tree -- while all six
    probes resolved clean. Every other arm here writes LF, so nothing else would catch it.
    """
    gitignore = deployed / ".gitignore"
    original = gitignore.read_bytes()
    try:
        crlf = original.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        gitignore.write_bytes(crlf)
        assert b"\r\n\r\n" in crlf, "fixture is wrong: no blank CRLF line to trip the bug"
        poisoned = subprocess.run(
            [git, "-C", str(deployed), "check-ignore", "-q", "--no-index", "--", "."]
        )
        assert poisoned.returncode == 0, (
            "precondition gone: the empty-pattern quirk no longer reproduces, so this arm "
            "no longer guards anything -- re-derive before deleting it"
        )

        out = _validate(deployed)
        assert PASS_LINE in out, (
            f"a CRLF .gitignore on a healthy tree was not reported clean:\n{out[-2000:]}"
        )
        assert "itself ignored by an outer repository" not in out
        assert "inside a larger repository" not in out
    finally:
        gitignore.write_bytes(original)


@pytest.mark.slow
@requires_bash
@requires_git
def test_a_tree_under_an_outer_ignore_names_that_cause(tmp_path: Path) -> None:
    """Deployed into a `vendor/`-style ignored path, every probe resolves ignored.

    Diagnosing that per-probe points at the outer repository's own directory rule and
    calls it "the pattern to remove" -- the same shape as reading `-v`'s exit status:
    a FAIL whose advice, if followed, breaks something that was working.
    """
    outer = tmp_path / "outer"
    (outer / "vendor").mkdir(parents=True)
    subprocess.run([git, "-C", str(outer), "init", "-q"], check=True)
    # write_bytes, not write_text(newline=...): that kwarg is 3.10+ and TypeErrors on
    # this repo's 3.9 CI floor (backlog #164, pinned by test_write_text_newline_ratchet).
    (outer / ".gitignore").write_bytes(b"vendor/\n")
    target = outer / "vendor" / "proj"
    target.mkdir()
    deployed = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    assert deployed.returncode == 0, f"deploy failed:\n{deployed.stderr}"

    out = _validate(target)
    assert "inside a larger repository" in out, (
        f"the outer-repo cause was not identified:\n{out[-2000:]}"
    )
    assert "vendor/proj/" in out, "the FAIL must name where the project sits"
    assert "probes ignored; the ignore source:line shown above is the pattern to remove" not in out, (
        "diagnosed per-probe, so the FAIL names the outer repo's own rule as removable"
    )
    assert PASS_LINE not in out


def _playbook_claimed_ignores(path: Path) -> list[str]:
    """The paths Test 1 tells the reader must come back `ignored (correct)`."""
    text = path.read_text(encoding="utf-8")
    block = re.search(r"for p in \\\n(.*?)\n\s*do\n", text, re.DOTALL)
    assert block is not None, f"{path.name}: Test 1's verification loop not found"
    return [
        line.strip().rstrip("\\").strip()
        for line in block.group(1).splitlines()
        if line.strip().rstrip("\\").strip()
    ]


def test_both_playbook_twins_claim_the_same_ignores() -> None:
    en = _playbook_claimed_ignores(ROOT / ".agentcortex/docs/guides/audit-guardrails.md")
    zh = _playbook_claimed_ignores(ROOT / ".agentcortex/docs/guides/audit-guardrails_zh-TW.md")
    assert en == zh, f"playbook twins drifted apart\nEN: {en}\nzh-TW: {zh}"
    assert len(en) >= 5, en


@pytest.mark.slow
@requires_bash
@requires_git
def test_the_playbook_claims_what_the_deploy_actually_ignores(deployed: Path) -> None:
    """Test 1 drifted once already: it asserted four paths were invisible to `git status`
    while a real cold deploy showed ninety of them, and nothing caught it because no
    mechanism was bound to the claim. This is that binding -- the page's assertion is now
    executed against a real deployed ignore block rather than trusted."""
    claimed = _playbook_claimed_ignores(ROOT / ".agentcortex/docs/guides/audit-guardrails.md")
    not_ignored = [
        p for p in claimed
        if subprocess.run(
            [git, "-C", str(deployed), "check-ignore", "-q", "--no-index", "--", p]
        ).returncode != 0
    ]
    assert not not_ignored, (
        "audit-guardrails.md Test 1 tells the reader these come back `ignored (correct)`, "
        f"but the deployed ignore block does not hide them: {not_ignored}"
    )


@pytest.mark.slow
@requires_bash
@requires_git
def test_a_non_git_tree_skips_rather_than_passing(deployed: Path) -> None:
    """A guard that could not run must not report assurance (cf. backlog #173/#412)."""
    dotgit = deployed / ".git"
    parked = deployed / ".git-parked"
    shutil.move(str(dotgit), str(parked))
    try:
        out = _validate(deployed)
        assert SKIP_LINE in out, out[-2000:]
        assert PASS_LINE not in out, "a check that did not run reported PASS"
        assert FAIL_LINE not in out
    finally:
        shutil.move(str(parked), str(dotgit))
