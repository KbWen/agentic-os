# Engineering Guardrails (Constitution)

## Scope

Global (applies to all projects using template).

## Reading Mode

- **Full Mode** (default for `feature`, `architecture-change`, `hotfix`): Read core sections first, then load conditional sections per the Heading-Scoped Read rules below.
- **Quick Mode** (for `quick-win`): Do NOT read this file. Essential quick-win rules (Confidence Gate, Bug Fix Protocol, Doc Integrity) are embedded in `bootstrap.md` §7 quick-win classification. If the task escalates beyond quick-win, switch to Full Mode.
- **Skip Mode** (for `tiny-fix` ONLY): Do NOT read this file. `AGENTS.md` §Core Directives provides sufficient governance for tiny-fix tasks (scope discipline, evidence requirement, fast-path rules). If the task escalates beyond tiny-fix, switch to Quick or Full Mode and read this file at that point.

### Heading-Scoped Read (Full Mode Optimization)

When in Full Mode, the following sections are **always required** (core):
- §1 Core Philosophy
- §2 Change Safety Principles
- §4 Design Before Implementation (including §4.1 Confidence Gate, §4.2 Spec Freezing, §4.4 Design-First Rule)
- §7 Scope Discipline
- §8 Agent Operating Mode (§8.1 Bug Fix Protocol only)
- §10 vNext Governance & Classification

The following sections are **conditional** (load only when triggered):
- §3 Data & Time Integrity → only when task involves temporal/numerical data processing
- §5 Testing & Verification → load at `/implement` entry and `/test` entry (not at `/bootstrap` or `/plan`)
- §6 Explainability & Traceability → only when task is `feature` or `architecture-change`
- §8.2 External Tool Delegation → only when external tools are invoked
- §9 Intent Safety Rules → already internalized by AI at session start; re-read only on ambiguity (per AGENTS.md Read-Once Discipline)
- §11 Multi-Person Collaboration → only when Work Log lock conflict detected or multi-person scenario
- §12 Data & Code Integrity Protection → load at `/implement` entry (not at `/bootstrap` or `/plan`)

> **Token budget estimate** (1 line ≈ 15 tokens):
> Core sections (§1, §2, §4, §7, §8.1, §10) ≈ 170 lines ≈ **2,550 tokens**
> Conditional sections (§3, §5, §6, §8.2, §9, §11, §12) ≈ 156 lines ≈ **2,340 tokens**
> Skipping all conditional sections saves up to **~2,340 tokens** per Full Mode session when none are triggered.

### Loaded-Sections Receipt (Agent-Facing Signal)

When `/bootstrap` reads this file in Full Mode, it MUST echo a one-line receipt in the Work Log `## Session Info` naming the sections actually loaded. Format:
`Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core)` — plus any conditional sections triggered, e.g. `+ §5 (testing), §12 (implement).`

This serves two purposes: (a) subsequent phases can trust that cited sections are in context without re-reading, and (b) the receipt is auditable — if a phase cites §6 but the receipt does not list it, either the receipt is stale (re-read per AGENTS.md Safety Valve + log to Drift Log) or the citation is fabricated.

## Role

Non-negotiable principles for agent-driven development.

## 1. Core Philosophy

### 1.1 Correctness First

- Correctness > Performance/Complexity/Features.
- Unverifiable behavior is classified as UNSAFE.

### 1.2 Explicit Over Implicit

- Assumptions, preconditions, limitations MUST be explicitly stated.
- Implicit magic behavior is PROHIBITED.
- Persistence-layer ↔ domain-model conversions MUST use explicit named methods (e.g., `fromRecord()`, `toRecord()`). Implicit casting or field-by-field spread at call sites is PROHIBITED.

### 1.3 Reproducibility by Default

- Same input MUST yield same output.
- Randomness MUST be controllable, toggleable, and traceable.

## 2. Change Safety Principles

### 2.1 Small & Reversible Changes

- Micro-patches preferred.
- Rollback MUST be designed upfront.

### 2.2 Preserve Existing Behavior

- DO NOT alter existing semantics unless explicitly requested.
- New behavior MUST be feature-flagged or config-driven.

## 3. Data & Time Integrity

- Look-ahead bias PROHIBITED.
- Exact temporal ordering MUST be stated.
- Input -> Output causality MUST be clear.

