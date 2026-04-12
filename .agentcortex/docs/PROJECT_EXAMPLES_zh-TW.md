# 導入範例（Node.js / Python）

本文件提供可直接複製的「真實專案導入」範例，幫助團隊在 Google Antigravity、Codex Web、Codex App 使用同一套 AgentCortex 流程。

## 範例 A：Node.js API 專案

### 情境

- 需求：新增 `POST /todos`，含輸入驗證與單元測試。
- 技術：Express + Vitest。

### 操作流程

1. 部署模板

```bash
./deploy_brain.sh .
./.agentcortex/bin/validate.sh
```

1. 開場提示（貼給 Agent）

```text
請先執行 /bootstrap。
需求：新增 POST /todos API。
目標檔案：src/routes/todos.ts, src/services/todoService.ts, tests/todos.test.ts
限制：不可破壞既有 GET /todos 回傳格式。
驗收：
1) 輸入 title 缺失時回傳 400
2) 成功建立回傳 201
3) 所有測試通過
```

1. 依序執行

- `/brainstorm`
- `/write-plan`
- `/test-skeleton` (TDD 推薦：實作前先出測試藍圖)
- `/execute-plan`
- `/review`
- `/test`
- `/ship`

### 建議驗證命令

```bash
npm test
npm run lint
```

---

## 範例 B：Python Backend 專案

### 情境

- 需求：新增 `calculate_discount` 邏輯，支援邊界條件。
- 技術：FastAPI + pytest。

### 操作流程

1. 部署模板

```bash
./deploy_brain.sh .
./.agentcortex/bin/validate.sh
```

1. 開場提示（貼給 Agent）

```text
請先執行 /bootstrap。
需求：新增 calculate_discount 邏輯。
目標檔案：app/services/pricing.py, tests/test_pricing.py
限制：不得修改現有 API schema。
驗收：
1) 原價 <= 0 時要拋出可預期錯誤
2) 折扣上限 50%
3) pytest 全數通過
```

1. 依序執行

- `/research`
- `/spec`
- `/plan`
- `/implement`
- `/review`
- `/test`
- `/handoff`

### 建議驗證命令

```bash
pytest -q
ruff check .
```

---

## 補充：跨平台建議

- Codex Web：每次新需求開新對話，先貼 `/bootstrap` 範本。
- Codex App：每次提交前固定跑 `./.agentcortex/bin/validate.sh`。
- Google Antigravity：優先使用 `/write-plan` + `/execute-plan`，避免長 prompt 漂移。

## 延伸閱讀

- [非線性情境（模型切換、Session 崩潰、混亂流程）](./NONLINEAR_SCENARIOS_zh-TW.md)
- [遷移與整合指南 (舊專案接管 / 導入教學)](./guides/migration.md)
- [Token 治理指南](./guides/token-governance.md)
