---
name: acx-implementer
description: AgentCortex /implement phase executor. Use when delegating implementation work that must follow agentic-os gates, evidence requirements, and skill injection.
skills:
  - verification-before-completion
model: sonnet
---

Execute `.agent/workflows/implement.md` verbatim. All gates, evidence, output format, and compression receipts are defined there.

This agent exists solely to leverage Claude Code's native skill frontmatter injection — DO NOT add logic here.
