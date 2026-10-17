# Work Log: fix/validator-cap-path-190

## Header

- Branch: `fix/validator-cap-path-190`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `2026-10-17`
- Created Date: `2026-10-17`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `4d7425f`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `195`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-17 12:59 UTC` (8ab306f9)
- Platform: `claude-code`

---

## Task Description

Backlog #190: both validator twins hardcode `.agentcortex/context/private/downstream-capabilities.yaml`, ignoring `.agent/config.yaml §downstream_capabilities.path`, so a retargeted unsafe capabilities file passes the ADR-007 gate-safety check. Resolve the configured path. Stacked on PR #470 (owner chose "do it here", 2026-10-17 chat).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-17 | quick-win per backlog Tier |
| plan | done | 2026-10-17 | inline plan below |
| implement | done | 2026-10-17 | tool --root mode + 2 call sites |
| review | done | 2026-10-17 | self-review + pre-mortem |
| test | done | 2026-10-17 | 457 passed |
| ship | done | 2026-10-17 | SSoT 195->196; #190 row archived |

---

## Phase Summary

- bootstrap: quick-win (path resolution in one Python tool + two wrapper call sites; caps unchanged). Reproduced on 4d7425f in a deployed fixture: `path:` → `caps/team-capabilities.yaml` holding `skills: [{id: review}]` → `[PASS] downstream-capabilities gate-safety` on validate.sh and validate.ps1.
- plan: Per ADR-006, the resolution lives in `validate_downstream_capabilities.py`: new `--root <repo>` mode reads `downstream_capabilities.path` from `<root>/.agent/config.yaml` through the shared `_yaml_loader` (config only; the capabilities file keeps the strict parser), relative paths resolve against root, absent/empty key → today's default. Positional `<file>` form unchanged (back-compat). Both twins call `--root`, so parity holds by construction. Tests: tool-level (default, retargeted unsafe → exit 1, retargeted absent → inert, key absent → default) + both twins end-to-end on a deployed fixture, mutation-checked. Rollback: revert the commit.
- implement: `validate_downstream_capabilities.py` gains `configured_path(root)` and a `--root <repo>` CLI form; an exception while resolving → exit 2 (fail closed: we cannot tell which file the agent reads). `validate.sh` (`--root "$ROOT"`) and `validate.ps1` (`@('--root', $root)`, the file's existing convention; BOM `ef bb bf` kept, LF) drop the hardcoded path. Tests: 7 tool-level cases in `tests/guard/test_capabilities_schema_gate_safety.py` (plain/double/single-quoted retarget, retargeted-absent inert with a stale unsafe default, three fallback shapes) + `test_190_validators_check_the_configured_capabilities_path[sh|ps1]` (deployed fixture: unsafe → FAIL, safe → PASS).
- review: Pre-mortem: (1) absolute or `../` paths resolve to the same file bootstrap §1b reads, so the check follows the agent, not a guess. (2) `_yaml_loader` parses only the framework config; the capabilities file still goes through `parse_strict`. (3) No-python path unchanged (WARN). (4) Positional `<file>` form kept for any caller outside the two twins. (5) Deploy ships tool + both validators together (all core), so no mixed old-wrapper/new-tool state from a normal upgrade. (6) bootstrap.md/config.yaml already describe this key; no doc change needed. Verdict PASS.
- test: validator + guard suites (`test_validator_false_positives`, `test_validator_absent_tool_signal`, `test_ci_hardening`, `tests/guard/`, `test_deploy_manifest_snapshot`) 457 passed.
- ship: PASS; #190 Shipped and its row moved to the archive's 10-column section; queue starts at #218; SSoT 195->196, Ship History rotated; archive `fix-validator-cap-path-190-20261017.md`; pushed to PR #470.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T12:59:50Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:02:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:10:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:15:08Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:16:20Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:16:36Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog.md | row #190 |
| ADR | docs/adr/ADR-007-downstream-capability-declaration-seam.md | invariant restored |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/470 | stacked |

---

## Known Risk

- `_yaml_loader` is lenient; it parses only the framework-owned config here, never the capabilities file.

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

- Plan, implement and test receipt timestamps reconstructed from the session timeline, not read from the clock at phase end.
- Lock `ensure` for implement/review run at review time (late).

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

- Baseline repro (4d7425f, deployed fixture, retargeted unsafe file): validate.sh `[PASS] downstream-capabilities gate-safety`, `Summary: pass=84 warn=2 fail=0 skip=9`; validate.ps1 identical.
- After fix, same repro: both twins `[FAIL] downstream-capabilities gate-safety`, `fail=1`.
- New tests: tool-level 54 passed (file total); `-k test_190` 2 passed (sh, ps1).
- Isolated mutants: A sh back to hardcoded → 1 failed; B ps1 back to hardcoded → 1 failed; C tool ignores config → 4 failed (3 fallback cases pass, as expected). Restored byte-for-byte, BOM intact.
- Repo: validate.sh `pass=116 warn=6 fail=0 skip=2` (+1 WARN = lock/header phase mismatch mid-phase); validate.ps1 identical.
- `pytest -n auto` validator + guard suites → 457 passed in 571s.
