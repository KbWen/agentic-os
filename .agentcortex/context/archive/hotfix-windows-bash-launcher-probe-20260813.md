# Work Log: hotfix/windows-bash-launcher-probe

## Header

- Branch: `hotfix/windows-bash-launcher-probe`
- Classification: `hotfix`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-13`
- Created Date: `2026-08-13`
- Owner: `claude-main-20260813`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `3faae10b801d001e82c7883d9145ade33c4e9813`
- Checkpoint SHA: `2bc0c7eb30fe3ede9d342537831b2c8bfa8b0496`
- Recommended Skills: `none`
- Primary Domain Snapshot: `tooling`
- SSoT Sequence: `149`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-13 (claude-main-20260813)`
- Platform: `claude-code`
- Files Read: `14`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §5 (testing), §12 (implement).

---

## Task Description

External (ChatGPT) audit `docs/reviews/2026-08-13-govern-audit-drift-core-health.md` handed over for remediation. This unit covers F1+F2 only: the Windows bash-launcher resolution used by the two shipped PowerShell deploy entry points accepts a bash that cannot execute `deploy.sh`, and the pytest bash-availability probe can abort collection instead of falling through.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-13 | Findings re-verified against real code paths before classification |
| plan | done | 2026-08-13 | Discriminating-probe design; e2e shape decided before editing |
| implement | done | 2026-08-13 | 6 files; e2e proven red before the fix |
| review | done | 2026-08-13 | 7 findings; R-1/R-2/R-6/R-7 fixed, R-3/R-4/R-5 dispositioned |
| test | done | 2026-08-13 | Full suite surfaced R-7; 883 passed after the one real failure was fixed |
| handoff | n/a | — | hotfix is exempt (state_machine.md) |
| ship | done | 2026-08-13 | PR #405 merged `2bc0c7e`, CI 18 pass / 1 skipping |

---

## Phase Summary

**bootstrap** — Re-verified all four findings against real code paths rather than accepting the report; two headlines needed correction. **F1's headline is refuted, its mechanism confirmed**: on a standard Git for Windows install `deploy.ps1` exits 0, writes the manifest, and the repo's own entry-point test passes — the supported Windows deploy path is *not* broken. What is real: `Resolve-BashLauncher` validates a candidate with `bash --version` alone, which `<git>\usr\bin\bash.exe` answers with exit 0 while carrying no `/usr/bin` on PATH. That candidate sits second in both entry points, so any layout lacking `bin\bash.exe` silently selects an unusable shell. **F2's class confirmed, reproduction environment-specific** (see Evidence). F3/F4 confirmed as stated, excluded per owner scope. Classification `hotfix` per §10.4 Supply-Chain Escalation.

**plan** — Make the probe discriminate rather than reorder the candidate list. `bash -c 'command -v dirname && command -v mktemp'` separates the two Git launchers because it asks for exactly what `deploy.sh` uses at startup. Candidate list and order stay byte-identical, so no working install loses its current launcher unless that launcher already could not run the script.

**implement** — Both entry points get the discriminating probe (`deploy_brain.ps1` carries a byte-divergent copy, hence a parity test rather than trusting review to catch drift). `has_bash_launcher()` gains a WindowsApps exclusion, an `OSError` handler, the same probe, and an injectable candidate list.

**review** — Seven findings, four fixed. Two mattered: the e2e's junction could have been followed by `TemporaryDirectory` cleanup into the real Git `usr/bin` on the 3.9 CI floor (R-1), and the fix made a previously-unreachable error path reachable, telling a user with a bare bash that "Bash is required" (R-6).

**test** — The full CI-equivalent suite earned this unit its most valuable finding. `1 failed, 883 passed`, and the failure was the one this repo has repeatedly recorded as a known local WSL-stub artifact. Treating that label as a hypothesis (`[paired-check-parity]`) exposed a third copy of the F2 defect: one test module resolving bash with no guard at all. The inventory that followed kept the fix small — eleven of twelve modules were already correct, so the answer was one aligned file plus a ratchet, not the broad test-helper refactor the audit warned against.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-13T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-13T01:00:00Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-13T02:00:00Z
- Gate: review | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-13T03:00:00Z
- Gate: test | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-13T04:00:00Z
- Gate: ship | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-13T12:45:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | `docs/reviews/2026-08-13-govern-audit-drift-core-health.md` | External (ChatGPT) audit; F1+F2 in scope, F3/F4 excluded by owner |
| PR | `https://github.com/KbWen/agentic-os/pull/405` | This unit |
| Spec | — | hotfix — no spec required |

---

## Known Risk

Root Cause: `Resolve-BashLauncher` conflated "a bash exists and reports a version" with "a bash that can run `deploy.sh`". `bash --version` is answered identically by `<git>\bin\bash.exe` (coreutils reachable) and `<git>\usr\bin\bash.exe` (bare, none on PATH).

