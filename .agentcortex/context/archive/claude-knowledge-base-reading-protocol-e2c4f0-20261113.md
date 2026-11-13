# Work Log: claude/knowledge-base-reading-protocol-e2c4f0

## Header

- Branch: `claude/knowledge-base-reading-protocol-e2c4f0`
- Classification: `architecture-change`
- Classified by: `claude-opus-5-5`
- Frozen: `true`
- Created Date: `2026-11-13`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `ship`
- Diff Base SHA: `daedb4b`
- Checkpoint SHA: `daedb4b`
- Recommended Skills: `karpathy-principles, verification-before-completion, red-team-adversarial, kb-consult`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `224`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-11-13 03:04 UTC`
- Platform: `claude-code`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §6 (arch), §13 (governance edit)
- Override: none
- Downstream-Capabilities: main-checkout private file (0 skills, knowledge_sources: kb-main→OK@<redacted>); worktree has no private dir

---

## Task Description

The KB side (merged 2026-11-13) now declares how it is read at the head of its entrypoint and asked consumers to depend on that declaration, not on its field names, field types or page constants. Rework the consumer contract: the framework decides whether/when to consult; the KB's declared reading plan decides how (pages, order, amount, stop); framework defaults apply only where the KB declares nothing. Owner decision (chat, 2026-11-13): the KB's declared page budget overrides the framework's default caps.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-11-13T03:04Z | arch-change; ADR-009 review_trigger fired (KB machine contract changed) |
| plan | done | 2026-11-13T03:07Z | roundtable (20 findings) folded in; owner approved ADR-009 amendment + spec freeze in chat |
| implement | done | 2026-11-13T03:25Z | 6 planned files + version cut, compact index, CHANGELOG |
| review | done | 2026-11-13T03:45Z | independent reviewer, 8 findings; 6 fixed, 2 out of scope |
| test | done | 2026-11-13T06:00Z | validators fail=0 (sh + ps1), targeted suites green, local full run 0 failures to ~52% then stopped (CPU contention); full suite = CI on the PR |
| handoff | done | 2026-11-13T06:00Z | Resume written |
| ship | done | 2026-11-13T06:01Z | SSoT 224->225, log archived, draft PR |

---

## Phase Summary

- bootstrap: classified architecture-change (alters the KB/consumer authority boundary; amends accepted ADR-009). ADR coverage exit 0 (ADR-009 covers bootstrap.md). Skills matched; KB consult routed (see Evidence).
- plan: 5 target files (ADR-009 amendment, new spec, bootstrap §1b+§3.6, AGENTS.md KB line, adopter guide); no eval/validator change; spec + ADR amendment stay draft until owner approval. Ref: docs/specs/kb-seam-declared-reading.md | Confidence: 88% — assumes keeping the digest procedure as a guide-described default is enough to avoid regressing BYO KBs built from the current guide (resolved: roundtable kept a one-clause digest default in the row)
- implement: AGENTS.md:34, bootstrap.md §1b + §3.6 row (net −4 bytes), guide (declaration + framework-read sections, typing/summary/cap fixes), template comment, eval case kb-declared-reading-plan-first, ADR-009 amendment accepted, spec frozen; release cut 1.8.39 (banners, CHANGELOG), compact index regenerated (bootstrap.md content hash). Scope divergence: version banners, CHANGELOG, compact index (release cut + required regen) | Confidence: 92% — high
- review: independent reviewer on the diff: BLOCKING AGENTS.md lost the consult instruction for KBs without a plan → fixed (consult per §3.6; plan chooses within limits); BLOCKING eval did not discriminate → fixed + 5 mutations fail; 4 non-blocking fixed (bounded search, plain-entry limits, guide digest/retrieval wording, per-KB raise + old hints not a plan); CHANGELOG added at release cut; retrieval-section names pre-existing (#473), on the framework-read list | Verdict: PASS
- test: validators fail=0 (sh/ps1), targeted suites green, full suite delegated to CI on the PR.
- handoff: Resume written; next /ship.
- ship: PASS; SSoT 224->225 (Spec Index +1, ADR-009 index note, Ship History rotated); spec shipped; archive .agentcortex/context/archive/claude-knowledge-base-reading-protocol-e2c4f0-20261113.md; Domain Doc skip: no `downstream-adaptability` L2 exists and this change's decisions are promoted to the accepted ADR-009 Amendment (2026-11-13), the domain's canonical record, so an L2 entry would duplicate it.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T03:07:14Z
- Gate: plan | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T03:09:16Z
- Gate: implement | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T03:53:18Z
- Gate: review | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T03:53:18Z
- Gate: test | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T06:00:18Z
- Gate: handoff | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T06:00:18Z
- Gate: ship | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-11-13T06:01:26Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/kb-seam-declared-reading.md | new, draft |
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | amendment 2026-11-13 (draft, owner approval pending) |
| ADR | ADR-001, ADR-004, ADR-007, ADR-008, ADR-011 | coverage hits on AGENTS.md / bootstrap.md; no conflict |
| Issue | — | KB-side notification relayed in chat 2026-11-13 |
| PR | — | — |

---

## Known Risk

- Granting the KB selection authority opens a channel for KB text to push actions under "reading plan". Mitigation: authority limited to selection/amount; exec/write/gate text stays DATA; T2 eval case guards it.
- A KB with digests but no reading declaration loses digest-first reads (falls to headings). Accepted: costlier, still bounded and correct; only one known KB and it declares.
- AGENTS.md is always-loaded; the clause is a small net add (justified below, §13).
- Rollback: revert the squash commit; detection = a KB consult reading more than the defaults without a plan=declared record, or the new eval case failing.
- HIGH Global Lessons checked: same-vendor roundtable (each finding verified against the text; one rejected), eval-mapping (protects resolves to §vNext State Model, which holds the KB line), cross-platform EOL (files kept LF), process-batching (edits and git steps kept in separate calls).
- Observability: no runtime code or catch blocks changed; the error-sink check does not apply (docs/prose change).

---

## Decisions

### D-1: KB-declared reading plan wins over framework defaults
- Decision: framework owns whether/when; KB owns how (incl. page count); defaults only where undeclared; no declared stop point → framework caps.
- Reason: KB-side division of labor; owner chose "KB declaration first" (chat 2026-11-13).
- Alternatives: keep framework caps as a hard ceiling (rejected by owner).
- Impact: ADR-009 amendment; bootstrap §3.6 row; AGENTS.md KB line; guide.
→ promoted: ADR-009

---

## Conflict Resolution

karpathy-principles vs verification-before-completion: compatible (matrix). red-team-adversarial: no pair conflict listed.

---

## Skill Notes

### karpathy-principles (plan)
- Checklist: state assumptions; simplest change that meets the ACs; surgical edits only
- Checklist: every changed line traces to an AC
- Constraint: no speculative tooling (no new eval/validator) without a verified consumer

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Spec feedback loop: added `## Domain Decisions` to own frozen spec (validator contract for specs with primary_domain); no AC change.
- Net-add (§13 Deletion-First): AGENTS.md KB line gains one clause (read the declared reading plan first); justified: the KB-side sim found no step asks for it on any entry; offset by the shorter §3.6 row.
- Recovered stale Work Log lock on 2026-11-13T06:00:18.870969+00:00; prior_owner=KbWen; prior_session=2026-11-13T03:04:40Z; reason=stale-time; lock=claude-knowledge-base-reading-protocol-e2c4f0.lock.json

