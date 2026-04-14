# /spec-intake

Execute the canonical workflow: `.agent/workflows/spec-intake.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Spec Intake Gate, Intent Router)
2. `.agent/rules/engineering_guardrails.md` — §4 Design Before Implementation
3. `.agentcortex/context/current_state.md` — check for existing `_product-backlog.md`

## Execution

Follow every step in `.agent/workflows/spec-intake.md` sequentially.

The user's spec input is: $ARGUMENTS

- If multi-feature input: decompose into Feature Inventory, ask user which to start.
- If single-feature: proceed directly to spec generation.
- Generate `docs/specs/<feature>.md` with quality assessment.
- Flag inferred items for user confirmation.
- After spec is frozen, proceed to bootstrap automatically.
- End response with ⚡ ACX.
