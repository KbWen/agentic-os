---
status: living
title: Optimization Roadmap
created: 2026-06-02
last_updated: 2026-06-02
---

# Optimization Roadmap

This roadmap captures the next wave of framework optimizations for agentic-os,
organized into three tracks. It is the planning layer that sits *above* the
[product backlog](specs/_product-backlog.md) and the GitHub issue tracker: the
backlog holds discrete units of work, the issues hold actionable tickets, and
this document explains **why** the work is grouped the way it is and **in what
order** it should land.

Items already filed as issues are linked inline. Items still in the "candidate"
state are described here first; each graduates to a backlog row + issue once it
clears the same bar as everything else (clear scope, real motivation, an owner
willing to write the spec).

> **2026-06-02 update.** A research pass first filed a large ticket set
> (#45–#64 / issues #151–#164), but most were **retracted on review** — they were
> conceptual ports with no verified problem or consumer in this repo (DELETE-bias).
> Only three survived with a demonstrated gap: token-baseline drift
> ([#157](https://github.com/KbWen/agentic-os/issues/157)), CI hardening
> ([#163](https://github.com/KbWen/agentic-os/issues/163)), and downstream
> `local_guardrails.md` ([#164](https://github.com/KbWen/agentic-os/issues/164)).
> The "candidate" lists below are **illustrative, not endorsed** — each still
> needs a verified problem + consumer before it earns a ticket. Treat
> [`specs/_product-backlog.md`](specs/_product-backlog.md) as the source of truth.

## How this roadmap was derived

Two inputs shaped it:

1. **Our own accumulated debt** — surfaces in the framework that grow unbounded
   (archive, Spec Index, audit ledger), honor-system rules with no enforcement,
   and token cost that scales with project age rather than task size.
2. **A survey of more mature governance patterns** — progressive summarization,
   LSM-style compaction, tiered retention, machine-checkable policy, and
   structured (rather than prose) evidence. These are well-trodden patterns; the
   work here is adapting them to our state model and cross-platform constraints,
   not inventing them.

The guiding bias is the same one in `engineering_guardrails.md`: **prefer
deleting an unenforced rule over adding a second unenforced rule**, and prefer a
cheap cold-path check over hot-path friction.

---

## Track 1 — Lifecycle & growth governance (highest leverage)

**Problem.** Several persistent surfaces grow with no upper bound and rely only
on advisory, per-surface compaction: `.agentcortex/context/archive/`, the Spec
Index in `current_state.md`, the Global Lessons registry, and the hash-chained
`INDEX.jsonl`. Read cost therefore scales with project *age*, not task size.

**Direction.** A single, config-driven document-lifecycle engine that gives
every surface a consistent aging policy, with the individual compaction passes
hanging off it. This is the cheapest, lowest-risk track — the patterns are
proven and the blast radius is cold-path only.

| Item | Issue | Tier | Notes |
|---|---|---|---|
| Tiered document lifecycle engine (umbrella) | [#140](https://github.com/KbWen/agentic-os/issues/140) | feature | 4-tier state machine + `config.yaml` triggers |
| Archive GC + `INDEX.jsonl` rotation | [#141](https://github.com/KbWen/agentic-os/issues/141) | feature | preserve chain anchor across rotation |
| Domain Doc L2 superseded-entry archival | [#142](https://github.com/KbWen/agentic-os/issues/142) | quick-win | independent of the engine |
| Spec Index compaction (status + age filter) | [#143](https://github.com/KbWen/agentic-os/issues/143) | quick-win | fold shipped specs > N days |
| Warm→Cold LLM summarization in `/ship` | [#144](https://github.com/KbWen/agentic-os/issues/144) | feature | progressive summarization at tier boundary |

**Recommended starting point.** Land #142 and #143 first (independent quick-wins
that immediately shrink SSoT read cost), then the engine (#140), then #141/#144
on top of it.

---

## Track 2 — Governance mechanization & observability

**Problem.** Our SSoT already records the core lesson:

> Every "MUST" rule that depends on agent self-attestation is honor-system and
> functionally theatre. Every "MUST" needs a hook, validator, test, or external
> observer — or it should be deleted.

Today several load-bearing rules (single-writer Work Log ownership, gate
receipts, confidence gating) are prose-only. This track turns the highest-value
ones into machine-checkable signals, and replaces free-form evidence with
structured, queryable records.

**Direction.**

- **Hard Work Log lock** — promote the advisory `<worklog-key>.lock.json` to a
  real blocking lock with stale-lock detection. → [#147](https://github.com/KbWen/agentic-os/issues/147)
- **Skill validation pipeline** — meta-governance that keeps stub ↔ `SKILL.md` ↔
  registry ↔ compact-index in sync, plus description-quality lint. → [#146](https://github.com/KbWen/agentic-os/issues/146)

**Candidates (not yet filed):**

- **Structured gate-receipt store** — migrate gate receipts from Work Log
  Markdown to an append-only `.jsonl` ledger with a small query tool, so
  "did this branch pass review?" becomes a programmatic check instead of a grep.
- **Governance observability signals** — lightweight, advisory phase-entry
  fields (e.g. confidence value, guardrails sections actually loaded, re-read
  counter) that make currently-invisible self-attestation auditable at `/review`
  without adding hot-path friction.
- **Contract / spec schema validation** — define JSON Schema for spec and Work
  Log frontmatter and validate against it, replacing bespoke bash field-presence
  checks with a single schema + clear failure messages.
- **Evidence-gated delete-bias tool** — a small diff harness that re-runs a
  governance eval with and without a candidate rule; zero behavioral diff ⇒ the
  rule is vacuous ⇒ delete candidate. Turns the DELETE-bias principle into a
  reproducible measurement instead of a judgement call.
- **End-to-end phase-transition tests** — a harness that simulates the full
  lifecycle (bootstrap → … → ship) and asserts gate enforcement, complementing
  the existing unit tests. (Relates to existing issue
  [#16](https://github.com/KbWen/agentic-os/issues/16).)

---

## Track 3 — Token discipline

**Problem.** Always-loaded governance mass and full-cost skill bodies are paid on
every conversation, including tiny-fix paths that don't need them.

**Direction.** Selective loading by classification and phase.

**Candidates (not yet filed):**

- **Governance kernel compression** — split `AGENTS.md` into an always-loaded
  core and a conditional extended section so tiny-fix conversations skip the
  detail they never use.
- **Per-phase / per-classification SKILL.md loading** — exclude appendix
  sections (behavioral anchors, examples, rationalizations) for lightweight
  classifications and phases that don't benefit from them.
- **Skill description quality lint** — a check that flags weak or pushy skill
  descriptions against a consistent `Use when X; skip Y` pattern, so skills
  trigger reliably without bloating always-loaded prose.

---

## Track 4 — Skill ecosystem & distribution (slower burn)

These are higher-effort and depend on the validation foundation above.

| Item | Issue | Tier | Notes |
|---|---|---|---|
| External skill research & integration (Phase A) | [#145](https://github.com/KbWen/agentic-os/issues/145) | feature | repeatable intake workflow, 3 core skills |
| Lightweight routing heuristics in `config.yaml` | [#148](https://github.com/KbWen/agentic-os/issues/148) | quick-win | decision tree, not a DSL |
| Skill cache timestamp + staleness invalidation | [#149](https://github.com/KbWen/agentic-os/issues/149) | quick-win | complements content-hash issue [#13](https://github.com/KbWen/agentic-os/issues/13) |
| Claude Code plugin packaging | [#150](https://github.com/KbWen/agentic-os/issues/150) | feature | `plugin.json` + command/agent/hook bundling |

**Candidates (not yet filed):**

- **Deploy hardening** — concurrency guard (lockfile around `deploy.sh`),
  optional shallow-clone for slow networks, and a signal trap so an interrupted
  clone doesn't leave a partial cache.
- **`/help` skill discoverability** — surface auto-activated skills (grouped by
  cluster) in `/help` output, closing the "downstream devs see commands but no
  skills" gap.

---

## Sequencing summary

1. **Track 1 quick-wins** (#142, #143) — immediate, independent SSoT savings.
2. **Track 1 engine** (#140) → #141, #144.
3. **Track 2 enforcement** (#147, #146) + file the gate-receipt / schema-validation candidates.
4. **Track 3 token discipline** — file kernel-compression + SKILL.md-scoping candidates.
5. **Track 4** — as capacity allows; #148/#149 are cheap, #145/#150 are larger.

## Status key

- **Issue** — filed, see linked GitHub issue.
- **Candidate** — described here; not yet a backlog row or issue. Graduates once
  scope, motivation, and an owner are clear.
