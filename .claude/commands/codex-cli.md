# /codex-cli

Execute the canonical workflow: `.agent/workflows/codex-cli.md`

## Execution

Follow every step in `.agent/workflows/codex-cli.md` sequentially.
The user's task description is: $ARGUMENTS

- [OPTIONAL MODULE] Requires globally installed `codex` CLI (`npm install -g @openai/codex`).
- If CLI is unavailable, inform the user and fall back to native execution.
- End response with ⚡ ACX.
