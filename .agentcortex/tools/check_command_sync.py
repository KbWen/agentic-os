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
    "spec-intake",
    "bootstrap",
    "plan",
    "implement",
    "review",
    "test",
    "handoff",
    "ship",
    "decide",
    "test-classify",
    "claude-cli",
]


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

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print(f"Command sync check passed ({len(EXPECTED_COMMANDS)} commands verified).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
