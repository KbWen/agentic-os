---
name: help
description: Read-only display of current state, available commands, and recommendations.
tasks:
  - help
---

# /help

Read-only command. DOES NOT change state.

> Canonical state list: `Ref: .agent/rules/state_machine.md`

Output Content:

1. Current State
2. Task Type (If classified)
3. Currently Available Commands (Filtered by State)
4. All Commands & Purposes
5. Suggested Next Steps (DO NOT Auto-Execute)

