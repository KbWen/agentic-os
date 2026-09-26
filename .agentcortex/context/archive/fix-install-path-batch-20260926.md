# Work Log: fix/install-path-batch

## Header

- Branch: `fix/install-path-batch`
- Classification: `hotfix`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-26`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `9b86567`
- Checkpoint SHA: `6678949`
- Recommended Skills: `systematic-debugging (auto: bug), verification-before-completion (auto), karpathy-principles (auto), red-team-adversarial (auto: hotfix -> Lite at review)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `174`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-26T12:35:05Z`
- Platform: `claude-code`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §12 (implement), §5 (implement/test)`
- Override: `none`
- Downstream-Capabilities: `private/downstream-capabilities.yaml present in main checkout only (worktree: none)`

---

## Task Description

Backlog #202 + #206 (docs/reviews/2026-09-26-govern-audit-downstream-sim.md F2, F6): hotfix per bootstrap §0 row 1 / guardrails §10.4 (manifest integrity + installer clone/pull).
- #202: `deploy.sh` keeps a trailing CR on stored manifest hashes; a CRLF manifest (Windows teammate, autocrlf) makes every hash mismatch -> false [OVERWRITE] + frozen scaffold updates, and the CR-bearing hash is re-recorded. Also the banner's `git add` line omits .gitignore/.gitattributes/.githooks/ (the trigger).
- #206: `installers/deploy_brain.sh` clones upstream into `<project>/.agentcortex-src` without core.longpaths (fails >~141-char roots on Windows) and a retry deploys from a partial checkout (empty index) with exit 0.
- Out of scope: #207 #208 #211 #213 (U3, feature), #209 #210 + validator NOT READY gaps (U4), #201 #205 #212 (specs).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-26T12:35:05Z | hotfix (installer/manifest integrity) |
| plan | done | 2026-09-26T12:37:09Z | red-first tests; 4 target files |
| implement | done | 2026-09-26T13:09:18Z | f321919; 4 files + tests red-first |
| review | NOT READY | 2026-09-26T14:11:15Z | independent reviewer READY; primary adjudication: fix F1-F5 before ship |
| test | done | 2026-09-26T21:01:01Z | full suite 956+2F -> 2 fixes -> rerun 18 passed |
| handoff | n/a | — | hotfix exempt |
| ship | done | 2026-09-26T21:03:04Z | based on 623395f (#445); SSoT 175->176 |

---

## Phase Summary

- bootstrap: hotfix; guardrails Full (core + §12/§5 later); ADR coverage: deploy.sh covered by ADR-005, ADR-008 (no tier change intended). ⚡ ACX
- plan: 4 files (deploy.sh CR-strip + banner paths; deploy_brain.sh longpaths + cache integrity + CR-safe source_repo; 2 test files, red-first); downstream A/B re-sim | Confidence: 90% — high
- implement: f321919 — deploy.sh CR strip (2 parse sites) + banner paths; installer acx_git (longpaths) + cache_is_intact + CR-safe source_repo; tests red-first; 1 patch attempt caught by re-sim | Confidence: 92% — high
- review rounds 1-2 + the implement round between them (NOT READY x2): moved to `archive/work/fix-install-path-batch-20260926.md`; receipts stay in Gate Evidence.
- implement (after round-2 NOT READY): 3336a1a — static long-path test reads the cache_is_intact() body and rejects any plain `git -C "$ACX_CACHE" ls-files|status`; abort-path test (git refuses the cache -> exit 1 + diagnostic + hint); two comments corrected | Confidence: 94% — high
- review (round 3, self; test/comment-only delta 6621bfb..3336a1a, installer code unchanged): PASS — R1 gate uses acx_git for both reads: PROVEN (mutants: plain git status / ls-files in the gate -> static test fails); R2 abort path survives a failing status: PROVEN (mutant without `|| true` -> new test fails, exit 128 vs 1); R3 comments match the reviewer's measurements: PROVEN by citation (13.5 min; case-collision repro). Self-review is weaker than independent; the delta adds no product code. ⚡ ACX
- test: full suite 956 passed / 2 failed (both this unit's) -> fixed -> rerun 18 passed. ⚡ ACX
- ship: PASS on 6678949 (based on 623395f). Backlog #202/#206 Shipped; tooling.log.md L2 entry; Ship History + rotation; archive MOVE + overflow; INDEX entry. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T12:35:05Z
- Gate: plan | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T12:37:09Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T13:09:18Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-26T14:11:15Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T14:17:51Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-26T15:10:04Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T15:13:56Z
- Gate: review | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T15:13:56Z
- Gate: test | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T21:01:01Z
- Gate: ship | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-26T21:01:43Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Report | docs/reviews/2026-09-26-govern-audit-downstream-sim.md | F2, F6 |
| ADR | docs/adr/ADR-005-downstream-file-preservation-tiering.md | preservation tiers — unchanged by this fix |
| ADR | docs/adr/ADR-008-portable-safety-floor.md | deploy ships the floor — unchanged |
| Git doc | https://git-scm.com/docs/git-config#Documentation/git-config.txt-corelongpaths | core.longpaths is a Git for Windows setting; ignored elsewhere |

---

## Known Risk

- Patch Attempt 1: cache_is_intact ran git status WITHOUT core.longpaths -> a healthy long-path cache read as "modified" and was rejected (exit 1). Found by the downstream long-path re-sim, not by the short-path unit test. Attempt 2: acx_git in the check + static test assertion -> pass.
- Rollback plan: revert the branch's commits (no state migration; manifests written by the fixed deploy are plain LF and remain readable by older deploy.sh).

---

## Decisions

none

---

## Conflict Resolution

- systematic-debugging vs karpathy-principles: compatible (MFR first, then the smallest fix). red-team-adversarial: review-phase only.

---

## Skill Notes

none

---

## Drift Log

- Compacted: 2026-09-26, archive: .agentcortex/context/archive/work/fix-install-path-batch-20260926.md (Phase Summary review rounds 1-2; Known Risk MFR/root-cause detail)
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Parallel development in a worktree while U1 (fix/agent-guidance-levers-204-203) runs its test suite; ship waits for U1 to merge.
- SSoT write at bootstrap (AGENTS.md non-ship exception, logged late — review F4): `current_state.md` Last Verified 2026-09-09 -> 2026-09-26 via `guard_context_write.py`, committed in f321919 with `.guard_receipt.json`. Expect a receipt conflict on rebase.
- Recovered stale Work Log lock on 2026-09-26T14:11:15.634337+00:00; prior_owner=KbWen; prior_session=2026-09-26T12:35:05Z; reason=stale-time; lock=fix-install-path-batch.lock.json
- Recovered stale Work Log lock on 2026-09-26T15:13:56.828779+00:00; prior_owner=KbWen; prior_session=2026-09-26T14:11:15Z; reason=stale-time; lock=fix-install-path-batch.lock.json
- Recovered stale Work Log lock on 2026-09-26T21:01:01.590839+00:00; prior_owner=KbWen; prior_session=2026-09-26T15:13:56Z; reason=stale-time; lock=fix-install-path-batch.lock.json

---

## Review Feedback

- Reviewer evidence: `scratchpad/ds/review-u2/` (harness + 11 experiments). Checks 1, 3, 4, 5, 6 PASS; check 2 CONCERN (F1, F2).
- F1 fix: `ls-files ... || return 1`; capture `status` output and `|| return 1` on its exit code; restore the line continuation.
- F2 fix: neutral wording ("failed the integrity check"); at the final abort print git's own diagnostics (no `2>/dev/null`) and name both likely causes (long path; source without deploy.sh). No `-c safe.directory`.
- F3 fix: set `pull.rebase false` in the test's cache repo.
- F5 fix: correct the ~20-minute claim, the "CI cannot build" claim and the stale batch-reader comment.

---

## Red Team Findings

- The cache gate is a correctness check, not a tamper control: an untracked file planted in the cache passes `--untracked-files=no` and deploys as core; skip-worktree entries and local commits also bypass it. Base had no gate, so not a regression — do not describe it as integrity protection.
- `$ACX_SOURCE` reaches `clone` without `--`; a dash-prefixed value fails closed. The committed `source_repo` already decides which code runs, by design.

---

## Security Findings

- Reviewer check 3: no new trust boundary — the cache was already fully trusted (its deploy.sh is exec'd; `git pull` already honoured cache-local config). `acx_git` adds only `-c core.longpaths=true`; no word-splitting, no safe.directory relaxation. No CRITICAL/HIGH findings.

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

- Full CI-equivalent suite on 6ce03d2 (rebased onto 623395f): 956 passed, 2 skipped, **2 failed** of 960 collected (3h15m under heavy machine load). Both failures were this unit's own: `test_no_locale_dependent_subprocess_decoding` (a `text=True` subprocess in the new partial-checkout test had no `encoding=`) and `test_171_ship_history_no_phase_summary_warn` (the handoff-compaction overflow file had no non-empty `## Phase Summary`). Fixed in 6678949 (test) and in the overflow file (committed at ship).
- Rerun on 6678949: the two failed tests + `tests/ci/test_deploy_brain_bootstrap.py` + `tests/ci/test_subprocess_encoding.py` -> 18 passed. A whole-suite run followed by a targeted rerun, not one clean run.
- Coverage delta: +8 tests (bootstrap file 12 total; tiering CRLF parametrized x2), each shown red against its reverted fix.

---

## Evidence

- RED first: test_crlf_manifest...[batch] FAILED on 9b86567 deploy.sh ([SKIP] CLAUDE.md + [OVERWRITE] engineering_guardrails.md); [per-file] PASSED on this host (MSYS awk strips CR) -> skipped on Windows, discriminating on Linux CI. Installer: partial_checkout + long_paths FAILED on base installer; crlf source_repo PASSED on base here (MSYS sed strips CR; discriminating on Linux).
- GREEN: deploy tests [batch] + enforcement-block banner assert PASSED; installer tests 9/9 PASSED.
- Downstream re-sim (fixed deploy.sh, CRLF teammate K-mate5, v1.8.24 -> branch): `203 updated / 0 skipped / 2 new`, 0 [OVERWRITE] (was 13), 0 [SKIP] (was 3), rewritten manifest 0 CR bytes.
- Downstream re-sim (fixed installer, 150-char Windows root): empty-index cache -> "Already up to date" -> detected incomplete -> re-cloned -> deployed, exit 0; no cache -> fresh clone with long paths -> deployed, exit 0 (was exit 128 "Filename too long").
- implement after review: `tests/ci/test_deploy_brain_bootstrap.py` 11 passed (also under LANGUAGE=zh_TW). Mutation: installer at f321919 fails 3 tests (partial-checkout text, F1, F2); reverting only the F1 lines fails only the F1 test. Both mutants restored and hash-checked (ff29febb).
- round 2: `tests/ci/test_deploy_brain_bootstrap.py` 12 passed. Mutation (installer swapped, restored, hash-checked): gate `status` via plain git -> `test_every_clone_and_pull_enables_long_paths` FAIL; gate `ls-files` via plain git -> same FAIL; abort `status` without `|| true` -> `test_abort_path_still_explains_when_git_refuses_the_cache` FAIL.
- Pre-existing, out of scope (reviewer note): a cache with dubious ownership reports `cache origin: <none> ... does not match` before the gate runs, then re-clones.
- ship writes (guarded): backlog #202/#206 -> Shipped, `docs/architecture/tooling.log.md` L2 entry, `archive/ship-history-2026.md` rotation (`Ship-fix-precommit-credential-failopen-2026-09-05`, asserted absent first), `current_state.md` Ship History + heartbeat 175->176.
- Post-write check: CI on the PR (validate.sh + full suite); local validate.sh took 1.5 h under this host's load during /test and is not repeated here.
