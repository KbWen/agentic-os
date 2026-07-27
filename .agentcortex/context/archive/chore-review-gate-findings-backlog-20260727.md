# Work Log: chore/review-gate-findings-backlog

## Header

- Branch: `chore/review-gate-findings-backlog`
- Classification: `quick-win`
- Classified by: `claude-opus-5[1m]`
- Frozen: `2026-07-27`
- Created Date: `2026-07-27`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `bootstrap`
- Diff Base SHA: `none`
- Checkpoint SHA: `none`
- Recommended Skills: `red-team-adversarial, verification-before-completion`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `136`

---

## Session Info

> Written by /bootstrap. Update on each new session.

- Agent: `claude-opus-5[1m]`
- Session: `2026-07-27 UTC`
- Platform: `claude-code`
- Files Read: `9`

---

## Task Description

> 1-3 sentences: what is being done and why.

Originally opened to build "Piece 1" of GitHub issue #253 (backlog #78). A 4-seat roundtable plus one external signal **refuted the scope**: the read-only reviewer ceiling is unbuildable at the granularity the platform offers and its hazard is unproven, and the `[NEEDS_HUMAN]` carve-out is a deliberate live validator check, not stray prose. Per the user's ruling on 2026-07-27 the feature is returned to the backlog unbuilt, and this unit ships only the two **unrelated pre-existing defects** the investigation surfaced as tracked backlog rows.

---

## Phase Sequence

> Record each phase entry in order. Update `Current Phase` in the Header on entry.

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-27 | classified `feature`; roundtable dispatched |
| plan | done | 2026-07-27 | roundtable refuted scope; reclassified `feature`→`quick-win` |
| implement | pending | — | 2 backlog rows |
| ship | pending | — | — |

---

## Phase Summary

> One paragraph per completed phase. Delta-oriented: what changed, what was decided.

