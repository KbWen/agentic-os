---
description: Workflow for importing external specs (from other LLMs, humans, or documents) into the AgentCortex governance system.
---
# /spec-intake

Accept an externally produced spec in any form and integrate it into the project governance system. The AI handles all organization and quality assessment — the user only needs to provide the raw material.

> **Design Intent**: Token-efficient handoff between a "spec-producing" LLM and an "implementing" agent. The spec may be large (full product spec) or small (single feature). The AI adapts automatically.

---

## 1. Receive Input

Accept spec from the user in ANY of these forms — do NOT ask the user to reformat:

- **Inline paste**: Raw text pasted into the conversation
- **File path**: `"Spec is at docs/specs/draft.md"` or similar
- **Natural language**: `"我要做一個 X，大概有 A、B、C 功能"`
- **Mixed**: Partial spec + verbal description

If the spec source is a file path, READ it immediately. Do NOT ask the user to paste it again.

---

## 1a. Context Budget: Persist Before Processing

**Problem**: A large spec (5K–50K+ tokens) pasted into conversation stays in context history permanently. As the conversation continues through bootstrap → plan → implement, the original spec blob competes for context window space, and context compression may silently discard critical details.

**Rule: Write first, think second.**

1. **Check for existing intake artifacts**:
   - If `docs/specs/_raw-intake.md` already exists, archive it to `docs/specs/_raw-intake-<date>.md` before writing the new one.
   - If `docs/specs/_product-backlog.md` already exists, warn: `"⚠️ Active backlog exists with [N] features. Merge new spec into existing backlog, or start a separate backlog?"` STOP until user decides.

2. **Immediately** write the raw input to `docs/specs/_raw-intake.md`:
   ```markdown
   ---
   status: raw
   title: Raw Spec Intake
   source: <inline-paste | file-path | natural-language>
   received: <date>
   ---

   <full original content, unmodified>
   ```
   - If input was a file path, copy the file content into `_raw-intake.md` so the original path can be ignored later.
   - If input was inline paste, write verbatim. Do NOT summarize or restructure at this stage.

3. **All subsequent steps read from `_raw-intake.md`**, NOT from conversation history.
   - Step 2 (Size Classification): `read docs/specs/_raw-intake.md`
   - Step 2a (Decomposition): read relevant sections of `_raw-intake.md`
   - Step 3 (Feature Spec Generation): read ONLY the section of `_raw-intake.md` relevant to the selected feature

4. **After decomposition is complete** (Feature Inventory saved to `_product-backlog.md` and at least one feature spec generated), `_raw-intake.md` MAY be deleted or archived. It has served its purpose — the structured specs are now the SSoT.

**Why this matters**:
- Conversation context stays lean: only the Feature Inventory table (~200 tokens) needs to be in active conversation, not the full spec
- Context compression can safely discard the original paste without data loss — everything is in files
- Cross-session resilience: if the user runs `/handoff` and starts a new conversation, the next session reads `_product-backlog.md` and individual specs, not a lost conversation blob
- Aligns with `context-budget.md` principle: minimize governance reads per turn

---

## 2. Size Classification

After reading the input, classify it as one of:

| Type | Signal | Path |
|---|---|---|
| **Single-feature spec** | One coherent goal, one set of ACs | → Step 3 (direct quality review) |
| **Multi-feature / product spec** | Multiple distinct features, epics, or modules | → Step 2a (decompose first) |
| **Vague / incomplete intent** | No clear goal or ACs | → Ask ONE targeted question, append answer to `_raw-intake.md`, then re-enter Step 2 |

### 2a. Decomposition (for multi-feature / product specs)

When the spec is large, read from `docs/specs/_raw-intake.md` (NOT from conversation memory):

1. Extract a **Feature Inventory** — one row per distinguishable feature/module:

   ```
   ## Feature Inventory (extracted from spec)
   | # | Feature | Rough Tier | Dependencies | Notes |
   |---|---|---|---|---|
   | 1 | User Auth | feature | — | OAuth + email |
   | 2 | Dashboard | feature | #1 | real-time data |
   | 3 | DB Schema | architecture-change | — | multi-tenant |
   ```

   Rough Tier uses classification from `engineering_guardrails.md §10.1`.

2. Save full product context to `docs/specs/_product-backlog.md` (see §6 for format).

3. **Present inventory to user and STOP**:
   ```
   Spec decomposed into [N] features. Which feature should we start with?
   (Reply with number or name — I'll generate the feature spec and run bootstrap.)
   ```

4. After user selects, proceed to Step 3 for **that feature only**.

---

## 3. Feature Spec Generation

