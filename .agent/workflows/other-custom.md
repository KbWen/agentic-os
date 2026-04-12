---
name: other-custom
description: Other custom workflows with strict branching and TDD gates.
tasks:
  - plan
  - implement
  - review
  - test
  - retro
---

# Other Custom Workflow

1. `/plan`: Define goals, constraints, risks, and rollback strategies for unmapped tasks.
2. Branch Governance: Apply `skills/using-git-worktrees` to establish a safe worktree before coding.
3. TDD Gate: Logic changes MUST follow RED (failing test) -> GREEN (minimal fix) -> REFACTOR.
4. `/implement`: Execute incrementally. Maintain small, reversible commits.
5. `/review` + `/test`: Verify strict regression and side-effects. Retain reproducible commands.
6. `/retro`: Evaluate if this custom flow should be abstracted into a new workflow card.

