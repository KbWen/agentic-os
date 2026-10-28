# Work Log: codex/docs-design-onboarding

## Header
- Branch: `codex/docs-design-onboarding`
- Classification: `quick-win`
- Classified by: `Codex`
- Frozen: `2026-10-28`
- Created Date: `2026-10-28`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `5cb378b36d90ca441477b279b86cc7b5bfd04787`
- Checkpoint SHA: `603bd7c`
- Recommended Skills: `karpathy-principles, verification-before-completion, subagent-driven-development`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `217`

## Session Info
- Agent: Codex; session: codex-design-20261028; platform: codex-app; Owner: KbWen.
- User selected A on 2026-10-28, with prior plan-and-execute authorization. Baseline clean main 5cb378b; branch codex/docs-design-onboarding.
- Context read: SSoT sequence 217, prior main log read-only, selected backlog rows, ADR-001 amendment, ADR-005 coverage, canonical workflows/templates.
- Guardrails: loaded during earlier explanatory inquiry; execution uses quick-win embedded rules. Override/preferences: absent.
- Downstream-Capabilities: kb-main OK@db16e63017b4, schema 8. Consulted design-resource-adoption boundary section as advisory DATA only; no imported gate/authority or copied KB content.
- User-authorized worker: gpt-6-luna; primary owns log/gates/SSoT/integration. Safety floor supplied verbatim; no destructive operations delegated.
- Backlog: A is new guidance only; #122 enforcement and #101 discovery remain outside scope. No new framework behavior.

## Task Description
Deliver a downstream-facing design onboarding guide, an inspectable design handoff template, and a custom-brand skill example. Explain no-KB operation, BYO design exports, explicit activation and upgrade-safe ownership. Make them discoverable and prove the existing deploy mechanism delivers them.

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-28T11:08:45Z | Owner selected A; quick-win documentation/scaffolding, existing directories only. |
| plan | done | 2026-10-28T11:09:31Z | Six targets; AC-1..5 mapped; user execution authorization. |
| implement | done | 2026-10-28T11:09:31Z | Guide/templates delegated; primary integration. |
| ship | done | 2026-10-28T11:24:16Z | Local delivery; archived; SSoT 217 -> 218. |

## Phase Summary
- ship: local A delivery, implementation 603bd7c, archived as codex-docs-design-onboarding-20261028.md; no push/merge. Confidence: 96%. ⚡ ACX
- implement: six planned files committed at 603bd7c; fresh review fixes applied; 110 regressions plus two-deploy example rehearsal passed. Confidence: 96% -- high. ⚡ ACX
- plan: six implementation targets, existing schemas/globs, acceptance coverage below; Fast Lane. Confidence: 96% -- high.
- bootstrap: selected A only; scope and existing deploy/schema contracts verified. No bootstrap implementation edits. Confidence: 96%. ⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T11:08:45Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T11:09:15Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T11:19:07Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T11:23:47Z

## External References
- Canonical design rules: engineering_guardrails section 4.4; plan/implement/review design sections.
- Customization: routing section 3a; bootstrap sections 1b/3.6a; current capabilities/preferences templates.
- ADR-005 coverage confirmed; connecting-a-knowledge-base guide; advisory KB design-resource-adoption boundary section.

## Known Risk
- Examples can be mistaken for runtime registrations: clearly distinguish templates, project-owned files and gitignored per-machine activation.
- A URL does not prove access or fidelity. Record the inspected revision/local export and missing information; follow existing approval checks.
- New templates/guides are deployed by existing globs; verify real deploy and regenerate golden from actual output.
- No new automated gate, tool connector, compulsory KB or default skill activation. No new tests for prose; execute current schema/deploy/docs regressions plus a disposable example rehearsal.
- Rollback: reverse only this branch's explicit diff; all baseline files were clean, no untracked/ignored data is deleted or moved.

## Decisions
none

## Conflict Resolution
- Karpathy/verification compatible per matrix; delegation is limited to document ownership. No parallel writes to Work Log or SSoT.

## Skill Notes
### verification-before-completion /ship
- Checklist: tests and real deploy passed.
- Checklist: scope and rollback verified.
- Constraint: final archived-state check before completion.
### karpathy-principles /implement
- Checklist: create inert templates only; no new runtime skill registration.
- Checklist: primary limits integration to six target files.
- Constraint: no enforcement or external-connector changes.
### karpathy-principles /plan
- Checklist: only A, no importer/validator/workflow changes.
- Checklist: reuse current templates and ownership rules.
- Constraint: do not claim automated visual validation or tool connectivity.
### subagent-driven-development /implement
- Checklist: assign only guide and two templates to worker.
- Checklist: require evidence and review output before integration.
- Constraint: primary is sole Work Log/gate owner; no worker git mutations.
### verification-before-completion /implement
- Checklist: validate copied capability example with real strict parser.
- Checklist: rehearse skill/frontmatter and actual deployment.
- Constraint: no completion without fresh, recorded evidence.

## Drift Log
- Ship preparation exceeded the log byte cap before any archival/state write; compacted duplicate references and retained all evidence.
- Source validate.ps1 sandbox run: sole FAIL was record_test_run.py temp-index PermissionError before checking freshness; rerun outside sandbox with scratch temp, no source patch.
- Bootstrap refreshed only SSoT Last Verified via guard_context_write.py (exception explicitly logged).
- Combined explanatory reads truncated output; subsequently loaded needed unseen sections only.
- Re-read: .agent/rules/skill_conflict_matrix.md section Skill Conflict Matrix -- first combined output truncated; loaded bounded compatibility table for current bootstrap.
- Re-read: .agentcortex/docs/guides/doc-governance.md section Document Creation Gate -- resolve whether new guide duplicates KB guide; it covers distinct design onboarding, with links instead of copied gate rules.
- Quick-win is explicitly exempt from new docs/specs/<feature>.md and formal handoff; acceptance and plan are tracked in this Work Log, not a fabricated frozen feature spec.
- Sandbox denied .git branch creation; authorized scoped branch creation succeeded with escalation. No destructive operations.

