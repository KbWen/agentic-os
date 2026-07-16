---
status: shipped
date: 2026-07-16
classification: feature
primary_domain: document-governance
signal_tier: T1
applies_to:
  - ".agent/workflows/decide.md"
  - ".agent/workflows/ship.md"
  - ".agentcortex/templates/worklog.md"
  - ".agentcortex/tools/check_decision_disposition.py"
  - ".agentcortex/bin/validate.sh"
  - ".agentcortex/bin/validate.ps1"
  - ".agent/config.yaml"
  - ".agentcortex/bin/deploy.sh"
  - ".agent/workflows/bootstrap.md"
---

# Decision-Capture Hardening (backlog #138)

## Goal

Close finding **F1** of the 2026-07-16 decision-capture govern-audit
(`docs/reviews/2026-07-16-govern-audit-decision-capture.md`): `decide.md §5`
promises an ADR-promotion "during /ship" that ship.md never implements (0
reads of Work Log `## Decisions`, 0 enforcement), so quick-win/hotfix product
decisions reach only volatile sinks (82→83/113-114 archived INDEX entries
carry decisions with empty `specs: []`). Fix: a ship-time **Decision
Disposition** step (every `## Decisions` entry gets a marker: promoted /
consolidated / local), truth-in-advertising rewrites on the free surfaces
(decide.md §5, worklog template), and a WARN-tier validator backstop behind
the ADR-006 seam — token-neutral on the ×6-counted ship.md via same-file
funding.

**Adopter delta**: before — a downstream agent's mid-task decisions silently
evaporate at ship unless a user answers the L2 nudge; after — every non-tiny
ship forces a one-time impact judgment per decision, the 1-liner lands in
INDEX.jsonl `decisions[]` (surfaced at bootstrap on module overlap), and a
CI-visible WARN names any post-cutoff archived log with undisposed entries.
Engine gates/state machine unchanged. Deployment semantics: config.yaml ships
core-tier with the cutoff SET, so deployed forks are active-by-default at the
framework cutoff (they receive ship.md 2b + the template in the same deploy,
so their new logs are marked from day one; pre-upgrade post-cutoff logs may
WARN once, with remediation text naming the legal forward-fix). Absent/empty
key = silent no-op (source-mode/BYO opt-out).

## Acceptance Criteria

- **AC-1 (decide.md §5 rewrite)**: §5 renamed "Promotion & Disposition";
  promises ONLY what ship.md does (marker-tagging + routing); defines the
  3-marker vocabulary and the promote-worthy heuristic (multi-branch/module/
  future-task impact, new reusable precedent, or reverses a durable decision);
  no longer claims ship auto-authors ADRs. Length is unconstrained (the file
  is lifecycle-uncounted); the binding requirement is decide.md §5 ↔ ship.md
  2b promise-parity (zero unimplemented promises).
- **AC-2 (template section)**: `.agentcortex/templates/worklog.md` gains an
  optional `## Decisions` section (blockquote format hint naming decide.md §2
  + the ship-time disposition, `none` default). NO validator required-section
  set or test changes (section checks are per-name; none requires Decisions).
- **AC-3 (ship.md step 2b)**: new step **2b. Decision Disposition** inside
  §State Update & Archival, immediately BEFORE the archival MOVE (markers are
  written while the log is active); scope = all classifications except
  tiny-fix; explicit skip when `## Decisions` is absent/empty; vocabulary
  `→ promoted: ADR-<id>` / `→ consolidated: L2 <domain>` / `→ local`;
  headless = agent self-marks (no user prompt); instructs copying each entry
  title into the INDEX.jsonl `decisions[]` field (existing step); references
  the check by bare name (no `.agentcortex/tools/` path string); carries the
  SIM-W tripwire: `→ local` is illegal for an entry naming an `ADR-<n>` or
  reversing a durable decision (closes the zero-judgment rubber-stamp for the
  machine-checkable class).
- **AC-4 (token neutrality)**: ship.md net character delta ≤ 0, funded by
  compressing the Quick-win/Hotfix Knowledge Nudge prose IN PLACE with
  semantics preserved (scope, domain inference incl. no-silent-guess, the
  single once-per-ship prompt, yes→L2 append/create-on-confirm, no→silent
  skip, never-a-gate). `test_aggregate_current_total_stays_under_355k` passes
  with the 355_000 literal UNCHANGED.
