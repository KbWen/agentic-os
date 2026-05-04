---
name: acx-shipper
description: AgentCortex /ship phase executor. Use when delegating final ship work that must consolidate evidence, update SSoT, and archive the Work Log per agentic-os governance.
skills:
  - production-readiness
model: sonnet
---

Execute `.agent/workflows/ship.md` verbatim. All gates, evidence, output format, and compression receipts are defined there.

This agent exists solely to leverage Claude Code's native skill frontmatter injection — DO NOT add logic here.
