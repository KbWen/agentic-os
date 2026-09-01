# Work Log: test/workflow-job-graph-integrity-183

## Header

- Branch: `test/workflow-job-graph-integrity-183`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `2026-09-01`
- Created Date: `2026-09-01`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `f250db1fc900d0baf9524b342e69a19293a81128`
- Checkpoint SHA: `447655b`
- Recommended Skills: `verification-before-completion (auto), systematic-debugging (auto), karpathy-principles (auto), kb-consult (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `164`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-09-01T06:26:12Z`
- Platform: `claude-code`
- Override: `none` (no project-root or ~/.agentcortex AGENTS.override.md)
- Downstream-Capabilities: `.agentcortex/context/private/downstream-capabilities.yaml (0 skills, subagent_policy=default, knowledge_sources: kb-main→OK@328b30ecb33b)`
- Guardrails loaded: Quick Mode (AGENTS.md §Core Directives only; engineering_guardrails.md NOT read — Token Leak block)
- Context Read Receipt: `current_state.md` → Update Sequence 164, Last Verified 2026-08-23 · Work Log → created · Spec Scope → none (no Spec Index entry covers CI workflow structure)

---

## Task Description

Backlog **#183**: workflow job-graph integrity is unguarded. A dangling `needs:` target makes GitHub reject the **whole** workflow at parse time — not skip one job — so every push-triggered check silently stops running while the local tree stays green.

Reported by a downstream fork (HabitFlow, 2026-08-24) who hit it with `flutter analyze` 0, 9994 tests passing, `validate.sh` 0 warnings, because the branch was unpushed and nothing in the repo parses `.github/workflows/`.

Here the exposure is narrower but real: `tests/ci/test_security_workflow.py:46,557` `yaml.safe_load`s both workflows (so a YAML syntax error is caught) and `:551` pins core job existence, but a dangling `needs:` is **valid YAML** and no test resolves the graph. Measured 2026-08-24 on this tree: `security.yml` 5 jobs, `validate.yml` 12 jobs, **0 dangling** — filed on a verified absence of a guard, not a live break.

**Read Plan**: Classification `quick-win`, Guardrails Mode `Quick`. Read: `bootstrap.md` (full), `shared-contracts.md` (full), `state_machine.md` (full), `tests/ci/test_ci_hardening.py` (structure), both workflow YAMLs. Skipped: `engineering_guardrails.md` (Token Leak block for quick-win), all `[Shipped]` specs (AC-28), `docs/architecture/` (quick-win skips §2b).

Phase chain: `/plan` → `/implement` → `/ship`.

**Target Files**: `tests/ci/test_ci_hardening.py` (only).

**AC-1**: a `needs:` target that is not a job in the same workflow fails the suite.
**AC-2**: both GitHub `needs:` forms are handled — `needs: job` (scalar) and `needs: [a, b]` (sequence). The live tree uses **only** the scalar form (6 edges, all `'changes'`), so the sequence arm has no natural coverage and needs a direct unit arm.
**AC-3**: a workflow that parses to no jobs, or a workflows dir that globs to no files, FAILS rather than passing vacuously.

