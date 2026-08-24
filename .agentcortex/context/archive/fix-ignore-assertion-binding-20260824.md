# Work Log: fix/ignore-assertion-binding

## Header

- Branch: `fix/ignore-assertion-binding`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-24`
- Created Date: `2026-08-24`
- Owner: `luvseldom`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `none`
- Checkpoint SHA: `none`
- Recommended Skills: `verification-before-completion, red-team-adversarial`
- Primary Domain Snapshot: `governance-tooling`
- SSoT Sequence: `162`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-24 01:55 UTC`
- Platform: `claude-code`
- Files Read: `0`

---

## Task Description

A downstream sibling fork (HabitFlow) reported six governance findings against the shared
upstream. Diagnosis against this fork confirmed one root cause worth fixing here: assertions
about `.gitignore` behaviour are not bound to git. Two altitudes of the same defect —
`validate.sh`/`validate.ps1` assert must-track artifacts by exact-line string match (blind to
`archive/*.md`-shaped patterns), and `audit-guardrails.md` Test 1 asserts four paths are
invisible to `git status` when a real cold deploy shows 90 of them.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-24 | classification frozen: quick-win |
| plan | done | 2026-08-24 | roundtable + tenth-man adjudicated; scope reduced to one unit |
| implement | done | 2026-08-24 | 2 validators + 2 doc twins + 1 test file + baseline bump |
| review | done | 2026-08-24 | self tenth-man PASS, then delegated adversarial = NOT READY (1 CRITICAL, 2 MAJOR); re-implemented; re-review PASS |
| test | done | 2026-08-24 | 13-arm suite, each new guard mutation-proved; both validators + full CI suite |
| handoff | n/a | — | quick-win exempt (AGENTS.md §Delivery Gates) |
| ship | done | 2026-08-24 | SSoT seq 163, L2 entry, 4 backlog rows, archived |

---

## Phase Summary

**bootstrap** — Diagnosis of the downstream report ran read-only before classification.
Six reported items triaged against this tree: 2 already solved here (twin parity, absent-tool
signal), 1 largely solved (static self-consistency), 3 real. Of the three real ones, only the
ignore-assertion class has a confirmed live instance; the other two are latent-but-untripped and
route to the backlog instead of this unit. One of my own diagnosis claims was refuted during
bootstrap and is recorded in Drift Log rather than carried forward.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T01:55:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T02:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T02:40:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T03:15:00Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Timestamp: 2026-08-24T04:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T04:40:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T04:55:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T06:20:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-24T09:45:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | quick-win: no new spec (§10.4); no existing spec covers the ignore-assertion seam |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | native-check escape hatch invoked (no-python path) |
| Issue | — | — |
| PR | — | — |

---

## Known Risk

Root Cause: the guard was a literal `.gitignore` line matcher rather than an assertion about git's
resolved behaviour, so any pattern hiding the artifact by a different spelling passed.

- **Adopter breakage on upgrade**: a downstream that glob-ignores its own specs/archive now goes red.
  For an untracked artifact that is real loss; for one already tracked, git keeps committing it, so the
  FAIL is a warning about the next fresh clone rather than about today. Either way it names the
  offending `source:line`, so it is actionable.
- **Probes are representative, not exhaustive**: synthetic filenames shaped like each directory's real
  contents, so `archive/*-worklog.md` still slips through and `!docs/adr/ADR-2*.md` can flag a healthy
  tree. Catches the whole-directory and whole-extension shapes — the class that bit downstream. Said in
  the code comment too.
- **Non-git hosts**: SKIP with an explicit reason, never PASS.

## Decisions

### D-1: Ask git, not `.gitignore`
- **Decision**: probe a representative FILE inside each persistent artifact via `git check-ignore`.
- **Reason**: `archive/*.md` ignores contents without naming the directory; a file probe subsumes the directory case.
- **Alternatives**: expand the literal pattern list — denylist whack-a-mole.
- **Impact**: inherits git's resolution, including `.git/info/exclude` and global excludes.
- **Disposition**: → consolidated: L2 governance