Read ONLY the relevant section of `docs/specs/_raw-intake.md` for the selected feature (use offset/limit or targeted search — do NOT re-read the entire file).

**Cross-feature content dependency**: If the selected feature has dependencies (per Feature Inventory), also read the dependency's frozen spec for API contracts, data schemas, or interface definitions that the current feature must conform to. Read only the `## API / Data Contract` and `## Constraints` sections of the dependency spec — do NOT read the full file. Mark fields derived from dependency specs as `[FROM-DEPENDENCY: <spec-name>]`.

**Fallback (if `_raw-intake.md` was deleted)**: This happens during continuation (§8a) when the original raw spec was cleaned up after the first feature. In this case, generate the feature spec from: (1) `_product-backlog.md` Feature Inventory row + Source Summary, (2) any shipped feature specs as style reference, (3) dependency specs for API/contract alignment, (4) targeted questions if critical details are missing. Mark all non-obvious fields as `[INFERRED]`.

**Template Selection**: Before generating, check if an APP feature spec template exists:
1. Check `.agentcortex/templates/spec-app-feature-<project>.md` (project-customized template from /app-init)
2. If not found, check `.agentcortex/templates/spec-app-feature.md` (generic APP template)
3. If neither exists, use the default format below.

When an APP template is found, use it as the structure — include only the sections relevant to this feature (API, DB, Frontend, Auth). Remove sections that don't apply. Read the project ADR to determine which sections are applicable.

Generate `docs/specs/<feature-name>.md` using the selected template or the default `/spec` workflow output format:

```markdown
---
status: draft
title: <Feature Name>
source: external              ← marks this spec as externally sourced
source_doc: <origin ref>      ← e.g. _product-backlog.md or "user-provided"
created: <date>
primary_domain: <domain|none> ← when clearly inferable from the source or existing domain docs
secondary_domains: []
---

# <Feature Name>

## Goal
...

## Acceptance Criteria
1. [INFERRED] ...   ← mark fields inferred from context
2. ...

## Non-goals
...

## Constraints
...

## API / Data Contract
...

## File Relationship
INDEPENDENT | EXTENDS <existing-spec> | REPLACES <existing-spec>
```

**Tagging Rules**:
- `[INFERRED]` — AI derived this from context, not stated explicitly in source
- `[NEEDS-CONFIRMATION]` — required field but source was ambiguous
- `[FROM-SOURCE]` — directly stated in the source spec (no inference)

**Domain Doc L1 conflict check**:
- If the generated spec declares `primary_domain` and `docs/architecture/<primary_domain>.md` exists with `status: living`, read that L1 before freeze.
- Treat external source assumptions as candidate inputs, not authority. If the generated spec contradicts the L1 current design, surface the conflict in the Spec Review Report and require confirmation before freeze.

---

## 4. Quality Assessment

After generating the spec, run quality check and output a **Spec Review Report**:

```
## Spec Review Report: <feature-name>

✅ Confirmed (directly from source):
- Goal: clear
- AC #2, #3: verifiable

⚠️ Inferred (AI-derived — please confirm):
- AC #1: [INFERRED] assumed X because source said Y
- Constraints: [INFERRED] assumed no mobile support based on scope

⚠️ L1 conflict check:
- Existing Domain Doc for <primary_domain>: aligned | conflicting | none
- If conflicting: external source stays input-only until the user confirms the divergence

❌ Missing (cannot proceed without):
- (none)

Quality Tier: READY | NEEDS-ADJUSTMENT | INCOMPLETE
```

| Quality Tier | Meaning | Next Action |
|---|---|---|
| **READY** | All required fields present, no critical inference | → Step 5 (confirm & freeze) |
| **NEEDS-ADJUSTMENT** | Some `[INFERRED]` or `[NEEDS-CONFIRMATION]` fields | → Ask targeted questions (max 3, batched) |
| **INCOMPLETE** | Critical fields missing, cannot proceed | → Targeted Q&A, then regenerate spec |

**Targeted Q&A Rules**:
- Batch all questions into ONE message — never ask one at a time
- Maximum 3 questions per round
- Maximum 2 Q&A rounds total. If still `INCOMPLETE` after 2 rounds, escalate: `"⚠️ Spec remains incomplete after 2 rounds of Q&A. Options: (1) proceed with [INFERRED] fields marked, (2) defer this feature, (3) provide additional source material."`
- Ask ONLY about `❌ Missing` and high-risk `[NEEDS-CONFIRMATION]` fields
- Do NOT ask about non-goals, nice-to-haves, or already-clear fields

---

## 5. Confirm & Freeze

After user confirms (any affirmative response):

