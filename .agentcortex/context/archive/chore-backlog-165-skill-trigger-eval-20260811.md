# Work Log: chore/backlog-165-skill-trigger-eval

## Header

- Branch: `chore/backlog-165-skill-trigger-eval`
- Classification: `quick-win`
- Classified by: `claude-opus-5[1m]`
- Frozen: `2026-08-11`
- Created Date: `2026-08-11`
- Owner: `luvseldom@gmail.com`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `44b2e33`
- Checkpoint SHA: `44b2e33`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `146`

---

## Session Info

- Agent: `claude-opus-5[1m]`
- Session: `2026-08-11 UTC`
- Platform: `claude-code`
- Files Read: `14`

---

## Task Description

Split the unblocked half of backlog #79 / issue #254 (skill effectiveness eval harness) into its own tracked, pickup-ready unit: a new backlog row #165 + GitHub issue #398 scoped to trigger-accuracy only, plus a scope-narrowing note on row #79 so the two halves cannot be confused. Motivated by a daily-triage analysis of #254 that found the trigger-accuracy half depends on neither #77 nor #78.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-11 | classified quick-win; SSoT + backlog read |
| plan | done | 2026-08-11 | split decision: row #165 + issue #398; row #79 narrowed |
| implement | done | 2026-08-11 | backlog rows added/edited; issue #398 created |
| review | skipped | 2026-08-11 | optional for quick-win |
| test | skipped | 2026-08-11 | optional for quick-win; validator run recorded as evidence |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-08-11 | PR opened; evidence below |

---

## Phase Summary

**bootstrap** — Task arrived from a daily-triage run on issue #254. Read SSoT (`current_state.md`, seq 146) and `docs/specs/_product-backlog.md`. Classified `quick-win`: one tracked file (`_product-backlog.md`, a sanctioned spec-intake write surface), no code or governance-rule change.

**plan** — Decided the disposition explicitly rather than deferring: **refine-to-precise**. #254's stated dependencies (#77/#78) gate only the effectiveness/A-B half; the trigger-accuracy half is deterministic against `.agentcortex/metadata/trigger-registry.yaml` and is unblocked today. Splitting it keeps the blocked work honestly blocked while making the actionable work pickable by the next agent without re-deriving the analysis.

**implement** — Created issue #398 with frozen scope, acceptance criteria, and the three repo-specific implementation traps (ADR-006 run_python_check routing; deploy whitelist ×2 + golden manifest; on-demand invocation to avoid a second standing coverage WARN). Added backlog row #165 (self-contained: evidence, contract source, deliverable, naming discipline, traps) and narrowed row #79 to the effectiveness half with the metrics-provenance open question recorded inline.

**ship** — Both validators `pass=117 warn=4 fail=0 skip=2` (exact parity). PR #399 merged `e358c1a`, CI green with no failures. SSoT sequence 146→147, Ship History rotated at cap 10 (review-gate-findings-backlog → `archive/ship-history-2026.md`). Archived to `.agentcortex/context/archive/chore-backlog-165-skill-trigger-eval-20260811.md`.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-11T14:30:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-11T14:34:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-11T14:36:18Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-11T15:37:32Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | — |
| ADR | — | — |
| Issue | https://github.com/KbWen/agentic-os/issues/254 | parent — effectiveness half, stays blocked on #252/#253 |
| Issue | https://github.com/KbWen/agentic-os/issues/398 | new — trigger-accuracy half, unblocked (backlog #165) |
| PR | — | opened at ship |

---

## Known Risk

- **Naming drift**: a future agent could implement #398 and mark #254 satisfied. Mitigated by an explicit "does NOT close #79/#254" line in both the issue body and backlog row #165.
- **Split rot**: two rows describing one topic can diverge. Mitigated by row #79 carrying the split note and the pointer to #165/#398, so either entry point reaches the whole picture.

---

## Decisions

### D-1: Split the trigger-accuracy half out of #254 rather than deferring

