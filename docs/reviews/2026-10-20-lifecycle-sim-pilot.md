---
status: review-snapshot
date: 2026-10-20
backlog: 239
---

# Lifecycle Simulation Pilot (#239): Six Releases, Governed vs No Framework

**Read first:** this is a pilot, n = 1 per arm. It can show a large difference or a harness
problem; it cannot show a small one. The owner approved the pilot design on 2026-10-20 (chat)
before it ran, including the decision rule below.

## Question

Every earlier simulation used single small tasks. The framework's claim is about a product's
whole lifecycle: decisions later versions must honour, regression across releases, style kept
over time. Does the governed workflow do better there than no framework, and at what cost?

## What was run

- **Product:** `ledgerlite`, a ~110-line Python expense CLI with `docs/STYLE.md` (error and
  warning format, exit codes, two-decimal amounts). Built once, git-committed.
- **Six steps, each a fresh `claude -p` session; state carried only by the repo:**
  1. fix a float total bug; 2. `list --category`; 3. **decision step**: store money as
  integer cents (`amount_cents`), keep old float ledgers loading, record the decision;
  4. CSV import; 5. **2.0**: one file per month with migration of the old single file;
  6. **3.0**: budgets with over-budget warnings. Steps 4–6 never restate the decision or
  the style guide.
- **Arms:** control (task text only) and governed (agentic-os at this wave's tip, deployed
  with `deploy.sh`; prompt = the README's `/bootstrap` entry). sonnet only
  (claude-sonnet-5-5); one chained run per arm.
- **Scoring:** hidden tests the agents never saw, all through the CLI: each step's feature
  tests, every earlier step's tests (regression), decision tests (no float stored anywhere,
  steps 4–6) and style tests (new commands' error format and exit codes). Before the run,
  every hidden test was shown to fail on the base product and pass on a reference solution.
  Up to two identical "go ahead" follow-ups were sent when a session changed no product file.

**Pre-registered decision rule:** the governed arm "helps the lifecycle" only if, over steps
4–6, its decision + regression pass count beats control by at least 2; anything less is
reported as no measurable benefit.

## Results

As scored by the pre-registered tests:

| | Control | Governed |
|---|---|---|
| Step feature tests (9) | 8/9 | 7/9 |
| Regression (19 cumulative) | 18/19 | 18/19 |
| Decision adherence, steps 4–6 (6) | **6/6** | **6/6** |
| Style adherence (4) | 4/4 | 4/4 |
| Cost | **$0.79** | **$41.79** |
| Wall time | ~3 min | ~74 min |
| Follow-ups needed | 0 | 6 |

Decision rule, steps 4–6: control 21/22, governed 21/22. **No measurable benefit.**

Every miss was checked in the transcripts and code:

- **Step 5 migration (both arms).** The test asserted that the monthly files exist right after
  a read-only `list`; the prompt asked only that old data survive. Both arms migrate on the
  first write instead. Re-run without that one assertion, both arms pass at steps 5 and 6
  (`scripts/relaxed_s5.py`). This is a harness defect, equal in both arms.
- **Step 3 (governed only).** The governed session stopped after `/plan`, as the workflow
  intends: it wrote `docs/specs/money-integer-cents.md` and asked two owner questions (reject
  sub-cent input? freeze the spec?). The harness counts a `docs/` change as product work, so it
  sent no "go ahead" and the step ended with nothing implemented. At step 4 the next session
  found the draft spec and implemented it; the decision tests pass from step 4 on. A real owner
  would have answered, so this is a harness artifact, but it also shows the cost of the
  framework's stop-and-ask on a single-session request.

With both corrections the arms are equal on every quality measure.

## What differed

- **Cost: about 53×.** About $12 of the governed $41.79 ($12.13, steps 4–6) is Opus spent by `acx-reviewer`
  subagents (pinned model, #236). Most of the rest is long Sonnet sessions: step 5 alone took
  103 turns and $26.53.
- **Where the decision was recorded.** Control wrote it into `CLAUDE.md` and `README.md`.
  Claude Code loads `CLAUDE.md` automatically, so that is an effective way to carry a decision
  forward. Governed wrote two ADRs, three specs, an L2 domain log, SSoT entries and archived
  Work Logs. Both carried it; the governed records are richer, but nothing in steps 4–6
  needed more than the plain note.
- **Tests written.** Governed grew the product's own suite to 23 tests; control to 13.

## Why the pilot cannot show a lifecycle benefit yet

Control passed every real requirement without help. The decision (integer cents) is visible
in the code from step 3 on, so any later session rediscovers it by reading `store.py`; the
style guide is a file in the repo. The tasks were within what sonnet does alone, so there was
no headroom for the framework to add quality. A benefit, if there is one, would show only
where the earlier decision is **not** recoverable from code, where a session must honour
something said in an earlier conversation, or with a weaker model.

## Before a full run

1. Count only `ledgerlite/` and `tests/` as product changes (send "go ahead" after a
   plan-only session), and drop the over-specified step-5 assertion.
2. Add decisions that the code does not reveal (e.g. "never delete a user's data, archive it";
   "categories are case-insensitive") and later steps whose natural implementation breaks them.
3. Add a weaker-model arm (haiku) where unaided quality is lower.
4. Unpin the reviewer model (#236) or account for it separately; cap cost per run.

## Evidence

Owner's local evidence archive `sim-239-20261020`: build, hidden-test, reference, run, score
and relaxed-check scripts; both arms' repos with per-step commits; every session's stream;
per-step rescore output; `scored.json`.
