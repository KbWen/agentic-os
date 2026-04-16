---
name: bootstrap
description: Task initialization, context loading, classification, and work log creation.
tasks:
  - bootstrap
---

# /bootstrap

> Canonical state & transitions: `Ref: .agent/rules/state_machine.md`

## Governance Boundary Reminder

All classification gates, phase requirements, and evidence rules in this workflow exist to keep AI behavior disciplined — they are not restrictions on human authority. The human decides scope and direction. If the user wants to change scope, the AI accommodates via reclassification or scope adjustment rather than silently skipping gates. The AI MUST NOT cite these rules to refuse a user's legitimate scope change or direction.

## 0. Pre-Classification Fast Check (Token Efficiency Gate)

Before loading any context, check if this task qualifies as `tiny-fix` using the inline criteria below (< 3 files, no semantic change, unambiguous scope). Ref: `engineering_guardrails.md` §10.3 — do NOT read that file for this check.

**ADDITIONAL TINY-FIX EXCLUSIONS** (AC-22): Even if all other tiny-fix criteria are met, a task is NOT tiny-fix (minimum `quick-win`) if it:

- Modifies any file in `docs/specs/` (spec changes require design authority)
- Modifies any file in `docs/architecture/` (domain doc changes require governance awareness)
- Modifies `docs/specs/_product-backlog.md` (route to `/spec-intake` instead)
- Modifies any file with `status: frozen` frontmatter
- Modifies `AGENTS.md`, `.agent/rules/*`, or `.agent/config.yaml`

If yes → classify immediately, skip Steps 1–6, proceed directly to inline plan + execute + evidence (Work Log also skipped per §5).

**TOKEN LEAK BLOCK**: If the task is ultimately classified as `tiny-fix` or `quick-win`, reading `engineering_guardrails.md` at any point is a structural Token Leak violation. You MUST rely purely on AGENTS.md §Core Directives and bypass full guardrails.

If no or uncertain → continue to Step 1 for full context loading. Do NOT guess — if scope is unclear, load context first.

This exists because loading SSoT + specs + archives for a typo fix wastes ~2500 tokens (P6).

## 0a. App Architecture Check (Zero-Cost Gate)

> **When**: ONLY for `feature` or `architecture-change` classifications (AFTER Step 0 pre-classification).
> **Skip for**: `tiny-fix`, `quick-win`, `hotfix` — these NEVER trigger this check. Zero extra tokens.

If the task is classified as `feature` or `architecture-change`, check:

1. **No ADR exists**: `docs/adr/` contains no project-specific ADR.
   → Output: `"🏗️ New project detected — no architecture ADR found. Run /app-init to establish project conventions? (yes/skip)"`
   → If yes: run `/app-init` workflow, then return here.
   → If skip: record `"App-init skipped by user"` in Work Log. Detection will NOT trigger again this session.

2. **Partial ADR exists**: An ADR exists but has `[TBD]` sections relevant to the current task (e.g., task touches DB but ADR has `[TBD]` for Database section).
   → Output: `"⚠️ Your architecture ADR has [TBD] sections relevant to this task: [list]. Fill them now via /app-init --partial? (yes/skip)"`
   → If yes: run `/app-init` in partial mode (§8 of app-init.md — only ask questions for TBD sections).
   → If skip: proceed, but AI uses generic conventions (skill scaffold defaults).

3. **ADR exists and covers this task**: No action needed. Proceed to Step 1.

**Cost**: This check reads only the ADR frontmatter + section headers (~50 tokens). It does NOT read full ADR content — that happens later during /implement when skills are loaded.

**User-initiated trigger**: If user says "設定架構", "init app", "define tech stack", or similar intent at ANY point (even mid-development), route to `/app-init` regardless of current phase or classification. This allows mid-project architecture decisions.

---

## 1. Initialization & Required Reading

