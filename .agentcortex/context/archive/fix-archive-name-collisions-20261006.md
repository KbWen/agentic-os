# Work Log: fix/archive-name-collisions

## Header

- Branch: `fix/archive-name-collisions`
- Classification: `feature`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-06`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `9905177b9850416a34b1a5f1b1c6db213ea2134c`
- Checkpoint SHA: `9dbd5ac`
- Recommended Skills: `verification-before-completion (auto), systematic-debugging (auto: false-PASS bug), red-team-adversarial (auto: feature→Full), karpathy-principles (auto), test-driven-development (auto: validator check is testable logic)`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `188`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-06 08:43 UTC`
- Platform: `claude-code`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §6 (feature), §13 (workflow edits)
- Override: none
- Downstream-Capabilities: `.agentcortex/context/private/downstream-capabilities.yaml` present (this is the framework repo's own dogfood file; not re-parsed — no custom skill or KB routes this task)
- Context Read Receipt: current_state.md (Last Verified 2026-10-05 → 2026-10-06, Seq 188) · Work Log created · Spec scope: none mapped (audit-chain-tamper-evidence + decision-capture-hardening are [Shipped], primary_domain document-governance → L1 read instead)

---

## Task Description

- Fix archive naming collisions per `docs/specs/archive-name-collisions.md` (AC-1..AC-10): D4 false PASS, undefined same-day ship/compaction names, #186.
- Compacted: 2026-10-06, archive: `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md`

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-06 | classified feature |
| plan | done | 2026-10-06 | 8 steps, TDD-first |
| implement | done | 2026-10-06 | TDD; 12 files + 2 moves |
| review | done | 2026-10-06 | NOT READY then PASS (3 fresh reviewers) |
| test | done | 2026-10-06 | full not-slow 832 + slow 4 |
| handoff | done | 2026-10-06 | ship next |
| ship | done | 2026-10-06 | PR #464 |

---

## Phase Summary

- bootstrap/brainstorm/spec/plan/implement-r1/review-NOT-READY lines moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` §Phase Summary (keep_recent_entries 5). ⚡ ACX
- implement (round 2): BOM restored + byte pin; D4 verdict gated on child exit 0 (sh+ps1); ps1 child under local Continue; ps1 `@'...'@`; identical re-append = no-op; token-governance "create it if absent". Confidence: 93% — high.
- review: PASS — fresh re-review READY (AC-1..7, 9 PROVEN by runs); AC-8 [NEEDS_HUMAN] amended with owner approval (chat 2026-10-06, commit 1a9cd46: text-only, 32 tests pass); AC-10 [NEEDS_HUMAN] carried to /test + PR CI by owner.
- test: 832 not-slow + 5 slow pass; AC-1..AC-9 mapped to tests; AC-10 = final validators + PR CI.
- handoff: ship:[doc=docs/specs/archive-name-collisions.md][code=.agentcortex/bin/validate.sh][log=.agentcortex/context/work/fix-archive-name-collisions.md]
- ship: PASS — PR #464 (draft, CI pending); SSoT seq 188->189; INDEX appended via the new guard; log archived to `.agentcortex/context/archive/fix-archive-name-collisions-20261006.md`. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T08:43:41Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T09:05:58Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T09:39:39Z
- Gate: review | Verdict: NOT READY | Classification: feature | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-10-06T09:59:25Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T10:20:22Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T10:33:06Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T10:36:01Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T10:49:41Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-10-06T10:51:27Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/archive-name-collisions.md | frozen 2026-10-06 |
| External | logrotate.c `prerotateSingleLog()` "destination %s already exists, skipping rotation" | collision precedent: fail closed, no renumber |
| ADR | docs/adr/ADR-003-hash-chained-audit-log.md | covers validate.* (INDEX.jsonl chain) — check_adr_coverage exit 0 |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | new checks = Python tools behind run_python_check |
| ADR | docs/adr/ADR-002-guarded-governance-writes.md · ADR-010 | also cover validate.* |
| Domain | docs/architecture/document-governance.md | L1 read at bootstrap |
| Backlog | #186, #155, #179, #3 | adjacent compaction/archive rows |

---

## Known Risk

- R1-R6 (token ceiling, twin drift, no-python SKIP, shim, history moves, deployed guard): all mitigated and verified; moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` §Known Risk.
- R7 (other `$(python)` abort sites) is now backlog row 223.
- Rollback: revert the squash-merge commit; validators, tool, tests and workflow text revert as one unit, and the 2 moved archive files return to `archive/work/` (content unchanged). Operators see the rollback took effect when D4 output returns to the pre-change `PASS ... (N checked)` form.
- Root Cause: D4 resolves by basename across two directories that share a naming shape; the workflows never defined same-day collisions.

---

## Decisions

### D-1: Directory is the type — fix consumers, do not rename fragments  → consolidated: L2 document-governance
- **Decision**: Option 2 (owner, chat 2026-10-06): D4 resolves INDEX `log` against archive root only; the Phase-Summary scan reads archive root only (closes #186); compaction keeps `<worklog-key>-<YYYYMMDD>.md` and is "append; create if absent".
- **Reason**: root = final log / `archive/work/` = fragment is already the rule (`ship.md:203`, `handoff.md:149`, `check_decision_disposition.py:274`); only D4 and the recursive scan cross it.
- **Alternatives**: distinct `-compact-N` name (3 surfaces to sync, contract check blind, `-compact-` hits real `fix-160-compact-index-lf-20260808.md`); overflow outside archive/ (gitignored downstream); Python archival helper (Option 3, new deployed tool).
- **Impact**: any future archive consumer must stay directory-aware; same basenames across the two dirs are allowed.

### D-2: Legacy work/-only finals move to archive root  → consolidated: L2 document-governance
- **Decision**: `git mv` the 2 legacy files (content unchanged); D4 keeps no exemption; a root-miss found only under `archive/work/` WARNs with "move it to archive root".
- **Reason**: no hard-coded names or date constants in two deployed twins; downstream legacy gets an actionable, clearable WARN.
- **Alternatives**: `shipped` < 2026-05-22 cutoff (forgeable by back-dated backfill); `archive_v` chain marker (new field + check).
- **Impact**: archive file locations are not immutable, contents are.

### D-3: D4 stays native, edited in place, twins pinned equal  → consolidated: L2 document-governance
- **Decision**: edit both embedded Python copies in place; add a test asserting the two copies are identical; sh child error/empty → WARN; no-Python → SKIP via the same single computed-level emission; update baseline justification #5.
- **Reason**: ADR-006 §3 port is blocked — `run_python_check` maps exit!=0 → FAIL and cannot express WARN (same rationale as 4 sibling justifications).
- **Alternatives**: extract to one tool (deploy wiring + golden); full port + wrapper WARN exit code (ADR-006 amendment).
- **Impact**: records a deliberate ADR-006 §3 deviation for D4 in `validator_native_baseline.json`.

### D-5: Identical INDEX re-append is a no-op (amends D-4, AC-8)  → consolidated: L2 document-governance
- **Decision**: `append_chain_entry.py` returns the recorded entry, exit 0, for a byte-identical re-append; a different entry with the same `log` still exits 1.
- **Reason**: red-team retry finding — refusing a retried ship pushed agents to rename an already-indexed archive, leaving the first entry dangling.
- **Alternatives**: strict reject (spec as frozen) — rejected by owner in chat 2026-10-06.
- **Impact**: AC-8 + [CONSTRAINT] amended (1a9cd46).

### D-4: Same-day ship collision → `<worklog-key>--N-<YYYYMMDD>.md`, rejected at INDEX append  → consolidated: L2 document-governance
- **Decision**: `/ship §3` checks the target exists before moving (never `-Force`; `mv -n` is not a check); on collision use `--N-` (N=2,3…); INDEX `log` = actual name; `append_chain_entry.py` rejects a `log` value already in INDEX.
- **Reason**: normalized keys never contain `--` (`bootstrap.md:127`) and the date stays last for `FILENAME_DATE_RE` (`check_decision_disposition.py:82`); the append guard is T1 at write time with no legacy grandfathering.
- **Alternatives**: `<key>-<D>-N.md` (ambiguous, breaks date regex); stop-and-ask (blocks ship).
- **Impact**: no-Python ships stay honor-system (T3: ship PR diff shows the archive as `M` not `A`).

---

## Conflict Resolution

- karpathy-principles vs verification-before-completion: compatible (matrix) — no action.
- No other recommended pair is listed in skill_conflict_matrix.md.

---

## Skill Notes

### karpathy-principles (plan/implement/review)
- Checklist: every changed line traces to an AC; no adjacent "improvements"; remove orphans this change creates.
- Constraint: surgical — leave other validator checks untouched.
### test-driven-development (implement/test)
- Checklist: failing test first per behavior; minimal green; all tests pass after refactor.
- Constraint: no production edit without a red test on the baseline.
### verification-before-completion (implement/test/ship)
- Checklist: scope diff vs plan; run the tests; record commands + results; rollback stated.
- Constraint: no evidence = no completion; final run must postdate the last write.

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- SSoT write (bootstrap exception): Last Verified 2026-10-05 → 2026-10-06 via guard_context_write.py (receipt .guard_receipts/337ffd90d88a8b4f.json).
- Drift narrative (§12.1 reads, test-file plan deviation, set -e finding, #179 compaction) moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` §Drift Log.

---

## Review Feedback

- Round-1 review feedback (all resolved in 1528513): moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` §Review Feedback.

---

## Security Findings

- Review scan (A01-A03, secrets): clean; scan_credentials exit 0 on 11 changed files. No new dependency.

---

## Red Team Findings

- Full Red Team ran (fresh reviewer); no HIGH left open — detail moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md`.

---

## Design Reference

none

---

## Observability

- Sink: validator stdout result lines (`[WARN]/[SKIP]` + indented detail) and `append_chain_entry.py` stderr + exit 1 | Scope: validate.sh, validate.ps1, append_chain_entry.py | Verified: yes (tests + live runs)

---

## Resume

- State: HANDEDOFF (feature).
- Completed: bootstrap, brainstorm, spec (AC-8 amended, owner OK), plan, implement x2, review NOT READY -> PASS, test.
- Next: /ship (SSoT, INDEX append, archive this log, backlog #186/#222/#223, L2), push, draft PR; merge on verified green CI + owner OK.
- Context: the archive directory is the file type; only D4 and the Phase-Summary scan crossed it.

### Read Map
- docs/specs/archive-name-collisions.md -> AC, Domain Decisions
- this log -> Decisions, Known Risk

### Skip List
- validate.sh / validate.ps1 — fully read, reviewed 3x; only D4 + Phase-Summary blocks changed

### Context Snapshot
Names stay; consumers resolve by directory. Release note needed: pre-#106 adopter finals under archive/work/ get an actionable WARN (`git mv` to root). #179 forced 7 verbatim moves here.

---

## Test Gate Results

- Command: `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -m "not slow" -n 4` -> 831 passed, 1 failed (`test_subprocess_encoding`: my new CLI test lacked `encoding=`); fixed in 9dbd5ac, that lint + `test_audit_chain.py` 27 passed. Slow: `test_archive_name_collisions.py -m slow` 4 passed (sh, ps1 pwsh, ps1 powershell 5.1) + existing PS 5.1 git-probe test passed.
- Final (test phase, after the last test-phase write): validate.sh = validate.ps1 `pass=116 warn=5 fail=0 skip=2`. AC map + adversarial list moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md`.
- Test Files: `tests/ci/test_archive_name_collisions.py`, `tests/guard/test_audit_chain.py`.


---

## Evidence

- Diagnosis evidence (D4 mutation `ok:194` false PASS; INDEX probe) moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md`.
- Brainstorm roundtable evidence (completed phase): moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` §Evidence.
- Implement round 1 evidence (red on baseline, green suites, live validate 116/5/0/2 at aefe22f): moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` §Evidence (#179 reading, as above).
- Round 2 + Known Risk R7 moved verbatim to `.agentcortex/context/archive/work/fix-archive-name-collisions-20261006.md` (ship-entry compaction).
