---
status: draft
title: Conflicting-Directive Scan + Resolution
date: 2026-07-26
classification: feature
source: backlog #145
primary_domain: governance
secondary_domains: [tooling]
signal_tier: T1
signal_tier_note: >
  The durable instrument is a section-reference consistency test in tests/ci/
  (AC-7): every Work-Log-scoped `## Section` cited by a governance surface must
  exist in .agentcortex/templates/worklog.md, capped at today via a committed
  allowlist. That covers Category C only — the one slice of the conflict axis
  that is machine-checkable. Categories M/A/B/D/E are resolved by EDIT (delete
  or correct the contradicting text), not by adding a watcher: per
  [enforcement], a rule with no feasible tier should be deleted rather than
  left as honor-system theatre, and per this repo's north star, resolving a
  conflict by adding a clarifying rule is the densification the external
  guidance warns against.
applies_to:
  - "AGENTS.md"
  - ".agent/rules/engineering_guardrails.md"
  - ".agent/rules/security_guardrails.md"
  - ".agent/workflows/bootstrap.md"
  - ".agent/workflows/plan.md"
  - ".agent/workflows/handoff.md"
  - ".agentcortex/templates/worklog.md"
  - "docs/reviews/2026-07-26-conflicting-directive-scan.md"
---

# Conflicting-Directive Scan + Resolution

## Problem

ADR-011 swept the phase-entry surfaces for **enforcement backing**. It never asked whether
directives **contradict each other**. The census
(`docs/reviews/2026-07-26-conflicting-directive-scan.md`) found **10 confirmed conflicts and
1 negative result**, every row carrying a `file:line` citation and passing the precedence
test (a candidate counts only if the declared chain does not resolve it, or resolves it
silently with no gate).

Three facts frame the work:

1. **The root cause is a two-line omission.** `AGENTS.md §Skill Safety & Precedence` item 2
   declares `AGENTS.md > .agent/workflows/ > .agent/skills/` and omits `.agent/rules/*`,
   `.agentcortex/templates/*`, and `docs/adr/*` — the surfaces carrying most directives
   (`engineering_guardrails.md` alone holds 84 hard-directive keyword hits). For most census
   rows there is no declared tie-breaker at all.
2. **Three findings are live, not theoretical.** C3 and C4 were violated silently by this
   task's own Work Logs; B1 was found by walking into it mid-bootstrap; E1 fired twice during
   the session that produced this spec. None was caught by any gate, validator, or review.
3. **The ADR-011 durable pattern does not transfer.** Conflicts are semantic and cannot be
   counted. Only Category C admits a machine check.

## Goals

- Resolve every confirmed census row by **editing the contradicting text**, preferring
  deletion or correction over clarification.
- Close the root cause (M1) so future conflicts have a declared tie-breaker.
- Ship one durable machine check for the one slice that supports it (Category C).
- Keep the change **token-neutral or negative** on the always-loaded surfaces (§13
  Deletion-First), funded by a real deletion rather than a waiver.

## Non-goals

- A general-purpose semantic conflict detector. Not feasible; claiming otherwise would be the
  false-confidence failure `[enforcement]` names.
- Re-running the ADR-011 enforcement census. Different axis, already done.
- Rewriting `§9.2` (vague inputs) or any rule the census did not flag.
- Adding a periodic re-scan duty. That is the observer honor-system process ADR-011 retired.

## Dispositions

Every row resolves to **delete · correct · add-artifact**. No `defer` (repo norm).

| # | Finding | Disposition | Change |
|---|---|---|---|
| **M1** | Precedence chain omits `.agent/rules/`, templates, ADRs | **correct** | `AGENTS.md` item 2 becomes `AGENTS.md > .agent/rules/ > .agent/workflows/ > .agent/skills/`, plus one clause: an accepted ADR governs within its declared `applies_to` scope. No new MUST keyword — the ratchet baseline (AGENTS.md 37) stays flat. |
| **A1** | Read-Once vs the guardrails' own conditional-load design | **correct** | Extend the existing Read-Once exemption — which already names `shared-contracts.md` — to cover guardrails sections the file itself marks conditional. Reuses the established carve-out shape; adds no rule. |
| **B1** | Exhaustive SSoT-write list excludes `/bootstrap`, which writes | **correct** | Add `/bootstrap` (Last Verified only) to the exhaustive list in `AGENTS.md`. The write is intentional and feeds the 14-day staleness advisory; the list is simply wrong. An honest list beats a clean false one. |
| **C1** | `## Security Findings` MUST-recorded, absent from template | **add-artifact** | Add the section to `worklog.md`. The template is lifecycle-uncounted, so this costs nothing against the 355k ceiling. |
| **C2** | `## Lessons` read by the §10.6 Completion Guard, absent from template | **add-artifact** | Same. Without it the retro check can never pass on a conformant log. |
| **C3** | `## Risks` (3 workflows) vs `## Known Risk` (template + contract + validator) | **correct** | Rename the 3 workflow mentions to `## Known Risk`. Changing 3 citations is smaller than changing the template, the `AGENTS.md` Work Log Contract, and the validator. |
| **C4** | `bootstrap.md` says write `## Recommended Skills` as a section; template has a header field | **correct** | Fix the `bootstrap.md` wording to name the header field. |
| **C5/C6** | `## Spec Seeds`, `## Research Findings` absent from template | **add-artifact** | Add both. They are written by `/retro` and `/research` respectively and are currently undeclared ad-hoc headings. |
| **D1** | "DEFER" carries two opposite senses | **correct** | Reword `guardrails §8` / `§8.1` to "escalate to user", leaving ADR-011's `no defer` unambiguous. Pure ambiguity removal, no net-add. |
| **E1** | `§9.1` says `好` MUST NOT execute; Runtime item 6 says explicit intent executes | **delete** | Delete `§9.1`. It is already dead text — unenforced, unnoticed, and overridden in practice twice this session. `§9.2` (vague inputs) stays. |
| **F1** | `spec` is a mandatory gate that no validator transition table accepts | **correct** | Add the node to all three tables in both validators: `'bootstrap': ['plan','spec']` and `'spec': ['plan']`. Makes the documented flow recordable. **Alternative (flagged below)**: drop `spec` from the `§10.2` gate list instead and state that its evidence is the spec ARTIFACT, not a receipt. |

