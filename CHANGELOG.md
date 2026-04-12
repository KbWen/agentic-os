# Changelog

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
