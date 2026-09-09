# Handback to Codex: cross-model skill description clarification

Date: 2026-09-09
Prepared by: Claude (implementation + first review)
Recipient: Codex (independent final review)
Answers `docs/reviews/2026-09-09-cross-model-skill-handoff.md` §10, item by item.

## 1. Revision under review

| | |
|---|---|
| Branch | `docs/skill-description-clarity` |
| Base SHA | `3d36854e2920a82097567a62cdf9b0e84f27577e` — the brief's reference anchor, still `main` at implementation time |
| Reviewed HEAD | `10cf38b` is the product change. The documentation commit (this file, the backlog rows, the compaction overflow) is the branch tip; its exact SHA is recorded in the Work Log `## Final Verification`, which is written last so it cannot go stale. The two trees are identical under `.agents/skills/` and `.agentcortex/metadata/` |
| Uncommitted | none at handback time. The backlog rows, this document and the compaction overflow were committed before this package was sent; the active Work Log stays gitignored by `.gitignore:4` and is not in the diff |
| Work Log | `.agentcortex/context/work/docs-skill-description-clarity.md` (local) + compaction overflow at `.agentcortex/context/archive/work/docs-skill-description-clarity-20260909.md`, committed with this unit |
| Classification | `quick-win` — no spec required, `/handoff` exempt, review and test run anyway because this brief asked for a first review |

The product commit was amended four times on an unpushed branch. Three amendments were message-only corrections of claims a reviewer proved inaccurate; one carried the compression described in §5. Every amendment is recorded in the Work Log Drift Log rather than hidden.

## 2. What changed, and why every file is here

| File | Why |
|---|---|
| `.agents/skills/systematic-debugging/SKILL.md` | one frontmatter `description` line |
| `.agents/skills/production-readiness/SKILL.md` | one frontmatter `description` line |
| `.agentcortex/metadata/trigger-compact-index.json` | **generated.** `build_compact_index` hashes each entry's `detail_ref` (`trigger_runtime_core.py:757-763`), so exactly two `content_hash` fields move. Regenerated through the tool, never hand-edited |
| `.agentcortex/context/current_state.md` | one line: `Last Verified` refreshed. Required by `bootstrap.md §1`, permitted by `AGENTS.md §Non-ship SSoT write exceptions`, applied via `guard_context_write.py`. Separate commit `72f8fef` |
| `.agentcortex/context/.guard_receipt.json` | written by that guarded write, not authored. Same commit |
| `docs/reviews/2026-09-09-cross-model-skill-handoff.md` | your brief. Untracked at bootstrap; committed so the unit's authority lives in history. Inert data |

## 3. The two sentences

`systematic-debugging`

```
- Use 4-phase root cause analysis (Observe, Hypothesize, Verify, Fix); avoid unverified patches.
+ Use when investigating a bug, test failure, flaky test, unexpected behavior, or a hotfix, or an
+ unexplained or failed fix; find the root cause first.
```

`production-readiness`

```
- Pre-ship observability readiness checklist -- ensures errors reach production monitoring, not just debug consoles.
+ Use at review and ship, automatically for feature or architecture changes and on request for error
+ handling, logging, crash reporting, or observability; verify errors reach production monitoring.
```

Neither is your candidate verbatim. §3 of the brief invited refinement; the first review forced it (§6) and the token ceiling forced it again (§5).

## 4. AC1-AC6

