---
name: handoff
description: Cross-turn handoff summary & hard reference checks.
tasks:
  - handoff
---

# /handoff

Hard completion gate for non-`tiny-fix` tasks. Transitions `TESTED → HANDEDOFF` for `feature`/`architecture-change` (per state_machine.md). Writes `Current Phase: handoff` and a gate receipt to the Work Log.

> Canonical gate: `Ref: .agent/rules/state_machine.md`

## 1. Trigger Conditions

- Non-`tiny-fix`, Non-`quick-win`, Non-`hotfix`: MUST execute before pause, end, or handoff. AI should remind the user if this step is missing (see §10.6 Completion Guard).
- `hotfix`: Exempt from formal handoff (fast-path to `/ship` per `engineering_guardrails.md §10.2`); MUST provide evidence (diff + behavior verification).
- `quick-win`: Exempt from formal handoff, but AI SHOULD offer a brief `/retro`.
- `tiny-fix`: Exempt, but MUST retain minimal evidence.

## 1a. Phase Verification

**Phase Verification** (per bootstrap §2b): Read `Current Phase` from Work Log header. Verify transition to `handoff` is legal. If illegal, STOP. Otherwise update `Current Phase: handoff`. If a new commit was created since the last `Checkpoint SHA`, SHOULD refresh it.

**Uncommitted WIP guard**: If `Checkpoint SHA` is `none`, empty, or does not match `git rev-parse HEAD`, the agent MUST commit or `git stash` the WIP before completing handoff, then record the resulting SHA or stash ref in the Resume Block. Handing off with un-anchored WIP leaves the next agent unable to scope resume work via `git diff <checkpoint>..HEAD`.

**Interrupted handoff resume**: If the Work Log already contains a `## Resume` block from a prior partial handoff execution, DO NOT re-run from scratch. Instead:
1. Read the existing `## Resume` block and the `## Phase Summary` handoff line.
2. Identify what was already completed. A Resume Block is **complete** only if it contains ALL of the following sub-sections (per §3 template): `State`, `Completed`, `Next`, `Context` fields AND `### Read Map`, `### Skip List`, `### Context Snapshot`, plus `### Backlog Status` if a product backlog exists. If any sub-section is missing or empty, treat the block as partial.
3. Complete ONLY the missing sub-sections — append deltas to the Work Log.
4. Do NOT duplicate existing content. If all required sub-sections are present and the gate receipt exists, the handoff is already complete — proceed directly to the closure recommendation (§3a).

## 2. Platform Specialization

- **Antigravity / Codex App**: Auto-write Layer 2, Resume Block, and Gate Receipt to `.agentcortex/context/work/<worklog-key>.md`.
- **Codex Web** (no file-write capability):
  - Layer 1 TL;DR: output in chat (same as all platforms).
  - Layer 2 + Resume Block + Gate Receipt: MUST output each as a separate fenced code block in chat with the instruction "Paste the block above into `.agentcortex/context/work/<worklog-key>.md` under `## Phase Summary` / `## Resume` / `## Gate Evidence` respectively." Do NOT proceed to `/ship` until the user confirms the paste is done.
- If the active Work Log is missing, resolve or create the current `<worklog-key>` log first. If the previous log was archived after a prior ship, create a follow-up active log and note that recovery in the delta.

## 3. Required Output Blocks

Apply `AGENTS.md §Phase Output Compression → /handoff`.

**Chat response is Layer 1 ONLY (≤ 10 lines). Layer 2 and the Resume Block are written to the Work Log file — do NOT emit them in chat.**

- **Layer 1 (Handoff TL;DR, chat output, ≤ 10 lines)**:
  - Goal — 1 line
  - Current State — 1 line
  - Next Action — 1 line
  - Blocker — 1 line or `none`
  - Owner — name / agent id
  - Last Verified Command — 1 line
- **Layer 2 (Traceability, Work Log only — NOT chat)**: Done, In Progress, Blockers, Next, Risks, References. Append to Work Log `## Phase Summary` and related sections. If the user asks for the full traceability, expand.
- **Resume Block**: MUST be written to the Work Log file:

```markdown
## Resume
- State: [current state machine state]
- Completed: [list of done steps]
- Next: [immediate next action]
- Context: [1-2 sentence summary of what was decided and why]

### Read Map (for next agent)
Files the next agent MUST read:
- [file path] → [section or "full"]
- [file path] → [section or "full"]

### Skip List
Files the next agent can SKIP (already processed, no changes expected):
- [file path] — [reason: e.g., "already reviewed, no issues"]

### Context Snapshot (≤ 200 tokens)
[Compressed summary of current understanding: key decisions made,
 constraints discovered, patterns observed. Written so that the next
 agent can bootstrap without re-reading everything.]

### Backlog Status (if applicable)
- Active Backlog: [path or "none"]
- Current Feature: [name and status]
- Remaining: [count] pending, [count] deferred
- Next Recommended: [feature name or "user choice"]
```

