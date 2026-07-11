# Governance Self-Audit — 2026-07-11

Scope: two-pass audit of governance gates, validators, adapter wiring, and
finding-routing enforcement. Pass 1 mapped rule-to-validator/test/CI coverage;
Pass 2 attacked the resulting seams with isolated fixtures.

External-signal status: `same-vendor-only` at snapshot time. The verified
findings are scheduled for a Claude CLI follow-up after this report commit.

## Validator Baseline

- Command: `.agentcortex/bin/validate.ps1`
- Result: `pass=98 warn=3 fail=0 skip=2`
- Existing warnings: three historical gate-bypass logs, one malformed historical
  receipt, and 28 MUST-bearing sections without behavioral eval coverage.

## Already Known and Excluded

- Backlog #105 already tracks version drift and interrupted half-upgrades. It
  does not cover manifest deletion changing repository identity and disabling
  adapter validation.
- Backlog #113 tracks no-Python validator divergence; no duplicate filed.
- Backlog #116 fixed command enumeration coverage. It does not verify the
  semantic dispatch target of ordinary command stubs.
- Backlog #122 tracks honor-system MUST deletion/evaluation; the 28 uncovered
  sections remain excluded from this report.
- Backlog #134 tracks template placeholder false-passes; no duplicate filed.
- The 2026-07-01 premortems already cover stale routing actions, default-branch
  Work Log collisions, reduced assurance, and WARN taxonomy.

## Verified Findings — Do Now

### P1 — Claude command sync validates substring presence, not the dispatch directive

The checker accepts a stub when the expected workflow path appears anywhere in
the file. In an isolated clone, changing the canonical execution directive from
`.agent/workflows/review.md` to `.agent/workflows/nonexistent.md` still returned
exit 0 while a later explanatory sentence retained the expected string. An
adapter can therefore dispatch to the wrong workflow while the sync gate stays
green.

Evidence:

- `.agentcortex/tools/check_command_sync.py:89-97` uses an unscoped substring
  membership check.
- `.agentcortex/tests/test_trigger_metadata_tools.py:300-350` checks repository
  pass, set equality, and alias targets, but does not behaviorally mutate and
  verify ordinary dispatch directives.
- Isolated fixture command: `python .agentcortex/tools/check_command_sync.py --root .`
  with a broken primary directive and a residual expected-path mention returned
  `Command sync check passed (28 commands verified, 2 aliases verified, 30 total)`.

Impact: a Claude command can execute a nonexistent or unintended workflow,
skipping the canonical phase instructions despite a green validator.

Required fix: parse and require exactly one canonical execution directive per
ordinary stub, then add a negative behavioral test where only a comment or later
prose retains the expected path.

### P1 — Missing deploy manifest fail-opens adapter validation

Repository identity is inferred from the absence of `.agentcortex-manifest`.
Both the top-level validators and command-sync tool treat that absence as source
mode and skip adapter checks, even though this source repository tracks all 30
Claude command stubs. In an isolated clone, a fully broken review adapter failed
with a manifest present and returned exit 0 immediately after only the manifest
was removed.

Evidence:

- `.agentcortex/tools/check_command_sync.py:71-76` equates missing manifest with
  source identity and exits 0.
- `.agentcortex/bin/validate.sh:27-31,307-315` and
  `.agentcortex/bin/validate.ps1:324-360` use the same source-mode skip.
- `.agentcortex/bin/deploy.sh:914-950` deploys both the canonical deploy script
  and command-sync tool downstream, so deploy-script presence plus missing
  manifest is a reachable downstream state.
- Isolated fixture: broken all references to `.agent/workflows/review.md`;
  manifest present produced exit 1, manifest absent produced
  `Source repo detected — .claude/commands/ sync check skipped.` and exit 0.

Impact: accidental deletion or a malicious change can remove the identity file
and simultaneously disable the checks most likely to catch adapter drift.

Required fix: use a positive, non-user-removable source marker for source-only
skips, or validate tracked adapters in both modes. Add a deploy fixture proving
manifest deletion cannot turn a broken adapter green.

### P1 — routing_actions validation accepts malformed inline maps without validating values

The validators first search the whole report for required field substrings, then
validate only standalone `target_doc:` and `status:` lines. A syntactically valid
inline YAML mapping contains every required substring but matches neither value
parser. Invalid paths and statuses therefore pass as structurally valid.

Evidence:

- `.agentcortex/bin/validate.sh:943-971` scopes required-field checks to the
  entire file and value checks to anchored standalone lines.
- `.agentcortex/bin/validate.ps1:913-944` mirrors the same split parsing model.
- Isolated fixture used:

  ```yaml
  routing_actions:
    - {finding: "escape canonical docs", target_doc: "../../escape.md", status: bogus, owner: attacker}
  ```

- Full `.agentcortex/bin/validate.ps1` result on that fixture:
  `[PASS] routing_actions contract is structurally valid when present` and
  `Summary: pass=98 warn=3 fail=0 skip=2`.

Impact: a report can claim routed findings while pointing outside canonical docs
or using an unrecognized status, defeating the audit-to-canonical-doc closure
contract.

Required fix: parse only the fenced `routing_actions` YAML block into structured
records, reject malformed/non-list forms, validate every record, and add inline
map plus fields-outside-block negative tests for both validators.

## Backlog Disposition

No new backlog rows. All three findings are `do-now` because the user requested
immediate Claude remediation after the two audit passes.

## Dropped False Alarms

- No-Python gate progression weakness: already tracked by #113.
- Empty Work Log Evidence placeholder: already tracked by #134.
- Governance eval coverage count: already tracked by #122 and emitted by the
  current validator.
- Manifest version/half-upgrade drift: the overlapping portion is already #105;
  only the independently reproduced identity fail-open remains above.

## routing_actions

```yaml
routing_actions:
  - finding: "Claude command sync must validate the canonical dispatch directive, not any substring occurrence."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "codex-governance-two-pass-audit"
  - finding: "Missing deploy manifest must not disable adapter validation or imply source identity."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "codex-governance-two-pass-audit"
  - finding: "routing_actions validators must structurally parse and validate every action record."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "codex-governance-two-pass-audit"
```