- Decision: refine-to-precise — new backlog row #165 + issue #398 scoped to trigger accuracy; #254/#79 narrowed to the effectiveness half.
- Reason: #254's dependency label (#77/#78) was over-broad. It gates A/B cost measurement, not activation scoring, which `trigger-registry.yaml` already makes deterministic. Leaving them merged kept actionable work invisible behind a blocked issue.
- Alternatives: (a) leave everything in #254 until #252/#253 land — rejected, hides an unblocked P2 and leaves `AGENTS.md §Skill Activation Triggers` at zero coverage indefinitely; (b) implement Increment A now — out of scope for this unit and not authorized.
- Impact: one new tracked row + one public issue. No runtime, workflow, or governance-rule change; engine behavior unchanged for adopters.
- → local

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Task originated from a scheduled daily-triage run; the triage step itself was report-only (comment on #254) and made no file change. This unit is the follow-on the user authorized in the same session.
- `_product-backlog.md` written outside `/ship` under the AGENTS.md spec-intake/ship backlog exception.
- **Gate receipt timestamp provenance** (corrected after a refute pass caught fabricated values): the implement receipt is the exact author time of commit `6d9665b` and the ship receipt the exact author time of `e397c7d`. The bootstrap and plan receipts are **bounded estimates** — no wall clock was captured at the time, and they are known to fall between session start and the 14:36:18Z implement commit. The first draft carried round `T00:00/00:10/00:25/00:40` placeholders, ~14 hours before the real work; that is a fabrication, not an estimate, and is recorded here rather than silently overwritten.
- **Ship-record branch has no Work Log of its own.** The state writes (SSoT, Ship History rotation, archival, INDEX append) were made on `chore/ship-record-165`, whose `<worklog-key>` would be `chore-ship-record-165`; no such log was created, so this log — keyed to `chore/backlog-165-skill-trigger-eval` — carries the ship evidence for both branches. Per `AGENTS.md §vNext State Model` the missing log is recoverable rather than a gate failure, and the same pattern is visible on prior ship-record branches (`chore/ship-143-record`, `chore/ship-152-record`, `chore/ship-163-164-record`), which makes it a systemic gap in the ship-record convention rather than a one-off. Surfaced by the refute pass; recorded, not papered over.

---

## Review Feedback

none

---

## Red Team Findings

Two fresh-context read-only passes were run against the merged row #165, issue #398, and the unmerged ship record: a **pickup simulation** (can a context-free agent act on these artifacts?) and a **refute-only (第十人) pass**. Every finding below was re-verified by the primary against ground truth before adoption — the subagents' reports were not taken at face value.

**Adopted — content corrections, applied before merge:**

- **The "zero behavioral evidence" claim was overstated.** `.agentcortex/tools/trigger_runtime_core.py` already implements `values_match:860` / `skill_is_candidate:884` / `skill_is_activated:918`, and `.agentcortex/tests/test_lifecycle_skill_activation.py` collects **53 tests** asserting registry-driven activation (verified: `pytest --collect-only -q` → `53 tests collected`). Deterministic *resolution* evidence exists; the real gap is free-text prompt → `intent_patterns` matching and near-miss negatives. Corrected in row #165, issue #398, and the Ship History entry.
- **Dotted-path notation was wrong for 3 of 5 fields.** Only `intent_patterns` and `classification` sit under `detect_by:`; `phase_scope`, `load_policy`, and `block_if_missed` are entry-level siblings (verified by indentation at `trigger-registry.yaml:71-97`).
- **AC-1 was unsatisfiable as frozen.** "≥1 near-miss negative per registry skill" is impossible where there is no `intent_pattern` to paraphrase: `intent_patterns: []` at `:17`, `:43`, `:110` — and `:110` is `verification-before-completion`, a real `kind: skill` with `block_if_missed: true` whose activation runs off `phase_conditions: [completion-claim]`, not prompt text. AC-1 now carves those out with a different negative shape.
- **Scope delta 16 vs 14 resolved**: the registry has 16 entries but exactly 14 `kind: skill` (verified `grep -c "^    kind: skill"` → 14); the other two are `kind: workflow` / `kind: policy`.
- **The determinism claim collided with the named helpers.** `_score_case:136` scores a transcript and has no `expect_activation` branch, and `_run_agent:197` is a live-model subprocess — so "deterministic, no agent runs" and "reuse these helpers" pointed opposite ways, while repeated-run aggregation was pushed out of scope against an exit-non-zero requirement. The scoring mechanism is now an explicit up-front decision in #398 rather than an implicit contradiction.
- **#143 overlap.** Backlog row #143 already owns the same 28/45 tier-blind metric and lists "backfill cases for load-bearing rules" as a pickup path — two rows could have been picked up independently to clear one WARN. Cross-reference added both ways.
- **Path precision**: `deploy.sh` is `.agentcortex/bin/deploy.sh` (a decoy `.agentcortex/tools/demo_deploy.sh` exists); `:946` anchors the member line inside the array opened at `:928`, not the array head.
- Fabricated gate timestamps, the misquoted `git diff --stat`, the missing `pass=118 warn=3` receipt, the ship-record branch's missing Work Log, and the Ship History heading blank-line drift — all corrected; see `## Drift Log` and `## Evidence`.

**Attacked and survived (recorded so they are not re-litigated):**

- **The #252/#253 split itself.** `#252` defines a Task→Step schema and `#253` a task capsule + read-only reviewer; neither produces an input a per-prompt activation check consumes. #252's claim that it "gates the skill-effectiveness evaluation" is a self-assertion with no mechanism behind it. The split stands.
- **Ship-record mechanics.** Chain intact; `Update Sequence: 147`; Ship History exactly 10 entries; the rotated entry byte-identical to what was removed; both guard receipts' `new_sha` match the on-disk sha256 of their targets, proving the SSoT went through `guard_context_write.py` rather than a hand edit.
- **CI-before-merge** (this repo's own #270 incident class): every job in both runs completed before PR #399's `mergedAt`. The merge did not front-run CI.

**Accepted, not fixed:** the new `INDEX.jsonl` record writes `"specs": ["-"]` where the file's 104 other entries use `[]`. The ledger is append-only and hash-chained — rewriting the line to fix a cosmetic placeholder would break tamper-evidence for a NIT. Left as-is deliberately.

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

- Zero-coverage claim (executed, not read): `python .agentcortex/tools/run_governance_eval.py --coverage` → `Rule inventory: 45 MUST-bearing section(s)` / `Cases evaluated: 28` / `Zero-coverage rules: 28`, listing `AGENTS.md §Skill Activation Triggers`.
- Contract-source claim: `.agentcortex/metadata/trigger-registry.yaml` has 16 `- id:` entries; `.agents/skills/*/SKILL.md` count = 14; `test-driven-development` `detect_by` block at `:80-85`.
- Backlog edit is additive and bounded: row count 99 → 100; `git show --stat e358c1a` → `1 file changed, 2 insertions(+), 1 deletion(-)` (row #165 added, row #79 narrowed).
- Validators after the final archival write (look-timing contract): `validate.ps1` → `Summary: pass=118 warn=3 fail=0 skip=2`, up from the pre-archival `pass=117 warn=4` as the `shipped work logs still in active work/ directory` WARN converted to a PASS. Both validators were run pre-archival at `117/4` with exact parity; the post-archival run is `validate.ps1` only (`validate.sh` takes ~50 min on this box and was run at the pre-archival state).
- Full CI-equivalent suite after archival: `pytest tests/ci/ tests/guard/ .agentcortex/tests/` → `1 failed, 876 passed in 2975.14s`. The single failure (`test_validator_worklog_family_skip.py::test_fresh_install_announces_the_absent_family_and_regains_it`) is a local PATH artifact — `bash` resolves to the WSL stub, so `deploy.sh` never ran; re-run with Git Bash ahead on PATH → `5 passed in 39.83s`.
- Adversarial verification of this unit (2 fresh-context read-only passes) is recorded in `## Red Team Findings`.
- Validator: see PR body for the `validate.sh` summary line captured at ship.
