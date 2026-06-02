---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12 + optimization-round-2026-05-04 + optimization-research-2026-06-02
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

> The **GH Issue** column links the GitHub tracker (`KbWen/agentic-os`). The
> **Dependencies** column uses bare `#N` = backlog entry numbers (this file).
> Entries #45–#68 came from a 2026-06-02 optimization-research pass mining a more
> mature internal reference implementation. The set was deliberately curated: each
> survivor was cross-checked against this repo's actual code paths over multiple
> verification rounds; items that were premature, already-handled, or
> deliberately-removed-before were dropped (DELETE-bias). The rows below are the
> verified ~1–2 month roadmap. See
> [`../OPTIMIZATION_ROADMAP.md`](../OPTIMIZATION_ROADMAP.md).

| # | Feature | Kind | Labels | Priority | Spec File | Tier | Status | GH Issue | Dependencies |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Tiered Document Lifecycle Engine (4-tier state machine + config) | framework | lifecycle | P1 | docs/specs/tiered-doc-lifecycle.md | feature | Pending | [#140](https://github.com/KbWen/agentic-os/issues/140) | — |
| 3 | Archive directory GC + INDEX.jsonl rotation | framework | lifecycle | P2 | — | feature | Pending | [#141](https://github.com/KbWen/agentic-os/issues/141) | #1 |
| 7 | Domain Doc L2 superseded entry archival | framework | lifecycle | P2 | — | quick-win | Pending | [#142](https://github.com/KbWen/agentic-os/issues/142) | — |
| 11 | Shipped specs accumulation — status-driven filtering | framework | lifecycle | P2 | — | quick-win | Pending | [#143](https://github.com/KbWen/agentic-os/issues/143) | #1 |
| 13 | Warm→Cold LLM summarization pass in /ship | framework | lifecycle | P2 | — | feature | Pending | [#144](https://github.com/KbWen/agentic-os/issues/144) | #1, #3 |
| 14 | External Skill Research & Integration (Phase A: 3 core skills) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Pending | [#145](https://github.com/KbWen/agentic-os/issues/145) | — |
| 16 | Skill Validation Pipeline (meta-governance) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Pending | [#146](https://github.com/KbWen/agentic-os/issues/146) | #14 |
| 17 | Hard Work Log lock (advisory → blocking) | framework | concurrency | P1 | — | feature | Pending | [#147](https://github.com/KbWen/agentic-os/issues/147) | — |
| 18 | Lightweight routing heuristics (decision tree in config.yaml, not a DSL) | framework | routing | P2 | — | quick-win | Pending | [#148](https://github.com/KbWen/agentic-os/issues/148) | — |
| 21 | Skill cache timestamp + staleness invalidation | framework | skills | P2 | — | quick-win | Pending | [#149](https://github.com/KbWen/agentic-os/issues/149) | — |
| 33 | Claude Code plugin packaging (.claude-plugin/plugin.json + bin/ + commands/agents/hooks bundling, no monitors) | dx | packaging | P2 | — | feature | Pending | [#150](https://github.com/KbWen/agentic-os/issues/150) | #30, #31 |
| 45 | Governance behavioral eval harness + DELETE-bias diff | framework | governance | P1 | — | feature | Pending | [#151](https://github.com/KbWen/agentic-os/issues/151) | — |
| 48 | Skill discovery linter + skill-cards.json index | framework | skills | P2 | — | quick-win | Pending | [#154](https://github.com/KbWen/agentic-os/issues/154) | — |
| 50 | Spec drift linter (AC coverage vs git diff, advisory) | framework | governance | P2 | — | quick-win | Pending | [#156](https://github.com/KbWen/agentic-os/issues/156) | — |
| 51 | Token lifecycle baseline + drift detector | framework | ci | P2 | — | quick-win | Pending | [#157](https://github.com/KbWen/agentic-os/issues/157) | — |
| 56 | Cross-platform adapter generator (Gemini/Cursor/Copilot stubs) | framework | platform | P2 | — | feature | Pending | [#162](https://github.com/KbWen/agentic-os/issues/162) | — |
| 57 | CI hardening: pinned requirements + pip cache + UTF-8 + pytest on PR | framework | ci | P2 | — | quick-win | Pending | [#163](https://github.com/KbWen/agentic-os/issues/163) | — |
| 58 | Downstream local_guardrails.md extension point | framework | governance | P2 | — | quick-win | Pending | [#164](https://github.com/KbWen/agentic-os/issues/164) | — |
| 65 | Deletion-First Norm + ADD-gate signal tiering | framework | governance | P1 | — | feature | Pending | [#166](https://github.com/KbWen/agentic-os/issues/166) | #45 |
| 66 | Recommended-workflows advisory layer | framework | routing | P2 | — | feature | Pending | [#167](https://github.com/KbWen/agentic-os/issues/167) | — |
| 67 | Canonical-doc-path gate + research-wiki sidecar | framework | governance | P2 | — | quick-win | Pending | [#168](https://github.com/KbWen/agentic-os/issues/168) | — |
| 68 | Authority-map metadata (read-this-not-that resolver) | framework | governance | P2 | — | quick-win | Pending | [#169](https://github.com/KbWen/agentic-os/issues/169) | — |

> Completed entries (#2, 4–6, 8–10, 12, 15, 19–20, 22–32, 34–44) are in [`_product-backlog-archive.md`](./_product-backlog-archive.md).

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
