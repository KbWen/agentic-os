# Agentic OS v1.1 — 模型選擇指南

> 人類參考用 — 此檔案不會被載入 AI context。

## 原則：依任務分類選模型

Agentic OS 會對每個任務分類。用分類結果來選模型：

| 分類 | 建議模型層級 | 原因 |
|---|---|---|
| **tiny-fix** | Fast | 改 typo、調 config — 不需推理 |
| **quick-win** | Fast 先試 → 不行再 Pro | 範圍明確，Fast 能處理多數情況 |
| **hotfix** | Pro | Debug 需要深度推理 + 上下文理解 |
| **feature** | /plan 用 Pro、/implement 可混用、/review 用 Pro | 混合 — 規劃和審查需要判斷力 |
| **architecture-change** | 全程 Pro | 跨模組推理、安全性考量 |

## Fast 模型（預設選擇）

*Claude Haiku 4.5、Gemini 3.1 Flash、GPT-5.4-mini*

適合「做什麼」已經很明確、AI 只需執行的任務：

- 根據 spec 或 skeleton 寫測試
- 格式修正、lint 修復、CSS 調整
- 多語系翻譯和 i18n 填寫
- 明確的代碼搬遷（來源 → 目標清楚）
- 根據已通過的 `/plan` 生成 boilerplate
- 文件整理和摘要

## Pro / Advanced 模型（需要判斷力時）

*Claude Opus 4.6 / Sonnet 4.6、Gemini 3.1 Pro、GPT-5.4*

當任務需要「權衡取捨的推理」時切換：

- feature 或 architecture-change 的 `/plan` phase — 設計方案
- 涉及安全性 skill（auth-security、red-team）的 `/review`
- Debug race condition、memory leak、flaky test
- 帶 migration 安全考量的 schema 設計
- 重構 3+ 個高耦合核心模組
- Fast 模型第一次產出的邏輯有錯時

## 實用技巧

1. **先讓 Fast 失敗。** 先用 Fast；如果產出有邏輯錯誤（不只是格式問題），再帶著同樣 context 切 Pro。一次浪費的 Fast 嘗試比一次 Pro 嘗試便宜。
2. **分類就是信號。** 如果 `/bootstrap` 分類為 `feature` 以上，plan 和 review phase 傾向用 Pro。
3. **分 phase 用不同模型。** Pro 產出 `/plan` 之後，讓 Fast 處理 `/implement` 的 boilerplate。不同 phase 可以用不同模型。
4. **給 Fast 精簡 context。** 提供具體檔案路徑，不要 `ls -R`。Fast 模型在 noisy context 下退化比 Pro 嚴重。