1. Remove all `[INFERRED]` / `[NEEDS-CONFIRMATION]` tags (incorporate answers)
2. Set `status: frozen` in frontmatter
3. If multi-feature: update `_product-backlog.md` Feature Inventory `Spec File` column to point to the frozen spec. (Spec Index in `current_state.md` is updated during `/ship` per Write Isolation rules.)
4. Output confirmation:
   ```
   ✅ Spec frozen: docs/specs/<feature-name>.md
   Ready to bootstrap. Proceed? (yes/no)
   ```

---

## 6. Product Backlog Format (`docs/specs/_product-backlog.md`)

```markdown
---
status: living          ← never frozen; updated as features are selected
title: Product Backlog
source: <origin>
created: <date>
last_updated: <date>
---

# Product Backlog

## Source Summary
<1-3 sentence summary of the original product spec>

## Feature Inventory
| # | Feature | Spec File | Tier | Status | Dependencies |
|---|---|---|---|---|---|
| 1 | User Auth | docs/specs/user-auth.md | feature | In Progress | — |
| 2 | Dashboard | — | feature | Pending | #1 |
| 3 | DB Schema | — | architecture-change | Pending | — |

## Status Key
- Pending: not yet started
- In Progress: spec generated, bootstrap running
- Shipped: feature shipped (see Ship History in current_state.md)
- Deferred: explicitly deferred
```

Update this file each time a feature moves status.

---

## 7. Hand Off to Bootstrap (Lite)

After spec is frozen, run `/bootstrap` with these pre-filled values (skip re-deriving them):

- Spec path: already known from Step 3
- Task classification: derived from Feature Inventory tier
- Goal / AC / Constraints: read from frozen spec

Bootstrap Step 2a (Spec Scope) MUST reference the frozen spec file. It does NOT re-generate the spec.

**If user confirms proceeding**: output "Spec intake complete. Proceeding to bootstrap." then run `/bootstrap`. This is the ONE exception to the general rule that each phase waits for user input — spec-intake-to-bootstrap is a single continuous handoff because the user already confirmed the spec.

---

## 8. Feature Lifecycle (Continuation, Amendment, Reorder)

After the first feature is shipped, the product backlog becomes the long-term coordination point. This section defines how subsequent features are selected, how specs evolve, and how errors decrease over time.

### 8a. Continuation: Selecting the Next Feature

**Trigger**: User says "next feature", "下一個", "繼續", or any intent indicating continuation of multi-feature work.

**Flow** (skips decomposition — already done):

```
AI reads _product-backlog.md (~200 tokens)
    ↓
Shows remaining Pending and Deferred features with dependency status:
  "Pending: #2 Dashboard (blocked by #1 ✅), #3 DB Schema (ready)
   Deferred: #4 Notifications (deferred — say 'un-defer #4' to resume)"
    ↓
User selects → AI runs Step 3 (feature spec generation)
    ↓
Normal flow: spec → freeze → bootstrap → plan → implement → ship
    ↓
/ship updates _product-backlog.md: feature status → Shipped
```

**Token savings**: No re-read of `_raw-intake.md` or full product spec. Backlog table is the only input (~200 tokens). Each subsequent feature costs LESS context than the first because:
- Shipped feature specs are frozen reference → skip unless explicitly needed
- Backlog narrows → fewer rows to evaluate
- Lessons from prior features accumulate in Work Log / Global Lessons

**Dependency check**: Before generating a feature spec, verify all dependencies are `Shipped` or `In Progress`. If blocked, warn: `"⚠️ Feature #N depends on #M which is still Pending. Proceed anyway or pick another?"`

### 8b. Spec Amendment (Changing an Existing Spec)

Specs will change. How they change depends on when:

| Timing | Spec Status | Action |
|---|---|---|
| **Before implementation** | `draft` | Edit directly. No ceremony needed. |
| **During implementation** | `frozen` | Unfreeze per §4.2 (user approval required), edit, refreeze. Update Work Log: `"Spec amended: [reason]"`. |
| **After shipping** | `frozen` (shipped) | Do NOT modify the old spec. Create a NEW spec with `File Relationship: EXTENDS <old-spec>`. The old spec stays as historical reference. |

**Why not modify shipped specs?** Shipped specs are reference documents. They answer "why was it built this way?". Modifying them after the fact destroys traceability. Instead:

```
Original: docs/specs/user-auth.md [Frozen] [Shipped]
    ↓ user wants to add SSO
Amendment: docs/specs/user-auth-sso.md [Draft]
  └─ File Relationship: EXTENDS docs/specs/user-auth.md
```

**Backlog update**: If the amendment is significant enough to be a new feature, add it to `_product-backlog.md` as a new row.

### 8c. Reorder, Defer, Cancel

