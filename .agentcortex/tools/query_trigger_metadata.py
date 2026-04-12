#!/usr/bin/env python3
"""Query the Stage 1 compact trigger index for selected skills or phases."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from trigger_runtime_core import DEFAULT_COMPACT_INDEX, DEFAULT_REGISTRY, load_registry, load_runtime_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query a compact slice of trigger metadata.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--compact-index",
        default=DEFAULT_COMPACT_INDEX,
        help="Compact index path relative to --root",
    )
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Registry fallback path relative to --root")
    parser.add_argument("--ids", nargs="*", default=[], help="Trigger ids to include")
    parser.add_argument("--phase", help="Optional phase filter")
    parser.add_argument("--classification", help="Optional classification filter")
    parser.add_argument("--kind", choices=("skill", "workflow", "policy"), help="Optional kind filter")
    parser.add_argument("--format", choices=("json", "table"), default="json", help="Output format")
    return parser.parse_args()


def matches(entry: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.ids and entry["id"] not in set(args.ids):
        return False
    if args.kind and entry.get("kind") != args.kind:
        return False
    if args.phase and args.phase not in entry.get("phase_scope", []):
        return False
    if args.classification and args.classification not in entry.get("detect_by", {}).get("classification", []):
        return False
    return True


def compact_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry["id"],
        "kind": entry["kind"],
        "phase_scope": entry["phase_scope"],
        "trigger_priority": entry.get("trigger_priority"),
        "load_policy": entry["load_policy"],
        "cost_type": entry.get("cost_type"),
        "cost_risk": entry.get("cost_risk"),
        "canonical_ref": entry.get("canonical_ref"),
        "mirror_ref": entry.get("mirror_ref"),
        "detail_ref": entry.get("detail_ref"),
        "content_hash": entry.get("content_hash"),
        "detect_by": entry.get("detect_by", {}),
        "runtime_anchor": entry.get("runtime_anchor"),
        "fallback_behavior": entry.get("fallback_behavior"),
    }


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    index, index_source = load_runtime_index(root, compact_index_rel=args.compact_index, registry_rel=args.registry)
    registry_entries: dict[str, Any] = {}
    registry_path = (root / args.registry).resolve()
    if registry_path.is_file():
        registry_entries = {entry["id"]: entry for entry in load_registry(root, args.registry).get("entries", [])}

    entries = []
    for entry in index["entries"]:
        merged = dict(registry_entries.get(entry["id"], {}))
        merged.update(entry)
        if matches(merged, args):
            entries.append(compact_entry(merged))

    if args.format == "table":
        print(f"source={index_source}")
        print("id | kind | phases | priority | load | hash")
        print("--- | --- | --- | --- | --- | ---")
        for entry in entries:
            print(
                f"{entry['id']} | "
                f"{entry['kind']} | "
                f"{','.join(entry['phase_scope'])} | "
                f"{entry.get('trigger_priority') or '-'} | "
                f"{entry['load_policy']} | "
                f"{entry.get('content_hash', '-') or '-'}"
            )
        return 0

    import json

    print(json.dumps({"source": index_source, "count": len(entries), "entries": entries}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
