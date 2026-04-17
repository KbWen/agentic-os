---
name: plan
description: Outputs actionable plan & enforces quality gates. Transitions state to IMPLEMENTABLE.
tasks:
  - plan
---

# /plan

> Canonical state & transitions: `Ref: .agent/rules/state_machine.md`

NO CODING YET. Planning phase ONLY.

## Gate Engine (Turn 1 — Antigravity Hard Path)

Before producing ANY plan content, output the Minimal Gate Block:

```yaml
gate: plan
classification: <from Work Log>
branch: <current branch>
checks:
  worklog_exists: yes|no
  spec_exists: yes|no|na
  state_ok: yes|no
verdict: pass|fail
missing: []
```

- If `verdict: fail` → output ONLY the gate block with populated `missing` list. STOP.
- Evaluate `worklog_exists` only after resolving the active Work Log path for the current `<worklog-key>`.
- If the active Work Log is missing but recoverable, create or recover it, warn the user, and continue. Only unresolved Work Log lookup failures should set `verdict: fail`.
- **Phase Verification** (per bootstrap §2b): Read `Current Phase` from Work Log header. Verify transition to `plan` is legal. If illegal, STOP. Otherwise update `Current Phase: plan`.
- If classification is `feature` or `architecture-change`:
  - If the user explicitly requested planning or gave an unambiguous request that already implies this phase, proceed directly to plan output in the same turn.
  - Only ask for an extra confirmation if phase entry was inferred rather than explicitly requested, or if planning surfaces a separate high-impact decision that needs human choice.
- If classification is `quick-win` or `hotfix`:
  - Proceed directly to plan output.

## Gate Evidence Receipt

After outputting the gate block, append a compact gate receipt to the Work Log under `## Gate Evidence`:

```markdown
- Gate: plan | Verdict: pass | Classification: <tier> | At: <ISO-timestamp>
```

If `verdict: fail`, the receipt records the failure and missing items. This makes gate progression auditable by `validate` without requiring a runtime hard blocker.

## Pre-Conditions (Existing)

- **Spec Gate**: If task classification is `feature` or `architecture-change`:
  - MUST have a corresponding `docs/specs/<feature>.md` with `status: draft` or `status: frozen`.
  - If no spec exists: STOP. Output: "⚠️ No specification found. Run `/spec` first."
- `tiny-fix`, `quick-win`, and `hotfix` are EXEMPT from this gate.

## Pre-Plan Advisory Suggestions (Advisory — never blocks)

> **Output format**: Single compact line. Emit ONLY when ≥1 condition triggers; emit NOTHING otherwise. Full reasoning goes to Drift Log, not chat.
> **Template**: `Advisory: <item1> · <item2> · <item3> — reply skip/accept-<n>`

Trigger conditions (check silently; emit only matches):
- Classification `feature` or `architecture-change` + no `/brainstorm` or `/research` phase in Work Log → `/brainstorm (no exploration)`
- Plan step selects a tech stack component (language, framework, database, infrastructure) → `/adr (tech choice)`
- Plan step reveals a design fork (two valid approaches, OR/Either in step descriptions) → `/decide (design fork)`

Skip → record reason in `## Drift Log` as `Skipped: <advisory> — <1-line reason>`. No reason required beyond 1 line.

## Design Gate (UI Tasks — Auto-Enforced)

> Ref: `engineering_guardrails.md` §4.4 — Design-First Rule

If the planned changes modify **user-visible UI** (screens, components, layouts, styling, navigation):

1. **DSoT Link Required**: The plan MUST include a `Design: <URL or file path>` entry pointing to the approved design in the project's Design Source of Truth tool (Stitch, Figma, Pencil, etc.).
2. **No Link = Plan Incomplete**: If no design link is provided, verdict is **fail** with `missing: [design_link]`. Agent MUST stop: "⚠️ UI changes planned but no design link provided. Create or link the design in [DSoT tool] before planning can complete."
3. **Design Scope Coverage**: Every UI-affecting step in the plan MUST reference which screen/component in the DSoT it implements. Orphan UI steps (no DSoT mapping) = plan quality gate fail.

**Exempt**: `tiny-fix`, backend-only changes, CLI tools, infrastructure, or non-visual config changes.

When the design link is present, record in the Work Log under `## Design Reference`:
```markdown
## Design Reference
- Tool: stitch|figma|pencil|other
- Link: <URL or file path>
- Approved: yes|pending
- Coverage: [list of screens/components mapped to plan steps]
```

## External References Gate

If the plan depends on a repo-external library, external API, package manager change, or unfamiliar platform capability:

1. Run `/research` first or verify equivalent official references already exist in the active Work Log.
2. Record them in `## External References` using authoritative sources only.
3. If the section is empty or `none`, planning MUST flag the gap and stop before `/implement`.

