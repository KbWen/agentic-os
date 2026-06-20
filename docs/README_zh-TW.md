<h1 align="center">Agentic OS</h1>

<p align="center">
  <strong>「Done。」—— 你的 AI coding agent,對著它根本沒測過的程式碼這樣說。</strong><br/>
  一份 rules 檔只是「請」agent 守規矩。Agentic OS <strong>會去查它到底有沒有做到</strong> —— agent 想跳過測試、跳過 review、或把外洩的密鑰送進 commit,都會撞上你的 git hooks、validator 和 CI,而不是聽 agent 自己一句話。
</p>

<p align="center">
  <strong>一套給 AI coding agent 的治理框架</strong> —— 用工作流程、交付閘門與工程護欄,為 Claude Code、Codex、Cursor、Copilot、Antigravity,或任何讀得懂 Markdown 的 agent 把關。
</p>

<p align="center">
  <a href="https://github.com/KbWen/agentic-os/releases"><img src="https://img.shields.io/github/v/release/KbWen/agentic-os?style=flat-square&label=release" alt="Release"/></a>
  <a href="https://github.com/KbWen/agentic-os/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/KbWen/agentic-os/validate.yml?branch=main&style=flat-square&label=CI" alt="CI"/></a>
  <a href="https://github.com/KbWen/agentic-os/actions/workflows/security.yml"><img src="https://img.shields.io/github/actions/workflow/status/KbWen/agentic-os/security.yml?branch=main&style=flat-square&label=Security" alt="Security"/></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="MIT"/></a>
  &nbsp;·&nbsp;
  <a href="../README.md">English</a> ·
  <a href="../CONTRIBUTING.md">Contributing</a> ·
  <a href="../CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img src="assets/concept-hero-zh.png" alt="一個 AI coding agent 自信地宣稱「Done. Tests pass. Shipping it.」,Agentic OS 在這句宣稱上蓋了一個「[citation needed]」的章。Agentic OS 會查證你的 AI agent 所宣稱的事 —— 外洩密鑰、沒寫的測試、被跳過的 review —— 靠 git hooks 和 CI,而不是聽 agent 自己說。" width="820"/>
</p>

<p align="center"><sub>它會查你的 AI coding agent 宣稱的事情背後有沒有證據 —— 密鑰、測試、review —— 靠的是 git hooks 和 CI,不是 agent 一句話。下面就是一道閘門實際擋下來的樣子:</sub></p>

<p align="center">
  <img src="assets/workflow-demo-zh.gif" alt="終端機裡,一個 AI coding agent 宣稱任務完成並嘗試 ship;Agentic OS 的閘門因為 work trail 裡沒有 review 或測試的證據而回傳 verdict FAIL、擋下 ship,直到 review、測試與證據都補齊才放行。" width="800"/>
</p>

上面的 `/bootstrap`、`/review`、`/ship` 都只是純文字 prompt —— 你的 agent 會把它們對應到 repo 裡的 workflow 檔,所以在 Cursor 或 Codex 裡跑起來,跟在 Claude Code 裡一樣。

其中一道閘門你現在就能跑,免安裝 —— 在外洩金鑰進到 git 歷史之前抓住它:

```sh
bash demo/run.sh          # Windows(PowerShell):pwsh demo/run.ps1
```

<details>
<summary>完整終端機輸出</summary>

```text
  An AI agent wrote this file and reported: "Done — config added."
  ----------------------------------------------------------------
    DB_HOST=prod.internal
    aws_access_key_id = AKIA****************
  ----------------------------------------------------------------

  Without a gate, that commit lands and the key is in git history forever.
  Agentic OS runs this before the commit is allowed:

    $ scan_credentials.py config.env

CREDENTIAL PATTERN(S) DETECTED (values redacted):
  config.env:2: aws-access-key-id
Rotate the exposed secret, remove it from the change, then retry.

  Commit BLOCKED. The agent said "done"; the machine said no — and it
  redacted the value instead of echoing your secret back at you.
```

