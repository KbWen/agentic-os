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
- **Last Updated**: 2026-04-17
- **Last Verified**: 2026-04-17
- **Update Sequence**: 4
- **ADR Index**: (none yet)
- **Active Backlog**: (none yet)
- **Spec Index** (framework template specs at `.agentcortex/specs/`; project specs go to `docs/specs/`):
  - (none yet — use `/spec-intake` or `/spec` to create new specs)
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

## Ship History

- **v1.1.2** (2026-04-17): Polish batch 2 — Python advisory in deploy.sh (1.1), guardrails Loaded-Sections Receipt (3.2), bootstrap Reading Mode Table + §0 decision table (3.3 + 2.1), Confidence Gate harmonized with structured receipts + step-level in /implement (2.3), Read-Once Drift Log audit receipt in AGENTS.md (4.3). Commit `4976a92`. Closes remaining 6 of 12 post-v1.1.0 audit findings. [CHANGELOG](../../CHANGELOG.md#112---2026-04-17)
- **v1.1.1-batch1** (2026-04-17): Polish pass — installer UX (Git-bash detection, clone progress), governance wiring (Confidence Gate receipt in /plan + /ship, No-Bypass scope clarified in AGENTS.md), token discipline (CLAUDE.md 51→27 lines), skill index signposted in routing.md §3. Commit `95ceafb`. Addresses 6 of 12 audit findings; remaining 6 deferred to batch 2 on same branch. [CHANGELOG](../../CHANGELOG.md#111---2026-04-17)
- **v1.1.0** (2026-04-16): Token optimization & governance hardening. SKILL.md heading-scope (#57), phase output compression (#54), expert review quick-wins (#56), deploy fixes (#52, #53, #55). [CHANGELOG](../../CHANGELOG.md#110---2026-04-16)
