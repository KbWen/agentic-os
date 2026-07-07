# Work Log: codex-research-main

## Header

- Branch: `main`
- Classification: `feature`
- Classified by: `Codex`
- Frozen: `true`
- Created Date: `2026-06-18`
- Owner: `codex-research`
- Guardrails Mode: `Full`
- Current Phase: `research`
- Checkpoint SHA: `77fca37b97dfc7771c93ae7c4d5b4fdd74fae6ef`
- Recommended Skills: `systematic-debugging, karpathy-principles, verification-before-completion`
- Primary Domain Snapshot: `governance-runtime`
- SSoT Sequence: `68`

---

## Session Info

- Agent: `Codex (GPT-5)`
- Session: `2026-06-19T09:28:15+08:00`
- Platform: `Codex App`
- Guardrails loaded: `§1, §2, §4, §7, §8.1, §10 (core) + §6 + §13`
- Override: `none`
- Downstream-Capabilities: `none`
- User Preferences: `none`
- Context Read Receipt: `SSoT sequence 68; owner-scoped Work Log resumed; ADR-009 coverage verified`

---

## Task Description

Complete the interrupted comparative research on reusable skill/workflow
practices. Persist each remaining source analysis, produce a final calibrated
synthesis, and hand issue/backlog/spec execution work to Claude.

Explicit boundary: no issue creation, backlog mutation, spec freeze, planning,
implementation, or shipping in this research run.

---

## Phase Sequence

| Phase | Status | Notes |
|---|---|---|
| bootstrap | completed | Recovery and feature classification restored. |
| research | completed | Nodes 0-15 plus re-audits 2A/3A persisted; Claude research handoff written. |
| brainstorm | completed | Private pre-browse Research Capsule recommended. |
| decide | completed | D-1 confirmed by user. |
| adr | completed | ADR-009 accepted and indexed. |
| spec | provisional draft | `docs/specs/research-capsule-persistence.md`; freeze deferred pending final synthesis. |
| issue/backlog/plan/implement | delegated | Reserved for Claude after handoff. |

---

## Research Inventory

- Nodes 0-7 + re-audits 2A/3A: Anthropic package/eval mechanics,
  Agentic OS overlap, Superpowers D → B+C, Karpathy no-new-gap disposition.
- Node 08: four persistence options; private Research Capsule recommended.
- Node 09: five remaining source identities, revisions, and licenses pinned.
- Node 10: Addy Osmani deep compare complete.
- Node 11: Tech Leads Club deep compare complete; useful progressive registry
  mechanics, but installed-byte integrity, expiring exceptions, audit
  guarantees, dependency health, and Windows parity are not established.
- Node 12: VoltAgent subagents deep compare complete; role/tool contracts and
  category packaging are useful, but permissions exceed claims and no
  behavioral/security validator establishes effectiveness.
- Node 13: Awesome Claude Code deep compare complete; machine-readable
  provenance/freshness catalog is useful, but current generated-view drift,
  stale data, license contradictions, and unpinned downloads prevent trust.
- Node 14: Awesome Agent Skills deep compare complete; broad discovery value
  only, with no schema, CI, audit, revision pins, or effectiveness evidence.
- Node 15: calibrated synthesis complete; ADR-009 retained, order confirmed as
  Research Capsule → D → B+C → A, with G split by present vs. conditional need.
- Claude handoff defines six separate work packets and the resume prompt.
- Remaining research: none.
- Candidate order remains `D → B+C → A`; Research Capsule is an immediate
  resilience seam and does not absorb those larger follow-ons.

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | `docs/adr/ADR-009-pre-browse-research-capsule.md` | Accepted persistence architecture. |
| Draft spec | `docs/specs/research-capsule-persistence.md` | Provisional until final synthesis. |
| Research | `.agentcortex/context/private/codex-research-main/node-00..15*.md` | Persistent evidence and dispositions. |
| Handoff | `.agentcortex/context/private/codex-research-main/claude-handoff-research-synthesis.md` | Research-to-workflow transfer for Claude. |
| Overflow 1 | `.agentcortex/context/archive/work/codex-research-main-20260619.md` | Earlier full Work Log. |
| Overflow 2 | `.agentcortex/context/archive/work/codex-research-main-20260619-2.md` | Full Work Log through Node 09. |

---

## Known Risk

- Remaining repositories are large catalogs; popularity and README claims are
  discovery evidence only.
- The provisional ADR/spec may need factual narrowing after final synthesis.
- `main` has unrelated `.acx-local/` content that must remain untouched.
- No issues/backlog rows may be created in this run.

---

## Conflict Resolution

- Debugging remains sequential and evidence-first.
- `karpathy-principles` and `verification-before-completion` are compatible.
- Same-vendor subagent opinions are hypotheses; primary repository inspection
  and primary-source evidence decide findings.
- `skill-research-integration.md` concerns candidate selection; the Research
  Capsule draft is independent session-persistence work.

---

## Skill Notes

### systematic-debugging

- Checklist: preserve the context-exhaustion symptom; verify exact missing
  persistence boundary; change one seam at a time.
- Constraint: no patch before the failure boundary and regression are evidenced.

### karpathy-principles

- Checklist: prefer minimal residual gaps; reject duplicate skills/systems;
  keep future changes surgical.
- Constraint: repository popularity is not implementation evidence.

### verification-before-completion

