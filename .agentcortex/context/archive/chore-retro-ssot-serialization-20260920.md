# Work Log: chore/retro-ssot-serialization

## Header

- Branch: `chore/retro-ssot-serialization`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-09-20`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `retro`
- Diff Base SHA: `0d67cb3`
- Checkpoint SHA: `0d67cb3`
- Recommended Skills: `verification-before-completion (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `174`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-09-20 09:31 UTC`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)`
- Override: `none`
- Downstream-Capabilities: `knowledge_sources: kb-main→OK@328b30ecb33b` (kb-consult not activated)
- Files Read: `2`

---

## Task Description

`/retro` over the two units shipped 2026-09-20 (PR #441 governance scope consistency, PR #442 external-review adjudication). Their Work Logs are already archived, so the retro runs as its own unit — the only durable output is the `## Global Lessons` write, which `AGENTS.md §vNext State Model` permits outside `/ship` for `/retro` and requires to be logged here.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-20 | quick-win |
| retro | done | 2026-09-20 | supporting workflow — excluded from gate progression (validate.sh:1553) |

---

## Keep / Problem / Try

- **Keep**: every external claim was re-run rather than read. The A/B on the `/plan` registry row turned a plausible-sounding doc fix into a measured one, and re-measuring the token ratchet caught a proposed wording that would have reddened CI.
- **Keep**: the `ship.md` fix was made net-negative instead of merely correct, so a correctness fix returned 6 tokens of headroom rather than spending 24.
- **Problem**: the second unit was branched from `main` while the first unit's ship PR was still open. Ship writes SSoT, so the second ship rotated the same Ship History entry out a second time. Caught pre-commit only because the rotation script printed the entry name it was moving — nothing asserted it.
- **Problem (smaller)**: a Work Log was rewritten with Python's default text mode, which silently converted the whole file to CRLF and inflated it by 183 bytes against a byte-based cap. Normalized back; `newline=""` is required on every write to a repo file on Windows.
- **Try**: before entering `/ship`, check whether an earlier ship for a sibling unit is still unmerged. If it is, merge and rebase first. Assert the rotated entry is absent from the archive before appending — turn a silent corruption into a stop.

---

## Global Lessons Candidate

- Appended: `[Category: ssot-serialization][Severity: HIGH][Trigger: second-unit-while-ship-pr-open]` — see `current_state.md §Global Lessons`.
- Archived to make room: `[Category: windows-install][Severity: MEDIUM]` (oldest, `prev: GENESIS`). Justification: the lesson is now realized in shipped code — `installers/deploy_brain.ps1:56` skips `*\WindowsApps\bash.exe` explicitly and the comment at `:42` states the lesson's own rationale. A lesson that enforcement has absorbed is holding a slot in an error-pattern registry. Note: the registry holds **zero** LOW-severity entries, and `append_lesson.py:211` pins HIGH, so MEDIUM was the only archivable tier — this was the one MEDIUM superseded by enforcement rather than still-live guidance.

---

## Spec Seeds

- **[NEW-GUARD-PROPOSED]** The `ssot-serialization` lesson is honor-system as written; by the repo's own `[enforcement][HIGH]` standard that makes it theatre. The smallest real guard is a single invariant: **no `### Ship-` heading may appear in both `current_state.md` and `archive/ship-history-*.md`**. It is cheap (a set intersection over two files), has a named runtime consumer (`check_ssot_caps.py`, already reading both surfaces), and converts today's silent corruption into a FAIL. Deliberately NOT built here — adding a validator check is outside a retro's scope, and `ADR-006` requires any new check to be a Python tool behind the wrapper with both deploy spots and the golden updated. Surfaced for the user's decision.

---

## Phase Summary

- bootstrap: classified `quick-win`; retro-only unit, no code change.
- retro: 2 Keep / 2 Problem / 1 Try. One Global Lesson appended, one archived with justification. One Spec Seed raised (guard proposal, not built).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T09:31:07Z
- Gate: retro | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-20T09:35:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| PR | https://github.com/KbWen/agentic-os/pull/441 | unit 1 — merged 5a89c9a |
| PR | https://github.com/KbWen/agentic-os/pull/442 | unit 2 — merged 0d67cb3 |

---

## Known Risk

- Archiving a Global Lesson re-anchors the successor's `[prev:]` hash. If done by hand the chain breaks and `check_lesson_chain.py` FAILs. Mitigation: `append_lesson.py --archive` only, verified with `check_lesson_chain.py` after. Rollback: `git checkout -- .agentcortex/context/current_state.md .agentcortex/context/archive/global-lessons-archive.md` plus the INDEX.jsonl bridge record.

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

- **Non-ship SSoT write (sanctioned)**: `## Global Lessons` append + archive executed via `append_lesson.py` under the `AGENTS.md §vNext State Model` `/retro` exception. No other SSoT field touched; `Update Sequence` NOT incremented (this is not a ship).
- Work Logs for both retro subjects were already archived when this retro ran, so the retro takes its own Work Log rather than appending to theirs. `/retro` is excluded from gate progression by `validate.sh:1553`, so this log carries no ship receipt by design.
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO

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

- `append_lesson.py --archive --index 1` -> `{"op":"archive","status":"ok","archived_body_sha":"4faa557a","bridge_prev":"GENESIS","successor_reanchored":true,"total_lessons":19}`. The `successor_reanchored` flag is the part that matters: a hand-deletion would have left the successor's `[prev:]` pointing at a removed entry.
- `append_lesson.py --category ssot-serialization --severity HIGH ...` -> `{"op":"append","status":"ok","prev_sha":"1f251152","appended_at_line":113,"total_lessons":20}`.
- `check_lesson_chain.py --path .agentcortex/context/current_state.md` -> **lesson chain intact** (verifies the shortened-then-extended chain, i.e. both the archive re-anchor and the append).
- `check_audit_chain.py --path .agentcortex/context/archive/INDEX.jsonl` -> **audit chain intact** (the archive wrote a `lesson_archive` bridge record).
- Cap: 20 -> 19 -> 20. Post-write terminal run: `validate.ps1` **pass=99 warn=4 fail=0 skip=3** (identical to the pre-retro baseline); `check_ssot_caps.py` OK (ship history 10/10, spec index 27/30); both chains re-verified intact after the final state write.
