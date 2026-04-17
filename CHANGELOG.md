# Changelog

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
