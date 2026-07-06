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
   - **Cap enforcement (chain-aware archival)**: Before appending, count `- [Category:` entries in `current_state.md` `## Global Lessons`. If count ≥ `document_lifecycle.global_lessons_max_entries` (default: 20 from `.agent/config.yaml`), archive the oldest LOW-severity entry with `append_lesson.py --archive` — do NOT hand-delete a bullet (the hash chain in `check_lesson_chain.py` requires each `[prev:]` to hash its predecessor, so a raw removal breaks verification and FAILs). Run once per slot needed:

     ```bash
     # index N = 1-based position of the oldest LOW entry within §Global Lessons
     python .agentcortex/tools/append_lesson.py --archive --index N
     ```

     This moves the entry to `.agentcortex/context/archive/global-lessons-archive.md`, re-anchors the successor's `[prev:]` to the archived entry's own predecessor, and writes a `lesson_archive` bridge record to the hash-chained `INDEX.jsonl` — so `check_lesson_chain.py` verifies the shortened chain GREEN while a removal WITHOUT a record still FAILs (fail-closed). HIGH-severity entries are pinned (the tool refuses to archive them) and can only be removed by explicit user request.
   - **Append the new lesson** with `append_lesson.py` (it section-locates `## Global Lessons`, computes the `[prev:]` chain hash, and inserts before `## Ship History` — do NOT use `guard_context_write.py --mode append`, whose `O_APPEND` writes land at file end under Ship History):

     ```bash
     python .agentcortex/tools/append_lesson.py \
       --category <tag> --severity <HIGH|MEDIUM|LOW> \
       --trigger <normalized-trigger> --body "<lesson>"
     ```

     **Python-unavailable fallback** (Python genuinely absent): hand-insert the bullet (with a correct `[prev:]` — sha256[:8] of the previous entry's canonical form per `check_lesson_chain.py`) directly inside `## Global Lessons`, and record `"Direct SSoT write: python unavailable"` in the Work Log `## Drift Log`. This is the only non-ship SSoT write exception. See `.agentcortex/docs/guides/guarded-context-writes.md`.
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
