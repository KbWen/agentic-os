# Work Log: fix/kb-consult-routed-order-218

## Header

- Branch: `fix/kb-consult-routed-order-218`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `2026-10-17`
- Created Date: `2026-10-17`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `091fcfc`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `196`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-17 13:29 UTC` (8ab306f9)
- Platform: `claude-code`

---

## Task Description

Backlog #218: the `kb-consult` row (`bootstrap.md` §3.6) says "smallest `approx_tokens` first", which overrides the KB's routed order (secondary standard read before the core one), and "query `task_routing`" lets agents print the whole routing table (~3K of a 5–7K consult). Keep routed order, use `approx_tokens` only to stop, and read only the task's routing entry — token-neutral. Stacked on PR #470 (owner request 2026-10-17 chat).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-17 | quick-win per backlog Tier |
| plan | done | 2026-10-17 | inline plan below |
| implement | done | 2026-10-17 | 2 wording rounds |
| review | done | 2026-10-17 | null-result adjudication |
| test | done | 2026-10-17 | 18 headless sessions |
| ship | done | 2026-10-17 | SSoT 196->197; #218 row archived |

---

## Phase Summary

- bootstrap: quick-win (one §3.6 row + the KB guide sentence that repeats the rule). Lifecycle aggregate 354,709 vs 355,000 ceiling — edit must be net ≤ 0 chars.
- plan: Targets `.agent/workflows/bootstrap.md` row `kb-consult` (via guard) and `.agentcortex/docs/guides/connecting-a-knowledge-base.md` §approx_tokens. Wording: "read only the task's `task_routing` entry, never the whole table"; "routed order; `approx_tokens` only to stop"; funded by tightening the applicability clause ("a bounded pass keeps only" → "keep only", same meaning) — net −4 chars. Evidence: headless `claude -p` sessions on a synthetic KB (30 routes; route `database-migrations` = core 2,400 tok then secondary 600 tok), old-row vs new-row arms, scored from the transcript's tool calls (read order; whether the whole table/manifest was printed). Rollback: revert the commit.
- implement: round 1 ("read only the task's entry, never the whole table") → 1/2 whole-manifest reads in the new arm, so round 2 made it an action: "grep the entrypoint for the task's `task_routing` key, never read the whole file"; "routed order; `approx_tokens` only to stop". Funded by "a bounded pass keeps only" → "keep only", "become blockers" → "block", "the routed page's" → "the page's". Row net −5 chars; lifecycle 354,709 → 354,704. KB guide §approx_tokens now says the same.
- review: Measured result is NULL on sonnet-5.5 (8 vs 8): order inverted 0/8 both arms, whole-manifest reads 2/8 both arms, manifest chars 39,059 vs 35,953 total, plans equal (8/8 batched backfill). Kept anyway: the old text instructed an order that contradicts the KB's routing (and the guide repeated it); the edit is token-negative and changes no gate. No savings are claimed. #218 closes with the finding; reopen trigger: a consult transcript that reads secondary-before-core, or a model/KB shape where wording is shown to move whole-table reads. Verdict PASS.
- test: lifecycle ceiling + baseline drift + directive ratchet 56 passed; validate.sh = validate.ps1 `pass=116 warn=5 fail=0 skip=2`; compact index fresh.
- ship: PASS; #218 Shipped (null result recorded), row archived; queue starts at #217; SSoT 196->197.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:29:25Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:31:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:38:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:41:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:42:30Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:43:43Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog.md | row #218 |
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | consume ladder |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/470 | stacked |

---

## Known Risk

- The sim isolates the rule text (no full bootstrap); it measures what the wording makes an agent do, not a whole downstream session.

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

- `bootstrap.md` edited (guarded write, 13:29Z) before this Work Log was written; plan was settled in chat first.
- Implement/review/test receipt timestamps reconstructed from the session timeline (ordered, not after the ship clock read).
- Sim harness, fixture and transcripts are scratchpad-only (`sim218/`: build.py, run.sh, score.py); not committed.

---

## Review Feedback

none

---

## Red Team Findings

none

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

none

---

## Evidence

- Sim: `claude -p --model sonnet` (resolved `claude-sonnet-5-5`, read from transcripts), host CLAUDE* env cleared, fresh copy per run; arm = RULE.md (HEAD row vs new row) + synthetic KB (31 routes, manifest 13,432 B; route `database-migrations` = core 2,400 tok, then secondary 600 tok) + TASK (/plan, NOT NULL column + backfill). Scored from tool calls only.
- Round 1 (n=2 each): whole-manifest reads old 1/2, new 1/2.
- Final (n=8 each): old — inverted 0, whole 2, manifest chars total 39,059 (median 2,472, max 15,109); new — inverted 0, whole 2, total 35,953 (median 4,199, max 8,880). Both 8/8 plans name a batched backfill.
- `pytest .agentcortex/tests/test_lifecycle_token_consumption.py tests/ci/test_lifecycle_baseline_drift.py tests/ci/test_directive_count_ratchet.py` → 56 passed. Aggregate 354,704 (ceiling 355,000).
- validate.sh `pass=116 warn=5 fail=0 skip=2`; validate.ps1 identical.
