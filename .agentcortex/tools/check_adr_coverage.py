#!/usr/bin/env python3
"""bootstrap §0a — ADR coverage check (replaces "no ADR exists" trigger).

Lesson L5 (current_state.md §Global Lessons, 2026-04-25):
  bootstrap §0a's existing "No ADR exists" condition becomes permanently
  False after the first ADR ships, silently skipping the ADR prompt for
  every subsequent architecture-change. This tool replaces existence
  with COVERAGE: each ADR declares its `applies_to:` glob list in
  frontmatter; if NO ADR's glob matches the current task's changed files,
  fire the prompt.

Usage:
  python .agentcortex/tools/check_adr_coverage.py --root . --paths file1 file2 ...

Exit codes:
  0  at least one ADR covers the given paths
  1  no ADR covers — bootstrap should fire the /adr prompt
  2  no ADRs exist at all — bootstrap should fire the /app-init prompt
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path
from typing import Iterable

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
APPLIES_TO_RE = re.compile(
    r"^applies_to\s*:\s*(\[.*?\]|\n(?:\s+-\s+\S.*\n?)+)",
    re.MULTILINE,
)
LIST_ITEM_RE = re.compile(r'^\s*-\s+["\']?([^"\'\n]+?)["\']?\s*$', re.MULTILINE)
FLOW_LIST_ITEM_RE = re.compile(r'["\']([^"\']+)["\']')


def parse_applies_to(fm_text: str) -> list[str]:
    """Extract `applies_to:` value (list of glob patterns) from frontmatter."""
    m = APPLIES_TO_RE.search(fm_text)
    if not m:
        return []
    body = m.group(1).strip()
    if body.startswith("["):
        # Flow list: ["a", "b"]
        return FLOW_LIST_ITEM_RE.findall(body)
    # Block list:
    #   - "a"
    #   - "b"
    return LIST_ITEM_RE.findall(body)


def adr_globs(adr_dir: Path) -> dict[str, list[str]]:
    """Map ADR filename → its applies_to globs (empty list if not declared)."""
    result: dict[str, list[str]] = {}
    if not adr_dir.is_dir():
        return result
    for path in sorted(adr_dir.glob("ADR-*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        m = FRONTMATTER_RE.match(text)
        if not m:
            result[path.name] = []
            continue
        result[path.name] = parse_applies_to(m.group(1))
    return result


def covers(globs: Iterable[str], target_path: str) -> bool:
    target_path = target_path.replace("\\", "/")
    for pattern in globs:
        if fnmatch.fnmatch(target_path, pattern):
            return True
        if pattern.endswith("/**") and target_path.startswith(pattern[:-3] + "/"):
            return True
        if pattern == target_path:
            return True
    return False


def covering_adrs(adr_map: dict[str, list[str]], paths: list[str]) -> dict[str, list[str]]:
    """Return {adr_name: [matched_paths]} for ADRs that cover at least one path."""
    result: dict[str, list[str]] = {}
    for adr, globs in adr_map.items():
        matched = [p for p in paths if covers(globs, p)]
        if matched:
            result[adr] = matched
    return result


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument(
        "--paths",
        nargs="+",
        required=True,
        help="Repo-relative POSIX paths the current task is changing",
    )
    ap.add_argument(
        "--adr-dir",
        default="docs/adr",
        help="ADR directory relative to root (default: docs/adr)",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    adr_dir = root / args.adr_dir

    adr_map = adr_globs(adr_dir)
    if not adr_map:
        print("no_adr_at_all", file=sys.stdout)
        return 2

    matches = covering_adrs(adr_map, args.paths)
    if matches:
        for adr, matched in matches.items():
            print(f"covered_by:{adr} → {','.join(matched)}")
        return 0

    print("no_covering_adr", file=sys.stdout)
    declared_adrs = [adr for adr, globs in adr_map.items() if globs]
    if declared_adrs:
        print(f"  declared ADRs: {', '.join(declared_adrs)}", file=sys.stderr)
    undeclared = [adr for adr, globs in adr_map.items() if not globs]
    if undeclared:
        print(
            f"  ADRs missing 'applies_to:' frontmatter: {', '.join(undeclared)}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
