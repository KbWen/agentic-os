---
status: shipped
title: Phase-Entry Directive Enforcement Audit + Prune
date: 2026-07-19
classification: feature
source: GitHub issue #176 / backlog #69 (Strand D only)
primary_domain: governance
secondary_domains: [tooling]
signal_tier: T1
signal_tier_note: >
  This spec ships a directive-count ratchet test (AC-11) in tests/ci/ — a
  machine gate (cap-at-today, FAILs on count growth) that is the durable drift
  instrument, hence T1. The enumeration artifact itself is a one-time dated
  point-in-time snapshot with NO observer re-snapshot duty (a re-snapshot duty
  would be exactly the T3 honor-system process this spec retires; upstream
  prior-art shows observer/advisory-only maintenance demonstrably fails).
applies_to:
  - "AGENTS.md"
  - ".agent/rules/engineering_guardrails.md"
  - ".agent/rules/security_guardrails.md"
  - ".agent/workflows/shared-contracts.md"
  - "docs/reviews/2026-07-19-phase-entry-directive-enumeration.md"
---

# Phase-Entry Directive Enforcement Audit + Prune (backlog #69 / Strand D)

## Goal

Retire honor-system theatre from the four surfaces loaded at every
non-`tiny-fix` phase entry — `AGENTS.md`, `.agent/rules/engineering_guardrails.md`,
`.agent/rules/security_guardrails.md`, `.agent/workflows/shared-contracts.md`
(the "phase-entry surfaces") — per the `[enforcement][HIGH]` Global Lesson:
*"every MUST = 1 hook OR validator OR test OR external observer; rules without
enforcement should be DELETED rather than left as honor-system theatre."*

As of 2026-07-19 the surfaces carry ~132 hard-directive keyword hits (AGENTS.md
38, guardrails 84, security 6, shared-contracts 4; **keyword hits ≠ directive
count** — the canonical per-directive enumeration is produced at `/plan`/
`/implement`, not here). This is Strand **D** of
`docs/specs/_research-rpi-qrspi-corroboration.md` ONLY; Strands A/B/C/E stay
open (see Non-goals).

**Reframe (predates the issue text).** The research doc §"Corrections /
constraints to carry forward" establishes that frontier models lose
instruction-consistency after **~150–200 instructions per prompt** — a RANGE,
not 85. Our measured ~90 phase-entry directives (a keyword-derived lower
bound — the semantic counting unit in AC-1 also captures keyword-less
imperatives, so the enumerated row count may run higher) sit *under* that range, so
**raw count is NOT the smoking gun.** The smoking guns are (a) directives with
NO enforcement backing (theatre), and (b) **burial depth / ordering** in the
~65-directives-in-one-file `engineering_guardrails.md` (deepest-buried rules
are skipped first). Count reduction is therefore an **OUTCOME**, never a
target — there is deliberately no `target < N` acceptance criterion.

