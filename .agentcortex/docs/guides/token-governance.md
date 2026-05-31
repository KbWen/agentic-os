# Token Governance Guide

## Objective

**Primary goals** (in priority order):
1. **Context quality** — precise, focused context loading; avoid polluting the context window with unnecessary content.
2. **Output token discipline** — concise AI responses; output tokens are never cached and compound every turn.
3. **Input token reduction** *(recommended, not mandatory)* — minimize redundant file reads and prompt bloat. In practice, prompt caching already handles 97-98% of input token cost at 0.1× price; further input reduction has diminishing returns but remains a good habit.

**Constraint**: None of the above may sacrifice correctness, evidence, or traceability.

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
> **Soft heuristic only — not the handoff signal.** A task is NOT "due for handoff" because it hit a turn number. The canonical handoff trigger is **context-occupancy + phase boundary** (see `AGENTS.md §Context Pruning` and §6.1 below); turn-count is a coarse fallback used only when occupancy can't be estimated.

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

Modern LLM providers support **context caching** — reusing attention computation for stable parts of the prompt (system instructions, AGENTS.md, guardrails) across calls. In practice this project achieves a **97-98% cache hit rate** (measured 2026-05-13 ~ 05-26), meaning ~97% of input tokens are served at 0.1× price.

### AI Behavior

- AI SHOULD structure its context reads to maximize cache hits:
  - Read stable documents (guardrails, state machine, AGENTS.md) **first** in every session — these rarely change and benefit most from caching.
  - Read volatile documents (Work Logs, git diffs, user code) **after** stable ones.
- AI SHOULD NOT re-paste large stable documents mid-conversation. They are already in context from the initial read.

### Human Action

- **Nothing required.** Context caching is provider-side (Gemini, Claude, etc.) and activated automatically when the prompt structure is consistent.
- Prompt caching is **already active by default on all major platforms today** (Claude, OpenAI/Codex, Google/Gemini) — see §6.1. Where an explicit cache API exists (Gemini `cachedContent`; Claude 1-hour-TTL opt-in `ENABLE_PROMPT_CACHING_1H`), you MAY pin `engineering_guardrails.md` + `AGENTS.md` for guaranteed retention.

### Cost Impact Estimate

| Scenario | Without Caching | With Caching |
| --- | --- | --- |
| 10-turn session, reading guardrails each turn | 10× full read cost | 1× full + 9× cache hit |
| `/bootstrap` re-read on resume | full cost | cache hit if same session window |

> This optimization requires ZERO framework changes. It only requires awareness of read ordering.

### 6.1 Cross-Platform Handoff Timing & Caching (canonical detail for `AGENTS.md §Context Pruning`)

The handoff trigger is **context-occupancy + phase boundary**, not turn-count — because the underlying facts are now uniform across platforms: each auto-caches the prompt prefix at ~0.1× read AND auto-compacts when the window fills. Two consequences:

1. A **premature handoff throws away a warm cache** and pays full price to re-prime a new session — so handing off "early" just to keep a session short is now a net cost, not a saving.
2. The crash/overflow risk that turn-based auto-checkpointing once guarded against is largely handled by the platform's own compaction.

So: hand off for **quality**, at a natural **phase boundary**, when occupancy is high — not on a turn counter. Turn-count survives only as a coarse fallback when occupancy can't be estimated.

| Platform | Prompt caching (2026) | Auto-compaction | Context window | Handoff nuance |
|---|---|---|---|---|
| Claude / Claude Code | automatic, read 0.1×; default TTL **5 min** (1 h opt-in `ENABLE_PROMPT_CACHING_1H`); compaction reuses prefix cache | when window fills | Opus 4.6–4.8 = **1M** | 5-min TTL makes mid-work warm-cache fragile → prefer phase-boundary handoff |
| OpenAI / Codex | automatic, no code/fee, 0.1×, prefix ≥1024 tok; **24 h extended on GPT-5.1** | server-side / local; **~95% capacity** | large (GPT-5.1-codex) | ~95% auto-compact is late & can derail mid-task → hand off at a boundary before that |
| Google / Gemini / Antigravity | **implicit caching default-on** (2.5+, 0.1×) + explicit `cachedContent` | large window absorbs more | **1M–2M** | big window → fewer handoffs; reason in occupancy %, not absolute turns |

