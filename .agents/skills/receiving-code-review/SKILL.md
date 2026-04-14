---
name: receiving-code-review
description: Effectively process reviewer feedback; categorize blocking vs. advisory items; apply 5-axis quality standard for self-review.
---

# Receiving Code Review

## Overview

Review feedback requires structured handling to quickly converge into a mergeable state.
When self-reviewing (AI reviewing its own output), apply the 5-axis quality standard below.

## 5-Axis Quality Standard

When conducting or receiving review, evaluate changes across ALL five axes:

| Axis | Key Questions | Severity if Missed |
|---|---|---|
| **Correctness** | Does it do what it claims? Edge cases handled? Error paths covered? | Critical |
| **Security** | Input validation? Auth checks? Injection vectors? Secrets exposure? | Critical |
| **Performance** | N+1 queries? Unbounded loops? Missing pagination? Memory leaks? | High |
| **Readability** | Clear naming? Reasonable function length? Comments where non-obvious? | Medium |
| **Architecture** | Right abstraction level? Consistent with existing patterns? Coupling minimized? | Medium |

**Change sizing guideline**: Review effectiveness drops sharply above ~100 changed lines.
If a diff exceeds 100 lines, consider splitting into smaller reviewable units.

## Feedback Categorization

- **Blocking**: Mandatory; affects correctness, security, or stability.
- **Non-blocking**: Advisory; readability or optimizations to handle later.
- **Question**: Requires added context or design explanation.

## Response Workflow

1. Reply iteratively to avoid omissions.
2. Re-run related tests after changes.
3. Report "Fixes + Verification Evidence + Reason for non-adoption (if any)".

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It works, that's good enough" | Working code that's unreadable, insecure, or architecturally wrong creates debt that compounds. |
| "The tests pass, so it's good" | Tests are necessary but not sufficient. They don't catch architecture problems, security issues, or readability. |
| "AI-generated code is probably fine" | AI code needs more scrutiny, not less. It's confident and plausible, even when wrong. |
| "We'll clean it up later" | Later never comes. The review is the quality gate — use it. |

## References

- Quality standard enrichment: [addyosmani/agent-skills — code-review-and-quality](https://github.com/addyosmani/agent-skills) (MIT)
