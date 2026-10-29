# Bringing your own design references

Use this guide when a project already has screens or brand direction in Stitch, Figma, Pencil, Claude Design, or another design source. These names identify possible producers; they do not imply that this repository can connect to, authenticate with, or inspect those tools.

Most projects do not need a knowledge base. Design onboarding works with a readable design link or a local export and the existing workflow. For optional knowledge-base setup, see [Connecting an external knowledge base](connecting-a-knowledge-base.md).

## What the existing workflow expects

The design-first rules already live in [engineering guardrails §4.4](../../../.agent/rules/engineering_guardrails.md) and the [plan workflow](../../../.agent/workflows/plan.md). Plans for UI work identify a design artifact and map each UI-affecting step to its screen or component. The Work Log records a `## Design Reference` block with `Tool`, `Link`, `Approved`, and `Coverage` fields.

Before UI rendering work, the [implementation workflow](../../../.agent/workflows/implement.md) checks that the reference exists, is approved, and has implementation-ready detail. The [review workflow](../../../.agent/workflows/review.md) compares the result with the reference and records evidence. The normal sequence is:

1. `/plan`: identify the design source and map planned UI work to screens/components.
2. Design owner approves the reference; export or summarize enough detail to implement it.
3. `/implement`: follow the approved, implementation-ready reference.
4. `/review`: compare the implementation with the reference and record findings.

