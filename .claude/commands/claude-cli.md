# /claude-cli

Execute the canonical workflow: `.agent/workflows/claude-cli.md`

## Execution

Follow every step in `.agent/workflows/claude-cli.md` sequentially.
The user's task description is: $ARGUMENTS

- [OPTIONAL MODULE] Requires Claude Code CLI to be installed and available as `claude`.
- If CLI is unavailable or not authenticated, inform the user and fall back to native execution.
- End response with ⚡ ACX.
