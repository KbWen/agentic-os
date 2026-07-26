# Conflicting-Directive Scan — 2026-07-26

> **Type**: point-in-time census (read-only). No fix is applied here.
> **Backlog**: #145 · **Branch**: `feat/conflicting-directive-scan` · **Base**: `f765a59`
> **Scope**: the 4 phase-entry surfaces × `.agent/workflows/*` × `.claude/commands/*` ×
> `.agentcortex/templates/worklog.md`.
>
> **Deliberately no `routing_actions` block**: the dispositions below target governance files
> (`AGENTS.md`, `.agent/rules/*`, `.agentcortex/templates/*`), and the schema restricts
> `target_doc` to `docs/(architecture|specs)/*.md`. Dispositions live in the spec instead —
> which also avoids the 14-day pending-routing-action staleness WARN.

## Why this axis

ADR-011 swept these same surfaces asking **"is each directive enforcement-backed?"** It never
asked **"do the directives contradict each other?"** Both prior instances of the second
question were found by accident, never by a sweep:

- **#126** (shipped): `.claude/commands` stubs listed guardrails as an unconditional
  Required-read, contradicting `CLAUDE.md` step 4 and the bootstrap TOKEN LEAK BLOCK.
- **2026-07-25**: found live mid-bootstrap (B1 below).

External signal (per the `[audit-method][HIGH]` Global Lesson, which requires one for
architecture-level audits): Anthropic's 2026-07-24 context-engineering guidance names
conflicting instructions as a direct cause of degraded instruction-following, and reports
removing >80% of Claude Code's own system prompt partly on that basis. It corroborates the
**premise**; it does not corroborate any individual finding below. Every finding here was
verified against file text with a citation.

## Test applied to every candidate

A candidate counts as a finding only if **the declared precedence chain does not resolve it**,
or resolves it **silently with no gate**. That test produced the census's most consequential
result, so it is stated first.

## M1 — The precedence chain does not cover the surfaces that carry most directives

`AGENTS.md §Skill Safety & Precedence` item 2 declares:

> Order: `AGENTS.md` > `.agent/workflows/` > `.agent/skills/`

It omits **`.agent/rules/*`**, **`.agentcortex/templates/*`**, and **`docs/adr/*`** — all three
of which carry binding directives. `engineering_guardrails.md` alone holds 84 hard-directive
keyword hits (per the committed ratchet baseline), more than any other surface.

**Consequence**: for most conflicts below there is no declared tie-breaker at all. They are
resolved by agent judgment, silently, differently each time. This is the root cause that makes
the rest of the census possible, and fixing it is worth more than fixing any individual row.

---

## Category A — Read policy

### A1 · `Read-Once Discipline` vs the guardrails' own conditional-load design

| Side | Text |
|---|---|
| `AGENTS.md §Core Directives` | "Read governance files once at session start; do NOT re-read in later turns. … Un-logged re-reads = Token Leak violation." Exemption list names **only** `shared-contracts.md`. |
| `engineering_guardrails.md` §Heading-Scoped Read | "§5 Testing & Verification → **load at `/implement` entry and `/test` entry**"; "§12 → **load at `/implement` entry**" |

Following the guardrails file's own design requires later-turn reads that `AGENTS.md`
classifies as a Token Leak violation unless each is individually Drift-logged. Neither
document exempts them.

**Precedence test**: unresolved — `.agent/rules/` is not in the chain (M1).

### A2 · (negative result) the #126 stub conflict is CLOSED

30 stubs in `.claude/commands/`. Only `ask-local.md:11` still cites guardrails, and that is
the functional `§8.2` citation #126 deliberately kept. The prior case-by-case fix held.
Recorded so a future sweep does not re-litigate it.

---

## Category B — Write authority

### B1 · Exhaustive SSoT-write exception list vs `bootstrap.md`

| Side | Text |
|---|---|
| `AGENTS.md §vNext State Model` | "**Non-ship SSoT write exceptions (exhaustive list)**: `/retro`, `/app-init`, `/adr`. … Do NOT generalize to `/implement`, `/review`, or any other workflow." |
| `bootstrap.md §1` | "**Last Verified Update**: After successfully reading SSoT, update the `Last Verified` field to today's ISO date via `guard_context_write.py`" |

