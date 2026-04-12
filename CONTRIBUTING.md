# Contributing to Agentic OS

Thank you for your interest in **Agentic OS**! This project is designed as an "Agentic-First" ecosystem. Whether you are a human developer or an AI Agent, please follow these guidelines to maintain project integrity and token efficiency.

## 🤖 For AI Agents & Subagents

If you are an AI assisting in this repository:

1. **Read the SSoT**: Always start by reading `.agentcortex/context/current_state.md`.
2. **Read the Active Work Log**: For every non-`tiny-fix` task, also load `.agentcortex/context/work/<worklog-key>.md` before planning or shipping.
3. **Follow the Guardrails**: Strictly adhere to `.agent/rules/engineering_guardrails.md`.
4. **No Evidence, No Completion**: Do not claim a task is finished without providing verifiable test logs or terminal output.
5. **Token Governance**: Avoid reading large files unless necessary. Use targeted search tools (`rg`, `grep`, or platform equivalents) to locate specific code items.

## 👤 For Human Contributors

1. **Issue First**: Please open an issue using the "Agent-Driven Issue" template before making significant changes.
2. **Feature Branches**: Use descriptive `codex/<task-name>` branch names for framework work in this repo.
3. **PR Standards**: Every Pull Request should include a clear "Problem/Solution" summary and verification evidence.
4. **Language**: All internal documentation, rules, and commit messages must be in **English** for maximum cross-model compatibility.

## 🛠️ Development Workflow

1. **Initialize**: Use `/bootstrap` to set up your task context and freeze classification.
2. **Plan**: Use `/plan` to document your approach and get approval.
3. **Implement**: Use `/implement` for small, reversible changes within the approved scope.
4. **Review**: Use `/review` for logic, safety, and scope checks.
5. **Test**: Use `/test` and record executable verification evidence.
6. **Handoff**: Use `/handoff` for non-`tiny-fix` branches that require resumable context.
7. **Ship**: Use `/ship` to consolidate evidence, sync context, and merge or open the final PR.

Quick reference:

- `tiny-fix`: inline plan + execute with minimal evidence
- `quick-win`: `bootstrap → plan → implement → evidence → ship`
- `feature` / `architecture-change`: full phase flow including review, test, and handoff

## ⚖️ Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors, regardless of whether they are biological or silicon-based.

---
*Questions? Open an issue or refer to [README.md](README.md).*
