# Canonical Development State Machine

## Defined States

`INIT` -> `BOOTSTRAPPED` -> `CLASSIFIED` -> [`SPECIFIED`] -> `PLANNED` -> `IMPLEMENTABLE` -> `IMPLEMENTING` -> `REVIEWED` -> `TESTED` -> `SHIPPED`

## Allowed Transitions

AI MUST self-enforce this phase order. Users may trigger transitions via slash commands (as shortcuts) OR via natural language — AI determines the appropriate phase regardless of wording.

- `INIT` --(external spec provided)--> `INIT` [runs `/spec-intake`; produces frozen spec + optional `_product-backlog.md`; loops back to INIT until spec is frozen]
- `INIT` --(context loaded)--> `BOOTSTRAPPED` [if frozen external spec exists, bootstrap reads it directly — Bootstrap Lite path]
- `BOOTSTRAPPED` --(task classified)--> `CLASSIFIED`  [Sets: Guardrails Mode (Full|Quick|Lite), Context Budget tier]
- `CLASSIFIED` --(research / brainstorm iteration)--> `CLASSIFIED`
- `CLASSIFIED` --(spec artifact created in `docs/specs/`)--> `SPECIFIED`
- `SPECIFIED` --(plan produced)--> `PLANNED`
- `CLASSIFIED` --(plan produced)--> `PLANNED`  [ONLY for: `tiny-fix`, `quick-win`, `hotfix`]
- `PLANNED` --(gate pass)--> `IMPLEMENTABLE`
- `IMPLEMENTABLE` --(begin implementation)--> `IMPLEMENTING`
- `IMPLEMENTING` --(review pass)--> `REVIEWED`
- `REVIEWED` --(test pass)--> `TESTED`
- `TESTED` --(ship executed)--> `SHIPPED`
- `IMPLEMENTING` --(evidence provided, quick-win only)--> `SHIPPED`  [fast-path: skip REVIEWED/TESTED states; quick-win only — hotfix MUST go through REVIEWED + TESTED]

## Spec Gate (Hard)

- Classifications `feature` and `architecture-change` MUST reach `SPECIFIED` before planning.
- `SPECIFIED` requires a corresponding `docs/specs/<feature>.md` artifact with `status: draft` or `status: frozen`.
- `tiny-fix`, `quick-win`, and `hotfix` may transition directly from `CLASSIFIED` to `PLANNED`.

## Read-Only Actions (No State Change)

- Listing help, available commands, generating test skeletons, producing handoff summaries

## Classification Escalation Rules

These rules override the initial classification. AI MUST apply them during `/bootstrap` and re-check during `/implement` Mid-Execution Guard.

- **Auth Escalation**: If a `quick-win` touches authentication, authorization, session management, or token handling → escalate to `hotfix` minimum. Hotfix requires REVIEWED + TESTED gates.
- **Governance File Escalation**: If a `tiny-fix` modifies `.agent/rules/*`, `.agent/config.yaml`, or `AGENTS.md` → escalate to `quick-win` minimum.
- **Scope Escalation**: If actual changes exceed classification threshold (e.g., `quick-win` touching >2 modules) → recommend rollback to `CLASSIFIED` and re-classify at higher tier.

## Hard Gates

- `feature` and `architecture-change` MUST complete a handoff phase before `SHIPPED`. Required references:
  1. ✅ `.agentcortex/` artifact path
  2. ✅ modified code path
  3. Resolved active work log path (`.agentcortex/context/work/<worklog-key>.md`)
- `quick-win` and `hotfix` are exempt from `/handoff` but MUST provide evidence (diff + behavior verification).
- `tiny-fix` allows fast-path but MUST provide minimal evidence (diff + one-line verification).

## Legacy State Mapping (Migration)

- `SPEC_READY` -> `SPECIFIED`
- `PLAN_READY` -> `IMPLEMENTABLE`
- `IN_PROGRESS` -> `IMPLEMENTING`
- `UNDER_REVIEW` -> `REVIEWED`
- `DONE` -> `SHIPPED` (Requires test & ship gates)
