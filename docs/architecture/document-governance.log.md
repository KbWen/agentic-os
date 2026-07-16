# Document Governance — Layer 2 Decision Log

> Append-only chronological entries. Never delete or modify existing entries.
> Each entry records a [DECISION] / [TRADEOFF] / [CONSTRAINT] from a shipped spec.
> See L1 Synthesis: [docs/architecture/document-governance.md](document-governance.md)

---

### [document-governance][2026-04-25][architecture-change/adr-002-lock-unification]
source_spec: docs/specs/lock-unification.md
source_adr: docs/adr/ADR-002-guarded-governance-writes.md
source_sha: <ship-commit-sha>

[DECISION] Replace path-restricted lock in `guard_context_write.py` with policy-driven allow-list (`.agent/config.yaml §guard_policy.protected_paths`). Preserves safety while expanding scope to all framework governance files (AGENTS.md, .agent/rules/**, .agent/workflows/**, docs/adr/**, docs/architecture/*.log.md, docs/specs/_product-backlog.md).

[DECISION] CI lint (`tools/lint_governed_writes.py`) enforces guard usage at PR time, not at runtime. Workflow authors using direct `open()` against governed paths get FAIL in CI; `# guard-exempt: <reason>` opt-out preserved with per-file exemption count tracking.

[DECISION] `lifecycle:` frontmatter contract for governance docs (audit/, guides/governance-*, adr/, architecture L1) — fields: {owner, review_cadence, review_trigger, supersedes, superseded_by}. Date-based grandfather: pre-2026-04-25 files WARN; newer FAIL. Closes meta-doc rot identified by Future-Proofing Skeptic in Phase A roundtable.

[TRADEOFF] Kept `guard_context_write.py` name vs renaming to `guard_write_any` — preserves muscle memory at the cost of slight name/scope mismatch. Pragmatist roundtable rejected the rename; downstream forks unaffected.

[TRADEOFF] Per-target receipt directory (`.guard_receipts/<sha[:16]>.json`) vs append-only JSONL — chose directory for O(1) latest-receipt lookup at the cost of inode-pressure risk at very high volume (bounded ~30-50 governance targets).

[TRADEOFF] Append-write serialization via per-target sidecar lock vs naive `O_APPEND` — Windows O_APPEND insufficient under thread concurrency, so we serialize via process-local `threading.Lock` + cross-process file lock. Cost: ~2 ms per append; benefit: cross-platform correctness.

[CONSTRAINT] Stdlib-only Python implementation. No new dependencies; YAML parsed via existing `_yaml_loader.load_data`; Windows liveness via `ctypes.windll.kernel32.OpenProcess`.

[CONSTRAINT] Backward compatibility for one full release via `guard_policy.legacy_receipt_mirror: true` (Phase 1 dual-write). Phase 2 callsite migration is post-ship; Phase 3 removes legacy mirror after one release runway.

[CONSTRAINT] `lock_group()` reserved API — single-path implementation in this ADR; multi-path `NotImplementedError` placeholder for ADR-003 D3 reverse-transition multi-file atomicity needs. Prevents future ADR from reinventing the lock primitive.

[CONSTRAINT] Capability-by-presence enforcement. Python checks (`lint_governed_writes.py`, `check_lifecycle_frontmatter.py`) gated by `run_python_check` in validate.sh — downstream projects without Python installed degrade to SKIP/WARN, never blocking CI.

### [document-governance][2026-05-29][feat/audit-chain-tamper-evidence]
source_spec: docs/specs/audit-chain-tamper-evidence.md
source_sha: 9c035887c83dad2e8095c1b2ae8cb49828642960

[DECISION] C1 tail-truncation detection uses git `origin/main` (merge-base) as an EXTERNAL append-only witness in validate.sh/.ps1, chosen over a forgeable in-repo anchor file — a same-commit-forgeable anchor is false-confidence theatre per the [enforcement][HIGH] Global Lesson.

[DECISION] C2 `migrate` fails closed (exit 2, no writes) on an existing-but-mismatched prev_sha, only filling genuinely-missing fields — removing the "run migrate to launder forged history" attack and aligning with ADR-003's documented migration intent.

[TRADEOFF] The git witness is tamper-EVIDENCE, not prevention: an attacker can still truncate + commit, but the removal of published audit lines becomes a visible diff against the merge-base baseline that must survive PR review. Accepted as the strongest dependency-free guarantee absent an external transparency log.

[CONSTRAINT] Future INDEX rotation (backlog #3) MUST re-anchor the witness baseline as a deliberate reviewed operation; until then origin/main's merge-base is a valid monotonic lower bound and the strict-prefix invariant holds.

[CONSTRAINT] The witness MUST degrade to WARN (never silent PASS) when git/origin/baseline is unavailable; and MUST CR-normalize + drop blank lines identically in bash (`tr -d '\r'` + `grep '.'`) and PowerShell (string-array read + `-ne ''`) so the two validators cannot disagree (Windows CRLF parity).

### [document-governance][2026-06-03][arch-downstream-fork-accommodation]
source_spec: docs/specs/downstream-fork-accommodation.md
source_sha: (ship commit on arch/downstream-fork-accommodation)

[DECISION] Activate the already-shipped-but-inert `AGENTS.override.md` layer (lazy, present-only via bootstrap §1a) rather than invent a new `AGENTS.local.md` eager-`@import` twin — avoids one-topic-two-files and warm-cache prefix bloat. The "no consumer" basis that justified parking it in quick-win #34 flipped once downstream users began arriving. (ADR-004)

[DECISION] Reclassify skills (`.agent/skills/**`, `.agents/skills/**`) to the deploy sidecar class while keeping rules/workflows/validate/deploy/platform/tools/metadata force-update — skills are advisory (non-gate), so a frozen skill is a visible, low-cost loss; a frozen workflow/rule is invisible governance drift. (ADR-005)

[TRADEOFF] Narrowed the user's literal "sidecar all core" to "skills only" — accepts that editing a framework skill freezes it (visible via `.acx-incoming`) in exchange for guaranteeing governance/security files always update. Worse-than-R1 invisible drift is the avoided failure. (ADR-005, user-confirmed)

[CONSTRAINT] Override carve-out (no gate relaxation) and citation requirement are warn-only advisory, not hard-block — a pure-text override cannot be machine-proven to relax vs legitimately narrow a gate; only the machine-verifiable deploy behaviors become hard-tested. Enforcement of the override-load step is structural (validate.sh/ps1 assert bootstrap ships §1a); per-agent compliance is honor-system, stated honestly (no fake MUST). (ADR-004, Lesson [enforcement])

[CONSTRAINT] The framework MUST NEVER ship a skill under the reserved `custom-*` prefix — a downstream namespace contract, regression-guarded by `tests/ci/test_deploy_tiering.py::test_framework_ships_no_custom_namespace_skill`. (ADR-005)

### [document-governance][2026-06-04][codex/issue-156-spec-drift-linter]
source_spec: docs/specs/spec-drift-linter.md
source_sha: c76812d6b1a71ee7e857543789ca88ab7934d2d0

[DECISION] Keep the linter advisory so it can surface likely scope drift without creating a brittle hard gate around prose parsing.

[DECISION] Extract only path-like references from Acceptance Criteria because that is deterministic and easy to test across platforms.

[CONSTRAINT] `/review` integration must describe the linter as non-blocking and must not change review verdict rules.

### [document-governance][2026-06-04][codex/multi-agent-review-guidelines]
source_spec: docs/specs/multi-agent-review-guidelines.md
source_sha: fe0f306ef529c5b30b099b5e1b7a8bac8b561f15

[DECISION] Keep `AGENTS.md` as the short cross-agent source of truth and keep tool-specific files as adapters rather than duplicated governance manuals.

[DECISION] Use `.github/copilot-instructions.md` for Copilot's always-on short entry point because Copilot code review has a documented custom-instruction length boundary.

[CONSTRAINT] Do not add new durable governance claims unless a guard test or validator verifies the structural presence or size constraint.

### [document-governance][2026-07-01][codex/governance-premortem-audit]
source_review: docs/reviews/2026-06-16-audit.md
source_review: docs/reviews/2026-07-01-governance-premortem-round2.md
source_sha: 59e4a34a0b10dae7c2018b880b3a5fea01d003a4

[DECISION] Review snapshot `routing_actions` are not closed merely by being visible. Old `status: pending` actions must transition to `merged` or `rejected` after their target canonical doc absorbs or rejects the finding; validator staleness warnings are an alarm, not the final remediation.

[DECISION] Optional audit-created Work Logs are support traces. If an `/audit` session creates one, it may record support-phase evidence for traceability, but that receipt must not imply normal state-machine advancement for `/plan`, `/implement`, `/review`, `/test`, `/handoff`, or `/ship`.

[DECISION] Same-day repeated audit/review snapshots should use scope-qualified filenames such as `docs/reviews/<date>-<scope>-audit.md` or `docs/reviews/<date>-<scope>-premortem.md`, so a second audit does not overwrite or blur the first temporal record.

[CONSTRAINT] Blast-radius evidence must preserve target-relative path context. Dry-run, deploy, or migration previews that collapse paths to basenames are insufficient for governance review when multiple files can share the same leaf name.


### [document-governance][2026-07-04][feat/local-model-delegation]
source_spec: docs/specs/local-model-delegation.md
source_sha: 6095c9c

- [DECISION] The local model joins as a delegated junior EXECUTOR (inside
  `/implement` + advisory `review`), never as a primary agent — the primary
  keeps all phases, gates, and the Work Log. Delegating governance to the
  weakest model in the room would invert the safety model; delegating labor to
  it is exactly what the machine-enforced gates are for.
- [DECISION] The driver is the adopter's own OpenAI-compatible endpoint spoken
  to directly (curl-shaped calls by the primary), not a shipped CLI or runtime —
  Ollama/LM Studio/vLLM/llama.cpp all expose this surface, and shipping no code
  keeps the module zero-cost-when-absent and the framework engine-free.
- [DECISION] Patch contract with primary-applies: the local model returns a
  diff; the primary reviews and applies it with its own edit tools. This
  preserves Write Isolation and the Destructive Command Gate structurally, and
  sidesteps the high patch-application failure rate of small models.
- [DECISION] `§8.2 External Tool Delegation Protocol` is reused UNCHANGED and
  the module introduces zero new MUST/gate rules — the protocol was already
  tool-agnostic; the wiring (not the prose) is the machine-enforced part
  (signal_tier T1 via `check_command_sync.py` + the deploy-manifest golden).
- [DECISION] `codex --oss` is documented as a variant inside `codex-cli.md`
  rather than a fourth module — adopters already running Codex CLI get local
  implementation with zero new wiring, and the cap table is shared.
- [TRADEOFF] Local inference is free, so the §8.2 cost-tier auto-executes
  without a confirmation pause; the quality risk this admits is absorbed by the
  mandatory Junior Tool review plus the normal review/test gates — the weaker
  the implementer, the more the gates matter, which is the framework's thesis.
- [CONSTRAINT] Delegation cap: architecture-change is never delegated to a
  local model; hotfix allows `review` mode only; feature work is delegated only
  as scoped sub-tasks under a plan the primary owns (mirrors and tightens the
  pre-existing `codex-cli.md` approval table).
- [CONSTRAINT] Local model output is UNTRUSTED DATA (AGENTS.md §Untrusted Tool
  Output): embedded directives in generated code, comments, or prose are never
  authorization; any shell mutation it proposes re-enters the Destructive
  Command Gate at the primary.

### [document-governance][2026-07-11][chore/audit-wave-wrapup-20260711]

Source: 2026-07-11 codex governance self-audits (PRs #337/#338, 3 review
snapshots, 10 findings) → same-day remediation PRs #339/#340/#341. Every
finding was primary-verified against the actual code path before delegation
(0 false alarms; F10 was broader than reported).

- [DECISION] Adapter dispatch integrity is directive-anchored, not
  substring-anchored: `check_command_sync.py` parses each stub's single
  canonical "Execute the canonical workflow:" directive line and requires that
  line's target to match — a prose mention elsewhere no longer satisfies the
  check (PR #340).
- [DECISION] Adapter validation is surface-keyed, not manifest-keyed: the
  command-sync check runs whenever `.claude/commands/` exists, so deleting
  `.agentcortex-manifest` can no longer disable adapter-drift detection by
  flipping repository identity to "source" (PR #340).
- [DECISION] routing_actions structural validation is a Python tool
  (`check_routing_actions.py`, ADR-006 seam) parsing only the canonical
  column-0 fenced block; the legacy native grep/sed block remains solely as
  the no-Python degraded backstop. Indented in-prose example blocks are
  deliberately out of scope — audit reports may quote malformed fixtures as
  evidence (PR #340).
- [DECISION] External write-capable executor contract (§8.2 is canon):
  `Requested Executor` recorded before probing; worktree baseline captured
  before invocation; abnormal exit (timeout/nonzero/kill) stops retries and
  requires baseline-relative reconciliation before re-invocation; a path dirty
  at baseline is never whole-file reverted; explicit executor requests must
  disclose fallback, implicit acceleration may stay silent (PR #339).
- [DECISION] Work Log current-branch detection implements bootstrap.md's full
  5-step canonical key normalization in BOTH validators with case-insensitive
  comparison — uppercase/punctuated branches can no longer demote
  current-branch FAIL escalations to WARN (PR #341).
- [DECISION] Receipt/anchor value validation extends the existing WARN-tier
  checks: Timestamp must contain a parseable ISO date (order-of-appearance
  stays authoritative — monotonic ordering deliberately NOT enforced), receipt
  Classification must match the header classification, and Checkpoint/Diff
  Base SHAs must be hex-or-known-placeholder with `git rev-parse`
  resolvability required on the current-branch log only (PR #341).
- [CONSTRAINT] `check_routing_actions.py` is deliberately NOT in the deploy
  runtime_tools whitelist yet — downstream keeps the native backstop;
  promotion is a tracked follow-up (backlog #137), not an accident.

### [document-governance][2026-07-16][chore/orphan-decision-homes]

Source: 2026-07-16 decision-capture govern-audit
(docs/reviews/2026-07-16-govern-audit-decision-capture.md, F2). Three product
decisions had landed only on rotating/temporal surfaces — the SSoT Ship
History (cap-10), a rejected-ADR gap, and archived work logs / oral tradition
— with no durable home, so a later session could re-derive or re-propose them.
This entry, plus the ADR-001 Amendment (2026-07-16), gives them one.

- [DECISION] `design_tool` capability-seam gate escape — the 2026-07-08
  roundtable UNANIMOUSLY rejected it; DO NOT retry this seam. Canonical record is the
  ADR-001 Amendment (2026-07-16); full rejection log at
  docs/reviews/2026-07-08-design-gate-roundtable.md. No content is duplicated
  here — the ADR amendment governs.
- [DECISION] SSoT section caps (PR #328, 2026-07-10): config
  `ship_history_max_entries: 10` mechanizes ship.md's pre-existing documented
  cap (ship.md:208 — "keep only the latest 10"); it is enforced WARN-tier-only
  via `check_ssot_caps.py` (advisory, never a hard FAIL — a size cap must not
  red-X a downstream fork's CI; rationale reconstructed 2026-07-16 from the
  framework's WARN-tier degradation pattern — the 2026-07-10 config comment
  records only the *what*). It landed a one-time 67→10 Ship
  History rotation into archive/ship-history-2026.md and gave the previously
  consumer-less `spec_index_max_entries: 30` cap its first validator consumer.
- [DECISION] NOT-READY re-review remediation hint (PR #328): a message-only
  hint was added to both validators' gate parser while the illegal `plan→review`
  FAIL verdict was deliberately preserved — the hint educates, the gate keeps
  its teeth (the config comment carries the *what*; this records the *why*).
- [DECISION] Point-in-time archival precedent (documented instance:
  archive/ship-history-2026.md — PR #315, 2026-07-02,
  Ship-chore-archive-stale-worklogs; the practice predates that PR): incomplete Work Logs (e.g. no ship
  receipt) are archived AS-IS — kept verbatim, not edited; receipts are never
  fabricated retroactively; and historical gate gaps stay visible as validator
  WARNs rather than laundered. Reapplied repeatedly since — each archival
  records an INDEX.jsonl chain entry (e.g. the 2026-07-11 wave, "as-is per
  point-in-time precedent").

### [document-governance][2026-07-16][feat/decision-capture-hardening]
source_spec: docs/specs/decision-capture-hardening.md
source_sha: (ship commit on feat/decision-capture-hardening — squash-merged via PR)

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
