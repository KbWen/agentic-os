# Work Log: fix/validator-downstream-truth-claims

## Header

- Branch: `fix/validator-downstream-truth-claims`
- Classification: `hotfix`
- Classified by: `claude-opus-5`
- Frozen: `true`
- Created Date: `2026-08-15`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `f5a161c008eb4d6e3d0fa471a5b8993dd1e5c9f2`
- Checkpoint SHA: `70015d2`
- Recommended Skills: `verification-before-completion, systematic-debugging, red-team-adversarial, karpathy-principles, kb-consult`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `154`
- Compacted: 2026-08-15, archive: `.agentcortex/context/archive/work/fix-validator-downstream-truth-claims-20260815.md`
  (full Decisions / Known-Risk rationale / Drift Log / Security detail / evidence narrative)

---

## Session Info

- Agent: `claude-opus-5` · Session: `2026-08-15 16:19 UTC` · Platform: `claude-code` · Files Read: `22`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §5, §12, §13` — full-file read.
- Override: `none` · Private scan: 4 `research-*.md` notes, none task-related; not resumed.
- Downstream-Capabilities: `private/downstream-capabilities.yaml` (0 skills, subagent_policy=
  read-only, knowledge_sources: kb-main→OK@328b30ecb33b)

---

## Task Description

Three untrue statements the deployed validators made to adopters: an unqualified integrity-pass
top line that ignores absent-tool SKIPs; a `tool not present` string that cannot distinguish a
source-only tool from a broken deploy; a permanent lifecycle WARN whose remediation command is
not deployed. Fixed at their emission sites, plus `check_audit_chain.py` deployed (the one
absence that is a real ADR-003 gap) and a regression guard in an existing CI step.

Origin: adopter report on v1.8.21 (`f5a161c`) + 4-lens panel. Backlog **#173**. Units B/C/D out
of scope — R5.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-15T16:19Z | `hotfix`; 5 skills; ADR coverage exit 0 |
| plan | done | 2026-08-15T16:32Z | 9 steps; dedup dropped on frozen-spec AC-S5 |
| implement | done | 2026-08-15T16:45Z | 5 files, `55e3314`; suite 884 passed / 1 skipped / 0 failed |
| review | PASS (round 2) | 2026-08-16T03:10Z | round 1 NOT READY → remediated → 3rd fresh reviewer: no CRITICAL/HIGH |
| test | done | 2026-08-16T03:55Z | 890 passed / 1 skipped / 0 failed; 2 Lite adversarial cases |
| handoff | n/a | — | hotfix is handoff-exempt |
| ship | done | 2026-08-16T04:10Z | SSoT seq 154→155; backlog #173 Shipped + #174–#178 opened |

---

## Phase Summary

- **bootstrap**: `hotfix` — `validate.*` is tiny-fix-excluded (§10.3); the `deploy.sh` edit is
  adjacent to §10.4 escalation. Judgment call resolved upward. | high
- **plan**: 9 steps, 5 files. Dedup **dropped** — Frozen Spec Pre-Check found AC-S5 requires
  both `deploy.sh` sites. | 88%
- **implement**: 5 files, `55e3314`, zero scope divergence; suite 884/1/0. | 95%
- **review r1: NOT READY.** Two fresh reviewers converged independently on the same blocking
  defect, **mine**: `| tee` at `validate.yml:214` discarded the validator's exit code (GHA runs
  `bash -e {0}`, no pipefail), so a FAILING downstream validate would have landed a green job —
  the very class this change removes, recreated by the plumbing added to support it, deviating
  from the correct pattern already at `:40`. B1–B6 + B9 fixed (`0a38cc9`), B7 → D-7, B8 carried.
- **review r2: PASS.** A third fresh reviewer **mutation-tested the tests I had just added** and
  found the guard single-platform. Closed in `be013a9`, red-first on both ps1 spellings.
- **test: PASS.** 890/1/0. Two Lite adversarial cases; A1 corrected my workflow comment a third
  time — I keep enumerating sets I have not behaviourally verified.
- **ship**: PASS. SSoT sequence 154→155, Ship History entry at top with the oldest rotated to
  `archive/ship-history-2026.md` (cap 10/10, spec index 26/30). Backlog #173 **Shipped** with its
  body corrected — it still asserted the pre-fix facts and still prescribed the rejected
  allowlist — and #174–#178 opened for the deferred findings. D-1..D-7 dispositioned in both the
  active log and the overflow. L2 amendment appended to `document-governance.log.md`: the live
  `[CONSTRAINT] Every validator-wired tool ships in deploy.sh runtime_tools` is now false as
  written, and the amended rule is ship-in-both-sites OR state-the-reason-at-the-call-site, with
  no third option.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-15T16:19:16Z
- Gate: plan | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-15T16:32:40Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-15T17:26:00Z
- Gate: review | Verdict: NOT READY | Classification: hotfix | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-08-16T01:55:00Z
- Gate: implement | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-16T02:40:00Z
- Gate: review | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-16T03:10:00Z
- Gate: test | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-16T03:55:00Z
- Gate: ship | Verdict: PASS | Classification: hotfix | Timestamp: 2026-08-16T04:10:00Z

---

## External References

| Type | Path | Notes |
|---|---|---|
| Backlog | `_product-backlog.md` #173 | primary row; its allowlist **rejected** — D-1 |
| Backlog | `_product-backlog.md` #161 | `check_worklog_references.py` source-only (PR #391) |
| Spec | `downstream-adaptability-optimization.md` | **frozen**; AC-S5 binds the `deploy.sh` edit |
| ADR | `ADR-002`/`003`/`005`/`006`/`008`/`010` | coverage exit 0; `006` binds the SKIP fix (R1) |

---

## Known Risk

Full rationale in the overflow file.

- **R1** ADR-006 ratchet, zero headroom (202/203, exact both ways) — materialised and caught.
- **R2/D-7** Chain deploy flips an adopter with an already-broken chain green→red, and `migrate`
  does **not** clear it. Release-banner item.
- **R3** `deploy.sh` copies, not syncs — a revert leaves the tool on upgraded disks (benign).
- **R4** `-m "not slow"` is not CI-equivalent — mitigated.
- **R5** Units B/C/D left unfixed; each becomes a backlog row at ship.
- **R6** `deploy.sh` frozen-spec-governed (AC-S5) — complied; dedup deferred.
- **R7** `kb-consult`: 34 routes, no match, 0 pages read.
- **Root Cause** (§10.4): the validators compute *whether a check ran* but never fold it into the
  *verdict they report*. Same class fixed once before for a different cause (#149).

---

## Decisions

Bodies in the overflow file. Dispositions at `/ship`.

- **D-1** Reject #173's `SOURCE_ONLY_TOOLS` allowlist; keep only its regression detection.  → consolidated: L2 document-governance
- **D-2** Deploy `check_audit_chain.py` rather than narrow ADR-003.  → consolidated: L2 document-governance
- **D-3** Fix the lifecycle WARN by branch reorder, not deletion or baseline deploy.  → local
- **D-4** Primary fix = the summary-line assurance label (not in the adopter's report).  → consolidated: L2 document-governance
- **D-5** Carry "why absent" at the call site, not a registry.  → consolidated: L2 document-governance
- **D-6** State the guard's coverage ceiling in the workflow itself.  → local
- **D-7** Keep the chain check at FAIL; its lack of a clean remediation is the property of tamper  → consolidated: L2 document-governance
  evidence, not a defect — but the banner must say `migrate` does not clear it (correcting R2).

---

## Conflict Resolution

none — matrix read once at bootstrap; the only listed pair in the recommended set is
`karpathy-principles` × `verification-before-completion`, marked **compatible**.

---

## Skill Notes

- **karpathy-principles** (cache miss → full read): surgical — no adjacent "improvements", match
  existing style, every changed line traces to the request, dead code mentioned not deleted.
  Applied: `run_python_check_source_only` is the one new abstraction, 2 callers — below the
  "extract at 3+" bar for duplicate logic, but it exists so the `ACX_ABSENT_REASON` reset is
  structural rather than remembered (correctness, not DRY). Flagged for `/review` to challenge.
- **verification-before-completion**: contract inlined in `shared-contracts.md`; look-timing
  honoured — final evidence run postdates the last Work Log write of the phase.
- **systematic-debugging** — LOADED on trigger, fired twice. (1) Unexpected `warn` delta vs the
  SSoT's recorded downstream figure → hypothesis "different tree/date, not a regression" → verified
  by building a pristine `f5a161c` A/B baseline. (2) `[FAIL] text integrity` after a sim restore →
  hypothesis "EOL not content" → `cmp` proved content-identical → harness defect, sim rebuilt.
- **kb-consult**: no-match (R7); no entry in `trigger-compact-index.json`, so metadata-first fell
  back to the bootstrap rule table as permitted.
- **HIGH Global Lessons bound to this step**: `[cross-platform-eol]` (no shell-append into CRLF
  tracked files; all edits via Edit tool — bit the harness anyway), `[process-batching]` (sequential
  mutations), `[audit-verification]`/`[audit-method]` (the 4-expert panel is same-vendor; every
  load-bearing claim re-derived against code before planning).

---

## Drift Log

Full text in the overflow file.

- SSoT `Last Verified` refresh (bootstrap-permitted); backlog #173 → `In Progress`, columns 11→11.
- **Conflicting directive surfaced, not patched**: `AGENTS.md` §Write Isolation scopes backlog
  writes to spec-intake/ship; `bootstrap.md` §1.5 mandates the advance at bootstrap. Followed the
  workflow; filed for the owner rather than editing governance inside a hotfix.
- **Self-corrections, all mine** (detail in overflow): a `cp950` probe error; a ratchet-breaking
  `if/else`; a sim whose `cp` restore tripped `text integrity` so the run proved nothing; a
  mutation that silently did not apply, so its green meant nothing; **three** workflow-comment
  precision errors. The `| tee` regression was found by review, not by me.
- **Compaction ×4** against 300 lines / 12KB — my §5.2b violation (evidence as narrative).
  **Deviation recorded openly**: `/handoff §6` protects `## Evidence` from rewriting, but verbatim
  Evidence makes 12KB unreachable; Constitution §5.2b outranks a workflow protection, so it was
  rewritten compliant with the narrative preserved verbatim in the tracked overflow.
