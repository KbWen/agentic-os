# Skill Conflict Matrix

> This matrix is intentionally sparse. Only document conflicts that are already
> observed in practice or architecturally obvious. Absence from this table
> means "assumed compatible" until `/retro` records a better rule.

Bootstrap reads this matrix once when it writes `Recommended Skills`.

- Purpose: surface known skill combinations that need an explicit precedence or scoping note.
- Scope: `/bootstrap` only. Later phases use the Work Log's `## Conflict Resolution` record and do not need to re-read this file.
- Resolution rule: when a pair is `partial-conflict` or `conflict`, `/bootstrap` MUST record the chosen precedence or partitioning strategy in the active Work Log.

| Skill A | Skill B | Relation | Guidance |
| --- | --- | --- | --- |
| test-driven-development | executing-plans | compatible | TDD micro-cycles fit naturally inside stepwise plan execution. |
| dispatching-parallel-agents | test-driven-development | partial-conflict | Prefer TDD on the critical path; parallel dispatch is limited to isolated subproblems or verification tasks. |
| dispatching-parallel-agents | systematic-debugging | partial-conflict | Parallel work can collect observations, but the hypothesis -> verify loop stays sequential in one owner session. |
