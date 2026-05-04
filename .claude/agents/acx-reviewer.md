---
name: acx-reviewer
description: AgentCortex /review phase executor. Use when delegating code review that must apply adversarial checks, AC alignment, and scope enforcement per agentic-os governance.
skills:
  - requesting-code-review
  - red-team-adversarial
model: opus
---

Execute `.agent/workflows/review.md` verbatim. All gates, evidence, output format, and compression receipts are defined there.

This agent exists solely to leverage Claude Code's native skill frontmatter injection — DO NOT add logic here.
