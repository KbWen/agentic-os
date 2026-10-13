# Work Log: fix/legacy-tools-migration-220

## Header

- Branch: `fix/legacy-tools-migration-220`
- Classification: `hotfix`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-13`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `32bb1cc`
- Checkpoint SHA: `1bff4a1`
- Recommended Skills: `verification-before-completion (auto), systematic-debugging (auto: bug), red-team-adversarial (auto: hotfix → Lite), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `191`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-13 03:44 UTC`
- Platform: `claude-code`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §5 (testing), §12 (implement) — full file in context this session
- Override: none
- Downstream-Capabilities: none

---

## Task Description

- Backlog #220 (P1): on a brownfield FIRST install, `deploy.sh`'s legacy-path migration deletes a project's own `tools/validate.{sh,ps1,cmd}` with no backup (data loss, same class as #188). Fix: only treat `tools/validate.*` as framework wrappers when a prior Agentic OS install is evidenced; otherwise leave them untouched. Owner asked to fix #220 before cutting the next stable release (chat 2026-10-13).
- Non-goals: #221 (`CP_FLAG`), other migration branches (agentcortex/, docs/context/ are already marker-gated).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-13 | hotfix: deploy data loss |
| research | done | 2026-10-13 | root cause inline (below) |
| plan | done | 2026-10-13 | RED tests first |
| implement | done | 2026-10-13 | b8aff0f |
| review | done | 2026-10-13 | NOT READY → D-1 → PASS (fresh reviewer) |
| test | done | 2026-10-13 | CI full suite + downstream spot-check |
| handoff | n/a | — | hotfix exempt |
| ship | done | 2026-10-13 | SSoT 191→192; archived |

---

## Phase Summary

- bootstrap: hotfix (installer data loss on adopter files; review + test mandatory). ⚡ ACX
- research: Root Cause — `deploy.sh` §"Migrate from legacy paths" enters on `_acx_legacy_confirmed || tools/validate.* exists`, and its last step `rm -f`s `tools/validate.*` unconditionally; the marker gate (`agentcortex/` dir or `.agentcortex-manifest`) protects only the docs/ branch. A project with its own `tools/validate.sh` and no Agentic OS marker therefore loses it. `deploy.ps1` delegates to `deploy.sh` (single implementation); nothing creates `$TARGET/.agentcortex` before the block. The framework wrappers never existed in this repo's history (removed before v5.4), so a content signature cannot be derived — gate on install evidence instead.
- MFR: (1) mkdir proj/tools; write own tools/validate.sh (2) `bash deploy.sh proj` (3) expected: file kept; actual: exit 0, "Migrating from legacy paths...", `[MIGRATE] removed legacy tools/validate.sh`, tools/ gone. Reproduced 2026-10-13 on 32bb1cc.
- plan: Target Files `.agentcortex/bin/deploy.sh`, `tests/ci/test_deploy_tiering.py`. Steps: 1 RED tests — AC-1 marker-less first install keeps tools/validate.{sh,ps1,cmd} byte-identical, exit 0, no [MIGRATE]/banner; AC-2 manifest-present target still removes wrappers; AC-3 pre-manifest `.agentcortex/` target still removes them (verify: new tests fail on 32bb1cc) · 2 deploy.sh: wrappers count as legacy only with prior-install evidence (`agentcortex/`, manifest, or `.agentcortex/`); outer gate, banner flag and rm use it (verify: new tests pass) · 3 mutate: drop the gate → AC-1 fails · 4 regression: test_deploy_tiering + test_deploy_dry_run_read_only (AC-4 dry run still reports legacy paths on an installed target) · 5 both validators. Risk+Rollback: Ref Known Risk. Confidence 93%.
- implement: RED first (AC-1 failed on 32bb1cc; AC-2/3 passed = preserved behaviour) → deploy.sh `_acx_legacy_tools` flag gates migration entry, banner and rm → GREEN. Mutant (prior-install condition → `true`) fails AC-1; restored byte-identical. Committed b8aff0f. ⚡ ACX
- review: Not Ready — fresh reviewer + Lite red team reproduced 2 CRITICAL: (1) the first install writes `.agentcortex-manifest`, so the next routine deploy treats it as prior-install evidence and deletes the project's tools/validate.* (exit 0); (2) a failed first install leaves `.agentcortex/` without a manifest, and the retry deletes them. MEDIUM: the AC-2 test fixture (wrapper written after an install) is indistinguishable from adopter files and pinned the bug. Routed back to implement.
- plan (revised, D-1): remove the tools/validate.* deletion entirely; drop tools/ from the migration gate, banner flag and dry-run text. AC-1 first install keeps · AC-2 install → own files → redeploy keeps · AC-3 failed-install residue (`.agentcortex/`, no manifest) → retry keeps · AC-4 dry run read-only.
- implement (resume): RED first (both new cases failed on b8aff0f = the reviewer's CRITICALs, reproduced independently) → removal, its gate, banner flag and dry-run mention deleted → GREEN. Committed 7511bb7. ⚡ ACX
- review: PASS on 32bb1cc..7511bb7 — fresh reviewer: AC-1..AC-4 + shell correctness ✅ PROVEN; old-vs-new matrix over 6 target states (first install, redeploy, failed-install residue, legacy agentcortex/, manifest-only, docs/context) deletes on old code, keeps on new. Lows applied in 1bff4a1 (legacy agentcortex/ test case; stale dry-run comment); CHANGELOG + backlog row → /ship; Info items pre-existing, untouched. Security: clean (change removes a deletion; no input handling, no secrets). Red Team Lite: see ## Red Team Findings. ⚡ ACX
- test: PR #467 CI @1bff4a1 18 pass / 0 fail / 1 skipped (Docs Content Pins, scope-gated; no docs touched). Downstream spot-check: A1 upgrade v1.8.32→candidate keeps own tools/validate.sh byte-identical, customized skill → .acx-incoming, downstream validate fail=0; A2 brownfield via deploy.ps1 keeps tools/validate.{sh,cmd} across install + redeploy, own CLAUDE.md kept (+ .acx-incoming). B behavioural A/B (claude -p, model claude-sonnet-5, hidden test): old v1.8.32 5/5 (56 turns, $1.30), new 5/5 (38 turns, $0.99); both quick-win, both read ADR-001 via the SSoT ADR Index; n=1, directional only — no regression.
- retro: Keep — refute/red-team round caught a CRITICAL the green tests had pinned as correct. Problem — first fix gated a deletion on a marker our own installer writes. Try — before gating any delete of an adopter path, ask whether the framework ever shipped that path; if not, delete the delete. Lessons: 1 (Work Log). Global Lessons at cap 20 with no LOW entry → retro.md has no rule for that case → backlog #229. ⚡ ACX
- ship: PASS — gate (receipts bootstrap/plan/implement/review/test present; security clean; D-1 → local). SSoT via guard 191→192 (Ship History entry, rotation of Ship-fix-dry-run-read-only-2026-09-27), backlog #220 → Shipped (resolution recorded) + #229, Work Log archived + INDEX chain entry. CHANGELOG lands in the v1.8.33 release PR. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T03:44:02Z
- Gate: plan | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T03:44:56Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T04:04:55Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-10-13T04:14:49Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T04:30:51Z
- Gate: review | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T04:46:58Z
- Gate: test | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T05:02:01Z
- Gate: ship | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-13T05:02:44Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #220 | reproduced 2026-10-05 |
| Spec | docs/specs/brownfield-first-install-preservation.md | #188, same data-loss class |
| ADR | docs/adr/ADR-005-downstream-file-preservation-tiering.md | file-preservation tiers |

---

## Known Risk

- A genuine legacy install without any marker would keep stale wrappers. Mitigation: prior-install evidence = `agentcortex/` dir, `.agentcortex-manifest`, OR an existing `.agentcortex/` dir (pre-manifest v6); a stale wrapper is harmless vs deleting adopter code.
- Root Cause: unconditional `rm -f tools/validate.*` behind a gate that admits marker-less targets.
- Rollback: `git revert` of the fix commit; adopters lose nothing either way (the fix only removes a deletion).

---

## Decisions

### D-1: Remove the tools/validate.* migration instead of gating it
- Decision: deploy.sh no longer deletes tools/validate.{sh,ps1,cmd} on any path.
- Reason: no install evidence proves file ownership (our own first install writes the manifest; a failed install leaves `.agentcortex/`). The public framework never deployed these wrappers: `c1ced66` (v5.4, initial public release) had only the removal code, and no `tools/` path exists in public history. So every deletion this step can still perform hits adopter files.
- Alternatives: content signature (`agentcortex` in the file) — rejected, because an adopter wrapper that calls `.agentcortex/bin/validate.sh` matches it; backup to `.acx-local` — rejected, because it still moves adopter files for no benefit.
- Impact: a pre-public install that still has stale wrappers keeps them (harmless unless run).
→ local

---

## Conflict Resolution

- systematic-debugging vs karpathy-principles: compatible — minimal fix + regression test.

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO

---

## Lessons

- [Category: deploy-ownership][Severity: HIGH][Trigger: gating-delete-of-adopter-path] An install marker (manifest, `.agentcortex/`) proves an install happened, never who owns a file — our own first install writes the manifest, so a marker-gated delete fires one run later. Before gating a delete of an adopter-visible path, check whether the framework ever shipped that path; if not, remove the delete (#220, same class as #188).

---

## Review Feedback

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| AC-1 | adopter tools/validate.* survive | ✗ UNPROVEN | survives run 1 only; reviewer repro `p1` run 2: "[MIGRATE] removed legacy tools/validate.sh" (manifest from run 1) |
| AC-2/3 | prior-install removal | ✗ UNPROVEN | the fixture equals adopter state after an install → the test pins the bug; failed-install residue repro `p3_docs` deletes on retry |

---

## Security Findings

none — the change only removes a deletion path in deploy.sh; no new input handling, no secrets, no new commands.

---

## Red Team Findings

- Lite (round 1, b8aff0f): CRITICAL ×2 (manifest from our own first install; failed-install residue) → resolved by D-1 in 7511bb7, verified by the round-2 old-vs-new matrix.
- Round 2 residual (pre-existing, not in diff): an unterminated legacy .gitignore block could strip a project's own `tools/validate.*` ignore line (deploy.sh strip table) — .gitignore only, never files; the dry-run "Legacy paths found" banner for a marker-less docs/context target. Risk decision: accept; not data loss.

---

## Design Reference

none

---

## Observability

none

---

## Resume

none

---

## Test Gate Results

- Test Files: tests/ci/test_deploy_tiering.py (new: test_first_install_keeps_projects_own_tools_validate, test_later_deploys_keep_projects_own_tools_validate ×3), tests/ci/test_deploy_dry_run_read_only.py
- Local: 71 passed, 2 skipped (deploy suites); CI @1bff4a1: Pytest (Windows) 1/2/3 + CI Structural + Framework Validation ×3 pass — 18 pass, 0 fail.

---

## Evidence

- RED @32bb1cc: `pytest test_deploy_tiering.py -k tools_validate` → 1 failed (AC-1: "tools/validate.sh: the project's own file must survive…"), 2 passed.
- GREEN: `pytest test_deploy_tiering.py test_deploy_dry_run_read_only.py` → 57 passed, 2 skipped (both skips pre-existing).
- Mutation: gate → `if true && \` ⇒ AC-1 `1 failed`; file restored (`cmp` equal).
- `bash -n deploy.sh` ok; shellcheck not local (CI job).
- Resume RED @b8aff0f: `-k tools_validate` → 2 failed (after-install, failed-install-residue), 1 passed.
- Resume GREEN @7511bb7: test_deploy_tiering + dry_run_read_only + deploy_brain_bootstrap + install_day_copy → 71 passed, 2 skipped (pre-existing).
