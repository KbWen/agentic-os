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
# Spec Index reverse/phantom check — format-robust path extraction.
#
# The reverse check ("indexed spec path no longer on disk") extracted paths
# with a bracket-anchored pattern that required "] " BEFORE the .md path. Real
# Spec Index entries put the path BEFORE the [Shipped] tag
# (`- docs/specs/X.md — ..., [Shipped ...]`), so the pattern matched nothing and
# the check was silently dead — a deleted-but-still-indexed spec PASSed. Fix:
# anchor extraction on the spec dirs (docs/specs | .agentcortex/specs), mirroring
# the ADR reverse check. Surfaced by behavioral simulation, not by reading.
# ---------------------------------------------------------------------------

SPEC_PHANTOM_FAIL_MSG = "not on disk"
# Real-repo entry format: the path precedes the [Shipped] tag (the format the
# old bracket-anchored extraction was blind to).
_REALFMT_GHOST_ENTRY = (
    "  - docs/specs/ghost-does-not-exist.md — Sim ghost, [Shipped 2026-01-01] (backlog #0)\n"
)
_REALFMT_REAL_ENTRY = (
    "  - docs/specs/test-feature.md — Sim real, [Shipped 2026-01-01] (backlog #0)\n"
)


def test_spec_phantom_extraction_format_robust_sh() -> None:
    """validate.sh must extract indexed spec paths anchored on the spec dirs,
    not on a preceding ']' (dead-check regression guard)."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    assert r"(docs/specs|\.agentcortex/specs)/[^[:space:]]+\.md" in sh, (
        "validate.sh spec phantom extraction must anchor on the spec dirs"
    )
    assert r"sed -n 's/.*\] \([^ ]*\.md\) .*/\1/p'" not in sh, (
        "validate.sh must not use the dead bracket-anchored phantom extraction"
    )


def test_spec_phantom_extraction_format_robust_ps1() -> None:
    """validate.ps1 must extract indexed spec paths anchored on the spec dirs
    (sh/ps1 parity)."""
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert r"(?:docs/specs|\.agentcortex/specs)/[\w./-]+\.md" in ps1, (
        "validate.ps1 spec phantom extraction must anchor on the spec dirs"
    )
    assert r"'(?m)\]\s+([\w./-]+\.md)\s'" not in ps1, (
        "validate.ps1 must not use the dead bracket-anchored phantom extraction"
    )


@pytest.mark.slow
@requires_bash
def test_spec_phantom_realfmt_deleted_spec_fails_sh() -> None:
    """A Spec Index entry (real format: path before [Shipped]) pointing to a
    spec NOT on disk must FAIL validate.sh's reverse check."""
    with tempfile.TemporaryDirectory() as td:
        # test-feature.md is status:frozen → skipped by the forward check, so
        # only the phantom (ghost) entry can drive the FAIL.
        target = _make_minimal_repo(
            Path(td), spec_status="frozen", index_entry=_REALFMT_GHOST_ENTRY
        )
        out = _run_validate(target)
        assert SPEC_PHANTOM_FAIL_MSG in out, (
            "validate.sh must FAIL when an indexed spec path (real format) is not "
            f"on disk. Output:\n{out[-600:]}"
        )


