---
status: accepted
date: 2026-06-03
classification: architecture-change
primary_domain: document-governance
deciders: "@kbwen + Claude Opus 4.8 + multi-expert workflow (3 rounds, 20+ agents; B-scope safety analyst + scenario-coverage analyst)"
applies_to:
  - ".agentcortex/bin/deploy.sh"
  - ".agentcortex/bin/deploy.ps1"
  - ".agent/workflows/routing.md"
  - "tests/ci/**"
  - "tests/deploy/**"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When a framework file legitimately moves between the force-update and sidecar scope classes, OR when a downstream consumer reports a preservation surprise"
  supersedes: none
  superseded_by: none
---

# ADR-005: Downstream File-Preservation Tiering

## Context

`deploy.sh` preserves user edits to **scaffold**-tier files (writes a
`<file>.acx-incoming` sidecar instead of overwriting) but **silently overwrites
core**-tier files unconditionally.

### Evidence (Verified)

- `deploy.sh:74-96` `get_tier()`: `wrapper`/`scaffold` are explicit lists; **everything else falls through to `core`** (`*) echo "core"`, line 94).
- `deploy.sh:149-153` (core branch): unconditional `cp` — no hash check, no sidecar.
- `deploy.sh:154-216` (scaffold branch): on manifest-hash mismatch, writes `.acx-incoming` and SKIPs (the reusable mechanism; PR #101 already extended it to a no-manifest branch).
- The 14 framework skills under `.agent/skills/<name>/` are deployed via the `*`→core fallback, so a user who edits a framework skill (e.g. `api-design`) loses it silently on next deploy. This is **R1**, the confirmed top downstream defect — four independent expert lenses surfaced it.

A naive fix — "sidecar **all** core" (the literal first instinct) — is **unsafe**.
`.agent/rules/*`, `.agent/workflows/*`, `validate.*`, the platform entry files,
and runtime `tools/` are **framework-authoritative**: they MUST keep receiving
governance and security updates. If a user merely reformats a workflow, an
all-core sidecar would freeze it on the old version and **silently stop
delivering security fixes** — a governance-drift failure that is *invisible*
(passes audit, is actually non-compliant), and therefore worse than R1 (which is
at least *visible* — the user notices their edit vanished). This directly
trips Global Lesson `[scope-expansion][HIGH]`.

## Decision

**Reclassify the skill directories from core to the sidecar (scaffold-equivalent)
class; keep all framework-authoritative paths force-update.** Concretely, in
`get_tier()`:

- **Sidecar class** (manifest-mismatch → `.acx-incoming`, SKIP, never silent overwrite): `.agent/skills/**` and `.agents/skills/**`. Skills are *advisory instruction extensions* (they "CANNOT bypass gates" per AGENTS.md §Skill Safety), so a frozen skill costs only missed guidance improvements — and the loss is **visible** via the sidecar + warning. Unmodified skills still force-update normally (scaffold updates when the manifest hash matches).
- **Force-update class** (always receives the framework version, **no** `.acx-incoming` sidecar; a differing local version is first backed up to `.acx-local` — see Amendment 2026-10-05): `.agent/rules/*`, `.agent/workflows/*`, `.agent/config.yaml`, `.agentcortex/bin/validate.*`, `.agentcortex/bin/deploy.*`, `.antigravity/rules.md`, `codex/rules/*`, `.agentcortex/tools/**`, `.agentcortex/metadata/**`. These are framework invariants; freezing them is governance drift.
- **Reserved namespace (D)**: `custom-*` skill names (`.agent/skills/custom-*/`, `.agents/skills/custom-*/`) are reserved for downstream — the framework guarantees it will **never** ship a skill under that prefix. Net-new `custom-*` skills are already immune (deploy iterates source only); the reservation makes that a published contract so an upstream skill can never later collide with a downstream `custom-*` name. The 14 framework-owned skill names are published in `routing.md` so downstream can avoid collision.

The core-branch code is **unchanged**; only the tier *classification* of skill
paths moves. This reuses the existing scaffold sidecar machinery (`deploy.sh:154-216`)
— minimal change, no new code path (DELETE-bias).

**Compliance check**: after a local edit to `.agent/rules/engineering_guardrails.md`, a re-deploy overwrites it with **no** `.acx-incoming` and keeps the edit in `.acx-local`; after a local edit to a framework-shipped skill, a re-deploy produces a `.acx-incoming`, leaves the original untouched, and increments `COUNT_SKIPPED`; a net-new `custom-*` skill remains untouched because the framework never ships that namespace.

> **🚩 DEVIATION FROM USER'S LITERAL DIRECTIVE (surface for confirmation).** The
> user chose "extend sidecar to **all** core tier". This ADR narrows that to
> "skills sidecar; framework-authoritative core stays force-update" on the
> governance-drift safety argument above (which also honours the user's own
> "don't break the flow" constraint — all-core *would* break the update flow for
> governance files). User confirmed this narrower scope before implementation;
> the decision is now accepted and shipped in the PR.

## Alternatives Considered

- **Sidecar all core** (user's literal directive). Rejected: governance drift on rules/workflows/validate (see Context).
- **Force-update the 14 framework skills too; only `custom-*` sidecars** (a stricter expert variant). Rejected: it does **not** fix R1 in code (editing `api-design` would still be silently overwritten), relying purely on the "copy to `custom-*`" discipline. Treating *all* skills as sidecar fixes R1 directly while staying safe (skills are not gate-critical), and is simpler (no framework-vs-custom partition inside the skills dir).
- **A new "preserve" tier between core and scaffold.** Rejected: adds a concept where a tier reclassification suffices (DELETE-bias).

## Consequences

**Positive**: R1 closed — editing any skill now surfaces a visible `.acx-incoming` instead of silent loss. Governance files keep force-updating, so security/governance fixes always land (no drift). `custom-*` becomes a stable downstream contract. Net code change is a one-place tier reclassification + tests.

**Negative / accepted**: a user who edits a framework skill and ignores the sidecar will miss framework skill improvements (acceptable — visible, and skills are advisory). A new low-severity risk: **sidecar merge paralysis** (user never merges `.acx-incoming`); mitigated by the existing deploy summary warning, optionally a future `/handoff` advisory (deferred — no verified consumer yet).

**Out of scope (honest boundaries)**: shared-SSoT/Work-Log contamination in submodule/monorepo adoption; manifest schema-versioning and tier-history (structural manifest weaknesses, independent of this decision).

## Amendment 2026-10-05: core files are backed up before they are replaced

Spec: `docs/specs/brownfield-first-install-preservation.md` (backlog #188). The Context above describes the core branch as of 2026-06-03; it no longer overwrites silently.

- **Update** (manifest present; shipped earlier under #173): a core file that differs from its manifest baseline and from the framework version is copied to `<path>.acx-local`, then force-updated, with an `[OVERWRITE]` line.
- **First install** (no manifest; new): a pre-existing core file whose CRLF-normalized hash differs from the framework version is copied byte-for-byte to `<path>.acx-local` before the copy policy runs. The run names the path and its backup and counts it in the existing overwrite summary. Equal or EOL-only-different files are left alone. If the backup cannot be written, the deploy exits nonzero before replacing that file and publishes no manifest; files already written earlier in the run are not rolled back.
- `.acx-local` keeps one generation, the latest version that was replaced; a later collision refreshes it. The backup is written whatever `CP_FLAG` says; when `CP_FLAG` (`-n`, or a declined `-i`) keeps the live file, that first-install run prints `[KEPT]` instead of reporting an overwrite. The manifest still records the upstream hash, so a later update treats the kept file as locally modified; under `-n` the update branch then reports an overwrite it did not perform (pre-existing, tracked in the backlog).
- Core files never get `.acx-incoming`; scaffold and wrapper files keep the `.acx-incoming` behavior above. The tiers and the force-update invariant are unchanged.
