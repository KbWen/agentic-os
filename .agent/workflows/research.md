---
description: Workflow for research
---
# /research

Conduct autonomous exploratory research. AI investigates the codebase, external docs, and system state to map the problem space. No implementation — only understanding.

## Process

1. **Investigate first, report after**: Read code, check git history, search for patterns, test hypotheses. Spend the effort upfront so the report is grounded in evidence, not speculation.

2. **Structure findings** using this format. Keep each bullet ≤ 1 line in chat. If a finding needs longer justification, write the detail to the Work Log `## Research Findings` section and reference it by section name — do NOT inline a paragraph in chat.
   - **Facts** (verified knowns): Things confirmed by reading code or running commands. Cite `file:line` references.
   - **Unknowns**: Things that need further investigation or require human input to resolve.
   - **Assumptions**: Things you believe to be true but haven't verified. Mark confidence level (High / Medium / Low).
   - **Risks**: Potential problems, ranked High / Medium / Low. Include blast radius estimate.
   - **Official References**: For external libraries, public APIs, or platform capabilities, list the primary source docs / release notes / vendor references you verified.
   - **Next Actions**: Concrete recommendations for what to do next. Each action should be specific enough to execute.

3. **Validate assumptions where possible**: If you can verify an assumption by reading code or running a command, do it instead of listing it as an assumption. The fewer unknowns in the final report, the better.

## Autonomous Decisions

- If research reveals a clear path forward, recommend it directly — don't just list facts and wait.
- If the problem is bigger than expected, suggest rollback + upgrade via `/decide` instead of silent reclassification.
- If research is inconclusive after reasonable effort, say so explicitly and list what would unblock further progress.

## Spec Handoff (optional)

If **Next Actions** point toward building or specifying something new, persist findings so `/spec-intake` can consume them without relying on conversation memory.

**Before writing**: Check if `docs/specs/_research-<topic>.md` (exact filename) already exists. If yes, update it in place — do NOT create a duplicate. If other `_research-*.md` files exist under different names, list them to the user and ask: `"Related research files exist: <list>. Write new file, append to one of these, or cancel?"` — do NOT guess semantic overlap.

1. Write (or update) `docs/specs/_research-<topic>.md`:
   ```markdown
   ---
   status: research
   topic: <topic>
   date: <YYYY-MM-DD>
   ---
   ## Key Facts
   <verified findings that should inform the spec>
   ## Constraints Found
   <hard limits or risks the spec must respect>
   ## Suggested Scope
   <recommended feature boundaries>
   ```
2. Tell the user: `"Research summary saved to docs/specs/_research-<topic>.md. Run /spec-intake to continue — it will load this file automatically and delete it after intake."`

**Lifecycle**: `_research-*.md` files are transient. They exist only between `/research` and `/spec-intake`. If the user does not intend to run `/spec-intake`, do NOT write the file — keep findings in the Work Log only.

This step is optional — only write the file if research concludes with a clear "build this next" direction AND the user will follow up with `/spec-intake`.
