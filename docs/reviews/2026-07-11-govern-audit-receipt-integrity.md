# Governance Self-Audit — Receipt Integrity — 2026-07-11

Scope: four Codex-led adversarial rounds over Work Log receipt semantics,
evidence anchors, classification consistency, and cross-platform current-branch
detection. Every candidate started as a hypothesis and was either reproduced,
downgraded after a counterargument, deduplicated, or dropped.

External-signal status: `same-vendor-only`. This is an audit-only snapshot; the
actual patch is handed to Claude after this pull request, then independently
reviewed by Codex or a human.

## Validator Baseline

- Command: `.agentcortex/bin/validate.ps1`
- Result: `pass=98 warn=3 fail=0 skip=2`
- The three warnings are already known: historical gate gaps, one malformed
  archived receipt, and 28 MUST-bearing sections without eval coverage.

## Already Known and Excluded

- Backlog #108 already tracks incomplete evidence stanza parsing.
- Backlog #109 already tracks post-implementation reclassification timing.
- Backlog #114 already tracks invisible `tiny-fix` self-labeling.
- Backlog #122 already tracks unenforced lock acquisition and honor-system MUSTs;
  missing Owner/no-lock hypotheses are not repeated.
- Draft PR #337 already tracks adapter, `routing_actions`, external-executor
  timeout, dirty-worktree, and executor-provenance defects.

## Round 1 — Receipt Time Semantics

### P3 — Gate receipts can omit or forge Timestamp without any signal

The receipt contract requires `Timestamp: <ISO>`, but both validators define a
valid receipt as one containing only Gate, Verdict, and Classification. A full
feature lifecycle with every Timestamp omitted still passed progression and
schema checks.

Evidence:

- `.agentcortex/templates/worklog.md` defines Timestamp as part of the mandatory
  receipt format.
- `.agentcortex/bin/validate.sh:1776-1804` checks Verdict and Classification only.
- `.agentcortex/bin/validate.ps1:1638-1663` mirrors that reduced schema.
- Isolated feature/ship fixture with seven timestamp-free PASS receipts returned
  `pass=113 warn=4 fail=0 skip=2`; the extra warning was only the expected active
  shipped-log hygiene warning.

Counterargument tested: missing timestamps do not directly reorder or bypass
gates because progression follows receipt file order. Severity is therefore P3,
not a blocking gate-bypass finding.

Required fix: require parseable ISO timestamps and monotonic nondecreasing order,
or explicitly remove Timestamp from the claimed receipt contract if chronology
is intentionally non-authoritative.

## Round 2 — Evidence Anchor Validity

### P2 — Diff Base and Checkpoint SHA fields are presence-only placeholders

Both validators report success when the fields exist, even if their values are
not Git object IDs and do not resolve. The same fixture used `not-a-sha` and
`also-not-a-sha`; validation still printed `all active work logs have Checkpoint
SHA field` and finished with fail=0.

Evidence:

- `.agentcortex/bin/validate.sh:1236-1238,1690-1693` checks only the Checkpoint
  field heading.
- `.agentcortex/bin/validate.ps1:1249,1559-1562` mirrors the presence-only check.
- No validator check was found for Diff Base SHA value or resolvability.
- Running `lint_spec_drift.py --base not-a-sha --head HEAD` exited 2 with Git's
  `fatal: ambiguous argument 'not-a-sha'`, proving the downstream review check
  cannot consume the accepted anchor.

Counterargument tested: the review linter is advisory and Burden of Proof can be
constructed from other evidence, so this is not a guaranteed ship bypass.
Nevertheless, immutable diff scope and resume reproducibility are lost.

Required fix: once implementation has begun, require both anchors to match the
expected SHA shape and resolve via `git rev-parse --verify <sha>^{commit}`. Permit
`none` only in phases where the workflow explicitly allows it.

## Round 3 — Receipt Classification Consistency

### P3 — Receipt Classification is never compared with the Work Log header

A Work Log whose header says `feature` accepted seven receipts that all claimed
`Classification: tiny-fix`. The parser used the header to demand the full feature
sequence, but separately declared every receipt structurally valid.

Evidence:

- `.agentcortex/bin/validate.sh:1310-1500` derives required transitions from the
  Work Log header and never binds each receipt's Classification field to it.
