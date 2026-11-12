---
status: frozen
frozen: 2026-11-12
date: 2026-11-12
classification: feature
primary_domain: governance
signal_tier: none
signal_tier_note: "Adds no new rule or gate; removes or corrects existing text and deletes one unconsumed tool."
backlog: 245
---

# State-Surface Cleanup

## Goal and relationship

A read-only inventory on 2026-11-12 compared `.agent/rules/state_machine.md` with what the workflows write and what the validators check. The eleven canonical state names are prose: the persisted and enforced model is the Work Log `Current Phase` header plus `Gate:` receipts. That gap is left as it is. This spec fixes the smaller defects the inventory confirmed against source: lifecycle documents that contradict each other, state values nothing produces or reads, and one tool that carries a second, divergent phase table and has no caller.

INDEPENDENT. No new state, rule, gate, validator check or tool is added. Engine behaviour (what `validate.sh` / `validate.ps1` pass or fail) does not change.

## Scope and targets

### A. Contradictions

- **A1** `.agent/workflows/ship.md` step 6 requires `status: frozen` on produced Specs and ADRs. All eleven ADRs carry `status: accepted`, the value `doc-governance.md` assigns them, and no check reads ADR status. Narrow step 6 to specs.
- **A2** `.agent/workflows/spec-intake.md` §8b table names the post-ship status "`frozen` (shipped)". `ship.md` step 6 sets `status: shipped`, and the validator enum has `shipped`. Use `shipped`.
- **A3** `docs/specs/_product-backlog.md` states that Shipped and Cancelled rows live in the archive. Rows #225, #226 and #231 shipped on 2026-11-07 and are still in the active table, because `ship.md` step 4 flips the status and never moves the row. Move the three rows verbatim to `_product-backlog-archive.md`. `ship.md` step 4 is left unchanged (amended 2026-11-12, owner decision in chat after review): the archive file is this repo's convention, no deployed file creates it, and `ship.md` ships downstream.

### B. State values with no producer or reader

- **B1** `Context Budget tier` in `state_machine.md` (the `BOOTSTRAPPED → CLASSIFIED` line). No header field, workflow or check carries it. Delete the phrase.
- **B2** `Finalized` in `engineering_guardrails.md` §4.2 and `review.md` scope enforcement. Nothing writes this marker; `status: frozen` is the only freeze signal. Delete the word in both places.
- **B3** `Mode: Normal | Fast Lane` in `plan.md` (compact block, Token Budget Checkpoint, Phase Summary line), the `· Mode` item in the `shared-contracts.md` plan output line, and in `token-governance.md` §2 and §4 with its zh-TW twin. The plan writes it and nothing reads it; `AGENTS.md` Response Brevity already sets the terse default. Delete the field and the two guide lines that require it; keep the rest of the guide's overflow advice.

Withdrawn from the first proposal: `state_ok` in the plan and ship gate blocks. It is undefined, but it sits beside the Phase Verification bullet and is the visible slot for that check. It stays.

### C. Unconsumed tool

