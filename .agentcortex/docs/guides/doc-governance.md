---
name: Document Lifecycle Governance
description: Taxonomy, naming axiom, and creation gate for governance documents
status: living
authority: extracted from AGENTS.md (2026-05-07) to keep AGENTS.md within token budget
---

# Document Lifecycle Governance

> **Realizes** ADR-002 / `docs/specs/lock-unification.md` AC-24 & AC-25. This guide is the
> canonical "Document Lifecycle Governance" home — extracted from `AGENTS.md` on 2026-05-07
> (token-budget consolidation). The **Document Taxonomy** below is the doc-ownership matrix
> that AC-25 planned under the filename `governance-doc-lifecycle-matrix.md`; that file was
> never created — this guide superseded it. AC-25's "3 ownership gaps marked as Spec Seeds"
> were superseded by the doc-lifecycle backlog (#1, #3, #7, #11, #13, #67).

## Document Taxonomy

| Type | Path | Status | Owner Workflow |
|---|---|---|---|
| Domain Doc (L1 Synthesis) | `docs/architecture/<domain>.md` | `living` | `/govern-docs` |
| Domain Doc (L2 Decision Log) | `docs/architecture/<domain>.log.md` | `living` | `/ship` |
| Feature Spec | `docs/specs/<feature>.md` | `draft→frozen→shipped` | `/spec`, `/ship` |
| ADR | `docs/adr/ADR-NNN-<name>.md` | `accepted` | `/adr` |
| Product Backlog | `docs/specs/_product-backlog.md` | `living` | `/spec-intake` |
| Guide | `docs/guides/<topic>.md` | `living` | varies |

## Naming Axiom

**One topic, one canonical file.** Before creating any new `.md` file in `docs/`, AI MUST verify no existing file covers the same domain (`ls docs/<subdir>/`). If a canonical file exists, write a pointer, not a copy. Duplicating content across documents is a governance violation.

## Document Creation Gate

Before creating any new governance document, AI MUST answer three questions:

1. Does this topic already have a canonical home? (check `docs/` structure)
2. Can a reader 6 months from now guess this file's location from its name alone?
3. Can this be a section in an existing file rather than a new standalone file?

If the answer to #3 is yes → add a section, do not create a new file.

## Override Layer (`AGENTS.override.md`) — active

Per-machine or per-fork overrides MUST live in a sibling override file rather than mutating canonical governance docs. This mirrors the Codex `AGENTS.override.md` precedence pattern (<https://developers.openai.com/codex/guides/agents-md>).

**Precedence chain** (later layers override earlier):

1. `AGENTS.md` (this file — canonical, committed)
2. Project root `AGENTS.override.md` (committed only if the project intends the override to apply to all collaborators; otherwise gitignored)
3. `~/.agentcortex/AGENTS.override.md` (per-user, never committed)

**Rules**:

- Override files MAY refine, narrow, or disable specific directives. They MUST NOT relax the gate sequence in `## Delivery Gates` or the No-Bypass Rule in `## Core Directives` — those are framework invariants.
- Each override directive MUST cite the section it overrides: `> Overrides: AGENTS.md §<section> — <reason>`.
- Agents MUST read override files at session start when present, in the precedence order above. Missing override files are not an error (capability-by-presence — absence costs zero reads).

**Status**: active (Ref: ADR-004). Runtime-wired via `.agent/workflows/bootstrap.md §1a "Load Override Layer"`, which loads present override files after the SSoT read and before Work Log setup, and records the result in the Work Log `## Session Info`.

**Implementation Contract**:

- Bootstrap §1a MUST check the project-root and per-user override paths at session start (present-only; absence is not an error).
- Each override directive MUST cite `> Overrides: AGENTS.md §<section> — <reason>`; an uncited directive is loaded but warned.
- Directives citing `## Delivery Gates`, `## Core Directives`, or the No-Bypass Rule are framework invariants: bootstrap warns, records `rejected` in the Work Log `## Drift Log`, and does NOT apply them (warn-only — it does not hard-block, because a pure-text override cannot be machine-proven to relax vs legitimately narrow a gate).
- Loaded override filenames + source are recorded in the Work Log `## Session Info` for audit.
- Enforcement is **structural**: `validate.sh`/`validate.ps1` assert that `bootstrap.md` still ships the §1a override-load step. Per-agent compliance ("did this agent actually read it") is honor-system, like the Sentinel — not falsely claimed as test-enforced.
- Cross-platform: the load logic is platform-agnostic (mirrors the Codex `AGENTS.override.md` convention); `.antigravity/rules.md` and `codex/rules/*` remain orthogonal platform-hardening files, not override layers.
