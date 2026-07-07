# Work Log: codex-research-main

## Header

- Branch: `main`
- Classification: `feature`
- Classified by: `Codex`
- Frozen: `true`
- Created Date: `2026-06-18`
- Owner: `codex-research`
- Guardrails Mode: `Full`
- Current Phase: `research`
- Checkpoint SHA: `77fca37b97dfc7771c93ae7c4d5b4fdd74fae6ef`
- Recommended Skills: `systematic-debugging (interrupted-session root cause), karpathy-principles (future surgical plan), verification-before-completion (future evidence gate)`
- Primary Domain Snapshot: `governance-runtime`
- SSoT Sequence: `68`

---

## Session Info

### Session 2026-06-18

- Agent: `Codex (GPT-5)`
- Platform: `Codex App`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §6 (feature traceability) + §13 (possible governance change)`
- Override: `none`
- Context Read Receipt: `SSoT sequence 68; owner-scoped recovery log resumed`

### Session 2026-06-19

- Agent: `Codex (GPT-5)`
- Session: `2026-06-19T09:28:15+08:00`
- Platform: `Codex App`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §6 (feature traceability) + §13 (possible governance change)`
- Override: `none`
- Downstream-Capabilities: `none`
- User Preferences: `none`
- Context Read Receipt: `SSoT sequence 68; Work Log resumed; 9 ADRs found; no covering ADR for the anticipated target paths`

---

## Task Description

Recover and continue the interrupted comparative research on reusable skill/workflow practices from `anthropics/skills` and `obra/superpowers`. Preserve the derived optimization inventory, then design a minimal, enforceable persistence boundary for long research/spec-intake batches before context exhaustion.

Expected phase chain: `/brainstorm → /spec → /plan → /implement → /review → /test → /handoff → /ship`.

---

## Phase Sequence

| Phase | Status | Notes |
|---|---|---|
| bootstrap | completed | Recovery, classification, and bounded comparative research context restored. |
| research | in progress | Nodes 0-9 persisted; five re-verified sources remain for deep analysis, followed by final synthesis. |
| brainstorm | completed | Four options compared; private pre-browse research capsule recommended; awaiting human confirmation. |
| decide | completed | D-1 records the confirmed private pre-browse capsule direction. |
| adr | completed | ADR-009 accepted and indexed; target paths now have ADR coverage. |
| spec | provisional draft | `docs/specs/research-capsule-persistence.md`; freeze deferred until the remaining source analysis and synthesis complete. |
| plan | pending | Define targeted files, enforcement, tests, and rollback. |
| implement | pending | No implementation authorized or started. |
| review | pending | Required. |
| test | pending | Required. |
| handoff | pending | Required for this classification. |
| ship | pending | Required. |

---

## Research Inventory Recovered

- `anthropics/skills` pinned at `57546260929473d4e0d1c1bb75297be2fdfa1949`; package/evaluation mechanics and residual gaps are persisted.
- `obra/superpowers` pinned at `b62616fc`; Node 6 verifies the sequence Task → capsule/ledger → one reviewer/two verdicts.
- `multica-ai/andrej-karpathy-skills` pinned at `2c606141`; Node 7 found no new behavioral feature gap beyond provenance hygiene.
- Candidate optimizations A-G and priority order `D → B+C → A`: `.agentcortex/context/private/codex-research-main/node-00-recovered-inventory.md`.
- Authoritative detailed checkpoints: `.agentcortex/context/private/codex-research-main/node-00..07*.md`, including re-audits 2A/3A.

---

## Root Cause Record

