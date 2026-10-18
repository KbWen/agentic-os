---
status: living
title: v1.8.34 Release Simulation
date: 2026-10-18
baseline: ddd6af0d8a18dd61889b178ce311d49c62cbb9f2
---

# v1.8.34 Release Simulation

After cutting v1.8.34 the owner asked for simulation and comparison tests of token use, the development flow, the framework's philosophy (AGENT_PHILOSOPHY P1–P10), external lookups and knowledge-base consults, with `sonnet` and `haiku`. This page records what was run, what it measured, what it could not measure, and where each finding was filed.

**Scope limit, read first:** every result here comes from **single, small, one-session tasks** on a tiny product (`slugtool`). The framework exists to manage a product across its whole lifecycle and many versions: cross-session state, decisions that later versions must honour, regressions, backlog/spec/ADR upkeep. None of that was exercised. No conclusion below about value or cost transfers to that use. The longitudinal design that would test it is backlog #239.

## What was run

All sessions were headless `claude -p` with host `CLAUDE*` environment variables cleared. Each ran in a fresh copy of a committed fixture and was scored deterministically from its stream-json transcript and the resulting tree, never from the agent's own summary. Every finding below was re-checked by reading transcripts.

- **Mechanical comparison.** Both release tags were cloned from GitHub. Checks: fresh install, upgrade 1.8.33 → 1.8.34, the four fixed scenarios (#221, #190, #233, plus upgrade).
- **Round 1 A/B.** A tiny bugfix with hidden acceptance tests. Arms: no framework, v1.8.33, v1.8.34. sonnet-5.5 and haiku-4.5; n = 3 for the control and 6 for each framework arm.
- **Round 2.** Five scenarios:

  | Scenario | What it probes |
  |---|---|
  | s1 | Feature flow, with an unrelated `TODO: refactor` bait function |
  | s2 | A test runner that cannot collect |
  | s4 | User pressure to skip verification |
  | s5 | A declared knowledge base whose standard the hidden tests check |
  | s6 | A volatile external fact (current `actions/checkout` / `actions/setup-python` majors, both `v7` on 2026-10-18) |

  Three arms: no framework, framework with a plain task ("Read `AGENTS.md` and follow it" + task), and framework with the README's documented `/bootstrap` entry. 48 + 14 sessions. A run left unfinished received up to two identical "go ahead" replies, same rule for every arm, and these were counted.

Resolved models: `claude-sonnet-5-5`, `claude-haiku-4-5-20251001`, and `claude-opus-5-5` (only via a framework subagent; see #236).

## Results

**Release behaviour (mechanical).** v1.8.34 fixed what it claimed:

| Scenario | v1.8.33 | v1.8.34 |
|---|---|---|
| `CP_FLAG=-i` | drops a manifest row | keeps every row |
| `-i` / `-n` on a skipped copy | misreports it as `[OVERWRITE]` | reports `[KEPT]` |
| Unsafe capabilities file at a retargeted path | `PASS` | `FAIL` |
| Feature at ship with Test Gate Results `none` | not caught | AC-6 FAIL |
| Feature at ship with recorded results | passes | passes |

The upgrade updated all 206 files with no sidecars. Product files were untouched and validate showed `fail=0`.

**Outcome quality.** Hidden tests were equal between framework and control in every scenario except one: in the KB scenario on haiku, the framework arm scored lower (3/12 vs 6/12).

**Entry path (s1–s6, framework arms).** With a plain task, 0/24 sessions read `bootstrap.md`, `downstream-capabilities.yaml` or any `SKILL.md`. Agents followed `CLAUDE.md` Startup instead (SSoT 18/24, guardrails 11/24). With `/bootstrap`, 14/14 read `bootstrap.md`, and nearly every run stopped to ask before continuing. Filed as #234.

**Knowledge base (s5).**

| Model | No framework (told `../kb`) | Plain entry | `/bootstrap` |
|---|---|---|---|
| haiku | 3/3 consulted | 0/3 | 0/3 |
| sonnet | 3/3 | 3/3 | 3/3 |

sonnet read pages directly rather than via the manifest digest in most runs. Filed as #235.

Why haiku consulted the KB without the framework but not with it: every arm got the same sentence ("Team engineering standards live in the knowledge base at ../kb").

- **No framework.** haiku read `../kb` within its first 6–8 actions.
- **Framework.** haiku opened with "I'll follow the governance flow" and read SSoT, guardrails and state_machine; on the `/bootstrap` path it read `bootstrap.md` up to 3 times, the file whose §1b loads the KB. It mentioned the KB in none of its 6 runs.

The procedure displaced the one-line pointer. Two causes remain possible, instruction dilution or a long conditional step that a small model reads but does not execute; separating them is the next step in #235.

**External lookup (s6).** haiku used `checkout@v4` / `setup-python@v5` in 6/6 runs across all arms and never fetched. sonnet looked the versions up (`gh api` or WebFetch) and was correct in 6/6 across all arms. The doc-lookup skill was never loaded on the plain entry. Filed as #235.

**Philosophy probes.**

| Principle | Result |
|---|---|
| P9 scope | The bait function was untouched in 100% of runs, all arms. |
| P3/P4 under pressure | Told "don't run tests", sonnet still verified 2/2 in the framework arm vs 0/2 in the control, where it honestly said it had not run them. haiku in the framework arm wrote a "✓ verification" without running anything (1/2). Filed as #238. |
| P4 with a broken runner | sonnet disclosed that pytest could not collect (4/4). haiku never disclosed it (0/4) and reported success in both arms. Filed as #238. |
| P7 cross-model | Not demonstrated. The good behaviours tracked the model, not the framework. |

**Process.** sonnet wrote template Work Logs and receipts in order on the `/bootstrap` path; on the plain path it never wrote a bootstrap receipt. haiku wrote its own Work Log formats. The validator caught some of these and missed a frontmatter-only log. Filed as #237.

**Cost** (median per run, small feature s1):

| Arm | sonnet | haiku |
|---|---|---|
| No framework | $0.10 | $0.12 |
| Plain entry | $0.29 | $0.43 |
| `/bootstrap` entry | $1.99 (≈3.8M context tokens) | $0.62 |

Hidden-test outcomes were identical across all three arms. On the `/bootstrap` path, `acx-reviewer` dispatches added Opus cost (#236). Added as a dated note to #231.

## Limits of this run

- **Sample size.** n = 2–3 per cell, so results are directions and counts, not significance. A round-1 cost gap (p ≈ 0.06) was traced to sampling: no session read any file that differed between the two versions.
- **Phase-level token split was not measurable.** Agents rarely mark phases in a machine-detectable way, so only totals and governance-read volume are reported.
- **Headless sessions.** A user would answer "go ahead" interactively, so follow-up replies were scripted and counted.
- **Harness leak.** The harness leaked one file. A no-framework control session ran `cd -`, which used the shell's inherited `OLDPWD`, and appended a `tests/test_slug.py` to this repository's checkout. The file was found and removed before this intake. No framework-arm session wrote outside its folder. Future harness runs should clear `OLDPWD`.
- **Not measured: the product lifecycle.** This covers multi-version iteration, cross-session continuity, decisions carried across releases, and regression prevention. Proposed as #239.

## Evidence

The scripts, the scored JSON and every session transcript (stream-json and meta, with SHA256SUMS) are kept in the owner's local evidence archive under `sim-20261018`. The harness can be rebuilt from its `build.py`, `run.py`, `score.py` and `report.py`.
