---
name: decide
description: Record important decisions with reasoning to prevent redundant re-derivation across sessions.
tasks:
  - decide
---

# /decide

Lightweight decision-recording protocol. Designed to reduce token waste from agents re-reasoning the same problem across sessions.

> Canonical gate: `Ref: .agent/rules/engineering_guardrails.md` §6 (Explainability & Traceability)

## 1. When to Record a Decision

A decision MUST be recorded when ANY of the following apply:

- **Trade-off made**: Two or more viable approaches existed; one was chosen.
- **Constraint discovered**: A limitation was found that narrows future options.
- **Scope boundary set**: Something was explicitly excluded (non-goal).
- **Tool/library/pattern chosen**: A specific implementation approach was selected over alternatives.
- **Assumption validated or invalidated**: A hypothesis was tested and resolved.

A decision SHOULD NOT be recorded for:

- Obvious choices with no alternatives (e.g., "fixed the typo").
- Choices already documented in a Spec or ADR.
- Per-line code decisions (those belong in code comments if needed).

## 2. Decision Entry Format

Append to the Work Log under `## Decisions`:

```markdown
## Decisions

### D-[N]: [Short title]
- **Decision**: [What was decided — 1 sentence]
- **Reason**: [Why — the key factor that tipped the balance]
- **Alternatives**: [What was considered and rejected — 1 line each]
- **Impact**: [What this constrains going forward — 1 sentence]
```

Rules:
- Each entry ≤ 5 lines. Brevity is critical — verbose decisions defeat the purpose.
- Number decisions sequentially (D-1, D-2, ...) within a Work Log session.
- If a decision reverses a previous one, reference it: `Reverses D-[N]: [reason]`.

## 3. Classification-Specific Behavior

| Classification | Decision Recording |
| --- | --- |
| `tiny-fix` | SKIP — no decisions expected |
| `quick-win` | OPTIONAL — record only if a non-obvious choice was made |
| `feature` | SHOULD — record 1-3 key decisions per session |
| `architecture-change` | MUST — record all trade-offs; these feed into ADRs |
| `hotfix` | SHOULD — record root cause determination and fix approach |

## 4. How Next Agent Uses Decisions

During `/bootstrap`, if a Work Log contains `## Decisions`:

1. Read the Decisions section BEFORE planning.
2. Do NOT re-evaluate settled decisions unless new evidence contradicts them.
3. If new evidence arises, record a new decision that references and reverses the old one.

This prevents the most common cross-session token waste: Agent B spending 500+ tokens re-deriving a conclusion Agent A already reached.

## 5. Promotion to ADR

If a decision has project-wide impact (affects multiple branches, modules, or future tasks), it SHOULD be promoted to a formal ADR during `/ship`:

1. Copy the decision entry to `docs/adr/ADR-[ID]-[kebab-case].md`.
2. Expand with full ADR structure (Context, Decision, Consequences).
3. Add to `current_state.md` ADR Index.
4. Remove from Work Log Decisions section (replace with pointer: `→ Promoted to ADR-[ID]`).

## 6. Compaction Rule

During Work Log compaction (§6 of `/handoff`):

- Keep ALL decisions from the current session.
- Archive decisions from prior sessions (they are in the archived Work Log).
- Exception: Decisions referenced by the latest `## Resume` block MUST be retained.
