# Work Log: docs/readme-dedup

| Field | Value |
|---|---|
| Branch | docs/readme-dedup |
| Classification | quick-win |
| Classified by | Claude (Opus 4.8) |
| Frozen | true |
| Created Date | 2026-06-20 |
| Owner | luvseldom (session 2026-06-20T14:05:59+0800) |
| Guardrails Mode | Quick |
| Current Phase | review |
| Checkpoint SHA | 3cf9ca8 |
| Recommended Skills | verification-before-completion (auto) |
| Primary Domain Snapshot | none |

## Session Info
- Agent: Claude (Opus 4.8)
- Session: 2026-06-20T14:05:59+0800
- Platform: Antigravity
- Guardrails loaded: skipped (quick-win)
- Override: none
- Downstream-Capabilities: none

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Reclassification: backlog #86 was tier `tiny-fix`; escalated to `quick-win` — the change is editorial content on the PUBLIC landing page (EN + zh), canary/test-pinned, 2 files → not "no semantic change". Escalation (never silent downgrade) per state_machine.md.
- Scope reduction (honest): #86 had 3 parts. (a) prose de-dup of the "leaked secret/fake tests/skipped phase" triple + (b) the 2× cross-platform mention → DONE conservatively. (c) "unify the workflow + pipeline GIFs onto one example task" → DESCOPED: requires re-rendering binary GIF assets + visual verification that neither agent nor user (no Cursor / can't eyeball GIFs reliably) can confirm — shipping unverifiable binary assets to the public README is unsafe. Left as a reopen-trigger (do when a visual-review path exists).
- FAQ kept intentionally: the FAQ "leaked secret/missing test/skipped review" restatement (README.md ~:189) is LEFT self-contained on purpose — the FAQ exists for answer-engine/SEO extraction (added in #230); self-contained Q&A is the point. De-dup targeted the body redundancy (What-you-get rows), not the SEO surface.

## Task Description
- Backlog #86 (docs/adoption): de-dup README redundancy + (descoped) unify GIFs. Done: trimmed the What-you-get "Machine-enforced backstops" row (it verbatim re-listed the Rules-vs-enforcement table's 3 failure modes) and the "Cross-platform" row (it re-listed the "Works with your agent" table's platforms) — EN (README.md:103,106) + zh parity (README_zh-TW.md:102,105). Each row keeps its distinct point; the canonical tables remain the single detailed source. All canaries preserved.

## Phase Sequence
- bootstrap
- plan
- implement
- review
- test
- ship

## External References
- Canonical sources kept: Rules vs. enforcement table (README ~:73-79) + Works with your agent table (~:152-163). De-dup removed the verbatim restatements in the What-you-get table only.

## Known Risk
- R1 (canary/pins): README is pinned by validate.sh canary (line-8 "governance-first layer for AI coding agents"; zh "用工作流程、交付閘門與工程護欄"; "客製化而不衝突") + tests/ci (docs/INSTALL.md link, pre-commit strings). VERIFIED intact post-edit (grep: EN 2/2, zh 1/1). Note: CI docs-skip SKIPS the pin tests on a docs-only PR → ran them LOCALLY.
- R2 (public face / subjectivity): editorial de-dup on the owner's #262-crafted landing page is judgment-laden; kept conservative (2 rows) + independent review + PR描述 so the owner can eyeball. Rollback = revert PR (cheap).
- Rollback: revert PR (README + README_zh prose only).

## Conflict Resolution
none

## Skill Notes
- verification-before-completion: canary grep + pin tests (local) + validate + independent review as evidence.

## Recommended Skills
- verification-before-completion (auto) — implement, review, ship

## Phase Summary
- bootstrap: classified quick-win (escalated from tiny-fix; public-face editorial). Branch off main 3cf9ca8.
- plan: 2 files (README.md + README_zh-TW.md), 2 rows each (Machine-enforced + Cross-platform de-dup); FAQ kept (SEO); GIF unification descoped. | Confidence: 92% — public-face editorial is subjective; cuts kept conservative + canary-safe + owner-reviewable.
- implement: 4 edits (EN :103,:106 + zh :102,:105) removing verbatim re-lists, keeping each row's distinct point. Canaries grep-verified intact (EN 2/2, zh 1/1). | Confidence: 95% — high
- review: PASS — independent fresh-context reviewer (public-face editorial lens): 6/6 OK (meaning preserved + sharpened; "failure modes above" reference resolves; canaries intact; EN/zh parity faithful + natural; honesty preserved; no regression, exactly 2 rows/file, table syntax intact). "Page is tighter, not weaker." 0 issues. | Confidence: 96% — high
- test: PASS — pin tests `test_pre_commit_hook` + `test_deploy_tiering` → 31 passed locally (CI docs-skip skips them on a docs-only PR); validate.sh fail=2 pre-existing gitignored (CI fail=0). | Confidence: 97% — high
- ship: PASS — gate PASS; Ship History prepended + Update Sequence 75→76; PR pending (end-of-batch backfill). Archival + INDEX deferred to the batched chore. | Confidence: 96% — high

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T14:05:59+0800
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T14:05:59+0800
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T14:05:59+0800
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T14:05:59+0800
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T14:17:11+0800
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T14:17:11+0800

## Evidence
- Files: README.md (2 rows: :103 Machine-enforced + :106 Cross-platform) + docs/README_zh-TW.md (2 rows: :102 + :105). Removed verbatim re-lists; canonical tables retained.
- Canaries grep-verified intact: EN "governance-first layer for AI coding agents" (2) + "docs/INSTALL.md" (2); zh "用工作流程、交付閘門與工程護欄" (1) + "客製化而不衝突" (1).
- Independent fresh-context review: PASS 6/6 (0 issues; "page is tighter, not weaker").
- Pin tests: `pytest test_pre_commit_hook test_deploy_tiering` → 31 passed (507s) locally — CI docs-skip skips these on a docs-only PR, so run locally.
- validate.sh: pass=106 warn=8 fail=2 (2 FAILs pre-existing gitignored work-log hygiene, CI fail=0).
- Rollback: revert PR (README + README_zh prose only).

⚡ ACX
