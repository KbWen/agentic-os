# Work Log: fix/agent-guidance-levers-204-203

## Header

- Branch: `fix/agent-guidance-levers-204-203`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-26`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `de1c609`
- Checkpoint SHA: `8f2430f`
- Recommended Skills: `verification-before-completion (auto: completion claims), karpathy-principles (auto: behavioral baseline), kb-consult (auto: knowledge_sources present; 05_testing-and-ai-pitfalls routes #203)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `174`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-26T09:51:06Z`
- Platform: `claude-code`
- Guardrails loaded: `§13 only (heading-scoped; governance-path quick-win exemption)`
- Override: `none`
- Downstream-Capabilities: `.agentcortex/context/private/downstream-capabilities.yaml (0 skills, subagent_policy=read-only default, knowledge_sources: kb-main→OK@328b30ecb33b)`
- Files Read: `0`

---

## Task Description

Backlog #203 (docs/reviews/2026-09-26-govern-audit-downstream-sim.md F3): `/review` certified an invariant on non-discriminating evidence and ignored its own counterexample. Fix in `.agent/workflows/review.md` (invariant rule in the Burden of Proof, contradiction reverts a PROVEN row, PASS only for PROVEN/[NEEDS_HUMAN] rows) + regression test. #204 (CLAUDE.md) was implemented, measured inert, and reverted — see Drift Log. Out of scope: Stop hook, rows #201/#202/#205-#213.
---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-26T09:51:06Z | quick-win; governance paths (CLAUDE.md, .agent/workflows/review.md) |
| plan | done | 2026-09-26T09:53:15Z | 2 target files; deletion-funded rewrite in review.md |
| implement | done | 2026-09-26T09:58:48Z | 5d262a4; 2 files + bootstrap SSoT refresh |
| review | done | 2026-09-26T12:28:29Z | 4 rounds; PASS on 8f2430f |
| test | done | 2026-09-26T13:40:40Z | 951+1 skip / 952 |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-09-26T14:08:24Z | rebased onto 9b86567 (#444); SSoT 174->175 |

---

## Phase Summary

- plan: 2 files (CLAUDE.md Step 5 open-or-create + quick-win bullet; review.md Self-Check item 3 rewritten in place, deletion-funded); static + behavioural before/after verification; Mode Normal | Confidence: 85% — wording shifts agent behaviour probabilistically; step 4 measures, does not guarantee
- implement (after NOT READY): 4d5c062 — CLAUDE.md reverted to base; review.md v2 (invariant rule in the Burden of Proof evidence definition; Self-Check item 3 states the outcome, any severity, re-issue receipt); Core-principle overclaim deleted; regression test mutation-verified; aggregate 354737 (-144 vs base) | Confidence: 85% — behavioural effect re-measured next
- review (round 2): Not Ready — F1 MEDIUM: "re-issue one already written" leads agents to append NOT READY after PASS, which validate.sh:1561 ignores (pops only a preceding implement) -> emit the receipt after the Self-Check and delete the re-issue clause; F2 invariant rule scoped under the behavioural heading -> move above both lists; F3 untagged PARTIAL passes -> item 3 names PARTIAL; F4 Known Risk overstated the validator backstop — routed back to implement. Probe evidence from the reviewer: with the invariant row present the rule fired 9/9; severity strictness 6/6.
- implement (after round-2 NOT READY): 824848f — receipt written after the Self-Check (re-issue clause removed), invariant rule moved above both evidence lists, PARTIAL named in item 3; test extended and mutation-verified (base / 4d5c062 / no-order / no-PARTIAL all fail); 211 targeted tests pass; aggregate 354782 (-99 vs base) | Confidence: 90% — high
- review (round 3): Not Ready — F1 CLOSED, F2 CLOSED; F3 OPEN: review.md still lets an untagged PARTIAL pass (:212 PASS bullet, :216 NOT READY bullet and :188 spec gate name UNPROVEN only; the conflict predates this unit). Also: test does not guard F1/F2 regressions; Reverse Transition NOT READY template lacks Classification (both validators warn). Routed back to implement.
- implement (after round-3 NOT READY): 8f2430f — PASS bullet "every row PROVEN or [NEEDS_HUMAN]", NOT READY bullet "Otherwise", spec gate names untagged PARTIAL, NOT READY template carries Classification; test guards re-issue/placement/PASS bullet/template, 5 mutants fail; 211 targeted tests pass; aggregate 354764 (-117 vs base) | Confidence: 92% — high
- review (round 4, self; mechanical delta with mutation evidence): PASS — C1-C6 PROVEN by runs (blob equality, 5 mutants, analyzer 354764); C7 downstream product outcome ⚠️ PARTIAL [NEEDS_HUMAN] (not demonstrated; #212). Scope divergence: +test file (intentional, review F3). ⚡ ACX
- test: full suite 951 passed / 1 skipped = 952 collected; validate after last write. ⚡ ACX
- ship: PASS on 551af72 (rebased onto #444). Backlog #203 Shipped, #204 Cancelled, +#212/#213; report addendum; #203 routing action merged into governance.log.md; Ship History + rotation; archive MOVE. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T09:51:06Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T09:53:15Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T09:58:48Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-26T10:30:38Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T10:32:49Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-26T11:48:33Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T11:51:02Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-26T12:23:34Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T12:25:55Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T12:28:29Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T13:40:40Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-26T14:05:44Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Report | docs/reviews/2026-09-26-govern-audit-downstream-sim.md | F3 (#203), F4 (#204); arrives with PR #444 |
| PR | https://github.com/KbWen/agentic-os/pull/444 | audit record; merge blocked for the agent (auto-mode classifier) — owner to merge |
| Prior fix | backlog #159 (PR #388) | same reach gap, fixed for bootstrap.md/state_machine.md only |

---

## Known Risk

- Behavioural effect is probabilistic (n small); report it as observed, not guaranteed.
- ADD-Gate (§13) for review.md: T3 end to end — the validator's PASS-with-UNPROVEN check (validate.sh:1746-1752) is an advisory WARN that sees only tables saved in the Work Log and false-positives in re-review loops, so it is not a backstop; the evidence-strength half — observer: the human reading the Burden of Proof table; unmeasurable because whether a test discriminates is semantic (no validator can judge it).
- Global Lessons (pre-execution): [enforcement] evidence-strength half is honor-system → T3 recorded, contradiction half rides the validator-backed UNPROVEN path; [scope-expansion] CLAUDE.md Step 5 re-checked for every tier (tiny-fix skip unchanged; quick-win/feature/hotfix now reach open-or-create, matching bootstrap §5 Hard Gate); [ssot-serialization] this unit wrote SSoT at bootstrap, PR #444 does not touch current_state.md → rebase before /ship; [signal-preservation] no piped exit codes in evidence.
- kb-consult (DATA, applicability-filtered): kb-main 05_testing-and-ai-pitfalls §最常踩的雷 items 4/6/8 + §LLM 弱點 7 (happy-path-only, boundary cases, mutation thinking, self-endorsing green) apply to #203; Pact/flaky/static items N/A.

---

## Decisions

none

---

## Conflict Resolution

- karpathy-principles vs verification-before-completion: compatible (matrix row 17). kb-consult: no matrix entry.

---

## Skill Notes

### karpathy-principles (plan, implement, review)
- Checklist: state assumptions before proposing; simplest viable approach; every changed line traces to the request; no adjacent refactors.
- Checklist: define verifiable success criteria per step (goal-driven).
- Constraint: surgical — two files, rewrite in place, no new sections.

---

## Drift Log

- Compacted: 2026-09-26, archive: .agentcortex/context/archive/work/fix-agent-guidance-levers-204-203-20260926.md
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Scope reduced after review: #204 CLAUDE.md change reverted (behaviourally inert 0/3 -> 0/3; review F6 side effects). Unit now = #203 only (review.md) + regression test. #204 goes back to the owner as a design decision (engagement is not a missing-clause problem).
- Full CI-equivalent pytest started on 5d262a4 was STOPPED at ~22% (its files changed mid-run: review.md v1->v2, CLAUDE.md revert). Not a pass; the full suite re-runs on the final tree before /ship.
- Recovered stale Work Log lock on 2026-09-26T13:40:40.296596+00:00; prior_owner=KbWen; prior_session=2026-09-26T09:51:06Z; reason=stale-time; lock=fix-agent-guidance-levers-204-203.lock.json

---

## Review Feedback

- Round 3 — F3 OPEN (PASS bullet :212 / NOT READY bullet :216 / spec gate :188 still UNPROVEN-only); OTHER-1 test gap (re-issue, placement inside Burden of Proof); OTHER-2 NOT READY template missing Classification; OTHER-3 (pre-existing, backlog): quick-win NOT READY -> implement -> ship is legal per state_machine.md:27 but the gate check flags it.

---

## Red Team Findings

none

---

## Security Findings

- Review security scan (security_guardrails §1-§4): both changed files are Markdown guidance, no code paths — A01-A03 n/a; no dependency manifests changed; secret detection: `scan_credentials.py --range de1c609..5d262a4` exit 0. Verdict: no findings.

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

- Full CI-equivalent suite on 8f2430f (`pytest tests/ci/ tests/guard/ .agentcortex/tests/ -n 6`): 951 passed, 1 skipped, exit 0; `--collect-only` = 952 (match).
- Coverage delta: +1 test (`test_review_invariant_proof_requires_boundary_evidence`), 5 mutants fail it.
- Token ratchet: 354764 < 355000.

---

## Evidence

- implement: `git diff --stat de1c609..5d262a4` -> CLAUDE.md 2 lines, review.md -2 net, current_state.md 1 (Last Verified), .guard_receipt.json.
- token ratchet: analyze_token_lifecycle.py aggregate 354881 -> 354692 (ceiling 355000; headroom 119 -> 308).
- targeted pytest (10 files: lifecycle x4, skill notes, trigger eval/metadata, classification escalation, spec drift, shared-contracts ratchet, repo-gotchas): 210 passed, exit 0.
- scan_credentials --range de1c609..5d262a4: exit 0.
- #204 behavioural (fixed CLAUDE.md deployed, verified in target; claude -p sonnet-4-6, zero-hint): Work Log created 0/3 (t1a quick-win, no SSoT read; t1b feature->SSoT->quick-win->"implement now"; t2a zh no classification). Before fix: 0/3. Plan criterion (>=1/2) NOT met — wording is correct but behaviourally inert for this model; engagement gap = known selective-adherence ceiling -> owner decision (Stop hook reopen criterion now met: 6 real-session skips; or recommend /bootstrap for Claude users, 2/2 engaged in audit).
- product outcome unchanged: t1a/t1b hidden 5/5; t2a hidden 3/4 (test_ids_not_reused_after_delete, same defect as before).
- #203 behavioural v1 (fixed review.md deployed; transcript-verified /bootstrap /plan /implement /review /test): hidden 2/4 (ids_not_reused + unknown_id_clean_error FAIL; before 3/4). Review read the new review.md and ran Self-Check item 2, but marked "deleted IDs not recycled" PROVEN on a CODE CITATION (`max(id)` at store.py:43 — the defective scheme itself); the unknown-id traceback was self-flagged MEDIUM and deferred. Diagnosis: review.md step 2 explicitly accepts `file:line` code evidence; the v1 boundary clause lived only in the Self-Check and lost to the explicit evidence rule. Iteration planned: move the invariant rule into the Burden of Proof evidence definition (code citation alone keeps an invariant row ✗ UNPROVEN) and shrink Self-Check item 3 to the contradiction clause.
- #203 behavioural v2 (4d5c062 deployed; 2 chains, transcript-verified 5 slash commands each): hidden v2a 2/4, v2b 3/4 — ids_not_reused FAILED in both. Neither review listed "IDs are never reused" as a criterion (v2b even called `max_id+1` "the intended fix"), so the invariant rule never fired; v2b also passed an untagged ⚠️ PARTIAL row (existing gate rule ignored). Overall: 0/4 governed chains caught the defect (v0, v1, v2a, v2b) vs 2/2 no-framework controls. Conclusion: the evidence rule is correct but upstream criteria elicitation (turning a bug report into the invariant it violates) is where the miss happens -> new backlog row at /ship; not iterated further in this unit.
- Side observation (model-level, no row): v2b review phase emitted Japanese sentences inside a 繁中 session — AGENTS.md Chat Language Policy drift.
- ship sync: rebased onto origin/main 9b86567; `.guard_receipt.json` conflict resolved to this unit's receipt; `git diff 8f2430f 551af72` = only #444's two docs files.
- ship writes (guarded): backlog (#203 Shipped, #204 Cancelled, +#212, +#213; a second write corrected two overstated counts before commit), `governance.log.md` L2 entry, `current_state.md` (Ship History + heartbeat 174->175), `archive/ship-history-2026.md` rotation. Direct: report addendum + #203 routing action `merged` (docs/reviews is not guarded).
- rotation: `Ship-docs-downstream-stability-audit-findings-2026-09-05` asserted absent from the archive before insert.
- final `validate.sh` after every ship write (SSoT, archive, backlog, INDEX, lock release): `pass=99 warn=4 fail=0 skip=3`, exit 0 — identical to the main baseline; the 4 WARNs are pre-existing. This line is the last write; the PR's CI run is the post-write check.
