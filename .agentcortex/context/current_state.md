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
- **Last Updated**: 2026-05-18
- **Last Verified**: 2026-05-18
- **Update Sequence**: 20
- **ADR Index**:
  - docs/adr/ADR-001-governance-friction-tuning.md — ADR-001: Governance Friction Tuning, accepted 2026-04-23
  - docs/adr/ADR-002-guarded-governance-writes.md — ADR-002: Guarded Governance Writes (lock unification + CI lint + lifecycle frontmatter), accepted 2026-04-25
  - docs/adr/ADR-003-hash-chained-audit-log.md — ADR-003: Hash-Chained Tamper-Evident Audit Log (INDEX.jsonl), proposed 2026-04-25
- **Active Backlog**: docs/specs/_product-backlog.md (40 items; Kind/Labels/Priority columns active 2026-05-06)
- **Spec Index** (project specs at `docs/specs/`):
  - docs/specs/lock-unification.md — Guarded Governance Writes implementation spec, [Shipped 2026-04-25] (ADR-002)
  - docs/specs/ci-security-scanning.md — CI Security Scanning (Semgrep + TruffleHog + dependency audit), [Shipped 2026-05-11] (backlog #20)
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
## Ship History

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

### Ship-claude-modest-antonelli-da2aec-2026-05-07
- Feature shipped: Zero-Python downstream + AGENTS.md trim + deploy-gap fix + skill cleanup (PR #91, quick-win, 4 commits).
  - aec35d6: delete `.claude/hooks/check-{sentinel,precompact}.py`, strip hook wiring from `.claude/settings.json`, replace runtime hook intent with bash/PowerShell-native Work Log Phase Summary audit in `validate.{sh,ps1}`. AGENTS.md 229 → 181 lines (-993 tokens). Deploy `.claude/agents/acx-*.md` (5 shims) + `.claude/settings.json` as scaffold tier in `deploy.sh`.
  - d3d6e67: repair 3 cross-file anchor refs broken by AGENTS.md heading rename (`.agent/config.yaml`, `engineering_guardrails.md` §11 redirect, add `### Skill Activation Triggers` heading).
  - 9c23982: post-review cleanup — move `### Skill Activation Triggers` out of indented numbered list to top-level placement; fix pre-existing `validate.sh:1329` bash quirk (`grep -c` + `|| echo 0` → `0\n0` syntax error); remove `.claude/hooks/__pycache__/` residue.
  - f3d97fc: delete 5 redundant process skills (`executing-plans`, `writing-plans`, `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`); inline content into `implement.md` / `plan.md` / `handoff.md` / `review.md` / `ship.md` workflows as always-on rules. Demote Skill Notes MUST → SHOULD per Lesson L4. Skills 19 → 14, all remaining have at least one of (inlined-content / acx-shim native injection / workflow `IF active` block) — zero pure-honor-system.
- Tests: validate 74 PASS / 0 WARN / 0 FAIL / 2 SKIP (consistent across all 4 commits) + CI 7/7 green (Markdown Links, Deploy Smoke Test, Deploy Smoke Test (No Python), Framework Validation, Framework Validation Python 3.9, Framework Validation Windows, ShellCheck — run 25484303443).
- Commits: `aec35d6`, `d3d6e67`, `9c23982`, `f3d97fc`.
- PR: https://github.com/KbWen/agentic-os/pull/91

### Ship-feat-epic-spec-hierarchy-governance-2026-05-06
- Feature shipped: Label-based cluster grouping system for `_product-backlog.md` — resolves downstream backlog fragmentation.
- Edits:
  - `.agent/workflows/spec-intake.md` — §2b single-feature label & cluster check; §2a Feature Inventory 7-col (Kind/Labels/Priority replace Finding); §8c Reprioritize with P0 push-back; merge-guard backfill on all 3 new cols
  - `.agent/workflows/bootstrap.md` — §5 Active Backlog: Kind/Priority assignment + cluster check with suppression
  - `.agent/workflows/review.md` — Backlog Finding Registration section (review-finding auto-log)
  - `.agent/workflows/hotfix.md` — §5 Evidence: hotfix-spawn systemic issue auto-log
  - `.agent/workflows/routing.md` — Reprioritize trigger phrases + P-tier tiebreaker
  - `.agent/config.yaml` — `cluster:` section (threshold/label-cap/p0-pct/marker-cap/suppression-TTL)
  - `.agentcortex/bin/validate.sh` — backlog schema check + L-1 P0 ratio + L-2 label count + L-3 Kind diversity + L-4 declined markers
  - `.githooks/pre-commit.guard-ssot.sample` — new advisory git hook sample
  - `docs/specs/_product-backlog.md` — Kind/Labels/Priority columns backfilled (merge-guard)
- Tests: validate 81 PASS / 0 WARN / 0 FAIL (sha: 2760428).
- PR: https://github.com/KbWen/agentic-os/pull/89 (feat/epic-spec-hierarchy-governance → main)
- Backlog rows shipped: label-cluster system (framework-level; no row numbers — this is the system that manages rows).

### Ship-feat-optimization-batch2-2026-05-04
- Feature shipped: 4 follow-up quick-wins on `feat/optimization-hooks-2026-05-04` branch (PR #87 same-PR addition).
- Edits:
  - `.agentcortex/bin/validate.{sh,ps1}` — graduated active-work-log threshold: WARN at >8, FAIL at >12 (was WARN-only); plus `ARCHIVE_SIZE_WARN_KB` (default 10 MB) WARN check on `.agentcortex/context/archive/`.
  - `.agentcortex/templates/worklog.md` — optional `Files Read: N` field in `## Session Info` for token-budget instrumentation; `## Evidence` section now references `engineering_guardrails.md §5.2b Evidence Truncation Rule` (3-line success / 10-line failure caps).
- Tests: validate 73 PASS / 7 WARN / 0 FAIL (archive 74 KB, 8/8 active logs).
- Backlog rows shipped: #10, #12, #23, #28. Pending count 20 → 16.
- Commits: `c0f63c3`; merged via `30e6fcc` (PR #87).

*(Older entries archived to `.agentcortex/context/archive/ship-history-2026.md`)*
