# Work Log: fix/152-ship-md-nesting

## Header

- Branch: `fix/152-ship-md-nesting`
- Classification: `quick-win`
- Classified by: `claude-opus-5[1m]`
- Frozen: `2026-08-03`
- Created Date: `2026-08-03`
- Owner: `7d0ae52d-claude-opus-5`
- Guardrails Mode: `Full`
- Current Phase: `bootstrap`
- Diff Base SHA: `c663ed3`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `141`

---

## Session Info

- Agent: `claude-opus-5[1m]`
- Session: `2026-08-03`
- Platform: `claude-code`
- Files Read: `3`

---

## Task Description

Backlog #152: six always-applicable `/ship` rules are indented as markdown children of `- **No-Python fallback**`, so an agent that has Python can legitimately read the whole block as not applicable — including the Ship History newest-first rule this repo has already been bitten by. De-nest them to the sibling level they belong at.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-03 | quick-win; ship.md is a §10.3 governance-file escalation |
| plan | done | 2026-08-03 | whitespace-only; 6 bullets + fence |
| implement | done | 2026-08-03 | 11 lines dedented |
| review | pending | — | optional at this tier; running anyway |
| test | done | 2026-08-03 | 89 targeted passed; validate green |
| ship | pending | — | — |

---

## Phase Summary

**bootstrap** — Classified `quick-win`. `.agent/workflows/ship.md` is not tiny-fix eligible (governance workflow surface). Scope is whitespace-only: 6 bullets from 3-space to 0-space indent, and the 5-line fenced example from 5-space to 2-space so it stays attached to its parent bullet. No wording change, so the token ceiling gets a small refund rather than a cost.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T09:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T09:10:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T09:20:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T09:30:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | — |
| ADR | — | — |
| Issue | backlog #152 (`docs/specs/_product-backlog.md`) | backlog-only per issue-exposure policy |
| PR | — | — |

---

## Known Risk

- `tests/guard/test_ssot_heartbeat_contract.py` pins phrases on the moved lines. Substring assertions should be indifferent to leading whitespace, but this must be run, not assumed.
- Moving the fenced block's indent could change how the example renders or attaches. Verify the fence still belongs to `- Use the format:`.
- Root Cause: the block was authored with the Spec Index Cap and Ship History rules indented one level under a conditional bullet, and no renderer-level check exists for markdown list semantics, so it survived every review since.

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Local test strategy narrowed this session: the 838-test full suite is no longer run in the background locally (it spawns bash/PowerShell/git subprocesses for ~40 min and coincided with a desktop-app termination). Targeted subsets locally; CI owns the full sweep.

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

- Targeted set (every suite pinning `ship.md` content, plus the token/directive ratchets): `pytest tests/guard/test_ssot_heartbeat_contract.py tests/guard/test_ssot_caps_check.py .agentcortex/tests/test_skill_notes_contract.py .agentcortex/tests/test_lifecycle_contract.py .agentcortex/tests/test_lifecycle_token_consumption.py tests/ci/test_directive_count_ratchet.py tests/ci/test_lifecycle_baseline_drift.py` → **89 passed**
- `validate.sh` → `pass=117 warn=3 fail=0 skip=2`; `check_command_sync.py` → passed (30 total)
- Full 838-test sweep delegated to CI this time (see Drift Log).

---

## Evidence

- `git diff -w` on `ship.md` is **empty** — proof the change is indentation-only, zero content edited.
- Token ceiling: aggregate 354,277 → **354,229** (headroom 723 → 771); `ship.md` 24,458 → 24,425 chars, exactly the 33 whitespace characters removed.
- Self-inflicted defect caught and fixed mid-task: `Path.write_text` on Windows rewrote the whole file as CRLF (+275 bytes), violating the `eol=lf` attribute. Detected because `wc -c` grew while the token aggregate shrank — contradictory numbers. Restored by rewriting the bytes with CRLF replaced by LF; `git ls-files --eol` now reports `w/lf`.
- Pre-fix structure (`ship.md`, verified with an indent map): `:183` `- **No-Python fallback**` at indent 0; `:184-186` and `:194-196` at indent 3; fenced example `:188-192` at indent 5.
