# Changelog

## [1.3.0] - 2026-06-03

Consolidated release covering PRs #124–#177 since v1.2.0. Activates the downstream override layer, adds a merge-conflict-marker validator gate, brings the sh/ps1 validators to full count parity, expands governance contract tests, and polishes the public-facing docs.

**Features**
- **Downstream override layer activated + skill-sidecar tiering (#175)**: per-fork/per-user `AGENTS.override.md` is now loaded present-only at session start (MAY narrow/disable directives but cannot relax delivery gates), and `deploy` preserves locally-modified framework skills as visible `.acx-incoming` sidecars instead of overwriting them.
- **Merge-conflict-marker gate (#131)**: `validate.sh` / `validate.ps1` now FAIL on unresolved `<<<<<<<` / `=======` / `>>>>>>>` markers in tracked files.

**Validator & tooling**
- sh↔ps1 full count parity: closed parity gaps F2 + F4, gated the ps1 count-parity test to Windows, aligned `validate.sh` column indices, and removed the em-dash pre-filter (#133).
- Cleared 3 framework-self false-positive WARNs (#170, #171, #172); adopted code-review findings with stronger fixes plus regression tests.

**Governance & tests**
- State-machine transition-graph contract test (#132); classification-escalation + SSoT-heartbeat contract tests (#16).
- `CITATION.cff` correctness + skill count corrected 17→14 (#124); untracked a leaked work log and advanced the SSoT sequence (#125).

**Downstream & Windows**
- Hardened deploy + validation follow-ups for Windows; regenerated the AGENTS.md trigger-compact-index for content-hash drift; tightened downstream ADR tiering coverage; corrected ship-evidence SSoT root-cause notes.

**CI**
- Pinned test deps + pip cache + UTF-8 + branch-scoped concurrency (#163, #177); dropped the unsupported Dependabot pip ecosystem entry (#163 follow-up).

**Docs**
- **README de-slop (EN + zh-TW)**: removed AI-generated tonal artifacts so the project face reads as a genuine, professional share rather than a product launch page. Dropped the triple-slogan line, per-section header emoji, and the "demand discipline" footer in `README.md`; softened the buzzword-heavy opening ("頂尖開發者 / 高效能 / 結構化認知框架") and removed section-header emoji in `docs/README_zh-TW.md`. Aligned the top tagline ("operating system" → "layer") with the humbler open-source footer, and brought the zh-TW anti-drift bullets back to plain register for EN/zh parity. Trimmed the redundant "Ready/Compatible" marketing badges (platform support is already in the Platform Compatibility table). No content, tables, diagrams, or install steps were removed.
- Self-regenerating benchmark token snapshot + deleted-skill-ref fixes + zh-TW parity (#126–#130); documentation navigation map; refreshed stale platform/skill references; clarified the Windows Git Bash requirement; backlog issue-sync + archival (#8, #139, #165); Codex contributor attribution; QRSPI research notes (backlog #69).
- Version banners bumped to v1.3.0 across `README.md`, `docs/README_zh-TW.md`, `CITATION.cff`, the Model Selection Guide, and the Testing Protocol (EN + zh-TW). Validator encoding-canary phrases repointed (sh + ps1) to match the de-slopped READMEs. Measurement-tied banners (`LIFECYCLE_BENCHMARK`, dated to the 2026-05-31 snapshot) and illustrative example text were intentionally left unchanged.
- Fixed stale internal citations in live files surfaced by a doc-accuracy audit: `engineering_guardrails.md` (`bootstrap.md §7` → `§1 Classification Tiers`), `.agent/config.yaml` (nonexistent `AGENTS.md §Document Lifecycle Governance` → `doc-governance.md`; stale `§Skill Safety #7/#8` item numbers), `portable-minimal-kit.md` (removed `minimal-text-hardening-kit.md` → `check_text_integrity.py`), and a stale artifact-node filename in the `antigravity-v5-runtime.md` mermaid diagram. `PROJECT_EXAMPLES.md` (EN + zh) now uses the canonical `/plan` and `/implement` in its example flows instead of the `/write-plan` / `/execute-plan` aliases, which work on Codex/Antigravity but lack Claude `.claude/commands` stubs (so the examples are now cross-platform-portable).
- Audit also surfaced unbuilt planned deliverables in historical ADR-002 / `lock-unification.md` (AC-24/AC-25: `governance-doc-lifecycle-matrix.md` + an `AGENTS.md` section never created) — left unedited pending a scoping decision rather than papering over the record (tracked as a follow-up).

## [1.2.0] - 2026-05-31

Consolidated release covering PRs #98–#122 since v1.1.2. Highlights:

**Governance model**
- **Handoff-trigger overhaul (#121)**: replaced the turn-count handoff trigger with a **context-occupancy + phase-boundary** advisory model, converged four scattered/contradictory turn constants into one SSoT (`AGENTS.md §Context Pruning`), and added a cross-platform caching/compaction reference (`token-governance.md §6.1`) for Claude / OpenAI Codex / Google Gemini. Stays advisory — no enforced gate added.
- **Doc-consistency cleanup (#122)**: unified the tiny-fix threshold (`< 5 lines` → canonical `< 3 files, no semantic change`), unified the runtime sentinel (`[ACX-READ-OK]` → `⚡ ACX`), genericized stale exact model-version strings to drift-proof tier descriptors (EN + zh-TW + bug-report template), and aligned `ai-development-pitfalls.md` with the occupancy model + platform-neutral wording.

**Security & integrity**
- **CI security scanning (#20)**: Semgrep SAST + TruffleHog secret detection + pip-audit dependency audit, all tools pinned.
- **Audit-chain tamper-evidence hardening (#117, ADR-003)**: git append-only witness for tail-truncation detection + `migrate` fail-closed against re-blessing forged history.
- **Framework self-test integrity (#116)**: restored `tests/guard` collection and gated 82 governance-tool tests in CI.

**Tooling & reliability**
- validate.sh / validate.ps1: gate-injection hardening (#104), gate-progression repair (#110), inline-python hardening (#111), PS1↔SH parity backfill (#119), `--list-checks`, SSoT atomic writes, gate-receipt schema (#114).
- Downstream/install: cross-session path alignment for zero-Python downstream (#106), scaffold-tier sidecar preservation (#101), framework-ADR filename matching (#100), Windows `.cmd` install/update repair (#120).

**Docs**
- README/cross-doc links work in both GitHub and deployed contexts (#103); version banners + skill count (17→14) corrected (#102); framework-internal refs removed from downstream guidance (#99).

### Adversarial Governance Audit + Downstream UX Hardening (PR #104)

**Validator (validate.sh / validate.ps1) — gate-injection hardening:**
- T175–T247: 22 gate-injection scenarios closed — code-fence bypass, HTML-comment bypass, indented-receipt masking, unclosed-fence masking, multi-section masking, self-reclassification reset abuse (H4), receipts-in-fence diagnostic (T247)
- Validator maintained 80 PASS / 4 WARN / 0 FAIL throughout 20+ commits
- ACX phase shim check (`validate.sh`): guard fixed from `-d` (directory) to `-f` (file) — `.agent/skills/<name>` stubs are flat files; `-d` made the SKILL.md existence check dead code
- ACX phase shim check (`validate.sh`): CRLF line-ending strip added to frontmatter parser — frontmatter `---` delimiter failed to match on Windows checkouts with CRLF line endings
- ACX phase shim check (`validate.ps1`): `-PathType Container` → `-PathType Leaf` — same dead-code fix as validate.sh
- `routing.md §5` / `bootstrap.md §6`: stale "Runtime v5" version token corrected to "Runtime v1"

**Validator — M8 archive relative-link depth check:**
- `validate.sh` / `validate.ps1` M8: scan `archive/*.md` for relative links and WARN when target does not exist — catches depth-mismatch breakage from content copied out of `current_state.md` (depth 2) into `archive/` (depth 3)
- M8 link counter uses stdout read (not `sys.exit(count)`) to avoid mod-256 silent-PASS on ≥256 broken links
- `validate.sh` M8 parity-hardened: `try/except` file-read guard + `^\d+$` numeric pre-check (matches `validate.ps1`)
- `ship.md §2 State Update`: prose warning about relative-link depth hazard when archiving Ship History

**Validator — validate.ps1 loop-termination parity fix (T243/T245/T247):**
- `validate.ps1` T243/T245/T247 fail-closed branches used bare `exit 0` inside the `foreach ($wl in $worklogs)` loop — in PowerShell this terminates the entire script (not just the current iteration), silently skipping ~60 downstream checks and never printing a Summary line; Windows CI falsely reported exit 0 while `validate.sh` on Linux correctly reported exit 1
- Fix: replaced `exit 0` with `$gateProgressionIllegal++; continue` in all three branches — mirrors `validate.sh` behavior where `sys.exit(0)` exits only the Python subprocess and bash continues the outer loop

**test.md — no-test-runner fallback path:**
- `hotfix` moved to sign-off-required group (`engineering_guardrails.md §12.2 no-exceptions`)
- Gate 2 exception (5-Gate Contract) scoped to `quick-win`/`tiny-fix` only
- Fallback procedure step 5 tier-scoped: `quick-win`/`tiny-fix` write PASS; `feature`/`arch-change`/`hotfix` do not write PASS receipt when Gate 2 unsatisfied
- Step 6 tier-scoped: `quick-win`/`tiny-fix` → skip "Run all tests" and proceed to Step 4b; `feature`/`arch-change`/`hotfix` → step 5 terminal, do not proceed
- `quick-win`/`tiny-fix` fallback trigger now writes a Drift Log entry, satisfying Step 4b Gate 2 exception precondition from both paths

**bootstrap.md §3.7 — Next: field overflow fix:**
- Feature full-phase chain (`[/brainstorm →] /spec → ... → /ship`) removed from `Next:` field to prevent 8-line Response Budget breach; chain now recorded in Work Log `## Task Description` only

**`.codex/INSTALL.md` — bash dependency clarified:**
- Bash required on ALL platforms (Windows PS1 installer wraps bash internally)
- Git for Windows prerequisite explicit; PS1 commands include `-ExecutionPolicy Bypass`

## [1.1.2] - 2026-04-17

### Polish Batch 2: Governance Depth

**Installer UX (completes 1.1):**
- `deploy.sh` prints a Python-availability advisory at end-of-run — framework works without Python, but guarded SSoT writes fall back to direct writes (advisory locking disabled) when Python is missing, so multi-session users should install Python 3.8+

**Token Efficiency (completes 3.2 + 3.3):**
- `engineering_guardrails.md §Reading Mode` adds Loaded-Sections Receipt rule — `/bootstrap` echoes loaded §s to Work Log `## Session Info` so later phases can cite without re-reading
- `bootstrap.md` adds Reading Mode Table at top — at-a-glance per-classification index of which §s to read vs skip (saves re-scanning the 374-line file)
- `bootstrap.md §0` replaces inline prose with decision table (first-match-wins) — less cognitive load per classification

**Governance Depth (completes 2.3 + 4.3):**
- `engineering_guardrails.md §4.1` harmonizes "silent above 90%" with structured receipts — narrative-silent but plan/implement/ship compact blocks always include `Confidence:` field
- `implement.md` Pre-Execution Check adds per-step Confidence re-assessment — step-level auditability, not just plan-level
- `AGENTS.md §Read-Once Discipline` requires Drift Log receipt on Safety-Valve re-reads — creates auditable trail for the honor-system rule

## [1.1.1] - 2026-04-17

### Polish: Audit Findings

**Installer UX:**
- Broadened Git-bash detection via `Get-Command git` derivation — covers scoop, chocolatey, portable Git, and custom-prefix installs (installers/deploy_brain.ps1)
- Removed `--quiet` from `git clone` / `git pull` in bootstrap path so slow networks no longer look like a hang (installers/deploy_brain.sh)

**Governance Wiring:**
- `Confidence:` field added to `/plan` compact-block template — confidence gate (engineering_guardrails §4.1) now has an auditable receipt even when confidence is high
- Confidence Trace Audit advisory added to `/ship` pre-flight
- `AGENTS.md` No-Bypass rule clarified: bans skipping gates within a classification's documented phase list, does NOT override quick-win/hotfix fast-paths

**Token Discipline:**
- `CLAUDE.md` condensed 51→27 lines — removed duplicated Hard Rules section; Skills subsection reduced to pointer (AGENTS.md §Skill Safety already canonical)

**Discoverability:**
- `routing.md §3` header labels the skill activation table as the canonical skill index

## [1.1.0] - 2026-04-16

### Token Optimization & Governance Hardening

**Token Efficiency:**
- SKILL.md heading-scope optimization: phase-entry loads only essential sections (~15-22% skill token savings on heavy scenarios) (#57)
- Compressed phase outputs + Response Budget hard cap (≤8 lines prose) (#54)

**Governance Improvements:**
- Expert review quick-wins: rollback plan check in /ship, scope breach detection in /implement, ship-phase gate receipt audit, ADR auto-discovery in bootstrap (#56)
- File existence guards in validate.ps1 and validate.sh (#55)

**Deploy & Platform:**
- Deploy skill subdirs recursively and fix dry-run accuracy (#52)
- Correct migration guide path in bootstrap.md (#53)

## [1.0.0] - 2026-04-12

### Agentic OS v1.0 Public Release

First public release of Agentic OS as an open-source governance framework for AI coding agents.

**Core Framework:**
- Gate Engine with mandatory phase progression and handshake enforcement
- 5 task classifications: tiny-fix, quick-win, feature, hotfix, architecture-change
- Engineering guardrails constitution with OWASP Top 10 auto-scan
- Security guardrails with destructive command blocking
- Single Source of Truth (SSoT) state model with guarded writes

**Workflows & Commands:**
- 25 slash commands covering full development lifecycle
- Intent Router with 30+ bilingual (EN + zh-TW) intent mappings
- Phase-aware skill activation with deterministic rule table

**17 Professional Skills:**
- Test-Driven Development, Systematic Debugging, Red Team / Adversarial
- API Design, Auth Security, Database Design, Frontend Patterns
- Parallel Agent Dispatching, Subagent-Driven Development
- Writing Plans, Executing Plans, Requesting / Receiving Code Review
- Verification Before Completion, Git Worktrees, Finishing a Branch, Doc Lookup

**Multi-Platform Support:**
- Claude Code (CLAUDE.md auto-load)
- Google Antigravity (intent router + runtime)
- OpenAI Codex (platform guide + CLI delegation)
- Cursor, GitHub Copilot (AGENTS.md as project rules)

**Deploy System:**
- Manifest-based smart deploy with sha256 hash tracking
- Tier classification: core (always overwrite), scaffold (skip if modified), wrapper (skip if modified)
- Legacy path migration (automatic detection and recovery)
- Cross-platform installers (Bash, PowerShell, CMD)

**Token Efficiency:**
- Conditional governance loading by task classification
- Skill cache policy with metadata-first loading
- Phase summary compaction for low-token resume
