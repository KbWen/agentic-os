---
status: accepted
date: 2026-04-23
amended: 2026-11-07
deciders: "@kbwen, AI Agent (Claude Opus 4.6)"
classification: architecture-change
applies_to:
  - "AGENTS.md"
  - ".agent/rules/engineering_guardrails.md"
  - ".agentcortex/docs/guides/context-budget.md"
  - ".agentcortex/docs/guides/token-governance.md"
  - ".agentcortex/docs/guides/token-optimization-quickstart.md"
  - "docs/guides/token-optimization-quickstart*.md"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When friction-tuning rules are amended (new directory exemption, evidence truncation threshold change, prompt-cache policy update), OR when a downstream fork hits a token-cost regression attributable to these decisions"
  supersedes: none
  superseded_by: none
---

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

### Historical Evidence Sources

The following sources and figures were recorded for the original decision. They are historical context, not current cache guarantees; re-check the provider's current model/runtime documentation before quoting them. Decision 3 defines the current context-reuse policy.
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

### Amendment (2026-07-16, record-only): D2 reaffirmed — capability-seam `design_tool` escape rejected

Backlog #119 flagged that the §4.4 Design-First gate hard-blocks a solo / tool-less downstream
adopter from planning UI work. The proposed fix (path A) was a capability-seam escape: an opt-in
`design_tool` key in `downstream-capabilities.yaml`, plus a prospective successor ADR superseding this
Decision (referred to at the time as "ADR-011" — the next free number, which was NEVER authored for
this rejected escape; the number was later taken by the unrelated
`ADR-011-phase-entry-directive-enforcement.md`, accepted 2026-07-19). A 5-seat roundtable — its seats including a 第十人 (refute-only) and a 事前驗屍
(pre-mortem) — reviewed it on 2026-07-08; all agents were same-vendor, so the human operator was the external signal per the
`[audit-method]` Global Lesson. Path A was UNANIMOUSLY rejected on three verified grounds:

- **The problem barely existed.** §4.4 step 1 already accepts a linkable artifact ("URL or file
  path"); a committed wireframe file always qualified — only the tool-centric wording hid it, so
  the shipped fix un-hides an existing allowance rather than opening a new escape.
- **The seam forbids gate-relaxation by construction.** `validate_downstream_capabilities.py` is a
  strict top-level-key allowlist (docstring: "Makes gate-relaxation UNREPRESENTABLE") — an unknown
  `design_tool` key rejects the whole file (breaking the adopter's real skills/KB), and
  `design_tool: none` *is* the forbidden FAIL→WARN relaxation the ADR-007/ADR-009 invariant bars.
- **D2's own rationale applies harder.** A repo-level, self-declared `design_tool` flag is exactly
  the self-declared intent D2 chose directory-scope to avoid; it reincarnates the "Prototyping
  Mode" flag rejected above, and "nothing more permanent than a temporary workaround" binds worse.

Shipped instead: **R1**, a framing clarification (v1.8.9, PR #324) — §4.4 and the `/plan` Design
Gate now name a committed `docs/design/<screen>.md` wireframe as a valid artifact; the gate stays
**HARD** (a UI task with no artifact still hard-stops at `/plan`). R2 (enforce-vs-delete the
honor-system gate) folded into backlog #122. **Do NOT retry** the capability-seam escape absent
new evidence invalidating the three grounds above (a superseding ADR would be required); full
rejection record at `docs/reviews/2026-07-08-design-gate-roundtable.md`. Recorded here by the
2026-07-16 decision-capture audit, because the rejection previously lived only on rotating
(SSoT Ship History, cap-10) or un-metabolized (a routing-action-less review snapshot) surfaces,
and a rejected ADR leaves no ADR Index entry.

---

## Decision 3: Context Reuse without Duplicate Reads

Amended 2026-11-07 (owner decision in chat, 2026-11-07): clarify context reuse under existing Read-Once and phase-entry rules; replace the reread-for-caching premise.

### Problem

The previous guidance conflated retaining previously supplied context with reading the same file again. In an ongoing conversation, omitting a duplicate file read does not itself remove earlier messages. Appending another read does not guarantee a cache hit. Cache reuse depends on the provider, model, eligible boundaries, and the context supplied by the host.

### Decision

**Apply the existing classification-based reading rules and Read-Once discipline; treat provider caching as an advisory optimization.**

- **Fresh context**: Load the documents required by the task classification and phase. Existing tiny-fix and quick-win exemptions remain unchanged.
- **Ongoing context**: Reuse already loaded, applicable instructions. Do not read guardrails again solely to obtain a provider cache hit.
- **Recovery and exceptions**: If required context is unavailable or may be stale, follow the existing recovery and Read-Once rules. Classification escalation and explicit phase-entry reading contracts still apply; this decision does not waive fresh shared-contracts reads.
- **Provider caching**: Preserve stable request prefixes where the host supports it. Do not infer cache hits, retention, or savings from a prior-read receipt; report measured usage when available and otherwise leave it unknown. Cache optimization creates no new gate.

### Rationale

This separates agent-controlled file reads from host-controlled request construction. It avoids duplicate context while preserving required instructions, recovery, and evidence. Safety invariants, phase order, review, test, and handoff requirements are unchanged.

### Provider References

Provider cache eligibility, rates, and retention vary by model and runtime. Consult current official documentation before quoting them; this decision establishes no fixed discount or token-saving estimate. See the provider links in References.

### Affected Files

| File | Change |
|---|---|
| `.agentcortex/docs/guides/context-budget.md` | Align tier notes and caching guidance with Read-Once |
| `docs/guides/token-optimization-quickstart.md` | Explain context reuse without duplicate reads |
| `docs/guides/token-optimization-quickstart_zh-TW.md` | Keep the corresponding explanation aligned |

### Amendment (2026-06-11): Safety invariants carved out of D3 jurisdiction

A real downstream incident (destructive `rm -rf` cascade; see Ship History 2026-06-11) plus a
follow-up audit showed that D3's skip policy had been applied to *safety* rules (destructive
commands, secrets, untrusted tool output), whose worst-case under a probabilistic load gate is
irreversible data loss — not wasted tokens. A 3-expert panel review concluded:

- **D3 governs cost/process rules only.** Flow-independent safety invariants (hazard reachable
  from any tool call AND irreversible/exfiltrating) are exempt from all skip policies and live as
  one-liners in `AGENTS.md §Core Directives` (capped cluster, promote-one-demote-one).
- **The dollar premise is stale**: the ~3,500-token saving ≈ $0.04/session at 2026 cached
  pricing — noise relative to the incident class it permitted. The tiering architecture itself
  (small always-on core + conditional procedural depth) remains correct and is NOT reverted;
  the sorting key for safety content changes from token cost to hazard reachability.

---

## Consequences

### Positive

- **Reduced Work Log bloat**: Evidence truncation prevents premature compaction, preserving debug context across multiple fix attempts.
- **Faster prototyping**: Directory-based exemptions remove friction for legitimate non-production work without creating escape hatches for production code.
- **Less duplicate context**: Reuse applicable loaded instructions without an extra read solely for caching; actual savings require runtime measurement.

### Negative

- **Agent complexity**: AI agents still apply directory-based scope rules (Decision 2) and existing context recovery rules (Decision 3); a prior-read receipt is not a cache-hit guarantee.
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
