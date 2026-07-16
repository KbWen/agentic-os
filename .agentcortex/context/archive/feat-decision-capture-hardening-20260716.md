# Work Log: feat/decision-capture-hardening

## Header

- Branch: `feat/decision-capture-hardening`
- Classification: `feature`
- Classified by: `claude-fable-5`
- Frozen: `2026-07-16`
- Created Date: `2026-07-16`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `8aa698e`
- Checkpoint SHA: `8aa698e`
- Recommended Skills: `verification-before-completion, test-driven-development`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `123`

---

## Session Info

- Agent: `claude-fable-5`
- Session: `2026-07-16 15:07 UTC`
- Platform: `claude-code`
- Files Read: `20`

---

## Task Description

Backlog **#138** (from the 2026-07-16 decision-capture govern-audit; systemic half — #139 instance-batch shipped as PR #348): `decide.md §5` "promote to ADR during /ship" is an untriggered orphan — ship.md never reads Work Log `## Decisions`, zero validator/test/eval enforcement, quick-win/hotfix have no durable decision channel, the L2 nudge is user-gated (headless no-op). Fix shape: enforce-or-delete §5 + a ship-time decision-disposition step + WARN-tier validator check behind the ADR-006 seam. HARD constraints: DELETION-FUNDED (token ceiling 355k, headroom ≈63), sh+ps1 parity, work logs gitignored (CI sees only archived logs + INDEX.jsonl), WARN-never-FAIL downstream doctrine, minimal adopter ceremony (conversion thesis #120/#121 outrank).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-16T15:07Z | classification frozen: feature; 3 design-input agents dispatched |
| spec | done | 2026-07-16T15:20Z | docs/specs/decision-capture-hardening.md (draft; 10 AC; 9 Domain Decisions; freeze at ship) |
| plan | done | 2026-07-16T15:25Z | gate PASS; split: tool-half (opus) ∥ doc-half (primary, token math) |
| implement | done | 2026-07-16T15:25Z | opus: tool(304L)+tests(18)+wiring+config+deploy+golden; primary: decide.md §5 / template §Decisions / ship.md 2b + funding trims (net ≤ 0) |
| review | done | 2026-07-16T16:12Z | 第十人 (8 findings, 0 blocking) + 事前驗屍 (8 paths); 12 dispositions; fold-ins applied both halves |
| test | done | 2026-07-16T16:35Z | terminal: pytest 645 passed; validate pass=114 warn=4 fail=0; ceiling 42/42; 4-sim wave PASS (3 sim-fixes folded + re-gated) |
| handoff | done | 2026-07-16T16:38Z | Resume block below; feature gate satisfied |
| ship | pending | — | SSoT via ship flow; spec §8 → L2 consolidation (first self-consumer); 2b executes on THIS log (dogfood #2) |

---

## Phase Summary

- bootstrap: classification feature (behavior-boundary: ship.md + decide.md phase-doc changes + new validator check + tests → spec required per Learning Propagation Rule). ADR coverage per §0a: validator half covered by ADR-006 (applies_to validate.sh/ps1/tools/*.py — new check follows its run_python_check policy); workflow-doc half (ship.md/decide.md) has no covering ADR — decisions will be carried in the spec's `## Domain Decisions` (§8) and consolidated to L2 at ship, which is the designed non-ADR channel for workflow-behavior decisions; /adr skip logged in Drift Log. Design inputs dispatched: opus tradeoff panel (5 questions) + sonnet token-budget scout + sonnet validator-wiring scout. ⚡ ACX
- spec: docs/specs/decision-capture-hardening.md written from the adjudicated 3-input design (10 AC, 9 Domain Decisions, primary_domain document-governance, signal_tier T1). Key corrections baked in from the scouts: only the 8 phase files are token-counted (ship.md ×6 — decide.md/template are FREE), so funding is intra-ship.md; WARN-tier = tool-always-exits-0.
- plan: gate PASS; split implement — tool half (opus: check tool + tests + wiring + config + deploy + golden) ∥ doc half (primary: decide.md §5 rewrite, template §Decisions, ship.md 2b + compression funding with measured char math).
- implement: both halves landed; AC-4 initially FAILED (+257 chars measured) → 4 additional semantic-preserving trims → net −2, ceiling green. Tool 17 tests green, golden +1 line, real-repo run clean.
- review: 第十人 (8 findings, 0 blocking; semantic preservation verified element-by-element; deploy-to-temp-root ground truth) + 事前驗屍 (8 ranked paths; found the deploy-key-ships-SET contradiction + archived-WARN remediation ambiguity). 12 dispositions → fold-ins both halves; deploy-strip REJECTED (core-tier force-update would wipe fork opt-ins) → honest-reframe on 4 surfaces.
- test: user-directed 4-sim behavioral wave (SIM-W/R/V/D) → 3 more sim-driven fixes (2b tripwire, tool Signal A2, non-clearing WARN clause) + funding trims; terminal gates pytest **645 passed** / validate **114-4-0-2** / ceiling **42/42** (ship.md 24,464, net −147 vs HEAD).
- handoff: Resume block complete (HANDEDOFF; Read Map / Skip List / Context Snapshot; honest ceilings recorded).
- ship: 2b executed on THIS log (D-1/D-2 `→ consolidated: L2 document-governance`, D-3 `→ local`; tripwire clean); spec → shipped; SSoT Spec Index row + Ship History top-insert + rotation (ask-local-discovery → archive, count 10) + heartbeat 123→124; §7 consolidated the spec's 9 Domain Decisions into document-governance.log.md (first self-consumption); backlog #138 → Shipped + watch-item; audit routing_action #1 → merged. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T15:07:33Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T15:25:13Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T15:55:00Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T16:12:46Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T16:35:00Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T16:38:01Z
- Gate: ship | Verdict: PASS | Classification: feature | Timestamp: 2026-07-16T16:39:39Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/decision-capture-hardening.md | to be created at /spec |
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | governs the new check's seam (run_python_check) |
| Review | docs/reviews/2026-07-16-govern-audit-decision-capture.md | originating audit (F1 systemic); routing_action #1 pending → this task |
| Backlog | docs/specs/_product-backlog.md #138 | this task; #139 shipped PR #348 |
| PR | https://github.com/KbWen/agentic-os/pull/348 | instance-batch predecessor |

---

## Known Risk

- Token ceiling: ship.md/decide.md are counted phase-docs; any net addition must be deletion-funded (headroom ≈63 tokens). Mitigation: token scout quantifies exact costs + funding candidates before spec freeze; net-delta target ≤ 0.
- Legacy false positives: 113 archived work logs predate any disposition convention — a naive validator check would WARN-flood day one. Mitigation: date/convention grandfathering (ADR-002 lifecycle precedent) is a design input question.
- Ceremony creep vs conversion thesis: every new ship-time step adds adopter friction (#122 caution on record). Mitigation: WARN-tier advisory, headless-safe, output only when `## Decisions` is non-empty.
- Rollback: revert the PR (docs + one Python tool + validator wiring lines + tests — single squash).

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- §0a partial-coverage note: no ADR covers ship.md/decide.md; /adr prompt skipped deliberately — workflow-behavior decisions go to spec §8 Domain Decisions → L2 (the framework's designed channel), and the validator half follows ADR-006. Recorded here per bootstrap §0a Exit-1 skip discipline.
- User-directed simulation wave (mid-review): 4 behavioral e2e sims (SIM-W write-path diligent-vs-hurried · SIM-R read-path replay of the original user-discovered drift · SIM-V violation→WARN→remediation loop · SIM-D downstream deploy ×4 scenarios) run BEFORE ship per the "花式模擬測試" directive. Three sim-driven fixes landed: (1) ship.md 2b tripwire (`→ local` illegal for ADR-naming/reversal entries — SIM-W showed a hurried agent rubber-stamps all-local, 2/3 marker flips, tool clean either way); (2) tool Signal A2 (`ADR-\d` + `→ local` → review-WARN — the tripwire made machine-flagged per the [enforcement] lesson); (3) WARN non-clearing clause (SIM-V empirically proved the post-forward-fix WARN persists byte-identical, pressuring DILIGENT agents toward illegal archive edits). Tripwire funding: 2 further semantic-preserving ship.md compressions (relative-link-hazard + Confidence Trace paragraphs; docs_pin grep zero hits) → ship.md 24,464 chars, net −147 vs HEAD, ceiling test 42/42.
- SIM-D precision note: WARN-tier python checks surface in validate output as `[PASS]` + indented `WARN:` detail (not counted in the summary warn= tally) — pre-existing ADR-006 seam property shared with check_ssot_caps, recorded for future audits, not a defect of this feature.

---

## Review Feedback

Verdict: PASS (0 ship-blocking; both adversarial passes). 12 dispositions:
- ADOPTED: WARN remediation text (archives immutable → forward-fix via new ADR/L2, never a log edit); lenient-accept ASCII `->` (strict-emit `→`; permanent-false-WARN-on-immutable-file class outweighs vocabulary purity); code-fence skip in entry parsing (+ fixture); bootstrap.md:143 none-guard (empty-template nag); ship.md 2b idempotent `decisions[]` wording + "+ Index line" promise-parity + "ship L2 entry" tier-precision; AC-1 length clause amended (uncounted file; binding requirement = promise-parity); AC-5/AC-7/adopter-delta/Domain-Decision honest-reframe (deployed forks are ACTIVE-BY-DEFAULT at the framework cutoff — the "opt-in/silent-until-set" claim was false under core-tier deploy); chat-rule "(unresolved only)" micro-fix; docstring accuracy (3/1/2 legacy-log reality + lexicographic-date limitation).
- REJECTED: deploy-strip of the config key (core-tier force-update would wipe a fork's own opt-in value every upgrade — strip makes opt-in impossible; honest-reframe chosen instead; reopen trigger recorded in spec).
- CLOSED-WITH-REASON: rubber-stamp `→ local` ceiling (spec Non-goal, quantified real by 事前驗屍, reopen trigger well-placed); tracked-vs-glob NIT (non-recursive root glob is behaviorally equivalent; AC-5 reworded); future re-expansion of compressed ship.md text (the 355k pytest IS the guard).

---

## Red Team Findings

- 事前驗屍 A (M×M-H): the check WARNs on archived logs that doctrine declares immutable — remediation ambiguity could induce agents to edit archives. Risk decision: WARN text now names the ONLY legal remediation (forward-fix via new ADR/L2 entry; never edit the archive); guard test asserts the text.
- 事前驗屍 C / 第十人 F1 (H×M): config.yaml deploys core-tier with the cutoff SET → "opt-in downstream" was false. Risk decision: honest-reframe on 4 surfaces + spec reopen trigger ("a real fork reports upgrade WARN-flood → revisit deploy-time cutoff anchoring"); deploy-strip rejected (would wipe fork opt-ins on every force-update). Watch-item: core-tier config force-update clobbers ALL fork-tunable keys (incl. production_paths) — pre-existing framework tension, recorded at ship as a backlog watch-item, not a new row (no observed incident).
- Rubber-stamp `→ local` (M-H×L): accepted honest ceiling per spec Non-goal; reopen on systematic mis-local audit evidence.

---

## Design Reference

none

---

## Observability

none

---

## Resume

- State: `HANDEDOFF` — all gates green; ship is the only remaining phase.
- Completed: spec (draft, 10 AC, 9 Domain Decisions) → split implement (opus tool-half ×3 rounds / primary doc-half with token math) → 第十人 + 事前驗屍 (12 dispositions) → user-directed 4-sim wave (SIM-W/R/V/D) → 3 sim-driven fixes (2b tripwire · tool Signal A2 · non-clearing WARN) → terminal gates (pytest 645 / validate 114-4-0 / ceiling 42-42).
- Next: `/ship` — freeze spec → shipped; SSoT Spec Index row + Ship History top-insert (rotation: 10→11 ejects Ship-fix-ask-local-discovery-surfaces-2026-07-04 to archive) + heartbeat 123→124; §7 Knowledge Consolidation of the spec's 9 Domain Decisions → docs/architecture/document-governance.log.md (FIRST self-consumption); execute 2b on THIS log's 3 D-entries (markers already present); backlog #138 → Shipped + audit routing_action #1 → merged + config-tier watch-item note; archive MOVE + INDEX chain (decisions[] = 3 titles) + lock release; commit (exclude .claude/settings.local.json) → PR → CI watch → merge.
- Context: branch `feat/decision-capture-hardening` off `8aa698e`; spec `docs/specs/decision-capture-hardening.md`; marker vocabulary is a 4-surface API (decide.md §5 / template / ship.md 2b / tool) — strict-emit `→`, lenient-accept `->`; cutoff `2026-07-16` ships SET (core tier, deliberate).

### Read Map
1. `docs/specs/decision-capture-hardening.md` (authority: AC + Domain Decisions)
2. `.agent/workflows/ship.md` §State Update 2b + `.agent/workflows/decide.md` §5 (the wired pair)
3. `.agentcortex/tools/check_decision_disposition.py` + `tests/guard/test_decision_disposition_check.py`
4. This log: `## Review Feedback` (12 dispositions) + `## Drift Log` (sim wave + funding trail) + `## Test Gate Results`

### Skip List
- Scratchpad sim artifacts (`simw/ simv/ simd/` under the session temp dir) — temporal evidence, verdicts summarized here.
- Subagent transcripts; the #139 archive (`chore-orphan-decision-homes-20260716.md`) — separate shipped instance-batch.
- `docs/reviews/2026-07-16-govern-audit-decision-capture.md` body — read only if re-litigating F1 provenance.

### Context Snapshot
- Numbers: pytest 645 · validate 114/4/0/2 · ceiling 42/42 · ship.md 24,464 (−147) · tool 353 lines · guard tests 23 · cutoff 2026-07-16 · legacy ## Decisions logs 3 root (1 with D-entries) + 2 work/ (excluded).
- Honest ceilings on record: A2 covers only ADR-naming rubber-stamps (prose-fuzzy stays honor-system); WARN-tier surfaces as [PASS]+indented WARN (seam property); deployed forks inherit the cutoff SET (deliberate — see spec Domain Decision + reopen trigger).

---

## Test Gate Results

- Command: `python -m pytest tests/ci tests/guard .agentcortex/tests -m "not slow" -q` → **645 passed, 98 deselected** (terminal run on the final tree; 0 failed).
- `bash .agentcortex/bin/validate.sh` → **pass=114 warn=4 fail=0 skip=2** (the +1 pass = the new decision-disposition check registering clean).
- Token ceiling: `test_lifecycle_token_consumption.py` **42/42** incl. `test_aggregate_current_total_stays_under_355k` with the 355_000 literal unchanged; ship.md final 24,464 chars (**net −147 vs HEAD** including the 2b step + tripwire).
- New guard file `tests/guard/test_decision_disposition_check.py`: **23 cases** (unmarked WARN / marked clean / grandfather / config-absent / filename fallback / vocabulary exactness incl. lenient `->` / fence immunity / A2 rubber-stamp flags / dual-signal 2-line cap / real-repo clean / sh+ps1 wiring parity).
- Behavioral e2e sims (pre-ship, user-directed): SIM-R replay = drift HARD-STOPPED at the SSoT ADR-Index line (rotation-proof; counterfactual control confirmed pre-fix re-proposal); SIM-W = diligent 3/3 vs hurried 0/3 dispositions → tripwire + A2 landed; SIM-V = violation loop closed, non-clearing clause landed; SIM-D = 4/4 downstream scenarios PASS with real deploy.sh.

---

## Decisions

### D-1: Strict-emit / lenient-accept marker matching
- **Decision**: All emit surfaces use `→` (U+2192); the validator check additionally accepts ASCII `->`.
- **Reason**: A false WARN lands on an immutable archived file and is permanent — robustness beats purity there.
- **Alternatives**: Strict-both (rejected: permanent typo-WARNs); lenient-both (rejected: emit consistency is free).
- **Impact**: The 4-surface vocabulary constraint carries an explicit accept-asymmetry note.
→ consolidated: L2 document-governance

### D-2: Keep the deployed cutoff key SET; reject deploy-strip
- **Decision**: `decision_disposition_since` ships set at the framework cutoff; deploy does NOT strip it.
- **Reason**: config.yaml is deploy-tier core (force-updated) — stripping would wipe a fork's own opt-in value at every upgrade, making opt-in unusable.
- **Alternatives**: deploy-strip (rejected, above); deploy-time dynamic date (rejected: transform complexity + cutoff laundering on every upgrade).
- **Impact**: Deployed forks are active-by-default; 4 surfaces reframed honestly; reopen trigger in spec.
→ consolidated: L2 document-governance

### D-3: Fold-in scope discipline for bootstrap.md:143
- **Decision**: The none-guard qualifier on bootstrap.md:143 is in-scope for this feature (template now always emits an empty `## Decisions`), added to spec applies_to.
- **Reason**: Without it every fresh template log triggers the inherited-decisions confirmation nag — a regression this feature would introduce.
- **Alternatives**: Leave to #135 (rejected: the nag is caused HERE, not by template-tier work).
- **Impact**: bootstrap.md is a counted file; cost absorbed by ship.md's −149-char funding margin.
→ local

---

## Evidence

- implement (doc half): ship.md 24,611 → 24,609 chars pre-fold-in (net −2; post-fold-in −149 vs HEAD per reviewer measurement); `test_aggregate_current_total_stays_under_355k` PASS ×3 runs (post-edit, post-fold-in). decide.md §5 rewrite + template `## Decisions` are lifecycle-uncounted (verified vs PHASE_WORKFLOW_MAP).
- implement (tool half): check_decision_disposition.py (304 lines) + 18 guard tests; manual run `decision disposition OK (0 logs checked, cutoff 2026-07-16)`; wiring 1 line/validator with identical label; deploy 2 sites + golden +1 line; primary re-ran all (18/18, tool clean, lenient-accept confirmed at :208).
- review: 第十人 — semantic preservation of all 3 ship.md compressions verified element-by-element (9/9 nudge elements; rollback-check heading-scope equivalence; chat-rule nuance); 4-surface vocabulary verbatim; CRLF/cp950/docs_pin/step-numbering all clean; deploy-to-temp-root proved downstream reality. 事前驗屍 — 8 paths ranked; INDEX-rotation + ship-history-2027 exclusion verified year-agnostic.
- test: full CI-equiv 639 passed (pre-fold-in tree) → final run pending below; guard subset 314 passed post-fold-in; lifecycle 42/42 post-fold-in.
