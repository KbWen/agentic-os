# 非線性韌性：AI 自動管理規則

> 這些規則由 AI Agent 載入。定義 AI 在偵測到非線性人類行為時 **必須自動執行** 的行為。人類不需要記住或手動觸發這些規則 — AI 自行處理。

---

## 規則 1：自動存檔（預防 Session 崩潰數據遺失）

**觸發條件**：AI 偵測到已完成 **3 輪以上的實作工作** 但未更新 Work Log。

**AI 必須**：

1. 自動在 Work Log 寫入 `## Checkpoint` 區塊：

```markdown
## Checkpoint
- State: [當前狀態機狀態]
- Completed: [本次 Session 已完成步驟]
- Next: [下一個計畫動作]
- Modified Files: [已修改但未 commit 的檔案]
- Timestamp: [當前時間]
```

1. 建議 WIP commit：「建議將目前變更以 WIP 提交。繼續？」
2. 繼續工作 — 不要等人類批准存檔寫入本身。

**原理**：人類忘記存檔。Session 無預警崩潰。AI 是安全網。

---

## 規則 2：自動恢復偵測（處理模型切換和崩潰恢復）

**觸發條件**：`/bootstrap` 期間，AI 發現已有內容的 Work Log。

**AI 必須**：

1. 檢查是否有 `## Resume` 或 `## Checkpoint` 區塊（按此優先順序）。
2. 如果找到，宣布：「偵測到前次 Session 狀態：**[狀態]**。從 [最後存檔點] 恢復。前次 Session 修改的檔案：[清單]。」
3. 執行 `git status` 偵測孤兒變更（已崩潰 Session 中未 commit 的檔案）。
4. 如有孤兒變更，報告：「發現前次 Session 未 commit 的變更：[檔案]。可能來自崩潰。繼續前先檢查？（是/直接繼續）」
5. 從記錄的狀態恢復 — 不要從 `INIT` 重新開始。

**如果 Work Log 不存在但 `git log` 顯示該分支有近期 commit**：

- 從近期 commit 重建最小上下文。
- 建立新的 Work Log 並推斷狀態。
- 宣布：「未找到 Work Log，但偵測到此分支有近期工作。已建立恢復用 Work Log。」

**原理**：人類切換模型或 Session 崩潰時，新 AI 記憶為零。Work Log + git 狀態是橋樑。AI 做偵探工作，不是人類。

---

## 規則 3：切換前自動存檔（偵測即將進行的模型切換）

**觸發條件**：人類說出任何暗示模型切換的話語，例如：

- 中文：「換個模型」、「切換到...」、「我用 Claude 試試」、「這模型不行」、「換一個」
- 英文：「let me try another model」、「switching to...」、「I'll use Claude/GPT/Gemini」

**AI 必須**：

1. 立即在 Work Log 寫入 `## Resume` 區塊（格式同 `/handoff` 輸出）。
2. Commit 所有未 commit 的變更：`wip: auto-save before model switch`。
3. 輸出一行可複製文字給人類貼到下一個模型：

```
請執行 /bootstrap。Resolved Work Log: .agentcortex/context/work/<worklog-key>.md
```

1. 宣布：「狀態已存檔。將上面那行貼到新模型即可繼續。」

**原理**：人類只需要複製一行。其他全部自動。

---

## 規則 4：非線性狀態回退（處理實作中途的計畫變更）

**觸發條件**：在 `IMPLEMENTING` 期間，AI 或人類發現計畫錯誤、不完整或需要修訂。

**AI 必須**：

1. 在 Work Log 記錄：

```markdown
## State Rollback
- From: IMPLEMENTING
- To: CLASSIFIED
- Reason: [具體原因 — 例如「邊界情況 X 未包含在計畫中」]
- Timestamp: [當前時間]
```

1. 宣布：「需要修訂計畫：[原因]。回退到 CLASSIFIED。重新執行 /plan。」
2. 以更新的限制重新進入 `/plan` 階段。
3. 不要請求人類批准回退 — 記錄並執行。Work Log 中的審計軌跡已足夠。

**原理**：狀態機是指南，不是監獄。有記錄理由的回退永遠有效。

---

## 規則 5：阻擋項隔離（自動管理多任務混亂）

**觸發條件**：任務進行中，AI 發現需要單獨修復的阻擋問題。

**AI 必須**：

1. 在當前 Work Log 寫入 `## Blocker Detected`：

```markdown
## Blocker Detected
- Blocker: [簡述]
- Impact: [被阻擋的是什麼]
- Recommended: 先修復阻擋項，再恢復此任務。
```

1. 問人類一個問題：「發現阻擋項：[描述]。先修復它再回來，還是繞過？」
2. 如果人類說先修復：
   - 自動寫入當前任務的 `/handoff`。
   - 為阻擋項啟動新的 `/bootstrap`，使用獨立 Work Log。
   - 阻擋項解決後提示：「阻擋項已修復。恢復 [原始任務]？」

**原理**：人類自然會切換上下文。AI 管理任務的暫停和恢復。

---

## 規則 6：輪數自動接手（現有規則增強）

**增強 AGENTS.md §Context Pruning**：

滿 8 輪時現有規則是 _建議_ handoff。本增強使其更強：

**AI 必須**：

1. 第 8 輪：建議 handoff（現有行為）。
2. 第 12 輪：自動寫入 `## Checkpoint`，即使人類忽略了建議。
3. 第 15 輪：升級警告：「⚠️ 已經 15 輪了。上下文品質正在下降。強烈建議立即 `/handoff`。」

**原理**：人類會忽略警告。AI 無論如何都要寫入存檔以保護上下文品質。

---

## 總結：人類需要做什麼

| 情況 | 人類動作 | AI 動作 |
| --- | --- | --- |
| Session 可能崩潰 | **什麼都不用做** | 每 3 輪實作工作自動寫入 `## Checkpoint` |
| 切換模型 | **複製貼上一行字** | 自動存檔狀態、自動 commit WIP、產生那行字 |
| Session 崩潰後 | **只要開始 `/bootstrap`** | 自動偵測 Work Log + 孤兒 git 變更，自動恢復 |
| 實作中發現計畫有問題 | **什麼都不用做**（或說「計畫有問題」） | 自動回退狀態、重新計畫、記錄理由 |
| 發現阻擋項 | **回答一個是/否** | 自動管理任務暫停和切換 |
| 長 Session（8+ 輪） | **什麼都不用做** | 第 12 輪自動存檔，第 15 輪升級警告 |

> **設計原則**：人類的認知負擔趨近於零。AI 是流程管理者。

---

## 延伸閱讀

- [導入範例（線性流程）](./PROJECT_EXAMPLES_zh-TW.md)
- [工程護欄（憲法）](../../.agent/rules/engineering_guardrails.md)
- [模型選擇指南](../AGENT_MODEL_GUIDE_zh-TW.md)
