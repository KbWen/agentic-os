---
description: Workflow for brainstorm
---
# /brainstorm

Generate multiple solution options autonomously. AI explores the design space, weighs trade-offs, and presents a recommendation — the human confirms or redirects.

## Process

1. **Understand the problem space**: Read relevant code, specs, and constraints before generating options. Options grounded in the actual codebase are far more valuable than abstract suggestions.

2. **Generate at least 3 options**: Each option gets:
   - **Description**: What this approach does (1-2 sentences)
   - **Pros**: Why this is a good choice
   - **Risks**: What could go wrong
   - **Cost**: S / M / L (relative implementation effort)
   - **Confidence**: How certain you are this will work (High / Medium / Low)

3. **Include at least 1 conservative option**: Something low-risk that definitely works, even if it's not exciting. This gives the human a safe fallback.

4. **Recommend one option**: State which option you'd pick and why. Don't hedge — commit to a recommendation. The human can override.

## When to Record Decisions

If the brainstorm leads to a chosen direction, record it via `/decide` so the rationale is preserved for future sessions. If the brainstorm is purely exploratory, no decision record is needed.
