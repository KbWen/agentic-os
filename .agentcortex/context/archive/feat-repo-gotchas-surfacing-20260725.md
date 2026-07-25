# Work Log: feat/repo-gotchas-surfacing

## Header

- Branch: `feat/repo-gotchas-surfacing`
- Classification: `quick-win`
- Classified by: `Claude Opus 5`
- Frozen: `true`
- Created Date: `2026-07-25`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `16278527b9f3fe3c1a0d24b7e2edf1b24b9b07a2`
- Checkpoint SHA: `16278527b9f3fe3c1a0d24b7e2edf1b24b9b07a2`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto), kb-consult (auto, on-match <=1pg)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `131`

---

## Session Info

- Agent: `Claude Opus 5`
- Session: `2026-07-25 (claude-code 2.1.160)`
- Platform: `claude-code`
- Guardrails loaded: `skipped (quick-win)` — TOKEN LEAK BLOCK honored; the governance-path exemption (heading-scoped `§13 Governance Change Norms` read only) is reserved for `/implement`.
- Override: `none` (no `AGENTS.override.md` at project root; `~/.agentcortex/` variant not present)
- Downstream-Capabilities: `.agentcortex/context/private/downstream-capabilities.yaml` (0 skills, subagent_policy=read-only [default, undeclared], knowledge_sources: kb-main->OK [BYO, no kb_version])
- Files Read: `12`

---

## Task Description

Surface this repo's hard-won, incident-derived **gotchas** onto an AI-discoverable in-repo
surface. Today they exist only in one operator's private assistant memory, so Codex, Gemini,
a fresh Claude session, and any downstream adopter/contributor cannot see them. Grounded in
Anthropic's 2026-07-24 guidance ("keep CLAUDE.md lightweight ... spend most of the tokens on
gotchas inside of the codebase"). Also files one backlog item for a systematic
conflicting-directive scan.

**Scope (3 strands)**

- **A+B** (one deliverable): create a repo-gotchas surface + a pointer from the platform
  entry files so the next AI session discovers it without human memory.
- **C** (backlog only): file a conflicting-directive scan item — ADR-011 audited
  *enforcement backing*, never *rules that contradict each other*.

**Phase chain**: `/plan` -> `/implement` -> `/ship` (quick-win: spec + handoff exempt).

**Origin**: user-initiated external research, 2026-07-25.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-25 | classified quick-win; skills matched; context loaded |
| plan | done | 2026-07-25 | 7 steps; measure-first fork on the AGENTS.md pointer |
| implement | done | 2026-07-25 | 6 files; plan steps 3-5 collapsed into 1 after measurement |
| review | skipped | — | optional for quick-win |
| test | skipped | — | optional for quick-win (inline evidence recorded) |
| handoff | skipped | — | exempt (quick-win) |
| ship | done | 2026-07-25 | fast-path IMPLEMENTING -> SHIPPED |

---

## Phase Summary

- bootstrap: classified `quick-win`, 3 skills matched, context loaded. Not `feature` — both
  design questions that would have justified a spec were answered by direct verification here,
  so with no spec and no handoff intended the `[classification-flow]` self-check resolves to
  `quick-win`.

- plan: 7 steps / 6 target files, the surface decision deliberately deferred to a measurement
  rather than a guess. Content sourced from incident-derived traps in this repo's own history;
  the doc authored as reference with zero hard directives. Mode Normal. | Confidence: 88% —
  the one open variable was the `AGENTS.md` token multiplier.

- implement: 6 files (1 new doc, 1 new test, `AGENTS.md` +1 line, backlog +2 rows, 2
  regenerated artifacts). Step 1's measurement **refuted** the plan's R4 premise and collapsed
  steps 3/4/5 into a single edit. The first full CI-equivalent run exposed 4 defects of my own
  — three of them the very traps the new file documents — all fixed and re-verified; the
  other 6 failures were proven pre-existing against a clean-`main` worktree and routed to
  backlog #146. | Confidence: 95% — high.

- ship: PASS on the quick-win fast-path (`IMPLEMENTING -> SHIPPED`). `validate.ps1` pass=116
  warn=5 fail=0 skip=2; `origin/main` at `1627852` with zero drift since branch creation.
  Archived to `.agentcortex/context/archive/feat-repo-gotchas-surfacing-20260725.md`.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-25T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-25T10:30:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-25T12:40:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-25T12:55:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Research | https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models | Anthropic, 2026-07-24 — origin of this task |
