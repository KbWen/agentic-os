# Work Log: fix/no-python-reduced-assurance

## Header

- Branch: `fix/no-python-reduced-assurance`
- Classification: `quick-win`
- Classified by: `primary (delegated ruling)`
- Frozen: `2026-07-22`
- Created Date: `2026-07-22`
- Owner: `claude-opus-delegate`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `b3d5104fd4da889101ee5913b26da634610e5381`
- Checkpoint SHA: `b3d5104fd4da889101ee5913b26da634610e5381`
- Recommended Skills: `test-driven-development`
- Primary Domain Snapshot: `validators / governance tooling`
- SSoT Sequence: `128`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-07-22 05:12 UTC`
- Platform: `claude-code`
- Guardrails loaded: `Core Directives, Delivery Gates, engineering_guardrails §10.4 (quick-win), shared-contracts (phase-entry skill loading + 5-gate + compression), security_guardrails §1/§3`
- Files Read: `14`

---

## Task Description

Backlog #113: on a no-Python host the validators print an UNQUALIFIED top-line
"Agentic OS integrity check passed" even when python-dependent checks were
skipped (`--no-python`) or degraded (python unavailable) — so a feature Work Log
that skips review/test/handoff can produce a clean top-line pass. Fix: label the
top-line "reduced assurance" in BOTH validators when python-dependent checks did
not run (parity), plus a deterministic malformed-log corpus proving it. Exit code
unchanged (labeling, not a new gate). Also reconcile backlog #89 (already shipped
via PR #345).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-22 | classification quick-win (primary ruling) |
| plan | done | 2026-07-22 | design: reduced-assurance top-line label + corpus (primary ruling) |
| implement | active | 2026-07-22 | TDD red→green, sh+ps1 parity |
| review | skipped | — | quick-win: review optional (§10.4) |
| test | skipped | — | quick-win: test optional; evidence recorded inline |
| handoff | exempt | — | quick-win exempt from /handoff |
| ship | pending | — | PR + backlog reconciliation |

---

## Phase Summary

> One paragraph per completed phase. Delta-oriented.

- bootstrap: quick-win (1 module family: the two paired validators + the paired
  regression-test file). Classification frozen by the primary; no spec/handoff.
- plan: Chosen design (primary ruling) — add a reduced-assurance top-line label
  keyed on `PYTHON_BIN` empty (sh) / `$script:PythonCommand` null (ps1), which is
  exactly `--no-python` OR python-unavailable. Do NOT rebuild the ordering-legality
  parser natively (ADR-006). Prove with a deterministic malformed-log corpus
  (feature-tier, ship PASS receipt, missing review/test/handoff). Target files:
  `validate.sh`, `validate.ps1`, `tests/ci/test_validator_false_positives.py`,
  `docs/specs/_product-backlog.md` (ship-time).
- implement: TDD Red→Green. RED first — the new `#113` marker + `--no-python`
  corpus tests failed against the unfixed validators (sh --no-python printed
  `Summary: pass=89 warn=6 fail=0 skip=15` then the BARE `Agentic OS integrity
  check passed` — the exact defect: skip jumped to 15, fail=0, unqualified pass).
  Applied the byte-parallel label in both validators (sh: `[[ -z "${PYTHON_BIN:-}" ]]`;
  ps1: `if (-not $script:PythonCommand)`), plus 6 regression tests. GREEN — 6/6
  `#113` tests pass. ADR-006 native-check ratchet unchanged (5/5; the change adds
  `echo`/`Write-Output` verdict lines, not `record_result`/`Add-Result` sites).
  EOL preserved: validate.sh pure LF, validate.ps1 pure CRLF+BOM. Confidence: 95% —
  high (signal `PYTHON_BIN`/`$script:PythonCommand` empty is the exact degrade
  condition; else-branch preserves the unqualified line byte-for-byte).
- ship: full CI-equiv split by shard (deploy-heavy slow tests exceed the 10-min
  tool ceiling on this host) — `not slow` all 3 dirs = 657 passed; slow validator
  canaries (count_parity + ps1 no-python neighbor) = 2 passed; #113 block = 6
  passed; ratchet 5 passed. Remaining slow tests (deploy/SSoT/audit/guard) proven
  unaffected (validator change byte-identical on full-python + fail>0; no test
  asserts the top-line; backlog edit schema-valid). Four validator runs captured.
  Backlog #113 → Shipped, #89 reconciled → Shipped via PR #345. Staged 4 tracked
  files (excl. settings.local.json). PR opened; not merged.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T05:12:30Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T05:13:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T05:45:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T06:05:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | quick-win, no spec |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | constrains: no new native check |
