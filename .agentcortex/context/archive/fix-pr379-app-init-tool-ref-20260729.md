---
template: false
description: Work Log for the PR #379 remediation — deployed-doc tool citation + scaffold-exemption decision record.
---

# Work Log: fix/pr379-app-init-tool-ref

## Header

- Branch: `fix/pr379-app-init-tool-ref`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-07-29`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `bac16ea`
- Checkpoint SHA: `ef3390d`
- Recommended Skills: `verification-before-completion`
- Primary Domain Snapshot: `skill-ecosystem`
- SSoT Sequence: `140`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-07-29 00:00 UTC`
- Platform: `claude-code`
- Files Read: `18`

---

## Task Description

Unblock PR #379 (`codex/skill-runtime-modernization`), which is red on two CI jobs from a single
failure, and record the decision reversal the PR performs but does not name. Push target is the PR
branch; this local branch carries the remediation only.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | complete | 2026-07-29 | Read-only diagnosis of PR #379 first; classification deferred until root cause was known |
| plan | complete | 2026-07-29 | Two edits, no engine/logic change; deploy-whitelist alternative rejected on blast radius |
| implement | complete | 2026-07-29 | app-init.md §5 prose + skill-ecosystem L2 entry |
| review | skipped | 2026-07-29 | quick-win — review optional per AGENTS.md state model |
| test | complete | 2026-07-29 | Real CI Structural command, not a narrowed variant |
| handoff | skipped | 2026-07-29 | quick-win is exempt from /handoff |
| ship | complete | 2026-07-29 | PR #379 marked ready (it was still DRAFT) and squash-merged as `37bc85b`; receipt written only after the merge landed |

---

## Phase Summary

**bootstrap/diagnosis** — PR #379 showed `CI Structural Tests` and `Pytest (Windows) (1)` both red.
Both are the same assertion: `test_deployed_governance_referenced_tools_are_deployed`. Reproduced
locally before touching anything (`1 failed in 34.65s`) to rule out a runner artifact.

**plan** — Root cause is a one-line citation, not a missing tool. `.agent/workflows/app-init.md` gained
a reference to `.agentcortex/tools/check_skill_provenance.py`; that test deploys the tree and asserts
every `.agentcortex/tools/*.py` cited by a DEPLOYED governance doc was actually shipped. The tool is
deliberately source-repo-only — it self-skips when `.agentcortex-manifest` is present (PR #259 design).
Rejected the "add it to the deploy whitelist" fix: it would ship a tool that always no-ops downstream,
touch `deploy.sh` in two places plus the golden manifest, and move the downstream validator's
pass/skip counts for zero gain.

**implement** — (1) Rewrote the app-init.md §5 "Signal tier" paragraph so it describes upstream
enforcement in prose and cites no non-deployed path; kept the `Signal tier` / `machine-enforced`
phrases that `test_app_init_scaffold_contract_is_frontmatter_first` pins. (2) Added two entries to
`docs/architecture/skill-ecosystem.log.md`: a `[DECISION]` naming the superseded 2026-06-19 scaffold
exemption, and a `[CONSTRAINT]` recording the deployed-doc citation trap so the next author hits the
rule before the test.

**test** — Ran the actual CI Structural command (`pytest tests/ci/ tests/guard/ .agentcortex/tests/`),
not the `-m "not slow"` variant whose deselection hid this failure from the original author.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-29T00:05:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-29T00:20:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-29T00:35:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-29T00:50:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-29T08:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/skill-runtime-modernization.md | Shipped/frozen — not edited; this unit does not change any AC |
| ADR | — | — |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/379 | Push target; remediation lands on `codex/skill-runtime-modernization` |

---

## Known Risk

- The app-init.md rewrite is prose-only, but two assertions in `test_skill_provenance.py` read that
  section by string. Mitigated: `Signal tier`, `machine-enforced`, the fenced template, the SCAFFOLD
  comment, and `do not put HTML comments before it` are all preserved verbatim; the section is also
  parsed by `test_app_init_representative_generated_scaffold_passes_checker`, which re-instantiates
  the template through the real checker.

---

## Decisions

### D-1: Fix the citation, not the deployment

- Decision: Remove the source-repo-only tool path from the deployed governance doc rather than adding
  `check_skill_provenance.py` to `deploy.sh`'s runtime-tools whitelist.
- Reason: The tool is architecturally source-only — it exits early on a deployed tree by design. Shipping
  it would add a permanent no-op to every downstream install and change the downstream validator's
  pass/skip line counts, which parity tests read.
- Alternatives: (a) deploy the tool (rejected — blast radius, zero downstream value); (b) loosen the
  test's regex (rejected — the test is the only thing standing between a doc edit and a dangling
  `python ...` command in every downstream bootstrap).
