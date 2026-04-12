# Portable Minimal Kit for AgentCortex Adoption

This guide defines a minimal, portable set that other projects can adopt without changing core state-machine workflows.

For text encoding and EOL hardening specifically, see `minimal-text-hardening-kit.md`.

## Goal

Reduce handoff and state-document verbosity while preserving evidence and auditability.

## Minimal Kit Components

1. **Compact `/handoff` shape (2 layers)**
- Layer 1: <=10 lines (`Goal`, `Current State`, `Next`, `Blocker`, `Owner`, `Last Verified Command`).
- Layer 2: traceability details (`Done`, `In Progress`, `Risks`, `References`).

2. **Delta-only work log writing**
- Append only new changes from this turn.
- Do not restate prior context unless needed for rollback or decision trace.

3. **Compaction policy**
- Trigger when active log exceeds line or size threshold.
- Keep latest operational context in active log, move older history to archive.

## Recommended Defaults

- `WORKLOG_MAX_LINES=300`
- `WORKLOG_MAX_KB=12`
- `WORKLOG_KEEP_RECENT_ENTRIES=5`
- Archive path: `.agentcortex/context/archive/work/<worklog-key>-<YYYYMMDD>.md`

## Integration Steps (Any Repo)

1. Copy/update workflow text in `.agent/workflows/handoff.md`.
2. Add or merge compaction defaults into `.agentcortex/docs/guides/token-governance.md`.
3. Keep existing state-machine and ship gates unchanged.
4. During adoption, run one dry-run handoff and verify:
- Layer 1 can be read in <30 seconds.
- Layer 2 still contains doc + code + work-log references.

## Non-Goals

- No changes to canonical state transitions.
- No changes to release policy, review policy, or testing policy.