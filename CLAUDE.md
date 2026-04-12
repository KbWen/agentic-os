# Claude Integration Entry

**MANDATORY**: Read and follow `AGENTS.md` before any action. It contains the governance rules, delivery gates, and state model that apply to ALL work in this repository.

This repository uses **Agentic OS** — a governance-first AI agent framework.
All rules live in `AGENTS.md` and `.agent/`. This file is the Claude-specific loader only.

## Startup (REQUIRED — every conversation)

1. **Read `AGENTS.md`** — this is the canonical governance document. Follow it exactly.
2. **Assess task scope** from the user's message:
   - **tiny-fix** (< 3 files, no semantic change, typo/rename/config) → **skip to Step 5**.
   - **quick-win** (1-2 modules, clear scope, no cross-module impact) → read SSoT (Step 3), **skip Step 4** (guardrails). Essential quick-win rules are in `.agent/workflows/bootstrap.md` §7.
   - **feature / architecture-change / hotfix / uncertain** → continue to Step 3.
3. **Read `.agentcortex/context/current_state.md`** — Single Source of Truth (SSoT). *(Skip for tiny-fix.)*
4. **Read `.agent/rules/engineering_guardrails.md`** — constitution for all engineering work. *(Skip for tiny-fix and quick-win.)*
5. If a Work Log exists at `.agentcortex/context/work/<worklog-key>.md`, read it to resume context. *(Skip for tiny-fix.)*

> **Why conditional loading?** AGENTS.md alone provides sentinel check, intent routing, and core directives — sufficient for small tasks. SSoT and full guardrails are loaded only when the task warrants them. This saves ~5,000 tokens for tiny-fix and ~3,500 tokens for quick-win.

Do NOT invent your own workflow. Do NOT skip gates.
Every response MUST end with `⚡ ACX` (sentinel check per AGENTS.md §11).

## Slash Commands

All `/command` behavior is defined in `.agent/workflows/<command>.md`.
When a user invokes a command, read `.claude/commands/<command>.md` for dispatch, then execute the canonical workflow.

## Skills

Skills are defined in `.agents/skills/*/SKILL.md` (full instructions) and `.agent/skills/*` (metadata summaries).

- **Auto**: During `/bootstrap`, the rule table (bootstrap.md §3.6) recommends ALL matching skills. Do NOT limit to 0-2.
- **Manual**: User requests a skill via natural language (e.g., "用 TDD"). Activate in the current phase.
- **Phase entry**: Re-check Work Log `Recommended Skills` and apply cache policy per `.agent/config.yaml §skill_cache_policy`. Only on cache miss re-read `SKILL.md`.

Skills never override governance or gates — they extend the active workflow phase.
Full cache/conflict mechanics: see `AGENTS.md` §Skill Safety & Precedence and §Shared Phase Contracts.

## Hard Rules (Claude-specific reminders)

All governance rules are in `AGENTS.md` and `engineering_guardrails.md`. Key reminders:

- **Phase order is mandatory** — NEVER skip required phases, even if user asks. See `engineering_guardrails.md` §10.
- **No Evidence = No Completion** — `tiny-fix`: diff + 1-line. `quick-win`+: test logs or terminal output.
- **SSoT protection** — Only `/ship` writes to `.agentcortex/context/current_state.md` (via `guard_context_write.py`). Exception: `/retro` may append Global Lessons.
- **Installation**: NEVER manually copy framework files. Use `installers/deploy_brain.sh` or `deploy_brain.ps1`.

## Validate

Run `./.agentcortex/bin/validate.sh` (or `.agentcortex/bin/validate.ps1` on Windows) to verify structural integrity.