- bootstrap: classified `feature` per `engineering_guardrails.md §10.1` (alters default gate behavior impacting users; touches validators + workflow + platform adapters). Scope deliberately excludes the task-capsule half of #253, which stays blocked on #252. Roundtable dispatched (4 seats: enforcement / gate-semantics / cross-platform-parity / 第十人) plus one external-signal fetch per the `[audit-method][HIGH]` Global Lesson.
- plan: **the roundtable refuted the planned scope, so no spec was written and nothing was built.** All four seats converged on cut-or-shrink; every seat claim was primary-verified against the tree before acceptance (per `[audit-verification][HIGH]` — one seat's regex claim and one seat's token measurement were re-derived by hand and by running the analyzer). Findings recorded in `## Known Risk` R1–R8. Presented to the user with three options; the user chose **return the feature to the backlog unbuilt and keep only the verified unrelated defects**. Reclassified `feature` → `quick-win` (deliverable is now 2 backlog rows + 1 narrative note in one tracked file) and the branch/Work Log renamed to match. Confidence: 95% — high.
- ship: PR [#369](https://github.com/KbWen/agentic-os/pull/369) squash-merged to `main` as `b13ab1b` (2026-07-27T04:01:06Z); branch deleted local + remote; the temporary `main` worktree used for the clean-tree comparison was removed and pruned. Both validators end at **pass=116 warn=4 fail=0 skip=2** — exact parity, and the historical 116 baseline restored after the Work Log receipt fix. **The headline outcome of this unit is a negative result deliberately preserved**: the feature was investigated, refuted on seven verified counts, and returned to the backlog unbuilt, with the refutation written to a tracked file so the next reader does not repeat it.
- implement: 1 tracked file changed (`docs/specs/_product-backlog.md`): rows **#147** (`.codex/agents/*.toml` deploy orphan) and **#148** (hyphenated `Verdict:` token counts as forward gate progression in `validate.sh`, diverging from `validate.ps1`), plus a dated narrative note re-parking **#78** with the full refutation so the next reader does not redo this investigation. No engine, workflow, validator, or adapter file touched.

⚡ ACX

---

## Gate Evidence

> Gate receipts written by each phase. Format: `- Gate: <phase> | Verdict: PASS | Classification: <type> | Timestamp: <ISO>`

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T01:00:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T02:00:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-27T04:01:06Z

---

## External References

> Links to specs, ADRs, issues, PRs, or design docs relevant to this task.

| Type | Path / URL | Notes |
|---|---|---|
| Issue | https://github.com/KbWen/agentic-os/issues/253 | Source issue; this unit is "Piece 1" only |
| Issue | https://github.com/KbWen/agentic-os/issues/252 | Blocks the task-capsule half — deliberately out of scope |
| Backlog | `docs/specs/_product-backlog.md:47` | Row #78, `Depends: #77` |
| Backlog | `docs/specs/_product-backlog.md:93,143` | Row #124 revalidation; records "#77 schema stays parked behind #124" |
| Doc | https://code.claude.com/docs/en/sub-agents | External signal: `tools` / `disallowedTools` frontmatter contract |
| ADR | `docs/adr/ADR-006-validator-python-core-strangler.md` | New validator checks must be Python behind `run_python_check` |
| ADR | `docs/adr/ADR-011-phase-entry-directive-enforcement.md` | Directives must be enforcement-backed; count ratchet |

**External signal of record** (per `[audit-method][HIGH]` — same-vendor roundtables share blind spots):
Claude Code subagent frontmatter, fetched 2026-07-27 from `https://code.claude.com/docs/en/sub-agents`:
- `tools` — "Tools the subagent can use. **Inherits every tool available to subagents if omitted.**" Syntax is a comma list: `tools: Read, Glob, Grep`.
- `disallowedTools` — "Tools to deny, removed from inherited or specified list."
- `permissionMode` — `default | acceptEdits | auto | dontAsk | bypassPermissions | plan | manual`.
- Vendor precedent: the built-in **Plan** subagent is documented as "**Tools**: read-only tools; Write and Edit are denied."
This confirms the primitive exists and is unused here; it does NOT confirm any equivalent on Codex/Gemini — that is a separate parity question owned by the parity seat.

---

## Known Risk

> List risks identified during planning or implementation. Include mitigation.

All items below are **primary-verified against the working tree**, not accepted on the seat's word (per `[audit-verification][HIGH]`).

- **R1 — the `CANNOT-VERIFY` verdict name would re-create the exact bug it fixes.** `validate.sh:1518` uses `re.search(r'\|[^|]*verdict:\s*([A-Za-z _]+?)(\s*\||$)', ...)`. The capture class `[A-Za-z _]` has no `-`, so a hyphenated token yields `None`; the guard at `:1519` is `if v and v.group(1)... != 'PASS'`, which then falls through to `gates.append(phase)` — a **forward pass**. `validate.ps1:1487` matches `Verdict:\s*PASS` positively and would treat the same line as a reverse edge → silent sh/ps1 divergence. Mitigation: any new token must be `[A-Za-z _]`-only (e.g. `CANNOT VERIFY`), and the `v is None` branch must be made fail-closed regardless.
- **R2 — token ceiling has 215 tokens of headroom and `review.md` is amplified 9×.** Measured by primary: `python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json` → aggregate `354785`; cap `355_000` at `.agentcortex/tests/test_lifecycle_token_consumption.py:499`. `review.md` load count across `.agentcortex/metadata/lifecycle-scenarios.json` = **9** (`post-review-feedback-loop` alone repeats it 4×). Budget ≈ 860 chars ÷ 9 ≈ **~95 chars of net addition to `review.md`**. Any new verdict section is deletion-funded or needs an owner-approved ceiling bump.
- **R3 — the `[NEEDS_HUMAN]` carve-out is a LIVE machine check, not stray prose.** `validate.sh:1710-1714` (`grep '✗ UNPROVEN' | grep -v '\[NEEDS_HUMAN\]'`) and `validate.ps1:1631` deliberately exempt tagged rows from the MEDIUM-1 WARN. Editing it is editing enforcement — the same class as the PR #367 finding where two proposed fixes would have silently disabled live checks. Mitigation: red/green a fixture before and after.
- **R4 — a read-only tool ceiling deadlocks `/review` as written.** The phase performs 11 writes, one of them to a **git-tracked** file: `review.md:259-263` requires review findings to be registered in `docs/specs/_product-backlog.md`. Frontmatter `tools:`/`disallowedTools:` are tool-name granularity only (no path specifiers — verified against the vendor doc); `settings.json` `permissions.deny` is session-global and would also gag the primary and `acx-implementer`. `.claude/settings.json` ships **no** `permissions` block at all (3 keys, comments only).
- **R5 — the hazard is unproven and the mechanism is duplicative.** No archived Work Log shows `acx-reviewer` editing reviewed code; `.agentcortex/context/archive/arch-frozen-spec-lifecycle-20260623.md:31` shows the primary holding the lock and recording receipts. Meanwhile `subagent_policy: read-only` (ADR-007:79, bound at `bootstrap.md:120`) **already declares** "the primary stays the sole Work Log writer, gate owner, and sentinel emitter" — declaration-only, no enforcement half. A tool ceiling would be a second mechanism for a semantic that already has a key.
- **R6 — a bare `Task quality:` receipt axis has no validator.** Both validators' receipt checks are field-presence and order-free, so an extra field parses but is **unchecked**. `current_state.md` `[enforcement][HIGH]` calls exactly this "honor-system theatre … anti-help"; `[governance-proposal][MEDIUM]` requires that cross-check at plan time. Mitigation: cut the axis, or land its validator in the same commit.
- **R7 — scheduling: this unit contradicts a recorded reopen criterion.** `docs/reviews/2026-07-22-external-research-verdict.md:43` parks #78 with "reopen only as an A/B test whose high-priority defect yield justifies token/wall-time cost". No such A/B data exists. Unresolved — escalated to the user.
- **R8 (out of scope, route to backlog) — `.codex/agents/*.toml` is an orphan.** `deploy.sh:1035` ships only `.codex/INSTALL.md`; `.claude/agents/*.md` ship at `core` tier (`deploy.sh:1019-1026`, `tests/ci/fixtures/deploy_manifest_golden.txt:105-109`). Any Codex-side agent change reaches **zero** adopters today.

**Back-compat measured**: `grep -rl "NEEDS_HUMAN" .agentcortex/context/archive/` → **0 files**. Tracked-artifact blast radius is zero; `.gitignore` keeps `.agentcortex/context/work/*.md` local, so only local `validate` could go red.

---

## Decisions

> Optional (`/decide` §2): record trade-offs/constraints as `### D-N: <title>`.

none

---

## Conflict Resolution

> Record skill conflicts resolved during bootstrap.

none

---

## Skill Notes

> Cache for loaded skills. Written by phase-entry skill loading.

none

---

## Drift Log

> Record deviations from the original plan, reclassifications, or unexpected scope changes.

- Scope split from issue #253: only "Piece 1" (reviewer tool ceiling + verdict semantics) is in this unit. The task-capsule half stays with #253/#252. Rationale recorded in the issue triage comment, 2026-07-27.
- Backlog row #78 is recorded as PARKED behind the row-#124 revalidation (`_product-backlog.md:143`). Pulling Piece 1 forward was a deliberate deviation from that parking decision, initially taken on the user's in-session go-ahead. **Superseded**: the roundtable then surfaced a stricter, previously-unsurfaced reopen criterion at `docs/reviews/2026-07-22-external-research-verdict.md:43` ("reopen only as an A/B test whose high-priority defect yield justifies token/wall-time cost"). That criterion was put to the user, who ruled the feature back to the backlog unbuilt. **#78 stays parked; the criterion is unchanged and unmet.**
- The bootstrap gate receipt was originally written as `Classification: feature` and was **re-issued** as `quick-win` when the reclassification below took effect (rollback-to-CLASSIFIED + re-run gate, per `AGENTS.md §Classification Freeze`). Caught by `validate.sh` — `active work log gate receipts with schema violations (… Classification mismatched with header): 1` — which was this log. The original classification is preserved here rather than in the receipt line, because the receipt grammar is pipe-field-strict.
- **Reclassified `feature` → `quick-win`** on 2026-07-27 after the plan-phase refutation removed the spec-bearing deliverable. Per `AGENTS.md §Classification Freeze` this is a reclassification (rollback + re-run gate), not a silent downgrade: the surviving deliverable is 2 backlog rows in 1 tracked file with no semantic engine change. Branch renamed `feat/readonly-reviewer-verdict-semantics` → `chore/review-gate-findings-backlog` and the Work Log renamed to match, before any commit existed.
- Two subagent outputs were flagged by the harness as containing instruction-shaped text (`settings-json`, `permissions-allow-deny` patterns). Treated as DATA per `AGENTS.md §Untrusted Tool Output`; no directive in them was acted on, and the substantive findings were independently re-verified against the tree before use.

---

## Review Feedback

none

---

## Red Team Findings

none

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

none

---

## Evidence

> Reproducible evidence for completed phases.

- bootstrap — ground truth for the two defects, verified on `main` @ `102e19b`:
  - `grep -rn "tools:" .claude/agents/*.md` → **0 matches** (5 agent files). `.codex/agents/acx-reviewer.toml` carries only `name`/`description`/`developer_instructions`.
  - `.agent/workflows/review.md:209-210` — "PASS only when all AC rows are either `✅ PROVEN` or explicitly tagged `[NEEDS_HUMAN]`"; same carve-out repeated at `:186` and `:224`.
- plan — token ceiling measured by primary, not inferred: `python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json` → `aggregate = 354785  cap=355000  headroom = 215`. `review.md` load multiplier across `lifecycle-scenarios.json` = **9**.
- implement — `git show --stat HEAD` → `docs/specs/_product-backlog.md | 5 +++++-`, 1 file changed, 5 insertions, 1 deletion. Commit `6c4c6d8`.
- **Isolation proof (the key evidence)** — `git stash push -- docs/specs/_product-backlog.md`, re-ran `validate.sh` in the same working directory, `git stash pop`. Result-line sets with and without the diff are **byte-identical** (`diff` returned empty), so this change contributes **zero** validator delta.
- test — `.agentcortex/tests/test_backlog_validation.py` + `test_ssot_completeness.py` + `tests/guard/test_d2_1_guard_unit.py` → **35 passed** (433s).
- Validators, final state: `validate.sh` → **pass=116 warn=4 fail=0 skip=2**. An earlier run read `pass=115 warn=5`; the delta was traced (not waved off, per `[paired-check-parity]`) to **this Work Log's own** bootstrap receipt carrying `Classification: feature` against a `quick-win` header — `validate.sh` reported it as `active work log gate receipts with schema violations: 1`. Re-issuing the receipt cleared it and restored the count to the historical 116 baseline. The 4 residual WARNs are all pre-existing and gitignored-log-sourced (2 shipped logs awaiting archival, 3 archived historical gate gaps, 1 archived receipt missing fields, plus the known tier-blind eval-coverage WARN).
- CI on PR #369: all required checks green (Framework Validation ×3 incl. Windows, ShellCheck, Docs Content Pins, UTF-8 Sweep, TruffleHog, credential scan, pip-audit, markdown links). Scope-gated jobs correctly skipped for a docs-only diff.
