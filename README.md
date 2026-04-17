<p align="center">
  <img src="https://img.shields.io/badge/Agentic OS-v1.1-blueviolet?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDEgMC04LTMuNTktOC04czMuNTktOCA4LTggOCAzLjU5IDggOC0zLjU5IDgtOCA4eiIvPjwvc3ZnPg==" alt="Agentic OS v1.1"/>
</p>

<h1 align="center">Agentic OS</h1>

<p align="center">
  <strong>The governance-first operating system for AI coding agents.</strong><br/>
  Structured workflows, delivery gates, engineering guardrails, and 17 professional skills<br/>
  that work across Claude Code, Cursor, GitHub Copilot, Google Antigravity, and Codex.
</p>

<p align="center">
  <a href="https://github.com/KbWen/agentic-os/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/KbWen/agentic-os/validate.yml?branch=main&style=flat-square&label=CI" alt="CI Status"/></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT License"/></a>
  <img src="https://img.shields.io/badge/Claude_Code-Ready-8b5cf6?style=flat-square" alt="Claude Code"/>
  <img src="https://img.shields.io/badge/Antigravity-Compatible-3b82f6?style=flat-square" alt="Antigravity"/>
  <img src="https://img.shields.io/badge/Codex-Ready-f59e0b?style=flat-square" alt="Codex"/>
  <img src="https://img.shields.io/badge/Cursor-Compatible-ec4899?style=flat-square" alt="Cursor"/>
</p>

<p align="center">
  <a href="docs/README_zh-TW.md">繁體中文</a> &middot;
  <a href="CONTRIBUTING.md">Contributing</a> &middot;
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## The Problem

AI coding agents are powerful but undisciplined. Without structure, they:

- **Skip steps** — jump straight to code without planning or reviewing
- **Hallucinate completion** — claim "done" without verifiable evidence
- **Drift from scope** — refactor code nobody asked them to touch
- **Lose context** — forget decisions across conversations, forcing re-derivation
- **Break things silently** — no safety gates between "idea" and "production"

## The Solution

**Agentic OS** is a drop-in governance framework that makes any AI agent follow professional engineering workflows. Install it into your project, and your AI agents gain:

```
   Intent          Gate           Workflow         Evidence        Ship
  ┌──────┐      ┌──────┐       ┌──────────┐     ┌──────────┐   ┌──────┐
  │ User │ ───▸ │ Gate │ ───▸  │ Workflow  │ ──▸ │ Evidence │ ─▸│ Ship │
  │ says │      │Engine│       │ + Skills  │     │ Required │   │ SSoT │
  └──────┘      └──────┘       └──────────┘     └──────────┘   └──────┘
                  │ FAIL                           │ FAIL
                  ▼                                ▼
               ⛔ STOP                          ⛔ STOP
```

**No evidence = no completion. No gate = no progression. No exceptions.**

---

## Features

### 🔒 Gate Engine & Phase System

Every task flows through mandatory phases. The AI cannot skip ahead.

```mermaid
flowchart LR
    B["/bootstrap"] --> P["/plan"]
    P --> I["/implement"]
    I --> R["/review"]
    R --> T["/test"]
    T --> S["/ship"]

    style B fill:#8b5cf6,color:#fff,stroke:none
    style P fill:#3b82f6,color:#fff,stroke:none
    style I fill:#22c55e,color:#fff,stroke:none
    style R fill:#f59e0b,color:#fff,stroke:none
    style T fill:#ef4444,color:#fff,stroke:none
    style S fill:#06b6d4,color:#fff,stroke:none
```

| Classification | Required Phases |
|:---|:---|
| **tiny-fix** | Classify → Execute → Evidence → Done |
| **quick-win** | Bootstrap → Plan → Implement → Evidence → Ship |
| **feature** | Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship |
| **hotfix** | Bootstrap → Research → Plan → Implement → Review → Test → Ship |
| **architecture-change** | Bootstrap → ADR → Spec → Plan → Implement → Review → Test → Handoff → Ship |

### 🛡️ Engineering Guardrails

A constitution for AI behavior — loaded automatically, enforced at every phase:

