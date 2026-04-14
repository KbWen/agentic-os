# /hotfix

Execute the canonical workflow: `.agent/workflows/hotfix.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Intent Router, Gate Engine, Sentinel)
2. `.agent/rules/engineering_guardrails.md` — classification tiers and gate rules
3. `.agent/rules/state_machine.md` — phase transitions
4. `.agentcortex/context/current_state.md` — SSoT

## Execution

Follow every step in `.agent/workflows/hotfix.md` sequentially.
The user's task description is: $ARGUMENTS

- Root cause analysis FIRST, then minimal fix.
- Do NOT skip any phases (research → plan → implement → review → test).
- End response with ⚡ ACX.
