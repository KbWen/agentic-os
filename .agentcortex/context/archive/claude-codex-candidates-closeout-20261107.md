# Work Log: claude/codex-candidates-closeout

## Header
- Branch: `claude/codex-candidates-closeout`
- Classification: `feature`
- Classified by: `claude`
- Frozen: `2026-11-07`
- Created Date: `2026-11-07`
- Owner: `claude`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `b65d54e`
- Checkpoint SHA: `4b1630f`
- Recommended Skills: `verification-before-completion, red-team-adversarial`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `221`

## Session Info
- Agent: `claude-opus-5-5`
- Session: `codex-closeout-20261107`
- Platform: `claude-code`
- Guardrails loaded: §1, §2, §4.1, §4.2, §4.5, §10, §11.1, §12, §13 (targeted re-read at closeout)

## Task Description
Finish the staged workflow-optimization work Codex left unmerged (owner instruction in chat 2026-11-07: finish it cleanly, roundtable on doubts, low-tier models for paid runs). It includes 11 Codex commits plus one local-only commit (A): three frozen specs (#225, #226, #231), eval fixtures and tests, the delete-bias comparator fix, and six wording candidates. Each candidate's frozen spec requires a matched comparison before adoption.

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-11-07 | feature: 3 frozen specs, governance domain |
| plan | done | 2026-11-07 | rebase, roundtable design, Haiku comparison, dispositions |
| implement | done | 2026-11-07 | 11471d7 |
| review | done | 2026-11-07 | R1 NOT READY → fixed → R2 PASS |
| test | done | 2026-11-07 | 1179 + 263 rerun |
| handoff | done | 2026-11-07 | ready to ship |
| ship | done | 2026-11-07 | SSoT 221->222 |

## Phase Summary
- bootstrap: feature (frozen specs #225/#226/#231, behaviour-boundary wording in rules/skills). Specs already frozen 2026-11-06 by owner; no new spec needed.
- plan: cherry-pick the Codex commits onto main. Run a roundtable (3 seats plus tenth man) on the comparison design. Run a Haiku matched comparison through a subagent (cap USD 10): wording candidates use the injected section with arm-blind grading; B uses real /bootstrap runs. Apply the mechanical rules; candidates with no benefit are reverted. Rollback: revert the squash commit.
- implement: 12 cherry-picks (one SSoT conflict resolved by keeping main, which dropped Codex's Last Verified refresh). Comparison spend USD 4.28. Owner adopted A (ADR-001 D3, chat 2026-11-07) and C1 (amended bar, chat 2026-11-07). B, M4, M7 and M9 reverted to baseline, and their candidate-pinning tests removed. Spec dispositions, backlog rows and the review doc written.
- review: R1 NOT READY (H-1 stale §9.2 protects line, early ship-state writes, evidence wording) → fixed 4b1630f → R2 PASS.
- test: full suite 1179 passed (2 fails fixed/race), rerun 263 passed.
- handoff: Resume written; ship-ready.
- ship: PASS; L2 governance entry (owner-approved preview, chat 2026-11-07); specs → shipped; backlog 225/226/231 → Shipped; ship:[doc=docs/reviews/2026-11-07-workflow-candidate-comparison.md][code=.agents/skills/red-team-adversarial/SKILL.md][log=.agentcortex/context/archive/claude-codex-candidates-closeout-20261107.md]
⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T12:48:58Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T12:48:58Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T12:48:58Z
- Gate: review | Verdict: NOT READY | Classification: feature | Timestamp: 2026-11-07T13:14:52Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T13:15:40Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T13:17:00Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T14:28:58Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T14:28:59Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-11-07T14:29:40Z

## External References
| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/numeric-output-cap-evaluation.md | #225, C1 adopted (amended bar) |
| Spec | docs/specs/context-sensitive-instruction-evaluation.md | #226, baselines retained |
| Spec | docs/specs/bootstrap-read-scope-optimization.md | #231, baseline retained |
| ADR | docs/adr/ADR-001-governance-friction-tuning.md | D3 amended (A) |
| Review | docs/reviews/2026-11-07-workflow-candidate-comparison.md | comparison results |

## Known Risk
- Rollback plan: revert the squash-merge commit of this PR; C1, A, specs, eval packets and tests return together. No data or schema surface.
- Haiku-only, injected-section evidence: an upper bound on effect; plain-entry agents do not read these files. Scoped in every disposition.
- C1 adopted below the original AC-2 bar by owner decision; noisier Lite reports possible (false findings fell in the test).
- Rollback: revert the squash commit; the candidates and tests return as one unit.

## Decisions
### D-1: Adopt C1 on a strict gain → consolidated: L2 governance
- Decision: replace the Lite "1-2 findings max" cap. Reason: true findings 7→9, false findings 3→1; the cap cannot report three defects. Alternatives: retain baseline per the original AC-2. Impact: Lite red-team reports may list more findings. Owner decision in chat, 2026-11-07.
### D-2: Amend ADR-001 Decision 3 → promoted: ADR-001
- Decision: reuse loaded context; no re-read for caching. Owner decision in chat, 2026-11-07.

## Conflict Resolution
none

## Security Findings
none: no code, secret, auth or deploy-surface change; the red-team skill edit removes a report-count cap only (scope, severity and escalation rules unchanged).

## Skill Notes
none

## Drift Log

- ADR Coverage Check: ADR-001 (Decision 3 amended by owner decision, chat 2026-11-07); ADR-005 (customized skills preserved on upgrade: the C1 red-team wording reaches customized downstream skills only via .acx-incoming); ADR-011 (AGENTS.md ≤8-line cap kept). No conflict.
- Read-before-write (§12.1): red-team-adversarial SKILL.md Lite block (finding/token caps, 2 lines changed); ADR-001 Decision 3 (dual-mode caching rule replaced); three frozen specs (Disposition appended); backlog rows 225/226/231; governance.yaml protects line restored to main.
- Disposition sections appended to the three frozen specs before /ship (spec-freshness record); C1 bar override = owner decision in chat 2026-11-07. Status flips to shipped and backlog closure deferred to /ship (review M-2).
- Cherry-pick conflict in current_state.md/.guard_receipt.json (Codex bootstrap Last Verified refresh); kept main's copy.
- Codex commit text claimed "owner approval" for the ADR-001 amendment with no record; replaced with the chat date of the actual owner decision.
- Recovered stale Work Log lock on 2026-11-07T14:28:58.826311+00:00; prior_owner=claude; prior_session=codex-closeout-20261107; reason=stale-time; lock=claude-codex-candidates-closeout.lock.json

## Review Feedback
- Round 2 (same reviewer, 11471d7..4b1630f): H-1, M-1, M-2, L-1–L-3 PROVEN fixed; L-4 withdrawn (template requires the sentinel). Verdict: PASS.
- Round 1 (independent acx-reviewer, read-only): NOT READY.
  - H-1: `.agentcortex/eval/governance.yaml:295` still names the reverted §9.2 heading → `test_protects_resolve_against_live_rule_inventory` fails. Fix: restore main's line.
  - M-1: Evidence claim "source diff = red-team + index only" was wrong (governance.yaml, A's docs). Fix: correct after H-1.
  - M-2: specs set `shipped` and backlog `Shipped` at implement, before /ship; Disposition text on frozen specs not in Drift Log. Fix: revert to frozen / In Progress for /ship to flip; log.
  - L-1: unreachable staging SHAs in tracked docs. L-2: secondary metrics selective (M4/M9 safety, M9 false findings). L-3: removal note omits M7. L-4: receipt timestamps shared; Phase Summary ⚡ ACX (kept: template requires it).

## Red Team Findings
- C1 is a red-team skill change; reviewer checked the Lite block only drops the count cap (scope, severity, escalation unchanged). No HIGH findings.

## Design Reference
none

## Observability
- Sink: n/a | Scope: docs, skill wording, eval data, tests, shell comparator tool (exit-code fix only) | Verified: no runtime error paths added

## Resume
- State: TESTED, handoff done; next is /ship on this branch (checkpoint 4b1630f).
- Completed: Codex staging replayed; Haiku comparison; C1 + A adopted by owner; B/M4/M7/M9 retained; review R2 PASS; tests green.
- Next: /ship (L2 governance entry approved by owner in chat 2026-11-07; specs → shipped; backlog 225/226/231 → Shipped; Spec Index +3 with cap fold; ADR-001 index line); PR + CI; then release v1.8.37.
- Context: owner decisions live only in chat 2026-11-07 and are cited by date in the ADR, spec Dispositions and this log.
### Read Map
- docs/reviews/2026-11-07-workflow-candidate-comparison.md; the three spec Disposition sections; this log's Decisions and Review Feedback.
### Skip List
- `.agentcortex/context/private/candidate-compare/` raw runs (evidence only); Codex staging worktrees.
### Context Snapshot
- Behaviour delta vs main: red-team Lite block (C1); ADR-001 D3 + context-budget.md + 2 quickstarts (A). Everything else is specs, eval data, tests, tool fix, docs.

## Test Gate Results
- Full `pytest -n 6 tests/ci tests/guard .agentcortex/tests` at 11471d7: 1179 passed, 2 skipped, 2 failed → H-1 governance.yaml (fixed 4b1630f) and validator count parity (race: Work Log edited mid-run; standalone validate.sh = validate.ps1 = pass 114 / warn 8 / fail 0).
- Re-run at 4b1630f (governance_eval, validator_false_positives, context/lite/screen/delete-bias, lifecycle activation): 263 passed, 0 failed.
- Linter: none configured for markdown/YAML beyond validators; `generate_compact_index.py --check` fresh.

## Evidence
- 12 cherry-picks onto b65d54e: OK (1 SSoT conflict resolved to main).
- Pre-disposition tree: guard+lifecycle+2 ci modules 808 passed.
- Comparison: `.agentcortex/context/private/candidate-compare/RESULTS.md`, ledger 207 calls, USD 4.282; primary spot-checked C1 lite-c transcripts (baseline 2/1/1 defects, candidate 2/2/2).
- Post-review (4b1630f): byte-identical to main: bootstrap.md, engineering_guardrails.md, doc-lookup SKILL.md, governance.yaml. Behaviour diff vs main: red-team SKILL.md Lite block (C1) + compact index; A = ADR-001 D3 + context-budget.md + 2 quickstarts. Rest: specs, eval packets, tests, tool fix, review docs.
- `test_governance_eval.py` + `test_context_instruction_cases.py` serial: 83 passed.
