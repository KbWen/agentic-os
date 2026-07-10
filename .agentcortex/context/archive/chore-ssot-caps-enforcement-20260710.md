# Work Log: chore/ssot-caps-enforcement

## Header

- Branch: `chore/ssot-caps-enforcement`
- Classification: `quick-win`
- Classified by: `claude-fable`
- Frozen: `2026-07-10`
- Created Date: `2026-07-10`
- Owner: `claude-fable`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `5a9753cbbdb5d3c555536aa4de8dcd160e6cbeb3`
- Checkpoint SHA: `7f0c2c7`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-runtime`
- SSoT Sequence: `116`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-07-10 02:17 UTC`
- Platform: `claude-code`
- Files Read: `18`

---

## Task Description

> Settled quick-win, 3 units on one branch:
> 1. Execute the ship.md ship-history rotation rule — trim `## Ship History` from 67 to the latest 10, move entries 11-67 verbatim to `archive/ship-history-2026.md`.
> 2. Machine-enforce the two SSoT caps (ship history + spec index) via a new advisory Python tool `check_ssot_caps.py` wired into both validators (ADR-006 run_python_check WARN-tier, never FAIL) + config key `ship_history_max_entries: 10` + pytest fixtures.
> 3. NOT-READY remediation hint: augment the illegal-edge message in both validators' gate parser when a review NOT READY receipt was popped (message-only, FAIL verdict preserved).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-10 | quick-win classification (delegated, settled) |
| plan | done | 2026-07-10 | 3-unit plan settled by primary; SSoT + guardrail patterns read |
| implement | done | 2026-07-10 | 3 units complete; validators + tests green |
| review | n/a | — | quick-win self-review folded into verify |
| test | done | 2026-07-10 | full CI-equiv suite green |
| ship | pending | — | (not this task — commit only, no push) |

---

## Phase Summary

> Delta-oriented, one paragraph per completed phase.

- bootstrap: quick-win (settled by primary). Read SSoT `current_state.md`, `.agent/config.yaml`, worklog template. Confirmed worktree branch `chore/ssot-caps-enforcement`, HEAD `5a9753c`. ⚡ ACX
- plan: Verified the 3-unit design against ground truth — 67 `### Ship-` entries (keep 10, move 57); NO markdown links in current_state.md (grep `](` = 0 → zero relative-link WARN risk); ship-history archive is NOT an INDEX.jsonl chain node (the 3 grep hits are work-log nodes that merely mention the file); run_python_check/Invoke-PythonCheck contract is exit0→PASS / non-zero→FAIL (so an advisory never-FAIL tool must always exit 0 and print findings); target files are pure LF (eol=lf, 0 CR bytes). ⚡ ACX
- implement: UNIT 1 — rotated `## Ship History` 67→10 via `guard_context_write.py --mode replace` (snapshot+expected-sha, receipts `337ffd90d88a8b4f.json` / `c720d2fafb66e0cb.json`); moved 57 entries verbatim to `archive/ship-history-2026.md` (45→102), inserted above the pre-existing top; git diff = 340 ins / 340 del symmetric; 0 CR bytes; 0 markdown links so 0 new M8 WARNs. UNIT 2 — added `ship_history_max_entries: 10` to config; new `check_ssot_caps.py` (always exit 0, WARN-tier advisory, UTF-8-forced stdout) wired into validate.sh + validate.ps1 after the safety-nucleus check (run_python_check/Invoke-PythonCheck, MissingPythonLevel WARN); 8 fixture tests in tests/guard/. UNIT 3 — sticky `had_not_ready` flag augments the `...->review` illegal-edge message (fresh implement PASS receipt needed before re-review PASS, cites review.md §Reverse Transition), FAIL preserved, both validators; fixture tests (real bash + real ps1 + source parity) green. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T02:17:23Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T02:17:23Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T02:40:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T03:35:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-10T06:43:24Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | — |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | new validator check = Python tool behind run_python_check |
| Issue | — | — |
| PR | — | — |

---

## Known Risk

