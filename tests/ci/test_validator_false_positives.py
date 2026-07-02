"""Regression tests for validator framework-self false positives (#170/#171/#172).

Locks three WARNs that fired on the framework repo itself but should not, and
guards cross-platform (validate.sh ↔ validate.ps1) parity of each fix:

- #170: underscore-prefixed meta/index specs (`_product-backlog-archive.md`
  status:archive, `_research-*.md` status:research) are exempt from the
  spec-status enum, matching the `_*` skip convention already used elsewhere.
- #171: `ship-history-*.md` archives are not Work Logs (no `## Phase Summary`
  contract) and must be excluded from the archived-Work-Log Phase-Summary scan.
- #172: the app-init template / Project Name checks fire only for a genuine
  downstream app — detected by an `ADR-00N-project-architecture.md` (created by
  /app-init), NOT by any ADR. The framework's governance ADRs never match, and
  the signal is deploy-independent so it also covers fork/clone adopters that
  never ran deploy.sh (no `.agentcortex-manifest`).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# bash discovery (mirror test_deploy_tiering.py — avoid the WindowsApps stub).
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
requires_powershell = pytest.mark.skipif(powershell is None, reason="PowerShell not available")
requires_windows = pytest.mark.skipif(
    sys.platform != "win32",
    reason="validate.ps1 is the native Windows validator; running it under Linux "
    "pwsh mis-resolves $root. Behavioral sh↔ps1 parity is a Windows concern — the "
    "cross-platform regression guard is the structural test above. (The Linux CI "
    "'CI Structural Tests' job must NOT execute the native PS validator.)",
)


def _run_validate_ps1(cwd: Path) -> str:
    proc = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(cwd / ".agentcortex" / "bin" / "validate.ps1")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _summary_counts(output: str) -> dict:
    import re
    m = re.search(r"Summary:\s*pass=(\d+)\s+warn=(\d+)\s+fail=(\d+)", output)
    assert m, f"no Summary line in output:\n{output[-400:]}"
    return {"pass": int(m.group(1)), "warn": int(m.group(2)), "fail": int(m.group(3))}

# The four WARN substrings this change eliminates on the framework repo.
STATUS_WARN = "unrecognized status value"          # #170
PHASE_SUMMARY_WARN = "with empty Phase Summary"     # #171 (WARN-specific; avoids
#   matching the PASS line "...have non-empty Phase Summary")
TEMPLATE_WARN = "project spec template missing"     # #172
PROJECT_NAME_WARN = "Project Name field absent"     # #172
RESUME_WARN = "work logs with ## Resume section missing required sub-sections"
ROUTING_ACTION_STALE_WARN = "stale pending routing_actions need canonical-doc follow-up"


def _resume_warn_count(output: str) -> int | None:
    match = re.search(rf"{re.escape(RESUME_WARN)}.*?:\s*(\d+)", output)
    return int(match.group(1)) if match else None


def _run_validate(cwd: Path) -> str:
    proc = subprocess.run(
        [bash, str(cwd / ".agentcortex" / "bin" / "validate.sh")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd),
    )
    return proc.stdout + proc.stderr


def _write_worklog(
    target: Path,
    name: str,
    *,
    classification: str,
    phase: str,
    gates: tuple[str, ...],
    resume: str = "none",
    include_test_results: bool = False,
) -> None:
    work_dir = target / ".agentcortex" / "context" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    gate_lines = "\n".join(
        f"- Gate: {gate} | Verdict: PASS | Classification: {classification} | Timestamp: 2026-06-29T00:00:00Z"
        for gate in gates
    )
    test_section = (
        "\n---\n\n## Test Gate Results\n\n- Command: `pytest tests/ci`\n- Result: pass\n"
        if include_test_results else ""
    )
    (work_dir / name).write_text(
        f"""# Work Log: {name}

## Header

- Branch: `test/{name}`
- Classification: `{classification}`
- Current Phase: `{phase}`
- Checkpoint SHA: `0000000000000000000000000000000000000000`

---

## Phase Summary

Validator false-positive fixture. ACX

---

## Gate Evidence

{gate_lines}

---

## Drift Log

- ADR Coverage Check: test fixture.
{test_section}
---

## Resume

{resume}

---

## Evidence