- **C1** Delete `.agentcortex/tools/verify_agent_evidence.py` and `.agentcortex/tests/test_verify_agent_evidence.py`. No workflow, validator or CI job calls the tool (backlog #245), and its `PHASE_RULES` disagree with `validate.sh` on quick-win, hotfix and feature.
- **C2** Remove its entries from `.test_durations`. Close backlog #245 and #108 (a parser bug inside the deleted tool). Reword backlog #122, which cites the tool as an exemplar.
- **C3** Leave shipped specs, the CHANGELOG history and archived work logs that mention the tool unchanged.

### D. Duplicated state and classification text

The inventory was delivered on 2026-11-12 and the owner chose in chat that day to fold its confirmed items into this unit.

- **D1** `engineering_guardrails.md` Reading Mode calls the tiny-fix mode "Skip Mode"; `bootstrap.md`, `state_machine.md` and the Work Log template call it `Lite`. Rename the guardrails label to `Lite Mode`.
- **D2** `AGENTS.md` Runtime rule 8 requires a spec in every plan; `plan.md` Spec Requirement Tiers exempts tiny-fix, quick-win and hotfix. Scope rule 8 to `feature` / `architecture-change`.
- **D3** `engineering_guardrails.md` Quick Mode says "Do NOT read this file"; `bootstrap.md` §0 grants one exemption (§13 on a governance-path edit). Name the exemption in the Quick Mode line.

Withdrawn after reading the contract tests: deleting `state_machine.md` §Classification Escalation Rules and the `routing.md` §4 rule 3 exclusion list. `tests/guard/test_classification_escalation.py` pins both as deliberate mirrors of guardrails §10.3 / §10.4 (the routing test names it "site 3 of the 4-way mirror"), and quick-win does not read the guardrails copy. They stay.

### E. Second sweep (amended 2026-11-12, owner decision in chat)

A second read-only sweep covered `.agent/config.yaml` and the seven phase workflows; every item below was re-read against source.

- **E1** (backlog #179) `handoff.md` §6: step 2 moves older details out, step 4 forbids rewriting `## Evidence`. State in step 4 that a verbatim move of a completed phase's entries is not a rewrite.
- **E2** (backlog #154) Delete the unread `raw_intake_cleanup` key. The validator check stays: it matches `spec-intake.md` step 4.
- **E3** Delete eight more config keys with zero references: four under `cluster` (`p0_warn_pct`, `max_declined_markers`, `declined_growth_threshold`, `declined_ttl_days`) and four under `downstream_capabilities` (`load_policy_ceiling`, `custom_prefix_required`, `kb_role_fixed`, `kb_manifest_trusted_default`). The validators hard-code the same values; the comments describing the downstream caps stay.
- **E4** `test.md` cites "AGENTS.md Gate 3" (two places) and "AGENTS.md Routing §2"; neither exists. Point them at the 5-Gate contract and §Classification Freeze.
- **E5** `review.md` Design Link Verification says "Route back to `/plan`"; the file's own Not Ready procedure routes to implement, and no validator table allows review → plan. Delete the sentence.

Recorded in the backlog instead: `production_paths` (new #246, needs an ADR-001 decision), nine citations of undeployed files (folded into #192), and the no-runner dead end for `feature` tiers (folded into #110).

## Acceptance Criteria

- AC-1: `ship.md` step 6 no longer asks for `status: frozen` on ADRs; no ADR file changes.
- AC-2: `spec-intake.md` §8b names the post-ship status `shipped`.
- AC-3: the active backlog table has no `Shipped` row; rows #225, #226, #231 appear in the archive with their text unchanged; `ship.md` step 4 is unchanged.
- AC-4: `Context Budget tier`, `Finalized` and `Fast Lane` have zero hits under `.agent/`, and `Fast Lane` has zero hits in both `token-governance` guides.
- AC-5: both tool files are gone; `verify_agent_evidence` has zero hits outside `CHANGELOG.md`, shipped specs, the backlog archive and `.agentcortex/context/archive/`.
- AC-6: the full CI-equivalent test suite passes; `validate.sh` and `validate.ps1` both report `fail=0`; the directive-count ratchet and the state-machine contract test pass without loosening either.
- AC-7: the aggregate lifecycle token figure from `analyze_token_lifecycle.py` does not rise.
- AC-8: a real upgrade from v1.8.37 to this branch is run, and the report states whether the deleted tool is removed from, or left in, the downstream repo.
- AC-9: `Skip Mode` has zero hits under `.agent/`; `AGENTS.md` rule 8 names the two classifications it applies to; the guardrails Quick Mode line names the §13 exemption; `tests/guard/test_classification_escalation.py` is unchanged and passes.
- AC-10: the nine config keys named in E2 and E3 have zero hits in `.agent/config.yaml`, which still parses; `AGENTS.md Gate 3` and `Routing §2` have zero hits under `.agent/`; `review.md` no longer routes a Not Ready verdict to `/plan`; backlog #179 and #154 are in the archive.

## Non-goals

- Rewriting `state_machine.md` to the seven-phase model, or adding a phase-to-state mapping.
- Naming or recording a "blocked" state.
- Enforcing the escalation rules in code.
- Removing either test-pinned mirror named under D.

## Constraints

- Deletion-first: the touched governance surfaces end with fewer characters in total than they started; D2 and D3 add a short qualifier each and are paid for by B.
- `engineering_guardrails.md` edits may only lower the ADR-011 directive count.
- English only in repo artifacts; the zh-TW guide twin keeps parity with its source.

## Domain Decisions

- [DECISION] The eleven state names stay as descriptive prose. Making them the enforced model would add text for a path that plain-entry agents do not read (2026-11-07 plain-entry measurement).
- [DECISION] A status value with no producer and no reader is deleted, not documented.
- [TRADEOFF] Shipped rows are moved to the archive by hand in this repo; `ship.md` does not instruct it, so a row can sit in the active table until the next cleanup. Instructing it would push a repo-local file convention to every downstream install.
- [DECISION] The per-tier phase table lives in the validators only; the deleted tool held the one other copy, and it had drifted.
