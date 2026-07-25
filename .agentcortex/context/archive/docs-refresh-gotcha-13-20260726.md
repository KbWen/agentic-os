# Work Log: docs/refresh-gotcha-13

## Header

- Branch: `docs/refresh-gotcha-13`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-07-26`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `9827a77750c97ac595d6d11768d1d09618e65f0b`
- Checkpoint SHA: `9827a77750c97ac595d6d11768d1d09618e65f0b`
- Recommended Skills: `verification-before-completion (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `133`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-07-26 (claude-code 2.1.160)`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

Self-cleanup. PR #365 fixed the defect that repo-gotchas #13 describes, which left that entry
asserting a live failure that no longer exists ("six tests fail on clean main", "tracked as
backlog #146" — a closed item). A gotchas file whose entries point at fixed problems is worse
than one entry shorter: it sends the next reader hunting for nothing.

Rewritten to keep the diagnostic signature and the clean-worktree isolation technique, drop
the stale present-tense claim and the closed-backlog pointer, and say plainly that the Python
half is now ratcheted.

Classification is `quick-win`, not `tiny-fix`: `.agent/rules/*` is tiny-fix-excluded
(`bootstrap.md §0`, `state_machine.md` Governance File Escalation).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-26 | governance-file exclusion -> quick-win |
| plan | done | 2026-07-26 | single-entry rewrite; keep signature, drop stale claim |
| implement | done | 2026-07-26 | 1 file, 26 lines changed |
| review | skipped | — | optional for quick-win |
| test | skipped | — | optional for quick-win |
| handoff | skipped | — | exempt (quick-win) |
| ship | done | 2026-07-26 | fast-path IMPLEMENTING -> SHIPPED |

---

## Phase Summary

- bootstrap: `quick-win` — a `.agent/rules/*` edit cannot be `tiny-fix`.
- plan: rewrite entry #13 in place rather than delete it. The failure signature and the
  local-red/CI-green isolation technique keep their value after the fix; only the
  present-tense "six tests fail" claim and the closed-backlog pointer went stale.
  | Confidence: 95% — high.
- ship: PASS on the quick-win fast-path. Constraints re-verified, both gotchas-related guard
  suites green, `validate.ps1` fail=0.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T02:30:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T02:32:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T02:35:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T02:40:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| PR | https://github.com/KbWen/agentic-os/pull/364 | shipped the gotchas file + entry #13 |
| PR | https://github.com/KbWen/agentic-os/pull/365 | fixed the defect #13 described, making it stale |

---

## Known Risk

- R1 — deleting the entry outright was the DELETE-bias option and was rejected: the failure
  signature still applies wherever the AST ratchet does not reach (shell scripts, file reads,
  new dependencies), and the clean-worktree isolation technique is independent of this
  particular bug. Kept short instead of deleted.
- Rollback: revert the PR. Single doc file, no behaviour anywhere.

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Self-inflicted staleness: entry #13 was authored in PR #364 and invalidated by PR #365, both
  in the same session. Cleaning it is in scope for the session that caused it, not a candidate
  for a spawned follow-up.

---

## Review Feedback

none

---

## Red Team Findings

none

---

## Design Reference

none

---

## Observability

none

---

## Resume

none

---

## Test Gate Results

none

---

## Evidence

- File constraints after the rewrite: **127 lines** (cap 150), **0** hard-directive keywords
  (case-sensitive), **0** `.agentcortex/tools/*.py` references — the same three invariants the
  file shipped under.
- Both gotchas-related guard suites green: `test_repo_gotchas_discoverability.py` +
  `test_subprocess_encoding.py` -> **11 passed**.
- Diff: 1 source file, 18 insertions / 13 deletions.
- `validate.ps1`: pass=116 warn=4 fail=0 skip=2.
