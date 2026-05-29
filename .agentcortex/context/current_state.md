# Project Current State (vNext)

- **Project Intent**: Self-managed Agent OS for AI coding agents — structured governance, workflows, and skills for autonomous development.
- **Core Guardrails**:
  - Correctness first: No claim of completion without evidence.
  - Small & reversible: Prioritize small, reversible changes; avoid unauthorized refactoring.
  - Document-first: Core logic or structural changes require a Spec/ADR first.
  - Handoff gate: Non-`tiny-fix` tasks must produce a traceable handoff summary.
- **System Map**:
  - Global SSoT: `.agentcortex/context/current_state.md`
  - Task Isolation: `.agentcortex/context/work/<worklog-key>.md`
  - Active Work Log Path: derive <worklog-key> from the raw branch name using filesystem-safe normalization before any gate checks.
  - Workflows & Policies: `.agent/workflows/*.md`, `.agent/rules/*.md`
- **Project Name**: (set by /app-init)
- **Last Updated**: 2026-05-29
- **Last Verified**: 2026-05-29
- **Update Sequence**: 24
- **ADR Index**:
  - docs/adr/ADR-001-governance-friction-tuning.md — ADR-001: Governance Friction Tuning, accepted 2026-04-23
  - docs/adr/ADR-002-guarded-governance-writes.md — ADR-002: Guarded Governance Writes (lock unification + CI lint + lifecycle frontmatter), accepted 2026-04-25
  - docs/adr/ADR-003-hash-chained-audit-log.md — ADR-003: Hash-Chained Tamper-Evident Audit Log (INDEX.jsonl), accepted 2026-04-25 (amended 2026-05-29: tail-truncation witness + migrate fail-closed)
