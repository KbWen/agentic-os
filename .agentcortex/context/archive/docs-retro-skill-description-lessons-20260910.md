# Work Log: docs/retro-skill-description-lessons

## Header

- Branch: `docs/retro-skill-description-lessons`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-09-10`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `none`
- Checkpoint SHA: `7c13f5d`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `170`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-09-10T07:36:49Z`
- Platform: `claude-code`
- Guardrails loaded: `§13 only (heading-scoped; governance-path quick-win exemption)`
- Override: `none`

---

## Task Description

`/retro` for the skill-description unit (PR #437). The user corrected me for storing that unit's durable learnings in Claude-private memory, which Codex and Gemini cannot read: move them into the repo's own record system. Two targets: one structured Global Lesson (SSoT, hash-chained, read by every host, reviewed at `/implement`) and one `repo-gotchas §16` paragraph.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-09-10 | quick-win; `.agent/rules/*` edit -> §13 read |
| plan | done | 2026-09-10 | 2 target files, 4 steps |
| implement | done | 2026-09-10 | 1 lesson archived, 1 appended, gotcha §16 extended |
| review | skipped | - | optional for quick-win; not run - stated, not implied |
| ship | done | 2026-09-10 | SSoT Ship History, log archived, INDEX chained |

---

## Phase Summary

- implement: archived `[classification-flow]` via the chain tool (successor re-anchored, bridge record in INDEX.jsonl); appended `[skill-description-cost][HIGH][editing-skill-md]`; extended `repo-gotchas §16` with the host-side consumer. Token aggregate unchanged (354887, delta 0 - measured). | Confidence: 95% - high
- ship: no subagent review was run (optional for quick-win); evidence is the targeted tests, the chain checkers and both validators below.
- plan: archive 1 lesson, append 1, one repo-gotchas paragraph. | Confidence: 93% - high
- bootstrap: quick-win. Global Lessons at cap 20/20 with zero LOW entries; user chose to archive the oldest MEDIUM.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-10T07:36:49Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-10T07:37:10Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-10T07:39:48Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-09-10T07:39:48Z

---

## External References

| Type | Path | Note |
|---|---|---|
| Review | docs/reviews/2026-09-09-cross-model-skill-final-review.md | source of the host-consumer correction (F2) |
| Backlog | docs/specs/_product-backlog.md #199 | the open decision the new lesson points at |

---

## Known Risk

- Archiving a lesson removes it from the always-read registry on every host. Mitigated: the archive tool preserves it in `archive/global-lessons-archive.md` with a hash-chain bridge record, and its content is encoded in `bootstrap.md:25`.
- Rollback: `git revert` the implement commit. The archive tool's chain bridge makes the archive reversible by re-append.

---

## Decisions

### D-1: archive `[classification-flow]` to free the one Global Lessons slot

- **Decision**: archive lesson #1 (`[classification-flow][MEDIUM][prev: GENESIS]`) via `append_lesson.py --archive --index 1`.
- **Reason**: the registry is at cap 20 with no LOW entries, so `/retro`'s LOW-only archival path cannot free a slot. The user chose this option on 2026-09-10. Its content is now encoded as a rule in `bootstrap.md:25` (governance files -> minimum quick-win), so it is redundant as a lesson.
- **Alternatives**: raise the cap in `.agent/config.yaml` (only defers the problem); skip Global Lessons (then #199 would not surface in the `/implement` HIGH-lesson review on any host).

→ local

### D-2: add one lesson, not four

- **Decision**: the new Global Lesson covers only the SKILL.md token cost and #199.
- **Reason**: two of the unit's four record errors violated lessons already in the registry (`[signal-preservation]` for the swallowed exit code, `[audit-verification]` for trusting a reviewer's claim). Adding near-duplicates to a full registry adds length without adding obedience. The other two (shipping before a brief's review boundary, typed timestamps) are recorded durably in the committed review documents and archived Work Logs.

→ local

---

## Conflict Resolution

- karpathy-principles vs verification-before-completion: `compatible` per `.agent/rules/skill_conflict_matrix.md:17`.

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- **Ship History rotation, owed by the previous unit**: `check_ssot_caps.py` reported 12 entries against a cap of 10. The PR #437 ship had already taken it to 11 without rotating - a miss in that unit, not this one. Rotated the oldest 2 (`Ship-chore-release-v1.8.23-2026-08-24`, `Ship-perf-test-durations-shard-balance-88-2026-08-23`) verbatim into `archive/ship-history-2026.md`, newest-archived first; SSoT side through `guard_context_write.py`. Verified byte-identical in the archive; caps now 10/10.
- Gate Fail Reason: N/A
- Token Leak: NO
- Deletion-First (§13) net-add justification for `repo-gotchas.md`: one paragraph that prevents the specific misclaim that invalidated PR #437's handback (a host-consumer conclusion). `repo-gotchas.md` is a conditional read per `AGENTS.md §References`, not an always-loaded surface, and the same change deletes a lesson from the always-read registry.

---

## Evidence

- `check_lesson_chain.py` -> intact after archive (19) and after append (20).
- `analyze_token_lifecycle.py` sum -> 354887 before and after, delta 0.
- `pytest test_repo_gotchas_discoverability.py test_lifecycle_token_consumption.py test_lesson_chain_archival.py` -> 55 passed, exit 0 (read via PIPESTATUS, not through the pipe).
- `repo-gotchas.md` directive-keyword scan -> 0 hits.
- bootstrap: branch from `main` at `7c13f5d` (post-#437 merge); working tree clean before the branch.
