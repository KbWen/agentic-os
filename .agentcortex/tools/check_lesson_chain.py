#!/usr/bin/env python3
"""Hash-chain validator for current_state.md §Global Lessons.

Sister of check_audit_chain.py; same hash-chain primitive, different
format. Each lesson bullet carries `[prev:<8-char>]` between the trigger
tag and the body. The hash is sha256[:8] of the canonical form (tags +
body WITHOUT the prev token), matching the convention used in
append_chain_entry.py.

Without the chain, an agent could silently delete an inconvenient
lesson — for example, removing a lesson that constrains its own future
behaviour. The chain makes any retroactive edit cryptographically
detectable.

Legitimate archival: when the Global Lessons section hits its cap, one
entry may be moved to `.agentcortex/context/archive/global-lessons-archive.md`
by `append_lesson.py --archive`. That tool re-anchors the archived entry's
successor to the archived entry's OWN predecessor hash and records a
`lesson_archive` audit entry in the hash-chained `INDEX.jsonl`. This
validator walks the surviving chain; where a link does not match the
immediate predecessor, it accepts the break ONLY IF a matching
`lesson_archive` record authorizes exactly that bridge. A removal WITHOUT
a matching record is still reported as a broken chain (fail-closed).

Exit codes:
  0  chain intact (or no lessons / file missing — capability-by-presence)
  1  chain broken at one or more lessons
  2  parse / IO error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

GENESIS = "GENESIS"
SHA_LEN = 8

# Audit-record type (in INDEX.jsonl) that authorizes a legitimate archival bridge.
LESSON_ARCHIVE_TYPE = "lesson_archive"
DEFAULT_INDEX_JSONL = ".agentcortex/context/archive/INDEX.jsonl"

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


# lesson_body_sha is the identity hash of a single lesson (== chain_sha of that
# entry). Aliased so callers reading/writing archival records self-document.
lesson_body_sha = chain_sha


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


def load_archive_bridges(index_jsonl: Path) -> dict[tuple[str, str], dict]:
    """Read `lesson_archive` records from the hash-chained INDEX.jsonl.

    Returns a map keyed by (successor_body_sha, successor_new_prev) → record,
    so the verifier can look up whether a specific bridge is authorized.
    Records with a null successor (archived the tail entry — no successor to
    re-anchor) are keyed by ("__tail__", archived_prev); the walk never needs
    them (a removed tail leaves the surviving chain unbroken) but they are
    retained for auditability. Absent/malformed INDEX → empty map (fail-closed:
    no bridges authorized, so any break FAILs).
    """
    bridges: dict[tuple[str, str], dict] = {}
    if not index_jsonl.is_file():
        return bridges
    try:
        for raw in index_jsonl.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict) or obj.get("type") != LESSON_ARCHIVE_TYPE:
                continue
            succ_sha = obj.get("successor_body_sha")
            succ_new_prev = obj.get("successor_new_prev")
            if succ_sha is None or succ_new_prev is None:
                bridges[("__tail__", str(obj.get("archived_prev")))] = obj
                continue
            bridges[(str(succ_sha), str(succ_new_prev))] = obj
    except OSError:
        return bridges
    return bridges


def _archive_body_shas(archive_path: Path) -> set[str]:
    """Body-shas of every `- [Category:...]` bullet in an archive markdown file."""
    shas: set[str] = set()
    if not archive_path.is_file():
        return shas
    try:
        text = archive_path.read_text(encoding="utf-8")
    except OSError:
        return shas
    for raw in text.splitlines():
        stripped = raw.rstrip("\n").lstrip()
        if not stripped.startswith("- [Category:"):
            continue
        m = LESSON_RE.match(stripped)
        if not m:
            continue
        cat, sev, trig, _prev, body = m.groups()
        shas.add(lesson_body_sha(cat, sev, trig, body))
    return shas


def check_archive_integrity(index_jsonl: Path, *, root: Path | None = None) -> list[str]:
    """For each `lesson_archive` record, confirm the archived bullet still exists
    verbatim in its archive file (body-sha matches `archived_body_sha`).

    Makes a post-archival edit of the moved bullet detectable: the INDEX record
    pins the original content and is itself tamper-evident (check_audit_chain),
    so a mismatch means the archive file was altered after the move. Returns a
    list of error strings (empty = clean). Records whose archive file is absent
    are skipped (capability-by-presence — nothing to compare against).
    """
    errors: list[str] = []
    if not index_jsonl.is_file():
        return errors
    cache: dict[Path, set[str]] = {}
    try:
        raw_lines = index_jsonl.read_text(encoding="utf-8").splitlines()
    except OSError:
        return errors
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != LESSON_ARCHIVE_TYPE:
            continue
        body_sha = obj.get("archived_body_sha")
        archive_file = obj.get("archive_file")
        if not body_sha or not archive_file:
            continue
        arc_path = Path(archive_file)
        if root is not None and not arc_path.is_absolute():
            arc_path = root / arc_path
        if not arc_path.is_file():
            continue  # archive file absent → nothing to compare (present-only)
        if arc_path not in cache:
            cache[arc_path] = _archive_body_shas(arc_path)
        if str(body_sha) not in cache[arc_path]:
            errors.append(
                f"archive integrity: lesson_archive record body-sha '{body_sha}' "
                f"not found in {arc_path.as_posix()} — archived entry was edited "
                f"or removed after archival (record is tamper-evident via "
                f"check_audit_chain)"
            )
    return errors


def check_chain(path: Path, index_jsonl: Path | None = None) -> tuple[bool, list[str]]:
    """Return (intact, error-strings).

    A link that does not match its immediate predecessor is accepted only when
    a matching `lesson_archive` record in `index_jsonl` authorizes the bridge.
    """
    errors: list[str] = []
    lessons = parse_lessons(path)
    if not lessons:
        return True, []
    if index_jsonl is None:
        index_jsonl = path.parent / "archive" / "INDEX.jsonl"
    bridges = load_archive_bridges(index_jsonl)

    prev_obj: tuple[str, str, str, str] | None = None
    for cat, sev, trig, declared_prev, body, line_no in lessons:
        expected = GENESIS if prev_obj is None else chain_sha(*prev_obj)
        if declared_prev is None:
            errors.append(
                f"line {line_no}: lesson missing '[prev:...]' token "
                f"(expected '[prev:{expected}]')"
            )
        elif declared_prev != expected:
            # The immediate-predecessor link is broken. Accept ONLY if an
            # archival bridge authorizes exactly this (entry, declared_prev).
            body_sha = lesson_body_sha(cat, sev, trig, body)
            bridge = bridges.get((body_sha, declared_prev))
            if bridge is not None and str(bridge.get("archived_prev")) == declared_prev:
                # Legitimate archival: an entry was removed between the previous
                # surviving entry and this one; this entry now re-anchors to the
                # archived entry's own predecessor. Chain remains intact.
                pass
            else:
                errors.append(
                    f"line {line_no}: chain broken — declared prev='{declared_prev}', "
                    f"expected '{expected}' (no authorizing lesson_archive record in "
                    f"{index_jsonl.as_posix()})"
                )
        prev_obj = (cat, sev, trig, body)

    # Archive-integrity: every authorized archival record must still match its
    # archived bullet verbatim (detects a post-move edit of the archive file).
    errors.extend(check_archive_integrity(index_jsonl))

    return (len(errors) == 0), errors


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--path",
        default=".agentcortex/context/current_state.md",
        help="Path to current_state.md (default: .agentcortex/context/current_state.md)",
    )
    ap.add_argument(
        "--index-jsonl",
        default=None,
        help="Path to the archive INDEX.jsonl carrying lesson_archive bridge records "
        "(default: <current_state dir>/archive/INDEX.jsonl)",
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
    index_jsonl = Path(args.index_jsonl) if args.index_jsonl else None
    try:
        intact, errors = check_chain(path, index_jsonl)
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
