# Token 優化快速指南

> **對象**：Clone Agentic OS 後想立即降低 Token 消耗的開發者。
>
> **前置知識**：不需要。本指南自成一體。深入了解請參考 [Token Governance](../../.agentcortex/docs/guides/token-governance.md) 和 [Context Budget](../../.agentcortex/docs/guides/context-budget.md)。

---

## 快速摘要 — 立即可做的 3 件事

1. **精準分類任務** — 明確告訴 AI「tiny-fix」或「quick-win」，避免走完整 feature 流程。
2. **關閉耗能技能** — 複製 user preferences 範本，停用不需要的技能。
3. **保持 SSoT 精簡** — 定期歸檔舊紀錄，避免 Context 膨脹。

---

## 1. 了解 Token 成本分佈

Agentic OS 的每個任務都遵循階段式工作流。階段越多，Token 消耗越高：

| 分類 | 典型 Token 成本 | 階段 |
|:---|---:|:---|
| `tiny-fix` | ~2,000–5,000 | 分類 → 執行 → 證據 |
| `quick-win` | ~15,000–17,000 | Bootstrap → Plan → Implement → Ship |
| `feature` | ~30,000–60,000 | 完整 7 階段生命週期 |
| `architecture-change` | ~50,000–65,000 | 完整生命週期 + ADR + 全部技能 |

**核心洞察**：最大的成本來源是**任務分類錯誤**。一個 Typo 修正被歸類為 `feature`，會浪費 3 萬以上 Token 在不必要的計畫、審查與測試階段。

### 如何正確分類

給 AI 下指令時，請明確宣告：

```
❌ "修正日期格式的 bug"                    → AI 可能歸類為 feature
✅ "修正日期格式的 bug（tiny-fix）"         → AI 走快速通道
✅ "這是 quick-win：加上分頁功能"           → AI 跳過 guardrails，省下 ~3,500 tokens
```

---

## 2. 關閉耗能技能

Agentic OS 會根據任務類型自動啟動技能。某些技能消耗較高：

| 技能 | 消耗風險 | 何時可關閉 |
|:---|:---|:---|
| `red-team-adversarial` | 高 | 內部工具、非安全性專案 |
| `dispatching-parallel-agents` | 高 | 單人開發的工作流 |
| `subagent-driven-development` | 高 | 簡單、單模組的任務 |
| `test-driven-development` | 中 | 原型開發、探索性工作 |

### 如何關閉

1. 複製範本：
   ```bash
   cp .agentcortex/templates/user-preferences.yaml \
      .agentcortex/context/private/user-preferences.yaml
   ```

2. 編輯並停用技能：
   ```yaml
   skill_preferences:
     pinned: []
     disabled:
       - dispatching-parallel-agents
       - subagent-driven-development
       - red-team-adversarial
   ```

3. 此檔案已在 **.gitignore** 中 — 僅影響你個人的環境。

> **注意**：`verification-before-completion` 和 `auth-security` 是**受保護的技能**，無法被停用。這是刻意設計——它們對安全至關重要。

---

## 3. 保持 SSoT 精簡

SSoT 檔案（`.agentcortex/context/current_state.md`）會隨時間增長。膨脹的 SSoT 代表 AI 每次 Session 都要讀取數千個無關的 Token。

### 內建的自動控制

Agentic OS 已經在 `.agent/config.yaml` 中設定了自動限制：

| 設定 | 預設值 | 用途 |
|:---|:---|:---|
| `global_lessons_max_entries` | 20 | 自動歸檔舊教訓 |
| `spec_index_max_entries` | 30 | 摺疊已交付的規格 |
| `worklog.max_lines` | 300 | 觸發壓縮 |
| `worklog.max_kb` | 12 | 觸發壓縮 |

### 手動維護

如果你覺得 SSoT 太肥了，可以告訴 AI：

```
「幫我壓縮 SSoT — 歸檔已交付的 spec 和低嚴重性的教訓。」
```

或手動將舊紀錄從 `current_state.md` 移到 `.agentcortex/context/archive/`。

---

## 4. 善用 Provider 快取（雙模策略）

現代 LLM 供應商（Anthropic Claude、Google Gemini、OpenAI）會自動快取穩定的 Prompt 前綴，提供高達 90% 的折扣。你不需要做任何設定——但你可以最大化效益：

