# Token Governance Guide

## Objective

To continuously reduce average task token costs without sacrificing correctness or traceability.

## 0. Spirit of Architecture (No Token-Saving at the Expense of Correctness)

Lowering token usage must maintain the "Engineering Constitution":

- **Correctness first**: No evidence, no completion. Do not claim completion just to save tokens.
- **Document-first**: Architecture or core logic changes must have corresponding Spec/ADR before summarization.
- **Traceability floor**: Any summary must retain a traceable path (at least doc + code + work log).

> Quick check: If a "token-saving technique" makes AC alignment, risk rollback, or test evidence disappear, the technique is disallowed.

## 1. Task-Level Token Budget (Preliminary)

- `tiny-fix`: Recommended 1–2 turns to complete.
- `behavior-change`: Recommended 2–4 turns to complete.
- `feature` / `architecture-change`: Recommended 3–6 turns to complete.

> Turn counts are upper-limit reminders, not hard failure conditions.

## 2. Budget Overflow Handling (Cost Fallback)

If a small task (docs-update / small-fix) exceeds the budget:

1. Force use of `Mode: Fast Lane` for the next turn.
2. Switch response format to a fixed template (Summary + Evidence + Next), prohibiting lengthy background restatement.
3. Retain only essential references and AC alignment; do not repeat large sections of specification text.

## 3. Anti-Degradation Rules

- If a "small job results in excessive tokens," the root cause must be recorded in the `/retro` or work log.
- Use the verified short template for future tasks of the same type.

## 4. Relation to Process Documents

- `/plan` should include `Mode: Normal` or `Mode: Fast Lane`.
- `/handoff` should keep each block concise, avoiding full diffs.
- `/ship` should provide only necessary evidence, avoiding repetitive narratives.

## 5. Full Checklist (Post-Release Audit)

When a new version claims to "reduce token consumption for document reading," at least check:

1. **Precision Reading**: Whether SSoT guidance is followed, avoiding blind scans of `docs/`.
2. **Process Integrity**: Whether state machines and quality gates are still followed, avoiding skipping steps for summarization.
3. **Evidence Density**: Whether validate/test/command evidence is still provided.
4. **Rollback Mechanism**: Whether files can still be located and rollbacked quickly after compressed output.
5. **Cross-Platform Consistency**: Whether Web/App/Antigravity specifications remain consistent.

If any check fails, it is considered "breaking governance for efficiency" and must be corrected before success is declared.

## 6. Context Caching (Provider-Level Optimization)

Modern LLM providers support **context caching** — reusing attention computation for stable parts of the prompt (system instructions, AGENTS.md, guardrails) across calls. This can reduce token costs by 40–70% for repeated reads.

### AI Behavior

- AI SHOULD structure its context reads to maximize cache hits:
  - Read stable documents (guardrails, state machine, AGENTS.md) **first** in every session — these rarely change and benefit most from caching.
  - Read volatile documents (Work Logs, git diffs, user code) **after** stable ones.
- AI SHOULD NOT re-paste large stable documents mid-conversation. They are already in context from the initial read.

### Human Action

- **Nothing required.** Context caching is provider-side (Gemini, Claude, etc.) and activated automatically when the prompt structure is consistent.
- When Gemini's explicit cache API (`cachedContent`) or Claude's prompt caching becomes available in your platform, consider pinning `engineering_guardrails.md` + `AGENTS.md` as cached content.

### Cost Impact Estimate

| Scenario | Without Caching | With Caching |
| --- | --- | --- |
| 10-turn session, reading guardrails each turn | 10× full read cost | 1× full + 9× cache hit |
| `/bootstrap` re-read on resume | full cost | cache hit if same session window |

> This optimization requires ZERO framework changes. It only requires awareness of read ordering.

## 7. Portable Work Log Compaction Policy (Minimal Kit)

Use these defaults to keep handoff/state docs short across repositories:

- `WORKLOG_MAX_LINES=300`
- `WORKLOG_MAX_KB=12`
- `WORKLOG_KEEP_RECENT_ENTRIES=5`
- `WORKLOG_ARCHIVE_DIR=.agentcortex/context/archive/work`

Compaction procedure:

1. Keep only: `## Session Info`, latest `## Resume`, latest `## Risks`, latest 5 delta entries.
2. Move older entries to `.agentcortex/context/archive/work/<worklog-key>-<YYYYMMDD>.md`.
3. Add a pointer line in the active log: `Compacted: <date>, archive: <path>`.
4. Never compact away the evidence required by `/ship` gate.
