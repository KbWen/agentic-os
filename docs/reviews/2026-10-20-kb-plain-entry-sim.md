---
status: review-snapshot
date: 2026-10-20
spec: docs/specs/kb-plain-entry.md
---

# Declared KB on the Plain-Task Entry: Re-run of Round 3

Backlog #234. The 2026-10-18 simulation found that a plain-task session ("Read `AGENTS.md`
and follow it" + a task) consulted a declared knowledge base 0/12 times on KB-covered
tasks. This change adds one present-only startup line to `AGENTS.md §vNext State Model`
and `CLAUDE.md` Startup. This page records the runs that decide whether it ships.

## What was run

The 2026-10-18 Round 3 harness, unchanged (`round3-build.py`, `round3-run.py`,
`round3-score.py` and `tasks.json` are byte-identical): notekit product, a KB with 6
routed domains + 3 decoys, declared only in `knowledge_sources` (no prompt hint), plain
entry. The fixture was built from this branch's working tree.

- **Run A** — first wording. sonnet (claude-sonnet-5-5) and haiku (claude-haiku-4-5), 6
  covered + 2 uncovered tasks, one session each: 16 sessions.
- **Run B** — after review, the wording gained "a task outside the KB's routes needs no KB
  read" (both files) and the tiny-fix skip (AGENTS.md). sonnet only, 8 tasks plus a second
  session of each uncovered task: 10 sessions. haiku was not re-run: it never read the
  capabilities file in Run A, so the wording cannot reach it.

"Consulted" (the scorer's definition) means a standard page, digest or routing query was
read; the startup read of the capabilities file alone does not count. "Rule applied" is
the hidden acceptance test checking the KB-only rule.

## Results

| Arm | Covered: consulted (scored) | Covered: consulted (strict / transcripts) | Covered: rule applied | Uncovered: KB page read (transcripts) | Cost |
|---|---|---|---|---|---|
| sonnet plain, 2026-10-18 baseline | 0/6 | 0/6 | 0/6 | 0/2 | $2.22 (8) |
| sonnet `/bootstrap`, 2026-10-18 | 5/6 | 3/6 (strict, per that report) | 3/6 | — | $16.24 (8) |
| sonnet plain, Run A | 4/6 | 6/6 | **6/6** | 1/2 (release standard) | $1.93 (8) |
| sonnet plain, Run B | 5/6 | 6/6 | **6/6** | 1/4 (179 chars) | $2.24 (10) |
| haiku plain, 2026-10-18 baseline | 0/6 | 0/6 | 0/6 | 0/2 | $0.99 (8) |
| haiku plain, Run A | 0/6 | 0/6 | 0/6 | 0/2 | $1.97 (8) |

- **The scorer undercounts.** Its KB pattern is `../kb` or `/kb/`. In Run A's logging and
  caching tasks the transcripts show `cd <run dir>/kb && cat pages/logging.md` and
  `cat pages/caching*`, which it misses. A scan of all 16 baseline plain transcripts found
  no KB access of any form, so the baseline 0/6 is not the same artifact, and the hidden
  tests are identical: "rule applied 6/6 vs 0/6" compares like with like. Right-route reads
  are likewise 6/6 from Run A's transcripts (3/6 scored).
- **Off-route reads on covered tasks** (Run A): the migration task also read the
  `timestamps` page and the `sql-style-guide` decoy; the password task also read `logging`.
- **Uncovered reads.** The README task read nothing in any run. On the "bump the version"
  task every session read the KB manifest to check whether the task is routed (Run A 6,272
  characters in total; Run B 3,179 and about 4,100), and some went on to the `release-standard`
  page, which the fixture labels a decoy: Run A 1/1, Run B 1/2 (179 characters). The other
  Run B session read the manifest, found no route and wrote "out of scope" in its Work Log;
  the scorer counted that Work Log write (224 characters) as a KB read. So the added cost on
  an uncovered task is mostly the routing check, about 3–4k characters. AC-5 ("no increase in
  KB reads on uncovered tasks") is **not met** as written.
- **haiku:** no change in KB behaviour; it never read the capabilities file. Its cost rose
  because it invoked `/review` and `/test` skills in 6/6 covered runs against 1/6 in the
  baseline, including a `code-review` skill from the host's global configuration — the
  headless sessions are not isolated from user-level skills. This stays with #235.

## Decision

AC-4 met: covered-task consults 0/12 → 6/12 from transcripts (sonnet 6/6, haiku 0/6), KB
rule applied 0/12 → 6/12, sonnet cost about the same as the plain baseline and an eighth of
the `/bootstrap` entry. AC-5 as written not met: an uncovered task now costs a routing check against the KB
manifest (about 3–4k characters) and, in 1 of 2 Run B sessions, one related page. An
earlier owner ruling was given on miscounted figures (~200 characters, 2/2); re-asked with
these, the owner amended AC-5 to allow one routing check plus one related page (2026-10-20).
Ship.

## Limits

- One or two sessions per cell: directions, not significance.
- The fixture was built five commits after the baseline (including `bootstrap.md`
  kb-consult and installer changes); plain sessions read `bootstrap.md` 0/26 (Run A 0/16, Run B 0/10), so those
  changes were not on their path.
- Only the Claude path was measured, with both `CLAUDE.md` and `AGENTS.md` carrying the
  line. The AGENTS.md-only path (Codex, Gemini, Copilot) is untested.
- Same single-task fixture as the baseline: nothing here speaks to multi-version use (#239).

## Evidence

Owner's local evidence archive `sim-20261020-kb-plain` (Run A) and its `r2/` (Run B):
scripts, `tasks.json`, every session's stream and meta, run logs and scored output.