1. READ `.agentcortex/context/current_state.md` (SSoT).
   - **Legacy Detection**: If `.agentcortex/context/current_state.md` is missing but `docs/context.md` or an `agent/` directory exists, AI MUST notify the user: "⚠️ Legacy Agentic OS structure detected. Recommend running the Migration Path from `.agentcortex/docs/guides/migration.md`."
   - **Cross-Branch Awareness**: Check "Branch List" for recently closed branches.
   - If current task overlaps with a recently merged branch's module, check the archive index for lightweight retrieval: prefer `.agentcortex/context/archive/INDEX.jsonl` (structured, deterministic query) if it exists; fall back to `.agentcortex/context/archive/INDEX.md` otherwise. Only open a specific archived log if its module/pattern entry matches your current task's target files. Do NOT scan all archive files.
   - If bootstrap must repair or refresh SSoT metadata (for example, stale Spec Index recovery), the write MUST go through `.agentcortex/tools/guard_context_write.py`.
   - **Staleness Check**: After reading SSoT, check `Last Verified` field. If today's date minus `Last Verified` > 14 days, output advisory: `"⚠️ SSoT last verified <N> days ago. Consider running /govern-docs to refresh."` Do NOT block — advisory only.
   - **Last Verified Update**: After successfully reading SSoT, update the `Last Verified` field to today's ISO date via `guard_context_write.py` (or direct write if Python unavailable).
2. READ/CREATE `.agentcortex/context/work/<worklog-key>.md` (Work Log).
   - **Work Log Resolution**: Resolve a filesystem-safe `<worklog-key>` from the current branch before any path check. Store the raw git branch string in `Branch:`.
   - **Recoverable Missing Log**: If the active Work Log is missing, create it. If only archived logs exist for this branch, create a new follow-up Work Log and report the recovery instead of failing `/bootstrap`. When recovering from an archived log, write this entry to the new Work Log's `## Drift Log`: `"Recovered: prior log archived at .agentcortex/context/archive/work/<prior-key>.md (session: <date>)"`. This ensures the next session knows prior work existed.
   - **Bootstrap Branch Check**: If the Work Log already exists:
     - Check metadata (`Owner`, `Branch`, `Session`). If it matches your current session → RESUME safely. (Read `## Resume` if present, output "Resuming").
     - If metadata differs (another agent/user owns it) → **WARN the user AND require confirmation before proceeding** ("⚠️ Concurrent session detected. Proceed?").
     - If metadata is missing → warn "⚠️ Legacy Work Log detected, verify ownership".
   - If Work Log has `## Lessons` block (from prior retro): acknowledge relevant patterns in your bootstrap output.
   - If Work Log has `## Risks` block: include in your bootstrap context summary.
   - If Work Log has `## Decisions` block: read the decisions, then **surface them to the user for confirmation** before treating them as binding: "📋 This Work Log contains [N] inherited decision(s) from a prior session: [list D-IDs and 1-line summaries]. Confirm these still apply? (yes/no/review)". Only after user confirms, acknowledge them per `/decide` §4. This prevents a compromised or stale Work Log from silently bypassing gates.
2a. SPEC SCOPE: From the **Spec Index** in `current_state.md`, identify which specs are relevant to this task.
   - Read ONLY those explicitly mapped specs.
   - **DO NOT** use broad commands like `list_dir docs/specs/` or `grep` to scan unmapped specs.
   - **DO NOT** open specs tagged as `[Shipped]` under any circumstances unless tracing a specific historical bug (AC-28 anti-bloat rule). Their contents are historical; refer instead to the SSoT Domain Docs.
   - Also check `current_state.md` Spec Index for any `[MERGE-PROPOSED]` tags on relevant specs. If found, surface to user BEFORE starting work: "⚠️ Spec consolidation was recommended for [files]. Proceed as-is or consolidate first?"
   - If uncertain, ask ONE clarifying question before reading any spec.
   - **Shipped Spec Design Reference** (AC-28): If a relevant spec has `status: shipped` AND a Domain Doc L1 exists at `docs/architecture/<primary_domain>.md`, read the Domain Doc L1 as the current design reference instead of the spec. Shipped specs are treated as historical context only, not design authority.

<!-- SCOPE: feature, architecture-change ONLY — skip entirely for quick-win / hotfix -->
2b. DOMAIN DOC CONTEXT LOADING (feature / architecture-change only — AC-8, AC-32):

