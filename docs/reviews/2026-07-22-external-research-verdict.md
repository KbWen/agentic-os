---
status: point-in-time
title: External-Repository Research Verdict — Tracked Summary
date: 2026-07-22
source: codex research session (roundtable + tenth-person + premortem deliberation), primary-verified by the executing Claude session
---

# External-Repository Research Verdict — 2026-07-22 (Tracked Summary)

This is the **fresh-clone-resolvable provenance record** for the 2026-07-22 external-research wave
(PRs [#358](https://github.com/KbWen/agentic-os/pull/358), [#359](https://github.com/KbWen/agentic-os/pull/359),
[#360](https://github.com/KbWen/agentic-os/pull/360)). The full working note lives in the researcher's
local gitignored `context/private/` research file per the #76 persist-before-browse convention; this
summary is the reviewed distillation of its decision-bearing content. Recorded 2026-07-22 as a
post-ship follow-up after review feedback that tracked records referenced only the gitignored path.

## Scope of the research

A read-only survey of external workflow/spec, agent-runtime, evaluation/security, and
interoperability/packaging repositories (spec-kit, superpowers, gh-aw, inspect_ai, conftest,
BMAD, buildermethods agent-os, promptfoo, in-toto, Pydantic AI, LangGraph, MS Agent Framework,
symphony, DBOS/Temporal, ACP, MCP registry, OTel GenAI, and others), deduplicated against
shipped ADRs/specs and the active backlog. External repository content was treated as untrusted
data throughout.

## Verdict (after roundtable + tenth-person + premortem deliberation)

Core finding: **the external repositories prove useful mechanisms exist; they do not prove this
project has a consumer for them.** The initially drafted import sequence was withdrawn.

### Survived as executable candidates (all executed or routed 2026-07-22)

- **#113** — credibility fix: no unqualified top-line PASS when required checks are skipped. **Shipped PR #359.**
- **#107** — isolated precision fix in the eval coverage matcher. **Shipped PR #358.**
- **#89** — records-only reconciliation (enforcement had shipped 2026-07-17 via PR #345). **Row flipped in PR #359.**
- **#121** — README honesty correction (capability/enforcement matrix). **Remains the top pick; next unit.**
- **#77** — Task/Step schema: corroborated externally but no fresh local pain signal → **revalidate via #124 before any implementation**.

### Parked (reopen criteria required before any work)

- **#33 production packaging code** — mapping spike only first; any prototype must self-describe as a workflow companion, report `guidance installed / enforcement off`, and require source pinning + byte verification. Reopen: lossless Claude/Codex/Copilot field mapping proven + a product decision to promise standalone packaging.
- **#70 structured ship-receipt export** — reopen ONLY when an independent validator/CI computes digests, a real CI/PR consumer exists, and the artifact is named an *evidence envelope*, never "attestation".
- **#78 task capsule + read-only reviewer** — reopen only as an A/B test whose high-priority defect yield justifies token/wall-time cost; quick-win stays exempt.
- **#79 skill-effectiveness harness** — parked behind #77/#78.
- Durable approval envelopes / checkpoint schemas / autopilot runtime work — reopen on a real autopilot consumer.

### Killed (do not re-propose absent new evidence)

- Unsigned self-produced "attestation" (an unsigned self-produced receipt must not claim authenticated attestation).
- Raw prompt/tool-argument telemetry (also conflicts with the project's standing no-telemetry rule).
- OPA/Rego, Promptfoo, Inspect, LangGraph, Temporal, DBOS, or any second governance framework as core dependencies.

### Experiments explicitly NOT run this wave (recorded deviation, primary judgment)

#142 reachability probe, three-client scaffold-skill discovery reproduction, and plugin
field-mapping spike were deliberately not executed: no current consumer, and #121 outranks them.
The codex-proposed activation metrics (install-to-self-check rate, hook/CI enablement, D7) are
unmeasurable under the project's no-telemetry rule; #121 measurement scopes to GitHub-native
signals only.

## Routing

All dispositions above landed via the product backlog (rows #89/#107/#113 flipped Shipped; new
row #143; the 2026-07-22 dated note carries the deviation record and verdict constraints). No
pending routing_actions from this snapshot.

## Errata (wave records)

- The archived delegate Work Log `archive/fix-no-python-reduced-assurance-20260722.md` carries an
  internally inconsistent `## Phase Sequence` table (`implement: active`, `ship: pending`) alongside
  a valid `Gate: ship | Verdict: PASS` receipt — the delegate updated receipts but not the table.
  Archives are immutable (rotated/archived verbatim), so the file is NOT edited in place; final
  state of that work unit = shipped and merged via PR #359. Recorded here as the erratum of record.
- The wave's Ship History entry and the backlog's 2026-07-22 note originally cited only the
  gitignored private research note as provenance; this tracked summary is the follow-up fix. The
  live SSoT entry gained an additive pointer to this file (guarded write, logged in the follow-up
  unit's Work Log Drift Log); the shipped entry text was otherwise left as written.
