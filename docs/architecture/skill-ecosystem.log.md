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
