# Work Log: fix/163-164-audit-leftovers

## Header

- Branch: `fix/163-164-audit-leftovers`
- Classification: `quick-win`
- Classified by: `claude-fable-5`
- Frozen: `2026-08-08`
- Created Date: `2026-08-08`
- Owner: `62a71637-primary`
- Guardrails Mode: `Quick`
- Current Phase: `implement`
- Diff Base SHA: `152d077`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `145`

---

## Session Info

- Agent: `claude-fable-5`
- Session: `2026-08-08 13:10 UTC`
- Platform: `claude-code`
- Files Read: `~14`

---

## Task Description

Close the two open leftovers from the 2026-08-08 govern-audit wave. **#164**: `Path.write_text(newline=)` is Python ≥3.10 against the repo's 3.9 CI floor — fixed the shipped tool site (`update_lifecycle_baseline.py:78`, the `#160` open() pattern) plus every accumulated test site, and added a cap-at-zero AST ratchet (`tests/ci/test_write_text_newline_ratchet.py`, modeled on `test_subprocess_encoding.py`). **#163**: decided B+ — the lifecycle instrument's exclusion of `shared-contracts.md` stays (folding an every-phase doc into a per-phase-scenario aggregate would redefine the instrument's semantics for no new information), but the free-hosting loophole is closed mechanically by a size ratchet (`tests/ci/test_shared_contracts_size_ratchet.py`, cap 7306 = 6906 measured + 400 slack) and documented honestly in `token-governance.md §5.1`.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-08T13:05Z | quick-win; both rows carry tenth-man-verified analysis |
| plan | done (inline) | 2026-08-08T13:06Z | targets: update_lifecycle_baseline.py, offending test files, 2 new ratchet tests, token-governance.md §5.1 |
| implement | done | 2026-08-08T13:45Z | see Phase Summary; scope grew 7→19 sites, all same class |
| review | skipped | — | quick-win: optional |
| test | skipped | — | quick-win: optional; ratchets + touched suites as evidence |
| handoff | exempt | — | quick-win exempt |
| ship | pending | — | record PR follows merge |

---

## Phase Summary

