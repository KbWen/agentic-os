---
status: shipped
primary_domain: deploy
signal_tier: none
created: 2026-07-21
backlog_ref: "#120"
---

# Spec: Deploy-End Enforcement Onboarding (Surfacing Half)

## Goal

At the end of `deploy.sh`, surface the three already-shipped enforcement on-ramps — (1) a run-now `validate.sh` self-check, (2) pre-commit hook activation, (3) a CI floor — as cross-platform-correct, non-destructive, honestly-scoped copy-paste commands, so an adopter who reads deploy output can turn enforcement ON immediately. This is a **pure surfacing change**: it installs nothing, adds no flag, and writes no file. It does not change what enforcement *exists* (all three primitives already ship downstream); it closes the gap that deploy-end never *names* them.

Scope boundary (per user ruling 2026-07-21): #120 is the **surfacing half**. Reaching the adopter who does *not* read deploy output (a machine-backed "enforcement is OFF" nudge) is a separate, precise follow-on item — deliberately NOT in this spec.

## Acceptance Criteria

- **AC-1**: `deploy.sh` end-of-run prints a visually-distinct enforcement-activation block naming all three on-ramps: (a) run-now `.agentcortex/bin/validate.sh` self-check, (b) pre-commit hook activation, (c) CI floor. Verify: run `deploy.sh` to a temp target; assert the block + all three ramps in stdout.
- **AC-2**: The hook-activation commands appear in BOTH a bash form (`cp … && chmod +x … && git config core.hooksPath .githooks`) AND a PowerShell form (`Copy-Item …; git config core.hooksPath .githooks`, no `chmod`), mirroring `docs/INSTALL.md:48-59`. Verify: assert both forms present in stdout. *(Fixes 第十人 #1 — bash-only breaks paste-in-PowerShell for Windows adopters.)*
- **AC-3**: The block carries a one-line caveat that `git config core.hooksPath .githooks` **replaces** any existing hooks path (husky / lefthook / custom `.git/hooks`) — integrate rather than overwrite if one is already in use. Verify: assert caveat substring in stdout. *(Fixes #2 — silent clobber, unwarned today.)*
- **AC-4**: The CI-floor wording is honestly scoped — it states that running `validate.sh` as a required check **gates framework structural integrity**, attributes secret scanning to the **pre-commit hook** (validate.sh performs none, and `security.yml` is not deployed downstream), and does NOT claim it enforces per-PR work-log / gate discipline (work logs are gitignored → CI-invisible). Verify: assert the block does NOT contain an over-promise like "your AI can't skip a gate"; assert the honest-scope phrasing is present. *(Fixes #5.)*
- **AC-5**: The current weak framing — `deploy.sh:1471` "Validate the installation (optional)" — is reframed so the self-check reads as the enforcement run-now step, not optional validation. This is a REFRAME of the existing "Next steps" block, not a second parallel block. Verify: assert the "(optional)" validation framing is gone; the run-now self-check is present.
- **AC-6**: No new deploy flag, no file written into the target repo, no interactive prompt. The deploy manifest golden (`tests/ci/fixtures/deploy_manifest_golden.txt`) is UNCHANGED (no new deployed file). No edit to `deploy.ps1` or `deploy_brain.ps1` (cross-platform parity holds because `deploy.ps1` execs `deploy.sh`). Verify: `git diff` touches no `.ps1`; golden test green unchanged.
- **AC-7**: A test pins the enforcement block's presence + key content (the `validate.sh` line, both bash & PowerShell activation forms, the clobber caveat, the honest CI-floor phrasing) via substring assertions, preventing drift from `INSTALL.md`. Verify: the new test fails if the block is removed or a form is dropped. *(Fixes #6; matches the README-canary discipline of pinning user-facing text.)*
- **AC-8**: The hooksPath-clobber caveat is added for cross-surface consistency to `docs/INSTALL.md` (near :48-59) and the `.githooks/pre-commit.guard-ssot.sample` header, so no activation surface prints the bare command uncaveated while another warns. Verify: grep the caveat present in all three surfaces (deploy block, INSTALL.md, sample header).

## Non-goals

- `--with-hooks` flag or any deploy flag (rejected B/C — awareness gap can't be fixed by a flag; full ps1 parity tax).
- Writing a `.github/workflows/*.yml` into the adopter repo (rejected D — ADR-005 imposition: core-tier clobbers existing CI, scaffold-tier dead-sidecars so the floor never activates; reddens the golden).
- Any interactive / TTY prompt (deploy is frequently piped; no `read -p` exists).
- The reach-mechanism for the non-reading adopter (validate self-advertise / bootstrap-detect) — separate follow-on item, filed at /ship.
- Changing what enforcement actually exists — all three primitives already ship; this is surfacing only.

## Constraints

- **Cross-platform parity (mandatory)**: satisfied for free (deploy.ps1 execs deploy.sh) for the *rendering*, BUT the PowerShell activation FORM must be correct (no `chmod`, `Copy-Item`, backslash paths) per `INSTALL.md` — "parity for free" is true for stdout, false for executability (第十人 #1).
- **ADR-005**: no new deployed file (would force a preservation-tier decision + golden regen). Print-only.
- **Token discipline**: the block is deploy STDOUT, not an AI-loaded governance surface, so it does NOT count against the lifecycle token ceiling (no always-loaded doc grows).
- **Honesty**: MUST NOT over-promise downstream enforcement (work logs gitignored → downstream CI-validate cannot read the work trail).
- **No new rule/gate** (`signal_tier: none`): this is a surfacing/wording change; it adds no MUST, NEVER, or gate.

## File Relationship

INDEPENDENT. Relates to `downstream-fork-accommodation.md` (ADR-005 tiering) and `dev-flow-hardening.md` (enforcement-truth) but replaces/extends neither.

## Domain Decisions

- [DECISION] Print-only surfacing chosen over flag/auto-install (B/C) or a written CI file (D): all three primitives already ship, so the gap is `echo`; the comparable-tool category (husky/pre-commit/lefthook/semantic-release) uses explicit activation, not magic install; parity-free; zero ADR-005 imposition. (Unanimous 3-seat roundtable.)
- [TRADEOFF] Print reaches only the adopter who READS deploy output — it does NOT reach the disengaged non-reader. Accepted for #120; the reach-mechanism is split into a separate follow-on (user ruling 2026-07-21). #120 is honestly the "surfacing half," not a full conversion guarantee.
- [CONSTRAINT] Any hook-activation command shown to adopters MUST appear in both bash and PowerShell forms (INSTALL.md precedent) and MUST carry the hooksPath-clobber caveat. Future edits to any activation surface (deploy block, INSTALL.md, sample header) must keep both properties in sync.
- [CONSTRAINT] Deploy-end enforcement wording MUST NOT claim downstream CI enforces work-log / gate discipline (work logs are gitignored, CI-invisible). It gates framework structural integrity only — secret scanning is the pre-commit hook's job (validate.sh performs none; `security.yml` is framework-CI-only, not deployed to adopters).
