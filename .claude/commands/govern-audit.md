# /govern-audit

Execute the canonical workflow: `.agent/workflows/govern-audit.md`

## Required reads before execution

1. `AGENTS.md` — global directives (Intent Router, Gate Engine, Sentinel)

## Execution

Follow every step in `.agent/workflows/govern-audit.md` sequentially.
The user's task description is: $ARGUMENTS

- This is a read-only workflow. Do NOT modify any governance source code.
- Audit the governance system itself; verify every finding before reporting.
- Every surviving finding gets a disposition (do-now / backlog / close-with-reason).
- End response with ⚡ ACX.