- Checklist: every source has pinned identity, mechanics, local overlap, and a
  saved disposition; final synthesis must reconcile all candidates.
- Constraint: no evidence means no completion claim.

---

## Decisions

### D-1: Use a private pre-browse research capsule
- **Decision**: Create a primary-owned private capsule before long or multi-source research, with a manifest and bounded source/work-unit checkpoints.
- **Reason**: It is the smallest option that closes the verified failure before a Work Log exists while keeping detailed evidence out of the Work Log.
- **Alternatives**: Broaden Work Log checkpoints; tracked `_research-*` ledger; full Task/Step capsules now.
- **Impact**: `/research`, `/spec-intake`, and nonlinear recovery share the lifecycle; Task/Step review and skill evaluation remain separate.

---

## Phase Summary

- research: Node 06 verified D → B+C through Superpowers task capsules and one-reviewer/two-verdict review. ⚡ ACX
- research: Node 07 found Karpathy already integrated and locally strengthened; provenance hygiene only. ⚡ ACX
- brainstorm/decide: Option 2 private pre-browse Research Capsule selected and recorded as D-1. ⚡ ACX
- adr/spec: ADR-009 accepted; provisional Research Capsule spec written but not frozen. ⚡ ACX
- research: Node 09 pinned five remaining repos; Node 10 found three residuals from Addy: skill-body compatibility validation, isolated-research-to-capsule composition, and reinforcement of the future Task layer. ⚡ ACX
- research: Node 11 found TLC's progressive registry and validation concepts useful, but disproved installed-byte integrity, durable audit, exception-expiry, dependency-health, and Windows-parity assumptions. ⚡ ACX
- research: Node 12 found VoltAgent's role/tool contracts and category plugins useful, but its permission claims, unpinned installers, and effectiveness evidence do not support wholesale activation. ⚡ ACX
- research: Node 13 retained machine-readable provenance/freshness metadata from Awesome Claude Code while rejecting catalog inclusion, stale status, and unpinned downloads as execution evidence. ⚡ ACX
- research: Node 14 classified Awesome Agent Skills as a discovery queue only; it added no new residual or priority change. ⚡ ACX
- research: Node 15 retained ADR-009, confirmed Research Capsule → D → B+C → A, split G into actionable compatibility vs conditional installer integrity, and produced the Claude handoff. ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-18T10:05:40+08:00
- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-19T09:28:15+08:00

---

## Evidence

- Stable repository checkpoint: `77fca37b97dfc7771c93ae7c4d5b4fdd74fae6ef`.
- ADR-009 coverage check resolves all anticipated Research Capsule paths.
- Node 09 SHA-256: `f6f3745b585c0a31cc0a865a49c3c873f85ceab759a046338644848f3eaeb4d9`.
- Node 10 SHA-256: `3e56970dc21ce15dff661839d0663100df423a0a75517c8a5e1adbdfb22e7d80`.
- Node 11 SHA-256: `7b8e66dc4f2eaa77d0575a93643f0bbeba1c2938006a2971acd24a2b7ddd1fb0`.
- Node 12 SHA-256: `64214cd79256957d6369fcc73fdcf7fa4e4e903f346e049b1aba485e9939c693`.
- Node 13 SHA-256: `7365c94b8c3e7a8b953547b28328314582632a0893661dddb27552e9296fff5e`.
- Node 14 SHA-256: `270c142c655681674102d127dd882c77db0c521fb2ca9047a559b0448fb63d1a`.
- Node 15 SHA-256: `0c917d162dc23151426e410705b76becacc23f46946eabad69cd92f71c1f36e5`.
- Claude handoff SHA-256: `798eb91e355d8d9627ae5389c80b3b590ee0be70743b08b90f6a82924ae3143f`.
- Addy validator: `24 skills checked — 0 errors, 0 warnings — PASSED`.
- Addy shell-hook smoke test was unavailable through the WindowsApps WSL
  placeholder; upstream hook CI is Ubuntu-only.
- TLC Windows validator: `30 passed, 50 failed, 56 warnings`; core tests:
  `53 failed, 132 passed`; production audit: `13 vulnerabilities`.

---

## Drift Log

- 2026-06-18: Recovered interrupted multi-source research into owner-scoped persistent nodes.
- 2026-06-19: User confirmed Research Capsule Option 2; D-1 and ADR-009 recorded.
- 2026-06-19: Spec Index draft update deferred because `/spec` is not an exhaustive non-ship SSoT-write exception.
- 2026-06-19: User redirected scope to complete research and delegate issue/backlog/implementation work to Claude.
- 2026-06-19: Research completed without issue/backlog/spec-freeze/plan/implement mutations; final synthesis and Claude handoff persisted.
- Compacted: 2026-06-19, archive: `.agentcortex/context/archive/work/codex-research-main-20260619-2.md`.

---

## Design Reference

none

---

## Observability

none

---

## Resume

- State: `RESEARCH COMPLETE; SPEC DRAFT PROVISIONAL; WORKFLOW EXECUTION DELEGATED`
- Completed: `Nodes 0-15 + re-audits 2A/3A; D-1; ADR-009; provisional spec; Claude handoff`
- Next: `Claude /bootstrap, then canonical spec/issue/backlog workflows`
- Remaining: `no research; delegated workflow formalization and implementation`
- Do not: `create issues, mutate backlog, freeze spec, plan, implement, touch .acx-local/, or overwrite main.md`

⚡ ACX
