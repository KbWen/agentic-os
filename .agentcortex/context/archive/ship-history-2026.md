# Ship History Archive — 2026 (Entries 11–14)

Archived from `current_state.md ## Ship History` to stay within the 10-entry cap.

### Ship-feat-optimization-hooks-2026-05-04
- Feature shipped: Closing the Claude-platform half of backlog #30 — PreCompact hook + framework receipt integration. Stop hook (`check-sentinel.py`) was previously shipped under CC-2/L4 but its violations.jsonl was never read by validate; this ship closes that loop. PreToolUse + UserPromptSubmit deferred (risk > ROI per design review).
- Edits:
  - `.claude/hooks/check-precompact.py` — new PreCompact hook; refuses compaction when active Work Log `## Phase Summary` is empty or stale relative to `Current Phase`. WARN by default, blocks (exit 2) when `AGENTIC_OS_PRECOMPACT_BLOCK=1`. Violation receipts at `.agentcortex/context/precompact-violations.jsonl`.
  - `.claude/settings.json` — wired PreCompact hook alongside existing Stop hook.
  - `tests/guard/test_precompact_hook.py` — 13 unit tests covering header parsing (list + table form), Phase Summary extraction, evaluate logic, end-to-end with temp Work Logs, and block-mode exit code.
  - `.agentcortex/bin/validate.{sh,ps1}` — read both `sentinel-violations.jsonl` and `precompact-violations.jsonl`; emit WARN with count when non-zero, PASS when zero. Capability-by-presence (absent file = PASS).
  - `.gitignore` — added `precompact-violations.jsonl` (alongside existing sentinel entry).
- Tests: Pass — `python -m unittest tests.guard.test_sentinel_hook tests.guard.test_precompact_hook` → 27/27 in 0.1s. validate: 72 PASS / 7 WARN / 0 FAIL (new WARN: 3 historical sentinel violations now surfaced — these were silently accumulating in the receipt file before this ship).
- Commits: `0ca5788`; merged via `30e6fcc` (PR #87).
- Scope cuts: PreToolUse phase-discipline hook and UserPromptSubmit warn hook were evaluated and deferred — false-positive risk on legitimate edits/chat outweighs the catch rate. Document in Drift Log of work log.

### Ship-feat-optimization-round-2026-05-04
- Feature shipped: Quick-win batch from optimization-round-2026-05-04 — backlog rows #31, #32, #34, #35, #36, #37, #39, #40 (8 governance enhancements). Zero behavioral change to runtime; pure rule additions across 5 workflows + AGENTS.md + validate (sh/ps1).
- Edits:
  - `.agent/workflows/review.md` — Adversarial Reviewer Freshness Invariant H2 (codifies HIGH lesson 4faa557a) + Cloud Adversarial Review (`/ultrareview`) callout
  - `.agent/workflows/plan.md` — `[P]` parallel-task marker rule + template line (spec-kit pattern)
  - `.agent/workflows/spec-intake.md` — §4.5 Clarification Pass (≤3 questions, optional, single-round)
  - `.agent/workflows/app-init.md` — §10 Onboard Mode (read-only stdout, no doc writes; absorbs `/recap` pointer for active sessions)
  - `.agent/workflows/hotfix.md` — §6 Cloud PR Auto-Fix (`/autofix-pr`) callout
  - `AGENTS.md` — `## Override Layer (AGENTS.override.md)` precedence chain (mirrors Codex pattern)
  - `.agentcortex/bin/validate.{sh,ps1}` — Work Log Phase Summary sentinel marker (⚡ ACX) WARN check
- Tests: Pass — validate 71 PASS / 6 WARN / 0 FAIL (the new sentinel WARN counts 6 legacy logs without ⚡ ACX, by design WARN-only).
- Commits: `7b7071b`; merged via `30e6fcc` (PR #87).
- Source: external research round (Claude Code w14-w17, OpenAI Codex 2026 AGENTS.md docs, github/spec-kit, dsifry/metaswarm, sshh).
- Deferred: #30 (Claude hooks enforcement layer — feature), #33 (plugin packaging — feature), #38 (AGENTS.md token-budget pass — risky restructure).

### Ship-feat-acx-phase-shims-2026-05-04
- Feature shipped: acx-* phase shims for Claude Code native skill injection — 5 shims (.claude/agents/acx-{implementer,reviewer,tester,handoff,shipper}.md), validate.sh+ps1 shim skill-existence check, review.md acx-* enforcement check.
- Tests: Pass — validate 63 PASS / 0 FAIL; simulation confirmed native skill injection active at subagent startup.
- Commits: `94ab322`

### Ship-architecture-change-adr-002-lock-unification-2026-04-25
- Feature shipped: ADR-002 Guarded Governance Writes — D2.1 lock generalization (policy-driven scope, append mode, per-target receipts, configurable TTL, PID-liveness, lock_group stub for ADR-003); D2.2 CI lint `tools/lint_governed_writes.py` enforces guard usage on protected paths; D2.3 lifecycle frontmatter checker for governance docs (audit/, guides/governance-*, adr/, architecture L1).
- Tests: Pass — 56/56 in 0.4s + 8 Beast Mode adversarial scenarios green; live lint scan 0 FAIL / 67 WARN; live lifecycle scan 2 PASS / 3 WARN (grandfathered) / 0 FAIL.
- Commits: `65c5890` (ADR/spec), `20f2c21` (D2.1), `618ea61` (D2.2), `8eaf284` (D2.3) + ship commit.
- Spec drift: AC-24/AC-25 (ownership matrix doc + AGENTS.md pointer) deferred per Pragmatist roundtable + user direction; Architect content preserved in audit §0.4 + Work Log archive.

---

## Version History (archived)

- **v1.1.2** (2026-04-17): Polish batch 2 — Python advisory in deploy.sh (1.1), guardrails Loaded-Sections Receipt (3.2), bootstrap Reading Mode Table + §0 decision table (3.3 + 2.1), Confidence Gate harmonized with structured receipts + step-level in /implement (2.3), Read-Once Drift Log audit receipt in AGENTS.md (4.3). Commit `4976a92`. Closes remaining 6 of 12 post-v1.1.0 audit findings.
- **v1.1.1-batch1** (2026-04-17): Polish pass — installer UX (Git-bash detection, clone progress), governance wiring (Confidence Gate receipt in /plan + /ship, No-Bypass scope clarified in AGENTS.md), token discipline (CLAUDE.md 51→27 lines), skill index signpointed in routing.md §3. Commit `95ceafb`. Addresses 6 of 12 audit findings; remaining 6 deferred to batch 2 on same branch.
- **v1.1.0** (2026-04-16): Token optimization & governance hardening. SKILL.md heading-scope (#57), phase output compression (#54), expert review quick-wins (#56), deploy fixes (#52, #53, #55).