**Gate Receipt**: After the Resume Block is written, append to Work Log `## Gate Evidence`:
```
- Gate: handoff | Verdict: PASS | Classification: <tier> | Timestamp: <ISO>
```
This makes the `TESTED → HANDEDOFF → SHIPPED` chain auditable — the validator's STRICT progression check (`test → handoff → ship`) can only fire when handoff emits this receipt.

> **Why Read Map + Skip List?** The biggest cross-session token waste is the next agent re-reading files the previous agent already processed. The Read Map tells it exactly where to look; the Skip List prevents redundant reads. Together they can cut handoff bootstrap tokens by 40-60%.

## 3a. Skill-Aware Handoff (Auto-Enforced)

Apply the Phase-Entry Skill-Loading Protocol (AGENTS.md §Phase-Entry Skill Loading) for all skills listing `/handoff` in their phases. Read `Recommended Skills` from the active Work Log before selecting which skill guidance to apply in this phase. Then apply each skill's handoff-specific expectations as additional summary requirements. Explicitly state: "Applying [skill-name] strategy for handoff."

**Reviewer-facing handoff (always applies for review-bound handoff):**
- Include reviewer-facing risk focus and any high-attention files in Layer 2.
- Provide a concise PR-style summary: Context (background/goals), Scope (affected files + boundaries), Validation (tests run + results), Risks (side effects + mitigations), Questions (specific reviewer focus).

**Branch closure recommendation (always applies):**
- State the current closure recommendation explicitly: **Merge now** (verified, risks acceptable) / **Open PR** (needs reviewer) / **Keep branch** (remaining work) / **Archive-Close** (canceled).
- If merge is NOT yet appropriate, say what remains before closure.

## 4. Minimum References (HARD GATE)

MUST include ALL of the following:

1. At least 1 docs/ file path
2. At least 1 code file path
3. Corresponding Work Log path (`.agentcortex/context/work/<worklog-key>.md`)
4. Gate receipt appended to Work Log `## Gate Evidence` (written in this §, after Resume Block)

If requirements unsatisfied, COMPLETION AND `/ship` ARE STRICTLY PROHIBITED.

## 4a. Phase Summary Update

Before writing handoff blocks, append a one-line summary for the current phase to `## Phase Summary`:

```markdown
- handoff: [1-line summary of what was handed off, key decisions, next action]
```

Each phase appends one compact result line. Later phases (and the next agent) can read `## Phase Summary` first to get a low-token overview before deciding whether to read the full log.

## 5. Work Log Writing Rule (Delta-Only)

- Append only what changed in this turn (delta log).
- DO NOT restate old background unless it is required for a decision or rollback.
- If context repeats, link to the previous section instead of re-writing full paragraphs.
- Preserve the runtime contract sections (`## Gate Evidence`, `## Task Description`, `## Phase Sequence`, `## Evidence`, `## External References`, `## Known Risk`, `## Conflict Resolution`, `## Skill Notes`). Update them incrementally; do not delete them during compaction.
- For `## Skill Notes` and `## Conflict Resolution`, "update incrementally" means appending new phase notes or new conflict decisions only. Do NOT rewrite, compress, or replace existing validated entries.

## 6. Work Log Compaction Trigger

Thresholds are defined in `.agent/config.yaml` §worklog. If either is hit (`max_lines` or `max_kb`), MUST compact the Work Log:

1. Keep `## Session Info`, latest `## Resume`, latest `## Risks`, and the latest N delta entries (see `keep_recent_entries` in config).
2. Move older details to `.agentcortex/context/archive/work/<worklog-key>-<YYYYMMDD>.md`.
3. Add one line in current log: `Compacted: [date], archive: [path]`.
4. Protected sections MUST remain in the active Work Log and MUST NOT be summarized, folded, or rewritten: `## Gate Evidence`, `## Skill Notes`, `## Conflict Resolution`, `## Evidence`, latest `## Resume`, `## Session Info`.

## 7. Token & Efficiency Reflection

If task was abnormally long or consumed high tokens, briefly explain why (e.g., "ambiguous specs", "bug loop"). Aids in continuous governance optimization.
