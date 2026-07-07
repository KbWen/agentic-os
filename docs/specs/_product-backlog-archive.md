---
status: archive
title: Product Backlog — Completed Archive
source: split out of _product-backlog.md (backlog item #8)
created: 2026-06-02
last_updated: 2026-06-15
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
| 50 | Spec drift linter (AC coverage vs git diff, advisory) | framework | governance | P2 | docs/specs/spec-drift-linter.md | feature | Shipped | — |
| 56 | Cross-platform adapter generator (Gemini/Cursor/Copilot stubs) | framework | platform | P2 | docs/specs/multi-agent-review-guidelines.md | feature | Shipped | — |
| 17 | Hard Work Log lock (advisory → blocking) | framework | concurrency | P1 | docs/specs/worklog-lock-blocking.md | feature | Shipped | [#147](https://github.com/KbWen/agentic-os/issues/147) |
| 45 | Governance behavioral eval harness + DELETE-bias diff | framework | governance | P1 | docs/specs/governance-eval-harness.md | feature | Shipped | [#151](https://github.com/KbWen/agentic-os/issues/151) | — |
| 57 | CI hardening: pinned requirements + pip cache + UTF-8 + pytest on PR | framework | ci | P2 | — | quick-win | Shipped | [#163](https://github.com/KbWen/agentic-os/issues/163) | — |
| 65 | Deletion-First Norm + ADD-gate signal tiering | framework | governance | P1 | docs/specs/deletion-first-add-gate.md | feature | Shipped | [#166](https://github.com/KbWen/agentic-os/issues/166) | #45 |
| 48 | ~~Skill discovery linter + skill-cards.json index~~ — Cancelled (verified already-implemented: trigger-registry.yaml + trigger-compact-index.json + validate_trigger_metadata.py; issue #154 closure 2026-06-02; row desynced until 2026-06-10) | framework | skills | P2 | — | quick-win | Cancelled | [#154](https://github.com/KbWen/agentic-os/issues/154) | — |
| 58 | ~~Downstream local_guardrails.md extension point~~ — Cancelled (redundant: ADR-004 override layer already provides the surface; issue #164 closed 2026-06-10 after expert verification; zero downstream demand signal) | framework | governance | P2 | — | quick-win | Cancelled | [#164](https://github.com/KbWen/agentic-os/issues/164) | — |
| 14 | External Skill Research & Integration (Phase A: 3 core skills) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Shipped | [#145](https://github.com/KbWen/agentic-os/issues/145) | — |
| 51 | Token lifecycle baseline + drift detector | framework | ci | P2 | — | quick-win | Shipped | [#157](https://github.com/KbWen/agentic-os/issues/157) | — |
| 71 | T1 pre-commit credential regex (secrets L2 machine layer; CI TruffleHog is post-commit backstop) | framework | governance | P2 | — | quick-win | Shipped | [#225](https://github.com/KbWen/agentic-os/issues/225) | — |
| 73 | CI PR-diff credential scan (extend scan_credentials.py --staged to a --range base..head mode in a pull_request job → contributors who never install the opt-in hook still get pre-merge protection; the real cross-contributor T1) | review-finding | governance | P2 | — | quick-win | Shipped | — | #71 |
| 74 | ShellCheck CI lints only `**/*.sh` so `.githooks/*.sample` is never linted; fix the glob to cover the hook samples | review-finding | ci | P2 | — | quick-win | Shipped | — | #71 |
| 75 | Pre-commit hook dev-friendliness — the #192 hook gates every commit on the full validator; a gitignored, CI-invisible worklog-count FAIL blocked all commits. Shipped: worklog-count FAIL→WARN. Future dev-UX option: changed-files-scoped / advisory validator step in the hook (keep the #225 credential block hard) | review-finding | dx | P2 | — | quick-win | Shipped | — | #71 |
| 16 | ~~Skill Validation Pipeline (meta-governance)~~ — Cancelled (redundant: ~85-90% already implemented by validate.sh stub↔SKILL parity + phase hooks + acx-shim checks + validate_trigger_metadata.py registry/compact-index freshness; issue #146 closed 2026-06-15; same disposition as #154/#48) | framework | skills | P2 | docs/specs/skill-research-integration.md | feature | Cancelled | [#146](https://github.com/KbWen/agentic-os/issues/146) | #14 |
| 66 | ~~Recommended-workflows advisory layer~~ — Cancelled (no present consumer: trigger_runtime_core.py has zero recommend logic, routing.md has no Recommended-Workflows section; advisory-only = no teeth; issue #167 closed 2026-06-15) | framework | routing | P2 | — | feature | Cancelled | [#167](https://github.com/KbWen/agentic-os/issues/167) | — |
| 67 | ~~Canonical-doc-path gate + research-wiki sidecar~~ — Cancelled (premature: would add a MUST backed only by an optional validate WARN = honor-system; proposed consumer docs/research/wiki/ doesn't exist; reserved-namespace risk already covered by the Write Path Guard; issue #168 closed 2026-06-15) | framework | governance | P2 | — | quick-win | Cancelled | [#168](https://github.com/KbWen/agentic-os/issues/168) | — |
| 68 | ~~Authority-map metadata (read-this-not-that resolver)~~ — Cancelled (redundant: duplicates trigger-registry.yaml canonical_ref/detail_ref/runtime_anchor + routing.md authority precedence; same trap as #154/#48; non-skill slice has no cited present failure; issue #169 closed 2026-06-15) | framework | governance | P2 | — | quick-win | Cancelled | [#169](https://github.com/KbWen/agentic-os/issues/169) | — |
| 115 | Local-model delegation entry — `/ask-local` optional module (junior-executor patch contract, §8.2 reused) + codex-cli `--oss` variant | framework | adoption | P2 | docs/specs/local-model-delegation.md | feature | Shipped | [#316](https://github.com/KbWen/agentic-os/pull/316) | — |
