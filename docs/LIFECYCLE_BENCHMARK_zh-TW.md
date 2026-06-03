# 生命週期基準測試 & Token 消耗報告

> **框架**: Agentic OS v1.3.0 | **CI 把關套件**: 180 全數通過（2026-06-03 驗證） | **Token 快照**: 2026-05-31（為當日快照 — 下方數字由工具產生，見「重新產生本報告」）

本報告記錄生命週期場景覆蓋與 token 消耗量測，協助團隊在導入 Agentic OS 前評估治理成本。

---

## 測試套件摘要

存在兩套測試，用途不同：

- **CI 把關驗證套件** — `python -m pytest tests/ci/ tests/guard/` — **180 個測試，全數通過**（2026-06-03 驗證）。這是 GitHub Actions 在每個 PR 強制執行的套件，也是「框架是否健康」的權威訊號。

| 類別 | 測試數 | 檔案 |
|:---|:---:|:---|
| 安全掃描（Semgrep + TruffleHog + pip-audit） | 32 | `tests/ci/test_security_workflow.py` |
| 受控寫入（單元） | 24 | `tests/guard/test_d2_1_guard_unit.py` |
| 稽核鏈防竄改 | 17 | `tests/guard/test_audit_chain.py` |
| 受控寫入 lint | 16 | `tests/guard/test_d2_2_lint.py` |
| 文件生命週期契約 | 14 | `tests/guard/test_d2_3_lifecycle.py` |
| ADR 覆蓋 | 12 | `tests/guard/test_adr_coverage.py` |
| 狀態機契約 | 11 | `tests/guard/test_state_machine_contract.py` |
| 驗證器誤報防護 | 11 | `tests/ci/test_validator_false_positives.py` |
| 部署分層 | 9 | `tests/ci/test_deploy_tiering.py` |
| 稽核鏈見證 | 9 | `tests/ci/test_audit_witness.py` |
| 分類升級 | 8 | `tests/guard/test_classification_escalation.py` |
| 衝突標記 | 7 | `tests/guard/test_conflict_markers.py` |
| SSoT 心跳契約 | 4 | `tests/guard/test_ssot_heartbeat_contract.py` |
| CI 強化 | 4 | `tests/ci/test_ci_hardening.py` |
| 受控寫入（競態） | 2 | `tests/guard/test_d2_1_guard_race.py` |
| **總計（CI 把關）** | **180** | 全數通過 |

- **開發期分析套件** — `.agentcortex/tests/` — 透過 `analyze_token_lifecycle.py` 產生下方的 token 消耗數字。它包含追蹤倉庫演進的即時不變量檢查（SSoT 序列單調性、backlog／ship-history 可解析性），因此**不**納入發版把關。

---

## Token 消耗快照

> **下方數字是工具產生的，非手動維護。** 隨時可用
> `python .agentcortex/tools/analyze_token_lifecycle.py --root . --format text` 重新產生 —
> 數字會隨 workflow 與 skill 演進而變動，請當作有日期的快照，而非固定契約。
>
> **快照日期**: 2026-05-31 · **公式**: `字元數 / 4`（與你模型的 tokenizer 有 ±10% 差異）· **基準**: registry 4,838 tok、compact index 2,664 tok。

「當前」= 天真的每次完整讀取。「優化」= compact-index 探測 + heading-scoped workflow 讀取 + skill heading-scope。

| 場景 | 分類 | 當前 | 優化 | 節省 |
|:---|:---|---:|---:|---:|
| Quick-Win（單模組） | `quick-win` | 26,749 | 22,077 | 4,672 (17.5%) |
| Feature + TDD 循環 | `feature` | 56,139 | 38,739 | 17,400 (31.0%) |
| Feature（API + Auth + DB） | `feature` | 70,177 | 39,532 | 30,645 (43.7%) |
| Hotfix + 除錯循環 | `hotfix` | 44,662 | 30,740 | 13,922 (31.2%) |
| 架構變更 + 多 Agent | `architecture-change` | 82,665 | 44,130 | 38,535 (46.6%) |
| Review 反饋循環 | `feature` | 55,336 | 30,390 | 24,946 (45.1%) |
| **6 場景合計** | — | **335,728** | **205,608** | **130,120 (38.8%)** |

---

## 場景輪廓

各場景的定性樣貌（成本來源）。Token 數字見上方快照；下方技能名稱反映目前的 14 技能集。

### 1. Quick-Win — 單模組
> *「修正匯出 CSV 的日期格式」*
- **階段**: Bootstrap → Plan → Implement → Ship
- **技能**: verification-before-completion、karpathy-principles
- **成本來源**: 最輕量的生命週期 — 只有治理開銷；無 review/test/handoff。32K+ context 模型即可應付。