@pytest.mark.slow
@requires_bash
def test_spec_phantom_realfmt_existing_spec_passes_sh() -> None:
    """A Spec Index entry (real format) pointing to a spec that DOES exist on
    disk must NOT trigger a phantom FAIL (no false positive)."""
    with tempfile.TemporaryDirectory() as td:
        target = _make_minimal_repo(
            Path(td), spec_status="shipped", index_entry=_REALFMT_REAL_ENTRY
        )
        out = _run_validate(target)
        assert SPEC_PHANTOM_FAIL_MSG not in out, (
            "validate.sh must NOT phantom-FAIL a real-format entry whose spec "
            f"exists on disk. Output:\n{out[-600:]}"
        )


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_spec_phantom_realfmt_deleted_spec_fails_ps1() -> None:
    """sh/ps1 parity: a real-format indexed spec not on disk must FAIL validate.ps1."""
    with tempfile.TemporaryDirectory() as td:
        target = _make_minimal_repo(
            Path(td), spec_status="frozen", index_entry=_REALFMT_GHOST_ENTRY
        )
        out = _run_validate_ps1(target)
        assert SPEC_PHANTOM_FAIL_MSG in out, (
            "validate.ps1 must FAIL when an indexed spec path (real format) is not "
            f"on disk. Output:\n{out[-600:]}"
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


def test_ps1_d4_passes_index_path_as_argv_not_source_interpolation() -> None:
    """F1: validate.ps1 D4 must pass the INDEX path via sys.argv, NOT interpolate it
    into the Python source (a repo path with an apostrophe would crash the child and
    silently mask a dangling ref to PASS on Windows). validate.sh was always argv-based."""
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    assert "idx = r'" not in ps1, (
        "validate.ps1 must NOT interpolate the INDEX path into the D4 Python source "
        "(apostrophe-path SyntaxError → empty output → false PASS)"
    )
    assert "idx = sys.argv[1]" in ps1, "validate.ps1 D4 must read the INDEX path from sys.argv[1]"
    # Empty/errored child output must NOT silently default to PASS.
    assert "referenced-file check did not run" in ps1, (
        "validate.ps1 D4 must WARN (not PASS) when the child produces empty/unrecognized output"
    )


def test_created_date_parser_accepts_non_bold_forms_in_both_validators() -> None:
    """F2: the Created Date parser must accept list/backtick/table forms, not bold-only.
    The template + all real logs use plain/backtick form; a bold-only parser left the
    legacy gate-evidence exemption (and its D5 refinement) as dead code."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    # The bold-only anchors must be gone (replaced by bold-optional `\*{0,2}`).
    assert r"s/^- \*\*Created Date\*\*:" not in sh, "validate.sh Created Date parser must not be bold-only (F2)"
    assert r"'(?m)^- \*\*Created Date\*\*:\s*(.+)$'" not in ps1, "validate.ps1 Created Date parser must not be bold-only (F2)"
    assert r"Created Date\*{0,2}" in sh, "validate.sh Created Date parser must accept bold-optional form (F2)"
    assert r"Created Date\*{0,2}" in ps1, "validate.ps1 Created Date parser must accept bold-optional form (F2)"


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


# ---------------------------------------------------------------------------
# HANDEDOFF->IMPLEMENTING reverse edge (state_machine.md §Allowed Transitions:
# "ship Entry Condition fail; code change required"): a feature log that loops
# handoff -> (ship NOT READY) -> implement -> review -> test -> handoff must
# NOT flag illegal gate progression. Pre-fix, LEGAL_STRICT['handoff'] lacked
# 'implement' and the documented reverse edge was unrepresentable.
# ---------------------------------------------------------------------------

ILLEGAL_PROGRESSION_MARK = "illegal gate progression"


def _write_handoff_reverse_edge_worklog(target: Path) -> None:
    work_dir = target / ".agentcortex" / "context" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    stamp = "2026-07-04T0{i}:00:00Z"
    gate_lines = "\n".join(
        [
            f"- Gate: {g} | Verdict: PASS | Classification: feature | Timestamp: {stamp.format(i=i)}"
            for i, g in enumerate(
                ("bootstrap", "plan", "implement", "review", "test", "handoff")
            )
        ]
        + [
            "- Gate: ship | Verdict: NOT READY | Transition: HANDEDOFF->IMPLEMENTING | Classification: feature | Timestamp: 2026-07-04T06:00:00Z"
        ]
        + [
            f"- Gate: {g} | Verdict: PASS | Classification: feature | Timestamp: 2026-07-04T0{i + 7}:00:00Z"
            for i, g in enumerate(("implement", "review", "test", "handoff"))
        ]
    )
    (work_dir / "feature-reverse-edge.md").write_text(
        f"""# Work Log: feature-reverse-edge

## Header

- Branch: `test/feature-reverse-edge`
- Classification: `feature`
- Current Phase: `handoff`
- Checkpoint SHA: `0000000000000000000000000000000000000000`

---

## Phase Summary

Reverse-edge fixture (ship gate-entry NOT READY -> implement loop). ACX

---

## Gate Evidence

{gate_lines}

---

## Drift Log

- ADR Coverage Check: test fixture.
- Reverse edge: ship Entry Condition fail -> HANDEDOFF->IMPLEMENTING per state_machine.md.

---

## Resume

- State: HANDEDOFF
- Completed: fixture
- Next: ship
- Context: fixture

### Read Map (for next agent)
- fixture.md -> full

### Skip List
- none

### Context Snapshot (<= 200 tokens)
fixture

---

## Evidence

- Fixture evidence.
""",
        encoding="utf-8",
        newline="\n",
    )


@requires_bash
@pytest.mark.slow
def test_handoff_implement_reverse_edge_not_illegal_sh() -> None:
    """validate.sh: the HANDEDOFF->IMPLEMENTING reverse-edge loop is legal."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_handoff_reverse_edge_worklog(target)
        out = _run_validate(target)
        assert "handoff->implement" not in out, (
            f"handoff->implement flagged illegal despite state_machine.md reverse edge:\n{out[-800:]}"
        )
        assert ILLEGAL_PROGRESSION_MARK not in out, (
            f"unexpected illegal-progression FAIL for reverse-edge fixture:\n{out[-800:]}"
        )


@requires_bash
@pytest.mark.slow
def test_handoff_ship_skip_review_still_illegal_sh() -> None:
    """Negative control: the reverse edge must NOT weaken the M10 stale-review
    guard — implement after handoff followed directly by ship (no re-review)
    stays illegal."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_worklog(
            target,
            "feature-reverse-edge-bad.md",
            classification="feature",
            phase="ship",
            gates=(
                "bootstrap", "plan", "implement", "review", "test", "handoff",
                "implement", "ship",
            ),
            resume="- State: fixture\n\n### Read Map (for next agent)\n- x\n\n### Skip List\n- x\n\n### Context Snapshot (<= 200 tokens)\nx",
        )
        out = _run_validate(target)
        assert ILLEGAL_PROGRESSION_MARK in out, (
            f"implement->ship after reverse edge must stay illegal (stale review):\n{out[-800:]}"
        )


@requires_powershell
@requires_windows
@pytest.mark.slow
def test_handoff_implement_reverse_edge_not_illegal_ps1() -> None:
    """validate.ps1 parity: the HANDEDOFF->IMPLEMENTING reverse-edge loop is legal."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_handoff_reverse_edge_worklog(target)
        out = _run_validate_ps1(target)
        assert "handoff->implement" not in out, (
            f"[ps1] handoff->implement flagged illegal despite state_machine.md reverse edge:\n{out[-800:]}"
        )
        assert ILLEGAL_PROGRESSION_MARK not in out, (
            f"[ps1] unexpected illegal-progression FAIL for reverse-edge fixture:\n{out[-800:]}"
        )


# ---------------------------------------------------------------------------
# NOT-READY re-review remediation hint: a feature log that goes
# bootstrap/plan/implement PASS -> review NOT READY -> review PASS with NO
# fresh implement between the NOT READY and the re-review PASS is STILL an
# illegal edge (the reverse edge pops the implement, leaving plan->review).
# The message must now name the exact remedy (a fresh implement PASS receipt
# before the re-review PASS, review.md §Reverse Transition) — message-only
# change; the FAIL verdict is preserved.
# ---------------------------------------------------------------------------

# ASCII-only substrings (survive any child-process encoding on Windows).
NOT_READY_HINT = "NOT READY re-review: add a fresh"
NOT_READY_HINT_REMEDY = "receipt for the fix BEFORE the re-review PASS"


def _write_not_ready_re_review_worklog(target: Path) -> None:
    work_dir = target / ".agentcortex" / "context" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    gate_lines = "\n".join(
        [
            f"- Gate: {g} | Verdict: PASS | Classification: feature | Timestamp: 2026-07-10T0{i}:00:00Z"
            for i, g in enumerate(("bootstrap", "plan", "implement"))
        ]
        + [
            "- Gate: review | Verdict: NOT READY | Classification: feature | Timestamp: 2026-07-10T03:00:00Z",
            "- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-07-10T04:00:00Z",
        ]
    )
    (work_dir / "feature-not-ready-re-review.md").write_text(
        f"""# Work Log: feature-not-ready-re-review

## Header

- Branch: `test/feature-not-ready-re-review`
- Classification: `feature`
- Current Phase: `review`
- Checkpoint SHA: `0000000000000000000000000000000000000000`

---

## Phase Summary

NOT-READY re-review fixture (no fresh implement before re-review PASS). ACX

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
""",
        encoding="utf-8",
        newline="\n",
    )


@requires_bash
@pytest.mark.slow
def test_not_ready_re_review_hint_sh() -> None:
    """validate.sh: the illegal ...->review edge after a NOT-READY re-review
    (no fresh implement) STILL FAILs, but now names the remedy."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_not_ready_re_review_worklog(target)
        out = _run_validate(target)
        assert ILLEGAL_PROGRESSION_MARK in out, (
            f"NOT-READY re-review without fresh implement must stay illegal (FAIL preserved):\n{out[-800:]}"
        )
        assert NOT_READY_HINT in out and NOT_READY_HINT_REMEDY in out, (
            f"illegal ...->review edge after NOT READY must print the remediation hint:\n{out[-800:]}"
        )
        assert "review.md" in out, (
            f"remediation hint must cite review.md (Reverse Transition):\n{out[-800:]}"
        )


@requires_powershell
@requires_windows
@pytest.mark.slow
def test_not_ready_re_review_hint_ps1() -> None:
    """validate.ps1 parity: same NOT-READY re-review remediation hint."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        _write_not_ready_re_review_worklog(target)
        out = _run_validate_ps1(target)
        assert ILLEGAL_PROGRESSION_MARK in out, (
            f"[ps1] NOT-READY re-review without fresh implement must stay illegal:\n{out[-800:]}"
        )
        assert NOT_READY_HINT in out and NOT_READY_HINT_REMEDY in out, (
            f"[ps1] illegal ...->review edge after NOT READY must print the remediation hint:\n{out[-800:]}"
        )


def test_not_ready_re_review_hint_source_parity() -> None:
    """Source parity (fast, no shell): both validators carry the identical
    NOT-READY remediation hint text + the review.md §Reverse Transition cite."""
    sh = (ROOT / ".agentcortex" / "bin" / "validate.sh").read_text(encoding="utf-8")
    ps1 = (ROOT / ".agentcortex" / "bin" / "validate.ps1").read_text(encoding="utf-8")
    for src, label in ((sh, "validate.sh"), (ps1, "validate.ps1")):
        assert NOT_READY_HINT in src, f"{label} missing NOT-READY remediation hint"
        assert NOT_READY_HINT_REMEDY in src, f"{label} missing remedy phrasing"
        assert "review.md §Reverse Transition" in src, f"{label} missing review.md §Reverse Transition cite"


# ---------------------------------------------------------------------------
# 2026-07-11 receipt-integrity audit (docs/reviews/2026-07-11-govern-audit-
# receipt-integrity.md): F10 canonical Work Log key normalization, F7 receipt
# Timestamp requirement, F9 receipt/header Classification agreement, F8
# Checkpoint SHA / Diff Base SHA value-shape + resolvability validation.
# ---------------------------------------------------------------------------

GATE_SCHEMA_WARN = "active work log gate receipts with schema violations"
CHECKPOINT_SHA_WARN_MSG = "invalid Checkpoint SHA value"
DIFF_BASE_SHA_WARN_MSG = "invalid Diff Base SHA value"


def _write_receipt_schema_worklog(
    target: Path,
    name: str,
    *,
    header_classification: str,
    gate_lines: str,
    checkpoint_sha: str = "0000000000000000000000000000000000000000",
    extra_header: str = "",
) -> None:
    """Minimal Work Log fixture for F7/F8/F9 receipt-schema tests — a leaner
    header than `_write_worklog` so tests can inject a deliberately malformed
    Classification header, an overridden Checkpoint SHA, an extra Diff Base
    SHA line (via extra_header), or omit Timestamp from individual receipts.
    NOTE: Checkpoint SHA has exactly ONE emission site (the `checkpoint_sha`
    param) — do NOT also inject a "- Checkpoint SHA:" line via extra_header,
    or validate.sh/.ps1's `grep -m1` / first-match extraction will silently
    prefer whichever line comes first, masking the intended override."""
    work_dir = target / ".agentcortex" / "context" / "work"
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / name).write_text(
        f"""# Work Log: {name}

## Header

- Branch: `test/{name}`
- Classification: `{header_classification}`
- Current Phase: `ship`
- Checkpoint SHA: `{checkpoint_sha}`
{extra_header}
---

## Phase Summary

Receipt-schema fixture. ACX

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
""",
        encoding="utf-8",
        newline="\n",
    )


