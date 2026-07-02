"""Structural regression tests for CI hardening (#163).

Locks the reproducibility/hygiene wiring so a careless edit can't silently
un-pin the CI deps, drop pip caching, lose the UTF-8 default, or revert to the
old ad-hoc `pip install pyyaml pytest`. Mirrors the structural style of
test_security_workflow.py. Pure-Python (CI-safe on Linux).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYTEST_INI = ROOT / "pytest.ini"
REQS = ROOT / ".github" / "requirements-ci.txt"
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
SECURITY_WORKFLOW = ROOT / ".github" / "workflows" / "security.yml"


def test_requirements_file_pins_test_deps() -> None:
    assert REQS.exists(), ".github/requirements-ci.txt must exist (#163)"
    lines = [ln.strip() for ln in REQS.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.strip().startswith("#")]
    pkgs = {re.split(r"[=<>!~]", ln, maxsplit=1)[0].lower(): ln for ln in lines}
    for required in ("pytest", "pyyaml"):
        assert required in pkgs, f"requirements-ci.txt must list {required}"
        assert "==" in pkgs[required], f"{required} must be pinned with '==' (got: {pkgs[required]})"


def test_workflow_installs_from_pinned_requirements() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "pip install -r .github/requirements-ci.txt" in txt, \
        "CI must install from the pinned requirements file (#163)"
    assert "pip install pyyaml pytest" not in txt, \
        "CI must not reintroduce the ad-hoc unpinned install (#163)"


def test_workflow_enables_pip_cache() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "cache: 'pip'" in txt, "CI must enable pip caching (#163)"
    assert "cache-dependency-path: .github/requirements-ci.txt" in txt, \
        "pip cache must key on the requirements file (#163)"


def test_workflow_forces_utf8() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r"PYTHONUTF8:\s*[\"']?1", txt), \
        "CI must export PYTHONUTF8=1 for cross-platform encoding safety (#163)"


def test_workflow_gates_legacy_framework_tests_on_linux() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    linux_pytest = re.search(r"pytest tests/ci/ tests/guard/ \.agentcortex/tests/ -v", txt)
    assert linux_pytest, \
        ".agentcortex/tests/ must be CI-gated alongside tests/ci + tests/guard on Linux (#163)"


def test_workflow_runs_pytest_on_windows() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "test-windows:" in txt and "runs-on: windows-latest" in txt, \
        "CI must have a Windows pytest job (#163)"
    win_block = txt.split("test-windows:", 1)[1]
    assert re.search(r"pytest tests/ci/ tests/guard/ \.agentcortex/tests/", win_block), \
        "Windows job must run the full pytest set, not only validate.ps1 (#163)"


def test_workflow_has_utf8_sweep_and_critical_file_precheck() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "utf8-and-critical-files:" in txt, "CI must have the UTF-8 sweep job (#163)"
    block = txt.split("utf8-and-critical-files:", 1)[1]
    for needle in ('decode("utf-8")', "AGENTS.md", "validate.ps1", "git", "ls-files"):
        assert needle in block, f"UTF-8 sweep job must contain {needle!r} (#163)"


# AC-12: threat-aware classifier parity — .agentcortex/context/* must NOT be on
# the inert skip arm in EITHER workflow (both classifiers must stay in sync).
# The pattern matches an ACTIVE case arm (not a comment) — lines starting with
# whitespace + a path glob followed by ) are case arms; lines starting with # are comments.
_CONTEXT_INERT_ARM_RE = re.compile(
    r"^\s+(?:[^#\n]*\|)?\.agentcortex/context/\*(?:\|[^)]*)?[)]\s*;;",
    re.MULTILINE,
)


def _inert_arm_text(workflow_text: str) -> str:
    """Extract the case-arm block (non-comment lines only) between 'case' and the heavy arm."""
    m = re.search(r"case \"\$f\" in(.*?)\*\)\s*heavy=true", workflow_text, re.DOTALL)
    if not m:
        return ""
    block = m.group(1)
    # Strip comment lines so they don't affect the assertion.
    non_comment_lines = [
        ln for ln in block.splitlines() if not ln.lstrip().startswith("#")
    ]
    return "\n".join(non_comment_lines)


def test_ac12_context_not_on_inert_arm_validate_yml() -> None:
    txt = WORKFLOW.read_text(encoding="utf-8")
    inert = _inert_arm_text(txt)
    assert inert is not None, "Could not locate the case-arm classifier in validate.yml"
    assert not _CONTEXT_INERT_ARM_RE.search(inert), (
        ".agentcortex/context/* must NOT be on an active inert skip arm in validate.yml "
        "(SSoT/runtime state is security-relevant — AC-12)"
    )


def test_ac12_context_not_on_inert_arm_security_yml() -> None:
    txt = SECURITY_WORKFLOW.read_text(encoding="utf-8")
    inert = _inert_arm_text(txt)
    assert inert is not None, "Could not locate the case-arm classifier in security.yml"
    assert not _CONTEXT_INERT_ARM_RE.search(inert), (
        ".agentcortex/context/* must NOT be on an active inert skip arm in security.yml "
        "(SSoT/runtime state is security-relevant — AC-12)"
    )


# AC-10: default pytest command must be safe — no root-level *_test.py demo files
# that require unavailable secrets, and pytest.ini must prune non-test recursion.


def test_ac10_no_tracked_root_cache_test_py() -> None:
    """cache_test.py was renamed to cache_demo.py (AC-10). Ensure it cannot regress."""
    collision = ROOT / "cache_test.py"
    assert not collision.exists(), (
        "cache_test.py must not exist at repo root — it matches pytest's *_test.py "
        "collection pattern and requires ANTHROPIC_API_KEY at import, breaking bare "
        "pytest runs (AC-10). Rename to cache_demo.py or any non-test name."
    )


def test_ac10_pytest_ini_has_norecursedirs() -> None:
    """pytest.ini must prune non-test dirs so bare pytest does not collect demo files."""
    assert PYTEST_INI.exists(), "pytest.ini must exist at repo root"
    txt = PYTEST_INI.read_text(encoding="utf-8")
    assert "norecursedirs" in txt, (
        "pytest.ini must contain norecursedirs to prune temp/scratch/demo directories (AC-10)"
    )
    # Spot-check the entries most likely to harbour non-test scripts.
    for entry in ("temp_downstream", "scratch", "demo"):
        assert entry in txt, (
            f"pytest.ini norecursedirs must include {entry!r} to prevent collecting "
            f"non-test files from that directory (AC-10)"
        )


# ---------------------------------------------------------------------------
# Backlog #112: docs-pins job — content-pin tests must run on docs-only PRs.
# ---------------------------------------------------------------------------

def test_docs_pins_job_runs_when_heavy_is_false() -> None:
    """validate.yml must carry a docs-pins job gated on heavy != 'true' running -m docs_pin."""
    txt = WORKFLOW.read_text(encoding="utf-8")
    assert "docs-pins:" in txt, "validate.yml must define the docs-pins job (#112)"
    m = re.search(r"docs-pins:(.*?)\n  [a-z][a-z0-9-]*:", txt, re.DOTALL)
    block = m.group(1) if m else ""
    assert "needs.changes.outputs.heavy != 'true'" in block, (
        "docs-pins must run when heavy jobs are SKIPPED (heavy != 'true') — that is its whole point (#112)"
    )
    assert "-m docs_pin" in block, "docs-pins must select tests via the docs_pin marker (#112)"


def test_docs_pin_marker_registered_and_selects_tests() -> None:
    """pytest.ini registers docs_pin, and the marker selects the content-pin tests (>=4)."""
    assert "docs_pin" in PYTEST_INI.read_text(encoding="utf-8"), (
        "pytest.ini must register the docs_pin marker (#112)"
    )
    import subprocess, sys
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/ci/", "-m", "docs_pin", "--collect-only", "-q"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    m = re.search(r"(\d+)/\d+ tests collected", proc.stdout)
    count = int(m.group(1)) if m else 0
    assert count >= 4, (
        f"-m docs_pin must select >=4 content-pin tests (got {count}) — a lost tag silently "
        f"re-opens the docs-only gate hole (#112). {proc.stdout[-400:]}"
    )
