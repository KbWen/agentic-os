# Work Log: chore/v1.7.0-release

## Header

- Branch: `chore/v1.7.0-release`
- Classification: `quick-win`
- Classified by: `claude-opus-4-8`
- Frozen: `2026-06-20`
- Created Date: `2026-06-20`
- Owner: `session-37355664`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Checkpoint SHA: `afe5ddc`
- Recommended Skills: `none`
- Primary Domain Snapshot: `docs/release`
- SSoT Sequence: `81`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-06-20 13:52 UTC`
- Platform: `claude-code`
- Files Read: `0`

---

## Task Description

Cut the **v1.7.0** minor release packaging the since-v1.6.0 merges (headline: the ADR-009 `knowledge_sources` KB-consumption seam, PR #270/#271). Bump version banners, add the CHANGELOG `[1.7.0]` entry + SECURITY supported-versions, prepend the Ship-History ledger entry, and close the new guide's discoverability gap. Tag `v1.7.0` + GitHub release on merge.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-06-20 | state read; v1.6.0→1.7.0; minor (new feature) |
| plan | done | 2026-06-20 | banner inventory (8 files) + CHANGELOG + SECURITY + ledger + INSTALL pointer |
| implement | done | 2026-06-20 | all edits applied; README badges dynamic (no edit) |
| review | n/a | — | quick-win doc-only; self-review + validate |
| test | n/a | — | doc-only release; validators CI-equiv |
| handoff | n/a | — | quick-win exempt |
| ship | in-progress | 2026-06-20 | merge → tag v1.7.0 → GitHub release |

---

## Phase Summary

- **bootstrap/plan**: Classified quick-win (docs/release). Current version v1.6.0 (CITATION/deploy.sh/Ship History) → v1.7.0 (minor: the KB seam is a new feature). Inventoried banner locations via `grep 1.6.0`: CITATION.cff (+date-released), deploy.sh `ACX_VERSION`, TESTING_PROTOCOL EN+zh, AGENT_MODEL_GUIDE EN+zh, antigravity-v5-runtime pointer. README/README_zh-TW badges resolve to dynamic shields.io `github/v/release` → auto-update on the GitHub release, no edit. SECURITY keeps 2 supported minors (1.7.x + 1.6.x; `< 1.5`→`< 1.6`).
- **implement**: 8 banner edits + SECURITY table + CHANGELOG `[1.7.0]` (theme-grouped, PR-cited) + current_state (Last Updated, Update Sequence 80→81, ledger prepend newest-first per #265). Discoverability: the shipped `connecting-a-knowledge-base.md` guide was orphaned from every user-facing index → added one pointer row to `INSTALL.md` "Customizing without conflicts" table.

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T21:40:00+08:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T21:48:00+08:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T21:52:00+08:00
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T21:55:00+08:00

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/knowledge-source-seam.md | shipped feature in this release |
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | headline of v1.7.0 |
| PR | #270, #271 | KB seam + token-budget follow-up (both merged) |

---

## Known Risk

- Auto-merge can land while non-required CI (Structural Tests / Pytest Windows) is red — mitigated by manually confirming CI Structural green on the release PR before merge (the #270 incident lesson).

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

none

---

## Design Reference

none

---

## Observability

none

---

## Resume

none

---

## Evidence

- Banners: `grep -rn '1\.7\.0'` confirms CITATION.cff:7 + deploy.sh:29 + TESTING ×2 + MODEL_GUIDE ×2 + antigravity-v5-runtime:11; no stray `1.6.0` outside the historical Ship-chore-v1.6.0 ledger row.
- SECURITY supported-versions: 1.7.x + 1.6.x = Yes; `< 1.6` = No.
- Release is doc-only → validators CI-equiv fail=0 (local work-log FAILs are gitignored-only).
