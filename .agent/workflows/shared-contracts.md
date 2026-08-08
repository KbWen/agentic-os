# Shared Phase Contracts

Canonical shared contracts referenced by all phase workflows. Source of truth for phase-entry skill loading, verification gates, and output compression rules.

## Phase-Entry Skill Loading

At every phase entry (`/plan`, `/implement`, `/review`, `/test`, `/handoff`, `/ship`), when the Work Log contains a `Recommended Skills` entry AND those skills list the current phase in their `phases:` metadata:

- **Metadata First**: BEFORE reading any full `SKILL.md` body, check `.agentcortex/metadata/trigger-compact-index.json` or `.agentcortex/metadata/trigger-registry.yaml` to confirm `load_policy` and `cost_risk`. Blindly loading multiple heavy skill bodies without consulting metadata is a Token Leak violation. **Fallback**: If neither metadata file exists (e.g., fresh repo or pre-Stage-1 deployment), fall back to the Cache Check rules below — metadata absence MUST NOT block skill loading entirely.
- **Cache Check**: Prefer `## Skill Notes` cache when valid. Cache hit = phase block exists AND ≥2 Checklist bullets AND ≥1 Constraint AND body > 50 chars. Thresholds: `.agent/config.yaml §skill_cache_policy`.
- **On cache miss**: Only on cache miss AND metadata `load_policy` match may the AI re-read the full `SKILL.md`, then refresh that skill's `## Skill Notes` block in the Work Log. Explicitly state: "Applying [skill-name] strategy."
- **Conflict Resolution**: Reuse `## Conflict Resolution` from bootstrap if multiple skills need precedence or scoping boundaries.
- **Exception**: `tiny-fix` has no Work Log — skip this check entirely.

## Phase-Entry Lock (single-writer per Work Log)

At every non-`tiny-fix` phase entry (`/plan`, `/implement`, `/review`, `/test`, `/handoff`, `/ship`), acquire or refresh the Work Log lock BEFORE the first Work Log write of that phase:

```bash
python .agentcortex/tools/recover_worklog_lock.py ensure \
  --lock .agentcortex/context/work/<worklog-key>.lock.json \
  --worklog .agentcortex/context/work/<worklog-key>.md \
  --owner "<owner>" --session "<session>" \
  --branch "<branch>" --phase <entering-phase>
```

Consume the exit code per `.agent/config.yaml §worklog_lock.mode`:

- **Exit 0** (`created` / `updated` / `recovered`): proceed. A recovery already appended its own Drift Log line.
- **Exit 2** (`active` — held by another live session) under `mode: blocking` (default): **Gate FAIL**. Output the holder (owner / session / updated_at) and STOP with exactly these options: (a) wait until the lock goes stale (`stale_timeout_minutes`), (b) ask the user to approve a takeover, then re-run `ensure` with `--takeover` (requires `--worklog`; appends an audit line to the Work Log Drift Log), (c) continue on a different branch. Do NOT write to the Work Log while this gate is failed.
- **Exit 2** under `mode: advisory`: warn with holder details and ask the user to confirm before proceeding (legacy behavior).
- **Exit 3** (persistent filesystem failure): surface the error and retry once; do NOT misreport it as a held lock.

At `/ship` and `/handoff` completion, attempt `release` (steps live in those workflows; failure → WARN, never gate-fail — staleness self-heals). `tiny-fix` is exempt (no Work Log). **Python-unavailable fallback**: blocking enforcement requires the helper; without Python the lock degrades to the manual advisory checklist in `bootstrap.md §2a` — stated honestly, no fake MUST.

Enforcement teeth (per the [enforcement] Global Lesson): the tool's exit codes are tested in `tests/guard/test_worklog_lock_blocking.py`, and `validate.sh`/`validate.ps1` WARN when a non-stale lock's owner/phase mismatches the Work Log header — the signature of a session that skipped this contract.

## Verification Before Completion (5-Gate Sequence)

When `verification-before-completion` is active and completion is claimed for any non-`tiny-fix` phase, execute these gates IN ORDER before proceeding:

1. **Scope**: Confirm changes cover ONLY agreed scope — diff actual files vs. planned target files.
2. **Quality**: Execute required tests/static checks — ALL must pass. No "known failures".
3. **Evidence**: Compile reproducible evidence (specific commands, outputs, versions). "It should work" is NOT evidence. **Follow Evidence Truncation Rule (engineering_guardrails.md §5.2b)**: Max 3 lines for success, max 10 lines for failure. **Crucial:** For failures, extract the 10 *most diagnostic* lines (e.g., the actual Error/Exception and root stack trace at the bottom), NOT just the first 10 lines. **Look-timing:** the run quoted as final evidence has to postdate the last state write of this phase, including Work Log writes (gate receipt, `## Phase Summary`) — an earlier capture describes a tree that no longer exists, so re-run after the final write.
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