- Fixture evidence.
""",
        encoding="utf-8",
        newline="\n",
    )


def _deploy_for_validator_fixture(td: Path) -> Path:
    target = td / "proj"
    target.mkdir()
    first = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert first.returncode == 0, f"deploy failed:\n{first.stderr}"
    return target


@pytest.fixture(scope="module")
def framework_validate_output() -> str:
    if bash is None:
        pytest.skip("bash not available")
    return _run_validate(ROOT)


# ---------------------------------------------------------------------------
# Behavioral — the framework repo must validate without these false WARNs
# ---------------------------------------------------------------------------

@pytest.mark.slow
@requires_bash
def test_170_underscore_meta_specs_no_status_warn(framework_validate_output: str) -> None:
    # The repo really contains _product-backlog-archive.md (status: archive);
    # _research-*.md (status: research) may also be present transiently.
    assert STATUS_WARN not in framework_validate_output, (
        "underscore-prefixed meta specs must be exempt from the spec-status enum (#170)"
    )


@pytest.mark.slow
@requires_bash
def test_171_ship_history_no_phase_summary_warn(framework_validate_output: str) -> None:
    assert (ROOT / ".agentcortex" / "context" / "archive" / "ship-history-2026.md").exists(), \
        "fixture precondition: ship-history archive should exist in the framework repo"
    assert PHASE_SUMMARY_WARN not in framework_validate_output, (
        "ship-history-*.md is not a Work Log and must be excluded from the scan (#171)"
    )


@pytest.mark.slow
@requires_bash
def test_172_no_app_init_warn_on_framework(framework_validate_output: str) -> None:
    assert TEMPLATE_WARN not in framework_validate_output, (
        "framework governance ADRs must not trigger the app-init template check (#172)"
    )
    assert PROJECT_NAME_WARN not in framework_validate_output, (
        "framework repo has no Project Name and must not trigger the check (#172)"
    )


@pytest.mark.slow
@requires_bash
def test_framework_has_no_stale_pending_routing_actions_warn(framework_validate_output: str) -> None:
    assert ROUTING_ACTION_STALE_WARN not in framework_validate_output, (
        "framework review snapshots must close stale routing_actions by merging or rejecting "
        "them in the target canonical doc"
    )


@pytest.mark.slow
@requires_bash
def test_172_app_init_checks_fire_for_fork_downstream() -> None:
    """A fork/clone adopter (no .agentcortex-manifest) that ran /app-init — i.e.
    has an ADR-00N-project-architecture.md — MUST still get the template /
    Project Name checks. This is the case the earlier manifest-based marker
    under-suppressed; the project-architecture-ADR signal is deploy-independent.
    """
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        first = subprocess.run(
            [bash, str(DEPLOY_SH), str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT),
        )
        assert first.returncode == 0, f"deploy failed:\n{first.stderr}"

        # Simulate a fork adopter: remove the deploy manifest, then run /app-init's
        # observable effect (the project-architecture ADR) WITHOUT setting a
        # Project Name or creating a spec-app-feature template.
        (target / ".agentcortex-manifest").unlink(missing_ok=True)
        adr_dir = target / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "ADR-001-project-architecture.md").write_text(
            "# ADR-001 Project Architecture\n", encoding="utf-8"
        )

        out = _run_validate(target)
        assert TEMPLATE_WARN in out, "template check must fire for an app-init'd fork downstream (#172)"
        assert PROJECT_NAME_WARN in out, "Project Name check must fire for an app-init'd fork downstream (#172)"


@pytest.mark.slow
@requires_bash
def test_172_governance_only_adrs_do_not_fire() -> None:
    """A repo with ONLY governance-named ADRs (no *-project-architecture.md) must
    NOT trigger the app-init checks, even with a manifest present."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        first = subprocess.run(
            [bash, str(DEPLOY_SH), str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT),
        )
        assert first.returncode == 0, f"deploy failed:\n{first.stderr}"
        adr_dir = target / "docs" / "adr"
        adr_dir.mkdir(parents=True, exist_ok=True)
        (adr_dir / "ADR-001-governance-friction-tuning.md").write_text("# gov\n", encoding="utf-8")

        out = _run_validate(target)
        assert TEMPLATE_WARN not in out and PROJECT_NAME_WARN not in out, (
            "governance-only ADRs must not be read as an /app-init signal (#172)"
        )


