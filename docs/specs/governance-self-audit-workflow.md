---
status: frozen
date: 2026-07-02
classification: feature
primary_domain: document-governance
signal_tier: T1
applies_to:
  - ".agent/workflows/govern-audit.md"
  - ".agent/workflows/routing.md"
  - ".claude/commands/govern-audit.md"
  - ".agentcortex/tools/check_command_sync.py"
---

# Governance Self-Audit Workflow (/govern-audit)

## Goal

Give the framework a first-class, repeatable workflow for auditing the governance
system ITSELF. Today `/audit` is scoped to legacy-repo onboarding ("Map an existing
legacy repository", routing trigger "new module, no ADR"), so governance premortems
and self-audits (three waves on 2026-07-01/07-02, 12 subagents, 3 shipped PRs) were
run by overloading `/audit` ad-hoc — the method that made those waves effective
lives only in session transcripts and Global Lessons, not in a workflow an agent can
execute. `/govern-audit` encodes that proven method as a report-only diagnostic
phase with routing_actions and disposition discipline built in.

**Adopter delta**: a downstream governance user gains an invocable "audit my
governance wiring" command whose output funnels into their backlog/canonical docs
instead of rotting in a chat transcript. Engine behavior (gates, validators, state
machine) is unchanged — this is a new read-only workflow plus registry rows.

## Acceptance Criteria

- **AC-1 (workflow file)**: `.agent/workflows/govern-audit.md` exists; declares
  report-only + gate-exempt (same Environment Constraints family as `audit.md`:
  NO GATE / NO CODE MODIFICATION / REPORT ONLY / ROUTE FINDINGS); the only writes
  it permits are the report snapshot, `routing_actions`, and backlog intake rows.
- **AC-2 (method contract)**: the workflow body encodes, as numbered steps, the
  proven funnel: (1) **Baseline first** — run the validator, read prior
  `docs/reviews/` governance snapshots and the backlog, and build an
  already-known list so known findings are not re-reported; (2) **Findings are
  hypotheses** — any subagent- or heuristic-sourced finding MUST be verified
  against the actual code path (read both cited sides) before it may appear in
  the report ([audit-verification] Global Lesson); (3) **Disposition funnel** —
  every surviving finding resolves to exactly one of do-now / backlog /
  close-with-reason; a "deferred" disposition is prohibited; (4) **Same-vendor
  caveat** — architecture-level conclusions require at least one external signal
  (different-vendor model, published external source, or human review) OR must be
  labeled same-vendor-only ([audit-method] Global Lesson); (5) **Report** —
  scope-qualified snapshot at `docs/reviews/<date>-govern-audit[-<scope>].md`
  (scope qualifier mandatory on same-day reruns, per the document-governance L2
  decision) with a mandatory `routing_actions` block (AC-29/AC-31 semantics
  identical to `audit.md`).
- **AC-3 (routing)**: `routing.md` §1 gains a Research & Analysis row routing
  "governance audit", "premortem", "治理自我稽核", "audit the governance/brain"
  to `/govern-audit`; §5 Command Registry gains the row; §4 Ambiguity Rules gains
  a one-line disambiguation: `/audit` = mapping a legacy/project repo;
  `/govern-audit` = auditing the governance system itself.
- **AC-4 (adapter + sync)**: `.claude/commands/govern-audit.md` dispatcher stub
  exists (same shape as `audit.md`'s stub); `check_command_sync.py`
  EXPECTED_COMMANDS includes `govern-audit`; the deploy manifest snapshot test is
  re-baselined in the same change (the two new files change the golden list).
- **AC-5 (zero always-loaded cost)**: no edits to `AGENTS.md`,
  `shared-contracts.md`, or any lifecycle-counted phase doc other than
  `routing.md` lookup rows; `test_lifecycle_token_consumption.py` aggregate and
  per-scenario tests pass unchanged (no ceiling bump).
- **AC-6 (SSoT at ship)**: `current_state.md` Canonical Commands gains the
  `/govern-audit` row via the normal /ship SSoT write.

## Non-goals

- No auto-scheduling or recurring-trigger mechanics (invocation is explicit).
- No new validator checks, gates, or MUST rules on always-loaded surfaces.
- No replacement or deprecation of `/audit` — its legacy-onboarding scope stays.
- No mandated subagent orchestration (platform capability varies; the method
  contract holds whether findings come from subagents or a single agent's pass).
- No GEMINI/codex adapter stubs beyond what deploy already generates (adapters
  are deploy-time surfaces; source repo carries `.claude/commands/` only).

## Constraints

- Report-only: the workflow itself MUST NOT modify governance sources; fixes it
  motivates go through the normal classified flow (bootstrap → …).
- Deletion-First (§13): all additions are non-always-loaded except ~3 routing
  lookup rows; net-add justification = they replace the ad-hoc overloading of
  `/audit`'s routing row.
- Signal tier T1: wiring is machine-locked by `check_command_sync.py`
  EXPECTED_COMMANDS (downstream), the deploy manifest snapshot test, and the
  existing routing-index validator checks; the method contract itself is
  prose-tier (honest: agent-obeyed, verified by the report artifacts it must
  produce — snapshot + routing_actions are validator-visible).

## API / Data Contract

- Report path: `docs/reviews/<YYYY-MM-DD>-govern-audit[-<scope>].md`.
- `routing_actions` block: identical schema to `audit.md` (finding / target_doc /
  status / owner; target_doc MUST be a canonical doc, never the snapshot).
- Chat output: compact block (Files-equivalent summary → findings count by
  disposition → `routing_actions: <N> pending` → report path → `⚡ ACX`).

## File Relationship

- NEW `.agent/workflows/govern-audit.md` — canonical workflow body.
- EDIT `.agent/workflows/routing.md` — §1 trigger row, §4 disambiguation line,
  §5 registry row.
- NEW `.claude/commands/govern-audit.md` — dispatcher stub.
- EDIT `.agentcortex/tools/check_command_sync.py` — EXPECTED_COMMANDS + "govern-audit".
- EDIT `tests/ci/fixtures/deploy_manifest_golden.txt` (or its re-baseline
  mechanism) — two new deployed files.
- SHIP-TIME `.agentcortex/context/current_state.md` — Canonical Commands row.

## Domain Decisions

- [DECISION] A dedicated `/govern-audit` workflow, not an extension of `/audit`:
  the two have disjoint audiences (adopter onboarding a legacy codebase vs
  maintainer auditing the governance engine), disjoint auto-suggest conditions,
  and overloading one routing row already caused the 2026-07-01/02 ad-hoc runs.
- [DECISION] Not a skill: skills attach to phases and cannot own a report/routing
  contract; this is a phase-shaped activity with its own output artifact, like
  `/audit` and `/research`.
- [DECISION] Method contract is prose-tier by design (T3-style honesty inside a
  T1-wired feature): a validator cannot check "you verified the finding against
  the code path", but it CAN see the artifacts the contract forces (snapshot
  naming, routing_actions, backlog rows) — the same enforcement shape `audit.md`
  already uses.
- [CONSTRAINT] The workflow must stay executable by a single agent with no
  subagent capability — subagent fan-out is an optional acceleration, not a
  dependency.
