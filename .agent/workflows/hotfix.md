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

## 6. Optional: Cloud PR Auto-Fix (Claude Code CLI only)

When the hotfix is pushed to a PR and the user is running inside Claude Code CLI, the user MAY invoke `/autofix-pr` to enable Anthropic's cloud auto-fix loop on the PR. Claude Code on the web watches CI + review comments and pushes fixes until green.

- Trigger: user types `/autofix-pr` from the PR's branch.
- This is **opt-in and Claude-CLI-only** — agent MUST NOT auto-trigger; not part of the cross-platform `/hotfix` contract.
- Receipts: paste the `/autofix-pr` confirmation into Work Log `## External References` as `External Fix Loop: autofix-pr enabled — <PR#>`.
- The framework `/test` and `/review` gates STILL apply locally; cloud auto-fix is supplementary, not a substitute for the standard hotfix gate sequence.

Reference: <https://code.claude.com/docs/en/claude-code-on-the-web#auto-fix-pull-requests>.
