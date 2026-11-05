---
status: draft
date: 2026-11-06
classification: feature
primary_domain: governance
signal_tier: T1
signal_tier_note: "Planned structural coverage; actual reading behavior and savings still require matched evaluation."
backlog: 231
---

# Bootstrap Read-Scope Optimization

## Goal
Make existing conditional bootstrap instructions easier to retrieve without loading irrelevant branches. Preserve long-term product continuity and every current obligation; reduce actual unnecessary reads rather than chasing file size.

## Relationship
INDEPENDENT follow-up to ADR-001 Decision 3 (amended by A at 8e259c7). This refines delivery of existing bootstrap rules and does not replace the lifecycle, safety floor, skill policy or accepted ADRs. The original backlog #231 remains authoritative for disposition.

## Candidate and target files
The heading layout below is a testable hypothesis, not a finding that the current rules are defective. Record tool-call and available cost changes alongside read volume; a smaller file alone is not a benefit.

- `.agent/workflows/bootstrap.md`: give existing conditional Steps 3-6 individually addressable headings while preserving their existing conditions, decisions and required actions. Shorten redundant descriptions within that same block to fund headings; canonical text must not grow.
- `tests/ci/test_bootstrap_read_scopes.py`: focused structural checks that reject lost mandatory operations, changed preconditions, and whole-block-only retrieval. No test may equate headings alone with real savings.
- Existing lifecycle/validator tests remain applicable; no new router, summary, cache, config key or dependency.

## Acceptance Criteria
- AC-1: Every old conditional step remains discoverable under its old step number and a unique heading; nonmatching branches can be retrieved separately using existing tools. No additional policy condition is invented.
- AC-2: Private-context recovery, migration move/rename approval, backlog detection and status rules, skill selection, raw-spec intake and orphan recovery are preserved. Classification, locks, safety, evidence, phase order, shared-contract freshness and handoff do not change.
- AC-3: `bootstrap.md` character count does not exceed the pre-change base; changed prose is confined to the selected block and directly necessary reading-index references. Do not trim safety or unrelated rules to fund it.
- AC-4: Structural tests have negative controls for a dropped required operation, a missing conditional branch and ambiguous/duplicate headings; relevant existing tests and native validators pass.
- AC-5: Before adoption/ship, compare the same baseline/candidate downstream task with matching model, permissions, effort and fixture. Record actual file/section reads and read volume plus task behavior and required evidence. Static estimates alone do not satisfy this criterion.
- AC-6: Include a nonmatching case and a context-loss/resume case; a smaller read must not hide applicable decisions, HIGH lessons, unfinished work or existing recovery instructions.
- AC-7: If no avoidable read or improvement is demonstrated, retain the baseline and record a no-change disposition. Do not claim savings or ship the feature from structural tests alone.

## Verification and sequencing
First preserve A's checkpoint, then freeze this spec with owner confirmation. Plan and implement one bounded candidate, run local structural/regression checks, then obtain independent review and behavior evidence. Claude may perform the deferred model runs; their commands, results and cost limits must be explicit. No paid run is implied by spec approval. Complete review -> test -> handoff -> ship in the legal order.

## Predeclared evaluation contract
- Comparison unit: the same complete downstream task and final acceptance checkpoint, with matched fixture, model/version, effort, tools, permissions and context/cache setup; declare cases before seeing outputs.
- Read-volume metric: governance-source characters actually returned to the agent in tool transcripts across the complete task, including duplicate reads. Record retrieval calls and exposed token/cost fields separately; file size is not runtime read volume and characters are not billed tokens.
- Adoption requires all predeclared behavior/phase/recovery checks to remain correct, lower aggregate source-read characters and at least one strict reduction in a nonmatching-branch case. If extra retrieval calls erase the demonstrated benefit or costs are unavailable, report that limitation and do not claim an economic saving.
- A safety, applicability, recovery or required-evidence regression rejects the candidate. No demonstrated reduction retains the baseline. Report results as scoped observations, not universal model reliability.
- Reversible candidate construction may precede comparison evidence; adoption/ship may not. Current external/live comparison authorization is zero runs; a later Claude run needs its own explicit finite call/cost allowance, stopping when exhausted with an unproven result.

## Non-goals
SSoT restructuring; removing phases; shortening mandatory shared-contract reads; modifying skill-count guidance (#226); general numeric cleanup (#228); weakening safety or replacing product state with provider memory.

## Risks and rollback
Heading-only changes may save no runtime tokens or increase tool calls. Compare real traces and revert the candidate if it does not help. A missing conditional branch is a correctness failure. Roll back only the candidate's reviewed hunks and preserve all unrelated and untracked state.

## Domain Decisions
- [CONSTRAINT] Complete product-lifecycle obligations and cross-model compliance constrain optimization.
- [DECISION] Refine existing conditional boundaries before considering any new context subsystem.
- [TRADEOFF] A local structural candidate may remain unshipped until its real effect is independently established.
