---
status: accepted
date: 2026-06-22
classification: architecture-change
primary_domain: governance-lifecycle
deciders: "@kbwen (human steer — pinned Option B + classification freeze) + Claude Sonnet 4.6 (implementer)"
applies_to:
  - ".agentcortex/bin/validate.sh"
  - ".agentcortex/bin/validate.ps1"
  - ".agent/workflows/spec.md"
  - ".agent/workflows/spec-intake.md"
  - ".agent/workflows/plan.md"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When /ship's Spec Index write behavior changes, or a new lifecycle status is introduced to the spec frontmatter taxonomy"
  supersedes: none
  superseded_by: none
---

# ADR-010: Frozen-Spec Lifecycle Fix

## Context

### The Impossible-SSoT Cycle (pre-existing defect)

A legal `status: frozen` feature spec created BEFORE `/ship` causes the downstream validator
to FAIL, and the only instructed remedy is forbidden before `/ship`:

**Leg A (validator)**: `.agentcortex/bin/validate.sh` and `.agentcortex/bin/validate.ps1`
— the "SSoT Spec Index completeness" check SKIPS only `status: draft` specs and REQUIRES
every other non-`_` spec (frozen/shipped/living/cancelled) to appear in the Spec Index of
`current_state.md`, else FAILs with "non-draft spec(s) not in index → fix via /ship".

**Leg B (Write Isolation)**: `AGENTS.md` Write Isolation states only `/ship` writes
`current_state.md`; the exhaustive non-ship exceptions are only `{/retro, /app-init, /adr}`
— `/spec` is NOT allowed to write the SSoT pre-ship.

**Leg C (doc contradiction)**: `.agent/workflows/spec.md` (~lines 15 and 44) instructs
writing the `current_state.md` Spec Index entry at freeze-time AND draft-creation;
`.agent/workflows/spec-intake.md:276` correctly states the index is updated during /ship.
They contradict.

**A/B repro**: the same project passes validation when the spec is `status: draft`, FAILs
when `status: frozen`.

### Attribution

This is a **pre-existing lifecycle defect** predating v1.8 (the draft-only skip and Write
Isolation exceptions are ADR-002-era). It was NOT introduced by v1.8 — it was **surfaced
by a v1.8 downstream-integration simulation** that created a frozen spec before /ship and
observed the validator FAIL.

## Decision

**Adopt Option B: narrow the validator.** The Spec Index completeness check requires an
index entry ONLY for `shipped` and `living` (already-published) specs. A pre-ship `frozen`
spec is a **legal intermediate state** that is NOT yet required in the Spec Index; `/ship`
flips it to `shipped` and indexes it then. `/ship` remains the SOLE SSoT indexer →
**Write Isolation single-writer invariant preserved → `AGENTS.md` needs NO change**.

Concretely:

1. **`validate.sh` and `validate.ps1`**: change the skip condition so the check skips
   `draft`, `frozen`, AND `cancelled`. Require-in-index only for `shipped`, `living`, and
   specs with no status frontmatter. Parity between both files is mandatory.

2. **`spec.md`**: remove the instruction to write the `current_state.md` Spec Index entry
   at draft-creation and at freeze-time. The freeze step updates the spec's OWN frontmatter
   `status: draft→frozen` ONLY (no SSoT write). Add a one-line note that the Spec Index
   is written by `/ship` (pre-ship SSoT writes are forbidden by Write Isolation).

3. **`plan.md` Frozen Spec Pre-Check**: change it to read `status: frozen` from the spec
   FILE on disk, NOT from a `[Frozen]` Spec Index tag (which no longer exists pre-ship
   under Option B).

4. **`AGENTS.md`**: NO CHANGE. Option B requires none.

## Alternatives Considered

**Option A (rejected): allow a guarded `/spec` freeze-time Spec Index write.**

Allow `/spec` to write the `current_state.md` Spec Index entry when freezing, using
`guard_context_write.py` with a new section-targeting capability.

Rejected because:
- It re-introduces the multi-writer SSoT problem the exceptions list exists to prevent.
- `guard_context_write.py` has no section-targeting (whole-file replace or O_APPEND only);
  it would race the `/ship` Spec Index update, creating a lost-update window.
- It requires adding `/spec` to the non-ship SSoT write exceptions in `AGENTS.md` —
  expanding that list without an enforcement mechanism is honor-system theatre per the
  `[enforcement][HIGH]` Global Lesson.
- Write Isolation's single-writer invariant is a load-bearing safety property; narrowing
  the exception list is preferable to expanding it.

## Consequences

**Positive**:
- The impossible SSoT cycle is closed. A developer can legally freeze a spec before /ship
  without the validator FAILing.
- Write Isolation single-writer invariant is fully preserved — `AGENTS.md` is unchanged.
- `spec.md` and `spec-intake.md` are now consistent: both say the Spec Index is written
  at /ship.
- `plan.md` Frozen Spec Pre-Check reads the ground-truth source (the file on disk) rather
  than a tag that no longer exists pre-ship.
- sh/ps1 validator parity is maintained.

**Negative / accepted**:
- A `cancelled` spec is now also skipped by the validator. This is correct behavior
  (a cancelled pre-ship spec should not be required in the index) and is a low-risk
  extension of the same logic.
- A `frozen` spec is invisible to the Spec Index until /ship; this is acceptable because
  the spec file on disk remains the authoritative record, and plan.md reads disk status.

**Out of scope**:
- Stage-2 auto-indexing of frozen specs (would re-introduce multi-writer SSoT problem).
- Changes to the spec frontmatter status taxonomy.
- Changes to the `/ship` Spec Index write behavior.
