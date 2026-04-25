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
- **Last Updated**: 2026-04-25
- **Last Verified**: 2026-04-25
- **Update Sequence**: 6
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

- [Category: classification-flow][Severity: MEDIUM][Trigger: polish-pass-or-audit-batch] When the task is a batch of audit-driven polish edits that touch governance files (AGENTS.md, .agent/rules/*), the governance-file exclusion pushes it to `quick-win` minimum — not automatically `feature`. Classify by the flow you actually intend to run (quick-win skips spec + handoff legitimately); do not silently adopt `feature` label while running the quick-win flow. Self-check at bootstrap: "Am I going to write a spec? Will I run /handoff? If no to both, classification is quick-win."
- [Category: worklog-format][Severity: LOW][Trigger: worklog-creation] Worklog header fields MUST use markdown list format (`- Branch: ...`) to match `validate.sh` regex `^- (\*\*Branch\*\*|Branch):`. YAML frontmatter and markdown tables both fail the check. Template at `.agentcortex/templates/worklog.md` uses a table for readability but the validator accepts only the list form today.
- [Category: branch-awareness][Severity: LOW][Trigger: session-start-multi-turn-task] Run `git branch --show-current` at the start of any non-trivial task before deriving the worklog-key. The system-prompt gitStatus snapshot is taken once at session start and can become stale if the branch changed externally.
- [Category: windows-install][Severity: MEDIUM][Trigger: windows-cmd-lightweight-install] On Windows, installer wrappers should prefer PowerShell or a real Git Bash path over PATH `bash.exe`; the WindowsApps `bash.exe` can be a WSL placeholder and break lightweight downstream installs when no distro is configured.
- [Category: audit-method][Severity: HIGH][Trigger: multi-agent-roundtable-same-vendor] When using sub-agent "expert roundtable" for adversarial review, ALL sub-agents are the same model with shared training data and shared blind spots. The "diversity of perspective" is theatre. For architecture-level audits or trust-boundary work, MUST include at least one external signal: WebFetch of published external sources, `/ask-openrouter` to a different vendor, OR human review. Confirmed during the 2026-04-25 governance audit when a 4-Claude roundtable agreed on a CRITICAL finding (skill missing on Antigravity path) that turned out to be a false alarm — only spot-verification with `file` and `head` revealed the dual-path stub design was intentional.
- [Category: prioritization][Severity: HIGH][Trigger: audit-with-mixed-severity-findings] When an audit finds mixed CRITICAL/HIGH/MEDIUM and the agent ships fixes for the easy infrastructure (locks, lint, frontmatter) while deferring CRITICAL structural issues (prompt injection, state-machine reverse transition, honor-system enforcement) to "future ADR", that IS the easy-fix bias pattern. Self-check before ship: "Are all CRITICAL findings fixed OR scheduled with a specific PR # and date?" If still abstract "future work", ship is incomplete. Confirmed: ADR-002 shipped 3 infrastructure decisions while leaving SEC-N1 prompt injection and CC-2 honor-system both unfixed.
- [Category: adr-discipline][Severity: MEDIUM][Trigger: adr-bundling-multiple-decisions] Bundling multiple architectural decisions into one ADR (e.g., ADR-002 D2.1+D2.2+D2.3) trades short-term commit count for long-term spec drift. ADR-002's bundled spec accumulated 3 deferred ACs (AC-23/24/25) before ship. Future ADRs: 1 architectural decision per ADR. Multiple ADRs OK and preferred. "Mirror ADR-001's 3-decision discipline" is the wrong precedent — the right unit is the smallest decision that ships independently with its own contract.
- [Category: enforcement][Severity: HIGH][Trigger: must-rule-without-validator] Every "MUST" rule in AGENTS.md / engineering_guardrails.md that depends on agent self-attestation (Sentinel `⚡ ACX`, Token Leak Drift Log audit receipts, Skill cache hash, "MUST sanitize Work Log") is a honor-system rule and is functionally theatre. Adversary feasibility is 10/10 for these (a single user message can disable any of them). Discipline: every "MUST" = 1 hook OR validator OR test OR external observer. Rules without enforcement should be DELETED rather than left as honor-system theatre. Adding "MUST" without enforcement is anti-help — it creates false confidence the rule is in effect.
- [Category: bootstrap-flow][Severity: HIGH][Trigger: post-first-adr-architecture-change] `bootstrap §0a` "App Architecture Check" condition `1. No ADR exists: docs/adr/ contains no project-specific ADR.` becomes permanently False once ANY ADR ships. After ADR-001 landed, all subsequent `architecture-change` tasks silently skip the ADR prompt — the very next architecture-change (ADR-002) already triggered this regression but was caught by accident. Fix: replace existence check with frontmatter `applies_to:` glob coverage check. Lesson: rules with date-dependent trigger conditions (e.g., "when X exists" / "when X count == 0") need explicit post-ship validation and decay-aware re-test.

## Ship History

### Ship-architecture-change-adr-002-lock-unification-2026-04-25
- Feature shipped: ADR-002 Guarded Governance Writes — D2.1 lock generalization (policy-driven scope, append mode, per-target receipts, configurable TTL, PID-liveness, lock_group stub for ADR-003); D2.2 CI lint `tools/lint_governed_writes.py` enforces guard usage on protected paths; D2.3 lifecycle frontmatter checker for governance docs (audit/, guides/governance-*, adr/, architecture L1).
- Tests: Pass — 56/56 in 0.4s + 8 Beast Mode adversarial scenarios green; live lint scan 0 FAIL / 67 WARN; live lifecycle scan 2 PASS / 3 WARN (grandfathered) / 0 FAIL.
- Commits: `65c5890` (ADR/spec), `20f2c21` (D2.1), `618ea61` (D2.2), `8eaf284` (D2.3) + ship commit.
- Spec drift: AC-24/AC-25 (ownership matrix doc + AGENTS.md pointer) deferred per Pragmatist roundtable + user direction; Architect content preserved in audit §0.4 + Work Log archive.

- **v1.1.2** (2026-04-17): Polish batch 2 — Python advisory in deploy.sh (1.1), guardrails Loaded-Sections Receipt (3.2), bootstrap Reading Mode Table + §0 decision table (3.3 + 2.1), Confidence Gate harmonized with structured receipts + step-level in /implement (2.3), Read-Once Drift Log audit receipt in AGENTS.md (4.3). Commit `4976a92`. Closes remaining 6 of 12 post-v1.1.0 audit findings. [CHANGELOG](../../CHANGELOG.md#112---2026-04-17)
- **v1.1.1-batch1** (2026-04-17): Polish pass — installer UX (Git-bash detection, clone progress), governance wiring (Confidence Gate receipt in /plan + /ship, No-Bypass scope clarified in AGENTS.md), token discipline (CLAUDE.md 51→27 lines), skill index signposted in routing.md §3. Commit `95ceafb`. Addresses 6 of 12 audit findings; remaining 6 deferred to batch 2 on same branch. [CHANGELOG](../../CHANGELOG.md#111---2026-04-17)
- **v1.1.0** (2026-04-16): Token optimization & governance hardening. SKILL.md heading-scope (#57), phase output compression (#54), expert review quick-wins (#56), deploy fixes (#52, #53, #55). [CHANGELOG](../../CHANGELOG.md#110---2026-04-16)
