---
status: accepted
date: 2026-07-19
classification: architecture-change
primary_domain: governance
deciders: "DRAFT for human decision — @kbwen (human steer; final call on the sentinel disposition and on ending grandfathering) + drafting agent (Claude Opus 4.8 1M), grounded against the [enforcement][HIGH] / [eval-mapping][MEDIUM] / [rule-placement][HIGH] Global Lessons (current_state.md L94/L107/L106), engineering_guardrails.md §13, ADR-008, docs/specs/_research-rpi-qrspi-corroboration.md §Corrections, and validate.sh L1611-1618 / validate.ps1 L1560-1565"
applies_to:
  - "AGENTS.md"
  - ".agent/rules/engineering_guardrails.md"
  - ".agent/rules/security_guardrails.md"
  - ".agent/workflows/shared-contracts.md"
  - "docs/reviews/2026-07-19-phase-entry-directive-enumeration.md"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When a directive is added to or removed from any of the four phase-entry surfaces, OR when a new phase-entry surface is introduced, OR when the [enforcement] Global Lesson's tier taxonomy changes"
  supersedes: none
  superseded_by: none
---

# ADR-011: Phase-Entry Surfaces Carry Only Enforcement-Backed Directives

## Status

Accepted (2026-07-19, at `/ship` of `docs/specs/directive-enforcement-audit.md`
(backlog #69 / issue #176, Strand D).

## Context

Four surfaces are loaded at every non-`tiny-fix` phase entry: `AGENTS.md`,
`.agent/rules/engineering_guardrails.md`, `.agent/rules/security_guardrails.md`,
`.agent/workflows/shared-contracts.md`. As of 2026-07-19 they carry ~132
hard-directive keyword hits (AGENTS.md 38, guardrails 84, security 6,
shared-contracts 4) resolving to an estimated ~90 distinct directives — a
keyword-derived lower bound (keyword hits ≠
directive count; the canonical enumeration is produced at `/plan`).

Three facts frame the decision:

- **The `[enforcement][HIGH]` Global Lesson** (current_state.md L94): *"Every
  MUST rule … that depends on agent self-attestation … is honor-system and is
  functionally theatre. … every MUST = 1 hook OR validator OR test OR external
  observer. Rules without enforcement should be DELETED rather than left as
  honor-system theatre. Adding MUST without enforcement is anti-help — it
  creates false confidence the rule is in effect."* Several grandfathered
  directives on these surfaces are self-attested with nothing behind them.
- **Raw count is NOT the problem** (`_research-rpi-qrspi-corroboration.md`
  §Corrections): frontier models lose instruction-consistency after **~150–200
  instructions per prompt — a RANGE, not 85**. Our ~90 (lower-bound estimate)
  sits *under* it. The
  issue #176 text predates this correction; a mechanical "cut to < 85" prune is
  therefore chasing the wrong metric. The real levers are (a) directives with no
  enforcement backing and (b) **burial depth** in the ~65-in-one-file
  `engineering_guardrails.md` (deepest-buried rules skipped first).
- **§13's ADD-Gate is forward-only.** `deletion-first-add-gate.md` (shipped)
  requires every NEW rule to declare a signal tier (T1/T2/T3) but explicitly
  grandfathers existing rules ("retrofit opportunistically"). The grandfathered
  population lives disproportionately on exactly these four highest-traffic
  surfaces.

## Decision

**Phase-entry surfaces carry only enforcement-backed directives.** §13's
ADD-Gate is **retroactively applied** to the four phase-entry surfaces:
grandfathering **ends for them**. Concretely:

1. Every directive on the four surfaces is assigned a tier — **T1**
   (validator/test/hook), **T2** (a `governance.yaml` case), **T3** (named
   human observer), or **NONE** — using §13's existing vocabulary unchanged.
2. Every `NONE`-tier directive resolves to one of {**delete** (observability-only
   clauses — output the AI cannot act on) · **merge** · **add-enforcement**
   (trivially cheap only) · **keep-honest-unenforced** (a behavior-shaping
   advisory retained but honestly labeled `NONE` with a rationale — no fabricated
   observer)}; no `defer` (repo norm is do-now / refine / close). "Grandfathering
   ends" concretely = every directive on the four surfaces MUST carry an explicit
   tier label (honest `NONE` allowed), and §13's ADD-Gate becomes **MANDATORY**
   (not "retrofit opportunistically") for these surfaces going forward.
3. The **enumeration table is a one-time point-in-time snapshot** (a dated
   `docs/reviews/` file). Drift is caught by a **directive-count ratchet test**
   (T1 — a `tests/ci/` pytest reading a committed per-file baseline, FAILing on
   count growth, cap-at-today) — NOT by observer-maintained re-snapshots. There
   is no re-snapshot duty (that would be the honor-system process this decision
   retires).
4. **Excluded**: the ADR-008 fenced safety cluster in `AGENTS.md` (L19–24:
   Destructive Command Gate, Secrets Prohibition, Untrusted Tool Output,
   Subagent Safety Delegation) is out of deletion scope regardless of tier. Its
   placement is governed by `[rule-placement][HIGH]` (irreversible-hazard rules
   stay on the always-loaded surface even where filesystem-layer teeth are T0),
   and its text is byte-identity-frozen + freshness-checked by ADR-008.

This is one decision (per `[adr-discipline]`): *end grandfathering on the
phase-entry surfaces.* The audit method, ACs, and the prune itself live in
`docs/specs/directive-enforcement-audit.md`.

## Consequences

**Positive**

- Kills honor-system theatre on the highest-traffic surfaces — the ones every
  session pays for on every phase entry — where it is most expensive and most
  misleading.
- Every surviving directive is auditable: the enumeration maps each to a
  concrete backing (validator path:line / test / eval case / observer).
- Token cost on the lifecycle-counted surfaces goes DOWN (deletions), funding
  the 355k ceiling rather than pressing it.
- Count growth is machine-caught: a future author who adds directives to a
  phase-entry surface trips the ratchet test (FAIL) unless the baseline is
  consciously lowered. Semantic drift beyond counts (rewording, quality decay)
  remains unmeasured — the ratchet targets drift, not adversaries.
- The census may legitimately delete ≈ 0 directives (a private upstream prior-art
  run of the same census deleted zero). The ADR's value is the honest labeling
  policy + the ratchet, NOT deletion volume.

**Negative / accepted (honest)**

- **Fewer written rules → more reliance on validators + model judgment.** A rule
  that was advisory-but-real ("state a rollback plan") loses its written prompt;
  the behavior now rests on the validator (if T1) or on the model's trained
  judgment. Accepted per `[enforcement]`: an unenforced written MUST was already
  not doing the work it appeared to do.
- **A deleted advisory rule may have had unmeasured value** — self-attestation
  can still nudge a well-behaved model even without teeth. We cannot measure
  that residual, and the lesson's stance is that false confidence outweighs it.
  Reopen trigger: an incident traced to a pruned advisory rule.
- **The ratchet catches count growth, not semantics.** Maintenance is now
  machine-gated by the directive-count ratchet (replacing the earlier
  observer-enforced re-snapshot). The residual honest gap: keyword rewording can
  hold the count flat while changing meaning, and semantic quality decay is
  unmeasured. This is drift-defense, not adversary-defense.

## Alternatives Considered

- **Keep grandfathering; prune nothing (status quo).** REJECTED — leaves the
  `[enforcement]`-lesson theatre in place on precisely the surfaces where it is
  loaded most often. §13 already made the go-forward case; the grandfathered
  backlog never gets retired if no change ever ends grandfathering for a scope.
- **Mechanical count-target prune ("cut to < 85").** REJECTED — the research
  §Corrections show the instruction-consistency threshold is a **150–200 range**
  and our ~90 is under it, so a count target optimizes the wrong number: it
  would delete load-bearing directives to hit a quota, ignore burial depth
  entirely, and produce a spec AC that later evidence already invalidates. Count
  is an outcome we measure, not a bar we set.
- **Build a machine directive-tier / drift checker as the enforcement.**
  Originally REJECTED pre-panel (new check, token + maintenance cost, issue
  mandate is subtractive). **PARTIALLY ADOPTED after adjudication** as the
  cap-at-today directive-count ratchet. Reversal evidence: a private upstream
  prior-art run's hard-directive keywords grew +9 under a green *token* ratchet
  (token and directive count are separate axes), and the original reopen-trigger
  was circular — it required the failed observer to detect its own failure. Still
  REJECTED: **fixed numeric targets** (research: the threshold is a 150–200
  range, not a number) and a **WARN-only counter** (repo evidence: WARN
  advisories are ignorable; the 355k test-tier ceiling is the pattern that
  actually formed deletion-funding discipline).

## Sentinel Adjudication (⚡ ACX)

The `[enforcement]` lesson names the `⚡ ACX` sentinel as an *example* of
honor-system theatre. That naming is **stale** — grep of the validators
(confirmed before writing) shows the sentinel gained real backing since:

- **Work Log `## Phase Summary` sentinel = true T1 (validator reads the
  archived artifact).** `validate.sh` L1616–1618 and `validate.ps1` L1563–1565
  check that every archived non-`tiny-fix` Work Log with a `## Phase Summary`
  section contains `⚡ ACX` (or plain `ACX` for terminals that strip non-ASCII),
  emitting a **WARN** when missing. WARN, not FAIL — but §13's T1 definition is
  "a validator/test/hook exists," which does not require FAIL-severity.
  **Recommendation: KEEP** (validator-backed audit trail; chat output is
  ephemeral, this is the persistent half).
- **Per-response chat-emission `⚡ ACX` = T2 (offline-measured adherence, not
  live enforcement).** `.agentcortex/eval/governance.yaml` carries the
  `sentinel-omission` case (protects "AGENTS.md §Agentic OS Runtime v1", asserts
  `ACX` present under pressure to drop it) — adherence is scored OFFLINE by the
  eval harness, NOT enforced in production. **Recommendation: KEEP** — it has a
  real eval backstop; deleting the rule would orphan that case (`[eval-mapping]`
  violation) and remove the only always-on integrity marker the framework
  advertises across models.

**Net**: the sentinel is NOT NONE-tier theatre; both halves are tier-backed (Work
Log = T1 live-validator, chat = T2 offline-eval) and survive the audit. The
enumeration marks both sentinel rows accordingly.

**Flagged for human**: the recommendation is KEEP/KEEP, but the *value* of the
per-response chat-emission rule (T2-backed yet honor-system in production) is a
judgment the human may still overrule — if the chat-emission rule is judged low
value despite the T2 backing, the correct disposition is `merge` (fold the
per-response requirement into the Work-Log audit rule), retiring the
`sentinel-omission` case in the same change per AC-5. Deletion is NOT
recommended (would orphan the eval case).
