---
status: draft
title: Scaffold Sidecars Only When the Framework Changed
created: 2026-09-26
source: govern-audit-2026-09-26-downstream-sim (F1, backlog #201)
primary_domain: document-governance
adr: docs/adr/ADR-005-downstream-file-preservation-tiering.md
---

# Scaffold Sidecars Only When the Framework Changed

## Goal

Make a `.acx-incoming` sidecar mean "the framework changed this file; merge it", so the
signal is worth acting on. Today `deploy.sh` writes a sidecar for every locally modified
scaffold-tier file on every deploy, whether or not the framework's version changed since
the adopter's recorded baseline. The live `.agentcortex/context/current_state.md` is
scaffold-tier and always differs from its template once a project uses it, so every update
of every active adopter prints `[SKIP] .agentcortex/context/current_state.md` and the
"merge each *.acx-incoming" block for a template that is byte-identical upstream
(reproduced on upgrades from v1.8.10/20/24/26 and on a no-op redeploy). Agents of both
vendors, asked to follow the block, found nothing to merge. In the same run a no-op
redeploy reported `205 updated` and rewrote the tracked manifest's `deployed_at`, so
`git status` showed a change after an update that changed nothing.

## Acceptance Criteria

- **AC-1**: The manifest baseline of a scaffold file is the framework version last offered
  to the adopter. A file the adopter modified, whose framework source equals that baseline and
  that has no unmerged sidecar, is left untouched: no `.acx-incoming`, no `[SKIP]` line, the
  baseline stays, and the summary counts it as kept. *Verify*: deploy twice from the same
  source with a modified `current_state.md`; the second run writes no sidecar, reports 1 kept.
- **AC-2**: A file the adopter modified gets `.acx-incoming` (`[SKIP]`, counted as skipped)
  when the framework changed it since the baseline, and the offered version becomes the new
  baseline. *Verify*: simulate a framework change by an older recorded baseline.
- **AC-2a**: An offer stays until the adopter deals with it: if the file's sidecar existed
  when the run started (not merged and deleted yet), it is written again. Once deleted, it
  does not come back until the framework changes the file again. *Verify*: redeploy with the
  sidecar present (offered again), delete it, redeploy (kept, no sidecar).
- **AC-3**: The "merge each *.acx-incoming" block prints only when this run wrote at least
  one sidecar. *Verify*: absent in AC-1's run, present in AC-2's.
- **AC-4**: `updated` counts only files this run wrote; a file already identical to the
  framework version is counted as unchanged. *Verify*: a no-op redeploy reports 0 updated.
- **AC-5**: A redeploy of the same framework source over an install with no framework-file
  change leaves `.agentcortex-manifest` byte-identical, including `deployed_at`. *Verify*:
  hash the manifest before and after; `git status --porcelain` shows no manifest change.
- **AC-6**: Branches without a baseline hash (fresh install into existing files;
  pre-manifest or migrated installs) are unchanged on that deploy: they sidecar when content
  differs and record the framework hash. On later deploys AC-2a keeps the offer alive until
  the adopter deletes the sidecar. *Verify*: `test_preexisting_sidecar_file_stays_preserved_across_repeated_deploys`.
- **AC-7**: Core-tier behaviour is unchanged (force-update, `.acx-local` backup for local
  edits). *Verify*: existing core-overwrite tests stay green.
- **AC-8**: ADR-005 is amended: the sidecar condition, its compliance check and the
  "merge paralysis" consequence reflect AC-1..AC-3. *Verify*: the amendment section exists
  and its compliance check matches the tests.

## Non-goals

- No change to which files are core, scaffold or wrapper (ADR-005's classification stands).
- No manifest schema change or versioning; no new manifest field.
- No sidecar merge tooling, and no change to how `.acx-incoming` files are cleaned.
- No change to `deploy.ps1`, which delegates to `deploy.sh`.

## Constraints

- A kept file must never be overwritten; the only change for it is that no sidecar is
  written. The adopter's bytes and the recorded baseline stay as they were.
- The first deploy of this version into an existing install may offer one more sidecar for
  a file whose previous sidecar the adopter left in place; deleting it ends the offer.
- Hash comparisons use the existing EOL-normalized hashes (CR-stripped manifest values,
  per #202), so a CRLF checkout cannot turn "unchanged upstream" into "changed".
- The summary line keeps the `N updated / N skipped / N new / N removed` shape so existing
  readers of it still parse; new counts are appended, not interleaved.

## File Relationship

Amends ADR-005 (docs/adr/ADR-005-downstream-file-preservation-tiering.md). Supersedes the
wording of `docs/specs/downstream-fork-accommodation.md` AC-6 ("a re-deploy after a skill
edit produces `.acx-incoming`"): a re-deploy now offers a sidecar only when the framework
changed the skill or the previous offer is still unmerged. That spec is shipped and frozen,
so it is not edited.

## Domain Decisions

- [DECISION] The baseline records the framework version last offered to the adopter, and
  a sidecar is written only when there is something to merge: the framework changed the
  file since that offer, or the previous offer is still unmerged (its sidecar exists when
  the run starts). Deleting the sidecar is how the adopter says "done". Chosen over "never
  sidecar the live SSoT", which would also hide a real template change (a new SSoT field),
  and over keeping the old baseline after an offer, which made every later deploy offer
  the same change again (review F3).
- [TRADEOFF] An adopter who treated the recurring sidecar as a reminder of their own local
  edit loses that reminder; the kept count in the summary replaces it. A sidecar that
  appears on every update teaches adopters to ignore the one that matters.
- [CONSTRAINT] Deploy output reports what the run did: `updated` means written, and an
  update that changed no framework file leaves the tracked manifest byte-identical.

## ⚡ ACX
