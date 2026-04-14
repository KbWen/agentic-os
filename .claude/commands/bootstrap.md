# /bootstrap

Execute the canonical workflow: `.agent/workflows/bootstrap.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Intent Router, Gate Engine, Sentinel)
2. `.agent/rules/engineering_guardrails.md` — classification tiers and gate rules
3. `.agent/rules/state_machine.md` — phase transitions
4. `.agentcortex/context/current_state.md` — SSoT

## Execution

Follow every step in `.agent/workflows/bootstrap.md` sequentially.
The user's task description is: $ARGUMENTS

- Do NOT skip any steps.
- Do NOT proceed past bootstrap in the same turn.
- Output the bootstrap report, then STOP and ask user for next step.
- End response with ⚡ ACX.
