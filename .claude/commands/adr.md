# /adr

Execute the canonical workflow: `.agent/workflows/adr.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Intent Router, Gate Engine, Sentinel)
2. `.agentcortex/context/current_state.md` — SSoT

## Execution

Follow every step in `.agent/workflows/adr.md` sequentially.
The user's task description is: $ARGUMENTS

- Create an Architecture Decision Record for the specified decision.
- Do NOT skip the "When to Create an ADR" criteria check.
- End response with ⚡ ACX.
