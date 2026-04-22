---
description: Canonical human-readable routing index for intent-driven routing
authority: lookup-only — AGENTS.md outranks this file; workflows outrank skills
canonical: true
---

# Routing Index

This file is the **canonical lookup table** for natural-language trigger phrases.
It is consulted at routing time, ambiguity resolution time, or command discovery time.
It does NOT contain governance rules — those remain in `AGENTS.md`.

**Precedence**: `AGENTS.md` > `.agent/workflows/routing.md` > `.agent/skills/`

---

## 1. Workflow Trigger Map

> **Auto-suggest when** column: Present only in sections where phase-lifecycle or classification context can trigger the workflow without an explicit user phrase. Core Phase Workflows, Spec & Intake, Emergency & Fix, Testing Helpers, and Utility sections do not have this column — they are routed explicitly or through governance gates.

### Core Phase Workflows

| Phrases | Route |
|---|---|
| "help me design", "幫我規劃" | `/plan` |
| "ship this", "上線吧" | `/ship` |
| "implement this", "開始寫", "動手做" | `/implement` |
| "review this", "幫我看看", "code review" | `/review` |
| "run tests", "跑測試", "verify" | `/test` |
| "typo", "rename variable" | tiny-fix (execute directly) |

### Spec & Intake

| Phrases | Route |
|---|---|
| "here's my spec", "我有一個spec", "這是產品規格", user pastes a spec doc, user gives a file path to a spec | `/spec-intake` (do NOT jump directly to bootstrap or plan) |
| "next feature", "下一個", "繼續做", "continue with backlog" | `/spec-intake` §8a continuation (read `_product-backlog.md`, skip decomposition) |
| "改 spec", "amend the spec", "spec 要調整" | `/spec-intake` §8b amendment (check spec status, apply timing rules) |
| "先做 #5", "reorder", "defer #3", "不做了" | `/spec-intake` §8c reorder/defer/cancel |
| "寫規格", "write spec", "convert requirements" | `/spec` |

### Architecture & Setup

| Phrases | Route | Auto-suggest when |
|---|---|---|
| "設定架構", "init app", "define tech stack", "set up project" | `/app-init` (full) | — |
| "加後端", "set up [layer]", "define [layer] conventions", "加 API", "加資料庫" | `/app-init --partial` (mid-development) | — |
| "新增 skill", "add skill for X" | `/app-init` §3 (skill-only generation) | — |
| "architecture decision", "為什麼選這個", "record decision", "ADR" | `/adr` | tech stack selection detected in /plan |

### Emergency & Fix

| Phrases | Route |
|---|---|
| "production bug", "緊急修復", "urgent fix", "hotfix" | `/hotfix` |
| "bootstrap", "開始新任務", "start task" | `/bootstrap` |

### Research & Analysis

| Phrases | Route | Auto-suggest when |
|---|---|---|
| "研究一下", "investigate", "explore", "look into this" | `/research` | hotfix classification; uncertainty about root cause in /implement |
| "腦力激盪", "brainstorm", "explore options", "what are our choices" | `/brainstorm` | feature/arch-change with no frozen spec (bootstrap §3.7) |
| "audit this repo", "評估現狀", "map existing code" | `/audit` | first session in a new module, no ADR exists |

### Completion & Handoff

| Phrases | Route | Auto-suggest when |
|---|---|---|
| "交接", "handoff", "summarize for next session" | `/handoff` | — |
| "記錄決定", "log decision", "why did we choose" | `/decide` | design fork detected in /plan or /implement (see plan.md Pre-Plan Advisory) |
| "回顧", "retrospective", "lessons learned", "retro" | `/retro` | after /ship completes (ship.md lifecycle hook) |

### Documentation

| Phrases | Route | Auto-suggest when |
|---|---|---|
| "同步文件", "sync docs", "docs out of date" | `/sync-docs` | /ship touches docs/specs/ or docs/architecture/ files |
| "更新治理文件", "update governance docs" | `/govern-docs` | /ship release includes .agent/ or AGENTS.md changes |

### Testing & Planning Helpers

