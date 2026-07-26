# Compaction overflow: feat/conflicting-directive-scan (2026-07-26)

Offloaded from the active Work Log per `handoff.md §6` (16.3 KB > `worklog.max_kb: 12`).
This is compaction overflow of a STILL-ACTIVE log, not final archival.

## Phase Summary

- Compaction overflow only. The authoritative phase record stays in the ACTIVE log at
  `.agentcortex/context/work/feat-conflicting-directive-scan.md`; this file holds offloaded
  detail. Retained here so the archived-log scan has a section to read.


## Evidence (pre-review, full detail)

- Branch from `main` @ `f765a594bd5a14fd83762e968e31b78371c6db27`.
- ADR coverage (`check_adr_coverage.py` over AGENTS.md, engineering_guardrails.md,
  bootstrap.md, .claude/commands, the prospective review snapshot): **exit 0 — covered**.
- Surfaces loaded for the census: `AGENTS.md` (auto-injected), `engineering_guardrails.md`
  (full, 433 lines), `security_guardrails.md` (74 lines), `shared-contracts.md` (63 lines),
  plus `bootstrap.md`, `plan.md`, `implement.md`, `ship.md`, `state_machine.md` read earlier
  this session.
- **Census complete — 10 confirmed findings + 1 negative result**, written to
  `docs/reviews/2026-07-26-conflicting-directive-scan.md`. Every row carries a file:line
  citation and passed the precedence test (a candidate counts only if the declared chain does
  NOT resolve it, or resolves it silently with no gate).
- **Root-cause finding (M1)**: `AGENTS.md §Skill Safety & Precedence` item 2 declares
  `AGENTS.md > .agent/workflows/ > .agent/skills/` and **omits `.agent/rules/*`,
  `.agentcortex/templates/*`, and `docs/adr/*`** — the surfaces carrying most directives
  (`engineering_guardrails.md` alone holds 84 hard-directive hits per the ratchet baseline).
  For most rows there is therefore no declared tie-breaker at all. Fixing this outranks
  fixing any individual row.
- **Category C is machine-checkable** (6 rows): a rule naming a Work Log `## Section` can be
  validated against `.agentcortex/templates/worklog.md` (19 sections). Built and ran an AST-free
  reference sweep: 37 distinct `## X` references across the surfaces, 20 absent from the
  template, **6 genuine after filtering** the ones that legitimately name sections of
  `current_state.md` / spec files / ADRs. This is the only slice where an ADR-011-style durable
  instrument looks feasible.
- **Two findings were violated silently by this session's own Work Logs**: C3 (`plan.md`
  mandates a `## Risks` block; the template provides `## Known Risk`) and C4 (`bootstrap.md`
  says write `## Recommended Skills` as a section; the template carries it as a header field).
  All three logs written tonight followed the template, so both workflow instructions went
  unfulfilled — and no gate, validator, or review noticed.
- **E1 fired live in this session**: `guardrails §9.1` says `好` MUST NOT trigger execution;
  `AGENTS.md` Runtime item 6 says explicit intent executes in the same turn. The agent asked
  "要我進 /implement 嗎?", the user answered "好喔", the agent proceeded. §9.1 is already dead
  text for the answer-to-a-direct-question case.
- **Negative result recorded (A2)**: the #126 stub conflict is CLOSED — of 30
  `.claude/commands` stubs, only `ask-local.md:11` cites guardrails and that is the functional
  §8.2 citation #126 deliberately kept.
- No `routing_actions` block in the census by deliberate choice: `check_routing_actions.py`
  restricts `target_doc` to `^docs/(architecture|specs)/.+\.md$`, and every disposition here
  targets a governance file. Dispositions go in the spec instead, which also avoids the
  14-day pending-routing-action staleness WARN.


## Roundtable verdict table (full)

4-seat roundtable (tenth-man · pre-mortem · downstream · doctrine), all same-vendor — the
`[audit-method]` external seat FAILED (see Drift Log), so this is theatre-adjacent and every
verdict below was **primary-re-verified by me against file text** before adoption.

