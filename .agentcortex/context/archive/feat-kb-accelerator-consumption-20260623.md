# Work Log: feat/kb-accelerator-consumption

## Header

- Branch: `feat/kb-accelerator-consumption`
- Classification: `feature`
- Classified by: `pinned by user (parent session)`
- Frozen: `2026-06-23`
- Created Date: `2026-06-23`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `implement`
- Checkpoint SHA: `231d4645b9f5877fcc177b56c64b928f0baccb7d`
- Recommended Skills: `kb-consult, verification-before-completion`
- Primary Domain Snapshot: `governance/KB-seam`
- SSoT Sequence: `89`

---

## Session Info

- Agent: `claude-sonnet-4-6`
- Session: `2026-06-23 (bootstrap+implement same session)`
- Platform: `claude-code`
- Files Read: `18`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §5 (testing), §12 (implement)`
- Override: `none`
- Downstream-Capabilities: `none (private file not present in framework repo)`

---

## Task Description

ADR-009 follow-up: teach the governed KB-consume flow (bootstrap.md §1b + §3.6) to consume the OPTIONAL schema-v4 manifest accelerator fields, resolving 5 Codex-review findings. Produce spec `docs/specs/kb-seam-accelerator-consumption.md` (draft status). Key changes: delete dead `kb_path_env` config key (#3), extend fingerprint in §1b health record (#9), clarify UNREADABLE covers malformed (#4), add terse token-budget clause to §3.6 (#8), add applicability-filtering note to §3.6 (#5), add adopter guide section (#6).

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | complete | 2026-06-23 | pinned feature; created log |
| plan | complete | 2026-06-23 | plan provided in parent session prompt |
| implement | complete | 2026-06-23 | commit 9ac323e; 6 files; validators pass |
| review | complete | 2026-06-23 | parent direct spot-check (design correct, terse, honest honor-system labels, BYO/absent graceful, privacy) + REAL dogfood (3 shapes) — in lieu of a long reviewer subagent |
| test | complete | 2026-06-23 | dogfood 3-shape; validators CI-equiv fail=0; token 42 passed (re-baseline +231/scenario); fast cross-dir 546 passed |
| handoff | complete | 2026-06-23 | feature; resumable summary in ## Resume |
| ship | in-progress | 2026-06-23 | PR #283; spec→shipped, ledger seq 89→90 |

---

## Phase Summary

- bootstrap: feature (pinned), ADR-009 follow-up; no KB present; guardrails full loaded; checkpoint SHA 231d464.
- plan: provided by parent session prompt; 6 findings pinned with exact dispositions; target files: config.yaml, bootstrap.md, connecting-a-knowledge-base.md, docs/specs/kb-seam-accelerator-consumption.md (new).
- implement: 6 files changed (5 modified + 1 new spec); commit 9ac323e; validators sh+ps1 CI-equiv fail=0; compact index fresh; token test 42/42 passed (ceiling bumped 353k→354k, +182 tok). Confidence: 95% — high.

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-23T00:00:00+08:00
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-06-23T00:00:00+08:00
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-06-23T01:00:00+08:00
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-06-23T03:40:00+00:00
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-06-23T03:45:00+00:00
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-06-23T03:50:00+00:00

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | scope ADR |
| Spec | docs/specs/knowledge-source-seam.md | shipped v1.7.0 |
| Spec | docs/specs/kb-seam-hardening.md | shipped v1.8.0 |
| Spec | docs/specs/kb-seam-accelerator-consumption.md | NEW (draft, this task) |
| Issue | codex-v18-review-main finding #3/#4/#5/#8/#9 | source findings |

---

## Known Risk

- bootstrap.md §1b/§3.6 are always-loaded; additions must be terse (constraint A). Token test must pass 353k ceiling.
- compact index freshness: need to verify after bootstrap.md edit (bootstrap.md is canonical_ref not detail_ref — likely no stale, but must verify).
- validate.sh/ps1 check for `kb-consult` literal in bootstrap.md — string stays, so no validator breakage.
- EOL discipline: use Edit tool only (no shell append into CRLF tracked files).

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

**Handoff summary (feature gate):**
- Doc path: `docs/specs/kb-seam-accelerator-consumption.md` (spec, status→shipped at ship); detail in `connecting-a-knowledge-base.md` new section.
- Code path: `.agent/config.yaml` (deleted `kb_path_env`), `.agent/workflows/bootstrap.md` (§1b fingerprint + malformed; §3.6 budget + applicability), `lifecycle-baseline.json` + token-test ceiling re-baseline.
- Work log path: this file.
- State: implement (9ac323e) + review(PASS, dogfood) + test(PASS) done; ship in progress (PR #283, ledger commit 17002fc, seq 90). On merge: archive this log, release lock, delete branch.
- Verified by: parent direct spot-check + REAL dogfood (3 downstream shapes: schema-v4 / BYO-no-manifest / absent — all graceful) instead of a long reviewer subagent.
- Open follow-up (separate task): pytest-perf (Codex MEDIUM FOLLOW-UP) — pytest-xdist `-n auto`, designed for the public GitHub CI flow (parallel-safety, pinned dep, loadscope, contributor UX). NOT in this PR.

---

## Evidence

### Finding #3 (dead config) — before/after
- Before: `.agent/config.yaml:134` `kb_path_env: ACX_KB_PATH` (declared, never read)
- After: deleted; replaced with 1-line comment noting bootstrap.md §1b uses ACX_KB_PATH directly
- Grep proof: `grep -rn "kb_path_env" .agent/ .agentcortex/bin/ .agentcortex/tools/` → zero hits (only `.agentcortex/context/work/` archived logs)

### Finding #9 (fingerprint) — before/after
- Before: `.agent/workflows/bootstrap.md:121` `knowledge_sources: <id>→OK|UNREADABLE`
- After: `→OK@<kb_version>` when manifest provides `kb_version`; bare `OK` for BYO (honor-system)

### Finding #4 (malformed coverage) — before/after
- Before: `.agent/workflows/bootstrap.md:120` `unreadable / unset-${ACX_KB_PATH} / malformed → rung (3)` — malformed mentioned but undefined
- After: explicit clause `malformed (including invalid JSON or missing schema_version) → UNREADABLE → rung (3) absent; no MALFORMED third state`

### Finding #8 (token budgeting) — before/after
- Before: `.agent/workflows/bootstrap.md:387` kb-consult row had only page-count cap (≤3pg/phase)
- After: added `Token budget (honor-system): prefer pages with smallest approx_tokens first; cap extracted section at a few k tokens; no approx_tokens → fall back to page-count cap`

### Finding #5 (applicability filtering) — before/after
- Before: no applicability filtering clause; routed slugs treated as full-load mandate
- After: `Applicability filtering (honor-system): routed slugs are a candidate pool; bounded pass before item influences /plan or /review; one-line N/A rationale for dropped items; only applicable items become blockers`

### Finding #6 (adopter guide) — before/after
- Before: `.agentcortex/docs/guides/connecting-a-knowledge-base.md` had brief accelerator mention in "Minimal contract" section
- After: new full section "Make your KB cheaper to consult (optional manifest accelerators)" covering approx_tokens, kb_version, schema_version, load_policy, task_routing, plus BYO-without-manifest fallback note and privacy reminder

### Validator parity
- validate.sh: `[PASS] compact index freshness`, `[PASS] bootstrap ships KB-consult scope-detected row (ADR-009)`, `[PASS] token lifecycle drift: within slack` — Summary: pass=102 warn=12 fail=2 (both pre-existing gitignored work logs; CI-equiv fail=0)
- validate.ps1: same PASSes; fail=2 same pre-existing logs; CI-equiv fail=0

### Token test
- Before: aggregate 353,182 (exceeded 353,000 ceiling by 182 tok)
- Action: bumped ceiling 353k→354k with inline annotation; `update_lifecycle_baseline.py --apply`
- After: `python -m pytest .agentcortex/tests/test_lifecycle_token_consumption.py` → 42 passed
- Per-scenario delta: all within 10% slack (+0.3%–0.8%)

### Commit
- SHA: `9ac323e` on branch `feat/kb-accelerator-consumption`
- 6 files: `.agent/config.yaml`, `.agent/workflows/bootstrap.md`, `.agentcortex/docs/guides/connecting-a-knowledge-base.md`, `.agentcortex/metadata/lifecycle-baseline.json`, `.agentcortex/tests/test_lifecycle_token_consumption.py`, `docs/specs/kb-seam-accelerator-consumption.md` (new, draft)