## Skill-Aware Planning (Auto-Enforced)

Apply the Phase-Entry Skill-Loading Protocol (AGENTS.md §Phase-Entry Skill Loading) for all skills listing `/plan` in their phases. Read `Recommended Skills` from the active Work Log before selecting which skill guidance to apply in this phase. Then apply planning-specific constraints from those skills when shaping steps, verification, and rollback.

**IF `writing-plans` is active:**
- Use the skill's plan structure as the default plan skeleton.
- Keep every step independently verifiable and revertible.

**IF `database-design` is active:**
- Include migration safety, rollback shape, and schema verification in the plan.

**IF `auth-security` is active:**
- Include auth/permission risk checks and security verification in the plan.

## Expected Output Format

Apply the shared `Phase Output Compression` contract from `AGENTS.md §Phase Output Compression → /plan`.

**Chat response is the compact block below. NO section headers when the whole plan is < 15 lines. NO re-narration of the spec or task description.**

```
Target Files: <comma list>
Steps:
  1. <action> — verify: <1-line method>
  2. <action> — verify: <1-line method>
  ...
Risk+Rollback: <1-line risk> / <1-line rollback>
AC Coverage: AC-1→step-N, AC-2→step-M, ...
Non-goals: <comma list or "none">
Confidence: <N>% — <rationale if <90%, else "high">
Mode: Normal | Fast Lane
⚡ ACX
```

> **Confidence field** (Ref: `engineering_guardrails.md` §4.1): Always output the number. If `<80%`, this gate is auto-fail — STOP and clarify. `80–90%` means state the assumption explicitly on this line. `>90%` may render as `Confidence: 95% — high` without extended rationale. This keeps the gate auditable in the Work Log even when confidence is high.

Rules:
- Each step MUST be **Functionally Atomic** — one logical unit of change (e.g., "Implement Data Schema"), NOT a 2-paragraph explanation.
- Each step MUST have a 1-line verification method (test command, grep, or logic check). No 3-bullet sub-checklists per step.
- List ONLY files being modified (prevent scope creep).
- Detail that belongs in the Work Log (cited spec sections, rejected alternatives, design doc links) goes to `## Risks` and `## External References` sections of the Work Log — NOT the chat block. Reference by `Ref: Work Log §<section>`.
- If the user asks for more detail, expand. Default is terse.

## Quality Gates (ALL MUST PASS)

- Every AC MUST map to at least 1 step.
- Step granularity: Module/File/Function level.
- MUST identify at least 1 Risk + viable Rollback.
- List ONLY files being modified (Prevent scope creep).
- MUST explicitly cite documentation (e.g., `Ref: docs/specs/auth.md`).
- **Frozen Spec Pre-Check**: Cross-reference target files against Spec Index entries tagged `[Frozen]`. If any target file falls under a Frozen Spec, warn immediately: "⚠️ [file] is governed by Frozen Spec [spec-name]. Unfreeze required before proceeding. Approve? (yes/no)"

## Spec Feedback Loop

- If planning reveals that the Spec's AC, constraints, or boundaries need adjustment:
  1. STOP planning.
  2. Surface: "⚠️ Spec adjustment needed: [reason]. Returning to `/spec`."
  3. Apply §4.2 Unfreeze protocol if spec is frozen.
  4. Update `docs/specs/<feature>.md`, then resume `/plan`.
- The Plan MUST NOT contradict the Spec. If there's a conflict, Spec wins.

## Work Log Update (Mandatory)

After plan is approved, AI MUST append to the current Work Log:

```markdown
## Risks (from /plan)
- [Risk 1]: [brief description + mitigation]
- [Risk 2]: ...
- [Risk 3]: ...

## External References
- [Official doc / API / package release note] | [why it is needed]
```

This block persists across sessions. On resume, /bootstrap reads it immediately.

## Token Budget Checkpoint

- Plan MUST include `Mode: Normal` or `Mode: Fast Lane`.
- If task is small but output balloons, MUST switch to `Fast Lane` using summarization next turn.
- Detailed rules: `Ref: .agentcortex/docs/guides/token-governance.md`.

## Phase Summary Update

After plan is approved, append one line to `## Phase Summary` in the Work Log. **MUST include the `Confidence:` value** so `/ship`'s Confidence Trace Audit can read it from a persistent location (the chat-only compact block is ephemeral across sessions):

```
- plan: [1-line summary — key decisions, target files count, mode Normal/Fast Lane] | Confidence: <N>% — <high | 1-line rationale>
```

## State Transition

- Upon passing gates, state transitions from `PLANNED` to `IMPLEMENTABLE`.
- Automatically offer `/test-skeleton` in the same turn.
- Do not emit an extra "gate passed, waiting" line when the user already asked for planning; output the gate block and plan back-to-back.
