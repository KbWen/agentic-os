# Work Log compaction fragment: fix/archive-name-collisions

Older detail moved out of the active Work Log `.agentcortex/context/work/fix-archive-name-collisions.md` by `/handoff §6` compaction. The final log is archived by `/ship` to the archive root.

## Phase Summary

- Compaction fragment of the feature branch `fix/archive-name-collisions`; see the final archived log for phase results.

## Task Description (moved 2026-10-06, implement entry)

- Archive naming collisions found by read-only diagnosis in this session:
  1. D4 "INDEX.jsonl referenced logs present on disk" (`validate.sh:455`, `validate.ps1:524`) falls back to `archive/work/<log>`; `/handoff §6` compaction overflow uses the same `<key>-<YYYYMMDD>.md` basename as the `/ship §3` final archive, so a missing final archive is masked by the overflow (false PASS).
  2. `/ship §3` has no rule for a second same-day ship on the same key (downstream doing all work on `main`).
  3. `/handoff §6` does not name a second same-day compaction; agents improvised `-2`/`-3`; overwrite would lose the only copy of moved detail.
- Owner direction (chat 2026-10-06): consider more scenarios; roundtable + tenth-man before deciding; do not decide lightly. Public issue may list only this repo's items.
- Adjacent backlog rows to weigh for overlap: #186 (needs a compaction-fragment naming convention), #155 (depth-shift link hazard on compaction), #179 (§6 cap contradiction), #3 (archive GC / INDEX rotation).
- Read plan: Full guardrails (done). Next reads at /brainstorm: handoff.md §6, ship.md §3, token-governance.md §8, validate.* archive scans (D4, Phase Summary, M7, M8, archive_contract), check_decision_disposition.py scope, tests touching these. Skipped: shipped specs (AC-28).
- Phase chain: /brainstorm → /spec → /plan → /implement → /review → /test → /handoff → /ship

## Evidence (moved verbatim 2026-10-06, implement)

