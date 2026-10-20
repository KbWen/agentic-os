# Work Log: fix/deploy-brain-ref

## Header
- Branch: `fix/deploy-brain-ref`
- Classification: `hotfix`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-19`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `2e26862`
- Checkpoint SHA: `2e26862`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `207`

---

## Session Info
- Agent: `claude-opus-5-5`
- Session: `2026-10-19T15:48:52Z`
- Platform: `claude-code`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §5 (testing), §12 (implement)
- Override: none
- Downstream-Capabilities: none

---

## Task Description
Let adopters pin an update to a release: installers/deploy_brain.{sh,ps1,cmd} accept an optional --ref <tag-or-branch> (ACX_REF env). Root cause of the gap: an update always clones/pulls the source's default-branch HEAD (deploy_brain.sh:102-133), so a compromised or broken main reaches every adopter on their next update and there is no way to stay on a known release.

---

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-19T15:48:53Z | hotfix (installer source selection → min hotfix per bootstrap §0) |
| plan | done | 2026-10-19T15:49:05Z | - |
| implement | done | 2026-10-19T15:52:31Z | - |
| review | done | 2026-10-19T16:17:05Z | NOT READY → re-review PASS |
| test | done | 2026-10-19T16:17:05Z | deploy suites 104 + not-slow 852 |
| handoff | pending | — | — |
| ship | done | 2026-10-19T16:17:07Z | local commit, no push |

---

## Phase Summary
- bootstrap: hotfix (bootstrap §0 row 1: installer source-selection logic). ADR-005/008 cover deploy.sh only; installers/ not covered. Confidence: 90% — clone --branch semantics for tags are standard git; risk is the cache state machine.
- plan: (1) deploy_brain.sh parses --ref <x> / --ref=<x> / ACX_REF, validates [A-Za-z0-9._/-]+ with no leading '-', strips it from the args forwarded to deploy.sh (which rejects unknown flags since U1); with a ref, the cache is always re-cloned with `clone --depth 1 --branch <ref>` (incl. the integrity re-clone) and the pinned commit is printed; a cache on a detached HEAD (left by a pinned run) is re-cloned instead of pulled when no ref is given; --ref on the first-run path (deploying from a source checkout) exits 2 with 'check out the tag first'. (2) deploy_brain.ps1 gains -Ref → --ref; deploy_brain.cmd maps --ref/-Ref. (3) docs/INSTALL.md update section documents --ref. (4) tests in tests/ci/test_deploy_brain_bootstrap.py: tag pin deploys the tag's content, invalid ref rejected, first-run + --ref rejected, --ref not forwarded, unpinned run after a pinned one re-clones the default branch. Default behaviour unchanged when no ref (§2.2 flag-driven). Confidence: 90%. Rollback: revert the commit; no state migrates (the cache is disposable and re-cloned on mismatch).
- implement: §12.1 read-before-write — deploy_brain.sh (NVM-style install/update dispatch; clone/pull/integrity paths at :102-150), deploy_brain.ps1 (bash resolver + arg builder :101-104), deploy_brain.cmd (cmd→ps1 arg translation). Changes: sh parses/validates/strips --ref, clone_source() used at all 5 clone sites, pinned re-clone, detached-HEAD re-clone, first-run rejection, pinned-commit line; ps1 -Ref; cmd --ref/-Ref; INSTALL update note. 11 new tests (10 fail on HEAD; detached-HEAD branch removal caught by the unpinned test). cmd path checked by hand: `deploy_brain.cmd --ref v1.0.0 .` → `Deploying v1.0.0` + RELEASE-ONE; `--ref` alone → '[ERROR] --ref requires a value.'
- review: NOT READY (R1 HIGH branch pin sticks; R2 missing ref deletes cache; R3 cmd metachar break-out, pre-existing for --source too; R4 lows) → implement: detach after pinned clone; ls-remote pre-check exits 2 before touching the cache; cmd passes --source/--ref via ACX_SOURCE/ACX_REF env (no command-line re-expansion); --ref= errors; message names ACX_REF; cmd missing-value exit 2; advice.detachedHead=false and `--` before the URL in clone. 5 more tests (all fail on the first-iteration scripts); file 28 passed.
- test: deploy suites 104 passed; not-slow 852 passed; validate.sh fail=0.
- ship: local commit, not pushed (owner: publish after all units). Retro offer pending to owner (hotfix Completion Guard). ⚡ ACX

---

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T15:48:53Z
- Gate: plan | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T15:49:06Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T15:52:31Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Timestamp: 2026-10-19T15:55:56Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T15:58:07Z
- Gate: review | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T16:00:00Z
- Gate: test | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T16:17:06Z
- Gate: ship | Verdict: PASS | Classification: hotfix | Timestamp: 2026-10-19T16:17:07Z

---

## External References
- installers/deploy_brain.sh:102-133 (clone/pull of default HEAD); tests/ci/test_deploy_brain_bootstrap.py (local-repo harness)

---

## Known Risk
- Rollback plan: revert the commit; .agentcortex-src is a disposable cache (re-cloned on origin mismatch/integrity failure), so no adopter state needs undoing.
- A pinned run leaves the cache on a detached HEAD; the next unpinned run must not try `git pull` on it (handled: re-clone).

---

## Decisions
none

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
- Scope add: deploy_brain.cmd --source gets the same env-passing fix as --ref (same pre-existing metachar flaw, same lines).

---

## Review Feedback
- R1 HIGH: a branch ref leaves the cache on a symbolic branch, so the next unpinned run pulls the pinned branch (reproduced) — INSTALL claim false. Fix: detach after a pinned clone.
- R2 MED: a nonexistent ref deletes a good cache, then git exits 128. Fix: ls-remote the ref before touching the cache; exit 2.
- R3 MED: cmd `--ref "x&echo …"` breaks out at %ACX_REF_ARG% expansion before sh validation (pre-existing same flaw for --source). Fix: pass via env (set "ACX_REF=%~2").
- R4 LOW: `--ref=` silently clears env ACX_REF; source-checkout message omits ACX_REF; cmd missing-value exit 1 vs sh 2; detached-HEAD advice noise; no `--` before the URL in clone.
- R5 tests: branch ref, missing ref keeps cache, env on checkout path, cmd path untested.
- Re-review (same reviewer): R1–R4 RESOLVED with repros (branch pin detaches; v9.9.9 keeps cache; cmd metachar for --ref/--source inert; file://, /c/, C:/ sources; `--` OK on git 2.53). Note acted on: ls-remote network/auth failure reused the 'no tag' message → message now says 'or the source could not be reached'. Pre-existing, not changed: an unpinned run with a bad --source removes the cache before the clone fails.

---

## Red Team Findings
none

---

## Security Findings
- [MEDIUM — A03 Injection] deploy_brain.cmd re-expanded --ref/--source values on the powershell command line (`x&echo …` executed). RESOLVED: values travel as ACX_REF/ACX_SOURCE env; repro inert (re-review + test_cmd_wrapper_ref_with_shell_metacharacters_is_not_executed).
- [LOW — A08] option smuggling via ref: RESOLVED by allow-list regex + leading '-' rejection + `--` before URLs; verified with -u, --upload-pack=x, $(id), newline. No unresolved HIGH/CRITICAL.

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
- `pytest tests/ci/test_deploy_brain_bootstrap.py tests/ci/test_deploy_tiering.py tests/ci/test_deploy_dry_run_read_only.py` → 104 passed, 2 skipped (8m17s); `pytest tests/ci tests/guard .agentcortex/tests -m 'not slow'` → 852 passed. Lint: `bash -n installers/deploy_brain.sh` clean (ShellCheck runs in CI; not installed locally).

---

## Evidence
- Root cause: updates always took the source's default-branch HEAD (deploy_brain.sh clone/pull without a ref). Fix verification: 16 --ref tests (all fail on HEAD or on the first iteration); cmd path demonstrated by hand and by test.
- Demonstration: `deploy_brain.cmd --ref v1.0.0 .` → `Deploying v1.0.0 (commit b1e8de9).` + RELEASE-ONE (tag content, main had moved on); `--ref v9.9.9` → exit 2, cache untouched.
- final (post-archive): validate.sh `pass=116 warn=5 fail=0 skip=2`; `scan_credentials.py --staged` clean. Archive filename carries the local date (2026-10-20 +08:00); Ship History heading and INDEX `shipped` carry the UTC date (2026-10-19).