- **No Evidence = No Completion** — narrative claims are not proof
- **Scope Discipline** — unauthorized refactoring is strictly prohibited
- **Destructive Command Blocking** — `rm -rf`, `git reset --hard`, force pushes require pre-approved rollback plans
- **OWASP Top 10 Auto-Scan** — security checks run during `/implement` and `/review`
- **Confidence Gate** — AI must declare confidence level; low confidence triggers escalation

### ⚡ 17 Professional Skills

Skills auto-activate based on task classification and workflow phase:

| Skill | Trigger | Description |
|:---|:---|:---|
| Test-Driven Development | feature, architecture-change | Red → Green → Refactor cycles |
| Systematic Debugging | bug encounter | 4-phase root cause analysis |
| Red Team / Adversarial | review, test | Classification-based security analysis |
| API Design | API endpoints detected | Endpoint validation enforcement |
| Auth Security | auth code detected | Hashing, tokens, rate limiting |
| Database Design | migration detected | Forward-only ORM-aware migration safety |
| Frontend Patterns | UI components | Component and state management patterns |
| Parallel Agent Dispatching | complex tasks | Coordinated subagent execution |
| Subagent-Driven Development | multi-module tasks | Multi-agent coordination |
| Writing Plans | /plan | Plan structuring and validation |
| Executing Plans | /implement | Plan execution with checkpoints |
| Requesting Code Review | /review | Code review request protocol |
| Receiving Code Review | post-review | How to integrate feedback |
| Verification Before Completion | /ship | 5-gate check: Scope → Quality → Evidence → Risk → Communication |
| Git Worktrees | parallel branches | Worktree isolation workflows |
| Finishing a Branch | pre-merge | Mainline re-sync and closure |
| Doc Lookup | documentation needed | Documentation retrieval strategy |

### 🧠 Single Source of Truth (SSoT)

Every project has one canonical state file. AI agents read it first, write to it last.

```
.agentcortex/context/
├── current_state.md          # Global project state (SSoT)
└── work/
    └── <branch-name>.md      # Per-task work log (isolated)
```

- **Work Logs** track per-task progress, evidence, and gate receipts
- **SSoT** tracks global decisions, lessons, and ship history
- **Handoff** enables seamless AI-to-AI continuity across conversations

### 👥 Multi-Agent Collaboration

Built for teams where multiple AI sessions work on the same codebase:

- **One Branch = One Owner** — prevents concurrent Work Log corruption
- **Advisory Locking** — lock files signal active sessions without blocking
- **Ship Guard** — checks for SSoT conflicts before merging
- **Session Identity** — every AI session writes its model name and timestamp

### 🚀 Recommended: Start with /audit

New to Agentic OS? Run `/audit` first — it's a **read-only** traversal that maps your existing codebase with zero risk:

```
/audit  →  /app-init  →  /spec-intake  →  pick a quick-win  →  full feature
```

See the [Lifecycle Benchmark](docs/LIFECYCLE_BENCHMARK.md) ([繁體中文](docs/LIFECYCLE_BENCHMARK_zh-TW.md)) for real token consumption data across 6 development scenarios.

### 📉 Token Efficiency

Designed for cost-effective models (Gemini Flash, Haiku, etc.):

- **Conditional Loading** — tiny-fix skips guardrails (~5,000 tokens saved)
- **Skill Cache Policy** — metadata-first loading, full SKILL.md only on cache miss
- **Phase Summary** — compact 1-liner per phase for low-token resume
- **Read-Once Discipline** — governance docs persist in context, never re-read

---

## Quick Start

### 1. Install

**Prerequisites**:

| Dependency | Required? | Purpose |
|:---|:---|:---|
| **Git** | Required | Clone and deploy the framework |
| **Bash** | Required | Run deploy & validate scripts (Git Bash from [Git for Windows](https://gitforwindows.org/) is enough on Windows) |
| **Python 3.9+** | Recommended | Enables full validation (metadata, encoding, command sync checks) |
| **SHA-256 tool** | Required for deploy | `sha256sum`, `shasum`, or `openssl` (pre-installed on most systems) |

> **No Python?** The framework deploys and works without Python. Validation runs in
> degraded mode — Python-dependent checks report `WARN` instead of `FAIL`.
> Pass `--no-python` to suppress warnings: `bash .agentcortex/bin/validate.sh --no-python`

**Install (first time):**

```bash
# Clone Agentic OS
git clone https://github.com/KbWen/agentic-os.git

# Preview what will be deployed (no changes made)
./agentic-os/installers/deploy_brain.sh --dry-run /path/to/your-project

# Deploy into your project
./agentic-os/installers/deploy_brain.sh /path/to/your-project
```

**Update (after first install):** the installer lives inside your project. Run it from your project root — it reads the deploy manifest and auto-fetches the latest framework version from GitHub.

```bash
bash installers/deploy_brain.sh .
```

> **Existing files won't be overwritten.** If your project already has `AGENTS.md`, `CLAUDE.md`, or other framework-managed files, they are preserved. The new framework version is saved as `<filename>.acx-incoming` sidecar. Review and merge manually — or ask your AI agent: *"Merge each .acx-incoming into its target, preserving my project-specific content and adopting framework updates."*

> **AI-agent install:** If you're asking an AI assistant to install Agentic OS, point it to this README. The commands above are deterministic — no platform-specific heuristics required.

<details>
<summary><b>Windows (PowerShell / CMD)</b></summary>

```powershell
# Clone Agentic OS (first time)
git clone https://github.com/KbWen/agentic-os.git

# Deploy into your project
powershell -ExecutionPolicy Bypass -File .\agentic-os\installers\deploy_brain.ps1 C:\path\to\your-project

# CMD alternative
.\agentic-os\installers\deploy_brain.cmd C:\path\to\your-project
```

Use the PowerShell entrypoint when possible. It resolves Git Bash directly and does not require a WSL distro.

```powershell
# Already installed? Run from your project root to update:
powershell -ExecutionPolicy Bypass -File .\installers\deploy_brain.ps1 .

# Validation after install
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1

# Lightweight validation when Python is not installed
bash ./.agentcortex/bin/validate.sh --no-python
```

</details>

<details>
<summary><b>Text-only usage (no scripts)</b></summary>

If you only want the governance templates (Markdown files) without running any tooling:

1. Copy the `.agent/`, `.agents/`, and `AGENTS.md` files into your project
2. Optionally copy `.agentcortex/context/` and `.agentcortex/templates/` for state management
3. No Python, Bash, or other tools are needed — all governance is plain Markdown

</details>

### 2. Start Working

Tell your AI agent:

> "Read `AGENTS.md` and bootstrap this task."

Or use a slash command directly:

```
/bootstrap
```

### 3. Follow the Flow

The AI will classify your task and follow the required phases automatically:

```
You: "Add pagination to the user list API"

AI: [/bootstrap] → Classification: feature
    → Required: Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship
    → Loading skills: API Design, Test-Driven Development
    → ⚡ ACX
```

---

## Commands

| Command | Purpose |
|:---|:---|
| `/bootstrap` | Initialize task, classify scope, create work log |
| `/spec-intake` | Import and decompose external specs |
| `/spec` | Define verifiable specifications |
| `/plan` | Create implementation plan with rollback steps |
| `/implement` | Execute code changes (gate-protected) |
| `/review` | Logic, security, and scope audit |
| `/test` | Verify with minimal necessary tests |
| `/handoff` | Resumable state summary for next session |
| `/ship` | Consolidate evidence, update SSoT, merge |
| `/adr` | Architecture Decision Record |
| `/brainstorm` | Rapid solution exploration |
| `/research` | Autonomous research and recommendation |
| `/audit` | Read-only system mapping |
| `/retro` | Retrospective analysis |
| `/decide` | Record key decisions with reasoning |
| `/hotfix` | Emergency fix escalation |

---

## Architecture

```
your-project/
├── AGENTS.md                    # Global AI governance directives
├── CLAUDE.md                    # Claude Code integration entry
│
├── .agent/                      # Agent Intelligence Layer
│   ├── config.yaml              # Governance constants
│   ├── rules/                   # Engineering & security guardrails
│   ├── skills/                  # Skill metadata (auto-trigger defs)
│   └── workflows/               # Workflow definitions (35 workflows)
│
├── .agents/skills/              # Full skill implementations (17 skills)
│   ├── test-driven-development/
│   ├── systematic-debugging/
│   └── ...
│
├── .agentcortex/                # Runtime & State Layer
│   ├── bin/                     # Deploy & validation scripts
│   ├── context/                 # SSoT + work logs
│   ├── docs/                    # Philosophy, platform guides, examples
│   ├── metadata/                # Skill registry & cache index
│   ├── templates/               # Reusable ADR/spec/README templates
│   ├── tests/                   # Framework validation tests
│   └── tools/                   # Runtime tools (Python)
│
├── docs/                        # Project-level documentation
│   ├── specs/                   # Feature specifications
│   ├── adr/                     # Architecture Decision Records
│   └── architecture/            # Domain architecture docs
│
└── installers/                  # Cross-platform deploy wrappers
    ├── deploy_brain.sh          # Bash installer
    ├── deploy_brain.ps1         # PowerShell installer
    └── deploy_brain.cmd         # CMD installer
```

---

## Platform Compatibility

| Platform | Status | Integration |
|:---|:---|:---|
| **Claude Code** | Full support | `CLAUDE.md` auto-loads governance |
| **Google Antigravity** | Full support | Intent router + Antigravity runtime |
| **OpenAI Codex** | Full support | Platform guide + CLI delegation |
| **Cursor** | Compatible | Reads `AGENTS.md` as project rules |
| **GitHub Copilot** | Compatible | Follows guardrails via `AGENTS.md` |
| **Any LLM Agent** | Compatible | Model-agnostic governance language |

---

## Philosophy

Agentic OS is built on [10 non-negotiable principles](.agentcortex/docs/AGENT_PHILOSOPHY.md):

| # | Principle | Meaning |
|:---|:---|:---|
| 1 | AI Drives, Human Assists | AI follows phases autonomously; human confirms direction |
| 2 | Never Skip Phases | Sequential execution, not skip-to-end |
| 3 | Constitution Over Task | Guardrails override any request |
| 4 | No Evidence = No Completion | Claims without proof are rejected |
| 5 | Correctness First | Correct > performant > clever |
| 6 | Token Efficiency | Minimize cold-start cost, maximize context reuse |
| 7 | Cross-Model Compliance | Works with any AI model, no vendor lock-in |
| 8 | Actionable Documentation | Every doc must be directly usable |
| 9 | Scope Discipline | Only touch what was asked |
| 10 | Explainability | Every AI decision must be traceable |

---

## Documentation

| Document | Description |
|:---|:---|
| [Agent Philosophy](.agentcortex/docs/AGENT_PHILOSOPHY.md) | 10 core principles |
| [Model Selection Guide](docs/AGENT_MODEL_GUIDE.md) | Flash vs. Pro guidance |
| [Testing Protocol](.agentcortex/docs/TESTING_PROTOCOL.md) | Testing standards |
| [Project Examples](.agentcortex/docs/PROJECT_EXAMPLES.md) | Node.js & Python examples |
| [Token Governance](.agentcortex/docs/guides/token-governance.md) | Token optimization strategies |
| [Context Budget](.agentcortex/docs/guides/context-budget.md) | Context window management |
| [Migration Guide](.agentcortex/docs/guides/migration.md) | Upgrade to v1.1+ |
| [Codex Platform Guide](.agentcortex/docs/CODEX_PLATFORM_GUIDE.md) | Codex Web/App adaptation |
| [Claude Platform Guide](.agentcortex/docs/CLAUDE_PLATFORM_GUIDE.md) | Claude Code integration |
| [Nonlinear Scenarios](.agentcortex/docs/NONLINEAR_SCENARIOS.md) | Recovery from interrupted sessions |
| [Lifecycle Benchmark](docs/LIFECYCLE_BENCHMARK.md) | 6 real scenarios with token costs |
| [生命週期基準測試](docs/LIFECYCLE_BENCHMARK_zh-TW.md) | Token 消耗量測（繁體中文） |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing as a human or AI agent.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built for developers who demand discipline from their AI agents.</sub>
</p>