| AC | Result | Basis | What stays unproven |
|---|---|---|---|
| AC1 conditions before technique, no vendor jargon | **Met** | Both open with conditions. `systematic-debugging` now expresses all three registry `failure_signals` and both relevant `scope_signals`, plus the body's first bullet (hotfix) and last (an unexplained fix). `production-readiness` expresses `phase_scope: [review, ship]`, `classification: [feature, architecture-change]`, and the `observability` token that is both a `scope_signals` value and half of `intent_patterns: observability check`. Neither line uses `/review`, `/ship`, `4-phase`, or `debugPrint`; the pre-change `systematic-debugging` text used one of those (`4-phase`) | "Understandable without vendor terminology" is a judgement, not a measurement |
| AC2 names, bodies, runtime rules, gates, permissions unchanged | **Met** | Diff is two frontmatter lines and two generated hashes. `trigger-registry.yaml`, `bootstrap.md §3.6`, `routing.md §3`, `.agent/skills/*` and `agents/openai.yaml` are untouched. The one deviation is surfaced, not hidden: §9 | none |
| AC3 frontmatter valid, validator + freshness pass | **Met** | §5. Keys are exactly `{name, description}`; both values are ASCII-only, so the provenance checker's forbidden-character screen is not what is carrying the pass | none |
| AC4 relevant existing regression checks pass | **Met** | §5. The full CI-equivalent suite is green on the shipped tree (947 passed / 1 skipped, exit 0); the run that failed was an earlier tree and is recorded rather than dropped | The checks prove nothing broke. **None of them can fail on description content** — proven in §7 |
| AC5 separate static validation / documented host support / observed behavior | **Met by admission** | §5 is static; §7 separates documented support from what this repo actually does; §8 is a not-run matrix with reasons | **No live-model behavior was observed at all.** Every activation claim here is unmeasured |
| AC6 review-ready revision + complete handback | **Met** | Five review rounds (§6); this document | All five reviewers were fresh same-vendor subagents. Not an external signal. Yours is the first |

## 5. Validation, and the regression it caught

All exit codes below are from runs performed by the primary session against the shipped tree, not quoted from a reviewer.

| Command | Exit | Result |
|---|---|---|
| `validate_trigger_metadata.py` | 0 | 16 entries, 6 lifecycle scenarios, fresh compact-index parity |
| `generate_compact_index.py --check` | 0 | compact index fresh |
| `check_skill_provenance.py` | 0 | manifest complete (14 skills) + compatibility floor satisfied |
| `git diff --check` | 0 | no whitespace defects |
| `scan_credentials.py --range 3d36854..HEAD` | 0 | no findings. Run by hand: `core.hooksPath` is `.git/hooks` and holds no `pre-commit`, so the hook did **not** fire on these commits |
| `pytest` targeted set (3 files) | 0 | 132 passed |
| `run_skill_eval.py` | 0 | 27 pass / 0 fail / 19 known gap (baseline 19) — unchanged |
| `pytest tests/ci/ tests/guard/ .agentcortex/tests/` (CI path set) | 0 | **947 passed, 1 skipped in 65m37s** against the shipped tree. An earlier run against the pre-compression tree exited **1** -- see below |
| `validate.sh` / `validate.ps1` final | 0 / 0 | twin parity exact, WARN set identical line for line. Counts deliberately NOT repeated in this document: the same figure lived in three files and any write to any of them could stale it. Single authoritative record: `## Final Verification` in the Work Log, written after the last edit to it |

### The full suite found a regression that everything else missed

The first wording passed the targeted 132-test set, `validate.sh`, and two independent review rounds. The full suite failed:

```
test_aggregate_current_total_stays_under_355k
AssertionError: 355225 not less than 355000
```

Caused by this change. Measured against a detached worktree at the base commit rather than reasoned about:

| tree | aggregate `current_total_tokens` | vs ceiling 355000 |
|---|---|---|
| `3d36854` base | 354569 | headroom 431 |
| first wording | 355225 | **over by 225 — FAIL** |
| shipped | 354887 | headroom 113 — PASS |

Mechanism, read from `analyze_token_lifecycle.py` rather than guessed: `estimate_tokens` counts the **whole SKILL.md** as `ceil(len/4)`, and each file is charged once per scenario it is a candidate for (`current_probe_tokens`), plus first-load and continuation multipliers over its `phase_scope`. Measured cost of one character added to either file: **~2.33 tokens**, about 8.9x its own size, across the six lifecycle scenarios.

**Resolution: compression, not a ceiling bump.** That test comment records four prior transitions (350k to 352k to 353k to 354k to 355k), each justified in place and the most recent labelled an owner-approved minimal bump. This addition is not deletion-funded, so raising the ceiling was not mine to take. Both sentences were compressed until they fit; every activation condition the reviews required is retained, and the technique and benefit clauses carry the loss.

**This is a structural finding, not just an incident.** `app-init.md:200` requires a skill `description` to carry "both capability and activation context". The token ratchet charges about 8.9x for every character of exactly that. At the base commit the whole repository had 431 tokens of headroom, which is roughly **185 characters of SKILL.md growth for all fourteen skills combined**. Meeting the description contract across the remaining twelve skills is not affordable under the current ceiling. This unit does not resolve that tension; it only pays for its own two sentences.

