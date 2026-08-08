#!/usr/bin/env python3
"""Advisory existence checker for Work Log `## External References` referents.

Verified gap (backlog #161; docs/reviews/2026-08-08-govern-audit-task-simulation.md
F7): `## External References` (templates/worklog.md §External References) appears
zero times in either validator, so a Work Log that cites a nonexistent spec path or
a nonexistent PR passes both validators untouched (probe P1a, 2026-08-08). The
needed primitive already exists for another SSoT field -- `validate.sh:2452-2453`
FAILs when the SSoT's Active-Backlog reference names a missing file -- this tool
applies the same existence check to the `## External References` table of every
ACTIVE Work Log.

For each `.agentcortex/context/work/*.md` log (dotfiles excluded -- both validators
already exclude the gitignored `.gitkeep.md` placeholder and any other dotfile from
this directory; see repo-gotchas #14 / backlog #149), this tool parses the
`## External References` table and WARNs when:

  * a `Spec` or `ADR` row's Path/URL cell names a repo-relative file that does not
    exist on disk (`—`/blank and `http(s)://` URLs are exempt -- no network call);
  * a `PR` or `Issue` row's Path/URL cell is present but looks like neither a URL,
    a `#NNN` GitHub-shorthand reference, nor the `—` placeholder (format-presence
    only -- this does NOT verify the referenced PR/issue actually exists; that
    would need a network call and is deliberately out of scope per the backlog row).

SHA header fields (Diff Base SHA / Checkpoint SHA) are already existence-checked
elsewhere as commits (`git rev-parse --verify`, validate.sh:1338) and are not
duplicated here.

ADVISORY-ONLY contract (mirrors check_ssot_caps.py / run_python_check /
Invoke-PythonCheck WARN-tier wiring, ADR-006): this tool ALWAYS exits 0. A missing
Work Log directory, zero active logs, or a log with no `## External References`
section are all silent no-ops (capability-by-presence) -- a genuine finding is
fixed by correcting the Work Log, not by this tool.

Exit codes:
  0  always (advisory -- never fails the validator). Findings, if any, are printed
     to stdout as `WARN: ...` lines.

Nested-advisory contract (external-review clarification): run_python_check /
Invoke-PythonCheck map tool exit codes 0->PASS and nonzero->FAIL only -- the seam
has NO WARN exit mapping (validate.sh:192-196), so findings from this tool appear
as indented `WARN:` lines under a `[PASS] ... advisory` wrapper line and do NOT
increment the summary's warn count. The counted-WARN lines in the summary all come
from grandfathered native `record_result WARN` sites (e.g. governance eval
coverage, validate.sh:~2853). Promoting seam-check findings into counted WARNs is
the WARN-taxonomy design decision tracked as backlog #103(d) -- deliberately not
decided unilaterally here.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXTERNAL_REFS_HEADER_RE = re.compile(r"^##\s+External References\b")
SECTION_BOUNDARY_RE = re.compile(r"^(##\s|---\s*$)")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEPARATOR_CELL_RE = re.compile(r"^[:\-\s]*$")
# Only an unambiguous OS-absolute syntax counts as absolute (see _resolve_candidate).
WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\\/]|^\\\\")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)
ISSUE_REF_RE = re.compile(r"#\d+")

PLACEHOLDER_VALUES = {"", "-", "--", "—"}
EXISTENCE_CHECKED_TYPES = {"spec", "adr"}
FORMAT_ONLY_TYPES = {"issue", "pr"}


def _split_row(line: str) -> list[str] | None:
    """Split one `| a | b | c |` markdown table line into stripped cells."""
    m = TABLE_ROW_RE.match(line.rstrip("\n"))
    if not m:
        return None
    return [cell.strip() for cell in m.group(1).split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(SEPARATOR_CELL_RE.match(c) for c in cells)


def find_external_references_rows(lines: list[str]) -> list[list[str]]:
    """Return data rows (as [Type, Path/URL, ...]) from the External References table.

    Header prefix-matched (`## External References...`) rather than exact-matched:
    this tool is the SOLE parser invoked by both validators (no sh/ps1 split to
    diverge, unlike the backlog #140 class of bug), but staying prefix-tolerant of
    a suffixed heading costs nothing.

    Fence-aware (external-review fix, backlog #156 decoy family): lines inside
    ``` / ~~~ fenced blocks are invisible — a fenced example containing the
    heading cannot open (or shadow) the section, and fenced example tables are
    never scanned as live rows. Fence markers toggle regardless of info string.
    """
    rows: list[list[str]] = []
    in_section = False
    in_fence = False
    header_row_seen = False
    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not in_section:
            if EXTERNAL_REFS_HEADER_RE.match(line):
                in_section = True
            continue
        if SECTION_BOUNDARY_RE.match(line):
            break
        cells = _split_row(line)
        if cells is None:
            continue
        if not header_row_seen and cells and cells[0].strip("*` ").lower() == "type":
            header_row_seen = True
            continue
        if _is_separator_row(cells):
            continue
        rows.append(cells)
    return rows


def _strip_wrapping(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == "`" and v[-1] == "`":
        v = v[1:-1].strip()
    return v


def _resolve_candidate(root: Path, path_cell: str) -> Path:
    """Resolve a Path/URL cell to a filesystem path, repo-relative by default.

    Deliberately NOT using Path.is_absolute() to decide: it is platform-dependent
    (a leading `/` is absolute on POSIX but drive-relative on Windows), which would
    make the same Work Log cell resolve differently in a Windows-local run vs Linux
    CI -- the [cross-platform-eol]-class of bug this repo treats as HIGH severity.
    Only an unambiguous OS-absolute syntax (Windows drive letter or UNC prefix) is
    treated as absolute; everything else, including a leading slash, is repo-root
    relative.
    """
    if WINDOWS_ABS_RE.match(path_cell):
        return Path(path_cell)
    return root / path_cell.lstrip("/\\")


def check_log(path: Path, root: Path) -> tuple[list[str], int]:
    """Return (WARN findings, row_count) for one Work Log's External References."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ([f"WARN: {path.name} -- could not read External References ({exc})"], 0)

    rows = find_external_references_rows(text.splitlines())
    findings: list[str] = []
    for cells in rows:
        if not cells:
            continue
        ref_type_raw = cells[0].strip()
        ref_type = ref_type_raw.strip("*` ").lower()
        path_cell = _strip_wrapping(cells[1]) if len(cells) > 1 else ""

        if ref_type in EXISTENCE_CHECKED_TYPES:
            if path_cell in PLACEHOLDER_VALUES or URL_RE.match(path_cell):
                continue
            candidate = _resolve_candidate(root, path_cell)
            if not candidate.is_file():
                findings.append(
                    f"WARN: {path.name} -- External References: {ref_type_raw} path "
                    f"'{path_cell}' does not exist"
                )
        elif ref_type in FORMAT_ONLY_TYPES:
            if path_cell in PLACEHOLDER_VALUES:
                continue
            if URL_RE.match(path_cell) or ISSUE_REF_RE.search(path_cell):
                continue
            findings.append(
                f"WARN: {path.name} -- External References: {ref_type_raw} reference "
                f"'{path_cell}' is not a URL, #NNN reference, or `—` placeholder "
                f"(format check only -- referenced-item existence is not verified, "
                f"no network call)"
            )
        # Unknown ref types (future template rows) are ignored -- forward compatible.
    return (findings, len(rows))


def iter_active_worklogs(worklog_dir: Path):
    if not worklog_dir.is_dir():
        return
    for p in sorted(worklog_dir.glob("*.md")):
        # Dotfile exclusion parity with both validators (bash `*.md` glob does not
        # match a leading dot; validate.ps1:1114 filters `-notlike '.*'`). Python's
        # pathlib.glob does NOT exclude dotfiles by default -- explicit filter is
        # required (confirmed the hard way per the backlog #149 ship record: "the
        # test's first draft failed on exactly that").
        if p.name.startswith("."):
            continue
        if p.is_file():
            yield p


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory existence checker for Work Log `## External References` rows. "
            "Always exits 0; prints WARN lines for Spec/ADR referents that do not "
            "exist and malformed PR/Issue reference formats."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument(
        "--worklog-dir",
        default=None,
        help="Work Log directory to scan (default: <root>/.agentcortex/context/work)",
    )
    return ap.parse_args()


def main() -> int:
    # Force UTF-8 stdout so `—`/`§` survive a cp950 Windows console (mirrors
    # check_ssot_caps.py / check_decision_disposition.py).
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    args = parse_args()
    root = Path(args.root).resolve()
    worklog_dir = (
        Path(args.worklog_dir) if args.worklog_dir else root / ".agentcortex/context/work"
    )

    logs = list(iter_active_worklogs(worklog_dir))
    if not logs:
        return 0  # capability-by-presence: no active logs to check

    all_findings: list[str] = []
    total_rows = 0
    for log in logs:
        findings, row_count = check_log(log, root)
        all_findings.extend(findings)
        total_rows += row_count

    if all_findings:
        for f in all_findings:
            print(f)
    else:
        print(
            f"worklog external references OK -- {len(logs)} log(s), "
            f"{total_rows} row(s) checked."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