# --- F10: canonical Work Log key normalization ------------------------------
#
# bootstrap.md:123-131 canonical algorithm: (1) chars outside [a-zA-Z0-9._-]
# -> '-', (2) collapse '-' runs, (3) strip leading/trailing '-'/'.',
# (4) lowercase, (5) truncate to 100 chars. Branch "Feat/Add##Auth-" exercises
# steps 1 (slash + double-hash -> dashes), 2 (collapse), 3 (trailing-dash
# trim), and 4 (lowercase) all at once; canonical key = "feat-add-auth".

F10_COMBINED_BRANCH = "Feat/Add##Auth-"
F10_COMBINED_KEY = "feat-add-auth"


@pytest.mark.slow
@requires_bash
def test_f10_combined_normalization_current_log_detected_as_current_sh() -> None:
    """An uppercase + punctuated + trailing-dash branch must still canonicalize
    to its documented Work Log key and be detected as the CURRENT-branch log —
    missing Resume at handoff must FAIL (not WARN). Reproduces the audit's
    exact failure mode (case-sensitive compare in bash) plus the punctuation
    gap the case-only reproduction did not cover."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_with_git_branch(Path(td), F10_COMBINED_BRANCH)
        _write_worklog(
            target,
            f"{F10_COMBINED_KEY}.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",
        )
        out = _run_validate(target)
        assert AC6_FAIL_MSG in out, (
            f"validate.sh must detect the canonical log as CURRENT for a "
            f"combined uppercase/punctuation/trailing-dash branch (F10). "
            f"Output:\n{out[-1200:]}"
        )
        assert _resume_warn_count(out) == 0 or _resume_warn_count(out) is None, (
            f"validate.sh must not WARN (downgrade) once F10 is fixed. Output:\n{out[-1200:]}"
        )


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_f10_combined_normalization_current_log_detected_as_current_ps1() -> None:
    """validate.ps1 parity. PowerShell's -eq/-like are already case-insensitive
    (masking the case half pre-fix), but punctuation was NOT normalized on
    either platform before F10 — this branch still discriminates old vs new
    ps1 behavior via the double-hash + trailing-dash steps."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_with_git_branch(Path(td), F10_COMBINED_BRANCH)
        _write_worklog(
            target,
            f"{F10_COMBINED_KEY}.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",
        )
        out = _run_validate_ps1(target)
        assert AC6_FAIL_MSG in out, (
            f"validate.ps1 must detect the canonical log as CURRENT for a "
            f"combined uppercase/punctuation/trailing-dash branch (F10 parity). "
            f"Output:\n{out[-1200:]}"
        )
        assert _resume_warn_count(out) == 0 or _resume_warn_count(out) is None, (
            f"validate.ps1 must not WARN (downgrade) once F10 is fixed. Output:\n{out[-1200:]}"
        )


