# Shared Phase Contracts

Canonical shared contracts referenced by all phase workflows. Source of truth for phase-entry skill loading, verification gates, and output compression rules.

## Phase-Entry Skill Loading

At every phase entry (`/plan`, `/implement`, `/review`, `/test`, `/handoff`, `/ship`), when the Work Log contains a `Recommended Skills` entry AND those skills list the current phase in their `phases:` metadata:

- **Metadata First**: BEFORE reading any full `SKILL.md` body, check `.agentcortex/metadata/trigger-compact-index.json` or `.agentcortex/metadata/trigger-registry.yaml` to confirm `load_policy` and `cost_risk`. Blindly loading multiple heavy skill bodies without consulting metadata is a Token Leak violation. **Fallback**: If neither metadata file exists (e.g., fresh repo or pre-Stage-1 deployment), fall back to the Cache Check rules below — metadata absence MUST NOT block skill loading entirely.
- **Cache Check**: Prefer `## Skill Notes` cache when valid. Cache hit = phase block exists AND ≥2 Checklist bullets AND ≥1 Constraint AND body > 50 chars. Thresholds: `.agent/config.yaml §skill_cache_policy`.
- **On cache miss**: Only on cache miss AND metadata `load_policy` match may the AI re-read the full `SKILL.md`, then refresh that skill's `## Skill Notes` block in the Work Log. Explicitly state: "Applying [skill-name] strategy."
- **Conflict Resolution**: Reuse `## Conflict Resolution` from bootstrap if multiple skills need precedence or scoping boundaries.
- **Exception**: `tiny-fix` has no Work Log — skip this check entirely.

## Verification Before Completion (5-Gate Sequence)

When `verification-before-completion` is active and completion is claimed for any non-`tiny-fix` phase, execute these gates IN ORDER before proceeding:

1. **Scope**: Confirm changes cover ONLY agreed scope — diff actual files vs. planned target files.
2. **Quality**: Execute required tests/static checks — ALL must pass. No "known failures".
3. **Evidence**: Compile reproducible evidence (specific commands, outputs, versions). "It should work" is NOT evidence. **Follow Evidence Truncation Rule (engineering_guardrails.md §5.2b)**: Max 3 lines for success, max 10 lines for failure. **Crucial:** For failures, extract the 10 *most diagnostic* lines (e.g., the actual Error/Exception and root stack trace at the bottom), NOT just the first 10 lines.
4. **Risk**: Confirm rollback strategy exists. List known risks.
5. **Communication**: Output completion summary (what changed, what was validated, what constraints remain).

If ANY gate fails → verdict: fail. Do NOT proceed.

Each phase adds local scope after these 5 gates (see individual workflow files for phase-local additions).

## Phase Output Compression

Phase chat outputs MUST be compact deltas — the Work Log is the persistent record. Do NOT duplicate Work Log contents in chat; reuse prior evidence by reference (`Ref: Work Log §<section>`); no "awaiting confirmation" after gate pass on explicit phase request. Per-phase delta:
  - `/bootstrap` → Classification (+1-line why), Goal, Skills (comma list), Context Read Receipt (1 line), Next Step. Full Constraints, AC, Non-goals, Risks, and the Read Plan live in the Work Log file, NOT in the chat response.
  - `/plan` → gate + plan (compact block: Target Files · Steps · Risk+Rollback · AC Coverage · Mode). No section headers when the block is < 15 lines.
  - `/implement` → files changed (list), tests run (1 line), checkpoint SHA. No code re-narration.
  - `/review` → burden-of-proof table + delta since implement. No re-printing the task description.
  - `/test` → commands + pass/fail + coverage delta. No re-printing the test skeleton.
  - `/handoff` → pointer to archived Work Log + 3-line Resume block.
  - `/ship` → final deltas + evidence refs + remaining constraints. No multi-paragraph prose.
- **Output template is ceiling, not floor**: skip any field with value `none` / `n/a` / unchanged-from-prior-phase. No bonus explanations or self-summaries on top of the template. See `## Core Directives` Response Budget for the hard cap.