- **全新 Session**：對於獨立的 `tiny-fix` 任務，Agent 會跳過讀取 Guardrails。這能直接省下約 3,500 Base Tokens，因為沒有舊快取可以利用。
- **進行中的 Session（混合任務）**：如果目前的 Session 在前面的回合已經讀取過 Guardrails，後續回合**不要跳過它**。保持前綴一致能觸發大幅度的快取折扣，這比跳過它而導致 Cache Miss 還要便宜得多。
- **不要在對話中重複貼上治理文件。** 它們已經在 Context 中了。

---

## 5. 優化 AI 回應長度

輸出 Token 的成本跟輸入 Token 一樣，而且每一輪都會累加。一個多寫了 500 Token 的回應，10 輪下來就浪費了 10,000+ Token。

Agentic OS 已經強制執行這個規則（參見 `AGENTS.md §Response Brevity`），但你可以加強：

```
「回應保持在 8 行以內。引用 Work Log 而不是重新敘述。」
```

---

## 6. 進階：為你的專案客製化

### 減少 Bootstrap 時的檔案讀取

[Context Budget Guide](../../.agentcortex/docs/guides/context-budget.md) 定義了每個分類可以讀取的檔案數量上限：

| 分類 | 最大檔案讀取數 |
|:---|:---|
| `tiny-fix` | 1–2 |
| `quick-win` | 3–5 |
| `feature` | 6–9 |
| `architecture-change` | 8–12 |

如果 AI 讀取了超出預算的檔案，這是一個 **Token Leak** — 應該標記它。

### 小任務自動跳過 Guardrails

對於 `tiny-fix` 和 `quick-win`，完整的 `engineering_guardrails.md`（~14KB，~3,500 tokens）**已經被設計為跳過**。核心規則已嵌入在 `AGENTS.md §Core Directives` 中。

---

## 速查：已經內建的機制

在建立自定義優化之前，先了解這些已有的機制：

| 機制 | 位置 | 功能 |
|:---|:---|:---|
| 條件式載入 | `context-budget.md` | tiny-fix/quick-win 跳過 guardrails |
| 技能快取策略 | `.agent/config.yaml §skill_cache_policy` | Metadata 優先載入，僅 cache miss 時讀完整 SKILL.md |
| 使用者技能偏好 | `.agentcortex/templates/user-preferences.yaml` | 每位使用者可 pin/disable 技能 |
| Work Log 壓縮 | `.agent/config.yaml §worklog` | 超過 300 行 / 12KB 自動壓縮 |
| 文件生命週期 | `.agent/config.yaml §document_lifecycle` | 自動歸檔 SSoT 條目 |
| 輸出精簡 | `token-governance.md §8` | AI 回應 ≤ 8 行 + 結構化區塊 |
| 讀一次原則 | `AGENTS.md §Core Directives` | 治理文件絕不重讀 |
| Context 快取 | `token-governance.md §6` | 供應商端快取，零配置 |

---

## 自我優化路線圖

Agentic OS 的設計允許它隨著使用而自動改進：

1. **`/retro` 從錯誤中學習** — 流程失敗會被記錄為 SSoT 中的 Global Lessons，後續 Session 會讀取並避免重蹈覆轍。
2. **技能快取逐漸暖化** — 首次使用技能後，後續階段使用快取的 Skill Notes（約完整 SKILL.md 大小的 22%）。
3. **Work Log 自動壓縮** — 舊條目自動歸檔，保持 Context 精簡。
4. **分類精準度提升** — 隨著 SSoT 累積交付歷史，AI 能更好地進行任務類型的模式匹配。

> **給框架貢獻者**：如果你想提議結構性的 Token 優化（例如合併 Workflow 檔案、精簡 Guardrails），請開 Issue 或提交 PR。[生命週期基準測試](../LIFECYCLE_BENCHMARK_zh-TW.md) 提供了可量測的基線數據。

---

*另見：[Token Governance（內部）](../../.agentcortex/docs/guides/token-governance.md) · [Context Budget（內部）](../../.agentcortex/docs/guides/context-budget.md) · [生命週期基準測試](../LIFECYCLE_BENCHMARK_zh-TW.md)*
