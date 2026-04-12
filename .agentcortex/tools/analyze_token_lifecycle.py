#!/usr/bin/env python3
"""Analyze token lifecycle costs across all scenarios in lifecycle-scenarios.json.

Computes current-approach vs optimized-approach token costs for each scenario,
broken down by workflow, probe, and execution detail tokens.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


def estimate_tokens(path: Path) -> int:
    if not path.is_file():
        return 0
    return max(1, math.ceil(len(path.read_text(encoding="utf-8")) / 4))


def estimate_tokens_text(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


PHASE_WORKFLOW_MAP = {
    "bootstrap": "bootstrap.md",
    "plan": "plan.md",
    "implement": "implement.md",
    "review": "review.md",
    "test": "test.md",
    "handoff": "handoff.md",
    "ship": "ship.md",
    "hotfix": "hotfix.md",
}

# Continuation reads use ~22% of full detail (skill notes cache vs full SKILL.md).
CONTINUATION_FRACTION = 0.22


def scenario_phase_counts(
    phases: list[str], repeats: dict[str, int]
) -> dict[str, int]:
    """Compute effective phase counts from declared phases and repeat overrides."""
    counts: dict[str, int] = {}
    for phase in phases:
        counts[phase] = counts.get(phase, 0) + repeats.get(phase, 1)
    return counts


def _parse_heading_sections(text: str) -> dict[str, str]:
    """Split markdown into sections keyed by ``## heading`` line."""
    sections: dict[str, str] = {}
    current_key = "__preamble__"
    sections[current_key] = ""
    for line in text.split("\n"):
        if line.startswith("## "):
            current_key = line.strip()
            sections[current_key] = ""
        else:
            sections[current_key] += line + "\n"
    return sections


def compute_scoped_tokens(text: str) -> tuple[int, bool]:
    """Return ``(scoped_tokens, is_fallback)`` for a workflow file.

    * Files **with** a ``## Heading-Scoped Read Note`` → extract only listed
      sections.
    * Files **without** the note → scoped == full (no optimization but **no
      fallback** either).
    * If the note exists but cannot be parsed → return full with
      ``fallback=True``.
    """
    sections = _parse_heading_sections(text)
    full_tokens = estimate_tokens_text(text)

    note_key = None
    for key in sections:
        if "Heading-Scoped Read Note" in key:
            note_key = key
            break

    if note_key is None:
        return full_tokens, False

    note_content = sections[note_key]
    scoped_names: list[str] = []
    for line in note_content.split("\n"):
        line = line.strip()
        if line.startswith("- `") and "`" in line[3:]:
            name = line[3 : line.index("`", 3)]
            scoped_names.append(name)

    if not scoped_names:
        return full_tokens, True

    scoped_tokens = 0
    for heading, content in sections.items():
        if heading == "__preamble__" or "Heading-Scoped Read Note" in heading:
            continue
        heading_text = heading.replace("## ", "")
        for name in scoped_names:
            if name in heading_text:
                scoped_tokens += estimate_tokens_text(heading + "\n" + content)
                break

    if scoped_tokens == 0:
        return full_tokens, True

    return max(1, scoped_tokens), False


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------


