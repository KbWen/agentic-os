# Work Log: codex/docs-design-onboarding -- release follow-up

## Header
- Branch: `codex/docs-design-onboarding`
- Classification: `quick-win`
- Classified by: `Codex`
- Frozen: `2026-10-28`
- Created Date: `2026-10-28`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `9d633453e9ba991f929b81f785c284a53b3e31a4`
- Checkpoint SHA: `3ef05f5ccd95f4b29bde765016ecc42ed4c8fa86`
- Recommended Skills: `karpathy-principles, verification-before-completion, subagent-driven-development, systematic-debugging`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `218`

## Session Info
- Agent: Codex; platform: codex-app; session: codex-design-publish-20261028.
- User explicitly authorized PR -> wait for CI -> merge -> next patch GitHub Release on 2026-10-28. A only; B/C excluded.
- Recovered: prior local-delivery log archived at .agentcortex/context/archive/codex-docs-design-onboarding-20261028.md. This is a NEW release follow-up unit; historical receipts are not fabricated/copied.
- Baseline: clean 9d63345; main origin fetched; current latest GitHub release v1.8.35. Next patch v1.8.36.
- Guardrails loaded earlier in session; quick-win embedded workflow rules apply. Existing skills cached from original unit; review uses fresh agent with diff/AC/standards only.
- Override/preferences: absent at session start. Present local KB declared; previous source design-resource-adoption boundary advisory applies, no new gate.

## Task Description
Verify and publish A as v1.8.36 through a CI-green PR, tag and latest Release; B/C excluded.

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-28 | Release unit. |
| plan | done | 2026-10-28 | A verification + v1.8.36. |
| implement | done | 2026-10-28 | Metadata/README. |
| review | done | 2026-10-28 | Fresh A PASS. |
| test | returned | 2026-10-28 | CI runner setup failure. |
| implement | done | 2026-10-28 | 3.9 runner repair. |
| review | done | 2026-10-28 | Fresh delta PASS. |
| test | done | 2026-10-28 | Full CI b34d350 PASS. |
| implement | done | 2026-10-29 | Date finalization. |
| review | done | 2026-10-29 | Exact date delta PASS. |
| test | done | 2026-10-29 | 17 checks; source validator; post-sync 2 checks PASS. |
| ship | done | 2026-10-29 | Records archived; remote publication follows final CI. |

## Phase Summary
- ship: v1.8.36 records prepared; PR #480 final-head CI, merge, tag and GitHub Release remain explicit publication steps. Confidence: 95%. ⚡ ACX
- test finalization: prior full CI PASS plus final date-only delta 17 tests PASS, tree 85e354de. Final archived PR head must pass all CI again before merge. ⚡ ACX
- test: exact-head full Ubuntu/three-Windows CI PASS at b34d350, statistics in Evidence. ⚡ ACX
- review correction: fresh static reviewer PASS; only supported runner image changes, checks preserved. Full execution belongs to test phase. ⚡ ACX
- implement correction: only Python 3.9 runner image pinned to supported 24.04 and changelog note; all checks retained, 17 targeted tests passed. Confidence: 98% -- high. ⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:24:45Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:25:16Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:31:09Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:34:34Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:42:56Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:44:36Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T16:05:35Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T16:06:03Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T16:06:04Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T16:07:47Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T16:13:34Z

## External References
- Original A: .agentcortex/context/archive/codex-docs-design-onboarding-20261028.md.
- Canonical design/capability rules: guardrails 4.4; phase workflows; routing 3a; bootstrap 1b/3.6a.
- Release: repo-gotchas 12, existing version tests.
- Official runtime manifest: https://github.com/actions/python-versions/blob/main/versions-manifest.json (3.9 x64 on 24.04).

## Known Risk
- Native skill discovery varies by host; template/schema checks are not a live model-use guarantee.
- Final archived PR head must be CI green before merge; tag only the merged commit.
- Test temp outside Git; UTF-8/LF for bounded logs.
- Rollback via scoped revert PR; never rewrite published history or delete unrelated tracked/untracked/ignored data.

## Decisions
none

## Conflict Resolution
Karpathy and verification compatible; fresh reviewer has no implementation rationale; primary owns all logs/gates/git.

## Skill Notes
### verification-before-completion /test
- Checklist: full CI command, no deselection, non-Git temp.
- Checklist: code fingerprint recorded; no completion on unknown or failed tests.
- Constraint: GitHub and live URL remain later publication checks.
### karpathy-principles /review
- Checklist: full PR diff limited to A plus release metadata.
- Checklist: compare exact deployment paths and copyable YAML/native templates.
- Constraint: no broad fix of pre-existing README links or unselected B/C.
### karpathy-principles /plan
- Checklist: A validation plus release metadata only.
- Checklist: use existing version surfaces and release convention.
- Constraint: exclude B/C and no new runtime design behavior.
### verification-before-completion /implement
- Checklist: test final code tree and rehearse downstream adoption.
- Checklist: bind recorded suite to code fingerprint.
- Constraint: no release on unknown/failed checks.
### subagent-driven-development /review
- Checklist: fresh review with diff, acceptance and standards only.
- Checklist: primary verifies findings before changes.
- Constraint: reviewer read-only, no Work Log or git writes.

## Drift Log
- Compacted 2026-10-29 to archive/work/codex-docs-design-onboarding-20261029.md; earlier snapshot dated 20261028. Protected sections retained.
- README relocation and verified Python 3.9 runner repair preserve A/release scope and all checks.
- Local canceled suite is not PASS; exact-head full CI is authoritative.
- Client date rollover required date-only finalization to 2026-10-29.
- Re-read: .agent/workflows/implement.md section Phase Verification & Checkpoint -- confirm repair reverse path.

