# Token Governance Guide

## 目標

在不犧牲正確性與可追溯性的前提下，持續降低平均任務 token 成本。

## 0. 架構精神優先（不可為省 token 而犧牲）

降低 token 的前提是「維持工程憲法」：

- **Correctness first**：沒有驗證證據，不得因為想省 token 而宣告完成。
- **Document-first**：涉及架構或核心邏輯時，先補齊對應 Spec/ADR，再談摘要化。
- **Traceability floor**：任何摘要都必須保留可追溯路徑（至少 doc + code + work log）。

> 快速判斷：若某個「省 token 手法」會讓 AC 對應、風險回退、或測試證據消失，則該手法不允許採用。

## 1. 任務級 Token Budget（初版）

- `tiny-fix`：建議 1–2 回合完成。
- `behavior-change`：建議 2–4 回合完成。
- `feature` / `architecture-change`：建議 3–6 回合完成。

> 回合數是上限提醒，不是硬性失敗條件。

## 2. 超標處置（Cost Fallback）

若小任務（docs-update / small-fix）超過預算：
1. 下一輪強制使用 `Mode: Fast Lane`。
2. 回覆格式改為固定模板（Summary + Evidence + Next），禁止冗長背景重述。
3. 僅保留必要引用與 AC 對應，不重複貼大段規範原文。

## 3. 防退化規則

- 若發現「小工作反而產生大量 token」，必須在 `/retro` 或 work log 記錄 root cause。
- 下次同類任務優先套用已驗證的短模板。

## 4. 與流程文件的關聯

- `/plan` 需包含 `Mode: Normal` 或 `Mode: Fast Lane`。
- `/handoff` 保持每區塊精簡，避免貼完整 diff。
- `/ship` 提供必要證據即可，避免重複敘述。

## 5. 完整檢查清單（Release 後巡檢）

當新版本宣稱「降低讀取文件 token 消耗」時，至少檢查：

1. **讀取策略是否精準化**：是否遵守 SSoT 導引、避免盲掃 `docs/`。
2. **流程完整性是否保留**：是否仍遵守狀態機與 quality gate，不因摘要化跳步。
3. **證據密度是否足夠**：是否仍能提供 validate/test/command 證據。
4. **回退機制是否仍可執行**：壓縮輸出後，是否仍可定位檔案並快速 rollback。
5. **跨平台一致性是否維持**：Web/App/Antigravity 規範是否一致。

若任一項失敗，視為「以效率破壞治理」，必須先修正再宣告成功。
