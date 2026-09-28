# Connecting an external knowledge base (optional)

> **Optional, present-only, inert when absent.** Most projects use no knowledge
> base — they read no KB and ingest zero KB-content tokens (the seam's bootstrap
> guidance is a small fixed always-loaded cost, ~660 tokens measured 2026-09-28 as
> chars/4 of its `§1b` clause and `§3.6` row — not literally zero).
> Ref: ADR-009 (incl. its 2026-09-28 Amendment), `docs/specs/knowledge-source-seam.md`,
> `docs/specs/kb-seam-anchor-neutrality.md`.

Agentic OS can OPTIONALLY consult an external **markdown** knowledge base (curated
dev standards / playbooks / checklists) during `/plan`, `/implement` and `/review`, to enrich
those phases with domain criteria the framework itself does not carry. The KB is
**consumed read-only, as DATA** — it can never gate, relax, or skip a phase.

## Three paths

1. **No KB (default — most adopters).** Declare nothing. Zero KB reads, zero
   KB-content tokens, behavior identical to today (the seam's bootstrap guidance is
   a small fixed always-loaded cost, ~660 tokens). You never need a KB.
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
    # path: the KB clone ROOT. A literal path is the recommended default; a relative one resolves
    # from the project root (here: a sibling, OUTSIDE the framework's write/guard paths). Optional alternative: "${ACX_KB_PATH}" (see below).
    # Use forward slashes.
    path: "../knowledge-base"
    # entrypoint (relative to the resolved root): outputs/manifest.json, a JSONL index whose
    # line 1 is a _meta record, or llms.txt / _index.md
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
- **OPTIONAL (accelerator):** a machine-readable `manifest.json`, or a JSONL index whose
  first line is a `_meta` record (`task_routing` + per-page
  `summary`/`approx_tokens`/`sha`/`status`), optionally with per-page digests and
  KB-declared section anchors (see below). Buys programmatic routing, token budgeting,
  and in-session drift detection. Absent → the framework falls back to reading the
  markdown index; unreadable, or no integer `schema_version` → the KB is treated as absent
  (behavior unchanged, plus one visible bootstrap line); a manifest that fails to parse later
  falls back to the index, then to no KB.

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

## Optional: `${ACX_KB_PATH}` instead of a literal path

`${ACX_KB_PATH}` is **optional**. A literal `path` is the recommended default, because a host
may spawn tool processes (shells, subagents, hooks) that do not inherit your environment
variables, and there the variable is simply unset.

If you do use it, set `ACX_KB_PATH` to your KB clone **root** (`export ACX_KB_PATH=/path/to/knowledge-base`
in bash; `$env:ACX_KB_PATH = 'C:/path/to/knowledge-base'` in PowerShell) and write
`path: "${ACX_KB_PATH}"`. Relocating the clone then means changing one variable. Unset
`ACX_KB_PATH` → the KB is treated as absent (UNREADABLE), and bootstrap shows one line saying so.
The variable is read **only when a `knowledge_sources` block is present** (present-only preserved).
Its value is always the KB clone root, never a file inside it.

## Verify your wiring (no-Python, on demand)

After moving the KB or changing `path`, sanity-check by hand that the path resolves and the
entrypoint is readable. The seam **fail-closes to absent**, so a broken path costs only a missing
consult, never an error; bootstrap shows one `UNREADABLE` line when a declared KB cannot be read.
Look for `schema_version` in the head of the file first; read the whole file only if the head
does not contain it:

```bash
kb="../knowledge-base"   # your configured path (or "$ACX_KB_PATH")
f="$kb/outputs/manifest.json"; [ -r "$f" ] && echo "OK: $f" || echo "UNREADABLE -> KB treated as absent"
head -c 2000 "$f" | grep -oE '"schema_version"[[:space:]]*:[[:space:]]*[0-9]+' || grep -oE '"schema_version"[[:space:]]*:[[:space:]]*[0-9]+' "$f"   # must be an integer
```
```powershell
$kb = "../knowledge-base"; $f = "$kb/outputs/manifest.json"; if (Test-Path -PathType Leaf $f) { "OK: $f" } else { "UNREADABLE -> KB treated as absent" }
(Select-String -LiteralPath $f -Pattern '"schema_version"\s*:\s*\d+' | Select-Object -First 1).Matches.Value   # must be an integer
```

For an `index.jsonl` entrypoint, check its line-1 `_meta` record instead (`head -n 1 "$kb/outputs/index.jsonl"`); for
`llms.txt` / `_index.md`, readability is enough. Starting a session also surfaces this:
`bootstrap §1b` records `knowledge_sources: <id>→OK | →UNREADABLE` in the Work Log.