## Evidence
- Pre-ship validate.ps1: pass=117 warn=5 fail=0 skip=2. Fetch/merge main: already up to date at 5cb378b; post-sync version checks 2 passed, tree unchanged 85e354de.
- Final metadata tree 85e354de: 17 passed; only two publication-date fields differ from full-CI b34d350. Final-head CI remains a mandatory merge check, not yet claimed.
- Final date-delta review: exactly two one-line date changes, both current client date; prior independent A/CI reviews unchanged. No behavior/security/dependency change; 17 tests prove metadata consistency.
- Midnight date-only delta: CHANGELOG/CITATION now 2026-10-29, version/CI-hardening tests 17 passed; all non-date content unchanged.
- Full CI b34d350: Ubuntu 1066 passed/35 skipped; Windows shards total 1100 passed/2 skipped (73 subtests on each platform), all four suite jobs SUCCESS. Run https://github.com/KbWen/agentic-os/actions/runs/40718542475; all 19 PR checks completed, only Docs Content Pins skipped. Recorded CI verdict exit 0, code tree dd202b8f.
- Fresh CI-delta review PASS: independent parsed-YAML comparison confirms only validate-python39.runs-on changed; Python 3.9 version, all action pins, commands, conditions and every other job identical.
- CI setup MFR: ubuntu-latest=26.04 lacks Python 3.9 x64 before any project check. Upstream manifest confirms 3.9.25 Linux x64 for Ubuntu 24.04. Minimal runner pin committed b34d350; version + CI-hardening tests 17 passed.
- Independent final review at d6c559b: no actionable findings; confirmed canonical gates, strict no-KB schema, nested preferences, version tests, SSoT receipt hash and clean full diff.
- Demonstration: python scratch/verify_v1836_upgrade.py -> PASS: tagged v1.8.35 install -> current v1.8.36 via Windows deploy.ps1; 7 owned files preserved; 3 artifacts delivered; 14 guide links + 4 README entrypoints checked; capabilities OK and private config ignored. Downstream validate.ps1: pass=87 warn=1 fail=0 skip=8.
- Rehearsal: external non-Git run area v1836-upgrade-nejal06g. Online URL maps to the delivered guide; actual main URL availability is a post-merge publication check.
- Version consistency: 2 passed, exit 0. Fresh review P2 acknowledged and corrected; actual upgrade rehearsal in progress.
- git status --short clean; latest release v1.8.35 published 2026-10-20; this head has no existing PR.
- Work Log lock acquired for current release session.

## Review Feedback
- Full A review PASS at d6c559b; README relocation corrected. Fresh CI-delta review PASS at b34d350; only the supported runner image changed.

## Test Gate Results
- Test run: `python scratch/wait_v1836_ci.py` | exit: 0 | tree: dd202b8fd54b24074e9361ee09e1ec76f293a788 | at: 2026-10-28T16:00:19Z
- Test run: `python -m pytest -q tests/ci/test_release_version_consistency.py tests/ci/test_ci_hardening.py --basetemp C:\Users\wen\.codex\visualizations\2026\10\28\01a18229-3532-74b1-acb1-e2f78c50117d\v1836-final-metadata-8ad7a871d703413d940c63d08373c65d\suite --tb=short` | exit: 0 | tree: 85e354deecefa879f7b3171ece124dc44936e045 | at: 2026-10-28T16:06:53Z
- Test run: `python -m pytest -q tests/ci/test_release_version_consistency.py --basetemp C:\Users\wen\.codex\visualizations\2026\10\28\01a18229-3532-74b1-acb1-e2f78c50117d\v1836-sync-check-f405daa441424560ba53992e368e58a5\suite --tb=short` | exit: 0 | tree: 85e354deecefa879f7b3171ece124dc44936e045 | at: 2026-10-28T16:10:40Z

## Design Reference
none -- documentation, examples and release metadata only.

## Observability
none -- no application code.

## Lessons
- Floating runner images can outgrow old interpreter binaries; verify the upstream platform manifest while keeping compatibility checks enabled.
- Verify entrypoints in both source and deployed paths; checking only guide-internal links misses relocated README targets.
- Keep test temp outside Git worktrees; use UTF-8 and explicit LF for byte-capped archived logs.

## Resume
- PR #480: keep draft until final archived-head CI passes, then owner-authorized squash merge, tag merged SHA and publish latest v1.8.36. Verify main guide URL and remote tag. B/C excluded.

## Plan
- v1.8.36 metadata/changelog, independent A review, full CI, real upgrade, PR/merge/tag/release. Full target list and AC-1..4 in overflow snapshots. Quick-win spec exemption; no new feature/gate. Rollback by scoped revert PR; never move published tags. Confidence: 95%.

## Burden of Proof
| Criterion | Verdict | Evidence |
|---|---|---|
| A sources, handoff and customization fit canonical rules | PROVEN | guide lines 9-38; design-reference lines 5-68; strict parser/preferences checked by fresh reviewer |
| New entrypoints and project preservation | PROVEN | actual old-tag upgrade, 7 preserved files, 3 artifacts, 14 links, 4 README checks; reviewer independently reconstructed files |
| Release metadata accuracy and scope | PROVEN | release-version consistency 2 passed; full diff and receipt hash checked; A-only changelog |

## Test Blueprint
- Test Files: tests/ci/, tests/guard/, .agentcortex/tests/. Full Ubuntu + three Windows CI shards, no slow-test deselection; real upgrade covers artifacts/README boundaries. Non-Git temp, UTF-8 and LF. Final PR head must be CI green.
