# Work Log: feature/validator-fail-open-hardening

## Header

- Branch: `feature/validator-fail-open-hardening`
- Classification: `quick-win`
- Classified by: `claude-opus (WP1 implementer, orchestrator-assigned)`
- Frozen: `2026-07-11`
- Created Date: `2026-07-11`
- Owner: `claude-code-session-wp1`
- Guardrails Mode: `Quick`
- Current Phase: `implement`
- Diff Base SHA: `ba949e4290f829579400e787d36c139bffd792c8`
- Checkpoint SHA: `7890e78`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance-runtime / validators`
- SSoT Sequence: `119`

---

## Session Info

- Agent: `claude-opus-4-8[1m]`
- Session: `2026-07-11 (WP1 of 3-package validator fail-open remediation wave)`
- Platform: `claude-code`
- Files Read: `20`

---

## Task Description

WP1 of the 2026-07-11 govern-audit remediation wave (report: docs/reviews/2026-07-11-govern-audit.md, merged PR #337/#338). Close three verified validator fail-open paths:
- F1: check_command_sync.py validates substring presence, not the dispatch directive.
- F2: missing deploy manifest fail-opens adapter validation (manifest-identity inference).
- F3: routing_actions validation accepts malformed inline maps without validating values.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-11 | orchestrator-assigned classification quick-win |
| plan | done | 2026-07-11 | 3 findings, target files fixed by orchestrator |
| implement | in-progress | 2026-07-11 | F1/F2/F3 |
| ship | pending | — | PR only, no merge |

---

## Phase Summary

- bootstrap: classified quick-win (orchestrator-assigned); scope = 3 verified govern-audit findings + their tests; read SSoT + implement.md + shared-contracts.md + both validators' relevant regions + check_command_sync.py + check_ssot_caps.py (pattern) + ADR-006 + native-check ratchet.
- plan: target files = check_command_sync.py (F1+F2), new check_routing_actions.py (F3), validate.sh + validate.ps1 routing_actions regions (F3 wiring), tests in .agentcortex/tests/test_trigger_metadata_tools.py (F1+F2) + new tests/guard/test_routing_actions_check.py (F3). Key design: F3 hybrid (Python structural check when available + existing native block as no-python backstop) keeps the ADR-006 native-check ratchet neutral (197/198, zero native-line delta).
- implement: commit 7890e78, 6 files. F1 = directive parsing in check_command_sync.py; F2 = manifest-agnostic surface detection (same tool); F3 = new check_routing_actions.py (column-0 canonical block, inline-map/non-list/traversal/status rejection) wired into both validators behind the python seam with native backstop. All three findings closed with tests. No scope divergence (settings.local.json pre-existing, left unstaged).

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | docs/reviews/2026-07-11-govern-audit.md | source findings F1/F2/F3 |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | F3 Python-tool-behind-seam + native ratchet |
| PR | (pending) | non-draft, no merge |

---

## Known Risk

- F3 no-python degraded backstop: when Python is unavailable the native substring/anchor checks still run (weaker; the inline-map bypass is not closed in that reduced-assurance mode). Documented; tracked by backlog #113 (no-Python divergence). Primary assurance (CI + source repo + Python-available devs) is now robust.

---

## Drift Log

- Deviation (test placement): finding F2 suggested `tests/deploy/`, but that dir does not exist and CI collects only `tests/ci tests/guard .agentcortex/tests` (validate.yml). Placing the F2 fixture test with the other command-sync tests in `.agentcortex/tests/test_trigger_metadata_tools.py` so it actually runs in CI.
- Scope decision (F2): fixed at the tool level (check_command_sync.py manifest-agnostic surface detection). The validators already invoke `command sync check` unconditionally (validate.sh:359 / validate.ps1:416, outside the IS_SOURCE_REPO branch), so no IS_SOURCE_REPO change is required to close the demonstrated broken-adapter-green hole. Left the `claude adapter files present` source-mode SKIP untouched (it catches missing files, not drift; green-stays-green risk).

---

## Evidence

- F1: `test_command_sync_rejects_broken_directive_despite_residual_mention` + `_rejects_alias_directive_retarget` → both exit 1 (broken directive with residual prose mention now FAILs).
- F2: `test_command_sync_manifest_deletion_cannot_turn_broken_adapter_green` → exit 1; `_runs_and_passes_without_manifest` → exit 0; source repo now runs the real check (`Command sync check passed (28 commands verified, 2 aliases verified, 30 total)`) instead of self-skipping.
- F3: `tests/guard/test_routing_actions_check.py` 12/12 pass (inline-map, traversal, non-canonical, bad-status, fields-outside-block, non-list → FAIL; valid/nonexistent-target/indented-example → PASS). Real repo: `routing_actions: structurally valid across 7 review file(s)`.
- Full CI-equiv: `pytest tests/ci tests/guard .agentcortex/tests -m "not slow"` → 607 passed. Slow: 2 stale-pending routing_actions tests pass (native backstop in deployed fixtures).
- Validators (before AND after): validate.sh + validate.ps1 both `pass=114 warn=3 fail=0 skip=2` (green, parity, count-neutral). ADR-006 ratchet 197/198 unchanged.

---

## Test Gate Results

- quick-win (review/test optional). CI-equiv 607 passed; both validators fail=0; ratchet green. Command: `pytest tests/ci tests/guard .agentcortex/tests -m "not slow"`.
