# Changelog

## [5.4.0] - 2026-03-24

### 🔍 Command Discovery & Skill Activation Overhaul

- **14 new dispatch files** (`.claude/commands/`): adr, audit, brainstorm, help, hotfix, research, retro, spec, sync-docs, govern-docs, test-skeleton, worktree-first, ask-openrouter, codex-cli. Total commands: 11 → 25.
- **Intent Router expanded**: AGENTS.md §6 now covers 30+ bilingual intent mappings (EN + 繁中) across all 25 user-facing commands, organized by category.
- **Skill Activation Triggers**: All 16 skills now have natural language triggers in the Intent Router for manual activation (e.g., "用 TDD", "先寫測試" → `test-driven-development`).

### 🧠 Deterministic Skill Recommendation

- **bootstrap.md §3.6**: Replaced vague "select 0-2 skills" with deterministic rule table. Four categories: Mandatory, Scope-Detected, Phase-Triggered, Complexity-Conditional. Each entry includes `Phases` column for phase-entry loading.
- **Dual Activation Model** (AGENTS.md §9.4-9.5): Skills activate via Auto (bootstrap rule table) + Manual (Intent Router). No more 0-2 limit — recommend ALL matching skills.
- **Typical feature task now activates 4-8 skills** (vs. 0-2 previously).

### ⚡ Skill Behavioral Enforcement

- **implement.md — Skill Execution Overrides**: Skills now change actual implementation behavior, not just declarations. TDD enforces Red→Green→Refactor micro-cycles. api-design enforces endpoint validation. database-design enforces migration safety (with guardrails-aware caveat for forward-only ORMs). auth-security enforces hashing, token handling, rate limiting. systematic-debugging pauses implementation for 4-phase process. verification-before-completion enforces 5-gate check before claiming done.
- **test.md — Skill-Aware Test Implementation**: Mandatory test case checklists auto-generated per active skill (auth 401/403/token tests, API validation/pagination tests, DB migration/constraint tests, frontend 4-state tests). TDD gap detection verifies every production code path has a test.
- **ship.md — Skill-Aware Ship Checks**: verification-before-completion 5-gate sequence (Scope→Quality→Evidence→Risk→Communication) blocks ship if any gate fails. finishing-a-development-branch enforces mainline re-sync, re-test, and explicit closure option selection.
- **review.md**: Already had skill-aware review (unchanged, serves as the model for other phases).

### 🔧 Review Fixes

- **ship.md**: Replaced hardcoded `origin/main` with dynamic `origin/<main-branch>`.
- **AGENTS.md**: Disambiguated overlapping intent triggers ("parallel branch" → `/worktree-first` vs. "git worktree" → skill).
- **bootstrap.md**: Fixed `verification-before-completion` skip condition (Never → tiny-fix).
- **implement.md/test.md**: Added guardrails-precedence caveat for migration reversibility (forward-only ORMs respected).

### Migration Notes

- Downstream projects: see `.agentcortex/docs/MIGRATION_GUIDE_v5.4_command_discovery.md` for step-by-step upgrade instructions.
- Run `deploy_brain.sh` to update framework files after pulling this version.

## [5.3.1] - 2026-03-23

### 🔧 Downstream Spec/ADR Path Restoration

- **Fixed Anchor Restoration**: Reversed ace7fea consolidation that incorrectly moved downstream spec/ADR paths into framework directories. Project specs now go to `docs/specs/`, project ADRs to `docs/adr/` (not `.agentcortex/specs/` or `.agentcortex/adr/`). Framework template specs and ADR-001 remain in `.agentcortex/`.
- **Write Path Guard**: New rule in `bootstrap.md` (all classifications) and `engineering_guardrails.md` preventing AI agents from writing project artifacts to `.agentcortex/` directories.
- **Orphan Recovery**: `deploy.sh` auto-detects non-framework specs/ADRs stranded in `.agentcortex/` (from ace7fea era) and migrates them to `docs/` with collision-safe `mv` (skips if destination exists).
- **Deploy Safety**: `deploy.sh` now creates `docs/specs/` and `docs/adr/` directories during install; removed incorrect `rmdir` of fixed anchor dirs; added destination existence check before orphan migration.
- **SSoT Clarification**: `current_state.md` Spec Index header now distinguishes framework specs (`.agentcortex/specs/`) from project specs (`docs/specs/`).
- **Validation**: `validate.sh` must-track checks now include `docs/specs/` and `docs/adr/`.

