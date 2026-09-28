---
id: kb-seam-anchor-neutrality
title: "KB-Seam Anchor Neutrality (KB-declared digest anchors + additive schema_version)"
status: frozen
classification: feature
primary_domain: downstream-adaptability
adr: docs/adr/ADR-009-knowledge-source-consumption-seam.md
signal_tier: T3
branch: feat/kb-digest-consumption
created: 2026-09-28
---

# Spec: KB-Seam Anchor Neutrality

> **Status**: frozen at `/review` PASS (2026-09-28); `/ship` sets it to `shipped`.
> Decision record: ADR-009 §Amendment (2026-09-28).

## Problem

The shipped KB seam (ADR-009) only worked end to end for one knowledge base.

1. **Section anchors were the reference KB's own headings.** ADR-009 Decision 3 and
   `docs/specs/knowledge-source-seam.md` named that KB's checklist and risk headings as what
   `/review` and `/plan` pull, and `bootstrap.md §3.6` paraphrased them. Another KB has no
   such headings, so the consult extracted nothing and reported nothing.
2. **`schema_version` "matches the known shape" was not testable.** Read literally, a newer
   additive schema would be treated as absent.
3. **The UNREADABLE advisory had no destination.** Recorded only in the gitignored Work Log,
   it never reached the person who declared the KB.

The trigger was a change in the reference KB's machine contract: a line-1 `_meta` record in its
JSONL index that carries `schema_version`, `kb_version`, `task_routing` and a `digest` block;
per-row `digest` / `digest_tokens`; and a `sha` in each digest's first line.

## Scope

**In**: `bootstrap.md §1b` readability criterion and the visible UNREADABLE line;
`bootstrap.md §3.6` `kb-consult` row; the adopter guide
(`.agentcortex/docs/guides/connecting-a-knowledge-base.md`) and
`.agentcortex/templates/downstream-capabilities.example.yaml` comments; ADR-009 amendment.

**Out**: validator code, the `knowledge_sources` schema allowlist, a consumption engine, any
fixture-KB test. `docs/specs/kb-seam-hardening.md` records why each is rejected, and the
reasons still hold. Shipped specs are not edited (`spec-intake.md §8b`).

## Acceptance Criteria

