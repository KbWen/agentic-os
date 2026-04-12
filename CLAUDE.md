# Claude Integration Entry

**MANDATORY**: Read `AGENTS.md` first — it contains all governance rules, gates, and state model.
This file is the Claude-specific loader only. All rules live in `AGENTS.md` and `.agent/`.

## Startup (every conversation)

1. **Read `AGENTS.md`** — canonical governance. Follow exactly.
2. **Assess scope** → tiny-fix (< 3 files, no semantic change): skip to Step 5. quick-win: read SSoT (Step 3), skip Step 4. feature/architecture-change/hotfix/uncertain: all steps.
3. **Read `.agentcortex/context/current_state.md`** (SSoT). *(Skip for tiny-fix.)*
4. **Read `.agent/rules/engineering_guardrails.md`**. *(Skip for tiny-fix and quick-win.)*
5. Resume from Work Log at `.agentcortex/context/work/<worklog-key>.md` if exists. *(Skip for tiny-fix.)*

Do NOT invent workflows. Do NOT skip gates. Every response MUST end with `⚡ ACX`.

## Slash Commands

`/command` → read `.claude/commands/<command>.md` for dispatch → execute `.agent/workflows/<command>.md`.

## Skills

Defined in `.agents/skills/*/SKILL.md` (full) and `.agent/skills/*` (metadata).
- **Auto**: bootstrap §3.6 rule table recommends ALL matching skills.
- **Manual**: user requests via natural language → activate in current phase.
- **User pinned**: `.agentcortex/context/private/user-preferences.yaml` → bootstrap §3.6a merges after auto-detection.

Skills extend phases, never override governance. See `AGENTS.md` §Skill Safety & Precedence.

## Hard Rules

- **Phase order is mandatory** — NEVER skip, even if user asks.
- **No Evidence = No Completion** — tiny-fix: diff + 1-line. quick-win+: test logs or terminal output.
- **SSoT protection** — Only `/ship` writes to SSoT (via `guard_context_write.py`). Exception: `/retro` Global Lessons.
- **Installation**: Use `installers/deploy_brain.sh` or `deploy_brain.ps1`. NEVER manually copy framework files.

## Validate

Run `.agentcortex/bin/validate.ps1` (Windows) or `.agentcortex/bin/validate.sh` to verify integrity.
