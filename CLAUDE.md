# Claude Integration Entry

**MANDATORY**: Read and follow `AGENTS.md` before any action. It contains the governance rules, delivery gates, and state model that apply to ALL work in this repository.

This repository uses **AgentCortex** — a governance-first AI agent framework.
All rules live in `AGENTS.md` and `.agent/`. This file is the Claude-specific loader only.

## Startup (REQUIRED — every conversation)

1. **Read `AGENTS.md`** — this is the canonical governance document. Follow it exactly.
2. **Assess task scope** from the user's message:
   - **tiny-fix** (< 3 files, no semantic change, typo/rename/config) → **skip to Step 5**.
   - **quick-win** (1-2 modules, clear scope, no cross-module impact) → read SSoT (Step 3), **skip Step 4** (guardrails). Essential quick-win rules are in `bootstrap.md` §7.
   - **feature / architecture-change / hotfix / uncertain** → continue to Step 3.
3. **Read `.agentcortex/context/current_state.md`** — Single Source of Truth (SSoT). *(Skip for tiny-fix.)*
4. **Read `.agent/rules/engineering_guardrails.md`** — constitution for all engineering work. *(Skip for tiny-fix and quick-win.)*
5. If a Work Log exists at `.agentcortex/context/work/<worklog-key>.md`, read it to resume context. *(Skip for tiny-fix.)*

> **Why conditional loading?** AGENTS.md alone provides sentinel check, intent routing, and core directives — sufficient for small tasks. SSoT and full guardrails are loaded only when the task warrants them. This saves ~5,000 tokens for tiny-fix and ~3,500 tokens for quick-win.

Do NOT invent your own workflow. Do NOT skip gates.
Every response MUST end with `⚡ ACX` (sentinel check per AGENTS.md §11).

## Slash Commands

All `/command` behavior is defined in `.agent/workflows/<command>.md`.
When a command is invoked, read the corresponding `.claude/commands/<command>.md` for dispatch instructions, then execute the canonical workflow from `.agent/workflows/`.

Available commands:

- **Core phases**: `/bootstrap`, `/plan`, `/implement`, `/review`, `/test`, `/ship`
- **Spec & intake**: `/spec-intake`, `/spec`
- **Architecture**: `/app-init`, `/adr`
- **Emergency**: `/hotfix`
- **Research**: `/research`, `/brainstorm`, `/audit`
- **Completion**: `/handoff`, `/decide`, `/retro`
- **Documentation**: `/sync-docs`, `/govern-docs`
- **Testing helpers**: `/test-classify`, `/test-skeleton`
- **Workflow**: `/worktree-first`
- **Utility**: `/help`
- **Optional**: `/ask-openrouter`, `/codex-cli`, `/claude-cli`

## Skills

Skills are defined in `.agents/skills/*/SKILL.md` (detailed instructions) and `.agent/skills/*` (metadata summaries with trigger conditions).

**How skills activate (dual path):**
1. **Auto**: During `/bootstrap`, the deterministic rule table (bootstrap.md §3.6) matches ALL applicable skills based on task classification and scope. Recommend every skill whose condition is met — do NOT limit to 0-2.
2. **Manual**: User explicitly requests a skill via natural language (e.g., "用 TDD", "先寫測試"). Activate immediately in the current phase.

**At each phase entry** (`/plan`, `/implement`, `/review`, `/test`, `/handoff`, `/ship`): re-check Work Log `Recommended Skills`, prefer `## Skill Notes` for the current phase when a valid note already exists, and apply `.agent/config.yaml §skill_cache_policy` to decide cache hit vs. miss. Only on a cache miss re-read the corresponding `SKILL.md`. State: "Applying [skill-name] strategy." Skill conflict decisions come from `/bootstrap`; later phases should reuse the Work Log's `## Conflict Resolution` instead of re-reading the conflict matrix unless the skill set changes.

Skills never override governance or gates — they extend the active workflow phase.

## Hard Rules

- **Phase order is mandatory** (per classification, see `engineering_guardrails.md` §10):
  - `feature` / `architecture-change`: Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship.
  - `hotfix`: Bootstrap → Research → Plan → Implement → Review → Test → Ship.
  - `quick-win`: Bootstrap → Plan → Implement → Evidence → Ship. (No Spec, no Handoff.)
  - `tiny-fix`: Classify → Execute → Evidence → Done. (Minimal overhead.)
  - NEVER skip required phases for your classification, even if the user asks.
- **No Evidence = No Completion**: ALL classifications require evidence. `tiny-fix`: diff + 1-line verification. `quick-win`+: verifiable test logs or terminal output.
- **SSoT protection**: `/ship` is the normal writer for `.agentcortex/context/current_state.md`, and all SSoT writes must go through `.agentcortex/tools/guard_context_write.py`. The only non-ship exception is `/retro` appending structured Global Lessons.
- **Classification freeze**: task classification set during bootstrap cannot be silently downgraded. If scope grows, use rollback to `CLASSIFIED` and re-enter the required workflow at the higher tier.
- **Installation**: NEVER manually copy framework files. Use `deploy_brain.sh` or `deploy_brain.ps1`. NEVER overwrite the target repo's existing README.md or .gitignore outside the managed block.

## Validate

Run `./.agentcortex/bin/validate.sh` (or `.agentcortex/bin/validate.ps1` on Windows) to verify structural integrity.
