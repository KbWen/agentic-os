# Lifecycle Benchmark & Token Consumption Report

> **Framework**: Agentic OS v1.2.0 | **CI-gated suite**: 126 passing | **Token snapshot**: regenerated 2026-05-31 (numbers below are tool-generated — see "Regenerating This Report")

This report documents lifecycle scenario coverage and token-consumption measurements.
It helps teams evaluate Agentic OS governance overhead before adoption.

---

## Test Suite Summary

Two suites exist; they serve different purposes:

- **CI-gated validation suite** — `python -m pytest tests/ci/ tests/guard/` — **126 tests, all passing** (verified 2026-05-31). This is what GitHub Actions enforces on every PR and is the authoritative "is the framework healthy?" signal.

| Category | Tests | File |
|:---|:---:|:---|
| Security scanning (Semgrep + TruffleHog + pip-audit) | 32 | `tests/ci/test_security_workflow.py` |
| Audit-chain witness | 9 | `tests/ci/test_audit_witness.py` |
| Guard write (unit) | 24 | `tests/guard/test_d2_1_guard_unit.py` |
| Audit-chain tamper-evidence | 17 | `tests/guard/test_audit_chain.py` |
| Governed-write lint | 16 | `tests/guard/test_d2_2_lint.py` |
| Doc-lifecycle contract | 14 | `tests/guard/test_d2_3_lifecycle.py` |
| ADR coverage | 12 | `tests/guard/test_adr_coverage.py` |
| Guard write (race) | 2 | `tests/guard/test_d2_1_guard_race.py` |
| **Total (CI-gated)** | **126** | all passing |

- **Dev-time analysis suite** — `.agentcortex/tests/` — generates the token-consumption figures below via `analyze_token_lifecycle.py`. It includes live-repo invariant checks (SSoT sequence monotonicity, backlog/ship-history resolvability) that intentionally track the evolving repository, so it is **not** part of release gating.

---

## Token Consumption Snapshot

