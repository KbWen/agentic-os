#!/usr/bin/env python3
"""Generate or verify the checked-in Stage 1 trigger compact index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trigger_runtime_core import DEFAULT_COMPACT_INDEX, DEFAULT_REGISTRY, build_compact_index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Stage 1 trigger compact index.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY, help="Registry path relative to --root")
    parser.add_argument("--output", default=DEFAULT_COMPACT_INDEX, help="Output path relative to --root")
    parser.add_argument("--check", action="store_true", help="Verify the checked-in compact index is fresh")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    output_path = (root / args.output).resolve()
    expected = build_compact_index(root, registry_rel=args.registry)
    rendered = json.dumps(expected, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not output_path.is_file():
            print(f"missing compact index: {output_path}", file=sys.stderr)
            return 1
        actual = output_path.read_text(encoding="utf-8")
        if actual != rendered:
            print(f"stale compact index: {output_path}", file=sys.stderr)
            return 1
        print(f"compact index is fresh: {output_path.relative_to(root).as_posix()}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"wrote compact index: {output_path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