- Brainstorm roundtable (5 read-only seats: downstream, validator, minimalist, audit, tenth-man) — primary-verified facts only:
  - Same-day collisions HAVE happened, no loss: ship ×2 on `main` 2026-06-15 → agent improvised `claude-main-20260615.md`; compaction ×2 → `codex-research-main-20260619{,-2,-3}.md` and "Compacted: 2026-09-09 (twice)" appended into one fragment.
  - D4 sh twin: child `error`/empty → PASS (`validate.sh:465`); ps1 WARNs (`validate.ps1:541-546`). No-Python: neither twin emits a D4 line.
  - Phase-Summary (`validate.sh:2220`, `validate.ps1:2081`), M7 (`:2247`) and gate-schema (`:2276`) scans are recursive; `check_decision_disposition.py:274` is root-only (directory = type). #186 root cause = recursion, not naming.
  - `-compact-` marker collides with real final `archive/fix-160-compact-index-lf-20260808.md`; keys never contain `--` (`bootstrap.md:127`); `FILENAME_DATE_RE` `-(\d{4})(\d{2})(\d{2})\.md$` (`check_decision_disposition.py:82`) cannot date `<key>-<D>-2.md`.
  - Compaction target is named in 3 deployed docs: `handoff.md:149`, `token-governance.md:120` (§7, not §8 as #186 says), `portable-minimal-kit.md:30`; contract check (`validate.sh:770-795`) only greps the `<worklog-key>-<YYYYMMDD>` substring.
  - ADR-006 §3 (`ADR-006:38`): a touched native check should be ported; D4 baseline justification #5 cites wrapper exit!=0→FAIL (no WARN) — same rationale as 4 sibling justifications.
  - Git Bash coreutils 8.32: `mv` overwrites rc=0; `mv -n` refuses but rc=0. `guard_context_write.py` has `MISSING` create-only sentinel (`:42`).
  - The 2 legacy work/-only files: non-empty Phase Summary, well-formed receipts, no relative links, already scanned by recursive M7/gate-schema → `git mv` to root adds no WARN (predicted; verify at /test).
  - Seat over-claims corrected: "7 log entries lack `shipped`" → 2 (L150, L155, both in root); line-order of `shipped` is irrelevant to a per-entry cutoff.
  - External signal: logrotate `dateext` on an existing dated destination → error + skip rotation (fail closed, no renumber).

## Drift Log (moved verbatim 2026-10-06, review)

- §12.1 read-before-write: full reads of validate.sh (3121 l), validate.ps1 (2928 l), append_chain_entry.py; ship.md/handoff.md/token-governance.md read per section before edit.
- Plan deviation (before code): new behavioral tests go in new `tests/ci/test_archive_name_collisions.py` importing helpers; `test_validator_false_positives.py` is not modified (its D4 pins stay valid).
- Found while reading: sh D4 runs `x="$(python ...)"` under `set -e`, so a nonzero child ABORTS validate.sh before Summary (not just false PASS); fixed under AC-2 with `|| true` + WARN.
- Compaction 2026-10-06 (implement): log reached 14,150 B (cap 13,311). Completed brainstorm Evidence moved verbatim with an in-place pointer — the #179 reading (verbatim move is not summarize/fold/rewrite), precedent fix/validator-twin-parity-176-175 2026-08-23. #179 hit again.

## Evidence (implement round 1, moved verbatim 2026-10-06)

- Red on baseline 9905177: fast 11 failed (fragment masks final log `ok:1`; undecodable INDEX → traceback; twin snippets differ; duplicate log appended). Slow via scratch baseline_red.py: sh 4/4 RED incl. `aborted, no Summary`; ps1 2/4 RED (other 2 are parity, ps1 already WARNed).
- Green: new + related fast suites `-m "not slow"` 158 passed; new slow 2 passed (81s); existing slow d4/witness/#171 6 passed (525s).
- Live: D4 `PASS ... (194 checked)`; validate.sh = validate.ps1 `pass=116 warn=5 fail=0 skip=2` (same 5 pre-existing WARNs). Lifecycle 354,868 → 354,726 (ceiling 355,000 unchanged). AC-4 blobs unchanged: 73037ed…, e5898fc…. scan_credentials on 11 changed files: exit 0.
- Implement final (after receipt, HEAD aefe22f): validate.sh = validate.ps1 `pass=116 warn=5 fail=0 skip=2`.

## Phase Summary (moved verbatim 2026-10-06, implement round 2)

- bootstrap: classified as feature (workflow contract change in ship/handoff + both validator twins + tests; governance paths; downstream-deployed behaviour), 5 skills matched, context loaded. ⚡ ACX
- brainstorm: 5-seat read-only roundtable + tenth-man + logrotate external signal; lead proposal (rename fragments) refuted; owner chose Option 2 + D-1..D-4 (chat 2026-10-06).
- spec: `docs/specs/archive-name-collisions.md` AC-1..AC-10; frozen 2026-10-06 on the owner's explicit chat instruction. Lifecycle headroom 132 tokens (354,868 / 355,000) → AC-9 deletion-funded.

## Review Feedback (round 1, moved verbatim 2026-10-06)

- BLOCKING (both reviewers) `validate.ps1:1` BOM stripped by my re-indent (`WriteAllText`); PS 5.1 parse fails; existing slow test `test_validate_ps1_survives_failing_git_probes_on_windows_powershell` red. Fix: restore BOM + byte pin test.
- Fix in round 2: AC-6 `token-governance.md:120` add "create it if absent"; ps1 D4 child under local `Continue` (PS 5.1 aborted on child stderr, pre-existing); PASS/WARN only when the child exits 0 (sh + ps1); ps1 `@'...'@` literal here-string; identical re-append = no-op exit 0 (ship retry).
- Rejected (verified): non-ASCII cp950 (validate.sh:5 exports PYTHONIOENCODING=utf-8; works with it); "keys can contain --" (normalization collapses runs: `hotfix/issue--42` -> `hotfix-issue-42`); casefold/`./` match (keys are lowercase, `log` is a basename).
- Accepted, no change: root-only Phase-Summary scan leaves M7/gate-schema recursive (spec Non-goal); pre-#106 adopter finals in work/ get an actionable WARN -> release CHANGELOG upgrade note.
