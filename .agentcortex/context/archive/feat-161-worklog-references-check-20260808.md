# Work Log: feat/161-worklog-references-check

## Header

- Branch: `feat/161-worklog-references-check`
- Classification: `quick-win`
- Classified by: `claude-sonnet-5`
- Frozen: `2026-08-08`
- Created Date: `2026-08-08`
- Owner: `62a71637-claude-sonnet-5`
- Guardrails Mode: `Quick`
- Current Phase: `implement`
- Diff Base SHA: `b623421`
- Checkpoint SHA: `69639cd`
- Recommended Skills: `none`
- Primary Domain Snapshot: `framework/tooling`
- SSoT Sequence: `143`

---

## Session Info

- Agent: `claude-sonnet-5`
- Session: `2026-08-08 05:15 UTC`
- Platform: `claude-code`
- Files Read: `~20`

---

## Task Description

Implement backlog #161: WARN-tier, ADR-006-compliant tool
(`check_worklog_references.py`) that existence-checks `Spec`/`ADR` rows in an
active Work Log's `## External References` table (format-checks `PR`/`Issue`,
no network calls), wired into both validators via `run_python_check` /
`Invoke-PythonCheck`. Gap: this table was checked by neither validator, so a
fabricated spec/PR reference passed both untouched
(`docs/reviews/2026-08-08-govern-audit-task-simulation.md` F7, probe P1a).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-08T05:15:00Z | Read backlog #161, F7, repo-gotchas, SSoT; quick-win per user instruction |
| plan | done | 2026-08-08T05:25:00Z | Modeled on check_ssot_caps.py; no docs/specs file (backlog row is spec-equivalent) |
| implement | done | 2026-08-08T05:44:00Z | Tool + wiring + tests written, smoke-tested, unit-tested, committed |
| review | pending | — | Not run (quick-win: optional) |
| test | pending | — | Not run as separate phase; pytest evidence in `## Evidence` |
| handoff | pending | — | quick-win exempt |
| ship | pending | — | Local commit only, no PR/SSoT update this session |

---

## Phase Summary

Bootstrap: read backlog #161 verbatim + audit F7 + repo-gotchas (esp. #2
three-wiring-points, #14 count-isolation) + SSoT (seq 143). Verified actual
branch (worktree, not stale `main` snapshot) before deriving worklog-key.

Plan: modeled tool on `check_ssot_caps.py` (WARN-tier, exit-0-always, `--root`,
UTF-8 stdout) and test sibling `test_ssot_caps_check.py` (subprocess pattern).
Confirmed by reading code, not paraphrase: `run_python_check`/`Invoke-PythonCheck`
map exit!=0->FAIL, exit 0->PASS regardless of stdout — WARN lines surface as
indented findings under a PASS label. Confirmed #137 precedent
(`check_routing_actions.py` absent from deploy.sh whitelist + manifest golden)
to mirror for source/CI-only scope; confirmed the governance-tool-reference scan
(`test_deployed_governance_referenced_tools_are_deployed`) only reads
AGENTS.md/CLAUDE.md/GEMINI.md/workflows/rules, not the validators, so citing the
tool path inside validate.sh/.ps1 is safe. See Decisions D-1/D-2 for the two
scope judgment calls (PR/Issue format leniency; cross-platform path resolution).

