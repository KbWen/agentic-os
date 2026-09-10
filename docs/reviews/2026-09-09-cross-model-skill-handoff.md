# Cross-model skill description optimization: handoff to Claude

Date: 2026-09-09
Prepared by: Codex
Recipient: Claude (implementation and first review); Codex (independent final review)
Status: Pre-implementation brief. Research completed; implementation and live-model validation have not started.
Reference checkout: `main` at `3d36854e2920a82097567a62cdf9b0e84f27577e`.

## 1. Start here

The user wants a reasonable, minimal improvement to this project's skills and workflows that remains suitable for Claude, Gemini, Grok, and Codex. The agreed first-wave recommendation is to clarify two skill descriptions, preserve existing governance behavior, and return the change to Codex for independent final review.

Read this brief, inspect the current checkout, then follow the repository's normal bootstrap and planning flow for the bounded change below. Do not ask the user to restate the objective. Resolve routine wording and verification choices within this scope. If the live files or dependencies require a materially larger change, explain the evidence before expanding scope.

This document transfers research and intended work. It is **not** an approved implementation plan, frozen spec, Work Log, review PASS, or a `TESTED -> HANDEDOFF` receipt. No implementation phase has been completed. Do not manufacture phase receipts from this brief.

## 2. Ownership and execution boundary

| Owner | Responsibility | Deliverable |
|---|---|---|
| Claude, implementing session | Bootstrap, plan, minimal edit, generated metadata refresh, appropriate checks | Reviewable diff and reproducible evidence in its own Work Log |
| Claude, first review | Review scope, wording, trigger consistency and validation; use fresh context if available | Findings, fixes and remaining limitations; identify whether review was independent or self-review |
| Codex | Independently examine the actual change and evidence, not merely endorse Claude's summary | Final findings or approval of the reviewed revision |
| Claude, after final review | Resolve findings, then complete the applicable ship process | Final evidence and closure record |

Stop at the review-ready handback before merge, release, or ship closure. A Claude review does not replace the requested Codex final review. Any edits after that review need their relevant checks and affected review conclusions refreshed.

### User preference: one complete handback, minimal round trips

Claude owns the work through implementation, verification, first review, and correction of its own findings. Resolve routine wording, test selection, and in-scope implementation choices autonomously; do not send intermediate drafts to Codex or ask the user to approve each step. Complete the applicable governance steps within this authorized scope without adding discretionary confirmation pauses. Ask only for a material scope/authorization decision or a blocker that cannot be resolved independently; present all known blocking questions together.

Send Codex one complete review-ready package after those steps. Codex owns the final independent review and reports a concise verdict with actionable issues only. If corrections are necessary, consolidate them into one findings list; Claude resolves that list together, and Codex verifies the corrections and affected behavior. Do not create new review cycles for stylistic preferences or optional improvements outside acceptance criteria. Real correctness or safety failures still require correction; the one-handback preference is not permission to waive gates or evidence.

## 3. Bounded first-wave scope

Editorial targets:

1. `.agents/skills/systematic-debugging/SKILL.md`: clarify the frontmatter `description`.
2. `.agents/skills/production-readiness/SKILL.md`: clarify the frontmatter `description`.

Expected generated consequence:

3. `.agentcortex/metadata/trigger-compact-index.json`: regenerate through the existing generator because it incorporates skill content hashes.

The expected product diff is two descriptions plus the generated index. Normal branch-local governance artifacts are additional bookkeeping, not permission to expand the product change. Confirm the actual generator diff; do not promise exactly three total changed files before inspecting it.

Preserve skill names, body instructions, classification and phase eligibility, trigger registry conditions, load policies, permissions, and existing adapters. A description can affect model selection even if runtime metadata is unchanged: treat this as a small behavior-relevant edit, not automatically as a typo-only `tiny-fix`. Suggested starting classification is `quick-win`, subject to the current bootstrap rules.

### Candidate wording, not a frozen prescription

`systematic-debugging`:

```yaml
description: Use when investigating bugs, test failures, runtime errors, or unexpected behavior; reproduce the failure, verify root-cause hypotheses, then apply a minimal fix.
```

`production-readiness`:

```yaml
description: Use during review and ship of feature or architecture changes, or when requested for error handling, crash reporting, or logging; verify production observability.
```

Refine these sentences if comparison with the existing body and activation contract warrants it. Keep the primary use case first and the language provider-neutral. The production-readiness description must not imply an expanded implementation phase or silently suppress the existing automatic recommendation for feature/architecture-change work. Descriptions summarize eligibility; they do not override phase gates.

## 4. Why this scope survived investigation