- Impact: One paragraph in `.agent/workflows/app-init.md`. No engine, gate, or deploy-manifest change.
- → consolidated: L2 skill-ecosystem

### D-2: Name the superseded exemption

- Decision: Record in L2 that this PR supersedes PR #259's deliberate scaffold exemption.
- Reason: The PR reverses a prior decision of record and its spec presents the reversal as a fresh
  `[DECISION]` with no back-reference. Without the link, a future author reading the 2026-06-19 archive
  would find a live-looking exemption that no longer holds.
- Alternatives: amend the shipped spec (rejected — frozen); ADR (rejected — no behavior-boundary change,
  L2 is the right altitude).
- Impact: Two entries appended to `docs/architecture/skill-ecosystem.log.md`.
- → consolidated: L2 skill-ecosystem

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Upstream drift observed, not caused by this unit: PR #379 wrote its own ship records (SSoT sequence
  139→140, a Ship History entry, work-log archival, and an INDEX chain entry) while the PR was unmerged
  and CI was red. Left as-is — archives are immutable and the sequence is already consumed. Recorded
  here so the state is explained rather than silently inherited.
- The PR's Ship History entry is thinner than every neighbouring entry (no PR number, no merge SHA, no
  rollback line), and recent repo practice (#374, #375) lands ship records in a separate follow-up PR.
  Surfaced to the user as an open question; deliberately NOT restructured inside this unit.
- Classification note: this is a new quick-win work unit, not a continuation of codex's `feature` log
  (which is archived and immutable). No downgrade of that log's frozen classification is implied.
- Self-correction: this log first carried a `ship` PASS receipt with `Current Phase: ship` while PR #379
  was still unmerged — the exact premature-ship pattern flagged above in codex's log. `validate.sh`
  caught it as `shipped work logs still in active work/ directory`, which is the whole of the
  `pass=116 warn=4` vs `pass=117 warn=3` delta against the pre-remediation baseline. Rolled back to
  `test`; the ship receipt and the archival get written when the PR actually merges, not before.
- Local branch `fix/pr379-app-init-tool-ref` differs from the push target because
  `codex/skill-runtime-modernization` is still checked out in an abandoned worktree at
  `C:/tmp/wt-skill-runtime-modernization`. Not removed — another session's workspace.

---

## Review Feedback

none

---

## Red Team Findings

Two adversarial passes over `bfa50bd` (第十人 refute-only; 事前驗屍 pre-mortem), both required to
ground findings in a read `file:line` or a run command. Ten findings; every one re-verified by the
primary against ground truth before adjudication — two did not survive that check.

Full per-finding adjudication is in commit `ef3390d`'s message and the PR #379 body; the durable
design half is in `docs/architecture/skill-ecosystem.log.md`. Compacted here to the ledger only.

- **Adopted (8)** — 3 real code/test defects (no-PyYAML fallback false-rejects valid YAML on the
  FAIL-tier `Framework Validation` path; uncaught `IndexError` on an empty value; one-directional
  differential oracle) + `GEMINI.md` missing from the deployed-doc scan set + 4 corrections to records
  **I** wrote in `bfa50bd` (the false "validator-verifiable" assurance; `124`→`37`; the 2026-06-19
  exemption mis-attributed to the wrong half and its rationale dignified as goal-fit when the archive
  says scope-containment-under-ship-pressure; a gotcha that overstated coverage and used instruction
  voice in a no-directive file).
- **Overruled (2)** — BOM handling is deliberate, code-commented and pinned by a renamed test, not a
  silent regression; the gitignored Work Log is a framework property, not a defect of this commit.
- **Re-attributed (1)** — the resolver plural gap (`tokens`/`roles`/`migrations` do not activate their
  Skills) lives in `trigger_runtime_core`, the canonical runtime. The old CLI's substring match was
  masking it; the delegation exposed a pre-existing defect rather than causing one.
- **Surfaced, not fixed (2)** — that plural gap, and `resolve_runtime_contract.py` returning
  `resolved_workflow: null` with exit 0 on invalid input (latent, no caller, AC-6 freezes the output
  shape). Registered for the user rather than absorbed into this unit.

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

See `## Evidence` — quick-win, `/test` phase run for the CI-equivalence claim rather than for coverage delta.

---

## Evidence

- Failure reproduced on the unmodified PR head before any edit:
  `tests/ci/test_deploy_tiering.py::test_deployed_governance_referenced_tools_are_deployed`
  `AssertionError: ... deploy.sh did not ship ... ['check_skill_provenance.py']` — `1 failed in 34.65s`
- Why the original run missed it: `tests/ci/test_deploy_tiering.py` carries module-level
  `pytestmark = pytest.mark.slow`. The PR body's "CI-equivalent not-slow suite" was `-m "not slow"`,
  which takes the whole file with it. Counts from `--collect-only`: the file holds **37** tests
  (all 37 deselected under `not slow`); repo-wide the filter drops **124 of 835**. The real CI
  Structural command is `pytest tests/ci/ tests/guard/ .agentcortex/tests/ -v` — no marker filter.
  My first correction paragraph wrote "124 tests in test_deploy_tiering.py", conflating the two —
  caught by the 第十人 pass and corrected in the SSoT with an erratum rather than a silent edit.
- Post-fix, real CI Structural command on the complete tree:
  `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -q` → **835 passed in 5348.24s (1:29:08)**, 0 failed.
  (CI's own run of the same command on the pre-fix head was 809 passed / 25 skipped / **1 failed**.)
- Post-SSoT-write targeted re-run (`-k "ssot or governed or disposition or lifecycle or gotcha or skill_provenance"`):
  **154 passed** in 299.77s.
- Invariant self-check on the edited tree: `check_skill_provenance.py` no longer appears in any deployed
  governance doc; the 6 remaining `.agentcortex/tools/*.py` citations are all in `deploy.sh`'s whitelist;
  `repo-gotchas.md` carries 0 hard-directive keywords and 0 tool-path references.
- The five string assertions that `test_app_init_scaffold_contract_is_frontmatter_first` pins on the
  rewritten §5 section were replicated directly before the suite run — all 5 hold.
- `validate.sh` on the PR head before this fix: `pass=99 warn=3 fail=0 skip=3` (exit 0). The PR body's
  `117 PASS` was measured pre-archival; with the work log archived the 18-check work-log family
  correctly reports SKIP. `fail=0` in both states.

- Merge: PR #379 was still a **DRAFT** — `gh pr merge` refused with "Pull Request is still a draft".
  Marked ready, re-verified `fail=[] pending=[]`, then merged. Squash merge `37bc85b`.
  (Third recorded instance of codex leaving a PR in draft; the earlier two are in the #306 and
  #337/#338 records.)
- Final CI on the merged head: 18 checks pass, 1 skipping. Local full CI Structural command
  `838 passed / 0 failed` (2:01:32). `validate.sh` `pass=117 warn=3 fail=0 skip=2`.
- Compaction: this log crossed the 12KB ceiling (13362 bytes at 276 lines; the line ceiling of 300
  was not reached). The Red Team section was compacted to a ledger with pointers rather than split
  into a tracked `archive/work/` overflow file — the full adjudication already exists in commit
  `ef3390d`, the PR body, and the L2 log, so a fourth copy would be redundant. 12247 bytes after.