- **R1** — A stricter probe could reject a working launcher on an unusual layout. Mitigated: probe only the two utilities the script actually calls; candidate list untouched.
- **R2** — This host cannot reproduce the reporter's exact failures, so the fix is validated against a *constructed* red case, not their environment. Recorded rather than claimed as a repro of their box.
- **R3** — Eleven other test modules still list `<git>/usr/bin/bash.exe`. Latent: fires only where those tests are unrunnable anyway. Named in the ratchet docstring, out of scope.

Rollback plan: `git revert 728ed55` — additive guards inside one function per entry point plus test-side changes; no state migration, no manifest change.

---

## Decisions

### D-1: Align one outlier instead of extracting a shared bash resolver
- Decision: fix `test_validator_worklog_family_skip.py` in place and pin the population with a ratchet, rather than extracting a shared helper for all twelve modules.
- Reason: inventory showed 11/12 already correct. A shared helper would be a cross-directory refactor of working code to fix one file.
- Alternatives: shared `tests/_bash.py` helper (rejected — YAGNI §5.4, and the audit explicitly warned against a blind test-helper refactor); leave it labelled an environment artifact (rejected — it is a real missing guard).
- Impact: one file changed, one ratchet added; the latent `usr/bin` candidate hazard stays open and named.
- → consolidated: L2 testing

### D-2: Accept a launcher on capability, not existence
- Decision: probe `command -v dirname && command -v mktemp` instead of `bash --version`; leave the candidate list and its order byte-identical.
- Reason: the two Git for Windows launchers are indistinguishable to `--version`; they differ only in whether coreutils resolve, which is exactly what `deploy.sh:4`/`:549` need.
- Alternatives: drop `usr/bin/bash.exe` from the candidate list (rejected — it is a valid launcher on layouts that put coreutils on PATH, and removing candidates can strand an install that works today); reorder only (rejected — does not help a layout with no `bin/bash.exe`).
- Impact: rejection can only narrow, never widen; a host that worked before still works.
- → consolidated: L2 tooling

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Stale local residue at bootstrap: `.agentcortex/context/work/chore-archive-codex-review-log.{md,lock.json}` (owner `codex-root-pr401`, lock stale >24h). Different worklog-key, so no phase-entry lock conflict. Archived twin already tracked; cleanup deferred to the follow-on F4 unit per owner scope.
- In-flight validation run stopped and restarted after the R-6 fix, so one run describes the final tree rather than editing around a running suite.
- Work Log compacted at ship after `validate.ps1` reported `[FAIL] work log compaction` (17.2KB against the 12KB active cap) — self-inflicted, fixed per the look-timing contract's own remedy clause.

---

## Review Feedback

| # | Finding | Sev | Disposition |
|---|---|---|---|
| R-1 | The e2e built a junction inside `TemporaryDirectory()`. `os.path.islink()` returns **False** for junctions (measured, 3.14) and only `shutil.rmtree` ≥3.12 recognises them — on the 3.9 CI floor a recursive cleanup could delete the real Git `usr\bin`. | HIGH | **Fixed** — `os.rmdir` in a `finally` before cleanup, skip path included. No damage occurred (364 files intact); removal semantics verified in isolation. |
| R-7 | The full run's `1 failed` was the failure this repo wrote off across more than one ship as a WSL-stub artifact. `test_validator_worklog_family_skip.py:39` was a bare `shutil.which("bash")` — no guard, no probe. **Same class as F2, third copy, mislabelled as environment noise.** | HIGH | **Fixed** — aligned to the sibling pattern after inventorying the population (11/12 already guarded). Pinned by `test_bash_resolver_parity.py`. |
| R-6 | The fix makes a previously-unreachable path reachable: a host with only a bare bash is told "Bash is required" while it *has* bash. | MED | **Fixed** — both entry points now say a bash that cannot resolve `dirname`/`mktemp` is skipped on purpose. No test asserts on this text. |
| R-2 | Only `deploy.ps1` is covered behaviourally; `deploy_brain.ps1`'s copy would silently regress. | MED | **Fixed** — parity test pins both. Honest ceiling: text parity, not behaviour. |
| R-3 | Does the probe match what `deploy_brain.ps1` invokes? It calls `deploy_brain.sh`. | — | **Verified** — `deploy_brain.sh:4` uses `dirname` in the same idiom and delegates to `deploy.sh`, which adds `mktemp`. |
| R-4 | `has_bash_launcher()` may now return False where it returned True (WindowsApps-only host with a live WSL distro). | LOW | **Accepted, correct** — those tests drive `deploy.ps1`, which excludes WindowsApps, so such a host would see a *failure*, not a pass. |
| R-5 | `deploy_brain.cmd:59` has a third, unprobed `where bash` path. | LOW | **Out of scope, recorded** — reachable only when `deploy_brain.ps1` is absent. |