- **AC-5 (check tool)**: `.agentcortex/tools/check_decision_disposition.py` —
  WARN-tier (ALWAYS exits 0; findings are `WARN:` lines); scans
  `.agentcortex/context/archive/*.md` root only, non-recursive (excludes the
  `work/` subdir, `ship-history-*.md`, `.gitkeep.md`); Signal A only: a
  `## Decisions` section containing `### D-` entries where an entry body
  carries none of the three markers — matching is strict-emit/lenient-accept
  (ASCII `->` normalized to `→` before matching) and skips fenced code blocks;
  grandfathering: only logs whose INDEX.jsonl `shipped` date (fallback:
  filename `-YYYYMMDD` suffix; undatable → skip) ≥ config
  `document_lifecycle.decision_disposition_since`; key absent/empty → one-line
  "not configured — skipped" note, exit 0; Signal A findings aggregate into
  ONE summary WARN that lists offending files, names the legal remediation
  (archives are immutable — forward-fix via a new ADR/L2 entry, never a log
  edit), AND states the WARN does not clear after that fix (SIM-V: an
  unclearable line must never read as "edit the archive"); **Signal A2**: a
  disposed `→ local` entry whose body names an `ADR-<n>` (fence-skipped)
  emits one additional aggregate review-WARN line (max 2 WARN lines/run);
  stdout UTF-8 reconfigure guard (cp950 consoles).
- **AC-6 (wiring parity)**: exactly one `run_python_check "... " WARN ...`
  line in validate.sh and one `Invoke-PythonCheck ... -MissingPythonLevel
  'WARN'` line in validate.ps1, identical label text; NO native backstop
  (native-check ratchet baseline untouched).
- **AC-7 (config)**: `.agent/config.yaml §document_lifecycle` gains
  `decision_disposition_since: "2026-07-16"` with a comment naming the
  consumer tool, the absent/empty = silent semantics, AND the honest
  deployment note (core-tier ships the key SET → deployed forks inherit the
  framework cutoff; advisory-only consequences).
- **AC-8 (tests)**: `tests/guard/test_decision_disposition_check.py` with ≥8
  subprocess-driven cases: post-cutoff unmarked → WARN; fully-marked → clean;
  pre-cutoff unmarked → grandfathered clean; config-absent → silent no-op;
  filename-date fallback; marker-vocabulary exactness (all 3 accepted, near-miss
  rejected); real-repo run (must be clean: the 5 legacy `## Decisions` logs all
  predate the cutoff); sh+ps1 wiring-parity assertion (both validators contain
  tool name + label).
