---
status: shipped
frozen: 2026-11-12
date: 2026-11-12
classification: feature
primary_domain: governance
signal_tier: T3
signal_tier_note: "Observer: repo owner. Behaviour was measured on 2026-11-12 (headless Sonnet runs, table below); no validator can see whether an agent named a design artifact in chat."
---

# UI Design on Any Entry

## Goal and relationship

The Design-First rule (`engineering_guardrails.md` §4.4) is reachable only through `/plan`: `bootstrap.md` §0 tells quick-win agents not to read the guardrails, and a task given without a slash command reads no workflow. A 2026-11-12 simulation showed the result: the same request ("add an account settings screen") stopped at the design gate under `/plan` and was built with no design artifact when asked plainly.

EXTENDS the Design Gate (`plan.md`); it does not change it. The gate stays hard at `/plan`. No capability key, validator check or hook is added.

## Scope and targets

- Add one bullet to `AGENTS.md` §vNext State Model, after "Knowledge base on any entry":
  `**UI on any entry**: before editing user-visible UI under production dirs (not tools/scripts/tests), name its design artifact (DSoT link or committed docs/design/<screen>.md). None → say so and offer to draft the wireframe file first; /plan enforces this as a hard gate.`
- Pay for it in the same file: shorten the Context Pruning bullet: drop the sentences from "Premature handoff resets the warm prompt cache" to the end of the turn-count sentence, and keep turn-count named as a coarse fallback in five words (`handoff-trigger-policy.md` AC-1 requires that label). `token-governance.md` §6.1 already holds that detail, and the bullet keeps its pointer to it.
- Regenerate `.agentcortex/metadata/trigger-compact-index.json` if its source hash changes.

## Evidence (2026-11-12, Claude Sonnet 5.5, headless sessions in a deployed downstream repo)

| Cell | Runs | Result |
|---|---|---|
| New screen, no design artifact, baseline text | 3 | 2 built it without mentioning design; 1 stopped on its own citing §4.4 |
| New screen, no design artifact, this bullet | 6 | 6 named the missing artifact and offered a wireframe before any edit under `src/` |
| Same, prompt states a style (dark, orange accent) | 2 | 2 stopped; the offered wireframe carried the stated style |
| Same, app already has a distinctive stylesheet | 1 | stopped; the offer reused the existing header, stylesheet and button class |
| Text tweak to an existing screen | 2 | 0 stopped; both made the edit |
| Backend-only task in `src/` | 2 | 0 mentioned design; both completed |
| UI file under `tools/` | 2 | 0 mentioned design; both completed |
| New screen with an approved `docs/design/` file | 2 | both built from the design (its colour value is in the product) |
| Reply "yes, draft it and build" to one stopped run | 1 | wrote the wireframe file and built the screen |

Every no-artifact new-screen run stopped and waited after the offer. An adopter without a design file therefore spends one extra exchange per new screen.

A second wording ("write the wireframe yourself and build, say it is unapproved, do not wait") was run 11 times. It built without stopping and reused existing styles, but it writes UI before anyone has agreed to the design, and it is longer than the deletion that pays for it. Not adopted.

### Follow-up batch on the merged wording (2026-11-13, fixtures deployed from this branch)

Six two-turn sessions, four with a real external knowledge base declared. This batch lowers the figures above and is the more honest picture:

| Cell | Result |
|---|---|
| New settings screen, Sonnet (3 runs) | 2 stopped and offered a wireframe; 1 wrote the design file itself and built without waiting |
| "Add a notes list screen" rendered into the existing page, Sonnet (2 runs) | 0 stopped; one wrote the wireframe after the code, one skipped it and said so when asked |
| New settings screen, Haiku (1 run) | ignored the bullet and the knowledge base |

Across both batches Sonnet stopped on 11 of 14 new-screen tasks, against 1 of 3 without the bullet. The bullet raises the rate; it does not guarantee it, and a screen added inside an existing page is the weak case.

The bullet governs process, not quality. Where the agent drafted its own wireframe after a yes, the built screen was as bare as with no rule at all (browser-default styling); screens were only visibly designed when the user, a design file or an existing stylesheet supplied the design. Reading the knowledge base added form helper text and a loading state but did not change the look.

## Acceptance Criteria

- AC-1: `AGENTS.md` carries the bullet above and no longer carries the deleted tail; the file is smaller than at `b1bc39b`.
- AC-2: the directive-count ratchet passes with the baseline unchanged (the bullet uses none of the counted keywords).
- AC-3: the full CI-equivalent suite passes; `validate.sh` and `validate.ps1` report `fail=0`.
- AC-4: the lifecycle token figure does not rise.

## Not measured, and reopen triggers

- Other platforms (Codex, Gemini, API). Haiku ignored the bullet in its one run. Reopen if a comparison shows the bullet ignored or over-applied elsewhere.
- Only one kind of small edit was run (a link label, 2 runs, not stopped). Reopen and narrow the wording, or withdraw the bullet, on the first report of a small edit being stopped.
- One product fixture; n is 6 or less per cell, and 1 for two cells.

## Non-goals

- Machine enforcement of design-reference presence (backlog #122).
- Any change to `/plan`, `/implement` or `/review` design checks.

## Domain Decisions

- [DECISION] The design rule is stated once on the always-loaded surface, worded as naming an artifact, because the 2026-11-07 comparison found output-shaped lines are followed on plain entry and process rules are not. This supersedes the 2026-11-07 "accept ungoverned plain-entry quick-wins" outcome for UI work only (owner decision in chat, 2026-11-12).
- [TRADEOFF] An adopter with no design process gets one extra exchange per new screen; in return the same request no longer has two outcomes depending on phrasing.
