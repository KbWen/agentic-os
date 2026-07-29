---
status: shipped
title: "Skill Runtime Discovery Modernization"
created: 2026-07-28
primary_domain: skill-ecosystem
secondary_domains: [tooling, testing, adoption]
approval_basis: "User delegated end-to-end scope and implementation decisions on 2026-07-28 after requiring preservation of the existing architecture and multi-platform behavior."
---

# Skill Runtime Discovery Modernization

## Goal

Restore standards-compatible native discovery for all 14 first-party Skills, prevent `/app-init` from recreating non-discoverable scaffold Skills, and make the runtime simulation path exercise the canonical resolver while preserving Agentic OS routing, downstream customization, and cross-platform deployment behavior.

## Acceptance Criteria

- AC-1: All 14 `.agents/skills/<id>/SKILL.md` files contain valid YAML frontmatter as their first bytes, with non-empty `name` and `description`, and `name` equal to the directory ID. The five current scaffold Skills (`api-design`, `auth-security`, `database-design`, `doc-lookup`, and `frontend-patterns`) pass the current OpenAI `skill-creator` validator.
- AC-2: Scaffold/generated HTML comments remain after the closing frontmatter fence so existing `/app-init` scaffold detection and downstream customization semantics continue to work.
- AC-3: `.agent/workflows/app-init.md` defines a frontmatter-first minimum Skill structure and requires generated Skill descriptions to state both capability and activation context. A newly generated scaffold following the documented contract passes the same compatibility validator.
- AC-4: `.agentcortex/tools/check_skill_provenance.py` fails closed when any first-party `SKILL.md` lacks frontmatter, a name, or a description, including files marked as scaffold. Its source-repository provenance policy remains unchanged.
- AC-5: Focused provenance tests cover all-14 repository inventory, missing frontmatter, unclosed frontmatter, name mismatch, empty/missing description, BOM, and quoted scalars without retaining a scaffold exemption.
- AC-6: `.agentcortex/tools/resolve_runtime_contract.py` is a thin CLI adapter over `trigger_runtime_core.resolve_runtime_contract`; CLI inputs cover manual Skills, scope signals, failure signals, and optional Work Log context. Hotfix and manual-activation results match the canonical resolver.
- AC-7: Deterministic activation simulations cover direct/manual activation, indirect scope activation, negative/near-neighbor exclusion, ambiguous/no-signal behavior, isolation, and multi-Skill coexistence on `claude`, `codex`, and `antigravity` platform values. These simulations are explicitly labeled resolver tests, not proof of native host discovery or model-output effectiveness.
- AC-8: Clean-install simulation verifies 14 canonical Skill directories, 14 flat stubs, 14 OpenAI metadata mirrors, and 14 valid canonical frontmatters. Upgrade simulation verifies that an unmodified scaffold receives the compatible source update while a customized scaffold remains byte-preserved and receives a compatible `.acx-incoming` sidecar.
- AC-9: Windows PowerShell deployment and focused tests pass locally. Bash/POSIX behavior is covered by existing Ubuntu CI wiring and focused static/fixture tests; macOS remains explicitly unverified unless a macOS run is obtained.
- AC-10: Existing trigger registry entries, compact-index behavior, `.agent/skills` stubs, `agentcortex:` mirror metadata, deployment tiering, custom Skill preservation, workflow order, and Skill IDs remain unchanged except where AC-6 removes duplicate resolver logic.
- AC-11: Documentation touched by this work describes `.agents/skills/<id>/SKILL.md` as the canonical Skill body and `.agent/skills/<id>` as the compact metadata stub.

## Non-goals

- No migration of the 14 `agents/openai.yaml` files to the newer optional `interface` / `policy` / `dependencies` shape.
- No Skill deletion, consolidation, broad content rewrite, or token optimization before paired effectiveness evidence exists.
- No plugin packaging or second installation source of truth.
- No Claude `.claude/skills` mirror, Codex agent TOML deployment fix, or claims of native-host parity without real host smoke tests.
- No full LLM-judged Skill effectiveness harness; backlog #79 remains the owner of paired model-output evaluation after its dependencies are resolved or re-scoped.
- No change to ADR-005 preservation semantics: customized downstream scaffold files are never overwritten merely to add frontmatter.

## Constraints

- Preserve current scaffold comments because `/app-init` uses them to distinguish generic from customized content.
- Preserve the `agentcortex:` block and current flat-stub synchronization until a separately specified metadata migration proves compatibility.
- Use the canonical runtime resolver for all new deterministic activation tests; do not validate a duplicate implementation.
- Distinguish framework resolver parity, file-format compatibility, clean deployment, and actual native-host discovery in all evidence and completion claims.
- Keep changes surgical and reversible; no unrelated adapter, routing, or Skill-content refactors.

## File Relationship

- EXTENDS `docs/specs/governance-eval-harness.md` only by reusing its evaluation boundary: deterministic activation simulations stay separate from optional live-agent behavior scoring.
- INDEPENDENT from the legacy draft `docs/specs/skill-research-integration.md`; that file concerns content sourcing and prior integrations, not runtime discovery.
- REFINES backlog #79 by separating an immediately testable activation/discovery slice from the deferred paired effectiveness harness; backlog status changes remain a `/ship` concern.

## Domain Decisions

- [DECISION] Repair the five missing frontmatters and the `/app-init` generation contract before changing Skill content, because current Codex discovery and the official validator independently expose the same 9/14 gap.
- [DECISION] Keep the existing `.agent` stub, `.agents` canonical body, trigger registry, and `agentcortex:` metadata architecture; native discovery compatibility is additive, not a replacement control plane.
- [DECISION] Route the public resolver CLI through `trigger_runtime_core` so simulations cannot silently validate behavior different from the runtime used by phase workflows.
- [TRADEOFF] Customized downstream Skills will not be auto-rewritten; preserving user content is more important than automatic 14/14 upgrade discovery, so the compatible source arrives through `.acx-incoming` for explicit merge.
- [CONSTRAINT] Resolver parity across platform labels is not evidence of native host discovery; completion language must report these evidence classes separately.
- [CONSTRAINT] OpenAI metadata modernization, Claude-native discovery, Codex agent deployment, plugin packaging, and Skill consolidation require separate decisions and tests.
