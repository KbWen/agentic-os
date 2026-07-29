---
status: living
domain: skill-ecosystem
---

# Skill Ecosystem — Decision Log (L2)

### [skill-ecosystem][2026-05-04][feat/acx-phase-shims]
source_spec: none (quick-win, no spec)
source_sha: 94ab322

[DECISION] Subagent skill injection uses Claude Code native `skills:` frontmatter in `.claude/agents/acx-*.md` thin shims. Each shim body ≤5 lines pointing to the canonical workflow; all logic stays in `.agent/workflows/`. Shims are the enforcement layer for skill injection — not AGENTS.md MUST rules (which are honor-system theatre).

[CONSTRAINT] Shim skill names that map to `.agent/skills/<name>/` must have a corresponding `.agents/skills/<name>/SKILL.md` — validated by `validate.sh` + `validate.ps1` shim skill-existence check. Claude Code built-in skills (no `.agent/skills/` directory) are silently skipped by the validator.

[TRADEOFF] Native injection via shim is real enforcement (code-level, not honor-system) for subagents, but requires the caller to specify `subagent_type: "acx-<phase>"`. Parent session skill loading remains Phase-Entry Skill Loading (honor-system) — accepted as the industry norm for LLM governance systems.

### [skill-ecosystem][2026-07-28][codex/skill-runtime-modernization]
source_spec: docs/specs/skill-runtime-modernization.md
source_sha: 73327c9

[DECISION] Repair the five missing frontmatters and the `/app-init` generation contract before changing Skill content, because current Codex discovery and the official validator independently expose the same 9/14 gap.

[DECISION] Keep the existing `.agent` stub, `.agents` canonical body, trigger registry, and `agentcortex:` metadata architecture; native discovery compatibility is additive, not a replacement control plane.

[DECISION] Route the public resolver CLI through `trigger_runtime_core` so simulations cannot silently validate behavior different from the runtime used by phase workflows.

[TRADEOFF] Customized downstream Skills will not be auto-rewritten; preserving user content is more important than automatic 14/14 upgrade discovery, so the compatible source arrives through `.acx-incoming` for explicit merge.

[CONSTRAINT] Resolver parity across platform labels is not evidence of native host discovery; completion language must report these evidence classes separately.

[CONSTRAINT] OpenAI metadata modernization, Claude-native discovery, Codex agent deployment, plugin packaging, and Skill consolidation require separate decisions and tests.

[DECISION] **Supersedes the 2026-06-19 scaffold exemption** (PR #259 / backlog #80 G1a, archived at `.agentcortex/context/archive/feat-skill-provenance-20260619.md`). That decision deliberately exempted the five scaffold `SKILL.md` files from the compatibility floor on the grounds that they carried no frontmatter and their metadata already lived in the flat `.agent/skills/` stubs. The exemption was correct for its own goal (provenance inventory) and wrong for this one: it is exactly what let 5/14 Skills stay invisible to native host discovery for five weeks, because "no frontmatter" was treated as a legitimate state rather than the defect it is. `check_skill_provenance.py` is now fail-closed for every first-party Skill including scaffolds; the flat-stub metadata check is unchanged and remains additive. Reopening the exemption requires a superseding entry here, not a code-level carve-out.

[CONSTRAINT] Governance docs that ship downstream MUST NOT cite `.agentcortex/tools/<tool>.py` paths for source-repo-only validators. `deploy.sh` does not ship them, and `test_deployed_governance_referenced_tools_are_deployed` reads any such citation in a deployed doc as a dangling `python ...` command. Describe upstream enforcement in prose instead — the downstream reader cannot run the tool either way.
