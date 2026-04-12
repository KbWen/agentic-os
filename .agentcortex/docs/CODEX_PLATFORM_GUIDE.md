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
