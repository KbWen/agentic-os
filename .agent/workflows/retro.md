---
description: Workflow for retro
---
# /retro

Conduct a retrospective for the current task.

Output Format:

Apply `shared-contracts.md §Phase Output Compression`. Chat response is the compact KPT block below (≤ 6 lines). Everything under items 4–7 is Work Log content — do NOT emit it in chat unless the user asks.

```
Keep: <1-line — what went well>
Problem: <1-line — what to improve>
Try: <1-line — action for next time>
Lessons: <count appended to Work Log | none>
Spec Seeds: <count | none>
```

Work Log content (NOT chat):

1. Keep / Problem / Try — expanded bullets if the session had multiple themes.
2. Doc Health: Did this task create or reference more than 1 spec file for the same feature?
   - If YES: record the proposed merge in the Work Log and let `/ship` update the Spec Index through guarded SSoT write.
3. Lessons Append: If Problems exist, append to the current Work Log (max 3 bullets) AND convert repeatable lessons to structured Global Lessons format.
   - Structured format: `- [Category: <tag>][Severity: <HIGH|MEDIUM|LOW>][Trigger: <normalized-trigger>] <lesson>`
   - **Cap enforcement**: Before appending, count existing entries in `current_state.md` `## Global Lessons`. If count ≥ `document_lifecycle.global_lessons_max_entries` (default: 20 from `.agent/config.yaml`), archive the oldest LOW-severity entries to `.agentcortex/context/archive/global-lessons-archive.md` until count is under the cap. HIGH-severity entries are pinned and exempt from archival — they can only be removed by explicit user request.
   - If a lesson should persist globally, append it to `current_state.md` via `.agentcortex/tools/guard_context_write.py`. When Python is available, MUST use `guard_context_write.py` — writing directly to `current_state.md` on a Python-capable host is a governance violation. **Python-unavailable fallback** (Python genuinely absent): write directly to `current_state.md` AND record `"Direct SSoT write: python unavailable"` in the Work Log `## Drift Log`. This is the only non-ship SSoT write exception. See `.agentcortex/docs/guides/guarded-context-writes.md`.
4. Spec Seeds: Did the AI make any architectural decisions or discover new feature requirements during development that are NOT currently written in any formal Spec?
   - If YES: Append these to the current Work Log under a `## Spec Seeds` heading, and proactively ask the user: "I recorded [N] undocumented design decisions. Would you like me to formally add them to the Specs now?"
5. Spec Gap Check: Did this task modify code in a module/feature area that has NO Spec coverage at all in the Spec Index?
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
