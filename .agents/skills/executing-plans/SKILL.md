---
name: executing-plans
description: Execute plans step-by-step with evidence at each stage; maintain rollback capability.
---

# Executing Plans

## Overview

Execution phase focuses on: **following steps, preserving evidence, and syncing deviations immediately.**

## Execution Rhythm

1. Read the latest plan and constraints.
2. Execute exactly one step at a time.
3. Validate immediately and record results after each step.
4. If deviating from the plan, update the plan before proceeding.

## Definition of Done

- All steps have clear status (completed / pending).
- Validation outputs are reproducible.
- Known constraints and follow-up suggestions are documented.
