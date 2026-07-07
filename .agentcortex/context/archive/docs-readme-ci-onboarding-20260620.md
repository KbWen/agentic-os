# Work Log: docs/readme-ci-onboarding

| Field | Value |
|---|---|
| Branch | docs/readme-ci-onboarding |
| Classification | quick-win |
| Classified by | Claude (Opus 4.8) |
| Frozen | true |
| Created Date | 2026-06-20 |
| Owner | luvseldom (session 2026-06-20T10:34:18+0800) |
| Guardrails Mode | Quick |
| Current Phase | ship |
| Checkpoint SHA | 20b8800 |
| Recommended Skills | verification-before-completion (auto), doc-lookup (auto), karpathy-principles (auto) |
| Primary Domain Snapshot | none |

## Session Info
- Agent: Claude (Opus 4.8)
- Session: 2026-06-20T10:34:18+0800
- Platform: Antigravity
- Guardrails loaded: skipped (quick-win) — note: /bootstrap command listed engineering_guardrails.md as a required read and it was read before classification settled; classification is quick-win so future phases use Quick Mode (no re-read). Logged in Drift Log.
- Override: none (no root AGENTS.override.md)
- Downstream-Capabilities: none (no .agentcortex/context/private/downstream-capabilities.yaml)

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: engineering_guardrails.md was read per the /bootstrap command's "Required reads" list before classification resolved to quick-win. Not re-read; future phases use Quick Mode. Recorded for honesty, not a behavioral leak going forward.
- Note: Resumable research note `.agentcortex/context/private/research-skill-content-optimization.md` exists but belongs to backlog #83 (skill/workflow content-optimization), NOT this task. Surfaced, not loaded.
- Skipped: /decide (design fork: docs-only vs deploy-ships-starter-workflow) — resolved decisively to docs-only by 2 independent fresh-context reviewers (Plan + general-purpose, each file:line-verified) + self-verification of deploy.sh:1022-1027 / temp_downstream. Rationale recorded in ## Risks R3 + ## Conflict Resolution.
- Skipped: /research external-references gate — branch-protection facts verified directly via WebFetch of GitHub official docs (recorded in ## External References); no further /research needed.
- SSoT write deviation (ship): Ship History entry + Update Sequence/Last Updated written via Edit tool, NOT guard_context_write.py. Reason: guard `append` mode is O_APPEND (file-end), but Ship History convention is newest-first-at-top (verified: 2026-06-20 entries at top, 2026-06-10 at bottom); guard `replace` would require full-file reconstruction (higher corruption risk than a surgical anchored insert). Ship Guard verified no concurrent current_state.md modification this session (origin/main==HEAD==20b8800). Guard receipt not refreshed → validate WARN acceptable (advisory per guarded-context-writes.md Stage 1).
- Ship sequencing: work-log final archival + INDEX.jsonl (hash-chained) append + lock release DEFERRED to post-merge — avoids polluting the audit chain for an unmerged PR (archival = task-complete signal). PR# in Ship History = "(PR pending)"; backfill after PR open. → DONE: PR #263 opened (https://github.com/KbWen/agentic-os/pull/263); Ship History PR# backfilled via follow-up commit (no force-push).

## Task Description
- Backlog #84 (docs/adoption, quick-win, P2): README→CI onboarding. Show adopters how to wire CI as a *required, non-bypassable* check. The README sells "CI is the floor that can't be skipped" but Quick Start only covers `deploy_brain.sh` install — a final-review persona flagged this as the real conversion leak. Expected shape: a `docs/INSTALL.md` CI-onboarding section + a branch-protection recipe (GitHub required status checks). Dependency "after #262" is satisfied (#262 merged `318d8f2`).
- Phase chain (quick-win): /plan → /implement → /ship (review + test optional when evidence is inline).
- Context Read Receipt:
  - current_state.md → read; Update Sequence 72; Last Verified 2026-06-20; PR #262 Ship entry (lines 98-103) absorbed.
  - Work Log → created (new branch docs/readme-ci-onboarding).
  - Spec Scope → none (no spec file for #84; quick-win needs no new spec; existing README/INSTALL/reference docs are the target surfaces).
- Read Plan: Classification quick-win / Quick Mode. To read at /plan: docs/INSTALL.md (current CI/install content), README.md + README_zh-TW.md (the "CI is the floor" claims + canary lines to preserve), .github/workflows/*.yml (the actual required-check job names to cite accurately). Skipped: specs/archives (Token Leak avoidance for quick-win).

## Phase Sequence
- bootstrap
- plan
- implement
- review
- test
- ship

## External References
- docs/adr/ has ADR-001..ADR-008 (non-empty → quick-win new-project ADR check does not trigger). No covering-ADR check for quick-win.
- Ship History: Ship-docs-readme-revisual-2026-06-20 (PR #262) + Ship-docs-readme-proof-first-overhaul-2026-06-20 (PR #260/#261) — README is intentionally lean; deep content lives in docs/reference.md + docs/INSTALL.md. DO NOT re-bloat README.
- GitHub Docs — "About protected branches" (verified 2026-06-20 via WebFetch): required-check setting = "Require status checks to pass before merging" (+ "Require branches to be up to date"); a check must run ≥1 time before it is selectable by name; non-bypass knob = "Do not allow bypassing the above settings" (applies to admins); GitHub recommends Repository Rulesets as the modern alternative. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Internal grounding for the workflow example: security.yml:136 (`scan_credentials.py --range base...head`, exit-3=WARN) · validate.sh:183 + final exit (no-Python → WARN, exit 1 only when FAIL_COUNT>0) · ci-security-scanning.md:28 (validate.sh AC-8 already WARNs when .github/workflows/ exists without security.yml — a shipped nudge toward CI).

## Known Risk
- README content is pinned in two layers (validator encoding canaries in validate.sh/.ps1 + pytest structural tests in tests/ci/). Editing/relocating README or INSTALL can break a canary or a structural test — must grep tests/ + validators before restructuring. Canaries to preserve: EN line-8 "governance-first layer for AI coding agents"; zh "用工作流程、交付閘門與工程護欄"; parity anchor "客製化而不衝突".
- Factual-claim risk ([spec-factual-claims] Global Lesson): the CI-onboarding doc makes factual claims about GitHub branch-protection / required-status-check behavior. Verify against authoritative GitHub docs (doc-lookup) before freezing wording.
- Honesty boundary (carried from #262/#260): frame CI as the enforced floor adopters opt into via branch protection; do NOT overclaim machine-enforcement covers everything.

## Risks
- R1 (test pins): tests/ci/test_pre_commit_hook.py:152-155 asserts INSTALL.md still contains the exact pre-commit strings; tests/ci/test_deploy_tiering.py:390-391 asserts "Customizing without conflicts" in INSTALL + "docs/INSTALL.md" in README. Mitigation: insert the new section append-only AFTER line 59 (do not relocate the :44-59 pre-commit block); README change is a 1-clause extension of the existing :181 pointer. Verify: run both test files.
- R2 (factual drift): GitHub branch-protection UI click-paths change over time. Mitigation: give the stable setting NAMES + a `gh` example + link the official docs; do not pin screenshots/exact menu trees.
- R3 (first-run-failure of the example): a workflow that runs the framework's own pytest paths would red-X on a fresh deploy (tests/ not shipped). Mitigation: example runs ONLY deployed tools (validate.sh + scan_credentials.py --range) and wraps the adopter test step in `if [ -d tests ]`; no reference to .github/requirements-ci.txt or tests/ci.
- R4 (overclaim): implying CI auto-blocks after deploy, or "unbypassable" unqualified. Mitigation: imperative framing + 3 caveats (opt-in via branch protection; admin override; no-Python→WARN). Keep house line "machine-enforced, not 'the agent can't lie'".
- R5 (locale parity): docs/INSTALL.md is EN-only (no _zh-TW twin exists); the new section adds EN/zh asymmetry. Disposition: consistent with current EN-leads-INSTALL reality; record a follow-up to mirror once a zh INSTALL/README pass is done (ties to backlog #72 zh-TW parity). Not a blocker.
- Rollback: `git checkout main -- docs/INSTALL.md README.md` (or revert the PR). Additive docs only; zero code/behavior surface.

## Conflict Resolution
none (karpathy-principles ↔ verification-before-completion = compatible per skill_conflict_matrix; doc-lookup unlisted = assumed compatible). Design fork (docs-only vs deploy-ships-starter-workflow) was RESOLVED to docs-only by 2 independent fresh-context reviewers + self-verification — see Drift Log; no /decide needed.

## Skill Notes
- verification-before-completion: applies at /implement + /ship — every completion claim needs evidence.
- doc-lookup: verify GitHub Actions required-check + branch-protection mechanics against official docs before documenting (factual-claim safety).
- karpathy-principles: behavioral baseline; light touch (docs task, no code surface).

## Recommended Skills
- verification-before-completion (auto) — phases: implement, ship
- doc-lookup (auto) — phases: implement, review — verify CI/branch-protection facts
- karpathy-principles (auto) — phases: plan, implement, review — behavioral baseline

## Phase Summary
- bootstrap: classified quick-win (docs/adoption, backlog #84); branch docs/readme-ci-onboarding created (HEAD 20b8800); 3 skills matched (no conflicts); context loaded (SSoT seq 72, PR #262 entry); override/downstream/user-prefs all absent (present-only); backlog #84 advanced Pending→In Progress.
- plan: 2 target files (docs/INSTALL.md new "## Turn on the CI floor" section after :59 + README :181 pointer 1-clause). Premise triple-verified (self + 2 independent reviewers, file:line): README sells CI-floor in ~7 places but deploy ships validate.sh + scan_credentials.py and NOT .github/workflows or tests/ → adopter has scanners, no CI. Decision: docs-only (NOT ship-starter-workflow). Honesty framing locked (imperative + 3 caveats). GitHub branch-protection facts WebFetch-verified. Value calibration (honest): MEDIUM — credibility-debt fix backing the README's loudest claim, not the top funnel unlock (earlier-funnel gaps = no first-green-signal on adopter code, #85 Cursor guide). Mode Normal. | Confidence: 95% — high (premise verified 3×, append-only docs, test pins are existence-only)
- implement: 2 files (docs/INSTALL.md +74 = new "## Turn on the CI floor" section, security.yml-named minimal workflow running only deployed tools + branch-protection recipe + 3 honest caveats; README.md :181 pointer +1 clause). Pin tests 30 passed; validate.sh non-work-log checks all PASS (pass=105); secret quick-scan clean. Scope planned 2 = actual 2. | Confidence: 96% — high
- review: PASS — independent fresh-context reviewer (freshness invariant satisfied: diff+AC only, no impl rationale) + my verification; AC1-5 all PROVEN, 5/5 facts verified, AI-dumber check PASS, philosophy aligned; 0 CRITICAL/HIGH; 1 MEDIUM (scan_credentials rc=3 fail-closed) addressed via inline comment; 2 LOW accepted. Security clean (docs, no code). | Confidence: 96% — high
- test: PASS — pin tests 30 passed (final state, post review-comment edit); validate.sh pass=106 warn=8 fail=2 (2 FAIL = pre-existing gitignored work-log artifacts, CI fail=0). Adversarial skipped (quick-win). AC-5 directly re-verified; AC1-4 verified at review. | Confidence: 97% — high
- ship: PASS — gate PASS (worklog/spec=na/state/handoff=na); SSoT Ship History prepended + Update Sequence 72→73 + Last Updated; backlog #84→Shipped. Local commit on feature branch; push/PR awaiting user authorization (public-repo outward action). Archive + INDEX.jsonl + lock release DEFERRED to post-merge. | Confidence: 96% — high
- ship-complete: PR #263 squash-merged to main (2b34ca3); CI green (docs-only: heavy jobs skipped, required checks pass); post-merge archival + INDEX.jsonl append + lock release executed; backlog #84 SHIPPED.

⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T10:34:18+0800
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T10:47:53+0800
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T11:11:26+0800
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T11:24:21+0800
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T11:33:59+0800
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T11:37:12+0800

## Evidence
- Files: docs/INSTALL.md (+74, new "## Turn on the CI floor (required status check)" section), README.md (+1 clause at the docs/INSTALL.md pointer, line ~181). Both tracked; EOL preserved (Edit tool).
- Pin tests: `pytest tests/ci/test_pre_commit_hook.py tests/ci/test_deploy_tiering.py` → 30 passed (377s). README/INSTALL pinned strings intact (AC4/AC5 pre-commit doc strings + fork-guidance parity).
- validate.sh: pass=105 warn=9 fail=2 skip=2. The 2 FAILs = gitignored work-log hygiene (compaction warnings + 1 illegal-gate-progression in a pre-existing log) → CI fail=0 (established local-only pattern; NOT caused by this change's tracked files). All non-work-log checks PASS.
- /test re-run (final state, post review-comment edit): pin tests 30 passed (441s); validate.sh pass=106 warn=8 fail=2 skip=2 — same 2 pre-existing gitignored FAILs (codex-research-main.md bootstrap→bootstrap + compaction), CI fail=0; my work log carries sentinel (PASS). Comment edit + review writes introduced no new failure.
- Secret quick-scan on `git diff`: clean (no AKIA/PEM/ghp_/sk-proj/AIza/xox patterns).
- Rollback: `git checkout main -- docs/INSTALL.md README.md` (additive docs only; zero code/behavior surface).

## Review Feedback
Burden of Proof (quick-win behavioral; independent fresh-context reviewer + my verification, file:line):
| AC | Verdict | Evidence |
|---|---|---|
| AC-1 minimal workflow, only-deployed tools, no-op test, setup-python+fetch-depth:0 | PROVEN | INSTALL.md new section runs validate.sh + scan_credentials.py only; checkout@v4 fetch-depth:0; setup-python@v5; `if [ -d tests ]` no-op. deploy.sh:1022-1027 + temp_downstream confirm no workflows/tests shipped |
| AC-2 branch-protection recipe, accurate names | PROVEN | "Require status checks to pass before merging" + "Do not allow bypassing the above settings" + Rulesets; GitHub docs (WebFetch) confirmed |
| AC-3 honest framing + 3 caveats, no unqualified "unbypassable" | PROVEN | imperative voice; caveats advisory-until-protection / admin-override / no-Python→WARN; "raises the floor, does not make a bypass impossible" |
| AC-4 README ≤1-line pointer, no section/YAML | PROVEN | README pointer (~:181) +1 clause only |
| AC-5 pinned strings preserved | PROVEN | pin tests 30 passed; README still links docs/INSTALL.md; pre-commit strings intact |
Findings: 1 MEDIUM (scan_credentials rc=3 fail-closed divergence from repo CI's TruffleHog-backed soft-pass) → addressed via inline comment at the credential step. 2 LOW (python-version '3.x' floating vs repo 3.12; AC-8 advisory wording) → accepted (template-appropriate / accurate). Security: clean. AI-dumber check: PASS (no always-loaded surface touched; secure YAML, `permissions: contents: read`).
Verdict: PASS / Ready to commit.

## Retro (post-ship)
### Keep
- Full governed flow held: triple-verified premise (self + 2 plan-stage reviewers) + independent fresh-context content /review + honest framing (no overclaim) throughout; docs-only CI-skip worked (heavy jobs skipped, required checks green); pause-before-PR respected the public-action boundary.

### Problem
- ship.md §State Update step 2 says "append the completion record to the bottom of the file under ## Ship History (guard append mode)", but the actual + consistent convention is newest-first-at-TOP (verified: 2026-06-20 entries at top of ## Ship History, 2026-06-10 at bottom). guard append is O_APPEND (file-end) → a literal follower places the newest entry AFTER the oldest, breaking the convention. Practice has silently diverged from the doc for many ships. Worked around this ship via Edit-prepend + Drift Log deviation note.

### Try
- Land a quick-win fixing .agent/workflows/ship.md to match the live convention (prepend semantics) AND record the Global Lesson in the SAME PR (lesson + enforcement together).

## Lessons
- [ship-history-ordering]: ship.md's "append to bottom (guard append)" contradicts the newest-first-at-top convention + guard append's O_APPEND behavior; for ordered SSoT sections, prepend after the section header (guard replace / surgical Edit), not append.

## Global Lessons Candidate (promote WITH the ship.md fix PR — not as an orphan SSoT commit)
- [Category: governance-doc-drift][Severity: MEDIUM][Trigger: ship-history-append-or-ordered-ssot-section] ship.md instructs "append Ship History to the bottom of the file (guard append mode)", but the live convention is newest-first-at-TOP and guard append is O_APPEND (file-end) — a literal follower misplaces the newest entry after the oldest. For ordered SSoT sections, prepend after the section header (guard replace or a surgical anchored Edit), NOT guard append; reconcile ship.md to match. Land the lesson WITH the doc fix (a lesson without the fix is honor-system per the [enforcement] lesson).

## Spec Seeds
- [NEW-FOLLOWUP] Fix `.agent/workflows/ship.md` §State Update step 2: "append to the bottom of the file (append mode)" -> "prepend after the `## Ship History` header (newest-first), via guard replace or a surgical Edit; guard append (O_APPEND) would misplace it". Carry the [governance-doc-drift] Global Lesson in the same PR (quick-win, governance file -> §13 ADD-Gate: the doc fix IS the enforcement). Evidence: this work log's Drift Log + verified file ordering (current_state.md ## Ship History).
- Considered + REJECTED for Global Lessons (DELETE-bias; one-off/reference; already captured in Ship History): AC-8 `security.yml` filename satisfies validate.sh's CI nudge; pause-before-PR "(PR pending)" -> follow-up-commit backfill (no force-push).
