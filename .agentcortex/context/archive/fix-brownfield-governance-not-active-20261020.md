# Work Log: fix/brownfield-governance-not-active

## Header
- Branch: `fix/brownfield-governance-not-active`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-10-20`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `c8beda2`
- Checkpoint SHA: `c8beda2`
- Recommended Skills: `none`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `214`

---

## Session Info
- Agent: `claude-opus-5-5`
- Session: `2026-10-20T05:34:51Z`
- Platform: `claude-code`
- Guardrails loaded: skipped (quick-win)
- Override: none
- Downstream-Capabilities: none

---

## Task Description
Brownfield deploy: when the project already has its own AGENTS.md / CLAUDE.md / GEMINI.md, the framework version lands as *.acx-incoming and governance is not active until merged; deploy only says 'merge manually' and validate fails with three unrelated-sounding messages. Owner chose option B in chat 2026-10-20: state it plainly in deploy output and above the validator summary; do not modify the adopter's files (ADR-005 unchanged).

---

## Phase Sequence
| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-20T05:34:52Z | - |
| plan | done | 2026-10-20T05:34:52Z | - |
| implement | done | 2026-10-20T05:37:52Z | - |
| review | pending | — | — |
| test | done | 2026-10-20T06:36:32Z | full suite 1100 via recorder |
| handoff | pending | — | — |
| ship | done | 2026-10-20T06:36:33Z | local commit |

---

## Phase Summary
- bootstrap/plan: quick-win (deploy.sh + validate twins, message-only). Reproduced: own AGENTS.md+CLAUDE.md → [SKIP] + .acx-incoming; validate FAILs 'safety nucleus freshness', 'work log contract references are stale', 'AGENTS.md missing routing index reference'. Plan: deploy prints a GOVERNANCE NOT ACTIVE block naming the entry sidecars; validate.sh/.ps1 print a NOTE above Summary when an entry-file sidecar exists. No new record_result/Add-Result (ADR-006 ratchet unchanged); ADR-005 unchanged. Rollback: revert.
- implement: deploy.sh prints a 'GOVERNANCE IS NOT ACTIVE YET' block naming entry files with a .acx-incoming; validate.sh/.ps1 print a NOTE above Summary for the same state (no new record_result/Add-Result; ps1 BOM kept; PS 5.1 + 7 parse 0 errors). Reproduced on a brownfield fixture: banner + identical NOTE and tally in both twins; clean deploy prints neither. tests/ci/test_brownfield_entry_notice.py (slow-marked, 2 tests; NOTE removal mutant killed). Static ratchets/parity 24 passed.
- test: full CI-equivalent suite through the recorder → 1100 passed, 2 skipped (58m). review: optional for quick-win; self-checked message text against reproduced fixture output (banner + NOTE identical in both twins, clean deploy silent). ship: pre-merge check rc=0; local commit. ⚡ ACX

---

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T05:34:52Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T05:34:52Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T05:37:52Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T06:36:32Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-20T06:36:33Z

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
- Test run: `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q -p no:cacheprovider` | exit: 0 | tree: 5bddd851ecd2651e34c2c35c36f8609cd957621b | at: 2026-10-20T06:36:06Z

---

## Evidence
- Demonstration: brownfield fixture (own AGENTS.md + CLAUDE.md) → deploy prints '!! GOVERNANCE IS NOT ACTIVE YET: AGENTS.md CLAUDE.md kept your own version.'; validate.sh and validate.ps1 both print the NOTE and 'Summary: pass=84 warn=1 fail=3 skip=8'; a clean deploy prints neither.
- final (post-archive): validate.sh `pass=117 warn=5 fail=0 skip=2`; `scan_credentials.py --staged` clean.
