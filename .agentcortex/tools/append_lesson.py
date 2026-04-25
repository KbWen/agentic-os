#!/usr/bin/env python3
"""Append a hash-chained Global Lesson to current_state.md §Global Lessons.

Sister of append_chain_entry.py (ADR-003); same primitive, different format.
The new lesson bullet automatically gets `[prev:<8-char>]` computed from
the previous lesson's canonical form (or `GENESIS` for the first).

Usage:
  python .agentcortex/tools/append_lesson.py \\
    --category audit-method \\
    --severity HIGH \\
    --trigger multi-agent-roundtable-same-vendor \\
    --body "When using sub-agent expert roundtable for adversarial review..."

The lesson is inserted at the end of the ## Global Lessons section,
BEFORE the next ## section heading (typically "## Ship History").

Exit codes:
  0  appended successfully
  1  parse / IO / cap error (Global Lessons cap exceeded)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Reuse the chain primitive from the validator
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_lesson_chain import GENESIS, canonical, chain_sha, parse_lessons  # noqa: E402

DEFAULT_PATH = Path(".agentcortex/context/current_state.md")
GLOBAL_LESSONS_CAP = 20  # mirrors .agent/config.yaml §document_lifecycle


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
            f"run /retro to archive LOW-severity entries first"
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
    in_section = False
    insert_at = None
    last_lesson_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("## Global Lessons"):
            in_section = True
            continue
        if in_section and ln.startswith("## "):
            insert_at = i  # insert BEFORE next section heading
            break
        if in_section and ln.lstrip().startswith("- [Category:"):
            last_lesson_idx = i

    if insert_at is None and last_lesson_idx is not None:
        insert_at = last_lesson_idx + 1
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
        "prev_sha": prev,
        "appended_at_line": insert_at + 1,
        "total_lessons": len(lessons) + 1,
        "cap": GLOBAL_LESSONS_CAP,
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--path", default=str(DEFAULT_PATH))
    ap.add_argument("--category", required=True, help="e.g. audit-method, classification-flow")
    ap.add_argument("--severity", required=True, choices=("HIGH", "MEDIUM", "LOW"))
    ap.add_argument("--trigger", required=True, help="kebab-case normalized trigger key")
    ap.add_argument("--body", required=True, help="Lesson body text (single line)")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    try:
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
