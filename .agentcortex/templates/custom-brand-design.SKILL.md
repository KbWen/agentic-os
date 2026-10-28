---
name: custom-brand-design
description: Apply approved project brand guidance and the selected screen design reference during planning, implementation, and review.
---

# Custom brand design

This is a project-specific example. Copy it to `.agents/skills/custom-brand-design/SKILL.md` and create the matching one-line framework metadata file `.agent/skills/custom-brand-design` if the project chooses to use it. It is not active merely because this template exists.

## Project references

- Read approved brand guidance from `docs/design/brand.md` when that file exists and is relevant.
- Read the selected task reference from `docs/design/<screen>.md`.
- Treat those files as project-owned design input. State which revision or export you could actually inspect; if unavailable, request a readable local export and identify the gap.
- Do not treat a URL as proof of access, inspection, or approval. Do not invent brand values or mark pending decisions approved.

## Plan

Map each UI-affecting plan step to a named screen or component in the selected design reference. Record the required `Tool`, `Link`, `Approved`, and `Coverage` fields in the active Work Log's `## Design Reference` block. The link must point to the actual artifact or readable export.

## Implement

Use only approved, implementation-ready detail from the selected reference: component structure, layout, spacing, typography, colors, assets, interactive states, and responsive behavior where specified. Surface missing detail or conflicting guidance for resolution through the existing workflow. This skill supplements `frontend-patterns`; it does not replace it.

## Review

Compare the implementation with the source material that was actually inspected. Record concrete evidence, deviations, and any owner decision in the review and Work Log. Never claim a visual comparison for inaccessible material or a state/viewport that was not checked.

## Boundaries

Follow the canonical Agentic OS workflows and rules. This example cannot approve a design, bypass a gate, or replace framework skill registration. Use it only in its declared phases: plan, implement, and review.
