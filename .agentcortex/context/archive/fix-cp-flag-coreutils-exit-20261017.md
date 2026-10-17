# Work Log: fix/cp-flag-coreutils-exit

## Header

- Branch: `fix/cp-flag-coreutils-exit`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `2026-10-17`
- Created Date: `2026-10-17`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `3f06eb7`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `deploy`
- SSoT Sequence: `198`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-17 14:22 UTC` (8ab306f9)
- Platform: `claude-code`

---

## Task Description

PR #470 CI ("CI Structural Tests", Linux) failed the four `CP_FLAG=-i` answered-"n" cases of the #221 tests: coreutils >= 9.2 makes `cp -i` exit 1 when declined (8.32 locally exits 0), and `_cp_framework_version` turned that into `exit 1`, aborting the deploy. The pre-#221 code aborted the same way under `set -e`, so this is a pre-existing CP_FLAG defect the new tests exposed. Same pattern in the first-install branch and the `.gitkeep.md` placeholder copy.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-17 | quick-win; follow-up to shipped #221 |
| plan | done | 2026-10-17 | inline plan below |
| implement | done | 2026-10-17 | 3 cp sites |
| review | done | 2026-10-17 | self-review |
| test | done | 2026-10-17 | emulated coreutils 9.2 + real 8.32 |
| ship | done | 2026-10-17 | SSoT 198->199 |

---

## Phase Summary

- bootstrap: quick-win (deploy.sh only). Root cause from the CI log: `test_cp_flag_i_reads_answers_from_stdin_not_the_deploy_list[{batch,per-file}-n-{core,skill}]` → `deploy failed ... assert 1 == 0` at tests/ci/test_deploy_tiering.py:730; the Linux runner's coreutils exits 1 on a declined `-i`.
- plan: in `_cp_framework_version`, record cp's status instead of exiting; for `-n`/`-i` the post-copy hash decides kept vs delivered (either coreutils behaviour); any other nonzero status still exits. Route the first-install core copy through the same helper (its own post-copy hash check stays equivalent). `.gitkeep.md` placeholder: accept a nonzero cp when the placeholder exists. Rollback: revert the commit.
- implement: as planned; default (empty CP_FLAG) path unchanged — cp's nonzero status still exits with that status.
- review: a real cp failure under `-n`/`-i` that leaves dst unchanged is now reported `[KEPT]` instead of aborting; cp's own error line is still printed on stderr. Accepted: it cannot be told apart from a decline by exit code on coreutils >= 9.2. The other `cp ${CP_FLAG}` sites write to absent paths (new file, `.acx-incoming` after cleanup, `.acx-local` after `rm -f`), so they never prompt or skip.
- test: see Evidence. ship: PASS; SSoT 198->199; archive `fix-cp-flag-coreutils-exit-20261017.md`.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:22:30Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:22:40Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:22:50Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:23:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:23:10Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:23:16Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog-archive.md | row #221 (Shipped) |
| ADR | docs/adr/ADR-005-downstream-file-preservation-tiering.md | — |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/470 | CI run 39036380407 |

---

## Known Risk

- See review: a genuine cp failure under -n/-i reads as [KEPT] (stderr still shows cp's error).

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

- Work was done before this log existed (diagnose → patch → test, 14:10–14:21Z, CI auto-fix event); all receipts were written together at 14:22–14:23Z after the work, not at each phase end.

---

## Review Feedback

none

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

- CI run 39036380407 (Linux): 4 FAILED `...[batch-n-core|batch-n-skill|per-file-n-core|per-file-n-skill]`, `deploy failed`, `assert 1 == 0`.
- Local emulation of coreutils >= 9.2 (`BASH_ENV` shim: cp -n/-i returns 1 when dst is not replaced): pre-fix deploy.sh `-k "cp_flag_i and n-"` → 4 failed (CI reproduced); fixed → `-k cp_flag` 13 passed; `-k "brownfield or cp_flag"` 21 passed.
- Real coreutils 8.32, no shim: deploy_tiering + dry_run_read_only + install_day_copy → 70 passed, 2 skipped.
