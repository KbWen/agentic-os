# Conflicting-Directive Scan — 2026-07-26

> **Type**: point-in-time census (read-only). No fix is applied here.
> **Backlog**: #145 · **Branch**: `feat/conflicting-directive-scan` · **Base**: `f765a59`
> **Scope**: 4 phase-entry surfaces × `.agent/workflows/*` × `.claude/commands/*` ×
> `.agentcortex/templates/worklog.md` × `.agentcortex/docs/guides/*`.
>
> **Revision note (this document was rewritten after adversarial review).** The first draft
> claimed 11 confirmed conflicts. A 4-seat roundtable refuted **9 of them**, two with fixes
> that would have been actively harmful. The refuted rows are retained below with their
> refutations so they are not re-proposed. Six findings the first draft missed were added.
> Net: **7 findings, down from 11, and a different set.**
>
> No `routing_actions` block: `check_routing_actions.py` restricts `target_doc` to
> `docs/(architecture|specs)/*.md` and every disposition targets a governance file.

## Method and its honest ceiling

A candidate counts only if the declared precedence chain does not resolve it, or resolves it
silently with no gate.

`[audit-method][HIGH]` requires an **external signal** for an architecture-level audit.
`OPENROUTER_API_KEY` was set and `ask-openrouter` was live, but **two invocations across six
free-tier models all failed**; a paid model is `--profile quality` = high-cost, which §8.2
says needs user confirmation, and the user was asleep. **So the review seats were all
same-vendor — which the lesson itself calls theatre.** Anthropic's 2026-07-24
context-engineering guidance corroborates the *premise* (conflicting instructions degrade
instruction-following) but no individual row. Every row below was re-verified against file
text by the primary before adoption. Treat the judgment calls as unvalidated externally.

---

## SURVIVING FINDINGS

### S1 · `AGENTS.md` contradicts itself about which surface has authority

| Side | Text |
|---|---|
| `AGENTS.md:94` | "**Workflow Precedence Rule**: If conflict arises, workflows take precedence. Order: `AGENTS.md` > `.agent/workflows/` > `.agent/skills/`." |
| `AGENTS.md:13` | "**MUST OBEY**: `.agent/rules/engineering_guardrails.md`." |
| `AGENTS.md:109` | "Constitution: `.agent/rules/engineering_guardrails.md`" |
| `engineering_guardrails.md:1` | "# Engineering Guardrails (**Constitution**)" |

A file designated *Constitution* and *MUST OBEY* does not appear in the ordering at all, while
that ordering sits under a heading ("Skill Safety & Precedence") that scopes it to skills.

**Do not "fix" this by extending the chain.** That was the first draft's M1 and it is wrong
twice over: it would rank the Constitution *below* `AGENTS.md`, and 4 of 11 ADRs declare
`applies_to: AGENTS.md` (ADR-001/004/008/011, the last covering all four phase-entry
surfaces), so any ADR clause creates a loop where ADRs govern the precedence clause that ranks
ADRs. The honest fix is the opposite direction — make item 2's **scope** explicit (it is a
skill-vs-workflow tie-breaker) so it stops reading as a universal hierarchy it never claimed
to be.

### S2 · `## Risks` vs `## Known Risk` — five sites, one of them invisible to any checker

| Site | Says |
|---|---|
| `plan.md:143`, `plan.md:169` | `## Risks` — and **`:169` is a bare heading inside a fenced block agents copy verbatim** |
| `bootstrap.md:142` | reads `## Risks` |
| `handoff.md:148` | compaction keeps "latest `## Risks`" |
| `handoff.md:141` | preserve-list names `## Known Risk` — **contradicts `:148`, 7 lines apart, same file** |
| `.agentcortex/docs/guides/token-governance.md:115` | same stale `## Risks`; `AGENTS.md §Context Pruning` points readers here as the handoff-timing SSoT |
| `.agentcortex/templates/worklog.md` + `AGENTS.md §Work Log Contract` + validator | `## Known Risk` |