| Phrases | Route |
|---|---|
| "test blueprint", "測試骨架", "test structure only" | `/test-skeleton` |
| "classify tests", "測試分級" | `/test-classify` |
| "worktree", "parallel branch", "隔離分支" | `/worktree-first` |

### Utility & Help

| Phrases | Route |
|---|---|
| "help", "有什麼指令", "commands" | `/help` |

---

## 2. Optional Module Trigger Map

> **Hard Rule (from AGENTS.md)**: Optional modules are explicit opt-in. The AI MUST NOT silently choose any optional module. Phrases in this section only activate a module when the user **clearly requests** it.

| Phrases | Module | Condition |
|---|---|---|
| "ask openrouter", "用其他模型" | `/ask-openrouter` | requires CLI |
| "run with codex", "用 codex" | `/codex-cli` | requires CLI |
| "run with claude", "用 claude", "用 claude-cli", "implement 交給 claude", "實作交給 claude", "測試交給 claude", "讓 claude 寫", "讓 claude 跑測試" | `/claude-cli` | requires CLI; MUST NOT auto-trigger |

---

## 3. Skill Activation Trigger Map

> **This table IS the canonical skill index** — it maps every user-facing trigger phrase to a skill ID. For "what skills are available?" questions, this is the answer. Skill bodies live in `.agents/skills/<skill>/SKILL.md`; trigger metadata (phases, cost_risk, load_policy) lives in `.agentcortex/metadata/trigger-compact-index.json` when present.
>
> Skills activated via the Intent Router attach to the **current workflow phase only**. They MUST NOT replace, skip, or alter phase order. See AGENTS.md §Skill Safety & Precedence for the full hard rule.

| Phrases | Skill |
|---|---|
| "用 TDD", "test first", "先寫測試", "red green refactor" | `test-driven-development` |
| "API 設計", "endpoint conventions", "REST design" | `api-design` |
| "資料庫設計", "schema design", "migration safety" | `database-design` |
| "前端模式", "component patterns", "UI conventions" | `frontend-patterns` |
| "安全檢查", "auth check", "security review", "權限檢查" | `auth-security` |
| "紅隊測試", "adversarial test", "red team", "攻擊面分析" | `red-team-adversarial` |
| "debug", "除錯", "systematic debugging", "找 bug" | `systematic-debugging` |
| "平行開發", "parallel agents", "dispatch subtasks" | `dispatching-parallel-agents` |
| "subagent", "分派 agent", "multi-agent" | `subagent-driven-development` |
| "完成前檢查", "verify before done", "completion check" | `verification-before-completion` |
| "執行計畫", "execute the plan", "follow the plan" | `executing-plans` |
| "完成分支", "finish branch", "wrap up branch", "merge 準備" | `finishing-a-development-branch` |
| "接收 review", "review feedback", "收到 review 意見" | `receiving-code-review` |
| "請求 review", "request code review", "送 review", "要 review" | `requesting-code-review` |
| "用 worktree", "git worktree", "worktree 隔離" | `using-git-worktrees` |
| "寫計畫", "write plan", "規劃怎麼做" | `writing-plans` |
| "查文件", "check docs", "查官方文檔", "read the docs", "看文件再做" | `doc-lookup` |

---

## 4. Ambiguity Rules

1. **spec-intake vs bootstrap**: If the user provides a spec document or file path containing multiple features, route to `/spec-intake` — NOT directly to `/bootstrap` or `/plan`. Single-feature input without a spec document may proceed to `/bootstrap`.

2. **Optional module ambiguity**: A phrase like "用 claude" requires clear delegation intent. Ambiguous phrasing (e.g., "can Claude do this?") does NOT trigger `/claude-cli`. Require explicit delegation request before routing to any optional module.

3. **tiny-fix vs quick-win escalation**: Modifying `docs/specs/`, `docs/architecture/`, any file with `status: frozen`, `AGENTS.md`, `.agent/rules/*.md`, or `.agent/config.yaml` always escalates to quick-win minimum — even if fewer than 3 files are touched. (Authoritative rule in AGENTS.md §Agentic OS Runtime v5 rule 2.)

4. **Skill vs workflow**: If a user's request matches both a skill phrase (§3) and a workflow route (§1), route to the workflow phase first and activate the skill within that phase. Skills do not replace phase routing.

