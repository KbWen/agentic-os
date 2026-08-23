# Work Log: fix/agents-md-backlog-write-scope-178

## Header

- Branch: `fix/agents-md-backlog-write-scope-178`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `true`
- Created Date: `2026-08-23`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `a1cbf41`
- Checkpoint SHA: `a1cbf41`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `157`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-23 07:04 UTC`
- Platform: `claude-code`
- Guardrails loaded: `§13 only` (heading-scoped — the sanctioned exemption for a quick-win editing a governance path)
- Override: `none`
- Downstream-Capabilities: kb-main→OK@328b30ecb33b (not consulted — no KB routing for governance-text work)
- Context carried from the same session's #175 unit (Read-Once): SSoT, backlog, `state_machine.md`, `bootstrap.md`, `shared-contracts.md`, `skill_conflict_matrix.md`

---

## Task Description

Backlog **#178**: `AGENTS.md:37` §Write Isolation scopes `_product-backlog.md` writes to spec-intake/ship, while `bootstrap.md §1` step 5 **mandates** a `Pending → In Progress` advance at bootstrap. Precedence (AGENTS.md > workflows) forbids the step the workflow requires. **Reproduced live** in this session's #175 bootstrap.

Sub-item (same row): `docs/specs/downstream-adaptability-optimization.md` frontmatter still reads `status: frozen` while the SSoT Spec Index records `[Shipped 2026-06-14, PR #238]` and `ship.md §6` (AC-27) says ship sets `shipped`.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-23T07:04:43Z | quick-win; AGENTS.md + one spec frontmatter line |
| plan | done | 2026-08-23T07:10:00Z | Option A (widen the AGENTS.md enumeration) over Option B (move the advance) |
| implement | done | 2026-08-23T07:16:00Z | AGENTS.md 1 line, spec frontmatter 1 word, 1 test docstring word |
| review | pending | — | optional for quick-win |
| test | pending | — | optional for quick-win |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-08-23T09:05:00Z | SSoT 157→158; #178 Shipped, #177 premise rewritten, #181 filed |

---

## Phase Summary

**bootstrap** — `quick-win`. Two surfaces, both one-line: `AGENTS.md` §Write Isolation and one spec's `status:` frontmatter. Under the `> 2 modules` / 200-line thresholds.

**plan** — Chose **Option A (widen the AGENTS.md enumeration)** over Option B (move the advance to a later phase): the advance at bootstrap is the behaviour the repo wants (`bootstrap.md §1` step 5 calls it "the only valid `Pending → In Progress` transition"), so the surface that mis-describes it is the one to fix. Option B would have changed workflow behaviour to satisfy a text defect. Confidence: 93% — high.

**implement** — `AGENTS.md:37` rewritten in place (1 line changed, net 0 lines): the exception now names the bootstrap status advance, and the line's **two duplicate no-Python fallback clauses were merged into one** — that merge is the §13 Deletion-First trim funding the widening. `downstream-adaptability-optimization.md` `status: frozen` → `shipped`. One stale word in `test_validator_absent_tool_signal.py:43` ("frozen" → "shipped") corrected in the same change. Confidence: 95% — high.

**ship** — SSoT `Update Sequence` 157→158; Ship History entry at top, oldest rotated to `archive/ship-history-2026.md` (10/10 held). Backlog: #178 → **Shipped**; **#177 rewritten** — its frozen-gate half is gone, AC-S5 wording still blocks; **#181** filed for the macOS-coverage gap (non-required, first real run is the verification, do not green it by weakening a test). D-1 disposition: `→ local` (the durable home is the AGENTS.md line itself).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T07:04:43Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T07:10:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T07:16:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T09:05:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #178 | `review-finding` / `governance` / P3 / quick-win. |
| Rule | .agent/rules/engineering_guardrails.md §13 | Deletion-First + ADD-Gate; binds because AGENTS.md is in its Applies-to list. |
| Test | tests/ci/test_directive_count_ratchet.py | AGENTS.md at **37/37** — the edit must add zero `MUST/NEVER/PROHIBITED/STRICTLY/Gate FAIL` hits. |
| ADR | docs/adr/ADR-010-frozen-spec-lifecycle.md | Governs the frozen→shipped reconciliation and the require-in-index rule. |

---

## Known Risk

- **Directive ratchet is at cap (37/37)**: any wording that introduces one of the five counted keywords fails a CI test. Verify by re-counting, not by eye.
- **Deletion-First**: an AGENTS.md change must cite a deletion/trim in the same change, or record a net-add justification here. Plan is to **merge a genuine in-line duplicate** rather than claim an unrelated trim.
- **frozen→shipped is not cosmetic**: under ADR-010 the Spec-Index-completeness check skips `frozen` but *requires* `shipped` specs to be indexed. Confirm the index entry exists before flipping, or the flip turns a skip into a FAIL.
- **Scope honesty**: this reconciliation removes the *frozen-gate* half of #177's blocker. It does **not** amend **AC-S5**, so #177 still needs a spec-freshness update before the `deploy.sh` duplication can be collapsed.

---

## Decisions

### D-1: fix the surface, not the workflow

- Decision: widen the `AGENTS.md` §Write Isolation enumeration; leave `bootstrap.md` §1 step 5 untouched.
- Reason: the workflow step is the intended behaviour and is called "the only valid transition" there; the governance line simply failed to enumerate it. Moving the advance would trade a text defect for a behaviour change.
- Alternatives: move the advance to /plan or /implement (rejected — later phases are not guaranteed to run for every classification, so the row could stay `Pending` while work proceeds).
- Impact: removes a precedence contradiction that fires on every non-tiny-fix bootstrap.
- → local — the decision is now embodied in the shipped `AGENTS.md` line; no ADR named, no durable decision reversed.

---

## Conflict Resolution

Reused from the same session's #175 bootstrap: `karpathy-principles` vs `verification-before-completion` = compatible. No re-read of the matrix.

---

## Skill Notes

- `verification-before-completion` — cached from this session's #175 unit: Scope → Quality → Evidence → Risk → Communication; the quoted run must postdate the last state write of the phase.
- `systematic-debugging` (`on-failure`) — not loaded; no failure in scope.

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Re-read: `.agent/rules/engineering_guardrails.md` §13 (full section) — reason: §13's own Applies-to list names `AGENTS.md`, and §0's quick-win exemption permits exactly this heading-scoped read.
- Backlog write pending at ship (#178 → Shipped) — the very directive this unit is fixing.
- **§13 accounting**: the AGENTS.md line is net **0 lines** but **+56 characters** (352→408). The cited trim is the merge of two duplicated no-Python fallback clauses that both lived on that same line (one parenthetical, one trailing sentence, added by the 2026-05-26 compression pass `f3b3b81`). Net-add justification: the widening text names a concrete workflow step and section, which is what makes the enumeration checkable.
- **Ordering slip (disclosed)**: `Diff Base SHA` / `Checkpoint SHA` were recorded *after* the two edits rather than before, contrary to `implement.md` Turn 0. Both point at `a1cbf41`, the branch point, so the review base is still correct; the slip is the write order, not the value.
- Recovered stale Work Log lock on 2026-08-23T10:38:24.967137+00:00; prior_owner=KbWen; prior_session=2026-08-23T07:04:43Z; reason=stale-time; lock=fix-agents-md-backlog-write-scope-178.lock.json

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

- Branch `fix/agents-md-backlog-write-scope-178` from `a1cbf41` (main, post-#175 merge); tree clean.
- Lock: `created / missing`.
- AGENTS.md directive count measured at bootstrap: **37**, baseline **37** (`directive-count-baseline.json`).

### FINAL verification (postdates every implement-phase state write)

- `pwsh -File validate.ps1` → **exit 0** · `pass=118 warn=3 fail=0 skip=2` · unqualified `Agentic OS integrity check passed`.
- `bash validate.sh` → **exit 0** · `pass=118 warn=4 fail=0 skip=2` · unqualified pass. 4th WARN = `stale advisory work log locks detected: 1`, this session's own lock (60-min timeout vs a 90-min suite) — the documented limitation in `config.yaml §worklog_lock`, re-`ensure`d to `recovered / stale-time`.
- `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q` → **896 passed, 1 skipped**, **exit 0**, 1:30:03.
- Targeted, run first: `test_directive_count_ratchet.py` + `test_validator_absent_tool_signal.py` → **14 passed**.
- Ratchet mutation-verified before trusting the green: actual `(True, 'count 37 matches baseline 37')`; +1 `MUST` → `(False, 'count 38 exceeds baseline 37 (growth)')`.

### Two defects the gate caught in me during implement

- First `validate.ps1` run: `fail=2` — `metadata deep validation` + `compact index freshness`, both "compact index is stale". Editing `AGENTS.md` invalidates `trigger-compact-index.json`; fixed by re-running `generate_compact_index.py` in the same change (1 line diff = the AGENTS.md hash).
- Same run: `backlog label vocabulary: 16 distinct labels (>15)`. I filed the new row with `Labels: dx`, but `dx` is a **Kind** value, not an existing label — a violation of `bootstrap.md §5`'s label-reuse rule. Corrected to `tooling`; distinct active labels back to 15.

### Measured test-cost data (feeds backlog #88 / #181)

- #417 CI job times: `Pytest (Windows) (1)` **21m57s** vs shard 2 **3m19s**, shard 3 **4m14s**; Linux `CI Structural Tests` runs the **full** suite in **3m29s**.
- Cause: `--splits 3 --group N` with **no committed `.test_durations`** → even *count* split clusters the subprocess-shelling deploy tests onto one shard. Balanced ≈ **10 min/shard** (>2× wall-clock cut from one file). #88's recorded `7:14` is stale by ~3×.
- Closed paths, do not re-propose: `pytest-xdist` measured slower here; deselecting `slow` in CI is explicitly rejected in `pytest.ini`.
- macOS: **0 runners** (15 ubuntu + 2 windows). BSD-vs-GNU scan of both shipped shell scripts clean; `sha256sum` already falls back to `shasum -a 256` → `openssl dgst`. Filed as #181 on the verified *absence*, not a suspected break.