- Both candidate descriptions currently emphasize the technique or benefit; their existing body/metadata provides more explicit usage conditions. Surfacing those conditions improves the discoverability contract without rewriting the workflow.
- API, authentication and database skill descriptions already state useful trigger conditions. They are not part of this edit.
- `CLAUDE.md` and `GEMINI.md` already point to shared `AGENTS.md` context. Another model-specific governance hierarchy is unnecessary for this first wave.
- Official Claude, Gemini and Grok Build documentation describes `description` as a skill-selection input. This supports the direction, but does **not** prove a success-rate or token-cost improvement in this repository.
- Grok Build documents reading `AGENTS.md` and Claude-compatible instruction files. That does not establish that every Grok-backed IDE or API wrapper loads this repository identically.

## 5. Explicit exclusions and earlier recommendations corrected

| Excluded first-wave change | Reason / existing owner |
|---|---|
| Remove the Confidence Gate or change its threshold | Existing T2 case `confidence-gate-pressure` in `.agentcortex/eval/governance.yaml`; this would change a governance boundary |
| Relax the two-failed-patches escalation rule | Existing T2 case `two-strike-third-patch-pressure`; assess separately with behavioral evidence |
| Remove verification after the final Work Log write | Backlog #158 records an actual stale-evidence incident and the reason for the current terminal-write exception |
| Replace the verification skill body wholesale with links | Standalone consumption and reliable reference loading have not been established; fewer lines alone is not a sufficient justification |
| Add Claude/Gemini/Grok-specific workflow copies | Reuse existing shared instructions and adapters; do not duplicate policy |
| Build another model-evaluation framework | Backlog #79 already owns effectiveness evaluation, with dependencies #77/#78 |
| Reconcile routing phrases and the registry | Backlog #187 already tracks this separate issue; not required for description clarification |
| Rewrite all skills, tighten security policy, change deployment or release machinery | Outside the user's agreed minimal first wave |

Earlier chat suggestions to relax stopping rules or evidence timing were exploratory and are superseded by these exclusions.

## 6. Read map and working-state checks

Begin with the repository's active `AGENTS.md`, any applicable override, and its required bootstrap context. At implementation time, check the branch and working tree again; the reference SHA is a research anchor, not a claim that the checkout is still unchanged. Do not overwrite another session's edits or log.

Then read only the relevant parts of:

| Path | Purpose |
|---|---|
| The two target `SKILL.md` files | Current descriptions, usage conditions, unchanged instructions |
| `.agent/skills/systematic-debugging` and `.agent/skills/production-readiness` | Existing summary metadata, phases and triggers |
| `.agentcortex/metadata/trigger-registry.yaml` | These two entries only; compare existing eligibility and load policies |
| `.agent/workflows/bootstrap.md` | Applicable classification and skill-recommendation rules |
| `.agent/workflows/shared-contracts.md` | Required phase-entry contracts and evidence timing |
| `.agentcortex/tools/generate_compact_index.py` | Existing index generation/check mechanism |
| `.agentcortex/tools/validate_trigger_metadata.py` | Existing metadata and generated-index verification |
| `.agentcortex/tools/run_skill_eval.py` | Read its scope note before interpreting its results |
| `docs/specs/_product-backlog.md` | Rows #79, #158, #165, #187 only, if needed for scope or evidence interpretation |

Resolve the implementation Work Log from the branch selected by Claude under `.agentcortex/context/work/<worklog-key>.md`; acquire its lock under the current contract. No implementation Work Log has been created by this research session. Do not treat a future path as an existing artifact.

Skip unrelated historical review snapshots, all-skills rewrites, and model migration guides unless new evidence makes them relevant. The private research note is optional background; this brief is self-contained and does not depend on another user's local private directory.

## 7. Acceptance criteria

- AC1: Each edited description puts its existing use conditions before its technique or benefit, and remains understandable without vendor-specific terminology.
- AC2: Names, skill bodies, runtime classification/phase rules, gates, and permissions remain unchanged. Any deviation is surfaced rather than hidden in generated output.
- AC3: YAML frontmatter remains valid; the existing metadata validator and compact-index freshness check pass on the proposed tree.
- AC4: Relevant existing regression checks pass, with commands, exit codes, and concise results recorded. Do not claim unrelated checks passed without running them.
- AC5: The final report separates static contract validation, documented host support, and observed model behavior. No unmeasured improvement or universal compatibility claim.
- AC6: Claude provides a review-ready revision and complete handback to Codex before closure.

### Static validation

Use the project's environment and current required gates. These are existing focused commands to start with, not a waiver of checks required by the selected classification:

```text
python .agentcortex/tools/generate_compact_index.py
python .agentcortex/tools/validate_trigger_metadata.py
python .agentcortex/tools/generate_compact_index.py --check
python .agentcortex/tools/check_skill_provenance.py
python -m pytest tests/ci/test_skill_provenance.py .agentcortex/tests/test_trigger_metadata_tools.py .agentcortex/tests/test_lifecycle_skill_activation.py
git diff --check
```

Regenerate only after the approved edits, inspect the resulting diff, and use final evidence that satisfies the repository's last-write timing requirement. Add or broaden tests only for a concrete uncovered risk, new failure, or required gate; avoid assertions that merely pin the replacement prose.

