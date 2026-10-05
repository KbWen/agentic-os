---
status: frozen
created: 2026-10-05
classification: feature
primary_domain: document-governance
backlog: 188
extends: downstream-fork-accommodation
---

# Brownfield First-Install Preservation

## Goal

Close backlog row #188: when a first deployment collides with an existing,
different core-tier file, save the adopter's exact bytes before installing the
framework version and visibly identify the backup. Keep ADR-005's requirement
that framework-authoritative core files receive updates.

Owner approved this specification on 2026-10-05; frozen for execution.
Implementation and test evidence live in the executor's Work Log.

## Evidence and Root Cause

Baseline: `main` at `a33cc1145901db0e063f670c33cccca945caf913`.
`deploy.sh:224-226` determines update mode by manifest existence. The update
core branch (`:235-255`) creates an `.acx-local` backup; the fresh-install core
branch (`:308-331`) copies over a different destination with no backup or notice.
Both the batch and per-file dispatch paths call `_deploy_file_now`.
`deploy.ps1:102-103` invokes the canonical `deploy.sh`, so no second PowerShell
implementation is needed. Line anchors describe this baseline only.

Minimal failing scenario (for the executor to run before the patch):
1. Create a temporary target with no `.agentcortex-manifest` and write unique
   CRLF bytes to `.agent/rules/engineering_guardrails.md`.
2. Deploy the real script into that target using an isolated minimal source
   fixture or the repository source; never deploy into the framework checkout.
3. Compare destination, backup, notice, and manifest to the expected contract.

Expected: the original bytes exist at `<path>.acx-local` before the framework
replaces the live file, and stdout identifies the affected path and backup.
Existing source behavior: the first-install core branch replaces the live file
without making that backup. Historical reproduction is recorded in backlog #188.
The planning session's runtime reproduction was blocked by sandbox `mkdir`
permission errors before that branch; it is **not** red-test evidence.

## Acceptance Criteria

| ID | Observable contract |
|---|---|
| AC-1 | On a first install, an existing core file whose normalized hash differs from upstream is backed up byte-for-byte to `<path>.acx-local` before replacement. This works for tracked, untracked, and gitignored files; preservation never relies on Git history. |
| AC-2 | With normal copy settings, the live core file becomes the framework version, no `.acx-incoming` is created for it, and the manifest records the normalized upstream hash. No-manifest core collisions remain core-tier. |
| AC-3 | Each protected collision prints `[OVERWRITE]` with the relative path and actual backup path, and increments the existing `COUNT_CORE_OVERWRITTEN` summary. No message may claim a backup that was not written. |
| AC-4 | Backup failure exits nonzero before replacing the affected live file. Its original bytes remain intact, and the run does not emit a successful completed-deploy summary or publish a completed manifest. Earlier file operations are not rolled back transactionally. |
| AC-5 | A missing core destination or one with the same normalized content creates no backup or overwrite notice. A repeat deploy of an unchanged protected file leaves its existing backup intact and does not re-report a collision. CRLF-only differences use the existing normalization rule. |
| AC-6 | An existing `.acx-local` is a single-generation backup: a new collision refreshes it with the current pre-overwrite live bytes, as already done for updates. Backup creation must not silently skip or prompt under `CP_FLAG=-n` or `-i`; preserve the existing live-copy flag semantics. Test `-n` explicitly, without demanding a live overwrite when that flag forbids one. |
| AC-7 | Batch hashing and `ACX_FORCE_PERFILE=1` satisfy the same contract. A Windows `deploy.ps1` behavioral smoke confirms the wrapper inherits it; the wrapper implementation stays unchanged unless a concrete defect requires scope review. |
| AC-8 | Existing scaffold/wrapper preservation, edited-skill sidecars, core update backups, dry-run behavior, manifest format, deployed-file membership, and custom-* namespace behavior remain compatible. |
| AC-9 | ADR-005 and INSTALL.md describe both first-install core backups and scaffold `.acx-incoming` preservation accurately. INSTALL.md's blanket promise that all existing framework-managed files stay in place is narrowed. |

## Constraints and Non-goals

- One canonical deploy implementation; no new tier, dependency, setting, CLI
  flag, backup-history system, or broad deployment refactor.