| ADR | docs/adr/ADR-011-phase-entry-directive-enforcement.md | Directive census; audited enforcement backing, NOT rule-vs-rule conflict (the gap strand C targets) |
| ADR | docs/adr/ADR-001-governance-friction-tuning.md | D3 token/caching posture; covering ADR per coverage check |
| Test | .agentcortex/tests/test_lifecycle_token_consumption.py:28 | `CLASSIFICATION_BASE_FILES` — the counted-doc allowlist |
| Test | tests/ci/test_directive_count_ratchet.py:51 | ratchet `SURFACES` — the 4 phase-entry surfaces |
| Backlog | docs/specs/_product-backlog.md | strand C lands here; no existing gotchas/onboarding item (dedup grep clean) |

---

## Known Risk

- R1 — diff-size escalation (`>200 lines` / `>2 modules` is a mandatory reverse transition).
  **CLOSED**: doc capped at 124 lines; threshold never approached.
- R2 — net-add on a DELETE-bias repo. **CLOSED**: verified problem + consumer both hold, and
  the file carries zero hard-directive keywords, so it is knowledge rather than rules and
  §13 ADD-Gate tiering does not apply.
- R3 — cross-platform parity. **CLOSED**: one `AGENTS.md` pointer reaches all four entry
  points (CLAUDE/GEMINI via `@import`, Codex directly, Copilot by declared SoT); the three
  inheritance paths are now machine-pinned.
- R4 — lifecycle ceiling headroom (460 tokens). **REFUTED by measurement**: `AGENTS.md` is not
  part of the ceiling sum at all (delta 0 on a 400-char probe). The premise, not just the
  estimate, was wrong.
- R5 — ratchet keywords. **CLOSED**: the pointer line carries none of
  `MUST NOT|MUST|NEVER|PROHIBITED|STRICTLY|Gate FAIL`; `AGENTS.md` baseline 37 unchanged.
- R6 (residual, accepted) — the gotchas file ships downstream as **force-update** core tier
  (ADR-005), so adopters cannot customise it. Framed honestly in the file header rather than
  worked around; a source-only tier was not invented because ADR-005 explicitly rejected
  adding a tier.

---

## Decisions

none

---

## Conflict Resolution

- `karpathy-principles` vs `verification-before-completion`: **compatible** per
  `skill_conflict_matrix.md:17` (behavioral prompts vs procedural gates). No precedence
  needed. No other recommended pair appears in the matrix.

---

## Skill Notes

