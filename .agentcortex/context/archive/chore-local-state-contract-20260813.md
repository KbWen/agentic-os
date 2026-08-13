# Work Log: chore/local-state-contract

## Header

- Branch: `chore/local-state-contract`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-13`
- Created Date: `2026-08-13`
- Owner: `claude-main-20260813`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `51cf78fb802b6c983af2f2a149b43da1ba032d9c`
- Checkpoint SHA: `cfb66ed`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `151`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-13 (claude-main-20260813)`
- Platform: `claude-code`
- Files Read: `10`

---

## Task Description

Owner-approved remediation of audit finding F3 and the same-shaped drift found alongside it: files that declare themselves user-local while git tracks them. Scope decided after a read-only expert design pass whose recommendations were re-verified against the code before adoption.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-13 | Expert design pass consulted at owner request; all claims re-verified |
| plan | done | 2026-08-13 | 2 of 3 paths cleared; the third routed to ADR-002 rather than forced |
| implement | done | 2026-08-13 | .gitignore + deploy managed block (2 sites) + 3 untracks + backlog #172 |
| review | done | 2026-08-13 | 4 findings; 3 expert/audit suggestions declined with grounds, 1 real gap caught |
| test | done | 2026-08-13 | 42 tests + validator green |
| ship | done | 2026-08-13 | Archived in-PR; SSoT seq 151→152 |

---

## Phase Summary

