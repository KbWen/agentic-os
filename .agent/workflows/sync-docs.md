---
description: Workflow for sync-docs - Documentation Sync Workflow
---
# /sync-docs - Documentation Sync Workflow

Execute before task completion to ensure docs match code.

## Execution Steps

1. **Scan Changes**: Run `git diff --name-only` to identify impacted source files.
2. **Locate Docs**: Search `.agentcortex/` for relevant markdown files.
3. **Proactive Update**:
    - Logic changes -> Update `docs/specs/`.
    - Arch changes -> Create/Update `docs/adr/`.
    - Usage changes -> Update `.agentcortex/docs/guides/` or `README.md`.
4. **Verification**: Guarantee all paths and links in docs remain valid.


