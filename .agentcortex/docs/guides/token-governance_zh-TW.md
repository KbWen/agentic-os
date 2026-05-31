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
> **僅為啟發式 — 不是 handoff 訊號。** 任務不會因為「到了某個輪數」就該 handoff。正本 handoff 觸發是 **context 佔用率 + 階段邊界**（見 `AGENTS.md §Context Pruning` 與 §6.1）；輪數只是無法估計佔用率時的粗略 fallback。（英文版為準）

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

## 6. Context 快取與接手時機（跨平台）

現代 LLM 平台都支援 **prompt caching** — 對穩定前綴（系統指令、AGENTS.md、guardrails）重用計算。本專案實測 **97–98% 快取命中率**（2026-05-13~05-26），約 97% input token 以 0.1× 計價。快取為平台自動啟用（Claude / OpenAI / Gemini 2026 皆預設開啟），無需框架改動。

### 6.1 跨平台接手時機與快取（`AGENTS.md §Context Pruning` 正本細節）

接手觸發是 **context 佔用率 + 階段邊界**，不是輪數 — 因為各平台底層事實已趨一致：都自動以 ~0.1× 快取前綴、且在視窗將滿時自動壓縮。兩個後果：(1) **過早 handoff 丟棄溫快取**，需全價重建新 session — 為縮短 session 而提早 handoff 現在是淨成本；(2) 輪數型自動存檔原本要防的崩潰／溢位風險，大多已由平台自身壓縮覆蓋。所以：在**佔用率高**時、於自然**階段邊界**為了**品質**而 handoff，而非看輪數計時器。輪數僅在無法估計佔用率時作為粗略 fallback。

| 平台 | Prompt caching (2026) | 自動壓縮 | Context window | 接手要點 |
|---|---|---|---|---|
| Claude / Claude Code | 自動，讀 0.1×；預設 TTL **5 分鐘**（1h 需 opt-in `ENABLE_PROMPT_CACHING_1H`）；壓縮重用前綴快取 | 視窗將滿時 | Opus 4.6–4.8 = **1M** | 5 分鐘 TTL 使工作中的溫快取脆弱 → 偏好階段邊界 handoff |
| OpenAI / Codex | 自動、無需程式碼／免費，0.1×，前綴 ≥1024 tok；**GPT-5.1 有 24h 延長** | server-side／本地；**~95% 容量** | 大（agentic 優化；未公佈具體值） | ~95% 自動壓縮太晚、中途易失控 → 在那之前於邊界 handoff |
| Google / Gemini / Antigravity | **隱式快取預設開**（2.5+，0.1×）+ 顯式 `cachedContent` | 大視窗吸收更多 | **1M–2M** | 大視窗 → 更少 handoff；以佔用率% 思考，非絕對輪數 |

> 來源（2026-05-31 驗證）：[Claude](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching) + [compaction](https://developers.openai.com/api/docs/guides/compaction) · [Gemini](https://ai.google.dev/gemini-api/docs/caching)。引用前請重新查證。（英文版為準）
