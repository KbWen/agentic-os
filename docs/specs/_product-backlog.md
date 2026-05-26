---
status: living
title: Product Backlog
source: governance-bloat-review-2026-04-12 + optimization-round-2026-05-04
created: 2026-04-12
last_updated: 2026-05-11
---

# Product Backlog

## Source Summary

Governance file bloat review (2026-04-12) identified 10 findings across P0–P2: multiple data surfaces grow unbounded (archive/, Global Lessons, Spec Index, INDEX.jsonl), compaction mechanisms are advisory-only, and process artifacts (_raw-intake archives, superseded L2 entries, shipped specs) accumulate without consumers. Industry patterns (LSM-tree compaction, progressive summarization, tiered retention) converge on a 4-state document lifecycle with LLM-driven summarization at tier transitions.

## Feature Inventory

| # | Feature | Kind | Labels | Priority | Spec File | Tier | Status | Dependencies |
|---|---|---|---|---|---|---|---|---|
| 1 | Tiered Document Lifecycle Engine (4-tier state machine + config) | framework | lifecycle | P1 | docs/specs/tiered-doc-lifecycle.md | feature | Pending | — |
| 2 | Global Lessons cap + archive rotation | — | — | — | — | quick-win | Shipped | — |
| 3 | Archive directory GC + INDEX.jsonl rotation | framework | lifecycle | P2 | — | feature | Pending | #1 |
| 4 | Spec Index cap + archive section | — | — | — | — | quick-win | Shipped | — |
| 5 | Work Log compaction: validate WARN→FAIL | — | — | — | — | quick-win | Shipped | — |
| 6 | `_raw-intake-<date>.md` cleanup (MAY→MUST) | — | — | — | — | quick-win | Shipped | — |
| 7 | Domain Doc L2 superseded entry archival | framework | lifecycle | P2 | — | quick-win | Pending | — |
| 8 | `_product-backlog.md` completed backlog archive | framework | governance | P2 | — | quick-win | Pending | — |
| 9 | ~~`docs/reviews/` dead reference~~ — not a bug; created by `/audit`, ship check is capability-by-presence | — | — | — | — | tiny-fix | Cancelled | — |
| 10 | Active Work Log count: graduated WARN (>8) → FAIL (>12) | — | — | — | — | quick-win | Shipped | — |
| 11 | Shipped specs accumulation — status-driven filtering | framework | lifecycle | P2 | — | quick-win | Pending | #1 |
| 12 | validate.{sh,ps1}: archive size WARN check (Global Lessons cap already PASS) | — | — | — | — | quick-win | Shipped | — |
| 13 | Warm→Cold LLM summarization pass in /ship | framework | lifecycle | P2 | — | feature | Pending | #1, #3 |
| 14 | External Skill Research & Integration (Phase A: 3 core skills) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Pending | — |
| 15 | Anti-Rationalization Pattern (framework-wide enhancement) | governance | skills | P2 | docs/specs/skill-research-integration.md | quick-win | Pending | #14 |
| 16 | Skill Validation Pipeline (meta-governance) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Pending | #14 |
| 17 | Hard Work Log lock (advisory → blocking) | framework | concurrency | P1 | — | feature | Pending | — |
| 18 | Lightweight routing heuristics (decision tree in config.yaml, not a DSL) | framework | routing | P2 | — | quick-win | Pending | — |
| 19 | SSoT atomic writes (guard_context_write: CAS or transactional store) | framework | concurrency | P1 | — | feature | Shipped | 2026-05-26 |
| 20 | CI security scanning (Semgrep + TruffleHog + dependency audit) | security | ci | P1 | — | feature | Shipped | 2026-05-11 |
| 21 | Skill cache timestamp + staleness invalidation | framework | skills | P2 | — | quick-win | Pending | — |
| 22 | Rollback plan existence check in /ship (advisory, feature/arch-change only) | — | — | — | — | quick-win | Shipped | — |
| 23 | Evidence section terse format reference to §5.2b in worklog template | — | — | — | — | quick-win | Shipped | — |
| 24 | Scope breach detection in /implement (actual files vs plan) | — | — | — | — | quick-win | Shipped | — |
| 25 | Ship-phase gate receipt audit (verify prior phases have receipts, /ship only) | — | — | — | — | quick-win | Shipped | — |
| 26 | ~~Skill whitelist~~ — Reverted: auto-load is intentional for extensibility; code review is the real gate | — | — | — | — | — | Cancelled | — |
| 27 | ADR auto-discovery in bootstrap (frontmatter-only scan) | — | — | — | — | quick-win | Shipped | — |
| 28 | Token budget instrumentation (optional Files Read counter in §Session Info, worklog template) | — | — | — | — | quick-win | Shipped | — |
| 29 | SKILL.md heading-scope optimization (phase-entry loads only essential sections) | — | — | — | — | quick-win | Shipped | — |
| 30 | Claude hooks enforcement layer (Stop sentinel ✅ shipped previously; PreCompact Work Log guard ✅ shipped 2026-05-04; PreToolUse + UserPromptSubmit deferred — risk > ROI) | — | — | — | — | feature | Shipped | — |
| 31 | Cross-platform validate.sh sentinel + Work Log final-line marker check | — | — | — | — | quick-win | Shipped | #30 |
| 32 | Reviewer freshness invariant in /review template + Global Lesson cross-link | — | — | — | — | quick-win | Shipped | — |
| 33 | Claude Code plugin packaging (.claude-plugin/plugin.json + bin/ + commands/agents/hooks bundling, no monitors) | dx | packaging | P2 | — | feature | Pending | #30, #31 |
| 34 | AGENTS.override.md precedence chain support (mirror Codex pattern, byte-budget contract) | — | — | — | — | quick-win | Shipped | — |
| 35 | /spec-intake Clarification Pass (≤3 questions before emitting spec, recorded in spec ## Clarifications Resolved) | — | — | — | — | quick-win | Shipped | — |
| 36 | /app-init onboard mode (read-only stdout summary for existing repo, no file writes; absorbs #39 /recap pointer) | — | — | — | — | quick-win | Shipped | — |
| 37 | /plan template `[P]` parallel-task marker | — | — | — | — | quick-win | Shipped | — |
| 38 | AGENTS.md token-budget pass (~150 → ≤100 lines, link out detail to guides) | governance | docs | P2 | — | quick-win | Pending | — |
| 39 | /recap workflow pointer to Work Log Phase Summary (no new doc) | — | — | — | — | tiny-fix | Shipped | — |
| 40 | review.md /ultrareview callout + hotfix.md /autofix-pr callout (Claude-CLI-only doc hook-in) | — | — | — | — | tiny-fix | Shipped | — |

## Status Key

- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
