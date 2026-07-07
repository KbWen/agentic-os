# Work Log — arch/knowledge-source-seam

- Branch: arch/knowledge-source-seam
- Classification: architecture-change
- Classified by: Claude (Opus 4.8)
- Frozen: true
- Created Date: 2026-06-20
- Owner: KbWen
- Guardrails Mode: Full
- Current Phase: ship
- Checkpoint SHA: df9c10b
- Recommended Skills: verification-before-completion (impl/test/ship), karpathy-principles (plan/impl/review), red-team-adversarial (review — arch Full+Beast), test-driven-development (impl/test — validator allowlist + schema), production-readiness (review/ship — fail-closed parse error paths)
- Primary Domain Snapshot: none

## Session Info
- Agent: Claude Opus 4.8
- Session: 2026-06-20T11:32:31Z
- Platform: Antigravity (Claude Code)
- Guardrails loaded: §1, §2, §4 (incl §4.1/§4.4/§4.5), §7, §8.1, §10, §13 (core + §13 triggered: edits bootstrap.md/config.yaml/validator)
- Override: none
- Downstream-Capabilities: none

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Brainstorm/Research: COMPLETE before bootstrap — design explored via a 6-agent panel + 3-agent simulation (×2 rounds) + a re-validation after the KB optimization; full decision in `.agentcortex/context/private/research-kb-integration.md §DECISION`. /brainstorm skipped (exploration done); proceeding bootstrap → ADR-009 → spec.
- SSoT ADR-Index write: added the ADR-009 entry to current_state.md ADR Index directly (the /adr non-ship SSoT-write exception per AGENTS.md §Non-ship SSoT write exceptions); Update Sequence + Last Updated left for /ship.
- PAUSED before /spec (2026-06-20): user is making a small KB update ("可能影響不大"). On resume: (1) re-check the KB git delta + `outputs/manifest.json` schema/contract — esp. whether `tier` landed in `task_routing` (would simplify the ADR-009 §Decision-3 / M5 "tiers read from routing_playbook" line) or whether the manifest `schema_version` bumped; (2) reconcile ADR-009 ONLY if the manifest CONTRACT changed (content-only KB edits need NO ADR/spec change — the seam depends on the contract, not the content); (3) then write `/spec` → docs/specs/knowledge-source-seam.md. Nothing committed yet; all work is uncommitted on branch arch/knowledge-source-seam (ADR-009 + SSoT ADR-Index + this Work Log).

## Task Description
- Add a present-only, OPTIONAL `knowledge_sources:` capability seam to agentic-os so the governed flow can CONSUME an external markdown knowledge-base ("B-via-A v2 manifest-aware"). Extends ADR-007's `downstream-capabilities.yaml`. Absent → zero cost (most adopters have NO KB). architecture-change: new capability class + cross-platform context-loading + new ADR (ADR-009, ADR-004/007 family).
- Decision + 5 prerequisites + minimal Stage-1 surface: research note §DECISION.
- Full chain: bootstrap → ADR-009 → /spec → /plan → /implement → /review → /test → /handoff → /ship.

## Phase Sequence
- bootstrap
- adr
- spec
- plan
- implement
- review
- test
- handoff
- ship

## External References
- ADR-007 (seam to mirror), ADR-004 (override-layer present-only precedent)
- bootstrap.md §1b (loader) + §3.6 (scope-detected table)
- validate_downstream_capabilities.py (allowlist to extend) + validate.sh:541-560
- AGENTS.md §Untrusted Tool Output + §Read-Once Discipline
- engineering_guardrails.md §13 (Governance Change Norms — ADD-Gate signal tier)
- Reference KB manifest: <KB>/outputs/manifest.json (schema_v2)
- Full design + decision: .agentcortex/context/private/research-kb-integration.md

