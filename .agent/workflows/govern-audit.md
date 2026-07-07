---
name: govern-audit
description: Audit the governance system itself — gates, validators, docs, wiring — with verified findings and routed dispositions.
tasks:
  - govern-audit
---

# /govern-audit

> Purpose: a repeatable self-audit of the GOVERNANCE SYSTEM (AGENTS.md, rules,
> workflows, validators, CI wiring, eval coverage, templates) — find loopholes,
> contract drift, and enforcement gaps, and route every surviving finding to a
> disposition. For mapping a legacy/project codebase, use `/audit` instead.

## Environment Constraints

- **NO GATE**: bypasses all Gate Engine checks (report-only diagnostic phase).
- **NO CODE MODIFICATION**: read-only for all governance sources. Fixes this
  audit motivates go through the normal classified flow afterwards.
- **PERMITTED WRITES (exhaustive)**: the report snapshot, its `routing_actions`
  block, and backlog intake rows in `docs/specs/_product-backlog.md`.
- **ROUTE FINDINGS**: a lasting finding left only in the snapshot is a
  governance defect (same AC-29/AC-31 semantics as `/audit`).

## Workflow Execution Steps

1. **Baseline first (dedup against the known)**: run the validator
   (`validate.sh` / `validate.ps1`) for the current PASS/WARN/FAIL baseline;
   read prior governance snapshots in `docs/reviews/` and the open governance
   rows in `docs/specs/_product-backlog.md`; list the SSoT `## Global Lessons`.
   Build an ALREADY-KNOWN list — known findings are excluded from the report
   (cite the tracking row instead of re-reporting).
2. **Sweep** (single-agent or fan-out — subagents are optional acceleration,
   never a dependency): pick dimensions by staleness/risk, e.g. gate-bypass
   paths, MUST-rule enforcement coverage (rule ↔ validator/test/eval), sh↔ps1
   validator parity, CI gating blindness, always-loaded token cost, cross-doc
   contract drift, eval oracle quality, deploy/downstream propagation.
3. **Verify before report (findings are hypotheses)**: every finding — from a
   subagent, a heuristic, or a hunch — MUST be verified against the actual code
   path (read BOTH cited sides) before it may appear in the report. Same-vendor
   subagent findings have a documented high false-alarm rate ([audit-verification]
   Global Lesson); a dropped false alarm is recorded with its refutation.
4. **Disposition funnel (no "deferred")**: every surviving finding resolves to
   exactly ONE of: **do-now** (fix in a follow-up classified task), **backlog**
   (add a `_product-backlog.md` row in this run), or **close-with-reason**
   (working-as-intended / cosmetic / net-add-without-incident — reason recorded
   in the report). A "deferred" or "future direction" disposition is prohibited.
5. **External-signal caveat**: architecture-level conclusions require at least
   one external signal — a different-vendor model, a published external source,
   or human review — OR the report MUST label them `same-vendor-only`
   ([audit-method] Global Lesson).
6. **Report**: write `docs/reviews/<YYYY-MM-DD>-govern-audit[-<scope>].md` —
   the `-<scope>` qualifier is MANDATORY when a governance snapshot for the same
   date already exists (document-governance L2 decision). Include: validator
   baseline, already-known list, verified findings by disposition, dropped
   false alarms with refutations, and the `routing_actions` block:

   ```yaml
   routing_actions:
     - finding: "<1-line summary>"
       target_doc: "docs/architecture/<domain>.md"
       status: pending
       owner: "<session-id or 'unassigned'>"
   ```

   Each `target_doc` MUST point to a canonical Domain Doc or spec — never to the
   snapshot itself. Snapshots are temporal records, not design authority.

## Expected Output Format

Chat response is the compact block below; full detail lives in the report file.

```
Baseline: validate <pass/warn/fail> · <N> known findings excluded
Findings: <N> verified (<A> do-now · <B> backlog · <C> closed) · <D> false alarms dropped
routing_actions: <N> pending
Report: docs/reviews/<date>-govern-audit[-<scope>].md
Next: <follow-up recommendation or "none">
⚡ ACX
```
