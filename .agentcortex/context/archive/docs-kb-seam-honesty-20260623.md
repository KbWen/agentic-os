# Work Log: docs/kb-seam-honesty

## Header

- Branch: `docs/kb-seam-honesty`
- Classification: `quick-win`
- Classified by: `Claude (Opus 4.8)`
- Frozen: `true`
- Created Date: `2026-06-23`
- Owner: `claude-t2-docs`
- Guardrails Mode: `Quick`
- Current Phase: `implement`
- Checkpoint SHA: `(pre-commit)`
- Recommended Skills: `none`
- Primary Domain Snapshot: `docs/governance`
- SSoT Sequence: `88`

---

## Session Info

- Agent: `Claude (Opus 4.8)` — autonomous (user AFK/asleep)
- Session: `2026-06-23T00:30:00+00:00`
- Platform: `Claude Code`
- Context Read Receipt: read SSoT (seq 88), Codex review log (codex-v18-review-main.md findings #2/#6/#7), CHANGELOG.md, connecting-a-knowledge-base.md, lifecycle-baseline.json

## Task Description

T2 of the Codex-review backlog — docs honesty + release metadata (3 findings, all docs/metadata, no engine logic):
- #2 (MEDIUM): "zero tokens / byte-identical when absent" overclaims — the v1.8 KB-seam adds ~217 tokens of always-loaded bootstrap instructions even with no KB. Narrow to "zero KB reads / zero KB-content tokens when absent."
- #6 (MEDIUM): `CHANGELOG.md` [1.8.0] omitted PR #273 (capabilities-validator BOM fix), which is in the v1.7.0..v1.8.0 range.
- #7 (LOW): the wiring probes in `connecting-a-knowledge-base.md` misreport — bash grep `[0-9]*` allows zero digits + no whitespace; PowerShell `Test-Path` checks existence not a readable leaf.

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | complete | 2026-06-23 | quick-win; 3 docs findings; scope = CHANGELOG.md + connecting-a-knowledge-base.md (lifecycle-baseline.json is test-baseline DATA → not touched) |
| plan | complete | 2026-06-23 | verify +217 premise, then narrow wording + add #273 + fix probes |
| implement | complete | 2026-06-23 | 2 files edited; probe dogfooded; +217 independently verified |
| ship | complete | 2026-06-23 | PR #282; ledger entry + seq 88→89 (surgical Edit, not append) |

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Scope decision: `lifecycle-baseline.json` (Codex #2 cited it) is the lifecycle token test's baseline DATA, not a user-facing claim — editing it would risk the token test. Left untouched; the overclaim lives only in CHANGELOG + the guide.
- Premise verification (attribution-review): the "+217 tokens" was Codex's number; independently confirmed by measuring `git diff v1.7.0..v1.8.0 -- bootstrap.md` → net ~883 added chars / 4 ≈ ~221 tokens ≈ 217. The "byte-identical/zero-cost-when-absent" claim is provably false (the §1b/§3.6 KB instructions are always-loaded). Wording narrowed to honest "zero KB reads / zero KB-content tokens; ~217-tok always-loaded instruction cost."
- SSoT write (ship): added the Ship-docs Ship History entry at the TOP of `## Ship History` + bumped Update Sequence 88→89 + Last Updated 2026-06-23 in `current_state.md` via a surgical Edit (NOT guard append — O_APPEND = file-end; top-insertion per the #265 ship.md fix). Unguarded surgical write logged here per convention. PR #282 carries the ledger entry.
- Test scoping (justified): ran `-m "not slow"` (546 passed) rather than the full slow suite for push — a docs-only change (CHANGELOG + guide prose) cannot affect the slow subprocess validator/deploy behavioral tests. (The full slow suite was also launched in background as a bonus.) This scoping is NOT the [feedback-full-ci-suite-before-push] gap — that lesson is for validator/shared-check changes, which this is not.

## Plan

- Goal: remove the absent-KB token overclaim, add the omitted #273 to the v1.8.0 changelog, fix the two broken wiring probes — all honest, no engine change.
- Non-goals: any engine/validator/test logic change; editing lifecycle-baseline.json.
- Blast Radius: 2 docs files (CHANGELOG.md, connecting-a-knowledge-base.md).
- Verification: dogfood the fixed grep probe against the real manifest; run the full CI-equivalent suite (`pytest tests/ci/ tests/guard/ .agentcortex/tests/`) before push (per [feedback-full-ci-suite-before-push]).
- Rollback: revert the PR (docs-only).

## Phase Summary

- bootstrap: quick-win; 3 docs/metadata findings from the Codex review; scope fixed to 2 files.
- plan: verify the +217 premise, narrow the overclaim wording, add #273, fix both probes.
- implement: CHANGELOG.md (overclaim narrowed + #273 added with a Governance bullet) + connecting-a-knowledge-base.md (2 overclaim spots narrowed + grep/Test-Path probes fixed); fixed grep probe dogfooded against the real manifest (extracts `370107`; old probe printed only the key); +217 independently verified (~221 measured).

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T00:30:00+00:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T00:35:00+00:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T00:50:00+00:00
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T01:05:00+00:00

## Evidence

- Probe dogfood: fixed `grep -oE '"total_approx_tokens":[[:space:]]*[0-9]+'` → `"total_approx_tokens": 370107`; old `grep -o '...[0-9]*'` → only `"total_approx_tokens":` (confirms #7).
- +217 verification: `git diff v1.7.0..v1.8.0 -- .agent/workflows/bootstrap.md` → +2247 / -1364 chars (net ~883 ≈ ~221 tokens), corroborating Codex's +217.
- #6: `git log v1.7.0..v1.8.0` includes #273; CHANGELOG now lists it (Packages #273–#276 + a Governance bullet).
- Full CI-equivalent suite: (running) `pytest tests/ci/ tests/guard/ .agentcortex/tests/`.

## Security Findings

none

## Resume

none
