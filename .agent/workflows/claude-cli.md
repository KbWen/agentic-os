---
name: claude-cli
description: "[OPTIONAL MODULE] Run a task via Claude CLI while enforcing Agentic OS governance rules automatically."
tasks:
  - claude-cli
---

# /claude-cli

> `[OPTIONAL MODULE]` — This workflow requires Claude Code CLI to be installed and available as the `claude` executable. If unavailable or not authenticated, AI falls back to native execution and **discloses** the substitution (this is an explicit executor request) per `engineering_guardrails.md` §8.2.
> This module is explicit opt-in. The AI should route here only when the user clearly asks to use Claude for the delegated subtask.

Dispatch a task to Claude CLI while ensuring Agentic OS governance compliance.

> This workflow wraps `claude` CLI calls with automatic Work Log creation, classification, prompt construction, and evidence collection. The orchestrating agent remains the orchestrator and final reviewer; the delegated `claude` CLI handles implementation or testing subtasks.

## Prerequisites

- Claude Code CLI installed and available as `claude`
- Claude Code authentication configured (`claude auth status` returns success)

## 1. Usage

```text
/claude-cli <task description>
```

Or in natural language:

```text
Run this via Claude CLI: [task description]
(ZH: 用 Claude CLI 幫我 [task description])
implement 交給 claude: [task description]
測試交給 claude: [task description]
```

> The user only provides the task in natural language. The AI agent is responsible for discovering target files, determining constraints, composing the governance-wrapped prompt, and then invoking `claude`.

## 2. AI Pre-Flight (Before Dispatching to Claude)

> Ref: `engineering_guardrails.md` §8.2 (External Tool Delegation Protocol)

AI MUST perform these steps **before** invoking `claude` (canonical order per `engineering_guardrails.md` §8.2):

1. **Record `Requested Executor: Claude CLI`** in the Work Log **first**. `/claude-cli` is an explicit user request, so any later fallback MUST be disclosed (step 3), never silent.
2. **Classify** the task per `engineering_guardrails.md` §10.1, then **Create/Update Work Log** at `.agentcortex/context/work/<worklog-key>.md` with classification, goal, target files, constraints, and whether the delegated step is implementation, testing, or both.
3. **Availability + Auth Check**: run `claude -v` and `claude auth status --text` (cache per session). On failure, fall back to native execution, **disclose** the substitution to the user (final handoff at latest), and record `Actual Executor: native (reason: cli-missing | auth-missing)`. On success, record `Actual Executor: Claude CLI`.
4. **Baseline Capture** (before invoking `claude`): snapshot the worktree with `git status --porcelain` + `git diff` so post-flight rollback can distinguish Claude's edits from files already **dirty at baseline**. Prefer an isolated git worktree for write-capable runs.
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
| `feature` | delegated subtask only | `--model sonnet --permission-mode acceptEdits` | Keep orchestration and final review in the orchestrating agent |
| `architecture-change` | ❌ Do NOT delegate the full task | — | Too broad for this workflow |
| `hotfix` | testing or bounded patch only | `--model sonnet --permission-mode acceptEdits` | Prefer native debugging for root-cause analysis |

## 3. AI Post-Flight (After Claude Completes)

AI MUST perform these steps **after Claude returns — or after any abnormal exit**:

0. **Abnormal exit** (timeout / nonzero exit / killed process / no result payload): a timed-out `claude` can write files before termination, so **STOP — do not retry**. Wait for the process to fully terminate, then re-derive worktree state (`git status --porcelain` + diff against the pre-flight baseline), record the partial state in the Work Log, and require explicit reconciliation before any re-invocation. A retry over an unreconciled partial write duplicates or overlaps edits.
1. **Verify scope**: Check `git diff` against the pre-flight baseline — did Claude modify files outside the target list?
   - If yes: reverse only Claude-attributable hunks. **Never whole-file-revert (`git checkout -- <path>`) a path that was dirty at baseline** — that destroys pre-existing user/agent work; reverse the specific hunks surgically or escalate to the user. Log the violation in the Work Log and warn the user.
2. **Collect evidence**: Capture Claude's output summary and append it to the Work Log.
3. **Run tests** if applicable: `npm test`, `pytest -q`, or the project-specific verification command.
4. **Update Work Log** with:
   - Claude execution result (success/partial/failure/fallback)
   - `Actual Executor` (+ fallback reason if it differed from `Requested Executor`)
   - Files actually modified
   - Test results
   - Whether the orchestrating agent accepted or rejected the delegated output
5. **Gate check**: Apply the standard gate for the classification tier (see `engineering_guardrails.md` §10.2).

## 4. Example Session

```text
User: 用 claude 幫我補這個 parser 的測試。

AI (internal):
  → Finds target file and existing tests.
  → Classification: feature subtask
  → Work Log updated with Executor: Claude CLI, Mode: testing
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

  Post-flight: git diff verified, pytest -q run by the orchestrating agent, evidence appended.

AI → User: Claude 補了 parser 的邊界與錯誤路徑測試，我已經檢查 diff 並補跑測試。
```

## 5. Error Handling

| Error | AI Action |
| --- | --- |
| Claude CLI not installed | Fall back to native execution; **disclose** the substitution (explicit request) and record `Actual Executor: native` |
| Claude auth missing | Fall back to native execution; **disclose** the substitution and record `Actual Executor: native` |
| Claude abnormal exit (timeout / nonzero / kill) | **STOP — do not retry.** Wait for termination, re-derive state vs the pre-flight baseline, record partial state, reconcile before any re-invocation |
| Claude modified wrong files | Reverse only Claude-attributable hunks; never whole-file-revert a path **dirty at baseline** (surgical revert or escalate); log + warn |
| Claude output unclear | The orchestrating agent reviews the diff manually and applies standard review |
| Task too complex for delegation | Reject delegation and continue with native execution |

## 6. Guardrails Integration

- All Agentic OS rules in `engineering_guardrails.md` apply to Claude-generated code.
- Claude CLI is treated as a **Junior Tool** — its output ALWAYS gets AI review before being accepted.
- The orchestrating agent remains the governance and acceptance layer; the delegated CLI is the execution layer.
- The operator does not need to hand-craft Claude CLI flags or prompt scaffolding for normal use; natural-language intent is enough for the AI orchestrator to assemble the delegated task.
- Ref: `engineering_guardrails.md` §8.2 (External Tool Delegation Protocol).
