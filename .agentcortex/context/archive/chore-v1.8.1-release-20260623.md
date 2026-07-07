# Work Log: chore/v1.8.1-release

## Header

- Branch: `chore/v1.8.1-release`
- Classification: `quick-win`
- Classified by: `claude-sonnet-4-6`
- Frozen: `false`
- Created Date: `2026-06-23`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `91`

---

## Session Info

- Agent: `claude-sonnet-4-6`
- Session: `2026-06-23 UTC`
- Platform: `claude-code`
- Files Read: `12`

---

## Task Description

Cut the v1.8.1 patch release. Bumps version banners 1.8.0→1.8.1, adds CHANGELOG [1.8.1] section summarizing PRs #280-#284, adds Ship History ledger entry to current_state.md, increments Update Sequence 91→92.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-06-23 | quick-win, skipped SSoT/guardrails read |
| plan | done | 2026-06-23 | inline with implement (quick-win fast-path) |
| implement | done | 2026-06-23 | version banner bumps + CHANGELOG + SSoT ledger |
| review | skip | — | quick-win exempt |
| test | skip | — | quick-win exempt |
| handoff | skip | — | quick-win exempt |
| ship | in-progress | 2026-06-23 | — |

---

## Phase Summary

- bootstrap/plan/implement: bumped ACX_VERSION in deploy.sh, version+date in CITATION.cff, banners in 4 doc files, added CHANGELOG [1.8.1], added Ship History ledger entry, bumped SSoT Update Sequence 91→92.
- ship: [1-line summary pending]

---

## Gate Evidence

- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-23T00:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| PR | #280 | fix(eval): harden KB injection-decline oracle + live runner |
| PR | #281 | fix(governance): frozen-spec SSoT lifecycle cycle (ADR-010) |
| PR | #282 | docs(kb): honest absent-cost framing + changelog #273 + wiring probes |
| PR | #283 | feat(kb): consume optional schema-v4 manifest accelerators |
| PR | #284 | ci: shard Windows pytest job (pytest-split) |

---

## Known Risk

- Rollback = revert PR. No engine/test/logic change; doc/release only.

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

## Design Reference

none

---

## Observability

none

---

## Resume

none

---

## Evidence

- `bash -n .agentcortex/bin/deploy.sh` OK; version echo shows 1.8.1 (pending verification)
- `python -m pytest tests/ci/test_pre_commit_hook.py tests/ci/test_deploy_tiering.py -m "not slow" -q` green (pending)
- `git diff --check` clean (pending)
