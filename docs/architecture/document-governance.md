---
status: living
domain: document-governance
created: 2026-03-29
last_updated: 2026-10-19
lifecycle:
  owner: "/govern-docs"
  review_cadence: on-event
  review_trigger: "When a Domain Doc decision is added/superseded, OR when L2 Decision Log entry count exceeds restructure_threshold (.agent/config.yaml §domain_doc), OR when any new ADR amends document-governance scope"
  supersedes: none
  superseded_by: none
---

# Document Governance — Layer 1 Synthesis

> This is the current effective design. Updated only by `/govern-docs --restructure`.
> Decision history is in `docs/architecture/document-governance.log.md` (L2 — append-only).

## Current Design

Agentic OS uses a **two-layer Domain Doc architecture** to separate "what to read" from "what to trace":

- **L1 Synthesis** (`docs/architecture/<domain>.md`): Current effective design principles. Hard cap: 150 lines (configurable via `.agent/config.yaml` `domain_doc.max_synthesis_lines`). This is what `/bootstrap` reads.
- **L2 Decision Log** (`docs/architecture/<domain>.log.md`): Append-only chronological entry blocks. Never deleted, only appended. Agents read this only for traceability queries; bootstrap does not read it.

Document taxonomy: Domain Doc, Feature Spec, ADR, Product Backlog, Review Snapshot, Guide — each with a fixed path, lifecycle status, and owner workflow.

## Key Principles

- **One topic, one canonical file**: Before creating any `.md` in `docs/`, verify no existing file covers the same domain. Tool-specific entry files (`CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`) are adapters that point to `AGENTS.md`, never second copies of the rules.
- **Knowledge consolidation at /ship**: Every shipped spec's `## Domain Decisions` section (max 10 entries, tagged `[DECISION]`/`[TRADEOFF]`/`[CONSTRAINT]`) is appended to L2.
- **L1 is curated, L2 is permanent**: Only `/govern-docs --restructure` may rewrite L1. L2 entries are never deleted.
- **Capability-by-presence**: All domain doc mechanisms are no-ops when artifacts are absent — backward compatible with downstream projects that haven't adopted domain docs.
- **No hand-carried counts**: `current_state.md` holds no count of anything that lives in another file; a figure that must be maintained by hand goes stale and is deleted rather than monitored.
- **A check that cannot run says so**: it reports SKIP or WARN, never PASS and never silence; a validator's top-line verdict is qualified by every check that did not run without a stated reason.

## Governed Writes and Audit Trail

- **Guarded writes**: `guard_context_write.py` protects the paths in `.agent/config.yaml §guard_policy.protected_paths` (SSoT, `AGENTS.md`, `.agent/rules/**`, …) with a policy allow-list, a sha-checked replace, and per-target receipts. `lint_governed_writes.py` fails a PR whose code writes a governed path directly (`# guard-exempt: <reason>` is the opt-out).
- **Hash-chained archive index**: `archive/INDEX.jsonl` is append-only; every entry carries `prev_sha`, written only by `append_chain_entry.py`. Tail truncation is detected against `origin/main`'s merge-base (tamper-evidence, not prevention); `migrate` fails closed on a mismatched `prev_sha`. A pre-existing broken chain stays red — a log you can silently repair is not tamper-evident.
- **Archive layout**: the directory is the type. `archive/` root holds final Work Logs (`<worklog-key>-<YYYYMMDD>.md`; a same-day collision uses `--N-`); `archive/work/` holds compaction fragments of still-active logs. A `log` already recorded in INDEX is rejected at append time.
- **Point-in-time archival**: incomplete Work Logs are archived as-is; receipts are never fabricated retroactively, and historical gate gaps stay visible as validator WARNs.
- **SSoT caps** are WARN-only (`check_ssot_caps.py`): Ship History keeps the latest 10 (older entries rotate verbatim to `archive/ship-history-YYYY.md`), Spec Index keeps 30 inline.

## Decision Capture

- At `/ship`, every `## Decisions` entry in the **active** log gets one marker before the archival move: `→ promoted: ADR-<id>` / `→ consolidated: L2 <domain>` / `→ local`. An entry naming an ADR cannot be `→ local`. Markers added after archival cannot clear the WARN (archived logs are immutable).
- The durable home for non-promoted decisions is the INDEX.jsonl `decisions[]` one-liner, which bootstrap reads on module overlap — not an L2 auto-append.
- `check_decision_disposition.py` is WARN-tier and checks marker presence plus the ADR-naming tripwire; prose-fuzzy rubber-stamps stay honor-system (accepted ceiling).
- Grandfathering hangs on one switch, `document_lifecycle.decision_disposition_since`.

## Validator Integration

- A validator-wired tool either ships in **both** `deploy.sh` whitelist sites with the manifest golden regenerated in the same change, **or** states its reason at the call site (`run_python_check_source_only` / `-AbsentReason`). No third option (`tests/ci/test_validator_absent_tool_signal.py`).
- Adapter dispatch integrity is checked from each command stub's single "Execute the canonical workflow:" directive line, whenever `.claude/commands/` exists.
- Review-snapshot `routing_actions` are parsed from the canonical column-0 block by `check_routing_actions.py`; a pending action closes only by moving to `merged` or `rejected`.

## Constraints

- L2 writes are append-only. Existing entries MUST NOT be modified or deleted.
- Primary domain receives full consolidation; secondary domains get cross-reference pointers only.
- Progressive rollout: forward-only + backfill-on-touch (no retroactive migration of existing shipped specs).
- Delegated model output (`/ask-local`, `codex --oss`) is untrusted data; the primary agent keeps every phase, gate and Work Log write, and applies any returned patch itself.
- Rejected, do not retry: the `design_tool` capability-seam escape from the design gate (ADR-001 Amendment, 2026-07-16).

## Workflow Contracts

- **Bootstrap authority gate**: A candidate L1 file becomes current design authority only when `docs/architecture/<domain>.md` exists and its frontmatter declares `status: living`. Filename match alone is not enough.
- **Audit routing contract**: Significant architectural findings from `/audit` must be emitted as structured `routing_actions` blocks targeting canonical specs or domain docs, so follow-up work can survive beyond the review snapshot. Same-day snapshots use scope-qualified filenames.
- **Ship consolidation contract**: When a shipped spec still declares `primary_domain`, `/ship` must either update that domain's L2 log or record an explicit skip justification tied back to the spec field. Generic skip text is invalid.
