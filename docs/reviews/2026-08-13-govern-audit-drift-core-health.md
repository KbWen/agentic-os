# Governance Audit Handoff — Drift and Core Health (2026-08-13)

## Executive verdict

**HEALTHY WITH ONE CONFIRMED CORE WINDOWS DEFECT AND LOCALIZED DRIFT.**

The repository is not broadly unhealthy: local `HEAD`, `origin/main`, the remote
`refs/heads/main`, and tag `v1.8.20` all resolve to
`3faae10b801d001e82c7883d9145ade33c4e9813`; ADR/spec indexes, version surfaces,
the audit chain, and the PowerShell structural validator are internally
consistent. The latest validator run reported `118 PASS / 4 WARN / 0 FAIL /
2 SKIP`.

That validator result is a positive signal, not a complete health proof. Its
PASS count changes with gitignored active Work Logs, and the Windows test suite
currently cannot complete on this machine. Direct behavioral probes confirmed
that the PowerShell deployment entry point fails in this supported Windows
environment. Therefore the accurate top-line is not "all green"; it is
"governance structure intact, Windows deployment path broken, plus two smaller
state-contract drifts."

Method: read-only governance audit plus a three-seat roundtable (core health,
state/document drift, adversarial tenth-man). All subagent claims were treated
as hypotheses and rechecked against the real code path. External-signal status:
`same-vendor-only`; architecture conclusions should receive independent human
or different-vendor review before implementation is accepted.

## Baseline

| Check | Result |
|---|---|
| `git rev-list --left-right --count origin/main...HEAD` | `0  0` |
| `git ls-remote origin refs/heads/main refs/tags/v1.8.20` | both `3faae10...` |
| `.agentcortex/bin/validate.ps1` | `118 PASS / 4 WARN / 0 FAIL / 2 SKIP` |
| Active backlog | 64 `Pending`, 0 `In Progress` |
| Worktree | one pre-existing local diff: `.claude/settings.local.json` |
| Full pytest | not completed; two independently reproducible Windows launcher failures below |

The four validator warning groups are understood: one stale pending
`routing_actions` snapshot already tracked by backlog #103, one stale local Work
Log lock, historical archived receipt debt, and the 28-section eval-coverage
advisory already tracked by #143. They do not establish a new system-wide
failure.

## Verified findings

### F1 — HIGH — The supported PowerShell deployment entry point fails on Windows

This is the only new finding that changes the core-health verdict.

`Resolve-BashLauncher` selects a real Git Bash executable, but the wrapper then
invokes the canonical shell script and forwards a native Windows target without
establishing a reliable Git-for-Windows execution environment or translating
the target (`.agentcortex/bin/deploy.ps1:14-50,85`). Two real entry-point probes
failed in different manifestations:

1. Direct wrapper run to a newly created `%TEMP%` directory returned exit 1,
   created no `.agentcortex-manifest`, and attempted
   `mkdir 'C:\\Users/wen'` from the repository because the Windows target was
   consumed as a shell-relative path.
2. The repository's own behavioral test
   `tests/ci/test_deploy_tiering.py::test_deploy_ps1_entrypoint_resolves_real_bash`
   returned exit 127 because the selected `Git\\bin\\bash.exe` process could not
   resolve `dirname` or `mktemp`.

The roundtable initially disagreed: the core-health seat called this an
environment false alarm, while the tenth-man called it a core entry-point
failure. The primary probe of the actual wrapper and the repository's own
behavioral test resolve the dispute in favor of the tenth-man. Reading only the
test's `os.name == 'nt'` branch was insufficient; executing that branch fails.

Impact: a documented Windows deployment path can fail before producing a
manifest. This is a core portability defect, even though Linux CI and
`validate.ps1` remain healthy.

Claude direction: treat as a `hotfix`, not a documentation tweak. Reproduce
first, then make one canonical launcher/path-conversion design shared by
`.agentcortex/bin/deploy.ps1` and `installers/deploy_brain.ps1`. Preserve spaces
and Unicode in paths. Add discriminating Windows tests for: a native absolute
target, a target containing spaces, a broken WindowsApps alias before a valid
Git Bash candidate, and availability of required Unix utilities. Do not merely
switch from `bin\\bash.exe` to `usr\\bin\\bash.exe` without proving target-path
translation and both entry points.

