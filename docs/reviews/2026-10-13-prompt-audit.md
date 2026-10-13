---
status: review-snapshot
date: 2026-10-13
backlog: "#224, #225, #226, #227, #228"
---

# Prompt Audit: Instruction Surface vs Current Models (2026-10-13)

> Scope: every file an agent reads as instructions. That covers `AGENTS.md`,
> `CLAUDE.md`, `GEMINI.md`, the Copilot instructions, `.antigravity/rules.md`,
> `.agent/rules/*`, `.agent/workflows/*`, `.agents/skills/*/SKILL.md`,
> `.claude/commands/*`, `.claude/agents/*` and `.codex/agents/*`. Agent-facing
> guides and `.agentcortex/eval/governance.yaml` are included where a finding
> reaches them. Settings files and gitignored Work Logs are excluded. Base:
> `main` at `81a4034`.
>
> **Target models:** the root instruction files are judged against Claude
> Opus 5.5. The `acx-*` subagents pinned to `model: sonnet` are judged
> against Claude Sonnet 5.5. Both follow instructions more literally than the
> models much of this text was written for. Codex, Gemini CLI and Antigravity
> read the same files; this audit judges them only against Claude behaviour,
> so cross-platform effects are a stated limit, not a measured one.

## Verdict

- **No old-model prompting habits.** The audit found no "think step by
  step", scratchpad tags, "do not be lazy" boosters, retired model names or
  prefill scaffolds. Most of the MUST/NEVER register is normative gate
  language that the ADR-011 ratchet and the governance eval already back.
  It is kept.
- **The real defects are stale facts and contradictions between files.**
  Five domain skills point to a project ADR name that `/app-init` never
  creates. `engineering_guardrails.md` both requires and forbids pasting
  terminal output into the Work Log, in two sections that load together.
  Platform lists leave out shipped adapters. All of these are fixable
  without touching tools or validators: backlog #224 (#228 for token
  figures).
- **The behavioural findings are hypotheses, not results.** They are numeric
  chat-length caps, the "1-2 findings max" cap on red-team findings, an
  all-caps refactor slogan that the eval pins verbatim, and a vague-input
  rule that treats "fix it" as vague regardless of context. ADR-011 already
  labelled two of them (the 8-line cap, lexical-first search)
  `keep-honest-unenforced` on purpose on 2026-07-19. They are reopened only
  with eval before/after evidence: #225 and #226.
- **Why it matters for the product.** The 2026-09-26 downstream simulation
  measured framework sessions at 2.4–10.4x cost with no quality gain on
  small tasks. Instructions that literal models over-apply (asking for
  clarification after "fix it", padding a skill list to a target count,
  capping security findings) push that cost up with no product benefit.
  #225 and #226 are judged by that measure, not by line count.

## Findings

Confidence: **High** means the repository itself contradicts the text.
**Medium** means the text matches a documented pattern of current-model
behaviour. **Flag** means low confidence, or a decision only the owner can
make.

