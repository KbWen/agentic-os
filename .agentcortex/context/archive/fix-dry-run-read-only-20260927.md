# Work Log: fix/dry-run-read-only

## Header

- Branch: `fix/dry-run-read-only`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-27`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `733e69c`
- Checkpoint SHA: `3d3fdf2`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `181`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-27T03:59:56Z`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

`deploy.sh --dry-run` is not read-only. On an update it runs `clean_acx_incoming` (`deploy.sh:563`) before the dry-run branch (`:733`), deleting every pending `*.acx-incoming` sidecar; on a legacy install the path migration (`mv`, `rm -rf`, `rm -f` of legacy wrappers, orphan recovery) also runs first. Found by the #215 review; reproduced: a dry-run over an install with one pending sidecar printed `Cleaned 1 old .acx-incoming sidecar(s)` and the tree went from 214 to 213 files. Under #201's proposed semantics a deleted sidecar means "merged", so a dry-run would also cancel the offer. Backlog row #216 is added at ship.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-27T03:59:56Z | quick-win |
| plan | done | 2026-09-27T03:59:56Z | guard 2 blocks + 1 test |
| implement | done | 2026-09-27T04:05:49Z | 8324202 |
| review | done | 2026-09-27T04:06:39Z | self, tenth-man + pre-mortem: PASS |
| test | skipped | — | quick-win optional; test + 2 mutants local, PR #453 CI full suite |
| ship | done | 2026-09-27T11:44:45Z | rebased onto #452; SSoT 181->182 |

---

## Plan

- `deploy.sh`: skip `clean_acx_incoming` under `--dry-run`; skip the legacy migration block under `--dry-run` and print one line when legacy artifacts exist.
- Out of scope, stated in the PR: a dry-run still creates a missing target directory (empty; `mkdir -p` before the writability check).
- Test (one real deploy): add a pending sidecar and legacy artifacts (`tools/validate.sh`, `docs/context/work/x.md`), run `--dry-run`, assert the file tree (paths + hashes) is identical and the output says the migration would run. Mutants: each guard removed -> FAIL.

---

## Phase Summary

- bootstrap: quick-win (`--dry-run` side effects). ⚡ ACX
- plan: 2 guards + 1 snapshot test + 2 mutants | Confidence: 90% — both mutating steps sit before the dry-run branch, which exits before any deploy write
- implement: 8324202 — `$DRY_RUN || clean_acx_incoming`; migration block becomes the `elif` of a dry-run branch that only reports legacy paths; test snapshots the whole target around a dry run | Confidence: 92% — test passes and both mutants fail
- review (self; refute + pre-mortem): PASS. R1 a dry run deletes no sidecar: PROVEN (mutant FAILS). R2 a dry run migrates nothing: PROVEN (mutant FAILS). R3 real deploys unchanged: the `elif` condition is the old `if` verbatim; cleanup runs when `DRY_RUN=false`. R4 README.md:190 promises "preview, no changes": now true for deploy.sh; the installer's update path still refreshes the gitignored `.agentcortex-src/` cache, which the preview needs. Trade-off: a legacy install's preview lists statuses before migration (the notice says a real run migrates first). ⚡ ACX
- ship: PASS on 3d3fdf2 (rebased onto #452). Backlog #216 Shipped; tooling.log.md L2; Ship History + rotation; archive MOVE; INDEX. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T03:59:56Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T03:59:56Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T04:05:49Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T04:06:39Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T11:44:45Z

---

## Known Risk

- Ships after #215 (SSoT serializes): rebase onto it before the ship step. #201 (draft) edits `clean_acx_incoming`'s body, not its call site.
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

---

## Evidence

- Reproduced on main (733e69c): dry run over an install with one pending sidecar printed `Cleaned 1 old .acx-incoming sidecar(s)`; tree 214 -> 213 files.
- Test: 1 passed (95s, one real deploy + one dry run). Mutants (own clones): cleanup unguarded -> FAIL (`removed ['CLAUDE.md.acx-incoming']`); migration unguarded -> FAIL (`removed ['docs/context/work/old.md', 'tools/validate.sh']`).
- Observed, out of scope: a REAL legacy migration `rm -rf`s `docs/context/work` when `.agentcortex/context/work` already exists (old logs not merged). Both layouts coexist only if the first migration was bypassed; closed with reopen trigger: an adopter reports lost legacy Work Logs.
