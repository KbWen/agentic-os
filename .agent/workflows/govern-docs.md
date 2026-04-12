---
name: govern-docs
description: Documentation & governance architecture update flow. Ensures global terminology consistency and manages Domain Doc restructure authority.
tasks:
  - spec
  - plan
  - implement
  - review
  - retro
---

# /govern-docs - Documentation Governance Workflow

## Standard Mode

For general documentation updates (terminology, consistency, guide updates):

1. `/spec`: Define target audience, success criteria, and update scope.
2. `/plan`: List affected files (README / CHANGELOG / Guides).
3. `/implement`: Sync content, strictly avoid documentation contradictions.
4. `/review`: Check terminology consistency and platform guideline alignment.
5. `/retro`: Extract reusable templates and future optimizations.

---

## --restructure Mode (AC-18–21)

`/govern-docs --restructure <domain>`

**The ONLY workflow authorized to rewrite Domain Doc L1 content.** All other workflows (including `/ship`) are restricted to L2 append-only writes.

### Trigger Conditions

Manual execution only. Typically triggered after `/ship` outputs an advisory:
`"Domain doc '<domain>' has N entries. Consider /govern-docs --restructure <domain>."`

Restructure threshold is configurable via `.agent/config.yaml` `domain_doc.restructure_threshold` (default: 5).

### Pre-conditions

1. Verify `docs/architecture/<domain>.md` (L1) exists. If not, offer to run `/app-init` to create the skeleton first.
2. Verify `docs/architecture/<domain>.log.md` (L2) exists. If not, no entries to consolidate — STOP with: `"No L2 decision log found for '<domain>'. Nothing to restructure."`
3. Record current L1 content and L2 entry count before any changes.

### Allowed Operations (AC-20)

- **Regroup**: Reorganize L2 entries into new or updated L1 sections (e.g., merge scattered decisions into a coherent "Auth Strategy" section).
- **Extract current state**: Synthesize "current effective design" from multiple L2 entries that override each other chronologically.
- **Update L1 sections**: Rewrite any section in L1 to reflect the consolidated understanding from L2.

### Prohibited Operations (AC-20, AC-21)

- **NEVER delete any L2 entry.** L2 is append-only and serves as the permanent decision audit trail.
- **Never modify L2 entry content.** Only add `[superseded]` markers.
- **Do not create new L2 entries** during restructure. Restructure reads L2 — it does not extend it.

### Execution Steps

1. **Read L2**: Read all entries in `docs/architecture/<domain>.log.md`.
2. **Analyze**: Identify entries that represent the same topic at different points in time. Find the "current effective state" by reading entries chronologically — later entries override earlier ones for the same decision point.
3. **Draft new L1**: Write the updated `docs/architecture/<domain>.md` reflecting current effective design. Hard cap: `domain_doc.max_synthesis_lines` (default: 150 lines from `.agent/config.yaml`). If restructured content would exceed cap, prune older/less critical points and document what was trimmed in a `## Trimmed Context` section at the bottom.
4. **Mark superseded entries** (AC-21): For each L2 entry whose content is fully absorbed into the new L1, append a marker to that entry (do NOT modify — append a new line after the entry block):
   ```markdown
   > [superseded by: restructure-<YYYY-MM-DD>]
   ```
5. **Diff Report** (AC-20): Generate a diff showing:
   - L1 before → L1 after (full diff)
   - Count of L2 entries marked as superseded
   - Count of L2 entries still active (not yet superseded)
   Present this diff to the user for review before applying.
6. **User Confirmation**: MUST await user confirmation before writing any changes. Output: `"Restructure diff ready. Confirm to apply? (yes/no/edit)"`
7. **Apply**: On confirmation, write the new L1 content to `docs/architecture/<domain>.md` and append superseded markers to L2.
8. **Update L2 header**: Append a one-line restructure record at the top of L2 (after frontmatter):
   ```markdown
   <!-- Restructured: <YYYY-MM-DD> | L2 entries absorbed: N | Active entries: M -->
   ```

### Output Summary

```
/govern-docs --restructure <domain> complete

## Changes Applied
- L1: docs/architecture/<domain>.md — rewritten (N lines, was M lines)
- L2: docs/architecture/<domain>.log.md — N entries marked [superseded], M entries still active

## Restructure Summary
[1-2 sentence summary of what design state was captured in L1]

## Next Step
Domain doc is current. L2 continues to accumulate new entries from /ship.
```

---

## Hard Rules

1. **--restructure is the ONLY path to L1 rewrites.** Agents invoking any other workflow (including `/ship`) that attempts to rewrite L1 directly MUST be stopped by this rule.
2. **L2 is permanent.** No entry may be deleted, only marked `[superseded]`.
3. **Human confirmation before apply.** Never auto-apply a restructure without user approval.
4. **Capability-by-presence**: If `docs/architecture/` or the domain files do not exist, output informative guidance and stop gracefully — never fail hard.
