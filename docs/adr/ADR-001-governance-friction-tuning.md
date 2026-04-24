# ADR-001: Governance Friction Tuning

- **Status**: Accepted
- **Date**: 2026-04-23
- **Deciders**: @kbwen, AI Agent (Claude Opus 4.6)
- **Classification**: architecture-change

## Context

After a deep review of the Agentic OS governance framework, three systemic friction points were identified that cause unnecessary token waste, process fatigue, and developer frustration — without meaningfully improving code quality or safety.

These findings emerged from:
1. Analysis of `engineering_guardrails.md` (§4.4, §5.2a)
2. Analysis of `context-budget.md` read policies
3. Observation of Work Log compaction triggers in `.agent/config.yaml`

### Evidence Sources (Verified)

Prompt caching claims were verified against official documentation:
- [Anthropic Claude Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching): Cache reads = **10%** of base input price; cache writes = **125%** of base; **exact prefix match** required.
- [Google Gemini Context Caching](https://ai.google.dev/gemini-api/docs/caching): Implicit caching enabled by default on Gemini 2.5+; similar prefix-stability requirement.
- OpenAI Prompt Caching: Auto-enabled for ≥1024 tokens; up to **90% discount** on cached tokens; 5-10 minute TTL.

---

## Decision 1: Evidence Truncation in Work Logs

### Problem

`engineering_guardrails.md` and the Verification-Before-Completion contract require pasting terminal output (test results, error traces) into the Work Log `## Evidence` section. However, `.agent/config.yaml` triggers Work Log compaction at **300 lines / 12KB**. A single failed test with a full stack trace can consume 50-100 lines, triggering premature compaction that archives prior debug context — causing the AI to "forget" what it already tried.

### Decision

**Enforce evidence truncation at the source.** AI agents MUST NOT paste raw terminal output verbatim into Work Logs.

**Rules:**
- **Test pass**: Paste only the final summary line (e.g., `34 passed, 0 failed in 1.2s`). Maximum 3 lines.
- **Test fail**: Paste only the failing test name, the specific assertion error, and the relevant source line. Strip all passing test output and unrelated stack frames. Maximum 10 lines per failure.
- **Build/lint output**: Paste only error-level output. Strip warnings and informational messages unless they are the subject of the task.

### Rationale

This solves the problem at the source rather than creating a parallel `evidence/` directory structure that would cause file proliferation and require additional file-read operations at `/ship` time (each evidence file = 1 extra tool call = more tokens).

### Affected Files

| File | Change |
|---|---|
| `engineering_guardrails.md` | Add §5.2b "Evidence Truncation Rule" after §5.2a |
| `AGENTS.md` | Add truncation rule reference in "Verification Before Completion (5-Gate Sequence)" → Gate 3 (Evidence) |
| `.agent/config.yaml` | No change (compaction thresholds remain as-is) |

---

## Decision 2: Directory-Based Exemption for Design-First and Production Logger

### Problem

Two rules in `engineering_guardrails.md` are designed for production application code but create unnecessary friction when applied universally:

1. **§4.4 Design-First Rule**: Requires a DSoT (Design Source of Truth) link for any UI change. Blocks `/plan` if missing. This makes sense for production app screens, but blocks rapid prototyping of internal tools, CLI scripts, and scratch utilities.

2. **§5.2a Error Observability**: Prohibits `console.log()` / `print()` as the sole error path. This makes sense for production services, but blocks quick fixes to CLI scripts and dev tools that will never run in a production environment.

### Decision

**Bind these rules to directory scope, not to task classification.**

**Rules:**
- §4.4 Design-First Rule and §5.2a Error Observability apply **only** to files within production code directories: `src/`, `app/`, `lib/`, `packages/`.
- Files in the following directories are **automatically exempt**: `tools/`, `scripts/`, `scratch/`, `tests/`, `__tests__/`, `*.test.*`, `*.spec.*`, and any path under `.agentcortex/`.
- If a project defines custom production paths (e.g., `server/`, `frontend/`), those paths should be listed in `.agent/config.yaml` under a new `production_paths` key.

### Rationale

Using physical directory boundaries instead of subjective labels (like "PoC" or "internal tool") eliminates the classification-escape risk. Developers cannot abuse the exemption for production code because the exemption is tied to the file path, not to a developer's self-declared intent.

### Rejected Alternative

A "Prototyping Mode" flag that developers could set to bypass rules. Rejected because: (a) nothing is more permanent than a temporary workaround, (b) developers would label production code as "PoC" to skip design reviews, and (c) this requires human judgment at classification time, which is unreliable.

### Affected Files

| File | Change |
|---|---|
| `engineering_guardrails.md` §4.4 | Add "Scope Exemption" subsection defining exempt directories |
| `engineering_guardrails.md` §5.2a | Add note: "Scope: This rule applies to application/service code. **Files in `tools/`, `scripts/`, `scratch/`, and test directories are exempt.**" (Note: line 173 already says "Test-only code and CLI dev tools are exempt" — this formalizes the exact paths) |
| `.agent/config.yaml` | Add optional `production_paths` configuration key |

---

## Decision 3: Dual-Mode Context Budget (Prompt Caching Awareness)

### Problem

`context-budget.md` instructs `tiny-fix` tasks to **skip** reading `engineering_guardrails.md` entirely (saving ~3,500 tokens). This was a correct optimization when LLMs processed every token from scratch. However, all three major LLM providers (Anthropic, Google, OpenAI) now offer prompt caching with up to **90% discount** on cached input tokens — but only when the prompt **prefix is exactly identical** across requests.

The current policy creates two opposing scenarios:

1. **Standalone tiny-fix Session** (new conversation, 1-2 turns): No prior cache exists. Reading an extra 3,500 tokens is pure waste — the cache will never be reused.
2. **Mixed-task Session** (ongoing conversation, tiny-fix mid-stream): The guardrails are already in the cache from a prior `feature`/`hotfix` turn. Skipping the read **breaks the prefix**, causing a cache miss on the next turn — which costs far more than the 3,500 tokens saved.

### Decision

**Adopt a dual-mode strategy based on session context.**

**Rules:**
- **Fresh Session (no prior cache)**: `tiny-fix` and `quick-win` MAY skip `engineering_guardrails.md` as before. This is the default behavior.
- **Active Session (prior turns loaded guardrails)**: If the AI detects that `engineering_guardrails.md` was loaded in a prior turn of the current session (evidenced by the Guardrails Loaded receipt in the Work Log or conversation history), it MUST continue including the guardrails in subsequent requests to maintain prefix stability.
- **Guidance, not hard gate**: This is a SHOULD-level optimization recommendation, not a MUST-level gate. AI agents that cannot reliably detect session history may default to the current skip behavior without gate failure.

### Rationale

This preserves the original token-saving intent for the common case (one-shot tiny-fix conversations) while preventing the more expensive cache-thrashing scenario in longer sessions. The dual-mode approach avoids the "always read everything" extreme, which would penalize the simple case.

### Key Fact (Verified)

| Provider | Cache Read Discount | Cache Write Surcharge | TTL | Auto-Enable Threshold |
|---|---|---|---|---|
| Anthropic Claude | 90% off (0.1×) | 25% extra (1.25×) | 5 min (refreshable) | Manual `cache_control` |
| Google Gemini 2.5+ | ~75-90% off | Standard input rate | Configurable | Implicit (automatic) |
| OpenAI GPT | Up to 90% off | None | 5-10 min | Auto at ≥1024 tokens |

### Affected Files

| File | Change |
|---|---|
| `context-budget.md` | Add "Prompt Caching Awareness" section after §Anti-Patterns; update `tiny-fix` and `quick-win` tables with conditional note |
| `docs/guides/token-optimization-quickstart.md` | Add "Provider Caching" section explaining the dual-mode rationale |
| `docs/guides/token-optimization-quickstart_zh-TW.md` | Same, in Traditional Chinese |

---

## Consequences

### Positive

- **Reduced Work Log bloat**: Evidence truncation prevents premature compaction, preserving debug context across multiple fix attempts.
- **Faster prototyping**: Directory-based exemptions remove friction for legitimate non-production work without creating escape hatches for production code.
- **Better cost efficiency**: Dual-mode caching awareness prevents cache thrashing in mixed-task sessions while preserving savings for simple tasks.

### Negative

- **Agent complexity**: AI agents need to be aware of directory-based scope rules (Decision 2) and session-level caching state (Decision 3). Both add conditional logic to the agent's decision process.
- **Documentation surface**: Three files need updates, plus two quickstart guide translations.

### Neutral

- **No breaking changes**: All decisions are additive. Existing projects using the framework will continue to work without modification. The directory exemption formalizes behavior that was already partially documented (§5.2a line 173: "Test-only code and CLI dev tools are exempt").

---

## Implementation Plan

1. Update `engineering_guardrails.md` with §5.2b and directory-scope clarifications
2. Update `context-budget.md` with caching-awareness section
3. Update `AGENTS.md` evidence gate wording
4. Update both language versions of `token-optimization-quickstart`
5. Optionally add `production_paths` key to `.agent/config.yaml`

## References

- [Anthropic Prompt Caching Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Google Gemini Context Caching Docs](https://ai.google.dev/gemini-api/docs/caching)
- [OpenAI Prompt Caching Docs](https://platform.openai.com/docs/guides/prompt-caching)
- Internal: `engineering_guardrails.md` §4.4, §5.2a
- Internal: `context-budget.md`
- Internal: `.agent/config.yaml` compaction triggers