> Sources (verified 2026-05-31): [Claude prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) + [compaction](https://developers.openai.com/api/docs/guides/compaction) · [Gemini caching](https://ai.google.dev/gemini-api/docs/caching). Re-verify before quoting — platform facts drift.

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

## 8. Output Brevity (AI Response Token Discipline)

Input-token optimization (reading strategy, context caching, file slimming) is undermined if AI *output* stays verbose. Output tokens cost the same as input tokens and compound every turn. This section is the canonical rule for AI response style; `AGENTS.md §Core Directives → Response Brevity` is its 1-line enforcement pointer.

### Official Grounding

- **Claude Code Best Practices** — [code.claude.com/docs/en/best-practices](https://code.claude.com/docs/en/best-practices):
  > *"Keep it concise. For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it. Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"*
- **Anthropic Prompting Best Practices** — [platform.claude.com prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices):
  > *"More direct and grounded: Provides fact-based progress reports rather than self-celebratory updates. Less verbose: May skip detailed summaries for tool calls, jumping directly to the next action. Respond directly without preamble. Do not start with phrases like 'Here is...', 'Based on...', etc."*

### DO

- **Default to terse.** When unsure between short and thorough, pick short.
- **Lead with the answer.** The first line answers the user's question or states the outcome; reasoning comes after only if asked.
- **Compress structure.** Single sentence > bullet list > table > multi-section dashboard. Use the lightest structure that fits.
- **Trust the diff.** For code/doc edits, the diff itself is evidence — do not re-narrate what every hunk changed.
- **Reference, don't re-quote.** Point to Work Log Evidence, file:line, or a URL instead of pasting content again.
- **End when done.** A short response that ends after answering is correct, not lazy.

### DON'T

- ❌ **Preamble**: *"I'll now proceed to..."*, *"Let me check..."*, *"Based on the analysis..."*, *"Here is the requested..."*.
- ❌ **Postamble self-summary**: *"I've now completed..."*, *"To summarize what I did..."*, *"In conclusion, the changes are..."*.
- ❌ **Decorative framing**: emoji dividers, horizontal rules, section headers when the whole response is 3 lines.
- ❌ **Multi-section dashboards** for simple results: a "Summary / Details / Next Steps" template when a sentence would do.
- ❌ **Re-explaining the task** back to the user before answering.
- ❌ **Unprompted recommendations** tacked on ("You might also want to consider...") unless directly risk-relevant.

### When Verbosity IS Appropriate

- **User explicitly asks** for a detailed report, audit, review, or explanation.
- **Governance-required artifacts**: gate blocks, plan artifacts (target files + AC), ship evidence, handoff summaries. These have a prescribed minimum content by workflow — meet it, don't exceed it.
- **Risk escalation**: when about to take a destructive or high-blast-radius action, explicitly list the blast radius and ask for confirmation. Brevity yields to safety.
- **Correction of a prior mistake**: when the AI was wrong earlier, it's acceptable to spend extra lines naming the error and the correction so the user can verify.

### Enforcement

- Self-check before emitting any response longer than ~10 lines: "Did the user ask for this level of detail, or am I padding?"
- Phase reports (bootstrap / plan / implement / review / ship) MUST still contain the governance-prescribed content, but trim every decorative surface not in that prescription.
- If a user feedback memory exists (e.g., `feedback_response_brevity.md`), it outranks default behavior — honor the specific preference recorded there.

### Rationale (Why this matters enough to be a rule)

Every verbose response is an input-token tax on the *next* turn (the conversation history replays), plus the output-token cost of the current turn. A 500-token padded response over 10 turns = 5,000 output tokens + 5,000×N cumulative input as history replays. Tightening response style is the single highest-leverage optimization after input-file slimming — and unlike file slimming, it applies to every session of every task forever.
