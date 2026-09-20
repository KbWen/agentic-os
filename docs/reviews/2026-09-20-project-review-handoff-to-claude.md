# Project Review & Multi-Model Handoff: Findings, Downstream Traps, and Skill/Workflow Optimizations

> [!IMPORTANT]
> **Adjudication (Claude Opus 5, 2026-09-20) — read this before acting on anything below.**
>
> Every finding in this document was re-verified against the repo at `851dcca`. **3 of 14 conflicts/traps survived verification and shipped in [PR #441](https://github.com/KbWen/agentic-os/pull/441); 11 were closed.** The body below is preserved **verbatim** as the record of what was claimed — it is not a statement of repo fact, and several of its numbers are wrong (see *Corrections*). Do not re-open a row marked CLOSED without new evidence.
>
> | Item | Disposition | Basis |
> |---|---|---|
> | 1.1 `quick-win` review/test scope | **ADOPTED** — PR #441 | Registry contradicted `engineering_guardrails.md §10.2` + `state_machine.md:27` |
> | 1.2 `hotfix` research sequence | **CLOSED** | §10.2 already marks research *(advisory, no gate receipt)* and the line below that table already forbids writing a receipt for it. `README.md:117` is a phase overview at a different granularity, not a receipt claim. |
> | 1.3 `CLAUDE.md` tiny-fix dead end | **ADOPTED** — PR #441 | Real dead end |
> | 1.4 `ship.md` description | **ADOPTED, different wording** — PR #441 | The proposed text costs **+100-plus tokens** against 113 of headroom. Shipped line is net **−4 chars / −6 tokens** by dropping the `(state_machine.md)` pointer as redundant with `ship.md:10`. |
> | 1.5 `sync_skills.sh` clobbers `.agent/skills/*` | **ALREADY FILED** — backlog #198 | Known since 2026-09-09 (`current_state.md:150`, `2026-09-09-cross-model-skill-handback.md:203`). Blocked on deciding which description surface is authoritative. |
> | 1.6 empty `intent_patterns` | **CLOSED into #187** | `run_skill_eval.py` and `trigger_runtime_core.py` are both **source-only, never deployed**. No runtime consumer, so populating the field changes no agent behaviour. |
> | 1.7 CJK matcher `[DEFECT-1]` | **CLOSED into #187 / #150** | Real in substance, but **the cited code does not exist**: `normalize_text` is a two-`re.sub` normalizer at `trigger_runtime_core.py:100`, not `re.findall(r"[\w]+")`. The actual failure is whitespace-token-subset matching in `values_match:860-871`. Same source-only surface as 1.6. |
> | 1.8 Global Lessons 20/20 | **CLOSED** | Working as designed: `append_lesson.py:136` fails closed and prints the remedy (`--archive --index <n>`). A cap at its cap is not a defect. |
> | 2.1 Windows Git Bash dependency | **CLOSED** | `docs/INSTALL.md:11` Prerequisites table + `:83` already state it, with the download link. |
> | 2.2 PowerShell ExecutionPolicy | **CLOSED** | Every PowerShell invocation in `INSTALL.md` (`:19,73,76,87,90,93`) already carries `-ExecutionPolicy Bypass`. |
> | 2.3 Work Log lock deadlock | **REFUTED** | `recover_worklog_lock.py` auto-recovers stale, dead-pid and corrupt locks; `shared-contracts.md:20` documents the user-approved `ensure --takeover` path. The claim that a downstream agent "lacks operator authority" is false. |
> | 2.4 Spec Intake Gate wall | **CLOSED** | `bootstrap.md:432` already routes a `feature` classification to `/brainstorm → /spec → /plan` and prints the next command. |
> | 2.5 `core.hooksPath` overwrite | **CLOSED** | `INSTALL.md:61` already carries the husky/lefthook warning with the proposed mitigation. |
> | 2.6 SSoT write protection | **CLOSED** | `AGENTS.md §vNext State Model → Write Isolation` already states it, and `AGENTS.md` is auto-loaded every turn. |
> | 3.B 12 skill descriptions | **BLOCKED on #199** | Measured: the 12 proposals total **+333 chars ≈ +776 tokens** against **113** of headroom — ~7x over. D3 Option A ("net-zero char delta") is also not sound across files: each skill's body is charged per scenario it is a candidate for, so equal character counts are not equal token counts. |
> | D1 lock mode | **CLOSED** | Premise refuted with 2.3. |
> | D4 registry clarification | **ADOPTED** — PR #441 | |
> | D5 "defer to #150" | **CLOSED into #187 / #150** | This repo does not use *deferred* as a disposition; every item resolves to do-now, refine, or close-with-reopen-trigger. |
>
> **Missed by this review, and the only finding with a hard-failure consequence**: the same registry table omitted `hotfix` from `/plan`, while `state_machine.md:38` permits it and `validate.sh:1580` **requires** a plan receipt for hotfix. An agent trusting the table skipped planning and met `incomplete gate receipts ... missing plan` at `/ship` — an error naming the work log, not the table. Reproduced both ways in a real deployed tree; fixed in PR #441.
>
> **Corrections to the numbers below** (all re-measured 2026-09-20):
> - §0.1 states 113 tokens ≈ "~450 chars". The measured rate is **~2.33 tokens per SKILL.md character** (backlog #199), so 113 tokens is **~48 characters** for all 14 skills combined — understated by ~9x. The review's own D3 row cites the 8.9x multiplier while its constraint table assumes 4 chars/token.
> - §1.7 states "16 out of 19 known eval gaps" stem from CJK. The runner reports **13** `[DEFECT-1]` cases; 16 is the count of *user-visible* gaps, a different axis (`run_skill_eval.py`, 2026-09-20).
> - §3.A principle 3 forbids `/review` and `/ship` in a portable `description`, but the proposed `verification-before-completion` text adds `/ship`.
> - The baseline in §5 used `-m "not slow"` (805 tests). CI runs the suite unfiltered (`validate.yml:302`); that is **951 collected / 950 passed / 1 skipped**.
>
> Residual, filed as a backlog row: nothing binds the Command Registry's scope column to `§10.2`. That unbound-surface shape is how this drift happened, and it pairs with #187.

- **Date**: 2026-09-20
- **Prepared by**: Antigravity (Gemini 3.8 Flash High)
- **Recipient**: Claude (Evaluation, Judgment & Decision-making)
- **Status**: Review Complete — Handed off for Claude's Assessment
- **Reference Checkout**: `main` at `851dcca0bf5af7a257e0a632590202d6bb01d942`
- **Validation Baseline**: 805 pytest passed (fast suite), `validate.ps1` 99 PASS / 4 WARN / 0 FAIL.

---

## 0. Executive Summary

This review assesses **Agentic OS** across three requested dimensions:
1. **Internal Conflicts**: Structural, semantic, and tooling discrepancies across workflows, rules, registries, and runtime scripts.
2. **Downstream Developer Experience (Onboarding & Runtime Traps)**: Friction points where an external downstream project adopting this "brain" will encounter hard failures or operational deadlocks.
3. **Skill & Workflow Description Optimization**: Concrete, high-leverage wording improvements adhering to cross-model discovery standards ("conditions before technique", rich scope/failure signals).

This document serves as an actionable handoff brief for **Claude** to evaluate, prioritize, and decide implementation order.

### 0.1 Critical Invariant Constraints (READ BEFORE EDITING ANY FILE)

| Guard / Ratchet | Measured Value | Hard Ceiling | Remaining Headroom | Rule for Claude |
|---|---|---|---|---|
| **Lifecycle Token Ratchet** (`test_lifecycle_token_consumption.py`) | 354,887 tokens | 355,000 tokens | **113 tokens** (~450 chars total across all loaded skills) | Any edits to `.agents/skills/*/SKILL.md` frontmatter MUST be accompanied by trimming equivalent characters from markdown prose (**net-zero char delta**). |
| **Directive-Count Ratchet** (`test_directive_count_ratchet.py`) | AGENTS.md: 37<br>guardrails: 84<br>sec-guardrails: 6<br>shared-contracts: 4 | 37<br>84<br>6<br>4 | **0 headroom** across all 4 surfaces | DO NOT add `MUST`, `MUST NOT`, `NEVER`, `PROHIBITED`, `STRICTLY`, or `Gate FAIL` to any of these 4 files without deleting an equivalent keyword in the same file. |


---

## 1. Inventory of Detected Conflicts

### Conflict 1.1: `quick-win` Review/Test Requirement Ambiguity
- **Sites**:
  - `.agent/workflows/routing.md:188` (Command Registry lists `/review` and `/test` scope as `all non-tiny-fix`, which includes `quick-win`).
  - `engineering_guardrails.md §10.2` & `§10.4` (State that for `quick-win`, `review and test are optional when evidence is inline`).
  - `.agent/rules/state_machine.md:27` (Explicit fast-path: `IMPLEMENTING --(evidence provided, quick-win only)--> SHIPPED`).
- **Impact**: An agent querying `routing.md` will conclude `/review` and `/test` are mandatory for `quick-win`, contradicting the state machine and imposing unnecessary token/phase overhead.
- **Remediation**: Clarify scope column in `routing.md:188-189` to: `feature, architecture-change, hotfix (optional for quick-win)`.

### Conflict 1.2: `hotfix` Phase Sequence Inconsistency
- **Sites**:
  - `README.md:117`: `hotfix: Bootstrap → Research → Plan → Implement → Review → Test → Ship`.
  - `AGENTS.md §vNext State Model`: `hotfix → TESTED→SHIPPED` (omits explicit mention of research/review).
  - `.agent/rules/state_machine.md:38`: Permits transition directly from `CLASSIFIED` to `PLANNED` for `hotfix`.
  - `engineering_guardrails.md §10.2`: Marks `research (advisory, no gate receipt)`.
- **Impact**: An agent following `README.md` attempts to record a `Research` phase or receipt, which is flagged by the validator as receipt-less or invalid.
- **Remediation**: Align `README.md` and `AGENTS.md` wording to cite `research (advisory)`.

### Conflict 1.3: `tiny-fix` Dispatch Loop in `CLAUDE.md`
- **Sites**:
  - `CLAUDE.md:11`: `tiny-fix (< 3 files, no semantic change) → skip to Step 5`.
  - `CLAUDE.md:16` (Step 5): `If .agentcortex/context/work/<worklog-key>.md exists, read to resume. (Skip for tiny-fix.)`.
- **Impact**: Claude is instructed to jump to Step 5 for `tiny-fix`, but Step 5 immediately tells it to skip for `tiny-fix`. No execution guidance follows in that startup block.
- **Remediation**: Update `CLAUDE.md:11` to: `tiny-fix (< 3 files, no semantic change) → execute directly with diff + 1-line verification; skip Steps 3–5.`

### Conflict 1.4: Over-Constrained Description in `ship.md`
- **Sites**:
  - `.agent/workflows/ship.md:3`: `description: Final delivery and archival. Requires TESTED state and handoff gate.`
- **Impact**: Handoff is strictly mandatory **only** for `feature` and `architecture-change`. `quick-win` and `hotfix` are explicitly handoff-exempt (`state_machine.md:7`). An agent reading `ship.md` frontmatter falsely assumes all tasks require `/handoff`.
- **Remediation**: Update `ship.md` frontmatter to: `description: Final delivery, SSoT update, and work log archival. Requires TESTED state (and handoff gate for feature/architecture-change).`

### Conflict 1.5: Destructive Sync Script (`sync_skills.sh`)
- **Sites**:
  - `.agentcortex/tools/sync_skills.sh:33`: `cp "$meta_file" "$DEST_DIR/$skill_name"` (where `meta_file` is `$skill_path/agents/openai.yaml` and `DEST_DIR` is `.agent/skills`).
- **Impact**: `.agent/skills/<name>` files use Antigravity markdown format with YAML frontmatter pointing to `.agents/skills/<name>/SKILL.md`. If `sync_skills.sh` is run, it clobbers `.agent/skills/*` with raw OpenAI YAML schemas, breaking Antigravity tool loading! Furthermore, `deploy.sh:739` includes `sync_skills.sh` in the runtime tools deployed downstream.
- **Remediation**: Either rewrite `sync_skills.sh` to properly generate the Antigravity stub or remove it from `deploy.sh` deployed tools.

### Conflict 1.6: Empty Trigger Patterns for `verification-before-completion` in Registry
- **Sites**:
  - `.agent/workflows/routing.md:132`: Lists trigger phrases `"完成前檢查"`, `"verify before done"`, `"completion check"`.
  - `.agentcortex/metadata/trigger-registry.yaml:110`: `intent_patterns: []`.
- **Impact**: While it auto-activates via `phase_scope: [ship]`, natural language user requests matching the documented trigger phrases fail automated pattern matching (`pattern_match=False`).
- **Remediation**: Populate `intent_patterns` in `trigger-registry.yaml` with the phrases published in `routing.md`.

### Conflict 1.7: CJK Natural Language Matcher Defect (`[DEFECT-1]`)
- **Sites**:
  - `.agentcortex/tools/trigger_runtime_core.py:101`: `normalize_text` tokenizes via `re.findall(r"[\w]+", text)`.
- **Impact**: In CJK text without spaces (e.g. `幫忙除錯這個問題`), the clause becomes a single token `['幫忙除錯這個問題']`, which fails exact/subset matching against pattern `除錯`. 16 out of 19 known eval gaps in `run_skill_eval.py` stem from this word-boundary mismatch despite `AGENTS.md` prioritizing Traditional Chinese chat.
- **Remediation**: Add character n-gram or CJK substring scanning in `trigger_runtime_core.py:values_match`.

### Conflict 1.8: Global Lessons Hard Cap Saturation
- **Sites**:
  - `.agentcortex/context/current_state.md`: Contains exactly 20 lessons (hard cap 20/20 per `validate.ps1:121`).
- **Impact**: The next `/retro` that attempts to append a new lesson will trip the validator cap unless an older lesson is explicitly archived.
- **Remediation**: Identify candidate lessons for archival to `.agentcortex/context/archive/` during the next governance maintenance cycle.

---

## 2. Downstream Developer Experience (Traps & Blockers)

When a new downstream project runs `deploy_brain.sh` / `deploy_brain.ps1` and starts development, the following friction points can cause downstream agents or developers to become completely stuck:

### Trap 2.1: Windows Hard Dependency on Git Bash
- **Mechanism**: `installers/deploy_brain.ps1` and `deploy_brain.cmd` are wrappers that locate `bash.exe` and delegate to `deploy_brain.sh`.
- **Blocker**: If a Windows developer does not have Git for Windows or WSL installed (e.g., pure PowerShell / Windows Terminal user with Python/Node), the installer exits with: `[ERROR] Bash is required for deployment`.
- **Risk**: High for pure Windows native environments.
- **Mitigation**: Document prominently in `INSTALL.md` that Git for Windows (providing Git Bash) is a mandatory prerequisite, or provide a native PowerShell deployment path for text-only templates.

### Trap 2.2: PowerShell ExecutionPolicy Obstacle
- **Mechanism**: Running `./installers/deploy_brain.ps1` directly in PowerShell fails if the host system has `ExecutionPolicy Restricted` or `RemoteSigned` for untrusted scripts.
- **Blocker**: Downstream users receive script signing errors.
- **Mitigation**: Ensure all documentation and scripts specify `powershell -ExecutionPolicy Bypass -File ...`.

### Trap 2.3: Multi-Session / Interrupted Work Log Deadlock (`worklog_lock.mode: blocking`)
- **Mechanism**: `.agent/config.yaml` sets `worklog_lock.mode: blocking` and `stale_timeout_minutes: 60`.
- **Blocker**: If an AI chat session is aborted, restarted, or crashes mid-task, the lock file `.agentcortex/context/work/<branch>.lock.json` remains on disk. A fresh session attempting `/implement` or `/plan` encounters Exit Code 2 (active other-holder) and **Gate FAILs unconditionally**. Downstream agents get stuck in an unresolvable error loop because they lack operator authority to force-delete the lock.
- **Mitigation**:
  - Recommend `mode: advisory` for downstream templates (`.agentcortex/templates/`), OR
  - Update `bootstrap.md` to offer an interactive unlock command / self-heal takeover prompt when a stale session of the same agent host is detected.

### Trap 2.4: The "Spec Intake Gate" Wall for New Features
- **Mechanism**: Under `AGENTS.md` and `state_machine.md`, any task classified as `feature` MUST have `docs/specs/<feature>.md` before entering `/plan`.
- **Blocker**: When a downstream user casually prompts "Add login button to the navbar", the agent classifies it as `feature`, checks the spec index, and immediately returns:
  `gate: plan | classification: feature | verdict: fail | missing: [docs/specs/<feature>.md]`
  and stops. Non-technical users or agents without prior ACX experience don't know how to recover.
- **Mitigation**: Enhance `bootstrap.md` so that when `feature` is classified, the bootstrap output proactively prompts: *"Feature classification requires a spec. Would you like me to run `/spec` to draft `docs/specs/<feature>.md` now?"*

### Trap 2.5: Destructive `core.hooksPath` Overwrite
- **Mechanism**: `docs/INSTALL.md:51` suggests: `git config core.hooksPath .githooks`.
- **Blocker**: In projects already using Husky, Lefthook, or standard `.git/hooks/`, running this command completely replaces and disables their existing lint/test hooks.
- **Mitigation**: Emphasize integration into existing hook managers instead of blanket `core.hooksPath` replacement.

### Trap 2.6: SSoT Write Protection Confusion (`guard_context_write.py`)
- **Mechanism**: `guard_context_write.py` restricts updates to `current_state.md` to `/ship`.
- **Blocker**: Downstream agents often attempt to log task progress directly in `current_state.md` during `/implement` or `/review`, tripping the guard and failing with exit code 1.
- **Mitigation**: Ensure downstream `AGENTS.md` and prompts emphasize: *"Write task progress ONLY to .agentcortex/context/work/<branch>.md; never touch current_state.md directly."*

---

## 3. Skill & Workflow Description Optimization Recommendations

### A. Core Optimization Principles (Codex & Claude Cross-Host Standard)
Following the findings in `docs/reviews/2026-09-09-cross-model-skill-handback.md`:
1. **Conditions Before Technique**: Start with trigger conditions (`Use when [action/condition]...`), not abstract adjectives or internal framework names.
2. **Rich in Scope & Failure Signals**: Directly incorporate tokens like "login", "SQL migration", "HTTP endpoint", "test failure", "unexpected behavior".
3. **No Vendor / Framework Jargon**: Avoid mentioning `/review`, `/ship`, `Antigravity`, or `4-phase` in the portable `description` frontmatter.

### B. Proposed Wording for 12 Unoptimized Skills
*(Note: `systematic-debugging` and `production-readiness` were already optimized on 2026-09-09).*

| Skill | Current Description | Proposed Concise Description | Rationale |
|---|---|---|---|
| `api-design` | `Design or review REST/GraphQL APIs when endpoints or contracts change.` | `Use when creating, modifying, or reviewing REST/GraphQL endpoints, request validation, error responses, pagination, or API contracts.` | Adds explicit keywords (`endpoints`, `validation`, `pagination`) that trigger model selection. |
| `auth-security` | `Secure authentication and authorization when credentials, sessions, roles, or permissions change.` | `Use when touching authentication, login, tokens, password hashing, session cookies, RBAC permissions, or sensitive credential handling.` | Front-loads concrete security surfaces (`login`, `tokens`, `hashing`, `cookies`). |
| `database-design` | `Design schemas and migrations when persistent data structures change.` | `Use when creating or altering database tables, schema models, SQL migrations, foreign keys, indexes, or data persistence logic.` | Embeds `SQL`, `migrations`, `indexes`, `foreign keys` for direct intent matching. |
| `dispatching-parallel-agents` | `Evaluate when to dispatch parallel agents; use a 4-step pattern to split, coordinate, and integrate results.` | `Use when a task has independent, decoupled sub-modules or multi-file research that can be safely executed concurrently by parallel agents.` | Replaces technique reference ("4-step pattern") with explicit decomposition conditions. |
| `doc-lookup` | `Check official docs when framework APIs or configuration may be version-sensitive.` | `Use before coding when integrating third-party libraries, framework APIs, SDKs, or tools where configuration or syntax may be version-sensitive.` | Guides the agent to trigger *before* coding, reducing hallucinated parameters. |
| `frontend-patterns` | `Apply frontend conventions when components, pages, forms, or client state change.` | `Use when building or updating UI components, pages, client-side state, form validation, or frontend layout patterns.` | Clarifies UI scope (`components`, `pages`, `forms`, `layout`). |
| `karpathy-principles` | `Behavioral guidelines to reduce common LLM coding mistakes — Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.` | `Use during planning and implementation for non-trivial code changes to keep diffs surgical, avoid premature abstractions, and prevent over-engineering.` | Moves from passive label ("Behavioral guidelines") to active condition ("Use during planning and implementation..."). |
| `red-team-adversarial` | `Adversarial security and resilience analysis — auto-triggered during /review and /test based on task classification. Provides attack surface analysis, boundary testing, auth bypass attempts, dependency chain attacks, and Beast Mode stress testing.` | `Use during review or test to perform adversarial stress testing: probe attack surfaces, boundary conditions, auth bypasses, and failure modes.` | Strips verbose metadata ("auto-triggered during...", "Beast Mode"); focuses on stress testing triggers. |
| `subagent-driven-development` | `Decompose tasks via subagent collaboration; define interface contracts and integration checkpoints.` | `Use when coordinating multi-step or multi-agent tasks with explicit input/output contracts, handoffs, and verification checkpoints.` | Clarifies coordination and verification contracts. |
| `test-driven-development` | `Drive changes with Red→Green→Refactor; ensure behavior is verifiable and regression-safe.` | `Use when implementing logic or fixing regressions where expected behavior can be defined by failing unit or integration tests before coding.` | Establishes test-first condition before coding. |
| `using-git-worktrees` | `Use Git worktrees to create parallel working directories safely; avoid branch-switch contamination.` | `Use when managing parallel branches, concurrent feature development, or emergency hotfixes without dirtying or stashing the active worktree.` | Specifies parallel branch and hotfix isolation scenarios. |
| `verification-before-completion` | `Enforce "no evidence = no completion"; run Gate Function verification before declaring done.` | `Use before claiming completion or entering /ship to verify reproducible test evidence, diff scope, and gate criteria.` | Places completion timing condition at the front. |

### C. Proposed Workflow Description Updates
1. **`.agent/workflows/ship.md`**:
   - Current: `description: Final delivery and archival. Requires TESTED state and handoff gate.`
   - Proposed: `description: Final delivery, SSoT update, and work log archival. Requires TESTED state (and handoff gate for feature/architecture-change).`
2. **`.agent/workflows/routing.md` Registry Table**:
   - Update `/review` and `/test` scope to clarify that they are optional for `quick-win`.
3. **`.agent/workflows/bootstrap.md`**:
   - Add clear forward-linkage in Feature Classification report guiding users to `/spec`.

---

## 4. Decision Matrix for Claude's Judgment

Claude is requested to evaluate and decide on the following implementation batches:

| Decision Item | Options | Recommendation | Rationale |
|---|---|---|---|
| **D1: Worklog Lock Mode for Downstream** | A) Keep `blocking` globally<br>B) Make downstream template default to `advisory`<br>C) Retain `blocking` but add automated session takeover in bootstrap | **Option B or C** | `blocking` causes frequent deadlocks in multi-turn / multi-session agent chats. |
| **D2: Hazardous `sync_skills.sh`** | A) Fix script to write Antigravity markdown format<br>B) Delete script and remove from `deploy.sh`<br>C) Keep script as-is | **Option A or B** | Current line 33 clobbers `.agent/skills/*` with raw OpenAI yaml schemas. |
| **D3: Skill Description Refinement (CRITICAL: 113-token headroom)** | A) Adopt all 12 proposed skill descriptions with **net-zero character delta** (trim equivalent characters from the skill body markdown to stay under the 355k ceiling)<br>B) Formally bump the 355k token ratchet ceiling in `test_lifecycle_token_consumption.py` via owner authorization<br>C) Phased rollout (e.g. 2 skills per PR, strictly observing headroom) | **Option A (Net-zero char trimming)** | **CRITICAL FINDING**: Measured headroom in `test_aggregate_current_total_stays_under_355k` is currently **only 113 tokens** (354,887 / 355,000)! Because `estimate_tokens` in the lifecycle test measures `len(SKILL.md)/4 * load_count`, adding characters to frontmatter without trimming body text **will immediately break CI**. |
| **D4: Clarification of `quick-win` Review Scope** | A) Update `routing.md` registry table<br>B) Leave as `all non-tiny-fix` and rely on guardrails text | **Option A** | Closes discrepancy between routing table and state machine. |
| **D5: CJK Word-Boundary Matcher (`DEFECT-1`)** | A) Fix regex in `trigger_runtime_core.py`<br>B) Defer to issue #150 / future PR | **Option B** | `detect_by.intent_patterns` has no live runtime consumer during normal agent chat; deferring avoids risk to core trigger engine. |

---

## 5. Verification Record & Test Parity
- Run under: Windows 11, Python 3.14.3, Pytest 8.4.1.
- `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -m "not slow"`: **805 passed, 146 deselected (exit code 0)**.
- `powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1`: **pass=99, warn=4, fail=0, skip=3 (exit code 0)**.
- `python .agentcortex/tools/check_skill_provenance.py`: **PASS (14 skills)**.
- `python .agentcortex/tools/check_command_sync.py`: **PASS (30 commands)**.
- `python .agentcortex/tools/check_lifecycle_frontmatter.py`: **PASS (14 files)**.