none

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Conflicting-directive instance found live during this bootstrap (evidence for strand C /
  backlog #145): `bootstrap.md §1` orders a `Last Verified` SSoT write; `AGENTS.md §vNext State
  Model`'s non-ship exception list (`/retro`, `/app-init`, `/adr`) is exhaustive and excludes
  `/bootstrap`. Resolved by AGENTS.md-over-workflows precedence — not written (SSoT stays
  2026-07-22, under the 14-day advisory).
- Plan deviation: steps 3/4/5 collapsed into one edit. Measurement refuted plan risk R4 —
  `AGENTS.md` costs 0 against the 355k ceiling, so one `§References` pointer replaces 3 adapter
  pointers and is the only option reaching Codex (which has no adapter file). The three
  inheritance paths are pinned by `test_platform_entry_inherits_agents_md`.
- §13 net-add justification (required for `.agent/rules/*.md`): `repo-gotchas.md` is a
  conditionally-read reference table, not an instruction surface — zero always-on tokens, zero
  hard-directive keywords, so ADD-Gate tiering does not apply. Precedent:
  `ai-development-pitfalls.md` in the same directory.
- Evidence compaction: this log reached 17.8 KB (> `worklog.max_kb: 12`) because the
  Drift/Evidence prose broke ADR-001 D1 / §5.2b truncation. Compressed in place rather than
  mechanically archived — the root cause was my own verbosity, not log age.
- Research notes surfaced per `bootstrap.md §1 Step 3`: `research-external-repos.md`,
  `research-kb-integration.md`, `research-skill-content-optimization.md` — none resumed
  (separate work units; the nearest, backlog #83, records its own premise as disconfirmed).
- Recovered stale Work Log lock on 2026-07-25T11:32:46.885354+00:00; prior_owner=KbWen; prior_session=2026-07-25T00:00:00Z; reason=stale-time; lock=feat-repo-gotchas-surfacing.lock.json
- Recovered stale Work Log lock on 2026-07-25T14:51:01.647598+00:00; prior_owner=KbWen; prior_session=2026-07-25T00:00:00Z; reason=stale-time; lock=feat-repo-gotchas-surfacing.lock.json

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

- Branch from `main` @ `1627852`. ADR coverage `check_adr_coverage.py` -> exit 0 (covered via
  `AGENTS.md`); no `/adr` prompt.
- Problem proof: ripgrep `gotcha|pitfall|footgun|CRLF|canary` over every loaded surface -> 1
  hit, and it is the generic HN/Reddit-sourced `ai-development-pitfalls.md`. Zero repo-specific
  gotchas existed anywhere an AI loads.
- Ceiling probe: 400-char probe appended to `AGENTS.md` -> aggregate `354540` before AND after,
  **delta 0**; reverted, `git status` clean. Corroborated by the field split
  (`quick-win-single-module` 29,710 total / 24,928 `workflow_tokens`). `AGENTS.md` and
  `CLAUDE.md` sit outside the ceiling; plan risk R4 was simply wrong.
- Guard red/green: pointer removed -> `1 failed, 5 passed`; restored -> `6 passed`. Not a
  permanently-green test.
- KB health §1b: `kb-main` path + `outputs/manifest.json` both exist -> `OK` (BYO, no
  `kb_version`).
- Full CI-equivalent run 1: **`10 failed, 786 passed`** (50m47s). Attribution verified in a
  clean-`main` worktree, not assumed:
  - Mine, fixed (2): stale compact index — `AGENTS.md` is a registry `detail_ref`
    (`trigger-registry.yaml:36`); regenerated, `--check` fresh. Both tests PASS on the
    baseline, which is what proves ownership.
  - Mine, fixed (1): deploy manifest golden — the new file ships as `+core
    .agent/rules/repo-gotchas.md`; `--regen-golden` diff is exactly that one line.
  - Mine, fixed (1): a deployed governance doc referenced `analyze_token_lifecycle.py`, which
    deploy does not ship. Fixed by editing the doc — not by rewording to dodge the regex.
  - Pre-existing (6): reproduce on clean `main` @ `1627852`. Root cause = `cp950` ANSI code
    page vs UTF-8 tool output -> `stdout`/`stderr` arrive `None` -> `TypeError`. Green in CI.
    -> repo-gotchas #13 + backlog #146.
- Targeted re-run after fixes (`tests/ci/` + `tests/guard/` + trigger-metadata + lifecycle —
  every suite the diff reaches): **`1 failed, 679 passed`** (51m37s); the one failure is the
  confirmed pre-existing `cp950` case. Ceiling suite included and green.
- Final artifact shape: gotchas 124 lines (cap 150), 0 hard-directive keywords
  (case-sensitive), 0 `.agentcortex/tools/*.py` references. Backlog data rows 79 -> 81; rows
  144 / 145 / 146 each present exactly once (no CRLF row-merge).
- Security quick-scan: `scan_credentials.py` over the 4 touched files -> exit 0.
- `validate.ps1` after evidence compaction: **pass=116 warn=5 fail=0 skip=2**. The earlier
  `fail=1` was `work log compaction warnings detected` — this log at 17.8 KB over the 12 KB
  cap, i.e. self-inflicted, and fixed by compressing the prose to the §5.2b truncation rule
  rather than by archiving or by touching the validator.
- Scope divergence vs plan: planned `CLAUDE.md` / `GEMINI.md` / `copilot-instructions.md` were
  NOT touched (superseded by the single `AGENTS.md` pointer). Extra beyond plan: 2 regenerated
  artifacts (`trigger-compact-index.json`, `deploy_manifest_golden.txt`) — both mandatory
  consequences of the change, not new scope. `.claude/settings.local.json` was already dirty
  at session start and is NOT part of this change.
- `/doctor` (user-requested, **negative result**): `claude --version` -> `2.1.160`;
  `claude --help` documents `doctor` as the **auto-updater health check**, not the 2026-07-24
  blog's CLAUDE.md/skills rightsizer. `claude -p "/doctor"` ->
  `"/doctor isn't available in this environment."` The rightsizer needs an interactive TUI or
  is absent from 2.1.160. Not run; not assumed.
- Three of the four self-inflicted failures were the exact traps written into the new file
  minutes earlier (#2 deploy wiring, #9 compact index).
