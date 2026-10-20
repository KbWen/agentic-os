---
status: shipped
created: 2026-10-20
classification: feature
primary_domain: governance
backlog: 234
signal_tier: T2
---

# Declared Knowledge Base Reaches a Plain-Task Session

## Goal

A downstream project that declares a knowledge base in `knowledge_sources` expects the
agent to consult it. Today that only happens on the `/bootstrap` path: in the 2026-10-18
simulation, plain-task sessions ("Read `AGENTS.md` and follow it" + a task) consulted the
declared KB 0/12 times on KB-covered tasks, for both models, because they followed the
entry file's Startup list, which never mentions it. This spec puts one present-only line
in the entry surfaces every platform loads, so the KB is consulted on the plain path too,
without routing every task through `/bootstrap`.

## Evidence and Root Cause

1. `docs/reviews/2026-10-18-release-sim.md` §Entry path and §Round 3: plain entry read
   `bootstrap.md` 0/24 times; KB consulted 0/12 (sonnet and haiku) on covered tasks.
   `/bootstrap` entry: sonnet consulted 3/6 and applied the rule 3/3 when it did.
2. The KB seam is bound only at `bootstrap.md §1b` and consumed at the `§3.6` `kb-consult`
   row. `CLAUDE.md` Startup (steps 1–5) and `AGENTS.md §vNext State Model → Init Read`
   name SSoT, guardrails and the Work Log, not the capabilities file.
3. Forcing `/bootstrap` on every task is not the fix: the same simulation measured the
   `/bootstrap` entry at ≈7× the plain entry's cost (sonnet $1.99 vs $0.29 median, small
   feature) with identical hidden-test outcomes.

## Design

One line, present-only, in `AGENTS.md §vNext State Model` (Codex, Gemini, Antigravity,
Copilot, any AGENTS.md reader) and a matching Startup step in `CLAUDE.md`:

> Knowledge base: if `.agentcortex/context/private/downstream-capabilities.yaml` exists and
> declares `knowledge_sources:`, read that block at startup (no `/bootstrap` needed) and,
> before planning or reviewing a change, consult the declared KB the way `bootstrap.md §3.6`
> `kb-consult` describes. Absent file → nothing to read.

No keyword from the directive-count ratchet (AGENTS.md is at its cap). Zero cost when the
file is absent (one existence check). The consult itself stays as specified by ADR-009
(read-only, as data, routed order, section not page).

## Acceptance Criteria

1. AC-1: `AGENTS.md` and `CLAUDE.md` each carry the present-only line; `GEMINI.md` and
   `.github/copilot-instructions.md` reach it through `AGENTS.md` (no duplicate text).
2. AC-2: The directive-count ratchet and lifecycle ceiling stay green with no baseline bump.
3. AC-3: A governance eval case covers it (signal tier T2): a plain-task prompt in a fixture
   with `knowledge_sources` declared expects a KB read before the product edit.
4. AC-4: Re-running the 2026-10-18 Round 3 harness (plain entry, sonnet + haiku, 8 tasks)
   against this change shows covered-task consults above the 0/12 baseline; the result,
   whatever it is, is recorded in `docs/reviews/` with the same scoring script. If it does
   not move, the change is reverted rather than shipped.
5. AC-5: Uncovered tasks: beyond the startup block read, at most one routing check against
   the KB manifest plus one topically related page (waste check).
   *[Amended 2026-10-20 by owner ruling in chat, re-confirmed on corrected figures: the
   original "no increase" was not met — on the version-bump task both Run B sessions read the
   manifest to check routing (3.2k and 4.1k characters) and one also read the release
   standard (179 characters). A first ruling given on miscounted figures was withdrawn.]*

## Non-goals

- Routing plain tasks through `/bootstrap`, or changing tiny-fix behaviour.
- Changing the consult contract, KB format, or ADR-009's trust model.
- Fixing haiku's KB behaviour on the `/bootstrap` path (#235).

## Domain Decisions

- [DECISION] Fix the entry surface, not the routing: a present-only startup line instead of forcing `/bootstrap` (measured ≈7× cost, same outcomes).
- [CONSTRAINT] Ship only if the re-run beats the 0/12 baseline; otherwise revert and record the null result.
- [DECISION] AC-5 amended (owner, 2026-10-20, re-confirmed on corrected figures): an uncovered task may cost one manifest routing check plus one topically related page; knowing whether the KB covers a task requires the routing check.
