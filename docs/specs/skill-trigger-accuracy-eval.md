---
status: shipped
title: Skill Trigger-Accuracy Eval Suite
source: github-issue-398
primary_domain: skill-ecosystem
created: 2026-09-01
last_updated: 2026-09-01  # amended after the second review round
---

# Skill Trigger-Accuracy Eval Suite

Backlog #165 · GitHub issue #398 · split from #254 (backlog #79).

## Scope limitation, established after this spec was first frozen

**Nothing at runtime consumes `detect_by.intent_patterns`.** Verified three independent ways:

- `.agent/workflows/bootstrap.md:363` — *"**No skill metadata file reads required at this stage** — trigger data is embedded in the table above, and bootstrap does not depend on `.agentcortex/metadata/trigger-registry.yaml`."* The workflow that activates skills says outright that it does not read the registry.
- `resolve_runtime_contract.py`, the only CLI that reaches `values_match` with a caller-supplied list, is invoked by **zero** workflows, validators, or CI jobs.
- `validate_trigger_metadata.py`'s resolver-parity check exercises the resolver through `scope_signals`, passing `manual_skills: []`.

Skill activation is the AI reading `routing.md §3` and the table embedded in `bootstrap.md §3.6` — semantically, not by token matching. **This suite therefore measures a data contract, not a live user path.** It is worth guarding because `trigger-registry.yaml` ships core-tier and would otherwise rot unchecked; it is NOT evidence about what a user experiences.

The §Roundtable table below records this objection as REFUTED. **That refutation was wrong.** It rested on a code comment (`trigger_runtime_core.py:713-714`, *"Intent Router reads full registry"*) — a statement of intent, not a consumer. The correct answer was available in `bootstrap.md` the whole time. Left in place rather than deleted, because the mistake is the more useful record.

## Problem

`detect_by.intent_patterns` in `.agentcortex/metadata/trigger-registry.yaml` is the data that decides whether a user's phrasing reaches a skill. Nothing measures whether it works.

Activation *resolution* is already covered — `.agentcortex/tests/test_lifecycle_skill_activation.py` carries 53 tests over classification/phase gating, load policy, manual-activation blocking, and candidate/triggered goldens. What is uncovered is narrower and specific: **`values_match` is never fed a sentence.** Every production call site passes an explicit list, so no test asks whether a real phrasing discriminates, and none asks whether a near-miss correctly fails to activate.

This sits against a commitment the repo has already made. `docs/architecture/skill-ecosystem.md` §Strategic Principles:

> **Intent-first discovery**: users should discover skills by task intent and recommended outcomes, not by memorizing skill names.

## Measured baseline (re-derived 2026-09-01, not quoted from the issue)

```
$ python .agentcortex/tools/run_governance_eval.py --coverage
Rule inventory: 45 MUST-bearing section(s) across governance files
Cases evaluated: 28
Zero-coverage rules: 28
```

`.agentcortex/eval/` contains only `governance.yaml`. Registry: 16 entries — 14 `kind: skill`, 1 `workflow`, 1 `policy`.

### Two live matcher defects, both executed against the shipped resolver

`values_match` (`trigger_runtime_core.py:860`) normalizes both sides (`normalize_text:101` casefolds and replaces every non-alnum/non-CJK run with a space) and accepts a match on exact equality **or bidirectional token-subset**. Called at `:909` as `values_match([entry["id"], *intent_patterns], manual_skills)`.

| prompt (as `manual_skills=[prompt]`, vs `systematic-debugging`) | result | verdict |
|---|---|---|
| `help me debug this crash` | MATCH | correct |
| `the build is broken and I have no idea why` | no | correct |
| `這個功能除錯很難` | **no** | **DEFECT-1** |
| `I need to debug my understanding of the spec` | **MATCH** | **DEFECT-2** |