**Precedence test**: `AGENTS.md` > workflows resolves it — but **silently, with no gate**. An
agent that follows `bootstrap.md` literally writes SSoT outside the exhaustive list and
nothing catches it. Found live during this task's own bootstrap on 2026-07-25.

---

## Category C — Artifact contract (rule names a Work Log section the template never creates)

This category is **machine-checkable**, which matters for the durable-instrument question.
Template sections (19) are the ground truth: `.agentcortex/templates/worklog.md`.

| # | Section named | Cited at | Template | Severity |
|---|---|---|---|---|
| **C1** | `## Security Findings` | `security_guardrails.md:66` — "Security findings **MUST** be recorded in `…/work/<worklog-key>.md` under a `## Security Findings` section" | **absent** | MUST-level with no artifact |
| **C2** | `## Lessons` | `engineering_guardrails.md:361` (§10.6 Completion Guard: "Check: does Work Log have a `## Lessons` block?") · `bootstrap.md:141` | **absent** | the retro check can never pass on a template-conformant log |
| **C3** | `## Risks` | `plan.md:143` + `plan.md` §Work Log Update (Mandatory) · `bootstrap.md:142` · `handoff.md:148` (compaction keeps "latest `## Risks`") | template has **`## Known Risk`** | name mismatch across 3 workflows |
| **C4** | `## Recommended Skills` | `bootstrap.md:363` — "Write the result to Work Log `## Recommended Skills`" | present as a **header field**, not a `##` section | shape mismatch |
| **C5** | `## Spec Seeds` | `retro.md:45` | absent | additive; undeclared in the contract |
| **C6** | `## Research Findings` | `research.md:12` | absent | additive; undeclared in the contract |

**C3 and C4 were violated silently in this very session.** Three Work Logs written tonight
followed the template (`## Known Risk`, `Recommended Skills:` as a header field), so
`plan.md`'s and `bootstrap.md`'s instructions went unfulfilled — and no gate, validator, or
review noticed. That silence is the finding, not the naming.

**Precedence test**: unresolved — `.agentcortex/templates/` is not in the chain (M1).

**Filtered out as false positives** (the sweep raised them; the citing line proves they are
not Work Log sections): `## Reverse Transition` (a block inside `review.md` itself),
`## Global Lessons` / `## Ship History` / `## Spec Index Archive` (sections of
`current_state.md`), `## Domain Decisions` / `## Constraints` / `## API / Data Contract`
(spec-file sections), `## Conventions` / `## Doc URL Registry` / `## Open Decisions`
(app-init/ADR sections), `## Source Summary` (`_product-backlog.md`).

---

## Category D — Vocabulary

### D1 · "DEFER" means two opposite things

| Side | Text |
|---|---|
| `engineering_guardrails.md §8` | "When Uncertain: … **DEFER** high-impact decisions to user." §8.1: "Record failure in Work Log and **DEFER** to user for escalation." |
| `ADR-011` (Decision 2) | "no `defer` (repo norm is do-now / refine / close)" |

Two different senses — escalate-to-human versus postpone-a-disposition — carried by one token.
A reader applying the ADR's norm to §8's instruction gets a contradiction. Low blast radius,
but it is exactly the ambiguity class the external guidance flags.

**Precedence test**: unresolved — `docs/adr/` is not in the chain (M1).

---

## Category E — Input handling

### E1 · Acknowledgment-only inputs vs direct phase execution on explicit intent

| Side | Text |
|---|---|
| `engineering_guardrails.md §9.1` | "The following inputs **MUST NOT** trigger any state transition or execution: EN: `OK`, `Sure`, `Got it`, `Alright`, `Fine`; ZH: `好`, `收到`, `嗯`, `了解`, `沒問題`. Correct behavior: Confirm receipt, optionally ask what the next step should be." |
| `AGENTS.md §Agentic OS Runtime v1` item 6 | "**Direct phase execution on explicit user intent**: If the user explicitly requests `/plan`, `/implement`, … execute that phase in the SAME turn after gate pass — no second confirmation pause." |