### F2 — MEDIUM — Bash availability probing can abort pytest collection

`.agentcortex/tests/test_ssot_completeness.py:22-47` treats the first existing
`bash` candidate as safely startable. On this machine `shutil.which("bash")`
returns the WindowsApps WSL alias. `subprocess.run()` raises `OSError [WinError
1312]`; the exception is uncaught, so module import and collection abort before
the later valid Git Bash candidates can be tried. The same helper is imported
by `test_backlog_validation.py`.

Reproduction:

```text
python -m pytest .agentcortex/tests/test_ssot_completeness.py --collect-only -q -p no:cacheprovider
ERROR at test_ssot_completeness.py:36 — OSError [WinError 1312]
```

This is not proof that hundreds of tests regressed; it is one shared launcher
failure that prevents the suite from discovering them. It is nevertheless a
real test-startability defect and masks other regressions.

Claude direction: after F1 establishes the canonical launcher behavior, make
the probe reject WindowsApps aliases, catch `OSError`, continue to the next
candidate, and return false only after all candidates fail. Add a unit test
where candidate 1 raises and candidate 2 succeeds. Avoid a broad test-helper
refactor unless duplicate behavior is first inventoried and covered.

### F3 — MEDIUM — A file declared user-local is tracked as project state

`.claude/settings.json:2` says user-local permissions live in
`settings.local.json`, but `.claude/settings.local.json` is tracked and absent
from `.gitignore`. Its current diff adds local `gh issue`/`gh pr` permissions.
At least five archived Work Logs explicitly exclude this same file as local
permission noise, demonstrating repeated operational cost rather than a
one-off dirty tree.

This is a contract drift: Git behavior says shared project artifact while the
canonical comment and repeated workflow behavior say local-only.

Claude direction: this requires an owner-confirmed migration. Preferred shape:
ignore `.claude/settings.local.json`, move any intentional seed to a clearly
named example, and stop tracking the local file without deleting the operator's
working copy. Document how existing contributors retain their permissions.
Do not rewrite history; do not silently remove local permissions during pull.

### F4 — LOW — The SSoT embeds a stale volatile backlog count

`.agentcortex/context/current_state.md:30` says `59 Pending as of 2026-08-09`,
while strict row parsing of `docs/specs/_product-backlog.md` yields 64 Pending.
The SSoT was updated on 2026-08-12, so the old count survived later state writes.
The validator correctly checks the canonical backlog path but does not validate
this prose number.

This is document drift, not runtime corruption: the backlog remains canonical
and structurally valid.

Claude direction: prefer deleting the volatile count and linking only to the
canonical backlog. If the owner wants a dashboard count in SSoT, generate and
machine-check it; do not continue manual carry-forward.

## Known findings excluded from new scope

- Backlog #103 owns the four stale `routing_actions` in the 2026-07-01
  premortem. The current 43-day warning is expected pressure, not a new finding.
- #121 remains genuinely Pending. README contains earlier partial material, but
  still lacks the requested enforced/wire-up/advisory matrix, ACX/gate-block
  FAQ, and Traditional Chinese caveat parity. Do not close it by inference.
- #143 owns tier-blind governance eval coverage (`28` uncovered MUST-bearing
  sections).
- #148 owns the latent hyphenated-verdict parser fail-open; the canonical
  `NOT READY` spelling is verified to fail progression correctly.
- #169 owns the higher-priority decision-disposition fail-open for noncanonical
  bullet-form Decisions. It remains the highest known localized governance
  correctness debt.
- #170 is the owner's PII disposition decision; this audit does not recommend a
  destructive history rewrite.
