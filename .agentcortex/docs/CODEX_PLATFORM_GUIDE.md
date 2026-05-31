# Codex Platform Guide (Web / App)

## Scope

This template applies to both:

- Codex Web
- Codex App (Desktop)

## File Placement Standards (Codex Web / App / Google Antigravity)

To avoid procedural complexity, all three platforms share the same skill source and mirrored paths:

1. Canonical skill source: `.agent/skills/<skill>/SKILL.md` (Primary path for Antigravity; maintain 1:1 sync).
2. Codex Compatibility Path: `.agents/skills/<skill>/SKILL.md` (Codex mirror).
3. Platform Workflow Files: `.agent/workflows/*.md` and `.agent/rules/*.md` (No duplication).

Minimum Check Recommendations:

- Run `./.agentcortex/bin/validate.sh`.
- Confirm `AGENTS.md` still declares both `.agent/skills` and `.agents/skills`.

## Unified State Machine

Use the canonical state machine:
`Ref: .agent/rules/state_machine.md`

- `/help`, `/commands`, `/test-skeleton`, and `/handoff` are Read-Only commands.
- `/ship` is allowed only after `TESTED` state.

## Shared Recommendations

1. Provide target, target files, constraints, and acceptance criteria (AC) at the start of a task.
2. Run `/bootstrap` first, then `/plan`; only run `/implement` once the quality gate has passed.
3. Run `/review` and `/test` after every implementation.
4. Run `./.agentcortex/bin/validate.sh` before submission.

## Handoff Hard Gate (Non-tiny-fix)

Before `/ship`, you must have a `/handoff`. Minimum reference requirements:

1. At least 1 `docs/` artifact.
2. At least 1 code file path.
3. Corresponding work log: `.agentcortex/context/work/<worklog-key>.md`.
   Resolve `<worklog-key>` from the branch using a filesystem-safe name; if the active log is missing but recoverable, recreate it before rejecting `/ship`.

If unsatisfied, you must reject `/ship` and list the missing items.

## Gate Receipt Persistence — Codex Web

On Codex Web there is no file-write capability. Gate receipts MUST still be recorded for validator compliance. Protocol:

1. At each phase completion, output the gate receipt as a fenced block in chat:
   ```
   ## Gate Evidence
   - Gate: <phase> | Verdict: PASS | Classification: <tier> | Timestamp: <ISO>
   ```
2. Instruct the user: "Paste the block above into `.agentcortex/context/work/<worklog-key>.md` under `## Gate Evidence`."
3. Do NOT proceed to the next phase until the user confirms the paste is done (or acknowledges they will do it before `/ship`).
4. At `/ship`, the Gate Receipt Audit checks the Work Log — if receipts are missing because the user did not paste them, `/ship` MUST fail with `missing: [<phase> receipt]`.

This ensures Codex Web-authored Work Logs remain validator-compliant even without direct file access.

## Handoff Timing

Handoff timing follows the cross-platform SSoT — `AGENTS.md §Context Pruning` (context occupancy + phase boundary, not turn-count). Codex nuance (`.agentcortex/docs/guides/token-governance.md §6.1`): automatic prompt caching is active (0.1×, prefix ≥1024 tok; 24 h extended on GPT-5.1), and auto-compaction fires late (~95% capacity) and can derail mid-task — so prefer handing off at a clean phase boundary before that.

## Web Edition Recommendations

- Use one thread per requirement to avoid context pollution.
- Before pausing a long task, output `/handoff` and remind the human to save it.

## App Edition Recommendations

- Run `deploy_brain.sh` and validation scripts locally.
- Update the work log after every submodule completion to reduce context reconstruction costs.

## Quick Checklist

- [ ] `/bootstrap` completed
- [ ] `/plan` passed quality gate
- [ ] `/implement` executed in `IMPLEMENTABLE` state
- [ ] `/review` and `/test` completed
- [ ] `/handoff` completed for non-tiny-fix tasks
- [ ] `validate.sh` passed