**Two process errors of my own, recorded rather than tidied:**

1. The suite was launched as `pytest ... > out; echo $?; tail -3 out`. The tool-level exit code reported was the exit code of `tail`, which was 0; pytest exited 1. This is the same shape as the repository's own `[signal-preservation][HIGH]` Global Lesson, where a `tee` swallowed a validator status — reproduced by me, in this session, against a lesson already written down. The real code survived only because the `echo` captured it separately.
2. The Work Log asserted a passing test phase before any receipt supported it, and had grown past the 12KB compaction threshold. Both were caught by the third reviewer, not by me. `/review` section "Work Log Compaction Check" should have run before the review phase and did not.

## 6. Review rounds

Every round used a **fresh `acx-reviewer` subagent** given the diff plus the acceptance criteria only, refute-only framing, no implementation rationale — `review.md` section "Adversarial Reviewer Freshness Invariant". **None was a self-review.** None was an external signal either: same vendor, same training data, so per Global Lesson `[audit-method][HIGH]` they share my blind spots.

Every load-bearing claim any reviewer made was re-verified by me against the files before I acted on it, per `[audit-verification][HIGH]`. Two cases where that mattered: R2 independently recomputed the content hashes, and I checked them against the checked-in JSON before believing them; R3 raised three factual corrections, and each was checked against the cited source.

### R1 — NOT READY

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | BLOCKING | `production-readiness` was a disjunction where the phase qualifier bound only the first arm, leaving the second phase-unbounded. The pre-change text carried `Pre-ship` as its only phase word, so the edit was a **net loosening** on the exact constraint the brief singled out | Fixed |
| F2 | ADVISORY | `observability` had been dropped, though it is a registry `scope_signals` value and half of `intent_patterns: observability check` | Fixed |
| F3 | ADVISORY | dropped the "fixed but nobody knows why" case the body lists | Fixed |
| F4 | ADVISORY | hotfix incident response is the body first When-to-Use bullet; no description named it | Fixed |
| F5 | ADVISORY | three description surfaces disagree, and nothing binds them | **Not fixed — see section 9** |
| F6 | ADVISORY | my commit message overclaimed cross-host reach | Fixed by amending the unpushed commit, so the false claim never survives in the log |
| — | ADVISORY | over-trigger risk on a `cost_risk: high` skill | **Declined, with reason**: the phrase is the registry own `scope_signals` wording; narrowing it would make the description disagree with the metadata it summarises, and `load_policy: on-failure` already gates the load |

### R2 — PASS, on the pre-compression text

Confirmed F1 through F4 fixed, and found something I had not: `Pre-ship` is an **open interval** that admits `/implement`, whereas `at review and ship` is a closed enumeration equal to `phase_scope`. The new text is therefore tighter than what existed before this unit started, not merely restored. It could not construct an agent-initiated `/implement` prompt. It also caught a false clause in my commit message — I had written that two conditions are the ones the body "ranks first", when one of them is the body last bullet — which I verified and corrected.

### R3 through R6 — on the compressed text, because the R2 verdict did not cover it

The shipped text is not the text R2 read, so the R2 verdict was not reused. R3 checked whether compression had silently dropped a required property: **all six held.** It named precisely what compression cost — chiefly `production-readiness` losing the "not just debug consoles" contrast, which is the skill most discriminating semantic — and judged each loss summary-grade rather than a misrepresentation, since the body is `load_policy: phase-entry` and loads at those phases anyway.

R3 returned **NOT READY**, and it was right to: not on the text, but because the Work Log claimed a passing test phase and a green full suite that no receipt supported, and carried no review receipt covering the compressed revision. Those were fixed rather than argued with. R3 also corrected three inaccurate claims in my commit message: a bump count ("five prior bumps ... owner-approved" — it is four transitions, one so labelled), a field count (I had written "seven fields" — six summary plus eight mirror), and a claim-versus-diff gap ("hotfix incident response" against the delivered token "a hotfix"). The first and third were right and were corrected. The second was not: R3's replacement count was itself wrong, R5 later caught it, and the figure above is now counted from `validate_trigger_metadata.py:81-96` directly. A correction is not automatically correct -- it needs the same verification as the finding it replaces.

