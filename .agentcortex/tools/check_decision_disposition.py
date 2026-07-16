#!/usr/bin/env python3
"""Advisory disposition checker for archived Work Log `## Decisions` (spec AC-5).

Backstops the ship-time Decision Disposition step (ship.md §State Update 2b):
every `### D-` entry in a Work Log's `## Decisions` section must carry one of
the three disposition markers before the log is archived —

  * `→ promoted: ADR-<id>`     (durable precedent → ADR)
  * `→ consolidated: L2 <domain>` (folded into a Domain Doc Layer-2 log)
  * `→ local`                  (branch-local; the INDEX 1-liner is its home)

This tool scans tracked archive ROOT logs (`.agentcortex/context/archive/*.md`,
non-recursive so the gitignored/compaction `work/` subdir is excluded; also
skips `ship-history-*.md` and `.gitkeep.md`) and, for each in-scope log, WARNs
when a `### D-` entry body carries NONE of the three markers (Signal A). An
independent Signal A2 flags entries that ARE disposed `→ local` but whose text
names an ADR id (`ADR-\\d`) — a likely rubber-stamp where `→ promoted` /
`→ consolidated` applies. Each signal aggregates into at most ONE WARN line
(max 2 physical WARN lines per run).

Grandfathering + activation share ONE switch,
`document_lifecycle.decision_disposition_since` in .agent/config.yaml:
  * key set to a date -> only logs whose ship date >= that date are checked.
    The framework ships config.yaml core-tier WITH the key set, so deployed
    downstream forks are ACTIVE by default at the framework cutoff; the date
    grandfathers every log archived before it (ADR-002 date-grandfather
    precedent) — including this repo's legacy archive-root `## Decisions`
    logs (3 carry the section header; only 1 holds real `### D-` entries;
    2 more sit under the excluded `work/` subdir).
  * key absent/empty  -> the check is a silent no-op (prints a one-line
    note). This is the source-mode / bring-your-own-config path, not the
    deployed default.
A log's ship date comes from the archive INDEX.jsonl `shipped` field
(matched by the `log` filename); when the log has no INDEX entry, the
`-YYYYMMDD` filename suffix is the fallback. A log whose date cannot be
determined by either route is skipped (conservative: never a false WARN).
Date comparison is a lexicographic string compare and assumes zero-padded
ISO dates — which both the INDEX `shipped` field and the filename suffix
are; a non-padded date (e.g. `2026-7-1`) would mis-gate. Documented
limitation.

ADVISORY-ONLY contract (mirrors check_ssot_caps.py + the run_python_check /
Invoke-PythonCheck WARN-tier wiring): this tool ALWAYS exits 0, so the
validator never FAILs on an undisposed log. Findings aggregate into at most
one `WARN:` line per signal, naming the offending files; the fix is the
disposition step, not the validator. Note the Signal A WARN is intentionally
non-clearing: a marker can never be added back to an immutable archived log,
so after the forward-fix (ADR/L2 entry) the persisting line IS the accepted
historical gap. Capability-by-presence: a missing archive dir exits 0 silently.

Exit codes:
  0  always (advisory — never fails the validator). Findings, if any, are
     printed to stdout as at most two aggregated `WARN: ...` lines (one per
     signal).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Disposition marker vocabulary — a regex-stable 4-surface API (decide.md §5,
# worklog template hint, ship.md 2b, this tool). Any wording change is a
# 4-surface sync (spec Constraint + AC-8 vocabulary-exactness guard). The
# canonical arrow is U+2192 RIGHTWARDS ARROW; every EMIT surface writes `→`.
# Accept-side leniency: entry text is normalized `->` -> `→` before matching,
# so a hand-typed ASCII `-> local` still counts as disposed. Everything else
# is matched as a literal substring, so true near-misses (`→ promote:`,
# `→ Promoted:` case-mismatch, `→consolidated` missing space) stay rejected.
MARKERS = (
    "→ promoted: ADR-",
    "→ consolidated: L2 ",
    "→ local",
)

DECISIONS_HEADER = "## Decisions"
D_ENTRY_RE = re.compile(r"^### D-")
# `-YYYYMMDD.md` filename-date fallback (used when a log has no INDEX entry).
FILENAME_DATE_RE = re.compile(r"-(\d{4})(\d{2})(\d{2})\.md$")
# Signal A2: an entry disposed `→ local` whose text names an ADR id is a
# likely rubber-stamp (`→ promoted`/`→ consolidated` probably applies).
# Fenced content never reaches entry bodies (parse_decision_entries skips
# it), so a quoted ADR id inside a ``` fence cannot trip this.
ADR_ID_RE = re.compile(r"ADR-\d+")


def _read_cutoff(config_path: Path) -> str | None:
    """Return the configured `decision_disposition_since` date, or None.

    None (absent file, absent/empty key, or any parse failure) means the
    feature is OFF — the caller prints the not-configured note and exits 0.
    """
    if not config_path.is_file():
        return None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _yaml_loader import load_data  # type: ignore  # noqa: E402

        data = load_data(config_path)
        lifecycle = (data or {}).get("document_lifecycle") or {}
        raw = lifecycle.get("decision_disposition_since")
        if raw is None:
            return None
        value = str(raw).strip()
        return value or None
    except Exception:
        # Any parse/import failure → treat as not-configured (advisory tool,
        # never fail, never false-warn).
        return None


def _build_index_dates(index_path: Path) -> dict[str, str]:
    """Map archived log filename -> `shipped` date from INDEX.jsonl.

    Unreadable / malformed lines are skipped (never crash). Lines without both
    a `log` and a `shipped` field (e.g. worklog_archive pointer records) are
    naturally ignored.
    """
    dates: dict[str, str] = {}
    if not index_path.is_file():
        return dates
    try:
        text = index_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return dates
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            # Skip this unreadable line — never abort the whole scan.
            continue
        if not isinstance(obj, dict):
            continue
        log = obj.get("log")
        shipped = obj.get("shipped")
        if isinstance(log, str) and isinstance(shipped, str) and log and shipped:
            dates[log] = shipped
    return dates


def _filename_date(filename: str) -> str | None:
    """Extract `YYYY-MM-DD` from a `-YYYYMMDD.md` filename suffix, or None."""
    m = FILENAME_DATE_RE.search(filename)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def parse_decision_entries(lines: list[str]) -> list[str]:
    """Return each `### D-` entry block (heading + body) in `## Decisions`.

    A block runs from its `### D-` heading up to (not including) the next
    `###`/`##` heading. Text outside the Decisions section, and any non-`D-`
    `###` subheading, terminate the current block. Returns [] when there is no
    `## Decisions` section or it holds no `### D-` entries.

    Lines inside ``` code fences are invisible to the parser — for BOTH the
    `## Decisions` section detection and `### D-` entry detection — so a log
    that merely QUOTES the format in a fenced block (e.g. this feature's own
    dogfood work log) never opens a section or an entry.
    """
    in_section = False
    in_fence = False
    entries: list[list[str]] = []
    current: list[str] | None = None

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        # ``` fence delimiters toggle state; the delimiters and all fenced
        # content are skipped entirely (headings inside a fence are quotes,
        # not structure).
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if not in_section:
            if stripped == DECISIONS_HEADER:
                in_section = True
            continue

        # A new top-level `## ` heading ends the Decisions section entirely.
        if line.startswith("## ") and not line.startswith("### "):
            break

        if D_ENTRY_RE.match(line):
            if current is not None:
                entries.append(current)
            current = [line]
        elif line.startswith("### "):
            # A non-`D-` `###` subheading closes the current entry; its own
            # lines belong to no decision entry.
            if current is not None:
                entries.append(current)
                current = None
        elif current is not None:
            current.append(line)

    if current is not None:
        entries.append(current)

    return ["\n".join(block) for block in entries]


def entry_is_disposed(entry_text: str) -> bool:
    """True when the entry block carries at least one disposition marker.

    Accept is lenient on the arrow glyph only: ASCII `->` in the entry text is
    normalized to `→` before matching (emit surfaces always write `→`). Word
    choice, case, and spacing stay strict.
    """
    normalized = entry_text.replace("->", "→")
    return any(marker in normalized for marker in MARKERS)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory disposition checker for archived Work Log `## Decisions`. "
            "Always exits 0; prints a WARN line for post-cutoff logs with an "
            "undisposed `### D-` entry. Silent no-op until the config key is set."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument(
        "--config",
        default=None,
        help="Config file for the cutoff (default: <root>/.agent/config.yaml)",
    )
    return ap.parse_args()


def main() -> int:
    # Force UTF-8 stdout so the `→` / `—` in advisory messages survive a cp950
    # Windows console (child processes default to the console codepage). Both
    # validators and the pytest capture read this as UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    args = parse_args()
    root = Path(args.root).resolve()
    config_path = Path(args.config) if args.config else root / ".agent/config.yaml"
    archive_dir = root / ".agentcortex/context/archive"

    cutoff = _read_cutoff(config_path)
    if not cutoff:
        # Opt-in switch is off (absent/empty key) — silent no-op with a note.
        print("decision disposition: not configured — skipped")
        return 0

    if not archive_dir.is_dir():
        # Capability-by-presence: no archive to scan.
        return 0

    index_dates = _build_index_dates(archive_dir / "INDEX.jsonl")

    checked = 0
    findings: list[str] = []          # Signal A: logs with undisposed entries
    a2_entries = 0                    # Signal A2: suspicious `→ local` entries
    a2_files: list[str] = []          # logs containing them
    a2_ids: set[str] = set()          # the ADR ids those entries name

    for md_path in sorted(archive_dir.glob("*.md")):
        name = md_path.name
        if name == ".gitkeep.md" or name.startswith("ship-history-"):
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Unreadable log → skip (never crash the advisory scan).
            continue

        entries = parse_decision_entries(text.splitlines())
        if not entries:
            # No `## Decisions` section, or it has zero `### D-` entries →
            # nothing to disposition here.
            continue

        # Date-gate: INDEX `shipped` first, then the `-YYYYMMDD` filename suffix.
        log_date = index_dates.get(name) or _filename_date(name)
        if log_date is None:
            # Undatable log → conservatively out of scope (no false WARN).
            continue
        if log_date < cutoff:
            # Grandfathered: archived before the opt-in date.
            continue

        checked += 1
        if any(not entry_is_disposed(e) for e in entries):
            findings.append(name)

        # Signal A2 — independent of Signal A: an entry that IS disposed
        # `→ local` (after ASCII normalization) but names an ADR id in its
        # text is a likely rubber-stamp. For `→ local` entries ANY ADR-\d in
        # the block counts (a `→ promoted: ADR-x` marker only shields entries
        # that are not `→ local` — those never reach this scan).
        suspicious = 0
        for entry in entries:
            normalized = entry.replace("->", "→")
            if "→ local" not in normalized:
                continue
            ids = ADR_ID_RE.findall(normalized)
            if ids:
                suspicious += 1
                a2_ids.update(ids)
        if suspicious:
            a2_entries += suspicious
            a2_files.append(name)

    # At most one aggregated WARN line per signal (max 2 physical WARN lines).
    emitted = False
    if findings:
        files = ", ".join(sorted(findings))
        print(
            f"WARN: {len(findings)} archived log(s) shipped since {cutoff} have "
            f"undisposed ## Decisions entries: {files}. Disposition is a "
            "ship-time step (ship.md 2b) on the ACTIVE log; archived logs are "
            "immutable point-in-time records — do NOT edit them. If a listed "
            "decision still needs a durable home, add the ADR/L2 entry now (a "
            "new file/edit there, not a log edit). This WARN does NOT clear "
            "after that fix — the marker can never be added back to an "
            "archived log — so a persisting line is the accepted historical "
            "gap, never a reason to edit the archive."
        )
        emitted = True
    if a2_entries:
        noun = "entry" if a2_entries == 1 else "entries"
        ids = ", ".join(sorted(a2_ids))
        files = ", ".join(sorted(a2_files))
        print(
            f"WARN: {a2_entries} `→ local` {noun} in {len(a2_files)} log(s) "
            f"name an ADR ({ids}) — review whether → promoted/→ consolidated "
            f"applies: {files}"
        )
        emitted = True
    if not emitted:
        print(f"decision disposition OK ({checked} logs checked, cutoff {cutoff})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