- **DEFECT-1 — CJK patterns are inert inside a sentence, and the count is a property of the sentence.** With each pattern embedded in a zh-TW clause that adds no spaces around it, 21 of 21 are inert; space-delimit the whole pattern and 21 of 21 match. Three reviewers reached 21/21, 14/21 and 1/7 from three different corpora. Quote the mechanism — a pattern matches only when every one of its tokens is whitespace-bounded — never a bare count. `normalize_text` splits on whitespace only, so `這個功能除錯很難` normalizes to the single token `['這個功能除錯很難']` and the pattern `除錯` is not a subset of it. CJK has no whitespace word boundaries, so a zh-TW pattern only ever matches when the user happens to surround it with spaces. `AGENTS.md §Chat Language Policy` explicitly supports zh-TW input.
- **DEFECT-2 — single-token English patterns over-trigger.** `debug` is a subset of any sentence containing that token.

**Already owned elsewhere, deliberately not re-filed:** the plural/singular inflection gap is backlog **#150** (Pending, P2) — "53 inflections across 12 of 14 Skills stop matching". Cases in this suite must not re-file it; where a case would trip it, cite #150.

## Roundtable + tenth-man adjudication (2026-09-01)

Three independent seats ran on the AC-3 scoring fork. Recorded because the adjudication, not the conclusion, is the durable part.

### Rejected: substituting a `routing.md §3` ↔ registry binding test

A position formed mid-roundtable that the whole suite should be replaced by one pytest binding the two trigger surfaces. **Refuted**, each point verified first-hand:

| claim | verdict |
|---|---|
| `verification-before-completion` has `intent_patterns: []` while publishing 3 phrases in `routing.md §3` → drift | **REFUTED.** `resolve_runtime_contract.py --classification feature --phase ship --platform claude` returns `['production-readiness', 'verification-before-completion']` with no prompt at all — it activates off `phase_scope`, so the empty patterns are harmless. |
| the registry is machine-only; `routing.md §3` is what the AI reads | **REFUTED.** `resolve_runtime_contract.py` contains `intent_patterns` zero times, and `trigger_runtime_core.py:713-714` states the opposite: *"Compact index strips intent_patterns and phase_conditions (Intent Router reads full registry…)"*. |
| fold the remainder back into #254 | **REFUTED.** `archive/chore-backlog-165-skill-trigger-eval-20260811.md:98` records that exact alternative as already **rejected** — it re-blocks a deliberately unblocked P2 behind #77/#78. |
| a `tests/`-only pytest is cheaper | **REFUTED as a saving.** `run_governance_eval.py` ships downstream (`deploy.sh:739`, `:947`); a CI-only pytest gives adopters nothing. |
| swap the frozen `feature` for one pytest | **PROHIBITED.** `AGENTS.md §vNext State Model` — classification is frozen after bootstrap; reclassification requires rollback to `CLASSIFIED` and a re-run gate, not a silent downgrade. |

**A naive binding test would also false-fire by design.** `routing.md:135-136` publishes `karpathy-principles` and `production-readiness` as `_(auto; …)_` rows with **zero** phrases while the registry gives them 4 and 3 `intent_patterns` — both are `load_policy: phase-entry`, so there is nothing for a user to type. Two of four divergences are intentional; a consistency test whose exception list is half its findings is not a guard.

**The tenth man's own surviving drift is also refuted.** It reported `"systematic debugging"` as published in `routing.md §3` but unreachable in the registry. It computed `values_match` from `intent_patterns` alone; the real call at `:909` prepends `entry["id"]`, which normalizes to `systematic debugging`:

```
patterns only        : False
WITH entry id (:909) : True
```
No drift. Recorded because the same omission would silently weaken any case file written against patterns-only.

### Decision D-1 — scoring mechanism is STATIC, reusing the shipped resolver

**Chosen**: `run_skill_eval.py` imports `trigger_runtime_core` and calls `skill_is_candidate(entry, …, manual_skills=[prompt], …)` in-process.

