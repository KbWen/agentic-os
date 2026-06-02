---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12 + optimization-round-2026-05-04
created: 2026-04-12
last_updated: 2026-06-02
---

# Product Backlog

> **Completed entries** (Shipped / Cancelled) live in
> [`_product-backlog-archive.md`](./_product-backlog-archive.md). This index
> tracks only active (Pending / In Progress) work. Entry numbers are global and
> stable across both files, so `#N` dependency references resolve in either.

## Source Summary

Governance file bloat review (2026-04-12) identified 10 findings across P0–P2: multiple data surfaces grow unbounded (archive/, Global Lessons, Spec Index, INDEX.jsonl), compaction mechanisms are advisory-only, and process artifacts (_raw-intake archives, superseded L2 entries, shipped specs) accumulate without consumers. Industry patterns (LSM-tree compaction, progressive summarization, tiered retention) converge on a 4-state document lifecycle with LLM-driven summarization at tier transitions.

## Feature Inventory

| # | Feature | Kind | Labels | Priority | Spec File | Tier | Status | Dependencies |
|---|---|---|---|---|---|---|---|---|
| 1 | Tiered Document Lifecycle Engine (4-tier state machine + config) | framework | lifecycle | P1 | docs/specs/tiered-doc-lifecycle.md | feature | Pending | — |
| 3 | Archive directory GC + INDEX.jsonl rotation | framework | lifecycle | P2 | — | feature | Pending | #1 |
| 7 | Domain Doc L2 superseded entry archival | framework | lifecycle | P2 | — | quick-win | Pending | — |
| 11 | Shipped specs accumulation — status-driven filtering | framework | lifecycle | P2 | — | quick-win | Pending | #1 |
| 13 | Warm→Cold LLM summarization pass in /ship | framework | lifecycle | P2 | — | feature | Pending | #1, #3 |
| 14 | External Skill Research & Integration (Phase A: 3 core skills) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Pending | — |
| 16 | Skill Validation Pipeline (meta-governance) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Pending | #14 |
| 17 | Hard Work Log lock (advisory → blocking) | framework | concurrency | P1 | — | feature | Pending | — |
| 18 | Lightweight routing heuristics (decision tree in config.yaml, not a DSL) | framework | routing | P2 | — | quick-win | Pending | — |
| 21 | Skill cache timestamp + staleness invalidation | framework | skills | P2 | — | quick-win | Pending | — |
| 33 | Claude Code plugin packaging (.claude-plugin/plugin.json + bin/ + commands/agents/hooks bundling, no monitors) | dx | packaging | P2 | — | feature | Pending | #30, #31 |

> Completed entries (#2, 4–6, 8–10, 12, 15, 19–20, 22–32, 34–44) are in [`_product-backlog-archive.md`](./_product-backlog-archive.md).

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