## 4. Design Before Implementation

- BEFORE coding, MUST provide: Problem understanding, Design, Trade-offs, Risks.
- If ambiguous, priority is CLARIFICATION.

### 4.1 Confidence Gate (Auto-Enforced)

Before executing any implementation step, AI MUST internally assess and state:

- `Confidence: [0-100]%` with a 1-line rationale.
- **< 80%**: STOP. Surface the uncertainty and ask a clarifying question. DO NOT proceed.
- **80–90%**: State the assumption explicitly, then proceed with caution.
- **> 90%**: Proceed normally.

**Narrative vs structured receipt**: "Silent above 90%" means no free-text narrative or chat prose. It does NOT mean silent in structured phase outputs — `/plan`, `/implement`, and `/ship` compact blocks MUST always include a `Confidence:` field (e.g., `Confidence: 95% — high`) so the gate is auditable in the Work Log. This keeps chat output terse while making the gate traceable.

### 4.2 Spec Freezing (SSoT Protection)

- Whenever a Spec is approved or the task transitions to implementation, the Spec MUST be marked as **FROZEN** (e.g., via YAML frontmatter `status: frozen`).
- **Shipped Status**: After `/ship` delivers a spec's feature, `/ship` sets `status: shipped` on the spec frontmatter. Shipped specs are **historical reference only** — they document past decisions. For current system design, read the corresponding Domain Doc L1 (`docs/architecture/<domain>.md`) instead. Shipped specs MUST NOT be cited as authoritative current design.
- AI agents MUST NOT modify, review, or suggest refactoring for any document marked as `FROZEN` or `Finalized` during normal tasks.
- **Exception (AI-Initiated Unfreeze)**: If the AI discovers that a FROZEN spec must be changed (due to a bug or requirement change), the AI MUST:
  1. **STOP** and surface the issue explicitly: "⚠️ [Filename] is FROZEN but requires update: [Reason]. Approve to unfreeze and continue? (yes/no)"
  2. Only proceed after user responds **YES**.
  3. Set status to `draft`, make changes, then re-freeze during `/ship`.

### 4.3 Discovery Ownership

`/plan` owns discovery: existing code patterns, doc lookup, and spec alignment are resolved during planning via Target Files, External References Gate, and AC Coverage. If discovery proves insufficient at implement time, redirect to `/research` — do not add ad-hoc checks.

### 4.4 Design-First Rule (UI Changes)

> **Principle**: All UI changes MUST follow the **Design → Export → 1:1 Translate → Verify** pipeline.

**Scope**: Any task that modifies user-visible interface elements (screens, components, layouts, styling, animations, navigation flows). Backend-only, CLI, and infrastructure changes are EXEMPT.

**Scope Exemption (Directory-Based)**: This rule applies **only** to production code directories (e.g., `src/`, `app/`, `lib/`, `packages/`). Files in `tools/`, `scripts/`, `scratch/`, `tests/`, `__tests__/`, `*.test.*`, `*.spec.*`, and `.agentcortex/` are **automatically exempt**.

**Design Source of Truth (DSoT)**: The canonical visual specification for UI work. Default tool: **Stitch**. Alternative tools (Figma, Pencil, etc.) are equally valid — the requirement is a linkable, inspectable, exportable design artifact.

**Pipeline**:
1. **Design**: Create or update the visual specification in the DSoT tool. MUST produce a linkable artifact (URL or file path).
2. **Export**: Extract implementation-ready specs (tokens, spacing, typography, component structure) from the DSoT.
3. **1:1 Translate**: Implementation MUST faithfully reproduce the DSoT spec. Intentional deviations require explicit approval recorded in the Work Log with rationale.
4. **Verify**: `/review` MUST compare implementation against DSoT. Visual mismatch = **HIGH** severity finding.

**Enforcement**:
- `/plan` → Design Gate: plan MUST include a DSoT link for UI tasks. No link = plan incomplete.
- `/implement` → Design Approval Check: UI rendering code blocked until DSoT design is confirmed. No design = no UI code.
- `/review` → Design Compliance Check: 1:1 fidelity audit against DSoT. Structural deviation = **HIGH** severity.

**No DSoT = No UI Implementation**: If a UI task lacks a design artifact, it MUST NOT proceed past `/plan`. Agent MUST stop: "⚠️ This task modifies UI but has no design link. Create the design in [DSoT tool] first."