### Migration Notes

- **From ace7fea era**: Run `deploy_brain.sh` — orphaned specs/ADRs in `.agentcortex/specs/` and `.agentcortex/adr/` will be auto-migrated to `docs/specs/` and `docs/adr/`.
- **From pre-ace7fea**: No action needed — `docs/specs/` and `docs/adr/` were already the correct paths.
- **Directory ownership**: `docs/specs/` and `docs/adr/` are project-owned (committed to git). `.agentcortex/specs/` and `.agentcortex/adr/` are framework-owned (template fixtures only).

## [5.3.0] - 2026-03-19

### 🧠 Design Philosophy & Governance Hardening

- **10 Non-Negotiable Principles**: Rewrote `AGENT_PHILOSOPHY.md` (EN + zh-TW) from 33-line positioning doc into comprehensive P1-P10 principles document with Safety Mechanisms reference table.
- **Namespace Isolation** (engineering_guardrails.md §9.4): New rule preventing AgentCortex from hijacking downstream custom commands. Uses `.agentcortex-manifest` (not directory paths) as the framework-vs-user boundary. User commands always take priority.
- **Decisions Injection Defense**: Bootstrap now surfaces inherited Work Log decisions to user for confirmation before treating them as binding.
- **Sentinel Cross-Model Clarity**: AGENTS.md §11 rewritten from Claude-specific "prompt truncation" to model-agnostic "framework-wide runtime integrity marker".

### 🛡️ Security Fixes (deploy.sh)

- **CP_FLAG Whitelist**: Environment variable validated against allowlist (`-i -v -p -n -f -a`), rejecting command substitution attempts like `$(...)`.
- **Manifest Path Traversal**: `manifest_all_paths()` now rejects paths containing `..` or starting with `/`.
- **Counter Bug Fix**: Pass 2 untrack counter no longer inflates when `git rm --cached` fails on already-untracked files.
- **TOCTOU Removal**: Eliminated check-then-act patterns (`ls-files` before `git rm --cached`).
- **O(n) Manifest Diff**: Replaced O(n²) per-file grep with single awk two-file pass for removal detection.

### ⚡ Skill & Workflow Optimization

- **12 Skill Metadata Upgraded**: All skill files now declare `phases`, `trigger`, and quick-reference — enabling AI-autonomous activation without human prompting.
- **`/test` Rewrite**: 5-step AI-autonomous flow (classify → skeleton → implement → adversarial → evidence) replacing fragmented references.
- **Minimal Workflows Expanded**: `/hotfix` (escalation logic), `/brainstorm` (confidence scoring + /decide integration), `/research` (autonomous recommendation), `/adr` (alternatives-considered + when-to-create guidance).
- **Centralized Config**: Created `.agent/config.yaml` for governance constants (`WORKLOG_MAX_LINES`, `MAX_KB`, `KEEP_RECENT_ENTRIES`), replacing inline hardcoding in handoff/implement/ship.
- **deploy.sh Deduplication**: Extracted shared `FRAMEWORK_DIRS`, `is_git_repo()`, `keep_tracked()` helpers.

## [5.2.0] - 2026-03-16

### 🔧 Deploy Downstream Gitignore & Completeness Fix