### 2. Feature + TDD 循環
> *「新增使用者 Email 驗證功能（OTP 流程）」*
- **階段**: Bootstrap → Spec → Plan → Implement (×3) → Review → Test (×2) → Handoff → Ship
- **技能**: test-driven-development、verification-before-completion、red-team-adversarial、karpathy-principles
- **成本來源**: 紅→綠→重構的 implement 重複 + 回歸 test 重複；continuation 模型（首次讀取 + 快取筆記）吸收大部分重複成本。

### 3. Feature 涉及 API、Auth 與資料庫
> *「為管理後台新增角色權限控制，含新資料表」*
- **階段**: Bootstrap → Spec → Plan → Implement (×2) → Review → Test (×2) → Handoff → Ship
- **技能**: api-design、database-design、auth-security、doc-lookup、test-driven-development、red-team-adversarial、production-readiness
- **成本來源**: 跨領域功能啟動最多技能 → 探測成本上升；compact-index 探測是主要節省來源。

### 4. Hotfix + 除錯循環
> *「線上訂單重複建立 — 緊急修復」*
- **階段**: Bootstrap → Research → Plan → Implement (×2) → Review → Test (×2) → Ship
- **技能**: systematic-debugging、verification-before-completion、red-team-adversarial
- **成本來源**: hotfix 仍強制 review/test，但 `systematic-debugging` 採 on-failure 載入，使除錯循環成本適中。

### 5. 架構變更 + 多 Agent
> *「從單體架構遷移到微服務 — 拆分 auth、catalog、order 服務」*
- **階段**: Bootstrap → ADR → Spec → Plan → Implement (×2) → Review (×2) → Test (×2) → Handoff → Ship
- **技能**: 全部領域技能 + using-git-worktrees + dispatching-parallel-agents + subagent-driven-development
- **成本來源**: 最重的生命週期 — 啟動完整技能集與平行 agent 協調；優化在此省下最多絕對 token。

### 6. Review 反饋循環
> *「處理 reviewer 的 5 條意見、重新實作、通過複審」*
- **階段**: Review (×4) → Implement (×2) → Test (×2) → Handoff → Ship
- **技能**: red-team-adversarial、verification-before-completion、karpathy-principles
- **成本來源**: 最多階段重複；heading-scoped workflow 讀取（再進入時只重讀核心章節）帶來最高的優化百分比。

---

### Token 優化機制拆解

| 優化手段 | 運作方式 | 節省來源 |
|:---|:---|:---|
| **條件式載入** | tiny-fix 只讀 `AGENTS.md`；quick-win 跳過 guardrails | 基礎治理：省 ~3,500–5,000 tokens |
| **Compact Index 探測** | 讀取技能元數據（約 40 tokens/技能）而非完整 SKILL.md（200–2,200 tokens/技能） | 探測階段：便宜 ~60–85% |
| **Heading-Scoped 工作流** | 解析 `## Heading-Scoped Read Note` 只讀需要的章節 | 重複階段：跳過 ~20–30% 的文件 |
| **Continuation 模型** | 首次載入技能 = 完整 SKILL.md；後續 = 快取筆記（約 22%） | 執行細節：重型場景省 ~40–62% |
| **讀一次原則** | 治理文件每 session 只讀一次，不重複讀取 | 長對話中避免 token 洩漏 |

---

## 上手指南：推薦導入路徑

對於評估或導入 Agentic OS 的團隊，我們推薦從 `/audit` 開始：

### 為什麼從 /audit 開始？

```
/audit
```

`/audit` 指令對你的現有 codebase 進行**唯讀**遍歷：

1. **零風險** — 不修改程式碼、不需要 gate 驗證
2. **全面可見** — 映射你的目錄結構、架構、進入點、測試覆蓋率
3. **差距分析** — 識別缺少的文件並推薦下一步行動
4. **路由行動** — 產生結構化的後續項目指向正規文件

### 推薦導入順序

```
步驟 1: /audit          → 理解現狀
步驟 2: /app-init       → 建立專案特定慣例
步驟 3: /spec-intake    → 匯入現有規格/需求
步驟 4: 挑一個 quick-win → 以低成本（~27K tokens）體驗完整生命週期
步驟 5: 嘗試一個 feature → 完整生命週期 + 技能
```

這種漸進式路徑讓你的團隊可以逐步體驗治理機制，而不是第一天就嘗試完整的 feature 生命週期。

---

## 重新產生本報告

```bash
# CI 把關驗證套件（權威的通過/失敗訊號 — GitHub Actions 執行的就是這個）
python -m pytest tests/ci/ tests/guard/ -v

# 開發期分析套件，產生 token 數字（追蹤即時倉庫）
python -m pytest .agentcortex/tests/ -v

# 重新產生 Token 消耗快照數字
python .agentcortex/tools/analyze_token_lifecycle.py --root . --format text

# JSON 輸出供程式使用
python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json

# 審計 runtime 就緒狀態
python .agentcortex/tools/audit_agent_runtime.py --root . --format json
```

---

*本基準測試使用 `字元數 / 4` 作為 token 估算公式，與框架測試基礎設施一致。實際 token 數可能依模型 tokenizer 有 ±10% 差異。*
