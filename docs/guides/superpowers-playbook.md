---
title: Superpowers Playbook
type: guide
status: living
---

# Superpowers Playbook

Quick-reference for the full development lifecycle using Agentic OS. Applicable to any task classification.

## Execution Sequence

1. `/bootstrap` — Define goal, constraints, AC, non-goals. Classification is locked here.
2. `/spec` — Required for `feature` / `architecture-change`. Solidify AC, boundaries, data contracts.
3. `/plan` — Target files, verification method, risks, rollback plan.
4. `/implement` — Execute incrementally. Unauthorized scope expansion PROHIBITED.
5. `/review` — Side-effects, compatibility, security risks.
6. `/test` — Reproducible commands, retain results.
7. `/handoff` — Done / In Progress / Blockers / Next / Risks. Required for `feature` and `architecture-change`.
8. `/ship` — Final gate, SSoT update, branch cleanup.

## Classification → Phase Scope

| Classification | Required Phases |
|---|---|
| `tiny-fix` | direct execute + minimal evidence |
| `quick-win` | implement → ship |
| `hotfix` | bootstrap → implement → ship |
| `feature` | bootstrap → spec → plan → implement → review → test → handoff → ship |
| `architecture-change` | bootstrap → spec → plan → implement → review → test → handoff → ship |

## Reference

- Workflow files: `.agent/workflows/*.md`
- Governance rules: `AGENTS.md`