- **AC-9 (deploy parity — #334 lesson)**: tool filename added to BOTH
  deploy.sh whitelist sites (dry-run `_runtime_tools` string + `runtime_tools`
  array) and `tests/ci/fixtures/deploy_manifest_golden.txt` regenerated in the
  same change — downstream forks get the tool (silent until they set the key),
  never a `[SKIP] tool not present` line.
- **AC-10 (ship bookkeeping)**: at /ship — Spec Index row added; audit report
  routing_action #1 (decide.md §5 orphan) flipped to `merged`; backlog #138 →
  Shipped; spec status → shipped; §7 Knowledge Consolidation runs on THIS
  spec's Domain Decisions into `docs/architecture/document-governance.log.md`
  (first self-consumer of the channel it hardens).

## Non-goals

- **No semantic marker validation** (is `→ local` the RIGHT call?) — presence
  teeth only; rubber-stamp `→ local` is the accepted honest ceiling. Reopen
  trigger: an audit shows systematic mis-`local` of project-wide decisions.
- **No Signal B** (INDEX `decisions[]` emptiness cross-check) — samples show
  the field is already populated at ship; B would muddy the single trigger.
- **No L2 auto-append for quick-win decisions** — L2 is bootstrap-invisible
  (audit F3: write-only sink); the INDEX 1-liner IS the surfaced durable home.
  Reopen trigger: a re-derivation incident traced to a decision whose INDEX
  1-liner existed but whose reasoning was unrecoverable.
- **No native no-Python backstop** — WARN-tier advisory degrades to SKIP
  without Python (check_ssot_caps precedent); only FAIL-tier checks earn
  native backstops.
- **No eval-registry case** — enforcement is validator + pytest landing in the
  SAME change ([eval-mapping] lesson satisfied by stronger means than an eval).
- **No required-section enforcement of `## Decisions`** — stays optional
  (classification-aware template work is backlog #135's territory).
- **No active `work/` log scanning** — gitignored, CI-blind; disposition is a
  ship-completion property checked post-archival.
- **No ceiling bump** — the 355_000 test literal does not move.

## Constraints

- WARN-never-FAIL for anything downstream forks hit (framework doctrine).
- ship.md is lifecycle-counted at ×6 (all 6 scenarios) — every added char
  costs 6; decide.md and templates/worklog.md are UNCOUNTED (verified against
  `analyze_token_lifecycle.py` PHASE_WORKFLOW_MAP + trigger-registry).
- sh + ps1 parity mandatory; Python checks only via the ADR-006 seam.
- Read-Once: ship.md's step 2b text must be self-contained (no "re-read
  decide.md" instruction at ship time).
- Marker vocabulary is a regex-stable 4-surface API (decide.md, template,
  ship.md, check tool) — verbatim alignment required.

## File Relationship

INDEPENDENT new spec. Modifies behavior text in `.agent/workflows/decide.md`
+ `ship.md` (EXTENDS both; no existing spec owns them for this concern);
complements `governance-self-audit-workflow.md` (the audit that produced F1)
and the shipped #139 instance-batch (PR #348).

## Domain Decisions

- [DECISION] Disposition happens at /ship, in the ACTIVE log, immediately
  before the archival MOVE — markers must exist in the file that gets
  archived. Impact gates promotion, not tier: quick-win/hotfix are included
  (F1's leak), and a quick-win CAN be promote-worthy (the design_tool
  rejection was). Vocabulary: `→ promoted: ADR-<id>` / `→ consolidated: L2
  <domain>` / `→ local`.
- [DECISION] The durable surfaced home for non-promoted decisions is the
  INDEX.jsonl `decisions[]` 1-liner (read at bootstrap on module overlap),
  NOT an L2 auto-append — L2 is bootstrap-invisible (write-only sink, audit
  F3); spending headless ceremony on an unread surface was rejected.
- [DECISION] Enforcement = `check_decision_disposition.py`, WARN-tier via the
  ADR-006 seam with the tool ALWAYS exiting 0 (WARN-tier is a property of the
  tool's exit contract, not of `missing_python_level`); no native backstop;
  ratchet untouched (mirrors check_ssot_caps, not check_routing_actions).
- [DECISION] Scan surface = tracked archive ROOT logs only: active `work/`
  logs are gitignored (CI-blind) and legitimately undisposed pre-ship;
  `archive/work/` holds compaction offloads of still-active logs — both
  excluded by design.
- [DECISION] Grandfathering hangs on one switch:
  `document_lifecycle.decision_disposition_since` (INDEX.jsonl `shipped` date;
  filename `-YYYYMMDD` fallback; undatable → skip). Absent/empty key = silent
  no-op (source-mode/BYO opt-out). Deployed forks inherit the key SET
  (config.yaml is deploy-tier core, force-updated — a deploy-time strip was
  REJECTED: force-update would wipe a fork's own opt-in value every upgrade);
  they simultaneously receive ship.md 2b + the template, so only pre-upgrade
  post-cutoff logs can WARN, once, with remediation text. Reopen trigger: a
  real fork reports an upgrade WARN-flood → revisit deploy-time cutoff
  anchoring.
- [DECISION] decide.md §5 is REWRITTEN, not deleted — the promote-worthy
  heuristic survives; the section now promises only what ship.md 2b executes.
  Token funding is intra-ship.md (Knowledge Nudge prose compression, semantics
  preserved) because decide.md/template are lifecycle-uncounted and cannot fund
  a counted file.
- [TRADEOFF] Teeth are structural (marker presence + the syntactic A2
  tripwire), not fully semantic. SIM-W quantified the gap: a hurried agent
  rubber-stamps all entries `→ local` (2/3 flips vs a diligent agent) — the
  tripwire + A2 close the machine-checkable half (ADR-naming entries cannot
  legally be `→ local`); prose-fuzzy cases (e.g. doctrine-affirming entries
  with no ADR number) stay honor-system. Accepted ceiling per the
  [enforcement] Global Lesson; gain is ~0–5% → 100% forced judgment + flagged
  ADR-naming locals. Reopen: audit shows systematic mis-`local` beyond the
  A2-checkable class.
- [CONSTRAINT] The 3-marker vocabulary is a regex-stable API across exactly 4
  surfaces (decide.md §5, worklog template hint, ship.md 2b, check tool) —
  any wording change is a 4-surface sync, guard-tested by the vocabulary
  exactness case (AC-8). Emit is strictly `→` (U+2192); the check ACCEPTS
  ASCII `->` as equivalent (Postel) because a false WARN lands on an immutable
  archived file and would be permanent.
- [CONSTRAINT] Every validator-wired tool ships in deploy.sh runtime_tools
  (both whitelist sites) + regenerated manifest golden in the SAME change —
  the #334 downstream-SKIP gap class must not recur.
