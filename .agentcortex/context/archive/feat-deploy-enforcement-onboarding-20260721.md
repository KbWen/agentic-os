---
template: false
description: Work Log for backlog #120 — Deploy-end enforcement onboarding (conversion wedge).
---

# Work Log: feat/deploy-enforcement-onboarding

## Header

- Branch: `feat/deploy-enforcement-onboarding`
- Classification: `feature`
- Classified by: `claude-opus-4-8`
- Frozen: `2026-07-21`
- Created Date: `2026-07-21`
- Owner: `claude-opus-4-8 (session 40c9ba5b)`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `ed8b7d0b8ebc76b21be60395514c416c0a8fb815`
- Checkpoint SHA: `0dedc763a9969ec43a3fb69d30a402f5812cf49d`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `127`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-07-21 (session 40c9ba5b)`
- Platform: `claude-code`
- Files Read: `6`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §5, §12 (implement/test), §13 (governance-norms) — full-file read at bootstrap.

---

## Task Description

Backlog #120 (P1, conversion wedge): a default install ends with ZERO active machine enforcement — the pre-commit hook is opt-in (activation buried in the sample header), deploy prints no CI/branch-protection recipe, and the deploy-end "Next steps" frames `validate.sh` as optional validation rather than an enforcement self-check. Surface the three already-shipped enforcement on-ramps (credential/validator hook · CI floor · post-deploy self-check) at deploy end so an adopter can turn enforcement on immediately. **Constraint (user-directed): keep it LIGHT — no new mandatory gate, no adopter friction, no AI-constraining machinery. This is a surfacing change, not a new enforcement mechanism.**

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-21 | classify=feature; branch+worklog created |
| plan | in_progress | 2026-07-21 | roundtable+第十人 done; user scope ruling; spec written |
| implement | done | 2026-07-21 | 5 files +150/-9; 11/11 tests pass; scan clean |
| review | done | 2026-07-21 | acx-reviewer: HIGH-1 secret-scan over-promise, fixed; re-review PASS |
| test | done | 2026-07-21 | pytest 42 passed; validate fail=2 both non-deliverable (triaged) |
| handoff | done | 2026-07-21 | Resume block written; CI-clean (fail=1 local work-log only); awaiting commit auth |
| ship | done | 2026-07-21 | committed 0dedc76; SSoT+backlog updated; PR pending |

---

## Phase Summary

**bootstrap (2026-07-21)** — Read SSoT + full engineering_guardrails + deploy.sh (1487L) + deploy.ps1 (86L, thin bash wrapper) + installers/deploy_brain.sh + pre-commit.guard-ssot.sample + backlog #120. Ground truth: (a) deploy.ps1 delegates all logic to deploy.sh, so the deploy-end output block (deploy.sh L1470–1479 "Next steps") is a SINGLE cross-platform edit point — parity is free. (b) All three enforcement primitives already ship downstream (hook sample scaffold-tier L1053–1056; credential floor inside the hook; validate.sh). The #120 gap is surfacing, not building. Classification = `feature` (alters default deploy output seen by every adopter; conversion-critical; will produce a spec + run /handoff). Design tension deferred to /plan roundtable: print-only surfacing vs `--with-hooks` flag (note: deploy.ps1 L85 forwards only `$Target`, so a flag adds a real ps1 parity cost) vs hybrid; CI recipe print vs written `.github/workflows` file (ADR-005 preservation-tiering + presumptuousness concerns).

**plan (2026-07-21)** — Roundtable (3 seats) + 第十人 complete; user ruled scope = surfacing-only (reach-mechanism → separate follow-on). Spec `docs/specs/deploy-enforcement-onboarding.md` written (draft, 8 AC, `signal_tier: none`). Target = 4 files (deploy.sh block reframe + INSTALL.md/sample caveat + 1 deploy test); no `.ps1` edit (parity via wrapper), no new deployed file (golden unchanged). | Confidence: 93% — high

**implement (2026-07-21)** — deploy.sh end block reframed → "TURN ON ENFORCEMENT" (3 on-ramps: run-now validate.sh · hook activation with bash+PowerShell forms + hooksPath-clobber caveat · honest CI-floor recipe); "Validate the installation (optional)" framing dropped (AC-5). Clobber caveat mirrored to INSTALL.md + hook sample header (AC-8). +3 tests in test_deploy_tiering.py (source drift-pin · caveat-consistency · behavioral render). Scope = 5 files (+150/−9), NO `.ps1` edit (parity via wrapper). Verified: 11/11 pytest pass (incl. golden snapshot green — list-only, so content change ≠ golden drift, AC-6); real deploy→temp renders block + "Validate the installation (optional" count=0 (AC-5); credential scan exit 0. | Confidence: 95% — high

**review (2026-07-21)** — Fresh-context acx-reviewer on the staged diff: AC-1/2/3/5/6/7/8 PROVEN, but **HIGH-1 → NOT READY**: the CI-floor + step-1 wording over-promised "secret scanning" / credential checks BY validate.sh. Primary-verified real: `validate.sh:2607` is only a security.yml-presence WARN (zero secret detection); security.yml/TruffleHog is NOT deployed downstream (golden has no `.github/workflows`); secret pre-screen lives in the pre-commit HOOK (`scan_credentials.py`). Exactly the AC-4 / 第十人-#5 over-promise class — I fixed the old one and introduced a new one; reviewer caught it. Fix: step 1 → "governance + structural checks pass"; step 3 → "Gates ... structural integrity ... secret scanning stays in the hook above"; +3 test pins (2 negative guards + 1 honest-attribution). Re-verified: 4/4 pytest green, rendered wording honest, `secret scanning in CI`=0. Re-review PASS. LOW-1 (PS `/` vs INSTALL.md `\`) accepted (PowerShell normalizes `/`). | Confidence: 95% — high

**test (2026-07-21)** — Full CI-equiv subset: `pytest test_deploy_tiering.py test_pre_commit_hook.py` → **42 passed** (4.5min; tiering/golden/hook + my 3 new incl. negative over-promise pins). EOL confirmed LF (od -c bytes + `git ls-files --eol` = `i/lf w/lf`; the earlier `grep -c \r`=1510 was a `git show` autocrlf-smudge artifact, not real CRLF). `validate.sh --no-python`: pass=96 warn=5 **fail=2** — both triaged NON-deliverable: (a) my work-log size 204L > threshold [local-only, work logs gitignored → CI fail=0; clearing at /handoff §6 compaction], (b) pre-existing routing_actions on `docs/reviews/2026-07-01-governance-premortem.md` + `2026-07-16-govern-audit-decision-capture.md` [NOT in my diff; `--no-python` native backstop is stricter — CI runs Python `check_routing_actions.py`, green on main per Ship History]. Full Python validate running (background) to confirm zero new FAIL from this change. | Confidence: 92% — high (pending full-validate + compaction)

**handoff (2026-07-21)** — Resume block + Read Map/Skip List/Context Snapshot written (AI-discoverable). Full Python validate confirms CI-clean: fail=1 = local gitignored work-log compaction only (CI fail=0); routing_actions PASS on the Python check (the `--no-python` FAIL was the weaker native backstop #137). WIP staged-uncommitted by design (commit gated on user auth). Closure recommendation: **OPEN PR after user authorizes commit**. | Confidence: 95% — high

**ship (2026-07-21)** — Ship gate PASS. SSoT updated: Ship History top-entry + v1.8.10 rotated to `archive/ship-history-2026.md` (cap 10 held), Spec Index + spec `status: shipped`, Update Sequence 127→128, dates→2026-07-21. Backlog #120 → **Shipped**; reach-mechanism filed as follow-on **#142**. Knowledge consolidation skipped (justified): no `deploy` domain doc exists; this surfacing/wording change introduces no new deploy-architecture decision requiring L2 — the constraints live in the spec + Ship History. Decision disposition: D-1..D-4 → local. Next: commit 5 files → archive Work Log + INDEX.jsonl → push + open PR → lock release. | Confidence: 96% — high

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T01:00:00Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T02:00:00Z
- Gate: review | Verdict: NOT READY | Classification: feature | Timestamp: 2026-07-21T03:00:00Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T03:30:00Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T04:00:00Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T05:00:00Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T06:00:00Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-07-21T07:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/deploy-enforcement-onboarding.md | to be created at /plan |
| ADR | — | none expected (no new architectural decision; ADR-005/008 govern) |
| Issue | docs/specs/_product-backlog.md #120 | backlog-only, no GH issue (P1 conversion wedge) |
| PR | — | — |

---

## Known Risk

- **Over-light risk**: a pure print-only change may not move conversion vs. the existing (buried) instructions — the 第十人 must pressure-test whether surfacing alone is a real behavior change. Mitigation: roundtable adjudication at /plan.
- **Parity risk**: if the design adds a `--with-hooks` flag, deploy.ps1 (L85) + deploy_brain.ps1 must forward it or the flag silently no-ops on Windows (ref Global Lesson [cross-platform-cli]: `--flag` does not bind PowerShell `[switch]`).
- **Presumptuousness risk**: writing a CI workflow file or auto-installing hooks imposes files/config the adopter did not request (ADR-005 tiering). Mitigation: default to print-only unless roundtable overrides.

---

## Decisions

> Source: 3-seat design roundtable (conversion / minimalism / maintenance-parity, background subagents 2026-07-21) — UNANIMOUS on Option A. Pending 第十人 refutation before freeze. At `/ship`, each entry gets a disposition marker.
>
> **Ship disposition (2026-07-21)**: D-1 → local · D-2 → local · D-3 → local · D-4 → local — all are design/process decisions; durable homes are the spec's `## Domain Decisions`, the Ship History entry, and backlog follow-on #142. None names an ADR or reverses a durable decision, so `→ local` is legal (ship.md §2b).

