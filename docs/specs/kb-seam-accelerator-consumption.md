---
id: kb-seam-accelerator-consumption
title: "KB-Seam Accelerator Consumption (schema-v4 manifest fields)"
status: shipped
classification: feature
adr: ADR-009
branch: feat/kb-accelerator-consumption
created: 2026-06-23
---

# Spec: KB-Seam Accelerator Consumption

> **Status: draft** — validator skips draft specs (ADR-010); this file will be frozen on
> `/review` PASS and set to `shipped` at `/ship`.

## Problem

ADR-009 shipped a graceful KB-consume seam (`knowledge_sources` in
`downstream-capabilities.yaml`). An independent Codex review (work log
`codex-v18-review-main.md`) surfaced 5 follow-up findings:

| Finding | Summary |
|---|---|
| #3 | `kb_path_env: ACX_KB_PATH` declared in `config.yaml` but never read (bootstrap.md hardcodes `ACX_KB_PATH`). Dead config. |
| #9 | `§1b` health record `<id>→OK` gives no signal when KB content changes but path stays readable. |
| #4 | UNREADABLE meaning ambiguous: does it cover malformed/invalid JSON? |
| #8 | `§3.6 kb-consult` uses page-count cap but manifest provides per-page `approx_tokens` for data-driven budgeting. |
| #5 | `task_routing` routed slugs treated as a full-load mandate; irrelevant checklist items (e.g. BOLA/Firestore on a docs change) become false blockers. |

Finding #6 (adopter guidance on accelerator fields) accompanies the above.

## Non-goals

- No new ADR (within ADR-009 scope, per parent decision).
- No Stage-2 auto-consult, auto-backfill, or automated KB validation.
- No hard dependency on schema-v4 manifest fields — all accelerators are consume-if-present.
- No private KB path, content, or real `kb_version` value in any artifact.
- No third MALFORMED state (avoid vocab bloat; UNREADABLE already covers all unusable).

## Acceptance Criteria

### AC-1: Dead config deleted (#3)
`kb_path_env: ACX_KB_PATH` is removed from `.agent/config.yaml`. A repo-wide grep for
`kb_path_env` finds zero matches outside archived work logs.

### AC-2: Fingerprint in health record (#9)
`bootstrap.md §1b` health-record line documents: when the manifest provides `kb_version`,
record `<id>→OK@<kb_version>`; otherwise bare `OK`. Honor-system (agent records it; no
automated validation).

### AC-3: UNREADABLE covers malformed (#4)
`bootstrap.md §1b` Bind bullet explicitly states that malformed (including invalid JSON or
missing `schema_version`) → UNREADABLE → rung (3) absent. No third state.

### AC-4: Token budgeting clause (#8)
`bootstrap.md §3.6 kb-consult` row includes: budget by per-page `approx_tokens` when
available; cap an extracted section at a few k tokens; no `approx_tokens` → fall back to
page-count cap. Labeled honor-system.

### AC-5: Applicability filtering (#5)
`bootstrap.md §3.6 kb-consult` row includes: routed slugs are a candidate pool; before a
checklist item influences `/plan` or `/review`, do a bounded applicability pass; record a
one-line N/A rationale for dropped items; only applicable items become blockers. Labeled
honor-system.

### AC-6: Adopter guide updated (#6)
`connecting-a-knowledge-base.md` contains a section "Make your KB cheaper to consult
(optional manifest accelerators)" covering per-page `approx_tokens`, `kb_version`,
`schema_version`, `load_policy`, `task_routing`, AND the BYO-without-manifest fallback
(the seam still works without a manifest).

### AC-7: Validator parity and compact index
Both `validate.sh` and `validate.ps1` pass CI-equiv (fail=0). Compact index freshness
check passes (`[PASS] compact index freshness`). No new validator string checks required
(existing `kb-consult` literal in bootstrap.md is preserved).

### AC-8: Token budget
`test_lifecycle_token_consumption.py` passes the 353k ceiling (and per-scenario 10% slack).
If §1b/§3.6 growth causes a drift, re-baseline minimally via `update_lifecycle_baseline.py
--apply` and document inline.

### AC-9: Spec exists as draft
`docs/specs/kb-seam-accelerator-consumption.md` exists with `status: draft` and is NOT
required to be in the SSoT Spec Index (ADR-010 narrow-validator rule for draft status).

## Enforcement classification

| Property | Tier |
|---|---|
| Dead config deleted | Structural (deleted — no longer declarable) |
| `kb_version` fingerprint in health record | Honor-system (agent records it) |
| UNREADABLE covers malformed (fail-closed) | Structural-adjacent (always-on DATA discipline) |
| Token budgeting via `approx_tokens` | Honor-system |
| Applicability filtering | Honor-system |
| Adopter guide section | Informational (read-on-demand guide, not always-loaded) |

## Domain Decisions

- [DECISION] No MALFORMED third state: UNREADABLE is the single "not usable" bucket; adding
  a third state adds vocab with no behavioral difference (both map to rung-3 absent).
- [DECISION] bootstrap.md §1b/§3.6 additions must be terse: the spec/guide carry the
  how-to detail; bootstrap.md carries only the at-a-glance action clause. Always-loaded
  surface stays minimal (constraint A).
- [DECISION] Honor-system labeling is mandatory: fingerprint, token budgeting, and
  applicability filtering are agent-discipline; they raise probability but are not
  machine-enforced. Labeling them honestly prevents false confidence.

## Rollback

Revert the branch (4 files: `config.yaml`, `bootstrap.md`,
`connecting-a-knowledge-base.md`, `docs/specs/kb-seam-accelerator-consumption.md`).
All changes are additive or deletive cleanup; no engine/validator logic changed.