## 5. Testing & Verification

- Logic Change -> Add Test.
- Interface Change -> Verify Compatibility.
- **Sanity Check**: Is output bounding safe? Side-effects?
- **Doc-First Pillar**: Architecture/Core logic changes MUST precede with Spec/ADR in `docs/`.
- **Naming/Locations**:
  - ADRs: `docs/adr/ADR-[ID]-[kebab-case].md`
  - Specs: `docs/specs/[feature-name].md`
  - Guides: `docs/guides/[topic].md`
  - Agent Work Logs: `.agentcortex/context/work/`
- **Write Path Guard**: Agents MUST NOT write project specs to `.agentcortex/specs/` or project ADRs to `.agentcortex/adr/`. Those directories contain framework-owned template fixtures only. All project artifacts MUST go to `docs/specs/` and `docs/adr/`. If the SSoT Spec Index references `.agentcortex/specs/`, READ from it but WRITE new work to `docs/specs/`.
  - Private Context: `.agentcortex/context/private/` (local-only, gitignored)
    - USE FOR: personal dev environment configs, private remote URLs, internal credentials references, team-specific workflows not intended for public repos.
    - DO NOT USE FOR: project architecture docs, contribution guides, public development standards.
    - WHEN UNCERTAIN: Agent MUST present options to user in `/plan` phase. Autonomous path decisions on ambiguous content are PROHIBITED.

### 5.1 Service & Provider Test Coverage

- Every new Service class or Provider MUST have ≥ 1 unit test before Ship. No test = **Ship Gate FAIL**.
- Test count regression (fewer passing tests than the last committed baseline) MUST have written justification in the Work Log. Undocumented regression = **Ship Gate FAIL**.

### 5.2 Error Surface Rules

- Service/Provider layer errors MUST `return null` or a sealed error type. Unhandled exceptions that escape a Service or Provider boundary = **Gate FAIL**.
- Every `catch` block MUST include at minimum a log statement. Silent `catch {}` with no logging = **Review Gate FAIL**.

### 5.2a Error Observability (Production-Safety Critical)

Error logging MUST use a **production-observable sink** — a logger that survives release builds and reaches operators in production.

- ✅ Acceptable: framework logger (`Logger.error()`, `log.error()`), crash reporter (`errorReporter.capture()`), structured logging to stdout consumed by production infrastructure.
- ❌ Prohibited as sole error path: `debugPrint()`, `print()`, `console.log()` in debug-only mode, or any API that is stripped / tree-shaken / no-op'd in release builds.

**Rationale**: If an error is caught but logged only via a debug-only API, the catch block is functionally silent in production. Users experience failures while the team remains blind. This is the #1 cause of "beta testing is completely blind" incidents.

**Gate check**: Review MUST verify each `catch` block uses the project's production logger. If the project has no production logging strategy defined, flag at `/review`: *"No production-observable error sink identified — resolve before ship."*

**Scope**: This rule applies to application/service code (e.g., `src/`, `app/`, `lib/`, `packages/`). **Files in `tools/`, `scripts/`, `scratch/`, and test directories are automatically exempt.**

### 5.2b Evidence Truncation Rule

To prevent Work Log bloat and premature context compaction, agents MUST NOT paste raw terminal output verbatim into Work Logs.

- **Test pass**: Paste only the final summary line (max 3 lines).
- **Test fail**: Paste only the failing test name, assertion error, and relevant source line (max 10 lines per failure). Strip all passing test output.
- **Build/lint output**: Paste only error-level output. Strip warnings and informational messages unless they are the subject of the task.

### 5.3 Spec Drift Prevention & Test Quality

**Spec Drift Prevention**
- Before implementing any feature, the agent MUST read the corresponding Spec file in `docs/specs/`. Missing spec for a non-trivial feature = **Bootstrap Gate FAIL**.
- If implementation deviates from the spec (even slightly), STOP and report the deviation before proceeding. Silent scope expansion or shrinkage = **Gate FAIL**.
- Never silently expand or shrink scope — surface every delta to the user and obtain confirmation before continuing.

**Test Quality**
- Unit tests MUST cover: happy path, error path, and at least one boundary condition. A test asserting only `expect(result, isNotNull)` is insufficient — test actual values.
- For date-based, time-based, or numerical-boundary logic: always include edge cases (zero values, first/last day of period, maximum boundary).
- Tests MUST verify behaviour, not implementation. Mirroring the implementation formula in an assertion without validating the business rule is insufficient.

