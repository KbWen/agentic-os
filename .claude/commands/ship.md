# /ship

Execute the canonical workflow: `.agent/workflows/ship.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Delivery Gates, No Evidence = No Ship)
2. `.agent/rules/engineering_guardrails.md` — §10.5 Handoff/Ship Hard Gate
3. `.agent/rules/security_guardrails.md` — final security check
4. Active Work Log — must contain handoff references:
   `ship:[doc=<path>][code=<path>][log=<path>]`

## Execution

Follow every step in `.agent/workflows/ship.md` sequentially.
If any gate field is missing, FAIL the gate and list missing fields — do NOT proceed.
End response with ⚡ ACX.