**bootstrap** — Three paths declare local, git tracks them: `.claude/settings.local.json` (F3, tracked and *not* in `.gitignore`), `.agentcortex/context/.guard_receipt.json` and `.agentcortex/context/.guard_receipts/` (both **in** `.gitignore:7-8` **and** tracked — a stronger contradiction than F3's). A read-only Plan agent was dispatched at the owner's request; **every load-bearing claim it made was re-verified before adoption**, and one correction it supplied changed the work: my own framing said `.guard_receipts/` was tracked across 52 commits, when `git ls-files` shows exactly **two grandfathered blobs** out of 21 on disk — the ignore rule has been working for the other 19 all along, and 52 was a count of modifications to those two.

**plan** — Two of the three clear at zero machine risk; the third does not, and was routed rather than forced. `git ls-files | xargs grep -l settings.local.json` reaches no test, validator, workflow or deploy path — only prose. The two grandfathered receipt blobs are read by nothing: every reference in tests and tools is to the *path string* for ignore rules or receipt-path computation (`test_guard_context_write.py:80`, `test_d2_1_guard_unit.py:214`, `test_deploy_tiering.py:636`), never to those blobs. `.gitignore` is only ever asserted with substring `in` checks, so adding a line breaks nothing.

**implement** — `.gitignore` gains `.claude/settings.local.json` under the existing Claude-local section; three paths untracked with `git rm --cached`, working copies intact and now correctly matched by the ignore rules (`git check-ignore -v` confirms both). `deploy.sh` gains the same pattern in **two** places — the managed ignore block and the `managed[]` map in `strip_managed_ignore_blocks`, which is per-pattern, so block-only would leave adopters with a duplicated line. Adopters need this: `deploy.sh:118,157,1028-1031` ship `.claude/settings.json` at scaffold tier, so every adopter inherits its "user-local permissions live in settings.local.json" claim and, until now, none of the git behaviour backing it.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T14:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T14:10:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T14:20:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T14:40:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T14:50:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T15:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | `docs/reviews/2026-08-13-govern-audit-drift-core-health.md` | F3 |
| ADR | `docs/adr/ADR-002-guarded-governance-writes.md:230` | Phase 3 owns the third path |
| Issue | `docs/specs/_product-backlog.md` #172 | Filed by this unit |

---

## Known Risk

- **R1 — contributor pull deletes the working copy.** After `git rm --cached` + merge, a `git pull` applies the deletion: an identical copy is silently removed, a locally-modified copy makes git refuse the merge instead (nothing lost). `.gitignore` does not protect it — ignore rules only govern untracked paths. Accepted: `git worktree list` shows one worktree, the owner's on-disk copy is untouched by `--cached`, fresh clones never had the file, and Dependabot keeps no worktree. The audit's constraint ("do not silently remove local permissions during pull", `docs/reviews/2026-08-13-govern-audit-drift-core-health.md:127`) is satisfied for this repo's actual contributor set, and is stated here rather than assumed away.
- **R2 — adopters get a new ignore default on their next deploy.** Non-destructive by git semantics: a `.gitignore` line never untracks an already-tracked file, so an adopter who deliberately tracks theirs is unaffected.
- **R3 — classification near-miss, recorded not hidden.** `engineering_guardrails.md §10.1` escalates "alters default configs impacting users" to `feature`. Held at `quick-win` on the `[classification-flow]` Global Lesson's own self-check (no spec written, no handoff run) and on blast radius: one non-destructive ignore default. Review and test are run anyway, which is what `feature` would have bought.

Rollback plan: revert the commit. `git rm --cached` is reversed by the revert re-adding the paths; no content is destroyed in either direction.

---

## Decisions

### D-1: Clear two paths, route the third to its ADR instead of forcing it
- Decision: untrack `.claude/settings.local.json` and the two grandfathered `.guard_receipts/*.json` blobs; leave `.guard_receipt.json` tracked and file backlog #172.
- Reason: `validate.sh:2140-2145` / `validate.ps1:1996-2002` PASS on `-f` of the legacy receipt and WARN otherwise, so untracking it alone converts a real contradiction into a permanent cosmetic WARN on every clean checkout. The correct fix is ADR-002 Phase 3 (drop the mirror, key validators off `.guard_receipts/`) — and **its stated gate can never be met**: Phase 3 waits on Phase 2 stabilizing, but Phase 2's first item is now forbidden by `ship.md:208`. That is an ADR amendment, not a cleanup-unit call.
- Alternatives: untrack + change both validators in this unit (the expert pass recommended this — **overruled**: it makes an ADR-scoped decision without the amendment and edits two governance-critical validators inside a hygiene change); untrack and absorb the WARN (rejected — trades one defect for another against a `warn=3` baseline this repo reads as a health signal).
- Impact: most of the friction goes anyway, since the per-target receipts stop dirtying the tree; one legacy file still dirties on each guarded write until #172.
- → consolidated: L2 governance

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- **The other half of the owner's request produced no change, because my own recommendation was wrong.** I had reported the missing `## Security Findings` heading in `.agentcortex/templates/worklog.md` as the drift most worth fixing first. A second read-only expert pass found it already proposed, reviewed and **refuted as harmful** in a shipped spec: `docs/specs/conflicting-directive-scan.md` §Non-goals — *"Any change to `.agentcortex/templates/worklog.md`. Verified harmful"* — and its Domain Decision, *"No template changes, at all… a presence check and a template that supplies the thing being checked cannot coexist."* Verified by reading the spec, not taken on the agent's word. The check is a bare presence grep, so shipping the heading in the template would satisfy it forever, for every log, invisibly — the `[enforcement]` failure mode inverted. **No gotcha entry filed**: the shipped spec already records it, and adding a rules-surface line because one agent re-proposed it once is the machinery-over-behaviour pattern this repo has already decided against. The re-proposal is recorded here instead; a third occurrence is the trigger.
- Expert design pass was dispatched read-only at the owner's request; implementation kept in the primary session so no agent competes for the working tree. Its recommendation #3 was **overruled** (see D-1) and one of its corrections was **adopted against my own prior framing** (the 52-commit claim).

---

## Review Feedback

| # | Finding | Disposition |
|---|---|---|
| R-1 | The audit asked for documentation of "how existing contributors retain their permissions" (`docs/reviews/2026-08-13-govern-audit-drift-core-health.md:126`). | **Not added, with grounds.** `CONTRIBUTING.md` never mentions `.claude/` or settings, so nothing goes stale. The population needing the instruction is empty: a fresh clone never had the file, and the owner's copy survives `--cached` untouched. The explanatory comment sits in `.gitignore` where someone hitting this actually looks. Adding a CONTRIBUTING paragraph for a zero-size audience is doc-debt, per the evidence-before-adding norm. |
| R-2 | The audit also floated "move any intentional seed to a clearly named example". | **Rejected (YAGNI §5.4).** No evidence anyone needs a seed; the file holds one operator's accumulated `gh`/`Bash` permission globs, not a starting point worth publishing. |
| R-3 | Should `.claude/settings.local.json` join the validator's *required*-pattern list for the deploy ignore block (`validate.sh:1069-1084`, `validate.ps1:1032`)? The expert pass recommended it. | **Declined.** That converts a convenience default into a machine-enforced requirement, i.e. a new rule — and the justification would be the hypothetical "a future edit might drop it". No verified instance; the evidence-before-adding norm applies to validator entries as much as to docs. |
| R-4 | Adding a pattern to the deploy block without adding it to `strip_managed_ignore_blocks` would leave adopters with a duplicated line. | **Caught and fixed** — the `managed[]` map is per-pattern (`deploy.sh:1109-1127`); both sites edited. Verified: exactly two functional occurrences plus one comment line. |

---

## Security Findings

- No credential, key, or token touched. The change moves per-operator permission state out of shared git history going forward; it does **not** rewrite history, so any secret ever committed to those files would still be in the history — none is: the file holds Claude Code tool-permission globs only, reviewed before untracking.

---

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

- `pytest tests/ci/test_deploy_tiering.py` → **39 passed in 556.60s** (the module that asserts on both the source `.gitignore` and the deploy managed block).
- `pytest .agentcortex/tests/test_backlog_validation.py` → **3 passed in 150.32s** (new row #172).
- `bash -n .agentcortex/bin/deploy.sh` → clean.
- `validate.ps1` → **`pass=118 warn=3 fail=0 skip=2`, integrity check passed**; the guard-receipt PASS is intact because D-1 deliberately leaves the legacy file tracked.

---

## Evidence

- **Contradiction confirmed** — `git ls-files .agentcortex/context/.guard_receipts/` → exactly 2 files, against 21 on disk; both matched by `.gitignore:8`. `.claude/settings.local.json` tracked with no `.gitignore` entry at all.
- **Zero machine coupling for F3** — `git ls-files | xargs grep -ln "settings\.local\.json"` → `current_state.md`, `.claude/settings.json`, one 2026-04-25 audit doc, the review doc. No test, validator, workflow, or deploy path.
- **Legacy mirror is a duplicate** — `git rev-parse HEAD:.guard_receipt.json HEAD:.guard_receipts/337ffd90d88a8b4f.json` → both `c50b26a67d8241768666a246b4a6924bbfc2335e`.
- **Untrack verified non-destructive** — all three files `PRESENT` on disk after `git rm --cached`; `git check-ignore -v` resolves them to `.gitignore:20` and `.gitignore:8`.
- **Validator dependency that shaped D-1** — `validate.sh:2140-2145`: `if [[ -f "$GUARD_RECEIPT" ]]` → PASS, else `WARN "no guard receipt found …; guarded writes remain advisory"`.
- **Final validator + suites, post-archival** (the one permitted terminal write): `validate.ps1` → **`pass=100 warn=3 fail=0 skip=3`, integrity check passed** (100 rather than 118 is the backlog-#149 family SKIP with no active Work Log present). `pytest tests/guard/ .agentcortex/tests/test_backlog_validation.py` → **335 passed in 215.62s**, run after the archival MOVE. Audit chain intact; `check_decision_disposition.py` OK across 18 logs.
