#!/usr/bin/env python3
"""Verify a hash-chained JSONL audit log.

Walks each line, recomputes the canonical sha256[:8] of the previous
entry (excluding its prev_sha field), and compares to the declared
prev_sha. Any mismatch = chain broken = retroactive tampering detected.
Counterpart to append_chain_entry.py.

Exit codes:
  0  chain intact (or file empty / missing — capability-by-presence)
  1  chain broken at one or more lines
  2  parse / IO error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Reuse the helper to keep canonicalization in one place
sys.path.insert(0, str(Path(__file__).resolve().parent))
from append_chain_entry import (  # noqa: E402
    GENESIS,
    PREV_SHA_FIELD,
    chain_sha,
    iter_entries,
)


def check_chain(path: Path) -> tuple[bool, list[str]]:
    """Return (chain_intact, list-of-error-strings)."""
    errors: list[str] = []
    if not path.is_file():
        return True, []  # capability-by-presence; nothing to check
    try:
        entries = list(iter_entries(path))
    except ValueError as exc:
        return False, [f"parse error: {exc}"]

    prev_obj: dict | None = None
    for line_no, obj in entries:
        declared = obj.get(PREV_SHA_FIELD)
        expected = GENESIS if prev_obj is None else chain_sha(prev_obj)
        if declared is None:
            errors.append(
                f"line {line_no}: missing '{PREV_SHA_FIELD}' field "
                f"(expected '{expected}')"
            )
        elif declared != expected:
            errors.append(
                f"line {line_no}: chain broken — declared prev_sha='{declared}', "
                f"expected '{expected}'"
            )
        prev_obj = obj

    return (len(errors) == 0), errors


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--path", required=True, help="Target JSONL file to verify")
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Only emit the final summary line; suppress per-line errors",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    try:
        intact, errors = check_chain(path)
    except OSError as exc:
        print(f"IO error: {exc}", file=sys.stderr)
        return 2

    if intact:
        print(f"audit chain intact: {path}")
        return 0

    if not args.quiet:
        for err in errors:
            print(f"  [FAIL] {err}", file=sys.stderr)
    print(f"audit chain BROKEN: {path} ({len(errors)} error(s))")

    # Say what to do about it. This checker now ships downstream, and validate.sh calls
    # it with --quiet, so without this an adopter sees only "BROKEN" and no next step.
    # The two failure modes need opposite advice and must not be conflated:
    #   * every error is a MISSING prev_sha -> a pre-chain log, recoverable in one command
    #   * any error is a MISMATCH -> a real break; migrate refuses to re-bless it, on purpose
    only_missing = all("missing '" + PREV_SHA_FIELD + "'" in e for e in errors)
    if only_missing:
        print(
            "  -> Every entry is simply missing prev_sha, i.e. this log predates the "
            "hash chain. Fill them in with:\n"
            f"       python .agentcortex/tools/append_chain_entry.py migrate --path {path}\n"
            "     Commit the result: the append-only witness compares the merge-base "
            "copy to the working copy, so it stays red until the migration is committed "
            "and merged. That visibility is deliberate -- a rewrite of an audit log "
            "should be reviewable, not silent."
        )
    else:
        print(
            "  -> At least one entry declares a prev_sha that does not match its "
            "predecessor. `migrate` will REFUSE this on purpose: it only fills in missing "
            "values and never re-blesses a mismatch, because a tamper-evident log that "
            "can be silently repaired is not tamper-evident. Inspect the entries above, "
            "establish what happened, and record the finding -- do not overwrite the "
            "chain to make this green."
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