| ID | Location (at `81a4034`) | Finding | Confidence | Disposition |
|---|---|---|---|---|
| H1 | 5 domain `SKILL.md` "Project ADR" lines | Point to `ADR-002-project-architecture.md`; `app-init.md:50` creates `ADR-001-…` (or the next free number), and the template is `ADR-00N` | High | #224 |
| H2 | `engineering_guardrails.md` §12.2 vs §5.2b | "Terminal output MUST be pasted" vs "MUST NOT paste raw terminal output"; both load at `/implement` | High | #224 |
| H3 | `bootstrap.md` §2 Session Info vs `templates/worklog.md` | Platform enums disagree, and both leave out `gemini-cli` | High | #224 |
| H4 | `karpathy-principles` References | Names a `writing-plans` skill that does not exist | High | #224 |
| H5 | `methodology.md` principle 2 | Path `skills/verification-before-completion.md` does not exist | High | #224 |
| H6 | `engineering_guardrails.md` §5.4 vs `karpathy-principles` | Extract a shared abstraction at the 2nd consumer vs at 3+ ("not 2") | High | #224 (owner: third) |
| H7 | `bootstrap.md` §3.6 intro | Says "table above"; the tables are below | High | #224 |
| H8 | `context-budget.md` | "14KB guardrails … ~3,500 tokens"; the file is ~32 KB, and the same figure appears in 6 more places | High | #228 |
| M6 | `engineering_guardrails.md` §12.1, §12.4 | Claude Code tool names (`Read tool`, `Glob`) in a file every platform reads | Medium | #224 |
| M8 | `handoff.md` §2, `methodology.md` adapters | Platform lists leave out Claude Code and Gemini CLI; `.claude/commands/{write,execute}-plan.md` exist and cite methodology for parity | Medium | #224 |
| F2 | `methodology.md` principle 3 vs `bootstrap.md` §3.6 | "TDD Preferred … enforced" vs TDD skill only for feature/architecture-change | Flag | #224 (owner: follow bootstrap) |
| F3 | `karpathy-principles` simplification checklist | Splitting and extraction steps conflict with the same skill's "no drive-by refactoring" | Flag | #224 (owner: scope to touched lines) |
| M1 | `AGENTS.md` Response Brevity; `bootstrap.md` §3, `handoff.md` §3, `retro.md`, `app-init.md` partial mode | Numeric chat-length caps on top of field templates that already fix the shape; enumeration row 16 is NONE / keep-honest-unenforced | Medium | #225 |
| M2 | `red-team-adversarial` Lite mode | "≤300 tokens output", "1-2 findings max" caps a security review's findings | Medium | #225 |
| M3 | `AGENTS.md` Core Directives | "UNAUTHORIZED REFACTORING STRICTLY PROHIBITED" is the only all-caps slogan in Core Directives; eval case `unauthorized-refactor` requires the model to echo that string | Medium | #226 |
| M4 | `engineering_guardrails.md` §9.2 | Lists "fix it" as vague whatever the context; "NEVER guess intent" | Medium | #226 |
| M5 | `engineering_guardrails.md` §9.3 | Lexical-first search is strategy coaching; enumeration row 92 is NONE / keep-honest-unenforced | Medium | #226 |
| M7 | `bootstrap.md` §3.6 Rule | "Do NOT limit to 0-2 skills … typical feature 4-8 skills": phrasing relative to an old rule, plus a target count | Medium | #226 |
| M9 | `doc-lookup` Hard Rule | "When in doubt, fetch" booster plus a Claude-only tool name (`WebFetch`) | Medium | #226 |
| F1 | `engineering_guardrails.md` §1.2, §5.2, §5.2a | Dart/Flutter idioms (`fromRecord`, "return null or sealed error", `debugPrint`) in a constitution scoped to every project | Flag | #227 (owner: generalize) |
| F5 | `AGENTS.md` / `bootstrap.md` "Antigravity" section names on rules for every platform | Idiom only; renaming would break `§` references | Flag | closed |
| F6 | `CLAUDE.md`, `bootstrap.md` §0 token-savings figures | Rationale written for humans; the figures disagree with each other, and a test pins one | Flag | #228 (reopened) |
| F7 | `AGENTS.md` Context Pruning "~0.1×" cache figure | Volatile, but currently accurate | Flag | closed |
| F8 | `bootstrap.md` AC-NN labels | Traceability tags; cheap | Flag | closed |

Groups with nothing in scope: tool descriptions (no API tool definitions;
skill `description` fields are routing text) and request configuration (no
Messages-API code; the Python tools call the CLIs). The subagent roster
check passed: the five `acx-*` agents each cover one phase.

## Owner decisions (chat, 2026-10-13)

