---
template: false
description: Work Log for v1.8.7 stability-simulation hardening (F1/F2 validator bugs + doc discoverability).
---

# Work Log: fix/stability-sim-hardening

## Header

- Branch: `fix/stability-sim-hardening`
- Classification: `quick-win`
- Classified by: `claude-fable-5`
- Frozen: `false`
- Created Date: `2026-07-02`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `d3cfdf6`
- Checkpoint SHA: `d3cfdf6`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-runtime`
- SSoT Sequence: `109`

---

## Session Info

- Agent: `claude-fable-5`
- Session: `2026-07-02 11:00 UTC`
- Platform: `claude-code`
- Files Read: `52`

---

## Task Description

Post-release stability hardening from a 5-simulation wave (2× adopter-deploy, hotfix-e2e, 2× adversarial red-team, /govern-audit dogfood — all subagent-run, every finding re-verified against code by the primary). Goal: v1.8.7 stable for a month. Two REAL validator bugs I introduced this session (fixed here, both fail-safe), plus two triple-corroborated doc-discoverability one-liners:

- **F1** (real): `validate.ps1` D4 built the check's Python by interpolating the INDEX path into a raw single-quoted literal (`idx = r'...'`). A repo path containing an apostrophe → SyntaxError → empty child output → default `PASS` masks a real dangling reference on Windows. Fix: pass the path via `sys.argv[1]` (mirroring `validate.sh`, which was always immune) + make empty/unrecognized output WARN, not silent PASS.
- **F2** (dead code): both validators parsed only bold `- **Created Date**:`, but the template and all 40+ real logs use plain/backtick/table form → `created_date` always empty → the legacy gate-evidence exemption (and hence the D5 tightening shipped in #308) never executed. Fix: widen both parsers to list/bold/backtick/table (mirroring how sibling header fields are already parsed). Fail-safe: no existing log predates the 2026-03-25 cutoff, so no current verdict flips; the mechanism now works as documented.
- **F3** (parity gap I created in #311): `/govern-audit` was missing from the gate-parser's out-of-band support-workflow exclusion allowlist (`retro/research/brainstorm/decide/audit`) in BOTH validators — its sibling `audit` had it. A stray `Gate: govern-audit` receipt would false-FAIL as illegal progression. Added `govern-audit` to both lists (defense-in-depth; low reachability since permitted-writes forbids the receipt). Surfaced by the /govern-audit dogfood (which independently re-confirmed F1+F2).
- **Doc**: worklog template Phase Summary now states the `⚡ ACX` sentinel requirement (validator checks it, template never said so — I hit this WARN all session); ship.md step 3 states archival is a MOVE not a copy (I made this exact mistake; 3 independent sims flagged it) — compressed to stay under the 355k token ceiling (deletion-funded, no bump).

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-02T11:00Z | quick-win, governance-runtime |
| plan | done | 2026-07-02T11:02Z | F1+F2 validator (sh/ps1 parity + tests) + 2 doc one-liners |
| implement | done | 2026-07-02T11:40Z | F1+F2+F3 + 2 docs; token deletion-funded |
| ship | done | 2026-07-02T12:10Z | PR #314 squash 3b46930; archived (MOVE) |

---

## Phase Summary

- ship: PASS — merged PR #314 (squash `3b46930`); SSoT seq 109→110; archived (MOVE) to `.agentcortex/context/archive/fix-stability-sim-hardening-20260702.md`.

**bootstrap/plan** (2026-07-02): quick-win (validator hardening batch + doc prose; contained; F2 makes an existing mechanism work, F1 is a bug fix, no NEW gate). Both fixes fail-safe. Confidence: 90% — high.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T11:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T11:02Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T11:40Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T12:10Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Sims | 5 subagent stability simulations (this session) | every finding re-verified vs code |
| PR | https://github.com/KbWen/agentic-os/pull/314 | commit 6fe50ff; ship at merge |

---

## Known Risk

- F2 widens the Created Date parser → activates the legacy exemption for real logs for the first time. Verified no existing log predates the 2026-03-25 cutoff → zero verdict flips; only future pre-cutoff logs would qualify. Rollback = revert commit.
- F1/F2 touch validate.sh + validate.ps1 (governance-critical) → require sh/ps1 parity + full CI-equiv before push.

## Conflict Resolution

none

## Skill Notes

none

## Review Feedback

none

## Red Team Findings

Simulation-sourced, dispositioned:
- **do-now (this PR)**: F1 (ps1 D4 apostrophe-path false-PASS), F2 (Created Date bold-only dead parser).
- **backlog**: `--no-python` fallback checks receipt PRESENCE not ordering/completeness → a feature skipping review/test/handoff prints "integrity check passed" (reduced-assurance path; connects #103b). tiny-fix self-labeling has no validator visibility (no work log) — honor-system limit.
- **close-with-reason**: fabricated-but-perfect chain = documented honest ceiling (enforces sequencing, not truth-of-work); govern-audit permitted-writes is prose-tier by design (actual control is the path-based guard, applies regardless of workflow); D4 `..` traversal / non-JSON line / duplicate entry all fail-safe (WARN not masked-pass); docs-pins has no coverage hole (complementary `heavy`/`!heavy`, all fail-safe arms → heavy). govern-audit 2 cosmetic doc ambiguities (empty routing_actions form, "architecture-level" threshold) — marginal, not worth release churn.

## Drift Log

none

## Evidence

- validate.ps1 (F1/F2/F3): `pass=111 warn=5 fail=0`; D4 now argv-based ("86 checked").
- validate.sh (F1/F2/F3): `pass=111 warn=5 fail=0 skip=2`.
- Structural lock tests: F1 (`test_ps1_d4_passes_index_path_as_argv...`), F2 (`test_created_date_parser_accepts_non_bold_forms...`), + existing D4/D5 → all pass; validator-FP + token file = 59 passed.
- F2 sh parser extracts date from list/bold/backtick/table forms (verified 4 forms).
- Full CI-equiv sweep: 573 passed (the 1 failure was the token ceiling breach from the ship.md addition → fixed by compression, now 3 token tests pass; total < 355,000, deletion-funded, no ceiling bump).
- Rollback: revert the branch commit; F1=argv correctness, F2=parser widening (fail-safe), F3=allowlist add, docs=prose. No new gate/engine change.
