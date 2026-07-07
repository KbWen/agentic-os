#!/usr/bin/env python3
"""Append or archive a hash-chained Global Lesson in current_state.md §Global Lessons.

Sister of append_chain_entry.py; same hash-chain primitive, different
format. The new lesson bullet automatically gets `[prev:<8-char>]`
computed from the previous lesson's canonical form (or `GENESIS` for
the first).

Two operations:

  APPEND (default) — add a new lesson at the end of the section:
    python .agentcortex/tools/append_lesson.py \\
      --category audit-method \\
      --severity HIGH \\
      --trigger multi-agent-roundtable-same-vendor \\
      --body "When using sub-agent expert roundtable for adversarial review..."

  ARCHIVE (--archive) — chain-aware removal of ONE existing lesson (by
  1-based index within §Global Lessons) to make room under the cap:
    python .agentcortex/tools/append_lesson.py --archive \\
      --index 4 \\
      --archive-path .agentcortex/context/archive/global-lessons-archive.md \\
      --index-jsonl .agentcortex/context/archive/INDEX.jsonl

  Archival does three things atomically-in-spirit (moves + re-anchors +
  records) so the chain stays verifiable AFTER a legitimate removal:
    (a) moves the selected lesson bullet from `## Global Lessons` to the
        archive surface (`global-lessons-archive.md`), appending it under a
        dated heading;
    (b) re-anchors the successor lesson's `[prev:]` to the archived entry's
        OWN predecessor hash (i.e. the archived entry's declared `[prev:]`),
        so the surviving chain closes the gap without a rehash cascade;
    (c) writes a `lesson_archive` audit record into the hash-chained
        INDEX.jsonl (via append_chain_entry.py) carrying the removed entry's
        body-sha + old/new prev hashes + the successor's identity, so
        check_lesson_chain.py can distinguish a LEGITIMATE archival bridge
        from silent tampering. A removal WITHOUT such a record still FAILs
        (fail-closed).

The lesson is inserted at the end of the ## Global Lessons section,
BEFORE the next ## section heading (typically "## Ship History").

Exit codes:
  0  succeeded
  1  parse / IO / cap / index error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Reuse the chain primitive from the validator
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_lesson_chain import (  # noqa: E402
    GENESIS,
    LESSON_ARCHIVE_TYPE,
    canonical,
    chain_sha,
    lesson_body_sha,
    parse_lessons,
)

DEFAULT_PATH = Path(".agentcortex/context/current_state.md")
DEFAULT_ARCHIVE_PATH = Path(".agentcortex/context/archive/global-lessons-archive.md")
DEFAULT_INDEX_JSONL = Path(".agentcortex/context/archive/INDEX.jsonl")
GLOBAL_LESSONS_CAP = 20  # mirrors .agent/config.yaml §document_lifecycle


def _section_bounds(lines: list[str]) -> tuple[int | None, int | None, list[int]]:
    """Return (section_start_idx, next_heading_idx, lesson_line_indices).

    section_start_idx = index of the '## Global Lessons' heading.
    next_heading_idx  = index of the next '## ' heading after it (or None).
    lesson_line_indices = 0-based indices of '- [Category:' bullets in-section.
    """
    section_start = None
    next_heading = None
    lesson_idxs: list[int] = []
    in_section = False
    for i, ln in enumerate(lines):
        if ln.startswith("## Global Lessons"):
            in_section = True
            section_start = i
            continue
        if in_section and ln.startswith("## "):
            next_heading = i
            break
        if in_section and ln.lstrip().startswith("- [Category:"):
            lesson_idxs.append(i)
    return section_start, next_heading, lesson_idxs


def append_lesson(
    path: Path,
    category: str,
    severity: str,
    trigger: str,
    body: str,
) -> dict:
    """Append a chained lesson. Returns dict with status + computed prev_sha."""
    if severity not in {"HIGH", "MEDIUM", "LOW"}:
        raise ValueError(f"severity must be HIGH/MEDIUM/LOW, got: {severity}")
    if not category.strip() or not trigger.strip() or not body.strip():
        raise ValueError("category, trigger, body all required (non-empty)")

    lessons = parse_lessons(path)
    if len(lessons) >= GLOBAL_LESSONS_CAP:
        raise ValueError(
            f"Global Lessons at cap ({len(lessons)} >= {GLOBAL_LESSONS_CAP}); "
            f"run /retro to archive LOW-severity entries first "
            f"(use `--archive --index <n>` to make room)"
        )

    if not lessons:
        prev = GENESIS
    else:
        last_cat, last_sev, last_trig, _last_prev, last_body, _ln = lessons[-1]
        prev = chain_sha(last_cat, last_sev, last_trig, last_body)

    new_bullet = (
        f"- [Category: {category.strip()}]"
        f"[Severity: {severity.strip()}]"
        f"[Trigger: {trigger.strip()}]"
        f"[prev: {prev}] {body.strip()}"
    )

    # Find the end of the ## Global Lessons section: insert before the next
    # ## heading (typically "## Ship History").
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=False)
    section_start, insert_at, lesson_idxs = _section_bounds(lines)
    if insert_at is None and lesson_idxs:
        insert_at = lesson_idxs[-1] + 1
    if insert_at is None:
        raise ValueError(
            "Could not locate insertion point; expected '## Global Lessons' "
            "followed by either '## <next-section>' or existing lesson bullets."
        )

    # Insert with surrounding blank handling: the existing pattern is
    # `<lesson>\n<lesson>\n\n## Ship History`. Preserve the trailing blank.
    new_lines = lines[:insert_at] + [new_bullet] + lines[insert_at:]
    path.write_text("\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")

    return {
        "status": "ok",
        "op": "append",
        "prev_sha": prev,
        "appended_at_line": insert_at + 1,
        "total_lessons": len(lessons) + 1,
        "cap": GLOBAL_LESSONS_CAP,
    }


def archive_lesson(
    path: Path,
    index: int,
    archive_path: Path,
    index_jsonl: Path,
    *,
    date: str | None = None,
) -> dict:
    """Chain-aware archival of ONE lesson by 1-based index within §Global Lessons.

    Removes the entry, re-anchors its successor to the entry's own predecessor
    hash, moves the removed bullet to `archive_path`, and records a
    `lesson_archive` audit entry in the hash-chained `index_jsonl`. After this,
    check_lesson_chain.py verifies the surviving chain GREEN because the bridge
    is authorized by the audit record; a removal without the record FAILs.
    """
    import datetime

    lessons = parse_lessons(path)
    if not lessons:
        raise ValueError("no lessons to archive")
    if index < 1 or index > len(lessons):
        raise ValueError(f"--index out of range: {index} (have {len(lessons)} lessons)")

    k = index - 1  # 0-based
    tcat, tsev, ttrig, tprev, tbody, _tln = lessons[k]
    if tsev.strip() == "HIGH":
        raise ValueError(
            f"lesson #{index} is HIGH-severity (pinned); HIGH lessons are exempt "
            f"from archival and can only be removed by explicit user request"
        )

    # Predecessor hash the archived entry currently declares (== chain of k-1,
    # or GENESIS if k == 0). This is exactly what the successor must re-anchor to.
    old_prev_declared = tprev if tprev is not None else (GENESIS if k == 0 else None)
    bridge_prev = tprev.strip() if tprev is not None else GENESIS

    archived_body_sha = lesson_body_sha(tcat, tsev, ttrig, tbody)

    # Successor identity (the entry whose [prev:] we will rewrite), if any.
    successor = None
    if k + 1 < len(lessons):
        scat, ssev, strig, sprev, sbody, _sln = lessons[k + 1]
        successor_declared_prev = sprev.strip() if sprev is not None else None
        successor = {
            "body_sha": lesson_body_sha(scat, ssev, strig, sbody),
            "old_prev": successor_declared_prev,
            "new_prev": bridge_prev,
        }

    # ---- 1) Rewrite current_state.md: drop entry k, re-anchor successor ----
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=False)
    _section_start, _next_heading, lesson_idxs = _section_bounds(lines)
    if len(lesson_idxs) != len(lessons):
        raise ValueError(
            "internal: lesson line-index count mismatch "
            f"({len(lesson_idxs)} lines vs {len(lessons)} parsed)"
        )
    target_line_idx = lesson_idxs[k]
    removed_line = lines[target_line_idx]

    if successor is not None:
        succ_line_idx = lesson_idxs[k + 1]
        succ_line = lines[succ_line_idx]
        # Re-anchor: replace the successor's [prev: <old>] with [prev: <bridge>].
        old_token_val = successor["old_prev"] if successor["old_prev"] is not None else ""
        if successor["old_prev"] is not None:
            lines[succ_line_idx] = succ_line.replace(
                f"[prev: {successor['old_prev']}]", f"[prev: {bridge_prev}]", 1
            )
        if lines[succ_line_idx] == succ_line and successor["old_prev"] is not None:
            # Tolerate spacing variants: [prev:<x>] without the space.
            lines[succ_line_idx] = succ_line.replace(
                f"[prev:{successor['old_prev']}]", f"[prev: {bridge_prev}]", 1
            )
        if lines[succ_line_idx] == succ_line:
            raise ValueError(
                f"could not re-anchor successor lesson at line {succ_line_idx + 1}: "
                f"expected a [prev: {old_token_val}] token to rewrite"
            )

    del lines[target_line_idx]
    path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")

    # ---- 2) Move the removed bullet to the archive surface ----
    when = date or datetime.date.today().isoformat()
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    header = "# Global Lessons Archive\n"
    if not archive_path.exists():
        archive_path.write_text(
            header
            + "\n> Chain-aware archival target for §Global Lessons overflow "
            "(config.yaml §document_lifecycle.global_lessons_max_entries).\n"
            "> Each entry below was removed from current_state.md by "
            "`append_lesson.py --archive` and is authorized by a matching "
            "`lesson_archive` record in `INDEX.jsonl`.\n",
            encoding="utf-8",
        )
    with archive_path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## Archived {when} (prev: {bridge_prev}, body-sha: {archived_body_sha})\n\n")
        fh.write(removed_line.rstrip() + "\n")

    # ---- 3) Record the chain-bridge audit entry in INDEX.jsonl ----
    from append_chain_entry import append_chained

    record = {
        "type": LESSON_ARCHIVE_TYPE,
        "archived_at": when,
        "archived_body_sha": archived_body_sha,
        "archived_prev": bridge_prev,
        "archive_file": archive_path.as_posix(),
    }
    if successor is not None:
        record["successor_body_sha"] = successor["body_sha"]
        record["successor_new_prev"] = successor["new_prev"]
    else:
        record["successor_body_sha"] = None
        record["successor_new_prev"] = None
    written = append_chained(index_jsonl, record)

    return {
        "status": "ok",
        "op": "archive",
        "archived_index": index,
        "archived_body_sha": archived_body_sha,
        "bridge_prev": bridge_prev,
        "successor_reanchored": successor is not None,
        "index_prev_sha": written.get("prev_sha"),
        "total_lessons": len(lessons) - 1,
        "cap": GLOBAL_LESSONS_CAP,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument(
        "--archive",
        action="store_true",
        help="Archive (chain-aware remove) an existing lesson instead of appending a new one",
    )
    # append-mode args
    ap.add_argument("--category", help="APPEND: e.g. audit-method, classification-flow")
    ap.add_argument("--severity", choices=("HIGH", "MEDIUM", "LOW"), help="APPEND: severity")
    ap.add_argument("--trigger", help="APPEND: kebab-case normalized trigger key")
    ap.add_argument("--body", help="APPEND: lesson body text (single line)")
    # archive-mode args
    ap.add_argument("--index", type=int, help="ARCHIVE: 1-based index of the lesson to archive")
    ap.add_argument(
        "--archive-path",
        default=str(DEFAULT_ARCHIVE_PATH),
        help="ARCHIVE: destination archive markdown file",
    )
    ap.add_argument(
        "--index-jsonl",
        default=str(DEFAULT_INDEX_JSONL),
        help="ARCHIVE: hash-chained audit log to record the bridge record in",
    )
    ap.add_argument("--date", help="ARCHIVE: override the archival date (YYYY-MM-DD); default today")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.archive:
            if args.index is None:
                raise ValueError("--archive requires --index <n> (1-based)")
            result = archive_lesson(
                Path(args.path),
                index=args.index,
                archive_path=Path(args.archive_path),
                index_jsonl=Path(args.index_jsonl),
                date=args.date,
            )
        else:
            missing = [
                name
                for name, val in (
                    ("--category", args.category),
                    ("--severity", args.severity),
                    ("--trigger", args.trigger),
                    ("--body", args.body),
                )
                if not val
            ]
            if missing:
                raise ValueError(f"append mode requires: {', '.join(missing)}")
            result = append_lesson(
                Path(args.path),
                category=args.category,
                severity=args.severity,
                trigger=args.trigger,
                body=args.body,
            )
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    import json

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