</details>

agent 還是可以偷工減料。它做不到的,是讓外洩的密鑰、零測試的綠勾勾、或被跳過的 review 通過 hooks 和 CI —— 那些檢查不管它配不配合都會跑。上面那把金鑰是執行時即時產生、輸出時遮蔽的,所以這個 demo 從不存下真正的密鑰。

## 規則 vs. 強制

一份 rules 檔 —— Cursor Rules、或一份單純的 `AGENTS.md` —— 是一段 agent 可以無視的 prompt。Agentic OS 保留那份紀律(先計畫再動手、不做沒人要求的重構),再加上一層 agent 控制不了的東西:

| 失誤型態 | 誰擋下它 | 在哪 |
|:---|:---|:---|
| 密鑰被 commit 進歷史 | `scan_credentials.py`(上面的 demo) | pre-commit hook + CI |
| 「測試通過」但根本沒測試 | CI 跑真正的測試套件 | pull request |
| 跳過某個階段、沒有證據 | `validate.sh` 讀 work trail | pre-commit(本機) |

第三列是 rules 檔碰不到的地方:`validate.sh` 會解析每個任務的 work log,只要少了某個必要階段、或它的證據不見了,就讓檢查失敗。本機的 pre-commit hook 是選用的,你可以用 `--no-verify` 繞過;CI 才是那道無法跳過的底線。上面那顆 Security 徽章,就是這個 repo 在自己每次 push 時跑同一套密鑰與 SAST 閘門。

## 分階段把關,依風險縮放

每個任務都跑一條有閘門的工作流,而嚴謹度會依風險縮放。跳過一個階段,`validate.sh` 就失敗 —— 但改一個 typo 不必跟一個 feature 走同一條關卡:

<p align="center">
  <img src="assets/pipeline-demo-zh.gif" alt="Agentic OS 工作流的示意圖:一個 tiny-fix 任務走過 classify、execute、done 三步短路徑後 ship,而一個 feature 任務走完整的有閘門流程(bootstrap、plan、implement、review、test、ship),在 ship 閘門因為跳過測試而被擋下,直到測試證據補上才通過。" width="820"/>
</p>

完整的路徑,依分類:

| 分類 | 必經階段 |
|:---|:---|
| **tiny-fix** | Classify → Execute → Evidence → Done |
| **quick-win** | Bootstrap → Plan → Implement → Evidence → Ship |
| **feature** | Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship |
| **hotfix** | Bootstrap → Research → Plan → Implement → Review → Test → Ship |
| **architecture-change** | Bootstrap → ADR → Spec → Plan → Implement → Review → Test → Handoff → Ship |

## 你得到什麼

| | |
|:---|:---|
| **機器強制的底線** | 上面那些失敗模式,是由你的 git hooks、validator 和 CI 攔下的 —— 不是靠 agent 自己回報。agent 可以偷工,但它沒辦法讓那一步通過它管不到的檢查。 |
| **依階段自動掛上的 skill** | 工作流會依任務型態,把對的檢查清單放到 agent 面前 —— feature 上 TDD、login 程式碼上 auth-security —— 你不必手動接線。是引導,不是閘門。 |
| **跨交接還活著的記憶** | 決策與證據存在單一真實狀態檔裡,所以它們會跨 session、跨 agent 留下來,而不是隨對話一起重置。 |
| **跨平台** | 同一套治理檔通吃每個主流 AI coding agent —— 不管你跑哪一個,規則都一樣。 |
| **天生省 token** | 治理依風險縮放:tiny-fix 跳過笨重的護欄(約省 5,000 token),修個 typo 不必付旗艦模型的價。 |

<details>
<summary><strong>工作流依任務型態自動掛上的 14 個 skill</strong></summary>