@pytest.mark.slow
@requires_bash
def test_f10_non_matching_log_stays_historical_warn_sh() -> None:
    """Negative control: a Work Log that does NOT match the (correctly
    normalized) current-branch key must stay a historical WARN, not escalate
    to FAIL — proves F10 did not make detection overly permissive."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_with_git_branch(Path(td), F10_COMBINED_BRANCH)
        _write_worklog(
            target,
            "totally-unrelated-branch-log.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",
        )
        out = _run_validate(target)
        assert AC6_FAIL_MSG not in out, (
            f"validate.sh must NOT FAIL for a log that doesn't match the "
            f"current-branch key. Output:\n{out[-1200:]}"
        )
        assert _resume_warn_count(out) == 1, (
            f"non-matching log must still WARN as historical. Output:\n{out[-1200:]}"
        )


@pytest.mark.slow
@requires_bash
def test_f10_truncation_100_chars_current_log_detected_as_current_sh() -> None:
    """Step 5: a >100-char branch name canonicalizes to a 100-char-truncated
    key, and that truncated filename is still detected as CURRENT."""
    long_branch = "feat/" + ("x" * 105)  # "feat-" (5) + 105 x's = 110 raw chars
    truncated_key = ("feat-" + ("x" * 105))[:100]
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_with_git_branch(Path(td), long_branch)
        _write_worklog(
            target,
            f"{truncated_key}.md",
            classification="architecture-change",
            phase="handoff",
            gates=("bootstrap", "plan", "implement", "review", "test", "handoff"),
            resume="none",
        )
        out = _run_validate(target)
        assert AC6_FAIL_MSG in out, (
            f"validate.sh must truncate a >100-char branch to 100 chars and still "
            f"detect the resulting log as CURRENT (F10 step 5). Output:\n{out[-1200:]}"
        )


def test_f10_source_parity_five_step_normalization() -> None:
    """Structural (fast, no subprocess): both validators must implement all 5
    canonical normalization steps, not just slash->dash."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    # step 1: replace non-conforming chars with '-'
    assert "[^a-zA-Z0-9._-]" in sh, "validate.sh missing F10 step-1 char-class replacement"
    assert "[^a-zA-Z0-9._-]" in ps1, "validate.ps1 missing F10 step-1 char-class replacement"
    # step 2: collapse consecutive dashes
    assert "-+" in sh, "validate.sh missing F10 step-2 dash-collapse"
    # step 4: lowercase
    assert "tr '[:upper:]' '[:lower:]'" in sh, "validate.sh cur_key must lowercase (F10 step 4)"
    assert "ToLowerInvariant()" in ps1, "validate.ps1 curKey must lowercase (F10 step 4)"
    # step 5: truncate to 100 chars
    assert "cut -c1-100" in sh, "validate.sh cur_key must truncate to 100 chars (F10 step 5)"
    assert "Substring(0, 100)" in ps1, "validate.ps1 curKey must truncate to 100 chars (F10 step 5)"
    # filename comparison must be explicitly case-insensitive on both sides
    assert 'wl_basename="$(basename "$wl" | tr' in sh, (
        "validate.sh must lowercase wl_basename before comparing (F10 defense)"
    )
    assert "GetFileName($wl.FullName).ToLowerInvariant()" in ps1, (
        "validate.ps1 must lowercase wlBasename before comparing (F10 defense)"
    )


