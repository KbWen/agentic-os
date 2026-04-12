---
name: codex-cli
description: Run a task via Codex CLI while enforcing AgentCortex governance rules automatically.
tasks:
  - codex-cli
---

# /codex-cli

Dispatch a task to OpenAI Codex CLI while ensuring AgentCortex governance compliance.

> This workflow wraps `codex` CLI calls with automatic Work Log creation, classification, and evidence collection.

## Prerequisites

- Codex CLI installed: `npm install -g @openai/codex`
- API key configured: `OPENAI_API_KEY` set in environment (or run `codex login`)

## 1. Usage

```text
/codex-cli <task description>
```

Or in natural language:

```text
用 Codex CLI 幫我 [task description]
Run this via Codex CLI: [task description]
```

## 2. AI Pre-Flight (Before Dispatching to Codex)

AI MUST perform these steps **before** invoking `codex`:

1. **Classify** the task per `engineering_guardrails.md` §10.1.
2. **Create/Update Work Log** at `.agentcortex/context/work/<branch-name>.md` with:
   - Classification, goal, target files, constraints.
   - `Executor: Codex CLI` (to distinguish from AI-direct execution).
3. **Generate the Codex command** by injecting governance context:

### Interactive Mode (default — user can see and approve changes)

```bash
codex -a untrusted -s workspace-write -C <project-root> "<governance-wrapped prompt>"
```

### Non-Interactive Mode (for scripted / batch execution)

```bash
codex exec --full-auto -C <project-root> "<governance-wrapped prompt>"
```

> `codex exec` is inherently non-interactive (no user approval). `--full-auto` adds sandboxed write access.

### Governance-Wrapped Prompt Template

```text
You are working in a project governed by AgentCortex.
RULES:
- Do NOT modify files outside the target list: [target files].
- Do NOT refactor code that was not requested.
- After changes, output a summary: files modified, what changed, what was NOT changed.
- If uncertain about scope, STOP and output your question instead of guessing.

TASK: [user's task description]
TARGET FILES: [from classification]
CONSTRAINTS: [from Work Log]
```

### Approval & Sandbox Policy

| Classification | Approval (`-a`) | Sandbox (`-s`) | Shorthand |
| --- | --- | --- | --- |
| `tiny-fix` | `on-request` | `workspace-write` | `--full-auto` |
| `quick-win` | `untrusted` | `workspace-write` | — |
| `feature` | `untrusted` | `workspace-write` | — |
| `architecture-change` | ❌ Do NOT use Codex CLI. Too complex. | — | — |
| `hotfix` | `untrusted` | `read-only` | — |

> **Key reference for `-a` (ask-for-approval) values:**
>
> - `untrusted`: Auto-runs safe commands (ls, cat, sed); escalates others to user.
> - `on-request`: Model decides when to ask (lowest friction).
> - `never`: Never asks — use ONLY with `codex exec` in scripted mode.

## 3. AI Post-Flight (After Codex Completes)

AI MUST perform these steps **after** Codex returns:

1. **Verify scope**: Check `git diff` — did Codex modify files outside the target list?
   - If yes: revert unauthorized changes, log in Work Log, warn user.
2. **Collect evidence**: Capture Codex's output summary and append to Work Log.
3. **Run tests** if applicable: `npm test` / `pytest -q` / project-specific test command.
4. **Update Work Log** with:
   - Codex execution result (success/partial/failure).
   - Files actually modified.
   - Test results.
5. **Gate check**: Apply the standard gate for the classification tier (see §10.2).

## 4. Example Session

> The user speaks naturally. The AI handles all details (file discovery, classification, constraints, prompt construction).

```text
User: README 有個錯字，幫我用 codex 修一下

AI (internal):
  → Scans README.md, finds "recieve" on line 42.
  → Classification: tiny-fix
  → Work Log: skipped (tiny-fix)

  Running: codex --full-auto "Fix typo in README.md line 42: 'recieve' → 'receive'. Do NOT modify anything else."

  Result: ✅ README.md modified. 1 line changed.
  Evidence: diff shows only the typo fix. No other files touched.

AI → User: 已修好 README.md 的錯字（recieve → receive），沒有動其他東西。
```

```text
User: formatDate 能不能支援多語系？用 codex 幫我加

AI (internal):
  → Searches codebase: formatDate is in utils/format.ts.
  → Classification: quick-win (1 file, clear scope)
  → Work Log: .agentcortex/context/work/main.md (Executor: Codex CLI)
  → AI determines constraints: must be backward-compatible (no locale = current behavior).

  Running: codex -a untrusted -s workspace-write "
  AgentCortex rules: only modify utils/format.ts. No refactoring.
  Task: Add optional locale parameter to formatDate function.
  Constraint: Default behavior unchanged when locale is not provided.
  "

  Codex proposes:
    [shows diff — user approves in-terminal]
  
  Post-flight: git diff verified (only format.ts). npm test → all pass.

AI → User: 已加好 locale 參數，預設行為不變。測試通過。
```

## 5. Advanced: Non-Interactive Batch Execution

For tasks where the AI dispatches Codex without human interaction:

```bash
codex exec --full-auto -C /path/to/project "Task prompt here"
```

Use `codex exec` when:

- The classification is `tiny-fix` AND the scope is unambiguous.
- The AI orchestrator (e.g., Flash) is managing the task end-to-end.
- Post-flight verification is guaranteed.

> ⚠️ `codex exec` skips ALL human confirmation by design. AI MUST verify every change via `git diff` in Post-Flight.

## 6. Error Handling

| Error | AI Action |
| --- | --- |
| Codex not installed | Output: `npm install -g @openai/codex` and stop |
| API key missing | Output: run `codex login` or set `OPENAI_API_KEY` and stop |
| Codex modified wrong files | Auto-revert via `git checkout -- <file>`, log violation, warn user |
| Codex output unclear | AI reviews diff manually, applies standard review |
| Task too complex for Codex | Reject and suggest direct AI implementation |

## 7. Guardrails Integration

- All AgentCortex rules in `engineering_guardrails.md` apply to Codex-generated code.
- Codex is treated as a **Junior Tool** — its output ALWAYS gets AI review before being accepted.
- The AI is the governance layer; Codex is the execution layer.
