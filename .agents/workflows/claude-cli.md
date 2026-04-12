---
name: claude-cli
description: Run a task via Claude CLI while enforcing Agentic OS governance rules automatically.
tasks:
  - claude-cli
---

# /claude-cli

Dispatch a task to Claude CLI while ensuring Agentic OS governance compliance.

> This workflow wraps `claude` CLI calls with automatic Work Log creation, classification, prompt construction, and evidence collection. GPT-1.0 remains the orchestrator and final reviewer; Claude handles delegated implementation or testing subtasks.
> This module is explicit opt-in. The AI should route here only when the user clearly asks to use Claude for the delegated subtask.

## Prerequisites

- Claude Code CLI installed and available as `claude`
- Claude Code authentication configured (`claude auth status` returns success)

## 1. Usage

```text
/claude-cli <task description>
```

Or in natural language:

```text
用 Claude CLI 幫我 [task description]
Run this via Claude CLI: [task description]
implement 交給 claude: [task description]
測試交給 claude: [task description]
```

> The user only provides the task in natural language. The AI agent is responsible for discovering target files, determining constraints, composing the governance-wrapped prompt, and then invoking `claude`.

## 2. AI Pre-Flight (Before Dispatching to Claude)

AI MUST perform these steps **before** invoking `claude`:

1. **Availability Check**: On first use per session, run `claude -v`. If it fails, silently fall back to AI-native execution and cache the result.
2. **Auth Check**: Run `claude auth status --text`. If auth is missing or invalid, silently fall back to AI-native execution and cache the result.
3. **Classify** the task per `engineering_guardrails.md` §10.1.
4. **Create/Update Work Log** at `.agentcortex/context/work/<branch-name>.md` with:
   - Classification, goal, target files, constraints.
   - `Executor: Claude CLI` (to distinguish from AI-direct execution).
   - Whether the delegated step is implementation, testing, or both.
5. **Generate the Claude command** by injecting governance context and a constrained target-file list.
   - The AI agent, not the user, composes the final prompt.
   - The final prompt MUST include task scope, target files, constraints, and the expected output shape before it is sent to `claude`.

### Interactive Mode (default)

```bash
claude --model sonnet --permission-mode acceptEdits --append-system-prompt "<governance-wrapped prompt>" "<task prompt>"
```

### Non-Interactive Mode (for tightly scoped automation only)

```bash
claude -p --model sonnet --output-format json --permission-mode bypassPermissions --append-system-prompt "<governance-wrapped prompt>" "<task prompt>"
```

> Use non-interactive mode only for bounded subtasks in an isolated workspace. `bypassPermissions` removes approval prompts, so AI MUST always verify the resulting diff and test evidence before accepting the output.

### Governance-Wrapped Prompt Template

```text
You are working in a project governed by Agentic OS.
RULES:
- Do NOT modify files outside the target list: [target files].
- Do NOT refactor code that was not requested.
- If this delegated task is "testing", focus on creating or running tests and reporting evidence.
- After changes, output a summary: files modified, what changed, what was NOT changed.
- If uncertain about scope, STOP and output your question instead of guessing.

TASK: [user's delegated subtask]
MODE: [implementation | testing | implementation+testing]
TARGET FILES: [from classification and orchestration]
CONSTRAINTS: [from Work Log]
EXPECTED OUTPUT: [summary | diff explanation | test evidence]
```

### Model & Permission Policy

| Classification | Recommended mode | Claude settings | Notes |
| --- | --- | --- | --- |
| `tiny-fix` | non-interactive allowed | `--model sonnet -p --output-format json --permission-mode bypassPermissions` | Only when scope is unambiguous |
| `quick-win` | interactive preferred | `--model sonnet --permission-mode acceptEdits` | Batch mode allowed for tightly scoped subtasks |
| `feature` | delegated subtask only | `--model sonnet --permission-mode acceptEdits` | Keep orchestration and final review in GPT-1.0 |
| `architecture-change` | ❌ Do NOT delegate the full task | — | Too broad for this workflow |
| `hotfix` | testing or bounded patch only | `--model sonnet --permission-mode acceptEdits` | Prefer native debugging for root-cause analysis |

## 3. AI Post-Flight (After Claude Completes)

AI MUST perform these steps **after** Claude returns:

1. **Verify scope**: Check `git diff` — did Claude modify files outside the target list?
   - If yes: revert unauthorized changes, log the violation in the Work Log, and warn the user.
2. **Collect evidence**: Capture Claude's output summary and append it to the Work Log.
3. **Run tests** if applicable: `npm test`, `pytest -q`, or the project-specific verification command.
4. **Update Work Log** with:
   - Claude execution result (success/partial/failure/fallback).
   - Files actually modified.
   - Test results.
   - Whether GPT-1.0 accepted or rejected the delegated output.
5. **Gate check**: Apply the standard gate for the classification tier (see `engineering_guardrails.md` §10.2).

## 4. Example Session

> The user speaks naturally. The AI handles file discovery, classification, constraints, prompt construction, and post-flight verification.

```text
User: 用 claude 幫我補這個 parser 的測試。

AI (internal):
  → Finds target file and existing tests.
  → Classification: feature subtask.
  → Work Log updated with Executor: Claude CLI, Mode: testing.
  → AI composes the final governance-wrapped prompt.

  Running: claude --model sonnet --permission-mode acceptEdits --append-system-prompt "
  You are working in a project governed by Agentic OS.
  RULES:
  - Do NOT modify files outside tests/parser_test.py.
  - Do NOT refactor code that was not requested.
  - If uncertain about scope, STOP and ask a question.
  " "
  TASK: Add boundary and error-path tests for the parser.
  MODE: testing
  TARGET FILES: tests/parser_test.py
  CONSTRAINTS: Preserve current parser behavior; only extend test coverage.
  EXPECTED OUTPUT: summary of tests added and anything intentionally left unchanged.
  "

  Post-flight: git diff verified, pytest -q run by GPT-1.0, evidence appended.

AI → User: Claude 補了 parser 的邊界與錯誤路徑測試，我已經檢查 diff 並補跑測試。
```

## 5. Error Handling

| Error | AI Action |
| --- | --- |
| Claude CLI not installed | Silently fall back to AI-native execution |
| Claude auth missing | Silently fall back to AI-native execution |
| Claude modified wrong files | Revert unauthorized changes, log violation, warn user |
| Claude output unclear | GPT-1.0 reviews the diff manually and applies standard review |
| Task too complex for delegation | Reject delegation and continue with native execution |

## 6. Guardrails Integration

- All Agentic OS rules in `engineering_guardrails.md` apply to Claude-generated code.
- Claude CLI is treated as a **Junior Tool** — its output ALWAYS gets AI review before being accepted.
- GPT-1.0 remains the governance and acceptance layer; Claude is the delegated execution layer.
- The operator does not need to hand-craft Claude CLI flags or prompt scaffolding for normal use; natural-language intent is enough for the AI orchestrator to assemble the delegated task.