`run_skill_eval.py` evaluates the registry's lexical data contract. Its green result cannot show that a live model selected these edited descriptions correctly. `run_governance_eval.py` includes substring/regex scoring; keyword matches alone do not prove correct actions or preserved authorization behavior.

### Small cross-model comparison, without a new framework

Where usable environments are available, compare original and proposed descriptions using the same model version, host version, repository fixture, settings and prompt. Use fresh sessions; capture which instructions/skills were actually exposed. Do not install a new host, change account configuration, or silently substitute models merely to fill the matrix.

| Scenario | Example | Observe |
|---|---|---|
| Debugging positive | A test or runtime operation fails unexpectedly; investigate the cause | Whether the debugging skill is loaded and evidence precedes a patch |
| Observability positive | Review a feature whose caught errors only reach a debug sink | Whether production-readiness is applied in the eligible phase |
| Negative / near miss | Explain an API signature in a read-only question with no bug or completion claim | Whether unrelated diagnostic or readiness work is introduced |
| Explicit skill request | Request either skill within an eligible phase | Whether it is found and existing phase restrictions remain respected |
| Evidence / authorization boundary | Ask to declare completion while the required check is failing | Whether the agent accurately reports the incomplete state |

Determine expected behavior from existing phase/classification rules before scoring a case. A skill automatically recommended by those rules is not a false positive simply because the wording of the prompt is a near miss.

Record host, exact model/version if available, revision, prompt, skill exposure/loading, observed action, evidence link, and limitations. Separate host-required permission dialogs from discretionary model clarification. Repeat discrepant cases; a handful of runs is a smoke comparison, not a statistically established uplift.

If a host is unavailable, mark it **not run** and explain why. Static checks can establish a valid bounded change; they cannot establish cross-model behavioral improvement. Codex's final review must explicitly carry that limitation when deciding readiness.

## 8. Verified baseline and evidence limits

Recorded during research on 2026-09-09, before any skill implementation:

| Command / inspection | Observed result |
|---|---|
| `python .agentcortex/tools/validate_trigger_metadata.py` | Exit 0: 16 entries, 6 lifecycle scenarios, fresh compact-index parity |
| `python .agentcortex/tools/generate_compact_index.py --check` | Exit 0: compact index fresh |
| Tracked diff before writing this brief | Empty |
| Live Claude / Gemini / Grok comparison | Not run |
| Full validator / full test suite for the proposed edit | Not run; there is no implementation yet |

These are historical baseline observations, not validation of Claude's eventual revision. The handoff document itself is a new uncommitted research artifact; preserve it when establishing the implementation baseline. No code or skill edits were made by the research session.

## 9. Official references checked during research

- [Claude Code skills](https://code.claude.com/docs/en/skills): descriptions identify what a skill does and when to use it; keep the primary use case first.
- [Gemini CLI skill creation](https://geminicli.com/docs/cli/creating-skills/): skill selection uses the description; task scope and triggers should be specific.
- [Gemini CLI project context](https://geminicli.com/docs/cli/gemini-md/): environment-specific context handling reference.
- [Grok Build skills](https://docs.x.ai/build/features/skills-plugins-marketplaces): description and discovery behavior; some similarly named frontmatter fields have different semantics from other hosts.
- [Grok Build project rules](https://docs.x.ai/build/features/project-rules): `AGENTS.md`/Claude-compatible discovery and `grok inspect` support.

These are vendor documentation claims checked on the research date, not local integration tests. In particular, portable Markdown does not imply portable permission enforcement. Recheck only version-sensitive details needed for the environment actually being tested.

## 10. Required handback to Codex

Send the following together, using real paths and revisions:

1. Branch, base SHA, reviewed HEAD, and whether any uncommitted changes remain.
2. Work Log path and applicable plan/spec path, if required by classification.
3. Complete diff or PR link, with an explanation of any file beyond the two descriptions and generated index.
4. AC1-AC6 result table, with evidence and explicit unproven items.
5. Validation commands, exit codes, concise results, and the revision/state they cover.
6. Claude review findings, dispositions, and whether the reviewer had fresh context.
7. Cross-model observations, or a clear not-run matrix; no inferred success rows.
8. Remaining risks, including description-induced over-triggering or missed activation.

Codex final-review focus: unchanged scope/phase semantics, agreement between description and body/metadata, mechanically generated index changes, honest verification provenance, and absence of unsupported cross-model claims. Review the actual files and evidence independently; Claude's PASS is input, not the verdict.

## Resume snapshot

- Completed: narrowed research to two descriptions; identified generated-index dependency; checked official host guidance and existing static metadata baseline.
- Not started: bootstrap for implementation, skill edits, first review, live-model comparison, Codex final review, ship.
- Immediate next action: Claude establishes the current baseline and bootstraps the bounded description clarification.
- Closure recommendation: Keep work open for implementation and independent review; no merge/release recommendation yet.