**Token funding**: the E1 deletion and the D1 reword are net-negative on
`engineering_guardrails.md`; M1/A1/B1 are single clauses on `AGENTS.md`. Template additions
are lifecycle-uncounted. The change is expected to land net-neutral or negative on the
counted surfaces — verified at implement, not assumed.

## Acceptance Criteria

- **AC-1** `AGENTS.md` precedence clause names `.agent/rules/` in order, and states the ADR
  scope rule. Directive-count ratchet stays at or below the committed baseline (37).
- **AC-2** Read-Once exemption covers the guardrails' self-declared conditional sections.
- **AC-3** The `AGENTS.md` non-ship SSoT exception list includes `/bootstrap` (Last Verified
  only), and `bootstrap.md §1` is unchanged — the list was the wrong side.
- **AC-4** `worklog.md` contains `## Security Findings`, `## Lessons`, `## Spec Seeds`,
  `## Research Findings`. Existing sections unchanged.
- **AC-5** Zero remaining `## Risks` references in `.agent/workflows/*`; all read
  `## Known Risk`.
- **AC-6** `bootstrap.md §3.6` names `Recommended Skills` as a header field, not a `##`
  section.
- **AC-7** `tests/ci/test_worklog_section_refs.py` exists and passes: every Work-Log-scoped
  `` `## X` `` reference across `AGENTS.md`, `.agent/rules/*`, `.agent/workflows/*`,
  `.claude/commands/*` resolves to a section in `worklog.md`, with a committed allowlist for
  references that legitimately name `current_state.md` / spec / ADR sections. Cap-at-today;
  FAILs on a new unresolved reference. Carries an anti-vacuity guard proving the detector
  fires on a synthetic bad reference.
- **AC-8** `§9.1` is deleted; `§9.2` is intact; no replacement rule is added.
- **AC-9** The census snapshot is committed unchanged as the point-in-time record. No
  re-snapshot duty is created.
- **AC-10** Net token delta on the lifecycle-counted surfaces is ≤ 0, measured with
  `analyze_token_lifecycle.py`, not estimated.

## Domain Decisions

- **[DECISION] Fix by edit, not by watcher.** Categories M/A/B/D/E get no detector. A
  semantic conflict detector is infeasible, and a rule-about-rules with no teeth is the
  false-confidence pattern `[enforcement]` names. The edits remove the contradictions; nothing
  needs to keep watching for them.
- **[DECISION] Delete `§9.1` rather than carve out an exception.** A carve-out ("unless it
  answers a question the agent asked") is a third rule about two rules — denser surface, same
  failure mode. The rule is already unenforced and already overridden; deleting it makes the
  written state match the real state.
- **[TRADEOFF] Adding `/bootstrap` to the "exhaustive" SSoT list weakens the
  only-`/ship`-writes principle** in exchange for the list being true. Accepted: a false
  exhaustive list is worse than a slightly broader true one, and the alternative (deleting
  bootstrap's Last Verified write) would silently disable the 14-day staleness advisory.
- **[CONSTRAINT] Category C's check needs a hand-maintained allowlist** for non-Work-Log
  section references. That allowlist is itself drift-prone — an honest ceiling recorded here,
  not hidden. It is still strictly better than the current state, which has no check at all.

## Open for human decision

Two dispositions change agent-visible behaviour and are flagged rather than assumed:

1. **E1 delete vs carve-out.** The spec recommends deletion on doctrine (`[enforcement]` +
   DELETE-bias + the external guidance). A reader who values the "don't act on a bare 好"
   intent may prefer a carve-out. The census shows the rule is already not doing that work.
2. **M1's ADR clause.** Stating that an accepted ADR governs within its `applies_to` scope is
   a genuine precedence decision, not a clarification. If it is judged to be an
   architecture-level change it should be recorded as its own ADR rather than an `AGENTS.md`
   clause.

3. **F1 — teach the validator `spec`, or stop calling it a gate.** Adding the node makes the
   documented flow recordable and every future `feature` log honest, at the cost of touching
   both validators (sh + ps1 parity mandatory). Dropping `spec` from the `§10.2` gate list
   instead is a smaller edit and arguably more truthful — the Spec Gate really is enforced by
   the artifact on disk, not by a receipt — but it makes the guardrails table stop describing
   the phase sequence agents actually walk. The census cannot decide this one; it is a
   question about what a "gate" means in this framework.
