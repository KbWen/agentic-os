# Work Log: chore/ssot-drift-and-residue-cleanup

## Header

- Branch: `chore/ssot-drift-and-residue-cleanup`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-13`
- Created Date: `2026-08-13`
- Owner: `claude-main-20260813`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `3faae10b801d001e82c7883d9145ade33c4e9813`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `149`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-13 (claude-main-20260813)`
- Platform: `claude-code`
- Files Read: `4`

---

## Task Description

Second unit of the 2026-08-13 external-audit remediation, scoped by the owner as "F4 + residue cleanup". Remove the stale hand-maintained backlog count from the SSoT, and clear the two local Work Log residue files left by an external reviewer's Codex session — by archiving the log, not deleting it.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-13 | Spec Index checked — no spec covers SSoT prose or archival |
| plan | done | 2026-08-13 | Archive-not-delete decided after the residue proved not to be a duplicate |
| implement | done | 2026-08-13 | Log archived + chain appended + stale lock removed |
| ship | done | 2026-08-13 | Guarded SSoT write; seq 149→150 |

---

## Phase Summary

**bootstrap** — Two independent items, both verified before planning. **F4**: `current_state.md:30` says `59 Pending as of 2026-08-09`; strict row parsing of `_product-backlog.md` yields **64**. Confirmed the drift is inert to machinery — `validate.sh:2442-2450` checks only the backlog *path*, and no test references the number — so this is document drift with a manual-carry-forward failure mode, not runtime corruption. **Residue**: `chore-archive-codex-review-log.{md,lock.json}`. The first check nearly produced a wrong action: the archive already holds `chore-archive-codex-review-log-20260812.md`, which looked like the same file's twin. It is not — that is *this* repo's own log for the branch (`Owner: KbWen`, phase `ship`), while the active residue is the **external Codex reviewer's own log** (`Owner: codex-root-pr401`, phase `review`, 8 findings). Deleting it would have destroyed a different-vendor review artifact, which is the exact class of thing PR #401 existed to preserve. Read in full before any move: no credentials, and the PII it reports (backlog #170) is described, not reproduced.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T05:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T05:10:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T05:20:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T05:40:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | `docs/reviews/2026-08-13-govern-audit-drift-core-health.md` | F4 source (lands via PR #405) |
| PR | `https://github.com/KbWen/agentic-os/pull/405` | Unit 1 of this remediation (F1+F2) |
| Spec | — | quick-win — Spec Index checked, no existing spec covers this area |

---

## Known Risk

- **R1** — Archiving another owner's log makes a gitignored file public. Mitigated by reading it end to end first; it contains no credentials and does not reproduce the #170 email.
- **R2** — `INDEX.jsonl` is a hash chain; a wrong append breaks `check_audit_chain.py` for every later entry. Mitigated by using `append_chain_entry.py` (the only chain-aware path) and re-running the validator afterwards.
- **R3** — Deleting the volatile count removes a small dashboard convenience. Accepted: the count went stale within three days of being written, and the canonical backlog is one click away.

Rollback plan: revert the single commit; the archived log returns to untracked state and the SSoT line is restored verbatim.

---

## Decisions

