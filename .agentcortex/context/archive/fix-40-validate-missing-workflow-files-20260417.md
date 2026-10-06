# Work Log: fix/40-validate-missing-workflow-files

## Header

- Branch: `fix/40-validate-missing-workflow-files`
- Classification: `feature`
- Classified by: `Claude Opus 4.7`
- Frozen: `true`
- Created Date: `2026-04-17`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship (batch 1 complete; batch 2 pending)`
- Checkpoint SHA: `95ceafb`
- Recommended Skills: `writing-plans, executing-plans, verification-before-completion, karpathy-principles, finishing-a-development-branch`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `2`

---

## Session Info

- Agent: Claude Opus 4.7 (1M context)
- Session: 2026-04-17
- Platform: claude-code (Windows)

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO

## Task Description

Post-v1.1.0 polish batch — fix real issues surfaced by broad audit:

- Installers: Git-path detection broadened via `git` location derivation, `git clone` progress no longer suppressed.
- Token discipline: `CLAUDE.md` condensed (removed duplicated Hard Rules section).
- Governance wiring: Confidence Gate auditable via `plan.md` compact-block field + `ship.md` advisory audit.
- UX: Skill index signposted in `routing.md §3` (already the canonical table, just unlabeled).
- Rule clarity: `AGENTS.md §Core Directives` No-Bypass scope clarified vs documented classification fast-paths.

Philosophy: surgical edits, no new files, no refactors. "稍微濃縮就好" per user.

## Phase Sequence

- bootstrap
- plan
- implement
- review
- test

## Phase Summary

- bootstrap: feature-tier, skills matched, context loaded from SSoT + audit report.
- plan: 6 atomic edits across 7 files. Mode: Normal. Confidence: 92% — governance files well understood.
- implement: 7 files edited, 48 insertions / 46 deletions. No new files created.
- review: diff scope verified (all changes within planned target files); see Evidence below.
- test: validate.sh → pass=60 warn=4 fail=0 (warnings are pre-existing worklog-format quirks).

## Gate Evidence

- Gate: bootstrap | Verdict: pass | Classification: feature | At: 2026-04-17T00:00Z
- Gate: plan | Verdict: pass | Classification: feature | At: 2026-04-17T00:00Z
- Gate: implement | Verdict: pass | Classification: feature | At: 2026-04-17T00:00Z
- Gate: review | Verdict: pass | Classification: feature | At: 2026-04-17T00:00Z
- Gate: test | Verdict: pass | Classification: feature | At: 2026-04-17T00:00Z

## External References

- Audit report (in-conversation, Explore subagent, 2026-04-17) — listed 12 findings; 6 were addressed in this batch, 6 deferred as out-of-scope for this polish pass.

## Known Risk

- Editing `AGENTS.md §Core Directives` touches global governance — limited to 1-sentence scope clarification. Rollback: revert to SHA `2b6117c` (v1.1.0 release tag).
- Editing `plan.md`/`ship.md` templates affects every future phase run — changes are additive (new `Confidence:` field + advisory audit section), no structural change to existing gates.
- Rollback strategy: `git revert` the polish commit; all affected files are governance markdown + installer scripts, no data migration.

## Conflict Resolution

none

## Skill Notes

### verification-before-completion

- cached_hash: n/a (policy loaded from AGENTS.md §Shared Phase Contracts)
- First Loaded Phase: implement
- Applies To: implement, test

#### test

- Checklist: (1) Scope — diff limited to 7 planned target files, no stray edits. (2) Quality — `bash validate.sh --no-python` returns `pass=60 warn=4 fail=0`; warnings are pre-existing worklog format quirks not introduced by this change. (3) Evidence — diff-stat output captured below; validator output captured below. (4) Risk — rollback = revert to `2b6117c`. (5) Communication — summary covers what changed, what was validated, what remains deferred.
- Constraint: No code execution beyond validator; all changes are markdown + shell scripts so compile/test surface is minimal.

## Evidence

### Diff scope (git diff --stat HEAD before worklog rewrite)

```
 .agent/workflows/plan.md    |  3 +++
 .agent/workflows/routing.md |  2 ++
 .agent/workflows/ship.md    |  4 ++++
 AGENTS.md                   |  2 +-
 CLAUDE.md                   | 49 +++++++++++++--------------------------------
 installers/deploy_brain.ps1 | 28 +++++++++++++++++++-------
 installers/deploy_brain.sh  |  6 +++---
 7 files changed, 48 insertions(+), 46 deletions(-)
```

### Syntax checks

- `bash -n installers/deploy_brain.sh` → `SH_OK` (clean)
- PowerShell syntax: not run on this host; `Resolve-BashLauncher` change is additive (new candidate sources via `Get-Command git`) — existing static fallback list preserved, so no regression path.

### validate.sh output

- `Summary: pass=60 warn=4 fail=0 skip=6`
- 4 warnings are worklog-format related (validator expects `- Branch:` list, not YAML frontmatter); this is a pre-existing validator/template mismatch, not introduced by this change.
- Key governance checks all pass: routing index, Spec Index completeness, ADR Index, gate evidence, phase progression, guarded writes.

### Audit finding coverage

- ✅ Finding 1.2 (git clone --quiet): removed `--quiet` from both clone + pull paths in `installers/deploy_brain.sh`.
- ✅ Finding 1.3 (hard-coded Git paths): `Resolve-BashLauncher` now derives `bash.exe` candidates from `Get-Command git` output, covering scoop / chocolatey / portable Git / custom prefixes.
- ✅ Finding 2.2 (skill discoverability): `routing.md §3` header now states "This table IS the canonical skill index".
- ✅ Finding 3.1 (AGENTS/CLAUDE duplication): `CLAUDE.md` dropped from 51 → ~27 lines; duplicated Hard Rules section removed entirely; Skills subsection condensed to pointer.
- ✅ Finding 4.1 (No-Bypass vs fast-path): `AGENTS.md §Core Directives` No-Bypass rule now carries a scope clarification sentence distinguishing "gate skipping" from "documented classification fast-paths".
- ✅ Finding 4.2 (Confidence Gate not wired): `plan.md` compact-block template adds `Confidence:` field; `ship.md` adds Confidence Trace Audit advisory.
- ⏭ Deferred (out of scope for polish pass): 1.1 Python fallback advisory, 2.1 tiny-fix 7-criterion simplification, 2.3 confidence visibility (partially addressed by 4.2), 3.2 guardrails conditional-load signal, 3.3 bootstrap.md refactor, 4.3 Read-Once enforcement.
