---
name: using-git-worktrees
description: Use Git worktrees to create parallel working directories safely; avoid branch-switch contamination.
---

# Using Git Worktrees

## Overview

Git worktree allows mounting multiple working directories onto the same repository simultaneously, each mapped to a different branch. This is ideal for parallel development and hotfixes.

## Workspace Selection Principles

- Manage them centrally outside the repo or in a dedicated folder (e.g., `../wt-<task>`).
- Name them with task semantics (feature/hotfix + short name).
- Avoid confusing or overwriting existing workspaces.

## Safety Checks

1. Ensure the primary workspace is clean (prevent taking uncommitted changes).
2. List existing worktrees first: `git worktree list`.
3. Check that the target directory does not exist or is empty.
4. Confirm branch naming and tracking strategies.

## Setup Workflow

1. Create a branch and add a worktree:
   - `git worktree add ../wt-<task> -b <branch-name>`
2. Switch to the new directory and run a baseline test.
3. Develop, commit, and verify independently in that directory.
4. Remove the worktree when finished (if no longer needed):
   - `git worktree remove ../wt-<task>`

## Common Mistakes

- Committing in the wrong worktree.
- Deleting a worktree without confirming if the branch should be preserved.
- Chaotic directory naming, leading to unclear task mapping.