Implement: wrote `.agentcortex/tools/check_worklog_references.py`
(dependency-free). Smoke-tested red/green fixtures in scratchpad before writing
21 pytest cases (`.agentcortex/tests/test_worklog_references_check.py`, mirrors
`test_ssot_caps_check.py` style). Wired into both validators immediately after
`check_decision_disposition.py`, label-parity'd
(`'worklog external references (spec/ADR existence)'`), zero new native
`record_result`/`Add-Result` sites. Deliberately did NOT add to `deploy.sh`
whitelists or `deploy_manifest_golden.txt` (mirrors #137). Committed `69639cd`.
⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-08T05:15:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-08T05:25:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-08T05:44:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog.md | backlog row #161; audit finding docs/reviews/2026-08-08-govern-audit-task-simulation.md F7 |
| ADR | — | — |
| Issue | — | — |
| PR | — | local commit only, no PR opened (task scope: no push/PR/gh) |

---

## Known Risk

- PR/Issue format check accepts any `#NNN` substring + full URLs (D-1) — a malformed reference containing a stray `#123` would not WARN; in-scope per the row's own "format-presence only, no network" wording.
- Existence check does not verify a Spec/ADR path is semantically a spec/ADR (any existing file passes) — matches the backlog row's explicit "existence check" scope.
- No `/review` or `/test` phase run (quick-win optional); evidence rests on the pytest suite + both validators' full runs.

---

## Decisions

### D-1: PR/Issue format check accepts `#NNN` shorthand, not URL-only

- Decision: exempt from WARN if cell contains `#<digits>`, starts with `http(s)://`, or is `—`/blank.
- Reason: strict URL-or-placeholder would false-WARN on real archived content (`chore-v1.8.18-release-20260803.md` PR row: `#379 #381 #383 ... + 4 ship records`).
- Alternatives rejected: strict URL-only (false-positives on real data); no PR/Issue check at all (task explicitly scopes one).
- Disposition: → local (tool-internal behavior, not a rule change).

### D-2: Path resolution avoids `Path.is_absolute()` for a leading slash

- Decision: only Windows drive-letter/UNC prefixes count as OS-absolute; a bare leading `/` is stripped and treated as repo-relative on every platform.
- Reason: `Path("/x").is_absolute()` is `True` on POSIX, `False` on Windows — using it directly would make the same cell resolve differently in Windows-local vs Linux-CI runs (the `[cross-platform-eol]`-class failure mode).
- Disposition: → local (implementation detail; covered by the existing Global Lesson, no new lesson needed).

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Lock acquired via `recover_worklog_lock.py ensure` at bootstrap entry (`shared-contracts.md §Phase-Entry Lock`); status created, no prior holder; refreshed to `implement` phase mid-session.
- Worklog-key derived directly from the worktree's auto-generated branch name (already filesystem-safe) — no rename; this session runs inside a dedicated background-agent worktree, already task-isolated by construction.
- First validate.sh FOREGROUND run exceeded the tool's foreground timeout twice and fell back to background execution (platform behavior, not a task deviation); ground-truth output was still read and used once each background run genuinely completed (exit 0 / exit 1), never fabricated.
- Work Log initially written at 13.0KB, tripping the 12KB compaction WARN-turned-FAIL (`work log compaction warnings detected`) on the first post-commit validate.sh run — self-inflicted by an overly verbose Phase Summary/Decisions. Condensed in place (this revision) rather than deferring; re-validated after the edit.
- 2026-08-08 review-remediation session (primary agent): worktree switched from the auto-generated agent branch to `feat/161-worklog-references-check` (same commit lineage) for the PR #391 external-review fixes; log renamed to match the new worklog-key. External review (Codex/ChatGPT via PR #391) P1 CONFIRMED by experiment — parser bound fenced decoy content as live rows; fixed with fence-aware scanning + 3 regression tests (24 total). P2 partially adopted: `advisory` added to both validator call-site labels + nested-advisory contract documented in the tool docstring; counted-WARN promotion deliberately left to backlog #103(d).

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

- `.agentcortex/tests/test_worklog_references_check.py` -> 21 passed.
- `tests/ci/test_validator_native_check_ratchet.py` -> 5 passed (native counts unmoved).
- `tests/ci/test_deploy_tiering.py -k manifest` -> 2 passed (manifest golden unchanged — tool deliberately not in deploy.sh).
- `tests/guard/` full dir -> 332 passed. `.agentcortex/tests/` full dir -> 227 passed.
- Local commit `69639cd`, branch `worktree-agent-a21d311d5a0a6ba28`, 4 files / +510/-0. `git status --short` pre-stage showed exactly the 4 intended files.
- First post-commit `bash .agentcortex/bin/validate.sh` (full, untruncated): `pass=117 warn=3 fail=1 skip=2` — FAIL was work-log compaction (13.0KB > 12KB cap), traced and fixed by condensing this file (see Drift Log); own check's line confirmed present and correct: `[PASS] worklog external references (spec/ADR existence)` / `worklog external references OK -- 1 log(s), 4 row(s) checked.` (self-check passes honestly — Spec row cites a real file).
- Re-validation (post-condense, both FOREGROUND, sequential): `bash .agentcortex/bin/validate.sh` -> `pass=118 warn=3 fail=0 skip=2`, passed. `.agentcortex\bin\validate.ps1` -> `pass=118 warn=3 fail=0 skip=2`, passed. Exact sh/ps1 parity. Both show `[PASS] worklog external references (spec/ADR existence)` / `worklog external references OK -- 1 log(s), 4 row(s) checked.` (own log self-check: honest pass, 0 WARN). The 3 WARNs in both are pre-existing/unrelated (2 archived-log historical gaps + governance eval coverage); skip=2 is the populated-log fingerprint (claude-adapter + legacy-rule-surfaces SKIPs), not the no-log skip=3 fingerprint.
- Per the dogfood requirement this backlog row is about: this line is itself a write, so one more `validate.ps1` run follows AFTER it before any number is quoted as final in the chat report (not re-pasted here to avoid infinite regress).

- Archived 2026-08-08 by the primary session's ship chore (chore/ship-govern-audit-wave-20260808); work executed in an isolated agent worktree, landed as feat/161-worklog-references-check (PR #391, merged 4c5f497 + review commit 691ea68).