## Known Risk
- Validator allowlist must be extended ATOMICALLY (else rejects whole downstream-capabilities.yaml). [prerequisite #1]
- New rules need an ADD-Gate signal tier (§13): structural seam = T1 (validator); behavioral consult-quality = honor-system → MUST be labeled, not sold as enforced.
- Rollback: revert PR (purely additive + present-only; absent file = zero behavior change). [verify at implement/ship]
- [plan] Validator sub-schema mis-scope (reject valid OR pass a forbidden field) → AC-2 tests both directions. §12.1 Read-Before-Write the validator + bootstrap §1b/§3.6 + config.yaml §downstream_capabilities + validate.sh/.ps1 §1b-check before editing.
- Gate-receipt reconciliation: removed the `adr` + `spec` gate-evidence receipts — for architecture-change, ADR/spec are doc-prerequisite phases (recorded in Phase Sequence/Summary), NOT recognized gate phases (validate.sh:1304 legal set = bootstrap/plan/implement/review/test/handoff/ship). This clears the work-log "illegal gate progression" on this branch.
- LOW-1 (review finding) fixed: validator `role` isinstance guard + test case (`role: [list]` → clean reject, not traceback). The identical PRE-EXISTING pattern on `skills.load_policy`/`subagent_policy` left as a separate candidate (scope discipline — not introduced here).

## Conflict Resolution
none (recommended skills compose cleanly; no partial-conflict pairs)

## Skill Notes
none

## Phase Summary
- bootstrap: classified architecture-change (new capability seam + cross-platform context-loading + new ADR). Brainstorm/research done (research note §DECISION). Guardrails Full + §13. Next: ADR-009.
- adr: wrote `docs/adr/ADR-009-knowledge-source-consumption-seam.md` (mirrors ADR-007 structure; folds in the 5 prerequisites + the §13 honest-enforcement-boundary table; reuses ADR-007 seam, manifest-preferred ladder, C rejected, Stage-2 deferred). Registered in SSoT ADR Index. | Confidence: 95% — high (design fully pre-decided + grounded; ADR records it).
- spec: wrote `docs/specs/knowledge-source-seam.md` (status draft, signal_tier T1) — 10 AC incl. AC-2 (validator allowlist atomic, gate-safety), AC-5 (mixed-scope fan-out), AC-7 (structural T1 seam-ships check), AC-9 (§13 honesty table); Domain Decisions + Non-goals (Stage-2 deferred / C rejected). KB unchanged on resume → ADR-009 contract stands. | Confidence: 95% — high.
- plan: 6 target files (validator [critical/atomic], bootstrap §1b+§3.6, config.yaml, validate.sh/.ps1, tests/guard, docs guide); 7 atomic steps; AC-1..10 covered; Mode Normal. No AGENTS.md edit (cites §Untrusted Tool Output, no duplication → no Deletion-First trigger on the always-loaded trio). | Confidence: 92% — high (residual: exact validator sub-schema shape + docs-paragraph location → resolve at implement via §12.1 Read-Before-Write).
- implement: 7 files, all additive (validator allowlist+KS sub-schema; bootstrap §1b bind + §3.6 kb-consult row; config caps; validate.sh/.ps1 AC-7 structural; tests; guide). No AGENTS.md edit. Inline-verified validator 8/8. | Confidence: 95% — high.
- review: 2 INDEPENDENT fresh-context adversarial reviewers → **both READY**. AC-1..10 PROVEN (file:line); gate-relaxation UNREPRESENTABLE (46+30 attack fixtures, none reached exit 0); no-KB zero-cost CONFIRMED (structural; AGENTS.md/shared-contracts unchanged); §13 honesty table accurate; 0 CRITICAL/HIGH/MED. 1 LOW (unhashable-role traceback) → FIXED (isinstance guard + test). | Confidence: 95% — high.
- test: **45 pytest passed**; e2e sim (valid→rc0, reject→rc1, fail-closed-flowmap→rc2, absent→rc0, guide ships + 0 external-KB deploy refs); validate.sh [PASS] AC-7 kb-consult + gate-safety, CI-equiv fail=0 (2 local FAILs = gitignored work-logs).
- handoff: SHIP-READY; `## Resume` + doc/code/log refs recorded; adopter-install sim (16 validator scenarios + real deploy-to-downstream, no-KB + BYO-different-layout) → ZERO errors. Next: /ship.
- ship: SSoT Ship History prepended (newest-first) + seq 79→80 + Last Updated + Spec Index entry; spec status→shipped; ~10 tracked files committed → pushed → PR. (commit SHA + PR# in chat.)

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T11:32:31Z
- Gate: plan | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T12:04:23Z
- Gate: implement | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T12:50:37Z
- Gate: review | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T12:50:37Z
- Gate: test | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T12:50:37Z
- Gate: handoff | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T13:13:21Z
- Gate: ship | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-20T13:17:07Z

## Evidence
- ADR-009 + spec (`docs/specs/knowledge-source-seam.md`) written; SSoT ADR Index updated.
- Implement (7 files, all additive):
  - `validate_downstream_capabilities.py`: allowlist += `knowledge_sources` + strict sub-schema (path required; `role` fixed `advisory`; `manifest_trusted` bool default false; key-allowlist rejects `required`/etc.; existing `_forbidden` recursion rejects `gate`/`ship_edge`/`block_if_missed`). **Inline-verified 8/8** (valid→None; role:authority/gate/required/no-path/non-bool→reject; skills non-regress; absent→inert).
  - `bootstrap.md`: §1b `knowledge_sources` binding (read-only/DATA/present-only) + §3.6 `kb-consult` scope-detected row (tiny-fix NEVER; manifest-preferred ladder; mixed-scope fan-out; cites §Untrusted Tool Output, no duplicate rule).
  - `config.yaml`: `knowledge_sources` caps (`kb_role_fixed: advisory`, `kb_manifest_trusted_default: false`).
  - `validate.sh` + `validate.ps1`: AC-7 structural check (assert bootstrap ships the `kb-consult` row), sh↔ps1 parity.
  - `tests/guard/test_capabilities_schema_gate_safety.py`: +1 positive + 5 reject KS cases → **44 passed**.
  - `.agentcortex/docs/guides/connecting-a-knowledge-base.md`: downstream guide — 3 adopter paths (no-KB/BYO/template) + minimal contract + structural-vs-honor-system table (AC-8/9).
- Review: 2 independent fresh-context adversarial reviewers (correctness/AC + security/optionality) → both **READY**; AC-1..10 PROVEN; gate-relaxation UNREPRESENTABLE; no-KB zero-cost structural-CONFIRMED; honesty table accurate; 0 CRIT/HIGH/MED; 1 LOW fixed.
- Test Gate: **45 pytest passed**; e2e sim PASS (rc0 valid / rc1 reject / rc2 fail-closed / rc0 absent / guide ships, 0 external-KB deploy refs); `validate.sh` [PASS] AC-7 `kb-consult` + gate-safety, CI-equiv **fail=0** (2 local FAILs = gitignored work-logs only, confirmed by both reviewers via git check-ignore).
- Rollback: revert PR (purely additive + present-only; absent KB → zero behavior change).
- Adopter-install simulation ("確定不會報錯"): **16 validator scenarios** (no-KB / empty / version-only / BYO-manifest / BYO-no-manifest / BYO-diff-entrypoint / BYO-abs-path / manifest_trusted-true / multi-source / full-coexist → rc0; adopter-typos / escalation / unhashable-role / no-path → rc1; flow-map-smuggle → rc2) — **ZERO tracebacks, correct rc each**. Real **deploy-to-temp-downstream** (deploy rc0): seam deployed (kb-consult row + guide + validator); no-KB downstream → validator rc0 inert; BYO KB at a *different* location/layout (`../my-team-wiki`, `llms.txt`, no manifest, nonexistent path) → rc0 valid; deployed `validate.sh` KB checks `[PASS]`×2.

## Resume
- **State**: SHIP-READY. arch-change `knowledge_sources` consumption seam (ADR-009). Phases bootstrap→adr→spec→plan→implement→review→test→handoff complete; only `/ship` (commit + push + PR) remains. Uncommitted on branch `arch/knowledge-source-seam`; base `df9c10b`.
- **Handoff references** (doc + code + log): doc = `docs/adr/ADR-009-knowledge-source-consumption-seam.md`, `docs/specs/knowledge-source-seam.md`; code = `.agentcortex/tools/validate_downstream_capabilities.py`, `.agent/workflows/bootstrap.md` (§1b + §3.6 kb-consult), `.agent/config.yaml`, `.agentcortex/bin/validate.sh` + `validate.ps1`, `tests/guard/test_capabilities_schema_gate_safety.py`, `.agentcortex/docs/guides/connecting-a-knowledge-base.md`; log = this file.
- **Verified**: 2 fresh-context reviewers READY; 45 pytest; e2e + 16 adopter scenarios + real deploy-to-downstream (no-KB + BYO) → no-error; validate.sh CI-equiv fail=0; work log clean (not flagged).
- **Next `/ship`**: commit the tracked deliverables + ADR + spec + guide; SSoT Ship History prepend + seq bump; push + PR. Reverse edges / NOT-READY: none. Candidates NOT in this PR: Stage-2; the pre-existing house-wide `skills.load_policy`/`subagent_policy` role-traceback (LOW).