工作流會依分類掛上這些 skill,讓相關的檢查清單在對的階段就在 agent 面前 —— 碰 login 程式碼時掛 auth-security,做 migration 時掛 forward-only 檢查。它們是結構化的引導,不是機器閘門(閘門是上面的 hooks、validator 和 CI);它們省掉的是手動接線。

| Skill | 觸發 | 重點 |
|:---|:---|:---|
| Test-Driven Development | feature、architecture-change | Red → Green → Refactor 循環 |
| Systematic Debugging | 遇到 bug | 4 階段根因分析 |
| Red Team / Adversarial | review、test | 依分類的資安分析 |
| API Design | 偵測到 API 端點 | 端點驗證強制 |
| Auth Security | 偵測到 auth 程式碼 | hashing、token、rate limiting |
| Database Design | 偵測到 migration | forward-only、ORM-aware 的 migration 安全 |
| Frontend Patterns | UI 元件 | 元件與狀態管理樣式 |
| Parallel Agent Dispatching | 複雜任務 | 協調 subagent 執行 |
| Subagent-Driven Development | 多模組任務 | 多 agent 協作 |
| Karpathy Principles | 所有 coding 任務 | 針對 LLM 常見錯誤的行為護欄 |
| Production Readiness | feature、architecture-change | 上線前可觀測性:錯誤匯流、log 策略、rollback 遙測 |
| Verification Before Completion | /ship | 5 道閘門:Scope → Quality → Evidence → Risk → Communication |
| Git Worktrees | 平行分支 | worktree 隔離工作流 |
| Doc Lookup | 需要查文件 | 文件檢索策略 |

</details>

<details>
<summary><strong>多 agent & 跨交接的記憶</strong></summary>

為多個 AI session —— 或多人的 agent —— 同時動同一個 repo 而設計:

```
.agentcortex/context/
├── current_state.md          # 全域專案狀態(單一真實來源)
└── work/
    └── <branch-name>.md      # 每任務的 work log(隔離,含證據 + 閘門收據)
```

- **一個分支 = 一個 owner** —— 防止並發的 work-log 污染。
- **單一寫入者鎖** —— 原子鎖檔擋掉同分支上互撞的 session(可調回 advisory)。
- **Ship guard** —— 合併前檢查單一真實來源有無衝突。
- **Session 身分** —— 每個 AI session 都記下自己的模型名與時間戳,讓交接可追溯。

</details>

## 支援你的 agent

| 平台 | 狀態 | 整合 |
|:---|:---|:---|
| **Claude Code** | 原生 | `CLAUDE.md` 入口 + Claude 平台指南 |
| **OpenAI Codex** | 原生 | `AGENTS.md`、Codex 平台指南、CLI 委派工作流 |
| **Google Antigravity** | 原生 | Intent router + Antigravity runtime 指引 |
| **Cursor** | 相容 | 讀 `AGENTS.md` / project-rule 風格的指引 —— 斜線指令只是純 prompt |
| **GitHub Copilot** | 相容 | 用 repository instructions 與護欄文件 |
| **任何 LLM agent** | 相容 | 模型無關的 Markdown 工作流 + 證據規則 |

不管哪一種,真正的底線都一樣:git hooks 和 CI 不在乎你跑的是哪個 agent。

## 快速開始

```bash
git clone https://github.com/KbWen/agentic-os.git
./agentic-os/installers/deploy_brain.sh --dry-run /path/to/your-project   # 預覽,不動任何檔
./agentic-os/installers/deploy_brain.sh /path/to/your-project             # 部署
```

然後對你的 agent 說:*「讀 `AGENTS.md` 並遵循它。在 /review 與 /test 通過前,不准宣稱完成。」* —— 接著 `/bootstrap` 加上你的任務。

| 你的起點 | 第一個指令 |
|:---|:---|
| 全新專案、多 feature 想法 | `/spec-intake` |
| 既有 repo 首次導入 Agentic OS | `/audit`(唯讀,零風險) |
| 單一明確任務 | `/bootstrap` |

