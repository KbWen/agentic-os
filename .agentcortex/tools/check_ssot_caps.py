#!/usr/bin/env python3
"""Advisory cap checker for current_state.md SSoT sections (ADR-006).

Counts the two capped, unbounded-growth sections of the SSoT and, when a
count exceeds its configured cap, prints a WARN-style advisory naming the
rotation procedure:

  * `## Ship History`   — `### Ship-` entries; cap
    `document_lifecycle.ship_history_max_entries` (default 10). Rotate the
    oldest to `.agentcortex/context/archive/ship-history-YYYY.md`
    (ship.md §State Update).
  * `**Spec Index**`    — indented child entries; cap
    `document_lifecycle.spec_index_max_entries` (default 30). Collapse the
    oldest shipped entries into a `## Spec Index Archive` section
    (ship.md:197).

ADVISORY-ONLY contract (mirrors the run_python_check / Invoke-PythonCheck
WARN-tier wiring used by the downstream-capabilities and safety-nucleus
checks): this tool ALWAYS exits 0 so the validator never FAILs on an
over-cap count. The finding is surfaced in the validator's indented output;
a genuine over-cap state is fixed by the documented rotation, not by the
validator. Capability-by-presence: a missing SSoT file exits 0 silently.

Exit codes:
  0  always (advisory — never fails the validator). Findings, if any, are
     printed to stdout as `WARN: ...` lines.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Defaults mirror .agent/config.yaml §document_lifecycle. Used when the config
# file or key is absent (downstream / zero-config) so the tool degrades safely.
DEFAULT_SHIP_HISTORY_CAP = 10
DEFAULT_SPEC_INDEX_CAP = 30

SHIP_HISTORY_HEADER = "## Ship History"
SHIP_ENTRY_RE = re.compile(r"^### Ship-")
SPEC_INDEX_PARENT_RE = re.compile(r"^- \*\*Spec Index\*\*")
INDENTED_BULLET_RE = re.compile(r"^\s+- ")
TOP_LEVEL_BULLET_RE = re.compile(r"^- ")


def _read_caps(config_path: Path) -> tuple[int, int]:
    """Read the two caps from .agent/config.yaml with safe defaults."""
    ship_cap = DEFAULT_SHIP_HISTORY_CAP
    spec_cap = DEFAULT_SPEC_INDEX_CAP
    if not config_path.is_file():
        return ship_cap, spec_cap
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from _yaml_loader import load_data  # type: ignore  # noqa: E402

        data = load_data(config_path)
        lifecycle = data.get("document_lifecycle") or {}
        ship_cap = int(lifecycle.get("ship_history_max_entries", ship_cap))
        spec_cap = int(lifecycle.get("spec_index_max_entries", spec_cap))
    except Exception:
        # Any parse/import failure → keep defaults (advisory tool, never fail).
        return DEFAULT_SHIP_HISTORY_CAP, DEFAULT_SPEC_INDEX_CAP
    return ship_cap, spec_cap


def count_ship_history(lines: list[str]) -> int:
    """Count `### Ship-` entries inside the `## Ship History` section."""
    in_section = False
    count = 0
    for line in lines:
        stripped = line.rstrip("\n")
        if stripped.strip() == SHIP_HISTORY_HEADER:
            in_section = True
            continue
        if in_section:
            # A new `## ` section (other than Ship History itself) ends the scan.
            if stripped.startswith("## ") and stripped.strip() != SHIP_HISTORY_HEADER:
                break
            if SHIP_ENTRY_RE.match(stripped):
                count += 1
    return count


def count_spec_index(lines: list[str]) -> int:
    """Count indented child entries under the `- **Spec Index**` parent bullet."""
    in_section = False
    count = 0
    for line in lines:
        stripped = line.rstrip("\n")
        if SPEC_INDEX_PARENT_RE.match(stripped):
            in_section = True
            continue
        if in_section:
            if INDENTED_BULLET_RE.match(stripped):
                count += 1
            elif stripped.strip() == "":
                # tolerate incidental blank lines inside the block
                continue
            else:
                # next top-level bullet (e.g. `- **Canonical Commands**`) or a
                # header (`## Spec Index Archive`) ends the live index.
                break
    return count


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Advisory cap checker for current_state.md Ship History + Spec Index. "
            "Always exits 0; prints WARN lines when a section exceeds its config cap."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument(
        "--path",
        default=None,
        help="SSoT file to inspect (default: <root>/.agentcortex/context/current_state.md)",
    )
    ap.add_argument(
        "--config",
        default=None,
        help="Config file for caps (default: <root>/.agent/config.yaml)",
    )
    return ap.parse_args()


def main() -> int:
    # Force UTF-8 stdout so the `§` / `—` in advisory messages survive a cp950
    # Windows console (child processes default to the console codepage). Both
    # validators and the pytest capture read this as UTF-8.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    args = parse_args()
    root = Path(args.root).resolve()
    ssot_path = Path(args.path) if args.path else root / ".agentcortex/context/current_state.md"
    config_path = Path(args.config) if args.config else root / ".agent/config.yaml"

    if not ssot_path.is_file():
        # Capability-by-presence: no SSoT to check.
        return 0

    ship_cap, spec_cap = _read_caps(config_path)

    try:
        text = ssot_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"WARN: could not read {ssot_path}: {exc}")
        return 0

    lines = text.splitlines()
    ship_count = count_ship_history(lines)
    spec_count = count_spec_index(lines)

    findings = []
    if ship_count > ship_cap:
        findings.append(
            f"WARN: Ship History has {ship_count} entries (cap {ship_cap}); "
            f"rotate the oldest {ship_count - ship_cap} to "
            f".agentcortex/context/archive/ship-history-YYYY.md per "
            f"ship.md §State Update (Ship History rotation)."
        )
    if spec_count > spec_cap:
        findings.append(
            f"WARN: Spec Index has {spec_count} entries (cap {spec_cap}); "
            f"collapse the oldest shipped entries into a `## Spec Index Archive` "
            f"section per ship.md:197."
        )

    if findings:
        for f in findings:
            print(f)
    else:
        print(
            f"ssot caps OK — ship history {ship_count}/{ship_cap}, "
            f"spec index {spec_count}/{spec_cap}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