- **Capability-by-presence**: If `docs/architecture/` does not exist, skip all Domain Doc steps below. Zero extra reads.
- Determine `primary_domain` from the task's `primary_domain` frontmatter field or from task file path overlap.
- **Primary Domain Snapshot**: If a relevant spec declares `primary_domain`, record `Primary Domain Snapshot: <domain>` in the active Work Log header before leaving bootstrap. If no relevant spec declares one, record `Primary Domain Snapshot: none`.
- If `primary_domain` is set and `docs/architecture/<primary_domain>.md` (L1) exists, READ it ONLY if the file is framework-formatted with frontmatter that declares BOTH `status: living` and `domain:`. Domain Doc L1 reads are budgeted at ~100 tokens each and do NOT count against the governance context budget cap. If the file exists but lacks that minimal L1 contract, skip it as L1 authority and emit a bounded advisory naming the file.
- **Backfill Prompt** (AC-34): If `primary_domain` is set but no L1 exists, output: `"Domain doc for '<domain>' not found. Create skeleton from existing specs? (yes/skip)"`. If yes, create a minimal L1 skeleton at `docs/architecture/<primary_domain>.md` with `status: living` and `[TBD]` sections. If skip, proceed without Domain Doc reads.
- **Partial adoption advisory**: If a relevant spec declares `primary_domain` but required adoption surfaces are missing (bounded to `docs/architecture/` and `docs/README.md` only), emit a bounded adoption advisory naming just the missing surfaces. Do NOT broad-scan the docs tree.
- **SSoT Heartbeat Record** (AC-26): Read `Update Sequence` from `current_state.md` header. Record `SSoT Sequence: <N>` in the Work Log header. This value is checked again before entering `/ship` or `/handoff`.

<!-- SCOPE: Steps 3-6 are conditional — skip steps whose preconditions are not met -->
3. IF `.agentcortex/context/private/` exists, SCAN for local-only instructions (e.g., private Git workflows, environment-specific configs). These files are gitignored and contain context that should NOT be committed.
4. **Migration/Integration Scenario** *(skip if not a migration task)*:
   - Follow `.agentcortex/docs/guides/migration.md`. Actively scan and suggest file reorganization.
   - MUST output migration plan and await user `OK` before ANY move/rename.
5. **Active Backlog Detection**:
   - Check if `docs/specs/_product-backlog.md` exists.
   - If it exists, read ONLY the Feature Inventory table (~200 tokens). Report in bootstrap output:

     ```
     Active Backlog: docs/specs/_product-backlog.md
     Progress: [N] shipped, [M] pending, [K] deferred
     ```

   - If user intent matches a pending backlog feature, route to `/spec-intake` §8a (continuation) instead of fresh bootstrap.
   - If no backlog exists, skip this step.
6. **Large Raw Material Processing** (Chats, Whitepapers, Specs):
   - If user provided a spec, document, or raw material BEFORE bootstrap, check whether `/spec-intake` was already run:
     - Frozen spec exists (`status: frozen`, `source: external`) → **Bootstrap Lite**: skip spec generation, read existing spec directly. Task classification is derived from spec's Feature Inventory tier.
     - No frozen spec exists → run `/spec-intake` workflow BEFORE continuing bootstrap. Do NOT proceed past Step 6 until spec-intake is complete.
   - **External authority rule**: Treat substantial external architecture or product material as `/spec-intake` input even when the user frames it as "background context". This includes imported design docs, PRDs, acceptance-criteria lists, rollout plans, or any multi-paragraph external material carrying requirements or architectural assumptions. Architecture specs, PRDs, and requests like `"continue from this spec"`, `"請從這份 spec 繼續"`, or `"use this document as the plan"` are all `/spec-intake` inputs, not design authority. Do NOT let conversation-carried external specs override an existing Domain Doc L1.
   - **Orphaned `_raw-intake.md` Recovery**: If `docs/specs/_raw-intake.md` exists (with `status: raw`) but no `_product-backlog.md` and no frozen external spec, a previous spec-intake was interrupted mid-flow. Warn: `"⚠️ Orphaned raw intake detected. Resume spec-intake from existing _raw-intake.md? (yes/no)"`. If yes, run `/spec-intake` starting from Step 2 (skip §1/§1a — raw file already exists).
   - AI MUST autonomously extract requirements, constraints, and ACs. Burden of organization is on the AI, NOT the user. Never ask user to restructure input.
