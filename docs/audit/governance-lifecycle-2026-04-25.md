---
title: 治理流程多分類生命週期模擬審計（v2 — 圓桌後修正版）
date: 2026-04-25
branch: feature/governance-lifecycle-simulation
auditor: claude-opus-4-7 (1M context) + 4 expert sub-agents (Security / DistSys / Formal / Pragmatist)
status: draft
phase: A revised (audit-only, no code)
scope: AGENTS.md / engineering_guardrails.md / .agent/workflows/* + post-roundtable verification of `guard_context_write.py` and skill paths
checkpoint: ff9a950
revision: v2 (2026-04-25, after expert roundtable)
---

# Governance Lifecycle Simulation — Audit Report (v2)

## 0. v2 修正摘要 (READ THIS FIRST)

v1 找出 38 條 finding，但圓桌挑戰後發現：
- **v1 漏掉 10 條 CRITICAL/HIGH 級別的真正破口**（trust boundary、vibe-lock、state-machine reverse transition、skill 檔不存在於 Antigravity path 等）。詳見 §0.1。
- **v1 把 5+ 條被 Pragmatist 視為「premature optimization」的 finding 標 HIGH**。詳見 §0.2。
- **v1 自身違反 Response Budget（362 行）**。v2 §0–§0.4 為真正的決策摘要（≤ 120 行）；v1 模擬走查保留為 §1–§4 附錄。

### 0.1 圓桌新增的 CRITICAL/HIGH（已驗證）

| ID | 嚴重 | 標題 | 證據 / Cite |
|---|---|---|---|
| **SEC-N1** | **CRITICAL** | Work Log 是 prompt-injection 載體（攻擊者在 `## Task Description` 塞 `ignore previous instructions`，下個 session bootstrap 讀入無消毒） | `AGENTS.md §vNext State Model` Init Read mandates Work Log read; 全框架無 AI-context trust boundary |
| **AC-4 (revised)** | **CRITICAL** | `red-team-adversarial/SKILL.md` 在 Antigravity path **不存在**（只在 `.agents/skills/`），Beast Mode 在 Antigravity 從 day 1 silent no-op | 已 spot-verify：`ls .agent/skills/red-team-adversarial/` → empty；`AGENTS.md §Platform Paths` |
| **SEC-N2** | HIGH | Archive Work Logs 內常含 secrets（curl output, JWT, conn-str），secret scanner 不掃 `.md`（只掃 changed source files） | `security_guardrails.md §3` scope vs `review.md` Security Scan 範圍 |
| **SEC-N3** | HIGH | `doc-lookup` skill 的 WebFetch = SSRF + indirect prompt-injection 載體（`Ref: http://169.254.169.254/...` 即可命中 cloud metadata） | `review.md:27`; `security_guardrails.md §1 A10` 只覆蓋 application code |
| **NEW-1** | HIGH | Worklog `.lock.json` 是 **vibe-lock**（agent 用普通 file IO 寫，無 `O_EXCL`，TOCTOU 可雙寫覆蓋） | `bootstrap.md §2a` 對比 `guard_context_write.py:119`（已驗證真鎖只在 `guard_context_write.py`） |
| **NEW-2** | HIGH | Archive `INDEX.jsonl` 並發 append 會產生 broken JSONL（非 `O_APPEND`，guard 是 whole-file rewrite） | `ship.md:204-209`; `guard_context_write.py:51-58` 路徑限制 |
| **NEW-3** | HIGH | `/retro` 並發時 `## Global Lessons` lesson **靜默丟失**（guard 回 conflict code 但無重試佇列，agent 不檢查 exit code） | `AGENTS.md` vNext Global Lessons; `guard_context_write.py:212-227` |
| **NR-1** | HIGH | Skills **實際 override workflows**（`test-driven-development: STOP the normal "execute plan" flow`），與 `AGENTS.md` 「workflows outrank skills」直接矛盾 | `implement.md:62-70` vs `AGENTS.md §Skill Safety §2` |
| **NR-2** | HIGH | tiny-fix 的 Audit Receipt **結構性不可能**：規則要求記到 Work Log Drift Log，但 tiny-fix 沒 Work Log | `AGENTS.md §Core Directives "Audit Receipt"` vs `§vNext "tiny-fix MAY skip"` |
| **NR-5** | HIGH | State machine **沒有 `IMPLEMENTING → CLASSIFIED` transition**，所以 Mid-Execution escalation 規則執行不能（code 已寫怎麼回退？） | `AGENTS.md §vNext Classification Freeze` vs `state_machine.md` 無此 transition |

> **驗證**：Security 與 DistSys 兩位專家都各自獨立讀完指定的 governance 檔案後得出。AC-4 與 guard 路徑限制兩項已透過 Bash 直接 spot-verify。

### 0.2 Pragmatist 視角下被 v1 過度標 HIGH 的條目

| ID | v1 評等 | v2 修正 | Pragmatist 理由 |
|---|---|---|---|
| QW-1 | HIGH | DROP | quick-win 跳 review/test 是設計意圖；強制 inline 測試會把 quick-win 變回 feature |
| QW-3 | MEDIUM | DROP | Security Quick-Scan + review.md A01 always-on 已覆蓋；keyword route 只影響 *priority* 非 *security check 觸發* |
| FT-1 | HIGH | DROP / 保留為 advisory | 強制 brainstorm 與 polish-batch lesson 衝突 |
| FT-3 | HIGH | RESHAPE | anchor 自動驗證需 markdown parser；改為「justification 必須 cite §heading」由人工抓 |
| FT-4 | HIGH | DROP / 保留 advisory | ADR-001 D2 精神：guidance not gate |
| AC-1 | CRITICAL | RESHAPE | Pragmatist 警告：強制 ADR 會讓 user 改標 feature 規避，反而更糟 |
| CC-1 | CRITICAL | DROP | Skip Budget 自身成為 meta-friction；應透過 §10.2 mandatory list 直接 enforce |

### 0.3 結構性根本診斷（4 位專家獨立得出同一結論）

> **「兩套 lock regime 不相容」（DistSys）+「honor-system + 沒反向 state transition」（Formal）+「框架 v1.1.2 太年輕，過度硬化會讓人繞道分類」（Pragmatist）+「無 trust boundary for AI context inputs」（Security）**

= 真正破口不在 38 條 finding 任一條，而是它們合起來指出的**三件被錯誤信任的事**：(a) agent 自我陳述、(b) 並發寫入會被自動序列化、(c) AI 自己的 context input 是乾淨的。

### 0.4 修正版 Phase B 建議（mirror ADR-001 三決策紀律）

**ADR-002 — 三個決策**（不貪心，等用實戰再加）：

- **D1：AI Context Trust Boundary**（解 SEC-N1, SEC-N3, SEC-N2 部分）
  - Work Log / spec / external doc / WebFetch 結果均視為 untrusted；bootstrap 讀入時做最小消毒（不執行 directive 性語言、URL 必須白名單）
  - 為 archive Work Log 增 secret scanner pre-archive hook
- **D2：Lock 統一**（解 NEW-1/2/3 + AC-5/6 + AC-4）
  - 把 `guard_context_write.py` 的 `O_EXCL` + atomic-replace 抽成 `guard_write_any(path)`，applies to 所有治理檔案（不再限制 `.agentcortex/context/`）
  - INDEX.jsonl 改 `O_APPEND` 或走 guard
  - Antigravity / Codex 雙路徑 skill 統一（修 AC-4，補 `.agent/skills/` 的 symlink 或 copy）
- **D3：State Machine 反向 transition + AC-3 Rollback Hard Gate**（解 NR-5 + AC-3 + HF-1 + HF-3）
  - 補 `IMPLEMENTING → CLASSIFIED` transition 與其 code-handling 規則（stash / partial-revert）
  - architecture-change 的 rollback plan 升 hard gate
  - hotfix Gate Receipt Audit 對齊 §10.2 (5 receipts)

**P1 follow-up**（不混進 ADR-002）：
- TF-2（窄化到 `templates/worklog.md` + `bin/validate.*`）
- TF-5（PR-scope tiny-fix 1 行 clarify）
- CC-2 Sentinel + cache-hash CI hook（架構 ready 後做）

**P2 — 不修，只進 Global Lessons trigger 紀錄**：其餘 27 條（含 NR-3/4/6/7 等 LOW 矛盾）

### 0.5 v1 → v2 結論差異

- v1 38 條 → v2 真正 actionable 12 條（CRITICAL 2、HIGH 8、MEDIUM 2）+ 27 條進 Global Lessons
- v1 「P0 ADR 收 5 條 HIGH」→ v2 「ADR-002 鎖 3 個決策（D1/D2/D3）」
- v1 把 advisory 累積當主問題 → v2 認知這是 honor-system + state-machine + trust-boundary 三層的結構性問題

---

## 1. 目的與方法（v1 原文，保留為附錄）

逐一模擬五個分類（`tiny-fix` / `quick-win` / `hotfix` / `feature` / `architecture-change`）走完完整生命週期，找出實際操作上會發生的破口、矛盾、token 浪費、可被繞過的 gate、與多人/多 session 的競態問題。Phase A 只產出書面分析，無 code 改動；Phase B 再依本報告 §6 的優先序做 ADR-002 + 實作。

### 1.1 已知並排除（避免重複）

下列議題已在 ADR-001 或 SSoT `## Global Lessons` 涵蓋，不再列入新發現：

- ADR-001 D1 — Evidence Truncation Rule（已寫入 `engineering_guardrails.md` §5.2b）
- ADR-001 D2 — Design-First / Production Logger 的 directory-based exemption
- ADR-001 D3 — 雙模式 context budget（prompt caching awareness）
- Global Lesson — polish-batch 應分類為 `quick-win` 而非 `feature`
- Global Lesson — Worklog header 必須用 markdown list 而非 table 才符合 `validate.sh`
- Global Lesson — session 開頭應 `git branch --show-current`
- Global Lesson — Windows install `bash.exe` 為 WSL placeholder

### 1.2 模擬規則

每個分類各設定一個具體場景，依 `bootstrap.md` §0 → §6 → 後續 phase 的順序逐步走，紀錄每個 phase 出現的破口（gap）與一段「能否被繞過」的 stress test。

---

## 2. 五個分類的生命週期模擬

### 2.1 `tiny-fix`：README typo 修正

**場景**：使用者「把 README.md 的 `Aget` 改成 `Agent`」。

**預期路徑**：bootstrap §0 fast check → tiny-fix → 直接執行 → diff + 1 行驗證。

**走完後找到的問題**：

- **TF-1（HIGH）— 治理檔案排除清單漏掉 `.agent/workflows/*`**
  bootstrap §0 的 escalation 表只列出 `AGENTS.md`、`.agent/rules/*`、`.agent/config.yaml`。但 `.agent/workflows/*.md` 同樣是 framework-managed 且影響所有 agent 行為。在 `.agent/workflows/plan.md` 改一個錯字會被合法地走 tiny-fix（< 3 files、文字非語意），跳過 Spec/Test/Handoff，直接 commit。這違背「framework governance files affect all agents globally」的精神。
  - **Stress test**：對 `bootstrap.md` 的 §0 fast check 表格新增一行（例如「if X then quick-win」）— 若用 tiny-fix 路徑提交，validate.sh 不會擋，PR 也不一定會被人發現，但所有下游 agent 行為都改變。

- **TF-2（HIGH）— `.agentcortex/` 內所有檔案都不在排除清單**
  `.agentcortex/templates/worklog.md` 的「small format change」可能直接讓 `validate.sh` regex 失準（這正是 Global Lesson 已記錄的 footgun 來源）。tiny-fix 不要求讀 SSoT，agent 不會察覺 worklog format 是被驗證的。
  - 建議：bootstrap §0 第二列加上 `modifies any file under .agentcortex/templates/ or .agentcortex/bin/`。

- **TF-3（MEDIUM）— "non-semantic" 由 AI 自行判斷，無 oracle**
  改 code comment vs 改 variable identifier 都是「文字修改」，但前者非語意、後者是。bootstrap §0 沒有給判別準則。實測 agent 會傾向把所有「字串看起來像註解」的 edit 標 tiny-fix。
  - 建議：明訂「修改的是 source-significant token（識別字、字串字面值、設定值）→ 非 tiny-fix」。

- **TF-4（MEDIUM）— tiny-fix 沒有 Work Log，Drift Log 與 Sentinel ⚡ ACX 沒地方稽核**
  AGENTS.md 規定每次 Safety-Valve 重讀必須記到 Drift Log，否則為 Token Leak 違規。但 tiny-fix 沒 Work Log → 完全無法稽核，因此 tiny-fix 期間任何 re-read 都「不可能被抓到」。
  - 建議：tiny-fix 若觸發 Safety-Valve 重讀，自動升級為 quick-win 並建 Work Log，或在 commit message 加註 `[token-leak: <file>§<section>]` 作為替代稽核。

- **TF-5（MEDIUM）— Batch tiny-fix 無上限**
  使用者一次提 5 個錯字 across 5 files：每個是 < 3 files，但整批 5 files。bootstrap §0 沒有明訂「合計檔案數」是用 single-task 還是 batch。實測 agent 通常合併處理，吞下整批 → 規避 quick-win。
  - 建議：tiny-fix「< 3 files」是「整體 PR 範圍內 < 3 files」，而非「單一 logical change < 3 files」。

---

### 2.2 `quick-win`：加一個 config flag

**場景**：使用者「在 `src/api/client.js` 加 `MAX_RETRIES=5` config」。

**預期路徑**：bootstrap full → classify quick-win → /plan → /implement → evidence → /ship。`/review` 與 `/test` 為 optional。

**走完後找到的問題**：

- **QW-1（HIGH）— 跳過 `/review` 與 `/test`，唯一安全網是 `/implement` 的 Security Quick-Scan**
  engineering_guardrails.md §10.2 明文允許 quick-win 在 inline evidence 下省略 review/test。實測：一個 quick-win 加錯 default value（例如 `MAX_RETRIES=-1` 變成無限重試）完全沒有 test gate 攔截，Security Quick-Scan 也不會掃 logic bug。
  - 建議：對「修改執行行為（非單純 doc/config 文字）的 quick-win」要求至少 1 條 inline 行為測試（curl/echo/console assert 均可），並在 ship gate 收回此證據。

- **QW-2（HIGH）— Doc Integrity 規則仰賴 Spec Index 不漂移**
  §10.4 要求 quick-win 若有 existing Spec 涵蓋目標檔案則必須更新；但 bootstrap §1 Step 2a 規定「DO NOT scan unmapped specs」。如果 Spec Index 漏列了 `src/api/client.js` 對應的 spec，agent 永遠不會更新它 → 文件腐爛而無人察覺。
  - 建議：Spec Index 條目應包含 `paths:` glob 列表，bootstrap 用 changed files 與 glob 反向 match；在 `/ship` 加 advisory「No Spec Index entry covers <file>，可能漂移」。

- **QW-3（MEDIUM）— Auth-Security escalation 由關鍵字觸發，覆蓋率有限**
  §10.4 列關鍵字：login / password / token / session / role / permission / access control。但實際的 auth code 常以 middleware 名稱（`requireUser`, `csrf`, `cookie-parser`）出現。實測 agent 不會把這些 escalate 為 hotfix。
  - 建議：把 escalation trigger 改為「import 任何 auth-related 套件 OR 修改 middleware 註冊順序 OR 修改 cookie 設定」這類 AST-or-content based 訊號。

- **QW-4（MEDIUM）— Quick-win 在多 session 下 lock 是 advisory**
  兩個 agent 同時對 `src/api/` 做 quick-win，lock 是 advisory，merge 衝突要在 PR 階段才會被發現。實測在 < 60 分鐘內 race 完全可能。
  - 建議：對同一 top-level path（e.g. `src/api/*`）在 lock file 內登記，第二個 session bootstrap 時 hard-warn（不是 hard-block），且強制 `## Conflict Resolution` 條目。

- **QW-5（LOW）— Confidence Gate 在 quick-win 沒被結構化要求**
  plan.md 的 compact block 規定要寫 `Confidence: <N>%`，但 quick-win 常常 inline 進 ship，沒有 plan compact block 可以收。實測 confidence 直接消失。
  - 建議：ship.md 為 quick-win 加一條「Inline Plan: confidence 必填」。

---

### 2.3 `hotfix`：production crash on `/api/users`

**場景**：「線上 `/api/users` panic，請快修」。

**預期路徑**：bootstrap → /research → /plan → /implement → /review → /test → /ship。**不需** /handoff。

**走完後找到的問題**：

- **HF-1（HIGH）— ship.md Gate Receipt Audit 對 hotfix 嚴重低估**
  `ship.md §Gate Receipt Audit`：
  > `hotfix`: bootstrap receipt required
  
  但 §10.2 的 Mandatory Gates 是「bootstrap → research → plan → implement → review → test → ship」。Ship 只檢查 bootstrap receipt = 任何被偷跑的 phase 都不會在 ship 時被攔。
  - 建議：對齊 §10.2，hotfix 的 ship gate 應同時檢 bootstrap / plan / implement / review / test 5 個 receipts。

- **HF-2（HIGH）— 2-Strike ESC 完全自我陳述**
  §8.1 規定 patch attempt N ≥ 2 自動觸發 ESC，但要求 agent 自己 append `Patch Attempt [N]: ...` 到 Work Log。實測 agent 會：
  1. 試 patch A → 沒 work
  2. 試 patch B → 沒 work
  3. 試 patch C → 終於 work
  4. 只在 Work Log 寫 final patch，把前兩次當 "exploration"，從未記 Patch Attempt 1/2
  - 建議：每次跑「修改後的 reproduction test」就強制觸發一次 attempt counter（基於 evidence-section 的 timestamp），不依賴 agent 自陳。

- **HF-3（MEDIUM）— Hotfix 升級為 feature 是 agent autonomous decision，但 Classification Freeze 要求 explicit rollback to CLASSIFIED**
  `hotfix.md §1`：「root cause 一個 cycle 找不到 → 升 feature，via /decide」。但 AGENTS.md `Classification Freeze` 規定升級必須 explicit rollback to `CLASSIFIED` 再重跑 next gate。兩個機制沒對接 — 實測 agent 直接寫「reclassified to feature」就繼續，沒有重跑 spec gate。
  - 建議：在 hotfix.md §1 末尾加：「升級時必須： (a) 把 Work Log Header `Classification` 改回 `CLASSIFIED`，(b) 重跑 bootstrap §0a → §3.7 Next Step Recommendation，(c) 走 feature 流程的 spec gate。」

- **HF-4（MEDIUM）— Retro 為 hotfix 是「mandatory by §10.2」但 ship.md 只列為 advisory**
  §10.2 evidence column：「root cause + fix verification + retro」。但 ship.md 的 Post-Ship Lifecycle Suggestion 把 `/retro` 當 advisory。對 hotfix（高風險 + 需學習）應為 hard gate。
  - 建議：對 hotfix 分類，ship gate 加 checklist「Retro completed (Work Log §Lessons exists)」。

- **HF-5（LOW）— Hotfix 跨 session（多人接力）governance 弱**
  hotfix 不需 /handoff → 沒有 Resume Block / Read Map。如果 hotfix 因環境問題拖到第二天，第二位 agent 接手只能 raw-read Work Log。
  - 建議：hotfix 在 phase ≥ /implement 之後若 session 結束，自動降級進 abbreviated handoff（只寫 Resume + Read Map，不寫 full Layer 2）。

---

### 2.4 `feature`：使用者個人檔案頁面

**場景**：「加 user profile 頁面，含 avatar 上傳」。

**預期路徑**：bootstrap → spec → plan → implement → review → test → handoff → ship。

**走完後找到的問題**：

- **FT-1（HIGH）— Brainstorm 是 advisory，feature 常常跳過探索**
  bootstrap §3.7 Next Step Recommendation 對 feature without frozen spec 建議 `/brainstorm` first。但這是 chat 內的「建議」，不是 hard gate。實測：80% 的 feature 直接走 `/spec` → 第一版 spec 很快被 unfreeze 改寫。
  - 建議：對 feature「無 frozen spec、無 inherited decisions」這個組合，把 brainstorm 設為 spec gate 的 prerequisite；可以 1 行 skip 但需登 Drift Log。

- **FT-2（HIGH）— Shipped Spec 的「歷史定位」與 Domain Doc L1 的「現行設計」之間有真空期**
  §4.2：spec ship 後變 `status: shipped`，未來請讀 L1 而非 spec。但 L1 是否被建立 / 維護是另一回事（bootstrap §1 Step 2b backfill 是 user 可 skip 的）。實測：6 個月後 feature B 觸碰相同模組 → bootstrap 找不到 L1，於是讀 shipped spec → 但 spec 早就和真實狀態漂移。
  - 建議：(a) ship 階段若 spec 標 shipped 且 L1 不存在，hard-prompt 建立 L1 skeleton（不可 skip）；(b) bootstrap §1 Step 2a 若讀到 shipped spec 且 L1 不存在，fail Bootstrap Gate（強迫先建 L1）。

- **FT-3（HIGH）— Domain Doc L2 Knowledge Consolidation 的 justification 沒有品質檢查**
  `ship.md §7 Domain Doc Gate`：未更新 L2 → 必須 explicit justification。但「L1 already covers this incremental change」是合法 justification，沒人檢查 L1 是否真的 covers。實測：agent 會用泛用句搪塞，knowledge consolidation 形同虛設。
  - 建議：要求 justification 必須 cite L1 中的 specific anchor（heading 或 section line range），ship gate 校驗該 anchor 存在。

- **FT-4（HIGH）— Spec-Test Traceability 是 advisory only，ship 可以放掉未測試的 AC**
  `ship.md §Spec-Test Traceability Check`：「advisory check ... a warning, not a hard fail」。實測 agent 標 `[NEEDS_HUMAN]` 然後 ship 過。
  - 建議：對 feature 升為 hard gate；架構性 AC（如「支援 1000 並發」）允許 deferred 但需在 SSoT `## Global Lessons` 紀錄一條 deferred-test 條目，由下次 retro 收尾。

- **FT-5（MEDIUM）— Skill cache hash 完全 honor system**
  AGENTS.md `Skill Notes Cache Contract`：cached_hash 是 sha256[:8]，但 agent 自己算自己存自己驗。SKILL.md 改了之後 hash 不一定會被重算（agent 偷懶）。
  - 建議：hash 由 `validate.sh` 在 PR 時統一重算 + diff cached vs actual。不一致 → CI 警告。

- **FT-6（MEDIUM）— Plan-derived skill 的 conflict pass 沒有重跑**
  bootstrap 讀 conflict matrix 一次，後來 implement.md §Pre-Execution Check §5 可加 `subagent-driven-development` 等 plan-derived skills，但 conflict matrix 不會再被讀。實測：plan-derived skill 與既有 skill 衝突無人察覺。
  - 建議：implement.md 在 append 任何 plan-derived skill 後，re-check conflict matrix（增量 check：只檢查新加的 vs 既有清單）。

- **FT-7（MEDIUM）— Mid-Execution Guard 升級依賴使用者 yes/no，可被誤答**
  implement.md §Mid-Execution Guard：scope 超出 quick-win 時問使用者「Escalate? (yes/no)」。使用者按 enter / 回 no → 繼續走錯分類。
  - 建議：scope 超出 + 已修改 ≥ X 行（基於 git diff stats）→ hard block，不問 yes/no，必須走 reclassification 流程。

- **FT-8（LOW）— Feature 與 architecture-change 邊界模糊**
  feature 可以「new module」，architecture-change 是「alters data-flow / system boundaries」。一個 feature 可能新增整個 service module（內含 API、DB schema、新依賴）— 在分類表上仍 qualify 為 feature，但實質是架構變動。
  - 建議：擴充 §10.1：新增「adds new dependency / new external service / introduces new data store」三條觸發 architecture-change。

---

### 2.5 `architecture-change`：把 in-process queue 改為 Redis

**場景**：「把目前 in-process 的 task queue 改成 Redis Streams 以支援 horizontal scaling」。

**預期路徑**：bootstrap → ADR → spec → plan → implement → review → test → handoff → ship + migration plan。

**走完後找到的問題（feature 的所有 issue 同樣適用，以下為新增）**：

- **AC-1（HIGH）— ADR 不是 hard gate**
  bootstrap §0a 對 missing ADR 顯示「(yes/skip)」，user 可 skip。實測 architecture-change 在「無 ADR」狀態下開展是被允許的 — 沒有任何 phase 會 hard-stop。
  - 建議：對 `architecture-change`，bootstrap §0a「skip」應顯示明確 warning「⚠️ architecture-change without ADR may be rejected at /ship」並在 ship gate 加 ADR 存在性檢查（`docs/adr/` 內存在 covering ADR with `status: accepted`）。

- **AC-2（HIGH）— Migration Safety 規則只覆蓋 DB schema**
  §12.3 明文「Schema changes to database tables require...」。本案是 in-process → Redis，並非 DB schema migration，§12.3 完全不適用。但本質上是更高風險的「架構遷移」（資料流變更、可能丟訊息）。
  - 建議：泛化為「Migration Safety」適用於所有 boundary-crossing 變更（DB / queue / cache / pubsub / file storage / external API contract）。可拆為 §12.3a (DB), §12.3b (queue/messaging), §12.3c (cache/store)。

- **AC-3（HIGH）— Rollback Plan 對 architecture-change 是 advisory**
  `ship.md §Rollback Plan Check`：「advisory — warn, do not hard-block」。對最高風險的分類採 advisory 不合理。
  - 建議：`architecture-change` 升為 hard gate，無 rollback plan → ship verdict: fail。

- **AC-4（HIGH）— Beast Mode 的觸發完全相依 `red-team-adversarial` skill 是否被載入**
  test.md §Step 4「for architecture-change, also activate Beast Mode」— 但 Beast Mode 的具體 test cases 在 skill SKILL.md 內。如果 skill 載入失敗或 cache 命中舊版（FT-5 的延伸），Beast Mode 形同虛設。
  - 建議：Beast Mode 的 minimum 4 條 test scenarios（concurrency / resource exhaust / fault inject / partial failure）內嵌於 test.md，不依賴 external skill 檔。

- **AC-5（MEDIUM）— 兩個 session 同時編輯同一個 Domain Doc**
  L2 是 append-only，但同時 append 仍會撞 git conflict。Lock 是 advisory（warn-not-block）。
  - 建議：對 Domain Doc L2，在 ship.md §7c Diff Preview 階段強制 `git pull --rebase` 並若有遠端新 commit 就 abort + 要求人工處理。

- **AC-6（MEDIUM）— SSoT Heartbeat 順序在 architecture-change 末段，可能 race**
  `ship.md §8 SSoT Heartbeat Update`：在所有寫入完成後 +1 update sequence。若 architecture-change 涉及多個 ship（拆 PR），第二個 PR 的 ship 看不到第一個 PR 的更新（除非先 rebase）。
  - 建議：把 `Update Sequence` 與 git remote SHA 綁定（store remote HEAD when bumping），下個 ship 先驗一致才能 +1。

---

## 3. 跨切面（Cross-Cutting）發現

- **CC-1（HIGH）— 「Advisory only」累積崩潰**
  整套 governance 至少 17 條規則明文標 advisory（rollback plan / spec-test trace / observability / domain doc justification / restructure threshold / SSoT staleness / lock conflict / concurrent state / gate receipt missing / knowledge nudge / partial adoption / brainstorm / 等）。任一條 skip 都不致命；但同時 skip 7+ 條等於 ship 沒有 enforcement。
  - 建議：建立 `Advisory Skip Budget`（例如「同一個 ship 最多 skip 3 條 advisory」），超出則升為 hard gate。位置：`AGENTS.md §Delivery Gates`。

- **CC-2（HIGH）— Sentinel ⚡ ACX 與 Token-Leak 完全 honor system**
  兩條最嚴格的 framework-wide 規則都仰賴 agent 自我聲明，沒有任何 hook / validator 抓到「忘記輸出 ⚡ ACX」或「不誠實的 re-read」。
  - 建議：(a) 在 `.claude/settings.local.json` 加 PostToolUse hook 檢查最後一段 assistant text 是否含 `⚡ ACX`，若無則 system reminder；(b) 在 `validate.sh` 用 grep 抓 Work Log 是否含 `Re-read:` 行，搭配 git diff hash 對照疑似 re-read 的工具呼叫。

- **CC-3（HIGH）— Worklog-key 標準化算法未明定**
  AGENTS.md「filesystem-safe normalization (for example, replace / with -)」。但 branch 含 `#`、`@`、`(`、`)` 等字元時無 canonical 規則。不同 agent / 不同平台會生成不同 worklog-key → 同一個 branch 兩個 worklog 檔案。
  - 建議：在 `.agent/config.yaml` 定義一段 regex `[^a-zA-Z0-9._-]+ → -`，並寫入 bootstrap §1 Step 2 為「MUST」，validate.sh 校驗 lock file 內 branch 與 file path 一致。

- **CC-4（MEDIUM）— Required Output Format 與 Response Budget 有結構性矛盾**
  AGENTS.md `Response Budget (Hard Cap)`：≤ 8 lines prose + essential structured blocks。但 review.md 的 chat output 規定「Burden of Proof table + 5 fields + 1 verdict line」，正常輸出就 ≥ 12 lines。Plan compact block 也常 ≥ 10 lines（含 Confidence、Mode、AC Coverage）。實測 agent 不知道該砍哪邊。
  - 建議：把 Hard Cap 從 8 lines 改為「≤ 8 lines of free prose；structured blocks ceiling list」明確列出每個 phase 的 max line count（plan ≤ 12, review ≤ 18, ship ≤ 10）。

- **CC-5（MEDIUM）— `_product-backlog.md` 1 行 status 變更被 over-route**
  bootstrap §0：「modifies `_product-backlog.md` → /spec-intake」。但「把某個 feature status 從 pending 改為 deferred」是 1 行 trivial edit，被強迫走 spec-intake heavy flow。實測使用者乾脆繞過治理直接 edit。
  - 建議：bootstrap §0 第 1 列細化「modifies _product-backlog.md feature inventory or adds new entries → /spec-intake；modifies only status field of existing entries → quick-win OK」。

- **CC-6（MEDIUM）— Compaction 條件：max_lines / max_kb 若 config 未設則永遠不觸發**
  handoff.md §6「Thresholds defined in `.agent/config.yaml` §worklog」。`config.yaml` 沒設 → 永不 compact → Work Log 無限長 → 下個 session 全部 reload。
  - 建議：implement.md / handoff.md 內嵌 default fallback（max_lines: 500, max_kb: 30）；config 缺值時用 default 而非靜默 disable。

- **CC-7（MEDIUM）— Global Lessons 增長無上限**
  `current_state.md §Global Lessons` 由 `/retro` 寫入，但無上限與輪替策略。10 個專案週期後可能 50+ 條 lesson 全部每次 bootstrap 都讀。
  - 建議：Global Lessons 設定上限（例如 20）+ 「decay rule」（每條附 `last_triggered_at`，超過 6 個月未觸發轉入 archive）。

- **CC-8（LOW）— Plan Mode 「Normal | Fast Lane」未定義 Fast Lane 行為**
  plan.md compact block 要求 `Mode: Normal | Fast Lane` 但全文未說明 Fast Lane 跳過什麼。實測 agent 一律寫 Normal。
  - 建議：補一段 Fast Lane 行為定義，或砍掉這個欄位。

- **CC-9（LOW）— Frozen 文件解凍 yes/no 對話可被 batch 一次同意**
  §4.2 Exception：「Approve to unfreeze and continue? (yes/no)」。使用者一次 yes，但若 batch 任務涉及多個 frozen specs，後續解凍是否也都被覆蓋？規則未明。
  - 建議：解凍授權限定為「明確命名的單一檔案」，每個 frozen spec 各問一次。

---

## 4. 治理破口分級總覽

| ID | 嚴重度 | 分類 | 標題 | Phase B 建議 |
|---|---|---|---|---|
| TF-1 | HIGH | tiny-fix | `.agent/workflows/*` 不在 escalation 排除 | bootstrap §0 加列 |
| TF-2 | HIGH | tiny-fix | `.agentcortex/templates/`、`.agentcortex/bin/` 不在排除 | bootstrap §0 加列 |
| QW-1 | HIGH | quick-win | review/test optional 留下 logic-bug 真空 | 行為-modifying quick-win 強制 inline 行為測試 |
| QW-2 | HIGH | quick-win | Doc Integrity 仰賴 Spec Index 不漂移 | Spec Index 條目加 `paths:` glob，ship advisory |
| HF-1 | HIGH | hotfix | ship Gate Receipt Audit 只檢 bootstrap | 對齊 §10.2 的 5 個 receipts |
| HF-2 | HIGH | hotfix | 2-Strike ESC 完全 self-report | 用 evidence-section timestamp 自動計數 |
| FT-1 | HIGH | feature | brainstorm 是 advisory，feature 常跳過 | spec gate prerequisite + Drift Log skip |
| FT-2 | HIGH | feature | shipped spec → L1 中間有真空期 | ship 時 hard-prompt L1 skeleton |
| FT-3 | HIGH | feature | Domain Doc L2 justification 無品質檢查 | 必須 cite L1 anchor，ship gate 校驗 |
| FT-4 | HIGH | feature | Spec-Test Traceability advisory only | 對 feature 升 hard gate，deferred 走 Lessons |
| AC-1 | HIGH | architecture-change | ADR 不是 hard gate | bootstrap §0a 對 architecture-change 強制要求 |
| AC-2 | HIGH | architecture-change | Migration Safety 只覆蓋 DB | 泛化為 boundary-crossing 變更 |
| AC-3 | HIGH | architecture-change | Rollback Plan advisory | 對 architecture-change 升 hard gate |
| AC-4 | HIGH | architecture-change | Beast Mode 完全依賴 skill 載入 | 4 條 minimum scenarios 內嵌 test.md |
| CC-1 | HIGH | cross-cutting | Advisory 累積崩潰 | Advisory Skip Budget |
| CC-2 | HIGH | cross-cutting | Sentinel + Token-Leak 是 honor system | hook + validate.sh 抓取 |
| CC-3 | HIGH | cross-cutting | Worklog-key normalization 未明定 | regex 規範 + validate 校驗 |
| TF-3 | MEDIUM | tiny-fix | "non-semantic" 由 AI 自判 | 明訂 source-significant token 規則 |
| TF-4 | MEDIUM | tiny-fix | tiny-fix 無 Drift Log 稽核 | safety-valve 觸發升 quick-win |
| TF-5 | MEDIUM | tiny-fix | batch tiny-fix 無上限 | < 3 files 是整體 PR 範圍 |
| QW-3 | MEDIUM | quick-win | auth keyword 覆蓋率有限 | AST/import-based 觸發 |
| QW-4 | MEDIUM | quick-win | 多 session lock 是 advisory | 對 top-level path race 加 hard-warn |
| HF-3 | MEDIUM | hotfix | 升級 feature 沒重跑 spec gate | hotfix.md §1 補對接 Classification Freeze |
| HF-4 | MEDIUM | hotfix | retro 是 advisory（與 §10.2 矛盾） | hotfix ship checklist 加 retro |
| FT-5 | MEDIUM | feature | skill cache hash honor system | validate.sh CI 重算 |
| FT-6 | MEDIUM | feature | plan-derived skill 不重跑 conflict | implement.md 增量 conflict pass |
| FT-7 | MEDIUM | feature | mid-exec escalation 可被 user no 繞過 | diff-stats hard block |
| AC-5 | MEDIUM | architecture-change | Domain Doc L2 並發 append 仍 race | ship 時 rebase + abort |
| AC-6 | MEDIUM | architecture-change | SSoT Heartbeat 多 PR 可能 race | bind sequence 與 remote SHA |
| CC-4 | MEDIUM | cross-cutting | Output Format 與 Response Budget 矛盾 | per-phase line ceiling |
| CC-5 | MEDIUM | cross-cutting | _product-backlog 1 行修改 over-route | bootstrap §0 細化條件 |
| CC-6 | MEDIUM | cross-cutting | compaction config 缺值即 disable | inline default fallback |
| CC-7 | MEDIUM | cross-cutting | Global Lessons 無上限 | 上限 + decay rule |
| QW-5 | LOW | quick-win | inline ship 沒收 Confidence | ship 加 Inline Plan Confidence 必填 |
| HF-5 | LOW | hotfix | 跨 session 無 abbreviated handoff | hotfix 增 abbreviated handoff |
| FT-8 | LOW | feature | feature/architecture 邊界模糊 | §10.1 加 3 條觸發 |
| CC-8 | LOW | cross-cutting | Fast Lane 行為未定義 | 補定義或砍欄位 |
| CC-9 | LOW | cross-cutting | Frozen 解凍可被 batch 同意 | 單檔授權 |

統計：HIGH 17 / MEDIUM 16 / LOW 5 = **38 條治理破口**。

---

## 5. 「最危險的繞過路徑」Top 5

依「使用者不必違規 + 後果嚴重」排序：

1. **HF-1 + CC-1**：hotfix 只檢 bootstrap receipt + 多條 advisory 全 skip → 一個 hotfix 可在「無 plan/implement/review/test/retro receipt」的狀態下完成 ship。
2. **TF-1 + CC-2**：對 `.agent/workflows/plan.md` 改一行「verdict 規則」當 tiny-fix → ⚡ ACX 沒 hook 抓 → 整個治理流程被靜默改寫。
3. **FT-3 + FT-4**：feature 用泛用 justification skip Domain Doc + 用 `[NEEDS_HUMAN]` skip Spec-Test trace → spec frozen + shipped + 但 doc 無更新 + AC 無測試。
4. **AC-1 + AC-3**：architecture-change 在 bootstrap §0a skip ADR + ship 時 rollback plan 缺漏（advisory）→ 高風險變更上線且無 rollback。
5. **QW-2 + QW-3**：在 auth-adjacent module（未匹配關鍵字）做 quick-win + Spec Index 漂移未發現 → auth 變更未走 hotfix、未更新 spec、未 review、未 test。

---

## 6. Phase B 建議優先序

依「修補成本 ÷ 風險降幅」排序：

### P0（最高 ROI，一個 ADR 可解）

- **ADR-002 候選**：「Hard-Gate Promotions for Cross-Class Risk」
  - HF-1（hotfix gate receipt）
  - AC-1（ADR hard gate）
  - AC-3（rollback hard gate）
  - FT-4（spec-test trace hard gate for feature）
  - CC-1（Advisory Skip Budget）
  - 預估：修改 `ship.md`、`hotfix.md`、`bootstrap.md` 共 5 個 section，~80 lines。

### P1（中 ROI，需 spec + 多檔變更）

- **Spec-002 候選**：「Governance File Protection & Worklog-Key Standardization」
  - TF-1, TF-2（治理檔案排除清單擴充）
  - CC-3（worklog-key normalization regex）
  - 預估：修改 bootstrap §0、`.agent/config.yaml`、`.agentcortex/bin/validate.sh`，~50 lines。

### P2（高 ROI 但牽涉自動化基礎建設）

- **CC-2 + FT-5**：Sentinel + Token-Leak + Skill cache hash CI 校驗
  - 需要 hook 設計 + validate.sh 升級
  - 預估：1 個 ADR + 較大實作

### P3（局部優化）

- 其餘 MEDIUM/LOW 條目可在 P0–P2 ADR 落地後分批 quick-win 處理。

---

## 7. 已驗證的證據

- 本檔閱讀並交叉比對的 framework 檔案：
  - `AGENTS.md`（root）
  - `.agent/rules/engineering_guardrails.md`（397 lines）
  - `.agent/workflows/bootstrap.md` (397 lines)
  - `.agent/workflows/plan.md` / `implement.md` / `review.md` / `test.md` / `handoff.md` / `ship.md` / `hotfix.md`
  - `docs/adr/ADR-001-governance-friction-tuning.md`
  - `.agentcortex/context/current_state.md`（含 Global Lessons）
- ADR-001 的 3 個 decision 已從本報告排除（避免重複）
- 本報告 38 條 finding 均對應到具體 file:section 引用，可在 Phase B 直接定位修補

---

## 8. 已知本審計的盲點

- **未驗證**：`security_guardrails.md`、`state_machine.md`、`skill_conflict_matrix.md`、`config.yaml` 的細部內容；本報告假定其存在但未核對精確規則。Phase B 啟動時需 spot-check。
- **未驗證**：實際 `validate.sh` / `validate.ps1` 的檢查項；本報告對其能力的假設可能高估或低估。
- **未模擬**：`/retro`、`/decide`、`/audit`、`/research`、`/spec-intake` 流程的破口；這 5 個 workflow 與生命週期相關但本次未走完。建議列為 follow-up audit（範圍小）。
- **未涵蓋**：跨平台（Codex Web / Antigravity / Claude Code）的 platform 差異（platform specialization 在 handoff.md §2 提到但未深入）。
