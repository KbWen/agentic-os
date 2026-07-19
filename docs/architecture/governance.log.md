# Governance (meta) — Layer 2 Decision Log

> Append-only chronological entries. Never delete or modify existing entries.
> Each entry records a [DECISION] / [TRADEOFF] / [CONSTRAINT] from a shipped spec.
> Domain scope: meta-governance — rule authoring, enforcement tiers, behavioral evals,
> session/lock discipline. (Document lifecycle decisions live in document-governance.log.md.)

---

### [governance][2026-06-10][feat/deletion-first-add-gate]
source_spec: docs/specs/deletion-first-add-gate.md
source_sha: ccb0294

[DECISION] 3 tiers, not 4: "external standard" as a standalone tier fails the [enforcement] lesson's test (citation ≠ enforcement); demoted to supporting metadata. Tiers map 1:1 to the lesson's taxonomy (validator/test/hook · eval case · named observer), ordered strongest-first so authoring is "pick strongest feasible", not a 4-way judgment.

[DECISION] Deletion-First scope = the three always-loaded surfaces only (AGENTS.md, .agent/rules/*, shared-contracts.md). Workflow files are heading-scope-read and mostly receive operational fixes — taxing each tweak with a deletion citation is the heaviness this feature is forbidden to add. The ADD-gate still covers workflows for NEW gates.

[DECISION] T2 is constrained to rules inside the eval harness's governance files — the seed-schema test requires `protects` anchors to resolve against that inventory; expanding the inventory for workflow gates would be scope creep (workflow gates use T1: validate.* already does workflow-literal checking).

[CONSTRAINT] `signal_tier: none` escape exists so tooling-only governance specs don't WARN forever — a nagging false positive trains people to ignore the validator.

### [governance][2026-07-19][feature/directive-enforcement-audit]
source_spec: docs/specs/directive-enforcement-audit.md
source_sha: 3004d88

- [DECISION] Scope is the **four phase-entry surfaces only** (AGENTS.md, engineering_guardrails.md, security_guardrails.md, shared-contracts.md). Other `.agent/**` files (workflows read heading-scoped, skills) are out of scope — this is Strand D's declared bound, and deletion-first already limits the Deletion-First norm to the always-loaded surfaces.
- [DECISION] Enforcement tiers reuse §13's **T1/T2/T3 verbatim** (T1 validator/test/hook · T2 eval-backed case · T3 named human observer); `NONE` is the 4th bucket. The **counting unit is semantic**: one enforceable behavioral obligation = one row, keyword-independent (a keyword-less imperative like the reply-language rule is still a row). No new tier vocabulary is invented (would fork the taxonomy governance.log.md already records).
- [DECISION] Success = **100% of directives tier-LABELED (honest `NONE` allowed) + every NONE-tier directive carries a disposition**; count reduction is an OUTCOME, not a target. A `NONE` survivor is legitimate under `keep-honest-unenforced` — deleting a load-bearing-but-unenforceable rule (e.g. Read-Once Discipline) is self-harm, and fabricating an observer to manufacture a tier is the very theatre being retired. Calibration: expected clean deletions ≈ 0–2 (a private upstream prior-art run of the identical census deleted ZERO); the deliverable is the map, not the prune. The instruction-consistency threshold is a **150–200 range** (research doc Corrections), our ~90 sits under it, so a count target would delete load-bearing rules to hit a number while ignoring burial depth.
- [DECISION] `primary_domain: governance` (NOT document-governance): governance.log.md scope is explicitly "rule authoring, **enforcement tiers**, behavioral evals", while document-governance owns doc *lifecycle/taxonomy*. The parent spec deletion-first-add-gate.md also consolidated into governance.log.md — same domain, consistent sink.
- [DECISION] Enumeration artifact = a **one-time dated point-in-time snapshot** in `docs/reviews/` — NOT a living table and with **NO observer re-snapshot duty** (a re-snapshot duty would be a new T3 honor-system process, the exact category this spec retires). Drift is instead caught by a **directive-count ratchet test** (`tests/ci/`, cap-at-today). It is **test-tier FAIL, not WARN-tier**: the repo's own 355k test-tier ceiling demonstrably formed deletion-funding discipline, WARN advisories are ignorable, and a private upstream prior-art run's +9 keyword growth UNDER a green token ratchet proves observer-only fails. Cap-at-today ≠ the rejected fixed count target — it caps growth from today without setting a `target < N` bar.
- [DECISION] ADR-008 fenced cluster is **EXCLUDED regardless of tier** because placement governs it: an irreversible-hazard rule stays on the always-loaded surface even where its filesystem teeth are T0 advisory (`[rule-placement]`). Subagent Safety Delegation is itself T0 but survives *because it is fenced*, not because it is enforced — the one deliberate exception to the deletion rubric, and it is a placement decision, not a tier decision.
- [DECISION] The **sentinel is not NONE-tier theatre.** The Work Log `## Phase Summary` half is true T1 (validate.sh/ps1 WARN; validator reads the artifact) and the chat-emission half is T2 = adherence measured OFFLINE by the eval harness (`governance.yaml sentinel-omission`), NOT live-enforced in production. The `[enforcement]` lesson names `⚡ ACX` as a theatre *example*, but that naming predates the validator + eval case; both halves survive. ADR-011 makes the final call.
- [DECISION] *(ship-added, Work Log D-2 disposition — provenance: primary adjudication 2026-07-19, not in the spec's own section)* ADR frontmatter `classification` describes the DECISION's nature, not the task tier: a `feature`-classified task may author an `architecture-change`-classified ADR (ADR-010 precedent, reaffirmed by ADR-011).
- [TRADEOFF] Fewer *fake* tiers → honest labels. A behavior-shaping advisory with no teeth is now retained as `keep-honest-unenforced` (labeled `NONE` with a rationale) rather than deleted or given a manufactured observer — false confidence is removed by honest labeling, not by stripping the prompt. A rule genuinely deleted (observability-only) carries no behavioral loss. **Reopen trigger**: a post-ship incident traced to a rule this prune removed.
- [CONSTRAINT] Every touched eval case re-maps (SECTION-level) or retires its `governance.yaml` `protects`-tag in the same change; a green eval run is NOT evidence a rule survived — the runner never reads the protected text (`[eval-mapping]`).
- [CONSTRAINT] Burial-depth = **within-loaded-unit ordinal**, a first-class audit axis for engineering_guardrails.md. Each directive's read-moment / load-layer is marked BEFORE any move; **relocation across load-layers is forbidden for always-on rules** and merges may only hold or decrease a survivor's ordinal — moving a rule deeper transfers lost-in-the-middle risk (Strand D: ordering may matter more than count).
