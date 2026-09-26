# Work Log overflow: fix/gate-evidence-tooling (compacted 2026-09-26)

Moved verbatim from the active Work Log per handoff §6 to stay under the size cap.

## Phase Summary

- Compaction overflow of `.agentcortex/context/work/fix-gate-evidence-tooling.md` (quick-win #209/#210/#214 + #205/#211(f)): the original plan and the round-1 independent review, moved verbatim. Receipts and the current summary stay in the active log. ⚡ ACX

## Moved: Plan (original, steps 1-5)


- Target files (5 + tests): `.agentcortex/bin/validate.sh`, `.agentcortex/bin/validate.ps1`, `.agent/workflows/ship.md`, `.agent/workflows/implement.md`, `.agentcortex/docs/guides/guarded-context-writes.md`; tests in `tests/ci/test_validator_false_positives.py`.
- Step 1 (#210, both twins): collect the offending log name(s) for `work logs missing gate evidence receipts` and print them after the FAIL with the canonical line `- Gate: <phase> | Verdict: PASS | Classification: <tier> | Timestamp: <ISO>` (same list-then-print idiom as the checkpoint WARN).
- Step 2 (validator gap, both twins): in the non-PASS branch, a review NOT READY that follows a review PASS pops that PASS first, then the normal reverse edge pops the implement — the latest review verdict wins.
- Step 3 (OTHER-3): `implement.md` quick-win bullet says ship straight after implement; add the exception the validator already enforces for every tier (after a review NOT READY, re-review PASS first). Stricter reading kept: shipping over an unresolved NOT READY ships an unverified fix.
- Step 4 (#209): `ship.md` §2 gets one runnable snapshot→write template (`--lock-key`, `--input`, `--expected-sha`); delete "or a surgical anchored Edit", the `--mode replace` prose and the Stage-1 "warning, not a block" sentence (deletion-funded; ratchet headroom 119 tokens on main). Guide: correct the INDEX.jsonl bullet, which names the guard for a file only `append_chain_entry.py` may append (ship.md §3 says the guard breaks the chain).
- Tests: fixture per twin — PASS→NOT READY→test must FAIL, PASS→NOT READY→implement→review→test must stay legal; missing-receipt FAIL must name the log and the format; fast source-parity test for both twins + ship.md template flags. Mutation: revert each validator hunk, the matching test must go red.
- Verification: targeted tests, full CI-equivalent suite (`--collect-only` count), `validate.sh` + `validate.ps1`, lifecycle ratchet sum < 355000.
- Out of scope: review.md (U1 overlaps), #205 timestamp contract.
- Step 5 (scope addition, found while testing Step 1-2 under Windows PowerShell 5.1): `validate.ps1` aborts with no Summary when a git probe that is expected to fail writes stderr under `$ErrorActionPreference = 'Stop'` (5.1 only; pwsh 7 is fine). Fix: one `Invoke-GitQuiet` helper (EAP Continue, stderr dropped, stdout + `$LASTEXITCODE` intact); convert the 9 unguarded probes. Already-try-wrapped probes untouched.

## Moved: Phase Summary (round-1 independent review)

- review (independent, 45 fixture logs x sh/pwsh/5.1): Not Ready — F1 MEDIUM: voiding every gate after the last review PASS also erased ILLEGAL gates recorded there (a premature handoff/ship), so a later NOT READY + redo loop laundered what base flagged (4 repro sequences) — fix: never delete recorded gates; scope the NOT READY check to gates after the NOT READY (nr_index); F2 LOW/MED: quick-win PASS->NR->ship reported "missing implement" (sh) — resolved by F1's fix; F3 LOW pre-existing: :562/:658 throw under PSNativeCommandUseErrorActionPreference=$true — route through Invoke-GitQuiet, quote '--'; F4 LOW doc drift (implement.md:25/state_machine.md:27 unqualified) — kept: implement.md Resume-after-review states it, a second line costs 28 tokens x 12 loads; F5 LOW ship.md "edit a copy" can leave an untracked file — say outside the repo; F6 LOW add the laundering fixture to both behavioural tests. Also: test commits should pass `-c commit.gpgsign=false`. #210 listing, Invoke-GitQuiet under 5.1/pwsh, ship template run and all 7 tests' discrimination: PASS. Routed back to implement. ⚡ ACX
