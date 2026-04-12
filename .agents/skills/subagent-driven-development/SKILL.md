---
name: subagent-driven-development
description: Decompose tasks via subagent collaboration; define interface contracts and integration checkpoints.
---

# Subagent-Driven Development

## Overview

When a task is splittable, use multiple subagents to process in parallel, accelerating delivery without sacrificing consistency.

## Decomposition Strategy

- Split cleanly by module boundaries or responsibilities.
- Define input/output contracts for each sub-task.
- Establish sync checkpoints to avoid integration explosion.

## Delivery Requirements

1. Sub-tasks MUST include testing or checking evidence.
2. The primary agent is responsible for integration, conflict resolution, and final verification.
3. Any cross-module changes MUST be announced before integration.
