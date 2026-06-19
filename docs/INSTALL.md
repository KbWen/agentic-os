# Install & Usage

Full install, update, and first-task guidance for Agentic OS. The repo
[README](../README.md) keeps only the short version.

## Prerequisites

| Dependency | Required? | Purpose |
|:---|:---|:---|
| **Git** | Required | Clone and deploy the framework |
| **Bash** | Required | Run deploy & validate scripts (Git Bash from [Git for Windows](https://gitforwindows.org/) is enough on Windows) |
| **Python 3.9+** | Recommended | Enables full validation (metadata, encoding, command sync checks) |
| **SHA-256 tool** | Required for deploy | `sha256sum`, `shasum`, or `openssl` (pre-installed on most systems) |

> **No Python?** The framework deploys and works without Python. Validation runs in
> degraded mode — Python-dependent checks report `WARN` instead of `FAIL`.
> Pass `--no-python` to suppress warnings from a Git Bash or POSIX shell:
> `bash .agentcortex/bin/validate.sh --no-python`. On Windows PowerShell, prefer
> `powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1 -NoPython`.

## Install (first time)

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

> **AI-agent install:** If you're asking an AI assistant to install Agentic OS, point it to this file. The commands above are deterministic — no platform-specific heuristics required.

**Optional local pre-commit validation:** enable the bundled Git hook sample to run Agentic OS validation before each commit.

```bash
cp .githooks/pre-commit.guard-ssot.sample .githooks/pre-commit
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

On Windows, run the setup from PowerShell:

```powershell
Copy-Item .githooks\pre-commit.guard-ssot.sample .githooks\pre-commit
git config core.hooksPath .githooks
```

The hook runs `validate.ps1` from Git Bash on Windows when PowerShell is available, otherwise it runs `validate.sh`. Validator failures block the commit; guarded SSoT receipt warnings remain advisory.

<details>
<summary><b>Windows (PowerShell / CMD)</b></summary>

```powershell
# Clone Agentic OS (first time)
git clone https://github.com/KbWen/agentic-os.git

# Preview what will be deployed (no changes made)
powershell -ExecutionPolicy Bypass -File .\agentic-os\installers\deploy_brain.ps1 -DryRun C:\path\to\your-project

# Deploy into your project
powershell -ExecutionPolicy Bypass -File .\agentic-os\installers\deploy_brain.ps1 C:\path\to\your-project

# CMD alternative
.\agentic-os\installers\deploy_brain.cmd C:\path\to\your-project
```

Use the PowerShell entrypoint when possible. It resolves Git Bash directly and does not require a WSL distro.
Git Bash is still required on Windows for shell-based deploy and validation scripts; the PowerShell entrypoint simply locates and invokes it for you.

```powershell
# Already installed? Run from your project root to update:
powershell -ExecutionPolicy Bypass -File .\installers\deploy_brain.ps1 .

# Validation after install
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1

# Lightweight validation when Python is not installed
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1 -NoPython
```

</details>

<details>
<summary><b>Text-only usage (no scripts)</b></summary>

If you only want the governance templates (Markdown files) without running any tooling:

1. Copy the `.agent/`, `.agents/`, and `AGENTS.md` files into your project
2. Optionally copy `.agentcortex/context/` and `.agentcortex/templates/` for state management
3. No Python, Bash, or other tools are needed — all governance is plain Markdown

</details>

## Customizing without conflicts (fork or clone)

However you adopt Agentic OS — **fork** the repo, or **clone + `deploy_brain.sh`** into your project — the same rule keeps upgrades painless: **add your own files; never edit framework-owned files in place.** Put your customizations where the framework guarantees never to touch them, and they survive both `git pull upstream` (fork) and the next `deploy` (clone):

| You want to… | Put it here | Why it survives upgrades |
|---|---|---|
| Add project governance (narrow/disable a directive) | `AGENTS.override.md` (project root) or `~/.agentcortex/AGENTS.override.md` (personal) | Loaded present-only at session start; framework never ships these files. MAY narrow/disable directives but **cannot** relax delivery gates. |
| Add your own skills | `.agents/skills/custom-<name>/SKILL.md` (+ `.agent/skills/custom-<name>` metadata) | `custom-*` is a reserved namespace the framework never ships → zero collision, never overwritten. |
| Adjust skill activation (pin/exclude) | `.agentcortex/context/private/user-preferences.yaml` | Gitignored, personal, loaded by bootstrap. |

**What NOT to do:** editing a framework file in place (`AGENTS.md`, `.agent/rules/*`, `.agent/workflows/*`, a shipped skill body) causes merge conflicts on `git pull upstream` (fork) and is force-updated on the next `deploy` (clone). Framework **skills** are the one tolerant exception — if you edit one, `deploy` preserves your copy as a visible `<file>.acx-incoming` sidecar rather than silently overwriting it — but the cleaner pattern is always to copy it to a `custom-<name>` skill and edit that.

## Start working — pick your entry point

Always preface your first message with:

> "Read `AGENTS.md` and follow it. Do not claim completion until /review and /test pass."

Then add **one** of the following based on your situation:

**A. Brand-new project, multi-feature idea** — `/spec-intake` first

```text
This is a brand-new project. My initial idea is:
[1–2 paragraphs describing the product and its features]

Please run /spec-intake to decompose this into a feature inventory.
After I pick the first feature, run /bootstrap → /app-init to establish
the tech stack ADR, then /plan and /implement.
```

**B. Existing repository adopting Agentic OS** — `/audit` first

```text
This repo already has code; Agentic OS was just deployed.
Run /audit (read-only) to map the codebase, then /app-init to record
the tech stack ADR, then /spec-intake when I add features.
```

**C. Single concrete task on an established project** — `/bootstrap` directly

```text
/bootstrap
[describe the single task]
```

| Starting point | First command | Full chain |
|---|---|---|
| Brand-new project, multi-feature idea | `/spec-intake` | spec-intake → pick feature → bootstrap → app-init → plan → implement |
| Existing repo, adopting Agentic OS | `/audit` (read-only, zero risk) | audit → app-init → spec-intake → quick-win → feature |
| Single concrete task on an established project | `/bootstrap` | bootstrap → plan → implement → review → test → ship |

> **Why this matters**: a multi-feature raw idea routed straight to `/bootstrap` is classified as a single task, skipping the Feature Inventory and `_product-backlog.md` decomposition. The Intent Router auto-detects this in most cases, but explicit beats inferred.

Then the AI classifies your task and follows the required phases automatically:

```
You: "Add pagination to the user list API"

AI: [/bootstrap] → Classification: feature
    → Required: Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship
    → Loading skills: API Design, Test-Driven Development
```
