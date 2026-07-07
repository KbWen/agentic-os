# Work Log: codex-research-main

## Header

- Branch: `main`
- Classification: `feature`
- Classified by: `Codex`
- Frozen: `true`
- Created Date: `2026-06-18`
- Owner: `codex-research`
- Guardrails Mode: `Full`
- Current Phase: `bootstrap`
- Checkpoint SHA: `77fca37b97dfc7771c93ae7c4d5b4fdd74fae6ef`
- Recommended Skills: `systematic-debugging (interrupted-session root cause), karpathy-principles (future surgical plan), verification-before-completion (future evidence gate)`
- Primary Domain Snapshot: `governance-runtime`
- SSoT Sequence: `68`

---

## Session Info

- Agent: `Codex (GPT-5)`
- Session: `2026-06-18T10:05:40+08:00`
- Platform: `Codex App`
- Files Read: `governance + recovery evidence; exact count not retained after interruption`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §6 (feature traceability) + §13 (possible governance change)`
- Override: `none`
- Context Read Receipt: `SSoT sequence 68; main.md belongs to another task; owner-scoped recovery log created`

---

## Task Description

Recover and continue the interrupted comparative research on reusable skill/workflow practices from `anthropics/skills` and `obra/superpowers`. Preserve the already-derived optimization inventory before further browsing, then design a minimal, enforceable way for long research/spec-intake batches to persist progress before the model context window is exhausted.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | completed | 2026-06-18 | Recovery + bounded comparative research stage closed; no product mutation. |
| brainstorm | pending | — | Decide whether the durable fix belongs in spec-intake, research, or nonlinear resilience. |
| spec | pending | — | Required before changing workflow semantics. |
| plan | pending | — | Define targeted files, enforcement, tests, and rollback. |
| implement | pending | — | No implementation authorized or started yet. |
| review | pending | — | — |
| test | pending | — | — |
| handoff | pending | — | Required before ship for this classification. |
| ship | pending | — | — |

---

## Research Inventory Recovered

### Broader comparative scan queue

Only two of the original nine source names survived. Rediscover—not guess—others within the five recorded source classes.

### Source manifest

| Source | Owner/license | Revision/date | Question | Status |
|---|---|---|---|---|
| `anthropics/skills` | Anthropic PBC; mixed per-skill licensing | `57546260929473d4e0d1c1bb75297be2fdfa1949` · 2026-06-09 | Skill evaluation, package shape, descriptions | Node 1 baseline complete |
| `obra/superpowers` | Jesse Vincent; MIT | `b62616fc` · 2026-06-17 | Task boundaries, review, TDD/debug/worktree | Node 5 baseline complete |
| `multica-ai/andrej-karpathy-skills` | Declares MIT; root license absent | `2c606141` · 2026-04-20 | Check local Karpathy integration for residual gaps | Node 7 complete |
| Broader queue | five unreviewed rediscovered repos; original mapping unproven | pending | Search within five classes above | optional future work |

Persist source identity, license, revision, question, and checkpoint before synthesis.

### Research checkpoints

- Nodes 1/5: pinned source, revision, licensing, and repository baselines verified for `anthropics/skills` and `obra/superpowers`.
- Nodes 2-4: Agent Skills package/evaluation mechanics compared to live Agentic OS controls; detail remains in the node files.
- Re-audits 2A/3A: package metadata/resource-loading and evaluation fairness/reproducibility residuals verified.
- Node 6 complete: Superpowers v6 verifies Task→capsule/ledger→one reviewer/two verdicts; Agentic OS lacks the task-level seam. Detail: `.agentcortex/context/private/codex-research-main/node-06-superpowers-task-capsule-review.md`.
- Node 7 complete: current Karpathy source is already integrated and locally strengthened; only canonical-owner/license-provenance hygiene and future candidate-A benchmarking remain. Detail: `.agentcortex/context/private/codex-research-main/node-07-karpathy-guidelines-deep-compare.md`.

### Candidate optimizations

A–G, boundaries, and recovered order `D → B+C → A`:
`.agentcortex/context/private/codex-research-main/node-00-recovered-inventory.md`.
No issue/backlog/spec/implementation mutation has occurred.

---

## Root Cause Record

- Symptom: context-window exhaustion occurred during multi-source browsing before an issue, backlog row, or dedicated Work Log existed.
- Verified gap: `spec-intake §1a` persists supplied input; nonlinear Rule 1 checkpoints implementation only; Rule 6 requires an existing Work Log.
- Likely amplifier: one large synthesis batch instead of source-scoped checkpoints.
- Fix direction: create a research capsule before browsing; checkpoint claims/provenance/questions after each source; synthesize only from persisted checkpoints; any new imperative rule needs machine/eval evidence.

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Source repo | `https://github.com/anthropics/skills` | Re-verify current content and licensing before final recommendations. |
| Pinned revision | `https://github.com/anthropics/skills/tree/57546260929473d4e0d1c1bb75297be2fdfa1949` | Node 1 inspected revision. |
| Source repo | `https://github.com/obra/superpowers` | Re-verify current content and licensing before final recommendations. |
| Workflow | `.agent/workflows/spec-intake.md` | Persists raw user input but not this interrupted research pattern. |
| Resilience policy | `.agentcortex/docs/NONLINEAR_SCENARIOS.md` | Existing checkpoint trigger is implementation-centric. |
| Evidence directory | `.agentcortex/context/private/codex-research-main/evidence/` | Persistent local copies of all four screenshots; filenames 01–04 describe contents. |

---

## Known Risk

- Only two of the original nine source names survived; remaining names must be rediscovered, not inferred.
- `main` has unrelated untracked `.acx-local/` files that must remain untouched.
- The existing `.agentcortex/context/work/main.md` belongs to another task and must not be overwritten.

