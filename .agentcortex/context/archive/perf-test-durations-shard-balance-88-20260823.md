# Work Log: perf/test-durations-shard-balance-88

## Header

- Branch: `perf/test-durations-shard-balance-88`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `true`
- Created Date: `2026-08-23`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `818007e`
- Checkpoint SHA: `818007e`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `158`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-23 11:20 UTC`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`
- Context carried from the same session's #175/#178 units (Read-Once): SSoT, backlog, `state_machine.md`, `bootstrap.md`, `shared-contracts.md`

---

## Task Description

Backlog **#88**: the three Windows pytest shards are badly unbalanced because `--splits 3 --group N` runs with no committed `.test_durations`, so pytest-split falls back to an even **count** split and clusters the subprocess-shelling deploy tests onto one shard. Commit a durations file so the split balances by time.

**#88's recorded measurement (`7:14`) is stale by ~3×** — corrected here from the #417 CI run.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-23T11:20:00Z | quick-win; 1 new file + 2 stale comments |
| plan | done | 2026-08-23T11:25:00Z | keep the default algorithm; least_duration measured but rejected |
| implement | done | 2026-08-23T11:30:00Z | .test_durations + 2 stale comments |
| review | pending | — | optional for quick-win |
| test | pending | — | optional for quick-win |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-08-23T12:35:00Z | SSoT 158→159; #88 Shipped with its 7:14 figure corrected |

---

## Phase Summary

**bootstrap** — `quick-win`. Adds `.test_durations` (generated, not hand-written) and corrects two comments that assert the file does not exist. No test or source behaviour changes.

**plan** — Keep CI's default `duration_based_chunks`. `least_duration` was measured and is exactly ideal (19.1/19.1/19.1 vs 19.6/19.5/18.2), but it reorders tests across groups; 2.6% is not worth that risk. Measured decision, not preference. Confidence: 93% — high.

**implement** — Committed a 897-entry `.test_durations` (generated, not authored) and corrected two comments that asserted the file did not exist (`validate.yml:332`, `requirements-ci.txt:8`). No workflow flags changed — CI already passes `--splits/--group` and pytest-split picks up the default path. Confidence: 95% — high.

**ship** — SSoT 158→159, Ship History rotated (10/10 held). Backlog #88 → **Shipped** with its stale `7:14` figure corrected to the real `21m57s / 3m19s / 4m14s`. D-1: none recorded (no design fork survived to ship).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T11:20:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T11:25:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T11:30:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T12:35:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #88 | `dx` / `ci` / P3 / quick-win. Its `7:14` figure is stale — correct at ship. |
| CI | .github/workflows/validate.yml:332 | Comment asserts "no committed .test_durations file" — becomes false. |
| CI | .github/requirements-ci.txt:8 | Same assertion — becomes false. |

---

## Known Risk

- **The durations file is machine-relative**: generated on this Windows box (57.3 min total) rather than on `windows-latest` (~29.5 min total). pytest-split only needs **relative** weights and the dominant cost (subprocess spawn) is the same class, but absolute times differ ~1.9× and this must be stated in the PR, not implied away.
- **A durations file goes stale** as tests are added: pytest-split falls back to count-splitting for unknown test ids, so drift degrades gracefully rather than breaking. No guard exists to detect staleness — do not claim one.
- **Do NOT re-propose two closed paths**: `pytest-xdist` was measured slower here (`validate.yml:305-309`); deselecting `slow` in CI is explicitly rejected in `pytest.ini` (subprocess fidelity is the point of those tests).
- **Non-required contexts**: `Pytest (Windows)` is not a required check, so this improves wall-clock and feedback latency — it does not change what can block a merge.

---

## Decisions

none

---

## Conflict Resolution

Reused from this session's earlier units: `karpathy-principles` vs `verification-before-completion` = compatible.

---

## Skill Notes

- `verification-before-completion` — cached: Scope → Quality → Evidence → Risk → Communication; the quoted run must postdate the last state write.

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Backlog write at bootstrap (#88 → In Progress): **the first such advance permitted by the AGENTS.md line #178 shipped hours earlier** — previously this step contradicted §Write Isolation.

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

- Branch from `818007e` (main, post-#178 merge); tree clean. Lock: `created / missing`.
- Durations generated on this box: `pytest ... --store-durations` → **896 passed, 1 skipped, exit 0** in 57:20; **897 entries, 57.3 min total**.

### Predicted balance — CI's exact invocation, default algorithm

| shard | before (#417 real CI) | after (predicted, this box) |
|---|---|---|
| 1 | **21m57s** | 19.6 min (210 tests) |
| 2 | 3m19s | 19.5 min (47 tests) |
| 3 | 4m14s | 18.2 min (640 tests) |
| worst shard as % of total work | **74%** | **34%** (ideal 33.3%) |

Scaled by the 1.94× box↔runner factor the prediction was ≈ **10.1 min**.

### MEASURED on PR #419 — the prediction was optimistic

| shard | before (#417) | predicted | **actual (#419)** |
|---|---|---|---|
| 1 | 21m57s | 19.6 min | **7m18s** |
| 2 | 3m19s | 19.5 min | **8m28s** |
| 3 | 4m14s | 18.2 min | **13m7s** |
| worst | **21m57s** | — | **13m7s** |
| worst share of total | 74% | 34% | **45%** (ideal 33.3%) |

Real improvement **1.67×**, not the predicted 2.2×. The §Known Risk caveat — durations generated on a workstation, not `windows-latest` — is **confirmed by measurement**: the runner weights many-small-tests relatively higher, so the 640-test shard became the slowest rather than the fastest. Follow-up recorded on backlog #88: regenerate durations on the runner (`workflow_dispatch` + `--store-durations` + artifact) to approach the 9.6-min ideal. Owner accepted the 1.67× now and deferred the optimisation.

`least_duration` measured at 19.1/19.1/19.1 — better, rejected for cross-group reordering risk.

### Distribution (why ~10 min is the floor)

- `test_validator_count_parity_on_framework` **479.2s** and `test_170_underscore_meta_specs_no_status_warn` **406.9s** = **25.8% of the whole suite**; the heaviest single test alone is 13.9%.
- 87 of 897 tests (9.7%) carry 90% of the runtime.
- A perfect split cannot beat the heaviest single test — attacking those two is a separate unit with fidelity risk.

### FINAL verification (postdates every implement-phase state write)

- `validate.ps1` → **exit 0** · `pass=118 warn=3 fail=0 skip=2` · unqualified pass.
- `validate.sh` → **exit 0** · `pass=118 warn=3 fail=0 skip=2` · unqualified pass. **Twin WARN sets identical this time** — the run finished inside the 60-min lock window, so no staleness delta.
- Full CI-equivalent suite, no `-m` filter → **896 passed, 1 skipped, exit 0** in 47:19.
- `test_ci_hardening.py` (reads `validate.yml`) → **13 passed**.
- Scope check: `.test_durations` is not referenced by `deploy.sh`, so it is not shipped downstream.
