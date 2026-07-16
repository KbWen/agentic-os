# Work Log: chore/orphan-decision-homes

## Header

- Branch: `chore/orphan-decision-homes`
- Classification: `quick-win`
- Classified by: `claude-fable-5`
- Frozen: `2026-07-16`
- Created Date: `2026-07-16`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `935381b`
- Checkpoint SHA: `935381b`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `122`

---

## Session Info

> Written by /bootstrap. Update on each new session.

- Agent: `claude-fable-5`
- Session: `2026-07-16 13:56 UTC`
- Platform: `claude-code`
- Files Read: `12`

---

## Task Description

Backlog **#139** (from the 2026-07-16 decision-capture govern-audit): give durable canonical homes to product decisions currently recorded only on rotating/temporal surfaces — (a) the 2026-07-08 `design_tool`/ADR-011 unanimous rejection (ADR-001 D2 amendment + L2 pointer entry) before Ship History cap-10 rotation ejects it (~4 ships), (b) the SSoT-caps decision cluster (PR #328) and the point-in-time archival precedent (both → L2 `document-governance.log.md` entries).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-16T13:55Z | classification frozen: quick-win |
| plan | done | 2026-07-16T13:56Z | gate PASS; plan below |
| implement | done | 2026-07-16T14:00Z | opus draft; primary verified diff line-by-line vs sources |
| review | done | 2026-07-16T14:26Z | 第十人 (8 findings, 0 blocking) + 事前驗屍 (8 paths, 6 fold-ins); all adjudicated, 8 text edits applied |
| test | done | 2026-07-16T14:26Z | validate.sh pass=113 warn=4 fail=0 (= baseline); pytest 622 passed |
| handoff | skipped | — | exempt (quick-win) |
| ship | done | 2026-07-16T14:31Z | SSoT 5-edit update + rotation; gated annotation grep PASS |

---

## Phase Summary

