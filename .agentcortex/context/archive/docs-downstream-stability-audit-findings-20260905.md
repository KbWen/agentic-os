# Work Log: docs/downstream-stability-audit-findings

## Header

- Branch: `docs/downstream-stability-audit-findings`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-09-05`
- Created Date: `2026-09-05`
- Owner: `claude-code-session-15324ef8`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `93d0542`
- Checkpoint SHA: `e809006`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `166`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-09-05`
- Platform: `claude-code`
- Files Read: `24`
- Downstream-Capabilities: `none`

---

## Task Description

Record the verified findings of a downstream-simulation + governance-brain audit
into `_product-backlog.md`, and open one public GitHub issue for the single
lowest-severity, self-contained item. Report-only intake: no framework code or
governance rule is changed on this branch.

---

## Gate Evidence

- gate: bootstrap | classification: quick-win | verdict: pass | timestamp: 2026-09-05 | missing: []
- gate: plan | classification: quick-win | verdict: pass | timestamp: 2026-09-05 | missing: []
- gate: implement | classification: quick-win | verdict: pass | timestamp: 2026-09-05 | missing: []
- gate: ship | classification: quick-win | verdict: pass | timestamp: 2026-09-05 | missing: []
- Classification rationale: the change touches `docs/specs/_product-backlog.md`,
  which `engineering_guardrails.md §10.3` excludes from `tiny-fix`. Scope is a
  single file plus one GitHub issue, so `quick-win` (not `feature`).
- `quick-win` is exempt from `/handoff` per `AGENTS.md §Delivery Gates`; evidence
  is supplied below in `## Evidence`.

---

## Drift Log

- Archival deliberately NOT performed. The validator's `shipped work logs still in active work/ directory (archival incomplete - /ship step 3 skipped?)` WARN is CORRECT and expected here: the ship phase produced commit + push + PR #431, but the PR is not merged. Archiving a log for unmerged work would assert a completion that has not happened. Move this log to `.agentcortex/context/archive/` only after #431 merges. Do not treat the WARN as a missed step before then.

- `_product-backlog.md` written outside `/ship`. Permitted by
  `AGENTS.md §Write Isolation` (backlog updates during spec-intake/ship are a
  named exception). `current_state.md` NOT touched.
- Re-read: none.

---

## Evidence

All six rows were reproduced by the primary agent directly, not accepted from a
subagent report. Commands are copy-pasteable; targets live under the session
scratchpad, never in the repo.

### E1 — brownfield first install destroys pre-existing core-tier files (#188)

```
git init app && cd app
printf 'KEEPME\n' > .agent/rules/engineering_guardrails.md   # untracked, never committed
bash <repo>/.agentcortex/bin/deploy.sh .
grep -c KEEPME .agent/rules/engineering_guardrails.md   # -> 0  (sentinel gone)
git log --oneline -- .agent/rules/engineering_guardrails.md | wc -l   # -> 0  (unrecoverable)
grep -cE 'engineering_guardrails|commands/plan' deploy.log            # -> 0  (zero warning)
grep -c '^core ' .agentcortex-manifest                                # -> 142 affected paths
```
deploy exit code: `0`. `AGENTS.md` / `CLAUDE.md` were correctly preserved with
`.acx-incoming` sidecars and an explicit `[SKIP]` line — the defect is that the
core tier has no equivalent path.

### E2 — brownfield install ends validator-RED while the banner reports "Ready" (#193)

```
bash .agentcortex/bin/validate.sh   # in the same brownfield target
```
`Summary: pass=83 warn=1 fail=3 skip=8` / `Agentic OS integrity check failed`
(exit 1). Failures: `safety nucleus freshness`, `work log contract references
are stale`, `AGENTS.md missing routing index reference (authority handoff
absent)`. The same run's banner printed `Platform Entry Points Ready`.

### E3 — Active Backlog token cost understated ~170x (#189)

