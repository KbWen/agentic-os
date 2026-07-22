---
template: true
description: Work Log template for all non-tiny-fix tasks. Tracks session context, phase progress, gate evidence, and handoff state.
usage: Used by /bootstrap workflow when creating a new Work Log at .agentcortex/context/work/<worklog-key>.md. Fill all fields; write "none" for empty sections.
---

# Work Log: fix/eval-coverage-precision

## Header

- Branch: `fix/eval-coverage-precision`
- Classification: `quick-win`
- Classified by: `primary session (verified live), delegate executes`
- Frozen: `2026-07-22`
- Created Date: `2026-07-22`
- Owner: `claude-sonnet-delegate`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `b3d5104fd4da889101ee5913b26da634610e5381`
- Checkpoint SHA: `d38d7c76cdd70e7a0e01fecdafa3e0184e16c376`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-eval-harness`
- SSoT Sequence: `128`

---

## Session Info

> Written by /bootstrap. Update on each new session.

- Agent: `claude-sonnet-5`
- Session: `2026-07-22 (delegate, isolated worktree)`
- Platform: `claude-code`
- Files Read: `12`

---

## Task Description

Backlog #107 (P3 quick-win): `run_governance_eval.py` `_run_coverage` matched a case's `protects:` to the rule inventory via a bidirectional substring test, which could mis-attribute a case to a longer/shorter sibling anchor and over/under-count coverage. Tighten to exact-or-explicit-prefix matching; normalize the one `### §4.5` heading (literal `§` in the heading text made the inventory emit a doubled `§§4.5` anchor); update the one guarding eval case's `protects:` in the same change so coverage stays green.

---

## Phase Sequence

> Record each phase entry in order. Update `Current Phase` in the Header on entry.

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-22 | Task fully classified + scoped by primary session (verified live); delegate resumes at plan/implement. |
| plan | done | 2026-07-22 | Plan supplied by dispatching primary (task brief = plan artifact); target files + AC confirmed by delegate against live code before editing. |
| implement | done | 2026-07-22 | TDD red->green; see Gate Evidence + Evidence. |
| review | skipped | — | quick-win: review optional per engineering_guardrails.md §10.4. |
| test | skipped | — | quick-win: test phase optional; full CI-equivalent suite run inline instead (see Evidence). |
| handoff | n/a | — | quick-win exempt from /handoff. |
| ship | done | 2026-07-22 | PR opened to main; not merged (per instructions). |

---

## Phase Summary