- bootstrap: classification quick-win (doc-governance record work, 2 content files + ship-time SSoT/backlog bookkeeping; no engine/validator change). Context: SSoT read at session start; shared-contracts.md loaded; audit report docs/reviews/2026-07-16-govern-audit-decision-capture.md is the source finding (F2). Branch created off 935381b; single-writer lock acquired (created, exit 0).
- plan: gate PASS. Plan: (1) ADR-001 D2 amendment recording the design_tool rejection per ADR-001's own 2026-06-11 amendment precedent; (2) one append-only entry in document-governance.log.md covering the 3 orphaned decision clusters (design_tool pointer / SSoT-caps cluster / point-in-time precedent); (3) adversarial passes; (4) validate + pytest; (5) ship. ⚡ ACX
- implement: opus subagent drafted both artifacts under a strict source-fidelity contract (verification table returned; it corrected the SSoT's loose "#119" to the real PR #324 and confirmed the PR #315 point-in-time instance in archive/ship-history-2026.md). Primary re-verified the full diff line-by-line against the roundtable record, ADR-001 D2, SSoT ship entries, ship.md:208, and config.yaml. Pure append confirmed on L2 (0 deletions). One flagged inference (WARN-tier downstream rationale) carried to review.
- review: 第十人 (refute-only) — 0 ship-blocking; hard facts all verified (PR #324, allowlist docstring exact, ship.md:208 exact); findings F-1 (origin over-attribution), F-4 (rotating-only imprecise), F-5 (cosmetic + inference provenance), F-6 (5-seat ambiguity), F-7 (retry-freeze wording) ADOPTED as 8 text edits; F-2 (2/3 clusters L2-only = permanence-not-discoverability) + F-8 (L2 over restructure threshold, pre-existing) closed-with-reason. 事前驗屍 — fold-ins adopted: audit report MUST be committed in this PR; ship-time SSoT ADR Index annotation is the sole always-loaded carrier → post-write grep verify gated in ship checklist; frontmatter amended: 2026-07-16 (ADR-003 precedent verified); no-overclaim wording at ship (#139 = instance-batch, #138 systemic hole stays OPEN). Residual risk MEDIUM by design — a discoverability fix, not an enforcement gate (enforcement = #138). Also: full pytest caught a routing_actions schema violation in the audit report itself (target_doc pointed at docs/adr/ — not an allowed canonical target); fixed to docs/architecture/document-governance.md; tests/guard/test_routing_actions_check.py 12/12 green after.
- test: final post-adjudication tree — full CI-equiv pytest **622 passed** (98 deselected); validate.sh **pass=113 warn=4 fail=0 skip=2**, identical to the clean-main baseline recorded in the audit report. No new warn/fail introduced by the diff.
- ship: PASS — SSoT sequence 122→123 via 4 surgical anchored Edits (ADR Index do-NOT-retry annotation [gated grep=1], Ship History top-insert, v1.8.8 cap-10 rotation to archive/ship-history-2026.md [SSoT=0/archive=1, count=10], heartbeat); backlog #139 → Shipped (instance-batch only, #138 stays OPEN); audit-report design_tool routing_action → merged; Work Log archived to .agentcortex/context/archive/chore-orphan-decision-homes-20260716.md with hash-chained INDEX.jsonl entry (decisions field populated — dogfooding the audit's own finding); lock released. Commit SHA recorded in PR. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-16T13:55:56Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-16T13:56:53Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-16T14:10:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-16T14:26:15Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-16T14:29:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-16T14:31:06Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | quick-win: no spec (spec_exists: na) |
| ADR | docs/adr/ADR-001-governance-friction-tuning.md | D2 amendment target; 2026-06-11 amendment is the format precedent |
| Review | docs/reviews/2026-07-08-design-gate-roundtable.md | source of truth for the rejection content |
| Review | docs/reviews/2026-07-16-govern-audit-decision-capture.md | originating audit (finding F2) |
| Backlog | docs/specs/_product-backlog.md #139 | this task; flip to Shipped at /ship |
| L2 | docs/architecture/document-governance.log.md | append-only target |

---

## Known Risk

- Content-fidelity drift between the amendment/L2 text and the source records (roundtable review, PR #328 ship entry, archive origin). Mitigation: implementer must verify every factual token against the named source; primary re-verifies the diff line-by-line; 第十人 + 事前驗屍 passes before commit. Rollback: revert the branch (single PR; docs-only).
- L2 is append-only — any edit to existing entries is a defect. Mitigation: diff must show pure append after the 2026-07-11 entry.
- Ship-time SSoT edits (ADR Index amendment note + Ship History entry + heartbeat) go through guard_context_write.py; backlog #139 status flip is a ship-step exception per AGENTS.md.

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Direct writes to docs/adr/ADR-001*.md and docs/architecture/document-governance.log.md are the task deliverable (classified quick-win flow), not SSoT writes; SSoT/current_state.md writes happen only at /ship via guard_context_write.py.
- Ship SSoT update executed as surgical anchored Edits per ship.md §2 explicit alternative ("or a surgical anchored Edit") instead of guard_context_write.py --mode replace: 4 disjoint section edits (ADR Index line, Ship History top-insert, v1.8.8 rotation removal, heartbeat), sole session, lock held, post-write gated verification recorded in ## Evidence.
- Mid-flow fix on own artifact: full pytest caught a routing_actions schema violation in docs/reviews/2026-07-16-govern-audit-decision-capture.md (target_doc pointed at docs/adr/ — outside the docs/architecture|specs canonical-target schema of check_routing_actions.py). Fixed to docs/architecture/document-governance.md; tests/guard/test_routing_actions_check.py 12/12 green after.

---

## Review Feedback

Verdict: PASS (0 blocking). Adjudication of 第十人 F-1/F-4/F-5/F-6/F-7 + 事前驗屍 fold-ins 3/4/5 → 8 text edits applied same-session (provenance marker on the reconstructed WARN-tier rationale, "documented instance" framing for PR #315, un-metabolized-snapshot precision, 5-seat roundtable wording, supersedable do-not-retry, record-only heading, frontmatter amended:). Closed-with-reason: F-2 (L2 permanence-only for the 2 low-re-derivation clusters — audit F3 already closed L2-by-design), F-8 (L2 restructure threshold pre-existing → /govern-docs territory).

---

## Red Team Findings

- 事前驗屍 #1 (MED): the sole always-loaded carrier for the design_tool rejection is the ship-time SSoT ADR Index annotation, and NO validator enforces it (check_adr_coverage.py is path-presence only). Risk decision: gate THIS task's ship on a post-write `grep "amended 2026-07-16" current_state.md` verify recorded in Evidence; a machine gate is #138's scope, not this quick-win's.
- 事前驗屍 #3 (MED): #139 landing must not defuse #138 — recorded in ship wording ("instance-batch only; systemic hole OPEN"); backlog keeps #138 Pending with the audit report as provenance.

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

- implement: `git diff --stat` = ADR-001 +31 lines / document-governance.log.md +36 lines (pure append, 0 deletions — hunk `@@ -171,3 +171,37 @@` pre-adjudication); primary line-by-line source verification vs roundtable record + SSoT + ship.md:208 + config.yaml.
- test (final tree): `python -m pytest tests/ci tests/guard .agentcortex/tests -m "not slow" -q` → **622 passed, 98 deselected**; `bash .agentcortex/bin/validate.sh` → **pass=113 warn=4 fail=0 skip=2** (identical to clean-main baseline).
- ship gated verify (事前驗屍 must-fix #2): `grep -c "amended 2026-07-16: \`design_tool\`..." current_state.md` = 1; `grep -c '^### Ship-'` = 10 (cap held after rotation); v1.8.8 entry: SSoT=0 / archive=1. All PASS.
- Demonstration: SSoT ADR Index line 19 now carries the always-loaded do-NOT-retry marker; fresh-session read path (bootstrap → current_state.md ADR Index) surfaces the rejection without opening ADR-001.
