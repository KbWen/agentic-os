#!/usr/bin/env python3
"""Advisory growth checker for the archive directory (ADR-006, issue #141).

Counts the top-level `*.md` bodies in `.agentcortex/context/archive/` and, when
the count exceeds its configured cap, prints a WARN-style advisory naming the
rotation/GC procedure. The archive accumulates one file per ship/handoff with no
rotation; unbounded growth silently inflates the read cost of every
archive-scanning check (audit chain, decision-disposition, Phase-Summary audit).

Only top-level `*.md` bodies are counted. `INDEX.jsonl` is the append-only,
hash-chained audit witness — compacting it would break tamper-evidence — so it
is deliberately excluded; body rotation/compaction itself is deferred to the
lifecycle engine (#140). This tool is only the cheap early-signal half.

ADVISORY-ONLY contract (mirrors the run_python_check / Invoke-PythonCheck
WARN-tier wiring used by check_ssot_caps.py): this tool ALWAYS exits 0 so the
validator never FAILs on an over-cap count. The finding is surfaced in the
validator's indented output; a genuine over-cap state is fixed by the documented
rotation, not by the validator. Capability-by-presence: a missing archive
directory exits 0 silently.

Exit codes:
  0  always (advisory — never fails the validator). Findings, if any, are
     printed to stdout as `WARN: ...` lines.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Default mirrors .agent/config.yaml §document_lifecycle.archive_max_files. Used
# when the config file or key is absent (downstream / zero-config) so the tool
# degrades safely.
DEFAULT_ARCHIVE_MAX_FILES = 50


def _read_cap(config_path: Path) -> int:
    """Read archive_max_files from .agent/config.yaml with a safe default."""
    cap = DEFAULT_ARCHIVE_MAX_FILES
    if not config_path.is_file():
        return cap
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _yaml_loader import load_data  # type: ignore  # noqa: E402

        data = load_data(config_path)
        lifecycle = data.get("document_lifecycle") or {}
        cap = int(lifecycle.get("archive_max_files", cap))
    except Exception:
        # Any parse/import failure → keep default (advisory tool, never fail).
        return DEFAULT_ARCHIVE_MAX_FILES
    return cap


def count_archive_md(archive_dir: Path) -> int:
    """Count top-level `*.md` files directly under the archive directory.

    Non-recursive by design: subdirectories (e.g. `archive/work/`) are separate
    surfaces, and this mirrors the count the issue evidence was gathered with.
    """
    return sum(
        1 for p in archive_dir.iterdir() if p.is_file() and p.suffix == ".md"
    )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory growth checker for .agentcortex/context/archive/. Always "
            "exits 0; prints a WARN line when the top-level *.md count exceeds "
            "the config cap."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument(
        "--path",
        default=None,
        help="Archive directory to inspect (default: <root>/.agentcortex/context/archive)",
    )
    ap.add_argument(
        "--config",
        default=None,
        help="Config file for the cap (default: <root>/.agent/config.yaml)",
    )
    return ap.parse_args()


def main() -> int:
    # Force UTF-8 stdout so the em-dash in advisory messages survives a cp950
    # Windows console (child processes default to the console codepage). Both
    # validators and the pytest capture read this as UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    args = parse_args()
    root = Path(args.root).resolve()
    archive_dir = (
        Path(args.path) if args.path else root / ".agentcortex/context/archive"
    )
    config_path = Path(args.config) if args.config else root / ".agent/config.yaml"

    if not archive_dir.is_dir():
        # Capability-by-presence: no archive to check.
        return 0

    cap = _read_cap(config_path)

    try:
        count = count_archive_md(archive_dir)
    except OSError as exc:
        print(f"WARN: could not scan {archive_dir}: {exc}")
        return 0

    if count > cap:
        print(
            f"WARN: archive directory has {count} top-level *.md files (cap {cap}); "
            f"rotate/GC the oldest {count - cap} into a yearly summary index "
            f"(rotation/GC pending #141; INDEX.jsonl is append-only and excluded)."
        )
    else:
        print(f"archive growth OK — {count}/{cap} top-level *.md files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
