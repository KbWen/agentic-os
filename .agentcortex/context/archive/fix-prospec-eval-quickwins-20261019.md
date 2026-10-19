# Work Log: fix/prospec-eval-quickwins

## Header
- Branch: `fix/prospec-eval-quickwins`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-19`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `b3d6905db37d03ee9672d8d5c10468824b437351`
- Checkpoint SHA: `b3d6905db37d03ee9672d8d5c10468824b437351`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `205`

---

## Session Info
- Agent: `claude-opus-5-5`
- Session: `2026-10-19T14:41:23Z`
- Platform: `claude-code`
- Guardrails loaded: skipped (quick-win)
- Override: none
- Downstream-Capabilities: none

---

## Task Description
Five small fixes from the 2026-10-19 external-framework comparison: (1) README/zh-TW/llms.txt overclaims about phase enforcement; (2) adopter CI snippet in docs/INSTALL.md pins actions by tag, not SHA; (3) deploy.sh treats `--help` / unknown flags as the target path; (4) /retro lesson-cap archival gains a retire-when-mechanized preference; (5) INSTALL.md per-platform invocation table.

---

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-19T14:41:23Z | quick-win; ADR-005/008 cover deploy.sh |
| plan | done | 2026-10-19T14:41:34Z | inline quick-win plan |
| implement | done | 2026-10-19T14:44:18Z | 7 files |
| review | PASS (re-review 2026-10-19T15:08:27Z) | 2026-10-19T15:04:03Z | fresh reviewer, 6 findings |
| test | done | 2026-10-19T15:26:44Z | targeted 147 + not-slow 852 |
| handoff | skipped | — | quick-win exempt |
| ship | done | 2026-10-19T15:26:44Z | local commit, no push (owner: publish later) |

---

## Phase Summary
- bootstrap: classified quick-win (5 surfaces, docs + one arg-parse fix + one workflow clause); no skills matched; deploy.sh covered by ADR-005/ADR-008 (arg parsing only — no source/provenance logic touched).

---

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T14:41:23Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T14:41:34Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T14:44:18Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Timestamp: 2026-10-19T15:04:03Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T15:07:10Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T15:08:27Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T15:26:44Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-19T15:26:44Z

---

## External References
| Type | Path / URL | Notes |
|---|---|---|
| ADR | docs/adr/ADR-005-downstream-file-preservation-tiering.md | covers deploy.sh |
| ADR | docs/adr/ADR-008-portable-safety-floor.md | covers deploy.sh |

---

## Known Risk
- README/zh-TW phrases are pinned by validator canary + tests/ci pytest; grep before rewording.
- deploy.sh is forwarded to by deploy.ps1 and installers/deploy_brain.*; a stricter arg parser must not reject any flag those pass.

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
- Scope add: deploy.ps1 (same `--help` bug found while testing deploy.sh; forwarding fix, 2 lines).
- Plan-entry lock: first `ensure --phase plan` passed a wrong `--session` string (exit 2, own lock read as another holder); the plan receipt was written before that exit code was checked. Re-ran with the lock's own session → exit 0 (updated). Process slip, own session only; no other holder involved.

---

## Review Feedback
- R1 MED: deploy.ps1 `-File --dry-run <path>` leaves $Target unbound → forwards `<path> .` → deploy.sh targets `.` (reproduced). Fix: forward $Target only when bound.
- R2 MED: remaining README/zh-TW/llms.txt sentences still claim the agent's report has no vote / skipped phase fails CI (README:24,70,95,133,231; zh-TW:24,27,66,111,204; llms.txt:5).
- R3 LOW: "catches a skipped step" too broad — no work log = SKIP; completeness checked only once a ship receipt exists.
- R4 LOW: installers/deploy_brain.cmd:28-32 comment says unknown tokens fall through to deploy.sh as target (now exit 2).
- R5 LOW: no tests for --help / unknown flag / ps1 forwarding.
- R6 NIT: INSTALL example C uses `/bootstrap` plain text; pin comment ambiguous about which repo.
- Re-review (same reviewer, fix verification): R1–R6 RESOLVED; R1 probed with an arg-echo stub in PS 5.1 + pwsh 7. Not fixed, pre-existing: pwsh 7 `-File` splits `--source=URL` at the colon (the `--source URL` form works) → PR follow-up note. Wording nits README:99/111, zh-TW:91 left (consistent with work-trail context).

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
none

---

## Evidence
- targeted: `pytest tests/ci/test_deploy_tiering.py tests/ci/test_deploy_dry_run_read_only.py tests/ci/test_deploy_brain_bootstrap.py tests/ci/test_pre_commit_hook.py .agentcortex/tests/test_lifecycle_token_consumption.py tests/ci/test_directive_count_ratchet.py` → 147 passed, 2 skipped (7m37s).
- not-slow: `pytest tests/ci/ tests/guard/ .agentcortex/tests/ -m "not slow"` → 852 passed, 202 deselected. Full unfiltered suite left to CI at publish time.
- validators: validate.sh = validate.ps1 `pass=115 warn=6 fail=0 skip=2` (only branch-related WARN = this log's sentinel, cleared by the ship Phase Summary line).
- mutation: the 6 new tests all fail on HEAD deploy.sh/deploy.ps1; the ps1 flag-first case fails on the first-iteration fix (`@args "$Target"`).
- Demonstration: `bash .agentcortex/bin/deploy.sh --help` → `Usage: ... [--dry-run] [--source <git-url>] [/path/to/your-project]`, exit 0; `deploy.sh --bogus` → `ERROR: Unknown option '--bogus'.`, exit 2; `powershell -File deploy.ps1 --dry-run tgtA` (PS 5.1 + pwsh 7) → `[DRY RUN] Would deploy ... to tgtA` (was `to .`).
- final (post-archive): validate.sh = validate.ps1 `pass=116 warn=5 fail=0 skip=2`; `scan_credentials.py --staged` clean.
