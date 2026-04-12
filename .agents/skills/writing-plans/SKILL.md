---
name: writing-plans
description: Plan before implementing; produce verifiable, rollback-safe, incrementally executable task plans.
---

# Writing Plans

## Overview

High-quality plans must answer three things: **What to do, how to verify, and how to rollback if it fails.**

## Required Fields

- Goals and Non-goals
- Blast Radius (files/modules)
- Step-by-step breakdown (2–5 minute granularity)
- Verification commands and expected results
- Risks and Rollback plans

## Writing Principles

1. Small before large; start with reversible steps.
2. Every step MUST be verifiable.
3. Do NOT cross boundaries before confirmation (no scope creep).
