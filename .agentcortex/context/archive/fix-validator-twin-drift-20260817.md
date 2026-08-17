# Work Log: fix/validator-twin-drift

## Header

- Branch: `fix/validator-twin-drift`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `true`
- Created Date: `2026-08-16`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `implement`
- Diff Base SHA: `7ebf67c`
- Checkpoint SHA: `9c1c44d`
- Recommended Skills: `verification-before-completion, systematic-debugging, karpathy-principles`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `155`

---

## Session Info

- Agent: `claude-opus-5` · Session: `2026-08-16 10:30 UTC` · Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)` — Quick Mode per `engineering_guardrails.md §Reading Mode`;
  the quick-win essentials (Confidence Gate, Bug Fix Protocol, Doc Integrity) come from
  `bootstrap.md` §1. Reading the full guardrails at this tier would be a Token Leak violation.
- Override: `none` · Downstream-Capabilities: `kb-main→OK@328b30ecb33b` (no route match; 0 pages read)

---

## Task Description

Backlog **#174**: `validate.sh` and `validate.ps1` give different answers on the same tree, in three
places — (a) backlog row-set selection, (b) archive-size ruler, (c) a PASS gated on a bare glob.
Reported by a downstream adopter on v1.8.21 alongside the problem PR #412 fixed; this is the half
that was deliberately left.

**The finding that reshaped the unit, verified before planning**: `validate.ps1` runs in exactly one
CI job — `validate-windows` (`runs-on: windows-latest`, "Framework Validation (Windows)") — and
`gh api .../branches/main/protection` returns required contexts `Framework Validation`, `ShellCheck`,
`Check Markdown Links`. **"(Windows)" is not among them.** So `validate.ps1` is gated by nothing
today, and a parity guard placed in a Windows-gated pytest would land in the equally non-required
`Pytest (Windows)` — a guard that cannot block anything, which is the shape this repo deletes.
Making the guard land on a required check is therefore part of the fix, not scope creep.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-16T10:30Z | `quick-win`; ADR coverage exit 0 |
| plan | done | 2026-08-16T11:00Z | 7 steps; step 4 written conditional |
| implement | round 1 done | 2026-08-16T11:15Z | commit `cfbb954` |
| review | NOT READY | 2026-08-16T12:10Z | 1 BLOCKER + 3 MED; routed back to implement |
| test | done | 2026-08-17T00:30Z | 896 passed/1 skipped; 10-scenario downstream matrix 22/0 |
| handoff | n/a | — | quick-win is handoff-exempt |
| ship | done | 2026-08-17T02:00Z | merged `9c1c44d`; SSoT 155→156; v1.8.22 cut |

---

## Phase Summary

- **bootstrap**: `quick-win`. `.agentcortex/bin/validate.*` is tiny-fix-excluded (§10.3), which sets
  the floor; nothing escalates further — no `deploy.sh` edit this time, so §10.4's Supply-Chain
  trigger does not fire, and no auth surface is touched. **`/review` and `/test` are optional at this
  tier and I am running them anyway**: the blast radius here is CI gating, which is the exact surface
  I broke in the previous unit (a `| tee` that silently disabled an exit-code assertion, caught by
  fresh reviewers and not by me). Skipping review on the same surface twice would be the easy-fix
  bias the repo's own Global Lessons name.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T10:30:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T11:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T17:00:00Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-08-16T13:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T17:30:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T18:00:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-17T00:30:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-17T02:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T11:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-16T11:50:00Z
- Gate: review | Verdict: NOT READY | Classification: quick-win | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-08-16T12:10:00Z

---

## External References

| Type | Path | Notes |
|---|---|---|
| Backlog | `_product-backlog.md` #174 | the row this unit closes |
| ADR | `ADR-002`, `ADR-006`, `ADR-010` | cover the validators; ADR-006's native ratchet binds authoring |
| Prior | `archive/fix-validator-downstream-truth-claims-20260816.md` | the sibling half (#173/#412) |

---

## Known Risk

- **R1** ADR-006 native-check ratchet is exact-match both directions (202/203). Any new
  line-leading `record_result` / `Add-Result` breaks CI; message-shaping only.
- **R2** Placing a ps1 run inside the **required** `Framework Validation` job changes what gates
  every future merge. If `pwsh` is unavailable on `ubuntu-latest` the job breaks for everyone —
  so this must be proven by CI observation, not asserted from memory.
- **R3** `du --apparent-size` is GNU-only; a naive fix to (b) would break macOS/BSD adopters. Use a
  portable sum.
- **R4** The three divergences change no verdict on today's tree (measured: labels 15==15, both
  archive figures 4.5–5.7× under threshold, (c) needs a specs dir holding only placeholders). The
  case for fixing rests on (c) being a **vacuous PASS on a fresh downstream** — the same class
  PR #412 just treated — and on (a) hiding an unanchored alternation that matches prose cells.

---

## Decisions

Dispositions at `/ship`.

- **D-1** Put the parity guard in the **required** `Framework Validation` job (ubuntu), not in a  → consolidated: L2 document-governance
  Windows-gated pytest. `validate.ps1` is currently gated by nothing — the Windows job is not a
  required context — so a guard placed there could not block a merge. Placement is the check.
- **D-2** Compare **tallies**, not label sets. A full label-set comparison was measured and  → local
  rejected earlier (131 vs 153 literals; most divergences are `${var}` interpolation artifacts
  needing a normalizer whose own failures are undiagnosable). Tallies need no normalizer, and all
  three of #174's divergences move a count.
- **D-3** Fix the **sh** side of the archive ruler, not ps1. Logical bytes are the right measure  → consolidated: L2 document-governance
  for an ingestion-cost threshold, and block rounding is not stable across filesystems. Avoided
  `du --apparent-size` (GNU-only; would break macOS/BSD adopters) in favour of a portable sum.
- **D-4** **Did not** fix the 4th bare-glob site (`spec_dd_count`, `validate.sh:2774`) that the  → local
  plan flagged conditionally. Verified both sides: sh globs all `*.md` and ps1's `Get-ChildItem
  -Filter '*.md'` does too, with neither skipping `_*` or `.gitkeep.md`. They are identically
  permissive, so it is **not** a twin divergence and not in #174's premise. Left alone.

---

## Conflict Resolution

none — no `partial-conflict` pair in the recommended set.

---

## Skill Notes

none — populated at phase entry.

---

## Drift Log

- Backlog #174 `Pending` → `In Progress` (`bootstrap.md` §1.5). Same `AGENTS.md`-vs-workflow tension
  as last unit, already filed as backlog **#178**; not re-litigated here.

---

## Review Feedback

Round 1 **NOT READY**. Resume scope = these rows only.

- **B1 BLOCKER** `.github/workflows/validate.yml` — the parity step runs the **native Windows**
  validator under Linux `pwsh`, inside a **required** job. `validate.ps1:9-14`
  `Normalize-PathString` unconditionally does `$Path -replace '/', ''`, and this repo's OWN test
  skip reason says it outright: *"running it under Linux pwsh mis-resolves `$root` … (The Linux CI
  job must NOT execute the native PS validator.)"* — `test_validator_false_positives.py:53-58`,
  repeated in two more test modules. My guard would red-lock main on every PR.
  **My misjudgment, named precisely**: I deferred "does pwsh exist on ubuntu" to CI. Existence was
  never the question — correctness was, and it was statically knowable, and the repo had already
  written it down and tested it. Same class as the previous unit's `| tee`: wiring CI without
  reading what the existing wiring already knew.
- **B2 MED** `validate.sh:1239` — (b) is **not closed**. awk `int()` truncates, ps1 `[int]` rounds:
  verified `int(1835.6)`=1835 vs `[int]1835.6`=**1836**. The twins still print different KB on
  ~half of trees, and a verdict can flip in a ~0.5KB band around the threshold.
- **B3 MED** `validate.sh:2835` — (c) replaced a vacuous PASS with **silence**, not a SKIP. The
  repo's own ratchet justification #7 (backlog #149) names an absent result as itself the defect.
  Coherent fix costs +1 emission in each validator and a baseline bump with a justification —
  which is the sanctioned mechanism, not a workaround.
- **B4 MED** the guard compares only the `Summary:` line, so compensating swaps (sh PASS(A)+WARN(B)
  vs ps1 WARN(A)+PASS(B)) pass green; and the per-line `diff` sits inside the mismatch branch, so
  it never runs on a pass.
- **B5 LOW** (a) — I conflated two things. The unanchored alternative was a real bug; **narrowing
  the row set is a separate semantic choice**, and the backlog's own header says it tracks active
  = Pending **/ In Progress**. Today's count is exactly 15 against a `>15` threshold, so narrowing
  can hide a drift the old code would have caught.

---

## Red Team Findings

none — `red-team-adversarial` skips `quick-win` per the auto-trigger matrix.

---

## Design Reference

none — not a UI task.

---

## Observability

none — quick-win.

---

## Resume

none — quick-win is handoff-exempt.

---

## Test Gate Results

`pytest tests/ci/ tests/guard/ .agentcortex/tests/` (no `-m`) → **896 passed, 1 skipped,
0 failed**. Downstream simulation matrix, 10 adopter states deploying for real and running the
DEPLOYED validator → **22 assertions, 0 failures**. Both validators `pass=118 warn=4 fail=0
skip=2` — identical. ADR-006 ratchet 204/204.

---

## Evidence

- **bootstrap / ADR coverage**: `check_adr_coverage.py --paths <4>` → **exit 0** (ADR-002/003/005/006/010).
- **bootstrap / the gating fact**: `validate.ps1` appears in `.github/workflows/validate.yml:187`
  only, inside `validate-windows` (`runs-on: windows-latest`);
  `gh api repos/KbWen/agentic-os/branches/main/protection` → required contexts are
  `Framework Validation`, `ShellCheck`, `Check Markdown Links`. The Windows job is **not** required.
- **bootstrap / branch**: created from `main` at `7ebf67c`, tree clean.
