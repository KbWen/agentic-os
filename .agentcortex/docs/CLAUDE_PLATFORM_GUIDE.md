# Claude Platform Guide

## Scope

This guide adds a minimal Claude-compatible entry while keeping AgentCortex governance canonical in:

- `AGENTS.md`
- `.agent/rules/*.md`
- `.agent/workflows/*.md`

## Design Principle

- Do not fork core rules for Claude.
- Use `CLAUDE.md` and `.claude/commands/*.md` as prompt adapters only.
- Keep state and evidence in the same paths as other platforms.

## Required Files

- `CLAUDE.md`
- `.claude/commands/bootstrap.md`
- `.claude/commands/plan.md`
- `.claude/commands/implement.md`
- `.claude/commands/review.md`
- `.claude/commands/test.md`
- `.claude/commands/handoff.md`
- `.claude/commands/ship.md`

## Usage

1. Open Claude and paste the startup prompt from `CLAUDE.md`.
2. Use templates in `.claude/commands/` for each phase.
3. Preserve the same gate/evidence expectations as Codex/Antigravity.

## Validation

Run:

```bash
./.agentcortex/bin/validate.sh
```

This checks that Claude adapter files are present and that canonical governance files still exist.
