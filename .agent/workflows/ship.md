---
name: ship
description: Final delivery and archival. Requires TESTED state and handoff gate.
tasks:
  - ship
---

# /ship

> Canonical gate: `Ref: .agent/rules/state_machine.md`

## Gate Engine (Turn 1 — Antigravity Hard Path)

**Phase Verification** (per bootstrap §2b): Read `Current Phase` from Work Log header. Verify transition to `ship` is legal. If illegal, STOP. Otherwise update `Current Phase: ship`. If a new commit was created since the last `Checkpoint SHA`, SHOULD refresh it.

Before ANY ship action, output the Minimal Gate Block:

```yaml
gate: ship
classification: <from Work Log>
branch: <current branch>
checks:
  worklog_exists: yes|no
  spec_exists: yes|no|na
  state_ok: yes|no
  handoff_ok: yes|no|na
verdict: pass|fail
missing: []
```

- If `verdict: fail` → output ONLY the gate block. STOP.
- **Gate Evidence Receipt**: After outputting the gate block, append a compact gate receipt to the Work Log under `## Gate Evidence`:
  ```
  - Gate: ship | Verdict: <pass|fail> | Classification: <tier> | At: <ISO-timestamp>
  ```
- Resolve the active Work Log path for the current `<worklog-key>` before evaluating `worklog_exists`.
- If no active Work Log exists but archive context for the branch exists, create a follow-up active log, warn the user, and continue gate evaluation. Missing handoff references or missing evidence still require `verdict: fail`.
- If classification is `feature` or `architecture-change`:
  - If the user explicitly requested shipping, proceed directly after gate pass.
  - Only ask for an extra confirmation if ship entry was inferred rather than explicitly requested, or if a separate high-impact choice appears inside `/ship` (for example, concurrent-state merge risk or knowledge-consolidation diff preview).
- `quick-win` / `hotfix`: proceed directly after gate pass.

## Work Log Compaction Check

Before ship evaluation, check the active Work Log size. If it exceeds compaction thresholds (see `.agent/config.yaml` §worklog), compact per `/handoff` §6 BEFORE proceeding. Ship with a bloated log risks archiving an unnecessarily large file.

## Ship Checklist (mandatory — skip = ship fail)

- [ ] Evidence recorded in Work Log
- [ ] `current_state.md` updated
- [ ] Active Work Log archived to `.agentcortex/context/archive/`
- [ ] Spec-Test trace verified (feature / architecture-change only — see §Spec-Test Traceability below)
- [ ] Domain Doc updated or skip justified (feature / architecture-change only — see §Knowledge Consolidation below)
- [ ] Observability Readiness verified (feature / architecture-change only — see §Observability Readiness below)

## Observability Readiness Check (feature / architecture-change only)

**Scope**: This check applies ONLY to `feature` and `architecture-change` classifications. `tiny-fix`, `quick-win`, and `hotfix` are exempt.

Before ship, verify the delivered code meets production observability requirements:

1. **Error boundary defined**: all error-handling paths use a production-observable logger (per §5.2a). No debug-only logging as sole error path.
2. **Log sink documented**: Work Log records where errors are reported (e.g., "Sentry via `Logger.error()`", "stdout → CloudWatch", or "Crashlytics via `FirebaseCrashlytics.recordError()`"). If the project has no production logging infrastructure yet, document that as a Known Risk.
3. **Rollback telemetry**: rollback plan (per §12.5) includes how operators will know the rollback succeeded (e.g., error rate returns to baseline, health check passes).

This is an advisory check — missing observability readiness produces a warning, not a hard fail. The warning MUST be recorded in the Work Log under `## Known Risk`.

## Spec-Test Traceability Check (feature / architecture-change only)

**Scope**: This check applies ONLY to `feature` and `architecture-change` classifications. `tiny-fix`, `quick-win`, and `hotfix` are exempt.

Before ship, verify that every Acceptance Criterion in the referenced spec has at least one linked test or an explicitly justified exception:

1. Read the spec's AC section. Each AC SHOULD have a stable identifier (e.g., `AC-1`, `AC-2`).
2. Check test files for `spec_ref:` frontmatter or inline comments linking to the spec.
3. Build coverage map: AC → test(s). If any AC has no linked test, output: `"⚠️ AC [id] has no linked test. Justify or add test before ship."`.
4. An AC may be explicitly exempted with justification recorded in the Work Log (e.g., "AC-3: visual-only change, verified by screenshot evidence").

This is an advisory check in this batch — missing trace produces a warning, not a hard fail. Future batches may escalate to hard gate.

## Skill-Aware Ship Checks (Auto-Enforced)

Before evaluating entry conditions, apply the Phase-Entry Skill-Loading Protocol (AGENTS.md §Phase-Entry Skill Loading). Read `Recommended Skills` from the active Work Log before selecting which skill guidance to apply in this phase. Then enforce:

