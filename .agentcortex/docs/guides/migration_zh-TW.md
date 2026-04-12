# 遷移與整合指南 (Migration & Integration Guide)

本指南說明如何將舊版 Template 升級至 vNext，以及如何在開發到一半的專案中導入此系統。

---

## 1. 專案 A：舊版升級 (Upgrade Path)

升級到 vNext 的核心目標：**「從流程驅動轉為狀態驅動」**。

### 步驟 1：代碼更新

```bash
./deploy_brain.sh /path/to/project-a
```

> [!NOTE]
> v3.5.2 的 `deploy_brain.sh` 預設使用 `cp -n`（不覆蓋已存在的檔案），您的自訂設定不會被蓋掉。
> 若需強制更新所有檔案，請加上 `--force` 旗標。
> 腳本亦會自動更新目標專案的 `.gitignore`。

### 步驟 2：AI 自動遷移舊有文件

告訴 AI 執行遷移掃描：

```text
請執行 /bootstrap。
我們剛從舊版升級到 vNext v3.5.2。
請掃描專案中的既有文件，並自動完成以下工作：
1. 識別散亂的筆記、規格、ADR，移動到正確目錄並重新命名
2. 初始化 .agentcortex/context/current_state.md
3. 將進行中的任務建立 Work Log
```

AI 會自動執行：

| AI 判斷邏輯 | 動作 | 目標位置 |
|---|---|---|
| 檔案看起來像架構決策記錄 | 移動 + 命名為 `ADR-NNN-<topic>.md` | `docs/adr/` |
| 檔案看起來像規格或需求文件 | 移動 + 命名為 `<feature-name>.md` | `docs/specs/` |
| 檔案看起來像進行中的任務紀錄 | 移動 + 命名為 `<branch-name>.md` | `.agentcortex/context/work/` |
| 檔案看起來像已完成的歷史紀錄 | 移動 + 命名為原檔名 | `.agentcortex/context/archive/` |
| 檔案無法分類 | 不動，列入報告供人工審閱 | 原位置 |

> [!IMPORTANT]
> AI 在完成掃描後，會先**輸出遷移計畫**（列出每個檔案的來源、目標、重命名規則），等使用者確認後才執行搬移。不會靜默刪除或移動任何檔案。

### 步驟 3：確認與接軌

- 審閱 AI 的遷移計畫，確認後回覆 `OK`。
- AI 執行搬移，並更新 `.agentcortex/context/current_state.md`。
- 從此接軌自動化治理，後續 `/ship` 會自動維護 SSoT。

---

## 2. 專案 B：混亂舊專案 / 開發中導入 (Legacy Project / Mid-task Integration)

重點：**「Catch-up（追趕），AI 做整理，人類不需要預處理」**。

### 步驟 1：環境部署

```bash
./deploy_brain.sh /path/to/project-b
```

### 步驟 2：原始素材進氣 + 自動歸檔

利用 vNext 的「素材自動處理 + 文件重組」功能。**您不需要手動整理任何檔案**：

```text
請執行 /bootstrap。
這是一個開發到一半的專案，需要導入 AI Brain 管理系統。
請完成以下工作：
1. 消化以下前期討論素材，提取規格存入 docs/specs/
2. 掃描專案現有的文件，自動分類並移動到正確目錄
3. 初始化 .agentcortex/context/current_state.md
4. 將目前進行中的任務建立 Work Log
---
[直接貼上目前的 TODO 清單、對話記錄、專案規格書或任何雜亂的原始資料]
---
```

### 步驟 3：AI 自動重構

AI 收到素材後，會依照 vNext 邏輯自動執行：

1. **提取規格**：將雜亂素材轉化為詳細規格，存入 `docs/specs/<feature-name>.md`。
2. **掃描現有檔案**：識別專案中的散亂文件，根據內容自動判斷分類與命名。
3. **輸出遷移計畫**：列出所有建議的搬移與重命名，等待使用者確認。
4. **建立地圖**：產出 `.agentcortex/context/current_state.md` 描述專案全貌。
5. **建立任務**：將進行中的工作建立 Work Log (`.agentcortex/context/work/<worklog-key>.md`)。

### 關於目錄衝突

如果專案已有 `docs/` 目錄（例如 API 文件、使用手冊等），Template 的 `.agentcortex/context/`、`docs/specs/`、`docs/adr/` 只使用各自的子目錄，**不會**影響現有的 `docs/api/`、`docs/architecture/` 等結構。

---

## 💡 常見問題 (FAQ)

**Q: AI 會自動刪除我的檔案嗎？**
A: 不會。AI 只會**建議搬移**，並等待使用者確認後才執行。無法分類的檔案會保留在原位。

**Q: 我可以自己手動整理而不用 AI 嗎？**
A: 完全可以。手動將檔案放到正確目錄是最省 Token 的方式。AI 自動整理是一個「懶人選項」，不是強制流程。

**Q: 舊的 `superpowers/features/` 檔案可以刪嗎？**
A: 建議在確認新的 `.agent/workflows/` 流程正常後再刪除。

**Q: 素材太多 AI 處理不完怎麼辦？**
A: 分批。先給核心規格 `/bootstrap` 建 SSoT；再給細節 `/research` 補充。
