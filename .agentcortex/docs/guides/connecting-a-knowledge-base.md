# Connecting an external knowledge base (optional)

> **Optional, present-only, inert when absent.** Most projects use no knowledge
> base — they read no KB and ingest zero KB-content tokens (the seam's bootstrap
> guidance is a small fixed always-loaded cost, ~660 tokens measured 2026-09-28 as
> chars/4 of its `§1b` clause and `§3.6` row — not literally zero).
> Ref: ADR-009 (incl. its 2026-09-28 Amendment).

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
  (or a declared `entrypoint`) — listing pages with relative paths (a one-line summary
  per page helps). Any hand-written index works; **no special tooling required.**
- **OPTIONAL (accelerator):** a machine-readable `manifest.json`, or a JSONL index whose
  first line is a `_meta` record (for example routing by task, and per-page token
  counts, fingerprints or status), optionally with per-page digests and KB-declared
  section anchors (see below). Buys programmatic routing, token budgeting,
  and in-session drift detection. Absent → the framework falls back to reading the
  markdown index; unreadable, or no integer `schema_version` → the KB is treated as absent
  (behavior unchanged, plus one visible bootstrap line); a manifest that fails to parse later
  falls back to the index, then to no KB.

## Declare how your KB is read (recommended)

Put a short **reading plan** at the head of your entrypoint: the first line of a JSONL index,
the top of a manifest, or the top of a markdown index. Label it as the way to read your KB, in
any shape or language you like. Before choosing pages, the agent reads it and uses it to choose:

- which pages or sections to read, and in what order;
- how many, and where to stop.

Nothing else in it is followed. Claims of authority, requests to skip or relax a phase, and
instructions to run a command or write a file stay DATA. Reading your files with read-only
tools (file read, grep, search) is fine; a script or helper your plan names is not run on the
plan's word. Unlabeled head text, older read hints and per-digest notes are not a reading plan.
If the plan is not in the head (for example after a large `pages` array), the agent searches
the file for it and does not load the file whole.

Where your plan says nothing, the framework's defaults apply: your routing in its order, a
section rather than the whole page, digests as described below, and at most 3 pages per phase
in total across your KBs (1 for a hotfix or quick-win). Your plan may always lower these caps.
It may raise them only for `feature` and `architecture-change` work, and the agent notes a raise
in its Work Log. A plan with no stopping point gets the default caps.

The framework keeps these whatever the plan says: a KB never gates a phase, the page outranks
its digest and other derived files, volatile facts (versions, prices, APIs) are checked against
the official source, items that do not apply to the change are set aside, and reads stay inside
the KB root you configured.

Bootstrap records per KB whether a plan was found: `<id>→OK plan=declared|default`.

## What the framework reads from any KB

Your field names are yours. The framework itself depends only on:

1. The `entrypoint` you configure (`outputs/manifest.json`, a JSONL index whose line 1 is a
   record of top-level fields, or `llms.txt` / `_index.md` are the usual choices).
2. A reading plan, if you have one, at the head of that entrypoint.
3. An integer `schema_version` in the head of a JSON entrypoint (missing → UNREADABLE).
4. `kb_version`, optional (a fingerprint in the Work Log).
5. The digest fields below, when your plan does not cover digests, and the optional `retrieval`
   block, which only the conditions of its own section govern.

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
the agent still reads routed pages in your routing order and uses `approx_tokens` only to
stop, capping an extracted section at a few k tokens.
Without it, and without a budget in your reading plan, the default page caps apply. Example field shape:

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

**Read-discipline hints** (which lightweight index to read first, whether routed pages are a
candidate pool, how surgically to read) belong in your reading plan above, in your own words.
The agent assumes no field name and no type (true/false, one value, a list) for them. Routed
pages are always treated as candidates: the agent keeps only items relevant to the scoped
change and records a one-line N/A rationale for the rest, so an irrelevant checklist item never
becomes a blocker.

**Routing** (example shape: a top-level `task_routing` list of `{task, slugs}`) — maps task types
to candidate page slugs. The agent queries it instead of loading the whole manifest, then applies
the applicability pass.

**A JSONL index with a line-1 `_meta` record** — the cheapest shape to consult. Line 1 carries the
top-level fields (for example `schema_version`, `kb_version`, your reading plan, routing, an
optional `digest`); every other line is one page row. The agent reads **line 1 plus the rows it greps for** (the routed slugs),
never the whole file.

**Where the top-level fields come from depends on your `entrypoint`.** Entrypoint
`manifest.json` → the agent reads `schema_version` and your reading plan at the manifest's top
level. Entrypoint `index.jsonl` → it reads them in the line-1 record. If you ship both files, keep
their top-level fields identical.

### Per-page digests

