---
status: living
domain: document-governance
created: 2026-03-29
last_updated: 2026-03-29
---

# Document Governance — Layer 1 Synthesis

> This is the current effective design. Updated only by `/govern-docs --restructure`.
> Decision history is in `docs/architecture/document-governance.log.md` (L2 — append-only).

## Current Design

AgentCortex uses a **two-layer Domain Doc architecture** to separate "what to read" from "what to trace":

- **L1 Synthesis** (`docs/architecture/<domain>.md`): Current effective design principles. Hard cap: 150 lines (configurable via `.agent/config.yaml` `domain_doc.max_synthesis_lines`). This is what `/bootstrap` reads.
- **L2 Decision Log** (`docs/architecture/<domain>.log.md`): Append-only chronological entry blocks. Never deleted, only appended. Agents read this only for traceability queries.

Document taxonomy: Domain Doc, Feature Spec, ADR, Product Backlog, Review Snapshot, Guide — each with a fixed path, lifecycle status, and owner workflow.

## Key Principles

- **One topic, one canonical file**: Before creating any `.md` in `docs/`, verify no existing file covers the same domain.
- **Knowledge consolidation at /ship**: Every shipped spec's `## Domain Decisions` section (max 10 entries, tagged `[DECISION]`/`[TRADEOFF]`/`[CONSTRAINT]`) is appended to L2.
- **L1 is curated, L2 is permanent**: Only `/govern-docs --restructure` may rewrite L1. L2 entries are never deleted.
- **Capability-by-presence**: All domain doc mechanisms are no-ops when artifacts are absent — backward compatible with downstream projects that haven't adopted domain docs.

## Constraints

- L2 writes are append-only. Existing entries MUST NOT be modified or deleted.
- Primary domain receives full consolidation; secondary domains get cross-reference pointers only.
- Progressive rollout: forward-only + backfill-on-touch (no retroactive migration of existing shipped specs).

## Workflow Contracts

- **Bootstrap authority gate**: A candidate L1 file becomes current design authority only when `docs/architecture/<domain>.md` exists and its frontmatter declares `status: living`. Filename match alone is not enough.
- **Audit routing contract**: Significant architectural findings from `/audit` must be emitted as structured `routing_actions` blocks targeting canonical specs or domain docs, so follow-up work can survive beyond the review snapshot.
- **Ship consolidation contract**: When a shipped spec still declares `primary_domain`, `/ship` must either update that domain's L2 log or record an explicit skip justification tied back to the spec field. Generic skip text is invalid.
