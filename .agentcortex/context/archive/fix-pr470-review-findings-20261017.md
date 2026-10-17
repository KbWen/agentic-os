# Work Log: fix/pr470-review-findings

## Header

- Branch: `fix/pr470-review-findings`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `2026-10-17`
- Created Date: `2026-10-17`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `77a000e`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `199`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-17 14:34 UTC` (8ab306f9)
- Platform: `claude-code`

---

## Task Description

Fix the verified findings of the independent PR #470 review (owner asked for an independent review after #218/#121). Docs/governance reviewer findings are applied here; code-reviewer findings (deploy/validators) are added when that report lands.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-17 | quick-win |
| plan | done | 2026-10-17 | one fix per verified finding |
| implement | done | 2026-10-17 | 10 docs + 5 code findings |
| review | done | 2026-10-17 | mutants per fix |
| test | done | 2026-10-17 | 514 passed |
| ship | done | 2026-10-17 | SSoT 199->200 |

---

## Phase Summary

- bootstrap: quick-win. Each reviewer finding re-verified by me before acting (subagent self-reports are not ground truth): H1 confirmed (deploy.sh downstream ignore block gitignores `.agentcortex/context/work/*.md`; installer says "work-log discipline stays local"); M2 confirmed (validate.sh:1754 / ps1:1689 grep only the heading; template ships it); M3 confirmed (#230 test receipt 12:04:30Z > ship 11:52:09Z); M4 confirmed by reading ADR-009 §2 rung (2) + guide; L8 confirmed (`backlog spec links` WARN still raised, #201 cites the spec).
- plan / implement (docs/governance): H1 — README EN+zh-TW: phase/evidence row says it runs locally (hook or by hand) and CI never sees gitignored work logs; floor paragraph says what a required CI job can enforce (credential scan, your tests, structural checks); "How do I stop" FAQ splits CI vs local hook. M2 — removed the "validate.sh also fails a feature with no recorded test results" claim; new backlog row #233 for the heading-only check (not fixed here). M3 — #230 archived log test receipt corrected to 11:51:50Z with a dated correction note. M4 — `kb-consult` lookup reverted to the original "query `task_routing` (not the whole manifest/index)"; routed-order change kept; "a bounded pass keeps only" restored (row now −18 chars vs v1.8.33); archived #218 row gets a dated correction. L5 — standing notes gain #78's reopen preconditions and the 2026-07-06 unverified-claims watch-item. L6 — "(this file)" → "(this file or the archive)"; archive header note says the legacy table keeps its 9-column header. L7 — #232 stats recomputed (89 Pending, 82,244 chars, median 693). L8 — corrected in the #230 log note. ⚡ ACX FAQ nit: "a work log's Phase Summary" → "a work log".
- implement (code reviewer, each re-verified): C1 — `_cp_framework_version` took a real cp failure under `-n`/`-i` for a skip ([KEPT], rc 0): now a nonzero cp is "kept" only when dst is still writable and unchanged from its pre-copy hash (new 5th arg); else it exits with cp's status. The reviewer's "unchanged hash" alone could not tell a permission error from a decline. C2 — reproduced: without PyYAML, `_yaml_loader` resolved an inline-commented / header-commented / BOM config to the default, so an unsafe retargeted file PASSed; `configured_path` now uses its own fixed-grammar reader (`_configured_value`), same result on every host, and a flow mapping / tab indent / repeated key raises → exit 2. C3 — `.gitkeep.md` copy tolerates a nonzero cp only under `-n`/`-i`; default path fails again (rc 1, verified by hand). C4 — `-n` test now also asserts the kept skill files update with no sidecar on the next default deploy. C5 — `chmod +x` failure inside the helper exits. Two literal U+FEFF characters I had typed were replaced with `﻿` escapes.
- Not changed: L9 (#165 ship narrative dropped by 6b6cc02 — survives in its spec and archived log); L10 (already disclosed in the #218 log); watch-item (d) "features frozen until conversion signal" vs the 2026-10-15 queue — owner call.
- review: every fix has a mutant that its test kills: R1 failed-copy-reads-as-kept → 2 failed; R4 scaffold kept records src hash → 2 failed; R2 no inline-comment strip → 1 failed; R2 no BOM strip → 4 failed; R2 flow mapping accepted → 1 failed. Residual: under coreutils >= 9.2, `-n` on a read-only `.gitkeep.md` now stops the deploy (rare; placeholder only).
- test: see Evidence. ship: PASS; SSoT 199->200; the Ship History entry records the corrections to the #190, #218 and #121 entries (old entries are never edited).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:34:09Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:35:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:55:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T15:00:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T15:19:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T15:20:54Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog.md | rows #232, #233 |
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | M4 |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/470 | review target |

---

## Known Risk

- Archived Work Logs are edited only to correct verified factual errors, each with a dated correction line.

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

- README/bootstrap/backlog edits started before this log was written (14:34–14:45Z); receipts written after; implement/review/test timestamps reconstructed from the session timeline, ordered and before the ship clock read.

---

## Review Feedback

- Docs/governance reviewer: H1 fixed; M2 claim removed + #233; M3 fixed; M4 fixed (revert); L5–L8 fixed; L9/L10 no change (see Phase Summary).
- Code reviewer: C1–C5 fixed (see Phase Summary).

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

- After docs/governance fixes: validate.sh `pass=116 warn=5 fail=0 skip=2` (both README encoding canaries PASS); validate.ps1 identical; `pytest tests/ci/ -m docs_pin` 12 passed; lifecycle ceiling + drift + directive ratchet 56 passed; lifecycle aggregate 354,684.
- Code fixes: `pytest tests/guard/test_capabilities_schema_gate_safety.py` 61 passed with PyYAML and 61 passed with PyYAML blocked (`PYTHONPATH` → a `yaml.py` that raises ImportError); `test_deploy_tiering.py -k cp_flag` 15 passed; under the coreutils-9.2 `cp` shim `-k "brownfield or cp_flag"` 23 passed.
- Default-path `.gitkeep.md`: read-only placeholder → default deploy rc=1 with `Permission denied` (as at b1a3b83); `CP_FLAG=-n` rc=0.
- Regression: `pytest -n auto` deploy_tiering + dry_run_read_only + install_day_copy + validator_false_positives + tests/guard → 514 passed, 2 skipped; validate.sh `pass=116 warn=5 fail=0 skip=2`; validate.ps1 identical.
