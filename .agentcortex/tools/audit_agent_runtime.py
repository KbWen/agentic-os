#!/usr/bin/env python3
"""Audit agent runtime readiness: verify workflow files and skill phase hooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def audit(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root / ".agentcortex" / "tools"))
    from _yaml_loader import load_data

    registry = load_data(root / ".agentcortex/metadata/trigger-registry.yaml")
    workflow_dir = root / ".agent" / "workflows"

    # Check all core workflow files exist.
    core_phases = [
        "bootstrap", "plan", "implement", "review",
        "test", "handoff", "ship", "hotfix",
    ]
    all_workflows_ready = all(
        (workflow_dir / f"{phase}.md").is_file() for phase in core_phases
    )

    # Check each skill's phase hooks.
    skill_entries = [e for e in registry["entries"] if e["kind"] == "skill"]
    skills_output: list[dict[str, Any]] = []
    all_skills_ready = True

    for entry in skill_entries:
        skill_id = entry["id"]
        phase_scope = entry.get("phase_scope", [])
        detail_ref = entry.get("detail_ref", "")

        phase_hooks: dict[str, dict[str, bool]] = {}
        for phase in phase_scope:
            wf_exists = (workflow_dir / f"{phase}.md").is_file()
            detail_exists = (root / detail_ref).is_file() if detail_ref else True
            ready = wf_exists and detail_exists
            phase_hooks[phase] = {"ready": ready}
            if not ready:
                all_skills_ready = False

        skills_output.append({"skill": skill_id, "phase_hooks": phase_hooks})

    return {
        "all_workflows_ready": all_workflows_ready,
        "all_skills_auto_trigger_ready": all_skills_ready,
        "skills": skills_output,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit agent runtime readiness")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    payload = audit(root)

    if args.format == "json":
        json.dump(payload, sys.stdout, indent=2)
        print()
    else:
        ok = payload["all_workflows_ready"] and payload["all_skills_auto_trigger_ready"]
        print(f"Runtime status: {'READY' if ok else 'NOT READY'}")
        if not payload["all_workflows_ready"]:
            print("  WARNING: some core workflow files are missing")
        for info in payload["skills"]:
            phases = ", ".join(
                f"{p}={'OK' if h['ready'] else 'MISSING'}"
                for p, h in info["phase_hooks"].items()
            )
            print(f"  {info['skill']}: {phases}")


if __name__ == "__main__":
    main()
