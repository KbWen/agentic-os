@AGENTS.md

# Claude Integration Entry

`AGENTS.md` is auto-injected above via `@import` — governance rules, gates, and state model are already in context. This file only adds Claude-specific dispatch. **Do NOT duplicate rules from AGENTS.md here.**

## Startup (every conversation)

1. Governance rules from `AGENTS.md` are loaded — follow them exactly.
2. Classify task scope from the user's message:
   - `tiny-fix` (< 3 files, no semantic change) → skip to Step 5.
   - `quick-win` (1–2 modules, clear scope) → read SSoT (Step 3), skip Step 4.
   - `feature` / `architecture-change` / `hotfix` / uncertain → continue.
3. Read `.agentcortex/context/current_state.md` (SSoT). *(Skip for tiny-fix.)*
4. Read `.agent/rules/engineering_guardrails.md`. *(Skip for tiny-fix and quick-win.)*
5. If `.agentcortex/context/work/<worklog-key>.md` exists, read to resume. *(Skip for tiny-fix.)*

Token budget rationale: conditional loading saves ~5,000 tokens for tiny-fix, ~3,500 tokens for quick-win. Full mechanics: `AGENTS.md §vNext State Model`.

## Slash Commands

`/command` dispatches via `.claude/commands/<command>.md` → canonical workflow at `.agent/workflows/<command>.md`.

## Skills

Skill metadata: `.agent/skills/*`. Full instructions: `.agents/skills/*/SKILL.md`. Activation and cache policy: `AGENTS.md §Skill Safety & Precedence` and `§Shared Phase Contracts`.

## Validate

Run `.agentcortex/bin/validate.sh` (bash) or `.agentcortex/bin/validate.ps1` (PowerShell).