### 5.4 YAGNI — You Aren't Gonna Need It

- Do not introduce abstract base classes, mixins, or utility layers unless there are 3+ concrete use cases already in the codebase.
- Single-file implementation first; refactor to a shared abstraction only when the second real consumer exists.
- Adding a new dependency requires justification in the PR or Work Log: explain why existing code cannot solve the problem.

## 6. Explainability & Traceability

- Big decisions MUST be traceable ("Why was this done?").
- Intermediate results and Decision Traces prioritized.

## 7. Scope Discipline

> See also: `AGENTS.md` §Core Directives ("UNAUTHORIZED REFACTORING STRICTLY PROHIBITED").

- ONLY solve requested issue. If larger issue discovered, output a "Follow-up Issue" recommendation.

## 8. Agent Operating Mode

- **Default**: Conservative, Explainable, Stable.
- **When Uncertain**: State ambiguity, provide 2-3 options, DEFER high-impact decisions to user.

### 8.1 Bug Fix Protocol

**MFR (Minimal Reproducible Failure)**: BEFORE any fix, MUST provide:

- Repro steps (≤3 steps), Expected vs. Actual behavior.

**2-Strike ESC**: If the SAME issue fails after 2 patches:

1. STOP patching immediately.
2. Output diagnostic: modified code blocks, call relationships, behavior diffs ONLY. ❌ No narrative claims.
3. Record failure in Work Log and DEFER to user for escalation.

**Active Tracking**: After each failed patch attempt, AI MUST append to Work Log: `Patch Attempt [N]: [1-line result]`. When N ≥ 2, the 2-Strike ESC is automatically triggered.

**Async/Data-Flow Safety**: When modifying async or data-flow code, MUST verify: error handling, race condition guards, and loading state management.

### 8.2 External Tool Delegation Protocol

External CLI tools (e.g., `ask-openrouter`, `codex`) are **OPTIONAL accelerators**. Projects MAY operate without any of them.

**Pre/Post-Flight (Mandatory for all external tool invocations)**:

- **Pre-Flight** (in order — fail fast):
  1. **Cost-Tier Confirmation** (memory-only): low-cost → auto-execute; high-cost (quality/max profile) → confirm with user first.
  2. Update Work Log with `Executor: <tool-name>` (only if cost-tier passes).
  3. **Availability Check (Silent)**: run health check (e.g., `python -m ask_openrouter --help`, `codex --version`). If unavailable: **silently fall back** to AI-native execution. DO NOT warn user. DO NOT suggest installation. Cache per session.
- **Post-Flight**: Read tool output, verify scope alignment, update Work Log, apply Gate Check per §10.2.
- External tool output is treated as **Junior Tool output** — AI MUST review before accepting.

## 9. Intent Safety Rules

User input in any form (natural language, keywords, or slash commands) triggers the same workflow gates. AI determines the current phase and enforces prerequisites automatically. Slash commands are optional shortcuts, not required triggers.

### 9.1 Acknowledgment-only Inputs (No Action)

The following inputs MUST NOT trigger any state transition or execution:

- EN: "OK", "Sure", "Got it", "Alright", "Fine"
- ZH: "好", "收到", "嗯", "了解", "沒問題"

Correct behavior: Confirm receipt, optionally ask what the next step should be.

### 9.2 Vague Inputs (Must Clarify)

Inputs without a clear action verb or direction MUST prompt a clarification question:

- EN: "fix it", "tweak something", "make it better", "adjust this"
- ZH: "弄一下", "調整一下", "改改看", "處理一下"

NEVER guess intent. NEVER proceed on vague input.

### 9.3 Search Policy (Lexical-first)

When locating code, files, or definitions:

1. ALWAYS use lexical search first (ripgrep, path lookup, directory listing).
2. Semantic search is allowed ONLY after lexical search yields no results.
3. If still unresolved, ask a targeted question.

### 9.4 Namespace Isolation (Downstream Safety)

Agentic OS deploys workflows and skills into downstream projects. Those projects may have their own custom commands, skills, or automation — including inside `.agent/` directories. The Intent Router must respect boundaries:

