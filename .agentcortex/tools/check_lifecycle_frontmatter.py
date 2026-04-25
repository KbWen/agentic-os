#!/usr/bin/env python3
"""ADR-002 D2.3 — Lifecycle frontmatter checker for governance docs.

Spec: docs/specs/lock-unification.md AC-15..AC-20
ADR:  docs/adr/ADR-002-guarded-governance-writes.md §D3

Scans governance docs and verifies they declare the `lifecycle:` frontmatter
contract: {owner, review_cadence, review_trigger, supersedes, superseded_by}.

Grandfather rule: files dated before 2026-04-25 (the ADR's date) emit WARN
on missing fields. Files dated 2026-04-25+ emit FAIL.

Exit codes:
  0  no FAIL findings (PASS or WARN only)
  1  one or more FAIL findings
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, NamedTuple

# Reuse the framework YAML loader for frontmatter parsing
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _yaml_loader import load_data  # noqa: E402


CUTOFF_DATE = date(2026, 4, 25)
REQUIRED_FIELDS = ("owner", "review_cadence", "review_trigger", "supersedes", "superseded_by")
VALID_CADENCES = {"quarterly", "biannual", "annual", "on-event"}

# AC-15 — scan target globs (POSIX style; matched after relative-to-root)
TARGET_PATTERNS = (
    re.compile(r"^docs/audit/[^/]+\.md$"),
    re.compile(r"^docs/guides/governance-[^/]+\.md$"),
    re.compile(r"^docs/adr/[^/]+\.md$"),
    re.compile(r"^docs/architecture/[^/]+\.md$"),  # excludes .log.md below
)
EXCLUDE_RE = re.compile(r"\.log\.md$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
DATE_FIELD_RE = re.compile(r"^(?:date|created|frozen_date)\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", re.MULTILINE)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _is_target(rel_posix: str) -> bool:
    if EXCLUDE_RE.search(rel_posix):
        return False
    # Skip dotfiles like .gitkeep.md
    name = rel_posix.rsplit("/", 1)[-1]
    if name.startswith("."):
        return False
    return any(p.match(rel_posix) for p in TARGET_PATTERNS)


def parse_frontmatter(path: Path) -> tuple[str | None, dict | None]:
    """Return (raw_frontmatter_text, parsed_dict). Either may be None."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, None
    raw = m.group(1)
    # Build a temporary file-like for the YAML loader (.yaml extension required)
    tmp = Path(str(path) + ".__fm_probe__.yaml")
    try:
        # Write the frontmatter as a standalone YAML doc and parse via loader.
        # We avoid touching the source file; this just reuses the parser.
        tmp.write_text(raw, encoding="utf-8")
        try:
            data = load_data(tmp)
        except Exception:
            data = None
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return raw, data if isinstance(data, dict) else None


def extract_doc_date(path: Path, fm_text: str | None) -> date | None:
    """AC-18: prefer frontmatter date/created/frozen_date; fallback to git first commit."""
    if fm_text:
        m = DATE_FIELD_RE.search(fm_text)
        if m:
            try:
                return date.fromisoformat(m.group(1))
            except ValueError:
                pass
    # Fallback: git log first (oldest) commit date for this file
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%ad", "--date=short", "--", str(path)],
            cwd=path.parent,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        first = result.stdout.splitlines()[0].strip() if result.stdout else ""
        if first:
            return date.fromisoformat(first)
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError, ValueError):
        pass
    return None


def validate_lifecycle(fm: dict | None) -> list[str]:
    """Return a list of issues; empty list means valid."""
    if fm is None:
        return ["frontmatter missing or unparseable"]
    lc = fm.get("lifecycle")
    if not isinstance(lc, dict):
        return ["lifecycle: block missing"]
    issues: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in lc:
            issues.append(f"lifecycle.{field} missing")
    cadence = lc.get("review_cadence")
    if isinstance(cadence, str) and cadence not in VALID_CADENCES:
        issues.append(
            f"lifecycle.review_cadence='{cadence}' not in {sorted(VALID_CADENCES)}"
        )
    return issues


# --------------------------------------------------------------------------- #
# Scanner
# --------------------------------------------------------------------------- #


class Finding(NamedTuple):
    severity: str  # FAIL | WARN | PASS
    file: str
    detail: str


def list_target_files(root: Path) -> Iterable[Path]:
    """Yield governance docs in scope per AC-15."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        candidates = [root / line.strip() for line in result.stdout.splitlines() if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        candidates = list(root.rglob("*.md"))

    for path in candidates:
        try:
            rel = str(path.resolve().relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if _is_target(rel):
            yield path


def check_file(path: Path, rel_posix: str) -> Finding:
    raw, fm = parse_frontmatter(path)
    issues = validate_lifecycle(fm)
    if not issues:
        return Finding("PASS", rel_posix, "lifecycle frontmatter valid")
    doc_date = extract_doc_date(path, raw)
    grandfathered = doc_date is not None and doc_date < CUTOFF_DATE
    severity = "WARN" if grandfathered else "FAIL"
    detail = "; ".join(issues)
    if grandfathered:
        detail = f"grandfathered ({doc_date.isoformat()}): {detail}"
    return Finding(severity, rel_posix, detail)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Validate that governance docs (audit/, guides/governance-*, adr/, architecture/*.md L1) "
            "declare the lifecycle: frontmatter contract per ADR-002 D3. "
            "Files dated before 2026-04-25 are grandfathered (WARN); newer files FAIL on missing fields."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    findings: list[Finding] = []
    for path in list_target_files(root):
        try:
            rel = str(path.resolve().relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        findings.append(check_file(path, rel))

    fail_count = sum(1 for f in findings if f.severity == "FAIL")
    warn_count = sum(1 for f in findings if f.severity == "WARN")
    pass_count = sum(1 for f in findings if f.severity == "PASS")

    if args.json:
        payload = {
            "fail_count": fail_count,
            "warn_count": warn_count,
            "pass_count": pass_count,
            "findings": [f._asdict() for f in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for f in findings:
            if f.severity != "PASS":
                print(f"  [{f.severity}] {f.file} — {f.detail}", file=sys.stderr)
        print(
            f"lifecycle frontmatter: {pass_count} PASS, {warn_count} WARN, {fail_count} FAIL"
        )

    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