- **AC-1: Additive `schema_version`.** `bootstrap.md §1b` accepts any integer
  `schema_version`: known fields are read and unknown ones ignored, and a version higher than
  expected never makes a KB absent. For a JSON entrypoint, missing or non-integer is malformed,
  which is UNREADABLE (no third state); a markdown index (`llms.txt` / `_index.md`) only has to
  be readable. The manifest's head is matched as text for `"schema_version"\s*:\s*<int>`
  (the index's line-1 `_meta` for an `index.jsonl` entrypoint); only if the head lacks it is
  the whole file searched (not loaded). A truncated head is never parsed as JSON and misread
  as malformed.
- **AC-2: Visible UNREADABLE.** A declared KB that resolves UNREADABLE is recorded in the Work
  Log and also shown as one non-blocking line in the bootstrap chat output. With no
  `knowledge_sources` block, bootstrap is silent and reads nothing.
- **AC-3: KB-declared anchors.** The KB declares `digest` at the manifest's top level
  (entrypoint `manifest.json`) or in the index's line-1 `_meta` (entrypoint `index.jsonl`).
  The `§3.6` `kb-consult` row then reads a routed standard's `digest` and checks its first-line
  `sha` against the row's `sha`. It reads the page instead on a mismatch, when the row has no
  `digest` field or an empty one, or when the digest file is missing or unreadable; the section
  then comes from the page. It takes the section named by `digest.anchors.risks` for `/plan`
  and `/implement` (on-match), and by `.checklist` for `/review`.
- **AC-3b: KB clone state is flagged.** When the resolved KB root is its own git repo (its
  top level) that is not
  on a clean `main` / `master`, `bootstrap.md §1b` appends `(WARN: KB not on clean main)` to
  the `<id>→OK@<kb_version>` record and shows it on one bootstrap line. The KB is still
  consulted and no gate changes. The guide states that the clone should stay on merged
  `main` and gives the git commands to check it by hand.
- **AC-4: No framework-owned heading.** No current rule surface (`bootstrap.md`, ADR-009
  Decision text, the adopter guide, the `.example`) names a specific KB's heading as the
  section to read. A grep of those files for the reference KB's heading strings finds nothing
  outside the ADR's Evidence section.
- **AC-5: BYO fallback.** A KB without a `digest` block or `anchors`, or a file without the
  anchored heading, is consulted by
  choosing sections from the routed page's `summary` and headings within the token budget.
  The existing ≤3-page cap, applicability pass and DATA-not-instructions rules are unchanged.
- **AC-6: Adopter guide.** The guide shows the generic `digest` shape (manifest top level or line-1 `_meta`) with neutral
  English anchors (`{"risks": "Common AI mistakes", "checklist": "Self-audit checklist"}`),
  states that a KB without it still works, describes reading line 1 plus matching rows
  instead of the whole index, and marks `${ACX_KB_PATH}` optional with a literal path as the
  recommended default.
- **AC-7: No regression.** `validate.sh` / `validate.ps1` pass with fail=0 and still find the
  `kb-consult` literal. `test_lifecycle_token_consumption.py` passes under the existing 355k
  ceiling without a bump. `test_capabilities_schema_gate_safety.py` passes unmodified, and
  `validate_downstream_capabilities.py` accepts the edited `.example`.

## Enforcement classification

| Property | Tier |
|---|---|
| `kb-consult` row ships in `bootstrap.md` | Structural (existing `validate.*` literal check) |
| Additive `schema_version`, head-first check | Honor-system |
| Visible UNREADABLE line | Honor-system |
| KB-not-on-clean-main WARN | Honor-system (no validator reads the adopter's KB path) |
| KB-declared anchors, digest `sha` check, BYO fallback | Honor-system |
| Guide and `.example` wording | Informational |

`signal_tier: T3` (§13): no new behavior is machine-checkable, so the named observer is the
adopter who declares the KB, who sees the UNREADABLE / WARN line and the consult it feeds.

## File Relationship

EXTENDS `docs/specs/knowledge-source-seam.md` (the Stage-1 consult it corrects). Also relates
to `docs/specs/kb-seam-hardening.md` (`${ACX_KB_PATH}`) and
`docs/specs/kb-seam-accelerator-consumption.md` (UNREADABLE covers malformed; token budget;
applicability pass). It replaces none of them.

## Domain Decisions

- [DECISION] Anchors are data the KB declares, not framework vocabulary. A heading the
  framework hard-codes binds the seam to one KB and fails silently everywhere else.
- [DECISION] `schema_version` is additive-only. The producer only ever increases it, so any
  integer is accepted. Rejecting a newer version would turn every producer upgrade into a
  silent loss of the consult.
- [DECISION] Declared-but-UNREADABLE is shown to the user in one line and never blocks.
  Undeclared stays silent, so the present-only, zero-cost-when-absent property is unchanged.
- [DECISION] A KB clone that is not on a clean `main` is warned about, not demoted. Its
  content is unreviewed, which the reader should know, but dropping the consult would punish
  the common case of a KB author working on their own KB. No tool checks it: the
  capabilities validator never resolves the KB path (ADR-009 trust model), and no doctor-style
  tool exists to host a check.
- [DECISION] A literal `path` (relative → from the project root) is the recommended default and
  `${ACX_KB_PATH}` is optional.
  Tool processes that a host spawns may not inherit the variable. Its value, when used, is the
  KB clone root.
- [CONSTRAINT] `bootstrap.md` additions stay terse, with detail in this spec and the guide.
  The lifecycle ceiling had about 500 tokens of headroom before this change.

## Rollback

Revert the branch: `bootstrap.md`, ADR-009, this spec, the adopter guide and the `.example`.
No validator, schema or engine logic changed.
