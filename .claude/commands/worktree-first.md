# /worktree-first

Execute the canonical workflow: `.agent/workflows/worktree-first.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Intent Router, Gate Engine, Sentinel)
2. `.agent/rules/engineering_guardrails.md` — classification tiers and gate rules
3. `.agentcortex/context/current_state.md` — SSoT

## Execution

Follow every step in `.agent/workflows/worktree-first.md` sequentially.
The user's task description is: $ARGUMENTS

- Set up a git worktree-first branching workflow.
- Follow workspace governance rules strictly.
- End response with ⚡ ACX.
