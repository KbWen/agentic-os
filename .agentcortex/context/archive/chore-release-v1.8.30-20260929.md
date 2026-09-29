# Work Log: chore/release-v1.8.30

## Header

- Branch: `chore/release-v1.8.30`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-29`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `11b5851`
- Checkpoint SHA: `11b5851`
- Recommended Skills: `verification-before-completion`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `185`

## Session Info

- Agent: `claude-opus-5-5` · Session: `2026-09-29T03:00:00Z` · Platform: `claude-code` (desktop)
- Override: none
- Downstream-Capabilities: `.agentcortex/context/private/downstream-capabilities.yaml` (knowledge_sources: kb-main→OK@[redacted])
- Guardrails loaded: skipped (quick-win)

## Task Description

Cut v1.8.30: packages #457 (KB-declared anchors, additive schema_version, visible UNREADABLE / off-main lines) and #458 (optional `KB:` chat-template line), after an owner-requested end-to-end read-path check.

## Phase Sequence

| Phase | Status |
|---|---|
| bootstrap/plan/implement | done |
| ship | done |

## Phase Summary

- bootstrap: quick-win release cut (version surfaces + CHANGELOG + Ship History), same shape as v1.8.29.
- plan: bump the 7 guarded version surfaces 1.8.29→1.8.30, CITATION date → 2026-09-29, CHANGELOG `[Unreleased]` → `[1.8.30]` + e2e note, backlog #218 cost note, Ship History. Rollback: revert the squash commit; delete tag/release if already cut. Confidence: 95%.
- implement: surfaces bumped; CHANGELOG cut; #218 note.
- ship: SSoT 185→186 + Ship History (oldest rotated); after merge: tag `v1.8.30` + `gh release create --latest` (repo-gotchas §12).

⚡ ACX

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-29T03:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-29T03:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-29T03:00:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-29T03:00:00Z

## External References

- PR #457, PR #458

## Known Risk

- Release steps after merge are manual (tag + GitHub Release). Rollback: revert the squash commit.

## Decisions

none

## Conflict Resolution

none

## Skill Notes

none

## Drift Log

- Receipts written together at release cut (single-turn quick-win), as in v1.8.29.

## Security Findings

none

## Evidence

- End-to-end KB read check before release (4 unprimed sessions, sonnet ×2 + opus ×2, deployed fixture project, real KB): 4/4 consulted the right standard via its digest (never the page), sha-checked, risks section only; 0/4 read the irrelevant second routed page; 0/4 misled; plans visibly improved. ~5–7K KB tokens per consult (~1.3K guidance, ~3K routing table).
- Version surfaces: 7 files 1.8.29→1.8.30 (exactly one match each); guarded by tests/ci/test_release_version_consistency.py.