### D-1: Delete the SSoT backlog count rather than machine-checking it
- Decision: remove the hand-maintained `N Pending as of <date>` figure and point at the canonical backlog; add no validator check.
- Reason: the audit's own preference, and the DELETE-bias norm. A generated-and-checked count would mean a new Python tool behind `run_python_check`, a `deploy.sh` whitelist entry and a golden-manifest row (ADR-006 + the new-validator-check contract) — machinery whose cost exceeds a low-severity prose drift.
- Alternatives: regenerate the count at each ship (rejected — same manual carry-forward, one step removed); machine-checked count (rejected on cost above).
- Impact: the failure mode is removed rather than monitored. Wave-specific history in that line moves out; it is already recorded in Ship History.
- → consolidated: L2 document-governance

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Non-ship SSoT write exception not used: this unit's SSoT edit *is* its ship write, done through `guard_context_write.py` (receipt `.guard_receipts/337ffd90d88a8b4f.json`, `expected-sha ad02a4d1…` → `b261d8e0…`).
- **New drift found while validating, not in the external audit**: `security_guardrails.md:66` requires a `## Security Findings` section in review/ship-phase logs and both validators WARN when it is missing (#288), but `.agentcortex/templates/worklog.md` does not ship that heading (`grep -c` → 0). Every feature/hotfix log created from the template therefore earns the WARN unless the agent adds the section by hand — including downstream adopters, since the template propagates via `deploy.sh`. Both of this session's logs were fixed by hand; the template itself is **surfaced to the owner, not silently changed**, because templates are on the tiny-fix exclusion list and propagate downstream.
- **Self-inflicted, caught by this repo's own check.** The log was archived before its `## Decisions` entry carried a disposition marker, and `check_decision_disposition.py` fired on the fresh archive (`tests/guard/test_decision_disposition_check.py::test_real_repo_is_clean`, 1 failed / 356 passed). The WARN it emits is by design permanent — archived logs are immutable. Recovered only because the move was uncommitted: un-archived, D-1 dispositioned `→ consolidated: L2 document-governance` with the decision written into `docs/architecture/document-governance.log.md`, then re-archived under the same filename so the INDEX entry stays valid. The ordering rule (`ship.md 2b`: markers go in the ACTIVE log, immediately before the MOVE) is now also a `[CONSTRAINT]` in that L2 log. This also closes the audit's own `routing_actions` entry for `document-governance.log.md` with a verified decision rather than a claim.
- Residual state from the paused unit 1 cleared here rather than left for the validator to keep reporting: its Work Log was re-compacted under the 12KB active cap and its lock released (that unit is paused on PR #405 CI, so holding a `plan`-phase lock was both stale and a false claim of an active writer).

---

## Review Feedback

none

---

## Security Findings

- The archived Codex log was read end to end before being moved from gitignored to tracked in a public repo: no credentials, tokens, or keys. It *reports* the backlog #170 PII finding but does not reproduce the email, so archiving it adds no PII.

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

- **F4 drift confirmed** — SSoT line 30 reads `59 Pending as of 2026-08-09`; `grep -c "| Pending " docs/specs/_product-backlog.md` → **64**.
- **F4 is inert to machinery** — `validate.sh:2442-2450` validates only the Active Backlog *path* (`FAIL` when set to `none`, otherwise a path comparison). `git ls-files | xargs grep -l "59 Pending"` → only `current_state.md` and the audit doc.
- **Residue is not a duplicate** — active log 166 lines `Owner: codex-root-pr401` / `Current Phase: review`; archived `-20260812.md` 244 lines `Owner: KbWen` / `Current Phase: ship`. Different sessions, same branch.
- **Prior disposition located** — `archive/chore-archive-codex-review-log-20260812.md:242` records the residue being left in place deliberately, "because they belong to another owner". That session has since ended; its lock `updated_at` is 2026-08-12T05:44Z against a 60-minute stale timeout, and PR #401 merged at `6f9205d`.
- **Final validator, post-archival** (the one permitted terminal write): `validate.ps1` → **`pass=118 warn=3 fail=0 skip=2`, integrity check passed**. The 3 remaining WARNs are the historical set the external audit already documented (3 archived logs with a ship receipt but no plan/implement gates, 1 archived receipt missing Verdict/Classification, 28 tier-blind eval-coverage sections — backlog #143). The stale-lock WARN the audit listed as its 4th group is gone. Machine-local counts: a clean checkout runs fewer active-work-log checks and reports lower totals.
- **Post-archival suites** — `pytest tests/guard/ .agentcortex/tests/test_guard_context_write.py .agentcortex/tests/test_lesson_chain_archival.py tests/ci/test_audit_witness.py` → **357 passed in 186.02s**, run after the archival MOVE because that flips the log gitignored→tracked and changes what the disposition and chain checks see. The same command before the disposition fix was **1 failed / 356 passed**.