- bootstrap: Classification `quick-win` (given, verified against task shape: 3 files touched — 1 tool + 1 rule heading + 1 eval spec — clear scope, no new modules/directories). Confidence: 96% — high.
- plan: Target files = `.agentcortex/tools/run_governance_eval.py` (`_run_coverage` matcher), `.agent/rules/engineering_guardrails.md` (heading text only, line 96), `.agentcortex/eval/governance.yaml` (one `protects:` value), `tests/guard/test_governance_eval.py` (new regression tests). Confirmed via grep that no other file references the doubled `§§4.5` anchor text, and that the existing `docs/reviews/2026-07-19-phase-entry-directive-enumeration.md` row 65 + `.agent/workflows/review.md:76` already cite this section with a single `§` — the fix aligns the machine-extracted anchor with the pre-existing human convention. Confidence: 95% — high.
- implement: RED (4 of 5 new tests fail against unmodified code: synthetic mis-attribution repro, naked-prefix-no-longer-matches, and the doubled-`§§4.5` anchor pin all genuinely red; the delimiter-still-works test passes both before/after by design) -> replaced the bidirectional substring test in `_run_coverage` with a new `_protects_matches_rule()` helper (exact match, or explicit `<rule>/<sub-item>` prefix with a literal `/` delimiter) -> removed the stray `§` from the `### §4.5 Anti-Rationalization Rule` heading in engineering_guardrails.md -> updated the `verdict-before-evidence-pressure` case's `protects:` in governance.yaml from the doubled-sign form to the corrected single-sign form -> GREEN (all new + all 46 pre-existing governance-eval tests pass, 51 total). **Deviation from the original acceptance criterion**: `--coverage` on the real repo reports `Zero-coverage rules: 28`, not 0 — verified via `git stash`/`stash pop` that this exact 28-item set is byte-identical on unmodified `main` (pre-existing, unrelated to this bug; new MUST-headings added across later ships were never paired with eval cases). Per scope discipline did NOT backfill 28 new adversarial cases; replaced the blanket-zero test with one scoped to the rule this backlog item actually touches (Anti-Rationalization, confirmed not zero-coverage). Flagging as a separate follow-up recommendation, not silently absorbing or hiding it. Files: 5 touched (planned 4 code/data files + this Work Log; test file counts as 1 of the 4 "target" files per the TDD requirement — no undisclosed scope divergence). Confidence: 95% — high (the matcher/heading/case fix is 99% confident; the 28-item pre-existing finding required careful independent verification before I trusted it, hence the -2%).
- ship: Full CI-equivalent suite + both validators run (see Evidence); backlog #107 flipped Pending -> Shipped; PR opened to main, not merged.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T00:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T01:00:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T01:30:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | quick-win, no spec required |
| ADR | — | none |
| Issue | — | backlog #107 (docs/specs/_product-backlog.md row 76) |
| PR | https://github.com/KbWen/agentic-os/pull/358 | fix/eval-coverage-precision -> main, OPEN, not merged |

---

## Known Risk

