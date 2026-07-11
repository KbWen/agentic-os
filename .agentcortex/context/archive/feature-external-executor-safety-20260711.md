# Work Log: feature/external-executor-safety

## Header

- Branch: `feature/external-executor-safety`
- Classification: `quick-win`
- Classified by: `Claude Opus 4.8 (delegated WP2 implementer)`
- Frozen: `2026-07-11`
- Created Date: `2026-07-11`
- Owner: `wp2-external-executor-safety-session`
- Guardrails Mode: `Full`
- Current Phase: `implement`
- Diff Base SHA: `ba949e4290f829579400e787d36c139bffd792c8`
- Checkpoint SHA: `ba949e4290f829579400e787d36c139bffd792c8`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `119`

---

## Session Info

- Agent: `Claude Opus 4.8`
- Session: `2026-07-11 (WP2 remediation wave)`
- Platform: `claude-code`
- Files Read: `14`

---

## Task Description

WP2 of a 3-package remediation wave from the 2026-07-11 external-executor governance audit (PR #337). Implement three doc-contract fixes for write-capable external executors (Claude CLI / Codex CLI / §8.2 canon): F4 abnormal-exit state reconstruction, F5 baseline capture + dirty-preserving rollback, F6 requested/actual executor provenance + unified pre-flight ordering. Plus rider (two stale GPT-1.0 mentions in claude-cli.md) and a cross-workflow CI content-pin test.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-11 | quick-win; scope = 3 findings + rider + tests |
| plan | done | 2026-07-11 | target files + steps below |
| implement | active | 2026-07-11 | doc edits + CI pin test |
| ship | pending | — | PR (non-draft), no merge |

---

## Plan

**Target Files**:
- `.agent/workflows/claude-cli.md` — F4 (§3/§5 abnormal-exit), F5 (§2 baseline, §3/§5 rollback), F6 (§2 ordering + Requested/Actual + disclose fallback), rider (2x GPT-1.0 -> neutral in §3 step 4 + §5)
- `.agent/workflows/codex-cli.md` — F4, F5 (fix §6 `git checkout -- <file>` blanket revert), F6 (Requested/Actual + install-and-stop already correct for explicit)
- `.agent/rules/engineering_guardrails.md` — §8.2 canon: fold the four invariants in, deletion-funded (net <=0 target within §8.2)
- `tests/ci/test_external_executor_safety.py` — NEW cross-workflow content-pin test (`@pytest.mark.docs_pin`), asserts the 4 contract elements in all 3 docs + negative pin on the old codex blanket-revert line

**Steps**: (1) rewrite §8.2 canon; (2) claude-cli.md pre/post-flight + error table + rider; (3) codex-cli.md pre/post-flight + error table; (4) CI pin test; (5) token before/after; (6) full CI suite + both validators; (7) commit + push + non-draft PR.

**Risk + Rollback**: Docs + one new test file; no engine/logic change. Rollback = revert the PR. Risk: token ceiling (mitigated — none of the 3 docs are in the counted aggregate; verified empirically). Risk: docs_pin collected-count must stay >=4 (adding tests, so it rises).

**AC Coverage** (audit acceptance minimum): abnormal-exit/retry-blocking contract (F4) -> pinned; dirty-worktree preservation (F5) -> pinned + negative regression pin; requested/actual provenance (F6) -> pinned; cross-workflow test covering claude-cli + codex-cli + §8.2 -> the new test iterates all three.

**Mode**: quick-win -> implement -> ship (review/test optional; inline evidence).

---

## Phase Summary

- bootstrap: quick-win; read audit report + 3 target docs + token tooling + test patterns. Verified all 3 findings against files. Confirmed `.agents/workflows/` (plural) vestigial, `.agent/workflows/` (singular) canonical. ⚡ ACX
- implement: edited 3 docs (§8.2 canon + claude-cli.md + codex-cli.md) for F4/F5/F6 + rider (2× GPT-1.0 in claude-cli §3 step 4 + §5); added `tests/ci/test_external_executor_safety.py` (7 docs_pin tests). Full CI-equiv 597 passed; validate.sh + validate.ps1 both pass=114 warn=3 fail=0 skip=2; token aggregate 354,937 unchanged (docs not in counted set). ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T00:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-11T01:30:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Review | docs/reviews/2026-07-11-govern-audit-external-executor.md | Source audit (PR #337, merged) |
| PR | (this branch) | fix(workflows): external-executor safety |

---

## Known Risk

- Token ceiling (355k): empirically none of the 3 edited docs are in the analyzer's counted set (workflow phase files + skill detail_refs only). Aggregate expected unchanged at 354,937. §8.2 still kept near net-neutral per the discipline ask.

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Advisory Work Log lock skipped: sole owner of a fresh uniquely-named branch (zero collision risk); documented per the manual-advisory fallback in bootstrap.md §2a. No `.lock.json` created.
- Rider scope: only the two GPT-1.0 mentions in claude-cli.md §3 step 4 and §5 are replaced (per WP2 instruction "no other cosmetic edits"); the intro-blockquote and §6 mentions are intentionally left untouched to avoid out-of-scope churn.

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

- New test: `python -m pytest tests/ci/test_external_executor_safety.py -q` → `7 passed`.
- Full CI-equiv: `python -m pytest tests/ci tests/guard .agentcortex/tests -m "not slow" -q` → `597 passed, 77 deselected`.
- `bash .agentcortex/bin/validate.sh` → `pass=114 warn=3 fail=0 skip=2` (warns pre-existing eval-coverage advisory).
- `validate.ps1` → `pass=114 warn=3 fail=0 skip=2` (parity).
- Token aggregate before/after: `354,937 → 354,937` (unchanged; analyzer counts phase-workflow files + skill detail_refs only — none of the 3 edited docs qualify; §8.2 +494 chars is uncounted governance prose, kept compressed per discipline).
- docs_pin collected count: `12` (>=4 guard holds).
- F5 negative pin: `Auto-revert via` gone from codex-cli.md.