- SSoT write outside `/ship`: this quick-win rotates `## Ship History` directly. Mitigated by using `guard_context_write.py --mode replace` (optimistic-lock + receipts) and logging in Drift Log. Post-trim counts (ship 10, spec-index 21) are UNDER caps so the new check reports PASS.

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- UNIT 1 SSoT write (authorized): `## Ship History` rotation (67→10) and the move of 57 entries into `archive/ship-history-2026.md` are performed as an authorized quick-win maintenance task OUTSIDE `/ship` (normally only `/ship` writes SSoT — AGENTS.md §Write Isolation). Both writes go through `guard_context_write.py --mode replace` (snapshot + `--expected-sha`), producing per-target receipts. No INDEX.jsonl entry (ship-history archive is not a chain node; no work-log archival in this task).
- Worktree branch remediation: this agent's isolated worktree started on auto-branch `worktree-agent-ab9b246f2ae0b1f74`; renamed to `chore/ssot-caps-enforcement` (the shared main checkout was restored to `main`, stray branch deleted). HEAD unchanged at `5a9753c`.

---

## Review Feedback

Independent adversarial /review (fresh context, no implement carryover) — commit `9ddf762` vs `main`. Verdict: **PASS**.

**Burden of Proof (quick-win behavioral):**
- UNIT 1 (rotation + archive move): PROVEN. Reconstructed the move — blankless content diff of the 340 deleted SSoT lines vs 340 added archive lines is EMPTY (verbatim); 67 = 10 kept + 57 moved; order preserved (SSoT keeps newest entries 1-10 `v1.8.9…`→`fix-guard-lock-win-delete-pending`, archive receives 11-67 in order, first moved `fix-ci-docs-pins-gate` = main entry 11, last `fix-deploy-eol-hash-stale-skills-2026-06-10` = main entry 67). Seam clean: last-moved header (archive:337) and first pre-existing header `chore-backlog-tracker-sync-2026-06-10` (archive:345) are distinct — no duplicate. No duplicate headers in archive (102) nor across SSoT∪archive. Only diff artifact = one benign blank-line separator shuffle at the boundary. 0 CR bytes both files. 0 `](` markdown links in the moved block → zero new relative-link breaks.
- UNIT 2 (advisory cap tool + wiring): PROVEN. `check_ssot_caps.py` independently exercised: real repo → `ssot caps OK — ship history 10/10, spec index 21/30.` exit 0; 15-entry over-cap fixture → WARN line, exit 0; missing SSoT → silent, exit 0 (always-0 contract holds). `_yaml_loader.py` present so config caps are truly read; missing-key / non-int / parse-failure all fall back to defaults (10/30). Spec-index counter stops correctly at the next top-level bullet (`- **Canonical Commands**`), counts 21 flat entries; ADR Index cannot be miscounted. Both validators wire the SAME tool via `run_python_check`/`Invoke-PythonCheck` with `WARN` MissingPythonLevel + `--root` — true parity; both contracts are exit0→PASS / absent→SKIP / no-python→WARN, so the tool can NEVER move fail count. Native-ratchet untouched (direct call form, no record_result/Add-Result else-branch) — `test_validator_native_check_ratchet` green. config: `spec_index_max_entries: 30` pre-existing (main:146), `ship_history_max_entries: 10` new (branch:152).
- UNIT 3 (NOT-READY hint): PROVEN message-only. In BOTH validators the change is confined to the `curr == 'review' && had_not_ready` branch; every other illegal edge falls to the unchanged `else`. Both branches emit an `illegal:`/`illegal gate progression` line and take the identical failure path (bash `sys.exit(0)` after printing `illegal:`; ps1 `$gateProgressionIllegal++; break`) — FAIL verdict identical. Legal logs never reach the branch (unaffected). Source-parity test asserts identical hint text + `review.md §Reverse Transition` cite in both.

**Evidence runs:** `bash validate.sh` → `Summary: pass=114 warn=3 fail=0 skip=2`, integrity check passed; new line renders `[PASS] ssot section caps (ship history + spec index)` / `  ssot caps OK — ship history 10/10, spec index 21/30.` (em-dash survives). Full CI-equiv pytest `tests/ci tests/guard .agentcortex/tests -m "not slow"` → **590 passed, 77 deselected** (incl. new `test_ssot_caps_check.py` ×8 driving the real tool via subprocess, and `test_not_ready_re_review_hint_source_parity`). None of the 3 WARNs originate from this change (historical governance gaps + eval coverage).