- **Downstream .gitignore**: `write_downstream_ignore_block()` now includes all framework paths (`.agent/`, `.agents/`, `.agentcortex/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, `deploy_brain.*`, `.agentcortex/bin/validate.*`, `.agentcortex-manifest`, etc.) so downstream projects no longer accidentally commit framework files.
- **Missing doc deployments**: Added `NONLINEAR_SCENARIOS*.md` and `PROJECT_OVERVIEW*.md` to the deploy glob — previously these docs existed in the repo but were never deployed to downstream.
- **GitHub templates**: `.github/ISSUE_TEMPLATE/agent_issue.md` and `.github/PULL_REQUEST_TEMPLATE.md` are now deployed (directory was created but files were never copied).
- **Managed array sync**: `strip_managed_ignore_blocks` managed array updated to match actual deployed paths, with comment-line stripping for clean block replacement.
- **Cleanup**: Removed unused `mkdir` for `.agentcortex/templates` and `.agentcortex/specs` (never populated).

## [5.1.0] - 2026-03-16

### 🛡️ Manifest Deploy & Security Guardrails

- **Manifest-based smart deploy**: `deploy_brain.sh` now tracks all deployed files in `.agentcortex-manifest` with sha256 hashes. Updates intelligently skip user-modified scaffold/wrapper files, writing `.acx-incoming` sidecars for manual review.
- **Tier classification**: Files classified as `core` (always overwrite), `scaffold` (skip if modified), or `wrapper` (skip if modified). Summary reports `N updated / N skipped / N new / N removed`.
- **Security guardrails**: Added `.agent/rules/security_guardrails.md` with auto-enforced AI self-check mechanisms across implement, review, and ship workflows.
- **Confidence Gate**: Inserted confidence gate in plan/spec-intake workflows with updated cross-references.

## [5.0.0] - 2026-03-05

### 🛡️ Runtime v5 Anti-Drift & Concurrency Release

- **Gate Engine & Handshake**: Implemented a hard-path enforcement overlay for `plan`, `ship`, and `implement` workflows. High-risk tasks now require explicit `PROCEED-<STAGE>:<branch>` contextual handshakes to continue.
- **Skill Safety Guardrails**: Established strict precedence (`AGENTS.md` > `workflows` > `skills`) to prevent Antigravity semantic skills from hijacking execution loops.
- **Multi-Session Concurrency**: Added `Owner` and `Session` metadata requirements to Work Logs. `/bootstrap` now checks for concurrent edits to prevent collisions.
- **Legacy Migration Safety**: Introduced the `/audit` workflow for read-only system mapping of non-AgentCortex repos.
- **SSoT Append-only History**: Changed `current_state.md` to use an append-only `## Ship History` for safer archival.
- **Sentinel Token**: Injected `SENTINEL: ACX-READ-OK` to combat context truncation.

## [3.5.4] - 2026-03-04

### 🔌 External Tool Integration (Natural Language Driven)

- **ask-openrouter workflow**: New `[OPTIONAL MODULE]` workflow (`.agent/workflows/ask-openrouter.md`) enabling natural language delegation to OpenRouter models. Features 3-layer architecture: Intent Router, Pre/Post-Flight, and Dynamic Parameter Assembly.
- **codex-cli alignment**: Updated `codex-cli.md` with `[OPTIONAL MODULE]` tag, silent availability check, and `§8.2` reference for consistency.
- **§8.2 External Tool Delegation Protocol**: New section in `engineering_guardrails.md` defining shared rules for all external CLI tools — silent availability check, cost-tier confirmation, and mandatory Pre/Post-Flight.
- **Graceful degradation**: Users without external tools experience zero disruption — AI silently falls back to native execution.
- **Deploy script**: Bumped to v3.5.4. Added `.openrouter/` to gitignore template.
- **SSoT update**: Registered both tools as `[OPTIONAL]` in `current_state.md` Canonical Commands.

## [3.5.2] - 2026-02-27

### ⚖️ Governance Refinement & Directory Polish

- **指令語義優化**: 修正 `/test-skeleton` 的啟動狀態門檻為 `IMPLEMENTABLE`；為 `/implement` 與 `/execute-plan` 加入硬性進入條件提示（state machine 對齊）。
- **平台技能隔離**: 更新 `AGENTS.md` 與 `README.md`，明確區分 `.agent/skills` 與 `.agents/skills` 為平台獨立目錄，取消自動符號連結以增加配置彈性。
- **Token 反思機制**: 在 `/handoff` 工作流加入 `Token & Efficiency Reflection` 區塊，落實自我管理哲學。
- **清理修復**: 移除了已棄用的 `.agent/workflows/` 冗餘檔案（`update-docs.md`, `docs-update.md`）。

## [3.5.1] - 2026-02-27

### 🛠️ Directory Structure & Multi-Platform Support

- **部署升級**: `deploy_brain.sh` 升級為 v3.5.1，全面支援 vNext 目錄結構。
- **文件策略修復**: 修正 `AGENTS.md` 中的「盲目掃描」反模式，改為基於 `current_state.md` 的精準讀取。
- **Token 極致壓縮**: `rules.md` 與 `AGENTS.md` 完成大幅度內縮優化，節省每回合啟動開銷。

## [3.5.0] - 2026-02-27

### 🚀 vNext Self-Managed Architecture Release

- **SSoT 狀態模型**: 導入 `.agentcortex/context/current_state.md` 作為唯一真實來源，任務隔離於 `.agentcortex/context/work/` 目錄。
- **工作流全面遷移**: 所有 superpowers 遷移至 `.agent/workflows/`，對齊 Google Antigravity 原生指令。
- **任務分類凍結**: `/bootstrap` 現在強制執行任務分類並凍結，防止開發路徑偏離。
- **遷移工具**: 新增 `.agentcortex/docs/guides/migration.md`，支援從舊版 v3.0 無縫升級。

## [3.4.0] - 2026-02-23

### 🚀 Release v3.4.0 (Version Sync + Practical Examples)

- **版本同步**: `README.md`、`.agent/AGENT.md`、`deploy_brain.sh` 全面升級為 v3.4.0。
- **實戰範例**: 新增 `docs/PROJECT_EXAMPLES.md`，提供 Node.js（Express + Vitest）與 Python（FastAPI + pytest）導入流程。
- **部署擴充**: `deploy_brain.sh` 現在會部署 `docs/PROJECT_EXAMPLES.md`。
- **驗證強化**: `validate.sh` 新增 `PROJECT_EXAMPLES.md` 存在檢查，並驗證 README 已連結範例文件。

## [3.3.1] - 2026-02-23

### 🔧 Superpowers Features Completion & README Clarity

- **功能補齊**: 新增 `.agent/superpowers/features/` 模組，包含 `brainstorm`, `research`, `spec`, `execute`, `review`, `retro` 六種能力檔案。
- **指令擴充**: `.agent/superpowers/commands.md` 新增 `/brainstorm`, `/research`, `/spec`, `/retro` 指令模板。
- **工作流深化**: `.agent/superpowers/workflows.md` 納入探索型開發節奏（Idea → Spec → Plan → Implement → Review/Test）。
- **操作文件強化**: `README.md` 補上「原始操作流程」與「如何呼叫各功能檔案」的完整範例。
- **部署修正**: `deploy_brain.sh` 支援部署 `.agent/superpowers/features/*.md`。
- **可用性驗證**: 新增 `/.agent/superpowers/validate.sh`，可一鍵檢查指令、功能檔與 README 對應是否一致。
- **命名一致性**: 新增 `features/implement.md` 並將 `execute.md` 改為相容別名，避免 `/implement` 指令對不上檔名。
- **能力補齊**: 新增 `features/bootstrap.md`（任務啟動）與 `features/handoff.md`（跨回合交接）。
- **Codex 平台相容**: 新增 `docs/CODEX_PLATFORM_GUIDE.md`，提供 Web 與 App 兩端一致操作建議。
- **參考來源標註**: README 新增 Superpowers 原始專案連結，明確標示設計參考來源。
- **規範稽核強化**: `validate.sh` 新增平台文件與 AGENT 引用檢查，並驗證 README 含參考來源。
- **流程強制化**: 新增 `policies/methodology.md` 與 `policies/state_machine.md`，導入 workflow gate 與完成條件。
- **Codex 入口**: 新增 `.codex/INSTALL.md`，支援一句話「Fetch and follow instructions ...」載入流程。
- **指令別名**: 新增 `/write-plan`、`/execute-plan` 對齊 Superpowers 常見命名。

## [3.3.0] - 2026-02-23

### 🧩 Superpowers Alignment for Google Antigravity

- **流程升級**: `README.md` 改版為 Antigravity Superpowers Edition，加入 Plan → Implement → Review → Test 的標準節奏。
- **Agent 強化**: `.agent/AGENT.md` 新增 Superpowers 導向執行模式，明確化可重複操作流程。
- **Prompt 工具箱**: 新增 `.agent/superpowers/commands.md`，提供可直接貼用的高訊噪比指令模板。
- **工作流卡片**: 新增 `.agent/superpowers/workflows.md`，涵蓋小修補、中型功能、Hotfix 與文件治理場景。
- **部署腳本更新**: `deploy_brain.sh` 支援部署 `.agent/superpowers/` 內容與 v3.3 版本訊息。

## [3.2.0] - 2026-02-14

### 🧪 Zero-Token Enhancements (零成本工作流強化)

- **品質閘門**: 新增 `.github/PULL_REQUEST_TEMPLATE.md`，標準化 AI 的產出總結與自檢項目。
- **測試規範**: 新增 `docs/TESTING_PROTOCOL.md`，提供邊際情況與錯誤處理的測試標準，採 Opt-in (手動呼叫) 模式以節省 Token。
- **部署擴充**: `deploy_brain.sh` 現在完整支援所有 v3.2 文檔與模板。

## [3.1.0] - 2026-02-14

### ⚖️ Agent-First Constitution (憲法級架構)

- **憲法層級**: 新增 `.agent/rules/engineering_guardrails.md`，定義 Agent 不可違背的工程準則。
- **協作介面**: 新增 `.github/ISSUE_TEMPLATE/agent_issue.md`，將任務描述結構化。
- **角色 manifest**: 新增 `docs/AGENT_PHILOSOPHY.md`，定義 AI 與人類的協作邊界。
- **腳本優化**: `deploy_brain.sh` 支援部署隱藏資料夾（.github）與文檔。

## [3.0.0] - 2026-02-14

### 🪶 Pragmatic Lean (務實精小版)

- **Radical Simplification**: 將 40+ 個檔案整理為 1 個核心 Prompt (`AGENT.md`)，系統提示開銷降低 94%。
- **Antigravity-Native**: 專位 Google Antigravity 打造，利用 IDE 自動讀取 `.agent/` 目錄的特點，減少手動配置。
- **Human-Centric Guidance**: 移除無效的自動路由，改由 `AGENT_MODEL_GUIDE.md` 指引用戶手動切換模型，確保正確使用 Flash/Pro/Advanced 模型。
- **Audit Implementation**: 合併精華版 PII 掩碼、Secrets 偵測與編碼規範。

## [2.6.5] - 2026-02-13

### 🚀 Flash-First Strategy (重大策略轉變)

- **架構反轉**: 核心邏輯改為以 Flash 為主體，處理 80% 低成本任務。
- **升級請求 (Escalation)**: 當背景超出 Flash 負荷時，模型會主動停止並提示切換至 Pro，確保 100% 節省 Pro Token。
- **新版 README**: 強調操作流程的改變，降低 Token 誤用風險。

## [2.5.1] - 2026-02-13

### 🛡️ Security & Language

- **強制語言**: 全局強制使用繁體中文 (台灣) 進行對話。
- **隱私加固**: `08_compliance` 加入 PII 掩碼規則。
- **漏洞掃描**: `08_code_review` 加入 OWASP Top 10 與 Secrets 掃描指南。

## [2.5.0] - 2026-02-13

### ✨ Added

- **重大升級**: 正式進入工業級架構 (Industrial-Grade)。
- **元數據驅動**: 全檔案加入 YAML frontmatter 支援元數據解析。
- **精細化 Thresholds**: 支援各工作流自定義 Token 閾值，極大化節省成本。
- **新增 4 大工作流**: 工程開發 (`01`)、內容創作 (`10`)、數據報表 (`11`)、環境自檢 (`12`)。
- **新增 3 大規則**: 安全合規 (`08`)、格式標准 (`09`)、指令設計 (`10`)。
- **新增 3 大技能**: 質量審查、圖表建議、架構設計。

### 🚀 Optimized

- **Meta Router**: 升級動態信心調節與多階執行邏輯。
- **README**: 全面繁體中文優化，新增「擴充指南」範例。
- **Deployment**: `deploy_brain.sh` 支援更精確的模組複寫。
