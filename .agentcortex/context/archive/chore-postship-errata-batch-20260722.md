# Work Log: chore/postship-errata-batch

## Header

- Branch: `chore/postship-errata-batch`
- Classification: `quick-win`
- Classified by: `claude-fable-5`
- Frozen: `2026-07-22`
- Created Date: `2026-07-22`
- Owner: `claude-fable-primary`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `af6ca2e`
- Checkpoint SHA: `af6ca2e`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `130`

---

## Session Info

> Written by /bootstrap. Update on each new session.

- Agent: `claude-fable-5`
- Session: `2026-07-22 09:30 UTC`
- Platform: `claude-code`
- Guardrails loaded: Quick mode (quick-win — SSoT read + AGENTS.md; full guardrails read skipped per CLAUDE.md step 4)

---

## Task Description

Post-ship remediation batch for the 2026-07-22 codex review of commits 1021533/0aafbe9/af6ca2e. Every review claim was primary-verified against ground truth before scoping (2 real defects, 1 real records gap, 1 mostly-satisfied, 1 future-guidance, 1 wrong-on-locks). This batch (PR B): empty-`/`-suffix matcher guard + direct unit tests (F3), tracked verdict snapshot for fresh-clone provenance (F4), #113 archived-log erratum of record (F5), #143 reclassification note (F6), wave-close log ledger closure (F2). The Python-discovery startability fix (F1) ships separately as PR A (opus delegate, branch fix/python-discovery-startability).

---

## Phase Sequence

> Record each phase entry in order. Update `Current Phase` in the Header on entry.

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-22 | read-only claim verification first; classification frozen quick-win |
| plan | done | 2026-07-22 | 2-PR split: A = discovery fix (delegate), B = errata batch (primary) |
| implement | done | 2026-07-22 | F3 red→green; F4/F5/F6 records; F2 archival + INDEX |
| review | skipped | — | quick-win: review optional (§10.4); per-claim primary verification recorded in Evidence |
| test | skipped | — | quick-win: full eval-test file + not-slow CI-equiv run inline as ship evidence |
| handoff | skipped | — | quick-win exempt |
| ship | done | 2026-07-22 | PR + CI green + merge after PR A |

---

## Phase Summary

Post-ship remediation for the codex review of the external-research wave. Verification-first: of six review claims, claim 1 (Python discovery by existence only — WindowsApps python3 alias shadows working python) confirmed REAL but PRE-EXISTING (validate.sh:271-279 / validate.ps1:202-209 predate the wave; attribution recorded); claim 5 confirmed (archived #113 delegate log's Phase Sequence table contradicts its ship receipt — erratum of record in the tracked verdict snapshot, no in-place archive edit); claim 4 confirmed-with-context (private-note provenance follows the #76 convention but the verdict's PARK/KILL constraints are rejected-design decision content per #138 — tracked summary created at docs/reviews/2026-07-22-external-research-verdict.md); claim 3 mostly already satisfied (all 5 tests exercise production code; only the empty-`/`-suffix edge was missing — guard added + 5 direct unit tests, red→green); claim 2 half-right (archival was disclosed-and-scheduled, not pretended — done now as this unit's ledger closure; zero lock files existed, codex wrong on locks); claim 6 is future guidance (row #143 gained the reclassification note). F1 delegated to opus as PR A with ratchet-safe design (pure selection logic, no new result lines) and a 3-scenario PATH-shim test matrix.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T08:50:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T09:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T09:40:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T11:00:00Z

---

## External References

> Links to specs, ADRs, issues, PRs, or design docs relevant to this task.

| Type | Path / URL | Notes |
|---|---|---|
| Review | docs/reviews/2026-07-22-external-research-verdict.md | tracked verdict summary + errata (created this unit) |
| PR | https://github.com/KbWen/agentic-os/pull/358 | reviewed commit 1021533 |
| PR | https://github.com/KbWen/agentic-os/pull/359 | reviewed commit 0aafbe9 |
| PR | https://github.com/KbWen/agentic-os/pull/360 | reviewed commit af6ca2e |

---

## Known Risk

- Two PRs touch `docs/specs/_product-backlog.md` (A adds row #144, B edits note + #143) — different lines; update-branch dance expected at merge, resolved by merging A first.
- The remediation SSoT entry + additive provenance pointer land in ONE guarded write after PR A's evidence is known — until then SSoT is untouched on this branch.

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

- Per-claim attribution review performed before scoping (claim 1 = pre-existing defect, NOT wave regression; claim 2 lock-cleanup = nothing to clean; claim 3 = mostly already satisfied).
- Planned SSoT guarded write (additive provenance pointer + consolidated remediation Ship History entry, sequence 129→130) executes at ship after PR A merges; will be receipted here.
- INDEX append via `append_chain_entry.py` (wave-close log ledger closure) — tool-computed prev_sha b42d4335, chain verified intact.

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

> Terse per §5.2b.

- F3 RED: `git stash push` (tool only) → `TestProtectsMatchesRuleUnit` → 1 failed (empty-suffix), 4 passed; POP → full file 56 passed.
- Real-repo coverage after guard: `Zero-coverage rules: 28` (unchanged — no real case uses an empty-suffix citation).
- Wave-close log archived → `archive/chore-external-research-wave-close-20260722.md`; INDEX append prev_sha b42d4335; `check_audit_chain.py` intact.
- Ship-head validator + suite lines: recorded in PR body at push time.
