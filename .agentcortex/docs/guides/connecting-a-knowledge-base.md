# Connecting an external knowledge base (optional)

> **Optional, present-only, inert when absent.** Most projects use no knowledge
> base — they read no KB and ingest zero KB-content tokens (the seam's bootstrap
> guidance is a small fixed always-loaded cost, ~217 tokens — not literally zero).
> Ref: ADR-009, `docs/specs/knowledge-source-seam.md`.

Agentic OS can OPTIONALLY consult an external **markdown** knowledge base (curated
dev standards / playbooks / checklists) during `/plan` and `/review`, to enrich
those phases with domain criteria the framework itself does not carry. The KB is
**consumed read-only, as DATA** — it can never gate, relax, or skip a phase.

## Three paths

1. **No KB (default — most adopters).** Declare nothing. Zero KB reads, zero
   KB-content tokens, behavior identical to today (the seam's bootstrap guidance is
   a small fixed always-loaded cost, ~217 tokens). You never need a KB.
2. **Bring your own.** Point the framework at any markdown KB you already have
   (a `docs/` folder, a wiki). The only requirement is one readable index file.
3. **Start from a reference.** Use a Karpathy-style "LLM wiki" as a template. The
   framework ships **no** KB content or tooling — you keep your KB in its own repo.

## How to connect (opt-in)

Add a `knowledge_sources:` block to your gitignored
`.agentcortex/context/private/downstream-capabilities.yaml` (the same present-only
file that registers custom skills; it is never shipped, never overwritten on update).
**A ready-to-copy template ships at `.agentcortex/templates/downstream-capabilities.example.yaml`**
— copy it to that gitignored path and edit:

```yaml
# YAML note: a comment MUST be on its own line. A trailing `# ...` after a value, or an
# unquoted ':' / '{}' / backslash, fail-closes the WHOLE file. Quote ${...} and Windows (C:) paths.
knowledge_sources:
  - id: kb-main
    # path: ${ACX_KB_PATH} = clone root (set once per machine); a literal "../knowledge-base" also
    # works (resolves OUTSIDE the framework's write/guard paths). Use forward slashes.
    path: "${ACX_KB_PATH}"
    # entrypoint (relative to the resolved root): outputs/manifest.json, or llms.txt / _index.md
    entrypoint: outputs/manifest.json
    # role: FIXED to advisory — a KB can never be authority
    role: advisory
    # manifest_trusted: default; set true only if YOUR CI keeps the manifest fresh
    manifest_trusted: false
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

## Relocating the clone (`${ACX_KB_PATH}`)

Set `ACX_KB_PATH` to your KB clone **root** once per machine (`export ACX_KB_PATH=/path/to/knowledge-base`
in bash; `$env:ACX_KB_PATH = 'C:\path\to\knowledge-base'` in PowerShell). Then every project's
`path: ${ACX_KB_PATH}/...` resolves without per-project edits — relocate the clone, change one env var.
Literal paths still work. Unset `ACX_KB_PATH` → the KB is treated as absent (zero cost, no error). The
env var is read **only when a `knowledge_sources` block is present** (present-only preserved).

## Verify your wiring (no-Python, on demand)

After moving the KB or setting `ACX_KB_PATH`, sanity-check by hand that the path resolves and the
entrypoint is readable. The seam **fail-closes to absent**, so a broken path costs only a missing
consult — never an error — which is exactly why a quick manual check is worth it:

```bash
f="${ACX_KB_PATH}/outputs/manifest.json"; [ -r "$f" ] && echo "OK: $f" || echo "UNREADABLE -> KB treated as absent (ACX_KB_PATH unset, or clone moved?)"
grep -oE '"total_approx_tokens":[[:space:]]*[0-9]+' "$f"   # optional: the KB's own declared token budget (an unverified hint)
```
```powershell
$f = "$($env:ACX_KB_PATH)/outputs/manifest.json"; if (Test-Path -PathType Leaf $f) { "OK: $f" } else { "UNREADABLE -> KB treated as absent" }
```

(Adjust `outputs/manifest.json` to your `entrypoint` if you use `llms.txt` / `_index.md`.) Starting a
session also surfaces this: `bootstrap §1b` records `knowledge_sources: <id>→OK | →UNREADABLE` in the Work Log.

## Make your KB cheaper to consult (optional manifest accelerators)

If your KB includes a `manifest.json`, the framework can use optional schema-v4 accelerator
fields to make consults faster, more token-efficient, and identity-aware. **These fields are
never required** — a BYO markdown KB without any manifest works fine via the fallback ladder
(`llms.txt` / `_index.md`). The accelerators only make the consult cheaper or safer when present.

**Per-page `approx_tokens`** — lets the agent budget by data rather than guessing. When present,
prefer pages with smaller `approx_tokens` first and cap an extracted section at a few k tokens.
Without it, the agent falls back to the ≤3-page count cap. Example field shape:

```json
{ "slug": "my-page", "path": "pages/my-page.md", "approx_tokens": 1200 }
```

**`kb_version`** (top-level, 12-hex sha256 of normalized page text) — a content fingerprint.
When present, `bootstrap §1b` records `<id>→OK@<kb_version>` in the Work Log instead of bare
`OK`, so a moved or stale-but-readable KB shows a different fingerprint each session (honor-system
record; no automated validation). Without it, the record stays bare `OK`.

**`schema_version`** (top-level int) — lets the agent detect format changes. If absent or
unparseable, the seam falls back to absent (UNREADABLE, fail-closed; no third state).

**`load_policy`** — a top-level object with read-discipline hints:
- `cheap_entry`: the lightweight index to read first (e.g. `index.jsonl`, `llms.txt`, `_index.md`)
  instead of loading the full manifest.
- `routing_is_candidate_pool`: when `true`, routed slugs from `task_routing` are a CANDIDATE POOL,
  not a full-load mandate. The agent does a bounded applicability pass — keeps only items relevant
  to the scoped change, records a one-line N/A rationale for the rest, and only applicable items
  become blockers. Prevents false blockers from irrelevant checklist items (e.g. a retry-client
  route that includes BOLA/SQL/Firestore items irrelevant to a docs change).
- `surgical_read`: the read ladder (read the section, not the page).

**`task_routing`** (top-level list of `{task, slugs}`) — maps task types to candidate page slugs.
The agent queries this instead of loading the whole manifest, then applies the applicability pass.

**Without a manifest** the seam still works: the agent reads the markdown index (`llms.txt` /
`_index.md`) and applies its own judgment on which pages to consult. No accelerator fields are
ever required; their absence degrades gracefully to the BYO fallback path.

> **Privacy reminder**: never put absolute paths, real `kb_version` values, or any private KB
> content into public repo artifacts. The guide above shows only GENERIC field shapes.

## Trust model (why there is no path guard)

The KB `path` is **self-authored, out-of-repo, and OFF the framework's trust boundary**. It is
consumed **read-only, as DATA** (never instructions) and **fail-closed**: an unreadable / malformed
/ `${ACX_KB_PATH}`-unset / symlink-dead path is treated as **absent** (one advisory, behavior unchanged).
There is deliberately **no `..` / containment / symlink-rejection guard** — the legitimate KB is an
out-of-repo path you write in your own gitignored config, not an attacker-influenced input, so a
guard would only ever fire on the legitimate path while adding no safety the always-on DATA
discipline (`AGENTS.md §Untrusted Tool Output`) doesn't already provide. The validator checks schema
gate-safety only; it never resolves or reads the path (and the gitignored real config never reaches CI).