@pytest.mark.slow
@requires_bash
def test_resume_none_before_handoff_is_not_warned_but_handoff_is_sh() -> None:
    """`## Resume: none` is valid before handoff and for quick-win ship paths,
    but feature/architecture-change handoff still requires the three subsections."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_worklog(
            target,
            "plan-resume-none.md",
            classification="architecture-change",
            phase="plan",
            gates=("bootstrap", "plan"),
        )
        _write_worklog(
            target,
            "quickwin-resume-none.md",
            classification="quick-win",
            phase="ship",
            gates=("bootstrap", "plan", "implement", "ship"),
        )
        _write_worklog(
            target,
            "handoff-resume-missing.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            include_test_results=True,
        )

        out = _run_validate(target)
        assert _resume_warn_count(out) == 1, out[-1200:]


@pytest.mark.slow
@requires_bash
def test_stale_pending_routing_actions_warn_sh() -> None:
    """A pending routing_action in an old review snapshot must not stay invisible
    just because it targets a valid existing canonical doc."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        review_dir = target / "docs" / "reviews"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "2000-01-01-routing-actions.md").write_text(
            """# Routing Actions Fixture

## routing_actions

```yaml
routing_actions:
  - finding: "Old pending routing action should warn."
    target_doc: "docs/architecture/document-governance.md"
    status: pending
    owner: "test"
```
""",
            encoding="utf-8",
            newline="\n",
        )

        out = _run_validate(target)
        assert ROUTING_ACTION_STALE_WARN in out, out[-1200:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_stale_pending_routing_actions_warn_ps1() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        review_dir = target / "docs" / "reviews"
        review_dir.mkdir(parents=True, exist_ok=True)
        (review_dir / "2000-01-01-routing-actions.md").write_text(
            """# Routing Actions Fixture

## routing_actions

```yaml
routing_actions:
  - finding: "Old pending routing action should warn."
    target_doc: "docs/architecture/document-governance.md"
    status: pending
    owner: "test"
```
""",
            encoding="utf-8",
            newline="\n",
        )

        out = _run_validate_ps1(target)
        assert ROUTING_ACTION_STALE_WARN in out, out[-1200:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_resume_none_before_handoff_is_not_warned_but_handoff_is_ps1() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_worklog(
            target,
            "plan-resume-none.md",
            classification="architecture-change",
            phase="plan",
            gates=("bootstrap", "plan"),
        )
        _write_worklog(
            target,
            "quickwin-resume-none.md",
            classification="quick-win",
            phase="ship",
            gates=("bootstrap", "plan", "implement", "ship"),
        )
        _write_worklog(
            target,
            "handoff-resume-missing.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            include_test_results=True,
        )

        out = _run_validate_ps1(target)
        assert _resume_warn_count(out) == 1, out[-1200:]


# ---------------------------------------------------------------------------
# Structural — cross-platform parity (sh ↔ ps1) of each fix
# ---------------------------------------------------------------------------

def test_precondition_framework_has_no_project_architecture_adr() -> None:
    """The #172 discriminator relies on the framework never shipping an
    *-project-architecture.md ADR (its ADRs are governance-named)."""
    for base in (ROOT / "docs" / "adr", ROOT / ".agentcortex" / "adr"):
        if base.exists():
            offenders = list(base.glob("*-project-architecture.md"))
            assert not offenders, f"framework must not ship a project-architecture ADR: {offenders}"


def test_fix_markers_present_in_both_validators() -> None:
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    for marker in ("(#170)", "(#171)", "(#172)"):
        assert marker in sh, f"validate.sh missing {marker} fix"
        assert marker in ps1, f"validate.ps1 missing {marker} fix (parity)"


def test_172_pattern_parity() -> None:
    assert "*-project-architecture.md" in VALIDATE_SH.read_text(encoding="utf-8")
    assert "*-project-architecture.md" in VALIDATE_PS1.read_text(encoding="utf-8")


def test_171_ship_history_exclusion_parity() -> None:
    assert "ship-history-*" in VALIDATE_SH.read_text(encoding="utf-8")
    assert "ship-history-*" in VALIDATE_PS1.read_text(encoding="utf-8")


def test_f4_deprecated_files_pass_branch_parity() -> None:
    """F4: both validators must emit a PASS when no deprecated workflow files are
    present (previously validate.ps1 only emitted FAIL-on-present → 1-PASS skew)."""
    msg = "deprecated workflow files absent (new-feature, medium-feature, small-fix)"
    assert msg in VALIDATE_SH.read_text(encoding="utf-8")
    assert msg in VALIDATE_PS1.read_text(encoding="utf-8")


def test_validate_ps1_declares_unix_style_no_python_alias() -> None:
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8-sig")
    assert "[Alias('no-python')]" in ps1


@pytest.mark.slow
@requires_windows
@requires_powershell
def test_validate_ps1_unix_style_no_python_enters_reduced_assurance_mode() -> None:
    proc = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(VALIDATE_PS1),
            "--no-python",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(ROOT),
    )
    out = proc.stdout + proc.stderr
    assert "python checks disabled (--NoPython)" in out
    assert "Summary:" in out


def test_global_lessons_count_uses_match_count_in_ps1() -> None:
    """PowerShell must count regex matches, not the single Measure-Object result."""
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")

    assert "Measure-Object).Count" not in ps1
    assert "([regex]::Matches($csContent, '(?m)^- \\[Category:')).Count" in ps1


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_validator_count_parity_on_framework() -> None:
    """F4/F2 hardening: validate.sh and validate.ps1 must report identical
    pass/warn/fail counts on the framework repo (they previously differed by one
    PASS due to the missing deprecated-files PASS branch). Windows-only — see
    requires_windows rationale."""
    sh = _summary_counts(_run_validate(ROOT))
    ps = _summary_counts(_run_validate_ps1(ROOT))
    assert sh == ps, f"validator count parity broken: sh={sh} ps1={ps}"


# ---------------------------------------------------------------------------
# ADR-010: Frozen-Spec Lifecycle Fix — regression tests
#
# Structural (fast, no subprocess): verify the skip-condition pattern is
# identical in both validators (sh/ps1 parity).
#
# Behavioral (slow, subprocess): verify a status:frozen spec on disk NOT in
# the Spec Index does NOT FAIL the check (AC-1), and a status:shipped spec
# NOT in the index still FAILs (AC-2).
# ---------------------------------------------------------------------------

FROZEN_SPEC_SKIP_PATTERN_SH = r"draft\|frozen\|cancelled"
FROZEN_SPEC_SKIP_PATTERN_PS1 = r"draft|frozen|cancelled"
SPEC_INDEX_FAIL_MSG = "not in index"
SPEC_INDEX_PASS_MSG = "shipped/living specs are indexed"


def _minimal_current_state_with_spec_index(spec_index_entries: str = "") -> str:
    """Return a minimal current_state.md content with the given Spec Index entries."""
    return (
        "# Project Current State\n\n"
        "- **Update Sequence**: 1\n"
        "- **ADR Index**: none\n"
        f"- **Spec Index** (shipped specs at `docs/specs/`):\n{spec_index_entries}\n"
        "- **Active Backlog**: none\n"
        "\n## Global Lessons\n\nnone\n"
    )


def test_adr010_sh_skip_pattern_includes_frozen_and_cancelled() -> None:
    """validate.sh must skip status:frozen and status:cancelled (ADR-010 AC-5, structural)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    assert FROZEN_SPEC_SKIP_PATTERN_SH in sh, (
        "validate.sh must skip status:draft|frozen|cancelled (ADR-010 AC-1/AC-5)"
    )


def test_adr010_ps1_skip_pattern_includes_frozen_and_cancelled() -> None:
    """validate.ps1 must skip status:frozen and status:cancelled (ADR-010 AC-5, structural)."""
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert FROZEN_SPEC_SKIP_PATTERN_PS1 in ps1, (
        "validate.ps1 must skip status:draft|frozen|cancelled (ADR-010 AC-1/AC-5)"
    )


def test_adr010_parity_pass_message() -> None:
    """Both validators must use the same PASS message (shipped/living) for the Spec Index check."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert SPEC_INDEX_PASS_MSG in sh, "validate.sh must reference 'shipped/living' in PASS message"
    assert SPEC_INDEX_PASS_MSG in ps1, "validate.ps1 must reference 'shipped/living' in PASS message"


def _make_minimal_repo(td: Path, spec_status: str, index_entry: str = "") -> Path:
    """Set up a minimal repo layout for Spec Index behavioral tests.

    Creates:
    - docs/specs/_product-backlog.md (excluded by _* rule)
    - docs/specs/test-feature.md (with given status)
    - .agentcortex/context/current_state.md (with optional Spec Index entry)
    """
    import subprocess as sp
    target = td / "proj"
    target.mkdir()
    # Deploy the framework into the target
    result = sp.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )
    assert result.returncode == 0, f"deploy failed:\n{result.stderr}"

    # Create docs/specs dir and a test spec with the given status
    spec_dir = target / "docs" / "specs"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "_product-backlog.md").write_text(
        "# Backlog\n", encoding="utf-8"
    )
    (spec_dir / "test-feature.md").write_text(
        f"---\nstatus: {spec_status}\n---\n# Test Feature\n", encoding="utf-8"
    )

    # Write current_state.md with optional Spec Index entry
    cs = target / ".agentcortex" / "context" / "current_state.md"
    cs.write_text(
        _minimal_current_state_with_spec_index(index_entry),
        encoding="utf-8",
    )
    return target


