| Field | Value |
|---|---|
| Branch | feat/audit-chain-tamper-evidence |
| Classification | feature |
| Classified by | Claude Opus 4.8 (1M) |
| Frozen | true |
| Created Date | 2026-05-29 |
| Owner | luvseldom (session 2026-05-29) |
| Guardrails Mode | Full |
| Current Phase | ship |
| Checkpoint SHA | 9c03588 |
| Recommended Skills | verification-before-completion (completion claims), karpathy-principles (coding baseline), test-driven-development (testable integrity logic), red-team-adversarial (review/test — adversarial tamper attempts), systematic-debugging (if bugs), production-readiness (review/ship — error paths in validator) |
| Primary Domain Snapshot | document-governance |
| SSoT Sequence | 22 |

## Session Info
- Agent: Claude Opus 4.8 (1M context)
- Session: 2026-05-29
- Platform: Antigravity
- Guardrails loaded: §1,§2,§4,§7,§8,§10 (core, Full)
- Context Read Receipt: current_state.md (Seq 22) · Work Log (created) · ADR-003 (covering ADR, status: proposed) · Spec Scope (none shipped-relevant)

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Branch base: stacked on fix/guard-test-ci-coverage (PR #116, A+B) so new tests/guard audit-chain tests are CI-gated; rebase to main once #116 merges.

## Task Description
- **C1+C2 from 2026-05-29 self-audit**: harden the ADR-003 hash-chained audit log (`INDEX.jsonl`) tamper-evidence.
  - **C1 (HIGH, reproduced)**: `check_audit_chain.check_chain` only walks present entries via back-links — NO head/length anchor. Deleting the last (most recent) entry leaves a chain that still validates as intact. Reproduced 2026-05-29: a 3-entry chain truncated to 2 → `check_chain` returns True; the erased "SECRET-record" is undetectable. This contradicts ADR-003's stated guarantee (line 79: "any retroactive edit... breaks the chain... CI catches it").
  - **C2 (MED)**: `append_chain_entry.migrate` recomputes `prev_sha` for ANY entry where it mismatches (lines 112-116) — including entries that HAVE a prev_sha (i.e., tampered entries), silently re-blessing forged history. ADR-003/docstring intent is narrower: "add prev_sha to entries that LACK it."
- **Vehicle**: amend ADR-003 (status: proposed) — document the tail-truncation limitation honestly + record the chosen detection mechanism + the migrate-safety fix. Then spec/plan/implement/test.
- **DESIGN FORK (C1)** — how to detect tail-truncation without adding deps (ADR-003 rejected Merkle + git-coupling):
  - Option A: monotonic `seq` per entry + git-committed anchor file `{count, head_sha}`; validator checks actual==anchor.
  - Option B: git as external append-only witness — validate.sh asserts committed INDEX (origin/main) lines are a prefix of local (strong; CI has origin; but breaks under future rotation #3 and needs network).
  - Option C: accept-and-document residual + add `seq` for reorder/middle-gap robustness only.
  - → Resolve via /decide before /spec freezes the contract.
- Phase chain: /decide (design fork) → /spec (ADR-003 amendment) → /plan → /implement → /review → /test → /handoff → /ship

## Phase Sequence
- bootstrap

## External References
- docs/adr/ADR-003-hash-chained-audit-log.md (covering ADR, status: proposed) — the contract being amended.
- Crosby & Wallach USENIX 2009 (tamper-evident logging); transparency.dev (CT signed tree heads = external length commitment, the primitive C1 lacks).

## Known Risk
- Changing canonical hash input (e.g., adding `seq` to the hashed body) would invalidate the EXISTING INDEX.jsonl chain → needs a migration path. Mitigation: keep `seq` outside the hashed canonical form OR ship a re-migration. Decide in /plan.
- Over-engineering C1 into theatre (per Global Lesson [enforcement][HIGH]): any in-repo anchor is itself forgeable. The ADR amendment MUST state the honest threat boundary (raises cost + git-diff visibility), not claim prevention.
- Rollback: revert the feature commit(s); chain + validator return to current behavior; ADR-003 amendment section removed.

## Decisions

### D-1: C1 tail-truncation detection = git append-only witness (Option B)
- **Decision**: Detect tail-truncation/edit via a validate.sh/.ps1 check that asserts the `origin/main`-committed `INDEX.jsonl` content is a line-prefix of the local file (append-only-vs-published-baseline). Degrade to WARN when git/origin/INDEX-on-origin is unavailable; never silent-pass.
- **Reason**: Only Option B uses a genuinely EXTERNAL witness (origin/main published to GitHub = our nearest dependency-free analog to Certificate Transparency's signed tree head — the length commitment a back-linked chain structurally lacks). Option A's anchor file is forgeable in the same commit → false-confidence theatre, which the [enforcement][HIGH] Global Lesson forbids. Option C leaves a closeable gap open.
- **Alternatives**: A (seq+anchor file) — rejected: anchor forgeable in same commit, marginal over plain chain. C (document-only + seq) — rejected: a real dependency-free detector exists; seq unprotected-by-hash is theatre, and hashing seq forces a disruptive re-migration of every existing entry for little gain.
- **Impact**: No change to chain canonical form (existing INDEX chain stays valid; zero entry migration). Adds a git-read to validate (graceful offline degradation). Future INDEX rotation (#3) MUST re-anchor the witness baseline as a deliberate reviewed op — documented as a constraint in the ADR-003 amendment. The amendment states the honest bound: this raises truncation from a 1-line silent delete to a deletion visible in PR review against the published baseline — tamper-EVIDENCE, not prevention.

### D-2: C2 migrate hardening = fill-missing-only, fail-on-tamper
- **Decision**: `append_chain_entry.migrate` only ADDS `prev_sha` to entries that LACK it; if an entry HAS a `prev_sha` that mismatches the recomputed value, migrate FAILs (exit 2, "tampering — refusing to re-bless") instead of silently overwriting.
- **Reason**: Current impl re-blesses any mismatch (re-computes forward over forged content), defeating the chain's purpose. ADR-003 §Migration + the tool docstring scope migrate to entries that "lack" prev_sha (pre-ADR data), NOT to repair tampered entries.
- **Alternatives**: Require a `--force-rebless` flag for the overwrite path — rejected: an adversarial agent would just pass the flag; fail-closed is stronger and matches documented intent.
- **Impact**: migrate becomes idempotent + tamper-refusing. Legitimate re-migration of pre-ADR entries still works (they lack prev_sha). Removes the "run migrate to launder" attack.

## Conflict Resolution
none

## Skill Notes
none

## Phase Summary
- bootstrap: classified feature; covering ADR-003 found (status proposed); design fork on C1 detection mechanism flagged for /decide; skills matched (6).
- decide: D-1 (C1 = git append-only witness, rejecting forgeable anchor as theatre) + D-2 (C2 = migrate fail-on-tamper); /brainstorm skipped (fork already characterized).
- spec: docs/specs/audit-chain-tamper-evidence.md frozen (9 ACs, 6 Domain Decisions); registered in Spec Index via guard CAS (new_sha 7dbec98f); EXTENDS ADR-003.
- plan: 5 target files; TDD for C2; git-witness (best-effort fetch) for C1; Mode Normal | Confidence: 88% — assumption: CI network allows fetch, else witness WARN-degrades safely.
- implement: C2 migrate hardened (TDD red→green, AC-1/2/3); C1 git-witness in validate.sh (tr -d '\r' CR-fix after discovering CRLF false-FAIL) + validate.ps1 (parity); ADR-003 amended (proposed→accepted); commit d4240f8; 125 tests pass; witness sim verified PASS/truncate-FAIL/edit-FAIL on both validators. Confidence: 90% — high (CRLF bug found & fixed during impl).
- review: fresh acx-reviewer (Reviewer Freshness Invariant honored — diff+spec only, no impl rationale); 9/9 ACs PROVEN; 1 MEDIUM (bash/PS blank-line parity) FIXED in commit 9c03588 → AC-6 PARTIAL→PROVEN; 2 LOW (fetch side-effect noted, prior-commit scope transparency) accepted; security clean (no auto-caller of migrate; SHA-only shell vars; raise caught by cmd_migrate→exit 2). Verdict: Ready.
- test: 126 passed (tests/ci/ + tests/guard/), 0 failed; AC→test map complete (9/9 covered); adversarial done via fresh reviewer + dual-platform witness sims; chain intact (AC-7). Test Files: tests/guard/test_audit_chain.py, tests/ci/test_audit_witness.py.
- handoff: TESTED→HANDEDOFF; all 6 ACs+3 = 9/9 PROVEN, 126 tests, review PASS; doc+code+log refs complete; closure = Open PR (stacked on #116). Next: /ship.
- ship: HANDEDOFF→SHIPPED; SSoT updated (guard CAS new_sha 73351eb — ADR-003 accepted+amended, Spec Index→Shipped, Update Seq 23); spec status shipped; backlog #42 Shipped; L2 consolidated to docs/architecture/document-governance.log.md; observability sink = validator record_result (WARN/FAIL) + migrate stderr/exit-2 (no app logging infra — governance tooling). Closure: Open PR (stacked on #116).

## Resume
- State: HANDEDOFF
- Completed: bootstrap→decide(D-1,D-2)→spec(frozen)→plan→implement(d4240f8)→review(PASS)+fix(9c03588)→test(126 pass)→handoff
- Next: /ship — update SSoT (ADR Index: ADR-003 proposed→accepted+amended; Ship History), backlog #42→Shipped, archive work log + INDEX.jsonl chain append, spec→shipped, knowledge consolidation to docs/architecture/document-governance.log.md (primary_domain set).
- Context: Closed audit C1 (tail-truncation undetectable) via git append-only witness in validate.sh/.ps1, and C2 (migrate re-blessing forged history) via fail-closed migrate. ADR-003 amended with honest tamper-evidence boundary (evidence not prevention). Branch stacked on PR #116 (A+B); rebase to main after #116 merges.

### Read Map (for next agent / ship)
- .agentcortex/context/work/feat-audit-chain-tamper-evidence.md → full (this log)
- docs/specs/audit-chain-tamper-evidence.md → §Domain Decisions (for knowledge consolidation)
- docs/adr/ADR-003-hash-chained-audit-log.md → §Amendment 2026-05-29

### Skip List
- .agentcortex/tools/append_chain_entry.py — reviewed, C2 done, 17 tests pass
- .agentcortex/bin/validate.sh / validate.ps1 — witness done, parity verified
- tests/* — green, no changes expected

### Context Snapshot (≤200 tokens)
C1+C2 complete & tested. Witness = git merge-base origin/main prefix check (CR+blank normalized, WARN-degrade); migrate = fill-missing-only + fail-closed exit 2. ADR-003 accepted+amended; honest threat boundary stated (no false-confidence anchor). 126 tests pass; fresh-reviewer PASS. Ship must: ADR Index status update, Ship History, backlog #42 Shipped, archive+INDEX chain append, spec→shipped, L2 consolidation (domain document-governance). C3/D remain as backlog #43/#44.

### Backlog Status
- Active Backlog: docs/specs/_product-backlog.md
- Current Feature: #42 Audit-Chain Tamper-Evidence — In Progress → (Shipped at /ship)
- Remaining: #43 (lock unification) + #44 (validator parity) pending from this audit; plus prior pending items
- Next Recommended: user choice (C3 #43 or D #44, or other)

## AC → Test Coverage Map
- AC-1 (migrate fill-missing/idempotent) → test_migrate_fills_only_missing_then_idempotent [PASS]
- AC-2 (fail-on-tamper, exit 2, no write) → test_migrate_refuses_to_rebless_tampered_entry + CLI exit=2 [PASS]
- AC-3 (mixed, no partial write) → test_migrate_mixed_missing_and_tampered_no_partial_write [PASS]
- AC-4 (witness prefix/FAIL verdicts) → test_witness_present_* + test_*_fail_verdicts + sim(truncate/edit→FAIL) [PASS]
- AC-5 (WARN-degrade) → test_*_warn_degradation_paths + sim(no-origin→WARN) [PASS]
- AC-6 (cross-platform parity) → test_witness_verdict_parity + test_witness_blank_line_parity + dual-platform sim [PASS]
- AC-7 (zero migration, chain intact) → check_audit_chain.py intact + diff shows +1 legit append [PASS]
- AC-8 (ADR-003 amended, status accepted) → grep Amendment/boundary subsection present [PASS]
- AC-9 (covered + CI-gated) → 126 passed; tests/guard CI-gated via PR #116 [PASS]

## Red Team Findings
- MEDIUM (witness parity, RESOLVED): bash counted all lines, PS filtered blanks → latent divergence on a stray blank line. Fixed: both CR-normalize + drop blanks; behavioral parity test added (commit 9c03588).
- LOW (accepted): `git fetch --depth=1 origin main` is a network side-effect inside the validator (runs only when origin/main unresolved; `|| true`; no ref pollution found). CI must permit it; offline → WARN-degrade.
- Residual (documented in ADR-003 amendment, NOT a defect): if origin/main itself is truncated upstream via a reviewed merge, the witness diffs against a forged baseline — tamper-EVIDENCE not prevention. Honestly stated; not overclaimed.

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-05-29

## Evidence
- C2 unit (pytest tests/guard/test_audit_chain.py): TDD red (2 fail: migrate re-blesses) → green after fix; 17 passed. CLI: tampered file → `migrate` exits 2, file byte-unchanged.
- AC-7: `check_audit_chain.py --path INDEX.jsonl` → intact, before and after (zero entry migration; canonical form unchanged).
- C1 witness sim (validate.sh, CR-safe): real repo → PASS (local=11, base=10); truncate to 9 (<baseline 10) → FAIL "tail-truncation?"; edit baseline entry (preserve count) → FAIL "not a prefix"; restored → PASS.
- C1 witness sim (validate.ps1, user's Windows platform): real → PASS; truncate to 9 → FAIL "tail-truncation?". Cross-platform parity (AC-6) confirmed.
- CRLF regression: discovered working-copy CRLF vs `git show` LF false-FAILed every line; fixed via `tr -d '\r'` (bash) / native string-array read (PS1); covered by test_audit_witness.test_bash_witness_normalizes_cr.
- Full suite: `pytest tests/ci/ tests/guard/` → 125 passed. validate.ps1 → witness PASS, audit chain PASS, lesson chain PASS; sole FAIL = pre-existing stale work log (feat-optimization-round, gate progression) — flagged via spawn_task, gitignored, not in CI, not introduced here.
