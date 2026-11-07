---
name: test-driven-development
description: Drive changes with Red→Green→Refactor; ensure behavior is verifiable and regression-safe.
---

# Test-Driven Development

## When to Use

- Adding or modifying core logic.
- Fixing bugs and needing regression protection.
- Requirements can be written as explicit input/output acceptance tests.

## Workflow

1. **Red**: Write a failing test describing the expected behavior.
2. **Green**: Write the minimal code to make the test pass.
3. **Refactor**: Clean up naming, structure, and duplication.
4. Repeat the cycle until acceptance criteria are met.

## Ironclad Rules

- Do NOT write massive amounts of features before writing tests.
- Focus on one small goal per cycle.
- All tests MUST pass after refactoring.
