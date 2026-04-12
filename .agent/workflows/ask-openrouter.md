---
name: ask-openrouter
description: "[OPTIONAL MODULE] Delegate tasks to OpenRouter models via natural language or /or-* commands."
tasks:
  - ask-openrouter
---

# ask-openrouter

> `[OPTIONAL MODULE]` — This workflow requires the globally installed `ask-openrouter` CLI. If unavailable, AI silently falls back to native execution per `engineering_guardrails.md` §8.2.

Delegate development tasks (plan, design, review, implement) to external OpenRouter models for a second opinion or specialized processing.

## 1. Intent Router (Natural Language Driven)

AI does NOT require slash commands. When processing user input, AI checks for **delegation signals**:

### Explicit Signals (auto-trigger)

- EN: "use OpenRouter", "ask another model", "get a second opinion", "external review"
- ZH: "用 OpenRouter", "問別的模型", "第二意見", "外部審查", "用外部模型"

### Implicit Signals (AI proactively suggests)

- EN: "full architecture review", "comprehensive analysis", "complete restructuring"
- ZH: "全面架構審查", "完整分析", "全面重構"

When implicit signals are detected, AI suggests using OpenRouter. Example: "This task could benefit from an external model's perspective. Use OpenRouter?"

### No Signal = No Delegation

If user simply says "help me plan this", AI uses its own capabilities via the standard `/plan` workflow. OpenRouter does NOT intervene.

### Slash Command Shortcuts (still supported)

`/or-plan`, `/or-design`, `/or-review`, `/or-implement` — direct trigger, skip intent detection.

## 2. Task Mapping

| User Intent | `--task` | Default `--profile` | Context Flags |
| --- | --- | --- | --- |
| Plan | `plan` | `fast` | `--tree --spec-pack` |
| Design | `design` | `fast` | `--tree --spec-pack` |
| Review | `review` | `quality` | `--tree --spec-pack` |
| Implement | `code` | `quality` | `--research-files [report]` |

## 3. Pre-Flight (per §8.2)

Before invoking `ask-openrouter`, AI MUST:

1. **Availability Check**: On first use per session, run `python -m ask_openrouter --help`. If fails → silently fall back. Cache result.
2. **Classify** the task per `engineering_guardrails.md` §10.1.
3. **Cost-Tier Confirmation**: `--profile fast` → auto-execute. `--profile quality`/`max` → confirm with user.
4. **Update Work Log**: Add `Executor: ask-openrouter` to current entry.

## 4. Execute

Dynamically assemble the command based on user intent:

// turbo

```bash
python -m ask_openrouter "<user's request>" --task <mapped-task> --profile <mapped-profile> [context-flags] [--files <specific-files>]
```

### Dynamic Parameter Assembly

- **`--files`**: Add when user mentions specific files (e.g., "review `api.py`" → `--files api.py`).
- **`--profile` escalation**:
  - Default: `fast`.
  - Upgrade to `quality` on keywords (EN: "complex", "precise", "full architecture", "comprehensive refactor" / ZH: "複雜", "精準", "完整架構", "全面重構").
  - `max` only when user explicitly requests.
- **`--tree` & `--spec-pack`**: Add for plan/design/review tasks. Omit for single-file operations.
- **`-o <path>`**: Add when user specifies output path.
- **`--research-files`**: For `--task code`, include prior report path.

## 5. Post-Flight (per §8.2)

After `ask-openrouter` completes, AI MUST:

1. **Read output**: Check `.openrouter/` or `.agentcortex/context/work/` for the generated `.md` report.
2. **Verify scope**: Ensure output aligns with the original task scope.
3. **For `--task code`**: Check if auto-apply succeeded. If `.openrouter.patch` exists, review and handle.
4. **Update Work Log**: Append execution result, output file path, and any issues.
5. **Gate Check**: Apply standard gate per classification tier (§10.2).
6. **Chain to next step**: If report suggests implementation, offer to proceed with `/implement` using the report as input.

## 6. Example Sessions

> Natural language in, structured execution out. Works in any language.

```text
User: Use an external model to plan a user authentication feature.

AI (internal):
  → Intent Router: detected "external model" → delegation signal ✓
  → Task mapping: "plan" → --task plan
  → Profile: no complexity keywords → --profile fast
  → Availability: cached ✓
  → Cost: fast → auto-execute

  Running: python -m ask_openrouter "Plan user authentication feature" --task plan --profile fast --tree --spec-pack

  Post-Flight: report saved to .openrouter/plan_auth_20260304.md
  → Read report, update Work Log.

AI → User: OpenRouter completed the auth feature plan. Report at .openrouter/plan_auth_20260304.md.
           Want me to start implementing based on this report?
```

```text
User: 對目前的架構做一個全面審查
     (Do a comprehensive review of the current architecture)

AI (internal):
  → Intent Router: detected "全面架構審查" → implicit signal
  → AI suggests: "This task could benefit from an external model. Use OpenRouter?"

User: OK

  → Task mapping: "review" → --task review
  → Profile: "全面" (comprehensive) → --profile quality
  → Cost: quality → already confirmed ✓

  Running: python -m ask_openrouter "Comprehensive architecture review" --task review --profile quality --tree --spec-pack

AI → User: Review report complete. [summary of findings]
```

## 7. Error Handling

| Error | AI Action |
| --- | --- |
| Tool not installed | Silent fallback to AI-native. No warning. |
| API key missing / auth error | Inform user: "OpenRouter API key not configured." Fall back. |
| Tool timeout | Log in Work Log, fall back to AI-native. |
| Output unreadable | AI reviews raw output manually, applies standard review. |

## 8. Guardrails Integration

- All rules in `engineering_guardrails.md` apply to OpenRouter-generated output.
- OpenRouter is a **Junior Tool** — output ALWAYS gets AI review before acceptance.
- The AI is the governance layer; OpenRouter is the execution layer.
- Ref: `engineering_guardrails.md` §8.2 (External Tool Delegation Protocol).
