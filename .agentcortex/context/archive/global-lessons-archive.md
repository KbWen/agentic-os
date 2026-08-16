# Global Lessons Archive

> Chain-aware archival target for §Global Lessons overflow (config.yaml §document_lifecycle.global_lessons_max_entries).
> Each entry below was removed from current_state.md by `append_lesson.py --archive` and is authorized by a matching `lesson_archive` record in `INDEX.jsonl`.

## Archived 2026-07-19 (prev: 7d331603, body-sha: 73247dab)

- [Category: worklog-format][Severity: LOW][Trigger: worklog-creation][prev: 7d331603] Worklog header fields accept EITHER markdown list form (`- Branch: ...`) or table form (`| Branch | ... |`) — both pass `validate.sh` as of 2026-05-12. YAML frontmatter still fails (no `---` block parser). Template at `.agentcortex/templates/worklog.md` uses table form for readability; list form is also valid. Gate Evidence receipts MUST use `|` pipe separators exactly: `- Gate: <phase> | Verdict: PASS | Classification: <tier> | Timestamp: <ISO>` — and MUST NOT be placed inside markdown code fences (fenced receipts are silently masked and not counted).

## Archived 2026-08-16 (prev: 7d331603, body-sha: 285f5c5e)

- [Category: branch-awareness][Severity: LOW][Trigger: session-start-multi-turn-task][prev: 7d331603] Run `git branch --show-current` at the start of any non-trivial task before deriving the worklog-key. The system-prompt gitStatus snapshot is taken once at session start and can become stale if the branch changed externally.
