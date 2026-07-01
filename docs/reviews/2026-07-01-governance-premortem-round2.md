# Governance Premortem Round 2 — 2026-07-01

Scope: second-pass governance premortem for Agentic OS, focused on closure mechanics rather than first-pass detection.

Method: adversarially re-read the previous premortem, the stale review snapshot that triggered the new validator warning, the document-governance L1/L2 contract, and the validator tests. This pass asked: "What if the governance system detects a problem but never metabolizes it?"

## Validator Story

The first-pass PR added a validator WARN for stale pending `routing_actions`. That made the old `docs/reviews/2026-06-16-audit.md` actions visible, but visibility alone was not closure.

Red test:
- Command: `python -m pytest tests/ci/test_validator_false_positives.py::test_framework_has_no_stale_pending_routing_actions_warn -q`
- Result: failed, because framework validation still emitted `stale pending routing_actions need canonical-doc follow-up: 1`.

## Premortem Findings

### P1 — Alarm without metabolism

Failure story: the validator becomes excellent at announcing stale review actions, but the project still leaves old findings in temporal snapshots instead of routing them into canonical document-governance history.

Evidence:
- `docs/reviews/2026-06-16-audit.md` still had three `status: pending` routing actions after the first-pass validator fix.
- `docs/architecture/document-governance.md` says review snapshots are not design authority; significant findings must route to canonical docs.

Resolution:
- Appended the three durable decisions to `docs/architecture/document-governance.log.md`.
- Transitioned the old audit actions from `pending` to `merged`.
- Added a regression test that fails if the framework repo itself carries a stale pending routing-action WARN.

### P1 — Same-day audits need identity, not just date

Failure story: "run another audit today" overwrites or blurs `docs/reviews/<date>-audit.md`, so the second pass weakens temporal traceability instead of strengthening it.

Evidence:
- The 2026-06-16 audit already identified same-day filename collision risk.
- This second-pass report intentionally uses `2026-07-01-governance-premortem-round2.md` rather than replacing the first 2026-07-01 premortem.

Resolution:
- Added a document-governance L2 decision requiring scope-qualified audit/review snapshot names for repeated same-day runs.

### P2 — Support evidence can impersonate phase evidence

Failure story: an optional `/audit` Work Log records useful support evidence, then later tooling or a human mistakes it for a normal phase gate receipt.

Evidence:
- The 2026-06-16 audit found ambiguity between audit support traces and normal gate progression.
- The state machine treats `/audit` as report-only; support evidence must not imply `/plan` or `/ship` advancement.

Resolution:
- Added a document-governance L2 decision that audit-created Work Logs are support traces only.

### P2 — Blast-radius previews lose meaning when paths collapse

Failure story: a deploy dry-run tells the operator a file named `rules.md` will change, but hides which target path owns that basename; the human cannot assess blast radius.

Evidence:
- The 2026-06-16 audit found deploy dry-run basename-only output.
- Post-fix notes in that audit say the deploy dry-run was updated to print target-relative paths and tier labels.

Resolution:
- Added the durable document-governance constraint that governance-grade previews must preserve target-relative paths.

## routing_actions

```yaml
routing_actions:
  - finding: "Stale review routing_actions must be closed by canonical-doc merge/reject, not only validator visibility."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "codex-session"
```
