#!/usr/bin/env python3
"""Resolve the runtime contract: workflow + activated skills for a given context."""

from __future__ import annotations

import argparse
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
    sys.path.insert(0, str(root / ".agentcortex" / "tools"))
    from trigger_runtime_core import resolve_runtime_contract

    return resolve_runtime_contract(
        root,
        classification=classification,
        phase=phase,
        platform=platform,
        manual_skills=manual_skills,
        scope_signals=scope_signals,
        failure_signals=failure_signals,
        worklog_path=worklog_path,
    )


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
