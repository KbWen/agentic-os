#!/usr/bin/env python3
"""Check that .claude/commands/ dispatch files are in sync with .agent/workflows/.

The check is manifest-agnostic: it runs whenever the Claude adapter surface
(.claude/commands/) exists, regardless of .agentcortex-manifest presence, and
skips only when that surface is genuinely absent (a bare checkout with no
adapters). Repository identity is NOT inferred from manifest presence — deleting
the manifest downstream must not turn a broken adapter green (governance
self-audit 2026-07-11, F2).

Each ordinary stub must carry a single canonical dispatch directive
("Execute the canonical workflow: `.agent/workflows/<cmd>.md`") that references
the expected workflow. A residual mention of the path elsewhere in the file is
NOT accepted — the directive itself must be correct (F1).
"""
from __future__ import annotations

import argparse
import pathlib
import re
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


# The single canonical dispatch directive every stub carries on its own line.
# We require THIS line to reference the expected workflow — not merely that the
# path appears somewhere in the file. A broken directive that points at the wrong
# (or a nonexistent) workflow must fail even if later prose still mentions the
# correct path (governance self-audit 2026-07-11, F1).
CANONICAL_DIRECTIVE_RE = re.compile(
    r"Execute the canonical workflow:\s*`(\.agent/workflows/[^`]+\.md)`"
)


def _directive_target(content: str) -> str | None:
    """Return the workflow path referenced by the stub's canonical execution
    directive, or None when the stub has no such directive line."""
    match = CANONICAL_DIRECTIVE_RE.search(content)
    return match.group(1) if match else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Claude command adapter sync.")
    parser.add_argument("--root", type=pathlib.Path, default=".")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()

    commands_dir = root / ".claude" / "commands"
    workflows_dir = root / ".agent" / "workflows"
    errors: list[str] = []

    # Manifest-agnostic surface detection (governance self-audit F2): run the
    # sync check whenever the Claude adapter surface exists, regardless of
    # .agentcortex-manifest presence. Skip ONLY when the surface is genuinely
    # absent (a bare checkout that never had adapters) — a deleted manifest must
    # NOT disable adapter-drift detection or imply source identity.
    if not commands_dir.is_dir():
        print(
            ".claude/commands/ absent; Claude adapter surface not present, "
            "sync check skipped."
        )
        return 0

    for cmd in EXPECTED_COMMANDS:
        cmd_file = commands_dir / f"{cmd}.md"
        workflow_file = workflows_dir / f"{cmd}.md"

        if not cmd_file.is_file():
            errors.append(f"missing command adapter: .claude/commands/{cmd}.md")
            continue

        if not workflow_file.is_file():
            errors.append(f"command {cmd}.md exists but workflow .agent/workflows/{cmd}.md is missing")
            continue

        # Verify the stub's canonical dispatch directive references the expected
        # workflow — not merely that the path appears somewhere in the file (F1).
        content = cmd_file.read_text(encoding="utf-8")
        expected_ref = f".agent/workflows/{cmd}.md"
        directive_target = _directive_target(content)
        if directive_target is None:
            errors.append(
                f".claude/commands/{cmd}.md has no canonical dispatch directive "
                f"(expected 'Execute the canonical workflow: `{expected_ref}`')"
            )
        elif directive_target != expected_ref:
            errors.append(
                f".claude/commands/{cmd}.md dispatch directive references "
                f"{directive_target}, expected {expected_ref}"
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
        # The alias reason string documents which target path its directive must
        # reference. Parse the canonical directive (not any substring) so a
        # retargeted alias directive is caught even if prose still mentions the
        # documented target (F1).
        target_ref = ALIAS_EXCLUSIONS[cmd].rsplit("references ", 1)[-1].split(",")[0]
        directive_target = _directive_target(content)
        if directive_target is None:
            errors.append(
                f".claude/commands/{cmd}.md (alias) has no canonical dispatch "
                f"directive (expected it to reference {target_ref})"
            )
        elif directive_target != target_ref:
            errors.append(
                f".claude/commands/{cmd}.md (alias) dispatch directive references "
                f"{directive_target}, expected {target_ref} — update "
                f"ALIAS_EXCLUSIONS or fix the stub"
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