- Symptom: context exhaustion occurred during multi-source browsing before a dedicated Work Log or issue existed.
- Verified gap: `spec-intake §1a` persists supplied input; nonlinear Rule 1 checkpoints implementation only; Rule 6 assumes an existing Work Log.
- Fix direction: create a research capsule before browsing, checkpoint claims/provenance/questions per source, and synthesize only from persisted checkpoints.

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Source repo | `https://github.com/anthropics/skills` | Re-verify current revision before final recommendations. |
| Source repo | `https://github.com/obra/superpowers` | Re-verify current revision before final recommendations. |
| Workflow | `.agent/workflows/spec-intake.md` | Anticipated target; no covering ADR found. |
| Resilience policy | `.agentcortex/docs/NONLINEAR_SCENARIOS.md` | Anticipated target; no covering ADR found. |
| ADR | `docs/adr/ADR-009-pre-browse-research-capsule.md` | Accepted architecture and lifecycle boundary for this feature. |
| Spec | `docs/specs/research-capsule-persistence.md` | Draft feature contract; 15 ACs and 8 domain decisions. |
| Evidence | `.agentcortex/context/private/codex-research-main/` | Persistent research nodes and screenshots. |

---

## Known Risk

- Only two of the original nine source names survived; remaining names must be rediscovered, not inferred.
- `main` has unrelated untracked `.acx-local/` files that must remain untouched.
- The existing `.agentcortex/context/work/main.md` belongs to another task and must not be overwritten.
- ADR-009 now covers the anticipated workflow/resilience target paths.

---

## Conflict Resolution

- `karpathy-principles` and `verification-before-completion` are compatible.
- Keep debugging evidence-first; keep future changes surgical; require verification evidence before completion.
- Existing draft `docs/specs/skill-research-integration.md` concerns research candidate selection, not session persistence; the new spec is explicitly INDEPENDENT.

---

## Spec Review Report

- Confirmed: Goal and architecture align with D-1 and ADR-009; ADR coverage resolves every anticipated target path.
- Verified: 15 numbered ACs, `status: draft`, `primary_domain: governance-runtime`, `signal_tier: 1`, 8 tagged Domain Decisions, and no unresolved Open Questions.
- Boundary: T1 covers helper/schema/wiring; T2 covers agent ordering. The spec does not claim repository code can intercept an agent that ignores workflow instructions.
- Domain Doc: no living `docs/architecture/governance-runtime.md` exists, so there is no L1 conflict.
- Quality Tier: `READY`.
- Confidence: `92%` — the root failure and target seams are evidenced; remaining uncertainty is implementation detail, not product scope.

---

## Decisions

### D-1: Use a private pre-browse research capsule
- **Decision**: Create a primary-owned private capsule before long or multi-source research, with a manifest and bounded source/work-unit checkpoints.
- **Reason**: It is the smallest option that closes the verified failure before a Work Log exists while keeping detailed evidence out of the Work Log.
- **Alternatives**: Broaden Work Log checkpoints (root gap remains); use tracked `_research-*` as the ledger (wrong lifecycle); implement full Task/Step capsules now (oversized).
- **Impact**: `/research`, `/spec-intake`, and nonlinear recovery must share the capsule lifecycle; Task/Step review and skill evaluation remain separate features.

---

## Skill Notes

### systematic-debugging

- Checklist: preserve the symptom; test hypotheses; change one seam at a time.
- Constraint: no governance patch before the missing persistence boundary is evidenced.

### karpathy-principles

- Checklist: keep the future plan minimal; avoid unrelated governance refactors.
- Constraint: implementation scope must remain tied to the selected persistence seam.

### verification-before-completion

- Checklist: verify recovery readability; verify the fail-without-fix regression; verify final gates.
- Constraint: no evidence means no completion claim.

---

## Phase Summary

- bootstrap: Recovered classification, source scope, A-G priorities, persistence-gap diagnosis, and current governance context; no product mutation. ⚡ ACX
- research: Nodes 0-7 and re-audits 2A/3A completed with persistent evidence; research stage closed. ⚡ ACX
- brainstorm: Compared Work Log checkpointing, private research capsule, tracked `_research-*` ledger, and full Task/Step architecture; recommended the private pre-browse capsule. Full record: `.agentcortex/context/private/codex-research-main/node-08-brainstorm-persistence-seam.md`. ⚡ ACX
- decide: User confirmed D-1; the private pre-browse research capsule is binding for ADR/spec work. ⚡ ACX
- adr: Created and indexed ADR-009; coverage check now resolves all anticipated workflow, resilience, and helper paths. ⚡ ACX
- spec: Created `docs/specs/research-capsule-persistence.md` as a READY draft with verifiable ACs, explicit enforcement limits, and no open questions; freeze awaits user approval. ⚡ ACX
- research: User narrowed delivery to complete analysis and handoff only; issue/backlog/implementation work is reserved for Claude. Node 09 pins the five remaining source revisions. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-18T10:05:40+08:00
- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-19T09:28:15+08:00

