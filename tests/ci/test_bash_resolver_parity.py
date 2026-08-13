"""Ratchet: every test module that resolves a bash launcher must reject the
WindowsApps WSL placeholder.

On Windows, PATH commonly exposes `%LOCALAPPDATA%\\Microsoft\\WindowsApps\\bash.exe`.
It answers `shutil.which("bash")` and it starts, but with no distro installed it
prints `wsl --install <Distro>` and exits 1 — so any test that hands it a shipped
`.sh` script fails for a reason that has nothing to do with the code under test.

Ten of the twelve bash-using modules carried the guard before PR #405; **two did
not**, and that unit fixed both — `.agentcortex/tests/test_ssot_completeness.py`
(whose `has_bash_launcher()` also swallowed no `OSError`) and
`tests/ci/test_validator_worklog_family_skip.py`, whose recurring Windows red was
written off across more than one ship as a local environment artifact rather than
as the missing guard it was. This test exists so the population cannot drift back
apart silently.

Re-derive with `git ls-tree -r --name-only 3faae10` + a `which("bash")` /
`WindowsApps` scan; that returns 12 / 10 / 2. An earlier version of this docstring
said eleven and one — a count taken mid-change, after the first of the two was
already fixed, and recorded as if it were the pre-existing state. This file counts
itself into the population (it contains both marker strings and satisfies its own
assertion), so today's scan returns 13 / 13 / 0.

Scope note: the guard checked here is the WindowsApps exclusion. The candidate
lists also list `<git>/usr/bin/bash.exe`, which starts fine but resolves no
coreutils; that is a latent second hazard, live only on a Git layout with no
`bin/bash.exe`, and is deliberately not widened into this ratchet.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = (ROOT / "tests", ROOT / ".agentcortex" / "tests")

# Population size at the time this ratchet was written. The floor is an
# anti-vacuity guard: a broken glob would otherwise scan nothing and pass.
KNOWN_POPULATION_FLOOR = 10


def _modules_resolving_bash() -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for base in SCAN_DIRS:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("test_*.py")):
            text = path.read_text(encoding="utf-8")
            if 'which("bash")' in text:
                found.append((path, text))
    return found


def test_every_bash_resolving_test_module_rejects_the_windowsapps_alias() -> None:
    modules = _modules_resolving_bash()
    assert len(modules) >= KNOWN_POPULATION_FLOOR, (
        f"scan reached only {len(modules)} modules under {[str(d) for d in SCAN_DIRS]} — "
        "the glob is wrong, so a pass here would prove nothing"
    )

    unguarded = [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path, text in modules
        if "WindowsApps" not in text
    ]
    assert not unguarded, (
        "these test modules resolve bash without excluding the WindowsApps WSL "
        f"placeholder, so they go red on Windows for the wrong reason: {unguarded}"
    )
