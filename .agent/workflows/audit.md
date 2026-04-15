---
name: audit
description: Map existing repository state during migration or onboarding.
tasks:
  - audit
---

# /audit

> Purpose: Map an existing legacy repository to establish baseline context before transitioning to Agentic OS workflows.

## Environment Constraints

- **NO GATE**: This workflow bypasses all Gate Engine checks.
- **NO CODE MODIFICATION**: This workflow is read-only for codebase files.
- **REPORT ONLY**: The goal is to generate an analysis, not a plan or an implementation.
- **ROUTE FINDINGS**: Any design finding with lasting relevance MUST be routed to a canonical Domain Doc or spec via `routing_actions` — leaving it only in the audit snapshot is a governance defect.

## Workflow Execution Steps

1. **Discover Files**: Perform a broad scan of the directory structure (respecting `.gitignore`).
2. **Infer Architecture**: Analyze the imports, configuration files (e.g., `package.json`, `requirements.txt`), and main entry points.
3. **Assess Documentation**: Check for existing READMEs, inline comments, or legacy specs.
4. **Assess Test Coverage**: Locate test directories and gauge the approximate level of testing.

## Expected Output Format

Apply `AGENTS.md §Phase Output Compression`. Chat response is the compact block below; full multi-section detail (system_map breakdown, per-module dependency graph, full file inventory) is written to an audit report file at `docs/reviews/<date>-audit.md` and referenced by path.

```
Files: <count> files across <N> top-level dirs
System: <primary stack + key modules, 1 line>
Entry: <entry-point command or "(see audit report)">
Tests: <coverage summary, 1 line>
Missing docs: <top 3 gaps>
Next: <slash-command recommendation>
Report: docs/reviews/<date>-audit.md
```

1. **`routing_actions`** (AC-29): For each significant finding that constitutes a design decision, constraint, or architectural gap, output a structured routing action block to the audit report file (MANDATORY — omit only if no actionable findings exist). In chat, report only `routing_actions: <N> pending` — do NOT paste the full blocks unless the user asks.
   ```yaml
   routing_actions:
     - finding: "<1-line summary of the finding>"
       target_doc: "docs/architecture/<domain>.md"
       status: pending
       owner: "<session-id or 'unassigned'>"
   ```
   - Each `target_doc` MUST point to a canonical Domain Doc or spec — never to the review snapshot itself.
   - `status` is initially `pending`. It transitions to `merged` when the finding is incorporated into the target doc, or `rejected` with justification.
   - Review snapshots (`docs/reviews/<date>-<scope>.md`) are **temporal records** — their conclusions MUST be routed back to the canonical Domain Doc or spec via `routing_actions`. Review snapshots MUST NOT be treated as design authority (AC-31).
