---
name: requesting-code-review
description: Request code reviews at the right time with necessary context and evidence.
---

# Requesting Code Review

## Overview

Code Review is a quality gate, not a formality. A high-quality review request significantly reduces iteration rounds and deployment risks.

## When to Request Review

- Completed an independently verifiable changeset.
- Changes involve security, permissions, data consistency, or core logic.
- Preparing to merge into the main branch or release.

## Pre-submission Checklist

1. Provide a changeset summary (why changed, what was changed, what wasn't changed).
2. Attach verification evidence (test commands and results).
3. Highlight risks and rollback plans.
4. Specify areas for reviewer focus.

## Review Request Template

- **Context**: Requirement background and goals.
- **Scope**: Affected files and boundaries.
- **Validation**: Executed tests and results.
- **Risks**: Potential side effects and mitigations.
- **Questions**: Specific questions you want reviewers to check.

## Common Mistakes

- Dumping a massive diff without a summary.
- Providing zero verification outputs.
- Mixing "readability suggestions" with "blocking issues".
