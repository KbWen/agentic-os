# Release-to-Downstream Premortem — 2026-08-26

## Scope

Assume the next Agentic OS release is published successfully but a downstream
adopter receives an inconsistent or unverifiable package. Trace three failure
surfaces: release-version consistency, GitHub Actions job-graph integrity, and
a clean downstream deployment/self-check.

The working tree already contained the unrelated one-line `pytest.ini` change
for backlog #180 before this report was written. It is excluded from this
audit's conclusions.

## Baseline

- Source validator: `validate.ps1` exited 0 with `pass=99 warn=3 fail=0 skip=4`.
- Known validator advisories were not re-filed: two stale `routing_actions`,
  historical Work Log gaps, and tier-blind governance-eval coverage warnings.
- Current GitHub workflows parse as YAML: `security.yml` has 5 jobs and
  `validate.yml` has 12 jobs; both have zero dangling `needs` targets.
- Current release surfaces are aligned at 1.8.24 except the deployed
  Antigravity runtime guide, which still says 1.8.23.

## Already Known — Excluded from New Findings

| Tracking | Known gap | Revalidation in this audit |
|---|---|---|
| Backlog #180 | Bare pytest recurses into `.claude/worktrees` | Fix is present only as the pre-existing uncommitted `pytest.ini` diff; outside this audit scope. |
| Backlog #181 | No macOS CI runner | Still open; no new incident established here. |
| Backlog #182 | No machine guard keeps seven release-version surfaces aligned | **Live occurrence:** `.agentcortex/docs/guides/antigravity-v5-runtime.md:11` remained at v1.8.23 in the v1.8.24 release and in a fresh downstream deployment. |
| Backlog #183 | No test resolves workflow `needs` targets | Current graph is clean; an in-memory mutant with `needs: acx-missing-job` remains valid YAML, confirming the existing YAML parse checks do not cover graph integrity. |
| Backlog #184 | No Windows PowerShell 5.1 CI floor | Still open; not re-investigated because it is outside the selected three surfaces. |
| Repo gotcha #12 | Tag and GitHub Release are manual post-merge duties | Both duties were completed correctly for v1.8.24. |

## Release Surface Verification

| Surface | Observed version | Verdict |
|---|---:|---|
| `.agentcortex/bin/deploy.sh` | 1.8.24 | aligned |
| `CITATION.cff` | 1.8.24, released 2026-08-24 | aligned |
| Testing Protocol EN + zh-TW | 1.8.24 | aligned |
| Agent Model Guide EN + zh-TW | 1.8.24 | aligned |
| `CHANGELOG.md` newest heading | 1.8.24 | aligned |
| Antigravity runtime guide | **1.8.23** | **drift — tracked by #182** |

The annotated remote tag object `38afb2a` peels to release commit `a6b04a2`,
the same commit that carries the v1.8.24 release surfaces. GitHub Release
`v1.8.24` is published, non-draft, and non-prerelease:
<https://github.com/KbWen/agentic-os/releases/tag/v1.8.24>.

## Clean Downstream Simulation

- Source deploy command installed 205 files into an isolated empty target.
- Installer output identified `Agentic OS v1.8.24 (a6b04a2)` and the generated
  `.agentcortex-manifest` recorded `version: 1.8.24`.
- The deployed runtime guide reproduced the stale `v1.8.23` text, proving the
  drift reaches adopters rather than remaining source-only.
- After `git init`, deployed `validate.sh --no-python` exited 0 with
  `pass=76 warn=1 fail=0 skip=18`. The one WARN is the expected fresh-install
  absence of a guard receipt; the output labels reduced assurance explicitly.

## Disposition Funnel

| Hypothesis | Disposition | Reason |
|---|---|---|
| v1.8.24 may have no usable tag or Release | close-with-reason | Remote tag, peeled commit, and published GitHub Release all agree. |
| The shipped workflow graph may already contain a dangling dependency | close-with-reason | Both current graphs have zero dangling `needs` targets. |
| A fresh deploy may be structurally unusable | close-with-reason | Real 205-file deployment and downstream no-Python validation completed successfully. |
| Release metadata can drift while all current gates stay green | do-now via existing #182 | The predicted gap occurred in v1.8.24; do not create a duplicate row. Add the consistency test before the next release cut. |
| Workflow graph regressions are locally invisible | backlog via existing #183 | Current graph is healthy, so #183 remains hardening rather than a live repair. |

No novel finding survived deduplication: **0 new do-now, 0 new backlog, 3
close-with-reason, and 3 false alarms dropped**. The actionable result is
stronger evidence and urgency for existing backlog #182, followed by #183.

## External Signal

The published GitHub tag/Release is the external primary-source signal for the
release-state claims. No architecture-level conclusion relies only on a
same-vendor panel; no subagents were used.

```yaml
routing_actions: []
```
