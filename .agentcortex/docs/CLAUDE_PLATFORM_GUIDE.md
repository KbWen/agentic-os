# Claude Platform Guide

## Scope

This guide adds a minimal Claude-compatible entry while keeping Agentic OS governance canonical in:

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

## Phase Shims (Skill Injection)

`.claude/agents/acx-*.md` are thin custom subagent shims that use Claude Code's native `skills:` frontmatter to inject agentic-os skills into spawned subagents at startup. They exist solely to solve the context-propagation gap: subagents do not inherit skills from the parent session.

| Shim | Phase | Skills injected | Model |
|---|---|---|---|
| `acx-implementer.md` | /implement | verification-before-completion | sonnet |
| `acx-reviewer.md` | /review | requesting-code-review, red-team-adversarial | opus |
| `acx-tester.md` | /test | verification-before-completion, test-driven-development | sonnet |
| `acx-handoff.md` | /handoff | finishing-a-development-branch | sonnet |
| `acx-shipper.md` | /ship | production-readiness | sonnet |

**Design rule**: shim bodies are ≤5 lines pointing to the canonical workflow file. All logic lives in `.agent/workflows/`. If phase rules change, update the workflow — not the shim.

**Validation**: `validate.sh` and `validate.ps1` verify that all skill names in shim frontmatter that map to `.agent/skills/<name>/` have a corresponding `SKILL.md` body.

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
