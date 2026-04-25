#!/usr/bin/env python3
"""Hash-chain validator for current_state.md §Global Lessons.

Sister of check_audit_chain.py (ADR-003); same primitive, different format.
Each lesson bullet carries `[prev:<8-char>]` between the trigger tag and
the body. The hash is sha256[:8] of the canonical form (tags + body
WITHOUT the prev token), matching the convention used in
append_chain_entry.py.

Closes one half of the L4 honor-system gap for Global Lessons:
without the chain, an agent could silently delete an inconvenient
lesson (e.g., remove L4 itself to weaken the rule against silent
deletion). The chain makes any retroactive edit cryptographically
detectable.

Exit codes:
  0  chain intact (or no lessons / file missing — capability-by-presence)
  1  chain broken at one or more lessons
  2  parse / IO error
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

GENESIS = "GENESIS"
SHA_LEN = 8

# Match: `- [Category:<tag>][Severity:<level>][Trigger:<key>][prev:<sha>] <body>`
# The [prev:...] token is OPTIONAL during parsing so we can detect missing-prev
# as a chain error rather than a parse error.
LESSON_RE = re.compile(
    r"^- \[Category:\s*([^\]]+?)\s*\]\s*"
    r"\[Severity:\s*([^\]]+?)\s*\]\s*"
    r"\[Trigger:\s*([^\]]+?)\s*\]\s*"
    r"(?:\[prev:\s*([^\]]+?)\s*\]\s*)?"
    r"(.+)$"
)


def canonical(category: str, severity: str, trigger: str, body: str) -> str:
    """Deterministic form for hashing, EXCLUDING the [prev:...] token."""
    return (
        f"[Category:{category.strip()}]"
        f"[Severity:{severity.strip()}]"
        f"[Trigger:{trigger.strip()}] "
        f"{body.strip()}"
    )


def chain_sha(category: str, severity: str, trigger: str, body: str) -> str:
    return hashlib.sha256(canonical(category, severity, trigger, body).encode("utf-8")).hexdigest()[:SHA_LEN]


def parse_lessons(path: Path) -> list[tuple[str, str, str, str | None, str, int]]:
    """Yield (category, severity, trigger, prev, body, line_no) per lesson bullet
    inside the ## Global Lessons section."""
    lessons = []
    if not path.is_file():
        return lessons
    text = path.read_text(encoding="utf-8")
    in_section = False
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.rstrip("\n")
        if stripped.startswith("## Global Lessons"):
            in_section = True
            continue
        if in_section and stripped.startswith("## "):
            break
        if not in_section:
            continue
        if not stripped.lstrip().startswith("- [Category:"):
            continue
        m = LESSON_RE.match(stripped.lstrip())
        if not m:
            continue  # skip malformed bullets (will be caught elsewhere)
        cat, sev, trig, prev, body = m.groups()
        lessons.append((cat, sev, trig, prev, body, line_no))
    return lessons


def check_chain(path: Path) -> tuple[bool, list[str]]:
    """Return (intact, error-strings)."""
    errors: list[str] = []
    lessons = parse_lessons(path)
    if not lessons:
        return True, []
    prev_obj: tuple[str, str, str, str] | None = None
    for cat, sev, trig, declared_prev, body, line_no in lessons:
        expected = GENESIS if prev_obj is None else chain_sha(*prev_obj)
        if declared_prev is None:
            errors.append(
                f"line {line_no}: lesson missing '[prev:...]' token "
                f"(expected '[prev:{expected}]')"
            )
        elif declared_prev != expected:
            errors.append(
                f"line {line_no}: chain broken — declared prev='{declared_prev}', "
                f"expected '{expected}'"
            )
        prev_obj = (cat, sev, trig, body)
    return (len(errors) == 0), errors


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--path",
        default=".agentcortex/context/current_state.md",
        help="Path to current_state.md (default: .agentcortex/context/current_state.md)",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-line errors; only emit the summary line",
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
        print(f"lesson chain intact: {path}")
        return 0

    if not args.quiet:
        for err in errors:
            print(f"  [FAIL] {err}", file=sys.stderr)
    print(f"lesson chain BROKEN: {path} ({len(errors)} error(s))")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
