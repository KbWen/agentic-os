---
status: shipped
source: internal
primary_domain: governance
secondary_domains: [token-economics, cross-platform]
created: 2026-05-31
owner: "@kbwen + Claude Opus 4.8"
related_adr: docs/adr/ADR-001-governance-friction-tuning.md
---

# Spec: Handoff-Trigger Policy (Occupancy + Phase-Boundary)

## Goal

Replace the **turn-count** handoff trigger with a **context-occupancy + phase-boundary** model as the primary signal, demote turn-count to an explicitly-labelled soft fallback, converge the four scattered/contradictory turn constants into a single SSoT, fix the one genuinely stale caching statement, and make the whole model **uniform across Claude / OpenAI Codex / Google Gemini-Antigravity / raw API** — reflecting each platform's current (2026-verified) caching + compaction behaviour. The rule stays **advisory / honor-system**; no new enforced gate is introduced.

## Background (verified current state, grep + 2026 source-checked)

- **Turn-count handoff rules that exist today** (the real, to-change set):
  - `AGENTS.md §Context Pruning` — "At 8+ turns … suggest handoff."
  - `.agentcortex/docs/NONLINEAR_SCENARIOS.md` Rule 6 — 8 suggest / 12 auto-checkpoint / 15 escalate (+ zh-TW mirror).
  - `.agentcortex/docs/NONLINEAR_SCENARIOS.md` Rule 1 — auto-checkpoint every 3+ implementation turns (Work-Log checkpoint, not handoff).
  - `.agentcortex/docs/guides/token-governance.md §1` — feature budget 3–6 turns.
- **The only genuinely stale caching line**: `token-governance.md §6 L75` says caching "becomes available in your platform" (implies future / not-yet-GA).
- **Retracted false claims** (self-audit, Lesson [audit-verification]): the platform guides do NOT contain "no prompt caching (yet)" or "handoff before ~50% context" — no occupancy guidance exists anywhere today; this spec ADDS it.
- **2026 platform reality (source-verified)**: all three majors now have automatic prompt caching at ~0.1× read AND automatic compaction at high context-fill:
  - Claude/Claude Code: auto-cache 0.1× read; default TTL 5 min (since Mar 2026), 1 h opt-in; compaction reuses prefix KV cache; Opus 4.6–4.8 = 1M window. [[platform.claude.com prompt-caching]]
  - OpenAI/Codex: automatic caching, no code/fee, 0.1×, prefix ≥1024 tok; 24 h extended on GPT-5.1; auto-compact ~95% capacity. [[developers.openai.com prompt-caching + compaction]]
  - Gemini/Antigravity: implicit caching default-on (2.5+, since May 2025, 0.1×) + explicit `cachedContent`; 1M–2M window. [[ai.google.dev caching]]
  - **Common denominator** → occupancy % (turn-count is not, windows span 200K–2M); phase boundary is platform-agnostic (shared state machine); premature handoff resets a warm cache on every platform → costs more than continuing.

## Acceptance Criteria

- **AC-1**: `AGENTS.md §Context Pruning` states **context-occupancy + phase-boundary** as the primary handoff signal and labels turn-count an explicit coarse fallback. Verifiable: the section contains "occupancy" and "phase boundary", and the bare "8+ turns" is no longer the primary trigger.
- **AC-2**: The rule remains **advisory** — no new "MUST"/enforced wording in `AGENTS.md §Context Pruning`, and no new check added to `validate.sh`/`validate.ps1`. Verifiable: `git diff` of validate.* shows no handoff-trigger threshold check.
- **AC-3**: `NONLINEAR_SCENARIOS.md` Rule 6 reconciled — occupancy/phase primary, the 8/12/15 ladder demoted to a labelled fallback heuristic referencing the AGENTS.md SSoT; Rule 1 clarified as a cheap Work-Log checkpoint (not a handoff). zh-TW mirror identical in meaning.
- **AC-4**: `token-governance.md §6` L75 corrected — caching described as **active by default on Claude/Gemini/OpenAI today** (not "becomes available"); a compact cross-platform occupancy/caching/compaction table added. zh-TW parity (condensed).
- **AC-5**: `token-governance.md §1` turn budget reframed as a **soft heuristic** that points to the occupancy SSoT (resolves the "feature done at 6 turns but handoff at 8" contradiction). zh-TW parity.
- **AC-6**: A **1-line pointer** to the canonical handoff-timing rule added in `CLAUDE_PLATFORM_GUIDE.md`, `CODEX_PLATFORM_GUIDE.md` (+ zh-TW), and `antigravity-v5-runtime.md` so platform-specific readers find it.
- **AC-7**: After the change, none of the four loci present **conflicting handoff guidance** — each either references the SSoT or is explicitly labelled soft/fallback. Verifiable by reading the four sections.
- **AC-8**: `validate.sh` AND `validate.ps1` both pass (fail=0). No broken internal `.md` links introduced; EN/zh-TW parity intact.
- **AC-9**: Cross-platform caching claims in the spec and in `token-governance §6` cite authoritative 2026 sources (Anthropic / OpenAI / Google docs).