---

## Conflict Resolution

- Debug first; keep the eventual patch surgical; completion requires recovery and regression evidence.

---

## Skill Notes

### systematic-debugging

- Checklist: preserve symptom; test hypotheses; change one seam at a time.
- Constraint: no governance patch before the missing persistence boundary is evidenced.

### verification-before-completion

- Checklist: verify recovery readability, both repositories, A-G, and a fail-without-fix regression.
- Constraint: no evidence means no completion claim.

---

## Phase Summary

- bootstrap: Recovered source scope, A-G, priorities, broader scan queue, and persistence-gap diagnosis; no issue/backlog/spec/implementation mutation. ⚡ ACX
- research: Node 6 verified D→B+C: define Task-above-Step first, then add a private primary-owned capsule/ledger and one-reviewer/two-verdict checkpoint; retain final branch review. ⚡ ACX
- research: Node 7 found no new Karpathy feature gap; local skill is stronger than source. Research stage closed with resumable evidence and no product mutation. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-18T10:05:40+08:00

---

## Evidence

- Persistent screenshots preserve source names, A-G, priority, and the context-exhaustion error.
- Recovery and Node 1-5 evidence are recorded in their private node files; no product files changed.
- Node 6 evidence: Superpowers main remains `b62616fc`; temporary-clone checks returned task brief `0`, missing task `3`, review package `0`, invalid SHA `2`, and a clean worktree.
- Node 7 evidence: both old/new Git URLs resolve `2c606141`; API canonical owner is `multica-ai`; source has no tests/evals or root license file; local skill preserves all four principles plus 84 net lines of operational controls.
- Stage close: lifecycle activation `53 passed`; `validate.ps1` → `pass=109 warn=4 fail=0 skip=2`; Work Log 12,014 bytes before this receipt.

---

## Drift Log

- 2026-06-18: Created owner-scoped log because `main.md` belongs to another task.
- 2026-06-18: Initial governance batch output truncated; future uncertain re-read must name one section.
- 2026-06-18: Repo search found no exact nine-source manifest; recorded five classes rather than inventing names.
- 2026-06-18: Copied Temp screenshots into the persistent private evidence directory and compacted this log after validator reported the 12 KB limit.
- 2026-06-18: User required small sequential research nodes with a Work Log checkpoint at every boundary and authorized rediscovery of additional high-signal sources; every practice node follows the Node 00 depth contract.
- 2026-06-18: Nodes 1-5 and Re-audits 2A/3A completed sequentially; conclusions remain source-scoped until final synthesis.
- 2026-06-18: Node 6 completed; script contracts and public-test limits recorded, B/C/D classified Keep/Adapt/Reject, and no issue/backlog/spec mutation occurred.
- 2026-06-18: Node 7 completed and bounded research stage closed at user request; formal `/handoff` was not emitted because plan/implement/review/test never occurred.
- Takeover of ACTIVE Work Log lock on 2026-06-18T13:30:45.801326+00:00; prior_owner=codex-research; prior_session=2026-06-18T14:00:00+08:00; lock=codex-research-main.lock.json

---

## Design Reference

none

---

## Observability

none

---

## Resume

- State: `BOOTSTRAPPED / CLASSIFIED (feature); RESEARCH STAGE CLOSED`
- Completed: `Nodes 0-7 + Re-audits 2A/3A; Anthropic evaluation/package gaps, Superpowers D→B+C, and Karpathy no-gap disposition verified`
- Next: `New owner chooses: (a) continue optional source queue one node at a time, or (b) enter brainstorm/spec for D→B+C plus research-capsule persistence. Do not implement directly.`
- Context: `Highest-value verified sequence is D Task→Step, then B capsule/ledger + C one-reviewer/two-verdict, then A evaluation. Karpathy needs provenance hygiene only. No issue/backlog/spec/product mutation exists.`

### Read Map

- `.agentcortex/context/work/codex-research-main.md` — canonical recovery state and A-G inventory.
- `.agentcortex/context/private/codex-research-main/node-00..05*.md` — completed checkpoints.
- `.agentcortex/context/private/codex-research-main/node-02a-*.md`, `node-03a-*.md` — authoritative deep comparisons.
- `.agentcortex/context/private/codex-research-main/node-06-superpowers-task-capsule-review.md` — authoritative B/C/D mechanics, script checks, gap matrix, and dispositions.
- `.agentcortex/context/private/codex-research-main/node-07-karpathy-guidelines-deep-compare.md` — source transfer/license status and local no-gap disposition.
- `.agent/workflows/spec-intake.md §1a` — existing persist-before-processing behavior.
- `.agentcortex/docs/NONLINEAR_SCENARIOS.md Rules 1 and 6` — current checkpoint/handoff behavior.
- `docs/specs/handoff-trigger-policy.md` — shipped historical decision and non-goals.

### Skip List

- Do not re-read `.agentcortex/context/work/main.md`; it belongs to another completed task.
- Do not touch `.acx-local/`.
- Do not create GitHub issues or mutate `_product-backlog.md` until both source checkpoints are re-verified.
- Do not modify `docs/specs/handoff-trigger-policy.md` unless the user explicitly approves unfreezing it.

### Context Snapshot

- Recovery lock is released between sessions; reacquire `.agentcortex/context/work/codex-research-main.lock.json` before the next Work Log write.
- Stable code checkpoint: `77fca37b97dfc7771c93ae7c4d5b4fdd74fae6ef`.
- Research stage closed cleanly. Optional broader candidates remain; no active source node is half-finished.
- Formal `/handoff` is not yet legal because the feature has not passed plan, implement, review, and test; this Resume block is a recovery checkpoint, not a false handoff receipt.

⚡ ACX