- **Active Backlog**: docs/specs/_product-backlog.md (40 items; Kind/Labels/Priority columns active 2026-05-06)
- **Spec Index** (project specs at `docs/specs/`):
  - docs/specs/lock-unification.md — Guarded Governance Writes implementation spec, [Shipped 2026-04-25] (ADR-002)
  - docs/specs/ci-security-scanning.md — CI Security Scanning (Semgrep + TruffleHog + dependency audit), [Shipped 2026-05-11] (backlog #20)
  - docs/specs/audit-chain-tamper-evidence.md — Audit-Chain Tamper-Evidence Hardening (C1 truncation + C2 migrate), [Shipped 2026-05-29] (ADR-003 amendment, backlog #42)
- **Canonical Commands**:
  - `/spec-intake`: Import external specs (from other LLMs, documents, or natural language). Handles large product specs via decomposition. Runs before `/bootstrap`.
  - `/bootstrap`: Task initialization & classification freeze.
  - `/plan`: Define target files, steps, risks, and rollback.
  - `/implement`: Execute implementation only when `IMPLEMENTABLE`.
  - `/review`: Check AC alignment & scope creep.
  - `/test`: Report test coverage via Test Skeleton.
  - `/handoff`: Output resumable state summary (mandatory for non-tiny-fix).
  - `/decide`: Record key decisions with reasoning to prevent cross-session re-derivation.
  - `/test-classify`: Auto-select test depth and evidence format based on task classification.
  - `/ship`: Consolidate evidence and update/archive state.
  - `ask-openrouter`: [OPTIONAL] External model delegation. See `.agent/workflows/ask-openrouter.md`.
  - `codex-cli`: [OPTIONAL] Codex CLI delegation. See `.agent/workflows/codex-cli.md`.
- **References**:
  - `AGENTS.md`
  - `.agent/rules/engineering_guardrails.md`
  - `.agent/rules/state_machine.md`
  - `.agentcortex/docs/CODEX_PLATFORM_GUIDE.md`
  - `.agentcortex/docs/guides/token-governance.md` *(manual-only)*
  - `.agentcortex/docs/guides/context-budget.md` *(manual-only)*

> [!NOTE]
> This file is the Single Source of Truth for global project context only.
> Do not store per-task progress here; write progress to `.agentcortex/context/work/<worklog-key>.md`.

## Global Lessons (AI Error Pattern Registry)
>
> Structured format:
> `- [Category: <tag>][Severity: <HIGH|MEDIUM|LOW>][Trigger: <normalized-trigger>] <lesson>`
>
> `/implement` reviews active HIGH-severity lessons before code changes. `/retro` may append new structured entries via guarded write.

- [Category: classification-flow][Severity: MEDIUM][Trigger: polish-pass-or-audit-batch][prev: GENESIS] When the task is a batch of audit-driven polish edits that touch governance files (AGENTS.md, .agent/rules/*), the governance-file exclusion pushes it to `quick-win` minimum — not automatically `feature`. Classify by the flow you actually intend to run (quick-win skips spec + handoff legitimately); do not silently adopt `feature` label while running the quick-win flow. Self-check at bootstrap: "Am I going to write a spec? Will I run /handoff? If no to both, classification is quick-win."
- [Category: worklog-format][Severity: LOW][Trigger: worklog-creation][prev: 7d331603] Worklog header fields accept EITHER markdown list form (`- Branch: ...`) or table form (`| Branch | ... |`) — both pass `validate.sh` as of 2026-05-12. YAML frontmatter still fails (no `---` block parser). Template at `.agentcortex/templates/worklog.md` uses table form for readability; list form is also valid. Gate Evidence receipts MUST use `|` pipe separators exactly: `- Gate: <phase> | Verdict: PASS | Classification: <tier> | Timestamp: <ISO>` — and MUST NOT be placed inside markdown code fences (fenced receipts are silently masked and not counted).
- [Category: branch-awareness][Severity: LOW][Trigger: session-start-multi-turn-task][prev: 73247dab] Run `git branch --show-current` at the start of any non-trivial task before deriving the worklog-key. The system-prompt gitStatus snapshot is taken once at session start and can become stale if the branch changed externally.
- [Category: windows-install][Severity: MEDIUM][Trigger: windows-cmd-lightweight-install][prev: 285f5c5e] On Windows, installer wrappers should prefer PowerShell or a real Git Bash path over PATH `bash.exe`; the WindowsApps `bash.exe` can be a WSL placeholder and break lightweight downstream installs when no distro is configured.
- [Category: audit-method][Severity: HIGH][Trigger: multi-agent-roundtable-same-vendor][prev: 4faa557a] When using sub-agent "expert roundtable" for adversarial review, ALL sub-agents are the same model with shared training data and shared blind spots. The "diversity of perspective" is theatre. For architecture-level audits or trust-boundary work, MUST include at least one external signal: WebFetch of published external sources, `/ask-openrouter` to a different vendor, OR human review. Confirmed during the 2026-04-25 governance audit when a 4-Claude roundtable agreed on a CRITICAL finding (skill missing on Antigravity path) that turned out to be a false alarm — only spot-verification with `file` and `head` revealed the dual-path stub design was intentional.
- [Category: prioritization][Severity: HIGH][Trigger: audit-with-mixed-severity-findings][prev: 8afe0300] When an audit finds mixed CRITICAL/HIGH/MEDIUM and the agent ships fixes for the easy infrastructure (locks, lint, frontmatter) while deferring CRITICAL structural issues (prompt injection, state-machine reverse transition, honor-system enforcement) to "future ADR", that IS the easy-fix bias pattern. Self-check before ship: "Are all CRITICAL findings fixed OR scheduled with a specific PR # and date?" If still abstract "future work", ship is incomplete. Confirmed: ADR-002 shipped 3 infrastructure decisions while leaving SEC-N1 prompt injection and CC-2 honor-system both unfixed.
- [Category: adr-discipline][Severity: MEDIUM][Trigger: adr-bundling-multiple-decisions][prev: 6cf6a979] Bundling multiple architectural decisions into one ADR (e.g., ADR-002 D2.1+D2.2+D2.3) trades short-term commit count for long-term spec drift. ADR-002's bundled spec accumulated 3 deferred ACs (AC-23/24/25) before ship. Future ADRs: 1 architectural decision per ADR. Multiple ADRs OK and preferred. "Mirror ADR-001's 3-decision discipline" is the wrong precedent — the right unit is the smallest decision that ships independently with its own contract.
- [Category: enforcement][Severity: HIGH][Trigger: must-rule-without-validator][prev: 19c054e7] Every "MUST" rule in AGENTS.md / engineering_guardrails.md that depends on agent self-attestation (Sentinel `⚡ ACX`, Token Leak Drift Log audit receipts, Skill cache hash, "MUST sanitize Work Log") is a honor-system rule and is functionally theatre. Adversary feasibility is 10/10 for these (a single user message can disable any of them). Discipline: every "MUST" = 1 hook OR validator OR test OR external observer. Rules without enforcement should be DELETED rather than left as honor-system theatre. Adding "MUST" without enforcement is anti-help — it creates false confidence the rule is in effect.
- [Category: bootstrap-flow][Severity: HIGH][Trigger: post-first-adr-architecture-change][prev: efbd9e63] `bootstrap §0a` "App Architecture Check" condition `1. No ADR exists: docs/adr/ contains no project-specific ADR.` becomes permanently False once ANY ADR ships. After ADR-001 landed, all subsequent `architecture-change` tasks silently skip the ADR prompt — the very next architecture-change (ADR-002) already triggered this regression but was caught by accident. Fix: replace existence check with frontmatter `applies_to:` glob coverage check. Lesson: rules with date-dependent trigger conditions (e.g., "when X exists" / "when X count == 0") need explicit post-ship validation and decay-aware re-test.
- [Category: governance-proposal][Severity: MEDIUM][Trigger: plan-proposes-must-rule][prev: 7f5a25c3] When /plan proposes adding a MUST rule to AGENTS.md or .agent/rules/, cross-check the [enforcement][HIGH] Global Lesson immediately at plan time — not just at /implement. A MUST rule without a corresponding hook, validator, or test is honor-system theatre regardless of where in the workflow it is caught. Self-check: "What enforces this rule if the AI ignores it?" If the answer is "nothing", delete the rule or add the enforcement first.

- [Category: spec-factual-claims][Severity: MEDIUM][Trigger: domain-decision-tool-behavior-claim][prev: eea362e5] Domain Decisions that make factual claims about tool behavior (e.g., 'no external API call', 'language-agnostic') MUST be verified against tool documentation before the spec is frozen. Factual errors in Domain Decisions survive implementation and review phases because reviewers check AC compliance, not rationale accuracy. Self-check at spec-write: for each [DECISION] that asserts tool behavior, find one authoritative source confirming the claim.
- [Category: scope-expansion][Severity: HIGH][Trigger: procedure-header-scope-change][prev: 95082304] When expanding a procedure's tier scope (e.g., "quick-win only" → "all tiers"), MUST audit every step inside the procedure body for correctness under the new scope BEFORE committing. Changing only the header/trigger misses procedure-body invariants — e.g., a receipt-writing step that was safe for quick-win becomes a governance hole for feature/hotfix. Self-check: for each step N in the procedure, ask "does this step still hold correctly for every new tier I just added?"
- [Category: cross-platform-eol][Severity: HIGH][Trigger: validator-content-compare-or-shell-append][prev: 8e17e112] Windows EOL discipline for governance tooling. (a) Any validate.sh/validate.ps1 check that COMPARES file content (diff, prefix, line-match) MUST CR-normalize both sides first: the working copy is CRLF via git autocrlf while `git show`/committed blobs are LF, so an un-normalized diff false-FAILs every line. bash: pipe through `tr -d '\r'`; PowerShell reads `git show`/Get-Content as string arrays (CR already stripped). Confirmed when the ADR-003 audit-chain witness FAILed on a clean repo and PASSed on a truncated one (inverted) until tr -d added. (b) Do NOT `cat >> file` (LF heredoc) into a CRLF-checked-out TRACKED file — it produces mixed-eol that validate.sh text-integrity flags as FAIL locally (autocrlf still normalizes the committed blob, so CI is unaffected, but local validate goes red). Use the Edit tool or normalize EOL (`tr`) after a shell append.
- [Category: pr-workflow][Severity: MEDIUM][Trigger: stacked-pr-on-unmerged-base][prev: 704be7cc] When a PR is stacked on another unmerged PR's branch, SQUASH-merging the base orphans the stack: git no longer recognizes the base commits as merged, so the child PR's diff re-shows the base changes and squash-merging the child conflicts. Use a MERGE-COMMIT for the base PR (preserves commit identity → child diff stays base-free after retargeting to main), OR rebase the child onto main and force-push. Also: retargeting a PR's base via `gh pr edit --base` does NOT fire a pull_request CI trigger — push a sync commit (merge main in) to make CI run. Confirmed 2026-05-29 shipping stacked PRs #116→#117.
- [Category: audit-verification][Severity: HIGH][Trigger: subagent-deep-audit-finding][prev: ad985879] Same-vendor sub-agent deep-audit findings have a HIGH false-alarm rate — independently verify each by READING THE ACTUAL CODE PATH before committing to a fix. 2026-05-29: of 3 deep findings, C3 (claimed P1 'disjoint-lock lost-update' in guard_context_write) was entirely false (cmd_write holds the outer lock for both modes; the sub-agent saw two lock files but missed the wrapping lock), and 3 of 4 D parity gaps were false (validate.ps1 already had the checks the agent reported missing). Only 1 of D was real. The agents even 'reproduced' the false claims. Verifying first turned a claimed feature (C3 lock unification) into a 2-line docstring no-op and avoided 3 phantom validate.ps1 edits. Reinforces 4faa557a (same-vendor roundtables share blind spots): a sub-agent 'reproduction' is a hypothesis, not evidence — re-trace it.
## Ship History

### Ship-fix-validator-parity-and-audit-closure-2026-05-29
- **Commit `55ed8ea`** (quick-win, backlog #44 Shipped / #43 Cancelled) — Closed the final two 2026-05-29 self-audit items after INDEPENDENT verification.
  - **D (#44, real)**: backfilled the gate-receipt-schema check (Verdict/Classification validation on `- Gate:` receipts, active + archived) into `validate.ps1` — it existed only in `validate.sh`. Verdicts now match across platforms (active PASS, archived WARN:1 on the immutable ship-history archive). The parity sub-agent's other 3 claims (sentinel emoji, spec-template, Project Name, spec-status frontmatter) were FALSE — `validate.ps1` already had parity.
  - **C3 (#43, false alarm → Cancelled)**: the claimed replace/append disjoint-lock lost-update does NOT exist — `cmd_write` wraps both modes in `file_lock(lock_path_for_target)` and the only callers of `atomic_write`/`append_write` are inside that locked block. Added defensive docstrings closing the latent direct-call footgun.
  - Meta: 2 of the 3 deep audit findings (C3 entirely, 3/4 of D) were same-vendor sub-agent false alarms — caught only by reading the actual code path. Recorded as a Global Lesson.
- Verified: `validate.sh` & `validate.ps1` both fail=0 with identical schema verdicts; guard tests 94 passed.

### Ship-feat-audit-chain-tamper-evidence-2026-05-29
- **Commits `d4240f8` + `9c03588`** (feature, backlog #42) — Hardened ADR-003 hash-chained audit log against two verified tamper paths (2026-05-29 self-audit C1+C2). ADR-003 amended proposed→accepted with an honest tamper-evidence boundary.
  - **C1 (tail-truncation)**: the back-linked chain has no head/length anchor, so deleting the most recent entry still validated (reproduced). Added a git append-only **witness** to `validate.sh` + `validate.ps1`: the INDEX.jsonl committed at `merge-base origin/main HEAD` must be a line-prefix of the working copy (CR- + blank-normalized for Windows/parity; WARN-degrades offline; FAIL on truncation/edit of a published entry).
  - **C2 (migrate laundering)**: `append_chain_entry.migrate` re-blessed any mismatch; now fills only genuinely-missing prev_sha and **fails closed** (exit 2, no writes) on an existing-but-mismatched prev_sha — matching ADR-003's documented intent.
  - Design (Work Log D-1/D-2): rejected a forgeable in-repo anchor as false-confidence theatre per the [enforcement][HIGH] Global Lesson; git origin/main is the external append-only witness. Tamper-EVIDENCE not prevention, stated honestly in the ADR.
  - Tests: `tests/guard/test_audit_chain.py` +3 (C2 AC-1/2/3); `tests/ci/test_audit_witness.py` NEW (witness structural + cross-platform parity, AC-4/5/6). 126 passed. Witness sims (both validators): real→PASS, truncate-below-baseline→FAIL, edit-published→FAIL, blank-line→PASS.
  - CRLF bug found & fixed during impl (working copy CRLF vs `git show` LF false-FAILed every line → `tr -d '
'`).
- **Follow-ups still queued** (same audit): #43 guard replace/append lock unification (C3); #44 validate.sh↔validate.ps1 parity backfill (D).
- Stacked on PR #116 (A+B test/CI fix).

### Ship-fix-guard-test-ci-coverage-2026-05-29
- **Commit `8001ef5`** (quick-win) — Framework self-test integrity: restored `tests/guard/` collection + gated it in CI (audit items A+B, 2026-05-29 self-audit).
  - Root cause A: `tests/guard/test_sentinel_hook.py` + `test_precompact_hook.py` `exec_module()` the hook sources `.claude/hooks/check-sentinel.py` / `check-precompact.py`, intentionally removed in `aec35d6` (zero-python-downstream design, documented in `.claude/settings.json`). Missing files raised `FileNotFoundError` at pytest **collection** → aborted the ENTIRE `tests/guard/` collection → all 82 valid governance-tool tests silently never ran.
  - Root cause B: CI (`.github/workflows/validate.yml`) ran only `pytest tests/ci/`, never `tests/guard/` — so the 82 tests (guard_context_write, audit-chain, lint, lifecycle, adr-coverage) were ungated regardless.
  - Fix: deleted the 2 orphaned test files (355 lines; feature deliberately removed) + extended `test-ci-structural` job to `pytest tests/ci/ tests/guard/ -v`.
  - Evidence: pre-fix `pytest tests/guard/` = 2 collection errors / 0 run; post-fix `pytest tests/ci/ tests/guard/` = 114 passed, 0 errors.
- **Follow-ups queued (same self-audit, NOT shipped here)**: C1 audit-chain tail-truncation undetectable (reproduced — `check_chain` has no head/length anchor); C2 `migrate` re-blesses forged history; C3 guard replace/append take disjoint locks → lost-update risk on `current_state.md`; D validate.sh↔validate.ps1 parity gaps (unverified). See backlog #41–#44.

### Ship-brain-quality-sprint-2026-05-26
- **PR #112** (squash `f3b3b81`) — Brain quality batch: set -e hardening, Anti-Rationalization §4.5, AGENTS.md -43% tokens.
  - `validate.sh`: added `-e` flag (`set -euo pipefail`); hardened `run_python_check` for set-e abort; added `|| true` guards to all grep/wc/du/cat pipeline assignments.
  - `engineering_guardrails.md §4.5`: Anti-Rationalization Rule — structural tripwire requiring evidence citation written to Work Log before verdict appears in same response (backlog #15).
  - `AGENTS.md`: 191→98 lines (-43% tokens, backlog #38) — extracted 3 Shared Phase Contracts sub-sections to `.agent/workflows/shared-contracts.md`; Skill Safety items 5-9 clarified.
  - `.agent/workflows/shared-contracts.md`: NEW file; contains Phase-Entry Skill Loading, 5-Gate Verification Before Completion, Phase Output Compression.
  - 10 workflow files bulk-updated: anchors from `AGENTS.md §...` → `shared-contracts.md §...`.
  - `trigger-registry.yaml`, skill stubs (2 files): runtime_anchor updated from AGENTS.md to shared-contracts.md.
  - Tests: CI 11/11 green. validate.sh PASS.
- **PR #113** (squash `9868896`) — Expert review follow-up: validate.sh safety, shared-contracts unconditional, §4.5 tripwire.
  - `validate.sh`: hardened wc/du/cat assignments; `current_state.md` read guarded with `|| { record_result WARN ... }`.
  - `AGENTS.md §Shared Phase Contracts`: strengthened to unconditional load directive (Gate FAIL if skipped); added Read-Once exemption for shared-contracts.md.
  - `engineering_guardrails.md §4.5`: structural tripwire version (write-before-verdict); cross-reference added to `review.md`.
  - `guard_context_write.py`: B2 dangling anchors — regenerated trigger-compact-index.json.
  - Tests: CI 11/11 green.
- **PR #114** (squash `334907c`) — Consensus batch: #43 fix, --list-checks, B19 atomic writes, gate receipt schema.
  - `validate.sh`: FAIL if deprecated workflow files present (new-feature/medium-feature/small-fix); `--list-checks`/`-l` flag; gate receipt schema WARN checks for active+archived work logs.
  - `validate.ps1`: mirrored deprecated-files FAIL check; removed same 3 files from `$requiredFiles`.
  - `guard_context_write.py`: rename-CAS atomic write (`os.replace(tmp, target)`); `cleanup_stale_tmps()` at startup (backlog #19).
  - `.agent/workflows/new-feature.md`, `medium-feature.md`, `small-fix.md`: deleted (closes #43).
  - `_product-backlog.md`: B19 → Shipped 2026-05-26.
  - Tests: CI 11/11 green (including Framework Validation Windows).
- Backlog closed: #15 (Anti-Rationalization), #19 (SSoT atomic writes), #38 (AGENTS.md token-budget pass), #43 (deprecated workflow files).

### Ship-fix-downstream-path-consistency-2026-05-22
- **PR #106** (squash `40d3462`) — Cross-session doc write/read path alignment for zero-Python downstream (quick-win).
  - Archive paths: `/ship` final-archives to dated root `archive/<worklog-key>-<YYYYMMDD>.md` (collision-safe on reused branches like a downstream working only on `main`); `handoff §6` clarified as compaction overflow (`archive/work/`); `bootstrap` recovery breadcrumb resolves the root of `archive/` + resumes multi-person `<owner>-` logs; `deploy.sh` scaffolds `archive/work`.
  - Skill anchor: `systematic-debugging` `runtime_anchor` realigned to `implement.md#Skill Execution Overrides` across stub + `trigger-registry.yaml` + `openai.yaml` mirror.
  - Review mirror: removed dead producer instruction + downstream scaffolding (no downstream consumer; dropped phantom `agentcortex-verify.yml` reference). Upstream-only verify tool + 14 tests left intact.
- Tests: validate 93/6/0; `verify_agent_evidence` 14/14; `deploy.sh bash -n` OK. CI 11/11 green.

### Ship-claude-blissful-jemison-27dfb2-2026-05-18
- **PR #104** — Multi-round adversarial governance audit: validator gate-injection hardening + downstream UX gaps (feature).
  - `validate.sh`/`validate.ps1`: T175–T247 (22 gate-injection scenarios closed) — code-fence bypass, HTML-comment bypass, indented-receipt masking, unclosed-fence masking, multi-section masking, self-reclassification reset abuse (H4), receipts-in-fence diagnostic (T247).
  - `test.md` no-test-runner fallback path hardened: hotfix moved to sign-off-required group (§12.2); Gate 2 exception scoped to quick-win/tiny-fix; fallback step 5 tier-scoped receipt; step 6 scoped to quick-win/tiny-fix only (terminal for feature/hotfix); Drift Log write added to quick-win/tiny-fix trigger; Step 4b Gate-2 exception now satisfiable from both paths.
  - `bootstrap.md §3.7`: feature full-chain removed from `Next:` field (8-line budget breach); chain recorded in Work Log Task Description only.
  - `.codex/INSTALL.md`: bash required on ALL platforms; Windows Git Bash prerequisite explicit; PS1 -ExecutionPolicy Bypass.
  - `validate.sh`/`validate.ps1` M8: archive relative-link depth check; `ship.md §2`: depth-hazard warning.
  - M8 counter overflow fix: switched from `sys.exit(count)` to stdout count read (avoids mod-256 wrap on >255 broken links).
  - 7 Opus adversarial review rounds (rounds 1–7); validate.sh M8 parity-harden (try/except + numeric guard); CHANGELOG completeness; wording fixes.
- Tests: validate 80/4/0. PR: https://github.com/KbWen/agentic-os/pull/104

### Ship-claude-peaceful-aryabhata-fe5644-2026-05-12-pass3
- **PR #103** (squash `e732349`) — README/cross-doc broken-link fix, expert-reviewed (Plan subagent). The framework README is dual-purpose (GitHub face + downstream reference); a multi-angle audit found 6 broken `.md` links (33% of internal links) in the deployed README. Per-link triage:
  - Framework-internal (CONTRIBUTING, LIFECYCLE_BENCHMARK) → absolute GitHub URLs.
  - AGENT_MODEL_GUIDE: already deployed but README path wrong → absolute URL.
  - token-optimization-quickstart: genuinely downstream-needed actionable guide → **added to deploy whitelist** + absolute URL in README. File now ships to `.agentcortex/docs/guides/`.
  - Plus: fixed internal cross-refs inside `token-optimization-quickstart.md` (+ zh-TW) and `NONLINEAR_SCENARIOS.md` (+ zh-TW) that had the same source-vs-deployed mismatch.
- Verified post-merge: fresh downstream deploy → 0 broken relative `.md` links in deployed README (was 6); +2 files deployed (183 total, was 181). validate.sh 77/0/0/2.
- Audit residual: zero known broken-link or path-mismatch issues remaining in deployed scope.

### Ship-claude-peaceful-aryabhata-fe5644-2026-05-12-pass2
- Multi-angle downstream-UX audit pass after #99/#100. 11 scenarios tested across fresh install, update install, legacy v5→v6 upgrade, user-modified scaffold, post-install validators, /app-init flow, workflow cross-refs, Python tool functional, dry-run, first-run UX, and broken-link audit. Three findings surfaced and shipped:
  - **PR #101** (squash `469a2a5`, scaffold-preservation fix in `deploy.sh`) — legacy v5→v6 upgrade silently destroyed user's `.agentcortex/context/current_state.md` content. The migrated file landed at a path the manifest didn't track, hitting a "treat as new" branch that overwrote without sidecar. Fix: in the no-manifest-entry scaffold branch, compare dst hash to src and write `.acx-incoming` sidecar on mismatch (mirroring the existing `!$is_update` branch).
  - **PR #102** (squash `71f7a07`, version + skill-count alignment) — `deploy.sh ACX_VERSION` was 4 patch releases behind (`1.0.0` vs CHANGELOG `1.1.2`); 8 downstream-deployed docs (README badge, AGENT_MODEL_GUIDE, TESTING_PROTOCOL, antigravity-v5-runtime, migration EN+zh-TW, zh-TW README) said `v1.1`; README claimed `17 professional skills` (actual `14` post-f3d97fc consolidation). All bumped to `v1.1.2` / `14`.
- Tests: validate 77 PASS / 0 WARN / 0 FAIL / 2 SKIP (full python). Legacy-upgrade simulation: user content preserved at migrated path; framework template lands at `.acx-incoming`. All 11 audit scenarios pass.
- Remaining flagged (NOT yet shipped, recommended as separate follow-ups):
  - `.agentcortex/docs/README.md` (deployed framework README) has 6 broken internal `.md` links downstream — references to `docs/AGENT_MODEL_GUIDE.md`, `docs/LIFECYCLE_BENCHMARK.md` (+ zh-TW), `docs/guides/token-optimization-quickstart.md` (+ zh-TW), `CONTRIBUTING.md`. Class A (deployed at different path) + Class B (not deployed). Needs link rewrite or deploy-time URL substitution. Medium severity — README is key onboarding doc.

### Ship-claude-peaceful-aryabhata-fe5644-2026-05-12
- Two quick-win PRs merged: downstream guidance correctness pass + companion installer bug fix.
  - **PR #99** (squash `5c282c2`, 2026-05-12T04:19:39Z) — strip phantom `.agentcortex/specs|adr/` "framework template fixtures" claim from Write Path Guard and SSoT template; drop attributions to framework-internal ADR-001/002/003 and Global Lessons L4/L5 from workflows, rules, AGENTS.md, .agent/config.yaml, .agentcortex/tools/*.py docstrings, and validate.{sh,ps1} section header comments; `/app-init` now creates `ADR-001-project-architecture.md` (was hardcoded to `ADR-002`); regenerated `trigger-compact-index.json` for the one content_hash that shifted.
  - **PR #100** (squash `8db2900`, 2026-05-12T04:24:??Z) — `deploy.sh` orphan-ADR recovery: replace prefix-based `ADR-001-*` skip with the same `_framework_adrs` known-filename match already used for `_framework_specs`. Bug surfaced because #99's `/app-init` change made the prefix-match wrongly classify the downstream's own ADR-001 as framework-owned. Verified via 4-scenario sim (framework legacy ADR kept, project ADR-001/002/007 migrated).
- Tests: `validate.sh` 77 PASS / 0 WARN / 0 FAIL / 2 SKIP (full Python); fresh-install downstream sim 72/2/0/3 (full) and 67/2/0/8 (`--no-python`).
- CI: all 11 checks green on both merge commits.
- Audit residual: zero remaining ADR-00X / Lesson L4-L5 references in `.agent/**/*.md`, `AGENTS.md`, `.agent/config.yaml`, `.agentcortex/tools/*.py`, `.agentcortex/bin/validate.{sh,ps1}` (only legitimate match left is `app-init.md` instructing creation of `ADR-001-project-architecture.md`).

### Ship-claude-relaxed-pare-db9f89-2026-05-11-merged
- PR #94 merged to main: squash commit `2467f9ab` (2026-05-11T15:52:08Z).
  - Post-ship CI fixes: `--metrics=off` removed (Semgrep 1.123.0 incompatibility with `--config auto`); semgrep job Python 3.11 (`pkg_resources` missing on 3.12 runner).
  - AC-11 added: `.semgrepignore` existence + exclusions structurally tested; test count 31→32.
  - All 11 CI checks green on merge commit.

### Ship-claude-relaxed-pare-db9f89-2026-05-11-r8
- Feature shipped (continuation r5–r8): CI security scanning governance hardening.
  - TruffleHog SHA-pinned: `47e7b7cd74f578e1e3145d48f669f22fd1330ca6` (was semver `@v3.94.3`)
  - Added `.github/dependabot.yml` (github-actions weekly auto-bump)
  - 31 structural tests (was 26): added `--strict`, `write-all` perms, `test-ci-structural`, SHA regex, bash array, `::warning::` annotation
  - Spec amendments (frozen→shipped): AC-5 SHA req for 3rd-party, AC-8 SKIP 3-state, File Relationship, Accepted Risks, Semgrep factual correction
  - `docs/specs/ci-security-scanning.md`: status → shipped
- Tests: 31 PASS / 0 FAIL + validate 83/0/0/2.
- Commits: `f68a408`→`2ee0fd4`; PR: https://github.com/KbWen/agentic-os/pull/94

### Ship-claude-relaxed-pare-db9f89-2026-05-11
- Feature shipped: CI security scanning pipeline — Semgrep SAST + TruffleHog secret detection + pip-audit dependency audit (feature, backlog #20).
  - `.github/workflows/security.yml`: three parallel jobs, all tools pinned (`semgrep==1.123.0`, `trufflehog@v3.94.3`, `pip-audit==2.10.0`); `contents: read` permissions; no `continue-on-error`; `--config auto` (language-agnostic); dependency-audit `hashFiles` guard.
  - Critical correctness fix in /review: pip-audit `-r $f` per requirements file (without it, audits CI env not project deps).
  - `docs/specs/ci-security-scanning.md`: frozen spec, 10 ACs.
  - `tests/ci/test_security_workflow.py`: 26 structural tests, 4/4 adversarial mutations caught, PyYAML YAML-1.1 `on`-boolean handled.
  - `validate.sh` + `validate.ps1` + `.github/workflows/validate.yml`: security workflow presence check + pytest CI job added.
  - `deploy.sh`: 3 missing runtime tools added to whitelist (`check_adr_coverage.py`, `append_chain_entry.py`, `append_lesson.py`); WARN message genericized.
- Tests: 26 PASS / 0 FAIL (test_security_workflow.py) + validate 83 PASS / 0 WARN / 0 FAIL / 2 SKIP.
- Downstream smoke test: 181 files deployed; 72 PASS / 3 WARN / 0 FAIL / 3 SKIP.
- Commits: `da553fd`→`d9807c0`; PR: https://github.com/KbWen/agentic-os/pull/94

### Ship-claude-reverent-matsumoto-30a74e-2026-05-07
- Feature shipped: Onboarding entry-point unification — three-path branching (greenfield raw idea / brownfield adoption / single concrete task) consistently signaled across `.codex/INSTALL.md`, `README.md`, `docs/README_zh-TW.md` (quick-win, doc-only).
  - Closes the gap where `.codex/INSTALL.md` §3 told downstream LLMs to run `/bootstrap` first regardless of starting point, contradicting the routing-index Ambiguity Rule §1 (multi-feature input → `/spec-intake`).
  - 8 sibling docs audited (PROJECT_EXAMPLES × 2, CODEX_PLATFORM_GUIDE × 2, CLAUDE_PLATFORM_GUIDE, NONLINEAR_SCENARIOS × 2, superpowers-playbook) — all confirmed task-context language, no edit needed.
  - zh-TW §3–§6 renumbered to close the §4 hole created when "從零開始" + "帶入素材" were merged into §3.
- Tests: validate 66 PASS / 0 WARN / 0 FAIL / 10 SKIP.
- Commits: `867e37c`; merged via `cf9b622` (PR #92).

*(Older entries archived to `.agentcortex/context/archive/ship-history-2026.md`)*