- `.agentcortex/bin/validate.ps1:1227-1449` has the same split authority model.
- The isolated contradictory fixture passed both progression and receipt-schema
  checks with fail=0.

Counterargument tested: changing only receipt Classification cannot shed feature
gates because completeness is header-driven. Severity is P3 audit inconsistency,
not classification bypass; backlog #109 remains the real timing-bypass item.

Required fix: reject any receipt whose Classification differs from the active
header classification, except across an explicitly structured reclassification
reset where pre-reset and post-reset epochs are distinguishable.

## Round 4 — Cross-Platform Current-Branch Detection

### P1 — Bash does not apply the canonical lowercase Work Log key algorithm

Bootstrap requires lowercase normalized Work Log filenames. The bash validator
only replaces `/` with `-` and then performs a case-sensitive comparison. On an
uppercase Git branch, the canonical lowercase current Work Log is treated as a
historical log, downgrading current-branch-only Resume/Test Gate failures from
FAIL to WARN. PowerShell masks the defect because its string comparison is
case-insensitive.

Evidence:

- `.agent/workflows/bootstrap.md:123-131` defines replace, collapse, trim,
  lowercase, and 100-character truncation as the canonical algorithm.
- `.agentcortex/bin/validate.sh:1117-1127,1213-1219` performs slash replacement
  only and compares case-sensitively.
- `.agentcortex/bin/validate.ps1:1200-1224` also omits the canonical algorithm,
  but `-eq`/`-like` happen to be case-insensitive.
- Minimal real-shell reproduction for branch `Feat/ReceiptAudit` and canonical
  file `feat-receiptaudit.md`: Git Bash returned `historical`; PowerShell returned
  `current`.
- Existing AC-6 tests assert only that `cur_key` plumbing exists and use lowercase
  branches; no uppercase or full-normalization behavioral case exists.

Impact: on Linux/macOS/Git Bash, a feature or architecture-change branch with
uppercase characters can avoid the validator's current-branch FAIL escalation
for missing Resume or Test Gate Results.

Required fix: implement one shared canonical normalization contract in both
validators and add behavioral cases for uppercase, punctuation replacement,
dash collapsing, trimming, and 100-character truncation.

## Dropped or Refuted Hypotheses

- Full Git Bash validator execution in the Windows fixture exceeded 120 seconds;
  its timeout is not used as finding evidence. The normalization result above
  comes from the validator's exact shell expression plus cited control flow.
- Receipt Classification mismatch does not itself alter required phase sets;
  header classification remains authoritative. Finding retained only at P3.
- Missing Timestamp does not reorder receipts; finding retained only at P3.
- Missing Owner/lock enforcement is already a verified #122 instance.
- PowerShell is not evidence that normalization is correct; case-insensitive
  comparison merely hides one canonical-algorithm violation.

## Backlog Disposition

No backlog rows were added. The user requested immediate Claude remediation
after this audit-only PR, so all four surviving findings are `do-now` inputs.

## Claude Implementation Handoff

Create a separate feature branch after this audit PR is reviewed or merged. Do
not modify this report PR and do not reuse unrelated worktrees.

Implementation scope:

- Harden both validators' receipt schema and SHA anchor validation.
- Implement canonical Work Log key normalization identically in shell and
  PowerShell.
- Add focused behavioral fixtures for every reproduction above.
- Preserve legacy archived-log WARN behavior unless a new spec explicitly
  changes it.

Acceptance minimum:

- Timestamp missing, malformed, or decreasing cases are rejected or explicitly
  documented as non-authoritative.
- Header/receipt classification mismatch fails outside a structured reset.
- Invalid and unresolvable Diff Base/Checkpoint anchors are detected.
- Uppercase current branches produce identical current-log verdicts on shell and
  PowerShell validators.
- Full CI-equivalent pytest plus both validators pass before review.

## routing_actions

```yaml
routing_actions:
  - finding: "Gate receipt Timestamp semantics must be enforced or removed from the mandatory schema claim."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-receipt-integrity-handoff"
  - finding: "Diff Base and Checkpoint anchors must be phase-valid and resolve to Git commits."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-receipt-integrity-handoff"
  - finding: "Receipt Classification must agree with the active Work Log classification epoch."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-receipt-integrity-handoff"
  - finding: "Current-branch Work Log detection must use the canonical normalization algorithm on every platform."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-receipt-integrity-handoff"
```
