---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12
created: 2026-04-12
last_updated: 2026-04-16T+expert-review-items
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
| 14 | External Skill Research & Integration (Phase A: 3 core skills) | Gap Analysis | docs/specs/skill-research-integration.md | feature | Pending | — |
| 15 | Anti-Rationalization Pattern (framework-wide enhancement) | Gap Analysis | docs/specs/skill-research-integration.md §4C | quick-win | Pending | #14 |
| 16 | Skill Validation Pipeline (meta-governance) | Gap Analysis | docs/specs/skill-research-integration.md §4D | feature | Pending | #14 |
| 17 | Hard Work Log lock (advisory → blocking) | Expert review: concurrency safety | — | feature | Pending | — |
| 18 | Lightweight routing heuristics (decision tree in config.yaml, not a DSL) | Expert review: routing ambiguity | — | quick-win | Pending | — |
| 19 | SSoT atomic writes (guard_context_write: CAS or transactional store) | Expert review: concurrent SSoT corruption | — | feature | Pending | — |
| 20 | CI security scanning (Semgrep + TruffleHog + dependency audit) | Expert review: security posture | — | feature | Pending | — |
| 21 | Skill cache timestamp + staleness invalidation | Expert review: stale skill cache | — | quick-win | Pending | — |
| 22 | Rollback plan existence check in /ship (advisory, feature/arch-change only) | Expert review: rollback is documented not tested | — | quick-win | Pending | — |
| 23 | Evidence section terse format (current gate block is already structured; tighten §Evidence prose) | Expert review: audit trail opacity | — | quick-win | Pending | — |
| 24 | Scope breach detection in /implement (actual files vs plan) | Expert review: silent scope creep | — | quick-win | Pending | — |
| 25 | Ship-phase gate receipt audit (verify prior phases have receipts, /ship only) | Expert review: Work Log tampering risk | — | quick-win | Pending | — |
| 26 | Skill whitelist / injection protection for auto-loaded skills | Expert review: prompt injection via skill files | — | quick-win | Pending | — |
| 27 | ADR auto-discovery in bootstrap (frontmatter-only scan) | Expert review: ADR indexing weakness | — | quick-win | Pending | — |
| 28 | Token budget instrumentation (optional files_read counter in §Session Info) | Expert review: unverified token budgets | — | quick-win | Pending | — |

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
