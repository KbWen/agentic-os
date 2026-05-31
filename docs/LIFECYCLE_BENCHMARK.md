# Lifecycle Benchmark & Token Consumption Report

> **Framework**: Agentic OS v1.2.0 | **CI-gated suite**: 126 passing | **Token figures**: illustrative (measured 2026-04-12, not re-run per release)

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

## 6 Real-World Lifecycle Scenarios

### Scenario 1: Quick-Win Single Module

> **Example**: "Fix the date format in the export CSV feature"

| Attribute | Value |
|:---|:---|
| **Classification** | `quick-win` |
| **Phases** | Bootstrap → Plan → Implement → Ship |
| **Activated Skills** | 4 (writing-plans, executing-plans, verification-before-completion, finishing-a-development-branch) |
| **Phase Repeats** | None |

**Token Cost**:
| Metric | Tokens |
|:---|---:|
| Workflow reads | 14,336 |
| Skill probe (candidate evaluation) | 1,550 |
| Skill execution detail | 1,155 |
| **Current total** | **17,041** |
| Projected (optimized) | 15,315 |
| **Savings** | **1,726 (10.1%)** |

**Takeaway**: Lightest lifecycle. Governance overhead is ~17K tokens — about the cost of a single medium-length conversation turn. Adequate for models with 32K+ context.

---

### Scenario 2: Feature with TDD Loop

> **Example**: "Add user email verification with OTP flow"

| Attribute | Value |
|:---|:---|
| **Classification** | `feature` |
| **Phases** | Bootstrap → Plan → Implement (x3) → Review → Test (x2) → Handoff → Ship |
| **Activated Skills** | 7 (writing-plans, executing-plans, verification-before-completion, test-driven-development, red-team-adversarial, requesting-code-review, finishing-a-development-branch) |
| **Phase Repeats** | implement x3 (Red→Green→Refactor), test x2 (regression) |

**Token Cost**:
| Metric | Tokens |
|:---|---:|
| Workflow reads | 28,141 |
| Skill probe | 3,839 |
| Skill execution detail | 4,982 |
| **Current total** | **36,962** |
| Projected (optimized) | 29,340 |
| **Savings** | **7,622 (20.6%)** |

**Takeaway**: TDD loops inflate implement/test costs but the continuation model (first-load + cache) cuts execution detail by ~53% vs naive full-read-every-time approach.

---

### Scenario 3: Feature Touching API, Auth & Database

> **Example**: "Add role-based access control for the admin panel with new DB tables"

| Attribute | Value |
|:---|:---|
| **Classification** | `feature` |
| **Phases** | Bootstrap → Plan → Implement (x2) → Review → Test (x2) → Handoff → Ship |
| **Activated Skills** | 11 (includes api-design, database-design, auth-security, doc-lookup, TDD, red-team) |
| **Phase Repeats** | implement x2, test x2 |

**Token Cost**:
| Metric | Tokens |
|:---|---:|
| Workflow reads | 25,406 |
| Skill probe | 9,838 |
| Skill execution detail | 15,731 |
| **Current total** | **50,975** |
| Projected (optimized) | 38,544 |
| **Savings** | **12,431 (24.4%)** |

**Takeaway**: Cross-domain features activate more skills (11 vs 7), increasing probe cost. The compact index probe saves ~8.4K tokens vs reading full SKILL.md files for each candidate.

---

### Scenario 4: Hotfix with Debugging Loop

> **Example**: "Production orders are duplicating — urgent fix needed"

| Attribute | Value |
|:---|:---|
| **Classification** | `hotfix` |
| **Phases** | Bootstrap → Implement (x2) → Review → Test (x2) → Ship |
| **Activated Skills** | 6 (executing-plans, verification-before-completion, systematic-debugging, red-team-adversarial, requesting-code-review, finishing-a-development-branch) |
| **Phase Repeats** | implement x2 (debug cycles), test x2 (regression) |

**Token Cost**:
| Metric | Tokens |
|:---|---:|
| Workflow reads | 22,097 |
| Skill probe | 3,437 |
| Skill execution detail | 5,014 |
| **Current total** | **30,548** |
| Projected (optimized) | 23,824 |
| **Savings** | **6,724 (22.0%)** |

