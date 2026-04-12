---
name: test-classify
description: Auto-select test depth and evidence format based on task classification.
tasks:
  - test-classify
---

# /test-classify

Read-only protocol. Determines what testing is required based on task classification. Companion to `/test-skeleton` (which generates the actual test blueprint).

> Ref: `.agent/rules/engineering_guardrails.md` §5, §10.2

## Test Classification Matrix

| Task Classification | Test Depth | Evidence Format | Test Skeleton Required? |
| --- | --- | --- | --- |
| `tiny-fix` | Inline assertion | diff + 1-line verification statement | No |
| `quick-win` | Before/after check | diff + before/after behavior statement | No (but recommended) |
| `feature` | Unit + integration | test output + verifiable demo steps | Yes (`/test-skeleton`) |
| `architecture-change` | Unit + integration + migration + rollback | test output + migration plan + rollback verification | Yes (`/test-skeleton`) |
| `hotfix` | Regression + root cause | root cause analysis + fix verification + retro | No (but regression test required) |

## Evidence Templates

### tiny-fix Evidence

```markdown
## Evidence
- Diff: [1-line summary of change]
- Verification: [1-line statement, e.g., "typo corrected in output"]
```

### quick-win Evidence

```markdown
## Evidence
- Before: [behavior before change]
- After: [behavior after change]
- Verification command: `[command that demonstrates the change]`
```

### feature Evidence

```markdown
## Evidence
- Tests run: [command]
- Test results: [pass/fail with counts]
- Demo steps:
  1. [step]
  2. [step]
  3. [expected result]
- AC coverage: [list ACs and their test mapping]
```

### architecture-change Evidence

```markdown
## Evidence
- Tests run: [command]
- Test results: [pass/fail with counts]
- Migration test: [describe migration path tested]
- Rollback test: [describe rollback verification]
- AC coverage: [list ACs and their test mapping]
- Side-effect check: [list of verified non-regressions]
```

### hotfix Evidence

```markdown
## Evidence
- Root cause: [1-2 sentences]
- Fix approach: [1-2 sentences]
- Regression test: [command + result]
- Retro reference: [link to /retro output or Work Log section]
```

## Integration Points

- **At `/bootstrap`**: Classification determines test depth automatically. No separate decision needed.
- **At `/plan`**: Plan SHOULD reference the expected evidence format for the classified tier.
- **At `/test`**: Agent selects the matching evidence template and fills it in.
- **At `/ship`**: Gate engine validates that evidence meets the minimum for the classification tier.

## Minimum Test Coverage by Scope

| Change Scope | Minimum Test |
| --- | --- |
| Docs/config only (no logic) | Verify file renders / validates correctly |
| Single function change | 1 test covering the changed behavior |
| API/interface change | 1 contract test + 1 consumer test |
| Multi-module change | 1 integration test spanning affected modules |
| Data model change | 1 migration test + 1 rollback test |
| New workflow/command added | 1 structural validation (file exists, required sections present) |

## Anti-Patterns

| Anti-Pattern | Correct Behavior |
| --- | --- |
| Writing full test suites for a `tiny-fix` | Inline assertion only |
| Skipping evidence for `quick-win` because "it's small" | Before/after statement is mandatory |
| Testing unrelated code "while we're at it" | Test ONLY changed behavior (§7 Scope Discipline) |
| Using mocks when real execution is feasible and fast | Prefer real execution for evidence quality |
| Generating test skeleton for `tiny-fix` | Skip — overhead exceeds value |
