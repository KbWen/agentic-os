# Work Log: feat/test-evidence-freshness

## Header
- Branch: `feat/test-evidence-freshness`
- Classification: `feature`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-19`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `a74b37e`
- Checkpoint SHA: `bbd59cb`
- Recommended Skills: `none`
- Primary Domain Snapshot: `testing`
- SSoT Sequence: `209`

---

## Session Info
- Agent: `claude-opus-5-5`
- Session: `2026-10-19T17:13:24Z`
- Platform: `claude-code`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §5, §6, §12, §13
- Override: none
- Downstream-Capabilities: none

---

## Task Description
Tie recorded test runs to the code they tested: record_test_run.py runs the suite and writes exit + a code fingerprint into Test Gate Results; validate fails a ship whose code changed after the last recorded run, or a failed run followed by a PASS receipt. Owner approved the spec freeze in chat 2026-10-20.

---

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-19T17:13:25Z | feature; spec frozen (owner 2026-10-20) |
| plan | done | 2026-10-19T17:13:41Z | - |
| implement | done | 2026-10-19T17:16:19Z | - |
| review | done | 2026-10-20T04:02:39Z | NOT READY → 2 re-reviews → PASS |
| test | done | 2026-10-20T04:02:39Z | full suite 1095 via recorder |
| handoff | done | 2026-10-20T04:02:40Z | - |
| ship | done | 2026-10-20T04:02:59Z | local commit, no push |

---

## Phase Summary
- bootstrap: feature; spec docs/specs/test-evidence-freshness.md frozen with owner approval (chat 2026-10-20); primary_domain testing (L2 docs/architecture/testing.log.md). Worktree at scratchpad/wt-u5, based on a74b37e; rebase onto the U6 ship before /ship (SSoT serializes). Confidence: 85% — assumption: git write-tree on a copied index is stable across Git for Windows and Linux.
- plan: (1) .agentcortex/tools/record_test_run.py (run/check; stdlib); (2) validate.sh + validate.ps1 call it via run_python_check / Invoke-PythonCheck (WARN when Python missing); (3) deploy.sh runtime_tools + second whitelist site, manifest golden regenerated; (4) test.md: record the suite through the tool when Python is available, funded by an equal trim in test.md (lifecycle ceiling); (5) README enforcement table row + zh-TW: catches stale/failed runs, not hand-typed lines; (6) tests/ci/test_record_test_run.py: AC-1..AC-7 incl. both validators on one fixture; (7) L2 entry in docs/architecture/testing.log.md at ship. Rollback: revert the commit; logs without a Test run line are unaffected, so no adopter state depends on it.
- implement: new .agentcortex/tools/record_test_run.py (run/check; temp-index write-tree fingerprint excluding .agentcortex/context; owner-prefixed logs counted only when their Branch header matches). Wired: validate.sh + validate.ps1 (same label, WARN when no Python; ps1 BOM kept), deploy.sh both whitelist sites, manifest golden +1 line. test.md: one sentence pointing at the recorder, funded by three trims in the same file (lifecycle aggregate 354,999 → 354,619). README + zh-TW enforcement row. 12 tests in tests/ci/test_record_test_run.py. §12.1: read validate.sh run_python_check contract (:177-209), ps1 Invoke-PythonCheck call shape (:864), deploy.sh whitelist sites (:828, :1059), test.md (whole).
- review NOT READY (R1–R7) → implement: copy2 + update-index --refresh (racy entries re-read; copyfile mutant killed by a 5-repeat same-size test); receipts parsed as instants (Z/offset/minute/date-only; unparseable = later), case-insensitive; unstable FAILs once shipped; shutil.which resolves .cmd shims; symbolic-ref with an explicit detached-HEAD WARN; recorded command collapsed to one line (a newline used to split the record and silence check — found while testing); ship.md pre-merge step 2 runs through the recorder and requires check exit 0; README/zh-TW row says /ship runs the check and the command itself is not verified; test.md keeps 'Name tests descriptively' and cites the tool path; spec limits listed. Lifecycle 354,901 (< 355,000). Tests 22 passed ×3.
- review: two re-review rounds; all findings resolved or disclosed as stated limits; 27 tests pass.
- test: full CI-equivalent suite 1095 passed through the recorder (dogfood). handoff: Resume block written.
- ship: pre-merge check rc=0 after the ship receipt; SSoT + archive first, then spec status shipped + Spec Index + L2 testing (after archival, per ship.md order). Local commit, not pushed. ⚡ ACX

---

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-10-19T17:13:25Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-10-19T17:13:42Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-19T17:16:19Z
- Gate: review | Verdict: NOT READY | Classification: feature | Timestamp: 2026-10-19T17:42:24Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-19T17:48:30Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-10-20T01:17:10Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-10-20T04:02:39Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-10-20T04:02:40Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-10-20T04:02:48Z

---

## External References
none

---

## Known Risk
- Rollback plan: revert the commit; the check is opt-in by the presence of a Test run line, so reverting strands no adopter state.
- git add -A on a temp index writes blob objects for untracked files into .git/objects (unreferenced; removed by gc). The real index is never written.
- Receipt timestamps are agent-written; the failed-run rule compares them with the recorder's UTC time. A receipt written in local time with no Z could mis-order (template asks for UTC).

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
- Smoke-tested the new tool against this log during bootstrap; the smoke line was removed (not test evidence).
- ADR Coverage Check: validate.sh/validate.ps1 covered_by ADR-006 (Python tool behind run_python_check — followed); deploy.sh ADR-005/008 (whitelist addition only); new tool/test/spec: no_covering_adr — accepted (ADR-006 seam is the governing decision).
- Recovered stale Work Log lock on 2026-10-20T01:17:10.458561+00:00; prior_owner=KbWen; prior_session=2026-10-19T17:13:24Z; reason=stale-time; lock=feat-test-evidence-freshness.lock.json
- Recovered stale Work Log lock on 2026-10-20T03:07:11.811284+00:00; prior_owner=KbWen; prior_session=2026-10-19T17:13:24Z; reason=stale-time; lock=feat-test-evidence-freshness.lock.json
- Rebased (stash + fast-forward + pop) onto bbd59cb after U6 shipped; SSoT Sequence header stays the bootstrap snapshot (209), live is 210. Compact index fresh, lifecycle 354,901 after rebase.

---

## Review Feedback
- R1 HIGH: copyfile resets the temp index mtime → racy-git stat trust misses same-size edits (7/15 loop failures); copy2 → 0/15.
- R2 HIGH: README 'validate.sh fails the ship' unreachable — ship receipt at Turn 1, log archived at step 3, ship.md never runs the check; pre-merge merge changes the tree after the receipt and its re-run is unrecorded.
- R3 MED: receipt timestamps string-compared: +08:00 false FAIL, -05:00 miss; date-only / minute precision / 'Gate: Ship' ignored.
- R4 MED: unstable never FAILs even with ship receipt; recorded no-op after a failed suite passes — README does not admit the command is unverified.
- R5 MED: no-shell launch fails on Windows .cmd shims (npm) → 127.
- R6 LOW: detached HEAD silently 'nothing checked'; unborn branch → 'not a git work tree'.
- R7 LOW: spec says 'prints last lines' (code passes output through); test.md trim dropped 'Name tests descriptively' and cites the tool without its path; untracked nested repo/submodule edge cases.
- Re-review 1 (same reviewer): R1–R7 RESOLVED (15-loop flake 0/15; tz/date/case probes; npm shim; detached HEAD). New: N1 MED Unicode separators (\x85/U+2028/U+2029) hid a run; N2 MED unfingerprintable tree → permanent ship FAIL; N3 LOW date-only read as 00:00. Fixed: splitlines join; tree: none = WARN only; date-only = 23:59:59Z (checked before fromisoformat).
- Re-review 2: N1–N3 RESOLVED with probes. New LOW: a deliberately unreadable tree (empty nested repo) ships stale code with a WARN — disclosed in README/zh-TW row and spec limits (same class as a hand-typed line); recorded command now shown as typed, not the resolved path.

---

## Red Team Findings
none

---

## Security Findings
- [MEDIUM — A03] recorded command could carry newlines / Unicode separators that split the record and silence check — RESOLVED (splitlines join + control-char filter; tests for \n, U+2028, U+2029, \x85). [LOW] deliberate unreadable tree → WARN only: disclosed limit. No unresolved HIGH/CRITICAL.

---

## Design Reference
none

---

## Observability
none

---

## Resume
- State: HANDEDOFF
- Completed: bootstrap, plan, implement, review (NOT READY → two re-reviews → PASS), test (full suite 1095 recorded through the tool)
- Next: /ship in ship.md order — pre-merge `record_test_run.py check` exit 0 → ship receipt → SSoT + archive → spec shipped + Spec Index + L2 testing.log.md
- Context: test evidence is now tied to the code it tested; FAIL on a failed run before a PASS receipt or code changed after the run at ship; opt-in by a recorded line; stale/failed caught, forged not.

### Read Map (for next agent)
- docs/specs/test-evidence-freshness.md → full
- .agentcortex/tools/record_test_run.py → module docstring, check_log()

### Skip List
- tests/ci/test_record_test_run.py — 27 passing, mutation-checked
- .agentcortex/bin/validate.sh / validate.ps1 — one wiring line each, reviewed

### Context Snapshot (≤ 200 tokens)
Fingerprint = write-tree of a copied index (copy2 + refresh) minus .agentcortex/context. Receipts parsed as instants; bare date = end of day. tree: none = WARN only; unstable FAILs once shipped. /ship pre-merge step 2 runs the check before archival; docs written after archival are invisible to it by design. Lifecycle aggregate 354,901 (< 355,000).

### Backlog Status (if applicable)
- Active Backlog: docs/specs/_product-backlog.md
- Current Feature: none (wave item, no backlog row)
- Remaining: see backlog
- Next Recommended: re-score panel; wave-2 candidate #239

---

## Test Gate Results
- Test run: `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q -p no:cacheprovider` | exit: 0 | tree: 33b5f12c2417ef6f52c3d50a3d4bb05741130a55 | at: 2026-10-20T04:02:15Z
- Full CI-equivalent suite (no marker filter) through the recorder → 1095 passed, 2 skipped (55m01s); the recorded line above is that run. `record_test_run.py check` → '1 log(s) current'.

---

## Evidence
- Test Files: tests/ci/test_record_test_run.py (27 tests). Mutants killed: exclusion removed, branch filter removed, shell launch, ship-FAIL off, later-receipt rule off, copyfile index copy.
- Pre-merge (ship.md step 2): branch is at bbd59cb, the current local head — nothing to sync; `record_test_run.py check` with the ship receipt present → '1 log(s) current', rc=0.