**IF `verification-before-completion` is active (MANDATORY for non-tiny-fix):**
Apply the Verification-Before-Completion 5-Gate Contract (AGENTS.md §Verification Before Completion (5-Gate Sequence)). If ANY gate fails → `verdict: fail`. Do NOT proceed to Entry Conditions.
Phase-specific: Evidence = specific commands, outputs, versions; Communication Gate = include constraints that remain.

**IF `finishing-a-development-branch` is active:**
Before merge/PR, execute:
1. Re-sync with mainline: `git fetch origin && git merge origin/<main-branch>` (use repo's default branch) — verify no conflicts or behavioral drift
2. Re-run minimal required tests + critical regression tests after sync
3. Verify documentation, migration scripts, configuration changes are all committed
4. Select closure option and state it explicitly:
   - **Merge now**: Verification complete, risks acceptable
   - **Open PR**: Requires reviewer or cross-team sync
   - **Keep branch**: Has remaining work; keep active
   - **Archive/Close**: Requirement canceled or strategy changed
Entering "Merge now" is PROHIBITED if evidence is insufficient.

## Entry Conditions (HARD)

1. Current state is `TESTED` (for `quick-win`/`hotfix`: `IMPLEMENTED` with evidence is sufficient).
2. `feature` and `architecture-change` MUST have completed `/handoff`. `quick-win` and `hotfix` are exempt from `/handoff` (per engineering_guardrails.md §10.4).
3. When `/handoff` is required, references MUST meet minimums (doc + code + work log).
4. **Security Gate**: No unresolved CRITICAL/HIGH security findings in Work Log (per `.agent/rules/security_guardrails.md` §6). If found, `verdict: fail`, `missing: ["security: N unresolved CRITICAL/HIGH findings"]`.

If ANY condition fails, MUST reject `/ship` and output missing list.

## Output Format

Apply the shared `Phase Output Compression` contract from `AGENTS.md`.

- Commit message (Conventional Commits)
- Change summary (bullet points)
- Test results (Evidence)
- Doc sync status (Did `current_state.md` update?)
- Known risks and rollback strategy

Compression rule:
- summarize final deltas and evidence references only
- do not replay full implementation/review/test narratives that are already stored in the Work Log

## Phase Summary Update

After ship gate passes and before archival, append one line to `## Phase Summary` in the Work Log:
```
- ship: [1-line summary — verdict, commit SHA, archive path]
```

## Review Snapshot Routing Check (AC-30)

Before proceeding with ship, check `docs/reviews/` for any review snapshots that contain structured `routing_actions` blocks with `status: pending` targeting files in the current task's `primary_domain`. If found, MUST resolve before ship or record explicit deferral with justification in the Work Log.

## State Update & Archival

1. **Ship Guard (§11.3)**: Before writing, check if `current_state.md` has been modified since this task started. If modified by another session, warn user and request confirmation before merging. Use **additive merge**, never full overwrite.
2. **SSoT Update & Ship History**:
- Update `.agentcortex/context/current_state.md` Spec Index statuses (mutable snapshot) via `.agentcortex/tools/guard_context_write.py`.
- Use the helper as documented in `.agentcortex/docs/guides/guarded-context-writes.md`. In Stage 1, missing guard receipts are a validation warning, not a hard runtime block.
   - MUST append the completion record to the bottom of the file under `## Ship History`.
   - Use the format:

     ```markdown
     ### Ship-<branch_name>-<YYYY-MM-DD>
     - Feature shipped: [summary]
     - Tests: Pass
     ```

   - NEVER edit, reorder, or delete previous entries in the `## Ship History`.
   - If Ship History exceeds 10 entries, archive older entries to `.agentcortex/context/archive/ship-history-YYYY.md` and keep only the latest 10 in `current_state.md`.
3. Archive `.agentcortex/context/work/<worklog-key>.md` to `.agentcortex/context/archive/` (if task complete).
    - Do NOT duplicate `/retro`-promoted Global Lessons during ship. `/retro` owns structured Global Lesson promotion.
    - **Archive Index Update**: After archiving, append a structured record to `.agentcortex/context/archive/INDEX.jsonl` (one JSON object per line) via `.agentcortex/tools/guard_context_write.py`:
      ```json
      {"log": "<archived-filename>", "branch": "<branch>", "classification": "<tier>", "modules": ["<file-or-module>"], "specs": ["<spec-ref>"], "patterns": ["<tag>"], "decisions": ["<1-line>"], "shipped": "<YYYY-MM-DD>"}
      ```
      - If `INDEX.jsonl` does not exist, create it. If a legacy `INDEX.md` exists, keep it as a compatibility mirror but prefer `INDEX.jsonl` for new entries.
      - Fallback: If `.agentcortex/tools/guard_context_write.py` is unavailable, write the JSONL line directly.
4. **Product Backlog Update**: If `docs/specs/_product-backlog.md` exists and this feature is listed:
   - Update feature status: `In Progress` → `Shipped`
   - Update `last_updated` in frontmatter
   - If ALL features are now `Shipped` or `Deferred`/`Cancelled`, output: "🎉 Product backlog complete. All features shipped or resolved."
   - If Pending features remain, output: "Backlog: [N] features remaining. Next session can run `/spec-intake` §8a to continue."
   - Update `current_state.md` **Active Backlog** field to `docs/specs/_product-backlog.md` (if not already set). This is the only mechanism that persists backlog awareness across sessions via SSoT.
5. Freeze Artifacts: Ensure all produced Specs/ADRs have YAML frontmatter `status: frozen`. If missing, add it before commit.
   - **Skip non-freezable statuses**: Documents with `status: living` (e.g., `_product-backlog.md`) or `status: raw` (e.g., `_raw-intake.md`) MUST NOT be frozen. These are tracking/temporary artifacts, not spec deliverables.
   - **Spec Freshness**: If implementation DIFFERS from any referenced spec's AC, MUST update the spec to match actual behavior before freezing. Append `[Updated: <date>]` to the corresponding Spec Index entry in `current_state.md`.
   - **Shipped Frontmatter** (AC-27): After freezing, set `status: shipped` on all referenced specs that are being completed in this branch. This signals to future `/bootstrap` sessions to prefer Domain Doc L1 over these specs as design authority.

6. **Knowledge Consolidation** (feature / architecture-change only — AC-13–17, AC-32):

   **Capability-by-presence with snapshot accountability**: Read `Primary Domain Snapshot` from the active Work Log first. If the current spec lacks `primary_domain` but the snapshot records a non-`none` value, treat the snapshot as authoritative for ship gating and require an explicit justification for why the field was removed. If both the spec and snapshot are missing/`none`, skip this step entirely.

   **Forward-only rollout** (AC-33): Knowledge consolidation applies only to specs created after the doc-lifecycle-governance feature is shipped. Existing shipped specs (those with `status: shipped` set before this feature) are NOT retroactively consolidated. Do not attempt to consolidate them.

   **Domain Doc Gate** (AC-15): If the current spec or the `Primary Domain Snapshot` indicates `primary_domain` and Domain Doc L2 (`docs/architecture/<primary_domain>.log.md`) was NOT modified in this branch, MUST prompt:
   `"Domain doc not updated. Spec or bootstrap snapshot still points to primary_domain '<domain>'. Summarize or justify skip against that recorded field."` Missing justification = ship gate fail. Generic skip text is invalid; the justification must explicitly explain why consolidation is still unnecessary despite the recorded `primary_domain`, including any reason the field was later removed from the spec. Acceptable examples: `"L1 already covers this incremental change; no new domain decision was introduced."` or `"The domain doc was updated separately in this session and consolidation is therefore already satisfied."`

   **Advisory Lock Check** (AC-17): Before writing L2, check `.agentcortex/context/domain/<domain>.lock.json`. If a non-stale lock exists for another session, warn: `"⚠️ Domain doc lock held by [owner] since [updated_at]. Concurrent write risk. Proceed? (yes/no)"`. This is advisory — it warns but does not hard-block.

   **Consolidation Steps**:
   a. Read `## Domain Decisions` from the referenced spec. If absent, skip (no entries to consolidate).
   b. Build the entry block:
      ```markdown
      ### [<primary_domain>][<YYYY-MM-DD>][<branch-name>]
      source_spec: docs/specs/<feature>.md
      source_sha: <HEAD SHA>

      <copy each [DECISION] / [TRADEOFF] / [CONSTRAINT] entry verbatim>
      ```
   c. **Diff Preview** (AC-16, feature / architecture-change): Show the entry block as a diff preview to the user before writing. Require user confirmation before proceeding (consistent with existing `/ship` confirmation gate).
   d. Append the entry block to `docs/architecture/<primary_domain>.log.md` (L2, append-only — NEVER modify or delete existing entries).
   e. For each `secondary_domain` in the spec's `secondary_domains` list: append a cross-reference pointer only to that domain's L2 — no content duplication:
      ```markdown
      ### [<secondary_domain>][<YYYY-MM-DD>][<branch-name>]
      cross-ref: See [<primary_domain>][<YYYY-MM-DD>][<branch-name>] in docs/architecture/<primary_domain>.log.md
      ```
   f. **Restructure Advisory** (AC-19): Count L2 entries in the `primary_domain` log. If any section has ≥ `domain_doc.restructure_threshold` entries (default: 5 from `.agent/config.yaml`), output advisory: `"Domain doc '<domain>' has N entries. Consider /govern-docs --restructure <domain>."`

7. **SSoT Heartbeat Update** (AC-25): As the final step of State Update & Archival, increment the `Update Sequence` by 1 in `current_state.md` and set `Last Updated` to the current ISO timestamp. This runs after all other ship writes (SSoT, archive, backlog, freeze, knowledge consolidation) are complete. Use guard_context_write.py for this write.
