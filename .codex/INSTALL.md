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

To get a local warning when `.agentcortex/context/current_state.md` is staged without a recent guard receipt:

```bash
git config core.hooksPath .githooks
cp .githooks/pre-commit.guard-ssot.sample .githooks/pre-commit
chmod +x .githooks/pre-commit
```

This hook is advisory only. It does not block commits, but it makes direct SSoT edits visible during local review.

## 3) Codex Opening Commands (Recommended paste)

```text
Read and follow AGENTS.md first — it is the canonical governance for this repo.
Then run /bootstrap to classify your task and load context.
Use /brainstorm to clarify solutions, and /plan to generate an actionable plan.
DO NOT claim completion until /review and /test have passed.
```
