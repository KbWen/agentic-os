---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12 + optimization-round-2026-05-04
created: 2026-04-12
last_updated: 2026-05-04
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
| 22 | Rollback plan existence check in /ship (advisory, feature/arch-change only) | Expert review: rollback is documented not tested | — | quick-win | Shipped | — |
| 23 | Evidence section terse format (current gate block is already structured; tighten §Evidence prose) | Expert review: audit trail opacity | — | quick-win | Pending | — |
| 24 | Scope breach detection in /implement (actual files vs plan) | Expert review: silent scope creep | — | quick-win | Shipped | — |
| 25 | Ship-phase gate receipt audit (verify prior phases have receipts, /ship only) | Expert review: Work Log tampering risk | — | quick-win | Shipped | — |
| 26 | ~~Skill whitelist~~ — Reverted: auto-load is intentional for extensibility; code review is the real gate | Expert review: prompt injection via skill files | — | — | Cancelled | — |
| 27 | ADR auto-discovery in bootstrap (frontmatter-only scan) | Expert review: ADR indexing weakness | — | quick-win | Shipped | — |
| 28 | Token budget instrumentation (optional files_read counter in §Session Info) | Expert review: unverified token budgets | — | quick-win | Pending | — |
| 29 | SKILL.md heading-scope optimization (phase-entry loads only essential sections) | Upstream H73: ~30% skill token savings | — | quick-win | Shipped | — |
| 30 | Claude hooks enforcement layer (Stop sentinel, PreToolUse phase guard, PreCompact Work Log guard, UserPromptSubmit warn-only) | Opt-2026-05-04 T1.1a — closes HIGH lesson 19c054e7 (MUST without enforcement = theatre) | — | feature | Pending | — |
| 31 | Cross-platform validate.sh sentinel + Work Log final-line marker check | Opt-2026-05-04 T1.1b — non-Claude platforms parity | — | quick-win | Shipped | #30 |
| 32 | Reviewer freshness invariant in /review template + Global Lesson cross-link | Opt-2026-05-04 T1.4 — codifies HIGH lesson 4faa557a (multi-agent same-vendor blind spots) | — | quick-win | Shipped | — |
| 33 | Claude Code plugin packaging (.claude-plugin/plugin.json + bin/ + commands/agents/hooks bundling, no monitors) | Opt-2026-05-04 T1.2 — Claude distribution channel; one-step install for acx-* shims + workflows | — | feature | Pending | #30, #31 |
| 34 | AGENTS.override.md precedence chain support (mirror Codex pattern, byte-budget contract) | Opt-2026-05-04 T2.2a — per-machine override without polluting repo | — | quick-win | Shipped | — |
| 35 | /spec-intake Clarification Pass (≤3 questions before emitting spec, recorded in spec ## Clarifications Resolved) | Opt-2026-05-04 T2.A — borrows spec-kit Clarify gate without adding a new phase | — | quick-win | Shipped | — |
| 36 | /app-init onboard mode (read-only stdout summary for existing repo, no file writes; absorbs #39 /recap pointer) | Opt-2026-05-04 T2.B — w15 /team-onboarding pattern, no doc proliferation | — | quick-win | Shipped | — |
| 37 | /plan template `[P]` parallel-task marker | Opt-2026-05-04 — spec-kit dependency-aware ordering for /implement | — | quick-win | Shipped | — |
| 38 | AGENTS.md token-budget pass (~150 → ≤100 lines, link out detail to guides) | Opt-2026-05-04 T3 — "selling ad space" discipline (sshh) | — | quick-win | Pending | — |
| 39 | /recap workflow pointer to Work Log Phase Summary (no new doc) | Opt-2026-05-04 T3 — w17 session-recap leverage; absorbed into #36 Onboard Mode | — | tiny-fix | Shipped | — |
| 40 | review.md /ultrareview callout + hotfix.md /autofix-pr callout (Claude-CLI-only doc hook-in) | Opt-2026-05-04 T1.3 (descoped) — guide users to Anthropic cloud review fleet | — | tiny-fix | Shipped | — |

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