- Do not implement backlog #190, #184, #193's general banner readiness change,
  #201's scaffold sidecar proposal, or unrelated updater/source-provenance work.
- No change to manifest schema, normalized hashes, source selection, installer
  fetching, removed-file detection, legacy migration, or managed ignore rules.
- `.acx-local` protects the latest pre-overwrite bytes, not all historical
  versions. Users retaining older backups must copy them aside before deploy.
- No transactional rollback for a whole deployment and no new guarantee against
  concurrent modification of a target by another process.
- Do not edit shipped historical specs; amend the accepted ADR's current
  contract and introduce this independent first-install extension.

## Domain Decisions

- [DECISION] Reuse the existing `.acx-local` core backup contract on first-install
  collisions; core files still receive the framework version rather than freezing
  governance delivery behind `.acx-incoming`.
- [TRADEOFF] Keep one latest backup, matching existing core-update semantics,
  instead of adding versioned backup storage to a contained data-loss fix.
- [CONSTRAINT] The preservation invariant is backup-before-replacement, including
  files absent from Git history; backup failure must stop the affected overwrite.
- [CONSTRAINT] Preserve scaffold/wrapper sidecars and normalized-hash decisions;
  the first-install extension must not redesign other deploy branches.

## Proposed ADR-005 Amendment

Append a clearly dated amendment instead of rewriting its historical Context:
"For a fresh install with no manifest, a different pre-existing core-tier file
is backed up byte-for-byte to `<path>.acx-local` before applying the existing
copy policy. The operation names the backup and contributes to the existing
overwrite summary. A failed backup stops the affected overwrite. The backup
stores the latest pre-overwrite version, matching the already-shipped core
update contract; scaffold/wrapper files retain `.acx-incoming` preservation."
Clarify Decision/compliance wording that currently describes force-update as
having 'no sidecar': core uses `.acx-local`, never `.acx-incoming`.

## Target Files / Blast Radius

| File | Responsibility |
|---|---|
| `.agentcortex/bin/deploy.sh` | Fresh-install core branch of `_deploy_file_now`; reuse existing backup/reporting semantics. |
| `tests/ci/test_deploy_tiering.py` | Focused first-install behavioral regressions using existing fixture conventions. |
| `docs/adr/ADR-005-downstream-file-preservation-tiering.md` | Dated preservation-contract amendment and accurate current wording. |
| `docs/INSTALL.md` | Narrow existing-files promise and explain latest backup recovery. |
| `docs/specs/brownfield-first-install-preservation.md` | Owner-approved draft -> frozen; execution details/evidence references; shipped status only at ship. |

The intended production patch is localized to one branch of one function;
the exact line count is established by the executor's diff, not promised here.
Work Log/session receipts are local operational writes. Ship alone may update
backlog row #188, the document-governance L2 log, SSoT, and archive metadata.
These are delivery records, not additional features.

## Execution Plan and AC Coverage

Each edit/check below is a small work unit; slow subprocess suites may take
longer than the edit itself. Mode: Fast Lane, bounded scope; all feature gates
remain required. Confidence: 93% for scope and design; runtime is unverified.

1. **Approve and bind**: owner approves this proposal; freeze this spec. Resume
   the planning Work Log with a new session and an acquired lock. If moving to a
   task branch, confirm the context and create its own branch-derived Work Log,
   carrying forward the plan/evidence without changing the original receipts.
   Verify: baseline/diff checked, correct owner/branch/lock, frozen spec on disk.
2. **Write failing preservation tests**: use the existing minimal source fixture
   pattern (deploy script, both required templates, representative core files).
   Parameterize batch/per-file and cover a rule plus a `.claude/commands` core
   path. Cover tracked/untracked/gitignored ownership and assert original backup
   bytes, live upstream bytes, notice, count, and manifest hash. At least one test
   must fail on this baseline because the backup is missing, not because Bash
   or fixture prerequisites are absent. Verify: red tests explain AC-1/2/3/7.
3. **Patch only the fresh-install core branch**: before its existing replacement,
   write the current destination to `.acx-local` without a silent no-clobber or
   interactive backup option. Reuse existing overwrite wording/counter. Preserve
   failure ordering; do not extract/refactor unrelated update logic.
   Verify: step-2 tests green; inspect backup-before-copy ordering (AC-1/2/3/6).
