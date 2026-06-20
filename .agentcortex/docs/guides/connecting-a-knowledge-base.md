# Connecting an external knowledge base (optional)

> **Optional, present-only, zero-cost-when-absent.** Most projects use no knowledge
> base — they pay nothing for this seam. Ref: ADR-009, `docs/specs/knowledge-source-seam.md`.

Agentic OS can OPTIONALLY consult an external **markdown** knowledge base (curated
dev standards / playbooks / checklists) during `/plan` and `/review`, to enrich
those phases with domain criteria the framework itself does not carry. The KB is
**consumed read-only, as DATA** — it can never gate, relax, or skip a phase.

## Three paths

1. **No KB (default — most adopters).** Declare nothing. Zero reads, zero tokens,
   behavior identical to today. You never need a KB.
2. **Bring your own.** Point the framework at any markdown KB you already have
   (a `docs/` folder, a wiki). The only requirement is one readable index file.
3. **Start from a reference.** Use a Karpathy-style "LLM wiki" as a template. The
   framework ships **no** KB content or tooling — you keep your KB in its own repo.

## How to connect (opt-in)

Add a `knowledge_sources:` block to your gitignored
`.agentcortex/context/private/downstream-capabilities.yaml` (the same present-only
file that registers custom skills; it is never shipped, never overwritten on update):

```yaml
knowledge_sources:
  - id: kb-main
    path: ../knowledge-base            # resolves OUTSIDE the framework's write/guard paths
    entrypoint: outputs/manifest.json  # or llms.txt / _index.md
    role: advisory                     # FIXED — a KB can never be authority
    manifest_trusted: false            # default; set true only if YOUR CI keeps the manifest fresh
```

## Minimal contract a KB must satisfy

- **REQUIRED (floor):** one readable **markdown index** — `llms.txt` or `_index.md`
  (or a declared `entrypoint`) — listing pages with one-line summaries + relative
  paths. Any hand-written index works; **no special tooling required.**
- **OPTIONAL (accelerator):** a machine-readable `manifest.json` (`task_routing` +
  per-page `summary`/`approx_tokens`/`sha`/`status`). Buys programmatic routing,
  token budgeting, and in-session drift detection. Absent → the framework falls
  back to reading the markdown index; broken/malformed → falls back to no-KB
  (behavior unchanged).

## What is enforced vs. what is agent-discipline (honest boundary)

| Property | Enforcement |
|---|---|
| The seam is present-only; **absent → zero cost** | **Structural** — `validate.*` assert the §1b load step + the §3.6 `kb-consult` row ship; deploy ships no KB artifact |
| A KB can never gate/relax a phase (`role: advisory`, no gate fields) | **Structural** — `validate_downstream_capabilities.py` REJECTS any forbidden field (whole-file, never clamped) |
| KB content cannot issue instructions | **Structural-adjacent** — `AGENTS.md §Untrusted Tool Output` (always-on, eval-backed) |
| The agent consults the right page / re-reads a stale one / prefers official sources for volatile facts / treats the manifest as a hint | **Honor-system** — agent discipline, NOT a machine control. A stale or thin KB just yields a weaker consult; it never breaks a gate. |

> The KB is a **fallible starting pointer**, never verified truth. "No evidence, no
> completion" always outranks "the KB said so." A BYO manifest's freshness is YOUR
> CI's job — off the framework's trust boundary, hence `manifest_trusted: false` by
> default.
