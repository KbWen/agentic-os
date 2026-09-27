# Work Log: fix/hook-monorepo-and-notices

## Header

- Branch: `fix/hook-monorepo-and-notices`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-26`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `623395f`
- Checkpoint SHA: `f3033f1`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `175`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-26T14:48:46Z`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

Opt-in pre-commit hook fixes from the 2026-09-26 downstream simulation (2 modules: `.githooks/pre-commit.guard-ssot.sample` + its install copy in `docs/INSTALL.md`/deploy banner):
- #208: in a monorepo per-package install, `git config core.hooksPath .githooks` run inside the package resolves against the repository root, so the hook never ran; and pointed correctly, the hook `cd`s to the repository root and blocks every commit with "missing .agentcortex/bin/validate.sh". Fix: the hook locates the framework from its own path; guarded-path matching uses `git diff --cached --relative`; INSTALL.md and the banner give the sub-directory `core.hooksPath` command.
- #211(a): without Python the floor passes a clean commit silently although it screens 3 credential shapes to the scanner's 7 — print that once.
- #211(c): the install-day commit prints three `GUARD WARN ... use the /ship workflow` lines; warn only for modified guarded files (`--diff-filter=M`), not added ones.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-26T14:48:46Z | quick-win |
| plan | done | 2026-09-26T14:48:46Z | hook + INSTALL.md + banner + tests |
| implement | done | 2026-09-26T15:15:58Z | dd77d64; 5 files |
| review | done | 2026-09-26T17:59:00Z | self; found the deletion gap (eb3d43e) |
| test | skipped | — | quick-win optional; hook/banner tests + mutations; PR #449 CI full suite green |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-09-27T00:41:17Z | rebased onto 6538a90 (#448); SSoT 178->179 |

---

## Plan

- Hook: `ROOT` = the directory above the hook's own `.githooks/` when it has `.agentcortex/`, else `git rev-parse --show-toplevel` (unchanged fallback). Guarded paths: `git diff --cached --name-only --relative --diff-filter=M`. No-Python floor pass: one notice line.
- INSTALL.md: sub-directory `core.hooksPath` note. Banner (deploy.sh): when the target is a sub-directory of its repository, print the exact `git config core.hooksPath <prefix>.githooks`.
- Tests: monorepo layout with a stub validator (hook from the repo root passes; guarded file under the package warns); install-day add does not warn, a modification does (rewrite `test_ac3`, which pinned warn-on-add); no-Python notice via a non-startable python shim. Mutation per hunk.

---

## Phase Summary

- bootstrap: quick-win (hook sample + its install copy). ⚡ ACX
- plan: 3 hook hunks, INSTALL.md note, conditional banner lines, tests | Confidence: 88% — git resolves a relative hooksPath from the top-level; verified in the test, not assumed
- implement: dd77d64 — hook self-locates the framework root, `--relative --diff-filter=M` guard match, no-Python notice; INSTALL.md sub-directory note; conditional banner line; test_ac3 rewritten (add = no warn, edit = warn) + monorepo, banner and notice tests | Confidence: 92% — high
- review (self, adversarial): PASS after one fix — found that `--diff-filter=M` also silenced a DELETED current_state.md, which the validator's required-files list does not cover (AGENTS.md and config.yaml are) -> eb3d43e uses `--diff-filter=a` + a direct warn for a missing path; test covers the deletion and reaches the receipt lookup (=M and no-`-e` mutants FAIL). R1 monorepo hook runs the package's validator: PROVEN (self-location mutant FAILS); R2 guarded match under the package: PROVEN (`--relative` mutant FAILS); R3 add silent, edit and delete warn: PROVEN; R4 no-Python notice: PROVEN; R5 banner hint only for a sub-directory target: PROVEN (hint-removed mutant FAILS; top-level deploy prints none); R6 fallbacks reasoned: hook under .git/hooks or a copied hook without .agentcortex falls back to the repository root (unchanged behaviour). ⚡ ACX
- ship: PASS on f3033f1 (rebased onto 6538a90). Backlog #208 and #211 Shipped; tooling.log.md L2; Ship History + rotation; archive MOVE; INDEX. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T14:48:46Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T14:48:46Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T15:15:58Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T17:59:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T00:41:17Z

---

## Known Risk

- deploy.sh banner lines sit ~6 lines above U2's banner hunk and ~20 above U3a's :1521 hunk; rebase after both merge.
- Behaviour change for adopters with the hook installed: a newly ADDED `AGENTS.md`/`current_state.md`/`config.yaml` no longer warns; the installed hook is a copy, so nothing changes until they re-copy it (banner/CHANGELOG note).
- Rollback: revert the branch commit.

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Recovered stale Work Log lock on 2026-09-26T17:59:00.794158+00:00; prior_owner=KbWen; prior_session=2026-09-26T14:48:46Z; reason=stale-time; lock=fix-hook-monorepo-and-notices.lock.json
- Recovered stale Work Log lock on 2026-09-27T00:41:17.972964+00:00; prior_owner=KbWen; prior_session=2026-09-26T17:59:00Z; reason=stale-time; lock=fix-hook-monorepo-and-notices.lock.json

---

## Evidence

- Demonstration: deploy into `mono/pkg` (a sub-directory of a git repo) prints `git config core.hooksPath pkg/.githooks` under the hook step; a top-level deploy prints no sub-directory line.
- Tests: `test_pre_commit_hook.py` + `test_precommit_hook_credential_e2e.py` 17 passed; banner test 1 passed (2 real deploys).
- Mutation (hook/deploy.sh swapped, restored, hash-checked): self-location reverted -> monorepo test FAIL; `--relative` removed -> monorepo test FAIL (guard warn missed); `--diff-filter=M` removed -> test_ac3 FAIL (warns on add); notice removed -> notice test FAIL; banner hint removed -> banner test FAIL.
- test_ac3 change is intentional: it pinned warn-on-add, the behaviour #211(c) removes.
- Self-review fix eb3d43e: deletion warns again; `hook_tests` ac3 1 passed; mutants `--diff-filter=M` and no `-e` guard each 1 failed.
- Full suite: PR #449 CI green on 745c936 (same code, pre-rebase onto #448). ship writes (guarded): backlog, `docs/architecture/tooling.log.md` L2, `archive/ship-history-2026.md` rotation, `current_state.md` Ship History + heartbeat 178->179.
