---
status: shipped
created: 2026-10-19
classification: feature
primary_domain: testing
signal_tier: T1
---

# Test Evidence Freshness: a Recorded Run Is Tied to the Code It Tested

## Goal

Today a `/test` PASS is a line the agent writes. Nothing ties it to the code state, so a
run recorded early still reads as current after later edits, and a failed run can be
followed by a PASS receipt. This spec adds an optional recorder that runs the test command
itself and writes the result with a fingerprint of the code it ran against, and a
validator check that fails a ship whose code changed after the last recorded run.

It catches **stale or failed** evidence. It does not catch forged evidence: a line typed
by hand with a correct fingerprint passes. The README says so.

## Evidence and Root Cause

1. The test gate is satisfied by text: `test.md` asks for results in the Work Log and
   `validate.sh` checks the `## Test Gate Results` body is non-empty (AC-6, #233). The
   body is never compared with anything.
2. The 2026-10-19 comparison scored enforcement 5/10 for this repo, with "a PASS receipt
   is just typed text" as the main reason. `verify_agent_evidence.py` can re-run claimed
   commands but is wired only to a manual job.
3. The only check that fires in the agent's own command sequence before ship is the
   `guard_context_write.py --expected-sha` call (`ship.md` §State Update). A stale test
   result produces no signal anywhere.

## Design

**Fingerprint.** `git write-tree` over a temporary index seeded from `.git/index`, after
`git add -A` and with `.agentcortex/context/` removed from that index. It covers tracked
and untracked, non-ignored files, and it ignores runtime state (Work Logs, SSoT, archive),
so writing the result into the Work Log and the ship's SSoT writes do not change it. The
real index is never touched.

**Recorder** — `.agentcortex/tools/record_test_run.py --worklog <path> -- <command...>`:
runs the command without a shell, fingerprints before and after, and appends to
`## Test Gate Results`:

`- Test run: `<command>` | exit: <n> | tree: <40-hex, unstable or none> | at: <ISO-UTC>`

`unstable` means the code changed while the tests ran; `none` means git could not fingerprint
the tree (reported, never a FAIL). It exits with the command's exit
code; the command's own output passes through unchanged.

**Check** — `record_test_run.py check --root <repo>`: reads the current branch's active
Work Log(s) (canonical key normalization, owner-prefixed variants included). Per log:

| State | Result |
|---|---|
| no `Test run:` line | PASS, silent (opt-in) — except a feature/architecture-change/hotfix log with a `test` or `ship` PASS receipt: WARN text naming the recorder, never a FAIL *[Updated: 2026-10-20]* |
| latest run `exit` ≠ 0 and a `test` or `ship` PASS receipt follows it | FAIL |
| latest run `tree` ≠ current fingerprint and a `ship` receipt exists | FAIL |
| latest run `tree` ≠ current fingerprint, no `ship` receipt | WARN text (PASS line) |
| latest run `unstable` | WARN text; FAIL once a `ship` receipt exists |
| not a git work tree / git missing | WARN text, exit 0 |

Wired through `run_python_check` in both validators (ADR-006 seam), WARN when Python is
missing, shipped in both `deploy.sh` whitelist sites with the manifest golden regenerated.

**Workflow.** `test.md` tells the agent to run the suite through the recorder when Python
is available. `ship.md` §Pre-merge step 2 re-runs through it and requires `check` to exit 0
(the ship gate fails otherwise) — this is where the stale-after-merge case is caught, since
the active log is archived later in the same ship. Funded by trimming `test.md`
(lifecycle ceiling). Accepted limits: the recorded command is not verified to be the real
suite; a detached HEAD is reported, not checked; uncommitted edits inside a submodule are
not fingerprinted; a tree git cannot read records `tree: none`, which WARNs and
never FAILs, so an agent that makes the tree unreadable on purpose ships stale code with a
WARN; `git add -A` on the temporary index writes unreferenced blobs that `gc`
removes.

## Acceptance Criteria

1. AC-1: The recorder runs the command without a shell, returns its exit code, and appends
   exactly one `Test run:` line under `## Test Gate Results` (replacing a lone `none`).
2. AC-2: The fingerprint is unchanged by writes under `.agentcortex/context/` and by
   gitignored files; it changes on any edit, add or delete of other files; the real
   `.git/index` is byte-identical before and after.
3. AC-3: A code change during the run records `tree: unstable`.
4. AC-4: `check` FAILs (exit 1) when the latest run failed and a later test/ship PASS
   receipt exists, and when the fingerprint differs and a ship receipt exists.
5. AC-5: `check` exits 0 with WARN text for a differing fingerprint before ship and for
   `unstable`; exits 0 silently for a log with no `Test run:` line.
   *[Updated 2026-10-20 — owner decision in chat (wave 2): a tested-tier log with a test/ship PASS
   receipt and no recorded run now WARNs; still never a FAIL.]*
6. AC-6: validate.sh and validate.ps1 report the same tally for the check on one fixture.
7. AC-7: The tool ships downstream (both whitelist sites + golden) and a fresh deploy's
   validator runs it (no unexpected-absence count).
8. AC-8: README's enforcement table says what this catches (stale/failed runs) and what it
   does not (a hand-typed line).

## Non-goals

- Proving tests were not forged; signing; CI re-running the agent's command.
- Changing what `## Test Gate Results` must contain for existing logs.
- Requiring the recorder: logs without a `Test run:` line keep today's behaviour.

## Constraints

- Stdlib-only Python; git ≥ 2.20; works on Windows (Git for Windows) and POSIX.
- Zero-Python adopters: the check SKIPs/WARNs via the existing seam; nothing breaks.
- Lifecycle token ceiling: any counted-doc addition is funded in the same change.

## Domain Decisions

- [DECISION] Fingerprint = `git write-tree` of a temp index excluding `.agentcortex/context/`, so recording evidence and shipping do not invalidate it.
- [DECISION] Opt-in by presence of a `Test run:` line; FAIL only when a recorded run contradicts a later receipt or the shipped code.
- [TRADEOFF] Detects stale and failed evidence, not forged evidence — accepted, stated in README; signing was previously rejected as self-attestation theatre.
- [CONSTRAINT] One Python tool behind `run_python_check`; no native twin logic.
