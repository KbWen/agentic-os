#!/usr/bin/env python3
"""Stop hook: verify last assistant text ends with the Sentinel ⚡ ACX marker.

Closes the CC-2 honor-system gap (audit `docs/audit/governance-lifecycle-2026-04-25.md`
§0.1 + Lesson L4 in current_state.md §Global Lessons): without an external
observer, the agent can silently drop the Sentinel and there is no detection
or audit trail.

Contract:
  - Reads Claude Code Stop hook payload from stdin (JSON with `transcript_path`,
    `session_id`, `stop_hook_active`).
  - Tails the transcript JSONL, finds the last assistant message's text content.
  - If `⚡ ACX` is NOT present in the last ~200 characters, writes a violation
    receipt to `.agentcortex/context/sentinel-violations.jsonl` (append-only),
    prints a stderr warning (surfaced in Claude Code hook logs), and exits 1.
  - Otherwise exits 0.

Capability-by-presence: if Python is unavailable downstream, Claude Code logs
the missing command but does not block the session. Adopters opt in by keeping
`.claude/settings.json` registration; opt out by removing it.

This hook is intentionally minimal — it observes, it does not block. Blocking
would risk a denial-of-service against legitimate sessions if the sentinel
check has a bug. The receipt + stderr warning are sufficient for `validate.sh`
to surface violations on next run (see follow-up PR adding the validate.sh
integration).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

SENTINEL = "⚡ ACX"
SENTINEL_WINDOW = 200  # search the last N chars of the assistant text
RECEIPT = Path(".agentcortex/context/sentinel-violations.jsonl")


def read_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def last_assistant_text(transcript_path: Path) -> str:
    """Return the text content of the last assistant message in the transcript."""
    last_text = ""
    if not transcript_path.exists():
        return last_text
    try:
        with transcript_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                content = obj.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text.strip():
                            last_text = text
    except OSError:
        pass
    return last_text


def has_sentinel(text: str) -> bool:
    if not text:
        return False
    tail = text.rstrip()[-SENTINEL_WINDOW:]
    return SENTINEL in tail


def write_violation(payload: dict, last_text: str, receipt_path: Path | None = None) -> None:
    # Late-bind to module RECEIPT so test patches via hook.RECEIPT take effect.
    if receipt_path is None:
        receipt_path = RECEIPT
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": int(time.time()),
        "session_id": payload.get("session_id"),
        "violation": "missing_sentinel",
        "marker": SENTINEL,
        "tail": last_text.rstrip()[-SENTINEL_WINDOW:] if last_text else "",
        "stop_hook_active": payload.get("stop_hook_active", False),
    }
    line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    # O_APPEND for kernel-atomic line writes (matches guard_context_write append mode)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(str(receipt_path), flags, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def main() -> int:
    payload = read_payload()
    transcript_str = payload.get("transcript_path", "")
    if not transcript_str:
        return 0
    last_text = last_assistant_text(Path(transcript_str))
    if not last_text:
        # No assistant text yet — nothing to check.
        return 0
    if has_sentinel(last_text):
        return 0
    write_violation(payload, last_text)
    print(
        f"⚠️ Sentinel '{SENTINEL}' missing from last assistant message. "
        f"Logged to {RECEIPT}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
