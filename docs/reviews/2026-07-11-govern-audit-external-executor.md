# Governance Self-Audit — External Executor Safety — 2026-07-11

Scope: two additional Codex-led passes over external CLI delegation governance.
Pass 1 traced timeout, retry, and post-flight state transitions. Pass 2 tested
executor attribution, dirty-worktree preservation, and explicit Claude handoff.

External-signal status: `same-vendor-only` for the audit verdict. Claude is the
designated implementation executor after this audit-only pull request; Claude's
patch remains junior-tool output and requires independent Codex or human review.

## Validator Baseline

- Command: `.agentcortex/bin/validate.ps1`
- Result: `pass=114 warn=4 fail=0 skip=2`
- The extra local warning versus the prior snapshot is one stale advisory Work
  Log lock from the intentionally paused remediation attempt. The other warnings
  are the known historical receipts and eval-coverage inventory.

## Already Known and Excluded

- Backlog #105 covers deploy version drift and interrupted half-upgrades, not
  external executor process timeout or retry state.
- Backlog #113 covers no-Python validator divergence, not tool process failures.
- Backlog #120 covers missing default-on downstream enforcement, not executor
  attribution or worktree preservation.
- The first 2026-07-11 audit covers command adapters and `routing_actions`
  parsing. Those findings are not repeated here.
- The Global Lesson on errored mutation batches warns operators to re-derive
  state, but the external-tool workflow does not operationalize that lesson.

## Round 1 — Failure-State and Retry Audit

### P1 — Timeout has no mandatory post-failure state reconstruction

The Claude workflow defines post-flight only "after Claude returns" and its error
table has no timeout, killed-process, partial-output, or nonzero-exit branch. A
timed-out executor can write files before termination while returning no usable
summary. Retrying from an earlier status sample can then overlap or duplicate
those changes.

Observed reproduction:

1. A bounded Claude CLI implementation command was started with a 600-second
   shell timeout and a five-file allowlist.
2. A mid-run `git status --short` sample was empty; the command later exited 124
   at 604 seconds without a Claude result payload.
3. Before the retry completed, all five allowed files were present in the diff;
   the retry reported that negative tests "were already added by a prior pass."
4. The recovered changes were preserved in the local diagnostic stash named
   `scope-creep escalation: codex/governance-two-pass-audit claude-wip`.

Evidence:

- `.agent/workflows/claude-cli.md:98-110` runs post-flight only after normal
  completion.
- `.agent/workflows/claude-cli.md:143-151` omits timeout and nonzero-exit cases.
- `.agent/rules/engineering_guardrails.md:238-245` requires post-flight review
  but does not define failure-state reconstruction.
- No test under `tests/` or `.agentcortex/tests/` exercises Claude/Codex CLI
  timeout, late writes, or retry behavior.

Impact: duplicate edits, acceptance of an unreported partial patch, or a second
executor mutating a worktree whose state the orchestrator incorrectly considers
clean.

Required fix: every abnormal executor exit must stop retries, wait for process
termination, re-run `git status` plus a baseline-relative diff, record partial
state, and require explicit reconciliation before another invocation.

## Round 2 — Attribution and Worktree-Preservation Audit

### P1 — Unauthorized-file rollback can erase pre-existing user work

Claude and Codex pre-flight steps do not capture the starting worktree or a
per-file diff baseline. Post-flight then instructs the orchestrator to revert
files outside the target list; the Codex workflow explicitly recommends
`git checkout -- <file>`. If an out-of-scope file was already dirty before the
executor touched it, an entire-file revert cannot distinguish user changes from
executor changes and can destroy both.

Evidence:

- `.agent/workflows/claude-cli.md:39-54` has no clean-tree check, status snapshot,
  or baseline diff capture.
- `.agent/workflows/claude-cli.md:98-103` orders scope verification only after
  execution and mandates a revert on violation.
- `.agent/workflows/codex-cli.md:92-102,179-185` mirrors the gap and names the
  destructive whole-file checkout directly.
- `ask-local` avoids this class because the junior model returns a patch and the
  primary applies it; it never writes the worktree directly.

Impact: loss of unrelated human or agent changes in a dirty worktree while the
governance system claims it is restoring scope.

Required fix: capture the pre-flight dirty-file set and diff, prefer an isolated
worktree for write-capable executors, and never whole-file-revert a path that was
dirty at baseline. Reject or surgically reverse only executor-attributable hunks.

### P2 — Explicit Claude delegation can silently become a different executor

The canonical guardrail requires `Executor: <tool>` before availability probing
and then silently falls back when the tool is unavailable. The Claude workflow
reverses that order by probing first and creating/updating the Work Log later.
Neither contract requires the final user-facing handoff to state that an
explicitly requested Claude execution was actually performed by the native
orchestrator.

Evidence:

- `.agent/rules/engineering_guardrails.md:240-244` orders executor recording
  before the silent availability fallback.
- `.agent/workflows/claude-cli.md:44-54` probes availability/auth first, then
  writes `Executor: Claude CLI`.
- `.agent/workflows/claude-cli.md:145-151` silently falls back for missing CLI or
  auth, while post-flight recording is described only after Claude completes.
- `.agent/workflows/codex-cli.md:179-185` instead tells the user to install/login
  and stop, demonstrating cross-module policy drift for the same §8.2 contract.

Impact: inaccurate executor provenance in Work Logs and a user believing Claude
made a change when a different model actually did.

Required fix: distinguish optional acceleration from explicit executor intent;
always record `Requested Executor`, `Actual Executor`, and fallback reason. A
fallback may remain low-noise, but final completion and handoff must disclose an
executor mismatch.

## Closed With Reason

- The stale `GPT-1.0` orchestrator wording in CLI examples is cosmetic and does
  not change runtime behavior. Close unless it causes a real adapter failure.
- `bypassPermissions` is not independently reported: bounded prompts plus
  post-flight review are a valid defense when the new pre-flight baseline and
  abnormal-exit reconciliation requirements above are added.

## Backlog Disposition

No backlog rows were added. All three surviving findings are `do-now` inputs for
the user-requested Claude implementation after this audit PR is opened.

## Claude Implementation Handoff

Do not add fixes to this audit-only PR. Start from updated `main` after the audit
PR is merged, or use a clearly labeled stacked branch if implementation must
start earlier.

Recommended work split:

1. `feature/validator-fail-open-hardening`: implement the three findings from
   `docs/reviews/2026-07-11-govern-audit.md`. The preserved local stash is
   evidence, not an approved patch; inspect it with `git stash show -p` and do
   not apply it before feature bootstrap/spec/plan gates pass.
2. `feature/external-executor-safety`: implement timeout reconciliation,
   dirty-tree baselines, safe scope rollback, and requested/actual executor
   receipts from this report.

Acceptance minimum:

- Negative behavioral tests for timeout/partial writes and retry blocking.
- Dirty-worktree fixture proving unrelated pre-existing hunks survive a scope
  violation.
- Work Log fixture proving requested and actual executors cannot be conflated.
- Cross-workflow contract test covering Claude CLI, Codex CLI, and §8.2.
- Full `pytest` CI-equivalent suite and both validators pass before review.

## routing_actions

```yaml
routing_actions:
  - finding: "External executor timeout and nonzero exits require baseline-relative state reconstruction before retry."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-implementation-handoff"
  - finding: "Write-capable executor rollback must preserve files and hunks that were dirty at pre-flight baseline."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-implementation-handoff"
  - finding: "Requested and actual external executors require distinct, user-visible provenance."
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "claude-implementation-handoff"
```
