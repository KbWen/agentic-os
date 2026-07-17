---
status: snapshot
title: Governance Self-Audit — Decision-Capture Surface
date: 2026-07-16
scope: decision-capture
method: 3 sonnet scans + 2 opus behavioral simulations + primary spot-verification (same-vendor-only)
---

# Governance Self-Audit — Decision-Capture Surface (2026-07-16)

**Trigger (user hypothesis)**: "AI product decisions sometimes land only in the SSoT with no ADR or spec behind them, so later sessions drift." Verify if real; propose handling.

**Verdict up front**: **Real, recurring, and structural — but bounded.** Decisions that take the ADR/spec path are durably discoverable (counter-examples verified: ADR-007 non-goal, ADR-010 Option-A rejection, kb-seam deferrals, PR #341 monotonic-ordering choice). The leak is path-specific: (a) `quick-win`/`hotfix` decisions have **no structural channel** to any durable surface, (b) **rejected** designs leave no ADR entry by construction, and (c) the SSoT copy everyone relies on (Ship History narrative) **rotates out at cap 10**.

## Validator Baseline

`validate.sh` on main @ `935381b`: **pass=113 · warn=4 · fail=0 · skip=2**. Directly relevant WARN: the governance eval-coverage advisory lists `engineering_guardrails.md §6 Explainability & Traceability` — the canonical gate `/decide` cites — among the MUST-sections with **zero guarding eval cases**.

## Already-Known (excluded from findings; cited not re-reported)

- Backlog #1/#3/#7/#11/#13/#98/#124/#127/#133 — document **volume/rotation** lifecycle; none address decision-content backing. #127 (Shipped) capped Ship History size; it never checks whether rotated entries' decisions have homes.
- `2026-07-01-governance-premortem-round2.md` P1 "Alarm without metabolism" — resolved, but scoped to `/audit`-generated `routing_actions` only.
- `2026-07-11-govern-audit-receipt-integrity.md` P3s — receipt integrity, a different failure class.
- Backlog #122 — enforce-vs-delete for the **design gate** (adjacent honor-system theme, different mechanism).

No existing row or snapshot names the decision-capture gap. Findings below are new.

## Verified Findings (5)

### F1 — `/decide` §5 ADR-promotion is an untriggered orphan; quick-win/hotfix decisions have no durable channel
**Disposition: backlog → row #138.** All evidence primary-verified:

- `decide.md:69-77` (§5): project-wide decisions "SHOULD be promoted to a formal ADR **during `/ship`**".
- `ship.md` (288 lines, full primary read): **zero** steps read Work Log `## Decisions`; zero `promot*` hits. Its only decision-shaped step (§7 Knowledge Consolidation, ship.md:247) reads the **spec's** `## Domain Decisions` — feature/architecture-change only. `spec.md:20` confirms: "the ONLY section `/ship` reads".
- Enforcement: `validate.sh:888-901, 2639-2662` (+ ps1 mirrors) check spec-level Domain Decisions only; tests grep = homonyms (`LockDecision`, fixtures); `/decide`'s canonical gate §6 has zero eval cases (baseline WARN).
- `templates/worklog.md` (182 lines, 18 sections): **no `## Decisions` section** — the target of `/decide` §2 isn't in the skeleton.
- Read-path: `bootstrap.md:143` reads `## Decisions` only when resuming the **same** worklog-key; `bootstrap.md:103` surfaces archived decisions only as INDEX.jsonl 1-liners **on module overlap**; L1 domain docs read for feature/arch only (`bootstrap.md:150-158`); L2 (`.log.md`) has **zero references in bootstrap.md** — a write-only sink.
- Quick-win Knowledge Nudge (`ship.md:81-95`) requires a user "yes" → **no-op in autonomous/headless runs**.
- Quantified (spot-verified): `archive/INDEX.jsonl` = 113 entries; **82 have empty `specs: []`** while carrying decisions. Live Ship History window: 4 embedded decisions, **3 unbacked**. `docs/architecture/governance.log.md` has **1 entry (2026-06-10)** while ≥5 governance-mechanism decisions shipped since.
- Behavioral sims (opus): write-path — a by-the-book quick-win ship deposits the decision only into archive-tier/discretionary sinks; §5 promotion probability ~0–5% for a model driving off ship.md literally. Read-path — see F2.

The repo's own `[enforcement][HIGH]` Global Lesson applies verbatim: a SHOULD/MUST without hook/validator/test is theatre — **wire it or delete it**.

### F2 — Live instance: the `design_tool`/ADR-011 unanimous rejection has no canonical home and rotates out of the SSoT in ~4 ships
**Disposition: backlog → row #139 (recommended immediate pick; soft deadline = before ~4 more ships).**

- Recorded today in: `current_state.md:134` (Ship History position 7/10 → **ejected after ~4 more ships**); backlog #119 prose (status Shipped → filtered out by open-work scans); `docs/reviews/2026-07-08-design-gate-roundtable.md` ("Do NOT retry this.") — which is the **only one of the 5 review snapshots with no `routing_actions` block** (verified: 0 hits), so it was never metabolized into L2.
- Absent from: `docs/adr/` (tops at ADR-010 — a rejected ADR-011 leaves no entry by construction); `docs/architecture/*` (0 hits for `design_tool`, verified); and ADR-001 — the ADR the rejection reaffirms — was **not amended**, despite ADR-001's own amendment precedent (ADR-001:152, 2026-06-11 incident).
- Read-path simulation (opus, fresh-context): **Phase 1 (today)** — catchable but buried mid-paragraph in a release-chore entry; catch depends on thoroughness, not mechanism. **Phase 2 (post-rotation)** — zero record in allowed reading; the agent **re-proposes the rejected design verbatim**, including proposing "ADR-011". **Phase 3** — the only durable init-surface catch is keyword-grepping **Shipped** backlog rows; no hard gate routes there.
- Same pass should batch the other 2 unbacked live-window decisions: `ship_history_max_entries: 10` rationale + "NOT-READY hint added but illegal `plan→review` FAIL deliberately preserved" (`current_state.md:130`; config comment has the *what*, not the *why*), and the "point-in-time archival" precedent (`current_state.md:118`; origin reasoning already in cold storage, reapplied 4+ times as oral tradition).

### F3 — bootstrap reads L1-only / L2 is a write-only sink — **close-with-reason**
Deliberate token economy: L1 reads are ~100-token budgeted (bootstrap.md:158), L2 is an unbounded append-only log, and `/govern-docs --restructure` (≥5-entry advisory, ship.md:263) is the designed distillation path. Not a defect on its own; the actual leak is upstream — nothing *feeds* L2 for quick-win/hotfix — and that is #138's scope. No change to bootstrap read policy.

### F4 — Ship History cap-10 rotation ejects decision narratives — **close-with-reason**
Rotation is by-design and recently, deliberately shipped (#127; SSoT bloat was real: 67→10). The defect is Ship History being used as a de-facto decision ledger (its entry format — `Feature shipped:`/`Tests:` — has no decisions field). Fix = give decisions a proper home **before** rotation (#138/#139), not raise the cap.

### F5 — Historical total-loss: the 2026-05-06 "Symphony model" backlog-governance decisions — **close-with-reason**
A feature-tier task replaced the Epic→Feature hierarchy with label-based clustering + cluster-declined suppression; its promised spec was never created (archived log: `Spec | — | to be created`), and today `docs/` has **zero** hits for Symphony/cluster-declined (verified) — the *why* behind the live backlog schema survives only in the raw archive. Predates dev-flow-hardening (PRs #299–#303) and the ship gate's `spec_exists` check; recurrence risk under current gates is low, and the rationale remains recoverable on demand (archive grep + INDEX.jsonl). **Reopen trigger**: any future backlog-schema redesign MUST first grep `archive/feat-epic-spec-hierarchy-governance-20260506.md`.

## Dropped False Alarms (refutations on record)

1. Sim-B claim "L2 domain docs are auto-read at feature/arch bootstrap" — **refuted by primary grep**: bootstrap.md reads L1 (`<domain>.md`) only; zero `.log.md` references. (L1/L2 conflation.)
2. Audit working claim "nothing on a new branch ever reads archives" — **refuted as stated**: `bootstrap.md:103` Cross-Branch Awareness conditionally surfaces INDEX.jsonl entries (incl. 1-line `decisions`) on module overlap. Correct form: isolated new branches get nothing; overlapping ones get 1-liners.
3. Hypothesis universality ("decisions only ever land in SSoT") — **narrowed**: every decision that took the ADR/spec path was found durably discoverable; the leak is tier/path-specific, not universal.

## Method & External-Signal Caveat

3 sonnet scans (dedup/known-list · historical instances · wiring trace) + 2 opus simulations (read-path drift · write-path trace), every load-bearing claim re-verified by the primary against actual file content (ship.md full read; greps on bootstrap.md/validate.sh/templates; INDEX.jsonl counts; ADR glob). All models same-vendor (Anthropic); no external-vendor or human signal in this run — architecture-level conclusions are labeled **same-vendor-only** per the `[audit-method]` Global Lesson.

## routing_actions

```yaml
routing_actions:
  - finding: "decide.md §5 ADR-promotion never triggered at /ship; quick-win/hotfix decisions have no durable capture channel (enforce-or-delete §5 + ship-time decision disposition + WARN-tier validator)"
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "fable-20260716"
  - finding: "design_tool/ADR-011 unanimous rejection lacks a canonical home (fix vehicle: ADR-001 amendment + document-governance.log.md L2 entry) before Ship History rotation ejects it (~4 ships)"
    target_doc: "docs/architecture/document-governance.md"
    status: merged
    owner: "fable-20260716"
```

## Disposition Summary

5 verified findings → **2 backlog** (#138 systemic · #139 instance-batch) · **3 closed-with-reason** (F3 token-economy by design · F4 rotation by design · F5 historical, gated since) · **3 false alarms dropped with refutations**.

**Next**: #139 first (quick-win, doc-only, has a rotation deadline); #138 as a feature under the deletion-funded constraint (token headroom ≈ 63; sh+ps1 parity; new checks behind the ADR-006 Python seam).
