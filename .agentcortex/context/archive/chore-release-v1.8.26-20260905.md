# Work Log: chore/release-v1.8.26

## Header

- Branch: `chore/release-v1.8.26`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-09-05`
- Created Date: `2026-09-05`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `0b08cb5`
- Checkpoint SHA: `none`
- Recommended Skills: `verification-before-completion, karpathy-principles`
- Primary Domain Snapshot: `release metadata`
- SSoT Sequence: `168`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-09-05 14:30 UTC`
- Platform: `claude-code`
- Files Read: `6`

---

## Task Description

Cut release v1.8.26. Bump the seven canonical version surfaces plus `CITATION.cff` `date-released`, and write the CHANGELOG entry for the three units merged since v1.8.25 (#183, #398, #433). No engine, gate, or configuration change.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-05 | quick-win, matching `chore/release-v1.8.23` precedent |
| plan | done | 2026-09-05 | 8 surfaces + CHANGELOG; downstream delta measured first |
| implement | done | 2026-09-05 | version bump + CHANGELOG entry |
| review | n/a | — | quick-win: optional, evidence inline |
| test | n/a | — | quick-win: optional, evidence inline |
| handoff | n/a | — | quick-win exempt |
| ship | pending | — | — |

---

## Phase Summary

**bootstrap/plan** — Classified `quick-win` on the `chore/release-v1.8.23` precedent (same shape, same archive header). The plan step that mattered was measuring the adopter delta **before** writing the notes rather than describing the release from its commit list: `git diff --name-only v1.8.25..HEAD` intersected with the deploy manifest golden gives **6 of 26** changed files actually reaching an adopter. That number, not the 14-commit log, is what the Downstream delta paragraph states.

**implement** — Seven version surfaces plus `CITATION.cff date-released` bumped 1.8.25 → 1.8.26 / 2026-08-27 → 2026-09-05, each by an asserted single-occurrence replace. CHANGELOG entry written in house format. The release notes lead with the one instruction an adopter must act on: **re-run the INSTALL copy**, because `.githooks/pre-commit` is a user-made copy `deploy.sh` never rewrites — without that line the release would claim a fix most existing adopters do not have, which is the same over-promise class this release fixes.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-05T14:30:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-05T14:35:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-05T14:45:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| PR | https://github.com/KbWen/agentic-os/pull/433 | the security fix this release carries |
| Backlog | `#195` / `#196` / `#197` / `#194(b)-(h)` | named in the release notes as NOT done |
| Guard | `tests/ci/test_release_version_consistency.py` | pins all 8 surfaces to `deploy.sh` |

---

## Known Risk

- The hook fix does not reach an already-installed `.githooks/pre-commit`. Mitigated only by the release notes; the mechanical fix is filed as **#197**, not attempted here.
- Rollback: revert the version bump commit; no state migration. The tag/Release are the only non-git artifacts and are created after merge.

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

none

---

## Review Feedback

none

---

## Red Team Findings

none

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

none

---

## Evidence

- **Adopter delta measured, not assumed**: `git diff --name-only v1.8.25..HEAD` = 26 files; intersected with `deploy_manifest_golden.txt` = **6** — `.githooks/pre-commit.guard-ssot.sample`, `credential_floor.sh`, `credential_floor.ps1`, `scan_credentials.py`, `repo-gotchas.md`, `current_state.md` (scaffold, adopter copy preserved). `run_skill_eval.py` and `eval/skills.yaml` are **not** in the deploy set (grep count 0), so #398's suite is upstream-only.
- Release guard `tests/ci/test_release_version_consistency.py`: **2 passed** after the bump.
- Version-sensitive subset run locally: `test_release_version_consistency.py` + `test_deploy_tiering.py` + `test_pre_commit_hook.py` -> **47 passed, 1 skipped** (9:41). This is a **subset, not CI-equivalent** - the full 947-test suite runs on CI's three Windows shards, which is the real environment for it; no local full-suite claim is made for this cut.
- Stale-version sweep after the bump: the only surviving `1.8.25` outside `CHANGELOG.md`/archive is inside the v1.8.25 Ship History entry, which `ship.md` forbids editing. Correct to leave.