**Takeaway**: Hotfix skips Spec and Plan phases but still enforces Review + Test. Debug loop costs are moderate thanks to systematic-debugging skill's on-failure loading policy (only loaded when failures are detected).

---

### Scenario 5: Architecture Change with Multi-Agent

> **Example**: "Migrate from monolith to microservices — separate auth, catalog, and order services"

| Attribute | Value |
|:---|:---|
| **Classification** | `architecture-change` |
| **Phases** | Bootstrap → Plan → Implement (x2) → Review (x2) → Test (x2) → Handoff → Ship |
| **Activated Skills** | 14 (all domain skills + worktrees + parallel agents + subagent development) |
| **Phase Repeats** | implement x2, review x2, test x2 |

**Token Cost**:
| Metric | Tokens |
|:---|---:|
| Workflow reads | 28,682 |
| Skill probe | 11,752 |
| Skill execution detail | 20,850 |
| **Current total** | **61,284** |
| Projected (optimized) | 45,947 |
| **Savings** | **15,337 (25.0%)** |

**Takeaway**: The heaviest lifecycle — activates all 14 domain skills and uses parallel agent coordination. Even so, total governance cost stays under 62K tokens. The optimization saves 15K+ tokens through compact probing and heading-scoped workflow reads.

---

### Scenario 6: Post-Review Feedback Loop

> **Example**: "Address reviewer's 5 comments, re-implement, then pass re-review"

| Attribute | Value |
|:---|:---|
| **Classification** | `feature` |
| **Phases** | Review (x4) → Implement (x2) → Test (x2) → Handoff → Ship |
| **Activated Skills** | 6 (receiving-code-review, requesting-code-review, executing-plans, verification-before-completion, red-team-adversarial, finishing-a-development-branch) |
| **Phase Repeats** | review x4, implement x2, test x2 |

**Token Cost**:
| Metric | Tokens |
|:---|---:|
| Workflow reads | 27,381 |
| Skill probe | 3,606 |
| Skill execution detail | 5,878 |
| **Current total** | **36,865** |
| Projected (optimized) | 26,188 |
| **Savings** | **10,677 (29.0%)** |

**Takeaway**: Reviewer feedback loops cause the most phase repetitions. Heading-scoped workflow reads save ~7.9K tokens by re-reading only the core sections on subsequent entries, not the full 3.3K-token review.md each time.

---

## Aggregate Comparison

| Metric | All 6 Scenarios Combined |
|:---|---:|
| Total current approach | **233,675 tokens** |
| Total optimized approach | **179,158 tokens** |
| Total savings | **54,517 tokens (23.3%)** |

### By Classification Tier

| Classification | Current Tokens | Projected Tokens | Savings |
|:---|---:|---:|---:|
| Quick-Win | 17,041 | 15,315 | 1,726 (10.1%) |
| Feature (TDD) | 36,962 | 29,340 | 7,622 (20.6%) |
| Feature (API+Auth+DB) | 50,975 | 38,544 | 12,431 (24.4%) |
| Hotfix | 30,548 | 23,824 | 6,724 (22.0%) |
| Architecture Change | 61,284 | 45,947 | 15,337 (25.0%) |
| Post-Review Loop | 36,865 | 26,188 | 10,677 (29.0%) |

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
Step 4: Pick a quick-win → Experience the full lifecycle at low cost (~17K tokens)
Step 5: Attempt a feature → Full 7-phase lifecycle with skills
```

This graduated approach lets your team experience governance incrementally rather than attempting a full feature lifecycle on day one.

---

## Running the Benchmarks Yourself

```bash
# CI-gated validation suite (the authoritative pass/fail signal — what GitHub Actions runs)
python -m pytest tests/ci/ tests/guard/ -v

# Dev-time analysis suite that produces the token figures below
# (includes live-repo invariant checks that track the evolving repo)
python -m pytest .agentcortex/tests/ -v

# Generate token analysis report
python .agentcortex/tools/analyze_token_lifecycle.py --root . --format text

# JSON output for programmatic consumption
python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json

# Audit runtime readiness
python .agentcortex/tools/audit_agent_runtime.py --root . --format json
```

---

*This benchmark uses `chars / 4` as the token estimation formula, consistent with the framework's test infrastructure. Actual token counts may vary by ±10% depending on the tokenizer used by your model.*
