# Work Log: fix/149-worklog-checks-skip-when-absent

## Header

- Branch: `fix/149-worklog-checks-skip-when-absent`
- Classification: `quick-win`
- Classified by: `claude-opus-5[1m]`
- Frozen: `2026-07-27`
- Created Date: `2026-07-27`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `e6523b1`
- Checkpoint SHA: `1c616d9`
- Recommended Skills: `verification-before-completion`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `138`

---

## Session Info

- Agent: `claude-opus-5[1m]`
- Session: `2026-07-27 UTC`
- Platform: `claude-code`
- Files Read: `6`
- Loaded-Sections: `engineering_guardrails.md §10.1, §10.4; ADR-006 ratchet contract via tests/ci/validator_native_baseline.json`

---

## Task Description

Fix backlog #149: with `.agentcortex/context/work/` empty, the 18 active-work-log checks in both validators emit nothing at all — not a `SKIP` line — while the run still prints `Agentic OS integrity check passed`. A fresh clone or downstream install is the default case for that state, so an adopter runs ~18 fewer governance checks and is told everything passed.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-27 | `quick-win`; validators are tiny-fix-excluded |
| plan | done | 2026-07-27 | mechanics verified BEFORE committing to scope |
| implement | done | 2026-07-27 | 2 validators + 1 test + baseline bump |
| ship | done | 2026-07-27 | PR #373 merged as ac48209 |

---

## Phase Summary

- bootstrap: classified `quick-win`. Observability-only change — no verdict, exit code, or gate semantics move. `.agentcortex/bin/validate.*` is tiny-fix-excluded (`engineering_guardrails.md §10.3`).
- plan: the scope decision was made **after** reading the structure, not before. The 18 checks share a single `worklog_count -gt 0` / `$worklogs.Count -gt 0` guard pattern, so a family-level SKIP costs **1** native site per validator rather than 18 — which is what makes this worth doing at all. Had it required ~40 new emission sites the ADR-006 cost would have outweighed the fix and the design would have had to change. Confidence: 95% — high.
- implement: one SKIP emission per validator at the head of the guarded block; ADR-006 baseline 201→202 / 202→203 with a justification entry; new pinning test with 4 structural cases and 1 behavioral red/green over a real `deploy.sh` install.
- ship: PR [#373](https://github.com/KbWen/agentic-os/pull/373) squash-merged as `ac48209`; all 18 CI checks green incl. CI Structural, all three Pytest-Windows shards, and both Deploy Smoke jobs. Same-session self-cleanup: `repo-gotchas` #14, written hours earlier in PR #371, asserted the family “does not report SKIP” — true when written, false once this shipped. Refreshed in place rather than deleted (the stash-and-rerun advice still holds; only the SKIP claim moved), mirroring the PR #365→#366 precedent.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T07:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T07:10:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T07:45:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T09:30:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | `docs/specs/_product-backlog.md` | row #149 — the finding this fixes |
| ADR | `docs/adr/ADR-006-validator-python-core-strangler.md` | native-site ratchet + escape hatch |
| Archive | `.agentcortex/context/archive/docs-repo-gotchas-14-worklog-archival-20260727.md` | where #149 was discovered |

---

## Known Risk

- **ADR-006 cost is real and was paid deliberately.** This adds a native emission site to each validator, which the ratchet correctly flagged red before the baseline was bumped. Justified in `validator_native_baseline.json`: the `run_python_check` / `Invoke-PythonCheck` wrappers map exit!=0 → FAIL and cannot express SKIP, and a Python tool would have to re-implement the entire work-log family to know the count. Mitigation against future drift: `test_emission_is_family_level_not_per_check` fails if anyone expands it to one SKIP per check, which would make the justification a lie.
- **A guard written the wrong way round would be silently backwards** (emitting the SKIP on every run that *has* logs). Pinned by a regex asserting `-eq 0`, not just the message's presence.
- **Message drift between sh and ps1** would be an invisible parity break. Pinned by a test that extracts and compares both message strings.
- **Rejected design — qualifying the top line.** #113 ships `(reduced assurance: python-dependent checks skipped)` for the `--no-python` case. Applying it here was considered and rejected: that labels a *capability* gap, while this is an *input-absent* case. A repo with no in-flight work is fully checked with respect to what exists, and permanently labeling every clean install "reduced assurance" would be noise that trains readers to ignore the qualifier. The `skip=N` counter carries the signal.

---

## Decisions

### D-1: Family-level SKIP, not per-check, and no top-line qualifier

- **Decision**: emit exactly one SKIP for the whole absent work-log family; leave the summary top line unqualified.
- **Reason**: per-check SKIPs would grow the validator native-site count by ~18 and buy no information a single line does not carry. The top-line qualifier is reserved for capability gaps (#113), not for checks whose input legitimately does not exist.
- **Alternatives**: (a) one SKIP per check — rejected on ratchet cost and noise; (b) qualify the top line — rejected as above; (c) a Python tool behind `run_python_check` — impossible, the wrapper cannot express SKIP.
- **Disposition**: this is an implementation decision governed BY the native-site ratchet, not a new architectural precedent amending it — its durable homes are the baseline justification entry, `test_emission_is_family_level_not_per_check`, and backlog row #149. Ratchet context stays in `## Known Risk` above.
- **Impact**: `skip` goes 2→3 on a repo with no active logs; no verdict, exit code, or gate semantics change.
- → local

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- The behavioral test's first precondition was wrong and was caught by the test itself failing: Python's `pathlib.glob("*.md")` **matches** the shipped `.gitkeep.md` placeholder, while both validators deliberately exclude dotfiles (bash `*` does not match a leading dot; `validate.ps1:1114` filters with `Where-Object { $_.Name -notlike '.*' }`). The assertion now mirrors validator behavior. Parity between the two validators was confirmed intact in the process — this was a test bug, not a product bug.

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

- **Red/green proven by stashing the fix**: with `validate.sh`'s emission stashed → **4 failed, 1 passed**; restored → **5 passed**. The behavioral case runs a real `deploy.sh` install, asserts the SKIP appears with no logs, then writes one log and asserts it disappears and ≥10 checks return.
- ADR-006 ratchet observed red **before** the baseline bump (`native validator check surface GREW (validate_sh: 202 > 201)`) and green after — so the bump is evidenced, not assumed.
- `tests/ci/test_validator_worklog_family_skip.py` → 4 structural passed (0.07s) + 1 behavioral passed (113s).
- Full CI-equivalent suite (`tests/ci` + `tests/guard` + `.agentcortex/tests`) → **813 passed** (1h21m) — run because the diff touches both validators, per the shared-check rule.
- `validate.sh` **and** `validate.ps1` both **pass=117 warn=3 fail=0 skip=2** on a tree that HAS an active log, i.e. the populated path is byte-for-byte unchanged by this fix.
- CI on PR #373: 18/18 green (CI Structural, all three Pytest-Windows shards, both Deploy Smoke jobs), 1 scope-gated skip.
- `repo-gotchas` #14 invariants re-verified after the same-session refresh: **0** hard-directive keywords, **0** `.agentcortex` tool-path references, `test_repo_gotchas_discoverability.py` 6 passed.