- **Stale lock** twice during long runs; refreshed via `ensure` each time (exit 0).
- Skip Attempt: NO · Gate Fail Reason: N/A · Token Leak: NO

---

## Review Feedback

Round 1 **NOT READY**, 9 rows, all dispositioned: B1 CRITICAL (`| tee`) + B2 HIGH (`ship.md`
prose) fixed; B3/B4/B6 fixed; B5 deleted as duplicate; B9 fixed with red-first tests; B7 → D-7;
B8 carried. Round 2 **PASS**, no CRITICAL/HIGH. Two governance-truth items routed to `/ship`:
a live shipped-spec `[CONSTRAINT]` the source-only exception contradicts (fix = L2 append, never
an edit to a shipped spec), and backlog **#173**'s body, still asserting pre-fix facts and still
prescribing the allowlist D-1 rejects. Full findings in the overflow file.

---

## Security Findings

Implement quick-scan (§1 A01–A03 + §3) on all changed files; full A01–A10 at review. Detail in
the overflow file. A01 n/a · A02 none · A03 no finding (`ACX_ABSENT_REASON` / `-AbsentReason`
values are literals at the call site inside the validator; no user-input path) · A03 (CI, LOW)
the honesty step echoes matched validator lines into the Actions log, repo-controlled today ·
§3 `scan_credentials.py` → **exit 0**. **No CRITICAL/HIGH.**

