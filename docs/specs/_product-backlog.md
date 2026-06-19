---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12 + optimization-round-2026-05-04 + optimization-research-2026-06-02
created: 2026-04-12
last_updated: 2026-06-15
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
| 18 | Lightweight routing heuristics (decision tree in config.yaml, not a DSL) | framework | routing | P2 | — | quick-win | Pending | [#148](https://github.com/KbWen/agentic-os/issues/148) | — |
| 21 | Skill cache timestamp + staleness invalidation | framework | skills | P2 | — | quick-win | Pending | [#149](https://github.com/KbWen/agentic-os/issues/149) | — |
| 33 | Claude Code plugin packaging (.claude-plugin/plugin.json + bin/ + commands/agents/hooks bundling, no monitors) | dx | packaging | P2 | — | feature | Pending | [#150](https://github.com/KbWen/agentic-os/issues/150) | #30, #31 |
| 70 | Export structured JSON Drift Log on ship for CI/CD audit trails | framework | governance | P2 | — | feature | Pending | [#193](https://github.com/KbWen/agentic-os/issues/193) | — |
| 69 | RPI→QRSPI flow-adaptation study (alignment-side Q/D/S decomposition before Plan; strands A–E incl. governance load) | framework | governance | P1 | docs/specs/_research-rpi-qrspi-corroboration.md | feature | Pending | [#176](https://github.com/KbWen/agentic-os/issues/176) | #45, #65 |
| 72 | zh-TW README FAQ mirror (parity with EN discoverability FAQ added in PR #230) | docs | i18n | P3 | — | quick-win | Pending | — | — |
| 76 | Research persist-before-browse note (lightweight `research.md` convention; capsule design retired per external prior-art) | framework | governance | P2 | — | quick-win | Shipped | [#251](https://github.com/KbWen/agentic-os/issues/251) | — |
| 77 | D — Reviewable Task→Step hierarchy | framework | governance | P1 | — | architecture-change | Pending | [#252](https://github.com/KbWen/agentic-os/issues/252) | — |
| 78 | B+C — Task capsule + one read-only reviewer (two verdicts) | framework | governance | P1 | — | feature | Pending | [#253](https://github.com/KbWen/agentic-os/issues/253) | #77 |
| 79 | A — Skill effectiveness evaluation harness | framework | skills | P2 | — | feature | Pending | [#254](https://github.com/KbWen/agentic-os/issues/254) | #77, #78 |
| 80 | G1a — First-party SKILL.md compatibility floor (delta over validate.sh) | framework | skills | P1 | — | quick-win | Pending | [#255](https://github.com/KbWen/agentic-os/issues/255) | — |
| 81 | G1b — Activated-skill provenance inventory | framework | skills | P2 | — | feature | Pending | [#256](https://github.com/KbWen/agentic-os/issues/256) | — |
| 82 | Karpathy-principles source/license provenance wording | docs | governance | P3 | — | tiny-fix | Pending | [#257](https://github.com/KbWen/agentic-os/issues/257) | — |

> Rows whose GH issue is CLOSED-premature (#7, #13, #18, #21, #33) are kept deliberately as
> future directions — reopen the issue when a concrete signal appears (2026-06-02 curation).
> Rows #76–82 (added 2026-06-19) came from the external skill/workflow-practices research (Node-15 synthesis). #76 was reduced to a lightweight `research.md` note-taking convention and the heavier capsule design (ADR-009 + draft spec) retired — external prior art (Anthropic context-engineering + multi-agent research system) treats research-state persistence as lightweight "structured note-taking", not infrastructure, and agentic-os already externalizes to Work Logs / private notes. **Reopen-triggers (record-only, no issue opened):** G2 byte/installer-verification → when an external skill-installation capability is separately approved; E context-free author testing → when #79 is built; F isolation-aware worktree portability → when a non-git-worktree platform target appears (must not duplicate existing worktree rules).
> Completed entries (#2, 4–6, 8–10, 12, 14–16, 19–20, 22–32, 34–44, 51, 66–68, 71, 73–75) are in [`_product-backlog-archive.md`](./_product-backlog-archive.md).

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