**Non-blocking observations (none change the verdict):**
- LOW / informational: the `had_not_ready` sticky flag is set on ANY review NOT-READY reverse edge anywhere in a log, so a *doubly-malformed* log (a resolved NOT-READY cycle PLUS a later, unrelated illegal `X->review` edge, e.g. `handoff->review`) would attach the NOT-READY remediation text to that unrelated edge. The log is already FAILing and the verdict is unchanged — cosmetic message-accuracy only. Acceptable for an advisory hint; the common/intended case (`plan->review` after a popped implement) is exactly correct.
- Informational: the spec-index counter matches every `^\s+- ` line, so a future nested sub-bullet under a spec entry would inflate the advisory count by 1. Current SSoT is flat (21 real entries) so no present impact; WARN-only anyway.
- Informational (outside the reviewed commit): working tree carries uncommitted churn in `.agentcortex/context/.guard_receipt.json`, `.guard_receipts/337ffd90d88a8b4f.json`, `.claude/settings.local.json` — runtime guard-write/settings artifacts, not part of commit `9ddf762` (which is exactly the 8 intended files).

**Scope:** exactly 8 files in the commit, all mapped to the 3 units — no unrelated changes. **Security:** clean (file-read tool, no eval/shell/network; tests use fixed-arg subprocess). **Governance:** bootstrap/plan/implement receipts present (pipe format, unfenced); Drift Log records both the authorized guarded SSoT write and the shared-checkout worktree remediation.

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

## Evidence

> Reproducible evidence. Filled during implement/verify.

- **UNIT 1 counts**: `grep -c '^### Ship-' current_state.md` → 10 (was 67, verified by grep at plan time). `grep -c '^### Ship-' archive/ship-history-2026.md` → 102 (was 45; +57 moved). `git diff --stat` → archive +340 / current_state -340 (symmetric verbatim move). 0 CR bytes both files. 0 markdown links in moved block (`](` grep = 0) → 0 new M8 WARNs. Guarded writes: current_state.md new_sha `73f6b48a…`, archive new_sha `171039bf…`; receipts `337ffd90d88a8b4f.json` + `c720d2fafb66e0cb.json`.
- **UNIT 2 tool**: live `check_ssot_caps.py --root .` → `ssot caps OK — ship history 10/10, spec index 21/30.` exit 0. Over-cap fixture (12 ship / 31 spec) → both `WARN:` lines, exit 0 (never FAIL).
- **UNIT 3 hint**: bash + ps1 fixture (bootstrap/plan/implement PASS + review NOT READY + review PASS, no fresh implement) → still FAIL (`illegal gate progression`) AND prints `NOT READY re-review: add a fresh …review.md §Reverse Transition`.
- **validate.sh**: `Summary: pass=114 warn=3 fail=0 skip=2`; `[PASS] ssot section caps (ship history + spec index)` → `ssot caps OK — ship history 10/10, spec index 21/30.` The 3 WARNs are pre-existing (archived-worklog historical gaps ×2 + governance-eval-coverage 28) — none from this change; pass 113→114 = the new check.
- **validate.ps1**: parity `Summary: pass=114 warn=3 fail=0 skip=2`; same check PASS. UNIT 3 ps1 execution fixture green.
- **Full CI-equiv pytest** (`tests/ci tests/guard .agentcortex/tests -m "not slow"`): 590 passed, 0 failed, 77 deselected. Includes new `tests/guard/test_ssot_caps_check.py` (8) + `test_not_ready_re_review_hint_source_parity`.
- **Flagged tests**: `test_ssot_completeness.py` + `test_lifecycle_token_consumption.py` + `test_lifecycle_baseline_drift.py` → 48 passed (SSoT edit did NOT break completeness — only Ship History touched, Spec Index untouched; current_state.md shrank → net token decrease, drift-detector shrink is advisory-only).
- **ADR-006 ratchet**: `test_validator_native_check_ratchet.py` PASS — wiring uses the direct `run_python_check`/`Invoke-PythonCheck` call form (no `record_result`/`Add-Result` else-branch), so the native surface is unchanged; no baseline bump.

⚡ ACX