- The new `_protects_matches_rule` matcher only recognizes ONE explicit-prefix delimiter (`/`) for sub-anchor citations (the `AGENTS.md §Core Directives/<bullet>` pattern already in use). Any future eval case that tries a different delimiter convention will need the matcher extended — low risk, the delimiter convention is already the only one in use across all cases (verified by grep before editing).
- Mitigation: `test_protects_resolve_against_live_rule_inventory` (existing, unmodified) independently pins that every `protects:` tag still resolves to a known rule under its own (intentionally looser, schema-only) check — provides a second, independent signal if a future case's tag drifts from both conventions.
- **Pre-existing, out-of-scope finding (recommend follow-up backlog item)**: `--coverage` on the real repo currently reports 28 (of 45) MUST-bearing governance sections with zero guarding eval cases (e.g. `AGENTS.md §References`, `engineering_guardrails.md §5.2b Evidence Truncation Rule`, `security_guardrails.md §1. OWASP Top 10 Auto-Scan`, and 25 others). Verified via `git stash`/`stash pop` that this set is byte-identical on unmodified `main` — pre-existing, not caused or exposed by this change. `validate.sh`/`validate.ps1` only WARN (never FAIL) on this, so no gate is blocked, but the eval harness's actual behavioral coverage is materially thinner than the harness's own "governance eval coverage clean" Ship History claims (2026-07-19) suggested — coverage has silently regressed since then as new MUST-headings were added without matching cases. Recommend a dedicated follow-up backlog item (design pass on which of the 28 warrant real adversarial cases vs. tier-exemption, per the same rigor `docs/reviews/2026-07-19-phase-entry-directive-enumeration.md`'s census used) rather than backfilling ad hoc here.

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

none

---

## Review Feedback

none

---

## Red Team Findings

none

---

## Design Reference

none (non-UI, backend tooling fix)

---

## Observability

n/a (quick-win; no production error-sink change — this is a dev-time eval/lint tool, not shipped runtime code path)

---

## Resume

none (quick-win exempt from /handoff)

---

## Test Gate Results

none (quick-win; full CI-equivalent suite run inline instead, see Evidence)

---

## Evidence

> Filled incrementally during implement/ship below.

- Baseline (pre-edit): `python -m pytest tests/guard/test_governance_eval.py -q` -> `46 passed in 4.87s` (worktree HEAD == origin/main == b3d5104).
- RED (new tests added, code unmodified): `python -m pytest tests/guard/test_governance_eval.py::TestCoverageMatchPrecision -v` -> `4 failed, 1 passed` — `test_short_protects_is_not_mis_attributed_to_longer_sibling_anchor` failed (zero-coverage list wrongly named the synthetic "Alpha" anchor instead of "Alpha Extended", proving the mis-attribution bug); `test_no_delimiter_naked_prefix_no_longer_matches` failed (naked prefix wrongly matched); `test_real_anti_rationalization_anchor_has_single_section_sign` failed (doubled `§§4.5` anchor present); the original blanket zero-coverage acceptance test (later replaced, see below) failed with "Zero-coverage rules: 28" not 0.
- Applied 3 edits: `.agentcortex/tools/run_governance_eval.py` (`_protects_matches_rule` helper replacing the bidirectional substring test), `.agent/rules/engineering_guardrails.md:96` (`### §4.5` -> `### 4.5`, text-only), `.agentcortex/eval/governance.yaml:260` (`protects:` doubled-sign -> single-sign).
- GREEN: `python -m pytest tests/guard/test_governance_eval.py -q` -> `51 passed in 4.67s` (46 pre-existing + 5 new, zero regressions).
- **Finding, verified not caused by this change**: `python .agentcortex/tools/run_governance_eval.py --coverage` reports `Zero-coverage rules: 28` both BEFORE (`git stash`) and AFTER this change — diffed the two full outputs byte-for-byte identical (same 28 anchor names, same order). This is a pre-existing gap (headings added across later ships without matching eval cases), unrelated to backlog #107's substring-matching bug, and out of scope for this fix. Replaced the originally-planned blanket "Zero-coverage rules: 0" acceptance test with a scoped one (`test_real_anti_rationalization_rule_is_not_zero_coverage`) asserting only that THIS backlog item's specific rule (Anti-Rationalization) is not in the zero list — true both before and after (self-consistent double-sign, then self-consistent single-sign).
- `validate.sh`/`validate.ps1`'s governance-eval-coverage check is WARN-only (never FAIL) on nonzero zero-coverage count per source comment `.agentcortex/bin/validate.sh:2805` ("Never FAIL; ... Zero zero-coverage rules -> PASS") — so the pre-existing 28-count WARN is expected/unavoidable on this branch too, identically to `main`, and does not block any gate.
- Full CI-equivalent suite: `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q -n auto -p no:cacheprovider` -> `771 passed in 731.03s (0:12:11)`. (First attempt via a `tail`-piped foreground call lost its output to pipe buffering when backgrounded after timeout; re-ran directly redirected to a file, discovered 3 stray duplicate pytest invocations from earlier background/retry transitions running concurrently, killed them, confirmed exactly one clean master process before trusting the result.)
- `bash .agentcortex/bin/validate.sh` -> `Summary: pass=116 warn=4 fail=0 skip=2`. WARNs: 1 shipped-work-log-still-active (this Work Log itself, pre-ship-archival, expected for quick-win), 2 pre-existing archived-log historical gaps (unrelated), 1 governance-eval-coverage (the same pre-existing 28-count, confirmed independently by the validator itself).
- `pwsh -File .agentcortex/bin/validate.ps1` -> `Summary: pass=116 warn=4 fail=0 skip=2` — byte-identical parity with validate.sh (same 4 WARN categories).
- `python .agentcortex/tools/run_governance_eval.py --coverage` (final, clean re-check) -> `Rule inventory: 45 ... Cases evaluated: 28 ... Zero-coverage rules: 28`.
- Committed `d38d7c7` (5 files: run_governance_eval.py, governance.yaml, test_governance_eval.py, engineering_guardrails.md, _product-backlog.md — `.claude/settings.local.json` explicitly excluded, unrelated local permissions noise). Pushed `fix/eval-coverage-precision` to origin. PR opened: https://github.com/KbWen/agentic-os/pull/358 (OPEN, base=main, not merged).
