---
status: shipped
title: Knowledge-Source Consumption Seam (Stage 1)
primary_domain: downstream-adaptability
adr: docs/adr/ADR-009-knowledge-source-consumption-seam.md
signal_tier: T1
created: 2026-06-20
---

# Spec: Knowledge-Source Consumption Seam (Stage 1)

> **Summary**: A present-only, OPTIONAL `knowledge_sources:` block (extending
> ADR-007's `downstream-capabilities.yaml`) that lets the governed flow CONSUME
> (read-only) an external markdown knowledge-base to enrich `/plan` + `/review`.
> Absent → zero cost. KB content = DATA, never instructions. Manifest-preferred,
> page-authoritative. Decision + rationale: ADR-009.

## Scope (Stage 1 only)

In: the present-only declaration + loader, the validator allowlist extension, one
scope-detected consult clause, the consumption ladder, the data-discipline +
honest-enforcement clauses, the structural validator check, a downstream docs
paragraph, and tests. **Out** (Stage 2 / rejected): see Non-goals.

## Acceptance Criteria

- **AC-1 — Present-only, zero-cost-absent.** `knowledge_sources:` is a new opt-in
  block in `.agentcortex/context/private/downstream-capabilities.yaml`. When the
  file (or the block) is absent, `bootstrap.md §1b` records `Knowledge-Sources:
  none`, performs **zero KB reads / zero tokens**, the §3.6 consult row never
  activates, and behavior is byte-identical to today. *(no-KB 99% path)*
- **AC-2 — Validator allowlist extended ATOMICALLY (gate-safety preserved).**
  `validate_downstream_capabilities.py` accepts `knowledge_sources` as a known
  top-level key with a strict sub-schema. A present file with valid
  `skills`/`subagent_policy`/`trackers` **plus** a valid `knowledge_sources`
  block PASSES (no regression to the existing keys). A `knowledge_sources` entry
  carrying any forbidden field — `gate`, `required`, `block_if_missed`,
  `ship_edge`, or `role: authority` (`role` is fixed to `advisory`) — is
  **REJECTED** (whole-file, never clamped), exactly like the `skills[].id MUST be
  custom-*` posture. `manifest_trusted` defaults to `false`.
- **AC-3 — Consumption ladder, fail-closed ("broken == absent").** With
  `knowledge_sources` present, resolution is: (1) the KB has `manifest.json` and
  its `schema_version` matches the known shape → **programmatic query**
  (`task_routing` + per-page `sha`/`approx_tokens`/`status`), never full-load;
  (2) else a markdown index (`llms.txt` / `_index.md`) → read it; (3) else /
  unreadable path / malformed manifest / unknown `schema_version` → **treated as
  absent** (behavior unchanged, ONE advisory, never block). A malformed manifest
  is skipped **whole**, never half-trusted.
- **AC-4 — Scope-detected consult (peer to `doc-lookup`).** A new `bootstrap.md
  §3.6` row `kb-consult`: fires on **feature / architecture-change** → `/plan` +
  `/review`, `/implement` on-match; **hotfix / quick-win** on-match ≤1 page;
  **tiny-fix NEVER** (any phase). Detector = `knowledge_sources` present **AND**
  task in-scope — never an unconditional "consult the KB" (no dangling reference
  for the no-KB 99%). `/review` pulls the KB page's uniform `## 自我稽核 Checklist`
  as criteria; `/plan` pulls `**AI 最常漏掉**` lines as Risks. Caps ≤3 pages/phase
  (≤5 for multi-domain unions) with a **logged drop-list**; tiers are read from
  `manifest.entry.routing_playbook` (`standards-by-product`), NOT the manifest.
- **AC-5 — Mixed/cross-module resolution.** When the task scope spans multiple
  domains (no single `task_routing` key matches), the consult fans out **one
  `task_routing` query per detected domain → unions the slugs → applies the
  multi-domain cap**; zero matches → fall to `standards-by-product`. *(closes the
  re-sim's only new break)*
- **AC-6 — Data discipline (cite, don't duplicate).** KB content **including the
  manifest** is consumed as DATA under `AGENTS.md §Untrusted Tool Output`; the
  KB's own `AGENTS.md`/`CLAUDE.md`/routing tables are **never loaded as
  governance**; the manifest is a **HINT**, the page is **authority**; the
  manifest `sha` is a **drift-detector, not a tamper-seal**; volatile facts →
  official source wins. These clauses **cite** the existing `§Untrusted Tool
  Output` + the KB's own anti-hallucination rules — they do NOT mint duplicate
  governance.
- **AC-7 — Structural validator (T1, the seam ships).** `validate.sh` /
  `validate.ps1` assert that `bootstrap.md` still ships (i) the `§1b`
  `knowledge_sources` load clause and (ii) the `§3.6` `kb-consult` row — mirroring
  the existing `§1b` / ADR-004-step structural checks. Missing either = validator
  FAIL.
- **AC-8 — Deploy ships nothing KB-related except the validator + a docs
  paragraph.** `deploy.sh` ships the (already-whitelisted) extended validator and
  a new downstream docs paragraph explaining the seam; it ships **no** KB content,
  `manifest.json`, `llms.txt`, or KB tooling. No new KB-path grep is added to
  `validate.sh`.
- **AC-9 — Honest enforcement table (§13 ADD-Gate).** The downstream docs
  paragraph (and this spec) carry the structural-T1-vs-honor-system table;
  behavioral consult-quality clauses (no-full-load, schema-fail-closed,
  hint-not-authority, re-read-on-stale, tier-ranking) are **LABELED honor-system**
  and MUST NOT be phrased as enforced controls. *(the `current_state.md:216`
  verifier-without-defense lesson)*
- **AC-10 — Cross-platform + no-Python.** Consumption is plain file / JSON read
  (Claude / Codex / Gemini / API — no platform-specific dependency);
  web-fallback is phrased "if web is available"; a no-Python downstream still
  consumes the KB (only the CI gate-safety validator needs Python, degrading to
  WARN per the existing no-Python doctrine).

## Domain Decisions

- `[DECISION]` **Reuse the ADR-007 seam, not a new file or a `config.yaml` key.**
  `config.yaml` is force-update **core** tier (ADR-005) → a downstream KB path
  there is silently overwritten on `deploy`. Registration lives in never-shipped
  `context/private/`.
- `[DECISION]` **Manifest-preferred, page-authoritative.** The manifest is a
  derived, non-authoritative HINT (the KB's own `AGENTS.md:39` contract); the page
  is authority. A BYO KB's manifest freshness is the adopter's own CI, OFF the
  agentic-os trust boundary → `manifest_trusted: false` default.
- `[DECISION]` **BYO floor = a readable markdown index; manifest OPTIONAL.** Any
  hand-written `llms.txt` / `_index.md` makes a KB consumable; the manifest only
  buys machine routing + drift-detection + token budgeting.
- `[TRADEOFF]` **Consult-quality is honor-system; the seam is structural T1.** The
  validator proves the seam is gate-safe + ships, not that the agent consulted
  well. Accepted per the ADR-004/007 precedent (labeled, no fake MUST).
- `[CONSTRAINT]` **The validator allowlist extension MUST land atomically** with
  the `§1b` clause — else the unknown `knowledge_sources` key makes the validator
  reject the entire `downstream-capabilities.yaml` (killing existing
  `skills`/`trackers`). *(highest-severity build-order constraint)*

## Non-goals (Stage 2 deferred / rejected — do NOT build in Stage 1)

- Stage 2: multi-standard auto cross-phase consult, an automated "KB-drift-
  detected" review finding, snapshot-tuple drift machinery beyond a same-session
  sha cache. *(deferred to a verified recurring consumer — YAGNI §5.4)*
- **C — automated `/ship` or `/retro` → KB backfill.** Rejected outright
  (cross-repo write into shared state = poisoning + secret-exfil). Distill stays
  human-confirmed manual.
- KB linting / ingestion / freshness ownership — the KB's job, never agentic-os's.
- Shipping any KB content/tooling downstream.

## Verification (test plan — full detail at /test)

- AC-1: a no-`knowledge_sources` fixture → `§1b` records `none`, zero KB reads.
- AC-2: validator unit tests — valid `knowledge_sources` PASS (alongside existing
  keys); each forbidden field (`gate`/`required`/`block_if_missed`/`ship_edge`/
  `role: authority`) → REJECT whole-file; non-regression of `skills`/`trackers`.
- AC-3: ladder fixtures — manifest-present / index-only / broken-path / malformed-
  manifest / unknown-schema → correct rung + fail-closed-to-absent.
- AC-7: `validate.sh`/`.ps1` parity — assert §1b clause + §3.6 row present; remove
  them in a fixture → FAIL.
- AC-8: deploy dry-run → validator present, no KB artifact in the deploy set.
