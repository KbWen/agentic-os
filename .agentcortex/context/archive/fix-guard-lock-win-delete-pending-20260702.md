---
template: false
description: Work Log for the guard file_lock Windows delete-pending PermissionError fix.
---

# Work Log: fix/guard-lock-win-delete-pending

## Header

- Branch: `fix/guard-lock-win-delete-pending`
- Classification: `quick-win`
- Classified by: `claude-fable-5`
- Frozen: `false`
- Created Date: `2026-07-02`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `be78c6a`
- Checkpoint SHA: `be78c6a`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-runtime`
- SSoT Sequence: `106`

---

## Session Info

- Agent: `claude-fable-5`
- Session: `2026-07-02 07:50 UTC`
- Platform: `claude-code`
- Files Read: `44`

---

## Task Description

PR #311's Windows CI shard failed twice on `test_d2_1_guard_race` with `PermissionError: [Errno 13]` from `guard_context_write.py file_lock` — a pre-existing bug on main (the PR touches no guard code; local Windows passes; the 2-core hosted runner widens the window). Root cause: on Windows, `os.open(O_CREAT|O_EXCL)` on a lock file in the delete-pending state (previous holder mid-`unlink`, or AV/indexer briefly holding it) raises `PermissionError`, not `FileExistsError` — and the retry loop caught only `FileExistsError`, so the acquirer crashed instead of retrying. The unlink side already documents the sibling WinError 32 quirk; the open side was missed.

Fix: add a `PermissionError` arm to the retry loop — treat as lock-busy with the same backoff; if it persists past the deadline, re-raise the ORIGINAL `PermissionError` (genuine ACL misconfiguration stays diagnosable, unlike the busy-timeout RuntimeError). Cross-platform (no platform gate) → deterministically testable.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-02T07:50Z | quick-win; root-cause from CI logs read twice |
| plan | done | 2026-07-02T07:52Z | 1 except-arm + 2 deterministic tests |
| implement | done | 2026-07-02T08:00Z | fix + tests green locally |
| ship | done | 2026-07-02T08:20Z | merged; archived |

---

## Phase Summary

**bootstrap/plan/implement** (2026-07-02): Root cause established from two identical CI failures (same test, same errno, delete-pending signature) + code read confirming the single-exception retry loop. Fix is one `except PermissionError` arm (busy-backoff; deadline → re-raise original). Two deterministic regression tests added to `test_d2_1_guard_race.py`: injected one-shot PermissionError must be retried through to acquisition; persistent PermissionError must re-raise the original after the deadline. Confidence: 93% — high.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T07:50Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T07:52Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T08:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T08:20Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| PR | https://github.com/KbWen/agentic-os/pull/311 | the CI failures that exposed this (unrelated feature) |
| CI | runs/28572936404 Pytest (Windows) (2) | two identical failures |

---

## Known Risk

- Root Cause: Windows delete-pending `os.open` → `PermissionError` not handled by the lock retry loop (only `FileExistsError` was).
- Behavior change bound: a genuine ACL error now surfaces after `max_wait_seconds` (as the original PermissionError) instead of instantly — bounded and diagnosable. Rollback = revert commit.

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Review Feedback

none

---

## Red Team Findings

none

---

## Drift Log

none

---

## Evidence

- `pytest tests/guard/test_d2_1_guard_race.py -q` → 4 passed (2 original race tests + 2 new deterministic PermissionError tests; the retried-branch assertion proves the new arm executed).
- `pytest tests/guard/ -m "not slow"` → 274 passed.
- CI logs (two runs): identical `PermissionError ... race.jsonl.guard.lock` at `guard_context_write.py:354` — signature matches delete-pending, not ACL.
