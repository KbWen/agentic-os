---
status: accepted
date: 2026-06-03
amended: 2026-09-26
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
- **Force-update class** (unconditional overwrite, **no** sidecar — unchanged behavior): `.agent/rules/*`, `.agent/workflows/*`, `.agent/config.yaml`, `.agentcortex/bin/validate.*`, `.agentcortex/bin/deploy.*`, `.antigravity/rules.md`, `codex/rules/*`, `.agentcortex/tools/**`, `.agentcortex/metadata/**`. These are framework invariants; freezing them is governance drift.
- **Reserved namespace (D)**: `custom-*` skill names (`.agent/skills/custom-*/`, `.agents/skills/custom-*/`) are reserved for downstream — the framework guarantees it will **never** ship a skill under that prefix. Net-new `custom-*` skills are already immune (deploy iterates source only); the reservation makes that a published contract so an upstream skill can never later collide with a downstream `custom-*` name. The 14 framework-owned skill names are published in `routing.md` so downstream can avoid collision.

The core-branch code is **unchanged**; only the tier *classification* of skill
paths moves. This reuses the existing scaffold sidecar machinery (`deploy.sh:154-216`)
— minimal change, no new code path (DELETE-bias).

**Compliance check**: after a local edit to `.agent/rules/engineering_guardrails.md`, a re-deploy overwrites it with **no** `.acx-incoming`; after a local edit to a framework-shipped skill, a re-deploy produces a `.acx-incoming`, leaves the original untouched, and increments `COUNT_SKIPPED`; a net-new `custom-*` skill remains untouched because the framework never ships that namespace.

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

### Amendment (2026-09-26): a sidecar is written only when the framework changed the file

A downstream simulation met this ADR's review trigger, a downstream consumer reporting a
preservation surprise (`docs/reviews/2026-09-26-govern-audit-downstream-sim.md` F1; backlog
#201). Every update of every active adopter wrote
`.agentcortex/context/current_state.md.acx-incoming` and printed the merge block, although the
template was byte-identical upstream: the sidecar condition was only "the adopter's copy
differs from the recorded baseline". Agents asked to follow the block found nothing to merge.
Spec: `docs/specs/scaffold-sidecar-on-upstream-change.md`.

- **Sidecar condition (amended).** The manifest baseline of a sidecar-class file is the
  framework version last offered to the adopter. A locally modified file gets
  `.acx-incoming` when the framework changed it since that offer, or when the previous offer
  is still unmerged (its sidecar existed when the run started); the offered version then
  becomes the baseline. Otherwise the adopter's copy is kept, no sidecar is written, and the
  deploy summary counts it as kept. Deleting a sidecar ends that offer until the framework
  changes the file again.
- **Compliance check (amended).** After a local edit to a framework-shipped skill, a
  re-deploy of the same framework version keeps the edit and writes no `.acx-incoming`; a
  deploy of a version that changed that skill writes one and leaves the original untouched;
  the next deploy writes it again while it is still there, and not after it is deleted.
- **Consequence (amended).** Part of the "sidecar merge paralysis" risk above came from
  this ADR itself: a sidecar on every update teaches adopters to ignore the one that
  matters. The merge block now prints only when the run wrote a sidecar.
- **Unchanged.** Which files are sidecar-class and which force-update; the core branch;
  and the branches with no recorded baseline (a fresh install into existing files, a
  pre-manifest migration), which still write a sidecar on any difference, now kept on offer
  until the adopter deletes it.