1. **Framework-managed vs user-owned**: The distinction is NOT by directory. Files listed in `.agentcortex-manifest` are framework-managed. Everything else — even files inside `.agent/workflows/` or `.agent/skills/` — belongs to the project owner. Users are free to add their own workflows and skills alongside Agentic OS's.
2. **Collision resolution**: If a user-created command name collides with an Agentic OS workflow (e.g., both have a `/deploy`), the **user's command takes priority**. Agentic OS workflows are infrastructure; user commands are application-level.
3. **Natural language routing**: When AI receives natural language that could map to either an Agentic OS phase or a user-defined command, AI MUST check: "Is the user talking about the Agentic OS governance process, or about their project-specific action?" If ambiguous, ask.
4. **Governance still applies**: User-defined workflows and skills are not exempt from Agentic OS governance. Phase order, gates, and evidence requirements still apply — but the user's custom logic drives the implementation, not Agentic OS's.

### 9.5 Core Principle
>
> When intent is unclear, ASK. Never guess. Never proceed.

## 10. vNext Governance & Classification

### 10.1 Escalation Rules

| Trigger Condition | Minimum Classification |
| --- | --- |
| < 3 files, no semantic change | `tiny-fix` |
| 1-2 modules, clear scope, no cross-module impact | `quick-win` |
| Touches `exports` / public API / signature | `feature` |
| Touches >1 module import graph | `feature` |
| Adds new directories | `feature` |
| Alters data-flow / system boundaries | `architecture-change` |
| Alters default configs impacting users | `feature` |

### 10.2 Gate Type & Evidence Standards

| Category | Mandatory Gates | Min Evidence Required |
| --- | --- | --- |
| **tiny-fix** | classify → plan (inline) → execute | diff summary + 1-line verification |
| **quick-win** | bootstrap → check Spec Index → plan → implement → evidence → ship (review and test are optional when evidence is inline) | diff + before/after behavior statement |
| **feature** | bootstrap → spec → plan → implement → review → test → handoff → ship | test output + verifiable demo steps |
| **architecture-change** | bootstrap → ADR → spec → plan → implement → review → test → handoff → ship | migration plan + rollback verification |
| **hotfix** | bootstrap → research → plan → implement → review → test → ship | root cause + fix verification + retro |

AI self-enforces the phase order above. Users may invoke phases via slash commands (as shortcuts) or natural language.

For non-`tiny-fix` Work Logs, the minimum runtime contract is:

- `## Task Description`
- `## Phase Sequence`
- `## Evidence`
- `## External References`
- `## Known Risk`
- `## Conflict Resolution`

If a section is not applicable, write `none` instead of omitting it. This keeps CI verification deterministic.

### 10.3 Tiny-Fix Fast-Path

- **Definition**: Modifies < 3 files WITHOUT semantic change (typo, docs, non-functional config).
- **Flow**: `classify → one-line scope → execute → inline evidence → done`.
- **Exclusion**: Bypasses full bootstrap, handoff, and Work Log overhead.
- **Governance File Exclusions** (always escalate to quick-win minimum, even if < 3 files):
  - Any file in `docs/specs/` or `docs/architecture/` — spec/Domain Doc changes are always semantic by governance definition
  - `docs/specs/_product-backlog.md` — route to `/spec-intake` instead of tiny-fix
  - Any file with `status: frozen` frontmatter — frozen files require unfreeze approval (§4.2)
  - `AGENTS.md`, `.agent/rules/*.md`, `.agent/config.yaml` — framework governance files affect all agents globally

### 10.4 Quick-Win Fast-Path

- **Definition**: Clear, contained change to 1-2 modules with a well-defined outcome. Semantic change IS present, but cross-module impact is LOW.
- **Flow**: `classify → check Spec Index for existing coverage → plan (brief) → execute → update existing Spec if found → inline evidence → done`.
- **Exclusion**: No formal Spec required. No `/handoff` required. Work Log MUST be created (lightweight — needed for skill loading and evidence tracking).
- **Doc Integrity (MANDATORY)**: While No *new* Spec is required, if an **existing** Spec already covers the target area, the AI MUST update that Spec to prevent "Documentation Decay." If the change is too complex for a stealth update, use the "Spec Seed" mechanism in `/retro` to flag it for formalization.
- **Examples**: Changing an API response format, adding a config flag, fixing a single-module bug with known root cause.
- **Security Escalation**: If a quick-win task touches auth/security code (login, password, token, session, role, permission, access control), it MUST be escalated to at least `hotfix` classification to activate review and test phases. Auth-adjacent quick-wins are not safe to ship without review.
- **Root-Cause Escalation**: If a quick-win task addresses a crash, data loss, or behavioral regression (not just a new feature), the Work Log MUST include a 1-line root-cause statement explaining why the bug occurred. Missing root-cause for regression-class bugs = review warning. Format: `Root Cause: <1-line explanation>` in Work Log `## Known Risk`.

