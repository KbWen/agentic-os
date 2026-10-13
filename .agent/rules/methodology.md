# Development Methodology

## Core Principles (Mandatory)

1. **Spec before code**: Brainstorm/Spec -> Plan -> Implement.
2. **Evidence over claims**: NO completion without verifiable test/check evidence. See `.agents/skills/verification-before-completion/SKILL.md`.
3. **Test-first**: RED -> GREEN -> REFACTOR for feature/architecture-change logic; bug fixes start from a reproducing test.
4. **Review as Gate**: Critical issues rollback to Implementation. See `.agent/workflows/review.md` (5-Axis Quality Standard inlined there).
5. **Micro-Tasks**: Break work into 2-5 minute verifiable units.

## Platform Adapters

- **Google Antigravity**: Follows a structured phase flow (bootstrap → plan → implement). AI self-enforces phase order regardless of user wording; slash commands remain as optional shortcuts.
- **Codex Web/App and Claude Code**: Support alias flows (`/write-plan` → plan phase, `/execute-plan` → implement phase).
