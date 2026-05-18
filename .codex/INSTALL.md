# Agentic OS Installer (Codex)

Goal: Enable Codex (Web / App) to quickly load the workflow-first behavior of Agentic OS.

## Prerequisites

- **Git for Windows** (required on Windows — use the [official installer](https://git-scm.com/download/win) which includes Git Bash; standalone Git without Git Bash will not work)
- **Git** (required on Linux/macOS)
- **Bash** (required on all platforms — included in Git for Windows; also available via WSL on Windows)
- **Python 3.9+** (recommended — enables full validation; not required for core functionality)

## 1) Installation (Run from your target project's root directory)

**Linux / macOS / Git Bash:**
```bash
git clone https://github.com/KbWen/agentic-os.git
./agentic-os/installers/deploy_brain.sh .
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/KbWen/agentic-os.git
powershell -ExecutionPolicy Bypass -File .\agentic-os\installers\deploy_brain.ps1 .
```

**Windows (CMD):**
```cmd
git clone https://github.com/KbWen/agentic-os.git
.\agentic-os\installers\deploy_brain.cmd .
```

> If you already have the framework deployed, update directly:
> - Bash: `./installers/deploy_brain.sh .`
> - Windows (PowerShell): `powershell -ExecutionPolicy Bypass -File .\installers\deploy_brain.ps1 .`
> - Windows (CMD): `.\installers\deploy_brain.cmd .`

## 2) Verification

**Linux / macOS / Git Bash:**
```bash
.agentcortex/bin/validate.sh

# Without Python (skip Python-dependent checks)
.agentcortex/bin/validate.sh --no-python
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1

# Without Python
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1 -NoPython
```

### Optional: local SSoT guard hook

> **Note**: Git hook templates are not deployed by default. If you need a
> pre-commit guard for SSoT writes, use `guard_context_write.py` directly
> or create your own `.githooks/pre-commit` script that checks for a
> recent guard receipt before allowing staged changes to `current_state.md`.
> This is advisory only — it does not block commits.

## 3) Opening Commands — Pick Your Entry Point

The right first command depends on your starting point. **Always start with this preamble**:

```text
Read and follow AGENTS.md first — it is the canonical governance for this repo.
DO NOT claim completion without the evidence required for the task's classification
(feature/hotfix: /review + /test required; quick-win/tiny-fix: diff + verification sufficient).
```

Then add ONE of the three openers below:

### A. Brand-new project, multi-feature idea

> Use when you have a product idea with several features and no code yet.

```text
This is a brand-new project. My initial idea is:
[1–2 paragraphs describing the product and its features]

Please run /spec-intake to decompose this into a feature inventory.
After I pick the first feature, run /bootstrap → /app-init to establish
the tech stack ADR, then /plan and /implement.
```

**Why /spec-intake first**: a multi-feature raw idea must be decomposed into
`docs/specs/_product-backlog.md` before any single feature is bootstrapped,
otherwise classification and Work Log scope will be wrong.

### B. Existing repository — adopting Agentic OS for the first time

> Use when the framework was just deployed into a repo that already has code.

```text
This repo already has code but Agentic OS was just deployed.
Please run /audit (read-only) to map the existing codebase,
then /app-init to record the tech stack ADR,
then /spec-intake when I'm ready to add features.
```

### C. Single, well-scoped task on an established project

> Use when the project already has an ADR and you have one concrete task.

```text
Please run /bootstrap to classify and start this task.
[Then describe the task — single feature, bug, or quick-win.]
```

### D. Continue multi-feature work from an existing backlog

> Use when one or more features have already shipped and you want to pick up the next item from the backlog.

```text
Please read docs/specs/_product-backlog.md and run /spec-intake §8a
to continue with the next pending feature.
```

**Why different from C**: `/bootstrap` on an established project will surface the backlog as a side-effect, but `/spec-intake §8a` is the explicit continuation path — it reads the backlog index, skips decomposition, and feeds the next feature directly into bootstrap. This prevents re-classifying already-decomposed features.

> **Not sure which one?** Default to A for raw ideas, C for concrete single tasks, D when you have a running backlog.
> The AI's Intent Router will also auto-detect multi-feature input and
> route to /spec-intake, but explicit beats inferred.
