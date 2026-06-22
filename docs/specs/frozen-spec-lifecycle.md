---
status: shipped
date: 2026-06-22
classification: architecture-change
primary_domain: governance-lifecycle
applies_to:
  - ".agentcortex/bin/validate.sh"
  - ".agentcortex/bin/validate.ps1"
  - ".agent/workflows/spec.md"
  - ".agent/workflows/spec-intake.md"
  - ".agent/workflows/plan.md"
---

# Frozen-Spec Lifecycle Fix

## Goal

Close the impossible-SSoT cycle that blocks legal `status: frozen` specs created before /ship:
the validator requires every non-draft spec to appear in the Spec Index, but Write Isolation
forbids writing the Spec Index before /ship. Adopt Option B: narrow the validator so only
`shipped`/`living` (already-published) specs are required in the Spec Index. A frozen
(pre-ship) or cancelled spec is a legal intermediate state, not yet indexed.

## Acceptance Criteria

- **AC-1**: A spec file on disk with `status: frozen` that is NOT listed in the Spec Index of
  `current_state.md` causes `validate.sh` and `validate.ps1` to PASS (not FAIL) the SSoT Spec
  Index completeness check.
- **AC-2**: A spec file on disk with `status: shipped` (or no status) that is NOT listed in the
  Spec Index of `current_state.md` continues to FAIL the same check.
- **AC-3**: `.agent/workflows/spec.md` no longer instructs writing the `current_state.md` Spec
  Index entry at draft-creation or freeze-time. A note clarifies that the Spec Index is updated
  by `/ship` only (consistent with `spec-intake.md §5.3`).
- **AC-4**: `.agent/workflows/plan.md` Frozen Spec Pre-Check reads `status: frozen` from the
  spec file on disk, NOT from a `[Frozen]` tag in the Spec Index (which no longer exists
  pre-ship under Option B).
- **AC-5**: `validate.sh` and `validate.ps1` produce identical behavior (sh/ps1 parity):
  both skip `draft`, `frozen`, and `cancelled`; both require `shipped` and `living` (and
  no-status) specs in the index.
- **AC-6**: `AGENTS.md` requires NO change. Option B preserves the Write Isolation
  single-writer invariant.

## Non-goals

- Stage-2 auto-indexing of frozen specs (would re-introduce multi-writer SSoT problem).
- Changing the `/ship` Spec Index write behavior.
- Modifying `spec-intake.md` (already consistent with Option B at §5.3).
- Adding a `cancelled` status to any workflow beyond the validator skip (status taxonomy is
  out of scope for this fix).

## Constraints

- validate.sh and validate.ps1 must maintain parity — any skip-condition change must be
  identical in both files.
- The spec file itself MUST remain `status: draft` until the parent session ships this
  branch, to avoid tripping the validator it is fixing (self-referential guard).
- No AGENTS.md changes. Write Isolation single-writer invariant preserved.
- Surgical edits only; no drive-by refactoring.

## Domain Decisions

- [DECISION] Option B (narrow the validator) is chosen over Option A (allow a guarded
  `/spec` freeze-time SSoT write) because Option A re-introduces the multi-writer SSoT
  problem the exceptions list exists to prevent, and `guard_context_write.py` has no
  section-targeting — it would race the /ship Spec Index update.
- [DECISION] `cancelled` specs are added to the skip list alongside `frozen`, because a
  cancelled pre-ship spec is likewise a legal intermediate state that should not require
  an index entry.
- [CONSTRAINT] The Spec Index in `current_state.md` MUST contain entries ONLY for
  `shipped` and `living` specs (or specs with no status frontmatter). Pre-ship statuses
  (`draft`, `frozen`, `cancelled`) are intentionally excluded.
- [TRADEOFF] A frozen spec not yet in the Spec Index is invisible to the Spec Index query
  until /ship — this is acceptable because the spec file on disk is the authoritative
  record; plan.md reads disk status directly (AC-4).
