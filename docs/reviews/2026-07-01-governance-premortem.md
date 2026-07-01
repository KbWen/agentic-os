# Governance Premortem Audit — 2026-07-01

Scope: Agentic OS governance capability, evaluated as a premortem rather than an implementation review.

Method: read the governance entry points, state machine, audit/review/ship contracts, current SSoT, active Work Log for `main`, existing review snapshots, backlog, lock files, and ran the local PowerShell validator.

Validator snapshot:
- Command: `powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1`
- Result: `pass=105 warn=11 fail=0 skip=2`
- Interpretation: the framework is structurally healthy enough to pass, but the WARN set is itself governance evidence: hygiene debt remains visible without blocking.

## Premortem Findings

### P1 — Green validation can coexist with governance debt

Failure story: a future maintainer sees `fail=0` and treats governance as clean, while warning-level signals keep accumulating until a real phase transition or ship action depends on stale records.

Evidence:
- Validator passed with 11 warnings, including active work log count over limit, work logs missing sentinel markers, shipped work logs still active, stale advisory locks, and 30 MUST-rule sections without eval cases.
- `.agentcortex/context/current_state.md:89` already records the core lesson: self-attested MUST rules are "honor-system theatre" unless backed by a hook, validator, test, or external observer.

Impact: medium-high. The project is honest about residual risk, but the green headline can still create false confidence.

Likely fix direction: split WARNs into (a) hygiene, (b) governance-integrity debt, and (c) reduced-assurance mode; fail only the subset that can invalidate a phase verdict.

### P1 — Pending `routing_actions` can rot outside the current domain

Failure story: audit findings are correctly routed, but never merged into canonical docs because `/ship` only checks pending review actions for the current task's `primary_domain`.

Evidence:
- `docs/reviews/2026-06-16-audit.md:92-107` contains three pending `routing_actions`.
- `docs/specs/_product-backlog.md:66` already records backlog item #97: add staleness escalation for pending routing actions.
- `.agent/workflows/ship.md:186-188` scopes the ship-time check to pending actions targeting the current task's `primary_domain`.

Impact: high for governance learning loops. The audit workflow says leaving lasting findings only in the snapshot is a governance defect, but the current enforcement can miss cross-domain or old findings.

Likely fix direction: implement backlog #97 as a validator WARN/FAIL ladder based on age, severity, or target doc existence.

### P1 — `main` branch Work Log is stale and reusable

Failure story: a new session on `main` derives the worklog key `main`, resumes stale state, and inherits old phase/classification context from a prior task.

Evidence:
- `.agentcortex/context/work/main.md:5-16` says `Branch: main`, `Classification: quick-win`, `Current Phase: implement`, `SSoT Sequence: 68`.
- `.agentcortex/context/current_state.md:15-17` says `Last Updated: 2026-06-30T23:00:00Z` and `Update Sequence: 102`.

Impact: high on repos that work directly on `main`. Branch-derived Work Logs work best with task branches; `main` is a collision magnet.

Likely fix direction: special-case protected/default branches by requiring a session/task suffix, or auto-create `<owner>-main-<date>` unless the user explicitly resumes the existing `main` log.

### P2 — Reduced-assurance platforms weaken the strongest gates

Failure story: the same governance rule is hard-gated in local/direct-file-access environments but becomes manual verification in API-only or no-file-access environments, exactly where the agent is least inspectable.

Evidence:
- `.agent/workflows/ship.md:64-65` makes missing required receipts a hard fail only on direct-file-access platforms; no-file-access platforms paste evidence into chat for manual verification.

Impact: medium-high. This is honest, but it creates a two-tier governance model.

Likely fix direction: make reduced-assurance mode visibly non-equivalent in output, and require an explicit "reduced-assurance ship" label in any ship receipt.

### P2 — Quick-win classification remains the pressure valve

Failure story: a risky governance change gets framed as quick-win to avoid spec/handoff/review overhead, then ships with lighter evidence.

