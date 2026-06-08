#!/usr/bin/env python3
"""Recover advisory Work Log lock files during bootstrap and phase entry."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from guard_context_write import pid_alive

DEFAULT_STALE_TIMEOUT_MINUTES = 60


@dataclass
class LockDecision:
    status: str
    reason: str
    exit_code: int = 0
    holder: dict[str, Any] | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _read_payload(lock: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not lock.exists():
        return None, "missing"
    try:
        payload = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "invalid-json"
    if not isinstance(payload, dict):
        return None, "invalid-json"
    return payload, None


def _timeout_minutes(payload: dict[str, Any], default: int) -> int:
    raw = payload.get("stale_timeout_minutes", default)
    try:
        timeout = int(raw)
    except (TypeError, ValueError):
        return default
    return max(timeout, 0)


def _pid_is_dead(payload: dict[str, Any]) -> bool:
    if "pid" not in payload or payload.get("pid") in (None, ""):
        return False
    try:
        pid = int(payload["pid"])
    except (TypeError, ValueError):
        return True
    return not pid_alive(pid)


def classify_lock(
    lock: Path,
    *,
    now: datetime | None = None,
    stale_timeout_minutes: int = DEFAULT_STALE_TIMEOUT_MINUTES,
) -> LockDecision:
    """Classify a Work Log advisory lock as missing, active, or recoverable."""
    payload, error = _read_payload(lock)
    if error == "missing":
        return LockDecision("missing", "missing")
    if error:
        return LockDecision("recoverable", error)
    assert payload is not None

    if _pid_is_dead(payload):
        return LockDecision("recoverable", "dead-pid", holder=payload)

    updated_at = _parse_datetime(payload.get("updated_at"))
    if updated_at is None:
        return LockDecision("recoverable", "missing-updated-at", holder=payload)

    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    timeout = _timeout_minutes(payload, stale_timeout_minutes)
    age_minutes = (current - updated_at).total_seconds() / 60
    if age_minutes >= timeout:
        return LockDecision("recoverable", "stale-time", holder=payload)

    return LockDecision("active", "active", exit_code=2, holder=payload)


def _lock_payload(
    *,
    owner: str,
    session: str,
    branch: str,
    phase: str,
    now: datetime,
    stale_timeout_minutes: int,
    pid: int | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "owner": owner,
        "session": session,
        "branch": branch,
        "phase": phase,
        "updated_at": now.isoformat(),
        "stale_timeout_minutes": stale_timeout_minutes,
    }
    if pid is not None:
        payload["pid"] = pid
    return payload


def _write_lock(lock: Path, payload: dict[str, Any]) -> None:
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_drift_log(worklog: Path, line: str) -> None:
    text = worklog.read_text(encoding="utf-8") if worklog.exists() else ""
    marker = "## Drift Log"
    if marker not in text:
        suffix = "\n\n" if text and not text.endswith("\n\n") else ""
        worklog.write_text(f"{text}{suffix}{marker}\n\n{line}\n", encoding="utf-8")
        return

    start = text.index(marker) + len(marker)
    section_start = text.find("\n", start)
    if section_start == -1:
        section_start = len(text)
    else:
        section_start += 1

    end_candidates = [idx for idx in (text.find("\n---", section_start), text.find("\n## ", section_start)) if idx != -1]
    section_end = min(end_candidates) if end_candidates else len(text)
    section = text[section_start:section_end]
    kept = [existing for existing in section.splitlines() if existing.strip() and existing.strip() != "none"]
    kept.append(line)
    replacement = "\n" + "\n".join(kept) + "\n"
    worklog.write_text(text[:section_start] + replacement + text[section_end:], encoding="utf-8")


def ensure_lock(
    lock: Path,
    *,
    owner: str,
    session: str,
    branch: str,
    phase: str,
    worklog: Path | None = None,
    now: datetime | None = None,
    stale_timeout_minutes: int = DEFAULT_STALE_TIMEOUT_MINUTES,
    owner_pid: int | None = None,
    include_pid: bool = False,
) -> LockDecision:
    current = now or _now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)

    decision = classify_lock(lock, now=current, stale_timeout_minutes=stale_timeout_minutes)
    payload = _lock_payload(
        owner=owner,
        session=session,
        branch=branch,
        phase=phase,
        now=current,
        stale_timeout_minutes=stale_timeout_minutes,
        pid=owner_pid if owner_pid is not None else os.getpid() if include_pid else None,
    )

    if decision.status == "missing":
        _write_lock(lock, payload)
        return LockDecision("created", "missing")

    holder = decision.holder or {}
    same_session = holder.get("owner") == owner and holder.get("session") == session
    if decision.status == "active" and not same_session:
        return decision

    _write_lock(lock, payload)
    status = "updated" if decision.status == "active" else "recovered"
    result = LockDecision(status, decision.reason, holder=holder or None)

    if status == "recovered" and worklog is not None:
        prior_owner = holder.get("owner", "unknown") if holder else "unknown"
        prior_session = holder.get("session", "unknown") if holder else "unknown"
        append_drift_log(
            worklog,
            "- Recovered stale Work Log lock "
            f"on {current.isoformat()}; prior_owner={prior_owner}; "
            f"prior_session={prior_session}; reason={decision.reason}; lock={lock.name}",
        )

    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    ensure = sub.add_parser("ensure", help="create, update, or recover a Work Log advisory lock")
    ensure.add_argument("--lock", required=True, type=Path)
    ensure.add_argument("--owner", required=True)
    ensure.add_argument("--session", required=True)
    ensure.add_argument("--branch", required=True)
    ensure.add_argument("--phase", required=True)
    ensure.add_argument("--worklog", type=Path)
    ensure.add_argument("--stale-timeout-minutes", type=int, default=DEFAULT_STALE_TIMEOUT_MINUTES)
    ensure.add_argument("--pid", type=int, help="owner process id; use only for a long-lived lock owner")
    ensure.add_argument("--no-pid", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "ensure":
        result = ensure_lock(
            args.lock,
            owner=args.owner,
            session=args.session,
            branch=args.branch,
            phase=args.phase,
            worklog=args.worklog,
            stale_timeout_minutes=args.stale_timeout_minutes,
            owner_pid=None if args.no_pid else args.pid,
        )
        print(json.dumps(asdict(result), sort_keys=True))
        return result.exit_code
    return 1


if __name__ == "__main__":
    sys.exit(main())