**Non-goals**: `needs.<job>` references inside `if:` expressions (those evaluate to null — they do not trigger GitHub's whole-workflow parse rejection, which is the failure this row is about); backlog #181, #184, #185; any change to the workflows themselves.

**New-check rules do NOT apply** (ADR-006 `run_python_check` + `deploy.sh` whitelist + golden manifest): pytest-only, no validator check, nothing deployed downstream.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | completed | 2026-09-01T06:26:12Z | classified quick-win; backlog row advanced Pending → In Progress |
| plan | completed | 2026-09-01T06:32Z | 1 file, 2 test arms + 1 helper; RED proof planned for both `needs:` YAML forms |
| implement | completed | 2026-09-01T06:38Z | +51/-2 in one file; 3 RED proofs run and reverted |
| review | optional | — | quick-win fast-path |
| test | optional | — | inline evidence required |
| ship | completed | 2026-09-01T06:47Z | SSoT + rotation + backlog done; terminal post-archive evidence follows |

---

## Phase Summary

- bootstrap: backlog #183 taken as a quick-win — one new pytest arm in `tests/ci/test_ci_hardening.py`, no deployed files, no governance-surface edit. New-check rules (ADR-006 `run_python_check` + deploy whitelist + golden manifest) do NOT apply: pytest-only, nothing shipped downstream. ⚡ ACX
- plan: glob every `.github/workflows/*.yml` (not the two hard-coded paths — a future third workflow is then covered on arrival), resolve each job's `needs:` against that file's own job names, and refuse to pass on an empty file set or an empty jobs map. `yaml` via `pytest.importorskip` so an absent PyYAML reports SKIP, not assurance (CI pins `PyYAML==6.0.2`). Verify by mutation, both forms. Fast Lane | Confidence: 96% — high
- implement: `tests/ci/test_ci_hardening.py` only (+51/-2). `_needs_targets` normalizes scalar/sequence/None/non-str; `test_workflow_needs_targets_all_resolve` globs `*.yml`+`*.yaml`, refuses an empty file set and an empty jobs map, and resolves every edge against the same file's job names. All three failure arms proved RED before being trusted. No implementation-scope divergence.
- ship: implementation commit `447655b`; SSoT Ship History entry added at top and rotated at cap 10 (`Ship-chore-v1.8.21-release-2026-08-14` → `archive/ship-history-2026.md`); backlog #183 `In Progress → Shipped`; sequence 164→165. AC-30 routing check: 3 stale `pending` routing_actions exist in `docs/reviews/`, none in this task's domain (`Primary Domain Snapshot: none`) — not deferred by me, pre-existing and unrelated. Knowledge Nudge: declined — a new test guard changes no module behaviour, so no L2 line.

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-01T06:26:12Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-01T06:32:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-01T06:38:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-01T06:47:00Z

---

## External References

| Type | Path | Why |
|---|---|---|
| Backlog | `docs/specs/_product-backlog.md` #183 | task contract |
| ADR | `docs/adr/ADR-005-downstream-file-preservation-tiering.md` | `check_adr_coverage.py --paths tests/ci/test_ci_hardening.py` → exit 0, covered |
| Prior art | `tests/ci/test_security_workflow.py:46,551,557` | already `yaml.safe_load`s both workflows and pins core job existence — the gap is graph resolution only |

---

## Known Risk

- A guard that resolves `needs:` must handle both YAML forms (`needs: job` scalar and `needs: [a, b]` list) or it will false-pass on one of them. Mutation-proof both.
- The guard must fail on a *new* dangling edge, not merely pass today. Prove RED by injecting a dangling `needs:` before trusting green.
- Rollback: single file, `git checkout -- tests/ci/test_ci_hardening.py`. No workflow, validator, or deployed file is touched. Ship-side writes (SSoT entry + rotation, backlog row) revert with `git revert` of the ship commit.
- **Ship-time operator error, recorded rather than smoothed over**: the first guarded SSoT write passed the whole `snapshot` JSON blob as `--expected-sha` instead of its `sha256` field. The guard correctly refused (`status: conflict`, `reason: stale-sha`) — but the surrounding shell had already appended the rotated entry to `archive/ship-history-2026.md`, leaving `Ship-chore-v1.8.21-release-2026-08-14` in **both** files for one step. Converged by re-running the guarded write with the extracted sha; verified after: heading present once in the archive, zero `### Ship-chore-v1.8.21` headings in the SSoT, 10 entries newest-first. The guard did its job; the rotation half was not behind it.

---

## Decisions

none

---

## Conflict Resolution

none — `.agent/rules/skill_conflict_matrix.md:17` marks `karpathy-principles` × `verification-before-completion` **compatible**; `systematic-debugging`'s only listed partial-conflict is with `dispatching-parallel-agents`, which is not recommended here.

---

## Skill Notes

### kb-consult
Phases: plan
- Source: `kb-main` → `wiki/standards/05_testing-and-ai-pitfalls.md` (routed via `task_routing` key `測試 / AI 陷阱`; 1 page, `最常踩的雷` + `自我稽核 Checklist（測試）` sections only, not the 9,728-token page). Consumed as DATA.
- Applicable: (a) *邊界沒測* → the sequence `needs:` form has zero natural coverage in this tree; add a direct unit arm. (b) *斷言形同 `assert result is not None`* → assert the jobs map is non-empty, else a parse yielding nothing passes vacuously. (c) *只測 happy path* → the tree has 0 dangling edges today, so the guard is green on day one regardless of correctness; prove RED first.
- N/A (recorded, not applied): coverage-as-quality, testing implementation details, over-mocking, flaky/retry, TDD-as-silver-bullet, `getByRole`, Pact contract tests, static-analyzer strictness — none reach a structural YAML-graph assertion.

### karpathy-principles
Phases: plan, implement
- Checklist: touch exactly one file; do not "improve" neighbouring tests.

### verification-before-completion
Phases: implement, ship
- Checklist: prove the guard RED for BOTH `needs:` forms before trusting green; final evidence run must postdate the last Work Log write.

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Backlog write: `docs/specs/_product-backlog.md` #183 status `Pending → In Progress` at bootstrap, per `AGENTS.md §vNext State Model §Write Isolation` (bootstrap status-advance exception) and `bootstrap.md §1` step 5.
- SSoT write: `current_state.md` `Last Verified` refreshed to 2026-09-01 via `guard_context_write.py`, per `AGENTS.md §Non-ship SSoT write exceptions` (/bootstrap, that field only).

---

## Review Feedback

none

---

## Red Team Findings

none (quick-win — `red-team-adversarial` skip-when applies)

---

## Design Reference

none

---

## Observability

none

---

## Resume

Bootstrap complete, `/plan` next. Branch `test/workflow-job-graph-integrity-183` off `f250db1` (v1.8.25).

---

## Test Gate Results

none

---

## Evidence

**RED before GREEN — all three arms mutated against the live tree, each reverted in a `finally`:**

| mutation | expected | result |
|---|---|---|
| `needs: changes` → `needs: does-not-exist` (scalar form) | FAIL | exit 1 — `validate.yml: job 'deploy-smoke-test' needs 'does-not-exist', which is not a job in this workflow` |
| `needs: changes` → `needs: [changes, does-not-exist]` (sequence form) | FAIL | exit 1 — same assertion, reached through the list branch |
| new `zz-tmp-red-probe.yml` with `jobs:` empty | FAIL | exit 1 — `zz-tmp-red-probe.yml declares no jobs — a parse yielding nothing must not pass vacuously` |

The third probe doubles as proof the glob picks up a workflow file added **after** this test was written — the two hard-coded paths in `test_security_workflow.py` would not have seen it. `.github/` verified clean (`git status --short .github/` empty, `ls .github/workflows/` = 2 files) after every mutation.

**GREEN**: `pytest tests/ci/test_ci_hardening.py tests/ci/test_security_workflow.py -q` → **57 passed in 1.80s**.
`python .agentcortex/tools/check_text_integrity.py` → passed, 0 baseline exceptions.
`pytest .agentcortex/tests/test_backlog_validation.py` → exit 0 (covers the #183 status advance).

**Not run, stated rather than implied**: the full local CI-equivalent suite (916 tests). Measured on this box at ~35 tests / 15 min — 6h+ — consistent with the standing precedent that a local full repeat is waste when CI runs the same set plus three Windows shards. PR CI is the authoritative full-suite evidence.
