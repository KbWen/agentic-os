#!/usr/bin/env python3
"""Structural validator for `routing_actions` blocks in docs/reviews/*.md (ADR-006).

Governance self-audit 2026-07-11 (F3): the native validators searched the WHOLE
review file for required-field substrings ('finding:', 'target_doc:', ...) and
validated only standalone `target_doc:`/`status:` lines. A single inline YAML
mapping —

    routing_actions:
      - {finding: "x", target_doc: "../../escape.md", status: bogus, owner: y}

— contains every required substring but matches neither value parser, so invalid
paths (path traversal / non-canonical docs) and unrecognized statuses passed as
"structurally valid".

This tool closes that hole by parsing ONLY the fenced/keyed routing_actions block
into structured records and validating every record:

  * required fields present (finding, target_doc, status, owner) WITHIN the block
  * target_doc matches `^docs/(architecture|specs)/.+\\.md$` with no `..` traversal
  * status in {pending, merged, rejected}
  * inline-map (`- { ... }`) and non-list forms are rejected outright (unvalidated)

target_doc that is well-formed but missing on disk is a WARN (advisory, as today),
as is a stale `pending` action whose review file is older than the configured
threshold. Structural violations FAIL (exit 1); everything else exits 0.

Only the CANONICAL column-0 `routing_actions:` block is validated. Indented
occurrences are in-prose examples (an audit report may quote an attack fixture
inside a list item) and are skipped — otherwise a report documenting a malformed
form would false-FAIL on its own evidence.

Dependency-free: no PyYAML assumption — a small deterministic line parser is used
so inline-map rejection behaves identically whether or not PyYAML is installed
(the shared _yaml_loader would silently mis-parse or leniently accept inline maps
depending on backend).

Exit codes:
  0  no structural violations (WARN advisories, if any, are printed to stdout)
  1  one or more structural violations (printed to stdout as `FAIL: ...`)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ("finding", "target_doc", "status", "owner")
VALID_STATUSES = {"pending", "merged", "rejected"}
TARGET_DOC_RE = re.compile(r"^docs/(architecture|specs)/.+\.md$")
DEFAULT_PENDING_WARN_DAYS = 14

_ROUTING_KEY_RE = re.compile(r"^(?P<indent>[ \t]*)routing_actions:[ \t]*$")
_LIST_ITEM_RE = re.compile(r"^(?P<indent>[ \t]*)-[ \t]*(?P<body>.*)$")
_KV_RE = re.compile(r"^[ \t]*(?P<key>[A-Za-z_][A-Za-z0-9_]*):[ \t]*(?P<val>.*?)[ \t]*$")
_FILENAME_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


class RoutingBlock:
    """One parsed routing_actions block: its records and any parse-time errors."""

    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []
        self.errors: list[str] = []


def parse_routing_blocks(text: str) -> list[RoutingBlock]:
    """Parse every `routing_actions:` block in *text* into structured records.

    A block is bounded by the `routing_actions:` key line and the first code
    fence (```) or dedent to a sibling key. Inline-map list items (`- { ... }`)
    are recorded as errors and produce no record.
    """
    lines = text.splitlines()
    blocks: list[RoutingBlock] = []
    n = len(lines)
    i = 0
    while i < n:
        key_match = _ROUTING_KEY_RE.match(lines[i])
        if not key_match:
            i += 1
            continue
        key_indent = len(key_match.group("indent"))
        if key_indent != 0:
            # An INDENTED `routing_actions:` is an in-prose example (e.g. an audit
            # report quoting an attack fixture inside a list item), not the
            # canonical column-0 block that /govern-audit emits and /ship consumes.
            # Validating quoted examples would false-FAIL reports that document the
            # very malformed forms this tool rejects.
            i += 1
            continue
        block = RoutingBlock()
        current: dict[str, str] | None = None
        item_indent: int | None = None
        i += 1
        while i < n:
            line = lines[i]
            stripped = line.strip()
            if stripped == "":
                i += 1
                continue
            if stripped.startswith("```"):
                break  # code fence terminates the block
            indent = _indent_of(line)
            item = _LIST_ITEM_RE.match(line)
            if item and (item_indent is None or indent == item_indent):
                if item_indent is None:
                    item_indent = indent
                body = item.group("body").strip()
                if body.startswith("{"):
                    block.errors.append(
                        "inline-map form not permitted; use block mappings "
                        "(`- finding:` on its own line): " + stripped
                    )
                    current = None
                    i += 1
                    continue
                current = {}
                block.records.append(current)
                kv = _KV_RE.match(body)
                if kv:
                    current[kv.group("key")] = _unquote(kv.group("val"))
                i += 1
                continue
            if current is not None and item_indent is not None and indent > item_indent:
                kv = _KV_RE.match(stripped)
                if kv:
                    current[kv.group("key")] = _unquote(kv.group("val"))
                i += 1
                continue
            if indent <= key_indent:
                break  # dedent to a sibling key / section ends the block
            i += 1  # deeper orphan line with no active record — ignore
        blocks.append(block)
    return blocks


def _pending_warn_days(config_path: Path) -> int:
    """Read document_lifecycle.routing_actions_pending_warn_days (default 14)."""
    if not config_path.is_file():
        return DEFAULT_PENDING_WARN_DAYS
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _yaml_loader import load_data  # type: ignore  # noqa: E402

        data = load_data(config_path)
        lifecycle = data.get("document_lifecycle") or {}
        return int(lifecycle.get("routing_actions_pending_warn_days", DEFAULT_PENDING_WARN_DAYS))
    except Exception:
        return DEFAULT_PENDING_WARN_DAYS


def _review_age_days(name: str, today: _dt.date) -> int | None:
    """Age in days from a leading YYYY-MM-DD in the review filename, or None."""
    m = _FILENAME_DATE_RE.match(name)
    if not m:
        return None
    try:
        review_date = _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
    return (today - review_date).days


def validate_review(
    review: Path, root: Path, pending_warn_days: int, today: _dt.date
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a single review file."""
    errors: list[str] = []
    warnings: list[str] = []
    try:
        text = review.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:  # pragma: no cover - IO edge
        return [f"could not read {review.name}: {exc}"], []

    blocks = parse_routing_blocks(text)
    if not blocks:
        return errors, warnings  # no routing_actions in this file

    has_pending = False
    for block in blocks:
        errors.extend(f"{review.name}: {e}" for e in block.errors)
        if not block.records and not block.errors:
            errors.append(
                f"{review.name}: routing_actions present but no valid action "
                "records parsed (expected a YAML list of block mappings)"
            )
        for idx, record in enumerate(block.records):
            for field in REQUIRED_FIELDS:
                if not record.get(field):
                    errors.append(
                        f"{review.name}: routing_actions record #{idx + 1} missing "
                        f"required field '{field}'"
                    )
            target = record.get("target_doc", "")
            if target:
                if ".." in target or not TARGET_DOC_RE.match(target):
                    errors.append(
                        f"{review.name}: routing_actions target_doc must match "
                        "^docs/(architecture|specs)/.+.md$ with no path traversal: "
                        f"{target}"
                    )
                elif not (root / target).is_file():
                    warnings.append(
                        f"{review.name}: routing_actions target_doc does not exist "
                        f"yet: {target}"
                    )
            status = record.get("status", "")
            if status and status not in VALID_STATUSES:
                errors.append(
                    f"{review.name}: routing_actions status must be pending, merged, "
                    f"or rejected: {status}"
                )
            if status == "pending":
                has_pending = True

    if has_pending:
        age = _review_age_days(review.name, today)
        if age is not None and age >= pending_warn_days:
            warnings.append(
                f"{review.name}: stale pending routing_actions ({age}d old, "
                f"threshold {pending_warn_days}d) needs canonical-doc follow-up"
            )
    return errors, warnings


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Structurally validate routing_actions blocks in docs/reviews/*.md. "
            "Exit 1 on structural violations; WARN advisories print but exit 0."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument(
        "--reviews-dir",
        default=None,
        help="Reviews directory (default: <root>/docs/reviews)",
    )
    ap.add_argument(
        "--config",
        default=None,
        help="Config file for the pending-warn threshold (default: <root>/.agent/config.yaml)",
    )
    return ap.parse_args()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    args = parse_args()
    root = Path(args.root).resolve()
    reviews_dir = Path(args.reviews_dir) if args.reviews_dir else root / "docs" / "reviews"
    config_path = Path(args.config) if args.config else root / ".agent" / "config.yaml"

    if not reviews_dir.is_dir():
        # Capability-by-presence: no reviews to validate.
        print("routing_actions: no docs/reviews directory; nothing to check.")
        return 0

    pending_warn_days = _pending_warn_days(config_path)
    today = _dt.datetime.now(_dt.timezone.utc).date()

    errors: list[str] = []
    warnings: list[str] = []
    checked = 0
    for review in sorted(reviews_dir.glob("*.md")):
        if not review.is_file():
            continue
        file_errors, file_warnings = validate_review(review, root, pending_warn_days, today)
        errors.extend(file_errors)
        warnings.extend(file_warnings)
        checked += 1

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"FAIL: {error}")

    if errors:
        print(f"routing_actions: {len(errors)} structural violation(s) across {checked} review file(s).")
        return 1

    print(
        f"routing_actions: structurally valid across {checked} review file(s)"
        + (f" ({len(warnings)} advisory warning(s))" if warnings else "")
        + "."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