<!-- END conditional steps -->
7. Classify task per `engineering_guardrails.md`.

**Write Path Guard** (all classifications): Project specs → `docs/specs/`, project ADRs → `docs/adr/`. NEVER write to `.agentcortex/specs/` or `.agentcortex/adr/` — those are framework-owned template fixtures. If the Spec Index references `.agentcortex/specs/`, READ from it but WRITE new work to `docs/specs/`.

Classification Tiers:

- `tiny-fix` — No overhead. Directly execute.
- `quick-win` — Light overhead. Plan → Execute → Evidence. No Spec/Handoff.
  - **Confidence Gate**: Before implementation, internally assess confidence (0-100%). < 80% → STOP and ask. 80-90% → state assumption. > 90% → proceed.
  - **Bug Fix Protocol**: If fixing a bug, provide MFR (Minimal Reproducible Failure) first. 2 failed patches → STOP and defer to user.
  - **Doc Integrity**: If an existing Spec covers the target area, update it. No new Spec required, but existing ones must not decay.
- `feature` — Standard flow. Full bootstrap gates required. **(MUST create/log session start in Work Log BEFORE planning begins to claim ownership.)**
- `architecture-change` — Heavy flow. ADR + migration plan required. **(MUST create/log session start in Work Log BEFORE planning begins to claim ownership.)**
- `hotfix` — Urgent path. Systematic debug → fix → retro.

## 2. Work Log Header Setup

Write to `.agentcortex/context/work/<worklog-key>.md`:

- `Branch`: [branch-name]
- `Classification`: [Tier]
- `Classified by`: [AI Name]
- `Frozen`: true
- `Created Date`: [Date]
- `Owner`: [user-name or session-id] — *(required for multi-person; see §11.1)*
- `Guardrails Mode`: [Full|Quick|Lite] — *(auto-derived from classification per `engineering_guardrails.md` Reading Mode. Full for feature/architecture-change/hotfix, Quick for quick-win, Lite for tiny-fix.)*
- `Current Phase`: bootstrap — *(updated by each workflow on entry; see §2b Phase Tracking.)*
- `Checkpoint SHA`: N/A — *(`/implement` records HEAD before code changes; later phases SHOULD refresh after new commits.)*
- `Recommended Skills`: [skill-1 (reason), skill-2 (reason), ...] | none — *(Use §3.6 rule table. Recommend ALL skills whose conditions match. Skip for `tiny-fix`.)*
- `Primary Domain Snapshot`: [domain|none] — *(If a relevant spec declares `primary_domain`, copy its bootstrap-time value here so `/ship` can detect later edits.)*

Write `## Session Info` and `## Drift Log` blocks immediately after header:

```markdown
## Session Info
- Agent: [model name]
- Session: [timestamp]
- Platform: [Antigravity / Codex Web / Codex App]

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
```

Then ensure the active Work Log contains these runtime sections (write `none` when not yet applicable):

```markdown
## Task Description
- [normalized task summary]

## Phase Sequence
- bootstrap

## External References
none

## Known Risk
none

## Conflict Resolution
none

## Skill Notes
none

## Phase Summary
- bootstrap: classified as <tier>, skills matched, context loaded.

## Gate Evidence
- Gate: bootstrap | Verdict: pass | Classification: <tier> | At: <ISO-timestamp>

## Evidence
- Pending: bootstrap only; no implementation evidence yet.
```

## 2a. Advisory Work Log Lock

When creating or resuming a Work Log (non-`tiny-fix`), write or update an advisory lock file at `.agentcortex/context/work/<worklog-key>.lock.json`:

```json
{
  "owner": "<user-name or session-id>",
  "session": "<ISO-timestamp>",
  "branch": "<branch-name>",
  "phase": "bootstrap",
  "updated_at": "<ISO-timestamp>",
  "stale_timeout_minutes": 60
}
```

**On resume**: If a lock file exists and belongs to another session:

