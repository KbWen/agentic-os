---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12
created: 2026-04-12
last_updated: 2026-04-12T+quick-wins
---

# Product Backlog

## Source Summary

Governance file bloat review (2026-04-12) identified 10 findings across P0–P2: multiple data surfaces grow unbounded (archive/, Global Lessons, Spec Index, INDEX.jsonl), compaction mechanisms are advisory-only, and process artifacts (_raw-intake archives, superseded L2 entries, shipped specs) accumulate without consumers. Industry patterns (LSM-tree compaction, progressive summarization, tiered retention) converge on a 4-state document lifecycle with LLM-driven summarization at tier transitions.

## Feature Inventory

| # | Feature | Finding | Spec File | Tier | Status | Dependencies |
|---|---|---|---|---|---|---|
| 1 | Tiered Document Lifecycle Engine (4-tier state machine + config) | Design | docs/specs/tiered-doc-lifecycle.md | feature | Pending | — |
| 2 | Global Lessons cap + archive rotation | F-01 (P0) | — | quick-win | Shipped | — |
| 3 | Archive directory GC + INDEX.jsonl rotation | F-02 (P0) | — | feature | Pending | #1 |
| 4 | Spec Index cap + archive section | F-03 (P0) | — | quick-win | Shipped | — |
| 5 | Work Log compaction: validate WARN→FAIL | F-04 (P1) | — | quick-win | Shipped | — |
| 6 | `_raw-intake-<date>.md` cleanup (MAY→MUST) | F-05 (P1) | — | quick-win | Shipped | — |
| 7 | Domain Doc L2 superseded entry archival | F-06 (P1) | — | quick-win | Pending | — |
| 8 | `_product-backlog.md` completed backlog archive | F-07 (P1) | — | quick-win | Pending | — |
| 9 | ~~`docs/reviews/` dead reference~~ — not a bug; created by `/audit`, ship check is capability-by-presence | F-08 (P2) | — | tiny-fix | Cancelled | — |
| 10 | Active Work Log count: validate WARN→FAIL | F-09 (P2) | — | quick-win | Pending | — |
| 11 | Shipped specs accumulation — status-driven filtering | F-10 (P2) | — | quick-win | Pending | #1 |
| 12 | validate.sh: add archive size + Global Lessons count checks | F-02,F-01 | — | quick-win | Pending | #2, #3 |
| 13 | Warm→Cold LLM summarization pass in /ship | Design | — | feature | Pending | #1, #3 |

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
