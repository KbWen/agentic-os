---
id: kb-seam-declared-reading
title: "KB-Seam Declared Reading (the KB declares how it is read; framework rules become defaults)"
status: shipped
classification: architecture-change
primary_domain: downstream-adaptability
adr: docs/adr/ADR-009-knowledge-source-consumption-seam.md
signal_tier: T2
branch: claude/knowledge-base-reading-protocol-e2c4f0
created: 2026-11-13
---

# KB-Seam Declared Reading: the knowledge base says how it is read

Extends `docs/specs/knowledge-source-seam.md` and `docs/specs/kb-seam-anchor-neutrality.md`
(both shipped, not edited). Decision record: ADR-009 Amendment (2026-11-13).

## Goal

A knowledge base that declares how it should be read is read that way. The framework keeps
deciding **whether and when** to consult a declared KB and keeps the safety floor; the KB
decides **how**: which pages, in what order, how many, and where to stop. The framework's own
reading rules become defaults for what the KB leaves undeclared, and the consult procedure
stops naming the KB's internal fields, field types and page constants.

## Evidence

1. The reference KB's machine contract changed (2026-11-13): its entrypoint now opens with an
   explicitly labeled reading declaration (index line 1 and manifest head), its schema version
   rose, and index rows for pages with a digest no longer repeat the summary. ADR-009's
   `review_trigger` ("a consumed KB's machine-contract changes") fired.
2. KB-side simulation (n=2, fresh agents, current framework text, a new-screen task): both
   read the declaration and stayed in budget, but only because it sat at the file head. No
   framework step asks for it.
3. Description drift, confirmed here: the adopter guide types two read hints as a boolean and
   a single value where the reference KB gives text or lists; the guide and the
   `bootstrap.md §3.6` row assume every index row carries a `summary`; guide §Optional bounded
   lookup restates fixed page caps.
4. Consumer-side inventory: KB-internal names appear in the `§3.6` `kb-consult` row, `§1b`,
   the adopter guide, the `.example` template and ADR-009. No validator reads a KB field;
   `validate.*` pin only the literal `kb-consult`.
5. Design roundtable (2026-11-13; adopter-diversity, trust-boundary, philosophy/cost seats):
   findings adjudicated in the Work Log; accepted ones are folded into the Design below.

## Design

**What counts as a declaration.** Only text the KB explicitly presents as how to read it (a
labeled reading plan) at the head of its entrypoint: the first line of a JSONL index, the top
of a manifest, the top of a markdown index. Unlabeled head prose, older read hints and
per-digest notes stay hints or DATA, and the defaults apply. If the head has no declaration,
search the entrypoint for one without loading it whole (same rule as `schema_version`).

**Split of authority.**

| Owned by | What |
|---|---|
| Framework (floor) | whether to consult (`knowledge_sources` present AND task in a KB-routed domain); which phases; `tiny-fix` never; `role: advisory` (a KB never gates); KB content is DATA; the page outranks digests and other derived outputs; volatile facts are checked against the official source; the applicability filter; reads stay inside the configured KB root; never load a whole manifest, index or retrieval artifact into context |
| The KB, via its declaration | which pages or sections, their order, how many, where to stop; it may always lower a cap and may raise one only for `feature` / `architecture-change` (hotfix / quick-win stay ≤1 page) |
| Framework defaults (only where the KB declares nothing) | the KB's routing in its order; a section, not the page; digest-first with KB-declared anchors (guide §Per-page digests); ≤3 pages per phase in total across KBs, ≤1 for hotfix / quick-win; a declaration with no stop point → these caps |

**Authority is an allowlist.** From the declaration the agent uses only: which KB pages or
sections to read, their order, how many, and where to stop. Every other statement in it is
DATA, including claims of authority, requests to skip or relax a phase, and instructions to
run a command. Reading KB files with read-only tools (file read, grep, search) is within the
allowlist; any other command is not, including a helper the declaration names. The optional
bounded lookup helper stays governed only by the adopter guide's own conditions.

**Observable.** `§1b` already reads the entrypoint head for `schema_version`; it also records
per KB `plan=declared|default` in the existing Session Info record, and a consult that uses a
declared budget above the defaults says so in the Work Log. No extra read.

## Adopter situations

