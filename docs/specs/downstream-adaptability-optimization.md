---
status: shipped
title: Downstream Adaptability Optimization
source: internal
classification: architecture-change
primary_domain: downstream-adaptability
secondary_domains: [safety-governance, deploy, skills]
adr: [ADR-007, ADR-008]
created: 2026-06-14
---

# Spec: Downstream Adaptability Optimization (Capability Seam + Portable Safety Floor)

Make the framework adapt to heterogeneous downstream usage — many custom skills,
harness/subagent fan-out, and other work-management flows — via (1) a present-only,
opt-in, gate-capped capability declaration seam (ADR-007) and (2) a portable,
inheritable safety floor with a no-python credential control (ADR-008).

**North star: AI self-adherence.** The success metric is that agents — the primary
AND harness-dispatched subagents — autonomously comply with governance across these
scenarios. **Every change is additive + present-only** (an absent file → byte-for-byte
unchanged behavior), nothing relaxes a gate, and nothing breaks the existing
bootstrap→plan→implement→review→test→handoff→ship flow.

## 1. Goal

A downstream project can, without editing framework-owned files and without relaxing
any gate: register its `custom-*` skills into auto-activation; declare a subagent
policy; declare an external tracker (advisory) — all opt-in and present-only. And any
harness (not just Claude `acx-*` shims) can inherit the three always-loaded safety
invariants plus a Python-independent secrets pre-screen. The existing governance flow,
the single-writer lock, the deploy tiers, and the validators behave identically when
none of the new files are present.

## 2. Acceptance Criteria

> Signal tiers: **T0** honest-advisory (honor-system; no machine proof of agent
> behavior) · **T1** validator/hook/test (machine-verified structure or correctness) ·
> **T2** eval-backed (`governance.yaml` adversarial case). Every AC names the failure
> mode it guards.

### Group A — Downstream Capability Declaration Seam (ADR-007)

- **AC-D1 (loader ships, structural)** — `bootstrap.md` gains a `§1b "Load Downstream
  Capabilities"` step (imperative phrasing), a present-only twin of `§1a` (override)
  and `§3.6a` (user-prefs). `validate.sh` + `validate.ps1` assert it via
  `check_contains_literal`/`Test-ContainsLiteral` on the literal `'Load Downstream
  Capabilities'` (mirror the override check at validate.sh:528 / validate.ps1:673).
  **T1.** *Guards: a source-regen silently dropping the loader → dead seam.*
- **AC-D2 (present-only, absent→zero cost)** — When `.agentcortex/context/private/
  downstream-capabilities.yaml` is absent, `§1b` does zero reads, zero tokens, no
  error; Work Log `## Session Info` records `Downstream-Capabilities: none`. **T0**
  (per-agent honoring) / inherent (private/ tree never read when absent). *Guards:
  eager-load warm-cache bloat / behavior change when absent.*
- **AC-D3 (custom-* union into §3.6a step-3)** — A declared `skills[].id` is unioned
  into the bootstrap §3.6a step-3 validation set so a `custom-*` id resolves instead of
  "unknown → ignore" (bootstrap.md:398). Non-`custom-*` ids in `skills:` are **rejected**,
  not unioned. **T1** (the custom-*-only + cap constraints via AC-D6); **T0** (agent
  actually activates). *Guards: ADR-007's headline (custom skills auto-activatable) being a no-op.*
- **AC-D4 (cap in real schema vocabulary)** — A declared skill's `load_policy` is capped
  at ceiling `on-match` and clamped to its declared `phase_scope`. There is **no
  `trigger_priority`/`contextual` field** (it does not exist in `trigger-compact-index.json`);
  gate-relaxation is unrepresentable. A file declaring a higher policy / `block_if_missed`
  / a gate / a ship-edge is **rejected**. **T1.** *Guards: back-door promotion of a downstream skill to gate-blocking.*
