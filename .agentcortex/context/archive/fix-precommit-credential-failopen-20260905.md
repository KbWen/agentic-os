# Work Log: fix/precommit-credential-failopen

## Header

- Branch: `fix/precommit-credential-failopen`
- Classification: `hotfix`
- Classified by: `claude-opus-5`
- Frozen: `2026-09-05`
- Created Date: `2026-09-05`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `2d3aab9a`
- Checkpoint SHA: `890da53`
- Recommended Skills: `verification-before-completion, systematic-debugging, red-team-adversarial, karpathy-principles, auth-security`
- Primary Domain Snapshot: `security-control / pre-commit hook`
- SSoT Sequence: `167`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-09-05 07:00 UTC`
- Platform: `claude-code`
- Files Read: `18`

---

## Task Description

The opt-in pre-commit hook picked its interpreter by existence only and treated a scanner "could not run" exit as pass-through. Two reproduced arms landed a staged PEM private-key header in object history with the hook exiting 0. The fix restores ADR-008's chosen precedence: regex floor canonical, `.py` enriches. Continues #194(a).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-05 | hotfix; 5 skills; no conflicts |
| plan | done | 2026-09-05 | roundtable + tenth man adjudicated; floor-first alternative refuted by measurement |
| implement | done | 2026-09-05 | mutation-verified; 5 arms + benign controls |
| review | done | 2026-09-05 | r1 NOT READY 3 MAJOR; r2 NOT READY 1 MEDIUM (mine); r3 PASS |
| test | done | 2026-09-05 | 946 passed, 1 skipped, exit 0 |
| handoff | n/a | — | hotfix exempt |
| ship | done | 2026-09-05 | SSoT 167->168; history rotated at cap 10; L2 ci-security |

---

## Phase Summary

**bootstrap** - Diagnosis first per #194(a). The zero-Python surface came back **healthy**. The defect is one layer up, in the hook #144's startability fix never reached. Classified `hotfix` over the permitted `quick-win` so REVIEWED + TESTED are mandatory.

**plan** - Tenth man failed to refute on six angles and correctly narrowed scope (a crashing-but-startable python is already fail-CLOSED). Philosophy seat settled the contract: ADR-008 chose "(A) shell+PS regex canonical + `.py` optional", so this is conformance, not amendment. Its smaller remedy was refuted by measurement (D-1).

**implement** - Two hook changes, each pinned to a distinct arm. One vacuous green caught mid-phase: a re-run reported four arms exit 0 because `git reset --hard HEAD~2` had failed against a 2-commit history and nothing was staged; re-run with a per-arm `staged != 0` assertion.

**review** - Round 1 NOT READY, three MAJOR, each proved by a mutant. Fixed, re-mutated, round 2 entered. Scope grew 2 -> 4 files for a live downstream break found on the way (D-4).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T07:00:00Z
- Gate: plan | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T07:20:00Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T08:10:00Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Timestamp: 2026-09-05T09:05:00Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T09:40:00Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Timestamp: 2026-09-05T10:30:00Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T11:00:00Z
- Gate: review | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T11:45:00Z
- Gate: test | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T13:40:00Z
- Gate: ship | Verdict: PASS | Classification: hotfix | Timestamp: 2026-09-05T14:15:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | `ADR-008-portable-safety-floor.md` | `(A) shell+PS regex canonical + .py optional [CHOSEN]` -- the hook inverted it |
| Spec | `downstream-adaptability-optimization.md` | AC-S4: floor is canonical, `per-staged-file`, no python dependency |
| Spec | `dev-flow-hardening.md` | AC-8 "Credential floor cannot fail open silently"; only the CI half shipped |
| Backlog | `#194(a)` / `#144` / `#195-#197` | resume pointer / 2-site probe fix / filed here |
| PR | https://github.com/KbWen/agentic-os/pull/433 | 18 checks pass, 0 fail |

---

## Known Risk

Root Cause: `#144` added a startability probe to both validator twins but not to this hook, which still selected by `command -v` alone; and the hook's `cred_rc -ne 0` branch turned every non-0/1 scanner exit into "continuing" instead of consulting the deployed python-free floor.

