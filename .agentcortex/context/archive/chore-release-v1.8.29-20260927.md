# Work Log: chore/release-v1.8.29

## Header

- Branch: `chore/release-v1.8.29`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-27`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `4413f2b`
- Checkpoint SHA: `4413f2b`
- Recommended Skills: `verification-before-completion (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `182`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-27T14:16:34Z`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

Cut v1.8.29 from main 4413f2b: the seven canonical version surfaces plus CITATION date, and a CHANGELOG entry for #452 (#215) and #453 (#216), leading with the one-time upgrade step for clones checked out under the old repo-wide `.gitattributes`. After merge: lightweight tag v1.8.29 and `gh release create --latest` (repo-gotchas §12).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-27T14:16:34Z | quick-win (release chore) |
| plan | done | 2026-09-27T14:16:34Z | bump.py + CHANGELOG |
| implement | done | 2026-09-27T14:16:34Z | — |
| ship | done | 2026-09-27T14:16:34Z | SSoT 182->183 |

---

## Plan

- `scratchpad/ds/rel129/bump.py`: each surface replaced by an asserted single occurrence; CHANGELOG entry prepended (downstream delta measured: 4 of 17 changed files reach an adopter).
- Verify: `test_release_version_consistency.py`, docs pins; CI on the PR.

---

## Phase Summary

- bootstrap: quick-win release chore. ⚡ ACX
- plan: version surfaces + CHANGELOG | Confidence: 95% — high
- implement: 7 surfaces + CITATION date, CHANGELOG (PRs #452, #453; delta 4/17) | Confidence: 97% — high
- ship: PASS; Ship History + rotation; archive MOVE; INDEX; tag + GitHub Release after merge. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T14:16:34Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T14:16:34Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T14:16:34Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T14:16:34Z

---

## Known Risk

- Tag and GitHub Release are separate steps after the merge; the release is not done at merge (repo-gotchas §12).
- Rollback: revert the release PR; delete the tag only with the owner's confirmation.

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

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO

---

## Evidence

- Demonstration: `git diff --name-only v1.8.28 HEAD` = 17 files; 4 reach an adopter: core `deploy.sh`, `validate.sh`; scaffold `.gitattributes` (installed from the new template) and `.agentcortex/templates/downstream.gitattributes`. `current_state.md` excluded: it deploys from the unchanged template.
- `test_release_version_consistency.py` 2 passed; `pytest tests/ci -m docs_pin` 12 passed. Full suite: the release PR's CI.
