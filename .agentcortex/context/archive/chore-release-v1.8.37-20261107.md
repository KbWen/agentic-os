# Work Log: chore/release-v1.8.37

## Header
- Branch: `chore/release-v1.8.37`
- Classification: `quick-win`
- Classified by: `claude`
- Frozen: `2026-11-07`
- Created Date: `2026-11-07`
- Owner: `claude`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `82203b5`
- Checkpoint SHA: `fc56ced`
- Recommended Skills: `verification-before-completion`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `222`

## Session Info
- Agent: `claude-opus-5-5`
- Session: `release-v1.8.37-20261107`
- Platform: `claude-code`

## Task Description
Cut v1.8.37 (owner asked in chat 2026-11-07 for the release, tag and GitHub Release). Packages #481, #484 and #485 since v1.8.36.

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-11-07 | quick-win release cut |
| plan | done | 2026-11-07 | banners + CHANGELOG + Ship History, then tag + release |
| implement | done | 2026-11-07 | fc56ced |
| ship | done | 2026-11-07 | SSoT 222->223 |

## Phase Summary
- bootstrap/plan: release cut per repo-gotchas §12; banner sites from tests/ci/test_release_version_consistency.py plus the INSTALL --ref example.
- implement: banners 1.8.36 → 1.8.37 (deploy.sh, TESTING_PROTOCOL ×2, antigravity runtime guide, CITATION version+date, AGENT_MODEL_GUIDE ×2, INSTALL --ref); CHANGELOG [1.8.37] with downstream delta from a real upgrade.
- ship: PASS; archive `.agentcortex/context/archive/chore-release-v1.8.37-20261107.md`; after merge: tag v1.8.37 + GitHub Release --latest.
⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-11-07T15:06:46Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-11-07T15:06:46Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-11-07T15:06:46Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-11-07T15:06:46Z

## External References
| Type | Path / URL | Notes |
|---|---|---|
| PR | #481, #484, #485 | contents |

## Known Risk
- Rollback: revert the release commit; delete tag/release only on owner request.

## Decisions
none

## Conflict Resolution
none

## Skill Notes
none

## Drift Log
none

## Review Feedback
none

## Red Team Findings
none

## Design Reference
none

## Observability
none

## Resume
none

## Test Gate Results
none

## Evidence
- `pytest tests/ci/test_release_version_consistency.py`: 2 passed.
- Real upgrade v1.8.36 → candidate (closeout tip, same content as main 82203b5 minus banners): 209 updated / 1 skipped (locally edited AGENTS.md → .acx-incoming) / 0 new / 0 removed; app.py, README.md, AGENTS.md hashes unchanged; downstream validate.sh pass=87 warn=1 fail=0 skip=8; C1 wording present in deployed skill.
- Demonstration: `bash .agentcortex/bin/deploy.sh <proj>` over a 1.8.36 install → "Summary: 209 updated / 1 skipped / 0 new / 0 removed".
