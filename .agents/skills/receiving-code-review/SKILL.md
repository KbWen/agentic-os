---
name: receiving-code-review
description: Effectively process reviewer feedback; categorize blocking vs. advisory items.
---

# Receiving Code Review

## Overview

Review feedback requires structured handling to quickly converge into a mergeable state.

## Feedback Categorization

- **Blocking**: Mandatory; affects correctness, security, or stability.
- **Non-blocking**: Advisory; readability or optimizations to handle later.
- **Question**: Requires added context or design explanation.

## Response Workflow

1. Reply iteratively to avoid omissions.
2. Re-run related tests after changes.
3. Report "Fixes + Verification Evidence + Reason for non-adoption (if any)".
