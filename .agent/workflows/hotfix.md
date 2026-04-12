---
name: hotfix
description: Emergency patch workflow. Root cause analysis followed by minimal fix.
tasks:
  - research
  - plan
  - implement
  - review
  - test
---

# Hotfix Workflow

AI drives this end-to-end. The goal is speed with safety — find the root cause, apply the smallest possible fix, and verify it works. Do not expand scope.

## 1. Research & Root Cause Analysis

Start with `/research` to map what is known vs unknown. Then apply the `systematic-debugging` skill (Observe → Hypothesize → Verify → Fix) to converge on root cause.

**Autonomous decision**: If root cause cannot be isolated after one investigation cycle (read code, check logs, form hypothesis, test it), escalate the classification to `feature` — the problem is bigger than a hotfix. Record this decision via `/decide`.

## 2. Plan Minimal Fix

Run `/plan` with these constraints:
- Target: fewest files possible (ideally 1-2)
- Rollback: must be trivially reversible (revert commit, toggle flag)
- Blast radius: document every caller/consumer of changed code

**Autonomous decision**: If the fix requires changing >3 files or modifying a public API, escalate to `feature`. Hotfixes are surgical.

## 3. Implement

Run `/implement`. Stay within the plan. No refactoring, no "while I'm here" improvements.

## 4. Review & Test

Run `/review` then `/test`. Testing must include:
- **Reproduction test**: Prove the original bug is fixed
- **Regression tests**: Prove nothing else broke
- Lite Red Team scan applies (per classification matrix)

## 5. Evidence

Work Log must contain: root cause description, fix rationale, reproduction test output, regression test output.
