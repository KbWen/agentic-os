# Work Log: feat/brownfield-first-install-preservation

## Header

- Branch: `feat/brownfield-first-install-preservation`
- Classification: `feature`
- Classified by: `Codex (planning); resumed by Claude Opus 5.5`
- Frozen: `true`
- Created Date: `2026-10-05`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `a33cc1145901db0e063f670c33cccca945caf913`
- Checkpoint SHA: `e80f5ad`
- Recommended Skills: `karpathy-principles (auto), verification-before-completion (auto), systematic-debugging (auto), test-driven-development (auto), red-team-adversarial (auto, Full), production-readiness (auto), subagent-driven-development (auto), kb-consult (auto)`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `186`

## Session Info

- Agent: Claude Opus 5.5; Platform: claude-code (desktop)
- Session: `2026-10-05T08:24:28Z-claude-brownfield-exec`
- Scope (owner request in chat, 2026-10-05): execute spec `brownfield-first-install-preservation` through handoff; Codex final review before merge.
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 carried from planning session; Full mode.
- Override: none (both supported locations absent).
- Downstream-Capabilities: .agentcortex/context/private/downstream-capabilities.yaml (0 skills, subagent_policy=read-only, knowledge_sources: kb-main→OK@796bb16dadcc)
- Context Read Receipt: current_state.md (seq 186, Last Verified 2026-10-05); Work Log created (continuation of kbwen-main.md); Spec Scope: docs/specs/brownfield-first-install-preservation.md.

## Task Description

Backlog #188: on a first install (no manifest) a pre-existing, different core-tier file is overwritten with no backup. Fix: back up to `<path>.acx-local` before replacement, report it, fail closed on backup failure; amend ADR-005 + INSTALL.md. Canonical scope/AC/plan: the frozen spec.
Chain: /implement → /review → /test → /handoff → ship preparation (no merge).

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-05T08:15:21Z | Codex, kbwen-main.md; resumed by Claude 2026-10-05T08:24:28Z on task branch |
| plan | done | 2026-10-05T08:21:09Z | Codex; plan lives in the spec; owner approved + frozen 2026-10-05 |
| implement | done | 2026-10-05T08:35Z | TDD red 7/7 → green 7/7; 4 mutants killed |
| review | PASS (round 3) | 2026-10-05T08:52:23Z | 2 fresh reviewers (AC proof: PASS; pre-mortem: NOT READY) → routed back |
| test | done | 2026-10-05T09:32:34Z | local 56/2 skipped; CI 18 green on ddb1911 |
| handoff | done | 2026-10-05T09:32:57Z | PR #461 draft; Codex final review next |
| ship | pending | — | — |

## Phase Summary