@pytest.mark.slow
@requires_bash
def test_adr010_frozen_spec_not_indexed_does_not_fail_sh() -> None:
    """AC-1: a status:frozen spec NOT in the Spec Index must NOT FAIL validate.sh."""
    with tempfile.TemporaryDirectory() as td:
        target = _make_minimal_repo(Path(td), spec_status="frozen")
        out = _run_validate(target)
        assert SPEC_INDEX_FAIL_MSG not in out, (
            f"validate.sh must not FAIL for a status:frozen spec missing from Spec Index "
            f"(ADR-010 AC-1). Output:\n{out[-600:]}"
        )


@pytest.mark.slow
@requires_bash
def test_adr010_shipped_spec_not_indexed_fails_sh() -> None:
    """AC-2: a status:shipped spec NOT in the Spec Index must still FAIL validate.sh."""
    with tempfile.TemporaryDirectory() as td:
        target = _make_minimal_repo(Path(td), spec_status="shipped")
        out = _run_validate(target)
        assert SPEC_INDEX_FAIL_MSG in out, (
            f"validate.sh must FAIL when a status:shipped spec is missing from Spec Index "
            f"(ADR-010 AC-2). Output:\n{out[-600:]}"
        )


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_adr010_frozen_spec_not_indexed_does_not_fail_ps1() -> None:
    """AC-1/AC-5: a status:frozen spec NOT in the Spec Index must NOT FAIL validate.ps1."""
    with tempfile.TemporaryDirectory() as td:
        target = _make_minimal_repo(Path(td), spec_status="frozen")
        out = _run_validate_ps1(target)
        assert SPEC_INDEX_FAIL_MSG not in out, (
            f"validate.ps1 must not FAIL for a status:frozen spec missing from Spec Index "
            f"(ADR-010 AC-1/AC-5). Output:\n{out[-600:]}"
        )


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_adr010_shipped_spec_not_indexed_fails_ps1() -> None:
    """AC-2/AC-5: a status:shipped spec NOT in the Spec Index must still FAIL validate.ps1."""
    with tempfile.TemporaryDirectory() as td:
        target = _make_minimal_repo(Path(td), spec_status="shipped")
        out = _run_validate_ps1(target)
        assert SPEC_INDEX_FAIL_MSG in out, (
            f"validate.ps1 must FAIL when a status:shipped spec is missing from Spec Index "
            f"(ADR-010 AC-2/AC-5). Output:\n{out[-600:]}"
        )