4. **Add boundary tests**: backup-copy failure (deterministic `cp` shim scoped to
   the `.acx-local` destination), an older backup, `CP_FLAG=-n`, equal/CRLF-only
   content, absent destination, repeat deploy, and Windows wrapper smoke. Compare
   byte snapshots around failure/dry-run; assert no successful final manifest on
   backup failure. Verify: AC-4/5/6/7 plus existing AC-8 regression suite passes.
5. **Amend documentation**: apply the ADR proposal and narrow INSTALL.md's first
   install promise. Include restoration from `.acx-local`, its latest-only
   semantics, and the distinction from `.acx-incoming`.
   Verify: AC-9 against actual behavior; lifecycle check + docs-pin tests.
6. **Review, test, and delivery**: execute review -> test -> formal handoff, fix
   findings through legal reverse edges, and prepare ship evidence. Codex performs
   the final independent review before accepting this work as delivered. Final
   ship/merge follows the user's authorization and all normal gates.
   Verify: PASS review receipt, test results, handoff paths, and final diff/SHAs.

AC mapping: AC-1/2/3 -> steps 2-3; AC-4/5/6/7 -> steps 3-4;
AC-8 -> steps 4/6; AC-9 -> steps 5-6.

## Test Skeleton / Commands

First confirm usable Git Bash utilities; PATH's WindowsApps bash is not evidence
of a working shell. On this Codex sandbox, even repaired Git Bash probes could
not create target subdirectories; do not mislabel that as a product red test.
The executor should use a working host shell or CI without changing deployment
logic merely to accommodate this session's sandbox.

```text
python -m pytest tests/ci/test_deploy_tiering.py -k brownfield -q
python -m pytest tests/ci/test_deploy_tiering.py tests/ci/test_deploy_dry_run_read_only.py tests/ci/test_deploy_install_day_copy.py -q
python .agentcortex/tools/check_lifecycle_frontmatter.py --root .
python -m pytest -m docs_pin -q
bash .agentcortex/bin/validate.sh
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .agentcortex/bin/validate.ps1
git diff --check
```

Name new tests with `brownfield` so the focused selection is nonempty. Expected:
first command red on baseline, green after patch; final checks exit 0. Record
versions, commands, pass/fail/skip counts, and checkpoint SHA in the executor's
Work Log. Run the existing required CI suite once for delivery; a required test
skipped for missing Bash/PowerShell needs execution on the appropriate runner.
Do not weaken skips, snapshots, or validators to obtain green output.

## Risks and Rollback

- A failed backup must precede live replacement. Exercise this with an injected
  copy error; a green happy path alone is insufficient.
- `.acx-local` may contain an older backup. Refreshing it is the existing
  latest-only policy, so disclose it rather than promising historical recovery.
- `CP_FLAG` affects live copy semantics. Ensure backup preservation is reliable
  without broadening this fix into flag-policy redesign or false overwrite claims.
- Roll back the implementation with a normal revert of the task commits after
  checking the working tree; never reset/clean unrelated or untracked state.
  For an affected adopter, restore each original from its `.acx-local` backup;
  first copy the live framework file and any older backup the user wants to keep
  to a separate user-selected location. Git alone does not preserve ignored
  backups or untracked original content. Reverting source does not restore a
  previously deployed target automatically.

## Claude Pickup and Codex Final Review

Read this spec, AGENTS.md, and `.agentcortex/context/work/kbwen-main.md` first.
The latter is a **planning pickup**, not a completed formal handoff or ship.
Use its read map; do not repeat the entire initial repository discovery.
No implementation, review, test, or formal handoff receipt exists yet.

Claude owns implementation, its review/fixes, tests, formal handoff, and ship
preparation. Stay within this feature and provide the final diff/checkpoint or
PR plus Work Log path and the red/green/failure evidence. A self-review PASS does
not replace the final Codex review requested by the owner.

Codex final review checks: original bytes recoverable without Git; actual backup
before every changed overwrite; honest failure/notice/manifest behavior; batch
and wrapper coverage; focused diff; ADR/INSTALL parity; and valid gate evidence.
Do not merge/publish solely because implementation or self-review completed.
