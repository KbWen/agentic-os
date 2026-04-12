#!/usr/bin/env python3
"""Resolve the runtime contract: workflow + activated skills for a given context."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _signal_matches(user_signal: str, entry_signal: str) -> bool:
    """Check if a user scope signal matches a registry scope signal.

    Uses bidirectional substring matching (case-insensitive).
    """
    u = user_signal.lower()
    e = entry_signal.lower()
    return u in e or e in u


def resolve(
    root: Path,
    classification: str,
    phase: str,
    platform: str,
    scope_signals: list[str],
) -> dict[str, Any]:
    sys.path.insert(0, str(root / ".agentcortex" / "tools"))
    from _yaml_loader import load_data

    registry = load_data(root / ".agentcortex/metadata/trigger-registry.yaml")

    resolved_workflow = f"{phase}.md"
    activated_skills: list[str] = []

    for entry in registry["entries"]:
        if entry["kind"] != "skill":
            continue

        detect = entry.get("detect_by", {})

        # Classification gate.
        classifications = detect.get("classification", [])
        if classifications and classification not in classifications:
            continue

        # Phase gate.
        phases = entry.get("phase_scope", [])
        if phase not in phases:
            continue

        # Platform gate.
        platforms = entry.get("platforms", [])
        if platforms and platform not in platforms:
            continue

        # Determine activation based on load policy.
        load_policy = entry.get("load_policy", "on-match")

        if load_policy in ("always", "phase-entry"):
            # Mandatory / phase-entry skills activate without scope signals.
            activated_skills.append(entry["id"])
            continue

        # For on-match / on-failure: require scope signal match.
        entry_signals = detect.get("scope_signals", [])
        if entry_signals and scope_signals:
            for user_sig in scope_signals:
                matched = False
                for entry_sig in entry_signals:
                    if _signal_matches(user_sig, entry_sig):
                        matched = True
                        break
                if matched:
                    activated_skills.append(entry["id"])
                    break

    return {
        "resolved_workflow": resolved_workflow,
        "activated_skills": sorted(activated_skills),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve runtime contract for classification/phase/platform"
    )
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--classification", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--scope-signals", default="")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    signals = [s.strip() for s in args.scope_signals.split(",") if s.strip()]

    payload = resolve(root, args.classification, args.phase, args.platform, signals)
    json.dump(payload, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
