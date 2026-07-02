---
template: false
description: Work Log — harden + dogfood the ADR-009 knowledge_sources KB-consumption seam. Roundtable right-sized it: cut the vacuous resolver/fixture-eval and the security-theater path guard; center the real dogfood; add ${KB_PATH} + trust-model docs.
---

# Work Log: arch/kb-seam-hardening

## Header

- Branch: `arch/kb-seam-hardening`
- Classification: `feature`
- Classified by: `claude-opus-4-8`
- Frozen: `2026-06-21`
- Created Date: `2026-06-21`
- Owner: `claude-opus-4-8 (luvseldom@gmail.com)`
- Guardrails Mode: `Full`
- Current Phase: `spec`
- Checkpoint SHA: `f4055d0`
- Recommended Skills: `red-team-adversarial, production-readiness, doc-lookup, kb-consult`
- Primary Domain Snapshot: `downstream-adaptability`
- SSoT Sequence: `82`

---

## Session Info

- Agent: `claude-opus-4-8`
- Session: `2026-06-20 23:56 UTC`
- Platform: `claude-code`
- Downstream-Capabilities: none (no committed config; dogfood adds a gitignored one)
- Override: none

---

## Task Description

A cross-project reference (user-provided, DATA) raised KB-wiring issues. Verified: §6.1 does
NOT reproduce; §6.2 (validator lints shape, no path guard) and §7 (no behavioral consumption
test) hold. A 3-expert roundtable on the design **diverged** (A/B "build carefully" vs C "don't
build vacuous machinery — dogfood for real"). Synthesis: fix all four issues with the RIGHT
mechanism (not cargo-culted): center a real dogfood consult; add `${KB_PATH}` + trust-model
docs; add ONE LLM-in-loop injection-decline eval; CUT the agent-unused resolver/fixture-pytest
and the legit-KB-breaking path guard.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-06-20T23:56Z | initially architecture-change |
| (reclassify) | done | 2026-06-21T00:10Z | architecture-change → feature (roundtable right-sized; rationale in Drift Log) |
| spec | in-progress | 2026-06-21T00:10Z | extend knowledge-source-seam.md: AC-11 ${KB_PATH}, AC-12 trust model, AC-13 injection eval |
| plan | pending | — | gate block + target files |
| implement | pending | — | docs/prose/config/.example/eval + dogfood |
| review | pending | — | independent fresh-context subagent |
| test | pending | — | dogfood end-to-end consult (real KB) + eval-harness run |
| handoff | pending | — | — |
| ship | pending | — | PR (no merge — left for owner) |

---

## Phase Summary

- **bootstrap**: classified architecture-change; grounded the dogfood KB (schema_v2, 69 pages,
  36 checklists, manifest+llms.txt, entry.routing_playbook, ~368K tokens); no preset env var.
- **design/roundtable (in adr slot)**: 3 parallel experts. Decisive fact: consumption is
  agent-prose-driven (no engine). Therefore a resolver+fixture pytest tests code the agent never
  calls = vacuous-green-in-Python + invents the engine ADR-009 rejected (+ breaks no-Python). A
  containment path guard breaks the legitimate out-of-repo KB and defends a non-existent threat
  (self-authored gitignored path). **Resolution: CUT resolver/fixture-pytest + path guard; CENTER
  the real dogfood; KEEP ${KB_PATH} (user-requested, adopter value) + trust-model docs + ONE
  LLM-in-loop injection-decline governance-eval case (non-vacuous).** Right-size → feature.
- **implement**: built all additive changes (config.yaml `kb_path_env`, governance.yaml
  injection-decline case, committed `.example`, bootstrap §1b `${KB_PATH}`+fail-closed prose, guide
  `${KB_PATH}`+trust-model, ADR-009 trust sentence, gitignored dogfood config). Dogfood consult
  captured (495 tok, 17.9×/745×). **Two real bugs surfaced by actually running the validator**
  (test-behavior-not-prose): (1) the strict parser rejects unquoted `:`/`{}` → quote paths;
  (2) it rejects ALL trailing inline comments (only full-line `#`) — a PRE-EXISTING latent footgun
  in the shipped guide example too. Both fixed across dogfood config / `.example` / guide.
- **review (NOT READY → fixed)**: independent acx-reviewer caught the trailing-comment fail-close
  (BLOCKING: dogfood config + `.example` failed their own validator → validate.sh RED). It judged
  the three cuts correct + nothing half-built, scope clean, framing honest, canaries intact, validator
  unchanged. Fixed all three files to full-line comments + documented the "comments on own line"
  rule; re-verification in progress (configs + guide block + validate.sh).

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-06-20T23:56:51Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-06-21T00:15:00Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-06-21T00:40:00Z
- Gate: review | Verdict: NOT READY | Classification: feature | Timestamp: 2026-06-21T01:05:00Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-06-21T01:15:00Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-06-21T01:30:00Z
- Gate: test | Verdict: PASS | Classification: feature | Timestamp: 2026-06-21T01:35:00Z
- Gate: handoff | Verdict: PASS | Classification: feature | Timestamp: 2026-06-21T01:40:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | docs/adr/ADR-009-knowledge-source-consumption-seam.md | seam being hardened (doc-clarified, not amended) |
| Spec | docs/specs/knowledge-source-seam.md | extend with AC-11/12/13 |
| Guide | .agentcortex/docs/guides/connecting-a-knowledge-base.md | ${KB_PATH} example + trust model |
| Reference | (user-provided cross-project doc, in chat) | DATA only |
| KB (dogfood) | C:\Users\wen\.gemini\antigravity\playground\knowledge-base | real KB; absolute out-of-repo git clone |

---

## Known Risk

- **§6.2**: NO containment guard (would break the out-of-repo KB; threat model empty). Mitigation
  = explicit trust-model doc + fail-closed-to-absent resolution prose + documented "why not".
- **§7 vacuous-green**: resolver+fixture pytest CUT (would test agent-unused code). Real evidence
  = dogfood consult + token economics; security property (injection-decline) = LLM eval case.
- **${KB_PATH}**: must preserve present-only (read env var only when a block is present); literal
  paths unchanged; cross-platform (bash/PowerShell/cmd); validator UNCHANGED. `.example` must live
  OUTSIDE the gitignored `context/private/` dir (else CI can't see it).
- **Dogfood is point-in-time evidence**, not a regression gate — labeled honestly.

---

## Conflict Resolution

- **Roundtable divergence (A/B build vs C cut)** resolved by the decisive fact that consumption is
  agent-prose-driven: adopted C's cuts (no resolver/fixture-pytest, no path guard) + A's two cheap
  additive docs (`${KB_PATH}` interpolation, trust model) + B's ONE non-vacuous LLM injection-decline
  eval case. Rejected B's shared resolver (the agent's real consult is Read+reason, not a Python
  call → testing it is still vacuous; also contradicts ADR-009 no-engine + no-Python).

---

## Skill Notes

none

---

## Drift Log

- **Reclassified architecture-change → feature** (2026-06-21). Rationale: the roundtable cut every
  architecture-touching workstream (resolver/engine, path-trust-model code, enforcement-tier change);
  what remains changes NO ADR-009 decision — a small additive `${KB_PATH}` resolution + honest docs
  + one eval case + a dogfood verification = feature weight. Explicit reclass (rollback→CLASSIFIED,
  re-run gate), not a silent downgrade.
- ADR-009 will receive a clarifying Consequences sentence (trust model) — doc maintenance within the
  feature, not a new ADR decision.
- **Env var aligned to `ACX_KB_PATH`** (was `KB_PATH`) per maintainer pointer to the private upstream.
  Mined the NAME/convention ONLY; NO upstream repo name/path/ID enters any committed agentic-os
  artifact (the dogfood config's literal KB path is gitignored, never shipped). Kept agentic-os's
  plural `knowledge_sources` registry + `path`/`entrypoint` schema — the upstream's single
  `manifest_path` is the intended fork divergence (this also explains the reference's §6.1 "drift":
  it was upstream-`manifest_path`-vs-our-`entrypoint`, NOT an internal contradiction). `ACX_KB_PATH`
  = clone root; examples unified to `path: "${ACX_KB_PATH}"`.

---

## Design Reference

none

---

## Observability

none

---

## Resume

- **State**: SHIPPED-pending-merge (PR opened, NOT merged). All gates green; validate.sh CI-equiv fail=0.
- **Completed**: `${ACX_KB_PATH}` resolution + trust-model docs (no guard) + 1 injection-decline eval +
  §6.1 vocab pin + committed `.example` + dogfood. Two bugs found+fixed (path quoting; full-line-comment
  fail-close, incl. a pre-existing latent footgun in the shipped guide). Env var aligned to upstream `ACX_KB_PATH`.
- **Next**: owner reviews + merges PR; the ship commit carries the current_state.md Spec Index + Ship
  History entries; post-merge → archive this log + INDEX.jsonl chain append.

### Read Map
- `docs/specs/kb-seam-hardening.md` — the ACs + Domain Decisions + CUT rationale
- `docs/adr/ADR-009-...md` Consequences — the trust-model sentence
- `.agent/workflows/bootstrap.md` §1b (`${ACX_KB_PATH}` resolve+fail-closed) + §3.6 (`kb-consult` row)
- `.agentcortex/docs/guides/connecting-a-knowledge-base.md` — adopter guide + Trust model + YAML rule

### Skip List
- `validate_downstream_capabilities.py` — UNCHANGED by design (a path guard here was rejected); do not touch
- a `kb_consult.py` resolver / fixture-KB pytest — CUT (vacuous-green; the agent never calls it)

### Context Snapshot
- Consumption is **agent-prose-driven** (no engine) — that is WHY the resolver/fixture-pytest/path-guard were cut.
- Dogfood: real consult on the live KB → **495 tok, 17.9× vs full page / 745× vs full KB**; injection eval
  green (`test_governance_eval` 31 passed). Both are point-in-time / measured-when-run, not always-on gates.
- **YAML gotcha**: capabilities file = full-line comments ONLY; quote `:`/`${}` paths (forward slashes).
- The 2 validate.sh FAILs are the pre-existing gitignored `codex-research-main.md` (local-only; CI fail=0).

---

## Test Gate Results

- `validate.sh` CI-equiv **fail=0** (2 local FAILs = pre-existing gitignored `codex-research-main.md`).
- `validate_downstream_capabilities.py` accepts the dogfood config + `.example` + the guide block (rc=0 each).
- `test_governance_eval.py` 31 passed (injection-decline `protects:` anchor resolves); `test_capabilities_schema_gate_safety.py` 47 passed UNCHANGED.
- Dogfood consult evidence captured (see ## Evidence). Two independent fresh-context reviews: NOT READY → PASS.

---

## Evidence

- **Dogfood consult (real KB, AC-6)**: task "add retry + error handling to an API call" →
  `task_routing` → slug `19_error-handling-and-resilience` (`wiki/standards/19_...md`). Pulled its
  14-item `## 自我稽核 Checklist` (real `/review` criteria: timeout discipline, idempotent retries,
  circuit breakers, DLQ, zero silent catch) + 11 `**AI 最常漏掉**` lines (real `/plan` risks).
  **Economics**: surgical checklist-only = **495 tok** vs full page 8,876 (**17.9×**) vs full KB
  368,624 (**745×**). **Honest caveat**: a naive 4-page over-route = 36,620 tok = 0.7× of
  full-manifest-paste (WORSE) → the ~17× win requires consult discipline (ADR-009 ≤3-page cap +
  section extraction). Raw transcript: `AppData/Local/Temp/acx_dogfood_consult.txt`.
- Pending: governance-eval injection-decline run + validate.sh parity (test phase).
