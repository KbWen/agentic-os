# Compaction overflow: feat/brownfield-first-install-preservation

## Phase Summary

- Overflow of the active log `.agentcortex/context/work/feat-brownfield-first-install-preservation.md` (review rounds 1-3 adjudication detail). Not a final archive. ⚡ ACX

## Review Feedback (moved 2026-10-05)

Fresh reviewers (diff+spec only): R-A AC proof → PASS (9/9 AC proven by runs); R-B pre-mortem → NOT READY. Primary adjudication:
- DO-NOW 1 (R-A MED): failure test's `rel in stderr` is satisfied by the shim text; bare-`cp` mutant survives → assert `ERROR: could not back up`.
- DO-NOW 2 (R-B F2, AC-9 intent): README.md:202 + README_zh-TW.md:180 "never overwritten" → narrow like INSTALL.md.
- DO-NOW 3 (R-B F4 / R-A MED): ADR CP_FLAG bullet true only for the first-install run; next -n update reports a false overwrite (update branch, #173) → scope the sentence, name the residual.
- DO-NOW 4 (R-B F1 honesty part): `[OVERWRITE]` says "your copy" — after an interrupted first install retried with a newer source the backed-up bytes are framework v1 → neutral "previous version".
- DO-NOW 5 (R-B F3, R-A LOW): INSTALL heading over-claims for non-framework paths; ".acx-local is gitignored" only after a completed run → narrow both.
- OWNER DECISION (R-B F1 HIGH, Red Team): see ## Red Team Findings.
- BACKLOG (pre-existing, reproduced by primary): legacy migration deletes adopter tools/validate.* on first install; CP_FLAG=-i consumes the batch queue / -n update false overwrite claim.
- Round 3 (ddb1911) LOW, CLOSED: retry blocked when the interrupt fell between backup and live copy (safe stop, one move-aside); one blocked file per run (UX, no loss); dry-run does not preview backups (pre-existing). [NEEDS_HUMAN]: owner confirms amended AC-6 text before ship.
- CLOSED: symlinked dirs written through (pre-existing; bytes recoverable); mode bits not kept (AC = bytes); rm -f drops the older generation when the new backup fails (latest-only by contract; live intact); chmod on [KEPT] (pre-existing pattern); coreutils 9.2 `cp -n` exit 1 (hypothesis; update branch same; CI is the check); first-install summary says "locally-modified" (#193 banner honesty); out-of-table files = bootstrap exceptions.

## Red Team Findings (moved 2026-10-05)

- HIGH (R-B F1, reproduced by R-B; logic confirmed by primary): a first install that stops partway (backup failure, Ctrl-C) leaves no manifest; a retry from a NEWER source treats already-replaced framework v1 bytes as a collision and AC-6's refresh overwrites the .acx-local holding the adopter's original. Not a regression (baseline lost the original on run 1 unconditionally); now needs interrupt + source change. Fixing it changes frozen AC-6 → owner decision. Primary recommendation: on a no-manifest run, if `<path>.acx-local` already exists and the live file differs from upstream, stop before touching that file and tell the user to move the old backup aside (fail-closed, no new state). Risk decision: owner asked (2026-10-05) and delegated — "whatever fits the product philosophy and helps AI development". Chosen: fail-closed (correctness first, no silent data loss, no new state). Frozen spec AC-6 amended with a dated note.

## Phase Summary detail (moved 2026-10-05)

- bootstrap: feature, backlog #188, ADR-005-covered first-install data-loss path; resumed on task branch with own Work Log. ⚡ ACX
- plan: (Codex) 9 ACs, 5 target files, 6 steps; owner approved, spec frozen this session. ⚡ ACX
- implement: deploy.sh fresh-install core branch backs up to .acx-local, fail-closed, [OVERWRITE]/[KEPT]; ADR-005 amendment; INSTALL.md; 7 brownfield tests (red 7/7 → green 7/7, 4 mutants killed); deploy regression 53 passed/2 skipped. Confidence: 92% — high. ⚡ ACX
- review: Not Ready — test gap (ERROR handler untested), README/zh-TW still promise never-overwritten, ADR CP_FLAG bullet over-claims, overwrite wording says "your copy" — routed back to implement. ⚡ ACX
- implement (fix round): 5 do-now items applied (744e031); backlog #220/#221 added; owner decision pending on Red Team HIGH. ⚡ ACX
- review (round 2): fresh re-review of 744e031 resolved all 6 items, no new findings; Not Ready only because the Red Team HIGH disposition (owner-delegated → fail-closed AC-6 amendment) requires a code change — routed back to implement. ⚡ ACX
- implement (round 3): first install stops on an existing .acx-local; spec AC-6/ADR/INSTALL amended; 10 brownfield tests green. Confidence: 93% — high. ⚡ ACX
- review (round 3): PASS — fresh reviewer, AC-1..AC-9 proven by runs (10 brownfield passed; full tiering file 53/2 skipped; ps1 smoke of the stop; guard mutant → 3 failed); 3 LOW closed; AC-6 amended text [NEEDS_HUMAN] owner confirmation. Security: clean. ⚡ ACX
- test: 10 brownfield tests cover AC-1..AC-8; local deploy suites 56 passed/2 skipped; PR #461 CI all green on ddb1911. ⚡ ACX
- handoff: Resume written; recommendation Open PR (draft #461) — Codex final review + owner AC-6 confirmation before /ship and merge. ⚡ ACX
