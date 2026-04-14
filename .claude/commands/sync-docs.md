# /sync-docs

Execute the canonical workflow: `.agent/workflows/sync-docs.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Intent Router, Gate Engine, Sentinel)
2. `.agentcortex/context/current_state.md` — SSoT

## Execution

Follow every step in `.agent/workflows/sync-docs.md` sequentially.
The user's task description is: $ARGUMENTS

- Ensure documentation matches the current code state.
- Scan changes, identify doc gaps, update affected docs.
- End response with ⚡ ACX.