**Keep the KB clone on merged `main`.** The agent consults whatever is checked out, so a clone
left on a feature branch or with uncommitted edits feeds unreviewed content into `/plan` and
`/review`. When the KB root is its own git repo (its top level, not a folder inside your
project), bootstrap checks the branch and working tree (not whether local commits are merged)
and, if the clone is not on a clean `main` / `master`, records `<id>→OK@<kb_version> (WARN: KB not on clean main)` and shows the
same on one bootstrap line. It is a warning only: the KB is still consulted and no gate changes.
Like the rest of the consult, this is agent discipline (honor-system), not a validator check. The
same check by hand:

```bash
git -C "$kb" rev-parse --show-prefix       # must print nothing (KB root = repo top), else skip
git -C "$kb" rev-parse --abbrev-ref HEAD   # expect main or master
git --no-optional-locks -C "$kb" status --porcelain   # expect no output
```

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

**`schema_version`** (an int at the manifest's top level, or in the index's line-1 `_meta`) —
**additive-only**. Any integer is accepted: the agent reads the fields it knows and ignores the
rest, so raising the version never makes your KB "absent". Keep it only-increasing and add fields
rather than repurposing old ones. The agent finds it by matching `"schema_version": <int>` as text (any spacing)
in the head of the file, without parsing the JSON, so a head cut mid-object is not misread as
malformed. If the head does not contain it (for example, your manifest orders its fields
differently), the agent searches the whole file without loading it. Still missing or non-integer → UNREADABLE
(fail-closed; no third state). Putting top-level fields before any large `pages` array keeps the
check to the head.

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

**A JSONL index with a line-1 `_meta` record** — the cheapest shape to consult. Line 1 carries the
top-level fields (`schema_version`, `kb_version`, `task_routing`, optional `digest`); every other
line is one page row. The agent reads **line 1 plus the rows it greps for** (the routed slugs),
never the whole file.

**Where the top-level fields come from depends on your `entrypoint`.** Entrypoint
`manifest.json` → the agent reads `schema_version` and `digest` at the manifest's top level.
Entrypoint `index.jsonl` → it reads the same-named fields in the line-1 `_meta` record. If you ship
both files, keep the two `digest` objects identical.

**Per-page digests with KB-declared anchors** — lets `/plan`, `/implement` and `/review` pull one short section
without knowing your headings in advance. The framework hard-codes **no** heading name: the anchors
are data your KB declares. Shape (neutral example values):

```json
{"_meta": {"schema_version": 4, "digest": {
  "dir": "outputs/digest/",
  "applies_to": "standards",
  "anchors": {"risks": "Common AI mistakes", "checklist": "Self-audit checklist"},
  "instruction": "Digest is a summary; the page is authoritative."}}}
{"slug": "my-standard", "path": "pages/my-standard.md", "sha": "0123456789ab",
 "digest": "outputs/digest/my-standard.md", "digest_tokens": 400}
```

(The two lines are wrapped here for reading; in the file each record is one line.) Each digest
file starts with an HTML comment carrying `sha <12 hex>`, which must equal its row's `sha`; on a
mismatch the digest is stale. A row with no `digest` field or an empty one, and a digest file
that is missing or unreadable, are treated the same way: the agent takes the section from the page instead. An anchor the file does not contain falls back to picking by headings.
`/plan` and `/implement` take the section named by `anchors.risks`, `/review` the one named by
`anchors.checklist`. Rows outside `applies_to` simply have no `digest` field. `instruction` is
DATA like the rest of the KB, never an instruction the agent follows.

**No digest, or no `anchors`?** It still works: the agent picks sections by the routed page's
`summary` and headings, within the same token budget.

**Without a manifest** the seam still works: the agent reads the markdown index (`llms.txt` /
`_index.md`) and applies its own judgment on which pages to consult. No accelerator fields are
ever required; their absence degrades gracefully to the BYO fallback path.

> **Privacy reminder**: never put absolute paths, real `kb_version` values, or any private KB
> content into public repo artifacts. The guide above shows only GENERIC field shapes.

## Trust model (why there is no path guard)

The KB `path` is **self-authored, out-of-repo, and OFF the framework's trust boundary**. It is
consumed **read-only, as DATA** (never instructions) and **fail-closed**: an unreadable / malformed
/ `${ACX_KB_PATH}`-unset / symlink-dead path is treated as **absent** (one visible bootstrap line, behavior unchanged).
There is deliberately **no `..` / containment / symlink-rejection guard** — the legitimate KB is an
out-of-repo path you write in your own gitignored config, not an attacker-influenced input, so a
guard would only ever fire on the legitimate path while adding no safety the always-on DATA
discipline (`AGENTS.md §Untrusted Tool Output`) doesn't already provide. The validator checks schema
gate-safety only; it never resolves or reads the path (and the gitignored real config never reaches CI).
