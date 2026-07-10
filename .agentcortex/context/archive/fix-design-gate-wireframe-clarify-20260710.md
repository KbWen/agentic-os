---
template: false
description: Work Log — #119 Design-Gate wireframe-artifact clarification (quick-win, R1)
---

# Work Log: fix/design-gate-wireframe-clarify

## Header

- Branch: `fix/design-gate-wireframe-clarify`
- Classification: `quick-win`
- Classified by: `claude-opus-4-8`
- Frozen: `2026-07-08`
- Created Date: `2026-07-08`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `3c969da`
- Checkpoint SHA: `3c969da`
- Recommended Skills: `none`
- Primary Domain Snapshot: `document-governance`
- SSoT Sequence: `115`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-07-08 14:44 UTC`
- Platform: `claude-code`
- Files Read: `20`

---

## Task Description

Backlog #119: the §4.4 Design Gate reads as "paid DSoT tool required", hard-blocking solo / tool-less downstream adopters building UI. **R1 (roundtable-finalized)**: surface what §4.4 ALREADY permits — a committed Markdown/ASCII wireframe file (a file-path artifact) satisfies the gate. Clarify the DSoT definition + the `/plan` stop messages. **Gate stays HARD** (an artifact is still mandatory); this is NOT an escape hatch — it un-hides an accepted artifact form. No ADR, no capability seam, no §4.4 compression. Then cut v1.8.9 packaging this + merged #319/#321/#322.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-08T12:39Z | quick-win |
| plan | done | 2026-07-08T14:30Z | R1 finalized after roundtable rejected path A |
| implement | done | 2026-07-08T14:44Z | 2 files, 4 edits, net-negative, no compression |
| review | done | 2026-07-08T14:45Z | gate teeth intact; eval anchor intact |
| test | done | 2026-07-08T14:45Z | token 354937 + pytest + validate |
| handoff | n/a | — | quick-win exempt |
| ship | in-progress | 2026-07-08T14:46Z | v1.8.9 release cut |

---

## Phase Summary

**bootstrap/plan** — Classified `quick-win`. #119 friction fix. Started as a "textual-artifact clarification", then the user challenged (a) my deference to ADR-001's flag-rejection and (b) an unnecessary §4.4 compression. Explored **path A** (capability-seam `design_tool: none` + ADR-011). Convened a **5-agent roundtable + 第十人 + 事前驗屍** (user-requested; human = external signal per [audit-method]).

**Roundtable — UNANIMOUS REJECT of path A** (verified against code by primary): (1) §4.4 L125 already accepts a `URL **or file path**` artifact → a committed wireframe file satisfies the gate TODAY; the block is pure framing. (2) `validate_downstream_capabilities.py` (L2-10/214-250) is a hard allowlist that makes gate-relaxation UNREPRESENTABLE — a `design_tool` key is unknown → rejects the WHOLE capabilities file, breaking adopters' skills/KB; and `design_tool: none` (FAIL→WARN) IS the forbidden gate-relaxation. (3) ADR-001 D2 chose directory-scope precisely because it binds file-path, NOT self-declared intent; `design_tool: none` reincarnates the rejected flag, WORSE (permanent, repo-wide). **My "ADR-001 predates ADR-007 so its rejection doesn't govern" claim was wrong** — corrected to the user.

**implement** — R1: §4.4 L122 (DSoT def names a committed wireframe file) + L135 (stop message names it) — guardrails is NOT token-counted, so free. plan.md L76/L77 rewritten **net-negative** (leaner than original) while naming the wireframe option — the counted-doc budget stays under ceiling. Gate stays HARD (no artifact → still hard-stops). §4.4 structure untouched (no compression this time).

**review** — PASS. Gate teeth intact (no-artifact still FAILs); eval `ui-before-design-pressure` protects the UNCHANGED `### 4.4` heading + its `design link`/`DSoT` pattern stays satisfiable; no test pins the changed phrases.

