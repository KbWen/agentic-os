---
status: draft
title: Conflicting-Directive Scan + Resolution
date: 2026-07-26
revised: 2026-07-26
classification: feature
source: backlog #145
primary_domain: governance
secondary_domains: [tooling]
signal_tier: T1
signal_tier_note: >
  ONE narrow machine check (AC-9): a fenced-block-aware consistency test pinning
  the `## Known Risk` naming across .agent/workflows/*, .agentcortex/docs/guides/*
  and the worklog template. That is the only surviving finding with a real
  recurrence risk. Every other disposition is a text correction with an honest
  per-directive tier of NONE recorded in the table below -- not a blanket claim.
  The first draft asserted a blanket T1 that its own note conceded covered one
  category; ADR-011 Decision 2 requires per-directive tiers, so this revision
  states them individually.
applies_to:
  - "AGENTS.md"
  - ".agent/rules/engineering_guardrails.md"
  - ".agent/workflows/plan.md"
  - ".agent/workflows/bootstrap.md"
  - ".agent/workflows/handoff.md"
  - ".claude/commands/*.md"
  - ".agentcortex/docs/guides/token-governance.md"
  - "docs/reviews/2026-07-26-conflicting-directive-scan.md"
---

# Conflicting-Directive Scan + Resolution

## Revision note

The first draft of this spec proposed 11 dispositions. A 4-seat adversarial roundtable refuted
**9 of the underlying findings**, and showed that **two of the proposed fixes were actively
harmful** — adding `## Security Findings` and `## Lessons` to the Work Log template would each
have silently disabled a live check. One "headline finding" turned out to be an error this
repo had already recorded and closed **twice**.

This revision is smaller, touches no template, adds no directive, and states an honest tier per
row. The refuted rows are retained in the census so they are not re-proposed.

## Problem

ADR-011 swept the phase-entry surfaces for **enforcement backing**. It never asked whether
directives **contradict each other**. The census
(`docs/reviews/2026-07-26-conflicting-directive-scan.md`) records **7 surviving findings**,
each `file:line`-cited and re-verified by the primary after review.

**Honest ceiling on record**: `[audit-method][HIGH]` requires an external signal for an
architecture-level audit. The `ask-openrouter` path was live but six free-tier models failed
across two attempts, and a paid model is high-cost (§8.2 → needs user confirmation, not
obtained). All review seats were same-vendor. The judgment calls below are **not** externally
validated.

## Goals

- Resolve the 7 surviving findings by **correcting or deleting text**. No new directive.
- Prevent recurrence of the single error class that has now bitten three separate sessions
  (writing a `Gate:` receipt for a receipt-less entry in the `§10.2` gate table).
- Stay within a **zero-headroom** ratchet: `AGENTS.md` is at 37/37.

## Non-goals

- Any change to `.agentcortex/templates/worklog.md`. Verified harmful (disables
  `validate.sh:1691` and `§10.6` item 3) and budget-hostile (+4 sections ≈ 74% of the 300-line
  compaction budget at zero content).
- A general semantic conflict detector. Infeasible; claiming otherwise is the false-confidence
  failure `[enforcement]` names.
- Re-proposing any refuted row. The census records why each fails.
- Tightening `LEGAL_STRICT` to force `implement → review`. Reverse edges are deliberate
  (`validate.sh:1385-1394` comments); changing them risks breaking real flows for a docs
  mismatch.

## Dispositions

Tier is stated **per row** (ADR-011 Decision 2). Honest `NONE` is allowed and used.

| # | Finding | Disposition | Change | Tier |
|---|---|---|---|---|
| **S1** | `AGENTS.md` ranks surfaces in a skill-scoped rule while designating `.agent/rules/` as Constitution elsewhere | **correct (scope, not extend)** | Reword `AGENTS.md:94` item 2 so its scope is explicit — it resolves **skill-vs-workflow** conflicts. Do **not** insert `.agent/rules/` into the order: that would rank the Constitution below `AGENTS.md` and loop through the 4 ADRs declaring `applies_to: AGENTS.md`. Keyword-free, net char delta ≈ 0. | NONE (wording clarity; nothing can gate a precedence reading) |
| **S2** | `## Risks` vs `## Known Risk` across 5 sites | **correct** | Rename `plan.md:143`, `plan.md:169` (bare heading **inside a fenced block**), `bootstrap.md:142`, `handoff.md:148`, `token-governance.md:115` to `## Known Risk`. Resolves the `handoff.md:141`↔`:148` intra-file contradiction. | **T1** — AC-9 |
| **S3** | 23 of 30 command stubs require re-reading `AGENTS.md`, which `CLAUDE.md:5` says is already `@import`ed and `AGENTS.md:27` makes a Token Leak violation to re-read | **delete** | Remove the redundant `AGENTS.md` Required-read line from the 23 stubs, and the `security_guardrails.md` line from `implement.md:8` / `ship.md:8`. This is #126's fix applied to the class it actually missed. **Net-negative tokens** — funds the rest under §13. | NONE (stub content is unpinned; the deletion removes the conflict rather than watching it) |
| **S4** | `§10.6` item 2 probes for a `## Resume` block the template always ships → already vacuous | **correct** | Change both probes from presence to content (`## Resume` / `## Lessons` containing more than `none`). Fixes the broken probe **without** breaking the working one — the inverse of the refuted C2. | NONE (honor-system self-check by construction; labelled honestly) |
| **S5** | Documented `implement → review → test` vs `LEGAL_STRICT` allowing `implement → test` | **verify-then-correct** | First verify whether the M10 stale-review check (named in `validate.sh:1385-1394`) already closes the gap. If it does → annotate `§10.2` to cite it. If it does not → correct `§10.2` to describe the enforced order. Decided by evidence at implement, not assumed here. | NONE until AC-7 resolves which branch applies |
| **S6** | `§10.2` lists `spec`, `ADR`, and "check Spec Index" in a **Mandatory Gates** column though none produces a receipt | **correct** | Annotate all three with the table's own existing convention, `(advisory, no gate receipt)` — already used at `:309` for hotfix research. **Highest-value row**: this exact ambiguity produced an identical agent error in three separate sessions (2026-07-02, 2026-07-19, and this one). | NONE (annotation) — but it is the mitigation for a thrice-observed failure |
| **S7** | `AGENTS.md:35` SSoT Recovery Exception + `bootstrap.md:99` Last Verified write vs the `:43-47` "exhaustive" list | **correct** | Add both to the exhaustive list. Names only, no governance keyword → ratchet-safe. **Must re-verify `governance.yaml:93` `ssot-write-isolation`**, whose `expect_substrings` includes "only /ship updates SSoT". | NONE (doc truth) + AC-8 pins the eval case |
| — | ~~C1, C2, C4, C5, C6, D1, E1, F1, M1-as-drafted, A1, A2~~ | **refuted** | See census "REFUTED" table. Two would have disabled live checks. | — |

**Also dropped by the primary, against a reviewer's recommendation**: `## Global Lessons
Candidate` (`retro.md:55`) was offered as a new Category-C row. It is the **same shape** as C5
and C6 — a *create* instruction, and `engineering_guardrails.md:314` calls the section list a
"**minimum** runtime contract". Accepting it while refuting C5/C6 would be inconsistent. It is
retained only as evidence for AC-9's fenced-block requirement.

## Acceptance Criteria

- **AC-1** `AGENTS.md:94` item 2 states its skill-vs-workflow scope; the surface ordering is
  **not** extended. `.agent/rules/` is not inserted into the chain.
- **AC-2** `test_directive_count_ratchet.py` passes with `AGENTS.md` at **≤ 37**, re-run after
  **all** `AGENTS.md` edits together (S1 + S7), not per-edit.
- **AC-3** Zero `## Risks` references remain in `.agent/workflows/*` **or**
  `.agentcortex/docs/guides/*`, including headings inside fenced blocks.
- **AC-4** The 23 stubs no longer list `AGENTS.md` as a Required read; `implement.md` and
  `ship.md` no longer list `security_guardrails.md`. Stub count stays 30 and
  `check_command_sync.py` still passes.
- **AC-5** `§10.6` items 2 and 3 both test content, not presence.
- **AC-6** `§10.2` annotates `spec`, `ADR`, and "check Spec Index" as advisory/no-receipt,
  using the wording already at `:309`.
- **AC-7** The S5 branch is decided by executing the M10 check against a fixture, and the
  chosen branch is applied. Evidence recorded in the Work Log.
- **AC-8** `run_governance_eval.py` still resolves `ssot-write-isolation` after the S7 edit,
  and the case's `expect_substrings` are re-read against the new list text.
- **AC-9** `tests/ci/test_worklog_risk_section_naming.py` exists and passes: no governance
  surface under `.agent/**`, `.agentcortex/docs/guides/**`, or `.claude/commands/**` names a
  Work Log `## Risks` section, **including bare headings inside fenced blocks**. Carries an
  anti-vacuity guard proving it fires on a synthetic fenced `## Risks`.
- **AC-10** Net byte delta across the changed governance surfaces is **≤ 0**, measured with a
  per-file char count. `analyze_token_lifecycle.py` is **not** used — verified to contain 0
  references to `AGENTS.md`, `rules/`, or `templates/`.
- **AC-11** An ADR-011 amendment (or successor ADR) records the `§10.6`, `§10.2`, and
  `AGENTS.md` directive edits with per-directive tiers, per ADR-011's own `review_trigger`.
- **AC-12** The Work Log `## Decisions` section carries the §13 net-add justification before
  implement begins.

## Domain Decisions

- **[DECISION] Scope the precedence rule; do not extend it.** Extending creates two new
  defects (Constitution demoted, ADR loop) to fix one reading error. Scoping removes the false
  universality with no ranking change.
- **[DECISION] No template changes, at all.** Two independent seats verified that adding a
  section satisfies a bare-grep check forever. The general principle: **a presence check and a
  template that supplies the thing being checked cannot coexist.**
- **[DECISION] The most valuable output is an annotation, not a mechanism.** S6 costs six words
  and prevents an error three sessions have now made. No detector proposed here would have
  caught it.
- **[TRADEOFF] `AGENTS.md` fixes reach only adopters who never edited it.** `AGENTS.md` is
  `scaffold` (`deploy.sh:112`), so a modified copy gets `.acx-incoming` and keeps the old text.
  The adopters most exposed to these conflicts are the least likely to receive the fix.
  Accepted — the alternative is forcing overwrites onto a file adopters are explicitly expected
  to modify.
- **[CONSTRAINT] All review was same-vendor.** The external signal failed and was not retried
  at cost. Every judgment call here is unvalidated externally, and the census says so.

## Open for human decision

1. **S5 branch.** Annotate `§10.2` to match the enforced order, or correct the docs to describe
   it? AC-7 gathers the evidence; the choice of which side moves is a question about whether
   documentation or enforcement is authoritative here.
2. **AC-11's form.** ADR-011 amendment versus a successor ADR. Its `review_trigger` fires
   either way; which vehicle is a house-style call.