- **Not a tautology.** The hazard the issue names is a second matcher written for the eval. Reuse removes it entirely, and the repo has already paid for that mistake once: backlog #150 records that the old `resolve_runtime_contract.py` carried its own bidirectional-substring matcher which *"masked the gap, so the simulation CLI reported activations the runtime never performed"*; PR #379's delegation to the core removed the mask.
- **Deterministic**, so a hard non-zero exit is permitted (AC-4). Precedent: `run_governance_eval.py:471` already returns `1 if has_failure else 0`.
- **Must not route through the `resolve_runtime_contract.py` CLI** — `_comma_list` splits on commas and would shred a prompt.
- **Named honestly.** This measures whether registry *data* discriminates. It does not measure whether an agent routes correctly. Landing it does not close #254.

**Rejected — live-agent scoring**: stochastic, needs a transcript-level definition of "activated" that `_score_case` has no concept of, and cannot carry a hard exit without the repeated-run aggregation explicitly reserved to #254.

### Decision D-5 — the runner is SOURCE-ONLY  *(supersedes D-4)*

D-4 was wrong and its own justification was false twice over. `trigger_runtime_core.py`, the runner's only import, ships **0** times — as does the entire resolver toolchain (`resolve_runtime_contract`, `query_trigger_metadata`, `resolve_skill_lockfile`). A shipped runner hands adopters an unhandled `FileNotFoundError`. And the ADR-007 gain D-4 claimed does not exist in code: `trigger_runtime_core.py` contains `custom-`, `downstream-capabilities` and `context/private` zero times each, so an adopter could not have evaluated their declared custom skills even with the runner in hand.

The de-facto rule this repo actually follows is *a tool ships iff a deployed surface invokes it*. Nothing deployed invokes this one. AC-6 therefore takes its **second** branch: an explicit written source-only decision. Precedent: `check_skill_provenance.py`, `check_worklog_references.py`.

### Decision D-4 — ship the runner  *(SUPERSEDED by D-5)*

Evidence, not analogy: `trigger-registry.yaml` is core tier in `tests/ci/fixtures/deploy_manifest_golden.txt:80`, while `.agentcortex/eval/governance.yaml` appears **0** times in that golden. `run_governance_eval.py` therefore already ships as a runner with no bundled data, and this unit copies that shape exactly rather than inventing one. Downstream value is real: the registry ships, so an adopter can evaluate their own trigger phrases — including `custom-*` skills declared through ADR-007's capability seam.

AC-6 therefore takes its first branch: `deploy.sh:739` (the `_runtime_tools` string) **and** `:947` (the array member) **and** one golden-manifest row. Omitting any one fails `tests/ci/test_deploy_tiering.py`.

### Decision D-2 — known-gap ratchet instead of a green board or a permanent red

The suite **will** be red on day one: DEFECT-1 and DEFECT-2 are live. Two dishonest resolutions are available and both are rejected — asserting the current (broken) behavior as expected produces a green board that measures nothing; leaving CI permanently red produces the WARN-numbness the repo already names as a failure mode.

Instead: a case may carry `known_gap: <ref>` naming the backlog row or defect it is blocked on. Known-gap cases are **printed on every run**, never silently skipped, and their count is asserted against a committed baseline that may only decrease. This is the cap-at-today ratchet ADR-011 already uses for directive counts. A new failure with no `known_gap` is a hard failure.

### Decision D-3 — coverage claim stated honestly, not banked

`validate.sh:2988` invokes the runner as `--coverage` with **no** `--eval`, so the standing 28-zero-coverage WARN reads `governance.yaml` only: a separate `skills.yaml` decrements nothing. That is the issue's deliberate choice (on-demand over a second standing WARN) and it stands.

Consequently this unit **does not** clear `AGENTS.md §Skill Activation Triggers` from the zero-coverage list, and must not claim to. Backlog **#143** owns that metric; do not let it be credited twice. Separately, that section's only MUST is about phase order (*"MUST NOT replace, skip, or alter workflow phase order"*), not trigger accuracy — so a case pointing at it would risk the `[eval-mapping]` Global Lesson: *"an eval case can silently guard an EMPTY rule… if you cannot quote it, the rule does not exist and the case is theatre."*

## Acceptance Criteria

