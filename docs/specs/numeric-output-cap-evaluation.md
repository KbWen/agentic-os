---
status: draft
date: 2026-11-06
classification: feature
primary_domain: governance
signal_tier: T2
signal_tier_note: "Planned behavior evaluation; no finding-completeness or cost benefit is established by draft fixtures."
backlog: 225
---

# Numeric Output-Cap Evaluation

## Goal and relationship
Evaluate whether numeric response/finding caps suppress necessary product evidence or actionable findings. INDEPENDENT evaluation following shipped #224; preserve concise communication, scope discipline and ADR-011's accepted dispositions. A cap is not removed merely because a model is newer.

## Scope and targets
- Inventory the existing chat/template caps cited by #225 and the Lite-mode token/finding caps in `.agents/skills/red-team-adversarial/SKILL.md`.
- First candidate: replace the Lite-mode hard finding/token ceilings with concise reporting of every distinct actionable finding inside the existing fix-point scope. Keep severity, escalation and Lite/Full/Beast selection unchanged.
- Add focused eval/scorer fixtures in existing test/eval surfaces and regenerate `.agentcortex/metadata/trigger-compact-index.json` with the existing generator if its source hash changes.
- Global caps in `AGENTS.md` and phase templates remain unchanged unless separate evidence and explicit approval of any affected accepted ADR decision are obtained. Do not silently generalize the first candidate into a rewrite.

## Finding rubric
An actionable finding identifies a reproducible failure or boundary breach caused by the changed fix point, its source location and a concrete remedy. Findings are distinct when they have independent failure mechanisms requiring different remedies; repeated instances with one mechanism/remedy may be grouped. Predeclare fixture defects, expected remedies and out-of-scope decoys before comparing outputs; keyword counts alone do not score completeness.

## Predeclared evaluation contract
- Use cases with zero, one and at least three independently fixable in-scope defects plus unrelated decoys. Freeze the answer key before model outputs and keep it, defect counts and expected remedies out of the agent prompt.
- Score matched baseline/candidate outputs with arm labels hidden from a reviewer who did not author the fixture; record disagreements rather than converting them into PASS. Equivalent valid remedies are allowed by the frozen rubric.
- Record expected defects found/missed, unsupported or out-of-scope findings, severity/approval correctness, output length and exposed usage. Candidate adoption requires every fixture defect found, no unsupported/scope-expanded findings, unchanged protection checks and a demonstrated completeness or correct-decision gain over baseline. Extra prose alone is not a gain; equal correct outcomes provide no evidence to remove a cap.
- Local fixtures/scorer controls do not constitute model-behavior evidence. Current external/live comparison authorization is zero runs; future Claude comparisons need a separate finite call/cost allowance. On exhaustion or unresolved scoring disagreement, retain the baseline and report unproven.

## Acceptance Criteria
- AC-1: Record every in-scope numeric cap with location, protected behavior, proposed disposition and evidence/reopen trigger. Keep unproven changes explicit; no blanket deletion.
- AC-2: A Lite-review fixture with at least three independent actionable fix-point defects surfaces every one; unrelated defects in a decoy area do not widen the review scope. Concision may group repeated root causes but cannot discard distinct defects.
- AC-3: Existing severity decisions, mandatory security handling, phase gates, evidence and handoff remain unchanged. Fewer words or fewer findings alone are not success metrics.
- AC-4: Existing eval/scorer validation includes positive and negative controls; local fixtures test scorer wiring, not live-model behavior. Generated metadata is fresh and relevant existing tests pass.
- AC-5: Before adoption/ship, compare baseline and candidate on matched relevant downstream cases and governance evaluation. Retain finding completeness, correct risk handling and useful brevity; record actual usage if available and unknown otherwise.
- AC-6: No demonstrated benefit means restore/retain the baseline and close the tested hypothesis with a reopen trigger. Preserve untested cap dispositions; do not mark the full original backlog item shipped without its required disposition scope.

## Sequence, non-goals and rollback
Queue after B; only one feature enters implementation at a time. Owner confirmation freezes this draft; paid/live model runs still require a bounded budget. Required review, test and handoff precede ship. No Work Log storage-cap change, broader red-team scope, automatic model trust, or new orchestration system. Revert only the tested candidate and its generated metadata/fixtures, preserving unrelated state.

## Risks
Removing a ceiling can increase report noise or cause scope expansion. The finding rubric, out-of-scope decoys and baseline comparison must distinguish useful completeness from extra prose.

## Domain Decisions
- [CONSTRAINT] Report completeness and long-term traceability take precedence over a numeric response ceiling.
- [DECISION] Start with the Lite finding-cap hypothesis; keep unrelated global-cap decisions explicit and unchanged until justified.
- [TRADEOFF] Local scorer tests cannot establish that a model will report all findings; independent behavior evidence remains required.