- Check `updated_at` + `stale_timeout_minutes`. If stale (expired), warn and overwrite.
- If non-stale, output: `"⚠️ Active lock held by [owner] since [updated_at]. Concurrent edit risk. Proceed? (yes/no)"`.
- This is advisory — it warns but does not hard-block.

**On phase transitions**: Each workflow SHOULD update the lock file's `phase` and `updated_at` when entering a new phase.

Lock file schema and timeout are defined in `.agent/config.yaml §worklog_lock`.

## 2b. Phase Tracking Contract

Every non-`tiny-fix` workflow MUST maintain two header fields in the active Work Log:

- **`Current Phase`**: Updated to the entering phase name at the start of each workflow's Gate Engine or first mandatory step. This lets the next agent instantly know where the state machine left off.
- **`Checkpoint SHA`**: The git HEAD SHA recorded at a stable resume point.
  - `/implement` MUST record `Checkpoint SHA` before any code changes begin.
  - `/review`, `/test`, `/handoff`, `/ship` SHOULD refresh `Checkpoint SHA` when a new commit is created during that phase.
  - If no new commit is created, the previous value is retained.

**Phase Verification (all gated workflows)**: Before proceeding past the Gate Engine, each workflow MUST:

1. Read `Current Phase` from the active Work Log header.
2. Verify the transition is legal per `state_machine.md` (e.g., `plan` → `implement` is legal; `bootstrap` → `ship` is not).
3. If the transition is illegal, output: `"⚠️ Phase transition [from] → [to] is not legal. Current phase is [from]. Expected: [legal-next-list]."` and STOP.
4. Update `Current Phase` to the new phase name.

This costs < 10 tokens per phase entry and eliminates phase-tracking hallucination.

**Session Caching**: If the agent transitions between phases within the SAME conversation (not resuming from handoff), it MAY trust its in-memory phase state and skip re-reading the Work Log header. The file read is only mandatory when: (a) resuming a Work Log from a prior session, or (b) the agent is uncertain about the current phase. The `Current Phase` header MUST still be written on every phase entry regardless of caching.

## 3. Expected Output Format

> **Compact block, not a dashboard.** Apply `AGENTS.md §Phase Output Compression → /bootstrap`. The chat response is a summary pointer; the full record lives in the Work Log file. Do NOT reprint `Constraints`, `AC`, `Non-goals`, `Known Risk`, or `Read Plan` detail in chat — write them to the Work Log and reference by section name.

Chat response template (≤ 10 lines for quick-win, ≤ 15 for feature/architecture):

```
Classification: <tier> — <1-line why>
Goal: <1-line>
Paths: <comma list or "(see Work Log §Task Description)">
Skills: <comma list> (Ref: Work Log §Recommended Skills)
Read: SSoT(<date>) · WorkLog(<new|resumed>) · Guardrails(<Full|Quick|Lite>)
Next: <slash-command>
⚡ ACX
```

Everything below — Classification justification, Recommended Skills rule table, skill conflict pass, user preference merge, Context Read Receipt, Read Plan, Next Step options — is written to the Work Log sections. It is the AI's working notes, NOT the chat response. If the user needs detail, they will ask.

### 3.6 Recommended Skills Rule Table

