# Work Log: fix/capabilities-bom-tolerance

## Header

- Branch: `fix/capabilities-bom-tolerance`
- Classification: `quick-win`
- Classified by: `claude-opus-4-8`
- Frozen: `2026-06-20`
- Created Date: `2026-06-20`
- Owner: `session-37355664`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Checkpoint SHA: `3999e2f`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance/capabilities-validator`
- SSoT Sequence: `81`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-06-20 14:30 UTC`
- Platform: `claude-code`
- Files Read: `0`

---

## Task Description

Make `validate_downstream_capabilities.py` tolerate a leading UTF-8 BOM in `downstream-capabilities.yaml`. A BOM-prefixed save (older Windows Notepad / PowerShell `Out-File` default) made the gate-safety validator fail with a cryptic `unknown top-level key '﻿version'`. Surfaced by the v1.7.0 KB-seam adversarial review (independent reviewer + own failure-angle testing).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-06-20 | quick-win; pre-existing parser-wide wart, fail-safe |
| plan | done | 2026-06-20 | 1-char read encoding utf-8 → utf-8-sig + 2 tests |
| implement | done | 2026-06-20 | validator line 303 + 2 BOM tests |
| test | done | 2026-06-20 | 47 capability tests pass (45 + 2 new); empirical repro fixed |
| ship | in-progress | 2026-06-20 | PR + merge |

---

## Phase Summary

- **plan/implement**: Root cause = `path.read_text(encoding="utf-8")` keeps a leading BOM, which attaches to the first YAML key (`﻿version`) → the allowlist rejects it as "unknown top-level key". Fix = read with `utf-8-sig` (strips a leading BOM; identical for non-BOM files). Fail-closed posture unchanged.
- **test**: Added `test_utf8_bom_is_tolerated` (BOM + valid → pass) and `test_utf8_bom_does_not_smuggle_gate_relaxation` (BOM + `role: authority` → still REJECT, no fail-open). Empirical: BOM+valid exit 0, BOM+evil exit 1.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T22:30:00+08:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T22:33:00+08:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T22:38:00+08:00
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T22:42:00+08:00
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T22:45:00+08:00

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | the v1.7.0 seam whose review surfaced this |

---

## Known Risk

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

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

## Evidence

- Empirical: BOM+valid `exit=0`; BOM+`role: authority` `exit=1` (no fail-open).
- `pytest tests/guard/test_capabilities_schema_gate_safety.py` → 47 passed.
- Parser-wide pre-existing (skills: rejected identically before the fix); not a v1.7.0 regression.
