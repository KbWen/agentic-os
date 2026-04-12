---
name: test-skeleton
description: Read-only test blueprint generation. NO implementation code.
tasks:
  - test-skeleton
---

# /test-skeleton

Read-only command. DOES NOT change state.

> Canonical state & transition: `Ref: .agent/rules/state_machine.md`

Generate Test Skeleton FIRST (No implementation code).

Rules:

1. At least 1 test per AC.
2. At least 1 regression/sanity test per Risk.
3. Each test MUST include: Name, Objective, Type, Preconditions/Mocks, Verification method.

Activation Condition:

- `/plan` passed quality gate (state >= `IMPLEMENTABLE`).
- If gate failed, MUST reject and list missing criteria.
