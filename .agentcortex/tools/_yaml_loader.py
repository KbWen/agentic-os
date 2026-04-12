#!/usr/bin/env python3
"""Dependency-free YAML/JSON loader for AgentCortex trigger metadata.

Loading priority:
  1. PyYAML (yaml.safe_load) when installed — full YAML support.
  2. Built-in YAML-subset parser — handles the specific patterns used in
     trigger-registry.yaml without any external dependency.
  3. json.loads — for files that are actually JSON despite .yaml extension.

The built-in parser supports: mappings, sequences of mappings, flow
sequences ([a, b, c]), quoted strings, booleans, integers, block scalars
(> folded), and --- document markers.  It does NOT support anchors, aliases,
tags, or multi-document streams.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Built-in YAML-subset parser (no external dependencies)
# ---------------------------------------------------------------------------

def _parse_scalar(value: str) -> Any:
    """Parse a single YAML scalar value."""
    value = value.strip()
    if not value:
        return ""
    if value in ("true", "false"):
        return value == "true"
    if value in ("null", "~"):
        return None
    if value.startswith(("'", '"')) and len(value) >= 2 and value[-1] == value[0]:
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip() for p in re.split(r",(?![^\[]*\])", inner)]
        return [_parse_scalar(p) for p in parts]
    try:
        return int(value)
    except ValueError:
        pass
    return value


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the YAML subset used by AgentCortex metadata files.

    Strategy: two-pass approach.
      Pass 1: Collect (indent, raw_line) tuples, stripping comments/blanks.
      Pass 2: Recursive descent on indent-grouped blocks.
    """
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or stripped == "---":
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, stripped))

    def _parse_block(start: int, end: int, base_indent: int) -> dict[str, Any] | list[Any]:
        """Parse a block of lines from start..end at base_indent."""
        # Determine if this block is a sequence or mapping
        if start < end:
            _, first_line = lines[start]
            if first_line.startswith("- "):
                return _parse_sequence(start, end, base_indent)
        return _parse_mapping(start, end, base_indent)

    def _collect_children(start: int, end: int, base_indent: int) -> list[tuple[int, int]]:
        """Return (child_start, child_end) ranges for top-level items at base_indent."""
        ranges: list[tuple[int, int]] = []
        i = start
        while i < end:
            ind, _ = lines[i]
            if ind < base_indent:
                break
            if ind == base_indent:
                child_start = i
                i += 1
                while i < end and lines[i][0] > base_indent:
                    i += 1
                ranges.append((child_start, i))
            else:
                i += 1
        return ranges

    def _parse_mapping(start: int, end: int, base_indent: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        i = start
        folded_key: str | None = None
        folded_parts: list[str] = []

        while i < end:
            ind, line = lines[i]
            if ind < base_indent:
                break
            if ind > base_indent:
                # Continuation of folded scalar
                if folded_key is not None:
                    folded_parts.append(line)
                    i += 1
                    continue
                i += 1
                continue

            # Flush any pending folded scalar
            if folded_key is not None:
                result[folded_key] = " ".join(folded_parts).strip()
                folded_key = None
                folded_parts = []

            key_part, sep, val_part = line.partition(":")
            if not sep:
                i += 1
                continue
            key = key_part.strip()
            value = val_part.strip()

            if value == ">" or value == "|":
                folded_key = key
                folded_parts = []
                i += 1
                continue

            if not value:
                # Nested block — find its extent
                child_start = i + 1
                child_end = child_start
                while child_end < end and lines[child_end][0] > base_indent:
                    child_end += 1
                if child_start < child_end:
                    child_indent = lines[child_start][0]
                    result[key] = _parse_block(child_start, child_end, child_indent)
                else:
                    result[key] = {}
                i = child_end
                continue

            result[key] = _parse_scalar(value)
            i += 1

        # Flush trailing folded
        if folded_key is not None:
            result[folded_key] = " ".join(folded_parts).strip()

        return result

    def _parse_sequence(start: int, end: int, base_indent: int) -> list[Any]:
        result: list[Any] = []
        i = start

        while i < end:
            ind, line = lines[i]
            if ind < base_indent:
                break
            if not line.startswith("- "):
                i += 1
                continue

            item_content = line[2:].strip()
            key_part, sep, val_part = item_content.partition(":")

            if sep and key_part.strip():
                # First key-value of a mapping item
                item: dict[str, Any] = {}
                k = key_part.strip()
                v = val_part.strip()

                if v == ">" or v == "|":
                    # Folded scalar as first value
                    parts: list[str] = []
                    i += 1
                    while i < end and lines[i][0] > base_indent:
                        parts.append(lines[i][1])
                        i += 1
                    item[k] = " ".join(parts).strip()
                elif v:
                    item[k] = _parse_scalar(v)
                    i += 1
                else:
                    # Nested block under this key
                    i += 1
                    child_start = i
                    # The nested content indent = indent of "- " + 2 (for "- ") + key indent
                    while i < end and lines[i][0] > base_indent:
                        i += 1
                    if child_start < i:
                        child_indent = lines[child_start][0]
                        item[k] = _parse_block(child_start, i, child_indent)
                    else:
                        item[k] = {}

                # Collect remaining keys at the item's indent level
                # Item keys are indented deeper than base_indent
                item_key_indent = base_indent + 2
                while i < end:
                    ni, nl = lines[i]
                    if ni < item_key_indent:
                        break
                    if ni == item_key_indent and not nl.startswith("- "):
                        kp, s2, vp = nl.partition(":")
                        if s2:
                            kk = kp.strip()
                            vv = vp.strip()
                            if vv == ">" or vv == "|":
                                parts = []
                                i += 1
                                while i < end and lines[i][0] > item_key_indent:
                                    parts.append(lines[i][1])
                                    i += 1
                                item[kk] = " ".join(parts).strip()
                                continue
                            elif not vv:
                                i += 1
                                cs = i
                                while i < end and lines[i][0] > item_key_indent:
                                    i += 1
                                if cs < i:
                                    ci = lines[cs][0]
                                    item[kk] = _parse_block(cs, i, ci)
                                else:
                                    item[kk] = {}
                                continue
                            else:
                                item[kk] = _parse_scalar(vv)
                                i += 1
                                continue
                    elif ni > item_key_indent:
                        i += 1
                        continue
                    break

                result.append(item)
            else:
                # Plain scalar item
                result.append(_parse_scalar(item_content))
                i += 1

        return result

    if not lines:
        return {}
    top_indent = lines[0][0]
    return _parse_mapping(0, len(lines), top_indent)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_data(path: Path) -> dict[str, Any]:
    """Load a YAML or JSON file with dependency-free fallback.

    This is the SINGLE authoritative loader for all AgentCortex metadata.
    All tools and tests should import and use this function.
    """
    text = path.read_text(encoding="utf-8")

    # 1. Try PyYAML if available (full YAML support)
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]
            return yaml.safe_load(text)  # type: ignore[no-any-return]
        except ImportError:
            pass
        # 2. Built-in YAML-subset parser (no dependencies)
        return _parse_yaml_subset(text)

    # 3. JSON files
    return json.loads(text)  # type: ignore[no-any-return]