Write the result to Work Log `## Recommended Skills` (provenance tags as per §3.6a). Chat response shows only the comma list per §3 template. Skip for `tiny-fix`. **No skill metadata file reads required at this stage** — trigger data is embedded in the table above, and bootstrap does not depend on `.agentcortex/metadata/trigger-registry.yaml` or `trigger-compact-index.json`. **Exception**: The Conflict Pass (below) DOES read `.agent/rules/skill_conflict_matrix.md` once when ≥2 skills are recommended and the task is NOT `tiny-fix`. This is the only file read at this stage. Repos MAY layer registry/compact-index metadata on top later for richer cost_risk signals.

   **Mandatory Skills (always activate when condition met):**

   | Skill | Phases | Condition | Skip when |
   |---|---|---|---|
   | `writing-plans` | plan | Classification ≠ tiny-fix AND entering /plan | tiny-fix |
   | `executing-plans` | implement | Approved plan exists in Work Log | Never |
   | `verification-before-completion` | implement, test, ship | Any phase completion claim | tiny-fix |
   | `systematic-debugging` | implement, review, test | Bug, error, or unexpected behavior encountered | Never |
   | `red-team-adversarial` | review, test | /review: hotfix→Lite, feature→Full, arch→Full+Beast | tiny-fix, quick-win |
   | `karpathy-principles` | plan, implement, review | All non-trivial coding tasks (behavioral baseline) | tiny-fix |

   **Scope-Detected Skills (activate when task touches that domain):**

   | Skill | Phases | Detect by | Classifications |
   |---|---|---|---|
   | `test-driven-development` | implement, test | Testable logic (not config/docs/scaffolding) | feature, architecture-change |
   | `api-design` | implement, review, test | Creates, modifies, or deprecates API endpoints | feature, architecture-change, hotfix |
   | `database-design` | implement, review, test | Creates tables, modifies schema, or writes migrations | feature, architecture-change, hotfix |
   | `frontend-patterns` | implement, review, test | Creates or modifies UI components, pages, client-side state | feature, architecture-change |
   | `auth-security` | implement, review, test | Touches login, password, token, session, role, permission | ALL |
   | `production-readiness` | review, ship | Adds or modifies error handling, catch blocks, or logging | feature, architecture-change |
   | `doc-lookup` | implement, review | Task uses any framework/library in the project ADR tech stack | feature, architecture-change, hotfix, quick-win |

   **Phase-Triggered Skills (auto-activate at phase entry):**

   | Skill | Phases | Condition |
   |---|---|---|
   | `finishing-a-development-branch` | ship, handoff | Branch work complete |
   | `receiving-code-review` | review | PR review comments received |
   | `requesting-code-review` | review, handoff | Changes ready for external review |

   **Complexity-Conditional Skills (recommend when scale warrants):**

   | Skill | Phases | Condition | Classifications |
   |---|---|---|---|
   | `dispatching-parallel-agents` | implement | 3+ independent subtasks with low coupling | feature, architecture-change |
   | `subagent-driven-development` | implement | 4+ files or cross-module scope | feature, architecture-change |
   | `using-git-worktrees` | bootstrap, implement | Parallel branch isolation needed | feature, architecture-change |

   **Rule**: Do NOT limit to "0-2 skills". Recommend ALL skills whose conditions are met. A typical `feature` task should activate 4-8 skills.
   **Conflict Pass**: After choosing `Recommended Skills`, read `.agent/rules/skill_conflict_matrix.md` ONCE. If any recommended pair is marked `partial-conflict` or `conflict`, write the chosen precedence or scoping strategy to `## Conflict Resolution` in the Work Log. Later phases reuse that note instead of re-reading the matrix.

### 3.6a. User Skill Preference Merge (Capability-by-Presence)

> **Scope**: Non-`tiny-fix` only. Runs AFTER rule table + conflict pass, BEFORE writing `Recommended Skills` to Work Log.
> **Config**: `.agent/config.yaml §user_preferences`

1. Check if the file at `.agent/config.yaml §user_preferences.path` (default: `.agentcortex/context/private/user-preferences.yaml`) exists. If not, skip this subsection entirely. **Zero cost.**
2. Parse the file as YAML. If malformed or empty: warn once (`"⚠️ User preferences file exists but is malformed. Skipping."`), skip. **NEVER block bootstrap.**
3. **Validate skill IDs** against the bootstrap rule table (§3.6) or, when available, `.agentcortex/metadata/trigger-compact-index.json`. Warn on unknown IDs; ignore them.
4. **For each `pinned` skill**:
   a. If already in `auto_skills` → no-op (already recommended via auto-detection).
   b. If its `Skip when` / classification column excludes the current classification AND entry does NOT have `force: true` → skip with note: `"Pinned skill [X] skipped: skip-when active for [classification]."`
   c. If its `Skip when` excludes the current classification AND entry has `force: true` → add with provenance `(pin+forced)`. **Hard ceiling**: even with `force`, a skill CANNOT activate in a phase outside its `phase_scope` (from trigger-compact-index or rule table `Phases` column).
   d. Otherwise → add with provenance `(pin)`.
   e. For each newly added pinned skill, check `.agent/rules/skill_conflict_matrix.md` against all existing recommended skills. If `partial-conflict`: apply guidance and record in `## Conflict Resolution` with `[pinned by user preference]`. If `conflict`: warn user and ask which takes priority — do NOT silently resolve.
