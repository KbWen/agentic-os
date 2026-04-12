---
description: Workflow for retro
---
# /retro

Conduct a retrospective for the current task.

Output Format:

1. Keep (What went well)
2. Problem (What to improve)
3. Try (Action items for next time)
4. Doc Health: Did this task create or reference more than 1 spec file for the same feature?
   - If YES: record the proposed merge in the Work Log and let `/ship` update the Spec Index through guarded SSoT write.
5. Lessons Append: If Problems exist, append to the current Work Log (max 3 bullets) AND convert repeatable lessons to structured Global Lessons format.
   - Structured format: `- [Category: <tag>][Severity: <HIGH|MEDIUM|LOW>][Trigger: <normalized-trigger>] <lesson>`
- If a lesson should persist globally, append it to `current_state.md` via `.agentcortex/tools/guard_context_write.py`. This is the only non-ship SSoT write exception. Stage 1 keeps missing guard receipts as a diagnostic warning only; see `.agentcortex/docs/guides/guarded-context-writes.md`.
6. Spec Seeds: Did the AI make any architectural decisions or discover new feature requirements during development that are NOT currently written in any formal Spec?
   - If YES: Append these to the current Work Log under a `## Spec Seeds` heading, and proactively ask the user: "I recorded [N] undocumented design decisions. Would you like me to formally add them to the Specs now?"
7. Spec Gap Check: Did this task modify code in a module/feature area that has NO Spec coverage at all in the Spec Index?
   - If YES and the change was `quick-win` or higher: Append to `## Spec Seeds` with tag `[NEW-SPEC-NEEDED]` and notify: "⚠️ Module [name] has no Spec coverage. Recommend creating `docs/specs/<module-name>.md` to prevent future documentation decay."
   - Advisory for `quick-win`; MANDATORY action for `feature` and above.

```markdown
## Lessons
- [Pattern]: [What went wrong + why]
- [Pattern]: ...

## Global Lessons Candidate
- [Category: path-safety][Severity: HIGH][Trigger: bulk-rename] Validate path rewrites immediately after bulk rename operations.

## Spec Seeds
- [Decision/Requirement]: [Context]
```
