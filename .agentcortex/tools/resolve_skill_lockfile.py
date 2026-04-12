#!/usr/bin/env python3
"""Build a local skill registry snapshot and resolve pinned lockfiles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trigger_runtime_core import (
    DEFAULT_SKILL_PACKAGE_ROOT,
    build_skill_registry_snapshot,
    resolve_skill_execution_policy,
    resolve_skill_lockfile,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve local skill packages into a snapshot or lockfile.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--skill-root",
        default=DEFAULT_SKILL_PACKAGE_ROOT,
        help="Skill package root relative to --root",
    )
    parser.add_argument(
        "--requested",
        nargs="*",
        default=[],
        help="Requested skill package ids to pin. Leave empty with --snapshot-only.",
    )
    parser.add_argument(
        "--snapshot-only",
        action="store_true",
        help="Emit the local registry snapshot without resolving a lockfile.",
    )
    parser.add_argument(
        "--runtime",
        choices=["claude", "codex", "antigravity"],
        help="Emit a resolved execution policy artifact for the selected runtime.",
    )
    parser.add_argument(
        "--target-skill",
        help="Target skill id for --runtime policy resolution. Defaults to the first requested skill.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    try:
        snapshot = build_skill_registry_snapshot(root, skill_package_root=args.skill_root)
        if args.snapshot_only:
            payload = snapshot
        elif args.runtime:
            target_skill = args.target_skill or (args.requested[0] if args.requested else "")
            if not target_skill:
                raise ValueError("target skill is required when resolving an execution policy")
            payload = resolve_skill_execution_policy(snapshot, args.requested, args.runtime, target_skill)
        else:
            payload = resolve_skill_lockfile(snapshot, args.requested)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