既有檔案永遠不會被覆寫(會存成 `.acx-incoming` sidecar 讓你合併)。Windows / 無 Python 模式、更新、客製化、完整開場提示 → **[docs/INSTALL.md](INSTALL.md)**。

### 客製化而不衝突

升級無痛的原則只有一條:**只「加」你自己的檔,絕不原地編輯框架檔。** 加自己的 skill 放 `.agents/skills/custom-<name>/`(`custom-*` 是框架永不 ship 的保留 namespace);加專案治理放 `AGENTS.override.md`(可窄化/停用指令,但**不得**放寬交付閘門);調整 skill 啟用放 `.agentcortex/context/private/user-preferences.yaml`。原地改框架檔會在 `git pull upstream`(fork)或下次 `deploy`(clone)被覆蓋。完整說明見 [docs/INSTALL.md](INSTALL.md)。

## 常見問題

**Agentic OS 是什麼?**
一套給 AI coding agent 的開源治理框架。它讓 Claude Code、Codex、Cursor、Copilot、Antigravity 這類 agent 有一條可重複的工作流 —— plan、build、review、test、ship —— 並用閘門強制,讓它們不能跳步驟、也不能在沒有可驗證證據下宣稱「done」。

**我要怎麼擋住 AI agent 跳過測試、或 ship 沒驗證過的程式碼?**
這就是核心。密鑰掃描、測試套件、階段/證據 validator 都跑在你的 git hooks 和 CI 裡 —— 所以外洩密鑰、缺測試、跳過的 review 會讓 commit 或 build 失敗,不管 agent 怎麼回報。agent 還是能偷工,只是那個工偷不過它控制不了的檢查。

**它跟 Cursor Rules 或單純一份 `AGENTS.md` 差在哪?**
rules 檔告訴 agent 怎麼做,agent 可以無視。Agentic OS 加上工作流、以及把行為釘住的檢查:階段順序、證據要求、scope 紀律,還有一份跨 session 記住決策的單一真實來源。skill 和紀律仍是 agent 跟隨的「引導」;真正被「強制」的,是那層會讓你 commit 或 CI 失敗的東西 —— 外洩密鑰、缺測試、被跳過的階段。

**會被綁死在單一 AI 廠商嗎?**
不會。它是模型無關的 Markdown —— 對 Claude Code(`CLAUDE.md`)和 Codex / Antigravity(`AGENTS.md`)有原生入口,並透過同一套 workflow 檔支援 Cursor、Copilot 與任何其他 LLM agent。

**免費嗎?**
是 —— MIT 授權。fork 它、ship 它。

## 文件

| 目標 | 從這裡開始 |
|:---|:---|
| 安裝、更新、客製化 | [安裝與使用](INSTALL.md) |
| 查所有指令、架構與原則 | [Reference](reference.md) |
| 選模型 · 看真實 token 成本 | [模型指南](AGENT_MODEL_GUIDE_zh-TW.md) · [生命週期基準](LIFECYCLE_BENCHMARK_zh-TW.md) |
| 核心原則與測試標準 | [設計哲學](../.agentcortex/docs/AGENT_PHILOSOPHY_zh-TW.md) · [測試協議](../.agentcortex/docs/TESTING_PROTOCOL_zh-TW.md) |
| 平台專屬注意事項 | [Codex](../.agentcortex/docs/CODEX_PLATFORM_GUIDE_zh-TW.md) · [Claude](../.agentcortex/docs/CLAUDE_PLATFORM_GUIDE_zh-TW.md) |
| 連接外部知識庫(選用) | [連接知識庫](../.agentcortex/docs/guides/connecting-a-knowledge-base.md) |

## 貢獻

見 [CONTRIBUTING.md](../CONTRIBUTING.md) —— 不論你是人類還是 AI agent 的貢獻指引。

## 授權

MIT。見 [LICENSE](../LICENSE)。

<p align="center"><sub>一套給 AI coding agent 的治理框架。歡迎貢獻與回饋。</sub></p>
