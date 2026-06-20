# Claude 平台使用指南

## 適用範圍

本指南新增一個最小化的 Claude 相容入口，同時讓 Agentic OS 治理正本維持在：

- `AGENTS.md`
- `.agent/rules/*.md`
- `.agent/workflows/*.md`

## 接手時機（Handoff Timing）

Handoff 時機依跨平台正本 — `AGENTS.md §Context Pruning`（context 佔用率 + 階段邊界，非輪數），Claude 特性的 caching/compaction 細節見 `.agentcortex/docs/guides/token-governance.md §6.1`（Claude：prefix cache 0.1×、預設 5 分鐘 TTL、compaction 重用 prefix）。

## 設計原則

- 不要為 Claude 分叉核心規則。
- `CLAUDE.md` 與 `.claude/commands/*.md` 僅作為 prompt adapter。
- state 與 evidence 維持與其他平台相同的路徑。

## 必要檔案

- `CLAUDE.md`
- `.claude/commands/bootstrap.md`
- `.claude/commands/plan.md`
- `.claude/commands/implement.md`
- `.claude/commands/review.md`
- `.claude/commands/test.md`
- `.claude/commands/handoff.md`
- `.claude/commands/ship.md`

## 階段 Shim（Skill 注入）

`.claude/agents/acx-*.md` 是輕量的 custom subagent shim，利用 Claude Code 原生的 `skills:` frontmatter，在 spawn 出來的 subagent 啟動時注入 agentic-os 的 skills。它們存在的唯一目的是解決 context 傳遞缺口：subagent 不會從 parent session 繼承 skills。

| Shim | 階段 | 注入的 Skill | Model |
|---|---|---|---|
| `acx-implementer.md` | /implement | verification-before-completion | sonnet |
| `acx-reviewer.md` | /review | red-team-adversarial | opus |
| `acx-tester.md` | /test | verification-before-completion, test-driven-development | sonnet |
| `acx-handoff.md` | /handoff | verification-before-completion | sonnet |
| `acx-shipper.md` | /ship | production-readiness | sonnet |

**設計守則**：shim 本體 ≤5 行，只指向 canonical workflow 檔案。所有邏輯都在 `.agent/workflows/`。階段規則變更時，更新 workflow，而非 shim。

**驗證**：`validate.sh` 與 `validate.ps1` 會確認 shim frontmatter 中所有對應到 `.agent/skills/<name>/` 的 skill 名稱，都有對應的 `SKILL.md` 本體。

## 使用方式

1. 開啟 Claude，貼上 `CLAUDE.md` 的啟動 prompt。
2. 各階段使用 `.claude/commands/` 中的 template。
3. 維持與 Codex/Antigravity 相同的 gate/evidence 要求。

## 驗證

執行：

```bash
./.agentcortex/bin/validate.sh
```

此檢查會確認 Claude adapter 檔案存在，且 canonical 治理檔案仍然存在。
