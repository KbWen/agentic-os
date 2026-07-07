#!/usr/bin/env python3
"""Check that .claude/commands/ dispatch files are in sync with .agent/workflows/.

In source-repo context (no .agentcortex-manifest), this check is skipped because
.claude/commands/ is an adapter surface created by deploy in downstream repos.
"""
from __future__ import annotations

import argparse
import pathlib
import sys


EXPECTED_COMMANDS = [
    # Core workflow commands (AGENTS.md §1)
    "spec-intake",
    "spec",
    "bootstrap",
    "plan",
    "implement",
    "review",
    "test",
    "test-classify",
    "test-skeleton",
    "handoff",
    "ship",
    "hotfix",
    "adr",
    "retro",
    "research",
    "brainstorm",
    "audit",
    "govern-audit",
    "decide",
    "sync-docs",
    "govern-docs",
    "worktree-first",
    "help",
    "app-init",
    # Optional modules
    "ask-openrouter",
    "codex-cli",
    "claude-cli",
    "ask-local",
]

# Commands present in .claude/commands/ that are intentionally EXCLUDED from
# EXPECTED_COMMANDS because they are pure aliases: their stub deliberately
# references the ALIASED workflow's path (not a same-named workflow file),
# so the standard "stub references .agent/workflows/<cmd>.md" check
# (see main() below) would false-fail if they were added as-is.
# Each entry documents which workflow the alias resolves to and where that
# is verified, so this list stays auditable instead of a silent gap.
ALIAS_EXCLUSIONS = {
    "execute-plan": "alias for /implement — .claude/commands/execute-plan.md "
    "references .agent/workflows/implement.md, not its own name",
    "write-plan": "alias for /plan — .claude/commands/write-plan.md "
    "references .agent/workflows/plan.md, not its own name",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Claude command adapter sync.")
    parser.add_argument("--root", type=pathlib.Path, default=".")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()

    # Source-repo detection: skip if no manifest (adapter surfaces don't exist yet)
    if not (root / ".agentcortex-manifest").is_file():
        print("Source repo detected — .claude/commands/ sync check skipped.")
        return 0

    commands_dir = root / ".claude" / "commands"
    workflows_dir = root / ".agent" / "workflows"
    errors: list[str] = []

    if not commands_dir.is_dir():
        print(f"Missing directory: {commands_dir.relative_to(root)}")
        return 1

    for cmd in EXPECTED_COMMANDS:
        cmd_file = commands_dir / f"{cmd}.md"
        workflow_file = workflows_dir / f"{cmd}.md"

        if not cmd_file.is_file():
            errors.append(f"missing command adapter: .claude/commands/{cmd}.md")
            continue

        if not workflow_file.is_file():
            errors.append(f"command {cmd}.md exists but workflow .agent/workflows/{cmd}.md is missing")
            continue

        # Verify the command file references the workflow
        content = cmd_file.read_text(encoding="utf-8")
        expected_ref = f".agent/workflows/{cmd}.md"
        if expected_ref not in content:
            errors.append(
                f".claude/commands/{cmd}.md does not reference {expected_ref}"
            )

    # Aliases are checked separately: verify the stub + its OWN redirect-stub
    # workflow file both exist, but do NOT require self-referencing text —
    # instead confirm the alias still points at its documented target so a
    # silent rename/retarget doesn't slip past this check unnoticed.
    for cmd in ALIAS_EXCLUSIONS:
        cmd_file = commands_dir / f"{cmd}.md"
        workflow_file = workflows_dir / f"{cmd}.md"

        if not cmd_file.is_file():
            errors.append(f"missing command adapter: .claude/commands/{cmd}.md (alias)")
            continue

        if not workflow_file.is_file():
            errors.append(
                f"alias {cmd}.md exists but its redirect workflow .agent/workflows/{cmd}.md is missing"
            )
            continue

        content = cmd_file.read_text(encoding="utf-8")
        # The alias reason string documents which target path it must reference.
        target_ref = ALIAS_EXCLUSIONS[cmd].rsplit("references ", 1)[-1].split(",")[0]
        if target_ref not in content:
            errors.append(
                f".claude/commands/{cmd}.md (alias) no longer references {target_ref} — "
                f"update ALIAS_EXCLUSIONS or fix the stub"
            )

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    total = len(EXPECTED_COMMANDS) + len(ALIAS_EXCLUSIONS)
    print(
        f"Command sync check passed ({len(EXPECTED_COMMANDS)} commands verified, "
        f"{len(ALIAS_EXCLUSIONS)} aliases verified, {total} total)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
