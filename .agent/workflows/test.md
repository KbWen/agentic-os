---
description: Workflow for test
---
# /test

Design and execute minimal necessary tests. AI drives the entire process autonomously — classify depth, generate skeletons, write tests, run adversarial cases, and persist evidence. Human review is optional, not a gate.

## Step 0: Phase Verification

**Phase Verification** (per bootstrap §2b): Read `Current Phase` from Work Log header. Verify transition to `test` is legal. If illegal, STOP. Otherwise update `Current Phase: test`. If a new commit was created since the last `Checkpoint SHA`, SHOULD refresh it.

## Step 1: Auto-Classify Test Depth

Read the task classification from the active Work Log (`Classification:` field). If no Work Log exists (e.g., tiny-fix fast-path from bootstrap §0), infer classification from the scope of changes (number of files, modules touched, whether logic changed).

Apply the test depth matrix from `.agent/workflows/test-classify.md` to determine:
- How many tests are needed (scope)
- What evidence format to use (rigor)
- Whether adversarial testing is required (Red Team)

Do NOT ask the user which depth to use — infer it autonomously.

## Step 2: Generate Test Skeleton

Before writing any test code, generate a test blueprint per `.agent/workflows/test-skeleton.md`:
- At least 1 test per Acceptance Criterion in the spec
- At least 1 regression test per Risk identified in the plan
- Name tests descriptively so failures are self-documenting

### Spec-Test Traceability (feature / architecture-change only)

When generating test skeletons for `feature` or `architecture-change` tasks:
1. Each spec AC SHOULD have a stable identifier (e.g., `AC-1`, `AC-2`). If missing, assign them.
2. Test files SHOULD include `spec_ref: docs/specs/<feature>.md` in frontmatter or a top-of-file comment.
3. Individual test functions SHOULD reference the AC they verify (e.g., in the test name or docstring: `test_ac1_user_can_login`).
4. Output an AC coverage map in the test skeleton showing which AC maps to which test(s).

`tiny-fix`, `quick-win`, and `hotfix` are exempt from this traceability requirement.

## Step 3: Skill-Aware Test Implementation (Auto-Enforced)

Apply the Phase-Entry Skill-Loading Protocol (AGENTS.md §Phase-Entry Skill Loading) for all skills listing `/test` in their phases. Read `Recommended Skills` from the active Work Log before selecting which skill guidance to apply in this phase. Then apply each skill's test-phase rules:

**IF `test-driven-development` is active:**
- Verify every piece of production code written during /implement has a corresponding test
- If gaps found: write the missing tests NOW before proceeding
- All tests MUST pass after completion — no "known failures" allowed

**IF `auth-security` is active — add these mandatory test cases:**
- [ ] Unauthenticated request → 401
- [ ] Wrong role/permission → 403
- [ ] Expired token → 401
- [ ] Manipulated token (wrong signature) → 401
- [ ] Rate limit triggers after N failures
- [ ] Password stored as hash (NOT plaintext) — verify in DB/mock

**IF `api-design` is active — add these mandatory test cases:**
- [ ] Input validation rejects invalid data with structured error response
- [ ] List endpoints return paginated results
- [ ] Correct HTTP status codes per action (201/204/404/422)
- [ ] Error responses don't leak internals (no stack traces, no SQL, no file paths)

**IF `database-design` is active — add these mandatory test cases:**
- [ ] Migration runs forward successfully
- [ ] Migration rolls back cleanly (skip if project uses forward-only migrations per guardrails)
- [ ] Foreign key constraints enforced (reject orphan records)
- [ ] NOT NULL constraints enforced

**IF `frontend-patterns` is active — add these mandatory test cases:**
- [ ] Components render all 4 states (loading, error, empty, success)
- [ ] Form submission disabled during request (no double-submit)

**IF `systematic-debugging` is active (test failures encountered):**
- PAUSE test writing. Execute 4-phase debug process:
  1. Observe: Record exact failure message, input conditions, stack trace
  2. Hypothesize: Propose 1-3 root causes for the failure
  3. Verify: Isolate the cause by changing ONE variable at a time
  4. Fix: Minimal fix + re-run all tests to confirm no regression
- Resume test implementation only after root cause is resolved with evidence.

Write test code to the project's test directory (e.g., `tests/`, `__tests__/`, or project convention). Follow naming conventions from `.agentcortex/docs/TESTING_PROTOCOL.md` if it exists; otherwise use reasonable defaults.

Run all tests. Capture pass/fail output as evidence.

## Step 4: Adversarial Test Cases (Auto-Triggered)

After standard tests pass, check if adversarial testing is required based on classification:

1. Read the auto-trigger matrix from `.agents/skills/red-team-adversarial/SKILL.md` §When to Use.
2. For `architecture-change`, also activate Beast Mode (concurrency stress, resource exhaustion, fault injection).
3. Generate adversarial test cases using the table format from the skill file.
4. Where possible, implement adversarial cases as actual test code alongside standard tests.

Skip adversarial testing entirely for `tiny-fix` and `quick-win` classifications.

## Step 4b: Verification Before Completion (Auto-Enforced)

IF `verification-before-completion` is active, before claiming tests are done:
Apply the Verification-Before-Completion 5-Gate Contract (AGENTS.md §Verification Before Completion (5-Gate Sequence)).
Phase-specific criteria: Scope = confirm test coverage matches planned scope (no untested AC); Evidence = paste full test output (pass/fail counts, command used); Communication = state "Test phase complete. [N] tests pass, [M] AC covered."

## Step 5: Persist Evidence (Hard Gate)

No evidence = no completion. This is non-negotiable.

- Work Log MUST record: `Test Files: [list of test file paths]`
- Work Log MUST contain actual test output (pass/fail), not narrative claims
- If adversarial testing ran, record results under `## Red Team Findings`
- State transition: task may proceed to `/review` or `/ship` only after evidence is persisted

## Output Compression Rule

Apply the shared `Phase Output Compression` contract from `AGENTS.md`.

- Report test commands, pass/fail counts, AC coverage deltas, and unresolved risks only.
- Do not reprint the full test skeleton or full AC list unless coverage changed or a failure requires it.
- If adversarial testing ran, summarize new adversarial evidence rather than replaying the standard test narrative.

## Phase Summary Update

After tests are complete and evidence is persisted, append one line to `## Phase Summary` in the Work Log:
```
- test: [1-line summary — tests passed/failed count, AC coverage, adversarial result]
```

## Heading-Scoped Read Note

For token budgeting and future automation, `/test` entry reads only:
- `Step 1: Auto-Classify Test Depth`
- `Step 2: Generate Test Skeleton`
- `Step 3: Skill-Aware Test Implementation`
- `Step 4: Adversarial Test Cases`

Read `Step 4b: Verification Before Completion` and `Step 5: Persist Evidence` only when preparing the test completion summary.
