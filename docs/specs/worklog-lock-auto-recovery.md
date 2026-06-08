---
status: shipped
title: Work Log Lock Auto-Recovery
source: GitHub issue #188
created: 2026-06-08
primary_domain: governance
secondary_domains: [workflow]
---

# Work Log Lock Auto-Recovery

## Goal

Make bootstrap able to recover stale, dead-PID, or corrupted advisory Work Log lock files without requiring manual deletion, while preserving the non-blocking advisory nature of Work Log locks.

## Acceptance Criteria

- AC-1: `.agentcortex/tools/recover_worklog_lock.py` can classify a Work Log lock as `missing`, `active`, or `recoverable` using `updated_at`, `stale_timeout_minutes`, and an optional `pid`.
- AC-2: `.agentcortex/tools/recover_worklog_lock.py ensure` overwrites missing or recoverable lock files with the current owner/session/branch/phase payload.
- AC-3: When a recoverable lock is replaced and `--worklog` is provided, the tool appends one concise recovery record to the Work Log `## Drift Log`.
- AC-4: A non-stale lock owned by another live session is not overwritten; the tool exits with a distinct non-zero code and reports the holder details.
- AC-5: `.agent/workflows/bootstrap.md` instructs agents to use the helper during §2a Advisory Work Log Lock, with a direct-write fallback when Python is unavailable.
- AC-6: `tests/guard/test_worklog_lock_recovery.py` covers missing-lock creation, stale-time recovery, dead-PID recovery, corrupted-lock recovery, active-lock preservation, and bootstrap wiring.

## Non-goals

- Do not promote advisory Work Log locks to hard blocking locks.
- Do not change `guard_context_write.py` hard-lock semantics.
- Do not add a third-party dependency such as `psutil`.
- Do not delete unrelated stale locks outside the active branch's lock file.

## Constraints

- The helper must be stdlib-only.
- Recovery evidence must be terse to avoid Work Log bloat.
- Live but expired advisory locks may be recovered because Work Log locks are advisory and already age-based in `bootstrap.md`.
- The behavior must remain cross-platform by reusing the existing `guard_context_write.pid_alive` implementation.

## File Relationship

This feature extends bootstrap's advisory lock workflow. It complements existing validator stale-lock warnings but does not replace validation or guarded SSoT hard locks.

## Domain Decisions

- [DECISION] Keep Work Log locks advisory: active locks warn/exit distinctly, but workflows still decide whether to proceed.
- [DECISION] Reuse `guard_context_write.pid_alive` so Windows liveness behavior stays consistent with ADR-002 hard locks.
- [CONSTRAINT] Recovery writes only the active lock path and optionally appends one Drift Log line to the active Work Log.