The fenced bare heading at `plan.md:169` matters beyond the rename: **a detector that scans
for backticked `` `## X` `` references cannot see it.** Any durable check for this class has
to read fenced template blocks too.

### S3 · The `#126` stub class is alive in 23 of 30 command stubs

`.claude/commands/implement.md:5-7` (and 22 siblings) list under "## Required reads before
execution": "1. `AGENTS.md` — global directives". Three stubs (`implement.md:8`, `ship.md:8`)
additionally require `.agent/rules/security_guardrails.md`.

Against: `CLAUDE.md:5` — "`AGENTS.md` is auto-injected above via `@import` … already in
context" — and `AGENTS.md:27`, which makes an un-logged later-turn governance re-read a **Token
Leak violation**.

The first draft recorded this class as CLOSED. That was wrong: the #126 fix grepped for
`engineering_guardrails` only, so it closed one filename, not the class.

### S4 · `§10.6`'s handoff probe is already vacuous

`engineering_guardrails.md:355-361` self-check:

- item 2 — "Has the handoff phase been executed? (Check: does Work Log have a `## Resume` block?)"
- item 3 — "Has the retro phase been executed? (Check: does Work Log have a `## Lessons` block?)"

`worklog.md` ships **`## Resume`** in every log (value `none` until `/handoff` runs). So item 2
is **already always-true** and has never distinguished ran-handoff from skipped-handoff. Item 3
still works precisely *because* `## Lessons` is absent from the template.

This is why the first draft's C2 (add `## Lessons` to the template) was refuted as harmful: it
would have broken the one probe that still works, to match the one that is already broken.

### S5 · Documented phase order vs enforced phase order

`engineering_guardrails.md:307` mandates `implement → review → test` for `feature`. But
`validate.sh:1390` / `validate.ps1:1221` `LEGAL_STRICT` sets `'implement': ['review','test']`
— so `implement → test` with review skipped is a **legal** transition. The documented
mandatory order is stricter than the enforced one.

### S6 · `§10.2` lists receipt-less entries in a "Mandatory Gates" column

`§10.2` lists `ADR` for architecture-change (`:308`) and "check Spec Index" for quick-win
(`:306`). Neither produces a receipt and neither exists in any validator table — the same
shape as the `spec` entry that produced the first draft's F1 error.

The cheap fix already exists in the same table: `:309` annotates hotfix's research step as
"research (**advisory, no gate receipt**)". Applying that annotation to `spec`, `ADR`, and
"check Spec Index" removes the ambiguity with no code change.

### S7 · `bootstrap`'s SSoT write vs the "exhaustive" exception list

| Side | Text |
|---|---|
| `AGENTS.md:43-47` | "**Non-ship SSoT write exceptions (exhaustive list)**: `/retro`, `/app-init`, `/adr`. … Do NOT generalize to … any other workflow." |
| `AGENTS.md:35` | "**SSoT Recovery Exception**: … then update `current_state.md` and log recovery" — a bootstrap-time write, **eight lines above the exhaustive list that omits it** |
| `bootstrap.md:99` | "update the `Last Verified` field … via `guard_context_write.py`" |

Both sides of the sharper instance live in one file. Note the write is *guarded* — it routes
through the tool `AGENTS.md:37` names — so the defect is the list's completeness, not safety.

**Caution for any fix**: `governance.yaml:93` `ssot-write-isolation` carries
`expect_substrings: [… "only /ship updates SSoT" …]`. Broadening the list without re-checking
that case orphans it (`[eval-mapping]`).

---

## REFUTED — recorded so they are not re-proposed

