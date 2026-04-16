# Agentic OS v1.1 — Model Selection Guide

> For human reference only — this file is not loaded into AI context.

## Principle: Match Model to Task Classification

Agentic OS classifies every task. Use that classification to pick your model:

| Classification | Recommended Tier | Why |
|---|---|---|
| **tiny-fix** | Fast | Typo, config tweak — no reasoning needed |
| **quick-win** | Fast (try first) → Pro (if stuck) | Scoped change; fast models handle most |
| **hotfix** | Pro | Debugging requires deep reasoning + context |
| **feature** | Pro for /plan, Fast for /implement boilerplate, Pro for /review | Mixed — plan and review need judgment |
| **architecture-change** | Pro throughout | Cross-module reasoning, security implications |

## Fast Models (Default Choice)

*Claude Haiku 4.5, Gemini 3.1 Flash, GPT-5.4-mini*

Best for tasks where the **what** is clear and the AI just needs to execute:

- Writing tests from a spec or skeleton
- Formatting, linting fixes, CSS adjustments
- Localization and i18n entries
- Migrating code between files (clear source → target)
- Generating boilerplate from an approved `/plan`
- Doc cleanup and summarization

## Pro / Advanced Models (When Judgment Matters)

*Claude Opus 4.6 / Sonnet 4.6, Gemini 3.1 Pro, GPT-5.4*

Switch when the task requires **reasoning about tradeoffs**:

- `/plan` phase for feature or architecture-change — designing the approach
- `/review` with security-sensitive skills (auth-security, red-team)
- Debugging race conditions, memory leaks, or flaky tests
- Schema design with migration safety concerns
- Core refactoring touching 3+ coupled modules
- Any task where the fast model produced incorrect logic on first attempt

## Practical Tips

1. **Let Fast fail first.** Start with Fast; if the output has logic errors (not just formatting), switch to Pro with the same context. One wasted Fast attempt costs less than one Pro attempt.
2. **Use classifications as a signal.** If `/bootstrap` classified the task as `feature` or higher, lean toward Pro for planning and review phases.
3. **Phase-split large tasks.** Let Fast handle `/implement` boilerplate after Pro produced the `/plan`. Different phases can use different models.
4. **Trim context for Fast models.** Provide specific file paths, not `ls -R`. Fast models degrade more on noisy context than Pro models do.
