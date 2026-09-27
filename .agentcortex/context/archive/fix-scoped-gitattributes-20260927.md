# Work Log: fix/scoped-gitattributes

## Header

- Branch: `fix/scoped-gitattributes`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-09-27`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `733e69c`
- Checkpoint SHA: `6de3dbb`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `180`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-09-27T02:21:47Z`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`

---

## Task Description

Owner check after v1.8.28: "the install must not weigh the product down or affect its development". The installed `.gitattributes` is the upstream repo's own file: repo-wide `* text=auto` plus `*.md/*.py/*.json/*.sh/*.yaml/*.yml text eol=lf` and `*.ps1/*.cmd/*.bat text eol=crlf`. Reproduced: in a product whose files are committed with CRLF, every product `.py/.json/.md/.sh/.ps1` shows as a whole-file EOL rewrite as soon as it is touched (7/7 fixture files). Fix: install a downstream template scoped to the paths Agentic OS installs and the docs its validators parse (`docs/specs|architecture|adr|reviews`), with `text=auto` so binaries and CRLF-committed files are left alone. The upstream `.gitattributes` is unchanged. Backlog row #215 is added at ship.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-27T02:21:47Z | quick-win |
| plan | done | 2026-09-27T02:21:47Z | template + deploy.sh + golden + test |
| implement | done | 2026-09-27T02:49:54Z | 1d728b7 + 1e74c3d (test helper fix) |
| review | NOT READY | 2026-09-27T03:52:30Z | independent: F1 MAJOR upgrade churn (reproduced) |
| implement | done | 2026-09-27T03:57:48Z | 4ea8f16: `* text=auto` kept, governed *.md explicit text, upstream LF pin, 4 fast tests |
| review | NOT READY | 2026-09-27T04:40:11Z | independent re-review: F1 MAJOR governed rules normalize product Markdown; F2 `* text=auto` not neutral |
| implement | done | 2026-09-27T04:48:32Z | 5c083dd: no product rule; top-level governed *.md; one-time re-checkout notice |
| review | NOT READY | 2026-09-27T05:49:36Z | independent round 3: printed command unsafe (skip-worktree), governed rules still reach product docs, false notice |
| implement | done | 2026-09-27T05:49:37Z | round 4: no command, no docs/.claude rules, 2 validator parsers CR-tolerant |
| review | PASS | 2026-09-27T06:08:17Z | independent focused round 4: 4 MINOR |
| implement | done | 2026-09-27T06:08:17Z | round 5: the 4 MINOR fixes |
| review | PASS | 2026-09-27T06:08:17Z | self: each MINOR fix has a failing mutant or a discriminating fixture |
| test | skipped | — | quick-win optional; targeted local + PR #452 CI full suite |
| ship | done | 2026-09-27T06:10:09Z | SSoT 180->181 |

---

## Plan

- New `.agentcortex/templates/downstream.gitattributes`: framework namespaces and governed docs dirs `text=auto eol=lf`; installed `.ps1`/`.cmd` `eol=crlf`; `.agentcortex-manifest text eol=lf`. No product-wide pattern.
- `deploy.sh`: `.gitattributes` comes from the template (deploy + `--dry-run` list). Tier unchanged (scaffold).
- Golden: add `scaffold .agentcortex/templates/downstream.gitattributes`.
- Test (one real deploy into a git repo with CRLF-committed product files): product paths have no `text`/`eol` attribute and stay unmodified after a touch; every deployed framework path resolves `eol` to lf/crlf via `git check-attr`; governed docs dirs resolve lf.
- Mutants: upstream global file as template -> product-churn assertion FAILS; one namespace line dropped -> coverage assertion FAILS.
- Verified before plan (EOL matrix, same fixtures): current file 7 product files churn, scoped 0; on `core.autocrlf=true` every framework/governed file checks out identically (LF; `.ps1`/`.cmd` CRLF); a binary under `docs/specs/` is untouched in both.

---

## Phase Summary

- bootstrap: quick-win (installed `.gitattributes` scope). ⚡ ACX
- plan: template + deploy.sh source swap + golden + one-deploy test + 2 mutants | Confidence: 85% — the validators' product-side doc paths were enumerated from `validate.sh`/`validate.ps1`; a missed path would only lose LF on `autocrlf=true` checkouts, which the coverage test pins for every deployed path
- implement: 1d728b7 template + deploy.sh (deploy, dry-run, fail-closed check) + golden + test; 1e74c3d test helper fix | Confidence: 90% — test passes on a real deploy and both mutants fail
- implement (round 2): 4ea8f16 — template keeps `* text=auto`; governed `*.md` `text eol=lf`; header tells adopters to delete the old repo-wide rules; upstream pins the template LF; tests: upgrade path x3 EOL configs (pure git) + attribute contract | Confidence: 90% — every review finding reproduced and each fix has a failing mutant
- implement (round 3): 5c083dd — no rule reaches product files; governed rules are top-level `docs/<dir>/*.md text=auto eol=lf`; on an update that replaces the old repo-wide file deploy prints a one-time notice with a re-checkout command for line-ending-only files (a customized old file is kept and the notice says what to replace); tests: new install (slow), update notice once + customized case (slow), attribute contract incl. nested docs and .sh/.json/.yaml/.ps1 (fast), printed command x3 EOL configs with a real edit kept (fast) | Confidence: 88% — neutral for new installs by construction; the transition is one command, tested in all 3 configs
- implement (round 4-5): 422b580 + 6de3dbb — no product rule, docs/ and .claude/ unpinned, 2 validator parsers CR-tolerant, notice only when the old file is replaced, root rules anchored | Confidence: 92%
- review: rounds 1-3 NOT READY (independent, each finding reproduced), round 4 PASS (focused, 4 MINOR fixed in round 5, self-verified) ⚡ ACX
- ship: PASS on 6de3dbb. Backlog #215 Shipped; tooling.log.md L2; Ship History + rotation; archive MOVE; INDEX. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T02:21:47Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T02:21:47Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T02:49:54Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-27T03:52:30Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T03:57:48Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-27T04:40:11Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T04:48:32Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-09-27T05:49:36Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T05:49:37Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T06:08:17Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T06:08:17Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T06:08:17Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-27T06:10:09Z

---

## Known Risk

- Adopters who already merged the old repo-wide rules into their own `.gitattributes` keep them; the CHANGELOG must say the scoped block replaces them.
- Rollback: revert the branch commit.

---

## Decisions

- Review round 1 (independent, NOT READY), each finding reproduced before acceptance: F1 MAJOR upgrade churn CONFIRMED (matrix: v1 Linux .cmd/.bat/.ps1 M, Windows autocrlf=false +src/web.js; old rules left LF blobs with CRLF copies, and removing `* text=auto` removed the conversion) -> keep `* text=auto`, Git's default, which never rewrites a CRLF-committed file; v2 upgrade matrix clean in all 3 configs. F2 test bug: fixed in 1e74c3d. F3 `.gitattributes` itself CRLF from a Windows source clone: `* text=auto` normalizes its blob; upstream pins the template LF. F4 governed CRLF docs never normalized under `text=auto`: governed `*.md` get explicit `text eol=lf` (by design they churn once when touched; validators need LF). F5 customized old file: template header says to delete the old repo-wide rules (the sidecar carries it); the adjacent pre-existing `--dry-run` sidecar deletion is a separate unit. F6 binary detection: accepted. → consolidated: L2 tooling
- Review round 2 (independent, NOT READY), verified before acceptance: F1 MAJOR CONFIRMED — the validators read only the top level of the 4 dirs (`validate.sh:940,963,1006,2453,2504`), most reads are CR-tolerant (unanchored or `tr -d '\r'`); only `:966` (WARN) and `:1024` (no-Python fallback) are CR-sensitive and only for framework-written docs, which `text=auto` stores LF -> governed rules become top-level `docs/<dir>/*.md text=auto eol=lf`. F2 CONFIRMED — `* text=auto` checks out every product text file CRLF for Windows `core.autocrlf=false`/`core.eol=crlf` (WSL/Docker scripts break) and stores new files LF in CRLF repos -> dropped: permanent neutrality for every future adopter outweighs a one-time transition for existing ones (0 external adopters detected; owner machine is `core.autocrlf=true`, clean either way). Transition: deploy prints a one-time notice when it replaces the old repo-wide file, with a remedy that re-checks-out only line-ending-only files (tested: R2 `rm` + `checkout` clean in all 3 configs, real edits kept; R1 `checkout` alone leaves stat-clean files CRLF). → consolidated: L2 tooling
- Review round 3 (independent, NOT READY), verified: B1 the printed command deletes skip-worktree and reverts assume-unchanged files -> command removed; the notice now gives the per-file standard (`git diff --ignore-cr-at-eol` empty -> `git checkout -- <file>`). B2 top-level docs rules still reached product docs (local run: `:151` 1 failed) -> docs/ and .claude/ rules removed; `validate.sh:966,1024` made CR-tolerant (the only anchored parsers of product docs; ps1 already normalizes). M3 false notice for a product's own `*.md text eol=lf` -> notice only when the old file was replaced (signature gone after deploy). m4 v1.3.0-1.4.1 `*.md text` -> signature `*.md text`. MSYS grep/sed drop CRs, so the validator test discriminates on Linux CI only. → consolidated: L2 tooling
- Review round 4 (independent, focused, PASS): 4 MINOR fixed in round 5 — `/AGENTS.md`, `/CLAUDE.md`, `/GEMINI.md`, `/.agentcortex-manifest` anchored (unanchored they matched a monorepo's nested files; mutant FAILS the contract test); notice wording (leftovers appear once a tool touches a file); validator fixture uses an unquoted `target_doc` (the old sed skipped a quoted CRLF line, so the check could not fail); template header carries the per-file advice for customized files. → consolidated: L2 tooling

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Post-ship CI (PR #452, Linux + Windows shard 1): 2 `test_preexisting_sidecar_file_stays_preserved_across_repeated_deploys` cases build a minimal source tree without the new template, so the fail-closed check fired. Fixture seeded; `test_deploy_fails_closed_when_gitattributes_template_missing` added. Local: 8 passed.

---

## Evidence

- Round 3: fast 4 passed. The printed command first returned exit 1 when the last file had a real edit (`&&` chain); now `if ...; then ...; fi`. Mutants each FAIL: whole-tree governed rules, `* text=auto` added, repo-wide rules (contract); command without `rm` (linux-default + windows-autocrlf-false). Remedy matrix before choosing: R1 `checkout` alone left stat-clean files CRLF under `core.eol=crlf`; R2 `rm` + `checkout` clean in all 3 configs with the real edit kept.
- EOL matrix (same fixtures, current vs scoped): product committed CRLF, files touched -> 7 modified vs 0; `core.autocrlf=true` clone -> framework/governed files identical (LF; `.ps1`/`.cmd` CRLF), product files follow the product's settings; `docs/specs/diagram.png` untouched in both.
- Test first run FAILED on a test bug: text-mode stdin on Windows sent `AGENTS.md\r` to `git check-attr --stdin`, so exact-name rules missed and the product assertion passed vacuously. 1e74c3d: `-z` + bytes, and the helper asserts it got every path back. Re-run: 1 passed (446s, one real deploy).
- Mutants (own clones): repo-wide template -> FAIL (`text` set on product files); `.agents/**` dropped -> FAIL (28 `.agents/skills/*` paths uncovered).
- Round 2 matrix (old / v1 / v2): new install into CRLF product -> 7 M / clean / only the governed `docs/specs/legacy.md` (by design); upgrade linux-default -> - / 3 M / clean; windows-autocrlf-false -> - / 4 M / clean; autocrlf=true -> - / clean / clean. v2 on an autocrlf=true clone: framework+governed LF, installed `.ps1`/`.cmd` CRLF, product files follow the product, PNG byte-identical.
- Round 2 tests: fast 4 passed (upgrade x3 + contract). Mutants: governed md -> `text=auto` FAIL (contract); repo-wide rules FAIL (contract); `* text=auto` dropped FAIL (contract + upgrade linux-default + windows-autocrlf-false); v1 template FAIL (same 2 upgrade configs).
