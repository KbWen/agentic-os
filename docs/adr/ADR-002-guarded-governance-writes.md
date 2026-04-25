---
status: proposed
date: 2026-04-25
classification: architecture-change
primary_domain: document-governance
deciders: "@kbwen + Claude Opus 4.7 + 4-expert roundtable (Lock Designer / Doc Lifecycle Architect / Future-Proofing Skeptic / Pragmatist v2)"
applies_to:
  - ".agentcortex/tools/guard_context_write.py"
  - ".agentcortex/tools/lint_governed_writes.py"
  - ".agentcortex/tools/check_lifecycle_frontmatter.py"
  - ".agentcortex/bin/validate.sh"
  - ".agentcortex/bin/validate.ps1"
  - ".agent/config.yaml"
  - ".agentcortex/context/.guard_receipts/**"
  - ".agentcortex/context/.guard_locks/**"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When a new ADR amends or supersedes ADR-002, OR when CI surfaces a recurring failure pattern in guarded writes the ADR did not anticipate"
  supersedes: none
  superseded_by: none
---

# ADR-002: Guarded Governance Writes

## Context

The Phase A governance lifecycle audit (`docs/audit/governance-lifecycle-2026-04-25.md` §0.1) identified three CRITICAL/HIGH structural gaps in how governance files are written:

1. **Vibe-locks** — `guard_context_write.py` provides a real `O_CREAT|O_EXCL` lock (line 119), but `resolve_target` (line 51-58) restricts it to `.agentcortex/context/`. Every other "lock" mentioned in `bootstrap.md §2a` (worklog `.lock.json`), `ship.md §7c` (`domain/<domain>.lock.json`), `ship.md §3` (archive `INDEX.jsonl` append), and `_product-backlog.md` status updates is **plain agent file IO** — `O_CREAT` without `O_EXCL`, no atomicity, TOCTOU windows.
2. **Receipt overwriting** — A single shared `DEFAULT_RECEIPT = .guard_receipt.json` (line 19) loses audit trail when two guarded writes target different files in the same window.
3. **No write enforcement** — Nothing prevents workflow authors from using plain `open()` against governed paths. The current "lock" only protects code that already wanted protection.

A 4-expert roundtable (Lock Designer + Future-Proofing Skeptic + Pragmatist v2 + Doc Lifecycle Architect, captured in audit §0.1–§0.4) converged on a single insight: **the framework trusts three things it should not trust** — agent self-attestation, automatic concurrent-write serialization, and AI's own context-input cleanliness. ADR-002 closes the second of these (concurrency); ADR-003 will close the other two.

### Evidence (Verified)