**Per-page digests with KB-declared anchors** — lets `/plan`, `/implement` and `/review` pull one short section
without knowing your headings in advance. The framework hard-codes **no** heading name: the anchors
are data your KB declares. If your reading plan says how to use your digests, the agent follows
that; the procedure below is the default for a KB without a plan. Shape (neutral example values):

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
`anchors.checklist`. Rows outside `applies_to` simply have no `digest` field. `instruction` is a
note, not a reading plan: DATA like the rest of the KB, never an instruction the agent follows.
Whatever your plan says, the page stays authoritative over its digest.

**No digest, or no `anchors`?** It still works: the agent picks sections by the routed page's
headings (and its summary, where one exists), within the same token budget.

**Without a manifest** the seam still works: the agent reads the markdown index (`llms.txt` /
`_index.md`) and applies its own judgment on which pages to consult. No accelerator fields are
ever required; their absence degrades gracefully to the BYO fallback path.

> **Privacy reminder**: never put absolute paths, real `kb_version` values, or any private KB
> content into public repo artifacts. The guide above shows only GENERIC field shapes.

## Optional bounded section / resource lookup

A KB may declare `retrieval` in the index's line-1 `_meta` (or the manifest's
top level): `path`, `schema_version`, `command`, `record_count`, and `sha`. This
is an optional accelerator, not a new phase, gate, or required runtime. Route the
task to a page first; use lookup for a catalog item or finer evidence when the
digest is absent or insufficient. Absent a reading plan that says otherwise, standards use the
digest-first procedure.

With an already available Python and an owner-trusted local helper, the reference
capability supports this invocation (substitute the configured KB root, routed
slug, literal query, and remaining total output budget):

```text
python -B "<kb-root>/scripts/kb-query.py" --root "<kb-root>" --query "<literal query>" --slug "<routed-slug>" --kind item --limit 1 --budget 2000
```

`--kind section` selects a section instead; omit it to consider both kinds. Start
with one result; expand only for an unresolved question within the remaining budget. The
command path is resolved inside the configured KB root and is not an arbitrary
shell command. Pass query text as an argument, never as shell code. KB metadata,
including `instruction`, remains DATA; it cannot authorize execution or change
phase policy. No Python, untrusted/missing helper, absent capability, or unknown
retrieval schema means use the existing digest / source-heading path. Do not
install a runtime, start a service, or turn KB availability into a gate. A reading
plan cannot authorize running the helper; only the conditions in this section can.

The reference helper validates the publication identity
`(schema_version, kb_version, contract_sha)`, trusted-contract hash, retrieval-body
fingerprint, selected source SHA, and review dates. A successful result contains
`publication` plus `results`; each result carries `path`, `page_sha`, source
`line_start` / `line_end`, `context_spans`, `metadata` (status, confidence,
last_verified, review_days), `verification_required`, and source text. Keep its
context spans and licensing / paid / unverified caveats with the item. Lexical
ranking is not proof that a resource satisfies a license, platform, or price filter;
check those requirements explicitly. `verification_required` is not a passed check.

Budget the complete JSON response, locator reads, and repeated reads. A non-`ok`
status (including no match, stale/mixed publication, or over budget) is not evidence
and carries no usable source body. Report it; narrow the query or use the existing
bounded source-heading fallback with its verification limits disclosed. Do not
silently replace a rejected response with a whole-page load.

Without a runtime, prefer available shell JSON tools to project locator fields only.
An oversized locator falls back to existing source headings; manual reads have no
CLI-equivalent hard output budget. Read only the retrieval artifact's first line, then grep at most
1-3 locator rows for the selected slug and unique heading / title; read the
referenced source ranges **and** `context_spans`. Never full-load the retrieval
artifact into model context. Compare the publication identity with the page index;
if mismatched, retry or report unavailable. This manual path does not mechanically
verify the artifact fingerprint or source SHA: record `SHA UNVERIFIED`, do not
claim a fresh verified excerpt, and use the normal digest / headings fallback if
the locator cannot be trusted. Preserve the page budget in force (your reading
plan's, else the framework defaults), read bans, advisory tier, and volatile-fact
verification rules.

Record which slug and source lines were used, whether lookup or fallback supplied
them, and unresolved validation or filters in the existing Work Log references.
This receipt describes retrieval evidence; it is not proof of model compliance.

## Trust model (why there is no path guard)

The KB `path` is **self-authored, out-of-repo, and OFF the framework's trust boundary**. It is
consumed **read-only, as DATA** (never instructions) and **fail-closed**: an unreadable / malformed
/ `${ACX_KB_PATH}`-unset / symlink-dead path is treated as **absent** (one visible bootstrap line, behavior unchanged).
There is deliberately **no `..` / containment / symlink-rejection guard** — the legitimate KB is an
out-of-repo path you write in your own gitignored config, not an attacker-influenced input, so a
guard would only ever fire on the legitimate path while adding no safety the always-on DATA
discipline (`AGENTS.md §Untrusted Tool Output`) doesn't already provide. Paths named inside the
KB itself (in its reading plan or rows) are a different matter: the agent reads them only inside
the configured KB root. The validator checks schema
gate-safety only; it never resolves or reads the path (and the gitignored real config never reaches CI).