---

## Evidence

- `git rev-parse HEAD` → `77fca37b97dfc7771c93ae7c4d5b4fdd74fae6ef`; worktree has only unrelated untracked `.acx-local/`.
- Work Log lock ensure → `status=created`, `reason=missing`, owner `codex-research`, phase `bootstrap`.
- ADR coverage check for `.agent/workflows/spec-intake.md` and `.agentcortex/docs/NONLINEAR_SCENARIOS.md` → exit `1`, `no_covering_adr`.
- Bootstrap context: SSoT sequence `68`, 9 ADR files, no override, no downstream capabilities, no user skill preferences.
- Research evidence and prior validation receipts remain in the compaction archive and private node files.
- Brainstorm artifact write receipt: `node-08-brainstorm-persistence-seam.md` SHA-256 `e2c1737c18e2bb2029c46d07a8639fe3ab55c42faee42e95081b0a6675bb4083`.
- ADR-009 write receipt: SHA-256 `f7332a8d683d7b4d72254163095c13b1247e28e1bdec473abad4a91dd5f040a9`; ADR coverage check reports `covered_by: ADR-009` for all target paths.
- Spec structure check: 179 lines, 15 ACs, 8 Domain Decisions, draft/domain/signal fields present, `git diff --check` clean.
- Node 09 source manifest receipt: SHA-256 `f6f3745b585c0a31cc0a865a49c3c873f85ceab759a046338644848f3eaeb4d9`; five repository HEADs and licenses re-verified on 2026-06-19.

---

## Drift Log

- 2026-06-18: Created owner-scoped log because `main.md` belongs to another task.
- 2026-06-18: Repo search found no exact nine-source manifest; recorded source classes rather than inventing names.
- 2026-06-18: Nodes 0-7 and re-audits 2A/3A completed; no issue, backlog, spec, or implementation mutation occurred.
- 2026-06-18: Formal `/handoff` was not emitted because plan, implement, review, and test never occurred.
- 2026-06-19: Bootstrap resumed on `main`; lock reacquired; no covering ADR found for anticipated target paths.
- 2026-06-19: User confirmed brainstorm Option 2; recorded as D-1 before ADR/spec generation.
- 2026-06-19: ADR Index update: ADR-009 added directly under the approved `/adr` SSoT-write exception.
- 2026-06-19: `/spec` workflow requests a Draft Spec Index write, but AGENTS.md Write Isolation lists exhaustive non-ship exceptions and does not include `/spec`; deferred SSoT Spec Index mutation and kept the draft pointer in this Work Log.
- 2026-06-19: User redirected scope before freeze: finish all remaining research and final analysis, then hand issue/backlog work to Claude. Spec remains draft and is not implementation authorization.
- Compacted: 2026-06-19, archive: `.agentcortex/context/archive/work/codex-research-main-20260619.md`.

---

## Design Reference

none

---

## Observability

none

---

## Resume

- State: `RESEARCH IN PROGRESS; SPEC DRAFT PROVISIONAL`
- Completed: `Nodes 0-9 + re-audits 2A/3A; D-1; ADR-009; provisional feature spec`
- Next: `Complete Nodes 10-14, then final synthesis and Claude handoff; do not create issues, mutate backlog, freeze, plan, or implement`
- Context: `Remaining sources are Addy agent-skills, TLC agent-skills, VoltAgent subagents, Awesome Claude Code, and Awesome Agent Skills`
- Read Map: `.agentcortex/context/private/codex-research-main/node-00..07*.md`; `.agent/workflows/spec-intake.md §1a`; `.agentcortex/docs/NONLINEAR_SCENARIOS.md Rules 1 and 6`
- Skip: `Do not touch .acx-local/ or .agentcortex/context/work/main.md; do not unfreeze shipped specs without approval`

⚡ ACX