### D-1: Ship Option A — print-only deploy-end enforcement surfacing
- **Decision**: #120 ships as a print-only reframe of the deploy-end output (deploy.sh tail ~L1457–1479), surfacing the 3 already-shipped on-ramps — (1) run-now `validate.sh` self-check, (2) pre-commit hook activation, (3) a CI-floor recipe — plus a "paste to your AI" escape hatch. NO new flag, NO written CI file, NO interactive prompt.
- **Reason**: Unanimous roundtable + external evidence. The comparable-tool category converged on prominent copy-paste activation, NOT magic install: husky v9 REMOVED auto-install (maintainer post-mortem: auto-install hides the confirmation new devs rely on); pre-commit.com requires explicit `pre-commit install` (its famous footgun = agentic-os's exact disease); lefthook/semantic-release default manual/print-degrade. All 3 primitives already ship downstream → #120's gap is surfacing (= `echo`). deploy.ps1 execs deploy.sh → cross-platform for free; no stdout golden test exists → zero required test churn.
- **Alternatives rejected**: B (`--with-hooks` flag) — a flag only fires if the adopter already knew it exists, so it serves the already-converted and does nothing for the discovered-not-converting cohort (can't fix an awareness gap); + full 3-file ps1 parity tax. C (hybrid) — inherits B's tax for a convenience the copy-paste line already delivers. D (write `.github/workflows/*.yml`) — preservation-tiering imposition (core-tier clobbers an adopter's existing CI; scaffold-tier dead-sidecars to `.acx-incoming` so the floor never activates → defeats the goal), reddens the manifest golden, crosses surfacing→mechanism.
- **Impact**: adopter sees enforcement activation as the deploy headline instead of today's "Validate the installation (optional)"; conversion lever added at zero new mechanism / zero parity / zero governance weight.

-> local

### D-2: Right-size the block (~15–18 lines), reframe not append
- **Decision**: block sits between the minimalism 4-liner and the conversion ~30-liner: a cost-of-nothing header + 3 inline-actionable ramps (one short why each) + the AI-paste escape hatch; it REPLACES the weak "Next steps → validate (optional)" framing rather than adding a parallel block; existing git-add / run-/bootstrap / docs lines are folded in, not duplicated.
- **Reason**: 4 lines drops the skimmer-catching cost-of-nothing framing + the AI-lever (both give print teeth per the husky evidence); the ~30-line version is terminal-noise. Reframe (not append) because the current "validate optional" line IS the defect #120 names. CI ramp prints a described recipe, NOT a full YAML block or an error-prone `gh api` incantation.
- **Impact**: honest, scannable, ~15–18 lines; single edit point.

-> local

### D-3: De-risk mechanisms are FOLLOW-ON, not bundled (scope discipline)
- **Decision**: the conversion seat's higher-leverage de-risks — (a) wire `/bootstrap` to detect `git config core.hooksPath != .githooks` and offer activation, (b) make `validate.sh` self-advertise the hook nudge when inactive — are explicitly OUT of #120 scope, flagged as a separate follow-on candidate.
- **Reason**: both ADD mechanism/behavior (bootstrap detection logic; validate output logic) → collide with the "don't make governance heavier / don't make the AI dumber" north-star; (a) is an honor-system bootstrap instruction (the [enforcement] Global Lesson class — a should/MUST with no machine backing = theatre + permanent token cost on an always-loaded surface). The "paste to your AI" print line already captures most of the AI-lever value at zero mechanism.
- **Alternatives**: bundle them (rejected — scope creep + mechanism weight); drop entirely (rejected — real levers worth their own enforce-vs-honest evaluation).
- **Impact**: #120 remains light; de-risk deferred to a separate backlog candidate.

-> local

### D-4: 第十人 adjudication + user scope ruling (2026-07-21) — FINAL locked design
- **Verified defects adopted** (folded into spec AC): #1 bash+PowerShell activation forms (INSTALL.md:48-59 precedent), #2 hooksPath-clobber caveat, #5 honest CI-floor wording (downstream CI can't read gitignored work logs), #6 +1 substring test pinning the block.
- **D-1 softened** (#4): husky/pre-commit precedent is double-edged (husky kept npm-`prepare` lifecycle auto-activation; pre-commit's teeth are CI) — it shows explicit activation is NORMAL, not that print-only CONVERTS. "externally validated" → "externally consistent".
- **D-1 trimmed** (#7): AI-paste escape hatch DROPPED — smuggles unreviewed Option D (AI writes a CI file) + unwatched hooksPath clobber + no-op on manual-entry platforms (CLAUDE.md/GEMINI.md).
- **User ruling on scope fork #8/#9 (2026-07-21)**: ship the fixed surfacing as #120, honestly labeled the "surfacing half" (NOT "done-as-if-converts"); the reach-mechanism becomes a SEPARATE precise follow-on. Acknowledged: `git config --get core.hooksPath` IS machine-observable (D-3's "theatre" framing was wrong for the detection itself), but whether /bootstrap runs it + validate.sh's CI/hook context-confusion need their own light design in that item.
- **Follow-on to file at /ship**: "Enforcement reach-mechanism — surface 'enforcement is OFF' to the disengaged adopter via a machine-backed nudge. Candidate A: validate.sh/.ps1 advisory when `core.hooksPath != .githooks` && not CI. Candidate B: /bootstrap core.hooksPath check + offer. Decide A-vs-B + enforce-vs-honest at its own plan. Pairs with #120."
- **Classification stays `feature`**: user-facing default deploy-output change + spec written + /handoff will run. Process rigor kept; product kept light (per user north-star — the two are compatible).

---

-> local

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- **Spec imprecision found at /review (2026-07-21)**: frozen spec AC-4 prose says CI-validate enforces "framework structural integrity + (with the shipped security.yml) secret scanning" — but `security.yml` is NOT deployed downstream (golden has no `.github/workflows`), so that parenthetical is factually off. The implementation honestly supersedes it (validate.sh = structural integrity; secret scanning = the pre-commit hook). Frozen spec NOT edited (§4.2 requires user unfreeze YES — No Bypass Rule). Flagged to user at the pre-commit checkpoint: unfreeze + fix the 1-line parenthetical, OR accept as historical (the block + tests are the enforced honest artifacts).
- **Handoff WIP state (2026-07-21)**: 5 files staged but UNCOMMITTED by design — commit gated on user authorization (stated plan + "commit only when authorized"). WIP is anchored in the git index (scopable via `git diff --cached`), satisfying the /handoff §1a WIP-guard intent without a premature commit. Checkpoint SHA left at pre-implement HEAD (`ed8b7d0`); Resume block documents the staged state.
- **Compaction deferred to ship-archival (2026-07-21)**: /handoff §6 threshold hit (204L/18KB) — FAIL is LOCAL-ONLY (work logs gitignored → CI fail=0, confirmed by full Python validate fail=1=this). Deferred to /ship §3 whole-log archival next phase; a mid-flight §6 overflow to `archive/work/` would create a redundant second archive file for one task. Header Current Phase synced implement→handoff (clears the lock/header phase-mismatch WARN).

---

## Review Feedback

### HIGH-1 (acx-reviewer, VERIFIED real, FIXED) — CI-floor secret-scanning over-promise
- **Finding**: the block claimed validate.sh (as a CI check) enforces "secret scanning" + step 1 claimed validate.sh runs "credential checks". Primary-verified ground truth: `validate.sh:2607` only WARNs on `security.yml` ABSENCE (zero secret detection); security.yml/TruffleHog is NOT deployed downstream (`deploy_manifest_golden.txt` has no `.github/workflows`); secret pre-screening is the pre-commit HOOK's job (`scan_credentials.py`/`credential_floor.sh`). Real over-promise (AC-4 / 第十人-#5 class).
- **Fix**: step 1 → "confirms the framework's governance + structural checks pass"; step 3 → "Gates the framework's structural integrity on every PR (secret scanning stays in the hook above; ...)"; +3 pins in `test_deploy_source_surfaces_enforcement_onramps` (assert `secret scanning in CI` absent, `credential checks work on this repo` absent, `secret scanning stays in the hook` present). Re-verified green + rendered.
- **LOW-1** (PS `Copy-Item` forward-slash vs INSTALL.md backslash): accepted — PowerShell normalizes `/`; non-blocking cosmetic.

---

## Red Team Findings

> 第十人 (refute-only subagent, 2026-07-21) vs D-1/D-2/D-3. 9 objections; primary verified the load-bearing ones against ground truth before adopting (per [verify-subagent-self-reports] Global Lesson).

**VERIFIED REAL (adopt — fix in design):**
- **#1 bash-only activation fails in PowerShell** — CONFIRMED: `docs/INSTALL.md:48-59` already ships a SEPARATE PowerShell variant (`Copy-Item`, chmod dropped) alongside the bash one. A deploy-end block printing only the bash one-liner (`cp && chmod && git config`) breaks paste-in-PowerShell for every Windows adopter (chmod → error → `&&` chain aborts → hooksPath never set). Fix: print bash + PowerShell forms (mirror INSTALL.md).
- **#2 `core.hooksPath .githooks` silently clobbers existing hooks** — CONFIRMED: repo-wide grep (README/INSTALL/.githooks) shows ZERO clobber warning; git uses ONLY hooksPath when set, so an adopter on husky/lefthook/custom `.git/hooks` loses them unwarned. Internal inconsistency: roundtable rejected D for "clobbers adopter CI" but A's command clobbers adopter hooks. Fix: add clobber caveat to the block (+ sample header / INSTALL.md).
- **#5 CI-floor over-promises** — CONFIRMED: `.gitignore:4` gitignores `.agentcortex/context/work/*.md`, so downstream CI running validate.sh CANNOT read work logs → the "validate.sh reads the work trail / AI can't skip a gate" enforcement never fires downstream (matches memory project_worklog_count_local_artifact + #120's own filed text). Downstream validate.sh enforces framework structural integrity + (with security.yml) secret scanning, NOT per-PR gate/work-log discipline. Fix: scope the CI wording honestly.
- **#6 block ships untested** — ADOPT: no stdout golden exists (`in`/`not in` substring asserts only); a safety-relevant copy-paste command would drift unpinned (memory project_readme_validator_canary: user-facing text is pinned BECAUSE it drifts). Fix: +1 substring test pinning the block.

**REFRAMED (partial adopt):**
- **#4 husky/pre-commit precedent is double-edged** — husky v9 kept npm-`prepare` LIFECYCLE auto-activation (removed only phone-home self-install); pre-commit's real teeth are CI (`run --all-files` required check ≈ Option D). Supports "explicit activation is normal", does NOT prove print-only SUFFICIENT. Downgrade D-1's "externally validated" claim.
- **#7 AI-paste escape hatch** — drop/trim: same read-dependency; if the AI acts it sets hooksPath (the #2 clobber, now unwatched) + writes a CI file (= rejected Option D, unreviewed); manual-entry platforms (CLAUDE.md/GEMINI.md) may have no shell agent to paste to.

**STRATEGIC — SCOPE FORK (surfaced to user):**
- **#3/#8/#9 print targets the non-reader; D-3 discoverability argument inverted** — `git config --get core.hooksPath` IS machine-observable, so the deferred /bootstrap-detect is NOT the honor-system "theatre" D-3 claimed; it lives on an AI-discoverable every-session surface (project north-star) while print-only is a one-time human-memory artifact. 第十人's minimum ask: do NOT mark #120 "done-as-if-it-converts" on print-only alone. → escalated to user as the mechanism-vs-lightness scope decision (their two explicit values in tension).

---

## Design Reference

none

---

## Observability

none

---

## Resume

- State: HANDEDOFF (feature; implement+review+test complete; awaiting user commit authorization → /ship)
- Completed: bootstrap → plan (roundtable + 第十人 + user scope ruling) → spec (frozen) → implement → review (HIGH-1 fixed) → test (42 pytest green; full Python validate fail=1 = local work-log compaction only)
- Next: user authorizes commit → /ship (commit 5 files, archive work log, update SSoT Ship History + backlog #120 Shipped-surfacing, file the reach-mechanism follow-on, open PR)
- Context: #120 surfacing-only per user ruling — deploy-end reframed to surface 3 enforcement on-ramps (bash+PowerShell forms, hooksPath-clobber caveat, honest CI wording); reach-mechanism split to a follow-on. Print-only chosen unanimously (roundtable) + externally consistent (husky/pre-commit). All defects (第十人 ×3 + reviewer HIGH-1 secret-scan over-promise) fixed + pinned.

### Read Map (for next agent)
- `.agentcortex/context/work/feat-deploy-enforcement-onboarding.md` → full (Decisions + Review Feedback + Gate Evidence)
- `docs/specs/deploy-enforcement-onboarding.md` → full (frozen spec, 8 AC)
- `.agentcortex/bin/deploy.sh` → the "TURN ON ENFORCEMENT" block (~L1470–1500)

### Skip List
- `tests/ci/test_deploy_tiering.py` — the 3 new tests are green + pinned; no re-run unless the deploy.sh block is edited
- `installers/deploy_brain.*`, `.agentcortex/bin/deploy.ps1` — NOT touched (parity via wrapper); no read needed
- `docs/reviews/*` — the `--no-python` routing_actions FAIL there is pre-existing, not this change (Python check PASSes)

### Context Snapshot (≤200 tokens)
#120 = deploy-end enforcement surfacing (print-only, light). Design locked via 3-seat roundtable (unanimous Option A) + 第十人 (3 verified defects fixed) + user scope ruling (surfacing-only; reach-mechanism = follow-on). Implemented: deploy.sh end block reframed (3 on-ramps, bash+PowerShell forms, hooksPath-clobber caveat, HONEST CI wording — secret scanning attributed to the hook, not validate.sh); caveat mirrored to INSTALL.md + hook sample; 3 pinning tests incl. negative over-promise guards. Verified: 42 pytest green; full Python validate fail=1 = local gitignored work-log compaction only (CI fail=0). EOL confirmed LF. Uncommitted: 5 files staged, awaiting user commit auth. OPEN for user: frozen-spec AC-4 parenthetical "(with the shipped security.yml)" is imprecise (security.yml not deployed downstream) — unfreeze+fix or accept as historical.

### Backlog Status
- Active Backlog: `docs/specs/_product-backlog.md`
- Current Feature: #120 Deploy-end enforcement onboarding — implement/review/test done, awaiting commit auth
- Remaining: reach-mechanism follow-on (file at ship); #121 README enforcement-matrix (next top pick)
- Next Recommended: #121 (pairs with #120) — user choice

---

## Test Gate Results

- Command: `pytest tests/ci/test_deploy_tiering.py tests/ci/test_pre_commit_hook.py` → **42 passed** (4.5min). New: `test_deploy_source_surfaces_enforcement_onramps` (incl. negative over-promise pins), `test_enforcement_clobber_caveat_is_consistent_across_surfaces`, `test_deploy_stdout_renders_enforcement_block`.
- Framework gate: `validate.sh` (full Python, CI-equiv) → **pass=114 warn=6 fail=1**; the sole FAIL = this Work Log's own compaction (204L, local-only — work logs gitignored → CI fail=0). routing_actions PASS (Python check); the `--no-python` routing_actions FAIL was the weaker native backstop (#137), not a real issue.
- Rollback: revert the PR (5 files; no engine/logic change; deploy manifest golden is list-only, unchanged).

---

## Evidence

- bootstrap file reads: `.agentcortex/context/current_state.md`, `.agent/rules/engineering_guardrails.md`, `.agentcortex/bin/deploy.sh` (L1420–1487 + grep), `.agentcortex/bin/deploy.ps1`, `installers/deploy_brain.sh`, `.githooks/pre-commit.guard-ssot.sample`.
- Ground-truth verified: deploy.ps1:85 `& $bashLauncher $bashScript "$Target"` (thin wrapper → single output edit point); deploy.sh:1053-1056 hook sample deployed scaffold-tier; deploy.sh:1470-1479 current "Next steps" block.
- **Demonstration** (§72, deploy-output change): `bash .agentcortex/bin/deploy.sh <temp>` renders the "TURN ON ENFORCEMENT" block; verified in stdout: `secret scanning stays in the hook`=1, `secret scanning in CI`=0, `credential checks work on this repo`=0, `Validate the installation (optional`=0. Behavioral test `test_deploy_stdout_renders_enforcement_block` PASSES. Full deploy+hook suites 42 passed; full Python validate green on the deliverable (sole local fail = this gitignored log's own compaction). CI anchor: `test_deploy_manifest_snapshot` (golden list-only, unchanged).
