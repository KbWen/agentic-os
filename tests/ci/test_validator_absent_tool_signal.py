"""Guards for the absent-tool signal in validate.sh / validate.ps1.

Background: the deployed validators referenced tools that `deploy.sh` does not ship.
Three checks printed a bare ``-- tool not present``, a string that cannot distinguish a
deliberately source-only tool from a broken install, and the top-line summary reported an
unqualified pass regardless (backlog #173, and the same class as #149 / #334).

The fix carries the reason at the CALL SITE -- ``run_python_check_source_only`` in bash,
``-AbsentReason`` in PowerShell -- and counts only absences with NO stated reason, so
"unexpected" is defined by a missing reason rather than by membership in a registry that
can go stale.

These tests are static (no deploy, no subprocess) and exist because the CI
``deploy-smoke-test`` grep is narrower than it looks: it only sees checks invoked through
``run_python_check`` WITHOUT a native presence guard, so it cannot catch a false
source-only claim, and it cannot see presence-guarded checks at all.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

# The exact suffix a deliberate absence must print. Kept as one literal so the two
# validators cannot drift apart silently (cross-platform parity is mandatory, AC-X1).
SOURCE_ONLY_REASON = "source-only tool, not deployed by design (safe to ignore downstream)"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _deployed_tool_names() -> set[str]:
    """Every basename deploy.sh ships from .agentcortex/tools/, from BOTH whitelist sites.

    AC-S5 of the frozen downstream-adaptability-optimization spec requires a tool to appear
    in both the dry-run string and the real array; reading both here means a one-spot edit
    cannot make this test pass by accident.
    """
    text = _read(DEPLOY_SH)

    dry = re.search(r'_runtime_tools="([^"]+)"', text)
    assert dry, "deploy.sh: _runtime_tools dry-run whitelist not found"
    dry_names = set(dry.group(1).split())

    real = re.search(r"^runtime_tools=\((.*?)^\)", text, re.S | re.M)
    assert real, "deploy.sh: runtime_tools array not found"
    real_names = {ln.strip() for ln in real.group(1).splitlines() if ln.strip()}

    assert dry_names == real_names, (
        "deploy.sh whitelist sites disagree (AC-S5 requires both to list the same tools); "
        f"only in dry-run: {sorted(dry_names - real_names)}; "
        f"only in array: {sorted(real_names - dry_names)}"
    )
    return dry_names


def test_source_only_claims_are_true() -> None:
    """A call site declaring a tool source-only must name a tool deploy.sh really withholds.

    This is the inverse of the CI grep: that catches an absence with no reason, this
    catches a reason that is a lie. A tool marked source-only while sitting in the
    whitelist would print "safe to ignore downstream" for a check whose tool IS shipped,
    and would also be excluded from the unexpected-absence counter -- hiding a real break
    behind a reassuring string, which is the exact failure this change exists to remove.

    Both call-site spellings are covered: a literal ``"$ROOT/.agentcortex/tools/x.py"``
    and an indirect ``"$SOME_CHECK"`` resolved through its assignment at the top of the file.
    """
    text = _read(VALIDATE_SH)
    deployed = _deployed_tool_names()

    # Positional contract: reason, label, missing-python level, script.
    calls = re.findall(
        r'run_python_check_source_only\s+"[^"]*"\s*\\?\s*\n?\s*"[^"]*"\s+\w+\s+"([^"]+)"',
        text,
    )
    assert calls, "validate.sh: no run_python_check_source_only call sites found"

    for script_expr in calls:
        if script_expr.startswith("$") and "/" not in script_expr:
            var = script_expr[1:]
            m = re.search(rf'^{re.escape(var)}="[^"]*/(\.agentcortex/tools/[\w.]+)"', text, re.M)
            assert m, f"validate.sh: could not resolve ${var} to a tools path"
            name = m.group(1).rsplit("/", 1)[-1]
        else:
            name = script_expr.rsplit("/", 1)[-1]
        assert name.endswith(".py"), f"unexpected script expression: {script_expr!r}"
        assert name not in deployed, (
            f"validate.sh claims {name} is source-only, but deploy.sh ships it. "
            "Either drop the source-only wrapper or remove it from the whitelist."
        )


def test_absent_reason_string_is_identical_across_validators() -> None:
    """Cross-platform parity (AC-X1): the same situation must read the same on both hosts."""
    sh, ps1 = _read(VALIDATE_SH), _read(VALIDATE_PS1)
    assert sh.count(SOURCE_ONLY_REASON) == ps1.count(SOURCE_ONLY_REASON) > 0, (
        "source-only reason string count differs between validate.sh and validate.ps1: "
        f"sh={sh.count(SOURCE_ONLY_REASON)} ps1={ps1.count(SOURCE_ONLY_REASON)}"
    )


def test_unexpected_absence_counter_is_wired_in_both_validators() -> None:
    """The counter must be initialised, incremented on an unreasoned absence, and READ.

    Incrementing without reading is the failure this whole change exists to remove: a
    number that nothing reports is the same as no number at all.
    """
    sh = _read(VALIDATE_SH)
    assert "TOOL_ABSENT_UNEXPECTED=0" in sh, "validate.sh: counter not initialised"
    assert "TOOL_ABSENT_UNEXPECTED + 1" in sh, "validate.sh: counter never incremented"
    assert re.search(r'\[\[ "\$TOOL_ABSENT_UNEXPECTED" -gt 0 \]\]', sh), (
        "validate.sh: counter never read by the summary line"
    )

    ps1 = _read(VALIDATE_PS1)
    assert "$script:ToolAbsentUnexpected = 0" in ps1, "validate.ps1: counter not initialised"
    assert "$script:ToolAbsentUnexpected++" in ps1, "validate.ps1: counter never incremented"
    assert "$script:ToolAbsentUnexpected -gt 0" in ps1, (
        "validate.ps1: counter never read by the summary line"
    )


@pytest.mark.parametrize("path", [VALIDATE_SH, VALIDATE_PS1])
def test_bare_absent_string_has_exactly_one_emission_site(path: Path) -> None:
    """ADR-006 ratchet safety plus a correctness invariant in one assertion.

    The fallback ``tool not present`` must live at exactly one place -- the python-check
    wrapper. A second copy means either a new counted emission (which breaks the
    exact-match native ratchet at 202/203) or a path that skips the counter.
    """
    body = _read(path)
    assert body.count("tool not present") == 1, (
        f"{path.name}: expected exactly 1 'tool not present' literal, "
        f"found {body.count('tool not present')}"
    )