- implement (#164): the AST ratchet's first red run listed violations grep had missed — twice (paren-bearing arguments defeat naive patterns; and the primary's own `-First 8` output truncation hid four more). Final count: **19 sites across 8 files** (1 shipped tool via the with-open #160 pattern; 18 test-fixture sites via semantically-identical `write_bytes(...encode("utf-8"))` one-liners — `newline="\n"`/`newline=""` text writes and exact-bytes writes are byte-equivalent for the fixture strings involved, including the deliberate CRLF `.bat` shim body). Ratchet now green at cap zero with an anti-vacuity scan-reach guard.
- implement (#163, decision **D-1**): Option A (add shared-contracts to `PHASE_WORKFLOW_MAP` with a true multiplier) REJECTED — it redefines the aggregate's per-scenario semantics, forces a large one-time ceiling rewrite, and adds no information the size ratchet doesn't capture; Option B-pure (prose only) REJECTED as `[enforcement]` theatre. Adopted **B+**: deliberate-exclusion paragraph in `token-governance.md §5.1` + cap-at-today size ratchet with the lifecycle-ceiling bump discipline in its failure message.
⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-08T13:05:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-08T13:06:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-08T13:45:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/reviews/2026-08-08-govern-audit-task-simulation.md | source audit (F-adjudication) |
| Spec | docs/specs/_product-backlog.md | rows #163/#164 |
| PR | — | created after final verification |

---

## Known Risk

- write_bytes swaps are byte-identical only if the original strings' newline handling matched (`newline="\n"`/`""` = no translation) — verified per site; the one deliberate-CRLF site (`.bat` shim, `\r\n` in the literal) preserves its bytes exactly. Rollback = revert the PR.

---

## Decisions

### D-1: #163 resolved as B+ (documented exclusion + size ratchet), not instrument redefinition
- Decision: keep `shared-contracts.md` out of `PHASE_WORKFLOW_MAP`; close the loophole with `test_shared_contracts_size_ratchet.py` + `token-governance.md §5.1`.
- Reason: folding an every-phase doc into a per-phase-scenario aggregate changes what the 355k ratchet measures and forces a semantic ceiling rewrite; the size ratchet delivers the same protection (growth is visible and deliberate) at ~40 lines.
- Alternatives: A (true-multiplier fold — rejected above); B-pure (prose only — `[enforcement]` theatre).
- Impact: shared-contracts edits now trip a test unless the cap is bumped in-commit; the aggregate's meaning is unchanged.
- → local (durable rationale + enforcement live in `token-governance.md §5.1` and `test_shared_contracts_size_ratchet.py`; no ADR/L2 promotion needed — the decision is fully machine-backed where it lands)

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Scope grew 7→19 sites mid-implement — same defect class, same mechanical fix, no module-boundary crossing → stayed quick-win (matches the #146 precedent where AST scope-setting found 32 sites from a 6-site report).
- Local-environment artifact (NOT this diff): `test_validator_worklog_family_skip.py::test_fresh_install...` fails locally because PATH `bash` resolves to the WindowsApps WSL stub in this shell (UTF-16 garbage in stderr, failure precedes the touched fixture line); the same test was CI-green an hour earlier on PRs #389/#390. CI owns it.
- **Tenth-man R3 BLOCK adjudicated (adopted in full)**: the first push carried a PR-introduced regression — the closer `replace_all` had converted MORE 8-space closers than the two predicted (`:1215`/`:1337`), leaving `:1176`/`:1298` openers as `write_text(` with `.encode()` closers → `TypeError`, 14 tests red, CI Structural red (non-required → branch protection would NOT have stopped the merge — the #270 class). Root-cause chain, all previously-documented failure modes: violation list truncated twice (`-First 8`), `replace_all` match count assumed not verified, only subsets run locally. Fixes: both openers → `write_bytes`; ratchet extended with the `write_text(<bytes-like>)` accident-shape check R3 recommended (the check that would have caught this); exclusion set switched to all-dot-directories (R3's `.venv` false-FAIL finding); `token-governance.md §5.1` "for no new information" softened to the honest framing. R3 also CONFIRMED: the other 17 swaps byte-identical (AST payload comparison + empirical three-form proof), size-ratchet CRLF-flap refuted (universal newlines), D-1 defensible on facts (true-multiplier = 10,362 tokens vs 771 headroom, 13.4× overshoot).

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

> Terminal write (§5-Gate look-timing): recorded after the final validator run, which postdates all code edits and this log's creation.

- New ratchets: `test_write_text_newline_ratchet.py` + `test_shared_contracts_size_ratchet.py` → **4 passed** (violations 19→0; red-first proven — the ratchet's own first runs produced the finding lists)
- Touched suites foreground: audit_witness + deploy_brain_bootstrap + python_discovery → **26 passed**; false_positives `-k "routing or reverse_edge"` → **5 passed**; precommit-e2e + largelog_sigpipe + worklog_enforcement → **20 passed**
- `update_lifecycle_baseline.py --dry-run` → runs clean post-fix (aggregate deltas `ok`)
- `validate.ps1` (post-last-write) → `pass=118 warn=3 fail=0 skip=2` / passed (3 WARNs = pre-existing historical trio)
- Known local-env artifact (pre-existing, not this diff): `worklog_family_skip` deploy test red locally via the PATH-bash WSL stub; CI-green an hour earlier — CI owns it
- Post-R3 remediation evidence: extended ratchets **4 passed** (incl. the new bytes-shape check; the exclusion-filter's own `.gemini`-root bug was caught by the scan-reach anti-vacuity guard and fixed via ROOT-relative filtering); **FULL `test_validator_false_positives.py` 74 passed in 40:51** — the complete file this time, including the 14 tests the first push broke
- PR #395 CI after remediation `c7b23ea`: **18 pass / 0 fail incl. CI Structural (3m24s)**; merged `43b9680`
- Ship-record terminal write (post-last-write): `validate.ps1` → `pass=118 warn=3 fail=0 skip=2` / passed, after the seq-146 guard write + this log's archival + INDEX append (chain intact)
