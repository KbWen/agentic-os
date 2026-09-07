# Work Log: dependabot/github_actions/trufflesecurity/trufflehog-3.97.1

## Header

- Branch: `dependabot/github_actions/trufflesecurity/trufflehog-3.97.1`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-09-07`
- Created Date: `2026-09-07`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `14b53ad`
- Checkpoint SHA: `9dee106`
- Recommended Skills: `none`
- Primary Domain Snapshot: `ci-security`
- SSoT Sequence: `169`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-09-07 UTC`
- Platform: `claude-code`
- Files Read: `14`

---

## Task Description

Complete dependabot PR #425. The bump moved the TruffleHog **wrapper** action SHA to v3.97.1 but left the `with: version:` scanner image digest on v3.96.0's, so merging as-delivered would upgrade nothing that executes. Adds the missing digest, plus the drift test the spec's own risk row had assigned to a human.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-07 | quick-win; SSoT read, guardrails skipped per CLAUDE.md step 4 |
| plan | done | 2026-09-07 | 3 targets: security.yml digest+comment, new drift test, spec sync |
| implement | done | 2026-09-07 | all 3 landed |
| review | skipped | — | quick-win exempt; mutation discrimination run instead |
| test | done | 2026-09-07 | PR CI full suite (Windows shards 1-3) green; local run not claimed |
| handoff | skipped | — | quick-win exempt per AGENTS.md §Delivery Gates |
| ship | done | 2026-09-07 | SSoT + Ship History (rotated) + archival |

---

## Phase Summary

**bootstrap → plan**: Triage of three open PRs surfaced #425 as a half-bump. Verified against ground truth rather than the PR body: `20652fbb…` dereferences to tag `v3.97.1` and `6f3c981e…` to `v3.96.0` (GitHub refs API); GHCR resolves tag `3.96.0` to `aa821cf4…` — byte-identical to the digest the workflow pins — and tag `3.97.1` to `deb2af10…`. Both digests are `manifest.list.v2` over `linux/amd64`+`linux/arm64`, so the swap is shape-preserving. `action.yml` at both SHAs still composes `"${IMAGE}:${VERSION}"`, so the digest-pin construction survives the bump.

**implement**: Digest and provenance comment moved to v3.97.1, with an inline note that the two fields must move together. Added `test_ac5_trufflehog_wrapper_and_digest_agree_on_release`, comparing the release named by the `uses:` comment against the one named by the digest comment. Synced `docs/specs/ci-security-scanning.md` AC-5 and its scanner-freshness risk row: the row previously mitigated this exact failure with a human cadence ("review the pin whenever Dependabot bumps the wrapper SHA"), which failed on first contact — #425 sat open a week with the halves disagreeing and nothing objected.

**test**: See `## Evidence`. Mutation discrimination confirms the new test isolates the drift: reverting only the digest half fails 1 of 43, and that one.

**Scope note**: the new test is deliberately NOT a revival of the comment-equality-as-provenance design that backlog #166 withdrew. It binds the *automated bump path* only; two hand edits still pass it, and both the test docstring and AC-5 say so. Immutability of what executes remains carried by the digest form alone.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-07T02:10:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-07T02:25:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-07T02:50:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-07T14:05:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/ci-security-scanning.md | AC-5 + scanner-freshness risk row amended |
| ADR | — | — |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/425 | dependabot bump completed in place |

---

## Known Risk

- The drift test compares two editable comments. A hand-edited `uses:` SHA with a stale comment, or a comment advanced without substituting the digest, still passes. Mitigation: `test_ac5_trufflehog_scanner_pinned_by_digest` remains the binding assertion; both holes are named in the new test's docstring and in AC-5, not left implicit.
- Detector-freshness lag is unchanged by this work — the digest still only moves when a human moves it.

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

- Scope grew from "update the digest" to include a regression test and a spec sync. Justification: the spec's own mitigation for this failure was an honour-system human cadence that had already failed once; leaving it unenforced would restate a control the repo does not have.

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

- `python -m pytest tests/ci/test_security_workflow.py -q` -> 43 passed (42 before this change; the +1 is the new test)
- `bash .agentcortex/bin/validate.sh` -> exit 0 throughout. Warn count moved 6 -> 5 -> 4 across three runs; **both deltas were self-inflicted by this log, and each was reproduced before being claimed**:
  - `Checkpoint SHA: pending` -> `[WARN] work logs with missing/invalid Checkpoint SHA field...`. The template contract is `<git-sha or none>`; `pending` is neither. Reproduced by setting it back: `pass=116 warn=5` vs `pass=117 warn=4`, single-warn diff.
  - A ship receipt written into `## Gate Evidence` before ship happened -> `[WARN] shipped work logs still in active work/ directory`. Receipt withdrawn; it gets written when ship actually completes.
  - Residual 4 warns all pre-date this branch (3 historical archived-log gate gaps, backlog label vocabulary 16>15, governance eval coverage). Baseline, not this task's.
  - A first hypothesis — that a check was working-tree-dirty sensitive — was **refuted** by experiment (tree dirtied via `git checkout HEAD~1 -- <3 files>`, restored after: `pass=117 warn=4`, identical). Recorded because the wrong hypothesis was reported to the user before it was tested.
- **Runtime proof the fix works, from PR #425 CI run 34127184393** (`Secret Detection (TruffleHog)`): the step logged `Pulling from trufflesecurity/trufflehog` at `Digest: sha256:deb2af10...`, then `finished scanning ... "trufflehog_version": "3.97.1"`. The scanner that executed is 3.97.1 — before this commit the same job would have run 3.96.0 under a wrapper labelled v3.97.1. This is the same evidence class backlog #166 used to prove the original unpin, taken from the job log rather than inferred from the config.
- PR #425 CI: 18 pass, 1 skip (Docs Content Pins, not applicable), 0 fail.
- Full suite: ran on PR #425 CI as `Pytest (Windows)` shards 1-3, all green — the real environment for it. A local run was still in flight at ship and **is not claimed**, following the v1.8.26 precedent of recording a subset as a subset.

---

## Evidence

- Tag -> commit, via GitHub refs API: `v3.97.1 -> 20652fbb…` (the SHA dependabot wrote), `v3.96.0 -> 6f3c981e…` (the SHA it replaced). Pin is legitimate.
- Tag -> GHCR digest: `3.96.0 -> sha256:aa821cf4…` (equals the digest the workflow pinned before this change), `3.97.1 -> sha256:deb2af10…`. Confirms the delivered bump left the scanner on 3.96.0.
- Both digests: `mediaType: application/vnd.docker.distribution.manifest.list.v2+json`, platforms `linux/amd64`, `linux/arm64`. Shape-preserving swap.
- `action.yml` at both SHAs: `docker run … "${IMAGE}:${VERSION}"` unchanged, so the digest-composition pin still holds at v3.97.1.
- Mutation discrimination — reverting the digest+comment half to v3.96.0 while leaving the wrapper at v3.97.1 (i.e. the PR exactly as dependabot delivered it):
  `1 failed, 42 passed` — `test_ac5_trufflehog_wrapper_and_digest_agree_on_release`, `AssertionError: '3.97.1' != '3.96.0'`. Restored -> `43 passed`.
