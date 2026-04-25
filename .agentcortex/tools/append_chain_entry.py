#!/usr/bin/env python3
"""ADR-003 — append a hash-chained entry to a JSONL audit log.

Each appended JSON object carries a `prev_sha` field naming the
sha256[:8] of the canonical-form previous entry (with its own `prev_sha`
stripped before hashing for stability). The first (genesis) entry uses
`prev_sha: "GENESIS"`.

Spec: docs/specs/hash-chained-audit-log.md
ADR: docs/adr/ADR-003-hash-chained-audit-log.md

Usage:
  # Append a new entry
  python .agentcortex/tools/append_chain_entry.py append \\
    --path .agentcortex/context/archive/INDEX.jsonl \\
    --entry '{"key": "value", "shipped": "2026-04-25"}'

  # One-time migration: add prev_sha to existing entries that lack it
  python .agentcortex/tools/append_chain_entry.py migrate \\
    --path .agentcortex/context/archive/INDEX.jsonl

Exit codes:
  0  success
  1  usage / parse / IO error
  2  chain integrity failure during migration
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Iterator

PREV_SHA_FIELD = "prev_sha"
GENESIS = "GENESIS"
SHA_LEN = 8


def canonical(entry: dict) -> str:
    """Deterministic JSON serialization for hashing.

    Excludes prev_sha so that re-computation never depends on the very field
    whose value is being computed.
    """
    body = {k: v for k, v in entry.items() if k != PREV_SHA_FIELD}
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def chain_sha(entry: dict) -> str:
    return hashlib.sha256(canonical(entry).encode("utf-8")).hexdigest()[:SHA_LEN]


def iter_entries(path: Path) -> Iterator[tuple[int, dict]]:
    """Yield (line_no, parsed-entry) pairs."""
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {i}: invalid JSON ({exc})") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"line {i}: not a JSON object")
            yield i, obj


def last_entry(path: Path) -> dict | None:
    last = None
    for _, obj in iter_entries(path):
        last = obj
    return last


def append_chained(path: Path, entry: dict) -> dict:
    """Append `entry` with computed prev_sha. Returns the entry as written."""
    if not isinstance(entry, dict):
        raise ValueError("entry must be a JSON object")
    if PREV_SHA_FIELD in entry:
        raise ValueError(f"entry must not contain '{PREV_SHA_FIELD}' (computed by helper)")
    prev = last_entry(path)
    entry_with_chain = dict(entry)
    entry_with_chain[PREV_SHA_FIELD] = chain_sha(prev) if prev is not None else GENESIS
    line = json.dumps(entry_with_chain, sort_keys=True, ensure_ascii=False) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    return entry_with_chain


def migrate(path: Path) -> int:
    """Forward-compute prev_sha for any existing entries missing it.

    Returns the number of entries updated. Pre-migration tampering is
    undetectable (we accept the existing data as the trust anchor).
    """
    if not path.is_file():
        return 0
    entries = [obj for _, obj in iter_entries(path)]
    updated_count = 0
    for i, obj in enumerate(entries):
        expected_prev = GENESIS if i == 0 else chain_sha(entries[i - 1])
        if obj.get(PREV_SHA_FIELD) != expected_prev:
            obj[PREV_SHA_FIELD] = expected_prev
            updated_count += 1
    if updated_count == 0:
        return 0
    # Atomic-replace whole file with migrated entries
    tmp = path.with_suffix(path.suffix + ".migrate.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for obj in entries:
            f.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return updated_count


def cmd_append(args: argparse.Namespace) -> int:
    try:
        entry = json.loads(args.entry)
    except json.JSONDecodeError as exc:
        print(f"--entry must be valid JSON: {exc}", file=sys.stderr)
        return 1
    try:
        written = append_chained(Path(args.path), entry)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"status": "ok", "prev_sha": written[PREV_SHA_FIELD]}))
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    try:
        n = migrate(Path(args.path))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"status": "ok", "migrated": n}))
    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)

    a = sub.add_parser("append", help="Append a new chained entry")
    a.add_argument("--path", required=True)
    a.add_argument("--entry", required=True, help="JSON object (must NOT contain prev_sha)")

    m = sub.add_parser("migrate", help="Forward-compute prev_sha for existing entries lacking it")
    m.add_argument("--path", required=True)

    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "append":
        return cmd_append(args)
    if args.command == "migrate":
        return cmd_migrate(args)
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