### 10.5 Handoff/Ship Hard Gate

> See also: `AGENTS.md` §Delivery Gates.

- The ship phase MUST verify handoff references in single-line format: `ship:[doc=<path>][code=<path>][log=<path>]`
- If any field is missing, AI MUST reject shipping and list the missing field(s).

### 10.6 Completion Guard (Anti-Silent-Exit)

When AI detects a task is nearing completion (e.g., user says "done", "完成了", "差不多了", or AI has finished all planned steps), AI MUST self-check BEFORE responding:

1. Is the task classified as `quick-win` or higher?
2. Has the handoff phase been executed? (Check: does Work Log have a `## Resume` block?)
3. Has the retro phase been executed? (Check: does Work Log have a `## Lessons` block?)

**For `feature` / `architecture-change`**: If handoff or retro is missing, AI MUST remind: "📋 Before closing: handoff and retro haven't run yet. Want me to proceed with them now?"

**For `quick-win`**: AI SHOULD ask: "Quick task done. Run a brief retro to capture lessons? (yes/skip)"

**For `tiny-fix`**: Skip entirely.

## 11. Multi-Person Collaboration Rules

> Canonical rules are in `AGENTS.md` §Multi-Person Collaboration and §Multi-Session Concurrency. This section adds implementation details.

- **Work Log Naming**: `.agentcortex/context/work/<worklog-key>.md` for single-person, `.agentcortex/context/work/<owner>-<worklog-key>.md` for multi-person.
- Missing active Work Logs are recoverable during bootstrap/plan/handoff: resolve `<worklog-key>`, create or recover the active log.

### 11.1 Ship Guard (SSoT Merge Protection)

Before `/ship` writes to `current_state.md`:

1. AI MUST check if `current_state.md` has been modified since the task started (compare timestamps or last-known content hash).
2. If modified by another person/session: AI MUST warn and require confirmation before merge.
3. If proceeding, AI MUST perform an **additive merge** (append new entries without removing existing ones), NOT a full overwrite.

## 12. Data & Code Integrity Protection

**Applies to**: all feature, architecture-change, and hotfix tasks. Not required for tiny-fix.

### 12.1 Read-Before-Write
Any task that modifies an existing file MUST:
1. Read the full file first using the Read tool.
2. Record in the Work Log what was found: file purpose, key exports, and any sections that will change.
Skipping this step is a gate violation — the task cannot proceed to Implement.

### 12.2 Test Gate (mandatory before commit)
- The project's linter/analyzer MUST produce **zero errors** (warnings are allowed but must be noted).
- The project's test suite MUST pass with **zero failures**.
- Red on either = no commit, no ship. No exceptions.
- Evidence (terminal output) MUST be pasted into the Work Log under "Test Gate Results".
- *(Project-specific test commands should be defined in `/app-init` or project README.)*

### 12.3 Migration Safety
Schema changes to database tables require ALL of the following:
1. Read all existing migration files before writing a new one.
2. Determine migration strategy from project ADR or conventions (forward-only vs. reversible).
3. Record in the Work Log: **"Will this migration destroy existing user data? YES/NO + reasoning"**
4. Add an explicit test that verifies existing data survives the migration.

### 12.4 No Silent File Shadowing
Before creating any new file:
1. Use Glob to check if a file with that name already exists anywhere in the project.
2. If a match is found, document the conflict in the Work Log and resolve intentionally (rename, merge, or replace with justification).
Never silently overwrite an existing file.

### 12.5 Rollback Awareness
Every implementation task MUST include in the Work Log:
> **"Rollback plan: How do I undo this if it breaks production?"**
Acceptable answers: revert commit SHA, feature-flag toggle, migration rollback steps. "Delete the file" is not sufficient.
