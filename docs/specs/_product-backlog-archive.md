---
status: archive
title: Product Backlog — Completed Archive
source: split out of _product-backlog.md (backlog item #8)
created: 2026-06-02
last_updated: 2026-06-02
---

# Product Backlog — Completed Archive

Cold storage for **Shipped** and **Cancelled** backlog entries, split out of
the living `_product-backlog.md` so the active index stays small (backlog #8).
Entry numbers are preserved verbatim — dependency references (`#N`) in the
living backlog still resolve here. Ship details: see Ship History in
`.agentcortex/context/current_state.md` and `.agentcortex/context/archive/`.

## Completed Entries

| # | Feature | Kind | Labels | Priority | Spec File | Tier | Status | Dependencies |
|---|---|---|---|---|---|---|---|---|
| 2 | Global Lessons cap + archive rotation | — | — | — | — | quick-win | Shipped | — |
| 4 | Spec Index cap + archive section | — | — | — | — | quick-win | Shipped | — |
| 5 | Work Log compaction: validate WARN→FAIL | — | — | — | — | quick-win | Shipped | — |
| 6 | `_raw-intake-<date>.md` cleanup (MAY→MUST) | — | — | — | — | quick-win | Shipped | — |
| 8 | `_product-backlog.md` completed backlog archive | framework | governance | P2 | — | quick-win | Shipped | — |
| 9 | ~~`docs/reviews/` dead reference~~ — not a bug; created by `/audit`, ship check is capability-by-presence | — | — | — | — | tiny-fix | Cancelled | — |
| 10 | Active Work Log count: graduated WARN (>8) → FAIL (>12) | — | — | — | — | quick-win | Shipped | — |
| 12 | validate.{sh,ps1}: archive size WARN check (Global Lessons cap already PASS) | — | — | — | — | quick-win | Shipped | — |
| 15 | Anti-Rationalization Pattern (framework-wide enhancement) | governance | skills | P2 | docs/specs/skill-research-integration.md | quick-win | Shipped | #14 |
| 19 | SSoT atomic writes (guard_context_write: CAS or transactional store) | framework | concurrency | P1 | — | feature | Shipped | 2026-05-26 |
| 20 | CI security scanning (Semgrep + TruffleHog + dependency audit) | security | ci | P1 | — | feature | Shipped | 2026-05-11 |
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
| 34 | AGENTS.override.md precedence chain support (mirror Codex pattern, byte-budget contract) | — | — | — | — | quick-win | Shipped | — |
| 35 | /spec-intake Clarification Pass (≤3 questions before emitting spec, recorded in spec ## Clarifications Resolved) | — | — | — | — | quick-win | Shipped | — |
| 36 | /app-init onboard mode (read-only stdout summary for existing repo, no file writes; absorbs #39 /recap pointer) | — | — | — | — | quick-win | Shipped | — |
| 37 | /plan template `[P]` parallel-task marker | — | — | — | — | quick-win | Shipped | — |
| 38 | AGENTS.md token-budget pass (~150 → ≤100 lines, link out detail to guides) | governance | docs | P2 | — | quick-win | Shipped | — |
| 39 | /recap workflow pointer to Work Log Phase Summary (no new doc) | — | — | — | — | tiny-fix | Shipped | — |
| 40 | review.md /ultrareview callout + hotfix.md /autofix-pr callout (Claude-CLI-only doc hook-in) | — | — | — | — | tiny-fix | Shipped | — |
| 41 | Framework self-test integrity: restore tests/guard collection (orphaned hook tests) + gate tests/guard in CI | framework | testing | P1 | — | quick-win | Shipped | — |
| 42 | Audit-chain tamper-evidence hardening: tail-truncation detection (git append-only witness) + guard `migrate` against re-blessing forged history [audit C1+C2] | framework | governance | P1 | docs/specs/audit-chain-tamper-evidence.md | feature | Shipped | — |
| 43 | ~~Guard write lock unification [audit C3]~~ — **Cancelled (verified not-a-bug 2026-05-29)**: cmd_write wraps BOTH replace & append in `file_lock(lock_path_for_target)`; append_write's sidecar is a redundant nested lock and has no direct callers. No disjoint-lock path. Defensive docstrings added to prevent the latent direct-call footgun. | framework | concurrency | P1 | — | — | Cancelled | — |
| 44 | validate.sh ↔ validate.ps1 parity backfill [audit D] — verified: only gate-receipt-schema check was a real PS1 gap (others already at parity); backfilled into validate.ps1 | framework | tooling | P2 | — | quick-win | Shipped | — |