- **AC-1** `.agentcortex/eval/skills.yaml` exists, data-only, covering all **14** `kind: skill` entries with ≥1 **positive** case each (the positive requirement is asserted separately — coverage alone would pass on negatives only). Case shape: `{id, skill_id, prompt, classification, phase, expect_pattern_match}` plus optional `{platform, activates_anyway, known_gap, note}`. Unknown keys are rejected fail-closed.
- **AC-2** ≥1 near-miss negative for every skill with non-empty `intent_patterns`. **Re-derived: 13 of 14, not 11** — the issue's AC-2 counted a `kind: workflow` and a `kind: policy` entry its own Scope excludes. `verification-before-completion` is the single exclusion; its `intent_patterns` is empty by design and activation is `phase_scope`-driven (verified by executing the resolver).
- **AC-3** The scoring-mechanism decision is written before the runner. → **D-1**.
- **AC-4** `run_skill_eval.py` scores cases; `--format json` emits a run-identity header with explicit `unknown` where unavailable. Hard non-zero exit permitted because D-1 is deterministic.
- **AC-5** `run_governance_eval.py` behaviour unchanged — proven by `git diff` returning zero lines for it plus a before/after `--coverage` run.
- **AC-6** → **D-5**: source-only, second branch. `run_skill_eval.py` appears 0 times in `deploy.sh` and in the golden manifest.
- **AC-7** *(partially met — stated honestly rather than rewritten to match the code)*. The spec asked for a baseline "asserted **non-increasing**". What shipped is **exact equality** against an anchor duplicated in the guard test, so moving it requires editing two files. That is stronger against the one-file attack the review demonstrated and **weaker** than non-increasing: two consistent edits still move it, and the ratchet cannot distinguish "the matcher was fixed" from "the case was deleted". Recorded as a known ceiling, not claimed as satisfied.
- **AC-8** No second matcher. `run_skill_eval.py` delegates to `trigger_runtime_core`, proved at **runtime** by an in-process spy — a source grep was shown to pass a hand-rolled-matcher mutant that produced a byte-identical green board.
- **AC-9** *(added after review)* No case prompt may match a skill other than its own. This is the only guard that sees pattern **widening**; the case file is otherwise a diagonal, and an over-broad pattern added to skill B is invisible to a suite that only ever scores prompts against skill A.

## Non-goals

- A/B baseline pairing, repeated-run aggregation, isolation mode, measured token/time/tool metrics, human-feedback channel — all stay in #254.
- Do not name this "effectiveness". It measures trigger accuracy.
- Fixing `values_match` (DEFECT-1/DEFECT-2 or backlog #150). This unit *measures*; the fix moves skill loading for every user and needs its own unit.
- Binding `routing.md §3` to the registry. The "which surface is the contract" question is real and unowned, but two of four divergences are intentional and it needs its own scope decision.
- Any change to `.agentcortex/eval/governance.yaml`.

## Implementation traps (repo-specific)

- A new validator check must be a Python tool behind `run_python_check` / `Invoke-PythonCheck` in **both** validators — ADR-006's native ratchet fails a raw `record_result` / `Add-Result`. This unit plans **no** validator check.
- `platforms` on a registry entry uses `claude`, not `claude-code`. `skill_is_candidate` returns `(False, {})` early on a platform miss, so a wrong literal yields empty match dicts rather than an error — a case file with the wrong platform silently tests nothing.
- Four `phase_conditions` values in the registry are **dead**: `approved-plan-exists`, `completion-claim`, `enter-review`, `enter-review-or-ship` are absent from `PHASE_CONDITION_MATCHERS` (`trigger_runtime_core.py:69-75`), so `phase_condition_matches` returns `False` for them unconditionally. Three are masked by an overlapping `phase_scope`; `test-driven-development` is `load_policy: on-match`, where the dead condition removes a real activation path. **Pre-existing runtime bug, out of scope — file separately, do not fix here.**

## Rollback

All new files. `git revert` of the implement commit removes the suite; no runtime, workflow, validator, or governance surface is touched.
