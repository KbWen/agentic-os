# Work Log: fix/deploy-cp-flag-queue

## Header

- Branch: `fix/deploy-cp-flag-queue`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `2026-10-17`
- Created Date: `2026-10-17`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `2541054`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `deploy`
- SSoT Sequence: `193`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-17 10:21 UTC` (8ab306f9)
- Platform: `claude-code`

---

## Task Description

Backlog #221: `CP_FLAG=-i` lets `cp` read its answer from the deploy queue (a record is lost from deploy + manifest); `CP_FLAG=-n` on an update reports `[OVERWRITE]` and counts a copy that `cp -n` skipped. Fix both in `deploy.sh` with focused regressions. Handoff source: `docs/reviews/2026-10-15-token-lightweight-triage.md` §Claude implementation handoff.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-17 | quick-win: 1 script + 1 test file, backlog Tier quick-win |
| plan | done | 2026-10-17 | inline plan below |
| implement | done | 2026-10-17 | fd-3 loops + post-copy check |
| review | done | 2026-10-17 | self-review + pre-mortem |
| test | done | 2026-10-17 | 13 cp_flag + 90 deploy-suite |
| ship | done | 2026-10-17 | SSoT 193->194, backlog #221 Shipped |

---

## Phase Summary

- bootstrap: quick-win (deploy.sh behaviour + focused tests; no ADR-level contract change — ADR-005 promises are what is being restored). Both failures reproduced on 2541054 (see Evidence).
- plan: Target `.agentcortex/bin/deploy.sh`, `tests/ci/test_deploy_tiering.py`. (1) Read the batch queue loop and the per-file skills `find` loop on fd 3 so `cp -i` keeps the caller's stdin. (2) Core-update and scaffold-unmodified-update copies go through one helper that, only for `-n`/`-i`, checks the post-copy hash; a skipped copy prints `[KEPT]`, counts `COUNT_KEPT` (not updated/overwritten), and records the old manifest hash so the next deploy still sees the difference. Risk: post-copy hash cost — limited to `-n`/`-i`. Rollback: revert the commit. Non-goal: first-install branch (#188 already truthful), deploy.ps1 (no CP_FLAG).
- implement: `deploy.sh` +`_cp_framework_version` (cp, then for -n/-i only compare the normalized post-copy hash; explicit `exit 1` on cp failure because the `if !` caller suspends set -e) and `_record_kept` (`[KEPT]`, `COUNT_KEPT`, previous manifest hash). Core-update and scaffold-unmodified-update use it; `[OVERWRITE]`/force-updated count now print only after a delivered copy. Queue second pass and per-file skills loop read on fd 3. Summary gains `/ N kept by CP_FLAG` when N>0. Tests: `test_cp_flag_i_reads_answers_from_stdin_not_the_deploy_list` (batch/per-file × y/n × core/skill, one prompt per run) and `test_cp_flag_n_update_reports_and_records_only_what_was_delivered` (batch/per-file; a later default deploy still force-updates with backup).
- review: Scope = deploy.sh + test file only. Pre-mortem: (1) `cp -n` exit status on coreutils 9.x/BSD — unchanged vs baseline (set -e aborted there too). (2) fd 3 unused elsewhere in deploy.sh. (3) kept core with no prior manifest hash records src hash → next deploy backs up + overwrites, same as before. (4) `.gitkeep.md` CP_FLAG copy is a fixed `for` loop — no stdin leak, left as is. (5) Piped stdin: GNU `cp -i` buffers the whole pipe, so tests use one prompt per run; real terminals are line-buffered. Verdict PASS.
- test: mutation-checked both fixes (see Evidence); full deploy suites green; validate.sh fail=0.
- ship: PASS; shipped in the fix commit on fix/deploy-cp-flag-queue (same PR as the 2026-10-15 queue docs and #230, owner choice 2026-10-17 chat); archive `fix-deploy-cp-flag-queue-20261017.md`; SSoT 193->194; Ship History rotated at cap 10.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T10:21:23Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T10:23:04Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T10:31:40Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T10:36:30Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T10:37:12Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T11:23:12Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog.md | row #221; quick-win, no spec |
| ADR | docs/adr/ADR-005-downstream-file-preservation-tiering.md | promises restored |
| Issue | — | — |
| PR | — | — |

---

## Known Risk

- MSYS spawn cost of the post-copy hash — scoped to `CP_FLAG=-n|-i` only.

---

## Decisions

### D-1: a skipped copy keeps the previous manifest hash
- Decision: `[KEPT]` records the old manifest hash (src hash when none).
- Reason: the next deploy must still see the difference; recording src would make an unmodified kept file look locally edited.
- Alternatives: record src hash (spurious `.acx-local` next run); record live hash (loses edit detection).
- Impact: deploy.sh only. → local

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Pending intake docs (`_product-backlog.md`, triage review, archived main log) carried uncommitted from main; not part of this unit.
- Per-file path has the same stdin leak (skills `find` loop feeds `cp -i`); fixed in the same change — same promise, same mechanism.
- Lock refreshed only at bootstrap and then at test entry (implement/review entries missed the `ensure` call; caught by validate.sh lock-phase WARN, re-run 10:37Z).
- Implement/review receipt timestamps reconstructed from the session timeline, not read from the clock at phase end.

---

## Review Feedback

none

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

none

---

## Evidence

- Baseline repro (2541054, minimal source, 1 core collision): `-i` + stdin `y` → rc=0, manifest 12→11 rows (missing `security_guardrails.md`), rule NOT updated. `-n` → rc=0, live kept, stdout `[OVERWRITE] .../engineering_guardrails.md`, summary `1 locally-modified core force-updated`.
- After fix, same repro: `-i` rows 12→12, rule updated; `-n` → `[KEPT] ... a copy is at ...acx-local`, `Summary: 11 updated / 0 skipped / 1 kept by CP_FLAG`.
- `pytest tests/ci/test_deploy_tiering.py -k cp_flag` → 13 passed.
- Mutation A (fd 3 → stdin): 5 failed (batch ×4, per-file-y-skill). Mutation B (no post-copy check): 6 failed. Restored, `cmp` identical.
- `pytest -n auto` deploy_tiering + dry_run_read_only + install_day_copy + scoped_gitattributes + brain_bootstrap + release_version_consistency → 90 passed, 2 skipped.
- `validate.sh` → pass=116 warn=6 fail=0 skip=2 (lock + spec-path WARNs fixed after; re-run warn=5).
- Demonstration: `python scratchpad/repro221.py` (minimal source, 1 core collision) → `[a] rc=0 rows before=12 after=12`; `[KEPT] .agent/rules/engineering_guardrails.md (existing file kept by CP_FLAG=-n; ...)`; `Summary: 11 updated / 0 skipped / 1 kept by CP_FLAG / 0 new / 0 removed`. `test_deploy_manifest_snapshot` 1 passed.
