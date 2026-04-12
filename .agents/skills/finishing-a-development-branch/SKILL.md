---
name: finishing-a-development-branch
description: Perform final verification on development branches; choose from 4 merge strategies.
---

# Finishing a Development Branch

## Overview

Feature completion does not mean process completion. Final verification and risk assessment MUST occur before closing a branch to prevent pushing unverified changes to mainline.

## Pre-completion Verification

- Re-sync with mainline to verify no conflicts or behavioral drift.
- Execute minimal required tests + critical regression tests.
- Verify documentation, migration scripts, and configuration changes are ready.

## Four Closure Options

1. **Merge now**: Verification is complete, risks are acceptable; merge directly.
2. **Open PR**: Requires reviewer or cross-team sync; open PR first.
3. **Keep branch**: Has remaining split work; keep branch active for continuation.
4. **Archive / Close**: Requirement canceled or strategy changed; archive and close branch.

## Decision Criteria

- Determined by acceptance completion level and risk level.
- Entering "Merge now" is PROHIBITED if evidence is insufficient.
- For major uncertainties, prioritize "Open PR" for review.

## Common Mistakes

- Rushing to merge before tests finish running.
- Closing a branch without logging the decision.
- Keeping a branch without context, causing a long-tail tech debt.
