# Project Current State (vNext)

- **Project Intent**: Self-managed Agent OS for AI coding agents — structured governance, workflows, and skills for autonomous development.
- **Core Guardrails**:
  - Correctness first: No claim of completion without evidence.
  - Small & reversible: Prioritize small, reversible changes; avoid unauthorized refactoring.
  - Document-first: Core logic or structural changes require a Spec/ADR first.
  - Handoff gate: Non-`tiny-fix` tasks must produce a traceable handoff summary.
- **System Map**:
  - Global SSoT: `.agentcortex/context/current_state.md`
  - Task Isolation: `.agentcortex/context/work/<worklog-key>.md`
  - Active Work Log Path: derive <worklog-key> from the raw branch name using filesystem-safe normalization before any gate checks.
  - Workflows & Policies: `.agent/workflows/*.md`, `.agent/rules/*.md`
- **Last Updated**: 2026-05-04
- **Last Verified**: 2026-05-04
- **Update Sequence**: 10
- **ADR Index**:
  - docs/adr/ADR-001-governance-friction-tuning.md — ADR-001: Governance Friction Tuning, accepted 2026-04-23
  - docs/adr/ADR-002-guarded-governance-writes.md — ADR-002: Guarded Governance Writes (lock unification + CI lint + lifecycle frontmatter), accepted 2026-04-25
  - docs/adr/ADR-003-hash-chained-audit-log.md — ADR-003: Hash-Chained Tamper-Evident Audit Log (INDEX.jsonl), proposed 2026-04-25
- **Active Backlog**: (none yet)
- **Spec Index** (framework template specs at `.agentcortex/specs/`; project specs go to `docs/specs/`):
  - docs/specs/lock-unification.md — Guarded Governance Writes implementation spec, [Shipped 2026-04-25] (ADR-002)
- **Canonical Commands**:
  - `/spec-intake`: Import external specs (from other LLMs, documents, or natural language). Handles large product specs via decomposition. Runs before `/bootstrap`.
  - `/bootstrap`: Task initialization & classification freeze.
  - `/plan`: Define target files, steps, risks, and rollback.
  - `/implement`: Execute implementation only when `IMPLEMENTABLE`.
  - `/review`: Check AC alignment & scope creep.
  - `/test`: Report test coverage via Test Skeleton.
  - `/handoff`: Output resumable state summary (mandatory for non-tiny-fix).
  - `/decide`: Record key decisions with reasoning to prevent cross-session re-derivation.
  - `/test-classify`: Auto-select test depth and evidence format based on task classification.
  - `/ship`: Consolidate evidence and update/archive state.
  - `ask-openrouter`: [OPTIONAL] External model delegation. See `.agent/workflows/ask-openrouter.md`.
  - `codex-cli`: [OPTIONAL] Codex CLI delegation. See `.agent/workflows/codex-cli.md`.
- **References**:
  - `AGENTS.md`
  - `.agent/rules/engineering_guardrails.md`
  - `.agent/rules/state_machine.md`
  - `.agentcortex/docs/CODEX_PLATFORM_GUIDE.md`
  - `.agentcortex/docs/guides/token-governance.md` *(manual-only)*
  - `.agentcortex/docs/guides/context-budget.md` *(manual-only)*

> [!NOTE]
> This file is the Single Source of Truth for global project context only.
> Do not store per-task progress here; write progress to `.agentcortex/context/work/<worklog-key>.md`.

## Global Lessons (AI Error Pattern Registry)
>
> Structured format:
> `- [Category: <tag>][Severity: <HIGH|MEDIUM|LOW>][Trigger: <normalized-trigger>] <lesson>`
>
> `/implement` reviews active HIGH-severity lessons before code changes. `/retro` may append new structured entries via guarded write.

