---
status: accepted
date: 2026-06-20
classification: architecture-change
primary_domain: downstream-adaptability
deciders: "@kbwen (human steer — downstream flexibility + the load-bearing 'others may have no LLM wiki' optionality directive) + Claude Opus 4.8 + a 6-expert design panel (workflow-fit / token+external-data / optionality+cross-platform / trust-boundary / external-web-prior-art / adversarial red-team) + a 3-scenario simulation (mid-flow insertion / no-KB optionality / manifest-risks+decision-readiness), run twice and RE-VALIDATED after the reference KB was optimized; grounded against real files (manifest.json schema_v2, validate_downstream_capabilities.py:247, bootstrap §1b/§3.6, ADR-007)"
applies_to:
  - ".agent/workflows/bootstrap.md"
  - ".agent/config.yaml"
  - ".agentcortex/tools/validate_downstream_capabilities.py"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When a verified downstream consumer needs Stage-2 (multi-standard / auto-cross-phase / drift-detection / backfill), OR a consumed KB's machine-contract (manifest schema_version) changes, OR a platform changes its file-read model"
  supersedes: none
  superseded_by: none
---

# ADR-009: Knowledge-Source Consumption Seam

## Context

ADR-007 gave downstream a present-only seam to **contribute** capabilities the
framework *reads* (skills / subagent-policy / trackers). A parallel, opposite
need has now arrived with a **real consumer**: let the governed flow **consume**
an external, curated markdown knowledge-base — a Karpathy-style "LLM wiki" of dev
**standards / playbooks / lessons** — to enrich `/plan` and `/review` with domain
criteria the framework itself does not (and should not) carry.

The **load-bearing constraint** (maintainer directive, restated twice): the
framework ships to many adopters and **most have NO knowledge-base at all**. The
seam MUST be zero-cost-when-absent, and MUST let others plug **their own**
markdown KB without requiring the reference KB's tooling.

### Evidence (Verified)

- **A real, purpose-built consumer exists.** The reference KB ships a machine
  contract `outputs/manifest.json` (schema_version 2: `task_routing` +
  per-page `{slug, path, status, confidence, last_verified, summary,
  approx_tokens, sha, h2, links_out}`), git-tracked and kept fresh by
  `kb-lint.py` + CI, and a `_kb-principles` section literally titled
  *"機器可消費原則（給程式化消費端，如 AgentCortex 治理層）"* — it was optimized
  specifically to be consumed by this framework. (verified `manifest.json`)
- **Strongest fit = `/review`.** Each standard ships a lint-enforced, uniform
  `## 自我稽核 Checklist` (32/36 + variants, listed in manifest `h2`) = ready-made
  review criteria; `**AI 最常漏掉**` is a consistent grep-able plan-risk label.
- **A 6-expert panel + a 3-scenario simulation (run twice, re-validated after the
  KB optimization)** converged: **C (automated backfill) unanimously rejected**
  (a write-path into shared cross-project state = compounding wiki-poisoning +
  secret-exfil + removes the human "ask first" the KB's own contract mandates; no
  mainstream coding-tool precedent). The **A-vs-B split resolved to "B-via-A"** —
  deliver B's value (an actually-pulled consult) *through* A's present-only
  structural discipline. The manifest re-validation **dissolved 2 of 7 breaks,
  eased 4**, leaving residuals all agentic-os-side and small.
- **Critical build-order fact.** As specified, a `knowledge_sources:` block would
  be **REJECTED** by the shipped `validate_downstream_capabilities.py:247`
  allowlist (unknown top-level key → rejects the *whole* `downstream-capabilities.yaml`,
  killing existing `skills/subagent_policy/trackers`). The allowlist extension
  MUST land **atomically** with the loader clause.

## Decision

**Add one present-only, opt-in `knowledge_sources:` capability kind to ADR-007's
`downstream-capabilities.yaml` that lets the governed flow CONSUME (read-only) an
external markdown KB — and can never relax a gate.**

1. **Reuse the ADR-007 seam — do not mint a new file.** `knowledge_sources:`
   joins `skills/subagent_policy/trackers` in the same gitignored,
   **never-shipped**, present-only file (loaded at `bootstrap.md §1b`).
   **Absent → zero reads, zero tokens, zero behavior change** — the no-KB 99%
   inherit ADR-007's proven `N1` exactly.