- H6: extract at the **third** consumer.
- F1: **generalize** the stack-specific rules (behavioural, so it goes to #227
  with an eval, not into #224).
- F2: TDD scope **follows `bootstrap.md` §3.6**; fix the methodology wording.
- F3: scope the simplification checklist to **lines the change touches**;
  note older code as a follow-up.
- F4 (no question asked): add `gemini-cli` to the Platform enum, because
  cross-platform parity is a standing rule.

## Adjudication (refute pass, primary-verified)

A refute-only subagent (same vendor) attacked each #224 finding. The primary
re-checked every point below against the files and by running the tools.

- **Budget blocker the audit missed.** The lifecycle aggregate is 354,726
  against 355,000, and the quick-win scenario is 29,844 against 30,000.
  Edits multiply into the aggregate: about ×16 for `karpathy-principles`,
  ×5 for `bootstrap.md`, ×4 for `handoff.md`. The proposed parentheticals,
  "(created by `/app-init`)" and a full path for `writing-plans`, would
  have exceeded the ceiling. #224 is therefore deletion-funded:
  - H1 uses the repo's existing `ADR-00N` convention.
  - H4 names `/plan` only.
  - F3 rescopes the existing checklist lead-in instead of adding a sentence.
  - H3 is paid for by deleting a claim from `bootstrap.md` §2b ("costs < 10
    tokens … eliminates phase-tracking hallucination") that nothing measures.
- **Directive ratchet.** `engineering_guardrails.md` sits at exactly its cap
  of 84. H2 keeps exactly one MUST; M6 and H6 add none.
- **H3 corrected.** Collapsing "Codex Web / Codex App" into `codex` would
  lose a distinction that `handoff.md` §2 and `ship.md` (reduced-assurance
  mode for platforms without file access) depend on. Both enums become
  `claude-code | codex-app | codex-web | gemini-cli | antigravity | api`.
- **M8 corrected.** There is no `.gemini/commands/`, so Gemini CLI is *not*
  added to the methodology alias line. It is added to the `handoff.md`
  list of platforms that can write files.
- **F2 constraint.** `hotfix.md` and karpathy §4 require a reproducing test
  for bug fixes, so the new methodology wording keeps that.
- **H8 widened and moved.** The stale "14KB / ~3,500 tokens" figure also
  appears in `context-budget.md` (three places), both quickstart guides,
  and `LIFECYCLE_BENCHMARK` (en and zh-TW). The CLAUDE.md figure is pinned
  by `test_lifecycle_skill_activation.py:780`. That also triggers F6's
  reopen condition (a test asserts the figures). H8 and F6 become #228,
  which replaces hand-carried figures with one measured source.
- **No refutations.** H1, H2, H4, H5, H6 and H7 stand; H6 is stronger than
  reported, because guardrails §5.4 contradicts its own neighbouring "3+"
  line. Required co-change: regenerate `trigger-compact-index.json`
  (`content_hash` of every edited SKILL.md). Not affected: the deploy
  golden (paths only), `lifecycle-baseline.json` (≤ +0.9% against 10%
  slack), and skill provenance (frontmatter only).

## Dispositions

- **#224 (do-now, quick-win):** H1–H7, M6, M8, F2, F3, F4. Stale facts and
  contradictions, deletion-funded (see Adjudication). Tools and validators
  are unchanged. Three rule texts do change agent behaviour, each toward a
  rule the repo already stated: H6 (extract at the 3rd consumer), F2 (TDD
  for feature/architecture-change, bug fixes start from a reproducing
  test), F3 (the simplification checklist applies only to touched lines
  during review/refactor).
- **#228 (refine, quick-win):** H8 + F6. Hand-carried token figures across
  CLAUDE.md, the guides and the benchmark disagree with the files they
  describe. Replace them with a pointer to `analyze_token_lifecycle.py`
  output, and move the CLAUDE.md pin in the same change.
- **#225 (refine, feature):** M1 + M2, removed together because they are one
  over-constraint pattern. Before and after: run `run_governance_eval.py`
  and a downstream sim cell. Close if the eval shows no difference.
- **#226 (refine, feature):** M3, M4, M5, M7, M9, one at a time, eval before
  and after. M3 rewrites the eval's `expect_substrings`, because echoing the
  slogan is not the behaviour being tested. M4 adds a "fix it after a failing
  test" eval case that expects action.
- **#227 (refine, feature):** F1 generalization.
- **F5, F7, F8 closed.** Reopen triggers: a `§` rename lands for another
  reason (F5); a vendor changes cache pricing (F7); an AC label stops
  resolving to a shipped spec (F8). F6 reopened as #228.