- [Category: classification-flow][Severity: MEDIUM][Trigger: polish-pass-or-audit-batch][prev: GENESIS] When the task is a batch of audit-driven polish edits that touch governance files (AGENTS.md, .agent/rules/*), the governance-file exclusion pushes it to `quick-win` minimum — not automatically `feature`. Classify by the flow you actually intend to run (quick-win skips spec + handoff legitimately); do not silently adopt `feature` label while running the quick-win flow. Self-check at bootstrap: "Am I going to write a spec? Will I run /handoff? If no to both, classification is quick-win."
- [Category: worklog-format][Severity: LOW][Trigger: worklog-creation][prev: 7d331603] Worklog header fields MUST use markdown list format (`- Branch: ...`) to match `validate.sh` regex `^- (\*\*Branch\*\*|Branch):`. YAML frontmatter and markdown tables both fail the check. Template at `.agentcortex/templates/worklog.md` uses a table for readability but the validator accepts only the list form today.
- [Category: branch-awareness][Severity: LOW][Trigger: session-start-multi-turn-task][prev: ea7ae3df] Run `git branch --show-current` at the start of any non-trivial task before deriving the worklog-key. The system-prompt gitStatus snapshot is taken once at session start and can become stale if the branch changed externally.
- [Category: windows-install][Severity: MEDIUM][Trigger: windows-cmd-lightweight-install][prev: 285f5c5e] On Windows, installer wrappers should prefer PowerShell or a real Git Bash path over PATH `bash.exe`; the WindowsApps `bash.exe` can be a WSL placeholder and break lightweight downstream installs when no distro is configured.
- [Category: audit-method][Severity: HIGH][Trigger: multi-agent-roundtable-same-vendor][prev: 4faa557a] When using sub-agent "expert roundtable" for adversarial review, ALL sub-agents are the same model with shared training data and shared blind spots. The "diversity of perspective" is theatre. For architecture-level audits or trust-boundary work, MUST include at least one external signal: WebFetch of published external sources, `/ask-openrouter` to a different vendor, OR human review. Confirmed during the 2026-04-25 governance audit when a 4-Claude roundtable agreed on a CRITICAL finding (skill missing on Antigravity path) that turned out to be a false alarm — only spot-verification with `file` and `head` revealed the dual-path stub design was intentional.
- [Category: prioritization][Severity: HIGH][Trigger: audit-with-mixed-severity-findings][prev: 8afe0300] When an audit finds mixed CRITICAL/HIGH/MEDIUM and the agent ships fixes for the easy infrastructure (locks, lint, frontmatter) while deferring CRITICAL structural issues (prompt injection, state-machine reverse transition, honor-system enforcement) to "future ADR", that IS the easy-fix bias pattern. Self-check before ship: "Are all CRITICAL findings fixed OR scheduled with a specific PR # and date?" If still abstract "future work", ship is incomplete. Confirmed: ADR-002 shipped 3 infrastructure decisions while leaving SEC-N1 prompt injection and CC-2 honor-system both unfixed.
- [Category: adr-discipline][Severity: MEDIUM][Trigger: adr-bundling-multiple-decisions][prev: 6cf6a979] Bundling multiple architectural decisions into one ADR (e.g., ADR-002 D2.1+D2.2+D2.3) trades short-term commit count for long-term spec drift. ADR-002's bundled spec accumulated 3 deferred ACs (AC-23/24/25) before ship. Future ADRs: 1 architectural decision per ADR. Multiple ADRs OK and preferred. "Mirror ADR-001's 3-decision discipline" is the wrong precedent — the right unit is the smallest decision that ships independently with its own contract.
- [Category: enforcement][Severity: HIGH][Trigger: must-rule-without-validator][prev: 19c054e7] Every "MUST" rule in AGENTS.md / engineering_guardrails.md that depends on agent self-attestation (Sentinel `⚡ ACX`, Token Leak Drift Log audit receipts, Skill cache hash, "MUST sanitize Work Log") is a honor-system rule and is functionally theatre. Adversary feasibility is 10/10 for these (a single user message can disable any of them). Discipline: every "MUST" = 1 hook OR validator OR test OR external observer. Rules without enforcement should be DELETED rather than left as honor-system theatre. Adding "MUST" without enforcement is anti-help — it creates false confidence the rule is in effect.
- [Category: bootstrap-flow][Severity: HIGH][Trigger: post-first-adr-architecture-change][prev: efbd9e63] `bootstrap §0a` "App Architecture Check" condition `1. No ADR exists: docs/adr/ contains no project-specific ADR.` becomes permanently False once ANY ADR ships. After ADR-001 landed, all subsequent `architecture-change` tasks silently skip the ADR prompt — the very next architecture-change (ADR-002) already triggered this regression but was caught by accident. Fix: replace existence check with frontmatter `applies_to:` glob coverage check. Lesson: rules with date-dependent trigger conditions (e.g., "when X exists" / "when X count == 0") need explicit post-ship validation and decay-aware re-test.
- [Category: governance-proposal][Severity: MEDIUM][Trigger: plan-proposes-must-rule][prev: 7f5a25c3] When /plan proposes adding a MUST rule to AGENTS.md or .agent/rules/, cross-check the [enforcement][HIGH] Global Lesson immediately at plan time — not just at /implement. A MUST rule without a corresponding hook, validator, or test is honor-system theatre regardless of where in the workflow it is caught. Self-check: "What enforces this rule if the AI ignores it?" If the answer is "nothing", delete the rule or add the enforcement first.

## Ship History

### Ship-feat-optimization-batch2-2026-05-04
- Feature shipped: 4 follow-up quick-wins on `feat/optimization-hooks-2026-05-04` branch (PR #87 same-PR addition).
- Edits:
  - `.agentcortex/bin/validate.{sh,ps1}` — graduated active-work-log threshold: WARN at >8, FAIL at >12 (was WARN-only); plus `ARCHIVE_SIZE_WARN_KB` (default 10 MB) WARN check on `.agentcortex/context/archive/`.
  - `.agentcortex/templates/worklog.md` — optional `Files Read: N` field in `## Session Info` for token-budget instrumentation; `## Evidence` section now references `engineering_guardrails.md §5.2b Evidence Truncation Rule` (3-line success / 10-line failure caps).
- Tests: validate 73 PASS / 7 WARN / 0 FAIL (archive 74 KB, 8/8 active logs).
- Backlog rows shipped: #10, #12, #23, #28. Pending count 20 → 16.
- Commits: pending — same branch as PR #87.

### Ship-feat-optimization-hooks-2026-05-04
- Feature shipped: Closing the Claude-platform half of backlog #30 — PreCompact hook + framework receipt integration. Stop hook (`check-sentinel.py`) was previously shipped under CC-2/L4 but its violations.jsonl was never read by validate; this ship closes that loop. PreToolUse + UserPromptSubmit deferred (risk > ROI per design review).
- Edits:
  - `.claude/hooks/check-precompact.py` — new PreCompact hook; refuses compaction when active Work Log `## Phase Summary` is empty or stale relative to `Current Phase`. WARN by default, blocks (exit 2) when `AGENTIC_OS_PRECOMPACT_BLOCK=1`. Violation receipts at `.agentcortex/context/precompact-violations.jsonl`.
  - `.claude/settings.json` — wired PreCompact hook alongside existing Stop hook.
  - `tests/guard/test_precompact_hook.py` — 13 unit tests covering header parsing (list + table form), Phase Summary extraction, evaluate logic, end-to-end with temp Work Logs, and block-mode exit code.
  - `.agentcortex/bin/validate.{sh,ps1}` — read both `sentinel-violations.jsonl` and `precompact-violations.jsonl`; emit WARN with count when non-zero, PASS when zero. Capability-by-presence (absent file = PASS).
  - `.gitignore` — added `precompact-violations.jsonl` (alongside existing sentinel entry).
- Tests: Pass — `python -m unittest tests.guard.test_sentinel_hook tests.guard.test_precompact_hook` → 27/27 in 0.1s. validate: 72 PASS / 7 WARN / 0 FAIL (new WARN: 3 historical sentinel violations now surfaced — these were silently accumulating in the receipt file before this ship).
- Commits: pending — see `feat/optimization-hooks-2026-05-04` branch.
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
- Commits: pending — see `feat/optimization-round-2026-05-04` branch.
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

- **v1.1.2** (2026-04-17): Polish batch 2 — Python advisory in deploy.sh (1.1), guardrails Loaded-Sections Receipt (3.2), bootstrap Reading Mode Table + §0 decision table (3.3 + 2.1), Confidence Gate harmonized with structured receipts + step-level in /implement (2.3), Read-Once Drift Log audit receipt in AGENTS.md (4.3). Commit `4976a92`. Closes remaining 6 of 12 post-v1.1.0 audit findings. [CHANGELOG](../../CHANGELOG.md#112---2026-04-17)
- **v1.1.1-batch1** (2026-04-17): Polish pass — installer UX (Git-bash detection, clone progress), governance wiring (Confidence Gate receipt in /plan + /ship, No-Bypass scope clarified in AGENTS.md), token discipline (CLAUDE.md 51→27 lines), skill index signposted in routing.md §3. Commit `95ceafb`. Addresses 6 of 12 audit findings; remaining 6 deferred to batch 2 on same branch. [CHANGELOG](../../CHANGELOG.md#111---2026-04-17)
- **v1.1.0** (2026-04-16): Token optimization & governance hardening. SKILL.md heading-scope (#57), phase output compression (#54), expert review quick-wins (#56), deploy fixes (#52, #53, #55). [CHANGELOG](../../CHANGELOG.md#110---2026-04-16)
