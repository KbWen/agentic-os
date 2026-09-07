---
status: living
title: Review — Skill Trigger-Accuracy Eval Suite (issue #398)
date: 2026-09-01
branch: feat/skill-trigger-accuracy-eval-398
verdict: NOT READY
---

# Review — Skill Trigger-Accuracy Eval Suite

Two **fresh** reviewers (diff + frozen spec + standards only; no implementation rationale, per `review.md §Adversarial Reviewer Freshness Invariant`), plus the primary's own burden-of-proof walk. Every finding below was **re-executed by the primary** before being accepted — two reviewer claims were rejected on that basis and are recorded at the bottom.

**Verdict: NOT READY.** Reverse edge `REVIEWED → IMPLEMENTING` per `state_machine.md`.

## The headline: the shipped tool is dead on arrival, and the primary's own D-4 caused it

`run_skill_eval.py` was wired to ship (D-4). Its only dependency is not shipped:

```
resolve_runtime_contract.py      golden=0 deploy=0
trigger_runtime_core.py          golden=0 deploy=0   <- the runner's only import
query_trigger_metadata.py        golden=0 deploy=0
resolve_skill_lockfile.py        golden=0 deploy=0
run_governance_eval.py           golden=1 deploy=2
run_skill_eval.py                golden=1 deploy=2   <- added by this unit
```

The **entire trigger/resolver toolchain is deliberately source-only.** D-4 reasoned from the `run_governance_eval.py` precedent — but that runner has no unshipped dependency, and mine does. The primary verified that `trigger-registry.yaml` ships and stopped there, never checking whether the *code* that reads it ships. That is the same shape of error this unit's own roundtable caught in others.

Downstream failure is worse than a clean error: `_load_core` raises `RuntimeError` only when `spec is None`. A missing file yields a valid spec and then `exec_module` raises `FileNotFoundError`, an `OSError` — not caught by `except (RuntimeError, ValueError)`. The adopter gets an unhandled traceback.

**Resolution → D-5 supersedes D-4**: the runner becomes **source-only**. AC-6 takes its second branch (an explicit written source-only decision) instead of its first. `_load_core` must still fail with a message rather than a traceback.

## Findings (all re-executed by the primary)

| # | Sev | Finding | Fix |
|---|---|---|---|
| C-1 | CRITICAL | Runner ships; `trigger_runtime_core.py` does not. Unhandled `FileNotFoundError` downstream. | D-5: source-only. Unship from `deploy.sh` ×2 + golden. Catch `OSError` in `_load_core`. |
| H-1 | HIGH | **The AC-8 guard is decorative.** `trigger_runtime_core` and `skill_is_candidate` both appear in docstrings, so a mutant that deletes the delegation and hand-rolls the matcher passes all five assertions and produces a byte-identical green run. Demonstrated by the reviewer. | Assert the literal `core.skill_is_candidate(` call; add a runtime spy that proves the core function was invoked. |
| H-2 | HIGH | **3 of 13 negatives assert a claim the resolver contradicts.** `redteam-neg`, `karpathy-neg`, `prodready-neg` declare `expect_activation: false`, but `skill_is_activated` returns True for all three regardless of prompt (`phase_scope` / `phase_conditions`). The same 6-case disagreement makes **3 of 13 known gaps not gaps**: `redteam-pos-zhtw`, `karpathy-pos-zhtw`, `prodready-pos-zhtw` activate anyway — the baseline of 13 is 23% fictional. | Rename the field to `expect_pattern_match` (it never measured activation). Add a runner cross-check that hard-fails any case whose stated claim is contradicted by `skill_is_activated`. Drop the 3 phantom gaps; baseline 13 → 10. |
| H-3 | HIGH | **14 of 14 positives embed the trigger phrase verbatim** and all die when it is stripped. `skills.yaml` claims "Natural phrasing, not the trigger phrase alone" — false. The suite proves only "say the magic words and it works", while the commitment it cites is *"users should discover skills by task intent… not by memorizing skill names"*. | Correct the claim. Add intent-first positives that carry **no** verbatim pattern; those become honest known gaps and are the measurement the spec's own premise demands. |
| F-1 | HIGH | **False factual claim in the artifact.** `skills.yaml` asserts "21 of 21 CJK patterns are inert inside a natural zh-TW sentence". 7 of the 21 contain an internal space and DO match when the user spaces them normally — which is standard zh-TW typography for Latin tokens. Correct figure: **14 of 21**. The primary generalised from a single sentence construction. | Correct to 14/21 in both `skills.yaml` and the spec, with the method that produced the number. |
| M-1 | MEDIUM | **The ratchet has no anchor.** `known_gap_baseline` lives only in `skills.yaml`, and both the runner and its guard read count and limit from that one file. A regression plus a one-character edit to that integer takes the suite from EXIT=1 to EXIT=0 with all guards green — demonstrated end-to-end. | Anchor the expected count in the test file (ADR-011 cap-at-today pattern). Require `known_gaps == baseline` exactly, not `<=`. |
| M-2 | MEDIUM | `known_gap` values are unvalidated free text (`known_gap: PROBE` is accepted). AC-7's naming requirement is a convention with no verifier. | Enforce `^(DEFECT-\d+\|#\d+)$`. |
| M-3 | MEDIUM | **No unknown-key rejection.** A typo'd `expect_activatoin:` is silently ignored — the spec's own "wrong literal silently tests nothing" trap, one level up. | Strict allowlist over case keys (fail-closed, per the repo's fixed-schema-config norm). |
| M-4 | MEDIUM | `phase` is inert and unvalidated; replacing every phase with `not-a-real-phase` produced identical output. | Validate against the resolver's phase set. It becomes load-bearing once H-2's activation cross-check lands. |
| M-5 | MEDIUM | **DEFECT-2 has zero cases.** All 13 gaps are DEFECT-1. The negatives were built to route *around* the over-trigger defect rather than measure it, so a regression that widens over-triggering cannot turn the suite red. | Add DEFECT-2 cases; the spec already supplies one (`I need to debug my understanding of the spec`). |
| M-6 | MEDIUM | The AC-1 coverage assertion lives in the **runner**, so any user with their own case file gets EXIT=1. Moot once source-only, but wrong placement. | Move completeness to the guard test; the runner reports it. |
| A-1 | MEDIUM | AC-1's "≥1 **positive** each" is unenforced — deleting a positive while keeping its negative still reports 14/14. | Assert positives-per-skill in the test. |
| A-2 | LOW | The spec's case shape mandates a per-case `platform`; no case carries one and the runner ignores it. | Reconcile: drop it from the shape, or honour it per case. |
| L-1 | LOW | `karpathy-pos` and `prodready-pos` match on the skill **id**, not on `intent_patterns`, so they cannot detect a garbled pattern set. | Re-word, or record the limitation. |

## Axes reviewed with no defect found

- **Runner guard quality** — six guards independently mutation-proved by the reviewer in a scratch copy; all six caught their removal. Only the AC-8 guard (H-1) is decorative.
- **Python 3.9** — both files parse under `feature_version=(3,9)`; no 3.10+ constructs.
- **Security** — no secrets, no injection surface; `subprocess` uses list-form argv with timeouts.
- **Scope discipline** — `run_governance_eval.py`, `governance.yaml`, `values_match`, `routing.md` all untouched; no validator check added; the backlog status flip is permitted by `AGENTS.md §Write Isolation`.
- **AC-2 / AC-4 / AC-5** — PROVEN with cited evidence.

## Reviewer claims REJECTED by the primary

- **"Nothing runs the suite → zero signal"** (predicted headline for the red team). **False.** `validate.yml:302` and `:341` run `pytest … .agentcortex/tests/`, which collects the guard file; the guard shells out to the runner and asserts its exit code. The red team checked and reported against its own brief, correctly. Residual, accepted as true: those two jobs are **non-required** in branch protection, so the eval can go red and auto-merge can still land it.
- **"`scope_signals`/`failure_signals` empty is a defect"** — split. As an *activation* claim it is the H-2 finding. As a *positives* concern it is not a defect: `manual=True` implies activation under all three `load_policy` branches.

## Not re-derived, carried as reviewer judgment

The red team's assessment that ~10 of 13 negatives are phrasings a human **would** want routed to that skill is a judgment call, not a measurement. It is recorded because it sharpens H-3: if those phrasings should route and do not, they are findings rather than passes.
