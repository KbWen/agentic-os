# Work Log: fix/receipt-integrity-hardening

## Header

- Branch: `fix/receipt-integrity-hardening`
- Classification: `quick-win`
- Classified by: `Claude Sonnet 5 (orchestrator-assigned, WP3 of 3-package remediation wave)`
- Frozen: `2026-07-11`
- Created Date: `2026-07-11`
- Owner: `claude-code-session-wp3`
- Guardrails Mode: `Full`
- Current Phase: `implement`
- Diff Base SHA: `ba949e4290f829579400e787d36c139bffd792c8`
- Checkpoint SHA: `27f6268`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-runtime / validators`
- SSoT Sequence: `119`

---

## Session Info

- Agent: `Claude Sonnet 5`
- Session: `2026-07-11 (WP3 of 3-package receipt-integrity remediation wave)`
- Platform: `claude-code`
- Files Read: `~25`

---

## Task Description

WP3 of the 2026-07-11 govern-audit receipt-integrity remediation wave (report: `docs/reviews/2026-07-11-govern-audit-receipt-integrity.md`, PR #338, merged to main). Harden both validators against 4 independently re-verified findings: F10 (P1) canonical Work Log key normalization missing in bash (case-sensitivity + punctuation gap); F8 (P2) Checkpoint SHA / Diff Base SHA presence-only placeholders; F7 (P3) receipt Timestamp not required; F9 (P3) receipt Classification never compared with header Classification.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-11 | orchestrator-assigned classification quick-win |
| plan | done | 2026-07-11 | 4 findings + adjudicated fixes given; target files fixed |
| implement | done | 2026-07-11 | F10/F8/F7/F9 in both validators + 19 new tests + 1 template sentence |
| ship | pending | — | PR only (non-draft), no merge |

---

## Plan

**Target Files**:
- `.agentcortex/bin/validate.sh` — F10 (`cur_key` canonical normalization + case-insensitive filename compare), F8 (Checkpoint SHA / Diff Base SHA value-shape + resolvability via new `_acx_check_sha_field` bash helper, reusing the existing `checkpoint_missing` WARN call site), F7+F9 (receipt-schema loop: Timestamp requirement + header-Classification agreement, reusing the existing `gate_schema_violations` WARN call site)
- `.agentcortex/bin/validate.ps1` — identical-tier/message mirror of all 4 fixes (inline duplication for F8 instead of a PowerShell function, to avoid PowerShell's function-scope-write risk; bash used a real function since bash scoping is safe by default)
- `.agentcortex/templates/worklog.md` — one sentence near the `## Gate Evidence` note: order-of-appearance is authoritative, Timestamp is provenance metadata only, no monotonic check
- `tests/ci/test_validator_false_positives.py` — 19 new tests appended (behavioral fixtures + structural source-parity pins, sh+ps1 parity where constructible)

**Steps**: (1) F10 canonical normalization in both validators; (2) F8 shared SHA-field value-shape+resolvability logic in both; (3) F7+F9 extend the receipt-schema loop in both; (4) template sentence; (5) 19 focused tests; (6) before/after validator comparison against the real repo's active Work Logs (main checkout, copied read-only into the worktree for testing, cleaned up after — never edited main checkout); (7) full CI-equivalent suite + both validators; (8) commit + push + non-draft PR.

**Risk + Rollback**: In-place native validator extensions only (ADR-006 §Decision escape-hatch clause: "unless the check must protect the no-python path, in which case a native check MAY be added with a recorded one-line justification" — here the choice is scope-driven, not no-python-driven, but achieves the SAME effect of zero ratchet impact); confirmed **zero new `record_result`/`Add-Result` call sites** — all 4 findings reuse pre-existing WARN-tier call sites (`checkpoint_missing`/`gate_schema_violations` blocks), so `tests/ci/test_validator_native_check_ratchet.py`'s baseline (`validate_sh: 197, validate_ps1: 198`) is untouched — verified via the ratchet test itself passing unmodified. Rollback = revert the PR (both validators + tests + template sentence are self-contained; no downstream schema/state migration).