---

## Security Findings

- No credential, token, or key touched. The change narrows which executable is selected to run framework installer code — a supply-chain surface — and narrows it only: the candidate list is unchanged and the new probe can reject a candidate, never admit one the old check rejected.

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

- `pytest tests/ci/ tests/guard/ .agentcortex/tests/` → **1 failed, 883 passed in 6532.81s (1:48:52)**. The single failure was `test_validator_worklog_family_skip.py::test_fresh_install_announces_the_absent_family_and_regains_it`, diagnosed as R-7 (a real missing guard, not the artifact it had been labelled) and fixed in this unit.
- Post-fix targeted re-run: `pytest tests/ci/test_bash_resolver_parity.py tests/ci/test_validator_worklog_family_skip.py` → **6 passed in 54.48s**, including the previously-failing test.
- `validate.ps1` on the final tree: **`Agentic OS integrity check passed`, no FAIL**. The prior run's `[FAIL] work log compaction` was this log at 17.2KB against the 12KB active cap — self-inflicted, fixed, re-run clean.
- **PR #405 CI, the authoritative evidence** — **18 pass / 1 skipping**, including `CI Structural Tests` (3m19s) and all three `Pytest (Windows)` shards (24m34s / 2m30s / 3m56s) on clean checkouts of the platform this fix targets. Merged `2bc0c7e`; every job completed before `mergedAt` (checked against the #270 red-merge class).
- **A third local full-suite run was started and deliberately stopped, not completed.** PR #405's CI runs the identical Structural suite *plus three Windows pytest shards* on a clean checkout, which is stronger and replayable evidence for exactly the platform this fix targets; repeating a ~2h local run of the same thing was waste. Local coverage of the delta since the 883-passed run (two test-only files) is the targeted 6-passed run above. Recorded as a stopped run rather than reported as a pass.

---

## Evidence

- **F1 headline refuted** — `deploy.ps1 <fresh temp dir>` → `EXIT=0`, `manifest exists: True`. `test_deploy_ps1_entrypoint_resolves_real_bash` → `1 passed in 39.61s`.
- **F1 mechanism confirmed** — `& '<git>\usr\bin\bash.exe' deploy.sh <fresh dir>` → `Exit code 127`; `deploy.sh: line 4: dirname: command not found`; `line 549: mktemp: command not found`; no manifest. The same binary answers `--version` with 0, which was the resolver's entire acceptance test.
- **Candidate asymmetry** — `bin\bash.exe -c 'command -v dirname; command -v mktemp'` → `/usr/bin/dirname`, `/usr/bin/mktemp`. `usr\bin\bash.exe` → `NO_DIRNAME`, `NO_MKTEMP`.
- **New e2e proven red before the fix** — probe reverted to `--version`: `AssertionError: deploy.ps1 selected a bash that cannot run deploy.sh` / `dirname: command not found` / returncode 127. With the fix: `1 passed in 22.74s`.
- **Helper unit tests** — `BashLauncherProbeTests` → `4 passed in 0.29s` (OSError fall-through with call-order assertion, WindowsApps never started, coreutils-less launcher rejected, empty candidates False).
- **Ratchet discrimination** — the ratchet's predicate against `git show HEAD:...family_skip.py`: resolves bash `True`, has guard `False` → the pre-fix module is exactly what it flags. Population: 12 modules call `which("bash")`, 11 guarded, 1 not.
- **F2 class confirmed, repro differs** — `--collect-only` → `11 tests collected` (no abort). `shutil.which("bash")` → `...\WindowsApps\bash.EXE`; `subprocess.run([that, "--version"])` returns rc=1 here rather than raising.
- **Host probe asymmetry** — pwsh 7.6.3 reports `$PSNativeCommandUseErrorActionPreference = False`, so a native non-zero exit under `Stop` does not throw here. The `try/catch` is defence-in-depth for hosts where a profile sets it `$true`, not a fix for an observed throw.
- **Final validator + suites, post-archival** (the one permitted terminal write): `validate.ps1` → **`pass=100 warn=3 fail=0 skip=3`, integrity check passed**. The drop from 118 is the documented backlog-#149 family SKIP — with no active Work Log the 18-check work-log family reports SKIP rather than running, so a clean-checkout total is lower by construction, not by regression. The 3 WARNs are the historical set the audit documented. `pytest tests/guard/ tests/ci/test_audit_witness.py .agentcortex/tests/test_guard_context_write.py .agentcortex/tests/test_lesson_chain_archival.py .agentcortex/tests/test_backlog_validation.py` → **360 passed in 240.74s**, run after the archival MOVE because that flips this log gitignored→tracked and changes what the disposition, chain and work-log checks see.
