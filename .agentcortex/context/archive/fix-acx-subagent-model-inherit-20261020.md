# Work Log: fix/acx-subagent-model-inherit

## Header
- Branch: `fix/acx-subagent-model-inherit`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-20`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `6ce32f9`
- Checkpoint SHA: `6ce32f9`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `215`

---

## Session Info
- Agent: `claude-opus-5-5`
- Session: `2026-10-20T07:25:46Z`
- Platform: `claude-code`
- Guardrails loaded: skipped (quick-win)
- Override: none
- Downstream-Capabilities: none

---

## Task Description
Backlog #236: the acx-* subagent shims pin their model (acx-reviewer opus, the other four sonnet), overriding the user's model choice. In the #239 pilot the reviewer's Opus cost was $12.13 of the governed $41.79 (steps 4-6). Owner chose 'inherit the session model' (chat 2026-10-20, by taking the brief). Set model: inherit on all five shims and update the Claude platform guide.

---

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-20T07:25:47Z | - |
| plan | done | 2026-10-20T07:25:48Z | - |
| implement | done | 2026-10-20T07:44:45Z | - |
| review | done | 2026-10-20T07:44:45Z | - |
| test | done | 2026-10-20T07:44:46Z | - |
| handoff | pending | — | — |
| ship | done | 2026-10-20T07:44:46Z | local commit |

---

## Phase Summary
- bootstrap: quick-win (#236, backlog → In Progress via guard); Claude-only surface (.claude/agents) — other platforms have no subagent model pins, so parity is unaffected. plan: model: inherit in all five acx-* shims (explicit value rather than deleting the key, so the intent is visible); CLAUDE_PLATFORM_GUIDE EN + zh-TW table column and one sentence on why; verify with a headless dispatch that the reviewer resolves to the session model. Rollback: revert.
- implement: model: inherit on acx-handoff/implementer/reviewer/shipper/tester; CLAUDE_PLATFORM_GUIDE EN + zh-TW table → inherit plus a 'Model' paragraph ($12 of $42 in the #239 pilot). review: self-review — Claude-only surface, no platform loses anything; no test pinned the old values (grep). test: headless dispatch from a haiku session → subagent ran (1 call) and modelUsage shows only claude-haiku-4-5; control with the old opus pin → claude-opus-5-5 $0.1424 appears. Agent/doc/skill tests 328 passed; deploy tiering 69 passed, 2 skipped; validate.sh fail=0.
- ship: backlog #236 → Shipped and moved to the archive; local commit, not pushed (stacked on PR #475's branch; push after #475 merges). ⚡ ACX

---

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T07:25:48Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T07:25:48Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T07:44:45Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T07:44:46Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T07:44:46Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T07:44:46Z

---

## External References
none

---

## Known Risk
none

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
- Demonstration: inherit → 'subagent calls 1 models {claude-haiku-4-5-20251001: 0.0442}'; old pin → 'subagent calls 1 models {claude-haiku-4-5-20251001: 0.0086, claude-opus-5-5: 0.1424}'.
- final (post-archive): validate.sh `pass=117 warn=5 fail=0 skip=2`; `scan_credentials.py --staged` clean.
