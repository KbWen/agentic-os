# Work Log: arch/frozen-spec-lifecycle

## Header

- Branch: `arch/frozen-spec-lifecycle`
- Classification: `architecture-change`
- Classified by: `parent-session (pinned — do not downgrade)`
- Frozen: `2026-06-22`
- Created Date: `2026-06-22`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `implement`
- Checkpoint SHA: `8102cf8` (post-implement commit)
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-lifecycle`
- SSoT Sequence: `87`

---

## Session Info

- Agent: `claude-sonnet-4-6`
- Session: `2026-06-22 UTC`
- Platform: `claude-code`
- Files Read: `12`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §5 (testing), §12 (implement), §13 (governance change)

- Agent: `Claude (Opus 4.8)` — orchestrator/reviewer/shipper
- Session: `2026-06-22T15:45:00+00:00`
- Platform: `Claude Code`
- Role: delegated implement to acx-implementer (commit 8102cf8); ran INDEPENDENT acx-reviewer (PASS); handles review→test→handoff→ship gates. Lock owner `claude-t1-ship`.

---

## Task Description

Fix a pre-existing lifecycle defect: a legal `status: frozen` spec created before /ship causes the SSoT Spec Index completeness validator to FAIL (Leg A), yet the only instructed remedy (writing to `current_state.md`) is forbidden before /ship by Write Isolation (Leg B), and the workflow docs contradict each other (Leg C). Adopt Option B: narrow the validator to require index entries only for `shipped`/`living` specs — preserving Write Isolation single-writer invariant. Requires ADR-010.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | complete | 2026-06-22 | parent session + this session |
| plan | complete | 2026-06-22 | pinned by parent session |
| implement | complete | 2026-06-22 | commit 8102cf8 |
| review | complete | 2026-06-22 | independent acx-reviewer (fresh-context) → PASS; AC-1..6 PROVEN; 1 LOW accepted (status regex not end-anchored — fixing risks inline-comment regression; latent-only, no such status value exists) |
| test | complete | 2026-06-22 | 9 non-slow + 4 behavioral (sh+ps1 AC-1/AC-2) passed |
| handoff | complete | 2026-06-22 | in-session ship; resumable summary in ## Resume |
| ship | in-progress | 2026-06-22 | parent session claude-t1-ship |

---

## Phase Summary

- bootstrap: architecture-change classification pinned by parent session; defect independently verified (Leg A/B/C); Option B selected.
- plan: 7 target files identified; ADR-010 + spec + validator changes + workflow reconciliation + test addition + SSoT ADR entry.
- implement: 8 files changed (validate.sh, validate.ps1, spec.md, plan.md, ADR-010, spec/frozen-spec-lifecycle.md, current_state.md, tests); pytest 9 non-slow + 4 behavioral passed; validate.ps1 pass=102 CI-equiv; commit 8102cf8.

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-22T00:00:00+08:00
- Gate: plan | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-22T00:00:00+08:00
- Gate: implement | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-22T16:00:00+08:00
- Gate: review | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-22T15:30:00+00:00
- Gate: test | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-22T15:35:00+00:00
- Gate: handoff | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-22T15:45:00+00:00

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/frozen-spec-lifecycle.md | new spec (this task) |
| ADR | docs/adr/ADR-010-frozen-spec-lifecycle.md | new ADR (this task) |
| Issue | — | — |
| PR | — | — |

---

## Known Risk

- cross-platform EOL: validate.sh is CRLF on Windows checkout; use Edit tool (not shell append) per [cross-platform-eol][HIGH] Global Lesson
- sh/ps1 parity: both validators must be verified by running, not reading — parent session instruction
- Token lifecycle ceiling: adding new spec/ADR adds ~few-hundred tokens; not near the 353k ceiling
- Rollback: revert the branch commits (additive ADR/spec + narrowed validator + reconciled docs)

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- ADR Index write (direct, sanctioned /adr exception): adding ADR-010 entry to `.agentcortex/context/current_state.md` ADR Index — logged here per AGENTS.md non-ship SSoT write exceptions. Update Sequence NOT bumped (parent handles at /ship).

---

## Design Reference

none

---

## Observability

none

---

## Resume

**Handoff summary (architecture-change gate):**
- Doc path: `docs/adr/ADR-010-frozen-spec-lifecycle.md` (decision) + `docs/specs/frozen-spec-lifecycle.md` (AC-1..6, status:draft until ship)
- Code path: `validate.sh`/`validate.ps1` (skip draft|frozen|cancelled), `spec.md`/`plan.md` reconciled, `current_state.md` ADR Index +1; tests in `tests/ci/test_validator_false_positives.py`
- Work log path: this file (`.agentcortex/context/work/arch-frozen-spec-lifecycle.md`)
- State at handoff: implement+review(PASS)+test(PASS) done; ship in progress (commit `8102cf8`). On ship: bump seq 87→88, add Ship History entry, flip spec `status: draft→shipped`, PR+CI+merge+archive.
- Independent review: acx-reviewer PASS; 1 LOW accepted (regex end-anchor — fixing risks inline-comment regression).

---

## Evidence

- A/B repro: behavioral tests confirmed — status:frozen spec NOT in index → validate.sh PASS, validate.ps1 PASS; status:shipped NOT in index → FAIL (4 slow tests passed, 671s)
- validate.ps1 on framework repo: pass=102 warn=12 fail=2 (pre-existing gitignored worklog FAILs); [PASS] SSoT Spec Index completeness: all shipped/living specs are indexed
- validate.sh: behavioral tests confirmed correct behavior (sh skip pattern verified structurally + 2 behavioral sh tests passed AC-1/AC-2)
- pytest tests/ci/test_validator_false_positives.py -m "not slow": 9 passed (3 new ADR-010 structural + 6 prior)
- pytest (slow behavioral): 4 passed — test_adr010_frozen_spec_not_indexed_does_not_fail_sh, test_adr010_shipped_spec_not_indexed_fails_sh, test_adr010_frozen_spec_not_indexed_does_not_fail_ps1, test_adr010_shipped_spec_not_indexed_fails_ps1
- git diff --check: clean (CRLF normalization warning only — not an error)
- Checkpoint SHA: 8102cf8 (post-commit)

---

## Plan (from parent session — pinned)

Target Files:
1. `.agentcortex/bin/validate.sh` — narrow skip condition: draft + frozen + cancelled (line ~1983)
2. `.agentcortex/bin/validate.ps1` — same change, parity (line ~1817)
3. `.agent/workflows/spec.md` — remove SSoT write instructions at lines ~15 and ~44; add note that Spec Index written by /ship
4. `.agent/workflows/plan.md` — change Frozen Spec Pre-Check to read disk status, not Spec Index tag (line ~153)
5. `docs/adr/ADR-010-frozen-spec-lifecycle.md` — new ADR (mirror ADR-009 house style)
6. `docs/specs/frozen-spec-lifecycle.md` — new spec with AC-1 through AC-6, status: draft
7. `.agentcortex/context/current_state.md` — add ADR-010 entry to ADR Index only (sanctioned /adr exception)

Steps:
1. Create spec (status: draft — do not trip own validator)
2. Create ADR-010
3. Edit validate.sh — narrow skip condition
4. Edit validate.ps1 — narrow skip condition (parity)
5. Edit spec.md — remove SSoT write instructions, add /ship note
6. Edit plan.md — fix Frozen Spec Pre-Check to read disk
7. Edit current_state.md — add ADR-010 entry to ADR Index
8. Add regression tests
9. Run both validators; confirm parity + CI-equiv fail=0
10. Commit

AC Coverage:
- AC-1: frozen pre-ship spec passes validator → validate.sh/ps1 change
- AC-2: shipped spec unindexed still FAILs → test (b)
- AC-3: spec.md/spec-intake.md reconciled → spec.md edit
- AC-4: plan.md reads disk status → plan.md edit
- AC-5: sh/ps1 parity → running both
- AC-6: no AGENTS.md change → confirmed
