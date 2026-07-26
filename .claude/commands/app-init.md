# /app-init

Execute the canonical workflow: `.agent/workflows/app-init.md`

## Required reads before execution

1. `.agent/workflows/app-init.md` — full workflow steps
2. `docs/adr/` — scan for existing project ADRs
3. `.agentcortex/templates/adr-tech-stack.md` — ADR template

## Execution

Follow every step in `.agent/workflows/app-init.md` sequentially.

If $ARGUMENTS contains `--partial`:
- Run §8 (Partial Mode) instead of full init.
- Read existing ADR first, ask only about [TBD] sections.

Otherwise:
- Run full init (§1–§7).
- Ask user about tech stack, generate ADR + skills + spec template.

This is a configuration workflow — do NOT write any project code.
End response with ⚡ ACX.
