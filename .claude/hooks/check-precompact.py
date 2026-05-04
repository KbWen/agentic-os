#!/usr/bin/env python3
"""PreCompact hook: refuse compaction when the active Work Log has not flushed
its Phase Summary for the current phase.

Closes the partial gap from CC-2 / Lesson L4: compaction can silently drop
in-flight reasoning if the agent has not yet written `## Phase Summary` for
the current phase, defeating downstream `validate.sh` audits.

Contract:
  - Reads Claude Code PreCompact payload from stdin (JSON; field names follow
    Claude Code 2026-w16 PreCompact contract: `transcript_path`, optional
    `cwd`).
  - Identifies active Work Log under `.agentcortex/context/work/` whose Header
    `Branch` matches the current git branch (filesystem-safe normalized).
  - Loads the Work Log:
      * If file is absent OR `## Phase Summary` is empty/missing OR the latest
        line in `## Phase Summary` does not contain the value of `Current
        Phase` from Header → write a violation receipt to
        `.agentcortex/context/precompact-violations.jsonl` and emit a stderr
        warning. Exit per CONFIG.

  - Default mode: WARN (exit 0). Block mode is opt-in via env var
    `AGENTIC_OS_PRECOMPACT_BLOCK=1` — exits 2 (Claude Code's "block" code
    per 2026-w16 PreCompact contract).

Capability-by-presence: if the work log path is absent (e.g., tiny-fix tasks),
the hook is silent. Adopters opt in by keeping `.claude/settings.json`
registration; opt out by removing it.

This hook never edits files. It only reads existing Work Logs and writes
append-only receipts.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

WORKLOG_DIR = Path(".agentcortex/context/work")
RECEIPT = Path(".agentcortex/context/precompact-violations.jsonl")
PHASE_SUMMARY_HEADER_RE = re.compile(r"^## Phase Summary\s*$", re.MULTILINE)
NEXT_H2_RE = re.compile(r"^## ", re.MULTILINE)


def read_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def current_branch() -> str:
    try:
        out = subprocess.run(
            ["git", "branch", "--show-current"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def worklog_key(branch: str) -> str:
    """Filesystem-safe normalization: same rule as validate.sh."""
    return branch.replace("/", "-")


def find_worklog(branch: str) -> Path | None:
    if not branch:
        return None
    key = worklog_key(branch)
    candidate = WORKLOG_DIR / f"{key}.md"
    if candidate.exists():
        return candidate
    # Also accept owner-prefixed form: <owner>-<key>.md
    for path in WORKLOG_DIR.glob(f"*-{key}.md"):
        return path
    return None


def parse_header_field(content: str, field: str) -> str:
    """Match list form `- Field: value` OR ``- `Field`: value``."""
    pattern = rf"^- (?:`{re.escape(field)}`|{re.escape(field)}):\s*`?([^\n`]+)`?"
    m = re.search(pattern, content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    # Table form: `| Field | value |`
    pattern2 = rf"^\|\s*(?:`{re.escape(field)}`|{re.escape(field)})\s*\|\s*`?([^\n|`]+)`?\s*\|"
    m = re.search(pattern2, content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def phase_summary_section(content: str) -> str:
    """Extract the body of `## Phase Summary` up to the next `## ` header."""
    head = PHASE_SUMMARY_HEADER_RE.search(content)
    if not head:
        return ""
    start = head.end()
    rest = content[start:]
    next_h = NEXT_H2_RE.search(rest)
    return rest[: next_h.start()] if next_h else rest


def write_receipt(record: dict, receipt_path: Path | None = None) -> None:
    if receipt_path is None:
        receipt_path = RECEIPT
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(str(receipt_path), flags, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def evaluate(content: str) -> tuple[bool, str]:
    """Return (ok, reason). ok=True means compaction may proceed."""
    current_phase = parse_header_field(content, "Current Phase")
    if not current_phase or current_phase.lower() == "none":
        return True, "no current phase set — pre-bootstrap state"
    body = phase_summary_section(content).strip()
    if not body or body == "none":
        return False, f"Phase Summary empty while Current Phase={current_phase}"
    # Heuristic: latest summary line should mention the current phase.
    # Match "current_phase" prefix (case-insensitive) on any non-empty bullet.
    pattern = re.compile(rf"(?im)^[\s\-*]*{re.escape(current_phase)}[:\s]")
    if not pattern.search(body):
        return False, f"Phase Summary does not mention Current Phase={current_phase}"
    return True, "ok"


def block_mode() -> bool:
    return os.environ.get("AGENTIC_OS_PRECOMPACT_BLOCK", "0") == "1"


def main() -> int:
    payload = read_payload()
    branch = current_branch()
    wl = find_worklog(branch)
    if wl is None:
        # No active Work Log — likely tiny-fix or no task; do not block compaction.
        return 0
    try:
        content = wl.read_text(encoding="utf-8")
    except OSError as exc:
        write_receipt(
            {
                "timestamp": int(time.time()),
                "session_id": payload.get("session_id"),
                "violation": "could_not_read_worklog",
                "worklog": str(wl),
                "reason": str(exc),
            }
        )
        return 0
    ok, reason = evaluate(content)
    if ok:
        return 0
    write_receipt(
        {
            "timestamp": int(time.time()),
            "session_id": payload.get("session_id"),
            "violation": "stale_phase_summary",
            "worklog": str(wl),
            "reason": reason,
        }
    )
    print(
        f"⚠️ PreCompact: {reason} ({wl}). Flush Work Log Phase Summary before "
        f"compaction or set AGENTIC_OS_PRECOMPACT_BLOCK=0 to override.",
        file=sys.stderr,
    )
    return 2 if block_mode() else 0


if __name__ == "__main__":
    raise SystemExit(main())
