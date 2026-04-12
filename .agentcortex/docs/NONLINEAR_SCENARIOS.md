# Non-Linear Resilience: AI Auto-Management Rules

> These rules are loaded by the AI Agent. They define **automatic behaviors** the AI MUST execute when detecting non-linear human patterns. Humans should not need to memorize or manually trigger these — the AI handles it.

---

## Rule 1: Auto-Checkpoint (Prevents Session Crash Data Loss)

**Trigger**: AI detects it has completed **3+ turns of implementation work** without a Work Log update.

**AI MUST**:

1. Automatically write a `## Checkpoint` block to the active Work Log:

```markdown
## Checkpoint
- State: [current state machine state]
- Completed: [list of completed steps this session]
- Next: [immediate next planned action]
- Modified Files: [list of files changed but not yet committed]
- Timestamp: [current time]
```

1. Suggest a WIP commit: "Recommend committing current changes as WIP. Proceed?"
2. Continue working — do NOT wait for user approval on the checkpoint write itself.

**Rationale**: Humans forget to save. Sessions crash without warning. The AI is the safety net.

---

## Rule 2: Auto-Resume Detection (Handles Model Switching & Crash Recovery)

**Trigger**: During `/bootstrap`, AI finds an existing Work Log with content.

**AI MUST**:

1. Check for `## Resume` or `## Checkpoint` blocks (in that priority order).
2. If found, announce: "Detected previous session state: **[State]**. Resuming from: [last checkpoint]. Modified files from previous session: [list]."
3. Run `git status` to detect orphaned changes (uncommitted files from crashed session).
4. If orphaned changes exist, report: "Found uncommitted changes from a previous session: [files]. These may be from a crash. Review before continuing? (yes/continue as-is)"
5. Resume from the recorded state — do NOT restart from `INIT`.

**If NO active Work Log exists but `git log` shows recent commits on the branch**:

- Reconstruct minimal context from recent commits.
- Create a new Work Log with inferred state.
- Announce: "No Work Log found, but detected recent work on this branch. Created recovery Work Log at the resolved `<worklog-key>` path."

**Rationale**: When a human switches models or a session crashes, the new AI instance has zero memory. The Work Log + git state is the bridge. The AI does the detective work, not the human.

---

## Rule 3: Pre-Switch Auto-Save (Detects Imminent Model Switch)

**Trigger**: Human says anything suggesting a model switch, such as:

- EN: "let me try another model", "switching to...", "I'll use Claude/GPT/Gemini", "this model isn't working"
- ZH: "換個模型", "切換到...", "我用Claude試試", "這模型不行", "換一個"

**AI MUST**:

1. Immediately write `## Resume` block to Work Log (same format as `/handoff` output).
2. Commit any uncommitted changes with message: `wip: auto-save before model switch`.
3. Output a **single copyable line** for the human to paste into the next model:

```
請執行 /bootstrap。Resolved Work Log: .agentcortex/context/work/<worklog-key>.md
```

1. Announce: "State saved. Paste the line above into the new model to continue."

**Rationale**: Human only needs to copy ONE line. Everything else is automatic.

---

## Rule 4: Non-Linear State Rollback (Handles Plan Changes Mid-Implementation)

**Trigger**: During `IMPLEMENTING`, AI or human discovers the plan is wrong, incomplete, or needs revision.

**AI MUST**:

1. Record in Work Log:

```markdown
## State Rollback
- From: IMPLEMENTING
- To: CLASSIFIED
- Reason: [concrete reason — e.g., "edge case X not covered in plan"]
- Timestamp: [current time]
```

1. Announce: "Plan revision needed: [reason]. Rolling back to CLASSIFIED. Re-running the required gate."
2. If scope grew, upgrade the classification explicitly before continuing. Silent downgrade is never allowed.
3. Re-enter the required workflow phase (`/plan`, `/spec`, or `/adr`) with updated constraints.
4. Do NOT ask human for permission to roll back — just log it and do it. The audit trail in the Work Log is sufficient.

**Rationale**: The state machine is a guide, not a prison. Rollbacks with logged justification are always valid.

---

## Rule 5: Blocker Isolation (Auto-Manages Multi-Task Chaos)

**Trigger**: During any task, AI discovers a blocking issue that requires a separate fix.

**AI MUST**:

1. Write `## Blocker Detected` to current Work Log:

```markdown
## Blocker Detected
- Blocker: [brief description]
- Impact: [what is blocked]
- Recommended: Fix blocker first, then resume this task.
```

1. Ask human ONE question: "Found a blocker: [description]. Fix it first and come back, or work around it?"
2. If human says fix first:
   - Auto-write `/handoff` for current task.
   - Start new `/bootstrap` for the blocker with its own Work Log.
   - After blocker is resolved, prompt: "Blocker fixed. Resume [original task]?"

**Rationale**: Humans naturally context-switch. The AI manages the parking and resuming of tasks.

---

## Rule 6: Turn Count Auto-Handoff (Existing Rule Enhancement)

**Enhancement to AGENTS.md §Context Pruning**:

When turn count exceeds 8, the existing rule says _suggest_ handoff. This enhancement makes it stronger:

**AI MUST**:

1. At turn 8: suggest handoff (existing behavior).
2. At turn 12: write `## Checkpoint` automatically, even if human ignored the suggestion.
3. At turn 15: escalate warning: "⚠️ We're at 15 turns. Context quality is degrading. Strongly recommend `/handoff` now."

**Rationale**: Humans ignore warnings. The AI protects against context degradation by writing checkpoints regardless.

---

## Summary: What the Human Needs to Do

| Situation | Human Action | AI Action |
| --- | --- | --- |
| Session might crash | **Nothing** | Auto-writes `## Checkpoint` every 3+ implementation turns |
| Switching models | **Copy-paste one line** | Auto-saves state, auto-commits WIP, generates the line |
| Session crashed | **Just start `/bootstrap`** | Auto-detects Work Log + orphaned git changes, auto-resumes |
| Plan is wrong mid-implementation | **Nothing** (or just say "計畫有問題") | Auto-rolls back state, re-plans, logs justification |
| Blocker discovered | **Answer one yes/no** | Manages task parking and switching automatically |
| Long session (8+ turns) | **Nothing** | Auto-checkpoints at 12 turns, escalates at 15 |

> **Design Principle**: The human's cognitive load is near-zero. The AI is the process manager.

---

## Further Reading

- [Project Examples (Linear Workflows)](./PROJECT_EXAMPLES.md)
- [Engineering Guardrails (Constitution)](../../.agent/rules/engineering_guardrails.md)
- [Agent Model Guide (Model Selection)](../AGENT_MODEL_GUIDE.md)
