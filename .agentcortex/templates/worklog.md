---
template: true
description: Work Log template for all non-tiny-fix tasks. Tracks session context, phase progress, gate evidence, and handoff state.
usage: Used by /bootstrap workflow when creating a new Work Log at .agentcortex/context/work/<worklog-key>.md. Fill all fields; write "none" for empty sections.
---

# Work Log: <branch-name>

## Header

| Field | Value |
|---|---|
| Branch | `<raw-branch-name>` |
| Classification | `<tiny-fix \| quick-win \| hotfix \| feature \| architecture-change>` |
| Classified by | `<model-name or human>` |
| Frozen | `true` |
| Created Date | `<YYYY-MM-DD>` |
| Owner | `<session-id or username>` |
| Guardrails Mode | `<Full \| Quick \| Lite>` |
| Current Phase | `<bootstrap \| plan \| implement \| review \| test \| handoff \| ship>` |
| Checkpoint SHA | `<git-sha or none>` |
| Recommended Skills | `<comma-separated skill IDs or none>` |
| Primary Domain Snapshot | `<domain \| none>` |
| SSoT Sequence | `<N>` |

---

## Session Info

> Written by /bootstrap. Update on each new session.

- Agent: `<model-name>`
- Session: `<YYYY-MM-DD HH:MM UTC>`
- Platform: `<claude-code | codex | antigravity | api>`
- Files Read: `<integer>` (optional — running count of file reads across this session for token-budget instrumentation; bootstrap may seed `0`, later phases may increment when material).

---

## Task Description

> 1-3 sentences: what is being done and why.

none

---

## Phase Sequence

> Record each phase entry in order. Update `Current Phase` in the Header on entry.

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | pending | — | — |
| plan | pending | — | — |
| implement | pending | — | — |
| review | pending | — | — |
| test | pending | — | — |
| handoff | pending | — | — |
| ship | pending | — | — |

---

## Phase Summary

> One paragraph per completed phase. Delta-oriented: what changed, what was decided.

none

---

## Gate Evidence

> Gate receipts written by each phase. Format: `gate: <phase> | verdict: pass/fail | classification: <type> | timestamp: <ISO>`

none

---

## External References

> Links to specs, ADRs, issues, PRs, or design docs relevant to this task.

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | — |
| ADR | — | — |
| Issue | — | — |
| PR | — | — |

---

## Known Risk

> List risks identified during planning or implementation. Include mitigation.

none

---

## Conflict Resolution

> Record skill conflicts resolved during bootstrap (from skill_conflict_matrix.md). Format: `<skill-A> vs <skill-B>: <chosen approach>`.

none

---

## Skill Notes

> Cache for loaded skills. Written by phase-entry skill loading. Leave as `none` until populated.

none

---

## Drift Log

> Record deviations from the original plan, reclassifications, or unexpected scope changes.

none

---

## Evidence

> Reproducible evidence for completed phases. Commands, outputs, versions. "It should work" is NOT evidence.
> **Terse format** (Ref: `engineering_guardrails.md` §5.2b Evidence Truncation Rule): success ≤ 3 lines per claim, failure ≤ 10 lines per claim with the most diagnostic context (root error + bottom of stack), strip passing-test noise. Multiple bullet entries preferred over one long paste.

none