Evidence:
- `AGENTS.md:55-58` exempts quick-win/hotfix from handoff but still requires evidence and valid review semantics.
- `.agent/workflows/ship.md:59-66` only hard-fails missing prior receipts for feature/architecture-change on direct-file platforms; quick-win/hotfix missing receipts are WARN.
- `.agent/workflows/bootstrap.md:31` says reading `engineering_guardrails.md` for quick-win is a Token Leak violation except for governance-path §13, while `AGENTS.md:13-14` says engineering/security guardrails are MUST OBEY. The intended optimization is understandable, but it is easy for agents to misread.

Impact: medium-high. The project has escalation rules, but classification still carries large governance consequences.

Likely fix direction: add a small "quick-win risk reconciliation" check before ship when changed paths are governance, deploy, validator, or trust-boundary adjacent.

### P2 — Advisory checks cover production-critical concerns

Failure story: a feature ships with weak rollback telemetry, missing spec-test links, or incomplete observability because the checks warn but do not fail.

Evidence:
- `.agent/workflows/ship.md:53-55` rollback plan check applies only to feature/architecture-change and is advisory.
- `.agent/workflows/ship.md:97-120` observability and spec-test traceability checks are advisory.

Impact: medium. Advisory is appropriate during rollout, but production-readiness can become ritual if no escalation path exists.

Likely fix direction: graduate advisory checks based on domain severity, e.g. auth, deploy, migration, data-loss, or public API changes.

### P2 — Lock enforcement degrades in no-Python environments

Failure story: a downstream environment without Python loses blocking lock behavior and falls back to manual advisory handling; concurrent agents then write divergent Work Logs.

Evidence:
- `.agent/workflows/shared-contracts.md:30-36` documents blocking behavior with Python, but says no-Python fallback degrades to manual advisory.
- Current local validator observed two stale advisory Work Log locks.

Impact: medium. The project states the limitation honestly, but no-Python downstream is a supported posture.

Likely fix direction: provide a tiny native lock verifier in both shell and PowerShell, or make no-Python lock degradation a loud reduced-assurance mode.

### P3 — Eval coverage is broad but still incomplete

Failure story: new MUST-bearing sections are added faster than eval cases, so humans believe the behavioral harness protects more than it does.

Evidence:
- Validator warning: `governance eval coverage: 30 MUST-rule section(s) without eval cases`.
- `.agentcortex/eval/governance.yaml:95-105` includes a sentinel omission case, proving the harness exists and catches some instruction-following failures.

Impact: medium. The harness is real, but the uncovered inventory needs prioritization.

Likely fix direction: prioritize eval coverage by blast radius rather than count: destructive actions, SSoT writes, ship gate, secret leakage, lock takeover, external tool output.

## Lens Summary

- Agent honesty lens: strong culture, but too many duties still depend on self-reporting.
- Operator lens: `fail=0` is comforting, but WARN taxonomy is not sharp enough to convey operational risk.
- Downstream lens: reduced-assurance paths are documented but can still feel equivalent to full governance.
- Collaboration lens: branch-keyed Work Logs are fragile on shared/default branches.
- Learning-loop lens: routing actions and backlog items can preserve findings without forcing closure.
- Review lens: same-vendor/fresh-context caveats are understood, but external signal remains mostly process-bound.

## routing_actions

```yaml
routing_actions:
  - finding: "Pending routing_actions need age/severity escalation instead of only current-domain ship checks."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "codex-session"
  - finding: "Default/protected branch Work Logs need collision-resistant session keys or explicit resume confirmation."
    target_doc: "docs/architecture/document-governance.md"
    status: pending
    owner: "codex-session"
  - finding: "Reduced-assurance environments need explicit receipt labeling for ship/gate claims."
    target_doc: "docs/architecture/document-governance.md"
    status: pending
    owner: "codex-session"
  - finding: "Quick-win governance/deploy/trust-boundary changes need a ship-time risk reconciliation check."
    target_doc: "docs/architecture/document-governance.md"
    status: pending
    owner: "codex-session"
  - finding: "Validator WARN taxonomy should distinguish hygiene from governance-integrity debt."
    target_doc: "docs/architecture/document-governance.md"
    status: pending
    owner: "codex-session"
```