- The fallback runs the floor where only the scanner ran before, and the two differ in both directions. The one live instance is fixed at source (D-4); the latent asymmetry is filed **#195** and named in the hook's own header.
- Candidate-order change (`python`->`python3` becomes `python3`->`python`) is behavioral, and is #144's documented order; it also removes a python2-selects-first false-BLOCK risk.
- Adopter delta is **new installs plus adopters who re-run the INSTALL copy** -- `.githooks/pre-commit` is a user copy `deploy.sh` never rewrites (**#197**).
- Rollback: revert the diff; no state migration, no config change.

---

## Decisions

### D-1: Reject floor-first-always; keep probe + fallthrough -> consolidated: L2 ci-security
- Decision: consult the floor when the python path yields no verdict, not on every commit.
- Reason: measured refutation of the roundtable's smaller remedy. `scan_credentials.py:62` exempts two files, the floor exempts none: staging exactly those gives floor `exit 1`, scanner `exit 0`. Floor-first-always would block every commit touching the credential controls on a working-python host, including this PR.
- Impact: working-python hosts byte-identical; only the broken/failed-python path changes, to match the shipped no-python path.

### D-2: The probe is justified on parity, not on security -> local
- Decision: keep the probe though the fallthrough alone closes the hole; declined the roundtable's advice to drop it.
- Reason: #144 fixed both validator twins and never swept this third site; `validate.sh:306` probes `python3`->`python`, the hook probed the reverse. Without it a stub is invoked once per commit, printing its Store message each time.
- Impact: also removes a python2-selects-first false-BLOCK risk. Pinned by M1.

### D-3: Classification stays `hotfix` above the rule minimum -> local
- Decision: `hotfix`, not the `quick-win` §10.1 permits.
- Reason: neither §10.4 security nor supply-chain escalation fires (a staged-content secret scanner authenticates nobody), but `state_machine.md:27` makes REVIEWED + TESTED mandatory for `hotfix` and optional for `quick-win`, and this is a live fail-open in a shipped security control.
- Impact: escalation above the minimum is permitted, silent downgrade is not. Two NOT READY rounds are that gate paying for itself.

### D-4: Fix the false positive at its source, not by re-scoping the floor -> consolidated: L2 ci-security
- Decision: abbreviate the credential shape in the two prose lines carrying it (`scan_credentials.py:79`, `test_scan_credentials.py:179`). Rejected: narrowing the floor to added lines (AC-S4 specifies `per-staged-file` and the archive records whole-blob as deliberate anti-FN -- needs a spec change) and floor `_SELF_SKIP` parity (drags in `credential_floor.ps1` + AC-S6 -> #195).
- Reason: already live and unrelated to this change. Exactly one line matched across the 169-file staged set -- the docstring documenting the allowlist escape hatch. The file's own fixtures avoid this by concatenation (`:34`); the prose never applied that convention.
- Impact: measured on the identical adopter path -- before `COMMIT_EXIT=1` blocked, after `COMMIT_EXIT=0` lands.

---

## Conflict Resolution

none — conflict matrix read once; only pair present is `karpathy-principles` vs `verification-before-completion` = compatible.

---

## Skill Notes

none

---

## Drift Log

- Review round 1 NOT READY -> reverse edge `REVIEWED -> IMPLEMENTING` (`state_machine.md:28`); phase set back to implement, fixes applied, review re-entered.
- Scope grew 2 -> 4 files mid-implement. Not creep: `scan_credentials.py` + its test carried the shape that makes the fallback misfire; the fix is 2 prose lines applying the file's own convention. Still one module, so `state_machine.md:51`'s `> 2 modules` hard-block is not crossed.
- Sequencing error, self-caught: a confirmation reviewer that mutates the hook was dispatched while the full suite ran. The suite was killed rather than quoted -- a suite racing a file-mutating agent is not evidence.
- Roundtable seat proposed floor-first-always as a smaller remedy; rejected on measured evidence (D-1), recorded rather than silently dropped because its contract analysis was adopted in full.

---

## Review Feedback

Round-by-round narrative: PR body. Summary:

- **R1 NOT READY, 3 MAJOR, each proved by a mutant.** Neither half was pinned (probe-deleted and always-blocking-fallback mutants both passed 6/6); the fallback exposed a reproducible false-positive block; the final message blamed the floor where it never ran. Closed by discriminator assertions + a benign fallback arm, D-4, and `floor_ran`.
- **R2 NOT READY on a regression I introduced.** All R1 findings re-verified closed. **NEW-1**: HEAD said "could not run; continuing" (honest); mine said "falling back to the no-python floor" then went silent, which reads as clean -- **quieter** than what it replaced, on the very path this diff adds, inverting the AC-8 invariant the new header cites. Fixed with a `REDUCED ASSURANCE` line (M4). Also closed NEW-2 (header stated only the broadening half of the trade), NEW-4 (both floors still printed the TruffleHog claim, interleaving with the hook's corrected text), NIT-1/2.
- **NEW-3 is the most durable artifact here.** `test_credential_floor_shell.py`'s docstring promised "no full literal sits in the repo" with **no verifier**, and it was already broken -- that is what blocked the adopter. A guard now runs the floor's own parsed patterns (never a second matcher -- #165) over every tracked file.
- **Declined, with reason**: a CHANGELOG entry -- every section is a released version with a narrative and there is no `Unreleased` convention; inventing one is a governance-surface change needing its own justification. Record goes to Ship History.
- **Self-caught in R3**: the `REDUCED ASSURANCE` line I added for NEW-1 quoted `3` and `7` -- a quantified claim in a shipped file with no verifier, the same advertised-but-unenforced defect this change exists to fix. Pinned by a test reading both counts from the two tools' own sources (M6: drift 7 -> 8 -> red).

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

`pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q` (CI's own paths): **947 collected, 946 passed, 1 skipped, exit 0** in 1:50:24. `validate.sh` un-piped: **pass=115 warn=7 fail=0 skip=2**, exit 0. Coverage delta +5 (3 hook arms, 2 floor guards), all mutation-verified.

---

## Evidence

- **#194(a) zero-Python surface: HEALTHY, not the defect.** Fresh deploy target, un-piped. Normal PATH `86/1/0/8` exit 0; python-absent/git-present `76/10/0/9` exit 0 with `reduced assurance`. Both emit **95** result lines -- nothing vanishes, all 10 degradations name `python unavailable`. (First run confounded: `PATH=/usr/bin:/bin` also drops `git`.)
- **Pre-fix fail-open, staged PEM header (no key material).** A (real python) and B (no python) blocked. **C** non-startable python -> `(exit 49); continuing` -> exit 0, commit landed, `git show HEAD:leak.txt` returns it. **E** healthy python, scanner rc=3 -> `(exit 3); continuing`, validator green -> exit 0, commit landed. D blocked only *incidentally* via a validator FAIL -- confound, not containment.
- **Post-fix, same arms, `staged=1` asserted per arm**: A/B/C/E all exit 1 `commit blocked` -- C via the probe (no fallback line), E via the fallback. Benign control exit 0 on all four PATH states. E2E under C and E: `commit_exit=1`, `head_moved=NO`.
- **Mutation-verified at every round.** R0 vs pre-fix hook: `2 failed, 4 passed`, output showing `returncode=0` / `continuing (CI TruffleHog backstops)` / `validator passed`. Then M1 probe-deleted, M4 reduced-assurance-line-removed, M5 example-key-reintroduced and M6 message-count-drift each 1 failed; M2 fallback-deleted and M3 fallback-always-blocks each 2 failed; clean **15 passed**.
- **Live downstream break found and fixed (D-4).** No-Python adopter, deploy banner's own `git add`, 169 staged: before `COMMIT_EXIT=1` flagging `scan_credentials.py:79: aws-access-key-id`; after `COMMIT_EXIT=0`. Residual shapes in both edited files: **0**.
- **Floor vs scanner asymmetry** (D-1/D-4 basis, filed #195): floor reads whole staged blobs (`credential_floor.sh:33`), scanner only added lines; scanner allowlist case-insensitive (`:84`), floor not (`:40`); scanner self-excludes two files (`:62`), floor none. Floor screens 3 shapes, scanner 7 -- measured scanner `exit 1`/4 findings vs floor `exit 0` on one staged file.
- **Adopter delta (`deploy.sh:283-290`)**: an unmodified sample IS updated; a modified one gets `[SKIP] ... .acx-incoming`. But `.githooks/pre-commit` is a user copy deploy never rewrites (#197). `credential_floor.ps1` has zero runtime callers (#196).
- **The gap**: the e2e file had 3 arms, neither failure state had one, so the suite stayed green. Now 8 + 2 floor guards.