### D-2: Native, and the ADR-006 ratchet did not move
- **Decision**: keep it native; baseline stays 204/204, no justification entry.
- **Reason**: a Python tool degrades to SKIP on no-Python downstreams and cannot express the did-not-run SKIP; D-6's deletion cancelled the planned +1.
- **Alternatives**: `run_python_check` — unprotects the adopters this guard exists for.
- **Impact**: no ratchet headroom spent.
- **Disposition**: → consolidated: L2 governance

### D-3: Tri-state — never PASS on a check that did not run
- **Decision**: ignored → FAIL, not ignored → PASS, git unusable → SKIP with a reason.
- **Reason**: the discipline the validators already adopted for absent tools (PR #412).
- **Alternatives**: treat unresolvable as PASS — recreates the v1.8.22 truth-claim defect.
- **Impact**: FAIL now wins over SKIP when both occur, and names the unresolved count in its tail.
- **Disposition**: → consolidated: L2 governance

### D-4: The playbook stops carrying an independent assertion
- **Decision**: Test 1 rewritten to the verified ignore set, pointing at the validator check; heading kept verbatim.
- **Reason**: nothing bound the doc's claim to a mechanism. The heading is an encoding canary (`validate.sh:1161`, `validate.ps1:1123`).
- **Alternatives**: enumerate ignored paths in prose only — a second driftable copy.
- **Impact**: ignore-block changes are caught by the check, not by the next reader.
- **Disposition**: → consolidated: L2 governance

### D-5: The claim-decay unit is dropped, not deferred
- **Decision**: build no claim-marking mechanism for U4.
- **Reason**: my instance was mis-attributed (Drift Log); dated `### Ship-*` headings already anchor those measurements. An unverified marker convention is the ritual defect the report itself diagnoses, and ADR-011 bans unenforced directives.
- **Alternatives**: `<!-- claim: verified-at <sha> -->` + gate distance check.
- **Impact**: reopen only on a second confirmed standing-claim decay.
- **Disposition**: → consolidated: L2 governance

### D-6: Not gated on `.gitignore` existing
- **Decision**: run the probes unconditionally; delete the `.gitignore absent` PASS branch.
- **Reason**: self tenth-man — that branch asserted a PASS without looking at anything.
- **Alternatives**: keep the gate (the same disease); hand-parse the other ignore sources.
- **Impact**: one fewer native emission, which is why D-2 cancelled out.
- **Disposition**: → local

### D-7: Verdict from `-q`, never `-v`
- **Decision**: `-q --no-index` decides; `-v --no-index` runs only on the failing path, for the message.
- **Reason**: `-v` exits 0 on a **negation** match. Measured on `docs/adr/*` + `!docs/adr/*.md`: `-v` 0, `-q` 1, git tracks the file. Reading `-v` as the verdict reds a correct adopter and names their protective `!` line as the thing to delete.
- **Alternatives**: parse `-v` output for a leading `!` — re-implements git precedence in two languages.
- **Impact**: a regression I introduced, caught by the delegated review, now mutation-guarded.
- **Disposition**: → consolidated: L2 governance

### D-8: `--no-index`, or the one real probe is inert
- **Decision**: pass `--no-index` on both calls.
- **Reason**: `check-ignore` skips TRACKED files by default and `current_state.md` is tracked in every healthy deploy — a detection narrowing inside a change meant to broaden.
- **Alternatives**: drop the real path from the list — loses the artifact that matters most.
- **Impact**: verified it does not reintroduce the negation false positive.
- **Disposition**: → consolidated: L2 governance

### D-9: Test 1 must work for a downstream reader, not just in the source repo
- **Decision**: Test 1 uses the canonical `.agentcortex/bin/deploy.sh`, not `installers/deploy_brain.sh`, and is framed as "any tree that has Agentic OS deployed".
- **Reason**: `deploy.sh:1001-1003` ships this guide to **every adopter**. My first rewrite said "from the source repo root" and used the wrapper — measured from a downstream: the wrapper takes its update path, **clones from the remote**, writes `.agentcortex-src/` into the reader's real project, and audits *that* version instead of theirs.
- **Alternatives**: keep the wrapper and add a caveat (leaves a network call and a side effect in an audit step).
- **Impact**: offline, no side effects, audits the copy on disk. Verified working from both the source repo and a deployed downstream.
- **Disposition**: → consolidated: L2 governance

### D-10: An outer-repo ignore is re-labelled, never re-decided
- **Decision**: run the probe loop first; relabel the cause as "an outer repository hides this whole tree" only when ALL probes came back ignored AND `git rev-parse --show-prefix` is non-empty. Same emission site, so the ADR-006 ratchet stays 204/204.
- **Reason**: under a `vendor/`-style ignore every probe resolves ignored and per-probe blame names the outer repo's own rule as "the pattern to remove" — the same shape as the `-v` CRITICAL: advice that breaks something working. Ordering it after the loop means it can never turn a PASS into a FAIL.
- **Alternatives**: `check-ignore -q --no-index -- .` as the discriminator — **shipped in the first version and wrong**: a blank CRLF line is the pattern `
`, git strips it to the empty string, and the empty pattern matches `.`, so every `core.autocrlf=true` checkout (the Git-for-Windows default, including this repo) was reported as ignored-by-an-outer-repo on a healthy tree. Caught by an independent reviewer running the validators against this repository.
- **Impact**: guarded by `test_a_crlf_gitignore_is_still_a_healthy_tree`, mutation-proved against the broken discriminator. The durable lesson is wider than the flag: **a fresh-deploy fixture is not a checkout** — 14 scenarios all built clean LF trees and none could see it.
- **Disposition**: → consolidated: L2 governance

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Refuted my own bootstrap-phase finding before planning on it: I reported `current_state.md:168`
  (`pass=87 warn=1 fail=0 skip=6`) as a decayed live claim after measuring 86/1/0/8 on v1.8.23.
  It sits under `### Ship-chore-v1.8.21-release-2026-08-14`, a dated Ship History heading — a
  historical record that was correct for v1.8.21, not a standing claim. The two measurements have
  different subjects. Consequence: the claim-decay unit I had scoped is dropped; the SSoT's
  dated-section structure already supplies the as-of anchor, and the only confirmed instance of a
  standing-claim-gone-false is `audit-guardrails.md` Test 1, already inside this unit.

---

## Review Feedback

**Pass 1 — self tenth-man, PASS.** 6 refutations, 1 stood (D-6). **That PASS did not hold up** — the
author reviewing their own diff found what was visible in it and missed what needed `git check-ignore`'s
exit semantics. **Pass 2 — delegated adversarial (`acx-reviewer`), NOT READY.** 1 CRITICAL + 2 MAJOR +
5 MINOR; **all 8 re-derived here before acting, none taken on the agent's word, all 8 fixed** (D-7, D-8,
the PS behavioural arm, and five smaller). It independently re-confirmed clean: ADR-006 ratchet 204/204,
`set -e`/`$?`, `$LASTEXITCODE` staleness, twin divergence, canaries, §10.3/§10.4/§13 scope.
**Pass 3 — scenario sweep** (install / update / dev, at the user's direction): found the outer-repo
mis-diagnosis → D-10.

Full findings table + pass-1 detail: see `## Review Feedback (long form)` below.

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

- `pytest tests/ci/test_ssot_ignore_probe_binding.py` → **15 passed** (228s). Command carries no `-m`
  filter; the four structural arms are the only ones that run on a bash-less host.
- `bash .agentcortex/bin/validate.sh` → exit 0, `pass=118 warn=3 fail=0 skip=2`.
  `pwsh -File .agentcortex/bin/validate.ps1` → exit 0, **identical tally**. No new WARN, no FAIL.
- Full CI-equivalent suite (`tests/ci/ tests/guard/ .agentcortex/tests/`, no `-m` filter): see Evidence.

---

## Evidence

### bootstrap (diagnosis, read-only)

Compacted during the branch, merged back at ship; long form in `## Bootstrap diagnosis (long form)` below.
Load-bearing findings: the guard PASSed on the reported accident shape (`fail=0` while `git check-ignore`
confirmed archived logs hidden); Test 1 was false 4/4 against a real cold deploy and its command errored
out (`--force` is not a `deploy.sh` flag); this repo itself was not mis-ignoring (188 tracked files under
`.agentcortex/context/archive/`).

### implement (post-review state)

**17 scenarios across install / update / dev, each run for real** — full matrix in `## Scenario matrix` below. Headlines: fresh `86/1/0/8`; `--no-python` `76/1/0/18` and still discriminating; non-git SKIP
`84/2/0/9`; nested-under-`vendor/` FAIL with its own cause; upgrade from v1.8.23 preserves downstream
state with tallies **unchanged** `96/6/2/6`; re-deploy x3 and rollback clean; worktree resolves all six
probes; the pre-commit hook's real interpreter (`powershell` 5.1) runs it end to end; and a **CRLF
`.gitignore`** — the state of every `core.autocrlf` checkout including this repo — which the first
version of D-10 wrongly FAILed. All four changed deployed files are `core` tier.

- **Mutation-proved on the shipped guards** — each applied to the real file, arm run, then restored:
  verdict from `-v` → negation arm **FAILED**; `--no-index` removed → tracked-artifact arm **FAILED**;
  PS twin unable to emit FAIL (`-eq 99`) → PS arm **FAILED** (that same mutation left the pre-review
  suite fully green — the gap it closes). Both validators reverted to HEAD → **7 failed, 1 passed** of 8;
  the passing one is the clean-tree arm, which exists so the FAIL arms cannot be met by an always-failing check.
- **11 passed** (144s). Native sites **204/204**. Exit signal survived: clean → 0 on `validate.sh`,
  `pwsh`, and `powershell 5.1`; failing → 1. `validate.ps1` parses clean on 7.6.3 and 5.1.26100.9168.
- EOL: Python text I/O rewrote the validators to CRLF three times; caught each time by `git diff`'s
  normalization warning. Final state matches `.gitattributes` (sh LF, ps1 CRLF+BOM).
- Security floor: `scan_credentials.py` 0, `check_text_integrity.py` pass, `lint_governed_writes.py` 0 FAIL.
- **Demonstration** (recipe + captured output, validator-output change):
  `git init t && bash .agentcortex/bin/deploy.sh t && printf '
.agentcortex/context/archive/*.md
' >> t/.gitignore && bash t/.agentcortex/bin/validate.sh`
  → `  .gitignore:31:.agentcortex/context/archive/*.md<TAB>.agentcortex/context/archive/acx-ignore-probe-20260101.md`
  / `[FAIL] .gitignore blocks persistent SSoT artifacts (1/6 probes ignored; the ignore source:line shown above is the pattern to remove)`
  / `Summary: pass=85 warn=1 fail=1 skip=8`. Same recipe on v1.8.23 prints `[PASS]` and `fail=0`.

### Upstream / downstream boundary

Ships: `validate.sh`/`.ps1`, and both `audit-guardrails` twins (`deploy.sh:1001-1003`) — which is why
the Test 1 rewrite is adopter-facing. Upstream-only: `tests/`, `.test_durations`, and the archive
fragment (`deploy.sh:821-822` creates `context/archive/` empty and copies no content, so it cannot
leak). Inverse case: `.agentcortex/specs/` and `.agentcortex/adr/` exist **downstream but not
upstream**; both probe clean in either position.

### Adopter delta (measured, not asserted)

One identical `.gitignore` mutation — `archive/*.md` + `docs/specs/*.md`, with git confirmed to be hiding
both the archive and the adopter's own spec — run against each version's **own deployed** validator:

- **v1.8.23**: `[PASS] .gitignore preserves persistent SSoT artifacts` · `pass=86 warn=1 fail=0 skip=8`
- **this branch**: `[FAIL] ... 2/6 probes ignored` naming each `source:line` · `pass=85 warn=1 fail=1 skip=8`

On a healthy tree the tallies are identical before and after upgrade, so the change adds detection without
adding churn. No new flags, no new deployed files, no engine change.

---

## Bootstrap diagnosis (long form)


- **The guard was vacuous against the reported shape.** Cold deploy, v1.8.23: with
  `.agentcortex/context/archive/*.md` in `.gitignore`, `git check-ignore -q` → 0 (archived logs hidden) while
  `validate.sh` printed `[PASS] .gitignore preserves persistent SSoT artifacts`, `fail=0`. `validate.ps1` used
  `-contains`, the same exact-element match.
- **Test 1 was false 4/4 and its command was broken.** Same deploy: `git status` showed `.agent/` 58 paths,
  `.agents/` 29, `.antigravity/` 1, `.agentcortex/context/` 2 — the doc claimed none appear. `--force` is not a
  `deploy.sh` flag; `*)` at `deploy.sh:22` takes it as TARGET → `ERROR: Target directory is not writable: --force`.
  Both language twins carried it; nowhere else in the repo.
- This repo was not itself mis-ignoring: 188 files tracked under `.agentcortex/context/archive/`.


## Review Feedback

**Pass 1 — self tenth-man (refute-only), verdict PASS.** 6 refutations attempted, 1 stood: the
`.gitignore`-exists gate and its unchecked `PASS` (→ D-6). Pre-mortem added the `.test_durations`
entries. **This PASS did not hold up**, which is the process finding worth keeping: a self-review by
the author who just wrote the code found the defect that was *visible in the diff* and missed the two
that required knowing `git check-ignore`'s exit semantics.

**Pass 2 — delegated adversarial review (`acx-reviewer`), verdict NOT READY.** 8 findings. Every one
re-derived here before acting; none taken on the agent's word.

| sev | finding | my verification | disposition |
|---|---|---|---|
| CRITICAL | `-v` exits 0 on a **negation** match, i.e. when the path is NOT ignored; verdict taken from `-v` reds a correct adopter and names their protective `!` line as the pattern to remove | reproduced: `docs/adr/*` + `!docs/adr/*.md` → `-v` exit 0, `-q` exit 1, git adds the file | **fixed** (D-7) + guarded |
| MAJOR | no `--no-index`, so the one real probe (`current_state.md`, tracked) is inert — a detection narrowing vs HEAD | reproduced: tracked + named in `.gitignore` → without `--no-index` exit 1 (PASS), with it exit 0 | **fixed** (D-8) + guarded |
| MAJOR | the tests had **zero** discriminating power over `validate.ps1`'s verdict logic | confirmed by construction and re-run: mutating the PS twin to `-eq 99` left the file green | **fixed** — Windows-gated behavioural arm added |
| MINOR | probe fidelity errs both ways, not stated | agreed | **fixed** — code comment + `## Known Risk` |
| MINOR | red-first receipt said `6 failed` | correct: that run predated the 8th test | **corrected** below |
| MINOR | two wrong glyphs in the zh-TW twin, which ships to adopters | confirmed, both mine | **fixed** — `U+5F03`→`U+68C4`, `U+80C7`→`U+8087` |
| MINOR | PS: profile-set `$PSNativeCommandUseErrorActionPreference` could route clean probes into `catch`; and SKIP was tested before FAIL | agreed on both | **fixed** — preference pinned in-block, FAIL now wins and reports unresolved probes in its tail |
| MINOR | `Current Phase` header stale | confirmed | **fixed** |

Checked-and-clean (independently re-derived): ADR-006 ratchet 204/204 both files; bash `set -e`/`$?`
handling; `$LASTEXITCODE` staleness refuted empirically; no twin divergence; encoding canaries intact;
scope and classification correct under §10.3/§10.4/§13.

---

## Review Feedback (long form)

**Pass 1 — self tenth-man (refute-only), verdict PASS.** 6 refutations attempted, 1 stood: the
`.gitignore`-exists gate and its unchecked `PASS` (→ D-6). Pre-mortem added the `.test_durations`
entries. **This PASS did not hold up**, which is the process finding worth keeping: a self-review by
the author who just wrote the code found the defect that was *visible in the diff* and missed the two
that required knowing `git check-ignore`'s exit semantics.

**Pass 2 — delegated adversarial review (`acx-reviewer`), verdict NOT READY.** 8 findings. Every one
re-derived here before acting; none taken on the agent's word.

| sev | finding | my verification | disposition |
|---|---|---|---|
| CRITICAL | `-v` exits 0 on a **negation** match, i.e. when the path is NOT ignored; verdict taken from `-v` reds a correct adopter and names their protective `!` line as the pattern to remove | reproduced: `docs/adr/*` + `!docs/adr/*.md` → `-v` exit 0, `-q` exit 1, git adds the file | **fixed** (D-7) + guarded |
| MAJOR | no `--no-index`, so the one real probe (`current_state.md`, tracked) is inert — a detection narrowing vs HEAD | reproduced: tracked + named in `.gitignore` → without `--no-index` exit 1 (PASS), with it exit 0 | **fixed** (D-8) + guarded |
| MAJOR | the tests had **zero** discriminating power over `validate.ps1`'s verdict logic | confirmed by construction and re-run: mutating the PS twin to `-eq 99` left the file green | **fixed** — Windows-gated behavioural arm added |
| MINOR | probe fidelity errs both ways, not stated | agreed | **fixed** — code comment + `## Known Risk` |
| MINOR | red-first receipt said `6 failed` | correct: that run predated the 8th test | **corrected** below |
| MINOR | two wrong glyphs in the zh-TW twin, which ships to adopters | confirmed, both mine | **fixed** — `U+5F03`→`U+68C4`, `U+80C7`→`U+8087` |
| MINOR | PS: profile-set `$PSNativeCommandUseErrorActionPreference` could route clean probes into `catch`; and SKIP was tested before FAIL | agreed on both | **fixed** — preference pinned in-block, FAIL now wins and reports unresolved probes in its tail |
| MINOR | `Current Phase` header stale | confirmed | **fixed** |

Checked-and-clean (independently re-derived): ADR-006 ratchet 204/204 both files; bash `set -e`/`$?`
handling; `$LASTEXITCODE` staleness refuted empirically; no twin divergence; encoding canaries intact;
scope and classification correct under §10.3/§10.4/§13.

---

## Scenario matrix

| scenario | expect | result |
|---|---|---|
| **install** fresh downstream | PASS | `86/1/0/8`, sh and ps1 identical |
| install, `--no-python` host | PASS | `76/1/0/18` — native, runs where Python does not |
| install, `--no-python` + accident | FAIL | `1/6` — still discriminates without Python |
| install, not a git work tree | SKIP | `84/2/0/9`, sh and ps1 identical — never PASS |
| **install nested under an outer repo's `vendor/` ignore** | FAIL, own cause | 6/6 probes ignored + prefix `vendor/proj/` → names the outer rule and says do **not** delete it (D-10) |
| **dev** a CRLF `.gitignore` (every `core.autocrlf` checkout, incl. this repo) | **PASS** | PASS — the first D-10 discriminator FAILed here; regression-guarded |
| **update** rollback branch → v1.8.23 | clean | PASS, ignore block markers intact at 2 |
| **install** `.gitignore` with no trailing newline | PASS | adopter's last line survives as its own line |
| **update** v1.8.23 → branch, downstream state seeded | preserved | work log, own spec, own ignore rule all kept; managed block 2 markers, no duplication; tallies **unchanged** `96/6/2/6` |
| **update** re-deploy ×3 | idempotent | markers stay 2; verdict unchanged |
| **dev** git worktree (`.git` is a file) | PASS | all 6 probes resolve; deploy-from-worktree validates `86/1/0/8` |
| **dev** framework repo, active work log | PASS | both validators exit 0, `118/3/0/2`, identical |
| **dev** pre-commit hook path — `powershell` 5.1, not `pwsh` | works | clean → PASS exit 0; accident → FAIL exit 1. Parses clean on 5.1.26100 and 7.6.3 |
| `.gitignore` + `archive/*.md`, `docs/specs/*.md` | FAIL | `2/6`, names each `source:line` |
| no `.gitignore`, `.git/info/exclude` hides specs | FAIL | `1/6`, names `.git/info/exclude:7` |
| `docs/adr/*` + `!docs/adr/*.md` | **PASS** | was a false FAIL before D-7 |
| `.gitignore` names the tracked `current_state.md` | **FAIL** | was a false PASS before D-8 |
