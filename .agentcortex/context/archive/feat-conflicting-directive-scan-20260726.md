# Work Log: feat/conflicting-directive-scan

## Header

- Branch: `feat/conflicting-directive-scan`
- Classification: `feature`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-07-26`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `none`
- Checkpoint SHA: `none`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto), red-team-adversarial (auto, review/test), kb-consult (auto, on-match)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `134`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-07-26 (claude-code 2.1.160)`
- Platform: `claude-code`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §5, §9, §11, §12, §13` — full read, because the guardrails file is itself PRIMARY SOURCE MATERIAL for this task, not just governance to obey.
- Override: `none`
- Downstream-Capabilities: `knowledge_sources: kb-main->OK`

---

## Task Description

Backlog **#145**. ADR-011 swept the four phase-entry surfaces for one axis — does each
directive have enforcement backing? It never asked a second question: **do the directives
contradict each other?** That axis has never been swept.

Two instances are already on record, both found by accident rather than by a sweep:

- **#126** (shipped): 10 `.claude/commands` stubs listed guardrails as an unconditional
  Required-read, contradicting `CLAUDE.md` step 4 and the bootstrap TOKEN LEAK BLOCK. Fixed
  case-by-case.
- **2026-07-25** (found live mid-bootstrap): `bootstrap.md §1` orders a `Last Verified` SSoT
  write; `AGENTS.md §vNext State Model`'s non-ship exception list is **exhaustive** and
  excludes `/bootstrap`.

Externally motivated: Anthropic's 2026-07-24 context-engineering guidance names conflicting
instructions as a direct cause of degraded instruction-following, and reports removing >80%
of Claude Code's own system prompt on exactly that basis.

**Deliverable shape is an open question, not a fill-in-the-blank.** ADR-011's answer was
"point-in-time census + a durable count ratchet". Conflicts are semantic and cannot be
counted, so the durable half needs a different answer — or an honest admission that there
isn't one. That question is the spec's job.

**Phase chain**: `/bootstrap` -> `/research` (size the problem) -> `/spec` -> `/plan` ->
`/implement` -> `/review` -> `/test` -> `/handoff` -> `/ship`.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-26 | feature; ADR coverage exit 0 |
| research | done | 2026-07-26 | census: 10 findings + 1 negative result |
| spec | done | 2026-07-26 | draft spec with dispositions; 2 items flagged for human |
| plan | done | 2026-07-26 | 8 dispositions after rewrite |
| implement | done | 2026-07-26 | 8 fixes + 1 guard test + ADR-011 amendment |
| review | done | 2026-07-26 | 4-seat roundtable; 9 of 11 refuted -> rewrite |
| test | done | 2026-07-26 | 126 passed on the affected suites |
| handoff | skipped | — | evidence inline; user directed ship |
| ship | done | 2026-07-26 | — |

---

## Phase Summary

- bootstrap: classified `feature` (backlog #145 tier, unchanged). ADR coverage check exit 0 —
  ADR-001 / ADR-004 / ADR-007 / ADR-008 / ADR-009 / ADR-011 all cover the target surfaces, so
  no `/adr` prompt. `/brainstorm` skipped in favour of `/research`: the design fork here is
  not "which of several approaches", it is "how big is the problem" — and that is measured,
  not brainstormed. Logged in Drift Log per bootstrap §3.7.

- research: census v1 claimed 11 findings. **Superseded** — see the spec phase.

- spec (v1): 11 dispositions, blanket `signal_tier: T1`, two items flagged for human.
  **Withdrawn** after adversarial review.

- spec (v2, current): rewritten against a 4-seat roundtable that refuted **9 of 11** findings,
  two of them with fixes that would have **silently disabled live checks** (adding a heading
  the bare-grep at `validate.sh:1691` tests for; adding the section §10.6's retro probe keys
  on). One "headline finding" was an error this repo had already closed twice. Census
  rewritten to 7 survivors + 6 new, with every refutation retained on record. The spec now
  touches **no template**, adds **no directive**, states a tier **per row** (mostly honest
  `NONE`), and its highest-value row is a six-word annotation that prevents an error three
  separate sessions have made. Primary also **rejected one reviewer recommendation** on
  consistency grounds. | Confidence: 80% — lower than v1 despite being better work, because
  the external-signal seat failed and every judgment call remains same-vendor.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-07-26T03:00:00Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-07-26T04:10:00Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-07-26T06:30:00Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-07-26T06:40:00Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-07-26T07:10:00Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-07-26T07:20:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #145 | the tracked item |
| ADR | docs/adr/ADR-011-phase-entry-directive-enforcement.md | swept the enforcement axis; explicitly NOT this one |
| Review | docs/reviews/2026-07-19-phase-entry-directive-enumeration.md | the 112-row ADR-011 census — reuse its row inventory, do not redo it |
| Research | https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models | external signal: conflicting instructions named as a degradation cause |
| Prior instance | backlog #126 (shipped, PR #327) | the stub Required-read conflict, fixed case-by-case |

---

## Known Risk

- Superseded by the census §"Constraints any fix must respect" (verified: zero ratchet headroom, no template changes, scaffold-tier reach, `analyze_token_lifecycle.py` blind to these surfaces, ADR-011 `review_trigger` fires).
- R1 stands and worsened: the external signal FAILED, so all review was same-vendor.
- Rollback: no fix applied yet; this branch is docs-only.

---

## Decisions

### D-1: §13 Deletion-First — the revised change set is deletion-funded, not waived

**Decision**: no net-add justification is claimed, because the change set is net-negative.
**Reason**: S3 deletes a Required-read line from 23 command stubs plus two
`security_guardrails.md` lines; S1/S4/S6 are rewordings at ≈0 char delta; S7 adds two short
names to an existing list. The first draft tried to fund an always-loaded addition with a
*conditional-load* deletion (§9.1) — an invalid trade a reviewer caught.
**Alternatives**: (a) the first draft's §9.1 deletion — rejected, ADR-011 already dispositioned
it `keep-honest-unenforced`; (b) a recorded net-add waiver — unnecessary once S3 lands.
**Impact**: AC-10 measures a per-file char delta, NOT `analyze_token_lifecycle.py`, which was
verified to contain zero references to any surface this spec touches.

---

## Conflict Resolution

- `red-team-adversarial` is recommended for `/review` and `/test` per the §3.6 rule table
  (feature tier). No pair in `skill_conflict_matrix.md` matches this set.

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- `/brainstorm` skipped (bootstrap §3.7 requires logging the skip): the open question is
  problem SIZE, which is measured by a read-only census, not explored by ideation. `/research`
  substitutes.
- Guardrails read in FULL despite the token cost, and deliberately: `engineering_guardrails.md`
  is one of the four surfaces under audit. Reading it is data collection, not overhead.
- **External-signal attempt FAILED — recorded, not glossed** (§8.2 disclosure: an explicit
  executor request MUST disclose the fallback). `[audit-method][HIGH]` requires at least one
  external signal for an architecture-level audit. `OPENROUTER_API_KEY` is set and
  `python -m ask_openrouter --help` succeeded, so the path was live. Two invocations, six
  free-tier models total (`z-ai/glm-4.5-air`, `arcee-ai/trinity-large-preview`,
  `qwen/qwen3-coder`, then `deepseek/deepseek-chat-v3.1`, `google/gemini-2.0-flash-exp`,
  `meta-llama/llama-3.3-70b-instruct`), **all failed**. `Requested Executor: ask-openrouter` /
  `Actual Executor: none (fallback-chain exhausted)`. A paid model is `--profile quality` =
  high-cost, which §8.2 says requires user confirmation first — the user is asleep, so it was
  NOT run. **Honest ceiling: the roundtable is currently same-vendor only, which the
  `[audit-method]` lesson calls theatre.** The Anthropic 2026-07-24 guidance corroborates the
  census PREMISE but no individual finding. Re-run with a paid model on user approval before
  treating any judgment call here as externally validated.
- **Caught by a real gate**: I wrote a `Gate: research | Verdict: PASS` receipt;
  `validate.ps1` returned `[FAIL] work logs with illegal gate phase progression: 1`. Correct
  behaviour on the validator's part — `guardrails §10.2` defines research as advisory with
  **no gate receipt**, and `state_machine.md` models it as a `CLASSIFIED → CLASSIFIED`
  self-loop, not a forward phase. Receipt removed. Recorded because it is the counter-example
  to this task's own census: here the framework's rules and its enforcement AGREED, and the
  gate caught the agent. Not every rule pair is broken.

---

## Review Feedback

4-seat same-vendor roundtable (tenth-man · pre-mortem · downstream · doctrine). The external
seat FAILED (Drift Log), so this is theatre-adjacent; every verdict was primary-re-verified
against file text before adoption.

**Outcome: 2 of 11 original findings survived; 9 refuted, 2 of those with actively harmful
fixes; 6 new findings adopted.** The full per-row verdict table now lives in the TRACKED
census (`docs/reviews/2026-07-26-conflicting-directive-scan.md` §REFUTED) rather than here —
a work log is gitignored and would have hidden it. Overflow copy:
`.agentcortex/context/archive/work/feat-conflicting-directive-scan-20260726.md`.

Disposition: withdraw and rewrite. Both artifacts rewritten 2026-07-26.

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

- `pytest tests/ci/ tests/guard/` full run + targeted re-run of every suite the diff reaches
  (`test_validator_false_positives` · `test_worklog_section_naming` ·
  `test_directive_count_ratchet` · `test_trigger_metadata_tools`): **126 passed, 0 failed**.
- `validate.sh` / `validate.ps1`: **pass=116 warn=5 fail=0 skip=2**.
- Ratchets held at baseline without a baseline change: `AGENTS.md` 37/37,
  `engineering_guardrails.md` 84/84.

---

## Evidence

> Full pre-review detail compacted to
> `.agentcortex/context/archive/work/feat-conflicting-directive-scan-20260726.md`
> (`handoff.md §6`). Load-bearing results retained below.

- Branch from `main` @ `f765a59`. ADR coverage `check_adr_coverage.py` -> exit 0.
- Census v1: 11 claimed findings. Census v2 after adversarial review: **8 surviving**, 9
  refuted (2 with actively harmful fixes), 6 new. Both artifacts rewritten.
- Verified constraints that shaped the rewrite: `AGENTS.md` ratchet **37/37, zero headroom**;
  `CI Structural Tests` is not a required check; `.agentcortex/templates/*` + `AGENTS.md` are
  **scaffold** not force-update (`deploy.sh:112-117`, golden:163/199); `analyze_token_lifecycle.py`
  has **0** references to `AGENTS.md` / `rules/` / `templates/`; `validate.sh:1691` is a bare
  presence grep; `worklog.md` is 190 lines against a 300-line compaction cap.
- Primary rejected one reviewer recommendation on consistency grounds: `## Global Lessons
  Candidate` (`retro.md:55`) is the same *create-instruction* shape as the refuted C5/C6, so
  accepting it would contradict the refutation. Retained only as evidence for AC-9.
- `validate.ps1` after this compaction: recorded at the next run below.
- **Implement**: 8 fixes landed. S1 rescoped the `AGENTS.md` precedence clause; S2 renamed 5
  `## Risks` sites (incl. the fenced one at `plan.md` and `token-governance.md`); S3 removed the
  redundant `AGENTS.md` Required-read from 23 stubs (3 sections emptied and dropped); S4 turned
  both `§10.6` probes from presence to content; S5+S6 annotated `§10.2`; S7 added `/bootstrap`
  to the SSoT exception list; S8 added `handoff.md §6` step 4.
- **S3 narrowed by the primary during implement**: the spec said to also delete the
  `security_guardrails.md` Required-read. Dropped — the A1 refutation ("a conditional section
  not loaded at bootstrap is a *first* read, not a re-read") applies to it identically, so
  removing it would contradict the refutation this rewrite is built on. Only the `@import`ed
  `AGENTS.md` line is genuinely redundant.
- **Two self-inflicted failures during implement, both caught and fixed**: (1) a renumbering
  script ate line endings in the stubs -> reverted via `git checkout` and redone line-by-line;
  (2) the compact index went stale after the `AGENTS.md` edit -> regenerated. (2) is
  repo-gotchas #9, which I wrote and have now tripped **twice in one session**.
- **S8 was found by walking into it**: compacting this very Work Log to `handoff.md §6`'s
  letter produced an overflow file with no `## Phase Summary`, turning
  `test_171_ship_history_no_phase_summary_warn` red. Fixed the artifact AND the instruction.
- Compacted: 2026-07-26, archive: `.agentcortex/context/archive/work/feat-conflicting-directive-scan-20260726.md`
