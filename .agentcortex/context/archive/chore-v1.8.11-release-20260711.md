---
template: true
description: Work Log template for all non-tiny-fix tasks. Tracks session context, phase progress, gate evidence, and handoff state.
usage: Used by /bootstrap workflow when creating a new Work Log at .agentcortex/context/work/<worklog-key>.md. Fill all fields; write "none" for empty sections.
---

# Work Log: <branch-name>

## Header

- Branch: `<raw-branch-name>`
- Classification: `<tiny-fix | quick-win | hotfix | feature | architecture-change>`
- Classified by: `<model-name or human>`
- Frozen: `<YYYY-MM-DD or true>`
- Created Date: `<YYYY-MM-DD>`
- Owner: `<session-id or username>`
- Guardrails Mode: `<Full | Quick | Lite>`
- Current Phase: `<bootstrap | plan | implement | review | test | handoff | ship>`
- Diff Base SHA: `<git-sha or none>` <!-- immutable: set once on first /implement -->
- Checkpoint SHA: `<git-sha or none>` <!-- mutable: refresh each commit -->
- Recommended Skills: `<comma-separated skill IDs or none>`
- Primary Domain Snapshot: `<domain | none>`
- SSoT Sequence: `<N>`

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
> End this section with the `⚡ ACX` sentinel at least once — `validate.sh` checks for it here so the runtime marker has a persistent audit trail (chat output is ephemeral).

none

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T12:20:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T12:22:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T12:35:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T13:05:00Z
> **Critical**: `|` pipe separators are mandatory. Receipts placed inside markdown code fences are silently masked and NOT counted by validate.sh — always write receipts as plain list lines.

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

## Review Feedback

> Written by /review (fix suggestions + NOT READY findings). Read by /implement on resume-after-review — scope is ONLY the UNPROVEN/blocking rows.

none

---

## Red Team Findings

> Written by /review and /test when adversarial testing runs. HIGH findings do not block but MUST record a risk decision here.

none

---

## Design Reference

> Populated by /plan for UI tasks. If not a UI task, write `none`.
> Format: `Link: <DSoT URL or file path> | Tool: <Stitch | Figma | Pencil | other>`

none

---

## Observability

> Populated by /ship for feature/architecture-change tasks. Document the production error sink used in changed code.
> Format: `Sink: <logger name or API> | Scope: <files> | Verified: <yes/no>`

none

---

## Resume

> Populated by /handoff for feature/architecture-change tasks. Required: `State`, `Completed`, `Next`, `Context` fields; then `### Read Map`, `### Skip List`, `### Context Snapshot`; optionally `### Backlog Status`. validate.sh enforces the three `###` headings. Leave as `none` until /handoff runs.

none

---

## Test Gate Results

> Test-phase gate outcome for `feature`/`architecture-change` logs (required at handoff/ship once an implement receipt exists; ref: `engineering_guardrails.md §12.2`). Record pass/fail counts + the test command. Leave `none` until `/test` runs.

none

---

## Evidence

> Reproducible evidence for completed phases. Commands, outputs, versions. "It should work" is NOT evidence.
> **Terse format** (Ref: `engineering_guardrails.md` §5.2b Evidence Truncation Rule): success ≤ 3 lines per claim, failure ≤ 10 lines per claim with the most diagnostic context (root error + bottom of stack), strip passing-test noise. Multiple bullet entries preferred over one long paste.

none
