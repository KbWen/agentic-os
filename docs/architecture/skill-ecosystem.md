---
status: living
domain: skill-ecosystem
created: 2026-04-05
last_updated: 2026-04-25
lifecycle:
  owner: "/govern-docs"
  review_cadence: on-event
  review_trigger: "When a new skill is added/retired, OR skill_conflict_matrix.md gains/removes entries, OR an ADR amends skill activation policy"
  supersedes: none
  superseded_by: none
---

# Skill Ecosystem — Layer 1 Synthesis

> This is the current strategic direction for Agentic OS skill evolution.
> Decision history is in `docs/architecture/skill-ecosystem.log.md` (L2 — append-only).

## Current Direction

Agentic OS should evolve from a repo that merely ships built-in skills into a **skill platform** that can safely absorb:

- first-party skills maintained by the core project
- third-party skills installed from external repositories or curated indexes
- user-pinned skill variants that continue to change over time

The platform goal is **safe extensibility without context explosion**. Skills are not treated as loose prompt files; they are treated as **versioned, policy-governed, capability-bounded packages**.

## Relationship to Product Construction Track

The skill-ecosystem direction is one half of a broader platform strategy.

- `docs/architecture/skill-ecosystem.md` defines the **tooling/control plane**: what skills are, how they are resolved, what they can do, and how they are distributed safely.
- `docs/architecture/product-construction.md` defines the **product authority/quality plane**: what the agent should build, how quality is described, and how delivery is verified across UI, API, security, and interactive product work.

Both tracks are required if Agentic OS is meant to help agents build complete products rather than only invoke isolated tools correctly.

## Strategic Principles

- **Package, not prompt**: every skill must become an installable unit with explicit metadata, versioning, and lifecycle state.
- **Control plane separated from runtime**: registry, trust, compatibility, rollout, and deprecation rules live outside the execution runtime.
- **Immutable content, mutable references**: executions should resolve to a pinned snapshot, not "whatever latest means today".
- **Least privilege by default**: third-party or user-installed skills only receive explicitly granted capabilities.
- **Boundary enforcement over behavior micromanagement**: runtime controls should enforce tool, path, network, budget, and version boundaries rather than trying to govern model reasoning quality.
- **Intent-first discovery**: users should discover skills by task intent and recommended outcomes, not by memorizing skill names.
- **Curated loading**: a session should load one primary skill and only a few helpers; broad prompt stacking is not a sustainable default.
- **Low-friction hot path**: heavier checks should concentrate at install, upgrade, and ship boundaries, while execution-time enforcement stays lightweight and cheap.

## Platform Shape

### 1. Skill Package Layer

Every skill should expose machine-readable metadata, including:

- stable `id` and human-friendly `name`
- semantic `version`
- engine and API compatibility ranges
- dependencies and optional companion skills
- required capabilities and declared outputs
- provenance, signature, and trust tier
- deprecation and replacement hints

### 2. Registry / Resolution Layer

The registry should own:

- discovery and indexing
- version resolution
- dependency graph validation
- compatibility checks
- trust evaluation
- deprecation, staged rollout, and rollback metadata

Runtime execution should consume a **resolved snapshot** or lockfile result, not query live registry state as the execution truth.

### 3. Runtime / Capability Layer

Skill execution should be sandboxed by:

- timeout, step budget, and tool budget
- file and network scope restrictions
- explicit capability grants such as `read_repo`, `write_docs`, or `invoke_search`
- trust-tier-aware defaults, where unverified skills start in the most restricted mode

Runtime enforcement is important, but its job is narrow:

- enforce capability boundaries
- bind execution to a resolved snapshot or lockfile result
- isolate untrusted skills
- keep execution cost bounded

Runtime enforcement is **not** the primary mechanism for:

- judging whether the model understood the task correctly
- guaranteeing workflow compliance by prompt discipline alone
- replacing spec, review, or evidence-based validation

The design target is a **lightweight runtime hot path**. Heavy policy checks should happen primarily during install, upgrade, rollout, and ship flows.

### 4. Discovery / UX Layer

The product should reduce user confusion through:

- task-intent-based recommendations
- visible skill cards with use case, non-goals, conflicts, and update summary
- conflict guidance that explains which skill should lead
- starter packs and safe bundles for validated combinations

## Roadmap Priorities

Execution priority should favor **foundations before breadth**:

- package contract before registry automation
- registry snapshot before capability expansion
- lightweight boundary enforcement before richer orchestration
- discovery quality before marketplace breadth
- developer-flow improvements before advanced intelligence layers

### Near Term

- standardize a minimal skill manifest schema
- add resolved snapshot or lockfile support
- define capability tokens and default sandbox boundaries
- introduce trust tiers for official, partner, community, and unverified skills

### Mid Term

- build compatibility resolution and downgrade/rollback flows
- add discovery ranking based on task fit, health, and compatibility
- add conflict rules for primary vs. helper skill orchestration
- keep runtime enforcement focused on cheap boundary checks instead of expanding into broad execution micromanagement

### Longer Term

- support curated starter packs and workspace-level sharing
- add staged rollout, canary, and deprecation windows for skill updates
- open a broader marketplace only after trust, rollback, and compatibility controls are reliable

## Non-Goals

- Do not treat download count or popularity as the main trust signal.
- Do not auto-load many skills into the same session by default.
- Do not allow third-party skills to inherit broad tool access implicitly.
- Do not rely on mutable "latest" references for reproducible execution.
- Do not use runtime enforcement as a substitute for spec quality, orchestration quality, or review discipline.

## Workflow Implication

Future feature work in the skill area should align to this sequence:

1. metadata and package contract
2. registry and snapshot resolution
3. runtime capability sandbox
4. discovery, ranking, and conflict management
5. ecosystem distribution and marketplace expansion