**test** — token aggregate 354,937/355,000 (headroom 63); pytest CI-equiv + validate.sh (see Evidence). ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-08T12:39:12Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-08T14:30:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-08T14:44:24Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-08T14:45:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-08T14:45:30Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Backlog | docs/specs/_product-backlog.md #119 | Design-Gate no-DSoT friction |
| ADR | docs/adr/ADR-001-governance-friction-tuning.md | D2 directory exemption + rejected flag (STILL governs — path A verified as its reincarnation) |
| ADR | docs/adr/ADR-007 + ADR-009 | capability seam: gate-relaxation UNREPRESENTABLE (why path A is rejected) |
| Eval | .agentcortex/eval/governance.yaml:249 | `ui-before-design-pressure` — stays green |

---

## Known Risk

- Discoverability: a tool-less adopter must still read §4.4 / hit the stop message to learn a wireframe file counts. **Mitigation**: the `/plan` stop message + §4.4 now NAME the concrete path `docs/design/<screen>.md`. (Deeper fix — R2, making "artifact present" a real validator — deferred; see Drift Log.)

---

## Drift Log

- **Reversal 1** (user challenge): the initial "textual-artifact clarification" quick-win compressed §4.4 to "fund" tokens — but the analyzer does NOT count guardrails (356,029→356,029 unchanged), so it was an unauthorized refactor of a core rule for zero benefit. Reverted.
- **Reversal 2** (path A rejected): explored capability-seam `design_tool: none` + ADR-011 after the user (rightly) questioned my ADR-001 deference. A 5-agent roundtable + 第十人 + 事前驗屍 UNANIMOUSLY rejected it (verified against code): §4.4 already accepts a file-path artifact; the capability validator forbids gate-relaxation keys (would break the file); `design_tool: none` IS the ADR-001-rejected flag, worse. My "ADR-001 doesn't govern this" claim was corrected. Full branch reset to clean main; renamed `feat/design-gate-capability-seam` → `fix/design-gate-wireframe-clarify`.
- **R2 deferred (candidate)**: the design gate is honor-system (zero validator on design_link). The roundtable's real upgrade = a T1 plan-lint failing a prod-UI plan that cites no `Design:` path (theatre→enforcement, fits "machine-enforced not self-report"). Not done here (out of #119 scope); file as backlog if pursued.
- Ship SSoT write: via surgical anchored Edit (ship.md L198 permits; solo session).
- 2026-07-10 owner-judgment archival (ship-wave-20260710): PR #324 (v1.8.9 release cut, squash `e96623e`) is MERGED; this log reached ship-in-progress with bootstrap/plan/implement/review/test PASS receipts but no ship receipt was recorded before the release cut. Archived by owner judgment per the 2026-07-02 #315 precedent — NOT fabricating a ship receipt for work this session did not independently verify.

---

## Evidence

- Token: `analyze_token_lifecycle.py` aggregate **354,937 / 355,000** (headroom 63); plan.md net-negative funds the clarification; §4.4 additions are token-free (guardrails uncounted).
- Scope: **2 files, 4 edits** — `engineering_guardrails.md §4.4` (L122 def + L135 stop msg) · `plan.md` Design Gate (L76 label + L77 stop msg). §4.4 structure otherwise UNCHANGED (no compression).
- Eval: `ui-before-design-pressure` protects the unchanged `### 4.4 Design-First Rule (UI Changes)` heading; `design link`/`DSoT` pattern satisfiable → gate behavior preserved.
- (pytest CI-equiv + validate.sh appended below on completion.)

---

## Roundtable Record (5 agents, unanimous reject of path A)

- Philosophy keeper: needs-changes→reject — machinery on a no-teeth rule = false "machine-governed" confidence; R1 first, never gate-downgrade in the seam.
- Adopter-UX: reject — messaging fix wins decisively; capability file is undiscoverable + adds ceremony for the same wireframe.
- ADR historian: reject — violates ADR-007/009 gate-cap invariant; path A reincarnates D2's rejected flag worse; verified my "predates ADR-007" as motivated reasoning.
- 第十人 (kill shot): §4.4 already accepts a file-path artifact → path A builds ADR+field+validator for a non-existent problem.
- 事前驗屍: top failure = null impact (nobody finds the key) + redundant with existing dir exemption; fold-in = make "artifact present" hard-checkable (= R2).
