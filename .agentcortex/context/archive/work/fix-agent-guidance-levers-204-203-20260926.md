# Work Log overflow: fix/agent-guidance-levers-204-203 (compaction, 2026-09-26)

## Phase Summary

- Compaction overflow of the still-active log `.agentcortex/context/work/fix-agent-guidance-levers-204-203.md` (handoff.md §6). Holds its three oldest Phase Summary entries, round-1 Review Feedback and three older Drift Log lines; the active log keeps every protected section. ⚡ ACX

## Moved: Phase Summary (oldest)

- bootstrap: classified quick-win (bootstrap §0: CLAUDE.md edit => minimum quick-win; 2 governance files, clear scope). Guardrails read limited to §13. ADR check: no_covering_adr (coverage check n/a for quick-win; no_adr_at_all not triggered). Skills: verification-before-completion, karpathy-principles, kb-consult. ⚡ ACX
- implement: CLAUDE.md (Step 5 open-or-create, quick-win names Step 5) + review.md (Self-Check item 3 rewritten; redundant receipt-location sentence deleted to fund it) at 5d262a4; lifecycle aggregate 354881 -> 354692; 210 targeted tests pass; no scope divergence | Confidence: 90% — high
- review: Not Ready — F1 (review.md item 3 states no outcome for a boundary miss; revert lands after the receipt), F2 (validator backstop is WARN-only, FP in re-review loops, blind to chat-only tables — claim overstated), F3 (no regression test; base text passes all tests) — routed back to implement. Also adopted: F4 any-severity, F5 two PROVEN bars (matches behavioural v1 failure), F6 + measured null effect -> revert CLAUDE.md.

## Moved: Review Feedback (round 1)

- F1 MEDIUM: Self-Check item 3 v1 gives no outcome for an evidence miss and runs after the receipt instruction (review.md:209) -> state the outcome, route it to the NOT READY rule, re-issue a written receipt.
- F2 MEDIUM: validate.sh:1942 PASS-with-UNPROVEN is WARN-only, false-positives in NOT READY -> re-review loops (Review Feedback keeps round-1 rows), blind when the table is chat-only -> #203 is T3 end to end; correct the claim.
- F3 MEDIUM: no test covers either change (0 tests mention UNPROVEN) -> add a review.md contract assertion; mutation-verify.
- F4/F5 LOW: any-severity contradiction; one PROVEN bar (code citation must not prove an invariant) -> put the rule in the Burden of Proof evidence definition.
- F6 LOW: CLAUDE.md "else create it" skips lock/multi-person lookup and fires for pre-bootstrap research -> with the measured 0/3 -> 0/3 null effect, REVERT the CLAUDE.md change.

## Moved: Drift Log (older)

- Backlog status advance (Pending -> In Progress) for #203/#204 not possible on this branch: the rows arrive with PR #444 (unmerged). Status is set at /ship after rebasing onto a main that contains #444.
- Label-cluster advisory (bootstrap §1.5): label `governance` has 3+ pending rows without a parent spec; advisory noted, not blocking; the owner asked to keep pushing.
- SSoT Last Verified was 2026-09-09 (17 days) — advisory; refreshed via guard_context_write.py at bootstrap.

## Moved: Known Risk (superseded)

- Token ratchet: aggregate 354881 / 355000 (headroom 119) at bootstrap; review.md is counted (PHASE_WORKFLOW_MAP). Mitigation: rewrite-in-place of Self-Check item 3 (deletion-funded), measure before commit.
- CLAUDE.md is always loaded for Claude: keep net growth to one clause; no MUST/NEVER; no receipt format (memory: trigger-only top layer).

## Moved: Review Feedback (round 2)

- Round 2 — F1 MEDIUM: receipt-order/re-issue path invisible to the gate (pre-existing validator gap: PASS then NOT READY is ignored) -> doc reorder now; validator fix filed for this wave. F2 LOW: invariant paragraph placement. F3 LOW: PARTIAL not named in the NOT READY trigger. F4 LOW: Known Risk wording.