## Non-goals

- NOT adding programmatic occupancy measurement, a validator, or any enforcement — the trigger stays advisory (harness auto-compaction is the real hard limit).
- NOT changing the state machine, phase order, or the handoff hard-gate (`feature`/`arch-change` still require `/handoff` before ship).
- NOT removing turn-count entirely — it is retained as a labelled coarse fallback.
- NOT editing `docs/AGENT_MODEL_GUIDE.md` (human-only model-selection doc — out of scope).
- NOT rewriting `context-budget.md §Prompt Caching Awareness` (already accurate).

## Constraints

- Advisory / honor-system only; no new unenforced "MUST" (Lessons [enforcement][HIGH], [governance-proposal][MEDIUM]).
- AGENTS.md is hot-path (loaded every turn) → its edit MUST stay tight; detailed rationale + the cross-platform table live in `token-governance.md §6` (cold, manual-load).
- Bilingual parity for every EN edit (`_zh-TW` mirrors).
- Surgical edits; preserve all unrelated semantics (downstream-UX-first, Lesson [scope-expansion]).
- Windows EOL discipline: use Edit tool / normalize EOL on any appended content to tracked CRLF files (Lesson [cross-platform-eol]).

## File Relationship

INDEPENDENT — no existing spec covers handoff-timing policy. Operates within ADR-001 (governance-friction-tuning) coverage; ADR-001 MAY be amended at `/ship` if the occupancy model is judged an ADR-level decision (deferred — not required, per [adr-discipline]).

## Domain Decisions

- [DECISION] Primary handoff trigger = **context-occupancy + phase-boundary**; turn-count demoted to a coarse fallback. Turn-count is a poor proxy across platforms (windows 200K–2M, per-turn token weight varies wildly); occupancy is the true driver of both quality and (pre-cache) cost.
- [DECISION] Rule stays **advisory / honor-system** — no new enforced MUST and no validator. grep confirms `validate.*` never enforced the turn thresholds; an unenforced MUST is theatre (Lesson [enforcement]).
- [DECISION] **Single SSoT** in `AGENTS.md §Context Pruning`; NONLINEAR Rule 6 and token-governance §1/§6 reference it instead of restating competing numbers — kills the prior 4-way contradiction.
- [DECISION] The core economic rationale is **"premature handoff resets the warm prompt cache"**, which now holds on every major platform (all cache the prefix at ~0.1× and auto-compact at high fill) — verified against 2026 vendor docs.
- [TRADEOFF] Occupancy % is not always programmatically readable by the agent → expressed as **model self-assessment** + reliance on harness auto-compaction for the hard limit. Accepted because cross-platform compaction already covers the crash/overflow case that the turn-12/15 ladder was invented for.
- [TRADEOFF] Keep ONE coarse turn-count fallback (~8) explicitly labelled a heuristic, rather than deleting turn-count outright — graceful degradation for environments that cannot estimate occupancy.
- [CONSTRAINT] The model MUST hold uniformly across Claude / Codex / Gemini-Antigravity / API; per-platform caching + compaction nuance is documented once in `token-governance.md §6`, with 1-line pointers from each platform guide.
- [CONSTRAINT] Every EN edit MUST have a zh-TW mirror; EN remains authoritative on conflict.