R4 then re-checked whether fixing R3's findings had introduced new ones, and it had. It proved by execution that both validators exited **1** on `illegal gate progression ... NOT_READY-review->test`, while the Work Log asserted they exited 0 -- the same look-timing defect as before, because the validator run was quoted before the receipt write that broke it. It also found the phrase "R3 PASS-on-text" in a section summary where the receipt says NOT READY, a "none uncommitted" claim in this document while three files sat uncommitted, and the bump-count claim I had corrected here and in backlog #199 still standing uncorrected in the tracked compaction overflow. All were fixed. The lesson this unit keeps re-teaching, twice on the same rule: **an evidence record edited in the same file that carries the evidence needs its verification re-run after the last edit, not before.**

R5 and R6 then audited the repairs rather than the code, and each found real defects in the record: three gate-receipt timestamps I had hand-authored as plausible-looking values that had not happened yet; a field count I adopted from R3 without re-deriving it, which was itself wrong; a validator figure invalidated by a later write for the third and fourth time; and - introduced by my own fix for that last one - a `## Final Verification` section that three files pointed at and which did not exist. All were corrected.

**The honest limitation on this handback**: six rounds ran, and R6's findings were resolved AFTER its verdict. No seventh round reviewed the final bytes. What every round from R2 onward did agree on is the product itself: the two description lines never changed after the compression, and each round re-verified them against the bodies and the registry. The defects were in how the work was recorded, not in what it changed - which is precisely why an external reviewer should look at the record as hard as at the diff.

Advisories declined, with reasons recorded: replacing a comma with a dash to close a strained parse of `production-readiness` (R3 itself calls the parse strained, and each further text change invalidates the review round that covers it); and `failed fix` widening the registry `repeated-patch-failure` to a single failure (an over-trigger whose remedy — investigate before patching again — is what the guardrails want anyway).

## 7. The finding that bounds every claim in this unit

The brief premise is that a skill `description` is a skill-selection input. That is what the vendor documentation says. **It is not what this repository does**, and I could not find a way to make it true without changing the layout.

Verified, not assumed:

- No host skill-discovery directory exists anywhere in the tree. `find . -maxdepth 3 -type d -name skills` returns exactly `./.agent/skills` and `./.agents/skills`. There is no `.claude/skills`, no `.gemini/skills`, no `.codex/skills`.
- `deploy.sh` never creates one: `grep -n "claude/skills\|gemini/skills\|codex/skills" .agentcortex/bin/deploy.sh` returns nothing. Its skill block ships `.agents/skills` and `.agent/skills` as they are (`deploy.sh:725,875-889`).
- Discovery here is **instruction-mediated, not host-scanned**. `CLAUDE.md:26` tells the agent where metadata and bodies live, and activation is decided by the AI reading `routing.md` section 3 and the table in `bootstrap.md` section 3.6. `repo-gotchas` section 16 already records that this repo has three trigger surfaces and that the registry one has no runtime consumer.
- The compact index, which phase-entry loading consults first, carries **no description field at all**: `'description' in json.dumps(index)` is `False`.

So what this change is:

- a **documentation-contract fix the repo already required of itself** (`app-init.md:200`);
- an improvement to what an agent reads when phase-entry loading opens the SKILL.md on a cache miss;
- live for any adopter who does place these skills in a host own skills directory.

What it is **not**: evidence that any model now selects either skill more accurately, here or anywhere. No such measurement was made, and the layout above means the obvious in-repo experiment would have measured nothing.

## 8. Cross-model comparison: not run, with reasons

| Host | Status | Reason |
|---|---|---|
| Gemini CLI | **not run** | not installed (`command -v gemini` finds nothing). The brief forbids installing a host to fill the matrix |
| Grok | **not run** | not installed (`command -v grok` finds nothing). Same reason |
| Claude Code | **not run as an A/B** | installed, but per section 7 there is no `.claude/skills/` in this repo, so a before/after run would not exercise the edited surface. Building a fixture that wires one would measure a synthetic layout, and a handful of stochastic runs is a smoke test, not an uplift |
| Codex CLI | **not run as an A/B** | installed, but it reads `agents/openai.yaml short_description`, which this change deliberately does not touch (section 9). A run would measure the unchanged surface |

No row is inferred. There are no success rows because there are no runs.

## 9. The one decision I did not take