| Issue | backlog #113 | docs/specs/_product-backlog.md |
| PR | — | opened at ship |

---

## Known Risk

- Top-line string is consumed by immutable archive Work Logs (evidence records)
  only — no active test/deploy/doc pins full-line equality (repo-wide grep). A
  suffix extension is safe for the two source files. Mitigation: pin-grep recorded
  in Evidence; reconcile any full-line-equality consumer before wording is frozen.
- The qualifier keys on `PYTHON_BIN`/`$script:PythonCommand` emptiness — the exact
  signal for both `--no-python` and python-unavailable. No behavior change on
  full-python runs (else branch preserves the byte-identical unqualified line).

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

- test-driven-development (implement phase): Red→Green — write the failing
  reduced-assurance assertion first (today's validators emit the bare line under
  `--no-python`), then apply the sh+ps1 label, then green. Never production code
  before a failing test for the new behavior.

---

## Drift Log

none

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

> Reproducible evidence. Terse per §5.2b.

**TDD red→green (deployed-fixture behavioral tests):**
- RED (pre-fix): `pytest -k 113 ...marker_parity ...corpus_reduced_assurance` → 2 failed.
  sh --no-python on clean deploy + corpus printed `Summary: pass=89 warn=6 fail=0
  skip=15` then the BARE `Agentic OS integrity check passed` (the #113 defect:
  skip jumped to 15, fail=0, unqualified).
- GREEN (post-fix): `pytest tests/ci/test_validator_false_positives.py -k 113` →
  `6 passed, 68 deselected in 81.22s`. (marker parity · sh --no-python corpus →
  qualifier not bare · sh full-python clean → bare · sh full-python corpus → FAIL
  incomplete · ps1 -NoPython clean → qualifier · ps1 -NoPython corpus → FAIL.)
- ADR-006 native-check ratchet: `pytest tests/ci/test_validator_native_check_ratchet.py`
  → `5 passed` (echo/Write-Output verdict lines are not record_result/Add-Result
  sites — native count unchanged).

**Four validator runs on the source worktree (final lines quoted):**
- `bash validate.sh` (full-python): `Summary: pass=117 warn=3 fail=0 skip=2` →
  `Agentic OS integrity check passed` (UNQUALIFIED — preserved by the else-branch).
- `bash validate.sh --no-python`: `Summary: pass=99 warn=3 fail=1 skip=20` →
  `Agentic OS integrity check failed`. The `fail=1` is `[FAIL] routing_actions
  contract violations detected` — the weaker routing_actions native degraded-
  backstop (validate.sh:1002, backlog #137) flags the source repo's
  docs/reviews/*.md where the authoritative Python parser (check_routing_actions.py,
  PASSES under full-python) does not. Pre-existing #137 divergence (its row links
  to #113); unrelated to this change (git diff = echo-only, runs after all
  checks). Because fail>0 the top-line correctly says "failed" — the
  reduced-assurance qualifier is fail=0-only by design.
- `pwsh validate.ps1` (full-python): `Summary: pass=117 warn=3 fail=0 skip=2` →
  `Agentic OS integrity check passed` (UNQUALIFIED — parity with sh full-python).
- `pwsh validate.ps1 -NoPython`: `Summary: pass=100 warn=3 fail=1 skip=18` →
  `Agentic OS integrity check failed` (same pre-existing #137 native backstop).

**Qualifier demonstrated on a fail=0 --no-python run (clean deploy to temp):**
- `bash validate.sh --no-python`: `Summary: pass=75 warn=3 fail=0 skip=14` →
  `Agentic OS integrity check passed (reduced assurance: python-dependent checks skipped)`.
- `pwsh validate.ps1 -NoPython`: `Summary: pass=75 warn=3 fail=0 skip=14` →
  `Agentic OS integrity check passed (reduced assurance: python-dependent checks skipped)`
  (BYTE-IDENTICAL to sh). The source worktree cannot show the qualifier directly
  because of the pre-existing #137 fail (fail>0 → "failed").

**EOL integrity:** validate.sh CRLF=0 LF_only=2921 (pure LF); validate.ps1
CRLF=2758 LF_only=0 BOM=True (pure CRLF+BOM). Edit tool preserved each.

**Pin-grep (before wording freeze):** repo-wide `integrity check passed` →
only the 2 source files + immutable archive Work Logs (evidence records, not
pins) + the #113 backlog row text. No test/deploy/README asserts full-line
equality → suffix extension safe.