```
awk '/^## Feature Inventory/,/^## [^F]/' docs/specs/_product-backlog.md | wc -c   # -> 137998
wc -c docs/specs/_product-backlog.md                                              # -> 139206
```
The Feature Inventory table is 99.1% of the file, so "read ONLY the table" is not
a mitigation. ~34,800 tokens against a claimed `~200 tokens` at `AGENTS.md:36`,
`bootstrap.md:171`, `spec-intake.md:64,349,362`.

### E4 — validators ignore `downstream_capabilities.path` (#190)

```
grep -n 'path:' .agent/config.yaml            # 112: .agentcortex/context/private/downstream-capabilities.yaml
grep -n 'downstream-capabilities' .agentcortex/bin/validate.sh   # 647: CAP_FILE hardcoded
grep -n 'downstream-capabilities' .agentcortex/bin/validate.ps1  # 791: $capFile hardcoded
grep -n 'downstream_capabilities.path' .agent/workflows/bootstrap.md  # 116
```
`bootstrap.md:116` instructs the agent to honour the config key; both validators
hardcode the default. Retargeting `path:` therefore leaves the gate-safety check
looking at a nonexistent file.

### E5 — deployed `.gitignore` omits `__pycache__/` and `*.pyc` (#191)

```
grep -nE '__pycache__|\*\.pyc' .gitignore                    # (target)  -> no match
grep -nE '__pycache__|\*\.pyc' <repo>/.gitignore             # (source)  -> 50,51
bash .agentcortex/bin/validate.sh && find . -name '*.pyc' | wc -l   # -> 2
```
The source repo protects itself; the deployed ignore block does not ship that
protection, and the deploy banner's own `git add ... .agentcortex/ ...` stages
the bytecode.

### E6 — `repo-gotchas.md` ships citing undeployed test paths (#192)

Full-path citations absent from a deployed target:
`.agentcortex/tests/test_lifecycle_token_consumption.py`,
`tests/ci/test_deploy_tiering.py`, `tests/ci/test_pre_commit_hook.py`,
`tests/ci/test_subprocess_encoding.py`. Bare basenames in the same file are the
known false-positive class described by backlog #185 and are excluded here.

### E7 — independent baseline (not a finding)