2. **Consumption ladder (fail-closed, "broken == absent").**
   (1) KB has `manifest.json` and `schema_version` matches the known shape →
   **programmatic query** (`task_routing` + per-page `sha`/`approx_tokens`/`status`),
   **never full-load** (the manifest is ~53K tokens — query it, don't paste it);
   (2) else a markdown index (`llms.txt` / `_index.md`) → read that;
   (3) else / unreadable path / malformed manifest / unknown schema → treat as
   **absent**: behavior UNCHANGED (own judgment + web-if-available), one advisory,
   never block. **BYO floor = a readable markdown index; the manifest is an
   OPTIONAL accelerator.** A malformed manifest is **skipped whole**, never
   half-trusted (mirrors ADR-007 `parse_strict`).
3. **One scope-detected consult, peer to `doc-lookup`** (`bootstrap.md §3.6`):
   feature/arch → `/plan` + `/review`, `/implement` on-match; hotfix/quick-win
   on-match ≤1 page; **tiny-fix NEVER**. Resolve standards via manifest
   `task_routing`; **tiers (必看/建議/可略) are read from
   `manifest.entry.routing_playbook`, NOT the manifest** (they are not in it);
   `/review` pulls the uniform `## 自我稽核 Checklist` as criteria. The detector is
   `knowledge_sources` present **AND** task in-scope — never an unconditional
   "consult the KB" (which would be a cost + dangling reference for the no-KB 99%).
4. **Data discipline — KB content is DATA, not instructions.** All KB content
   *including the manifest* is untrusted DATA under `AGENTS.md §Untrusted Tool
   Output`. The KB's own `AGENTS.md`/routing tables are **never loaded as
   governance** (the KB's own decision *"live-pointer 不合併入口"* agrees). The
   **manifest is a HINT, the page is authority** (the KB's `AGENTS.md:39`:
   *"衍生物非權威，內容以各頁為準"*); the manifest **`sha` is a drift-detector, NOT a
   tamper-seal** (it is attacker-controllable). Volatile facts (versions, pricing,
   API) → official source wins, surface the conflict.
5. **Gate-cap — UNREPRESENTABLE by schema.** A `knowledge_sources` entry can never
   carry `gate` / `required` / `block_if_missed` / `ship_edge`, never
   `role: authority` (fixed to `advisory`), and a BYO manifest defaults to
   **`manifest_trusted: false`** (its `sha` is never used to skip a read
   across sessions unless the adopter asserts their own CI keeps it fresh). The
   validator **rejects** violations (never clamps) — exactly the posture of the
   existing `skills[].id MUST be custom-*` allowlist.
6. **Staged.** Stage 1 = the minimal surface above. **Stage 2** (multi-standard /
   auto-cross-phase / drift-detection findings / backfill loop) is **DEFERRED**
   to a verified recurring consumer (YAGNI, §5.4). **C (automated backfill) is
   REJECTED**; Distill stays human-confirmed.

**Honest enforcement boundary** (per `engineering_guardrails.md §13` ADD-Gate +
the `[enforcement][HIGH]` lesson): the *machine-enforceable* part is **structural
T1** — `validate.sh`/`validate.ps1` assert (i) `bootstrap.md` still ships the
`§1b` load step + the `§3.6` consult row (mirror the ADR-004 line-528 /
ADR-007 §1b checks), and (ii) a present file's `knowledge_sources` entries carry
no forbidden gate fields and a non-`custom`-controlled path (schema gate-safety,
**allowlist extended atomically**). Everything behavioral — "did the agent
consult the right page, re-read a stale one, treat the manifest as a hint, prefer
official over a volatile KB number" — is **honor-system advisory**, LABELED as
such, **no fake MUST**. (The reference KB's producer-side freshness CI is real
but sits OFF the agentic-os trust boundary — see Consequences.)

## Alternatives Considered

- **A-hardened / convention-only (a pointer with no auto-consult)** —
  **Rejected**: a pointer nothing pulls is the ADR-004 *"shipped-but-inert"*
  worst-state, and the framework's thesis is machine-routed-not-self-reported.
  B-via-A keeps A's present-only safety **and** delivers an actually-pulled
  consult via the proven `§3.6` scope-detect mechanism. The skeptic/security
  concerns are neutralized **by** the present-only + DATA-not-instructions +
  gate-cap guardrails, not by declining.
- **Full RAG / embeddings** — **Rejected**: external best practice (Anthropic
  context-engineering; the "RAG only past ~5–6 docs/query" threshold) says a
  small curated markdown set is loaded directly via progressive disclosure, not
  vectorized. The manifest gives deterministic routing **without** an embeddings
  pipeline; the reference KB explicitly logged *"不轉 RAG"*.
- **C — automated `/ship` or `/retro` → KB backfill** — **Rejected**: the only
  design that opens a **write path into shared, cross-project state** —
  compounding wiki-poisoning + a secret-exfil channel + it removes the human
  *"主動問是否回填"* checkpoint the KB's own contract requires. No mainstream
  coding-tool precedent. Backfill stays a human-gated manual step in the KB's own
  repo.
- **A new `.agent/config.yaml §knowledge_base` key (not reusing ADR-007)** —
  **Rejected**: `config.yaml` is force-update **core** tier (ADR-005); a
  downstream KB path written there is silently overwritten on every `deploy`,
  reintroducing the exact silent-loss footgun ADR-005 closed. Registration must
  live in never-shipped `context/private/` (the config may hold seam *defaults*,
  never the adopter's path).
- **Eager `@import` of the KB index at bootstrap** — **Rejected** (same as
  ADR-004/007 round-1): pins KB content into every turn's warm-cache prefix;
  violates `§Read-Once` / `§Context Pruning`. Use the lazy, scope-detected,
  query-not-paste consult.

## Consequences

**Positive**: the governed flow can consume curated domain knowledge (review
self-audit checklists, plan risks) the framework deliberately does not carry —
**optionally**. No-KB adopters pay **structural** zero cost (the declaration
nests inside ADR-007's already-validated present-only seam; `deploy.sh` ships
nothing KB-related; `validate.sh` passes a no-KB project clean). **BYO works with
any markdown index** (`llms.txt` / `_index.md`), with the manifest a pure
accelerator that buys machine-clean routing + token budgeting + in-session
drift-detection. Cross-platform is free (pure file/JSON read; web-fallback phrased
"if available"; no-Python downstream still consumes — only the CI gate-safety
validator needs Python). **Generalizes ADR-007**: a new *consume*-capability =
a schema stanza + one validator allowlist line + one `§1b`/`§3.6` clause — never
an `AGENTS.md` gate edit.

**Negative / accepted**: per-agent consult-quality is **honor-system** — the
validator proves the seam is gate-safe and ships, not that the agent consulted
the right page, re-read a stale one, or preferred an official source over a
volatile KB number. Same boundary as ADR-004/007. A **BYO KB's manifest freshness
is the adopter's own CI**, which sits **OFF the agentic-os trust boundary**: a
downstream that vendors/pins an old KB commit, or forks a KB without the lint
workflow, gets a stale-but-authoritative-looking manifest — bounded by
`manifest_trusted: false` default + "the page, not the manifest, is authority" +
"`sha` is a drift hint, never a seal." A **poisoned manifest** can mis-ground
(waste tokens, surface a wrong-but-inert page) but **cannot escalate to
instruction execution** — bounded by the always-on, eval-backed `§Untrusted Tool
Output`; this is **parity with a poisoned markdown index, not worse**. The KB **path**
is self-authored and out-of-repo (off the agentic-os trust boundary); it is consumed
**fail-closed as DATA** (unreadable / `${ACX_KB_PATH}`-unset / malformed / symlink-dead →
treated as absent). No containment / `..` / symlink-rejection guard is applied: the
legitimate KB is an out-of-repo sibling path the adopter writes in their own gitignored
config (not attacker-influenced), so a guard would only ever fire on the legitimate path
while adding no anti-execution safety over the always-on DATA discipline. The optional
`${ACX_KB_PATH}` env-var resolution + this path trust model are specified in
`docs/specs/kb-seam-hardening.md` (a present-only, additive ADR-009 follow-up).

**Out of scope (honest boundaries)**: **Stage 2** (multi-standard resolution /
auto cross-phase consult / a "KB-drift-detected" review finding / a backfill
loop) — deferred to a verified recurring consumer (YAGNI); **automated KB
write-back (C)** — rejected outright; **KB linting / ingestion / freshness
ownership** — the KB's job, never agentic-os's (it must not take on linting an
external, optional, per-adopter directory); the **mixed/cross-module
`task_routing` fan-out rule** (single-domain keys → fan-out-per-domain + union +
fall-to-`standards-by-product`) — an implementation detail of the `§3.6` consult,
specified in the feature spec, not this ADR.
