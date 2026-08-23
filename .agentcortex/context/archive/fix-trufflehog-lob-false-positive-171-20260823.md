# Work Log: fix/trufflehog-lob-false-positive-171

## Header

- Branch: `fix/trufflehog-lob-false-positive-171`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `true`
- Created Date: `2026-08-23`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `818007e`
- Checkpoint SHA: `818007e`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `159`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-23 13:00 UTC`
- Platform: `claude-code`
- Guardrails loaded: `§13 (carried from the #178 unit, same session — Read-Once)`; `security_guardrails.md` grepped for `detector|scanner|exclude` → **no matching rule**, so nothing there constrains this change.
- Context carried from this session's #175/#178/#88 units (Read-Once).

---

## Task Description

Backlog **#171**: TruffleHog's Lob detector matches a word boundary, `live` or `test`, an underscore, then **exactly 35** characters from `[a-zA-Z0-9_]` — underscores included — so an ordinary snake_case identifier satisfies it, and its verifier returns **VERIFIED**, which `--only-verified` therefore does not bound.

**Now blocking, not latent**: #88's `.test_durations` carries 897 pytest node ids and made `Secret Detection (TruffleHog)` FAIL on PR #419 with a wall of `Found verified Lob result`. #88 cannot merge until this is resolved.

Implements the row's own recorded preference **(a)**: `--exclude-detectors=lob`, paired with documenting the squash remedy in `repo-gotchas`. Options (b) absorb-the-blocks and (c) upstream-a-bug-report are not taken — (b) is what just cost a merge, and (c) is not a fix for this repo's CI.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-23T13:00:00Z | quick-win; 1 workflow arg + 1 gotchas entry |
| plan | done | 2026-08-23T13:05:00Z | option (a) per #171's own recorded preference |
| implement | done | 2026-08-23T13:12:00Z | workflow arg + gotchas §15 + a scope-guard test |
| review | pending | — | optional for quick-win |
| test | pending | — | optional for quick-win |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-08-23T14:35:00Z | SSoT 159→160; #171 Shipped |

---

## Phase Summary

**bootstrap** — `quick-win`. Two surfaces: `.github/workflows/security.yml` `extra_args`, and a new `## 15` entry in `.agent/rules/repo-gotchas.md`.

**plan** — Take #171's own recorded option (a). (b) absorb-the-blocks is what just cost a merge; (c) upstream bug report is worth doing but fixes nothing here. Scope the narrowing to one detector and make the scope machine-enforced. Confidence: 94% — high.

**implement** — `security.yml` `extra_args` gains `--exclude-detectors=lob` with the reasoning inline; `repo-gotchas` §15 records the rename-does-not-clear and commit-messages-are-in-scope facts; `test_detector_exclusions_stay_scoped_to_lob` added and mutation-verified both ways. Working diff self-checked against the detector regex → 0 matches. Confidence: 95% — high.

**ship** — SSoT 159→160, Ship History rotated (10/10). #171 → Shipped. Unblocks #88 (PR #419), which needs this on main before its own scan can clear.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T13:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T13:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T13:12:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-23T14:35:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #171 | Carries the detector's exact shape, the 35-identifier census, and the recorded preference (a). |
| Backlog | docs/specs/_product-backlog.md #88 | Blocked by this; PR #419 is red on TruffleHog only. |
| CI | .github/workflows/security.yml:118 | `extra_args: --only-verified` — the line being changed. |

---

## Known Risk

- **This narrows a security scanner.** Compensating controls, both pre-existing: the `credential-scan` job (`security.yml`, PR-diff `scan_credentials.py`) stays fully enabled, as does the pre-commit credential floor. Only the **Lob** detector is dropped — a payments/mail API this repo has no integration with. Every other TruffleHog detector keeps running. This is the disposition #171 itself recorded, not a new judgement.
- **Do NOT write a matching identifier anywhere in this change** — not in the gotchas entry, not in the commit message. #171 records that commit *messages* are in scope and that its own squash message had to be reworded. The shape is described in prose only.
- **A follow-up rename or a net-zero add-then-remove does NOT clear an existing finding** — the action walks each commit's diff across the range. Only removing the introducing commit from the range does (squash). This is why #88 needs this landed *before* it can go green, not merely rebased.
- **Deletion-First (§13)**: `repo-gotchas.md` is under `.agent/rules/`. This is a net-add of one entry; justification recorded in the Drift Log.

---

## Decisions

none

---

## Conflict Resolution

Reused from this session's earlier units: `karpathy-principles` vs `verification-before-completion` = compatible.

---

## Skill Notes

- `verification-before-completion` — cached: Scope → Quality → Evidence → Risk → Communication.

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- **§13 net-add justification**: `repo-gotchas.md` gains one entry with no offsetting deletion. The file is an explicitly *conditional* lookup table (its own header: "there is no directive here and nothing to obey"), not an always-loaded directive surface, and the entry documents a trap that has now cost two sessions (PR #402, PR #419). No existing entry covers it.
- Backlog write at bootstrap (#171 → In Progress), now permitted by the AGENTS.md line shipped in #178.

---

## Review Feedback

none

---

## Red Team Findings

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

## Test Gate Results

none

---

## Evidence

- Branch from `818007e` (main, post-#178); tree clean. Lock: `created / missing`.
- Trigger: PR #419 job `Secret Detection (TruffleHog)` → **fail in 9s**, log shows repeated `##[warning]Found verified Lob result` under `extra_args: --only-verified`.

### Mutation verification of the new scope guard (run before trusting its green)

| state | `test_detector_exclusions_stay_scoped_to_lob` |
|---|---|
| clean (`--only-verified --exclude-detectors=lob`) | **42 passed** |
| exclusion broadened to `lob,github` | **1 failed** |
| `--only-verified` removed | **1 failed** |

File restored and byte-compared after the mutation run.

### Self-check against the detector's own pattern

Compiled `(live|test)_[a-zA-Z0-9_]{35}` and ran it over `git diff` → **0 matches**, i.e. this change does not re-instantiate the shape it documents (the failure mode #171 records for its own row).

### FINAL verification (postdates every implement-phase state write)

- Full CI-equivalent suite, no `-m` filter → **897 passed, 1 skipped, exit 0** in 1:16:00. **+1 vs the prior 896 = the new scope test**, a verifiable delta.
- `validate.ps1` → **exit 0** · `pass=118 warn=3 fail=0 skip=2` · unqualified pass.
- `validate.sh` → **exit 0** · `pass=118 warn=4 fail=0 skip=2` · unqualified pass; the 4th WARN is this session's own stale advisory lock (76-minute run vs a 60-minute timeout), the documented limitation in `config.yaml §worklog_lock`.
- `test_security_workflow.py` 41 → **42 passed**.
- Note for #88: its committed `.test_durations` has 897 entries while the suite now has 898 tests. pytest-split count-splits unknown ids, and the new test is sub-second, so the balance impact is nil.
