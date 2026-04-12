---
name: superpowers-playbook
description: Comprehensive playbook for Antigravity (New Feature, Small Fix, Medium Feature, Hotfix, Handoff).
tasks:
  - bootstrap
  - classify
  - spec
  - plan
  - implement
  - review
  - test
  - handoff
---

# Superpowers Playbook Workflow

## Applicable Scenarios

- New Feature
- Small Fix
- Medium Feature
- Emergency Hotfix
- Cross-Agent / Human Handoff

## Execution Sequence

1. `/bootstrap`: Define Goal / Paths / Constraints / AC / Non-goals.
2. Classification: Assess risk/impact (Docs / Small Fix / Medium Feature / New Feature / Hotfix).
3. `/spec` (REQUIRED for `feature` / `architecture-change`): Solidify AC, boundaries, non-goals.
4. `/plan`: List target files, verification method, risks, rollback.
5. `/implement`: Execute incrementally. Unauthorized scope expansion PROHIBITED.
6. `/review`: Check side-effects, compatibility, security.
7. `/test`: Run reproducible commands and retain results.
8. `/handoff`: Output Done / In Progress / Blockers / Next / Risks.

## Reference Paths

- Task workflow cards: `.agent/workflows/*.md`