# ---------------------------------------------------------------------------
# AC-6: current-branch gate-evidence FAIL (dev-flow-hardening spec)
#
# Structural: verify the cur_key resolution and FAIL message are present in
# both validators (fast, no subprocess).
#
# Behavioral (slow, subprocess): verify that a current-branch
# architecture-change worklog at handoff without a Resume block → FAIL (not
# WARN), while a same-content historical worklog (no git repo → curKey empty)
# → WARN (preserved invariant). Windows-only for PS1 behavioral test.
# ---------------------------------------------------------------------------

AC6_FAIL_MSG = "current-branch work log missing required gate evidence at handoff/ship"
AC6_SH_CURKEY_PATTERN = "cur_key="
AC6_PS1_CURKEY_PATTERN = "$curKey"


def test_ac6_cur_key_resolution_in_sh() -> None:
    """validate.sh must contain cur_key resolution for AC-6."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    assert AC6_SH_CURKEY_PATTERN in sh, "validate.sh missing cur_key resolution (AC-6)"


def test_ac6_cur_key_resolution_in_ps1() -> None:
    """validate.ps1 must contain $curKey resolution for AC-6."""
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert AC6_PS1_CURKEY_PATTERN in ps1, "validate.ps1 missing $curKey resolution (AC-6)"


def test_ac6_fail_message_parity() -> None:
    """Both validators must emit the same AC-6 FAIL message string."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert AC6_FAIL_MSG in sh, f"validate.sh missing AC-6 FAIL message"
    assert AC6_FAIL_MSG in ps1, f"validate.ps1 missing AC-6 FAIL message"


