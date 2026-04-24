# Token Optimization Quickstart

> **Audience**: Developers who cloned Agentic OS and want to reduce token consumption immediately.
>
> **Prerequisite knowledge**: None — this guide is self-contained. For deep dives, see [Token Governance](../../.agentcortex/docs/guides/token-governance.md) and [Context Budget](../../.agentcortex/docs/guides/context-budget.md).

---

## TL;DR — 3 Things You Can Do Right Now

1. **Classify tasks accurately** — say "tiny-fix" or "quick-win" explicitly to avoid full feature workflows.
2. **Disable expensive skills** — copy the user preferences template and turn off what you don't need.
3. **Keep your SSoT clean** — archive old entries before they bloat your context window.

---

## 1. Understand the Token Cost Landscape

Every task in Agentic OS follows a phase-based workflow. The more phases, the more tokens consumed:

| Classification | Typical Token Cost | Phases |
|:---|---:|:---|
| `tiny-fix` | ~2,000–5,000 | Classify → Execute → Evidence |
| `quick-win` | ~15,000–17,000 | Bootstrap → Plan → Implement → Ship |
| `feature` | ~30,000–60,000 | Full 7-phase lifecycle |
| `architecture-change` | ~50,000–65,000 | Full lifecycle + ADR + all skills |

**Key insight**: The single biggest cost driver is **task misclassification**. A typo fix classified as `feature` wastes 30K+ tokens on unnecessary planning, review, and testing phases.

### How to Classify Correctly

When you give your AI agent a task, be explicit:

```
❌ "Fix the date format bug"              → AI may classify as feature
✅ "Fix the date format bug (tiny-fix)"   → AI takes the fast path
✅ "This is a quick-win: add pagination"  → AI skips guardrails, saves ~3,500 tokens
```

---

## 2. Disable Expensive Skills

Agentic OS auto-activates skills based on task type. Some skills are heavy:

| Skill | Cost Risk | When to Disable |
|:---|:---|:---|
| `red-team-adversarial` | High | Internal tools, non-security projects |
| `dispatching-parallel-agents` | High | Single-developer workflows |
| `subagent-driven-development` | High | Simple, single-module tasks |
| `test-driven-development` | Medium | Prototyping, exploratory work |

### How to Disable

1. Copy the template:
   ```bash
   cp .agentcortex/templates/user-preferences.yaml \
      .agentcortex/context/private/user-preferences.yaml
   ```

2. Edit to disable skills:
   ```yaml
   skill_preferences:
     pinned: []
     disabled:
       - dispatching-parallel-agents
       - subagent-driven-development
       - red-team-adversarial
   ```

3. This file is **gitignored** — it's personal to your environment.

> **Note**: `verification-before-completion` and `auth-security` are **protected** and cannot be disabled. This is by design — they are safety-critical.

---

## 3. Keep Your SSoT Lean

The Single Source of Truth (`.agentcortex/context/current_state.md`) grows over time. A bloated SSoT means the AI reads thousands of irrelevant tokens every session.

### Built-in Safeguards

Agentic OS already has automatic limits (in `.agent/config.yaml`):

| Setting | Default | Purpose |
|:---|:---|:---|
| `global_lessons_max_entries` | 20 | Auto-archive old lessons |
| `spec_index_max_entries` | 30 | Collapse shipped specs |
| `worklog.max_lines` | 300 | Trigger compaction |
| `worklog.max_kb` | 12 | Trigger compaction |

### Manual Maintenance

If your SSoT feels heavy, ask your AI agent:

```
"Compact the SSoT — archive shipped specs and low-severity lessons."
```

Or manually move old entries from `current_state.md` into `.agentcortex/context/archive/`.

---

## 4. Leverage Provider Context Caching (Dual-Mode Strategy)

Modern LLM providers (Anthropic Claude, Google Gemini, OpenAI) automatically cache stable prompt prefixes, offering massive discounts (up to 90% off). You don't need to configure this, but you can maximize its benefit:

- **Fresh Sessions**: For standalone `tiny-fix` tasks, the agent skips reading guardrails. This saves ~3,500 base tokens outright since there's no prior cache to leverage.
- **Active Sessions (Mixed-Task)**: If your session already loaded guardrails earlier, **do not skip them** in subsequent turns. Keeping the prompt prefix identical triggers a massive cache discount, which is cheaper than breaking the cache by skipping them.
- **Don't re-paste governance docs** mid-conversation. They're already in context.

---

## 5. Optimize AI Response Length

Output tokens cost the same as input tokens and compound every turn. A 500-token padded response over 10 turns = 10,000+ wasted tokens.

Agentic OS already enforces this (see `AGENTS.md §Response Brevity`), but you can reinforce it:

```
"Keep responses under 8 lines. Reference the Work Log instead of re-narrating."
```

---

## 6. Advanced: Customize for Your Project

### Reduce File Reads at Bootstrap

The [Context Budget Guide](../../.agentcortex/docs/guides/context-budget.md) defines exactly which files are read per classification:

| Classification | Max File Reads |
|:---|:---|
| `tiny-fix` | 1–2 |
| `quick-win` | 3–5 |
| `feature` | 6–9 |
| `architecture-change` | 8–12 |

If the AI is reading files outside these budgets, it's a **Token Leak** — flag it.

### Skip Guardrails for Small Tasks

For `tiny-fix` and `quick-win`, the full `engineering_guardrails.md` (~14KB, ~3,500 tokens) is **already skipped** by design. The essential rules are embedded in `AGENTS.md §Core Directives`.

---

## Quick Reference: What's Already Built In

Before building custom optimizations, know that these mechanisms already exist:

| Mechanism | Location | What It Does |
|:---|:---|:---|
| Conditional loading | `context-budget.md` | Skip guardrails for tiny-fix/quick-win |
| Skill cache policy | `.agent/config.yaml §skill_cache_policy` | Metadata-first loading, full SKILL.md only on cache miss |
| User skill preferences | `.agentcortex/templates/user-preferences.yaml` | Pin/disable skills per user |
| Work Log compaction | `.agent/config.yaml §worklog` | Auto-compact at 300 lines / 12KB |
| Document lifecycle | `.agent/config.yaml §document_lifecycle` | Auto-archive SSoT entries |
| Output brevity | `token-governance.md §8` | AI response ≤ 8 lines + structured blocks |
| Read-Once Discipline | `AGENTS.md §Core Directives` | Governance docs never re-read |
| Context caching | `token-governance.md §6` | Provider-side caching, zero config |

---

## Self-Optimization Roadmap

Agentic OS is designed to improve over time. Here's how the framework evolves with usage:

1. **`/retro` learns from mistakes** — Process failures are recorded as Global Lessons in the SSoT, which future sessions read and avoid.
2. **Skill cache warms up** — After the first use of a skill, subsequent phases use cached Skill Notes (~22% of full SKILL.md size).
3. **Work Log compaction** — Old entries are automatically archived, keeping context lean.
4. **Classification accuracy improves** — As the SSoT accumulates ship history, the AI gets better at pattern-matching task types.

> **For framework contributors**: If you want to propose structural token optimizations (e.g., merging workflow files, slimming guardrails), open an issue or submit a PR. The [Lifecycle Benchmark](../LIFECYCLE_BENCHMARK.md) provides baseline measurements for comparison.

---

*See also: [Token Governance (internal)](../../.agentcortex/docs/guides/token-governance.md) · [Context Budget (internal)](../../.agentcortex/docs/guides/context-budget.md) · [Lifecycle Benchmark](../LIFECYCLE_BENCHMARK.md)*
