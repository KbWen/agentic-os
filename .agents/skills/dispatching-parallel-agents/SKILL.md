---
name: dispatching-parallel-agents
description: Evaluate when to dispatch parallel agents; use a 4-step pattern to split, coordinate, and integrate results.
---

# Dispatching Parallel Agents

## Overview

Parallel agents are suitable for handling splittable tasks with low coupling. The goal is to shorten total lead time, not to increase coordination overhead.

## When to Use

- Tasks can be decomposed into independent sub-problems (e.g., documentation, testing, separate modules).
- Dependencies between sub-tasks are low; clear interfaces can be defined.
- Deadlines are tight, and lead time needs compression.

## When NOT to Use

- Problems are highly coupled and require frequent synchronization.
- Requirements are still unclear; the cost of decomposition outweighs the benefits.
- Unable to define unified acceptance criteria.

## Four-Step Pattern

1. **Decompose**: Split into mutually exclusive, independently verifiable sub-tasks.
2. **Dispatch**: Specify each agent's scope, inputs/outputs, constraints, and deadline.
3. **Sync**: Perform brief synchronizations at fixed checkpoints to handle conflicts and dependencies.
4. **Merge**: Integrate outputs using a unified set of acceptance criteria and run regression tests.

## Best Practices

- Every sub-task MUST have a clear Definition of Done.
- Collaborate primarily via interface contracts to avoid modifying each other's blocks.
- Perform a global check before final integration.

## Common Mistakes

- Forcefully splitting non-splittable tasks, leading to rework.
- Lacking sync checkpoints, resulting in integration explosion at the end.
- Sub-tasks passing individually but failing global acceptance.