def _deploy_with_git_branch(td: Path, branch: str) -> Path:
    """Deploy validator fixture AND git-init the target with a named branch.

    This lets validators see a real current branch via git rev-parse --abbrev-ref HEAD,
    which is needed for AC-6 current-branch detection tests.
    """
    target = _deploy_for_validator_fixture(td)
    # Try git init -b (requires git >= 2.28); fall back to init + symbolic-ref.
    result = subprocess.run(
        ["git", "init", "-b", branch, str(target)],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        subprocess.run(["git", "init", str(target)], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(target), "symbolic-ref", "HEAD", f"refs/heads/{branch}"],
            check=True, capture_output=True,
        )
    else:
        # Verify via symbolic-ref (works on empty repos; rev-parse --abbrev-ref
        # returns "HEAD" on an empty repo with no commits).
        verify = subprocess.run(
            ["git", "-C", str(target), "symbolic-ref", "--short", "HEAD"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if verify.returncode != 0 or verify.stdout.strip() != branch:
            subprocess.run(
                ["git", "-C", str(target), "symbolic-ref", "HEAD", f"refs/heads/{branch}"],
                check=True, capture_output=True,
            )
    return target


@pytest.mark.slow
@requires_bash
def test_ac6_current_branch_arch_change_at_handoff_no_resume_fails_sh() -> None:
    """AC-6: architecture-change worklog at handoff with no Resume block on the
    current branch must emit FAIL (not WARN) from validate.sh."""
    with tempfile.TemporaryDirectory() as td:
        branch = "feat/ac6-test"
        worklog_name = "feat-ac6-test.md"  # slash→dash normalization
        target = _deploy_with_git_branch(Path(td), branch)
        _write_worklog(
            target,
            worklog_name,
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",  # pre-handoff placeholder — no ## sub-sections
        )
        out = _run_validate(target)
        assert AC6_FAIL_MSG in out, (
            f"validate.sh must FAIL for current-branch arch-change at handoff with no Resume block "
            f"(AC-6). Output:\n{out[-1200:]}"
        )
        # Must NOT appear in the WARN bucket (should be escalated to FAIL)
        assert _resume_warn_count(out) == 0 or _resume_warn_count(out) is None, (
            f"validate.sh must not WARN for current-branch Resume missing (escalated to FAIL). "
            f"Output:\n{out[-1200:]}"
        )


@pytest.mark.slow
@requires_bash
def test_ac6_historical_worklog_at_handoff_no_resume_still_warns_sh() -> None:
    """AC-6: when there is NO git repo (historical / offline fixture), an
    architecture-change worklog at handoff with no Resume must still emit WARN
    (not FAIL) — preserving the existing invariant (_resume_warn_count == 1)."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_worklog(
            target,
            "handoff-resume-missing.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",
        )
        out = _run_validate(target)
        assert _resume_warn_count(out) == 1, (
            f"validate.sh must still WARN (not FAIL) for historical worklog with incomplete Resume "
            f"(no git repo → curKey empty → AC-6 FAIL must not fire). Output:\n{out[-1200:]}"
        )
        assert AC6_FAIL_MSG not in out, (
            f"validate.sh must not emit AC-6 FAIL for historical (no git repo) worklog. "
            f"Output:\n{out[-1200:]}"
        )


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_ac6_current_branch_arch_change_at_handoff_no_resume_fails_ps1() -> None:
    """AC-6 parity: same scenario as the sh test but via validate.ps1."""
    with tempfile.TemporaryDirectory() as td:
        branch = "feat/ac6-test"
        worklog_name = "feat-ac6-test.md"
        target = _deploy_with_git_branch(Path(td), branch)
        _write_worklog(
            target,
            worklog_name,
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",
        )
        out = _run_validate_ps1(target)
        assert AC6_FAIL_MSG in out, (
            f"validate.ps1 must FAIL for current-branch arch-change at handoff with no Resume block "
            f"(AC-6). Output:\n{out[-1200:]}"
        )
        assert _resume_warn_count(out) == 0 or _resume_warn_count(out) is None, (
            f"validate.ps1 must not WARN for current-branch Resume missing (escalated to FAIL). "
            f"Output:\n{out[-1200:]}"
        )


# ---------------------------------------------------------------------------
# D4: INDEX.jsonl referenced-file existence (governance self-audit).
# The hash chain + git witness prove entries are append-only and unedited, but
# neither verifies each entry's `log` artifact still exists on disk. D4 surfaces
# a dangling reference (entry present, file gone) as a WARN in BOTH validators.
#
# D5: a current-branch log claiming legacy status (Created Date < cutoff) but
# missing gate evidence cannot legitimately be pre-Runtime-v4 — the legacy WARN
# downgrade is denied (FAIL-tier miss) in BOTH validators.
# ---------------------------------------------------------------------------

D4_INDEX_REF_WARN = "INDEX.jsonl referenced logs missing on disk"


def test_d4_index_ref_check_present_in_both_validators() -> None:
    """D4 dangling-reference check must exist in sh and ps1 (parity, structural)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert D4_INDEX_REF_WARN in sh, "validate.sh must carry the D4 INDEX referenced-file check"
    assert D4_INDEX_REF_WARN in ps1, "validate.ps1 must carry the D4 INDEX referenced-file check"


def test_d5_current_branch_legacy_guard_present_in_both_validators() -> None:
    """D5 current-branch-cannot-be-legacy guard must exist in sh and ps1 (parity, structural)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert 'is_current_branch" -eq 0' in sh, (
        "validate.sh legacy gate-evidence exemption must be guarded by NOT current-branch (D5)"
    )
    assert "-not $isCurrentBranch" in ps1, (
        "validate.ps1 legacy gate-evidence exemption must be guarded by NOT current-branch (D5)"
    )


def _seed_index_jsonl(target: Path, log_name: str, *, create_file: bool) -> None:
    """Write a minimal 1-entry archive/INDEX.jsonl referencing log_name.

    D4 only reads the `log` field and checks disk existence, so a valid hash
    chain is not required for this check (unrelated audit-chain output, if any,
    does not remove the D4 line)."""
    archive = target / ".agentcortex" / "context" / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "INDEX.jsonl").write_text(
        '{"log": "%s", "prev_sha": "GENESIS", "branch": "test", "shipped": "2026-07-02"}\n' % log_name,
        encoding="utf-8", newline="\n",
    )
    if create_file:
        (archive / log_name).write_text("# archived fixture log\n", encoding="utf-8", newline="\n")


@pytest.mark.slow
@requires_bash
def test_d4_dangling_index_ref_warns_sh() -> None:
    """A dangling INDEX `log` reference (file absent on disk) must WARN in validate.sh."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _seed_index_jsonl(target, "never-committed-log-20260702.md", create_file=False)
        out = _run_validate(target)
        assert D4_INDEX_REF_WARN in out, (
            f"validate.sh must WARN on a dangling INDEX reference (D4). Output:\n{out[-800:]}"
        )


@pytest.mark.slow
@requires_bash
def test_d4_present_index_ref_no_warn_sh() -> None:
    """An INDEX `log` reference whose file exists must NOT trigger the D4 dangling WARN."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _seed_index_jsonl(target, "present-log-20260702.md", create_file=True)
        out = _run_validate(target)
        assert D4_INDEX_REF_WARN not in out, (
            f"validate.sh must NOT WARN when every INDEX reference resolves on disk (D4). "
            f"Output:\n{out[-800:]}"
        )
