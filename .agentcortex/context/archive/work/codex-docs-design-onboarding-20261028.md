

---
Compaction snapshot 2026-10-28T15:46:05.728716+00:00

# Work Log: codex/docs-design-onboarding -- release follow-up

## Header
- Branch: `codex/docs-design-onboarding`
- Classification: `quick-win`
- Classified by: `Codex`
- Frozen: `2026-10-28`
- Created Date: `2026-10-28`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `test`
- Diff Base SHA: `9d633453e9ba991f929b81f785c284a53b3e31a4`
- Checkpoint SHA: `b34d3502b76fdcd81ac10bc96d0cf6361b141d8e`
- Recommended Skills: `karpathy-principles, verification-before-completion, subagent-driven-development`
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
Independently verify the completed A design-onboarding change against its acceptance and real downstream use, run the full CI suite on the release tree, prepare v1.8.36 metadata/release notes, then publish via a CI-green PR and GitHub tag/release. No new design enforcement or tool connectors.

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-28T15:24:45Z | New owner-authorized release unit; unchanged quick-win tier. |

## Phase Summary
- review correction: fresh static reviewer PASS; only supported runner image changes, checks preserved. Full execution belongs to test phase. ⚡ ACX
- implement correction: only Python 3.9 runner image pinned to supported 24.04 and changelog note; all checks retained, 17 targeted tests passed. Confidence: 98% -- high. ⚡ ACX
- review: fresh final reviewer PASS; prior P2 fixed; proof table recorded, no unresolved blocker. ⚡ ACX
- implement: v1.8.36 canonical metadata/changelog and bounded README relocation correction committed; version tests 2 passed, diff check clean. Confidence: 95% -- high. ⚡ ACX
- implement entry: Ref Work Log Plan; canonical version metadata only. Confidence: 95% -- high.
- plan: eight release metadata targets; AC-1..4 mapped, independent A review and full test/release verification. Confidence: 95% -- high.
- bootstrap: release scope confirmed; clean baseline, latest release verified, v1.8.36 selected; no implementation yet. ⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:24:45Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:25:16Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:31:09Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:34:34Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:42:56Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-28T15:44:36Z

## External References
- https://github.com/actions/python-versions/blob/main/versions-manifest.json -- live upstream manifest: 3.9.25/3.9.24/3.9.23 publish linux x64 for 22.04 and 24.04; no 26.04.
- Original acceptance/implementation: .agentcortex/context/archive/codex-docs-design-onboarding-20261028.md, original A base 5cb378b.
- Canonical design gates in engineering_guardrails section 4.4 and plan/implement/review; routing section 3a; capabilities/preferences schema.
- Release contract: repo-gotchas section 12 (version banners + changelog + tag + GitHub release).
- Existing release-version-consistency tests define all canonical version surfaces.

## Known Risk
- Previous tests predate final EOF-only cleanup: rerun full CI suite against final release contents; do not use past counts as new evidence.
- Native registration declarations are not proof of actual model skill use; independently check handoff examples and capabilities/native discovery limits.
- Use temp OUTSIDE every Git repo so non-repository guard assertions remain valid.
- Release only after CI-green head; merge allowed by explicit user selection. No force push, gate bypass or direct main commits.
- Rollback: revert only this unit's scoped commits in a reviewed PR. No deletion/reset of tracked, untracked or ignored state. A published tag/release is not silently moved.

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
- TESTED->IMPLEMENTING reverse: CI Python 3.9 job failed during setup on ubuntu-latest=26.04, before project checks. Job 122919719655 / run 40717685833 reports no 3.9 x64 package for Ubuntu 26.04. Scope adds only that job runner pin plus changelog note; original check retained. User's CI-green publication authorization covers this bounded compatibility repair.
- Local full suite canceled at about 6% before changing the candidate; no completed/pass run recorded. Full suite remains required and will be proven by all Ubuntu/Windows CI jobs on the exact final head; local targeted checks supplement it.
- Plan target addition: README.md and docs/README_zh-TW.md, bounded correction of fresh-review P2 in original A; no new capability or gate.
- New follow-up log after original archived local delivery, not a continuation pretending the old ship was remotely published.
- Earlier governance files are reused per Read-Once; phase-operational shared-contracts loaded fresh at entry.