Neither carves out the commonest case in practice: **the token IS the affirmative answer to a
yes/no question the agent itself just asked.** §9.1 is unconditional and token-based; item 6
is intent-based.

**Live instance, this session**: the agent asked *"要我進 `/implement` 嗎?"* and the user
answered *"好喔"*. Under §9.1 that MUST NOT trigger execution; under item 6 it is explicit
intent. The agent proceeded — i.e. §9.1 is already dead text for this case, unenforced and
unnoticed. It fired at least twice on 2026-07-25/26.

**Precedence test**: `AGENTS.md` > `.agent/rules/`… except `.agent/rules/` is not in the chain
(M1). Resolved only by agent judgment.

---

## Category F — Documented phase vs enforced phase

### F1 · The mandatory `spec` gate cannot be recorded without failing the validator

Found by walking into it while writing this very census.

| Side | Text |
|---|---|
| `engineering_guardrails.md §10.2` | **feature** — Mandatory Gates: `bootstrap → `**`spec`**` → plan → implement → review → test → handoff → ship`. **architecture-change**: `bootstrap → ADR → `**`spec`**` → plan → …` |
| `state_machine.md` | `CLASSIFIED --(spec artifact created in docs/specs/)--> SPECIFIED`, and "**Spec Gate (Hard)**: `feature` and `architecture-change` MUST reach `SPECIFIED` before planning." |
| `plan.md §Pre-Conditions` | "Spec Gate: … MUST have a corresponding `docs/specs/<feature>.md`" |
| `validate.sh` L1374–1395 | All three transition tables — `LEGAL_DEFAULT`, `LEGAL_STRICT`, `LEGAL_HOTFIX` — begin `'bootstrap': ['plan']`. **There is no `spec` key and no edge to it anywhere.** |

Writing the receipt the documented flow implies produces:

```
[FAIL] work logs with illegal gate phase progression: 1
  illegal gate progression in feat-conflicting-directive-scan.md: bootstrap->spec
```

**The compliant behaviour is therefore to leave the mandated phase unrecorded.**

**Historically verified, not inferred**: across every archived `feature` /
`architecture-change` Work Log, `grep -c "^- Gate: spec"` returns **0** — including the
ADR-011 audit itself. Not one feature in this repo's history has ever recorded the spec gate.

**Precedence test**: unresolved, and worse than unresolved — this is a rule that *cannot* be
followed as written. The Spec Gate is real, but it is enforced by **artifact existence**
(`plan.md` checks the file on disk), not by a receipt. `§10.2` listing `spec` among "Mandatory
Gates" beside phases that do produce receipts is what makes it unfollowable.

---

## Census summary

| Category | Findings | Machine-checkable |
|---|---|---|
| M — precedence chain incompleteness | 1 (root cause) | partially (surface list is enumerable) |
| A — read policy | 1 confirmed + 1 negative result | no |
| B — write authority | 1 confirmed | possibly (writer-vs-allowlist) |
| C — artifact contract | 6 confirmed | **yes** |
| D — vocabulary | 1 confirmed | no |
| E — input handling | 1 confirmed, live | no |
| F — documented vs enforced phase | 1 confirmed, historically verified | **yes** |

**11 confirmed findings + 1 negative result.**

Two of them (C3, C4) were violated silently by this session's own Work Logs, and one (B1) was
found by walking into it. None was caught by any gate, validator, or review — which is the
census's actual point: **nothing in the framework looks for this class at all.**

## Open question the spec must answer

ADR-011's durable half was a cap-at-today count ratchet. Conflicts are **semantic** and cannot
be counted, so that pattern does not transfer. Category C is the one slice with a real
machine check available (a rule naming a Work Log section can be validated against the
template). For M/A/B/D/E, either an honest T3 disposition is recorded or the finding is fixed
by **deletion/merge** — per `[enforcement]`, an unenforced MUST is worse than no rule, and per
this repo's north star, resolving a conflict by adding a clarifying rule makes the surface
denser, which is the very failure the external guidance describes.
