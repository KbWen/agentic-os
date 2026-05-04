---
name: acx-tester
description: AgentCortex /test phase executor. Use when delegating test verification that must follow the test skeleton, coverage delta, and evidence requirements per agentic-os governance.
skills:
  - verification-before-completion
  - test-driven-development
model: sonnet
---

Execute `.agent/workflows/test.md` verbatim. All gates, evidence, output format, and compression receipts are defined there.

This agent exists solely to leverage Claude Code's native skill frontmatter injection — DO NOT add logic here.
