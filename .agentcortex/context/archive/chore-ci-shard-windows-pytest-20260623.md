# Work Log: chore/ci-shard-windows-pytest

## Header

- Branch: `chore/ci-shard-windows-pytest`
- Classification: `quick-win`
- Classified by: `Claude (Opus 4.8)`
- Frozen: `true`
- Created Date: `2026-06-23`
- Owner: `claude-ci-shard`
- Guardrails Mode: `Quick`
- Current Phase: `implement`
- Checkpoint SHA: `e22eb6f`
- Recommended Skills: `none`
- Primary Domain Snapshot: `ci/test-infra`
- SSoT Sequence: `90`

---

## Session Info

- Agent: `Claude (Opus 4.8)` — autonomous test-perf follow-up (Codex review MEDIUM FOLLOW-UP)
- Session: `2026-06-23T06:00:00+00:00`
- Platform: `Claude Code`
- Context Read Receipt: SSoT seq 90; required-checks API (3 required: Framework Validation/ShellCheck/Check Markdown Links — Pytest Windows + CI Structural NON-required); pytest-split research

## Task Description

Codex review's pytest-perf MEDIUM FOLLOW-UP. Investigation outcome (evidence-based):
- pytest-xdist `-n auto` MEASURED slower (test_deploy_tiering 34 min vs ~13 min serial) — single-machine contention on a subprocess/IO-bound suite. REJECTED.
- The slow `Pytest (Windows)` job (~8:26) is NON-required → sharding it is low-risk (no branch-protection footgun) AND it doesn't actually block merge.
- Fix: shard the Windows pytest job across 3 parallel matrix runners via pytest-split (separate machines → no contention).

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | complete | 2026-06-23 | quick-win; research + required-checks verified |
| plan | complete | 2026-06-23 | pytest-split 3-way shard on test-windows; pinned dep; count-split first |
| implement | complete | 2026-06-23 | commit e22eb6f; pytest-split==0.11.0 + matrix; YAML valid; 3-way split 199/199/198 |
| ship | pending | — | PR #284; measuring per-shard times before merge |

## Drift Log

- Skip Attempt: NO
- Token Leak: NO
- Approach pivot (evidence): xdist→REJECTED (measured slower); chose pytest-split sharding after verifying required-checks make it low-risk. See [[project_kb_seam_v181_hardening]] pytest-perf note.

## Plan

- Goal: cut the Windows pytest wall-clock without single-machine contention or breaking branch protection.
- Non-goals: changing test logic/fidelity; touching the required checks; promoting tests to required (separate decision).
- Blast Radius: `.github/workflows/validate.yml` (matrix test-windows) + `.github/requirements-ci.txt` (pin pytest-split). NOT deployed downstream (deploy.sh ships no .github/workflows or tests/ — confirmed).
- Verification: this PR's own CI runs the sharded jobs (heavy=true since .github/* changed); measure per-shard times vs the 8:26 baseline; if uneven, add a `.test_durations` file.
- Rollback: revert PR.

## Phase Summary

- bootstrap: quick-win; the pytest-perf follow-up; verified required-checks (3 fast ones; the pytest jobs are non-required).
- plan: shard test-windows 3-way via pytest-split; pin the dep; even count-split first, durations later if needed.
- implement: `requirements-ci.txt` += `pytest-split==0.11.0`; `validate.yml` test-windows gains `strategy.matrix.group:[1,2,3]` + `--splits 3 --group`; YAML valid; full-set collection splits 199/199/198.

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T06:00:00+00:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T06:05:00+00:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T06:15:00+00:00

## Evidence

- pytest-xdist measurement: `test_deploy_tiering.py -n auto` → 2039s (34m), vs ~13m serial — REJECTED.
- pytest-split local verify: 0.11.0; full set splits 199/199/198 (collect-only); group runs deselect the others.
- Required checks (API): `Framework Validation`, `ShellCheck`, `Check Markdown Links` only → test-windows non-required.
- YAML valid (`yaml.safe_load`); test-windows strategy = {fail-fast:false, matrix.group:[1,2,3]}.
- Downstream: `deploy.sh` ships no `.github/workflows/*` or `tests/` → zero downstream impact (forks only).

## Security Findings

none

## Resume

none
