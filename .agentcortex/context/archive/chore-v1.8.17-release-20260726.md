# Work Log: chore/v1.8.17-release

## Header

- Branch: `chore/v1.8.17-release`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-07-26`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `4ae078cf565e83888814d46b7ab2a7a200621ca5`
- Checkpoint SHA: `4ae078cf565e83888814d46b7ab2a7a200621ca5`
- Recommended Skills: `verification-before-completion (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `135`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-07-26 (claude-code 2.1.160)`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

Release cut for **v1.8.17**, packaging the four PRs merged since `v1.8.16`: #364 (repo-gotchas
surface), #365 (backlog #146 locale-independent subprocess decoding), #366 (gotcha #13
refresh), #367 (backlog #145 conflicting-directive scan). Docs-only chore — version banners
across the 7 canonical files, CHANGELOG `[1.8.17]`, SSoT Ship History entry. **No engine,
test, or logic change in the release cut itself.**

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-26 | quick-win release chore |
| plan | done | 2026-07-26 | 7 banners + CHANGELOG + SSoT |
| implement | done | 2026-07-26 | all 8 files bumped |
| review | skipped | — | optional for quick-win |
| test | skipped | — | docs-only; packaged PRs each CI-green at merge |
| handoff | skipped | — | exempt (quick-win) |
| ship | done | 2026-07-26 | PR + tag + gh release |

---

## Phase Summary

- bootstrap: `quick-win` release chore, unchanged tier.
- plan: bump the 7 canonical banner files + CHANGELOG, add the SSoT Ship History entry,
  rotate the oldest out. | Confidence: 95% — high.
- ship: banners verified by grep (0 residual `1.8.16` in the canonical set, `1.8.17` present in
  8 files incl. CHANGELOG). Tag + GitHub Release are the manual steps this repo has forgotten
  **twice** — done explicitly, not assumed.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T08:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T08:02:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T08:10:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T08:20:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| PR | https://github.com/KbWen/agentic-os/pull/364 | repo-gotchas surface |
| PR | https://github.com/KbWen/agentic-os/pull/365 | backlog #146 |
| PR | https://github.com/KbWen/agentic-os/pull/366 | gotcha #13 refresh |
| PR | https://github.com/KbWen/agentic-os/pull/367 | backlog #145 |

---

## Known Risk

- Docs-only chore; no engine change. Rollback = revert the release PR, delete the tag, delete
  the GitHub Release.
- The release is NOT complete at merge: the lightweight `v1.8.17` tag and
  `gh release create --latest` are manual and have been forgotten twice historically.

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

- Docs-only release chore. All four packaged PRs were individually CI-green at merge (18 checks
  each). `validate.sh` re-run on the release head recorded below.

---

## Evidence

- Banners bumped in the 7 canonical files + CHANGELOG: `deploy.sh` `ACX_VERSION`, `CITATION.cff`
  (`version` + `date-released: 2026-07-26`), Model Guide EN + zh-TW, Testing Protocol EN +
  zh-TW, `antigravity-v5-runtime.md`.
- Grep verification: **0** residual `1.8.16` across the canonical set; `1.8.17` present in 8
  files.
- Local full CI-equivalent suite on the packaged content: **808 passed** (run before the
  release cut, on `4ae078c`).

## Security Findings

none — docs-only version bump; no code, no dependency, no credential surface touched.
