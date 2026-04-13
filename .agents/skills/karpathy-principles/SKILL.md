---
name: karpathy-principles
description: Behavioral guidelines to reduce common LLM coding mistakes — Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.
---

# Karpathy Coding Principles

Derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## When to Apply

- **Classification**: quick-win, feature, architecture-change, hotfix
- **Phase**: /plan (assumption surfacing), /implement (simplicity + surgical), /review (scope audit)
- **Trigger**: All non-trivial coding tasks — this is a behavioral baseline, not a domain skill

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Self-check: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: **Every changed line should trace directly to the user's request.**

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Checklist

During /plan:
- [ ] Assumptions stated explicitly before proposing solution
- [ ] Ambiguities surfaced — multiple interpretations presented if they exist
- [ ] Simplest viable approach chosen (justify if not the simplest)

During /implement:
- [ ] No features beyond what was asked
- [ ] No abstractions for single-use code
- [ ] Every changed line traces to the user's request
- [ ] Pre-existing code left alone unless directly required
- [ ] Success criteria defined before implementation begins

During /review:
- [ ] Diff contains only requested changes — no drive-by refactoring
- [ ] Code is not overcomplicated — could a simpler version work?
- [ ] Orphaned imports/variables from THIS change are cleaned up
- [ ] Pre-existing dead code mentioned but not deleted

## Anti-Patterns

- **Silent assumption**: Picking one interpretation without surfacing alternatives
- **Speculative flexibility**: Adding config/abstraction layers "for the future"
- **Drive-by cleanup**: "Improving" adjacent code that wasn't part of the request
- **Vague completion**: Claiming "done" without verifiable success criteria

## References

- Source: [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT)
- Complements: `writing-plans` (Think Before Coding), `verification-before-completion` (Goal-Driven Execution)
- Guardrails: `.agent/rules/engineering_guardrails.md` §7 Scope Discipline
