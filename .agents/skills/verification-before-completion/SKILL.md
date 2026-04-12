---
name: verification-before-completion
description: Enforce "no evidence = no completion"; run Gate Function verification before declaring done.
---

# Verification Before Completion

## Overview

Any "completed" statement MUST be supported by evidence. This skill provides a pre-completion Gate Function, ensuring results are reproducible, traceable, and deliverable.

## Ironclad Rules

- **No evidence = no completion claim.**
- Evidence MUST be reproducible by others; verbal descriptions are NOT accepted.
- If tests/checks fail, the status MUST revert to in-progress.

## When to Use

- Tasks are preparing to enter `/ship`.
- Before submitting PRs or handing off work.
- After completing high-risk changes (data, permissions, core flows).

## Gate Function

1. **Scope Gate**: Confirm changes only cover the agreed scope.
2. **Quality Gate**: Execute required tests and static checks.
3. **Evidence Gate**: Compile reproducible evidence (commands, outputs, versions).
4. **Risk Gate**: Confirm rollback strategies and known risks.
5. **Communication Gate**: Output a completion summary (changes, validation, constraints).

## Minimum Evidence Checklist

- At least one set of tests/checks directly related to this change.
- Specific execution commands and results (Success/Failure/Warning).
- If there are unfinished items, explicitly mark them with follow-up suggestions.

## Common Mistakes

- Claiming "it should work" without any output evidence.
- Testing only the happy path, missing regressions or edge cases.
- Treating old test results as evidence for new changes.
