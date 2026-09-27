# Work Log: fix/install-day-copy

## Header

- Branch: `fix/install-day-copy`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-26`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `9b86567`
- Checkpoint SHA: `870e4f8`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `174`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-26T14:22:33Z`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

Install-day copy from the 2026-09-26 downstream simulation (2 modules: `deploy.sh`, `docs/INSTALL.md`):
- #207: the managed `.gitignore` block ignores `.cursor/` wholesale (Cursor project rules are meant to be committed). Drop it from the written block; keep `managed[".cursor/"]` so existing blocks still strip clean.
- #211(b): `--dry-run` counts 26 reference docs while deploy writes 30 (different globs) and omits the `.githooks` sample and the `.gitignore` edit.
- #211(d): the no-Python banner says Python 3.8+; INSTALL.md and both validators say 3.9+.
- #211(e): INSTALL.md says an in-place `AGENTS.md` edit is force-updated on the next deploy; `AGENTS.md` is scaffold-tier (kept, framework copy as `.acx-incoming`).
- #213 option A: tell Claude Code users to start a task with the slash command, with the measured numbers.
- Out of scope: #208/#211(a)(c) (pre-commit hook sample — separate unit), #211(f) (encoding), #201 (sidecar semantics, ADR-005).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-26T14:22:33Z | quick-win |
| plan | done | 2026-09-26T14:22:33Z | 2 modules + 1 test |
| implement | done | 2026-09-26T14:45:05Z | af8c33f; 3 files |
| review | done | 2026-09-26T17:59:00Z | self, burden-of-proof table |
| test | skipped | — | quick-win optional; targeted tests + mutations; PR #448 CI is the full-suite gate |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-09-27T00:23:00Z | rebased onto df2a2ae (#447); SSoT 177->178 |

---

## Plan

- deploy.sh: delete the `.cursor/` line from the written block only; dry-run doc count uses the same globs as the real "Deploy: reference docs" block (comment binds them); dry-run lists `.githooks/pre-commit.guard-ssot.sample` and the `.gitignore` managed-block edit; banner 3.8+ -> 3.9+.
- INSTALL.md: rewrite the "What NOT to do" sentence by tier (core force-updated with `.acx-local` backup; `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` and skills kept with an `.acx-incoming` sidecar); add the Claude Code slash-command note with the 2026-09-26 counts.
- Test: dry-run doc count == files deployed under `.agentcortex/docs/`; dry-run names the hook sample and `.gitignore`; deployed block has no `.cursor/` and an old block with `.cursor/` strips clean on upgrade. Mutation: revert each hunk, test goes red.
- Verification: targeted deploy tests, full suite at /test, validate after last write.

---

## Phase Summary

- bootstrap: quick-win (2 modules). ⚡ ACX
- plan: 4 deploy.sh hunks + 2 INSTALL.md edits + 1 test; mutation per hunk | Confidence: 90% — high
- implement: af8c33f — .cursor/ out of the block (managed[] kept); dry-run uses deploy's doc globs + names hook sample and .gitignore; 3.9+; INSTALL.md tier sentence + Claude Code slash-command note | Confidence: 92% — high
- review (self; 3 files, every behavioural claim mutation-tested): PASS — R1 dry-run doc count equals what deploy writes: PROVEN (30 = 30; globs-reverted mutant FAILS); R2 preview names the hook sample and the .gitignore edit: PROVEN (preview-lines mutant FAILS); R3 `.cursor/` gone from the block, an old block strips clean, adopter lines kept: PROVEN (managed[]-removed and line-restored mutants FAIL); R4 banner says 3.9+: PROVEN by citation (deploy.sh no-Python note); R5 INSTALL tier sentence: PROVEN by citation (get_tier: AGENTS/CLAUDE/GEMINI scaffold; rules/workflows fall through to core; core branch writes `.acx-local` at deploy.sh:230-253); R6 Claude Code numbers: PROVEN by citation (report results table: /bootstrap sessions 6/6 = 2 slash + 1 full chain + 3 re-measure chains; guided preface 1/2; zero-hint 0/3; Codex 6/6). Scope: 3 files as planned. ⚡ ACX
- ship: PASS on 870e4f8 (rebased onto df2a2ae; +validator companion fix found by PR #448 CI). Backlog #207/#213 Shipped, #211 (b)(d)(e) note; adoption.log.md L2; Ship History + rotation; archive MOVE; INDEX. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T14:22:33Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T14:22:33Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T14:45:05Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T17:59:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T00:23:00Z

---

## Known Risk

- deploy.sh is shared with U2 (hunks at :169, :399, :1508); this unit's hunks are at the block (~:1103), dry-run (~:718-801) and :1521 — adjacent-but-separate; rebase after U2 merges.
- Rollback: revert the branch commit; the only adopter-visible change is `.cursor/` no longer ignored (their own lines outside the block are untouched).

---

## Decisions

- #213: option A (document the slash-command entry with measured numbers). Option B (reopen the Stop hook) not taken: Claude-only machinery with a parity cost, against the shipped no-hooks downstream stance; reopen trigger kept on the #213 row.

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Scope addition (found by PR #448 CI): both validator twins required `.cursor/` in the deploy ignore block, so #207 turned 'deploy ignore block contents are valid' into a FAIL in every Framework Validation and Deploy Smoke job. Fixed by removing it from both required lists (companion change). Local runs had not included a full framework validate under this host's load; validate.ps1 on the fixed tree: pass=117 warn=5 fail=0.
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Recovered stale Work Log lock on 2026-09-26T17:59:00.372958+00:00; prior_owner=KbWen; prior_session=2026-09-26T14:22:33Z; reason=stale-time; lock=fix-install-day-copy.lock.json
- Recovered stale Work Log lock on 2026-09-27T00:23:01.717484+00:00; prior_owner=KbWen; prior_session=2026-09-26T17:59:00Z; reason=stale-time; lock=fix-install-day-copy.lock.json

---

## Evidence

- Demonstration: `bash .agentcortex/bin/deploy.sh --dry-run <empty dir>` -> `[NEW] (scaffold) .githooks/pre-commit.guard-ssot.sample`, `[NEW] (block) .gitignore -- created with the Agentic OS managed block`, `... 30 reference docs under .agentcortex/docs/`, `Total: ~205`; a real deploy into an empty dir writes 30 files under `.agentcortex/docs/` and a `.gitignore` with no `.cursor/` line. Before: 26 previewed, no hook/.gitignore lines.
- Tests: new `test_deploy_install_day_copy.py` 2 passed; with the ignore-block/bytecode/redeploy tiering tests 6 passed.
- Mutation (4 mutants, deploy.sh swapped then restored, hash-checked): dry-run globs reverted -> dry-run test FAIL; preview lines removed -> dry-run test FAIL; `managed[".cursor/"]` removed -> upgrade test FAIL; `.cursor/` back in the block -> upgrade test FAIL.
- README.md:202 ("Existing files are never overwritten") checked and left: it describes a first install into a project with pre-existing files; README already leads with `/bootstrap`.
- ship writes (guarded): backlog, `docs/architecture/adoption.log.md` L2, `archive/ship-history-2026.md` rotation, `current_state.md` Ship History + heartbeat 177->178. Full suite: PR #448 CI.