- #171 owns the TruffleHog Lob-detector false-positive class.
- `.agentcortex/context/work/chore-archive-codex-review-log.{md,lock.json}` is a
  real stale local residue, but `_product-backlog.md` already records it as a
  reviewer adherence/setup gap under an existing rule. Archive or remove the
  local residue through the normal chain-aware workflow; do not add machinery.

## Roundtable and tenth-man adjudication

| Candidate | Final verdict | Reason |
|---|---|---|
| Repository broadly unhealthy | Refuted | Core indexes, chain, versions, refs, and PowerShell validator are consistent. |
| `118 PASS / 4 WARN` proves full health | Refuted | PASS count is active-log-sensitive; full tests did not complete; behavioral deployment probe fails. |
| Windows PowerShell deploy defect | Confirmed after dispute | Actual wrapper and its own behavioral test both fail. |
| Windows pytest probe defect | Confirmed | Import-time `OSError` is reproducible and blocks collection. |
| Tracked `settings.local.json` is drift | Confirmed | Local-only declaration conflicts with Git tracking and repeated operational handling. |
| `59` vs `64` means core corruption | Narrowed | Real stale prose; canonical backlog remains correct. |
| Stale Work Log is a new product defect | Refuted | Known adherence residue with an existing rule and recorded disposition. |
| Remote main is ahead of local | Refuted | `ls-remote` and all local refs agree on `3faae10...`; webpage commit counts are not ref evidence. |
| Backlog #121 is already implemented | Refuted | Existing README content predates the row and does not satisfy its remaining deltas. |

## Recommended execution order for Claude

1. **Hotfix F1 + F2 as one Windows startability unit.** F1 is the required red
   test; F2 prevents the suite from honestly exercising it. Run the focused
   PowerShell deploy test, collection regression, both validators, then the CI
   structural suite on Windows. Keep this separate from documentation cleanup.
2. **Fix known #169 next.** It is a real localized fail-open with an existing
   fixture shape and higher governance correctness value than cosmetic drift.
3. **Resolve F3 only after the owner selects the migration behavior.** No
   history rewrite.
4. **Remove F4's volatile count** as a separate governance quick-win, using the
   guarded SSoT write path.
5. Continue existing product priority #121 after correctness work, unless the
   owner deliberately prioritizes adoption conversion over P2 hardening.

Owner decisions required before implementation:

- F3: retain a tracked example or have no seed file; confirm contributor
  migration wording.
- #170: accept and close the already-public email copies (recommended) or
  authorize a repository-history rewrite with full audit-chain consequences.
- #171: exclude the Lob detector and document the workaround, tolerate the
  false-positive class, or pursue upstream correction.

## Claude pickup prompt

```text
Read docs/reviews/2026-08-13-govern-audit-drift-core-health.md in full.
Start a new classified work unit for F1+F2 only. Treat F1 as a Windows deploy
hotfix, reproduce both recorded failures before editing, and preserve the
pre-existing .claude/settings.local.json diff. Use the repository's normal
bootstrap/plan/implement/review/test flow; do not mark the audit routing_actions
merged until the corresponding Domain Log receives the verified decision.
Do not implement F3 until the owner selects the migration behavior. Keep F4,
#121, #169, #170, and #171 as separate work units; do not opportunistically
bundle them into the Windows patch.
```

## routing_actions

```yaml
routing_actions:
  - finding: "The Windows PowerShell deployment entry points must invoke Git Bash with a usable tool environment and lossless native-target path conversion."
    target_doc: "docs/architecture/tooling.log.md"
    status: pending
    owner: "claude-handoff"
  - finding: "Windows shell availability probes must reject unusable aliases and continue after process-start errors instead of aborting pytest collection."
    target_doc: "docs/architecture/testing.log.md"
    status: pending
    owner: "claude-handoff"
  - finding: "Claude user-local permission state must not remain ambiguously tracked as shared project configuration."
    target_doc: "docs/architecture/governance.log.md"
    status: pending
    owner: "claude-handoff"
  - finding: "SSoT summaries should not manually duplicate volatile backlog counts without a freshness check."
    target_doc: "docs/architecture/document-governance.log.md"
    status: pending
    owner: "claude-handoff"
```