- bootstrap: feature #188, resumed on task branch. ⚡ ACX
- plan: (Codex) 9 ACs; owner approved, spec frozen. ⚡ ACX
- implement: first-install core backup to .acx-local, fail-closed; ADR-005/INSTALL; TDD red→green, mutants killed. Confidence: 92% — high. ⚡ ACX
- review: Not Ready ×2 (doc/test gaps; Red Team HIGH → fail-closed AC-6) → fixed 744e031, ddb1911; round 3 PASS, security clean. ⚡ ACX
- test: local 56 passed/2 skipped; PR #461 CI green on ddb1911. ⚡ ACX
- ship: PASS — owner approved amended AC-6 + ship + merge in chat; SSoT seq 186→187; archive .agentcortex/context/archive/feat-brownfield-first-install-preservation-20261005.md. ⚡ ACX
- handoff: Open PR (draft #461); Codex final review + owner AC-6 confirmation before /ship. ⚡ ACX
- Detail: overflow archive (see Review Feedback).

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T08:15:21Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T08:21:09Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T08:52:16Z
- Gate: review | Verdict: NOT READY | Classification: feature | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-10-05T08:52:23Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T08:54:28Z
- Gate: review | Verdict: NOT READY | Classification: feature | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-10-05T09:07:08Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T09:10:16Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T09:23:09Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T09:32:34Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T09:32:57Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-10-05T11:30:04Z

## External References

- Spec: docs/specs/brownfield-first-install-preservation.md (frozen 2026-10-05).
- ADR: docs/adr/ADR-005-downstream-file-preservation-tiering.md (amend); ADR-008 also covers deploy.sh.
- Backlog: docs/specs/_product-backlog.md #188.
- Planning log: .agentcortex/context/work/kbwen-main.md (Codex, main).

## Known Risk

- Rollback: revert the squash commit of PR #461 (deploy.sh branch + tests + docs). Already-deployed adopters keep their `.acx-local` backups; restore = copy `<file>.acx-local` over `<file>`. Signal: deploy stderr `ERROR:` lines / `[OVERWRITE]` count; CI Deploy Smoke + brownfield tests green after revert.
- [process-batching][HIGH] mutation runs edit deploy.sh in place: done sequentially, restored from a scratch copy and verified by sha256 -c.

- Backup failure must precede live replacement; exercise with injected copy error.
- Latest-only `.acx-local`; refreshed on new collision (disclose, no history).
- CP_FLAG=-n/-i must not silently skip the backup.
- Untracked/ignored originals: backup is the only copy.

## Decisions

none

## Conflict Resolution

- Carried from planning: skills load at their own phases; sequential execution, no broad fan-out.

## Skill Notes

### test-driven-development — implement
- Checklist: red on baseline for the right reason (missing backup), not prerequisites; then minimal patch.
- Checklist: mutate the patch (ignore backup failure, backup-after-copy, always-claim, CP_FLAG skip) — each must fail a test.
- Constraint: minimal source fixture so per-file path runs on Windows too (real-repo per-file costs 10+ min).

### karpathy-principles — implement
- Checklist: one branch of `_deploy_file_now` changed; no extraction/refactor of the update branch.
- Checklist: every line maps to AC-1..AC-9.
- Constraint: no new tier, flag, dependency, or backup history.

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Continued from kbwen-main.md (planning on `main`): moved to task branch per spec §Execution step 1; bootstrap+plan receipts carried verbatim from that log (phases ran under Codex), not re-issued.
- Spec status draft → frozen on owner approval (chat, 2026-10-05).
- Backlog #188 Pending → In Progress (bootstrap §1 step 5).
- AC-6 amendment and ship/merge: owner decisions in chat 2026-10-05 after the Codex final review; see PR #461 description. Merge gated on all-green CI.
- AC-30 routing: 7 pending routing_actions target document-governance/tooling/testing/governance logs (#201 Non-goal with its own PR #451; worklog keys, receipt labels, quick-win checks, look-timing, token map) — none concern this task's files; deferred to their own rows.
- Codex final review: PASS on e80f5ad (.agentcortex/context/private/pr-461-codex-final-review.md); no new defect.
- ADR Coverage Check: check_adr_coverage.py --paths deploy.sh test_deploy_tiering.py → exit 0, covered by ADR-005 (+ADR-008 for deploy.sh).
- Frozen-spec metadata: added `signal_tier: none` (no new governance rule) for the validator's §13 WARN.
- Frozen-spec edit: AC-6 + Domain Decisions + Risks amended (dated) after owner delegated the Red Team HIGH decision in chat (2026-10-05).
- Receipt correction: implement receipt first written with an estimated timestamp; replaced with clock time before any further phase, and the NOT READY receipt re-stamped so order and time agree.

## Security Findings

- /review security scan (A01–A03, secrets) on all changed files, 3 rounds: clean. New code: `[ -e ]`/`[ -L ]` tests + stderr echo of deploy's own relative paths; CP_FLAG stays whitelisted; no secrets.

## Review Feedback

Compacted: 2026-10-05, archive: .agentcortex/context/archive/work/feat-brownfield-first-install-preservation-20261005.md (round 1-3 adjudication: 5 do-now fixed in 744e031, Red Team HIGH fixed fail-closed in ddb1911, #220/#221 filed, LOWs closed with rationale; [NEEDS_HUMAN] owner confirms amended AC-6).

## Red Team Findings

- HIGH (pre-mortem): interrupted first install retried from a newer source could overwrite the .acx-local holding the original. Decision: owner delegated → fixed fail-closed in ddb1911 (AC-6 amended); verified round 3. Detail: overflow archive (see Review Feedback).

## Design Reference

none

## Observability

- Sink: deploy.sh stdout (`[OVERWRITE]`/`[KEPT]` + summary) and stderr (`ERROR:` + nonzero exit) | Scope: .agentcortex/bin/deploy.sh `_deploy_file_now` | Verified: yes (tests assert both streams). CLI tool; no telemetry by design.

## Resume

- State: HANDEDOFF — draft PR #461 (head e80f5ad; code final at ddb1911), CI green; NOT merged, NOT shipped.
- Completed: implement → review (3 rounds, PASS) → test → handoff; backlog #220/#221 filed.
- Next: Codex final review of PR #461 → owner confirms amended AC-6 → /ship (SSoT Ship History, backlog #188 Shipped, archive log) → merge.
- Context: first install backs up differing core files to .acx-local, fails closed on backup failure or an existing .acx-local; updates unchanged.

### Read Map
- docs/specs/brownfield-first-install-preservation.md → AC table (AC-6 amended), Domain Decisions
- .agentcortex/bin/deploy.sh → `_deploy_file_now` fresh-install core `else` branch
- tests/ci/test_deploy_tiering.py → `brownfield` section
- docs/adr/ADR-005-downstream-file-preservation-tiering.md → Amendment 2026-10-05; docs/INSTALL.md:40-42
- This log → Red Team Findings, Test Gate Results, Evidence; overflow archive/work/feat-brownfield-first-install-preservation-20261005.md

### Skip List
- kbwen-main.md — planning only, carried here.
- Update branch / scaffold branches of deploy.sh — unchanged.

### Context Snapshot
Pre-existing core collision on a no-manifest run: guard existing .acx-local (stop) → plain cp backup (stop on failure) → CP_FLAG live copy → post-copy hash decides [OVERWRITE] vs [KEPT]. Tiers, manifest, hashing, deploy.ps1 untouched. Not fixed (filed): legacy migration deletes tools/validate.* (#220); CP_FLAG -i queue / -n update claim (#221).

### Backlog Status
- Active Backlog: docs/specs/_product-backlog.md; #188 In Progress → Shipped at /ship.
- New: #220 (P1), #221 (P2), both review-finding Pending.

## Test Gate Results

- HEAD ddb1911. Test Files: tests/ci/test_deploy_tiering.py (10 `brownfield` tests), tests/ci/test_deploy_dry_run_read_only.py, tests/ci/test_deploy_install_day_copy.py.
- Local (Windows, Python 3.14.3, pytest 8.4.1, Git Bash 5.2): `pytest tests/ci/test_deploy_tiering.py tests/ci/test_deploy_dry_run_read_only.py tests/ci/test_deploy_install_day_copy.py -q -rs` → 56 passed, 2 skipped (coreutils hazard absent; MSYS awk CR per-file case) in 8m39s.
- CI PR #461 on ddb1911: 18 pass / 1 skipping (Docs Content Pins, scope) / 0 fail / 0 pending — incl. CI Structural Tests (full Linux suite), Pytest (Windows) ×3, Framework Validation ×3, Deploy Smoke ×2, ShellCheck, Semgrep, TruffleHog.
- AC coverage: AC-1/2/3/5 first_install_backs_up[batch,per-file]; AC-4 backup_failure[batch,per-file]; AC-6 existing_backup_stops[batch,per-file] + interrupted_retry + cp_flag[default,cp-n]; AC-7 parametrization + via_deploy_ps1; AC-8 regression above; AC-9 docs_pin 12 + reviewer line-by-line.
- Adversarial: mutants M1–M6 each killed (Evidence).

## Evidence

- Baseline: main a33cc1145901db0e063f670c33cccca945caf913; branch created with carried admin diff (SSoT Last Verified, guard receipt) + untracked spec.
- Red (baseline a33cc11 + new tests): `pytest tests/ci/test_deploy_tiering.py -k brownfield` → 7 failed; reasons: `.acx-local` FileNotFoundError ×3, backup bytes mismatch ×2, shim never reached (no backup attempted) ×2. Every deploy itself exited 0 (not a prerequisite failure).
- Shim fix: Git for Windows bash launcher prepends /mingw64/bin:/usr/bin to PATH, so the failure test injects `cp` via BASH_ENV (test-only).
- Green (5c0f1e5): same command → 7 passed in 36s.
- Mutants (deploy.sh restored, `sha256sum -c` OK): M1 ignore backup failure → 2 failed; M2 backup after live copy → 2 failed; M3 always print OVERWRITE → cp-n failed; M4 backup with CP_FLAG/no rm → cp-n failed.
- `git diff --check` 0; lifecycle frontmatter 14 PASS/0 WARN/0 FAIL; `-m docs_pin` 12 passed.
- Review-fix round (744e031): brownfield 7 passed; M5 bare-cp (no ERROR handler) now caught → 2 failed; deploy.sh restored + sha256 -c OK; docs_pin 12 passed.
- Primary re-ran 2 pre-existing findings on main's code path: legacy migration removed adopter `tools/validate.sh` (rc 0, `[MIGRATE] removed legacy tools/validate.sh`) → #220; `CP_FLAG=-i` batch: 11 manifest rows vs 12 control, rc 0 → #221.
- Fail-closed round (ddb1911): new tests red first (existing-backup ×2: rc 0 instead of stop; interrupted-retry story: original bytes gone) → green 10 passed; M6 guard removed → 3 failed; deploy.sh restored + sha256 -c OK; docs_pin 12; lifecycle 14/0/0.
- Final (after last log write, HEAD e80f5ad): validate.sh exit 0 pass=116 warn=5 fail=0 skip=2; validate.ps1 (PS 5.1) exit 0, identical tally; 5 WARN pre-existing (same set as v1.8.30 ship); `git diff --check a33cc11..HEAD` 0.
- KB kb-main: manifest schema_version=7, kb_version 796bb16dadcc, git status `main...origin/main` clean.
