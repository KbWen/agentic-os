# Work Log: fix/governance-scope-consistency

## Header

- Branch: `fix/governance-scope-consistency`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-09-20`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `851dcca0bf5af7a257e0a632590202d6bb01d942`
- Checkpoint SHA: `4635abebbbd9fe99d5e108ebab3c44135dff82b6`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `172`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-09-20 06:17 UTC`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)` — §13 heading-scoped read pending at /implement (governance-path edit exemption, bootstrap §0)
- Override: `none` (no AGENTS.override.md at project root or ~/.agentcortex/)
- Downstream-Capabilities: `.agentcortex/context/private/downstream-capabilities.yaml (0 skills, subagent_policy=read-only default, knowledge_sources: kb-main→OK@328b30ecb33b)`
- kb-consult: not activated — task is framework-internal governance wording; no `task_routing` domain maps to it.
- Files Read: `14`

---

## Task Description

Fix three verified governance-doc inconsistencies surfaced by the 2026-09-20 Gemini project review (`docs/reviews/2026-09-20-project-review-handoff-to-claude.md`), after Claude re-verified each against the repo:

1. `routing.md` Command Registry overstates `/review` + `/test` as required for `quick-win` (contradicts `engineering_guardrails.md §10.2` and `state_machine.md:27`), and omits `hotfix` from `/plan` scope (contradicts `state_machine.md:38` + README hotfix path).
2. `CLAUDE.md` Startup Step 2 routes `tiny-fix` to Step 5, which then tells it to skip — a dead end with no execution guidance.
3. `.agent/workflows/ship.md` frontmatter `description` asserts a handoff gate for all tasks; `state_machine.md:7` exempts `quick-win`/`hotfix`.

Docs-only consistency repair. No engine/behavior change. Read Plan: SSoT (read), bootstrap.md (read), state_machine.md (read), guardrails §10.2/§10.3/§10.4 (heading-scoped), worklog template (read); skipped: full guardrails (quick-win Token Leak block), shipped specs (AC-28).

Phase chain: `/bootstrap → /plan → /implement → /ship` (review/test optional per §10.2 — the very rule this unit is correcting).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-20 | quick-win, classification frozen |
| plan | done | 2026-09-20 | 3 files, 4 lines |
| implement | done | 2026-09-20 | 3 files / 5 lines |
| review | done | 2026-09-20 | user-requested (optional for quick-win) |
| test | done | 2026-09-20 | CI-equivalent suite + downstream simulation |
| handoff | n/a | — | exempt for quick-win (state_machine.md:7) |
| ship | done | 2026-09-20 | commit 4635abe |

---

## Phase Summary

- ship: PASS. Commit `4635abe`. SSoT Ship History entry added + rotated at cap 10 (`Ship-test-workflow-job-graph-integrity-183-2026-09-01` -> `archive/ship-history-2026.md`). Sequence 172->173. Archive: `.agentcortex/context/archive/fix-governance-scope-consistency-20260920.md`.
- test: CI-equivalent suite 950 passed / 1 skipped / 0 failed; validate.ps1 fail=0; downstream deploy + hotfix A/B demonstrations recorded in §Evidence. 0 tests added (no-test rationale in §Test Gate Results). | Confidence: 95% — high
- review: PASS, 0 issues, security clean, Red Team not triggered (quick-win). Scope 3 files / 5 lines. §13 net-add justification recorded for CLAUDE.md; ship.md is net-negative.
- plan: 3 target files / 4 changed lines. Key decisions: ship.md description kept near-current length (R1 ratchet), CLAUDE.md adjacent parentheticals left alone (karpathy surgical), routing.md `/plan` row added to scope because it is the same registry-vs-§10.2 defect one row up. Mode: Normal. | Confidence: 95% — high (all three defects re-verified against the repo this session; only open unknown is ship.md token cost, which step 4 measures)
- bootstrap: classified `quick-win` (governance-path edit — `CLAUDE.md` + `.agent/workflows/*` — escalated above tiny-fix per bootstrap §0). ADR coverage exit 0 (ADR-005, ADR-007 cover `routing.md`). Lock created. 2 skills matched, no conflict.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T06:17:54Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T06:25:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T06:41:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T07:05:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T08:35:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T08:50:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | `docs/reviews/2026-09-20-project-review-handoff-to-claude.md` | Gemini source review; items 1.1, 1.3, 1.4 adopted |
| ADR | `docs/adr/ADR-005-downstream-file-preservation-tiering.md` | covers `routing.md` |
| ADR | `docs/adr/ADR-007-downstream-capability-declaration-seam.md` | covers `routing.md` |

---

## Known Risk

- **R1 (live, measured)**: `ship.md` IS counted by `analyze_token_lifecycle.py` (`PHASE_WORKFLOW_MAP["ship"]`, tool:36/164). The aggregate ceiling `test_aggregate_current_total_stays_under_355k` has only **113 tokens** headroom (354887/355000, measured this session). Any frontmatter growth is charged per scenario. Mitigation: keep the new description close to the current 68 chars and re-run the analyzer before commit; shorten if over. Rollback: `git checkout -- .agent/workflows/ship.md`.
- **R2 (resolved)**: `.agent/workflows/**` is a `guard_policy.protected_paths` glob (`.agent/config.yaml:190`) — `routing.md` + `ship.md` writes go through `guard_context_write.py` (snapshot → edit temp → write `--expected-sha`). `CLAUDE.md` is NOT protected (only `AGENTS.md` is) → direct edit.
- **R3 (cleared)**: no pinned assertion covers the edited lines. `tests/guard/test_classification_escalation.py:246` scopes to routing.md §4's escalation clause, not the §5 Command Registry; `validate.sh:2731-2743` checks only `canonical: true` + `AGENTS.md outranks`; `check_command_sync.py` validates `.claude/commands/` dispatch directives, not registry scope columns; `"Final delivery and archival"` has no mirror in the repo. `check_text_integrity.py` is an encoding check — edits stay UTF-8.
- **R5 (audited, cleared)**: Global Lesson `[scope-expansion][HIGH]` fires on this change — the `/plan` registry row widens tier scope to include `hotfix`. Audited `plan.md` body per that lesson: it already handles hotfix at both decision points (`plan.md:37` proceed-directly, `plan.md:55` Spec-Gate exemption). No body step assumes the narrower tier set.
- **R4 (cleared)**: cross-platform parity — `GEMINI.md` and `.codex/` carry no equivalent startup-step block, so the CLAUDE.md defect is Claude-local and the fix does not need mirroring.

---

## Decisions

none

---

## Conflict Resolution

none — `karpathy-principles` × `verification-before-completion` = `compatible` (skill_conflict_matrix.md:17).

---

## Skill Notes

### karpathy-principles (plan)
- Checklist: assumptions stated; simplest viable approach; no scope crossing.
- Constraint: surgical — every changed line traces to the request; pre-existing redundancy is *mentioned*, not deleted.
- Applied: rejected the adjacent cleanup of CLAUDE.md Steps 3–5 "(Skip for tiny-fix.)" parentheticals — they become redundant but not wrong, so they stay (noted, not deleted). Also rejected Gemini's longer "SSoT update" wording for ship.md as unneeded char spend against R1.

---

## Drift Log

- Phase path extended beyond the quick-win fast-path at the user's explicit request (review + test + usage-scenario simulation before ship). Classification unchanged; `IMPLEMENTING -> REVIEWED -> TESTED -> SHIPPED` is legal for quick-win per `state_machine.md:26`.
- Review Snapshot Routing Check (AC-30): `docs/reviews/2026-07-01-governance-premortem.md` carries 4 `status: pending` routing actions, all targeting `docs/architecture/document-governance.md`. Primary Domain Snapshot is `none` and no pending action targets this task's files, so the check does not bind. Not resolved here, not deferred silently — recorded.
- Source review `docs/reviews/2026-09-20-project-review-handoff-to-claude.md` is intentionally left untracked in this unit: committing it would push the diff past the 200-line quick-win scope ceiling (`state_machine.md:51`), and it contains claims this unit refuted, so it needs an adjudication header before it belongs in the repo. Routed to the user as a follow-up decision.
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Recovered stale Work Log lock on 2026-09-20T07:50:46.189166+00:00; prior_owner=KbWen; prior_session=2026-09-20T06:17:54Z; reason=stale-time; lock=fix-governance-scope-consistency.lock.json

---

## Review Feedback

- Burden of Proof (quick-win behavioral): AC-1 routing scope / AC-2 CLAUDE.md tiny-fix / AC-3 ship.md description all PROVEN; AC-4 (no regression) routed to /test.
- Scope check: 3 files changed, all in the plan. `.agentcortex/context/.guard_receipt.json` also changed — generated by `guard_policy.legacy_receipt_mirror`, tracked and committed by prior ships (386d522, a45f4f6). Not scope creep.
- §13 Deletion-First: routing.md/ship.md are not always-loaded surfaces. `CLAUDE.md` is (net +30 chars) — **net-add justification**: the old line was a dead pointer ("skip to Step 5" → Step 5 says skip), so the added chars replace a non-functional instruction with an executable one. `ship.md` is net **-4 chars**. No new MUST/NEVER/gate → ADD-Gate not triggered, no signal tier needed.
- Security: `scan_credentials.py` on the 3 changed files → exit 0, no findings. Docs-only, no code paths, no error handling, no dependencies → §5.2a observability and dependency checks n/a.
- Red Team: not triggered (`quick-win` is in the skill's Skip-when column).
- Regression check: no callers break. `tests/guard/test_classification_escalation.py:246` scopes to routing.md §4, not §5; `validate.sh:2731-2743` pins only `canonical: true` + `AGENTS.md outranks`; `check_command_sync.py` checks `.claude/commands/` dispatch directives; the old ship description string had no mirror.
- Sizing: 5 changed lines, far under the 100-line review-effectiveness threshold.

---

## Red Team Findings

none

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

- Test Files: none added. **No-test rationale**: the change is prose on three governance surfaces. The only test that could pin it would assert the wording itself, which `current_state.md:150` explicitly rejects ("the obvious one pins prose, which the brief forbids"), and a real drift guard needs a named runtime consumer per `repo-gotchas §16`. Evidence is the reproducible A/B below instead.
- `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q` (CI-equivalent, full — matches `.github/workflows/validate.yml:302`): **950 passed, 1 skipped, exit 0** (4967s). Collected 951 via `--collect-only`.
- Coverage delta: 0 new tests, 0 removed. 951 collected before and after.

---

## Evidence

- Diff: 3 files / 5 lines. `git diff --numstat`: routing.md 3+/3-, ship.md 1+/1-, CLAUDE.md 1+/1-.
- Token ratchet: `analyze_token_lifecycle.py` aggregate 354887 → **354881** (ceiling 355000). Headroom 113 → **119**. The ship.md description fix is net-negative; the `(state_machine.md)` pointer was dropped as redundant with `ship.md:10`.
- Governance tools: `check_command_sync.py` 28 commands + 2 aliases PASS · `check_lifecycle_frontmatter.py` 14 PASS · `run_skill_eval.py` 19 known gaps = baseline 19 (unchanged) · `scan_credentials.py` on the 3 changed files exit 0.
- **Demonstration — downstream install**: `bash .agentcortex/bin/deploy.sh <clean-git-dir>` into an empty repo. All three corrected lines present in the deployed tree; downstream `validate.sh` → `pass=86 warn=1 fail=0 skip=8`.
- **Demonstration — A/B on the `/plan` row** (the only change with a hard-failure consequence). Synthetic hotfix Work Log in the deployed tree:
  - old-table behavior (no plan receipt) → `incomplete gate receipts in hotfix-old-routing.md: missing plan (classification:hotfix)`, `fail=1`, integrity check FAILED.
  - new-table behavior (plan receipt present) → 0 incomplete, `fail=0`, integrity check passed.
  - quick-win with no review/test receipts → 0 incomplete, confirming the new "optional for quick-win" wording matches `validate.sh:1583-1585`. (That fixture's own summary showed 1 unrelated FAIL: the minimal log has no `## Evidence` section.)