Each of these two skills publishes **three** descriptions, and after this change they disagree:

| Surface | Consumer | State |
|---|---|---|
| `.agents/skills/<name>/SKILL.md` | vendor-neutral; phase-entry body load | **new wording** |
| `.agent/skills/<name>` | Antigravity summary stub | old wording |
| `.agents/skills/<name>/agents/openai.yaml` `short_description` | Codex mirror | old wording, and for `systematic-debugging` it is "Skill for systematic debugging workflows." — a content-free placeholder |

Nothing binds them. `validate_trigger_metadata.py:81-96` compares summary and mirror against the registry on seven and eight fields respectively, and `description` is in neither set. The rule that would bind them — `trigger_runtime_core.py:693-698`, "mirror short_description must derive from manifest description" — is reached only for a skill shipping a per-skill `manifest.yaml` (`validate_trigger_metadata.py:98-100`), and no first-party skill ships one. That inert check is why the divergence survived unnoticed.

**Why I did not fold it in:**

1. Your section 3 preserve-list names "existing adapters" explicitly, and the product diff you authorised is two descriptions plus the generated index. Widening a change you have to adjudicate is the more expensive error.
2. It is not a wording edit. `.agent/skills/**` is guard-protected (`.agent/config.yaml:192`), so it must go through `guard_context_write.py`; and `.agentcortex/tools/sync_skills.sh:13,28` copies `agents/openai.yaml` **over** `.agent/skills/<name>`, which would reinstate the old text and destroy the `phases:` and `load_policy:` keys `validate_trigger_metadata.py:82-87` requires. Fixing it properly means first deciding which surface is authoritative.
3. Section 5 adds a third reason discovered after the fact: under the token ceiling there is no headroom to widen the same wording across more surfaces even if the decision went the other way.

Against all that: the stated goal is suitability for Claude, Gemini, Grok **and Codex**, and only the non-Codex surface improved. If you judge that decisive, the remedy is a follow-on unit, not a patch to this one.

Filed as backlog row **#198** (`Kind: review-finding`, `Labels: skill-ecosystem`, `Tier: quick-win`), paired with **#187**, which records the same shape one layer over. The ceiling conflict from section 5 is filed separately as **#199** (`Labels: governance`, P2), because it blocks #198 as much as it blocks any further description work.

## 10. Remaining risks

1. **Over-triggering.** `systematic-debugging` now names five conditions where it named none, and `unexpected behavior` is broad on a skill the registry marks `cost_type: execution`, `cost_risk: high`. Mitigated only by `load_policy: on-failure` and the phase gate, neither of which this change touched.
2. **Missed activation.** `production-readiness` names four scope signals; the registry lists seven (`new API endpoint`, `new service class`, `new background job` are absent). That gap predates this change and matches the body own When-to-Use list, so the description is faithful to the body — the body is the narrower document.
3. **Compression cost.** `production-readiness` lost the "not just debug consoles" contrast, which is what distinguishes a production sink from any log call. R3 judged it summary-grade because the body loads at those phases anyway. It is the first thing to restore if headroom ever appears.
4. **Neither risk 1 nor 2 is measured**, and section 7 explains why the in-repo experiment would have been vacuous rather than merely skipped.
5. **Cross-surface divergence** (section 9), left open by decision.
6. **No guard.** Nothing can detect a future regression of this wording. A test was refused rather than added, on the brief own AC4 wording plus `repo-gotchas` section 16; the reasoning is in the Work Log.

## 11. Where to look first

1. **Section 7.** Is the conclusion right that descriptions do not participate in selection in this repo? Everything else is scoped by it. If you can name a runtime consumer that ranks by `description`, my scoping is wrong and this unit under-delivers.
2. **Section 9.** Adjudicate the scope decision. I may have read "preserve existing adapters" too literally.
3. **Section 5, the ceiling tension.** A governance contract requires prose that a governance ratchet cannot afford. That is a design conflict this unit surfaced and did not fix.
4. **The two sentences against the bodies and the registry.** R1 found a phase-binding regression I did not, and R3 found evidence claims I had not earned. Assume there is a third.
5. **Verification provenance.** Section 5 lists exit codes for runs I performed. Re-run anything you would otherwise be taking on trust — including the token figures, which are reproducible with `analyze_token_lifecycle.py --root . --format json`.