---

## Red Team Findings

none — `red-team-adversarial` is a review/test-phase skill; runs next.

---

## Design Reference

none — not a UI task (§4.4 exempts `.agentcortex/`, `tests/`).

---

## Observability

none — hotfix.

---

## Resume

none — hotfix is handoff-exempt.

---

## Test Gate Results

`pytest tests/ci/ tests/guard/ .agentcortex/tests/` (no `-m`; R4) → **890 passed, 1 skipped,
0 failed** in 40m50s, exit 0. Baseline at `f5a161c` was 884+1; the delta is the 6 tests added
here. Skip = `test_deploy_tiering.py:474`, environment-conditional, unrelated.

Lite adversarial (hotfix tier), on a real deploy — **A1** the disclosed blind spot behaves
exactly as disclosed (deleting `generate_safety_nucleus.py` prints "safe to ignore" over a real
break, unqualified pass) **and corrected my workflow comment a third time**; **A2** the counter
reports the right *number* (2 tools removed → "2 referenced tool(s) absent"), not merely
non-zero. Detail in the overflow file.

---

## Evidence

Terse per §5.2b; long-form verbatim in the overflow file.

**implement** — A/B vs a pristine `f5a161c` deploy under identical conditions:
`pass=85 warn=3 fail=0 skip=6` → `pass=85 warn=2 fail=0 skip=7`, line-level diff of downstream
result lines **exactly 3**. Summary line both ways: healthy → unqualified pass; one tool removed
→ `reduced assurance: 1 referenced tool(s) absent`. ADR-003: baseline `tool not present` → after
`audit chain intact`. Ratchet 202/203 unchanged; golden diff exactly `+check_audit_chain.py`.
Full CI-equivalent suite (no `-m`, 885 collected): **884 passed, 1 skipped, 0 failed**.

**review remediation** — B1 proof: `bash -e -c 'bash -c "exit 7" | tee /dev/null'` → **0**;
with `set -o pipefail` → **7**. New `tests/ci/test_validator_absent_tool_signal.py` **5 passed**,
red-first (injecting a false source-only claim into `deploy.sh` turns it red). Affected suites
after remediation → **262 passed**; ratchet still 202/203; `validate.yml` parses, both steps
`shell: bash`. Downstream re-verified: `pass=85 warn=2 fail=0 skip=7`, exit 0, anchored CI grep
finds **0** bare `tool not present`. Text integrity after appending to the tracked overflow:
**pass**, 375/375 lines CRLF (checked — `cat >>` into a tracked CRLF file is the known hazard).
**Rollback**: `git revert` the branch commits; no persisted state, golden regenerates.
