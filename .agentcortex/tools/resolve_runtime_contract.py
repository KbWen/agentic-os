#!/usr/bin/env python3
"""Resolve the runtime contract: workflow + activated skills for a given context."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def resolve(
    root: Path,
    classification: str,
    phase: str,
    platform: str,
    scope_signals: list[str],
    manual_skills: list[str] | None = None,
    failure_signals: list[str] | None = None,
    worklog_path: str | None = None,
) -> dict[str, Any]:
    """Delegate resolution to the single canonical runtime implementation."""
    module_path = root / ".agentcortex" / "tools" / "trigger_runtime_core.py"
    spec = importlib.util.spec_from_file_location("_agentcortex_trigger_runtime_core", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical resolver: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    artifact = module.resolve_runtime_contract(
        root,
        classification=classification,
        phase=phase,
        platform=platform,
        manual_skills=manual_skills,
        scope_signals=scope_signals,
        failure_signals=failure_signals,
        worklog_path=worklog_path,
    )
    workflow = artifact.get("resolved_workflow")
    return {
        "resolved_workflow": Path(str(workflow)).name if workflow else None,
        "activated_skills": sorted(artifact.get("activated_skills", [])),
    }


def _comma_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve runtime contract for classification/phase/platform"
    )
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--classification", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--scope-signals", default="")
    parser.add_argument("--manual-skills", default="")
    parser.add_argument("--failure-signals", default="")
    parser.add_argument("--worklog-path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    payload = resolve(
        root,
        args.classification,
        args.phase,
        args.platform,
        _comma_list(args.scope_signals),
        manual_skills=_comma_list(args.manual_skills),
        failure_signals=_comma_list(args.failure_signals),
        worklog_path=args.worklog_path,
    )
    json.dump(payload, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