| Setup | Behavior after this change |
|---|---|
| No KB (most adopters) | Unchanged: zero KB reads. The always-loaded `AGENTS.md` KB line changes wording (net-add justified in the Work Log). |
| BYO markdown index, no declaration | Unchanged: defaults. Head prose is not a declaration unless labeled. |
| KB built from the guide (digest + anchors), no declaration | Unchanged: the row keeps a one-clause digest default pointing at the guide section. |
| KB with a declaration (any shape, any language) | Uses the declaration within the allowlist, incl. its page budget for `feature` / `architecture-change`; hotfix / quick-win keep ≤1 page unless the declaration asks for less. |
| Declaration without a stop point | Framework caps. |
| Declaration placed after a large array | Found by search, never by loading the file whole. |
| Several KBs | Each KB's declaration governs reads from that KB; the default caps are a total across KBs. |
| Declaration that asks to run commands, write, or skip gates | DATA; reads continue. DATA boundary already eval-backed (`kb-page-injection-decline`). |
| New KB, old framework (≤ v1.8.38) | Old row falls back to `summary` + headings; rows with a digest still read the digest first. A missing `summary` on those rows only matters when the digest is stale or unreadable. CHANGELOG notes it. |
| No Python, any platform | Nothing new required; `AGENTS.md` is read by every platform (Gemini imports it, Copilot defers to it). |
| Weaker models | Honor-system: raised probability, not a guarantee. |

## Changes

1. ADR-009: Amendment (2026-11-13), owner-approved before merge.
2. `bootstrap.md §3.6` `kb-consult` row: principle form per the Design; no KB field names or
   types; defaults marked as defaults.
3. `bootstrap.md §1b`: drop the `digest` location (consult detail); keep the integer
   `schema_version` readability check and the optional fingerprint; add `plan=declared|default`.
4. `AGENTS.md §vNext State Model` KB line: point to the declared reading plan; no new
   directive keyword; keeps the substrings the existing eval expects.
5. `connecting-a-knowledge-base.md`: section on declaring how the KB is read (incl. the
   allowlist); a "what the framework reads from any KB" list; drop the every-row-`summary`
   assumption and boolean / single-value typing of read hints; field shapes marked as
   examples; page caps described as defaults (incl. §Optional bounded lookup).
6. `downstream-capabilities.example.yaml`: one comment line pointing at the declaration
   section.
7. `.agentcortex/eval/governance.yaml`: one case — a fixture entrypoint whose labeled plan
   names a first page and a one-page stop; the agent names that page first and stops.
8. CHANGELOG entry incl. the new-KB/old-framework note.

## Acceptance Criteria

- AC-1: the `§3.6` row tells the agent to read the entrypoint's labeled reading plan and use it
  to choose what to read, and names no KB field, field type, or per-page field set.
- AC-2: the row and the guide state the defaults as applying only where the KB declares
  nothing, with framework caps when no stop point is declared and the default cap as a total
  across KBs; a declaration may lower any cap and raise one only for `feature` /
  `architecture-change`.
- AC-3: the declaration's authority is an allowlist (pages or sections, order, count, stop);
  read-only tools are within it; everything else is DATA; declared reads stay inside the KB
  root; the page-outranks-digest and volatile-fact rules stay framework-owned.
- AC-4: net `bootstrap.md` size change ≤ 0; `test_aggregate_current_total_stays_under_355k`
  and the directive-count ratchet pass; the `AGENTS.md` line adds no directive keyword.
- AC-5: the guide no longer assumes a `summary` on every index row, a boolean / single-value
  type for any read hint, or fixed page caps.
- AC-6: no reference-KB-specific field name, slug, or fingerprint value appears in a tracked
  file.
- AC-7: the new eval case is well-formed under `tests/guard/test_governance_eval.py`;
  `validate.sh` / `validate.ps1` and the full pytest suite pass.
- AC-8 (optional evidence): a fresh-agent run of the new eval case, reported as measured.

## Non-goals

- No validator, schema or `downstream-capabilities.yaml` key change.
- No change to when a KB is consulted.

## Signal tier

`signal_tier: T2`: the read-the-declaration step lives in `AGENTS.md`, inside the governance
eval harness, and is guarded by the new case in `.agentcortex/eval/governance.yaml`
(precedent: `kb-plain-entry`).

## Domain Decisions

- [DECISION] Whether and when to consult belong to the framework; how to read belongs to the
  KB's labeled reading plan. A consumer that names a KB's fields breaks on every KB but one.
- [DECISION] The plan's authority is an allowlist (pages or sections, order, count, stop).
  Everything else in it is DATA, so granting it cannot widen what KB text can make an agent do.
- [DECISION] A plan may lower any cap and raise one only for `feature` /
  `architecture-change`; hotfix / quick-win stay at one page (owner, chat 2026-11-13).