# --- F7: receipt Timestamp requirement --------------------------------------


@pytest.mark.slow
@requires_bash
def test_f7_missing_timestamp_warns_sh() -> None:
    """F7: a receipt with no Timestamp: field must trigger the schema WARN."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "\n".join([
            "- Gate: bootstrap | Verdict: PASS | Classification: quick-win",
            "- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z",
        ])
        _write_receipt_schema_worklog(
            target, "f7-missing-timestamp.md",
            header_classification="quick-win", gate_lines=gate_lines,
        )
        out = _run_validate(target)
        assert GATE_SCHEMA_WARN in out, out[-1200:]
        assert "missing/unparseable Timestamp" in out, out[-1200:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_f7_missing_timestamp_warns_ps1() -> None:
    """validate.ps1 parity for F7."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win"
        _write_receipt_schema_worklog(
            target, "f7-missing-timestamp.md",
            header_classification="quick-win", gate_lines=gate_lines,
        )
        out = _run_validate_ps1(target)
        assert GATE_SCHEMA_WARN in out, out[-1200:]
        assert "missing/unparseable Timestamp" in out, out[-1200:]


@pytest.mark.slow
@requires_bash
def test_f7_date_only_timestamp_accepted_sh() -> None:
    """F7: a date-only ISO Timestamp (no time component) is accepted — the
    audit's acceptance criterion explicitly permits a bare YYYY-MM-DD."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11"
        _write_receipt_schema_worklog(
            target, "f7-date-only.md",
            header_classification="quick-win", gate_lines=gate_lines,
        )
        out = _run_validate(target)
        assert "missing/unparseable Timestamp" not in out, out[-1200:]


# --- F9: receipt Classification must agree with header Classification -------


@pytest.mark.slow
@requires_bash
def test_f9_classification_mismatch_warns_sh() -> None:
    """F9: a receipt claiming a different Classification than the header must WARN."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: tiny-fix | Timestamp: 2026-07-11T00:00:00Z"
        _write_receipt_schema_worklog(
            target, "f9-mismatch.md",
            header_classification="feature", gate_lines=gate_lines,
        )
        out = _run_validate(target)
        assert GATE_SCHEMA_WARN in out, out[-1200:]
        assert "differs from header Classification" in out, out[-1200:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_f9_classification_mismatch_warns_ps1() -> None:
    """validate.ps1 parity for F9."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: tiny-fix | Timestamp: 2026-07-11T00:00:00Z"
        _write_receipt_schema_worklog(
            target, "f9-mismatch.md",
            header_classification="feature", gate_lines=gate_lines,
        )
        out = _run_validate_ps1(target)
        assert GATE_SCHEMA_WARN in out, out[-1200:]
        assert "differs from header Classification" in out, out[-1200:]


@pytest.mark.slow
@requires_bash
def test_f9_unfilled_header_classification_not_compared_sh() -> None:
    """F9: an unfilled/malformed header Classification (still the literal
    template placeholder — the exact state of two real active Work Logs in
    this repo at audit time) must NOT be compared; nothing meaningful to
    compare against, so it must not spuriously WARN."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z"
        _write_receipt_schema_worklog(
            target, "f9-unfilled-header.md",
            header_classification="<tiny-fix | quick-win | hotfix | feature | architecture-change>",
            gate_lines=gate_lines,
        )
        out = _run_validate(target)
        assert "differs from header Classification" not in out, out[-1200:]


@pytest.mark.slow
@requires_bash
def test_f9_matching_classification_no_warn_sh() -> None:
    """Regression guard: receipts whose Classification agrees with the header
    must not warn (the common case — every real receipt in this repo today)."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "\n".join([
            "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z",
            "- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:05:00Z",
        ])
        _write_receipt_schema_worklog(
            target, "f9-matching.md",
            header_classification="quick-win", gate_lines=gate_lines,
        )
        out = _run_validate(target)
        assert GATE_SCHEMA_WARN not in out, out[-1200:]


# --- F8: Checkpoint SHA / Diff Base SHA value-shape + resolvability ---------


@pytest.mark.slow
@requires_bash
def test_f8_invalid_checkpoint_sha_warns_sh() -> None:
    """F8: a non-hex, non-placeholder Checkpoint SHA value must WARN — the
    audit's exact repro value ('not-a-sha')."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z"
        _write_receipt_schema_worklog(
            target, "f8-bad-sha.md",
            header_classification="quick-win", gate_lines=gate_lines,
            checkpoint_sha="not-a-sha",
        )
        out = _run_validate(target)
        assert CHECKPOINT_SHA_WARN_MSG in out, out[-1200:]


@pytest.mark.slow
@requires_windows
@requires_bash
@requires_powershell
def test_f8_invalid_checkpoint_sha_warns_ps1() -> None:
    """validate.ps1 parity for F8."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z"
        _write_receipt_schema_worklog(
            target, "f8-bad-sha.md",
            header_classification="quick-win", gate_lines=gate_lines,
            checkpoint_sha="not-a-sha",
        )
        out = _run_validate_ps1(target)
        assert CHECKPOINT_SHA_WARN_MSG in out, out[-1200:]


@pytest.mark.slow
@requires_bash
def test_f8_accepted_placeholders_no_warn_sh() -> None:
    """F8: 'none', 'pending-commit', and the unfilled template default must
    NOT warn — observed legitimate placeholders (grepped from this repo's real
    active/archived Work Logs and templates/worklog.md before implementing)."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        work_dir = target / ".agentcortex" / "context" / "work"
        for i, val in enumerate(["none", "pending-commit", "<git-sha or none>", "abc1234"]):
            gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z"
            _write_receipt_schema_worklog(
                target, f"f8-placeholder-{i}.md",
                header_classification="quick-win", gate_lines=gate_lines,
                checkpoint_sha=val,
            )
        out = _run_validate(target)
        assert CHECKPOINT_SHA_WARN_MSG not in out, out[-1200:]


@pytest.mark.slow
@requires_bash
def test_f8_unresolvable_current_branch_sha_warns_but_historical_does_not_sh() -> None:
    """F8: a well-formed but non-existent SHA on the CURRENT-branch log must
    WARN (resolvability check, git rev-parse --verify); the identical value on
    a non-current (historical) log must NOT trigger resolvability — shape-only
    (squash/rebase legitimately invalidates old SHAs)."""
    branch = "feat/f8-resolve-test"
    current_log = "feat-f8-resolve-test.md"
    fake_sha = "deadbeefcafe"  # well-formed hex, does not resolve to a real commit
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_with_git_branch(Path(td), branch)
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z"
        for name in (current_log, "historical-other-branch.md"):
            _write_receipt_schema_worklog(
                target, name,
                header_classification="quick-win", gate_lines=gate_lines,
                checkpoint_sha=fake_sha,
            )
        out = _run_validate(target)
        assert out.count(f"unresolvable Checkpoint SHA ('{fake_sha}')") == 1, (
            f"exactly one (the current-branch) log must get the resolvability WARN:\n{out[-1500:]}"
        )
        assert f"unresolvable Checkpoint SHA ('{fake_sha}') in {current_log}" in out, (
            f"the resolvability WARN must name the current-branch log:\n{out[-1500:]}"
        )
        assert f"unresolvable Checkpoint SHA ('{fake_sha}') in historical-other-branch.md" not in out, (
            f"the non-current-branch log must NOT get the resolvability WARN (shape-only):\n{out[-1500:]}"
        )


@pytest.mark.slow
@requires_bash
def test_f8_diff_base_sha_invalid_value_warns_sh() -> None:
    """F8: Diff Base SHA gets the same value treatment as Checkpoint SHA even
    though (verified before implementing) it has no pre-existing presence
    check in either validator."""
    with tempfile.TemporaryDirectory() as td:
        target = _deploy_for_validator_fixture(Path(td))
        gate_lines = "- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z"
        _write_receipt_schema_worklog(
            target, "f8-bad-diffbase.md",
            header_classification="quick-win", gate_lines=gate_lines,
            checkpoint_sha="none",
            extra_header="- Diff Base SHA: `also-not-a-sha`\n",
        )
        out = _run_validate(target)
        assert DIFF_BASE_SHA_WARN_MSG in out, out[-1200:]


def test_f8_source_parity_accepted_vocabulary_and_resolvability() -> None:
    """Structural (fast, no subprocess): both validators must accept the same
    placeholder vocabulary and both must resolvability-check via `git
    rev-parse --verify ...^{commit}`, gated on the current-branch flag."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    for token in ("pending-commit", "<git-sha or none>", "rev-parse --verify"):
        assert token in sh, f"validate.sh missing F8 token: {token!r}"
        assert token in ps1, f"validate.ps1 missing F8 token: {token!r}"
    assert "Diff Base SHA" in sh and "Diff Base SHA" in ps1, (
        "both validators must extend value-validation to Diff Base SHA (F8)"
    )


def test_f7_f9_source_parity_messages() -> None:
    """Structural (fast, no subprocess): both validators must emit the same
    F7/F9 violation message substrings."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    for token in ("missing/unparseable Timestamp", "differs from header Classification"):
        assert token in sh, f"validate.sh missing token: {token!r}"
        assert token in ps1, f"validate.ps1 missing token: {token!r}"