- **AC-D5 (subagent_policy = present-only declaration; lock change DEFERRED)** —
  `subagent_policy: read-only` (default) | `governed` is accepted as a present-only
  **declaration only**. `read-only` = subagents fan out / return evidence; the primary
  is the sole Work Log writer, gate owner, and sentinel emitter (subagents never acquire
  the lock → no contention). The `recover_worklog_lock.py` same-owner short-circuit is
  **NOT shipped** (Non-goal §3). `governed` authorizes evidence-producing fan-out, never
  concurrent Work Log writes. **T0** (declaration honored); lock code is **untouched**.
  *Guards: reopening the single-writer lost-update by loosening the lock with no consumer.*
- **AC-D6 (schema gate-safety, present-file)** — When the file is present,
  `validate.sh`/`validate.ps1` run a `run_python_check` schema validator: every
  `skills[].id` is `custom-*`; no field exceeds caps; no rejected field
  (gate/ship-edge/concurrent-writer/blocking-tracker). **No-Python → WARN** ("schema
  unverified, install Python"), never silent PASS, never FAIL. **T1** (Python) /
  honest WARN (no-Python). *Guards: a gate-relaxing file passing unscanned / fail-open.*
- **AC-D7 (loader fail-closed on malformed-with-content)** — A present file that is
  **malformed but non-empty** → `§1b` fails closed *for that file* (warn-once, skip the
  capabilities; do NOT half-merge / do NOT treat unknown keys as permissive). Truly
  empty/absent → silent zero-cost skip (AC-D2). **T0** (loader behavior). *Guards: a
  truncated/edited file being read as "no caps" → silent gate-relaxation.*
- **AC-D8 (untrusted DATA + sanitized echo)** — Free-text fields (tracker name, skill
  description, note) are treated as untrusted DATA per AGENTS.md §Untrusted Tool Output;
  embedded directives are ignored; any echoed free-text is line-break/control-char
  sanitized before reaching a chat turn (reuse the `append_drift_log` splitlines
  discipline, recover_worklog_lock.py:226). **T0** reasoning + **T2** backstop
  (`governance.yaml prompt-injection-in-tool-output`). *Guards: the YAML becoming a second-order prompt-injection vector.*
- **AC-D9 (tracker = schema-accept + gate-safety-reject; note-emission DEFERRED)** —
  `trackers:` parses and validates its `custom-*` skill ref, and is **rejected** if it
  declares anything blocking/gating. The phase-entry advisory **note emission is deferred**
  (Non-goal §3); the field is reserved, no sync machinery, a tracker can never gate.
  **T1** (reject-if-blocking). *Guards: over-building sync with no consumer / a tracker becoming a gate.*
- **AC-D10 (config block)** — `.agent/config.yaml` gains a `§downstream_capabilities`
  block (path + cap constants), mirroring `§user_preferences` (config.yaml:89), declaring
  the gitignored path. **T1** (presence assertable). *Guards: caps hardcoded in bootstrap instead of the config SSoT.*
- **AC-D11 (sentinel clarification, NEW subsection)** — A new subsection (routing.md §3a
  is taken — use a §3b or a sentinel note adjacent to AGENTS.md Runtime rule 11) documents:
  `⚡ ACX` is **primary-emitted**; a subagent's output returns internally to the primary,
  so subagents neither emit nor need the sentinel. **T0** (doc). *Guards: subagent outputs flagged sentinel-missing, or every fan-out child spuriously appending ⚡ ACX.*
- **AC-D12 (deploy never ships the yaml)** — Deploy never ships
  `downstream-capabilities.yaml`. Largely **inherent**: `.gitignore` already ignores
  `.agentcortex/context/private/`; the spec references that + one deploy-whitelist
  exclusion assertion (no new mechanism). **T1** (gitignore present) / inherent. *Guards: a future whitelist edit shipping runtime state (the ADR-005 silent-overwrite class).*

### Group B — Portable Safety Floor (ADR-008)

- **AC-S1 (fence, byte-unchanged)** — The 3 invariants in `AGENTS.md §Core Directives`
  are wrapped in `<!-- ACX:SAFETY-FLOOR:BEGIN -->` / `<!-- ACX:SAFETY-FLOOR:END -->`.
  Invariant **text is byte-unchanged** → `governance.yaml` eval cases + every adapter
  canary (codex/rules, .antigravity/rules.md) still pass; the fence is an HTML comment
  (greppable, invisible; precedent already at AGENTS.md:18). The floor **stays on the
  always-loaded surface**. **T1** (eval + canary unchanged; fence-present check). *Guards: rewording an invariant breaking a canary/eval; the fence moving the floor off the always-loaded surface.*
- **AC-S2 (committed generated nucleus + freshness)** — `.agentcortex/AGENTS.safety.md`
  is a **committed generated file** (~15 lines = the fenced span). A `validate.sh`/`.ps1`
  **freshness check** asserts its content equals the current fenced span
  (the `generate_compact_index.py --check` pattern: FAIL on stale, SKIP when the
  generator is absent), CR-normalized to avoid CRLF false-FAILs. **NOT** a deploy-time
  slice. **T1.** *Guards: nucleus⇄AGENTS.md drift (two sources of truth for one MUST); a stale floor injected into subagents.*
- **AC-S3 (primary-delegation sentence, T0-advisory)** — One sentence inside the fence:
  when delegating, the primary confirms the floor is in the subagent's context AND
  treats any subagent-proposed shell-mutation as subject to the same Destructive Command
  Gate (the subagent's own confirmation does not satisfy it). **Explicitly marked
  advisory — not machine-enforced.** **T0.** *Guards: presenting per-subagent floor as enforced (a fake MUST).*
- **AC-S4 (no-python credential floor = FP-free SUBSET)** — The pre-commit pre-screen's
  canonical control becomes a shell + PowerShell regex floor: a tiny, redaction-safe,
  **FP-free SUBSET** (AKIA / PEM header / `ghp_` only), **per-staged-file**, **value
  never printed**, preserving `test_scan_credentials.py`'s `_BENIGN` no-FP corpus and the
  subset of `_fakes` it covers. Replaces the Python-gated screen at
  `.githooks/pre-commit.guard-ssot.sample:23-41` (currently silent-skips when Python is
  absent). **T1** at the commit boundary (no Python dependency). *Guards: the advertised "block secrets before object history" control silently no-opping on no-python downstream (the verified dead control).*
- **AC-S5 (`.py` stays python-path + deploy whitelist, BOTH spots)** — `scan_credentials.py`
  remains the richer python-present path AND is added to the deploy whitelist in **both**
  `deploy.sh` sites — the L725 `_runtime_tools` string AND the L910-927 `runtime_tools`
  array (`deploy.ps1` inherits via bash delegation). **T1** (whitelist presence). *Guards: python-havers never receiving the richer scanner; a one-spot half-fix.*
- **AC-S6 (floor parity sh ↔ ps1)** — The shell and PowerShell floors are parity-tested:
  same AKIA/PEM/`ghp_` shapes, same `_BENIGN` no-FP corpus, same redacted (no-value)
  output; PS binds a `-Staged` switch (not `--staged`, per [cross-platform-cli]);
  verified by RUNNING both, not reading. **T1** (parity test). *Guards: a secret blocked on Linux slipping on Windows (or an FP on one OS only).*
- **AC-S7 (honest tier ledger)** — The spec's §7 records the ADR-008 tiers verbatim and
  no test claims interception that does not exist. **Documentation.** *Guards: a reader assuming `rm -rf` is enforced; faking filesystem interception as T1.*

### Group C — Cross-Cutting

- **AC-X1 (cross-platform parity, mandatory)** — Every machine change lands in **both**
  `validate.sh`+`validate.ps1` and is verified by RUNNING each entry point, not reading
  ([cross-platform-cli]). **T1.** *Guards: Claude-centric drift; a check that exists only in `.sh`.*
- **AC-X2 (compact-index regen if a registry detail_ref changes)** — If the §1b/§3.6a
  edits change a registry `detail_ref` doc (bootstrap.md/routing.md), regenerate
  `trigger-compact-index.json` in the same change (validate.sh:346 already FAILs on
  stale). If the custom-* set is read from the present file at runtime (not baked into
  the index), record that regen is unnecessary — a deliberate non-action. **T1** (existing freshness check). *Guards: a stale index validating against an outdated id set.*
- **AC-X3 (§13 Deletion-First / ADD-Gate)** — Each net always-loaded AGENTS.md add cites
  its §13 justification: ADR-008 ≈ 2 comment lines + 1 delegation sentence (data-loss
  incident); ADR-007 adds **no** always-loaded AGENTS.md text (loader is in bootstrap.md).
  Every new MUST carries a declared tier (§7). **T1** (signal_tier WARN) / **T0** (deletion citation). *Guards: unbacked MUST as theatre; always-loaded growth without justification.*
- **AC-X4 (Windows EOL discipline)** — Any validator content-compare (notably AC-S2
  freshness) CR-normalizes both sides; any tracked-file write uses the Edit tool / LF-safe
  append, never `cat >>` into a CRLF checkout ([cross-platform-eol]). **T1.** *Guards: a CRLF-vs-LF mismatch making AC-S2 perpetually FAIL on Windows.*
- **AC-X5 (update delivery + no-overwrite, tier-correct)** — The change reaches downstream
  via correct ADR-005 tiers (verified `deploy.sh get_tier` L106-161, force-update L225-251):
  `bootstrap.md` (§1b), `routing.md`, `.agent/config.yaml`, `validate.*`, `scan_credentials.py`,
  and the new **`.agentcortex/AGENTS.safety.md`** are **core/force-update** — they reach ALL
  downstream on update; a downstream's local edit to a core file is force-updated but **backed
  up to `<file>.acx-local`**, never silently lost. `AGENTS.md` (the fence) is **scaffold** — a
  downstream's AGENTS.md is NOT overwritten; the safety floor still reaches them via the shipped
  core `AGENTS.safety.md`. `downstream-capabilities.yaml`, `custom-*` skills, and
  `AGENTS.override.md` live in **never-shipped/sidecar** locations → downstream customizations
  there are **never overwritten** (the sanctioned no-overwrite outlet). **Fork users who only
  add `custom-*`/capabilities get conflict-free `git pull`**; passive (no-edit) forkers
  fast-forward cleanly. **The no-python credential floor MUST reach existing-hook early
  adopters**: floor logic in a **core-tier script** that the scaffold `.sample` calls + a deploy
  re-activation nudge (the `.sample` is scaffold/created-once, so an already-installed hook is
  not auto-updated). **T1** (deploy-tier tests assert each file's tier + the `.acx-local` backup
  on a modified core file). *Guards: a governance/safety fix not reaching early adopters, or silently overwriting their edits.*

## 3. Non-goals

- **NOT** shipping the `recover_worklog_lock.py` same-owner short-circuit (loosening the
  single-writer lock has no verified parallel-shim consumer and would reopen lost-update;
  the `read-only` declaration makes contention moot without touching the lock). Deferred
  until a real `governed` parallel-mutation consumer **and** a write-side ownership check.
- **NOT** building tracker sync machinery or the phase-entry note emission (reserve the
  schema slot + gate-safety reject only; the note is the thin end of sync + an injection vector; no consumer).
- **NOT** the general "framework validators degrade to WARN (not FAIL) on
  downstream-authored content" principle (problem #6) — its own ADR/spec, sequenced next.
- **NOT** a full shell/PS reimplementation of `scan_credentials.py` (the narrow subset is
  deliberate; bash ERE lacks `\b`, `grep -P`/PCRE is absent on macOS/BSD/Alpine; full
  detection stays the Python path + CI TruffleHog).
- **NOT** runtime `rm -rf` / filesystem interception (no framework-side hook can; T0
  advisory; an opt-in operator-owned harness wrapper is the only lever — out of scope here).
- **NOT** custom-skill auto-discovery without an explicit declaration entry
  (auto-activating unvetted skill descriptions is an untrusted-activation surface).
- **NOT** multi-writer Work Log / concurrent governed mutation.

## 4. Constraints

- Cross-platform parity mandatory: `validate.sh`↔`validate.ps1`; `deploy.sh` carries the
  one bash implementation (`deploy.ps1`/`deploy_brain.ps1` are pure launchers — no PS twin).
- Every new MUST has a validator/test/hook or is honestly labeled advisory ([enforcement]).
- New validator checks use `check_contains_literal`/`Test-ContainsLiteral`, **never** a
  line-leading native `record_result`/`Add-Result` — else the ADR-006 native-baseline
  ratchet (192/193) hard-FAILs.
- AGENTS.md invariant **text** stays byte-identical inside the fence (eval + canary safety).
- Loaders are lazy/present-only — no eager `@import` (token governance).
- `§1b` and the primary-delegation sentence are written as **imperative directives**
  (self-adherence; a passive mention measurably lowers adherence, per [claude-startup-imperative]).
- Windows EOL discipline for any content-compare / shell append ([cross-platform-eol]).
- The no-python credential floor stays a narrow FP-free subset (a blocking hook that
  false-positives gets `--no-verify`'d into uselessness — adherence erosion).

## 5. File Relationship

**INDEPENDENT** — new spec. Sibling to the **Shipped** `downstream-fork-accommodation.md`
(ADR-004/005, preservation seams); this spec covers ADR-007/008 (the *integration* +
*safety-inheritance* seams). It does **not** modify that frozen spec.

## Domain Decisions

- [DECISION] Reuse the `§1a`/`§3.6a` present-only loader pattern + the `§user_preferences`
  config mirror for `§1b`/`§downstream_capabilities` — absent ⇒ zero tokens; not a new
  eager `@import`. (ADR-007)
- [DECISION] Ship the `subagent_policy` **declaration** now but **defer** the
  `recover_worklog_lock.py` same-owner short-circuit — a single-writer-safety code change
  with no verified in-repo parallel-shim consumer waits for evidence; the declaration is
  free, the code mutation is not. (ADR-007; red-team correction A)
- [DECISION] The no-python credential floor is the **canonical** control (shell+PS regex
  subset); `scan_credentials.py` is the richer python-present enrichment — honors the
  no-python doctrine and does what CI structurally cannot: block *before* object history. (ADR-008)
- [CONSTRAINT] Gate-relaxation is **UNREPRESENTABLE by schema** — over-cap `load_policy`,
  gate declarations, ship-edges, concurrent-writer authorization, and blocking trackers
  are validator-**rejected**, not merely discouraged. (ADR-007)
- [CONSTRAINT] The shell/PS floor is a deliberate **FP-free SUBSET** (AKIA/PEM/`ghp_`,
  value never printed) preserving the `_BENIGN` no-FP corpus; TruffleHog CI is the
  post-commit entropy backstop. Narrow > recall (a false-positiving block-hook gets disabled). (ADR-008)
- [TRADEOFF] `AGENTS.safety.md` is a **committed generated** file with a content-equality
  freshness check, not a deploy-time slice — accepts one committed artifact for a
  machine-verifiable single-source guarantee (AGENTS.md is scaffold-tier, so a slice would
  drift against a sidecar'd downstream AGENTS.md). (ADR-008)
- [DECISION] Update delivery rides the existing ADR-005 tiers: governance/safety
  (bootstrap §1b, validators, `scan_credentials.py`, the `AGENTS.safety.md` nucleus) ship
  **core/force-update** so fixes always land (a downstream's local core edit is preserved as
  `<file>.acx-local`); downstream customizations live in **never-overwritten** extension
  points (`custom-*`, `AGENTS.override.md`, `downstream-capabilities.yaml`) — the outlet that
  lets early adopters update smoothly without losing changes. The `.githooks/*.sample`
  credential floor reaches existing-hook users via a core-tier floor script + a re-activation
  nudge (the `.sample` is scaffold/created-once). This serves the dominant fork-without-edits
  user (clean fast-forward) and the early-adopter-with-edits user (no-overwrite via extension
  points / `.acx-local` backup). (ADR-005 + ADR-008)

## 7. Enforcement Boundary (honest signal tiers — kept, labeled, not faked)

These cover real risks but cannot be machine-proven at the agent-behavior layer.
Completeness = covered; polish = labeled T0, never dressed as T1:

1. **Per-agent honoring** of the §1b declaration + loader caps (AC-D2/D5/D7) — the
   validator proves the schema is gate-safe + the step ships (T1); it cannot prove the
   agent merged/clamped the declaration. Same boundary as the ADR-004 override read.
2. **Untrusted-DATA reasoning** (AC-D8) — T0 reasoning + T2 eval backstop.
3. **Sentinel clarification** (AC-D11) — pure doc, T0.
4. **Primary re-confirms subagent shell-mutation / floor injection** (AC-S3) — honor-system
   at the harness boundary; the validator proves only the fence + nucleus ship.
5. **`rm -rf` filesystem interception** (AC-S7) — **permanently T0**; no framework hook
   can intercept a runtime `rm`; only an opt-in operator wrapper. The 2026-06-11 incident's
   specific failure stays advisory.
6. **A harness that injects neither AGENTS.md nor the nucleus** — unreachable by any
   instruction (operator-wrapper territory); documented as an honest dead-zone.

## 8. Test Plan (seeds)

- `tests/guard/test_downstream_capabilities.py` — AC-D2 (absent→zero), AC-D7 (malformed→fail-closed), AC-D3/D4 (custom-* registers + caps; non-custom rejected).
- `tests/guard/test_capabilities_schema_gate_safety.py` — AC-D6 (malicious file: `load_policy` over-cap / gate / ship-edge / blocking-tracker → validator exit≠0 + names the field; **mutation**: change reject→clamp must fail the test).
- `tests/ci/test_deploy_tiering.py` (extend) — AC-D1/D10 validator literals (both platforms), AC-D12 (yaml never in deploy set), AC-S2 (AGENTS.safety.md committed + freshness), AC-S5 (scan_credentials.py in both whitelist spots).
- `tests/guard/test_worklog_lock_blocking.py` — AC-D5 regression: lock code UNCHANGED, all existing cases pass identically (no same-owner path added).
- `tests/guard/test_credential_floor_shell.py` + `test_credential_floor_ps.py` — AC-S4/S6: both floors catch AKIA/PEM/`ghp_`, 0 FPs on `_BENIGN`, redacted output, run with Python OFF PATH; parity across sh/ps1.
- `governance.yaml` — AC-D8/AC-S7 reuse existing `prompt-injection-in-tool-output` + `destructive-command-no-rollback-pressure` cases (the rm-rf T0 proof).
- Validators `validate.sh`/`validate.ps1` — AC-D1/D6/S2 checks via `check_contains_literal` + `run_python_check` (no native `record_result`; no-python→WARN); run BOTH ([cross-platform-cli], never parallel-batched on Windows per [process-batching]).

> **/review gate (recorded)**: the design panels were same-vendor; the trust-boundary ACs
> (AC-S4 credential floor, AC-S2/S3 safety inheritance) MUST get a cross-vendor external
> check (/ask-openrouter or Codex) at /review, per [audit-method][HIGH].