---

## Review Feedback

All blocking rows resolved in-phase (see Phase Summary review line). Out of scope: guide §Optional bounded lookup names (pre-existing, listed under "What the framework reads from any KB").

---

## Red Team Findings

- Roundtable trust seat (pre-implement): denylist authority leaks, digest could override page authority, no cost floor, unclear read tools, no path containment for KB-supplied paths, "follows" vs DATA wording → all fixed (allowlist, framework floor, raise-only-for-feature + Work Log note, read-only tools, inside-KB-root, "use it to choose").
- Risk decision: a KB plan may still raise feature/arch-change reads up to whatever it declares; accepted by owner (chat 2026-11-13), observable via plan=declared + Work Log note.

## Security Findings

- Secret scan of changed files: no credentials; no private KB path, field name, slug or fingerprint in tracked files (AC-6). CRITICAL/HIGH: none.

---

## Design Reference

none

---

## Observability

none

---

## Resume
- State: HANDEDOFF
- Completed: bootstrap, plan (roundtable), implement, review (independent), test, handoff
- Next: /ship — SSoT entry, archive this log, commit, draft PR, wait for CI all-green, then merge + tag v1.8.39 + GitHub Release (owner go-ahead)
- Context: KB declares how it is read (labeled plan at entrypoint head); framework keeps whether/when + floor; caps are defaults, raise only for feature/arch-change.

