# Work Log: fix/utf8-subprocess-decoding

## Header

- Branch: `fix/utf8-subprocess-decoding`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-07-26`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `17612ba8b7d1ae34d22c5e98dfcfea2267a9e332`
- Checkpoint SHA: `17612ba8b7d1ae34d22c5e98dfcfea2267a9e332`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `132`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-07-26 (claude-code 2.1.160)`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`
- Downstream-Capabilities: `knowledge_sources: kb-main->OK` (unchanged from the prior unit)

---

## Task Description

Backlog **#146**. `subprocess.run(..., text=True)` without an explicit `encoding=` decodes
child output with `locale.getpreferredencoding()`. On a non-UTF-8 Windows console (`cp950`)
one UTF-8 byte raises `UnicodeDecodeError` *inside* subprocess, `stdout`/`stderr` return
`None`, and the caller dies with `TypeError: ... 'NoneType' is not a container` — naming
nothing about encoding. Six tests were red locally and green in CI on the identical commit.

Fix: add `encoding="utf-8", errors="replace"` at every locale-dependent call site, plus a
cap-at-zero AST ratchet so a new one cannot reappear.

**Phase chain**: `/implement` -> `/ship` (quick-win).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-26 | classified quick-win off backlog #146 |
| plan | done | 2026-07-26 | AST scan first, then scripted patch + ratchet |
| implement | done | 2026-07-26 | 32 sites / 15 files + 1 new guard test |
| review | skipped | — | optional for quick-win |
| test | skipped | — | optional for quick-win (inline evidence) |
| handoff | skipped | — | exempt (quick-win) |
| ship | done | 2026-07-26 | fast-path IMPLEMENTING -> SHIPPED |

---

## Phase Summary

- bootstrap: `quick-win` off backlog #146. Governance-file exclusion does not apply (no
  `.agent/rules/*`, no `AGENTS.md`); the touched surfaces are tests plus two tools.

- plan: scope by AST rather than grep, because the vulnerable shape is semantic (`text=True`
  present AND `encoding=` absent), not textual. Fix shape was already established in-repo by
  `.agentcortex/tests/test_ssot_completeness.py`, so this is a consistency sweep, not a new
  design. | Confidence: 92% — high.

- implement: 32 call sites across 15 files, applied by an AST-located scripted patch and then
  diff-reviewed; +1 new ratchet test. Scope deliberately widened past the backlog wording —
  see Drift Log. | Confidence: 95% — high.

- ship: PASS on the quick-win fast-path. Full CI-equivalent **801 passed** (1h27m) — the first
  fully-green local run on this `cp950` box. `validate.ps1` pass=116 warn=5 fail=0 skip=2.
  Backlog #146 closed; SSoT 132→133 with the oldest Ship History entry rotated to the 2026
  archive. Archived to
  `.agentcortex/context/archive/fix-utf8-subprocess-decoding-20260726.md`.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T00:10:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T00:20:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T00:45:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-26T02:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #146 | the tracked item this closes |
| Precedent | .agentcortex/tests/test_ssot_completeness.py:19 | `encoding="utf-8", errors="replace"` already used here |
| Doc | .agent/rules/repo-gotchas.md #13 | the human-facing description shipped in PR #364 |

---

## Known Risk

- R1 — `errors="replace"` hides genuinely undecodable bytes behind U+FFFD instead of raising.
  Accepted: for a test asserting on tool output, a readable assertion failure beats a crash;
  for the two tools it beats a `RuntimeError(result.stderr.strip())` that would itself throw
  `AttributeError` on `None`. Matches the in-repo precedent.
- R2 — a scripted edit across 15 files could silently mangle source. Mitigated: the patcher
  re-parses each file with `ast.parse` before writing, the scanner re-ran to 0, and the whole
  diff was read (53 insertions / 16 deletions, no EOL churn).
- R3 — the new ratchet could scan stale agent worktrees under `.claude/worktrees/` (three
  exist on this box right now) and fail on code that is not on this branch. Mitigated by the
  dot-directory skip, and that skip is itself asserted by
  `test_scan_actually_reaches_the_repo`.
- Rollback: revert the PR. Mechanical keyword additions plus one new test file; no logic
  change anywhere.

---

## Decisions

none

---

## Conflict Resolution

- `karpathy-principles` vs `verification-before-completion`: compatible (recorded in the prior
  unit's log; matrix unchanged).

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- **Process deviation, recorded honestly**: the branch was cut and the patch applied BEFORE
  this Work Log existed; the log was created retroactively during implement. AGENTS.md wants
  the log to claim ownership first. Nothing was lost (single owner, single session, no
  concurrent writer), but the receipts above were written after the fact rather than at each
  phase boundary. Recorded rather than backdated silently.
- **Scope widened past the backlog wording, deliberately.** #146 said "test subprocess
  helpers". The AST scan found 32 sites across 15 files, of which **2 tool sites** —
  `lint_spec_drift.py:115,120` and `verify_agent_evidence.py:209,388` — carry the same defect
  with a LARGER blast radius: they ship downstream and run inside `/plan` and `/review`, they
  decode `git diff --name-only` output (filenames), and their `raise RuntimeError(
  result.stderr.strip() ...)` would itself throw `AttributeError` on `None`, masking the real
  error twice over. Fixing only the tests would be precisely the easy-fix bias the
  `[prioritization][HIGH]` Global Lesson names. One defect class, one-line fix, fixed together.
- Module count checked against the escalation rule: tests + tools = 2 modules, diff 53
  insertions — under both the `>2 modules` and `>200 lines` hard-block thresholds, so
  `quick-win` holds without reclassification.

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

- AST scan before: **32 vulnerable call sites across 15 files** (13 test files + 2 tool
  files). After the patch: **0 across 0**.
- **Decisive verification on the affected box** (`cp950` ANSI code page): the three files that
  held the six known failures — `test_lesson_chain_archival.py`, `test_verify_agent_evidence.py`,
  `test_trigger_metadata_tools.py` — go from `6 failed, 54 passed` on clean `main` @ `1627852`
  to **`60 passed`**. Same machine, same locale, no environment change.
- New ratchet `tests/ci/test_subprocess_encoding.py`: **5 passed**. It carries its own
  anti-vacuity guards — `test_detector_recognizes_the_unsafe_shape` proves the detector
  distinguishes unsafe/safe/bytes-mode, and `test_scan_actually_reaches_the_repo` fails if the
  file list is silently empty or leaks into `.claude/`.
- Diff reviewed by hand: 53 insertions / 16 deletions over 15 source files, no line-ending
  churn; longest changed line 130 chars (no Python linter or line-length gate exists in this
  repo — checked for ruff/flake8/black config and CI lint steps, none present).
