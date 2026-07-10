# Codex 平台使用指南（Web / App）

## 適用範圍

本模板同時適用：

- Codex Web 版
- Codex App（桌面版）

## 檔案放置規範（Codex Web／Codex App／Google Antigravity）

為避免流程複雜化，三平台統一使用同一套技能來源與鏡像路徑：

1. Canonical skills source：`.agent/skills/<skill>/SKILL.md`（Antigravity 主要讀取路徑，兩者必須保持一對一同步，修改時以此為主）。
2. Codex 相容路徑：`.agents/skills/<skill>/SKILL.md`（Codex 平台 mirror）。
3. 平台流程文件：`.agent/workflows/*.md` 與 `.agent/rules/*.md`，避免在多處維護重複版本。

最小檢查建議：

- 執行 `./.agentcortex/bin/validate.sh`。
- 確認 `AGENTS.md` 仍同時宣告 `.agent/skills` 與 `.agents/skills`。

## 統一狀態機（兩平台共用）

請以 canonical state machine 為準：
`Ref: .agent/rules/state_machine.md`

- `/help`、`/commands`、`/test-skeleton`、`/handoff` 為唯讀狀態指令。
- `/ship` 僅允許在 `TESTED` 後執行。

## 共用建議

1. 任務開場先提供：目標、目標檔案、限制、驗收標準。
2. 先跑 `/bootstrap`、再 `/plan`，通過 quality gate 才 `/implement`。
3. 每次實作後跑 `/review` 與 `/test`。
4. 提交前跑 `./.agentcortex/bin/validate.sh`。

## GitHub Contributors 歸屬

GitHub repo 右側的 `Contributors` 來自預設分支上的 commit attribution，不是 repository collaborator invitation。若專案希望 Codex 執行的工作在 Contributors 面板顯示為 `codex`，至少要有一個合併到預設分支的 commit 使用 GitHub `codex` 帳號可識別的作者或共同作者 email。

Codex App/Web authored commit 建議使用：

```text
Codex <267193182+codex@users.noreply.github.com>
```

合併 Codex-authored PR 時，優先使用會保留 individual commit authors 的 merge 或 rebase merge。若使用 squash merge，請在最終 squash commit 保留 `Co-authored-by: Codex <267193182+codex@users.noreply.github.com>` trailer。

## Handoff Hard Gate（非 tiny-fix）

在 `/ship` 之前，必須先有 `/handoff`，且 References 最低要求：

1. 至少 1 個 `docs/` 文件。
2. 至少 1 個 code file path。
3. 對應 work log：`.agentcortex/context/work/<worklog-key>.md`。
   以 filesystem-safe 名稱從分支解析 `<worklog-key>`；若 active log 缺失但可復原，必須在拒絕 `/ship` 前重建它。

若不滿足，必須拒絕 `/ship` 並列出缺失。

## Gate Receipt 持久化 — Codex Web

在 Codex Web 上沒有檔案寫入能力。Gate receipts 仍必須被記錄以維持 validator 合規。協定：

1. 在每個階段完成時，於 chat 輸出 gate receipt 作為 fenced block：
   ```
   ## Gate Evidence
   - Gate: <phase> | Verdict: PASS | Classification: <tier> | Timestamp: <ISO>
   ```
2. 指示使用者：「將上方區塊貼到 `.agentcortex/context/work/<worklog-key>.md` 的 `## Gate Evidence` 之下。」
3. 在使用者確認已貼上（或表明會在 `/ship` 前完成）之前，不要進入下一階段。
4. 在 `/ship` 時，Gate Receipt Audit 會檢查 Work Log — 若因使用者未貼上而缺少 receipts，`/ship` 必須以 `missing: [<phase> receipt]` 失敗。

這確保 Codex Web 撰寫的 Work Log 即使沒有直接檔案存取也維持 validator 合規。

## 接手時機（Handoff Timing）

Handoff 時機依跨平台正本 — `AGENTS.md §Context Pruning`（context 佔用率 + 階段邊界，非輪數）。Codex 特性（`.agentcortex/docs/guides/token-governance.md §6.1`）：自動 prompt caching 已啟用（0.1×、prefix ≥1024 tok；GPT-5.1 有 24h 延長），且 auto-compaction 觸發較晚（~95% 容量）、中途易失控 — 故建議在乾淨的階段邊界提前 handoff。

## Web 版建議

- 一個需求一個 thread，避免上下文污染。
- 長任務中斷前務必輸出 `/handoff`，並提醒人類保存。

## App 版建議

- 使用本地 repo 執行 `deploy_brain.sh` 與驗證腳本。
- 每次子目標完成即更新 work log，降低跨天重建成本。

## 快速檢查清單

- [ ] `/bootstrap` 已完成
- [ ] `/plan` 已通過 quality gate
- [ ] `/implement` 在 `IMPLEMENTABLE` 才執行
- [ ] `/review` 與 `/test` 已完成
- [ ] 非 `tiny-fix` 已完成 `/handoff`
- [ ] `validate.sh` 已通過
