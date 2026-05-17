---
name: worktree-first
description: Git worktree-first branching and workspace governance.
tasks:
  - using-git-worktrees
  - plan
  - implement
  - review
  - ship
---

# Worktree-first Workflow

1. Apply `skills/using-git-worktrees` to establish an isolated workspace FIRST.
2. `/plan`: Define scope exclusively within the new worktree.
3. `/implement`: Complete all modifications and commits inside the worktree.
4. `/review` + `/test`: Confirm zero side-effects.
5. Finalize via `/handoff` + `/ship` — choose closure option explicitly: Merge now / Open PR / Keep branch / Archive-Close (decision tree inlined in `ship.md`).

## Work Log Setup

Derive `<worklog-key>` from the worktree branch using filesystem-safe normalization (replace `/` with `-`, strip special chars). Create the Work Log at `.agentcortex/context/work/<worklog-key>.md` during `/bootstrap` — the branch name in the Work Log header MUST match the worktree branch, not `main`.

## SSoT Reads

Read `.agentcortex/context/current_state.md` at bootstrap to orient context (skip for `tiny-fix`). Do NOT write to SSoT from inside the worktree — only `/ship` (after merge) updates SSoT. The worktree Work Log is the local record; SSoT is updated once the branch lands in `main`.
