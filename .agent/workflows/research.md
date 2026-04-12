---
description: Workflow for research
---
# /research

Conduct autonomous exploratory research. AI investigates the codebase, external docs, and system state to map the problem space. No implementation — only understanding.

## Process

1. **Investigate first, report after**: Read code, check git history, search for patterns, test hypotheses. Spend the effort upfront so the report is grounded in evidence, not speculation.

2. **Structure findings** using this format:
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