| Action | Trigger | What AI does |
|---|---|---|
| **Reorder** | "先做 #5" | Update `_product-backlog.md` order. Check dependency conflicts. |
| **Defer** | "先不做 #3" | Set status → `Deferred` in backlog. If spec was already generated, leave it as `draft` (not frozen). |
| **Un-defer** | "恢復 #3", "un-defer #3" | Set status → `Pending` in backlog. If spec exists as `draft`, it remains usable. |
| **Cancel** | "不做 #3 了" | Set status → `Cancelled` in backlog. If spec exists, add `status: cancelled` to frontmatter. Remove from Spec Index. |
| **Merge** | "把 #2 和 #3 合成一個" | **Pre-check**: If any source feature is `In Progress` or has a Work Log, warn: `"⚠️ #N is in progress with existing work. Merge will require re-bootstrap. Proceed?"`. Create new combined spec. Old specs get `File Relationship: REPLACED-BY <new>`. Archive affected Work Logs. Update backlog. |
| **Split** | "把 #2 拆開" | **Pre-check**: If feature is `In Progress`, warn: `"⚠️ #N is in progress. Split will require re-bootstrap for both new features. Proceed?"`. Create two new specs. Old spec gets `REPLACED-BY <new-a>, <new-b>`. Archive affected Work Log. Update backlog with new rows. |

### 8d. Cross-Feature Learning (Error Reduction Over Time)

Each shipped feature produces lessons (via `/retro` → Work Log `## Lessons` → `current_state.md` Global Lessons). These lessons compound:

```
Feature #1: ship → lesson: "API contract needs explicit error codes"
Feature #2: bootstrap reads Global Lessons → AI applies lesson to spec generation
Feature #3: fewer [NEEDS-CONFIRMATION] tags because AI has learned the project's patterns
```

**Spec quality improves over time** because:
1. Each feature spec generation references Global Lessons from prior features
2. The AI's `[INFERRED]` accuracy improves as more project context exists
3. Shipped specs serve as pattern references for new specs (same style, same depth)

**Rule**: When generating a spec for feature N, AI MUST read `current_state.md` Global Lessons AND check ONE shipped feature spec (most similar to current feature) as a style reference. Cost: ~100 extra tokens. Value: significantly fewer amendment cycles.

### 8e. Product Lifecycle Phases

| Phase | Backlog State | Spec Behavior | Token Profile |
|---|---|---|---|
| **Early (0-30% shipped)** | Mostly Pending | Frequent amendments, reorders common, specs are rough | Higher — more Q&A, more inference |
| **Mid (30-70% shipped)** | Mixed | Dependencies surface, cross-feature issues emerge, amendments to frozen specs | Medium — lessons reduce inference |
| **Late (70-100% shipped)** | Mostly Shipped | Bug fixes (EXTENDS), refinements, scope trimming | Lower — patterns established, specs stable |

**AI behavior adapts by phase**:
- **Early**: Expect spec changes. Be lenient on [INFERRED] fields. Ask more questions upfront.
- **Mid**: Flag dependency conflicts proactively. When amending a frozen spec, check if downstream features are affected.
- **Late**: Default to `EXTENDS` for any changes. Discourage scope expansion. Focus on completion.

---

## Hard Rules

1. **Burden on AI**: The user must never be asked to reformat, restructure, or pre-process the spec.
2. **One feature at a time**: Even for large product specs, only ONE feature enters the implementation workflow at a time.
3. **Draft before frozen**: Spec MUST start as `status: draft`. Never write `status: frozen` before user confirmation.
4. **Backlog is living**: `_product-backlog.md` is never frozen. It is updated throughout the product lifecycle.
5. **Conflict check**: Before writing a new spec, check `current_state.md` Spec Index for existing specs that overlap. If overlap found, output: `⚠️ Existing spec [file] may overlap. Extend, replace, or keep independent?`
6. **`living` status**: `_product-backlog.md` uses `status: living` in frontmatter. This is a distinct status from `draft`/`frozen` — it signals a persistent tracking document that MUST NOT be frozen or treated as a spec artifact by §4.2 Spec Freezing rules. AI MUST NOT attempt to freeze or review `living`-status documents for freeze compliance.
7. **`raw` status**: `_raw-intake.md` uses `status: raw` in frontmatter. This is a temporary artifact — unprocessed input that exists only until decomposition is complete. It is NOT a spec and MUST NOT appear in the Spec Index. Delete or archive after all relevant feature specs are generated.
8. **`cancelled` status**: Set by §8c Cancel action. A cancelled spec is permanently inert — it MUST NOT appear in the Spec Index, MUST NOT be read during bootstrap Spec Scope, and MUST NOT be frozen or unfrozen. It exists only as historical record.