### Read Map
- docs/specs/kb-seam-declared-reading.md → full
- docs/adr/ADR-009-knowledge-source-consumption-seam.md → §Amendment (2026-11-13)
- .agent/workflows/bootstrap.md → §1b bind + §3.6 kb-consult row

### Skip List
- .agentcortex/docs/guides/connecting-a-knowledge-base.md — reviewed twice, consistent with the row
- .agentcortex/eval/governance.yaml — new case mutation-tested

### Context Snapshot
Principle-based KB contract: framework = whether/when + safety floor (advisory, DATA, page > digest, volatile facts, applicability, inside KB root, no full-load); KB = how via an explicitly labeled reading plan (allowlist: pages/sections, order, count, stop). Defaults only where undeclared; ≤3 pages/phase total across KBs, ≤1 hotfix/quick-win; a plan may lower any cap, raise only for feature/arch-change (noted in Work Log). §1b records plan=declared|default. T2 eval case. Version 1.8.39.

---

## Test Gate Results

- `bash .agentcortex/bin/validate.sh` → pass=117 warn=5 fail=0; `pwsh validate.ps1` → pass=117 warn=5 fail=0 (twin parity).
- `pytest tests/guard/test_governance_eval.py tests/guard/test_capabilities_schema_gate_safety.py tests/ci/test_directive_count_ratchet.py tests/ci/test_lifecycle_baseline_drift.py .agentcortex/tests/test_lifecycle_token_consumption.py` → all passed.
- `pytest -q` (full, local Windows) → 0 failures through ~52%, stopped for CPU contention with another session; full suite runs in CI (Linux + Windows) on the PR — merge only on all-green.
- AC trace: AC-1/2/3 row + guide text (review verified); AC-4 bootstrap.md −4 bytes, 355k + ratchet tests green; AC-5 guide; AC-6 grep + reviewer; AC-7 above; AC-8 Sonnet 1/1, Haiku 1/1.

---

## Evidence

- Read-before-write (§12.1): bootstrap.md (§1b bind + §3.6 table), AGENTS.md §vNext, guide (full), template (full), governance.yaml (KB cases), ADR-009 (Decision + Amendments), CHANGELOG head read before editing.
- Rollback plan: revert the single squash commit of this PR; no data/config migration, downstream re-deploy of the prior tag restores files.
- Targeted tests: governance eval + capabilities + ratchet + lifecycle token + baseline drift → 106/167 passed (all green); eval runner coverage OK.
- Eval kb-declared-reading-plan-first: Sonnet 1/1, Haiku 1/1 pass (answer sections scored); 5 wrong-answer mutations all fail.
- Downstream: plain project 1.8.38 → this tree: 12 framework files M, 0 added/removed, project file hash unchanged, validate fail=0 before and after.

- Bootstrap: ADR coverage `check_adr_coverage.py` exit 0; lock `recover_worklog_lock.py ensure` → created.
- KB state (read-only): clone on clean main; head commit is the KB side's own merge; schema raised; reading declaration present at entrypoint head (manifest + index line 1).
- kb-consult (/plan): one routed row matched; read its first page's headings only, per the KB's declared plan (page over its size threshold, no digest); applicability: generic done-definition/verification guidance, N/A to a consumer-contract change (framework already carries it).
- Roundtable 2026-11-13 (3 read-only seats, 20 findings): 17 accepted into spec/ADR, 1 rejected (AGENTS.md clause carries owner-amended kb-plain-entry AC-5), 2 merged into the owner cap question (answered: raise only for feature/arch-change).
- Owner reminder (chat 2026-11-13): honor prior-wave memory + project philosophy; cover differing adopter setups. Applied in spec §Adopter situations.
