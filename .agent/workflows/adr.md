---
description: Workflow for adr - Architecture Decision Record Workflow
---
# /adr - Architecture Decision Record Workflow

AI autonomously creates standardized architectural decision records. These capture the reasoning behind significant technical choices so future sessions understand not just what was decided, but why.

## When to Create an ADR

Create an ADR when a decision:
- Affects >1 module or crosses architectural boundaries
- Is hard to reverse (data model changes, API contracts, dependency choices)
- Was contentious or had multiple viable alternatives
- Was promoted from a `/decide` entry (decision too significant for inline recording)

For smaller decisions, `/decide` is sufficient — don't create ADRs for every choice.

## Execution Steps

1. **Check existing ADRs**: `ls docs/adr/` to find the next available ID and avoid duplicating existing records.

2. **Allocate ID**: Use sequential numbering (e.g., ADR-005). Keep the kebab-case suffix descriptive.

3. **Generate content**: Create `docs/adr/ADR-[ID]-[name].md` with:
   - **Status**: Proposed | Accepted | Deprecated | Superseded by ADR-[N]
   - **Context**: What problem prompted this decision? What constraints apply?
   - **Decision**: What exactly are we doing? Be specific enough that someone can verify compliance.
   - **Alternatives Considered**: What other options existed and why were they rejected?
   - **Consequences**: Both positive and negative impacts of this decision.

4. **Link from affected code**: Add references in relevant specs, code comments, or the Work Log. An unlinked ADR is an invisible ADR.

5. **Update SSoT ADR Index (mandatory)**: Always insert the new ADR into `current_state.md`. Find the `**ADR Index**` line and append the new entry immediately below it:
   ```
   - docs/adr/ADR-NNN-<slug>.md: <title> · applies_to: <glob-or-module>
   ```
   Write directly to the file (do NOT use `guard_context_write.py` — the tool has no section-targeting capability). This is an approved `/adr`-phase SSoT write exception; document the edit in the Work Log `## Drift Log` as `"ADR Index update: ADR-NNN added"`. **Failure to update leaves disk ADRs unindexed, causing the `SSoT ADR Index completeness` validator check to FAIL on the next run.**