5. **Skill manual activation block**: Even when a user explicitly requests a skill, the bootstrap rule table's `Skip when` column governs. If the rule table says skip for the current classification, manual activation is blocked.

6. **Pinned skill vs skip-when precedence**: Pinned skills from user preferences (`.agentcortex/context/private/user-preferences.yaml`) follow the same skip-when rules as manually activated skills UNLESS the pin entry includes `force: true`. Force-pinned skills override skip-when but still respect `phase_scope` boundaries — a skill cannot activate in a phase it was never designed for. This is the ONLY mechanism that can override skip-when; manual activation (rule 5) cannot. See bootstrap §3.6a.

---

## 5. Command Discovery Notes

All commands are dispatched per `AGENTS.md §Agentic OS Runtime v5` and execute canonical workflows from `.agent/workflows/<command>.md`. For the Claude platform, dispatcher stubs live in `.claude/commands/<command>.md`.

> **Note**: `.agent/workflows/commands.md` is a compatibility alias. This routing index is the canonical source for command discovery.

### Command Registry

| Command | Workflow File | Classification Scope |
|---|---|---|
| `/bootstrap` | `.agent/workflows/bootstrap.md` | all non-tiny-fix |
| `/plan` | `.agent/workflows/plan.md` | feature, architecture-change, quick-win |
| `/implement` | `.agent/workflows/implement.md` | all non-tiny-fix |
| `/review` | `.agent/workflows/review.md` | all non-tiny-fix |
| `/test` | `.agent/workflows/test.md` | all non-tiny-fix |
| `/ship` | `.agent/workflows/ship.md` | all non-tiny-fix |
| `/spec-intake` | `.agent/workflows/spec-intake.md` | multi-feature spec input |
| `/spec` | `.agent/workflows/spec.md` | spec writing |
| `/app-init` | `.agent/workflows/app-init.md` | architecture/setup |
| `/adr` | `.agent/workflows/adr.md` | architecture decisions |
| `/hotfix` | `.agent/workflows/hotfix.md` | emergency fix |
| `/handoff` | `.agent/workflows/handoff.md` | feature, architecture-change |
| `/research` | `.agent/workflows/research.md` | investigation |
| `/brainstorm` | `.agent/workflows/brainstorm.md` | exploration |
| `/audit` | `.agent/workflows/audit.md` | repo assessment |
| `/decide` | `.agent/workflows/decide.md` | decision logging |
| `/retro` | `.agent/workflows/retro.md` | retrospective |
| `/sync-docs` | `.agent/workflows/sync-docs.md` | documentation sync |
| `/govern-docs` | `.agent/workflows/govern-docs.md` | governance docs update |
| `/test-skeleton` | `.agent/workflows/test-skeleton.md` | test structure |
| `/test-classify` | `.agent/workflows/test-classify.md` | test classification |
| `/worktree-first` | `.agent/workflows/worktree-first.md` | branch isolation |
| `/help` | `.agent/workflows/help.md` | help |
| `/ask-openrouter` | `.agent/workflows/ask-openrouter.md` | **optional**: OpenRouter model |
| `/codex-cli` | `.agent/workflows/codex-cli.md` | **optional**: Codex CLI delegation |
| `/claude-cli` | `.agent/workflows/claude-cli.md` | **optional**: Claude CLI delegation |
| `/execute-plan` | `.agent/workflows/execute-plan.md` | **alias** → `/implement` |
| `/write-plan` | `.agent/workflows/write-plan.md` | **alias** → `/plan` |
| `/superpowers-playbook` | `.agent/workflows/superpowers-playbook.md` | meta-playbook, all classifications |
| `/new-feature` | `.agent/workflows/new-feature.md` | **deprecated**: use `feature` + `/bootstrap` |
| `/medium-feature` | `.agent/workflows/medium-feature.md` | **deprecated**: use `feature`/`architecture-change` + `/bootstrap` |
| `/small-fix` | `.agent/workflows/small-fix.md` | **deprecated**: use `quick-win` + `/bootstrap` |
| `/other-custom` | `.agent/workflows/other-custom.md` | **deprecated**: custom/experimental flow |