def analyze(root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(root / ".agentcortex" / "tools"))
    from _yaml_loader import load_data

    scenarios_data = load_data(
        root / ".agentcortex/metadata/lifecycle-scenarios.json"
    )
    registry = load_data(root / ".agentcortex/metadata/trigger-registry.yaml")
    compact_index = json.loads(
        (root / ".agentcortex/metadata/trigger-compact-index.json").read_text(
            encoding="utf-8"
        )
    )

    skill_entries = {
        e["id"]: e for e in registry["entries"] if e["kind"] == "skill"
    }

    registry_tokens = estimate_tokens(
        root / ".agentcortex/metadata/trigger-registry.yaml"
    )
    compact_index_tokens = estimate_tokens(
        root / ".agentcortex/metadata/trigger-compact-index.json"
    )

    # Pre-compute workflow scope data per phase.
    wf_scope_cache: dict[str, tuple[int, int, bool]] = {}
    for phase, filename in PHASE_WORKFLOW_MAP.items():
        wf_path = root / ".agent" / "workflows" / filename
        if wf_path.is_file():
            full_text = wf_path.read_text(encoding="utf-8")
            full_tok = estimate_tokens_text(full_text)
            scoped_tok, fallback = compute_scoped_tokens(full_text)
            wf_scope_cache[phase] = (full_tok, scoped_tok, fallback)
        else:
            wf_scope_cache[phase] = (0, 0, False)

    # Pre-compute compact-index entries for fast lookup.
    compact_entries = {e["id"]: e for e in compact_index["entries"]}

    results: list[dict[str, Any]] = []

    for scenario in scenarios_data["scenarios"]:
        sid = scenario["id"]
        classification = scenario["classification"]
        phases = scenario["phases"]
        repeats = scenario.get("phase_repeats", {})
        candidate_skills = scenario["candidate_skills"]
        triggered_skills = scenario["triggered_skills"]

        phase_counts = scenario_phase_counts(phases, repeats)

        # --- Workflow tokens ---
        workflow_tokens = 0
        workflow_scoped_tokens = 0
        workflow_scope_fallbacks: list[str] = []

        for phase, count in phase_counts.items():
            if phase in wf_scope_cache:
                full, scoped, fallback = wf_scope_cache[phase]
                workflow_tokens += full * count
                workflow_scoped_tokens += scoped * count
                if fallback:
                    workflow_scope_fallbacks.append(phase)

        # --- Current probe tokens ---
        current_probe_tokens = sum(
            estimate_tokens(root / skill_entries[s]["detail_ref"])
            for s in candidate_skills
            if s in skill_entries
        )

        # --- Execution detail (first-load + continuation) ---
        detail_first_load_tokens = 0
        continuation_tokens = 0
        detail_load_counts: dict[str, int] = {}

        for skill_id in triggered_skills:
            if skill_id not in skill_entries:
                continue
            entry = skill_entries[skill_id]
            detail_tok = estimate_tokens(root / entry["detail_ref"])
            load_count = sum(
                phase_counts.get(p, 0) for p in entry["phase_scope"]
            )
            load_count = max(load_count, 1)
            detail_load_counts[skill_id] = load_count

            detail_first_load_tokens += detail_tok
            if load_count > 1:
                cont_cost = max(1, int(detail_tok * CONTINUATION_FRACTION))
                continuation_tokens += (load_count - 1) * cont_cost

        execution_detail_tokens = detail_first_load_tokens + continuation_tokens

        # --- Totals ---
        current_total_tokens = (
            workflow_tokens + current_probe_tokens + execution_detail_tokens
        )

        compact_slice_tokens = 0
        for s in candidate_skills:
            if s in compact_entries:
                compact_slice_tokens += estimate_tokens_text(
                    json.dumps(compact_entries[s])
                )

        projected_total = (
            workflow_scoped_tokens
            + compact_slice_tokens
            + execution_detail_tokens
        )
        delta = current_total_tokens - projected_total

        results.append(
            {
                "id": sid,
                "classification": classification,
                "current_total_tokens": current_total_tokens,
                "current_probe_tokens": current_probe_tokens,
                "execution_detail_tokens": execution_detail_tokens,
                "detail_first_load_tokens": detail_first_load_tokens,
                "continuation_tokens": continuation_tokens,
                "workflow_tokens": workflow_tokens,
                "workflow_scoped_tokens": workflow_scoped_tokens,
                "workflow_scope_fallbacks": workflow_scope_fallbacks,
                "phase_counts": phase_counts,
                "detail_load_counts": detail_load_counts,
                "platforms": {
                    "codex": {
                        "projected_total_tokens": projected_total,
                        "delta_vs_current_tokens": delta,
                        "compact_slice_tokens": compact_slice_tokens,
                        "probe_strategy": "compact-index",
                    },
                    "claude": {
                        "projected_total_tokens": projected_total,
                        "delta_vs_current_tokens": delta,
                        "compact_slice_tokens": compact_slice_tokens,
                        "probe_strategy": "compact-index",
                    },
                },
            }
        )

    return {
        "results": results,
        "registry_tokens": registry_tokens,
        "compact_index_tokens": compact_index_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze token lifecycle costs across scenarios"
    )
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text"
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    payload = analyze(root)

    if args.format == "json":
        json.dump(payload, sys.stdout, indent=2)
        print()
    else:
        print(f"Registry: {payload['registry_tokens']:,} tokens")
        print(f"Compact index: {payload['compact_index_tokens']:,} tokens")
        for result in payload["results"]:
            codex = result["platforms"]["codex"]
            print(f"\n--- {result['id']} ({result['classification']}) ---")
            print(f"  Current total : {result['current_total_tokens']:>8,}")
            print(f"  Projected     : {codex['projected_total_tokens']:>8,}")
            print(f"  Savings       : {codex['delta_vs_current_tokens']:>8,}")
            print(f"  Workflow      : {result['workflow_tokens']:>8,}  (scoped: {result['workflow_scoped_tokens']:,})")
            print(f"  Probe         : {result['current_probe_tokens']:>8,}  (compact: {codex['compact_slice_tokens']:,})")
            print(f"  Exec detail   : {result['execution_detail_tokens']:>8,}  (first: {result['detail_first_load_tokens']:,}, cont: {result['continuation_tokens']:,})")


if __name__ == "__main__":
    main()
