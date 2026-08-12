# Work Log: chore/v1.8.18-release

## Header

- Branch: `chore/v1.8.18-release`
- Classification: `quick-win`
- Classified by: `claude-opus-5[1m]`
- Frozen: `2026-08-03`
- Created Date: `2026-08-03`
- Owner: `7d0ae52d-claude-opus-5`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `fad0a5d`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `142`

---

## Session Info

- Agent: `claude-opus-5[1m]`
- Session: `2026-08-03`
- Platform: `claude-code`
- Files Read: `6`

---

## Task Description

Cut release **v1.8.18**, packaging the 2026-08-03 governance-correctness wave (13 commits since `v1.8.17`). Docs-only chore: version banners, CHANGELOG, Ship History entry. No engine, test, or logic change in the cut itself.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-03 | quick-win release chore |
| plan | done | 2026-08-03 | 7 banners + CHANGELOG + Ship History + seq |
| implement | done | 2026-08-03 | banners bumped via byte-level replace (EOL-safe) |
| test | done | 2026-08-03 | 411 passed incl. deploy tiering; validators green |
| ship | in-progress | 2026-08-03 | PR + tag + GitHub Release |

---

## Phase Summary

**release cut** — Version 1.8.17 → 1.8.18 across the canonical 7 banner files, `CITATION.cff` `date-released` → 2026-08-03, CHANGELOG `[1.8.18]`, Ship History entry with the 10-entry rotation (live 10 / archived 129), SSoT sequence 142 → 143. Banners were rewritten at byte level rather than via `Path.write_text`, because earlier this session that call silently converted a whole file to CRLF against its `eol=lf` attribute. Verified with `git ls-files --eol` after the edit.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T10:40:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T10:45:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T10:55:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-03T11:10:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | — |
| ADR | — | — |
| Issue | — | — |
| PR | #379 #381 #383 #373 #369 #371 #375 #376 + 4 ship records | packaged in this release |

---

## Known Risk

- The release is NOT complete at merge: the lightweight `v1.8.18` tag and `gh release create --latest` are manual follow-ups. This step has been forgotten twice historically (the #239 ledger and the v1.8.13 tag), so it is tracked here explicitly and must be confirmed by `git ls-remote --tags` + `gh release view`, not assumed.
- Rollback: revert the release-cut PR. It touches only banners, CHANGELOG, and SSoT — no engine change — so revert is clean. If the tag was already pushed, delete it remotely before re-cutting.

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Local test strategy narrowed this session: the full 838-test sweep is no longer run in the background locally (~40 min of bash/PowerShell/git subprocesses; coincided with a desktop-app termination). Release verification used a targeted 411-test set that includes `test_deploy_tiering.py` in full, since the banner bump touches `deploy.sh`. CI owns the complete sweep.

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

- `bash .agentcortex/bin/validate.sh` → `pass=99 warn=3 fail=0 skip=3`
- `pytest tests/ci/test_deploy_tiering.py tests/guard/ .agentcortex/tests/test_lifecycle_token_consumption.py` → **411 passed** (9:59). `test_deploy_tiering` run in full — the `ACX_VERSION` bump touches `deploy.sh`, so the manifest/tiering contract had to be re-proven rather than assumed.

---

## Evidence

- Banners verified after edit: `deploy.sh:29 ACX_VERSION="1.8.18"`, `TESTING_PROTOCOL{,_zh-TW}.md:1`, `CITATION.cff:7` + `date-released: 2026-08-03`, `AGENT_MODEL_GUIDE{,_zh-TW}.md:1`, `antigravity-v5-runtime.md` framework-version reference — 7/7.
- `git ls-files --eol` after the byte-level rewrite: `deploy.sh` and `CHANGELOG.md` both `w/lf`; `CITATION.cff` `w/crlf` under `attr/text=auto`, i.e. unchanged from its prior state.
- Ship History: live 10 / archived 129; `check_ssot_caps` → `ship history 10/10, spec index 26/30`.
- Downstream isolation re-verified this session with a real `deploy.sh` into an empty target: zero project state shipped (no Work Logs, no `INDEX.jsonl`, no backlog, no ADRs, no `docs/architecture/`; SSoT is the template at `Update Sequence: 0`), while framework fixes do reach it — the new over-fold WARN fires in the deployed copy. Deployed tree self-validates at `pass=86 warn=2 fail=0 skip=5`.