| First-draft row | Why it fails |
|---|---|
| **M1** universal precedence chain | Misread instrument: `AGENTS.md:94` is scoped to skills. Fix would demote the Constitution and loop through 4 ADRs. Replaced by **S1**. |
| **A1** Read-Once vs conditional loads | `engineering_guardrails.md:26` routes §9 re-reads "per AGENTS.md Read-Once Discipline"; `:38` routes stale-receipt re-reads "per AGENTS.md Safety Valve + log to Drift Log". The file defers to the mechanism. A first conditional load is not a re-read. |
| **A2** "#126 is closed" | Wrong in the opposite direction. Replaced by **S3**. |
| **C1** add `## Security Findings` | `validate.sh:1691` is a bare presence grep; template-supplying the heading **permanently disables a live WARN**, invisibly (CI tests use synthetic logs). Already tiered T1 at enumeration:133. |
| **C2** add `## Lessons` | Would make `§10.6` item 3 vacuous. See **S4**. |
| **C4** `Recommended Skills` shape | `bootstrap.md:226` and `:416` (the final merged write) both treat it as a header field; `implement.md:47` and `shared-contracts.md:7` say "entry". One `##`-shaped mention is a typo, not a contract conflict. |
| **C5 / C6** `## Spec Seeds`, `## Research Findings` | These are *create* instructions ("append … under a `## Spec Seeds` heading"), and `engineering_guardrails.md:314` calls the 6-section list a "**minimum** runtime contract" — a floor, so additive sections are not undeclared. |
| **D1** "DEFER" collision | ADR-011's "no `defer`" is self-scoped: "Every `NONE`-tier directive resolves to one of {…}; no `defer`". It never reaches `§8`'s escalate-to-user sense. |
| **E1** delete `§9.1` | `2026-07-19-phase-entry-directive-enumeration.md:116` row 90 already dispositions §9.1 as `NONE` / **`keep-honest-unenforced`** — ADR-011 ran this exact test and chose KEEP. Its reopen trigger is "an incident traced to a pruned advisory rule", not "an agent overrode it". The texts also do not collide: `AGENTS.md:81` item 6 fires on an **explicit phase request**. |
| **F1** `spec` gate unrecordable | **Closed twice before as agent error, not a framework gap.** `feat-govern-audit-workflow-20260702.md:143` — "the gate-progression parser's vocabulary is the 7 receipt phases … enforcement working; **my error, not a gap**"; repeated at `feature-directive-enforcement-audit-20260719.md:161`; carried as binding precedent at `feat-local-model-delegation-20260704.md:94`. `state_machine.md:17` makes the edge **artifact-triggered**; `spec.md` contains zero receipt instructions. The historical `grep -c "Gate: spec" == 0` is an enforced convention, not an unfollowable rule. |

---

## Constraints any fix must respect (verified during review)

- **`AGENTS.md` ratchet headroom is zero** — live count 37, baseline 37. Any keyword-bearing
  addition FAILs `test_directive_count_ratchet.py`. And `CI Structural Tests` is **not** a
  branch-protection-required check, so a 38-count could auto-merge red.
- **Do not add template sections.** Beyond S4's vacuity problem: `worklog.md` is 190 lines and
  the compaction thresholds are 300 lines / 12 KB, so four additions put a new log at ~74% of
  budget at zero content — and `handoff.md:148`'s keep-list would then compact them away.
- **`.agentcortex/templates/*` and `AGENTS.md` are `scaffold`**, not force-update
  (`deploy.sh:112-117`; golden:163/199). A downstream that edited them gets `.acx-incoming` and
  keeps the old file — so the adopters most exposed to these conflicts are exactly the ones a
  fix does not reach. `.agent/rules/*` **is** core/force-update (golden:2-9).
- **`analyze_token_lifecycle.py` cannot measure any surface here** — 0 references to
  `AGENTS.md`, `rules/`, or `templates/`. Token claims about these files need a byte/char
  delta, not that tool.
- **ADR-011's `review_trigger` fires** on any directive added to or removed from the four
  phase-entry surfaces. Any disposition touching them owes an ADR-011 amendment and a
  **per-directive** tier (honest `NONE` allowed) — a blanket spec-level `signal_tier` does not
  satisfy Decision 2.