## Evidence
- Fresh CI-delta review PASS: independent parsed-YAML comparison confirms only validate-python39.runs-on changed; Python 3.9 version, all action pins, commands, conditions and every other job identical.
- CI setup MFR: ubuntu-latest=26.04 lacks Python 3.9 x64 before any project check. Upstream manifest confirms 3.9.25 Linux x64 for Ubuntu 24.04. Minimal runner pin committed b34d350; version + CI-hardening tests 17 passed.
- Independent final review at d6c559b: no actionable findings; confirmed canonical gates, strict no-KB schema, nested preferences, version tests, SSoT receipt hash and clean full diff.
- Demonstration: python scratch/verify_v1836_upgrade.py -> PASS: tagged v1.8.35 install -> current v1.8.36 via Windows deploy.ps1; 7 owned files preserved; 3 artifacts delivered; 14 guide links + 4 README entrypoints checked; capabilities OK and private config ignored. Downstream validate.ps1: pass=87 warn=1 fail=0 skip=8.
- Rehearsal: external non-Git run area v1836-upgrade-nejal06g. Online URL maps to the delivered guide; actual main URL availability is a post-merge publication check.
- Version consistency: 2 passed, exit 0. Fresh review P2 acknowledged and corrected; actual upgrade rehearsal in progress.
- git status --short clean; latest release v1.8.35 published 2026-10-20; this head has no existing PR.
- Work Log lock acquired for current release session.

## Review Feedback
- New blocking release issue: setup-python cannot install 3.9 on Ubuntu 26.04. Minimal fix pins only validate-python39 to verified ubuntu-24.04; no skip/continue-on-error or Python-version removal. Fresh re-review required.
- Final fresh reviewer: no actionable findings at d6c559b; previous P2 resolved. Independent evidence includes exact seven-file reconstruction and source/deployed links.
- Fresh reviewer found P2: source-relative new README links break after deploy relocation. Fix uses clearly labelled canonical online link plus project-root local installed path in both READMEs; no deploy logic change. Verify target after merge.


## Test Gate Results
none

## Design Reference
none -- documentation, examples and release metadata only.

## Observability
none -- no application code.

## Lessons
- Verify entrypoints in both source and deployed paths; checking only guide-internal links misses relocated README targets.
- Keep test temp outside Git worktrees; use UTF-8 and explicit LF for byte-capped archived logs.

## Resume
- Next: plan version surfaces, implement metadata, fresh review, full suite, downstream smoke, PR/CI/merge/tag/release.

## Plan
- Targets: CHANGELOG.md, CITATION.cff, .agentcortex/bin/deploy.sh (ACX_VERSION only), .agentcortex/docs/TESTING_PROTOCOL.md, .agentcortex/docs/TESTING_PROTOCOL_zh-TW.md, .agentcortex/docs/guides/antigravity-v5-runtime.md, docs/AGENT_MODEL_GUIDE.md, docs/AGENT_MODEL_GUIDE_zh-TW.md. Work Log/SSoT/archive are phase evidence, not new runtime scope.
- Spec: quick-win exemption; original A acceptance remains in its archived log. No new docs/specs/<feature>.md or new gate policy is introduced.
- AC-1: all version surfaces align at 1.8.36 with correct date, accurate A-only changelog.
- AC-2: fresh review proves readable design sources/tool-less fallback, no-KB customization, safe activation and ownership; no unresolved blockers.
- AC-3: final tree passes the full CI test command plus source validation; real downstream deployment and update preserve project files and deliver three A artifacts.
- AC-4: PR CI green before merge; merged SHA has v1.8.36 tag and published latest GitHub Release, with verifiable URLs and no leftover active log/lock.
- Steps: (1) update canonical version surfaces/changelog -> release-version tests; (2) fresh review of full A+release diff -> burden-of-proof table; (3) full CI suite, native validation, clean install and update smoke -> recorded evidence; (4) archive release evidence, PR, wait CI, merge, tag and publish -> GitHub state checks.
- Risks+Rollback: native activation differs by agent; document limits and avoid runtime claims. Revert via a scoped PR only; never rewrite published history or delete unrelated data.
- Mode: Fast Lane. Confidence: 95% -- high.

## Burden of Proof
| Criterion | Verdict | Evidence |
|---|---|---|
| A sources, handoff and customization fit canonical rules | PROVEN | guide lines 9-38; design-reference lines 5-68; strict parser/preferences checked by fresh reviewer |
| New entrypoints and project preservation | PROVEN | actual old-tag upgrade, 7 preserved files, 3 artifacts, 14 links, 4 README checks; reviewer independently reconstructed files |
| Release metadata accuracy and scope | PROVEN | release-version consistency 2 passed; full diff and receipt hash checked; A-only changelog |

## Test Blueprint
- Test Files: tests/ci/, tests/guard/, .agentcortex/tests/ -- exact full CI suite, no deselection.
- Existing tests cover version consistency, strict schema/native skill format, deploy manifest/preservation, source governance/CLI/security boundaries and lifecycle budgets.
- No new implementation-mirroring prose tests; explicit real adoption rehearsal covers new guide/template behavior and the relocated README boundary.
- Test temp outside any Git worktree; UTF-8 and explicit LF throughout.