```
python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q   # exit 0, 940 tests
python .agentcortex/tools/check_ssot_caps.py                      # exit 0
```
CI-equivalent suite is fully green on Windows / Python 3.14. Ship History sits at
`10/10` and Spec Index at `27/30` — near-zero headroom, already tracked by the
lifecycle backlog rows (#1/#3/#13), not re-filed here.

---

## Decisions

- Filed six rows, not more. Findings that were reported by a subagent but not
  reproduced by the primary agent are deliberately NOT filed — the audit
  workflow was still running when this branch was cut, and unverified findings
  would violate `feedback_evidence_before_adding`.
- Only ONE finding is exposed as a public GitHub issue (#191). Per the issue
  exposure policy the backlog tracks everything; issues are reserved for
  feature-like, self-contained items. #191 is additive, lowest-severity, and has
  no design ambiguity.
- No fix is attempted on this branch. #188 is a data-loss defect whose fix
  changes ADR-005's preservation contract and therefore needs its own spec.

---

## Phase Summary

Read-only downstream simulation of the deploy + validate surface (greenfield,
brownfield, upgrade, zero-Python, Windows paths, capability seam) plus a
governance-brain consistency pass. Six findings were reproduced by the primary
agent and recorded as backlog rows #188-#193; the highest-severity one is a
silent, unrecoverable overwrite of pre-existing files across 142 core-tier paths
on a brownfield first install. One low-severity row (#191) was additionally
opened as a public GitHub issue. The framework's own CI-equivalent suite (940
tests) is green, so the defects are all in the downstream-facing surface rather
than in the framework's self-checks.

---

## Handoff — unfinished audit work

**Status of this branch:** complete and green. Rows #188–#193 landed, issue #430 open, CI pass. Nothing here is blocked.

What follows is the work this session did **not** finish, recorded so a later session can resume without re-deriving it.

### 1. The audit was stopped at 8/16 agents

A 16-agent simulation was launched and deliberately halted at 8 returned reports to conserve budget. **Eight scenarios never returned**, so their surfaces are *unaudited*, not *clean*:

| Not returned | Surface left unaudited |
|---|---|
| `S1-greenfield` | virgin-install validator noise; manifest-vs-disk spot check |
| `S3-upgrade` | re-deploy idempotency; local-modification tiering; orphan removal; stale-manifest handling |
| `S4-zero-python` | **highest-value gap** — whether a never-run check reports as PASS when Python is absent; no-Python credential floor |
| `S5-windows-native` | space-in-path installs; `compute_sha256` backslash hazard; CRLF on deployed `.sh` |
| `S6-context-bleed` | non-git and nested-in-parent-repo targets; worklog-key derivation on hostile branch names |
| `A3-platform-parity` | `validate.sh` vs `validate.ps1` check-for-check diff (3105 vs 2895 lines — unexplained) |
| `A4-skill-wiring` | whether `.agents/skills/*/SKILL.md` bodies actually ship downstream |
| `A8-gate-integrity` | the bypass battery (phase skipping, forged receipts, lock stealing, `INDEX.jsonl` tamper) |

Re-running is cheap to restart: the workflow script is saved and resumable, and completed agents return cached results.

- Script: `~/.claude/projects/<proj>/<session>/workflows/scripts/downstream-stability-audit-wf_15af2b9b-3f2.js`
- Resume: NOT POSSIBLE from a new conversation — `resumeFromRunId` is same-session-only. Use the plain-shell recipe in backlog row #194 instead.
- Journal (raw returns of the 8 that did finish): the run's `journal.jsonl` in the sibling `subagents/workflows/wf_15af2b9b-3f2/` directory

### 2. Reported-but-unverified findings were intentionally NOT filed

The 8 returned reports contained roughly a dozen further findings that the primary agent did **not** reproduce. They are not in the backlog on purpose — filing unverified findings would violate the evidence-before-adding norm. They are recoverable from `journal.jsonl` if someone wants to verify them later. Recurring themes worth a look, in rough order of how often independent agents hit them:

- the deploy banner's `git add` line omitting `.gitignore` / `.githooks/` / `.gitattributes` (3 independent agents)
- `security_guardrails.md §6`'s "ship gate = FAIL" labelled T1-enforced with no enforcing mechanism found
- the 355k token ceiling being enforced by zero *required* status checks
- `.codex/INSTALL.md` describing the git hook's behaviour incorrectly
- `.agentcortex/docs/README.md` shipping as the repo-root README, dangling its intra-doc links downstream

### 3. Next actions, in priority order

1. **#188** needs a spec before any code — the fix amends ADR-005's preservation contract. Do not patch the branch directly.
2. **#190** is the smallest real fix (path resolution in both validator twins; parity required).
3. Re-run the audit's `S4-zero-python` scenario on its own — it is the one unaudited surface with a plausible false-pass.
4. **#191** is issue-ready and unblocked if someone wants a warm-up task.

### 4. Verified-good (do not re-audit)

- CI-equivalent suite: 940 tests, exit 0, Windows / Python 3.14.3
- 14/14 skill stub↔body pairs aligned; 30/30 slash commands backed by a canonical workflow, zero dangling
- CI docs-only classifier is a fail-safe allowlist, and the `docs-pins` job correctly covers the pin tests the heavy suite would skip (both README-asserting tests carry `@pytest.mark.docs_pin`) — confirmed live on this PR
- Platform entry points (`AGENTS.md` / `CLAUDE.md`) *are* correctly sidecar-preserved on brownfield installs; the #188 defect is specific to the core tier

⚡ ACX
