---
status: draft
title: "External Skill Research & Integration"
created: 2026-04-13
goal: "Mine open-source repos for behavioral/procedural skills that strengthen AI agent self-governance"
---

# External Skill Research & Integration

## 1. Objective

Systematically evaluate high-quality open-source repos and extract skills that fill
governance gaps in Agentic OS. End goal: AI agents become better at self-discipline,
not just following gates.

## 2. Governance Gap Analysis

Current inventory: 19 skills. Coverage is strong on **gates & workflows** but weak
on **behavioral discipline** and **quality depth**.

| Gap | Severity | Description |
|---|---|---|
| Anti-Rationalization | HIGH | No mechanism to counter agent excuses ("I'll add tests later") |
| Change Sizing | HIGH | No upfront scope-estimation gate — agents underestimate then sprawl |
| Code Review Depth | MEDIUM | Request/receive skills exist, but no *quality standard* for conducting reviews |
| Performance Awareness | MEDIUM | No measure-first mindset; production-readiness covers logging but not perf |
| Source-Grounded Decisions | MEDIUM | Agents hallucinate API usage instead of checking official docs first |
| Documentation Discipline | LOW | No enforcement for doc-as-contract or ADR creation triggers |
| Technical Debt Tracking | LOW | No periodic debt assessment or "shortcut → debt ticket" enforcement |
| Testing Strategy Selection | LOW | TDD covers one pattern; no "match test type to risk level" guidance |

## 3. Source Repos (Verified)

| Priority | Repo | Stars | Format Compatibility | Integration Effort |
|---|---|---|---|---|
| P0 | `addyosmani/agent-skills` | 14.6k | SKILL.md + frontmatter (identical) | Low |
| P1 | `tech-leads-club/agent-skills` | 2.1k | Antigravity-native | Low |
| P2 | `VoltAgent/awesome-claude-code-subagents` | 17.2k | Markdown + YAML (similar) | Medium |
| P3 | `hesreallyhim/awesome-claude-code` | 38.5k | Hub/index (curation source) | N/A |
| P3 | `VoltAgent/awesome-agent-skills` | 15.5k | Mixed (catalog mining) | Medium |

## 4. Skill Candidates — Detailed Selection

### 4.1 From `addyosmani/agent-skills` (P0)

Each skill includes anti-rationalization tables + evidence gates — a pattern
we should adopt framework-wide.

| Candidate Skill | Fills Gap | Phase Scope | Type | Priority |
|---|---|---|---|---|
| `code-review-and-quality` | Code Review Depth + Change Sizing | review | Procedural | P0 |
| `performance-optimization` | Performance Awareness | review, implement | Procedural | P0 |
| `source-driven-development` | Source-Grounded Decisions | implement, review | Behavioral | P0 |
| `code-simplification` | Technical Debt + Anti-Rationalization | review | Behavioral | P1 |
| `incremental-implementation` | Change Sizing (reinforcement) | implement | Behavioral | P1 |
| `documentation-and-adrs` | Documentation Discipline | ship, handoff | Procedural | P2 |

**Cross-cutting extraction**: Anti-rationalization table pattern → add to
`engineering_guardrails.md` or create a meta-skill `anti-rationalization`.

### 4.2 From `tech-leads-club/agent-skills` (P1)

| Candidate | Value | Priority |
|---|---|---|
| Skill validation pipeline (Snyk) | Meta-governance: validate skills themselves | P1 |
| Security-audited skill patterns | Enhance `auth-security` skill | P2 |

### 4.3 From `VoltAgent/awesome-claude-code-subagents` (P2)

| Candidate | Value | Priority |
|---|---|---|
| Security auditor subagent patterns | Reference for `red-team-adversarial` enhancement | P2 |
| Multi-agent coordination patterns | Reference for `dispatching-parallel-agents` | P2 |

## 5. Integration Phases (Revised — Integration-Only)

After detailed analysis, `doc-lookup` already covers 70% of `source-driven-development`.
All candidates are integrated into existing skills — zero new skills added.

### Phase A: Enhance Existing Skills (P0) ✅ DONE

| Target Skill | Enhancement | Source |
|---|---|---|
| `doc-lookup` | Anti-rationalization table + Conflict Detection Template | addyosmani/source-driven-development |
| `karpathy-principles` | Anti-rationalization table + Code Simplification Checklist | addyosmani/code-simplification |
| `receiving-code-review` | 5-Axis Quality Standard + Anti-rationalization table | addyosmani/code-review-and-quality |

### Phase B: Future Candidates (P2, not yet started)

| Candidate | Value | Source |
|---|---|---|
| Skill validation pipeline (Snyk) | Meta-governance | tech-leads-club/agent-skills |
| Security auditor subagent patterns | Enhance red-team-adversarial | VoltAgent/awesome-claude-code-subagents |

### Phase C: Reference Mining (Ongoing, P3)

Use `hesreallyhim/awesome-claude-code` and `VoltAgent/awesome-agent-skills`
as ongoing discovery sources. Check monthly for new community skills worth
evaluating.

## 6. Evaluation Criteria (per candidate skill)

| Criterion | Weight | Question |
|---|---|---|
| Gap Coverage | 30% | Does it fill an identified governance gap? |
| Phase Fit | 20% | Does it map to existing workflow phases? |
| Token Cost | 15% | Is the SKILL.md ≤ 150 lines? (cost_risk: low preferred) |
| Conflict Risk | 15% | Does it conflict with existing skills? |
| Behavioral vs Procedural | 10% | Behavioral skills are scarcer — slight preference |
| Community Signal | 10% | Star count, author credibility, maintenance status |

## 7. Success Metrics

- [x] 3 existing skills enhanced with anti-rationalization tables (Phase A)
- [x] Code simplification checklist integrated into karpathy-principles
- [x] 5-axis quality standard integrated into receiving-code-review
- [x] Conflict detection template integrated into doc-lookup
- [ ] `validate.sh` passes with all changes
- [ ] Zero governance gaps rated HIGH remaining

## 8. References

- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)
- [tech-leads-club/agent-skills](https://github.com/tech-leads-club/agent-skills)
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)
- [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (already integrated as karpathy-principles)