- `guard_context_write.py` line 119: `os.O_CREAT | os.O_EXCL | os.O_WRONLY` — confirmed real lock
- `guard_context_write.py` line 51-58: `path.relative_to(context_root)` raises on paths outside `.agentcortex/context/` — confirmed scope restriction
- `guard_context_write.py` line 19: `DEFAULT_RECEIPT = Path(".agentcortex/context/.guard_receipt.json")` — confirmed single-file receipt
- `ls .agent/skills/red-team-adversarial` returned text file (not directory) — confirmed dual-platform skill stub design (already documented via DOC-N1 in PR #71)

---

## Decision 1: Generalize `guard_context_write` with policy-driven path scope

### Problem

The path restriction at line 51-58 prevents `guard_context_write.py` from protecting governance files outside `.agentcortex/context/` (AGENTS.md, `.agent/rules/*`, `.agent/workflows/*`, `docs/adr/*`, `docs/architecture/*.log.md`, `docs/specs/_product-backlog.md`). Naively removing the restriction (the audit's first proposal) would allow arbitrary writes via crafted `--path`, defeating the safety property.

### Decision

**Replace the hard-coded path restriction with a policy-driven allow-list configured in `.agent/config.yaml`.**

**Rules:**

- New config block `guard_policy.protected_paths` (list of POSIX-style globs). Default value:
  ```yaml
  guard_policy:
    protected_paths:
      - ".agentcortex/context/**"
      - "AGENTS.md"
      - ".agent/rules/**"
      - ".agent/workflows/**"
      - ".agent/config.yaml"
      - ".agent/skills/**"
      - "docs/adr/**"
      - "docs/architecture/*.log.md"
      - "docs/specs/_product-backlog.md"
    allow_outside_paths: false   # set true ONLY for explicit non-policy targets
    lock_stale_seconds: 900
    receipt_dir: ".agentcortex/context/.guard_receipts"
    per_target_receipts: true
    legacy_receipt_mirror: true   # write to BOTH per-target dir AND legacy path during Phase 1
  ```
- `resolve_target` reads policy at runtime; rejects writes to paths matching no allowed glob unless `allow_outside_paths: true` AND CLI passes `--allow-outside`.
- New CLI flag `--mode {replace,append}` on the `write` subcommand:
  - `replace` (default): existing tempfile + `os.replace` whole-file behavior
  - `append`: requires `expected_sha` to be omitted (strict — programmer error if present); uses `O_WRONLY|O_CREAT|O_APPEND` for kernel-atomic single-line append (covers `INDEX.jsonl`, `.log.md` Domain Doc L2 entries)
- Per-target receipt at `<receipt_dir>/<sha256(rel_posix)[:16]>.json`. Validators read the directory. Legacy `.guard_receipt.json` mirror written during Phase 1 (config-gated for rollback).
- `clear_stale_lock` extended with **liveness check**: read `pid` from lock JSON, verify process exists (POSIX `os.kill(pid, 0)`; Windows `OpenProcess`/`GetExitCodeProcess`); only clear if process is dead OR age > `lock_stale_seconds`.
- `lock_group([paths])` exposed as a public API stub (single-path implementation in this ADR; multi-path semantics deferred to ADR-003 D3 reverse-transition needs). Signature: `lock_group(paths: list[str | Path]) -> ContextManager[None]`.

### Rationale

A config-driven allow-list satisfies all three roundtable constraints:
- **Skeptic** Amendment #1 (Scenario 1 path-traversal escape) — explicit positive list is safer than negative restriction
- **Lock Designer** API (per-target receipts, append mode, liveness) — directly inherited
- **Pragmatist** ergonomics — workflow authors don't learn a new API name; `guard_context_write` keeps its name and CLI surface

### Rejected Alternatives

- **A. Naive restriction removal** — would let `--path /etc/passwd` succeed; rejected for security.
- **B. New `guard_write_any` API alongside legacy** — double maintenance; legacy will rot. Pragmatist correctly flagged the rename as friction. Rejected.
- **C. Plain Python `flock`/`fcntl`** — adds platform branching with no benefit; current `O_EXCL` works on POSIX + Windows (NTFS `CREATE_NEW`). Rejected.

### Affected Files

| File | Change |
|---|---|
| `.agentcortex/tools/guard_context_write.py` | +~150 LOC: policy parsing, append mode, per-target receipts, liveness check, `lock_group` stub |
| `.agent/config.yaml` | +`guard_policy` block (~12 lines) |
| `.agentcortex/docs/guides/guarded-context-writes.md` | Rewritten — new flag docs, migration guide |

---

## Decision 2: CI lint enforces guarded writes for governance paths

### Problem

Decision 1 expands what `guard_context_write` *can* protect, but nothing forces workflow authors to *use* it. The Pragmatist roundtable expert insisted: "Without enforcement, the unification only protects code that already wanted protection — exactly the code that's already safe."

### Decision

**Add `tools/lint_governed_writes.py` invoked by `validate.sh`/`validate.ps1` that fails CI on direct `open()` (or `Set-Content`/`Out-File`/`fs.writeFileSync`) against any path matching `guard_policy.protected_paths`.**

**Rules:**

- Scan tracked source files: `.py`, `.sh`, `.ps1`, `.js`, `.ts`, `.mjs`, `.cjs`. Skip `.md` (markdown literal `open(...)` examples are common false positives).
- Match write patterns:
  - Python: `open(<expr>, 'w'|'a'|'x')`, `pathlib.Path(<expr>).write_text/write_bytes`, `shutil.copyfile/move`
  - Shell: `> <path>`, `>> <path>`, `tee <path>`
  - PowerShell: `Set-Content`, `Out-File`, `Add-Content`
  - JS/TS: `fs.writeFile(Sync)?`, `fs.appendFile(Sync)?`, `fs.createWriteStream`
- Resolve the `<path>` literal against `guard_policy.protected_paths` globs. Variable paths that cannot be statically resolved → emit a WARN (not FAIL) requesting reviewer attention.
- **Exemption marker** — same-line or previous-line comment `# guard-exempt: <one-line reason>` (or `// guard-exempt:` / `<!-- guard-exempt: -->`) suppresses the FAIL for that single occurrence. Linter still records the count of exemptions per file in its report.
- `validate.sh` integration: new `record_result` block calling `python .agentcortex/tools/lint_governed_writes.py --root .` with FAIL → propagates to summary `fail=` count.

### Rationale

Pragmatist Recommendation #1: "Add a CI lint, not a doc." Zero token cost per agent turn, binary enforcement at PR time. Replaces the original audit's idea of writing more rules into AGENTS.md.

### Rejected Alternatives

- **Pre-commit hook only** — bypassed by `--no-verify`. Rejected.
- **Runtime check inside guard tool** — only fires when guard IS called. Doesn't catch the bypass. Rejected.

### Affected Files

| File | Change |
|---|---|
| `.agentcortex/tools/lint_governed_writes.py` | NEW (~80 LOC) |
| `.agentcortex/bin/validate.sh` | +1 `record_result` block (~10 LOC) |
| `.agentcortex/bin/validate.ps1` | mirror addition (~10 LOC) |

---

## Decision 3: `lifecycle:` frontmatter for governance docs

### Problem

The Skeptic roundtable expert identified meta-doc rot: the audit doc and the SOP doc would themselves drift without any owner or review trigger. The Document Creation Gate in `AGENTS.md §Document Lifecycle Governance` enforces *naming* discipline but not *lifecycle* discipline.

### Decision

**Define a `lifecycle:` frontmatter contract for governance docs and validate it in CI.**

**Rules:**

- New frontmatter fields required for files in `docs/audit/`, `docs/guides/governance-*`, `docs/adr/`, `docs/architecture/*.md` (L1):
  ```yaml
  lifecycle:
    owner: <workflow-name or human-handle>     # e.g. "/govern-docs", "@kbwen"
    review_cadence: <quarterly|biannual|annual|on-event>
    review_trigger: <description>              # natural-language event that triggers review
    supersedes: <ADR-id|spec-path|"none">
    superseded_by: <ADR-id|spec-path|"none">
  ```
- L2 Domain Docs (`docs/architecture/*.log.md`) are append-only and exempt (each entry has its own date/branch in-line).
- Specs in `docs/specs/` already have `status: draft|frozen|shipped` lifecycle — add `lifecycle:` is OPTIONAL for specs; required only when shipped (so future readers know if it's still authoritative).
- **Grandfather clause**: files dated before 2026-04-25 (this ADR's date) are warned, not failed. New files MUST.
- `validate.sh` integration: scan target paths, check frontmatter parses + has all 5 fields. Missing/invalid → FAIL for new files; WARN for grandfathered.

### Rationale

Skeptic Amendment #3: "Closes Part B & D in one stroke; ~15 LOC, no friction added to feature work." Solves the policer-of-the-policer question structurally rather than ceremonially.

### Affected Files

| File | Change |
|---|---|
| `.agentcortex/tools/check_lifecycle_frontmatter.py` | NEW (~50 LOC) |
| `.agentcortex/bin/validate.sh` | +1 `record_result` block (~10 LOC) |
| `.agentcortex/bin/validate.ps1` | mirror (~10 LOC) |
| `docs/audit/governance-lifecycle-2026-04-25.md` | retroactively add `lifecycle:` (this is THE audit doc; lead by example) |
| `docs/adr/ADR-002-guarded-governance-writes.md` | this file's frontmatter ALREADY includes `lifecycle:` fields (see top) |
| `AGENTS.md §Document Lifecycle Governance` | +1 paragraph pointer to `docs/guides/governance-doc-lifecycle-matrix.md` |

---

## Consequences

### Positive

- **Vibe-locks become real locks** for all governance file writes; eliminates 6+ documented race conditions (audit NEW-1/2/3, AC-5/6, NEW-7).
- **Per-target receipts** preserve audit trail when concurrent writes hit different files.
- **CI lint** prevents bypass — workflow authors cannot regress to plain `open()` without explicit `guard-exempt:` annotation that future reviewers can question.
- **Lifecycle frontmatter** gives every governance doc a self-described owner + review trigger; closes meta-doc rot.
- **`lock_group` stub** prepares the API surface for ADR-003 D3 reverse-transition multi-file atomicity without forcing premature implementation.

### Negative

- **One-time migration cost** for existing callers (Phase 2): identify every workflow that writes to a now-protected path. Estimate: 4-6 sites (`/ship` SSoT update, `/ship` archive INDEX, `/bootstrap` lock file, `/ship` domain doc, `/spec-intake` backlog updates).
- **Lint false-positive maintenance**: variable paths and dynamic constructions will need `guard-exempt:` markers. First wave estimated at <10 markers across the codebase.
- **Config surface grows**: `.agent/config.yaml` adds 1 new top-level block; downstream forks need to merge.

### Neutral

- **No backward incompatibility**: legacy CLI flags + receipt path continue to work during dual-write Phase 1 (one release).
- **No new dependencies**: implementation uses stdlib only (`os`, `pathlib`, `json`, `time`, `hashlib`, `fnmatch`, `tempfile`, `subprocess` for liveness check).

---

## Implementation Plan

Follows `architecture-change` flow per `engineering_guardrails.md` §10.2:

1. **/spec** — `docs/specs/lock-unification.md` (signed off; this ADR is the contract)
2. **/plan** — Target Files + Steps + Risk + AC Coverage compact block
3. **/implement** — staged in 3 commits matching D1/D2/D3, each with TDD cycles per `test-driven-development` skill
4. **/review** — Burden of Proof per AC; Security Scan; Self-Check; Pragmatist counter-review
5. **/test** — Race tests (2 processes), cross-platform CI matrix (Linux + Windows + macOS), regression for every existing call site
6. **/handoff** — Resume block + Read Map for next agent
7. **/ship** — Conventional Commits release; SSoT update; L2 Domain Doc append (`docs/architecture/document-governance.log.md`); spec → `status: shipped`

## Migration Phases (post-ship)

- **Phase 1** (this ADR's ship): coexistence mode — `guard_context_write` accepts new flags, writes to BOTH new + legacy receipt paths. No behavior change for existing callers.
- **Phase 2** (lowest blast radius first): migrate `/ship` archive `INDEX.jsonl` append → currently no guard, biggest correctness gain. Then `/bootstrap` worklog locks. Then `/ship` Domain Doc L2 lock. Then `/ship` SSoT (already guarded; flag flip only).
- **Phase 3** (one release after Phase 2 stabilizes): drop `legacy_receipt_mirror`, deprecate the legacy DEFAULT_RECEIPT path. Validators key off the new `.guard_receipts/` directory.

## Open Questions Resolved (from Lock Designer §D)

| Q | Decision |
|---|---|
| Receipt structure | per-file `.guard_receipts/<digest>.json` (O(1) by filename for validator) |
| INDEX.jsonl lock granularity | per-file lock + `O_APPEND` (Windows SMB safety) |
| Retry backoff defaults | 50/100/200 ms tight (agent UX); CI overrides via `RetryPolicy` |
| Append + expected_sha | strict — raise on present (catch programmer bugs) |
| Legacy receipt removal | 2 releases (foundation infra) |

## References

- Phase A audit: `docs/audit/governance-lifecycle-2026-04-25.md` §0.1, §0.3, §0.4
- Precedent: `docs/adr/ADR-001-governance-friction-tuning.md` (3-decision discipline)
- Implementation anchors: `.agentcortex/tools/guard_context_write.py` lines 19, 51-58, 72-76, 115-143, 146-158, 161-171
- Domain L1: `docs/architecture/document-governance.md`
- Roundtable transcripts: in-conversation, summarized in audit §0.1–§0.4
- External: [POSIX `O_APPEND` atomicity](https://pubs.opengroup.org/onlinepubs/9699919799/functions/write.html); [Windows `CREATE_NEW`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)

## Domain Decisions

- [DECISION] Replace path-restricted lock with policy-driven allow-list (D1) — preserves safety while expanding scope
- [DECISION] CI lint enforces guard usage at PR time, not at runtime (D2) — zero per-turn token cost
- [DECISION] Lifecycle frontmatter as the meta-governance mechanism (D3) — structural, not ceremonial
- [TRADEOFF] Keep `guard_context_write` name vs rename to `guard_write_any` — keep name to preserve muscle memory, accept that the name now slightly misrepresents scope
- [TRADEOFF] Per-target receipt directory vs append-only JSONL — chose directory for O(1) latest-receipt lookup, accept potential inode pressure at very high volume
- [CONSTRAINT] Stdlib-only Python implementation — no new dependencies
- [CONSTRAINT] Backward compat for one full release via `legacy_receipt_mirror` flag
- [CONSTRAINT] Liveness check MUST work on Windows + POSIX without external libs
