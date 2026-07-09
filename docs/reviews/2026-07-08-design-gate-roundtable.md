# Design-Gate Friction (#119) — Roundtable Decision Record — 2026-07-08

Scope: how to resolve backlog **#119** (the §4.4 Design-First gate hard-blocks a solo / tool-less downstream adopter from planning UI work). Cross-platform decision record so non-Claude sessions have the full context, not just the distilled backlog note.

Method: two candidate fixes were on the table; a **5-agent roundtable + 第十人 (tenth-man, refute-only) + 事前驗屍 (pre-mortem)** was run (read-only, user-requested). All agents were same-vendor (Claude), so per the `[audit-method]` Global Lesson the **human operator was the external signal** and adjudicated. Every load-bearing claim was re-verified against code by the primary before acting.

## Decision

- **SHIPPED: R1 — a framing clarification** (v1.8.9, PR #324). `engineering_guardrails.md §4.4` + the `/plan` Design Gate now name a committed **Markdown/ASCII wireframe file** (`docs/design/<screen>.md`) as a valid design artifact. **The gate stays HARD** — a UI task with *no* artifact still hard-stops at `/plan`.
- **REJECTED: path A — a capability-seam `design_tool` escape** (`downstream-capabilities.yaml` opt-in + a new ADR-011 superseding ADR-001 D2). **Do NOT retry this.**
- **DEFERRED: R2** — make the (honor-system) design gate a real validator, or delete it. Folded into backlog **#122** (Honor-system MUST pass), not a new row.

## Why path A was rejected (verified against code)

1. **§4.4 already accepts a file-path artifact.** [`engineering_guardrails.md`](../../.agent/rules/engineering_guardrails.md) §4.4 step 1: "MUST produce a linkable artifact (URL **or file path**)". A committed wireframe file always qualified — only the wording ("Default tool: Stitch", "Create the design in [DSoT tool]") hid it. So R1 *un-hides* what the rule already permits; it is not a new escape. The "problem" path A solved barely existed.
2. **The capability seam forbids gate-relaxation by construction.** [`validate_downstream_capabilities.py`](../../.agentcortex/tools/validate_downstream_capabilities.py) is a hard **allowlist** of top-level keys `{version, skills, subagent_policy, trackers, knowledge_sources}` + `FORBIDDEN_KEYS {gate, ship_edge, block_if_missed, …}`; its docstring: "Makes gate-relaxation UNREPRESENTABLE." A `design_tool` key is unknown → the validator **rejects the whole file** → breaks an adopter's existing skills/KB. And `design_tool: none` (FAIL→WARN) *is* the forbidden gate-relaxation. Making path A work would require deleting the invariant the seam exists to enforce (ADR-007 §4 / ADR-009 D5).
3. **ADR-001 Decision 2 still governs** (the primary's earlier "predates ADR-007, so its rejection doesn't apply" was **wrong** — corrected on record). D2 chose directory-scope *precisely because it binds file-path, not self-declared intent*. A repo-level `design_tool: none` is self-declared intent and a permanent, repo-wide switch — it reincarnates the "Prototyping Mode flag" D2 rejected, and "nothing more permanent than a temporary workaround" applies *harder*. ADR-007 did not open a door around D2; it structurally closed the same door.

## Roundtable verdicts (unanimous reject of path A)

| Seat | Verdict | Core point |
|---|---|---|
| Philosophy keeper | reject | Machinery on a no-teeth rule = false "machine-governed" confidence; R1 first; never put a gate-downgrade in the seam. |
| Adopter-UX | reject | Messaging fix wins decisively; a gitignored capability file is undiscoverable + adds ceremony for the same wireframe. |
| ADR historian | reject | Violates the ADR-007/009 gate-cap invariant; reincarnates D2's flag, worse; verified "predates ADR-007" as motivated reasoning. |
| 第十人 (kill shot) | refute | §4.4 already accepts a file-path artifact → path A builds an ADR + field + validator for a non-existent problem. |
| 事前驗屍 | fail-modes | Top failure = null impact (nobody finds the gitignored key) + redundant with the existing directory exemption; fold-in = make "artifact present" hard-checkable (= R2). |

## Follow-ups

- **R2 (backlog #122)**: enforce-vs-delete the honor-system design gate. CAUTION recorded: enforcing *adds* adopter friction — weigh against the conversion thesis (#120/#121).
- **Discoverability (pre-mortem #1)**: R1 names the concrete path `docs/design/<screen>.md` in the stop messages so a tool-less adopter learns "what counts" at the wall. An optional `docs/design/_wireframe.template.md` skeleton was noted but not built.