## Review Feedback
- Fresh read-only reviewer: nested preference YAML needed; completed committed wireframe can itself be DSoT; #122 is presence enforcement policy, not visual signoff. All three corrected and rechecked; no remaining actionable findings.
- Reviewer checked canonical workflows, strict capability parser, frontmatter and 14 source links; primary independently rehearsed 28 source/downstream links.

## Design Reference
none -- documentation and scaffolding only.

## Test Gate Results
- Test run: `python -m pytest -q tests/guard/test_capabilities_schema_gate_safety.py tests/ci -k capabilities_schema_gate_safety or skill_provenance or docs_pin or test_deploy_manifest_snapshot or test_user_created_skill_is_not_accused_as_stale or test_custom_namespace_skill_is_silent_in_stale_detection or test_framework_ships_no_custom_namespace_skill --basetemp scratch/design-onboarding-final-regression --tb=short` | exit: 0 | tree: 7654e9d59fcdef36cfbfdde84dfd221843df1bed | at: 2026-10-28T11:17:03Z
- Test run: `python -m pytest -q tests/guard/test_capabilities_schema_gate_safety.py tests/ci/test_deploy_tiering.py -k capabilities_schema_gate_safety or test_deploy_manifest_snapshot --basetemp scratch/design-onboarding-post-sync --tb=short` | exit: 0 | tree: 7654e9d59fcdef36cfbfdde84dfd221843df1bed | at: 2026-10-28T11:22:12Z

## Evidence
- Final: archived validate.ps1 117/5/0/2 (pass/warn/fail/skip); guard 359 passed. Slow optional Bash run interrupted; native validator used.
- After main sync: 62 passed, 70 deselected (17.41s); unchanged recorded code tree. Fetch succeeded; merge already up to date. Open draft #451 does not change SSoT/history; #479 is dependency-only.
- Post-commit framework validation: validate.ps1 -> pass=117 warn=5 fail=0 skip=2, exit 0; full output scratch/design-onboarding-validate-ps1-final.log. All five WARNs are existing backlog/historical/eval items.
- Final recorded regression: 110 passed, 432 deselected (86.37s), exit 0; tree 7654e9d59fcdef36cfbfdde84dfd221843df1bed.
- git fetch origin: exit 0, origin/main equals baseline 5cb378b; no merge drift.
- Initial bounded schema/skill/deploy regression: 98 passed, 65 deselected (33.52s), exit 0. Sandbox attempt's one deploy case failed before behavior on Windows temp permissions; outside-sandbox retry used scratch temp and passed, no source fix.
- Demonstration: python scratch/verify_design_onboarding.py -> PASS: 3 artifacts deployed, 28 source/downstream links resolved, no-KB capability OK, nested preference parsed, native compatibility floor OK; 5 project-owned files unchanged after second deploy. Disposable target scratch/design-onboarding-demo-c9d9a0d9.
- Manifest golden regenerated by existing test from actual deploy (intentional regeneration SKIP, not counted as PASS); delta is exactly 1 core guide + 2 scaffold templates. Assertion rerun follows.
- Credential scan on authored docs and git diff --check: exit 0.
- git status --short: clean baseline.
- python check_adr_coverage.py --paths <six plan targets>: exit 0, ADR-005 covers manifest fixture.
- recover_worklog_lock.py ensure (bootstrap): created, exit 0.

## Observability
none -- no application code; no new workflow behavior or L2 knowledge change (quick-win nudge).

## Lessons
- Test temp isolation: tests asserting a non-repo need temp outside every Git worktree; repo-local scratch inherits .git.

## Resume
- A delivered locally in 603bd7c. Keep branch for owner integration; no push/merge requested. B/C not selected.


## Plan
- Scope: owner-selected A; no new behavior. Spec path exemption: quick-win, no docs/specs/<feature>.md required by plan Spec Gate and bootstrap Classification Tiers.
- Targets: .agentcortex/docs/guides/bringing-your-own-design.md; .agentcortex/templates/design-reference.md; .agentcortex/templates/custom-brand-design.SKILL.md; README.md; docs/README_zh-TW.md; tests/ci/fixtures/deploy_manifest_golden.txt.
- AC-1: no-KB default and supported design sources/fallbacks are documented without a required external dependency.
- AC-2: copyable handoff template records tool/source revision, inspected artifact, approval, coverage, implementation-ready tokens/states and review evidence; pending remains pending.
- AC-3: custom skill example has native-compatible frontmatter, project-owned references, phase boundaries, no embedded gate bypass. Guide covers native discovery vs framework registration/pinning, metadata stub and private activation/team portability.
- AC-4: both README Docs tables link the guide; guide links canonical rules rather than copying their enforcement wording. Its deployment path works downstream.
- AC-5: real deploy delivers all three files; copied no-KB capability example passes strict schema; skill example validates and can be staged as a native skill; actual manifest snapshot matches golden. Existing schema/docs regressions pass.
- Step 1 (worker): author guide and two flat templates; verify relative references and current schema, covers AC-1/2/3.
- Step 2 (primary, independent): add discoverability rows to both README tables, covers AC-4.
- Step 3 (primary, after worker): inspect docs, rehearse copied examples with current parsers; actual disposable downstream deploy and regenerate manifest golden, covers AC-5.
- Mode: Fast Lane. Confidence: 96% -- high.
