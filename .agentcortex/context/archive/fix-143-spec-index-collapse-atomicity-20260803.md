# Work Log: fix/143-spec-index-collapse-atomicity

## Header

- Branch: `fix/143-spec-index-collapse-atomicity`
- Classification: `quick-win`
- Classified by: `claude-opus-5[1m]`
- Frozen: `2026-08-03`
- Created Date: `2026-08-03`
- Owner: `7d0ae52d-claude-opus-5`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `72ab8ef`
- Checkpoint SHA: `0d05cc7`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `140`

---

## Session Info

- Agent: `claude-opus-5[1m]`
- Session: `2026-08-03 (scheduled triage run, continued interactively)`
- Platform: `claude-code`
- Files Read: `28`

---

## Task Description

Make the Spec Index collapse remedy at `ship.md` §State Update executable (#143 Increment A). Following it literally FAILed the validator in both directions. Out of scope: the age-driven trigger #143 actually asks for (waits on #140).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-03 | quick-win; branch + log created |
| plan | done | 2026-08-03 | 3 expert audits consumed and re-verified |
| implement | done | 2026-08-03 | 7 files |
| review | done | 2026-08-03 | NOT READY → fixed → PASS |
| test | done | 2026-08-03 | full CI-equivalent suite + dual-platform |
| implement | done | 2026-08-03 | round 2: roundtable + 第十人 blockers R1/R4 |
| ship | in-progress | 2026-08-03 | PR #381 |

---

## Phase Summary

**bootstrap** — `quick-win` per §10.4: contained, but touches `.agentcortex/bin/validate.*` (a §10.3 tiny-fix exclusion), no public surface, no new config key, no new directory.

**plan** — Three read-only expert audits; every decision-relevant claim re-verified before use. Two audit claims were wrong: the `validate.ps1 -Depth 1` "asymmetry" does not exist (`-Recurse -Depth 1` ≡ `find -maxdepth 2`, 155 files each), and the duplicate-archive-header divergence reproduces only when the headers are adjacent. Design switched from the issue's `archive/specs/` relocation to teaching both validators about the archive section (D-1).

**implement** — Both validators read live index ∪ `## Spec Index Archive`; ship.md and the draft spec state the executable remedy; stale `ship.md:197` pointer → heading anchor (D-2); regression tests added.

**review** — Independent fresh-context review: NOT READY, 7 findings. One was a real defect newly introduced here (sh/ps1 divergence on a repeated archive header: bash unioned all sections, ps1 took the first → Linux green, Windows FAIL). Fixed with `!found &&`.

**round 2 (roundtable + 第十人)** — Four more lenses. The 第十人 found a **gate-laundering path I had wrongly claimed did not exist**: folding *every* entry into the archive leaves the live index empty, still PASSes completeness, and permanently silences the cap (`count_spec_index` reads the live block only → reports 0/30). My PR turned a main-FAIL into a PASS. Fixed by machine-checking ship.md's "keep the newest N inline" as an over-fold WARN in `check_ssot_caps.py` (D-3). Second blocker (R4) confirmed but its severity was overstated — see Review Feedback.

**test** — Full CI-equivalent suite, dual-platform live verification, plus new guards for both round-2 blockers.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T01:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T02:00:00Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Timestamp: 2026-08-03T03:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T03:30:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T04:00:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T04:30:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T05:30:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T06:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/tiered-doc-lifecycle.md | draft, owned by #140; carried the same half-instruction |
| ADR | docs/adr/ADR-010-frozen-spec-lifecycle.md | governs the completeness check |
| Issue | https://github.com/KbWen/agentic-os/issues/143 | Increment A only |
| PR | https://github.com/KbWen/agentic-os/pull/381 | CI 18 SUCCESS / 1 SKIPPED on first push |

---

## Known Risk

- Neither new completeness test runs in a **required** check (`.agentcortex/tests/` is in CI Structural + Pytest(Windows), neither branch-protection-required). A one-sided revert could merge green. Pre-existing repo property.
- Fenced-decoy footgun: a ```-fenced `## Spec Index Archive` at column 0 earlier in `current_state.md` binds both parsers to the decoy (both platforms agree, so not a parity bug; failure is a loud FAIL). Routed to backlog; my own ship record must not write that string at column 0.
- Root Cause: the remedy was authored in `972a7af` (2026-04-12) as a partial pre-implementation of an unshipped draft spec, and no validator ever learned about the section it created.

---

## Decisions

### D-1: Teach the validators about the archive section, not relocate spec bodies

- **Decision**: both validators read live index ∪ `## Spec Index Archive`; spec bodies stay in `docs/specs/`; `archive/specs/` is not created.
- **Reason**: `archive/` is walked by 4 scanners per platform, 3 classifying every `*.md` as a Work Log; `tests/ci/test_validator_false_positives.py:204` asserts that WARN's absence from the whole validate output and is `slow`-marked (invisible to `-m "not slow"`). Relocation buys no tokens — a spec body is not part of the SSoT read.
- **Alternatives**: issue-as-written (rejected: more code, more surface, same benefit); doc-only fix (rejected: leaves the FAIL).
- **Impact**: stays `quick-win` (no new directory). Public issue comment corrected.
- → local

### D-2: Heading anchor instead of the `ship.md:197` line pointer

- **Decision**: `check_ssot_caps.py` points at `ship.md §State Update & Archival`; the test pins both the anchor and the heading's existence.
- **Reason**: the pointer was already stale (bullet at ~184; 197 is Decision Disposition) and the test pinned the stale value.
- → local

### D-3: Machine-check "keep the newest N inline" instead of trusting the prose

- **Decision**: `check_ssot_caps.py` WARNs when the archive section is non-empty while the live index is below cap.
- **Reason**: 第十人 R1 — without it, folding everything PASSes completeness and silences the cap forever. Fixing an un-executable instruction by adding *more unenforced prose* would repeat the exact failure this PR exists to fix.
- **Alternatives**: prose-only "keep the newest 30 inline" (rejected: unenforced); FAIL-tier (rejected: the tool's ADR-006 contract is WARN-only, always exit 0).
- **Impact**: +1 advisory finding in an existing tool; no new file, no new `record_result`.
- → consolidated: L2 document-governance

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Round-2 expert panel reopened `implement` after `test` had passed. Not a reclassification: same quick-win scope, driven by a blocking review finding (R1). Phase receipts record the reverse edge.
- Ship-phase SSoT writes (Ship History entry + 10-entry rotation into `archive/ship-history-2026.md`, Update Sequence 140→141, Last Updated/Verified, Active Backlog count) made by direct edit rather than `guard_context_write.py`: single-session, no concurrent owner, and an append would mis-order the newest-first Ship History. Logged per AGENTS.md non-ship-exception discipline.
- `_product-backlog.md` rows #152–#157 appended during ship (permitted backlog exception).
- First rotation attempt partially wrote `archive/ship-history-2026.md` before failing on a missing input path, duplicating the rotated entry. Reverted with `git checkout --` and redone as a read-all-then-write-all pass. No data lost; noted because a partial multi-file write is exactly the failure mode the atomic-pair fix in this task is about.

---

## Review Feedback

**Round 1** (independent fresh-context): NOT READY, 7 findings. Adopted: F1 duplicate-header sh/ps1 divergence (real, newly introduced, narrowed to the adjacent case); F3 `###` parity overstatement; F4 token trim; F5 exclude the unrelated `.claude/settings.local.json`; test-quality nits. Corrected: F2 — "not auto-read during bootstrap" is false for `bootstrap.md §1`'s full read but true for `context-budget.md:30` scoped readers, so the claim was moved, not simply deleted. Partial: F6 (`≥` vs `>` left as pre-existing). Acknowledged only: F7 required-CI coverage.

**Round 2** (4 lenses: product philosophy / AI behavior / governance weight / 第十人):

| Finding | Adjudication |
|---|---|
| **R1 gate laundering** (第十人) | **ADOPTED — blocker.** Verified: emptying the live index into the archive → completeness PASS + `spec index 0/30` forever. Refutes my own PR claim that the gate kept its teeth (I had only tested the phantom direction). Fixed via D-3. |
| **R4 `^##` truncation untested** | **ADOPTED, severity corrected.** Verified the truncation is real, but ps1 on `main` already stopped at `\n##`; such a downstream was already FAILing on Windows. So this converges a pre-existing sh/ps1 divergence rather than creating a break. Regression test added. |
| **R7 draft-spec scope creep** | **PARTIALLY ADOPTED.** Kept the factual correction (leaving a known-wrong AC for #140 to inherit is worse), removed the design opinion about out-of-file archives — that is #140's call. |
| **R8 token not funded** | **ADOPTED.** Rewrote to point at the tool instead of restating the config key and hand-count: `ship.md` now 6 chars **smaller** than main; aggregate 354,475 → **354,277**, below main's 354,289. |
| **R5 `pass=117` not reproducible** | **ADOPTED.** That count depends on a gitignored Work Log; PR evidence re-quoted against main-vs-branch. |
| **R6 fenced decoy** | **ACKNOWLEDGED**, routed to backlog (loud FAIL, both platforms agree). |
| **R2/R3 in-file vs out-of-file** | **NOT ADOPTED here.** The three lenses split; the deciding fact is that the cap binds in ~1 month (31 specs / 4 months, 26/30 now), so this is not dormant ceremony. Out-of-file is #140's design call. |
| Delete-the-mechanism (all lenses considered) | **REJECTED.** Deleting a bound one month before it first binds; and it would not fix the validator, so any repo that already folded stays FAILing. |

---

## Red Team Findings

R1 (gate laundering) was found by the refute-only pass, not by the standard review — the standard review confirmed my framing instead. Recorded as evidence that the adversarial pass earns its cost.

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

- Command: `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q` (the `validate.yml` CI Structural command; **not** `-m "not slow"`, which deselects `test_deploy_tiering.py` wholesale)
- Round 1: **838 passed, 2 failed** (38:13). Both failures = one pre-existing Windows CRLF checkout artifact: `git ls-files --eol` → `i/lf w/crlf` for the two SKILL.md files, committed blobs start `---\n`, zero skill files in the diff, `Validate Framework Integrity` green on main. CI's own Pytest (Windows) job passed, confirming local-only.
- Round 2 targeted: `test_ssot_caps_check.py` → 11 passed; `test_ssot_completeness.py -k "prose or archive_section"` → 3 passed.
- PR #381 CI on first push: **18 SUCCESS / 1 SKIPPED / 0 failures**.

---

## Evidence

- Defect reproduction on main: fold-only → `[FAIL] 1 shipped/living spec(s) not in index`; move-body-only → `[FAIL] 1 indexed spec(s) not on disk`.
- After fix, same fold-only scenario: `[PASS] SSoT Spec Index completeness` on **both** `validate.sh` and `validate.ps1`, identical `pass=117 warn=3 fail=0 skip=2`. (117 counts this branch's gitignored Work Log; clean-checkout equivalent is 99 — CI is authoritative.)
- Gate still bites: deleting a folded spec → `[FAIL] ... phantom index entry: docs/specs/lock-unification.md`.
- R1 laundering, before D-3: 26/26 entries folded → `[PASS]` + `ssot caps OK — spec index 0/30`. After D-3: `WARN: Spec Index over-folded — live index has 0 entries (below cap 30) while 26 sit in ...; Restore the 26 newest archived entries inline.`
- R4: fixture with a spec path in prose under a `##` heading → main's awk extracted `{a.md, b.md}`, branch extracts `{a.md}`; ps1 extracted `{a.md}` on main already.
- Token ceiling: main 354,289 → branch **354,277** (headroom 711 → 723). `ship.md` 24,464 → 24,458 chars.
- ADR-006 native counts unchanged (202/203, exact-equality ratchet).
- Cap urgency: `docs/specs/` accrual 2026-04..07 = 4/3/17/7 (31 in 4 months); live index 26/30.
