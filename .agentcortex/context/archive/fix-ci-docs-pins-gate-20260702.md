---
template: false
description: Work Log for backlog #112 — CI docs-only gate hole + audit-witness behavioral tests.
---

# Work Log: fix/ci-docs-pins-gate

## Header

- Branch: `fix/ci-docs-pins-gate`
- Classification: `quick-win`
- Classified by: `claude-fable-5`
- Frozen: `false`
- Created Date: `2026-07-02`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `984e2ab`
- Checkpoint SHA: `984e2ab`
- Recommended Skills: `none`
- Primary Domain Snapshot: `ci-security`
- SSoT Sequence: `105`

---

## Session Info

- Agent: `claude-fable-5`
- Session: `2026-07-02 04:10 UTC`
- Platform: `claude-code`
- Files Read: `36`

---

## Task Description

Backlog #112 (from the 2026-07-02 test-quality audit, both P1s). (a) README/INSTALL/spec content-pin tests live only in pytest jobs gated `heavy == 'true'`, while README.md/docs/* classify inert → the pins never run on the docs-only PRs most likely to break them. Fix: register a `docs_pin` pytest marker, tag the four pin tests, add an ungated `docs-pins` job to validate.yml that runs `-m docs_pin` when `heavy != 'true'` (heavy PRs already run the full suite — no coverage loss, no double-gating). (b) The audit-chain git append-only witness (validate.sh/ps1) has only source-substring tests — add slow behavioral tests exercising append (PASS), tail-truncation (FAIL), and published-entry edit (FAIL) against a deployed temp repo with a real git origin/main baseline.

Verified pre-conditions: pin tests are pure file reads (no bash); test_ci_hardening.py pins only the classifier inert-arm content (a new job does not touch it); pytest.ini marker philosophy is "local opt-out, never default deselect" — `docs_pin` is an additive selector for a new job, not a deselect of CI's full suite.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-02T04:10Z | quick-win, ci-security |
| plan | done | 2026-07-02T04:15Z | marker+job by primary; witness tests delegated (opus) |
| implement | done | 2026-07-02T04:50Z | (a)+(b) done; subagent output verified; sweep 570 passed |
| ship | done | 2026-07-02T05:10Z | PR #310 squash 3c0ae22; archived |

---

## Phase Summary

- ship: PASS — merged PR #310 (squash `3c0ae22`); SSoT seq 105→106; archived to `.agentcortex/context/archive/fix-ci-docs-pins-gate-20260702.md`.

**bootstrap** (2026-07-02): Classified quick-win (CI workflow + test files; 1-2 modules, clear scope; not installer/source-provenance logic so the supply-chain hotfix escalation does not trigger). Evidence path = new job green on this PR (which is itself heavy → full suite also runs), `-m docs_pin` collection count, witness behavioral tests, full CI-equiv sweep.

**implement** (2026-07-02): Confidence: 90% — high. (a) `docs_pin` marker registered (additive selector, never a deselect — matches pytest.ini philosophy); 4 pin surfaces tagged (5 tests, 0.12s); `validate.yml` gains the `docs-pins` job gated `heavy != 'true'` (SHA-pinned actions; complementary to the heavy suite, never double-gated); 2 lock tests in test_ci_hardening.py (job stays ungated-inverted + marker selects ≥4). (b) Witness behavioral tests delegated to an opus subagent under a single-file constraint, then verified by primary (scope diff, line-by-line read, clean re-run → 12 passed). Final sweep 570 passed. One remediation: my nested-heredoc append initially mangled two escape sequences in the lock tests (SyntaxError caught by the immediate test run; fixed via Edit).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T04:10Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T04:15Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T04:50Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-02T05:10Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #112 | this task |
| PR | https://github.com/KbWen/agentic-os/pull/310 | commit 2835eab |

---

## Known Risk

- New CI job name must not collide with required-check config (docs-pins is additive, non-required). Rollback = revert commit.
- Marker-based selection can silently select zero tests if tags are lost → add a collection-count lock test (≥4) in the same change.
- Witness behavioral fixtures need a real git origin/main baseline; a wrong fixture could false-PASS — verify by asserting the FAIL message text on the tampered cases (positive + negative directions).

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Review Feedback

none

---

## Red Team Findings

none

---

## Drift Log

none

---

## Evidence

- Marker selection: `pytest tests/ci/ -m docs_pin -q` → 5 passed, 0.12s (pure file reads confirmed fast).
- Lock tests: `tests/ci/test_ci_hardening.py` → 13 passed (incl. 2 new #112 locks: job gated `heavy != 'true'` + `-m docs_pin`; marker registered + selects ≥4).
- Tagged-file regression: `test_security_workflow.py` + `test_pre_commit_hook.py` non-slow → 47 passed.
- `validate.yml` YAML parses OK after the docs-pins job insertion (SHA-pinned actions copied from existing jobs).
- Witness behavioral tests: delegated to opus subagent (only `tests/ci/test_audit_witness.py` authorized). VERIFIED by primary: scope diff = exactly that one file (+190 lines); code reviewed line-by-line (fixture: deploy → 3 chained entries via append_chain_entry.py + referenced logs → git init/commit → bare-clone origin → merge-base precondition assert; assertions grep the witness line only; PASS case asserts both FAIL verdicts absent); re-run from a clean process → 12 passed in 78s (9 string-presence + 3 behavioral).
