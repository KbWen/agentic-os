---
status: draft
title: Tiered Document Lifecycle Engine
source: external
source_doc: _product-backlog.md
created: 2026-04-12
primary_domain: document-governance
secondary_domains: []
---

# Tiered Document Lifecycle Engine

## Goal

Introduce a 4-tier document lifecycle (active → warm → cold → frozen-summary) so that process artifacts (worklogs, raw intake, decision logs) are progressively compacted while authoritative documents (specs, ADR, domain docs) remain intact. The primary outcome is bounded token cost at bootstrap — agents only read active/warm tier documents.

## Background & Industry Patterns

- **LSM-tree compaction analogy**: Worklogs = WAL/memtable (write-heavy, ephemeral). Shipped specs = SSTables (read-heavy, immutable). `/ship` = leveling compaction. Batch archive GC = size-tiered compaction.
- **Progressive summarization** (Tiago Forte, automated by claude-memory-compiler): Documents pass through layers of compression. At each tier transition, an LLM-generated summary replaces full text in the hot path.
- **MemOS MemCube pattern**: Each document unit carries metadata (provenance, tier, usage frequency) and a policy scheduler adjusts tier based on access patterns. Reported 35% token savings.
- **CrewAI cognitive memory**: Short-term buffer + LLM-driven consolidation into long-term memory. Low-relevance items decay.

## Design: 4-Tier Document State Machine

```
active ──(phase complete / TTL)──→ warm ──(age threshold / GC sweep)──→ cold ──(policy sweep)──→ frozen-summary
                                     │                                    │
                                     └─ full text, archive dir            └─ LLM summary + hash pointer
                                        agents read on explicit query        audit-only, never auto-read
```

### Tier Definitions

| Tier | Location | Content | Bootstrap Reads? | Transition Trigger |
|---|---|---|---|---|
| **active** | `.agentcortex/context/work/` | Full text | Yes | `/ship` archives → warm |
| **warm** | `.agentcortex/context/archive/` | Full text, indexed in INDEX.jsonl | Only on explicit module overlap query | `age > warm_ttl_days` OR archive count > `max_warm_entries` |
| **cold** | `.agentcortex/context/archive/cold/` | LLM summary (≤20 lines) + git SHA of original | Never | Policy sweep or manual |
| **frozen-summary** | Deleted from disk (git history only) | 1-line entry in INDEX.jsonl with hash | Never | `age > cold_ttl_days` |

### Pinned Documents (exempt from lifecycle)

These documents are **never** candidates for compaction or tier transition:
- `AGENTS.md`, `CLAUDE.md`
- `.agentcortex/context/current_state.md`
- `docs/specs/_product-backlog.md`
- Any doc with `status: living` or `status: frozen` in frontmatter

## Acceptance Criteria

### Config (`.agent/config.yaml`)

1. [FROM-SOURCE] New `document_lifecycle` section with tunables:
   ```yaml
   document_lifecycle:
     warm_ttl_days: 30
     cold_ttl_days: 90
     max_warm_entries: 20
     max_active_worklogs: 5
     global_lessons_max_entries: 20
     spec_index_max_entries: 30
     archive_index_max_lines: 200
     pinned_docs:
       - AGENTS.md
       - CLAUDE.md
       - .agentcortex/context/current_state.md
   ```

### SSoT Bloat Caps (addresses F-01, F-03)

2. [INFERRED] `current_state.md` Global Lessons: when exceeding `global_lessons_max_entries`, `/retro` MUST archive oldest LOW-severity lessons to `.agentcortex/context/archive/global-lessons-archive.md` before appending new ones. HIGH-severity lessons are pinned until manually demoted.
3. [INFERRED] `current_state.md` Spec Index: when exceeding `spec_index_max_entries`, `/ship` MUST move oldest `shipped` spec entries to an archive section at bottom of Spec Index (collapsed, not auto-read).

### Archive GC (addresses F-02)

4. [FROM-SOURCE] New `/ship` post-archival step: after archiving a Work Log, check warm-tier entry count. If `> max_warm_entries`, run GC sweep:
   - For each warm entry older than `warm_ttl_days`: generate LLM summary (≤20 lines), write to `cold/` subdir, update INDEX.jsonl entry with `tier: cold` + `summary_sha`.
   - Original warm file: delete from disk (git history preserves it).
5. [INFERRED] Cold-tier entries older than `cold_ttl_days`: remove file from disk, update INDEX.jsonl entry with `tier: frozen`, retain only the 1-line JSONL record.

### Process Artifact Cleanup (addresses F-05, F-06, F-07)

6. [FROM-SOURCE] `_raw-intake-<date>.md` cleanup: change spec-intake §1a.4 from "MAY be deleted" to "MUST be deleted after all features from that intake are either Shipped or Cancelled. `/ship` checks and deletes."
7. [INFERRED] Domain Doc L2 `[superseded]` entries: after `/govern-docs --restructure`, superseded entries older than `warm_ttl_days` MAY be moved to a `<domain>.log.archive.md` file. L2 retains only active entries + a pointer to the archive.
8. [INFERRED] `_product-backlog.md`: when all features are Shipped/Cancelled/Deferred, `/ship` outputs advisory: "Backlog complete. Archive to `docs/specs/_product-backlog-<date>.md`?"

### Validate Enforcement (addresses F-04, F-09)

9. [FROM-SOURCE] validate.sh/ps1: upgrade Work Log compaction check from WARN to FAIL.
10. [FROM-SOURCE] validate.sh/ps1: add archive warm-tier count check. WARN if `> max_warm_entries`.
11. [FROM-SOURCE] validate.sh/ps1: add Global Lessons count check. WARN if `> global_lessons_max_entries`.
12. [INFERRED] validate.sh/ps1: add active worklog count check upgrade from WARN to FAIL when `> max_active_worklogs`.

## Non-goals

- Automated LLM summarization during validate (validate stays pure assertion, no generation)
- Real-time memory systems (vector DB, embedding search) — this is file-based governance only
- Changing the authority model (who can write what) — that's already well-enforced

## Constraints

- All transitions MUST preserve git history — "delete" means remove working copy, not rewrite git history
- Cold-tier summaries MUST include the git SHA of the original file for traceability
- Pinned documents are NEVER compacted regardless of age or size
- GC sweep is triggered by `/ship` (event-driven), not by cron or background process
- Tier transitions are deterministic (age + count thresholds), not heuristic

## Backlog Mapping

This spec is the umbrella design for backlog items #1–#13. Individual items can be shipped independently where dependencies allow:
- **Independent quick-wins** (no dependency on #1): #2 (Global Lessons cap), #4 (Spec Index cap), #5 (validate WARN→FAIL), #6 (_raw-intake cleanup), #9 (dead reference)
- **Depends on #1 config**: #3 (archive GC), #7 (L2 archival), #8 (backlog archive), #10 (active WL FAIL), #11 (shipped spec filtering), #12 (validate checks), #13 (LLM summarization)

## Domain Decisions

- [DECISION] Adopt 4-tier lifecycle (active/warm/cold/frozen-summary) for process artifacts, modeled after LSM-tree compaction patterns.
- [DECISION] Pinned documents (governance files, living docs) are exempt from all lifecycle transitions.
- [CONSTRAINT] All tier transitions must preserve git history — delete means working copy only.
- [DECISION] GC sweep is event-driven (triggered by /ship), not cron-based — agents have no background process capability.

## File Relationship

INDEPENDENT
