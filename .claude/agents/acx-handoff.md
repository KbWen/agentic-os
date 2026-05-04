---
name: acx-handoff
description: AgentCortex /handoff phase executor. Use when delegating handoff work that must produce a resumable state summary with full Work Log archival per agentic-os governance.
skills:
  - finishing-a-development-branch
model: sonnet
---

Execute `.agent/workflows/handoff.md` verbatim. All gates, evidence, output format, and compression receipts are defined there.

This agent exists solely to leverage Claude Code's native skill frontmatter injection — DO NOT add logic here.