5. **For each `disabled` skill**:
   a. If skill has `trigger_priority: hard` AND `block_if_missed: true` in the trigger registry, OR is listed in `.agent/config.yaml §user_preferences.protected_skills` → ignore the disable, warn once: `"⚠️ Cannot disable protected skill [X]. Ignored."`
   b. Otherwise → remove from recommended skills with provenance `(disabled by user-pref)`.
6. **Token advisory**: If the final pinned set adds more than `high_cost_pin_advisory_threshold` skills with `cost_risk: high` (per compact index), emit: `"Note: [N] pinned high-cost skills may increase token usage."`
7. Write the final merged set to `Recommended Skills` with provenance tags: `(auto)`, `(pin)`, `(pin+forced)`, `(disabled by user-pref)`, `(protected, disable ignored)`.

**A skill in both `pinned` and `disabled`**: pin wins (explicit request > explicit removal). Warn: `"Skill [X] is both pinned and disabled. Pin takes precedence."`

### 3.7 Work Log Content (written to the Work Log file, NOT emitted in chat)

These items are the AI's working notes. They live in the Work Log sections listed in `AGENTS.md §Work Log Contract` and are NOT repeated in the chat response. Chat only shows the compact block in §3.

- **Context Read Receipt** (→ Work Log `## Session Info` or `## Task Description`):
  - `current_state.md` → [last modified date or key field read]
  - Work Log → [status: existing|created|resumed]
  - Spec Scope → [list of determined-relevant spec files, or "none"]
- **Read Plan** (→ Work Log `## Task Description` or header): Classification, Guardrails Mode (Full|Quick|Lite), Files to read (with sections), Files explicitly skipped (with reason), Estimated governance reads.
- **Next Step Recommendation** — the chat block's `Next:` field uses this map:
  - `tiny-fix` → proceed directly with inline plan
  - `quick-win` → `/plan`
  - `feature` → `/brainstorm` or `/spec` (spec required before `/plan`)
  - `architecture-change` → `/brainstorm` → `/spec` (ADR + spec required before `/plan`)
  - `hotfix` → `/research` (systematic debugging)

## 4. Hard Checkpoints

- Classification is locked once written to Work Log. Silent downgrade is prohibited. If the task must move upward, roll back to `CLASSIFIED`, update the classification explicitly, and re-enter the required workflow from there.
- `tiny-fix` bypasses full bootstrap/handoff overhead, but MUST provide evidence.
- `quick-win` bypasses Spec and Handoff, but MUST provide a brief plan and diff evidence.

## 5. Hard Gate

- MUST CREATE `.agentcortex/context/work/<worklog-key>.md` before proceeding. *(Skip for `tiny-fix`.)*
- If file already exists, READ and RESUME from existing state.

## 5b. SSoT Sequence Pre-Ship Check (AC-26)

Before entering `/ship` or `/handoff`, re-read the `current_state.md` header `Update Sequence` field. Compare with the `SSoT Sequence` recorded in the Work Log during bootstrap.

If the values differ: output advisory warning:
`"⚠️ SSoT updated by another session since bootstrap (was N, now M). Re-read recommended before shipping."`

This is advisory — it warns but does not hard-block. The user may proceed after acknowledging.

## 6. Antigravity Hard Stop (Runtime v5)

- After outputting the bootstrap report, STOP IMMEDIATELY.
- Do NOT proceed to `/plan`, `/implement`, or any code changes in the same turn.
- Next step MUST be planning (or direct execution if `tiny-fix` via §0 fast-path).
- Output: "Bootstrap complete. What would you like to do next? (e.g., proceed to plan)"
- **Tiny-fix fast-path**: If §0 pre-classified as tiny-fix, skip this stop entirely — proceed directly to inline plan + execute.