**Adopter delta**: before — a governance USER reads the four surfaces trusting
each MUST/NEVER is in effect, while several are self-attested with nothing
behind them (false confidence; the `[enforcement]` lesson's "anti-help"). After
— every directive on these surfaces carries an honest tier label (including the
new `keep-honest-unenforced` label for behavior-shaping advisories that are
retained but truthfully marked as unbacked), observability-only clauses are
deleted, and a committed enumeration table makes the enforcement map legible.
The three deliverables are (a) a complete enforcement map with honest labels
(incl. `keep-honest-unenforced`), (b) deletion of observability-only clauses
(expected ≈ 0–2 — this is deliberately NOT a large prune), and (c) a
machine-checked growth ratchet (AC-11). Engine gates, phase order, and state
machine are UNCHANGED; this is a documentation/enforcement-honesty change, not a
behavior change. Cross-platform: the surfaces are shared (Claude/Codex/Gemini/API
all consume the same files via `@import`), so the change lands identically for
every consumer — adapters MUST NOT diverge.

## Acceptance Criteria

- **AC-1 (enumeration artifact — one-time dated snapshot)**: A committed table at
  `docs/reviews/2026-07-19-phase-entry-directive-enumeration.md` lists every
  phase-entry behavioral obligation. **Counting unit: one enforceable behavioral
  obligation = one row** — keyword-INDEPENDENT, so keyword-less imperatives are
  captured too (e.g. AGENTS.md's reply-in-the-user's-language rule, which carries
  no MUST/NEVER token). Columns: `surface file` | `section` | `directive quote
  (or stable hash)` | `keyword class` (MUST / NEVER / MUST NOT / PROHIBITED /
  gate / none — a keyword-less imperative is class `none`) | `read-moment /
  load-layer` | `within-loaded-unit ordinal` | `enforcement tier` (T1 / T2 / T3 /
  NONE) + `backing citation` (validator path:line, test name, `governance.yaml`
  case id, or named observer) | `disposition` (keep / delete / merge /
  add-enforcement / keep-honest-unenforced / EXCLUDED). The keyword hits are
  reconciled to distinct obligations (multi-keyword directives collapse to one
  row; a keyword-less imperative is its own row; the obligation count, not the
  keyword count, is the enumeration unit).
  - `read-moment / load-layer` values: `always-on-per-turn` (AGENTS.md via
    `@import`) · `session-start-full-mode` (guardrails core §§1/2/4/7/8.1/10) ·
    `conditional-heading-scoped` (guardrails §§3/5/6/8.2/9/11/12/13) ·
    `phase-scoped` (security_guardrails: implement/review/ship only) ·
    `phase-entry` (shared-contracts.md).
  - `within-loaded-unit ordinal` = the directive's position INSIDE the unit that
    is actually loaded (the file is heading-scope loaded, never read linearly),
    NOT a whole-file line offset.
  - **Layer-stratified ceiling comparison**: compare only genuinely co-loaded
    sets against the ~150–200 instruction-following range — never the raw
    all-surfaces sum. State the **max co-load set** (feature-tier `/implement`
    entry: AGENTS.md always-on + guardrails core + the phase-relevant
    heading-scoped guardrails §§ + security_guardrails + shared-contracts) and
    the **quick-win set** (AGENTS.md + shared-contracts only — guardrails NOT
    read, "Quick Mode"). The comparison is per co-load set, not per file.
- **AC-2 (success metric a — 100% honest tier labeling)**: After the change,
  **100% of directives on the four surfaces carry an explicit tier label**
  (T1 / T2 / T3 / NONE). A `NONE`-tier survivor is PERMITTED, but ONLY with
  disposition `keep-honest-unenforced`: the advisory is retained and honestly
  labeled `NONE` in the table with a 1-line behavioral-value rationale — no fake
  observer or manufactured tier may be invented to paper over an unbacked rule.
  Verified by the enumeration table: no row lacks a tier label, and no row lacks
  a disposition.
- **AC-3 (success metric b — every NONE-tier directive gets a disposition)**:
  Each `NONE`-tier directive resolves to exactly one of:
  - `delete` — **RESERVED for observability-only clauses**: when the rule fires,
    the AI cannot change any behavior; the output exists only for post-hoc human
    reading.
  - `merge` — net-negative in obligation count; may NOT increase any survivor's
    within-unit ordinal; and MUST NOT relocate an always-on rule across
    load-layers.
  - `add-enforcement` — only when trivially cheap (e.g. extend an existing
    checker), never a net-new machine gate.
  - `keep-honest-unenforced` — behavior-shaping advisory rules retained but
    truthfully labeled `NONE`. Verified live examples: AGENTS.md **Read-Once
    Discipline** (zero backing — `grep` of `validate.sh` + `governance.yaml`
    confirms nothing enforces it), **Context Pruning**, **Response Brevity &
    Budget**.

  No `defer` / `future` disposition (repo norm: do-now / refine-to-precise /
  close only). **Honest calibration**: a private upstream prior-art run of the
  identical census deleted ZERO directives (its only deletable category was
  observability-only clauses, of which it had none); expected clean deletions
  here ≈ 0–2. The primary deliverable is the enforcement map, NOT deletion
  volume.
- **AC-4 (safety-cluster exclusion)**: The ADR-008 fenced span in `AGENTS.md`
  (lines 19–24: `Destructive Command Gate`, `Secrets Prohibition`, `Untrusted
  Tool Output`, `Subagent Safety Delegation`) is **EXCLUDED from deletion scope
  regardless of tier**. The enumeration marks each `EXCLUDED` with its actual
  backing (Secrets = T1 git-boundary; Destructive = T1 git-boundary + T0 fs
  advisory; Untrusted = T0 + T2 eval; Subagent Delegation = T0 advisory but
  fenced). Rationale: the fence is validator freshness-checked (ADR-008 §Decision
  2) and byte-identity-required; deleting/editing text breaks the freshness
  check AND orphans eval cases. Placement, not the enforcement test, governs
  this cluster (`[rule-placement][HIGH]`: irreversible-hazard rules live on the
  always-loaded surface even when their filesystem-layer teeth are T0).
  **Post-edit verification gate**: `git diff` over the `AGENTS.md` fence span
  (L19–24) MUST be empty AND `python .agentcortex/tools/generate_safety_nucleus.py
  --check` MUST pass.
- **AC-5 (eval protects-tag re-mapping — section granularity — [eval-mapping]
  lesson)**: `.agentcortex/eval/governance.yaml` `protects`-tags resolve at
  **SECTION** level — a sentence-level re-map does not exist. For any case whose
  protected section is touched, exactly one valid resolution applies, **in the
  same change**: (a) verify the protected section still contains text for the
  specific behavior the case tests, OR (b) retire the case. Paste
  `python .agentcortex/tools/run_governance_eval.py --coverage` output
  post-change. **Explicit rule**: a green eval run is NOT evidence a rule
  survived — the runner scores model responses against fixed prompts and never
  reads the protected text. No orphaned `protects`-tag after the change.
- **AC-6 (claim sync + cross-platform parity — enumerated protected-token
  checklist)**: No surface may advertise a pruned directive. Run this ENUMERATED
  protected-token checklist **before AND after every edit**:
  1. literal `<worklog-key>` present in `AGENTS.md` + `engineering_guardrails.md`
     + `security_guardrails.md` (`validate.sh` FAIL check ~L702).
  2. literal `.agent/workflows/routing.md` present in `AGENTS.md` (`validate.sh`
     FAIL ~L2587–2592).
  3. ADR-008 fence span intact + `generate_safety_nucleus.py --check` passes.
  4. sentinel `⚡ ACX` / `ACX` tokens present where required.
  5. adapter literal pins in `.antigravity/rules.md` and
     `codex/rules/default.rules` (docker-system-prune / chown / rollback
     phrases, `validate.sh` ~L565–661).
  6. `bootstrap.md §1 Classification Tiers` embedded DUPLICATES of guardrails
     quick-win rules (Confidence Gate / Bug Fix Protocol / Doc Integrity) stay
     in sync.
  7. intra-surface cross-references (guardrails §9 + §Loaded-Sections Receipt
     cite AGENTS.md Read-Once / Safety Valve) still resolve.
  8. mirror sweep: `CLAUDE.md`, `GEMINI.md`, and zh-TW mirror docs.
  9. `trigger-compact-index` freshness check — regenerate if a
     registry-referenced heading changed.

  The change lands identically for Claude/Codex/Gemini/API — adapters `@import`
  the surfaces and MUST NOT carry divergent copies of a kept-or-deleted
  directive. **Ship evidence** = full CI-equivalent suite
  `pytest tests/ci/ tests/guard/ .agentcortex/tests/` + BOTH validators
  (`validate.sh` AND `validate.ps1`) PASS lines pasted.
- **AC-7 (burial-depth / ordering audit — within-loaded-unit ordinal)**:
  Burial-depth is the **within-loaded-unit ordinal** (a directive's position
  inside the unit actually loaded), NOT a whole-file line offset — the surfaces
  are heading-scope loaded, never read linearly. Each directive's read-moment /
  load-layer is marked BEFORE any move. **Relocation across load-layers is
  forbidden for always-on rules.** Merges may only HOLD or DECREASE a survivor's
  within-unit ordinal (never bury it deeper). Deepest-buried `NONE`-tier
  directives are addressed first; deep + load-bearing survivors are surfaced
  (moved earlier / promoted to a core heading) or consolidated. Recorded as
  evidence, not a pass/fail threshold.
- **AC-8 (post-prune measurement — evidence, not gate)**: Before/after distinct
  directive count, per-file distribution, and burial-depth delta are recorded in
  the enumeration artifact and the Work Log `## Evidence`. This is a measured
  OUTCOME — the spec explicitly declares no numeric target and MUST NOT assert
  `target < 85` (or any count threshold) as an acceptance bar (Strand D
  correction). **Two distinct instruments**: the semantic directive rows (this
  table) and the keyword hits (the machine ratchet, AC-11) are deliberately
  separate measurements. Neither supports any *adherence* claim — "the model
  obeys better" is unprovable by synthetic measurement and appears nowhere as an
  AC.
- **AC-9 (token ceiling — deletions fund)**: Net token delta on the
  lifecycle-counted surfaces (`AGENTS.md`, `shared-contracts.md`,
  `engineering_guardrails.md`, `security_guardrails.md`) is **≤ 0** — any merge
  or consolidation is deletion-funded; `test_aggregate_current_total_stays_under_355k`
  passes with the `355_000` literal UNCHANGED. The enumeration artifact lives in
  `docs/reviews/` (not phase-loaded) → ~0 ceiling cost. In the same change, run
  `python .agentcortex/tools/update_lifecycle_baseline.py --apply` and commit the
  regenerated `lifecycle-baseline.json` — prevents a lingering post-prune DRIFT
  WARN.
- **AC-10 (sentinel disposition — conditional on ADR-011)**: The `⚡ ACX`
  sentinel disposition follows ADR-011 §Sentinel Adjudication. The Work Log
  `## Phase Summary` sentinel = **KEEP (true T1** — `validate.sh` L1616–1618 /
  `validate.ps1` L1563–1565 WARN; the validator reads the archived artifact).
  The per-response chat-emission rule = **KEEP (T2 = adherence measured OFFLINE
  by the eval harness, NOT live-enforced in production** — `governance.yaml`
  `sentinel-omission` case). The enumeration marks both sentinel rows with their
  real backing, NOT `NONE`. **Fragility note**: the T2 anchor is a section-level
  `protects`-tag — it guards by co-location only. Any sentinel disposition change
  is BOUND to same-change retirement of the `sentinel-omission` eval case. Final
  call is ADR-011's.
- **AC-11 (directive-count ratchet test — the durable drift instrument, T1)**:
  A **directive-count ratchet test** lands in the same change: a pytest in
  `tests/ci/` reads a committed per-file baseline (post-prune keyword-hit counts
  for the four surfaces; the test documents the exact `grep` pattern it counts).
  It **FAILs ONLY when a file's count EXCEEDS its baseline**. Lowering a count
  updates the baseline downward — a monotone **cap-at-today** ratchet, mirroring
  the repo's 355k token-ceiling pattern. This is explicitly **NOT a fixed numeric
  target** — there is no `< 85`-style bar. **Accepted limitation**: keyword
  rewording can evade the ratchet; it targets drift, not adversaries. Division of
  labor: the enumeration table is a **one-time dated point-in-time snapshot**
  (marked as such in its own header) and the ratchet is the durable drift
  instrument (T1). There is **NO observer re-snapshot duty** — deliberately,
  because that would be a new T3 honor-system process, the exact category this
  spec retires.
- **AC-12 (ADR + bookkeeping at ship)**: `docs/adr/ADR-011-phase-entry-directive-enforcement.md`
  authored (`status: proposed` → `accepted` at `/ship`); backlog #69 `In
  Progress` → `Shipped`; spec `status: draft` → `shipped`; `/ship` §7 Knowledge
  Consolidation routes this spec's `## Domain Decisions` into
  `docs/architecture/governance.log.md` (the L2 whose scope is explicitly
  "rule authoring, enforcement tiers").

## Non-goals

- **Strands A/B/C/E stay OPEN.** This spec is Strand D (instruction-load /
  enforcement) ONLY. Alignment-side decomposition (A), research quality (B),
  review leverage (C), and per-phase after-action → Skills (E) are untouched;
  choosing D does not close them (`_research-rpi-qrspi-corroboration.md`
  §Next Actions).
- **No numeric instruction-count target / gate.** No `target < 85`, no directive
  counter that FAILs on a threshold — Strand D and `deletion-first-add-gate.md`
  Non-goals both reject naive count thresholds. Count is a measured outcome.
- **No text change to the ADR-008 fenced safety invariants** (AC-4). The fence
  span stays byte-identical (freshness-checked; eval cases + canaries depend on
  it).
- **No new always-loaded `AGENTS.md` text**, no new phase, no new hard gate —
  the change is subtractive (`[enforcement]` lesson + issue #176 headline). The
  AC-11 ratchet is a `tests/ci/` test, ~0 ceiling cost — not always-loaded text.
- **Directive-count ratchet REOPENED and built (supersession note).** An earlier
  draft CLOSED "no machine directive-tier / drift checker." That is superseded:
  the count ratchet (AC-11) is reopened pre-freeze on upstream evidence — a
  private upstream prior-art run's hard-directive keywords grew **+9 / +7.6% in
  6 weeks UNDER a green token ratchet**, demonstrating that observer/advisory-only
  maintenance fails. Token count and directive count are separate axes that need
  separate ratchets. (The ratchet is a `tests/ci/` test, not new always-loaded
  text.)
- **No downstream template changes** (`.agentcortex/templates/*`,
  `spec-app-feature.md`) — the four surfaces are framework-internal; pushing
  enumeration duty downstream would export irrelevant load.
- **No deletion of an eval case without re-mapping** — restated as AC-5 (guard,
  not aspiration).

## Constraints

- **Subtractive only**: delete or merge; no net-add of rule text on the
  always-loaded surfaces (any merge is net-negative).
- **ADR-008 fenced span is a HARD deletion boundary** (validator
  freshness-checked; `AGENTS.md` L19–24).
- Every deletion re-maps/retires its `governance.yaml` `protects`-tag in the
  SAME change (`[eval-mapping][MEDIUM]`).
- `validate.sh` ↔ `validate.ps1` parity mandatory; any new/changed check goes
  through the ADR-006 Python seam (no new native check).
- **Cross-platform parity**: Claude / Codex / Gemini / API consume identical
  surfaces; adapters `@import` and MUST NOT diverge.
- 355k lifecycle ceiling MUST NOT increase; deletions fund (AC-9).
- **Read-Once**: do not add any "re-read <file>" instruction to the surfaces.
- **Governing test**: the `[enforcement][HIGH]` Global Lesson is the deletion
  rubric — every surviving MUST maps to 1 hook/validator/test/observer, else it
  is deleted, merged, or honestly labeled `keep-honest-unenforced`.
- **Primary-verification gate (delegated implementers)**: the primary itself
  runs and quotes the result lines — `validate.sh` + `validate.ps1`, the full
  CI-equivalent `pytest tests/ci/ tests/guard/ .agentcortex/tests/`,
  `run_governance_eval.py --coverage`, `generate_safety_nucleus.py --check` — and
  reconciles `git diff --stat` row-by-row against the enumeration's disposition
  column. Subagent self-reports are hypotheses until the primary re-verifies.

## File Relationship

**EXTENDS** `docs/specs/deletion-first-add-gate.md` — that spec (shipped, GitHub
issue #166 / backlog #65) introduced §13's ADD-Gate + signal tiers *forward-only*
(new rules must declare a tier; existing rules grandfathered). This spec
**retroactively applies §13's ADD-Gate to the four phase-entry surfaces** and
ends grandfathering *for them* — it operationalizes the norm deletion-first
established, using the same T1/T2/T3 vocabulary. **INDEPENDENT** of all other
specs. The enforcement *policy* (grandfathering ends for these surfaces) is
recorded in ADR-011; this spec is its execution.

## Domain Decisions

- [DECISION] Scope is the **four phase-entry surfaces only** (AGENTS.md,
  engineering_guardrails.md, security_guardrails.md, shared-contracts.md).
  Other `.agent/**` files (workflows read heading-scoped, skills) are out of
  scope — this is Strand D's declared bound, and deletion-first already limits
  the Deletion-First norm to the always-loaded surfaces.
- [DECISION] Enforcement tiers reuse §13's **T1/T2/T3 verbatim** (T1
  validator/test/hook · T2 eval-backed case · T3 named human observer); `NONE`
  is the 4th bucket. The **counting unit is semantic**: one enforceable
  behavioral obligation = one row, keyword-independent (a keyword-less imperative
  like the reply-language rule is still a row). No new tier vocabulary is
  invented (would fork the taxonomy governance.log.md already records).
- [DECISION] Success = **100% of directives tier-LABELED (honest `NONE`
  allowed) + every NONE-tier directive carries a disposition**; count reduction
  is an OUTCOME, not a target. A `NONE` survivor is legitimate under
  `keep-honest-unenforced` — deleting a load-bearing-but-unenforceable rule
  (e.g. Read-Once Discipline) is self-harm, and fabricating an observer to
  manufacture a tier is the very theatre being retired. Calibration: expected
  clean deletions ≈ 0–2 (a private upstream prior-art run of the identical
  census deleted ZERO); the deliverable is the map, not the prune. The
  instruction-consistency threshold is a **150–200 range** (research doc
  Corrections), our ~90 sits under it, so a count target would delete
  load-bearing rules to hit a number while ignoring burial depth.
- [DECISION] `primary_domain: governance` (NOT document-governance):
  `governance.log.md` scope is explicitly "rule authoring, **enforcement
  tiers**, behavioral evals" (its L5), while document-governance owns doc
  *lifecycle/taxonomy* (its L6). The parent spec deletion-first-add-gate.md also
  consolidated into governance.log.md — same domain, consistent sink.
- [DECISION] Enumeration artifact = a **one-time dated point-in-time snapshot**
  in `docs/reviews/` — NOT a living table and with **NO observer re-snapshot
  duty** (a re-snapshot duty would be a new T3 honor-system process, the exact
  category this spec retires). Drift is instead caught by a **directive-count
  ratchet test** (`tests/ci/`, cap-at-today). It is **test-tier FAIL, not
  WARN-tier**: the repo's own 355k test-tier ceiling demonstrably formed
  deletion-funding discipline, WARN advisories are ignorable, and a private
  upstream prior-art run's +9 keyword growth UNDER a green token ratchet proves
  observer-only fails. Cap-at-today ≠ the rejected fixed count target — it caps
  growth from today without setting a `target < N` bar.
- [DECISION] ADR-008 fenced cluster is **EXCLUDED regardless of tier** because
  placement governs it: an irreversible-hazard rule stays on the always-loaded
  surface even where its filesystem teeth are T0 advisory (`[rule-placement]`).
  Subagent Safety Delegation is itself T0 but survives *because it is fenced*,
  not because it is enforced — the one deliberate exception to the deletion
  rubric, and it is a placement decision, not a tier decision.
- [DECISION] The **sentinel is not NONE-tier theatre.** grep confirms the Work
  Log `## Phase Summary` half is true T1 (validate.sh/ps1 WARN; validator reads
  the artifact) and the chat-emission half is T2 = adherence measured OFFLINE by
  the eval harness (`governance.yaml sentinel-omission`), NOT live-enforced in
  production. The `[enforcement]` lesson names `⚡ ACX` as a theatre *example*,
  but that naming predates the validator + eval case; both halves survive.
  ADR-011 makes the final call.
- [TRADEOFF] Fewer *fake* tiers → honest labels. A behavior-shaping advisory
  with no teeth is now retained as `keep-honest-unenforced` (labeled `NONE` with
  a rationale) rather than deleted or given a manufactured observer — false
  confidence is removed by honest labeling, not by stripping the prompt. A rule
  genuinely deleted (observability-only) carries no behavioral loss. **Reopen
  trigger**: a post-ship incident traced to a rule this prune removed.
- [CONSTRAINT] Every touched eval case re-maps (SECTION-level) or retires its
  `governance.yaml` `protects`-tag in the same change; a green eval run is NOT
  evidence a rule survived — the runner never reads the protected text
  (`[eval-mapping]`).
- [CONSTRAINT] Burial-depth = **within-loaded-unit ordinal**, a first-class
  audit axis for engineering_guardrails.md. Each directive's read-moment /
  load-layer is marked BEFORE any move; **relocation across load-layers is
  forbidden for always-on rules** and merges may only hold or decrease a
  survivor's ordinal — moving a rule deeper transfers lost-in-the-middle risk
  (Strand D: ordering may matter more than count).