> **The numbers below are generated, not hand-maintained.** Regenerate them anytime with
> `python .agentcortex/tools/analyze_token_lifecycle.py --root . --format text` — they drift as
> workflows and skills evolve, so treat this table as a dated snapshot, not a fixed contract.
>
> **Snapshot date**: 2026-05-31 · **Formula**: `chars / 4` (±10% vs your model's tokenizer) · **Baseline**: registry 4,838 tok, compact index 2,664 tok.

"Current" = naïve full-read-every-time. "Optimized" = compact-index probing + heading-scoped workflow reads + skill heading-scope.

| Scenario | Class | Current | Optimized | Savings |
|:---|:---|---:|---:|---:|
| Quick-Win (single module) | `quick-win` | 26,749 | 22,077 | 4,672 (17.5%) |
| Feature + TDD loop | `feature` | 56,139 | 38,739 | 17,400 (31.0%) |
| Feature (API + Auth + DB) | `feature` | 70,177 | 39,532 | 30,645 (43.7%) |
| Hotfix + debug loop | `hotfix` | 44,662 | 30,740 | 13,922 (31.2%) |
| Architecture-change + multi-agent | `architecture-change` | 82,665 | 44,130 | 38,535 (46.0%) |
| Post-review feedback loop | `feature` | 55,336 | 30,390 | 24,946 (45.1%) |
| **All 6 combined** | — | **335,728** | **205,608** | **130,120 (38.8%)** |

---

## Scenario Profiles

Qualitative shape of each scenario (what drives cost). Token figures live in the snapshot above; skill names below reflect the current 14-skill set.

### 1. Quick-Win — single module
> *"Fix the date format in the export CSV feature"*
- **Phases**: Bootstrap → Plan → Implement → Ship
- **Skills**: verification-before-completion, karpathy-principles
- **Cost driver**: lightest lifecycle — governance overhead only; no review/test/handoff. Adequate for 32K+ context models.

### 2. Feature with TDD loop
> *"Add user email verification with OTP flow"*
- **Phases**: Bootstrap → Spec → Plan → Implement (×3) → Review → Test (×2) → Handoff → Ship
- **Skills**: test-driven-development, verification-before-completion, red-team-adversarial, karpathy-principles
- **Cost driver**: Red→Green→Refactor implement repeats + regression test repeats; the continuation model (first-load + cached notes) absorbs most of the repeat cost.

### 3. Feature touching API, Auth & Database
> *"Add role-based access control for the admin panel with new DB tables"*
- **Phases**: Bootstrap → Spec → Plan → Implement (×2) → Review → Test (×2) → Handoff → Ship
- **Skills**: api-design, database-design, auth-security, doc-lookup, test-driven-development, red-team-adversarial, production-readiness
- **Cost driver**: cross-domain features activate the most skills → probe cost rises; compact-index probing is where the big savings appear.

### 4. Hotfix with debugging loop
> *"Production orders are duplicating — urgent fix needed"*
- **Phases**: Bootstrap → Research → Plan → Implement (×2) → Review → Test (×2) → Ship
- **Skills**: systematic-debugging, verification-before-completion, red-team-adversarial
- **Cost driver**: hotfix still enforces review/test, but `systematic-debugging` loads on-failure only, keeping debug-loop cost moderate.

### 5. Architecture change with multi-agent
> *"Migrate from monolith to microservices — separate auth, catalog, order services"*
- **Phases**: Bootstrap → ADR → Spec → Plan → Implement (×2) → Review (×2) → Test (×2) → Handoff → Ship
- **Skills**: all domain skills + using-git-worktrees + dispatching-parallel-agents + subagent-driven-development
- **Cost driver**: the heaviest lifecycle — activates the full skill set and parallel-agent coordination; optimization saves the most absolute tokens here.

### 6. Post-review feedback loop
> *"Address reviewer's 5 comments, re-implement, then pass re-review"*
- **Phases**: Review (×4) → Implement (×2) → Test (×2) → Handoff → Ship
- **Skills**: red-team-adversarial, verification-before-completion, karpathy-principles
- **Cost driver**: the most phase repetitions; heading-scoped workflow reads (re-read only core sections on re-entry) drive the highest optimization percentage.

---

### Token Optimization Breakdown

| Optimization | How It Works | Savings Source |
|:---|:---|:---|
| **Conditional Loading** | tiny-fix reads only `AGENTS.md`; quick-win skips guardrails | Base governance: ~3,500–5,000 tokens saved |
| **Compact Index Probing** | Read skill metadata (40 tokens/skill) instead of full SKILL.md (200–2,200 tokens/skill) | Probe phase: ~60–85% cheaper |
| **Heading-Scoped Workflow** | Parse `## Heading-Scoped Read Note` to read only needed sections | Repeated phases: ~20–30% of full file skipped |
| **Continuation Model** | First skill load = full SKILL.md; subsequent = cached notes (~22% of full) | Execution detail: ~40–62% reduction for heavy scenarios |
| **Read-Once Discipline** | Governance files read once per session, never re-read | Session: prevents token leaks on long conversations |

---

## Getting Started: Recommended Onboarding Path

For teams evaluating or adopting Agentic OS, we recommend starting with `/audit`:

### Why Start with /audit?

```
/audit
```

The `/audit` command performs a **read-only** traversal of your existing codebase:

1. **Zero risk** — no code modifications, no gate requirements
2. **Full visibility** — maps your file structure, architecture, entry points, and test coverage
3. **Gap analysis** — identifies missing documentation and recommended next steps
4. **Routing actions** — generates structured follow-up items pointing to canonical docs

### Recommended Onboarding Sequence

```
Step 1: /audit          → Understand the current state
Step 2: /app-init       → Set up project-specific conventions
Step 3: /spec-intake    → Import existing specs/requirements
Step 4: Pick a quick-win → Experience the full lifecycle at low cost (~27K tokens)
Step 5: Attempt a feature → Full lifecycle with skills
```

This graduated approach lets your team experience governance incrementally rather than attempting a full feature lifecycle on day one.

---

## Regenerating This Report

```bash
# CI-gated validation suite (the authoritative pass/fail signal — what GitHub Actions runs)
python -m pytest tests/ci/ tests/guard/ -v

# Dev-time analysis suite that produces the token figures (tracks the live repo)
python -m pytest .agentcortex/tests/ -v

# Regenerate the Token Consumption Snapshot numbers
python .agentcortex/tools/analyze_token_lifecycle.py --root . --format text

# JSON output for programmatic consumption
python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json

# Audit runtime readiness
python .agentcortex/tools/audit_agent_runtime.py --root . --format json
```

---

*This benchmark uses `chars / 4` as the token estimation formula, consistent with the framework's test infrastructure. Actual token counts may vary by ±10% depending on the tokenizer used by your model.*
