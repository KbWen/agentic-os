# Work Log: chore/downstream-chain-honesty

## Header

- Branch: `chore/downstream-chain-honesty`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-13`
- Created Date: `2026-08-13`
- Owner: `claude-main-20260813`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `c1741de51c1a623e4568104a4ae3299086d47aac`
- Checkpoint SHA: `0eeba9b`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `153`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-13 (claude-main-20260813)`
- Platform: `claude-code`
- Files Read: `6`

---

## Task Description

A downstream development-flow simulation (run at the owner's request, after the wave had already merged) found that `ship.md` promises adopters a chain-integrity check they do not receive. This unit corrects the deployed prose; the deploy decision behind it is filed as backlog #173.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-13 | Found by simulation, not by review of the diff |
| plan | done | 2026-08-13 | Split: correct the false prose now, file the deploy decision |
| implement | done | 2026-08-13 | 2 sentences in ship.md + backlog row #173 |
| ship | done | 2026-08-13 | — |

---

## Phase Summary

**bootstrap** — Simulated an adopter's governed loop against a real `deploy.sh` target rather than reasoning about it. The loop itself is intact: the governance tools are deployed and runnable, the Work-Log lock acquires and releases, `guard_context_write.py` accepts a valid `expected-sha` and **rejects a stale one** (optimistic locking still bites downstream), a clean install validates `pass=87 warn=1 fail=0 skip=6`, and a deliberately un-indexed ADR is caught. But an adopter who has shipped once holds an `INDEX.jsonl` that nothing verifies: `ship.md:202` (deployed) instructs the append via `append_chain_entry.py` (deployed), while `check_audit_chain.py` is absent from `deploy.sh`'s whitelist and always has been. Observed, not inferred: `[SKIP] audit chain integrity (INDEX.jsonl) -- tool not present`.

**plan** — Two separable problems. The **prose is false regardless of how the deploy question resolves** — `ship.md:208`/`:210` tell adopters a broken chain is caught and will fail their validator, and downstream neither happens. That is corrected here. Whether the checker *should* ship is an ADR-003-adjacent decision with precedent on both sides, so it is filed (#173) rather than decided in a wrap-up unit — the same reasoning that routed `.guard_receipt.json` to #172.

**implement** — Two sentences reworded to say the check is source-repo-only and that downstream breakage goes unreported. Cost measured before editing, not after: a 400-character probe on `ship.md` moves the aggregate by 606 tokens (~1.5×/char), and the edit landed at **+126** against 431 headroom, leaving 305.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T17:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T17:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T17:15:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-13T17:30:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | `docs/adr/ADR-003-hash-chained-audit-log.md` | Owns the deploy decision (#173) |
| Issue | `docs/specs/_product-backlog.md` #173 | Filed by this unit |

---

## Known Risk

- **R1** — Correcting the prose does not restore the control; adopters still have no chain verification. Stated in the text itself rather than papered over, and #173 carries the fix.
- **R2** — If #173 later deploys the checker, these two sentences need updating again. Accepted: a doc that is honest today and edited later beats one that misleads until then.

Rollback plan: revert the commit — two sentences and one backlog row, no engine change.

---

## Decisions

### D-1: Correct the prose now, file the deploy decision
- Decision: reword `ship.md:208`/`:210`; do not add `check_audit_chain.py` to the deploy whitelist in this unit.
- Reason: the false statement harms adopters today and its correction is true either way. Whether the checker ships is ADR-003-adjacent and has precedent on both sides — `check_skill_provenance.py` (#379) and `check_worklog_references.py` (#161) are *deliberately* source-only, while ADR-003:140 names "fresh downstream" as a handled case and the check is wired at FAIL severity, not as a CI-only SKIP.
- Alternatives: deploy the tool here (rejected — changes what adopters execute, needs the golden-manifest regeneration and a per-tool decision across all 7 absent tools); leave the prose (rejected — it tells adopters they are protected when they are not).
- Impact: adopters read the truth now; the control gap stays open and named.
- → consolidated: L2 governance

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- **My own backlog row was malformed and the validator caught it.** Row #173 first contained `` `.agent/workflows|rules/*.md` `` — a literal `|` inside a markdown table cell — which shifted every column right, so the Labels field parsed as `framework` and tripped `[WARN] backlog label vocabulary: 16 distinct labels (>15)`. Diagnosed by cell-counting (13 where 12 are expected) rather than by dismissing a `warn=3 → warn=4` delta, per the `[paired-check-parity]` Global Lesson. Fixed; counts returned to the exact baseline.
- Earlier in this investigation I claimed the SKIP wording (`tool not present` vs `CI-only validator not deployed (safe to ignore downstream)`) proved the omission was accidental. **That inference was wrong** — `check_skill_provenance.py` and `check_worklog_references.py` are documented as deliberate and print the same generic string. Corrected before it reached any record; #173 states the non-discrimination explicitly so the next reader does not repeat it.

---

## Review Feedback

none

---

## Security Findings

- No credential, key, or token touched. The change is prose-only and *widens* the adopter's view of their own risk rather than narrowing it: it removes a claim of protection that does not exist.

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

- `pytest .agentcortex/tests/test_backlog_validation.py .agentcortex/tests/test_lifecycle_token_consumption.py` → **45 passed in 106.23s**.
- `validate.ps1` → **`pass=100 warn=3 fail=0 skip=3`**, integrity check passed — exactly the pre-change baseline, after the malformed-row fix.

---

## Evidence

- **Gap observed, not inferred** — fresh `deploy.sh` target + one real `append_chain_entry.py` append + the deployed `validate.sh` → `[SKIP] audit chain integrity (INDEX.jsonl) -- tool not present`. The tools directory contains `append_chain_entry.py` and `check_lesson_chain.py` but not `check_audit_chain.py`.
- **Never deployed** — `git log -S check_audit_chain -- .agentcortex/bin/deploy.sh` returns no commits; this wave's entire `deploy.sh` diff is the 5-line ignore-block change.
- **Wider class** — the deployed validators reference 19 tools; 7 are absent, at least 4 of them deliberately.
- **Guard blind spot** — `test_deployed_governance_referenced_tools_are_deployed` matches the literal path `.agentcortex/tools/<name>.py` in governance docs only; `ship.md` names this tool as a bare backticked filename, and the deployed validators are not in the scan set.
- **Token cost measured before the edit** — 400-char probe on `ship.md` → +606 aggregate tokens; the real edit → **+126** (354,569 → 354,695), headroom 431 → 305.
- **Final validator, post-archival** (the one permitted terminal write): `validate.ps1` → **`pass=100 warn=3 fail=0 skip=3`, integrity check passed** — the exact pre-change baseline. `check_decision_disposition.py` OK across 19 logs after D-1 was re-dispositioned from `→ local` to `→ consolidated: L2 governance`: the checker's A2 signal fired because a `→ local` entry named an ADR, and it was right — the correct-now / route-the-open-question pattern had by then been applied twice in one wave and belonged in the L2 log. Caught before commit; the archive was un-moved, fixed and re-archived, the same recovery PR #406 needed.
