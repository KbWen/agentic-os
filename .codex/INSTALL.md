# Agentic OS Installer (Codex)

Goal: Enable Codex (Web / App) to quickly load the workflow-first behavior of Agentic OS.

## Prerequisites

- **Git** (required)
- **Bash** (required — included with Git for Windows)
- **Python 3.9+** (recommended — enables full validation; not required for core functionality)

## 1) Installation (Run in target repo)

```bash
git clone https://github.com/KbWen/agentic-os.git
./agentic-os/installers/deploy_brain.sh .
```

> If you already have the framework deployed, run directly: `./installers/deploy_brain.sh .`

## 2) Verification

```bash
.agentcortex/bin/validate.sh

# Without Python (skip Python-dependent checks)
.agentcortex/bin/validate.sh --no-python
```

### Optional: local SSoT guard hook

> **Note**: Git hook templates are not deployed by default. If you need a
> pre-commit guard for SSoT writes, use `guard_context_write.py` directly
> or create your own `.githooks/pre-commit` script that checks for a
> recent guard receipt before allowing staged changes to `current_state.md`.
> This is advisory only — it does not block commits.

## 3) Codex Opening Commands (Recommended paste)

```text
Read and follow AGENTS.md first — it is the canonical governance for this repo.
Then run /bootstrap to classify your task and load context.
Use /brainstorm to clarify solutions, and /plan to generate an actionable plan.
DO NOT claim completion until /review and /test have passed.
```