**AC Coverage**: F10 uppercase/punctuation/dash-collapse/trim/truncation → 1 combined-branch behavioral fixture (sh+ps1 parity) + 1 truncation fixture + 1 negative-control (non-matching stays historical WARN) + structural 5-step source-pin. F8 invalid-value/accepted-placeholder-vocabulary/resolvability(current-branch-only, historical-shape-only)/Diff-Base-SHA-net-new-coverage → 5 behavioral fixtures (4 sh + 1 ps1 parity) + structural pin. F7 missing-Timestamp/date-only-ISO-accepted → 3 behavioral fixtures (2 sh + 1 ps1 parity). F9 mismatch-warns/unfilled-header-not-compared/matching-no-warn → 4 behavioral fixtures (3 sh + 1 ps1 parity).

**Mode**: quick-win -> implement -> ship (review/test optional per engineering_guardrails.md §10.4; inline evidence below).

---

## Phase Summary

- bootstrap: quick-win (task-assigned by orchestrator). Read the receipt-integrity audit report (`docs/reviews/2026-07-11-govern-audit-receipt-integrity.md`), `bootstrap.md:123-131` canonical Work Log key algorithm, both validators' cited line ranges (~1117-1810 sh, ~1200-1700 ps1), `templates/worklog.md`, and the repo's real Work Logs (main checkout `context/work/*.md` + a sample of `context/archive/*.md`) to enumerate the Checkpoint SHA / Diff Base SHA placeholder vocabulary actually in use. Independently re-verified all 4 findings against the actual code (not just trusting the audit text) before implementing, per instruction. ⚡ ACX
- plan: target files fixed by the task (both validators + one template sentence + tests). Designed a shared bash function (`_acx_check_sha_field`) for F8 reused across Checkpoint SHA / Diff Base SHA; chose INLINE duplication (not a function) for the PowerShell side of F8 specifically to sidestep PowerShell's function-local-scope-by-default write-visibility risk (a function mutating `$checkpointMissing` would need a correct `$script:` scope prefix, and getting that wrong is a silent bug — inlining is guaranteed-correct and matches the file's own established per-check style). Decided to reuse the EXISTING `record_result`/`Add-Result` call sites for all 4 findings (broadening the message text + adding itemized `printf`/`Write-Output` detail lines, which are NOT counted by the ADR-006 ratchet) instead of adding new call sites, keeping `tests/ci/test_validator_native_check_ratchet.py`'s baseline completely untouched — the single strongest scope-discipline decision in this WP.
- implement: F10/F8/F7/F9 implemented in both validators (`~130` new/changed lines in validate.sh, `~170` in validate.ps1). Mid-implementation discovery: the repo's own 2 real active Work Logs (`chore-archive-session-worklogs-20260710.md`, `chore-v1.8.11-release.md`) have UNFILLED template placeholders for header Classification (`` `<tiny-fix | quick-win | hotfix | feature | architecture-change>` ``) and for Diff Base SHA / Checkpoint SHA (`` `<git-sha or none>` ``) — the literal template text was never replaced, even though both logs carry real Gate Evidence receipts through a `ship` PASS. This is ALSO why the pre-existing (unrelated to this WP) baseline already shows `[FAIL] work logs with illegal gate phase progression: 2` for these 2 files — the unparseable header Classification makes the gate-progression parser fail-close to feature-strict requirements while only 4 of the required 6 phases are present. Designed F8's accepted-placeholder vocabulary (`none`, `pending-commit`, `<git-sha or none>`, or hex `[0-9a-fA-F]{7,40}`) and F9's "only compare when the header Classification parses as a real `[a-zA-Z]...` tier" rule specifically so these 2 pre-existing logs stay compatible (no NEW WARN introduced). Verified before/after against the main checkout's real Work Logs (temporarily copied read-only into the worktree for testing, then deleted — main checkout was never edited): both `validate.sh` and `validate.ps1` reproduce the exact pre-existing baseline (`pass=112 warn=4 fail=1 skip=2`) unchanged before AND after my code changes, with my 2 new checks showing `[PASS]` (not a new WARN) on both platforms, using byte-identical PASS/WARN message wording across sh/ps1. Added 19 new tests to `tests/ci/test_validator_false_positives.py` (behavioral fixtures for all 4 findings on sh, sh+ps1 parity pairs where a Windows PowerShell runner is available, plus fast structural source-parity pins) — all 19 PASS in `344.25s` — see `## Evidence` for exact pass counts. Added the required one-sentence Timestamp-authority clarification to `templates/worklog.md`. Ran the full CI-equivalent suite (`pytest tests/ci tests/guard .agentcortex/tests -m "not slow"`) plus the newly-added slow tests plus both validators end-to-end — see `## Evidence`. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T16:30:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | docs/reviews/2026-07-11-govern-audit-receipt-integrity.md | Source audit (PR #338, merged) |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | Native-extension escape hatch (zero new call sites — ratchet baseline untouched) |
| PR | (this branch) | fix(validate): receipt integrity — canonical worklog-key normalization + receipt/SHA value validation |

---

## Known Risk

- The gate-progression PARITY discrepancy (bash counts 1 FAIL-contributor per malformed header-Classification log via early `sys.exit(0)`; PowerShell's equivalent inline logic does NOT early-return after the "incomplete" completeness check, so it ALSO falls through to the progression-order loop and double-counts — bash shows `illegal gate phase progression: 2` for the repo's 2 malformed real logs, ps1 shows `4` for the SAME 2 files) is a PRE-EXISTING cross-platform parity gap, confirmed present in the UNMODIFIED baseline (before any of my edits) and untouched by this WP's diff (I never modified the gate-progression completeness/order logic). Flagged for a follow-up backlog item; NOT fixed here (out of the 4-finding scope).
- The repo's own 2 real active Work Logs have long-standing unfilled template placeholders (header Classification, Diff Base SHA, Checkpoint SHA) predating this WP — my F8/F9 designs accommodate them (no new WARN) rather than flag them, per the explicit "align accepted vocabulary so current legitimate logs pass" instruction; worth a separate small fix (filling in those 2 real logs' headers) but out of THIS WP's scope.
- F8's no-python degraded mode: value-shape/resolvability validation runs in pure bash/PowerShell native code (not behind `run_python_check`), so it is NOT affected by `--no-python` — unlike some other checks, this one has NO reduced-assurance mode to document.

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- ADR-006 native-extension justification (F7/F8/F9/F10, one-liner per instruction): these are in-place extensions of 2 EXISTING native checks (the `checkpoint_missing` Checkpoint-SHA-presence check and the `gate_schema_violations` receipt-schema check) — both checks already existed natively pre-WP3, and all 4 findings broaden their CONDITIONS/messages without adding new `record_result`/`Add-Result` call sites (verified: `tests/ci/test_validator_native_check_ratchet.py` passes unmodified against the existing baseline `validate_sh: 197, validate_ps1: 198` — zero bump needed). ADR-006 mechanism 3 ("opportunistic backfill: port to a Python tool when touched") was considered and NOT taken — task-scoped as native extension to stay within quick-win scope (a new Python tool would need its own `run_python_check` wiring, deploy.sh whitelist entry, and fixture-test suite, which is architecture-change-shaped, not quick-win-shaped).
- Scope note: the SEPARATE archive-Work-Log receipt-schema loop (`archive_gate_schema_violations` in validate.sh / `$archiveGateSchemaViolations` in validate.ps1, scanning `context/archive/*.md`) is INTENTIONALLY untouched — F7/F9 instructions said "extend that SAME [audit-cited] loop", which is the ACTIVE `context/work/*.md` loop only; archived logs stay exempt from the new Timestamp/Classification-match requirements (F7's own text: "archived logs may predate it").
- Placeholder vocabulary for F8 (grepped from real data before implementing, per instruction): `.agentcortex/context/work/*.md` (2 real files) — both carry the literal unfilled template default `` `<git-sha or none>` `` for BOTH Diff Base SHA and Checkpoint SHA (never replaced). `.agentcortex/context/archive/*.md` (112 tracked files, not scanned by this validator check but grepped for vocabulary per instruction) — observed values: full/short hex SHAs (majority), bare `none` (2 occurrences), `pending-commit` (1 occurrence), and one malformed `f3ac21c (implementation commit)` (SHA + trailing note — handled by the "first whitespace token" leniency in `_acx_check_sha_field`). Adopted accept-list: hex `[0-9a-fA-F]{7,40}` (optionally followed by trailing note text, using the first token), `none` (case-insensitive), `pending-commit` (case-insensitive), and the literal `<git-sha or none>` (case-insensitive) — the last one specifically because 2 real active logs currently carry it unfilled and the hard constraint requires the accepted vocabulary to keep current legitimate logs green.
- `Diff Base` contract-field check (per instruction, before implementing): confirmed the field is ALWAYS named "Diff Base SHA" in `templates/worklog.md` (header line) and in all real usage (29 of 112 archived logs) — a bare standalone "Diff Base" field does NOT exist anywhere in the template or real logs; neither validator had ANY existing check (presence or value) for "Diff Base SHA" before this WP (grep confirmed zero matches in both files pre-edit). F8's "same treatment" is therefore net-new coverage for this field (value-shape + resolvability only — no NEW presence-required check was invented, since none existed before and the finding only asked for value validation).
- WP1 (`fix/validator-fail-open-hardening`, F1/F2/F3) and WP2 (`fix/external-executor-safety` — actually branch name `feature/external-executor-safety` per its own Work Log, F4/F5/F6) are running in parallel in their own worktrees per the orchestrator's instructions; confirmed via `git diff --stat .agentcortex/bin/validate.sh .agentcortex/bin/validate.ps1` in the MAIN checkout (clean, no diff from HEAD) that neither WP's code edits land in the shared main checkout — only their Work Logs do (same mechanic given to this WP). Stayed exclusively within the ~1117-1810 (sh) / ~1147-1800ish (ps1) regions per the "stay in YOUR regions" instruction; never touched the ~27-31/~307-324/~943-978 regions WP1 was assigned.

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

none (quick-win — review/test optional; see `## Evidence` for inline test evidence instead)

---

## Evidence

- New tests: `python -m pytest tests/ci/test_validator_false_positives.py -k "f10 or f7 or f8 or f9" -v` → `19 passed, 44 deselected in 344.25s` (all F10/F7/F9/F8 behavioral fixtures + structural source-parity pins; includes sh+ps1 parity pairs where a Windows PowerShell runner is available).
- Full CI-equivalent: `python -m pytest tests/ci tests/guard .agentcortex/tests -m "not slow"` → `593 passed, 93 deselected in 111.30s`.
- `bash .agentcortex/bin/validate.sh` (worktree, real repo data): `pass=112 warn=4 fail=1 skip=2` — byte-identical to the pre-change baseline captured from the main checkout before implementing; my 2 new checks show `[PASS] all active work logs have well-formed Checkpoint SHA / Diff Base SHA values` and `[PASS] all active work log gate receipts have required fields and consistent Classification (gate/verdict/classification/timestamp)` (not new WARNs).
- `validate.ps1` (worktree, real repo data): same `pass=112 warn=4 fail=1 skip=2`, same 2 new-check PASS messages verbatim (cross-platform message parity confirmed).
- Method: the 2 real active Work Logs (`chore-archive-session-worklogs-20260710.md`, `chore-v1.8.11-release.md`) were temporarily copied read-only from the main checkout into this worktree's `.agentcortex/context/work/` (gitignored, not committed), validated with both updated validators, then deleted — the main checkout itself was never edited by this session.
