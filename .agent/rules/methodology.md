# Development Methodology (Antigravity & Codex)

## Core Principles (Mandatory)

1. **Spec before code**: Brainstorm/Spec -> Plan -> Implement.
2. **Evidence over claims**: NO completion without verifiable test/check evidence. See `skills/verification-before-completion.md`.
3. **TDD Preferred**: RED -> GREEN -> REFACTOR enforced on logic changes.
4. **Review as Gate**: Critical issues rollback to Implementation. See `skills/requesting-code-review.md`.
5. **Micro-Tasks**: Break work into 2-5 minute verifiable units.

## Platform Adapters

- **Google Antigravity**: Follows a structured phase flow (bootstrap → plan → implement). AI self-enforces phase order regardless of user wording; slash commands remain as optional shortcuts.
- **Codex Web/App**: Supports alias flows (`/write-plan` → plan phase, `/execute-plan` → implement phase).
