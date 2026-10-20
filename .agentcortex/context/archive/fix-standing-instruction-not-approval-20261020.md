# Work Log: fix/standing-instruction-not-approval

## Header
- Branch: `fix/standing-instruction-not-approval`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-20`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `eaa2a52`
- Checkpoint SHA: `eaa2a52`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `211`

---

## Session Info
- Agent: `claude-opus-5-5`
- Session: `2026-10-20T04:37:43Z`
- Platform: `claude-code`
- Guardrails loaded: skipped (quick-win)
- Override: none
- Downstream-Capabilities: none

---

## Task Description
Put the 'a standing instruction is not gate approval' rule into engineering_guardrails §8. It exists only in one platform's agent memory (2026-09-26 incident: a spec frozen and an accepted ADR amended under 'keep going'), so Codex/Gemini/Antigravity never see it — a cross-platform parity gap found by the 2026-10-20 re-score panel.

---

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-20T04:37:43Z | quick-win (.agent/rules) |
| plan | done | 2026-10-20T04:37:44Z | - |
| implement | done | 2026-10-20T04:38:11Z | - |
| review | done | 2026-10-20T04:38:12Z | - |
| test | done | 2026-10-20T04:38:12Z | - |
| handoff | pending | — | — |
| ship | done | 2026-10-20T04:38:13Z | - |

---

## Phase Summary
- bootstrap: quick-win; .agent/rules edit → §13 Deletion-First/ADD-Gate; engineering_guardrails directive ratchet at cap — wording carries no ratchet keyword.
- plan: one bullet in engineering_guardrails §8 after 'When Uncertain' naming which decisions a standing instruction does not answer (spec freeze/unfreeze, accepted-ADR or frozen-AC amendment, force push, owner-decision backlog rows) and that they are asked explicitly with the work kept as a draft. §13 net-add justification: verified incident + parity gap (rule lives only in one platform's memory). Tier: NONE / keep-honest-unenforced (behavioural, like §8's other bullets). Rollback: revert.
- implement: +1 bullet engineering_guardrails §8 (no MUST/NEVER/PROHIBITED/STRICTLY/Gate FAIL).
- review: self-review — scope matches the recorded incident (spec freeze, ADR amendment, force push, owner-decision rows); no authorization wording; record-where rule matches the no-authorization-text practice.
- test: directive ratchet + lifecycle 56 passed; compact index fresh; validate at ship. ship: local commit. ⚡ ACX

---

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T04:37:44Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T04:37:44Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T04:38:11Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T04:38:12Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T04:38:12Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T04:38:13Z

---

## External References
none

---

## Known Risk
none

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
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- §13 net-add justification: verified incident (2026-09-26/27) + parity gap; +1 line, no deletion found that carries the same meaning.

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
- `pytest tests/ci/test_directive_count_ratchet.py .agentcortex/tests/test_lifecycle_token_consumption.py tests/ci/test_lifecycle_baseline_drift.py` → 56 passed; `generate_compact_index.py --check` fresh.
- final (post-archive): validate.sh `pass=117 warn=5 fail=0 skip=2`; `scan_credentials.py --staged` clean.