This guide does not add a gate or change those workflow rules. The current design check is agent-enforced; there is no machine visual signoff. Machine enforcement of design-reference presence is a separate policy decision (#122), not visual validation and not part of this guide. Existing prototype and non-UI exemptions are described in the canonical guardrail; consult it rather than treating every change as a design task.

## Make the reference inspectable

A URL alone does not prove that an agent can open or inspect the design. Access may depend on an account, permissions, a browser session, or a tool unavailable in the current environment. Do not claim to have inspected, approved, or verified a reference based only on its link.

When the source cannot be read in the current environment, ask the design owner for a readable local export: for example, screenshots, a written screen specification, exported HTML, or relevant code. Record the source tool or producer, source revision/date, the local export path, and exactly which material was inspected. State what remains unavailable or unclear. A local export is a record of source material, not proof that the original source was accessed.

Prefer the smallest export that lets a reviewer understand the in-scope screen. A screenshot can show appearance but may omit interaction, responsive behavior, and token names. A written specification can capture those details if it identifies the corresponding screen and source revision. HTML or code can reveal structure and styles, but may not show every state or viewport. Note these limits instead of filling them with assumptions.

Before accepting an export, check that it opens locally, names the screen or flow, and corresponds to the revision the design owner intends. If multiple exports conflict, record the conflict and ask which is current. Do not silently combine values from different revisions.

For a durable handoff, copy [the design reference template](../../templates/design-reference.md) to `docs/design/<screen>.md`. Replace its prompts with project-specific details. Keep source and revision information, approval state, coverage mapping, implementation details, and honest review evidence together. Make `Link:` identify the actual design artifact or readable local export, not an unfilled template or circular pointer with no design content.

Without a design tool, the completed, committed document can itself be the design artifact: add a Markdown/ASCII wireframe, component structure, states, and implementation details to `docs/design/account-settings.md`, then use `Tool: other` and `Link: docs/design/account-settings.md`. Keep `Approved: pending` until the design owner approves that revision. A filled cover sheet that only points back to itself is not a wireframe or screen specification.

The template's `## Design Reference` block uses the fields required by `/plan`: `Tool`, `Link`, `Approved`, and `Coverage`. Copy and summarize that block into the active Work Log when planning. The document is a supporting handoff; it does not itself update the Work Log or satisfy a workflow check.

Use a stable path relative to the repository for committed exports. For private or licensed source material, record a permitted reference and a sanitized summary rather than committing files the project is not allowed to distribute. The `Link:` should still identify a real source or export the intended reviewer can resolve; if it is unavailable to that reviewer, say so and provide a readable substitute.

`Approved: pending` is the template default. Change it to `yes` only after the design owner has approved the referenced revision. If the approval state is unknown, leave it pending and ask. Record who approved and when in the source/inspection notes or approval evidence so later readers can distinguish a current decision from an old export.

## Record implementation-ready detail

Capture enough information for another person to implement and review the screen without guessing. Include the relevant items that the source actually specifies:

- Screen and component names, hierarchy, layout, and mapping to plan steps.
- Spacing, dimensions, typography, color values, and other design tokens.
- Required assets and their readable paths or links.
- Interactive states such as hover, focus, disabled, loading, error, and empty.
- Responsive behavior and supported breakpoints or viewport examples.
- Known gaps, decisions still pending, and the owner who can resolve them.

Do not invent missing values or label a direction approved when approval is pending. Ask the design owner to resolve material gaps before UI implementation, as the existing implementation workflow requires.

If a source uses tokens by name, include the token names and the project-owned definition or source location. If it provides only rendered values, record those values and the context in which they apply. Keep any new project token proposal visibly separate from approved design input.

For interactive behavior, distinguish states shown in the source from states inferred from product requirements. The workflow's comparison can only verify what the reference specifies; note unspecified behavior as an open question instead of claiming fidelity for it.

## Add optional project brand guidance

If the project needs reusable brand guidance, keep it in a project-owned file such as `docs/design/brand.md`. Record only approved, sourced direction there; identify unresolved decisions as unresolved. Select relevant brand guidance and the screen reference in `docs/design/<screen>.md` for each task.

The [custom skill example](../../templates/custom-brand-design.SKILL.md) is an inert starting point. To try it, copy the entire file, including its opening YAML frontmatter, to `.agents/skills/custom-brand-design/SKILL.md` and create the matching one-line metadata file `.agent/skills/custom-brand-design`. The body uses `docs/design/brand.md` and `docs/design/<screen>.md` as example destinations. Adapt those references to files your project actually maintains. It supplements project conventions; it does not replace the framework's `frontend-patterns` skill.

Native skill discovery and Agentic OS framework registration are separate mechanisms. Copying files does not guarantee discovery or activation in every agent/tool. The framework example below declares the custom skill to its own bootstrap path; use the native format expected by the specific agent when applicable. Do not assume all tools discover skills the same way.

The skill example has proper YAML frontmatter at byte one, with `name: custom-brand-design` matching the copy destination and a concise `description`. Its metadata stub is one line: `custom-brand-design: phases=[plan, implement, review] cost_risk=low load_policy=on-match`. Keep the body focused on brand references and implementation/review guidance.

Edit the copied skill to match the project vocabulary and file locations. Leave the example template in the framework templates directory untouched as a reference. Do not put credentials, private URLs requiring embedded secrets, or personal machine paths in a committed skill body.

## Optional framework activation (no KB)

The following is a minimal, copyable example for `.agentcortex/context/private/downstream-capabilities.yaml`. It declares no `knowledge_sources`; no knowledge base is required. The strict validator accepts only a supported subset, so preserve this plain YAML shape and validate the resulting file.

```yaml
skills:
  - id: custom-brand-design
    load_policy: on-match
    phase_scope: [plan, implement, review]
```

This declaration makes the custom ID available to the framework's skill validation and phase-scoped loading rules; it is not a universal native discovery mechanism. Request it explicitly in a relevant phase, for example: “During `/plan`, apply the `custom-brand-design` skill to the approved brand and screen references.” A skill cannot bypass or relax a workflow gate.

To include the declared skill in Recommended Skills, optionally add this personal preference to `.agentcortex/context/private/user-preferences.yaml`:

```yaml
skill_preferences:
  pinned: [custom-brand-design]
```

Merge the `skills` entry or preference into an existing file; do not replace other capabilities or preferences. These private files are gitignored and are not shared automatically. Keep sanitized, project-owned instructions and design references in the repository for teammates.

From the repository root, validate the private capabilities file with the shipped `validate_downstream_capabilities.py` script:

```powershell
python .agentcortex/tools/validate_downstream_capabilities.py .agentcortex/context/private/downstream-capabilities.yaml
```

An `OK` result means the declaration is syntactically supported and gate-safe. The script does not verify that a design link is accessible or that its content is accurate. Do not add credentials or authentication claims to these examples.

The framework capability file is optional and personal. If the file is absent, there is no custom framework skill declaration and no knowledge base is consulted. If it already contains other entries, preserve them and add only the desired `skills` item at the correct top-level location. Avoid YAML syntax the strict parser does not support, such as inline comments or flow mappings.

## Ownership and upgrades

| Material | Owner and location | Sharing and upgrade behavior |
| --- | --- | --- |
| Design references and approved brand guidance | Project: `docs/design/` | Commit readable, sanitized source notes and exports intended for teammates. |
| Custom native skill | Project: `.agents/skills/custom-brand-design/SKILL.md` and `.agent/skills/custom-brand-design` | Project-owned example; use the expected native format for each agent. |
| Framework activation and preferences | Personal: `.agentcortex/context/private/downstream-capabilities.yaml` and `user-preferences.yaml` | Gitignored and local; merge into existing files. |
| Framework workflows and rules | Agentic OS core: `.agent/workflows/` and `.agent/rules/` | Do not edit locally to customize a project; link and follow canonical rules. |

The deploy process retains `custom-*` downstream material according to its preservation policy. Check [document governance and the override layer](doc-governance.md) before considering framework documentation or overrides. Do not add a `design_tool` capability key: the rejected escape remains rejected. Neither overrides nor capability configuration can bypass framework gates.

## Walkthrough: prepare one screen

1. Ask which screen or flow is in scope and who owns its design approval.
2. Locate its current source in Stitch, Figma, Pencil, Claude Design, or another producer. Note the source name and revision/date.
3. Check whether the source is readable in the current agent environment. If not, ask for a local export that can be read; do not infer approval from the URL.
4. Copy `.agentcortex/templates/design-reference.md` to `docs/design/account-settings.md` (replace the example name with the real screen).
5. Fill in the actual artifact link or export path, source revision, inspected material, approval status, plan-step mapping, tokens, assets, states, and responsive behavior. Mark unknowns and pending decisions honestly.
6. In `/plan`, add a `Design:` entry and copy/summarize the template's `## Design Reference` block into the active Work Log. Ensure every planned UI step maps to a screen or component.
7. Have the design owner confirm approval. If implementation-ready details are missing, request an updated export or clarification before UI rendering work.
8. Implement against the approved reference. In `/review`, compare the actual UI and record evidence for layout, spacing, typography, color, states, and responsive behavior that the design specifies.
9. If the project benefits from reusable brand notes, add approved guidance to `docs/design/brand.md`. Only then adapt and optionally activate the custom skill example.
10. For local framework activation, merge the sample `skills` entry into the private capabilities file and run the shipped validator. Keep private config local; share project-owned guidance through reviewed project files.

## Common handoff problems

- **The source link opens only for its author:** ask for a readable export and record the inaccessible source as context, not as inspected evidence.
- **The export has no revision:** ask the owner which snapshot is current and add a date or other stable identifier before planning against it.
- **Approval is not clear:** keep `Approved: pending`; ask the owner to confirm the specific revision.
- **A plan step has no screen mapping:** update coverage so every UI-affecting step points to a screen/component, or correct the plan scope.
- **The export omits implementation details:** list the missing values and request a refined handoff before UI rendering work.
- **The framework skill is not picked up:** confirm the copy destination, native format, metadata file, private capability declaration, and phase scope. Discovery differs by agent/tool, so ask for explicit use in the relevant phase when appropriate.
- **The capability validator rejects the file:** use the supported YAML subset and merge carefully; do not weaken or bypass validation.

Keep the handoff focused on what the next person needs to implement and compare. A concise, accurate record of limitations is more useful than a complete-looking template filled with guesses.

## Keep references current

When the design changes during implementation, identify the new revision and ask whether it supersedes the approved one. Update the project reference and Work Log to point to the same revision before continuing affected UI work. Preserve enough history to explain review decisions, but avoid leaving two files that both appear to be the current source of truth.

After review, keep the evidence tied to the implementation revision and design material actually compared. If the source changes later, do not rewrite old review evidence as though that newer version had been checked. Add a new comparison record for the new implementation/design pair.

When a screen is retired, move or remove its project-owned handoff according to the project's normal documentation policy. Do not change core framework workflows to accommodate one project's design storage. If the framework's canonical rules change, follow the updated source documents linked above.

The handoff should let a teammate answer three questions quickly: which design revision applies, what details are approved and inspectable, and what the reviewer actually compared. If any answer is missing, record that gap and resolve it through the existing workflow before claiming completion.

## Related references

- [Plan workflow and Design Gate](../../../.agent/workflows/plan.md)
- [Implementation workflow and Design Approval Check](../../../.agent/workflows/implement.md)
- [Review workflow and Design Compliance Check](../../../.agent/workflows/review.md)
- [Design-First Rule](../../../.agent/rules/engineering_guardrails.md)
- [Optional knowledge-base setup](connecting-a-knowledge-base.md)
- [Override layer and document governance](doc-governance.md)