**Outcome: 2 of my 11 findings survived. 9 refuted, 2 of those with actively harmful fixes.**

| Row | Verdict | Verified basis |
|---|---|---|
| M1 | REFUTED | `AGENTS.md:94` is item 2 **"Workflow Precedence Rule"** under "Skill Safety & Precedence" — a skill-vs-workflow tie-breaker, not a universal hierarchy. I measured with the wrong instrument, and every "precedence test: unresolved" line rested on it. My fix would also demote the Constitution (`AGENTS.md:13` MUST OBEY, `:109` "Constitution") and create a loop: 4 ADRs declare `applies_to: AGENTS.md`. |
| A1 | REFUTED | `engineering_guardrails.md:26,38` explicitly route later reads through Read-Once / Safety Valve + Drift Log. No exemption needed; a conditional first-load is not a re-read. |
| A2 | REFUTED (wrong direction) | I declared #126 closed after grepping only `engineering_guardrails`. **23 of 30 stubs** still list `AGENTS.md` as a Required read vs `CLAUDE.md:5` (already `@import`ed) + `AGENTS.md:27`. The class is alive. |
| B1 | **SURVIVES** | Sharper form found: `AGENTS.md:35` SSoT Recovery Exception vs `:43-47` "exhaustive" list — **both sides in one file**. |
| C1 | REFUTED, **fix harmful** | `validate.sh:1691` is a bare `grep -qE '^## Security Findings'`. Adding it to the template satisfies it forever → **silently kills a live WARN**; CI misses it (tests use synthetic logs). Already tiered T1 at enumeration:133. |
| C2 | REFUTED, **fix harmful** | `## Lessons` is a presence-probe for whether `/retro` ran. Template-supplying it makes §10.6 vacuous. |
| C3 | **SURVIVES** | And is wider: 4 sites not 3 (`plan.md:169` is a **bare heading inside a fenced block** my AC-7 detector cannot see) + `token-governance.md:115`, outside both AC scopes. `handoff.md:141` vs `:148` contradict inside one file. |
| C4/C5/C6 | REFUTED | These are *create* instructions, not missing sections. Guardrails:314 calls the 6-section list a "**minimum**" contract. |
| D1 | REFUTED | ADR-011's "no `defer`" is self-scoped to NONE-tier disposition vocabulary; it never touches §8's escalate-to-user sense. |
| E1 | REFUTED | enumeration:116 row 90 already dispositions §9.1 `keep-honest-unenforced`. ADR-011 ran this exact test and chose KEEP; its reopen trigger is an incident, not "overridden twice". Texts also don't collide — `AGENTS.md:81` item 6 fires on an explicit phase request. |
| F1 | REFUTED | Closed **twice** before as my-error-not-a-gap: `feat-govern-audit-workflow-20260702.md:143` + `:164`, `feature-directive-enforcement-audit-20260719.md:161`, carried as binding precedent at `feat-local-model-delegation-20260704.md:94` ("do NOT write a `Gate: spec` receipt"). `state_machine.md:17` makes the edge artifact-triggered; `spec.md` has zero receipt instructions. |

**New findings the roundtable surfaced (adopted into the rewrite)**: AGENTS.md self-contradiction
on authority; the 23 live stubs; §10.6's `## Resume` probe is **already** vacuous (template
ships it); `## Global Lessons Candidate` (`retro.md:55`); documented `implement→review→test`
vs `LEGAL_STRICT` allowing implement→test; `§10.2` lists ADR + "check Spec Index" as
receipt-less gates, fixable with the table's existing "(advisory, no gate receipt)" annotation.

**Also verified**: `AGENTS.md` ratchet headroom is **0** (live 37 / baseline 37) and
`CI Structural Tests` is not a required check; `.agentcortex/templates/*` + `AGENTS.md` are
**scaffold** (sidecar), not force-update; `AC-10`'s instrument reads none of the changed
surfaces; both artifacts said 11 / 10 / 12 findings in three places; the spec mentioned
downstream **0** times.

**Disposition: withdraw and rewrite.** Keep the refuted rows on record so they are not
re-proposed.
