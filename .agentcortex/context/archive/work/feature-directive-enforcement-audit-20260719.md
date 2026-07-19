# Compaction overflow: feature/directive-enforcement-audit (2026-07-19)

> /handoff §6 compaction overflow of the still-active Work Log — NOT final archival.
> Active log: `.agentcortex/context/work/feature-directive-enforcement-audit.md`.
> Sections below are verbatim copies moved out to satisfy the 12KB active-log cap.

## Task Description (full)

- Issue [#176](https://github.com/KbWen/agentic-os/issues/176) / backlog #69 (P1): phase-entry hard-directive audit + prune. Enumerate every MUST/NEVER-class directive live at non-tiny-fix phase entry (`AGENTS.md`, `engineering_guardrails.md`, `security_guardrails.md`, `shared-contracts.md`); mark each with its enforcement backing (hook / validator / test / external observer / none); DELETE or merge unenforced honor-system MUSTs per Global Lesson 19c054e7 + guardrails §13 Deletion-First. Original issue target "count below ~85" was superseded pre-freeze by the research correction (threshold is a 150–200 RANGE; count = outcome, not target). Subtractive; ADR-011; cross-platform parity.
- Evidence at bootstrap: issue's 2026-06-03 measurement ~90 directives; 2026-07-19 recount 132 keyword hits (38/84/6/4) — grown through v1.8.9→v1.8.14 additive waves.
- Full phase chain: [/brainstorm →] /spec (ADR) → /plan → /implement → /review → /test → /handoff → /ship. Brainstorm skipped (strands A–E in `_research-rpi-qrspi-corroboration.md` provide the divergence; Drift-logged).

## Phase Summary

> Full-length phase entries moved here by /handoff §6 compaction.

- test: PASS — full CI-equiv 656 passed 0 failed (new: 1 adversarial counting-semantics pin test + citation fix, commit 3004d88); AC coverage map recorded in §Test Gate Results; adversarial cases landed as executable tests; validators fail=2 both = expected pre-ship. 5-Gate: scope✓ quality✓ evidence✓ risk✓(rollback=revert branch) communication✓. Next: /handoff (mandatory for feature). | Confidence: 95% — high ⚡ ACX
- review: PASS (Ready: yes) — fresh-context acx-reviewer (opus, freshness invariant honored: diff+spec+standards only). Burden of Proof: AC-1..AC-11 ✅ PROVEN with self-run evidence (ratchet 7/7, nucleus --check 0, coverage clean, fence 0-line diff, scan_credentials --range clean, baseline==live counts 37/84/6/4), AC-12 ⚠️ PARTIAL (ship-phase gap, by design). 10-row enumeration spot-verify: 0 refuted. Red Team Full: 0 CRIT/HIGH. Findings adjudicated by primary: 1 LOW→no-defect (bootstrap-sanctioned SSoT metadata write), 1 NIT→ship-prep fix (tests/guard/ dir prefix in 3 citations, fixed in 3004d88). Domain Decisions 10/10 tagged. Scope: 13/13 files map to ACs. ⚡ ACX
- implement: commit a440960 — enumeration (112 rows, opus, primary-verified vs ground truth) + ratchet TDD (sonnet, red→green; red caught a real table-schema violation) + adjudicated surface edits (opus; 2 merges + false-Gate-FAIL deletion + §9.5 dup removal + §13 reword + protects re-map). Primary-caught fixes: compact-index staleness misattributed by editor (registry:36 detail_ref AGENTS.md — regenerated ×2), illegal `Gate: spec` receipt removed (LEGAL_STRICT has no spec gate), protects inventory-membership test required MUST-bearing §Chat Language Policy (+1 keyword, baseline 37). Keyword census 132→131; AGENTS.md −200 chars, guardrails +217 (E4-funded, 355k test green 42/42). Evidence: 655 CI-equiv passed; validate.sh+ps1 both fail=2 (expected pre-ship); ratchet 7/7; eval coverage clean; nucleus --check green; fence byte-identical. Security quick-scan: docs/tests/yaml only, no code paths (A01-A03 n/a); scan_credentials green inside validators. | Confidence: 93% — high ⚡ ACX
- plan: 7 steps, Normal mode; targets = 4 surfaces + enumeration snapshot (docs/reviews/) + ratchet test/baseline (tests/ci/ + .agentcortex/metadata/) + governance.yaml re-maps + §13 grandfathering sentence; executors per D-1 (opus×2: enumeration fan-out + surface edits; sonnet×2: ratchet TDD + eval re-map) with C15 primary verification gate; spec frozen by user pre-plan. | Confidence: 92% — high ⚡ ACX
- spec: `docs/specs/directive-enforcement-audit.md` (draft→frozen; primary_domain: governance; signal_tier T3→T1 after panel; EXTENDS deletion-first-add-gate.md) + `docs/adr/ADR-011-phase-entry-directive-enforcement.md` (proposed — one decision: end §13 grandfathering on the four phase-entry surfaces) drafted by opus per D-1, adversarially verified by primary. KEY REFRAME: threshold is a 150–200 RANGE — no `<85` target. Sentinel ⚡ ACX NOT theatre: Work Log half T1 (validate.sh:1612-1618 / validate.ps1:1561-1565 WARN), chat half T2 (`sentinel-omission` L95); [enforcement] lesson's ACX example stale. ADR-008 fence = AGENTS.md L19–24 byte-exact. ⚡ ACX
- bootstrap: classified `feature` (backlog #69 authority; deps #45 + #65 both Shipped 2026-06-10). 8 skills matched. Context: SSoT (seq 125; Last Verified→2026-07-19 guarded write), state_machine, guardrails Full §1–§13, L1 document-governance.md, skill_conflict_matrix, downstream-capabilities (kb-main OK@38c4365a93ee schema 5). ADR coverage exit=0 (ADR-001/004/008). Backlog #69 Pending→In Progress. Private scan: research-skill-content-optimization.md (backlog #83) surfaced, distinct task, not resumed. ⚡ ACX

## Known Risk (full)

- **ADR-008 fenced safety block**: AGENTS.md safety invariants are fenced + mirrored in AGENTS.safety.md with freshness check — pruning MUST NOT delete/weaken them; validator will catch, but plan must exclude them up front.
- **Eval protects-tag orphaning** (14ac98ca): deleting rule text an eval protects-tag anchors silently creates verifier-without-defense. Every deletion re-maps/retires its cases same-change.
- **Advertised-but-unenforced drift** (3b15e10b): READMEs/adapters advertise always-on rules; deleting canonical text without syncing claims recreates the inverse failure. Cross-surface sync required.
- **Sentinel**: RESOLVED at spec — KEEP/KEEP (T1 worklog + T2-offline chat), ADR-011 §Sentinel Adjudication.
- Plan-phase risks R1–R6 (2026-07-19):
  - R1 Reword breaks pinned literals → AC-6 enumerated checklist before/after every edit + full CI-equiv pre-push. Rollback: revert branch PR (docs+test only; no engine change).
  - R2 Eval orphaning silent (green ≠ survival) → AC-5 section-verify-or-retire + `run_governance_eval.py --coverage` output pasted.
  - R3 Ratchet baseline wrong-at-birth → TDD fixtures first (growth FAIL, equal/lower PASS) before wiring real counts.
  - R4 Delegated-executor misreport → C15 primary verification gate: primary itself runs both validators + full CI-equiv + nucleus --check + git diff --stat reconciled row-by-row vs dispositions.
  - R5 Frozen-spec intersection: downstream-adaptability-optimization.md (frozen) governs AGENTS.md only at the ADR-008 fence span — untouched by design (AC-4); no unfreeze required.
  - R6 Enumeration row count may exceed ~90 (semantic unit catches keyword-less imperatives) → count is outcome-only, layer-stratified per AC-1. (Actual: 112 rows.)

## Decisions (full bodies)

### D-1: Delegated-executor arrangement (user-directed 2026-07-19)
- Decision: Development and implementation work (spec/ADR drafting, /implement changes) is delegated to sonnet and opus subagents. The primary (Fable 5) orchestrates, owns all gates, remains sole Work Log writer + `⚡ ACX` emitter, and independently verifies every subagent self-report against ground truth before accepting (per feedback_verify_subagent_self_reports + §8.2 Junior Tool rule).
- Reason: user directive ("開發和實作交給sonnet和opus"); cost/capability split — primary verifies, delegates draft.
- Alternatives: primary implements directly (rejected by user); external executor codex-cli (not requested).
- Impact: /implement runs via subagents with model overrides; safety floor present in each subagent context; destructive-command gate stays with primary.

### D-2: Task stays `feature`; ADR-011 frontmatter keeps `classification: architecture-change` (2026-07-19)
- Decision: no reclassification. Task classification remains `feature` (frozen at bootstrap); the ADR's own frontmatter `classification: architecture-change` describes the DECISION's nature, mirroring ADR-010 precedent (ADR frontmatter class ≠ task tier).
- Reason: backlog #69 row declares Tier: feature (authority); the change deletes unenforced doc text + syncs evals/validators — no state-machine, phase-order, or data-flow alteration (guardrails §10.1 triggers not met). Feature path already runs full review+test+handoff gates.
- Alternatives: reclassify to architecture-change (rejected — trips no §10.1 trigger; pure re-traversal cost, no added gate value).
- Impact: /plan proceeds under feature gates; ADR-011 accepted at /ship per its §Status.

### D-3: Spec-phase adjudications of drafter open questions (2026-07-19)
- Decision: (a) enumeration artifact = dated docs/reviews/ snapshot, NOT a living file; (b) spec signal_tier T3 at draft (later T1 after D-4 ratchet adoption); (c) sentinel KEEP/KEEP adopted into AC-10 with human-overrule path preserved.
- Reason: living tables rot into the unenforced-obligation class this task deletes; dated snapshots match docs/reviews/ precedent.
- Impact: /plan targets the snapshot path.

### D-4: Roundtable adjudication — 第十人(18 findings) + 事前驗屍(13 scenarios) + upstream premise-check P1–P7 (2026-07-19)
- Decision: pre-freeze revision of spec+ADR per adjudicated findings. ADOPTED: (1) F1/F15 fatal — AC-2/AC-3 gain `keep-honest-unenforced` disposition; "zero NONE survivors" absolutism dropped (Read-Once Discipline verified zero-backing yet behavior-bearing — deletion would be self-harm); delete reserved for observability-only clauses (upstream census criterion). (2) F2/F12/F13 — four surfaces do NOT co-load; AC-1 gains read-moment/load-layer column + semantic counting unit ("one enforceable behavioral obligation = one row"); AC-7 line-offset → within-loaded-unit ordinal; no cross-load-layer relocation of always-on rules (P3). (3) F3/F10 + PM#2 — expected census deletions ≈0–2 stated honestly; deliverable recalibrated to tier-labeling map; ADR decision #2 reworded. (4) F4/F5 + PM#2/#4 — Non-goal REOPENED on upstream evidence (+9 keywords under green token ratchet): ship a directive-count RATCHET pytest (cap-at-post-prune baseline, FAIL only on growth, baseline lowers monotonically — mirrors 355k pattern; NOT a fixed target). Adjudicated between conflicting reviewers: 第十人's WARN-only overruled — repo's own 355k test-tier precedent formed real deletion-funding discipline, WARN-tier advisories are ignorable; PM's version adopted. AC-11's observer re-snapshot duty DELETED (F11 — was new T3 theatre); enumeration = one-time point-in-time snapshot; ratchet is the durable T1 instrument. (5) F6 + PM#3 — AC-5: section-granularity reality; verify-or-retire only; --coverage output required; green eval ≠ survival. (6) F7/F8/F18 + PM#1/#8/#13 — AC-6 becomes enumerated protected-token checklist (worklog-key, routing pin, fence+nucleus --check, sentinel, adapter pins, bootstrap.md §1 duplicates, intra-surface cross-refs, mirrors, compact-index, full CI-equiv + both validators as evidence). (7) F9 — sentinel chat half relabeled "T2 offline-measured, not live-enforced"; KEEP/KEEP stands. (8) F14 — ADR effect-claim downgraded (count growth machine-caught; semantic drift unmeasured). (9) PM#9 — primary-verification gate command list into Constraints. (10) PM#10/#11/#12 — fence git-diff-empty gate; lifecycle baseline --apply same-change; sentinel disposition bound to eval retirement.
- Verification: all load-bearing reviewer claims independently re-grepped by primary before adoption (validate.sh:702 worklog-key, :2587-2592 routing pin, :565+ adapter pins, :2826-2833 baseline; Read-Once/Token-Leak zero hits in validate.sh+governance.yaml; run_governance_eval coverage = zero-coverage-rules only, no orphan detection).
- Rejected/overruled: F10's task-reclassification (D-2 stands); F11's living-file (point-in-time snapshot + T1 ratchet instead); P5's monotone cap as WARN (upgraded to test-tier); P2's "expect zero deletions" as an AC (calibration, not a bar).
- External-signal note (4faa557a): upstream executed-run evidence + human steer = non-same-vendor signal supplementing the 2-opus panel.

### D-5: Census adjudication (primary, 2026-07-19)
- Decision: enumeration ACCEPTED (112 rows; spot-checks vs ground truth all pass; 5 sampled eval case-ids verified). Dispositions: (1) row 1 FLAG → keep + re-map `chat-language-drift` protects →§Chat Language Policy; (2) row 52 FLAG → keep-honest-unenforced + DELETE the false "Skipping this load = Gate FAIL" claim (MUST-load stays); (3) rows 44/45 merge — delete Runtime v1 items 9/10, fold unique clauses into No Bypass Rule, renumber 11→9/12→10 with repo-wide ref grep; (4) §9.5 dup → merge into §9.2; (5) §13 grandfathering reworded per ADR-011; (6) delete=0 + add-enforcement=0 accepted; (7) table fixes: row 45 tier T1/T2→T1 (caught RED by the structure test — TDD working), FLAG rows re-dispositioned, header PROPOSED→ADJUDICATED; (8) baseline recounted post-edit.
- Evidence: ratchet 6/7 pre-fix (the 1 fail = the genuine row-45 violation); layer-stratified result confirms spec Reframe (max co-load ~102, quick-win ~60 — both under 150–200).

## Red Team Findings (full)

- 2026-07-19 /review (Full mode, fresh opus): 0 CRITICAL, 0 HIGH, 2 LOW, 1 INFO — no risk decisions required.
  - LOW: baseline json can be hand-bumped upward to loosen the ratchet — git-diff-visible, mirrors lifecycle-baseline pattern, disclosed limitation.
  - LOW: keyword regex has no word boundary (`MUSTARD` counts) and lowercase evades — internally consistent; can only loosen, never false-FAIL; pinned as executable tests in 3004d88.
  - INFO: keep-honest-unenforced labels live in non-phase-loaded docs/reviews/ — runtime surfaces unchanged; mislabel risk guarded by incident reopen-trigger.
  - Semantic-loss probe (deleted items 9/10, §9.5, false Gate-FAIL claim): NONE lost.
