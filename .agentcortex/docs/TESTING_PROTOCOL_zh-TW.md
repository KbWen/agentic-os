# Testing Protocol (測試教戰守則) v3.2
>
> **本文件旨在指引 AI Agent 產出高品質、可信任、且具備防禦性的測試程式碼。**

## 1. 測試命名規範 (Naming Convention)

測試函數命名應具備描述性且「自帶目標」。

- **格式**: `test_[行為]_[預期結果]_[情境]`
- **範例**: `test_calculate_total_should_precision_round_when_multiple_items_exist`
- **反例**: `test_calculation1` (嚴禁使用無意義編號)

---

## 2. 測試覆蓋重點 (Coverage Priorities)

### 2.1 Happy Path (成功路徑)

- 驗證輸入合法時的最基本預期輸出。

### 2.2 Boundary & Edge Cases (邊際情況)

- **數值**: `0`, 負數, 極大值, `null`, `undefined`。
- **集合**: 空陣列, 重複元素, 超長字串。
- **時序**: 同步執行 vs. 非同步延遲。

### 2.3 Error Handling (錯誤處理)

- 驗證系統是否能在遇到非法輸入時正確「噴錯 (Throw Error)」或返回特定錯誤代碼，而不是崩潰。

---

## 3. 測試安全性與獨立性

- **隔離度**: 測試不應依賴外部資料庫或網路 API（優先使用 Mock/Stub）。
- **副作用**: 測試執行完畢後，應清理所有暫存狀態或檔案，禁止對環境造成持久影響。
- **確定性**: 禁止在測試中使用非確定的變數（例如：當前時間），應注入 Mock 時鐘。

---

## 4. 懶人指令範例

當您需要 AI 補強測試時，可以說：
> 「*請讀取 .agentcortex/docs/TESTING_PROTOCOL.md，並依照規範為 [函數名] 補齊測試覆蓋率。*」

---

## 5. 驗收標準 (AC)

- 所有的測試案例皆能在 `npm test` (或專案對應指令) 下通過。
- 禁止為了提高覆蓋率而寫「廢話測試」（不帶斷言的測試）。

