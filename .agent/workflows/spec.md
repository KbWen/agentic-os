---
description: Workflow for spec
---
# /spec

Convert requirements into verifiable specs and verify consistency with existing `docs/specs/`.

Output Format:

1. Goal
2. Acceptance Criteria (AC)
3. Non-goals
4. Constraints
5. API / Data Contract (Optional)
6. State Metadata: Output YAML frontmatter with `status: draft`. Transitions to `status: frozen` when user approves.
   - **Primary Domain** (AC-12, REQUIRED for feature/architecture-change): Include `primary_domain: <domain-noun>` in frontmatter. This routes knowledge consolidation to the correct Domain Doc at `/ship`.
   - **Secondary Domains** (AC-12, optional): Include `secondary_domains: [<domain>, ...]` if the spec touches multiple domains. Secondary domains receive cross-reference pointers only — no full content consolidation.
7. File Relationship: Declare if this spec EXTENDS, REPLACES, or is INDEPENDENT from any existing `docs/specs/*.md` file.
8. **Domain Decisions** (AC-9, MANDATORY for feature/architecture-change): Include a `## Domain Decisions` section.
   - This is the ONLY section `/ship` reads for knowledge consolidation into Domain Docs.
   - Each entry MUST use one of: `[DECISION]`, `[TRADEOFF]`, or `[CONSTRAINT]`.
   - Hard cap: **10 entries maximum** (AC-11). If you have more than 10, ask the user to review and prune before freezing. Exceeding 10 requires user acknowledgment.
   - Format example:
     ```
     ## Domain Decisions
     - [DECISION] <why this architectural choice was made over alternatives>
     - [TRADEOFF] <what was traded off and why it is acceptable>
     - [CONSTRAINT] <a rule that all future work in this domain must respect>
     ```
   - `tiny-fix` and `quick-win` are EXEMPT from requiring this section.

Checkpoints:

- AC MUST be objectively verifiable.
- MUST check for conflicting legacy specs.
- Non-goals MUST prevent scope creep.
- MUST NOT modify any existing spec with `status: frozen` frontmatter (Ref: §4.2 Spec Freezing).
- For `feature` / `architecture-change`: `primary_domain` frontmatter field MUST be set before freezing.
- For `feature` / `architecture-change`: `## Domain Decisions` section MUST be present with at least one tagged entry before freezing.

## Output Location (Hard Rule)

- Write spec to: `docs/specs/<feature-name>.md`.
- Update `current_state.md` Spec Index with: `[<module>] docs/specs/<feature-name>.md [Draft]`.
- This file is the ONLY artifact that satisfies the Spec Gate in `/plan`.

> Note: Antigravity's `implementation_plan.md` (in brain/) is a per-conversation ephemeral artifact. It does NOT replace `docs/specs/<feature>.md` as the persistent specification SSoT.
