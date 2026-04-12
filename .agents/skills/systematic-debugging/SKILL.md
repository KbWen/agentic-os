---
name: systematic-debugging
description: Use 4-phase root cause analysis (Observe, Hypothesize, Verify, Fix); avoid unverified patches.
---

# Systematic Debugging

## Overview

The core of systematic debugging is: **understand first, then fix**. When encountering a bug, clarify symptoms, reproduction conditions, and blast radius. Draw hypotheses, verify them with experiments to isolate the root cause, and only then submit a minimal, verifiable fix.

## Ironclad Rules

1. **No random patching**: Do not submit fixes without root cause evidence.
2. **Change one variable at a time**: Prevent unexplainable results from touching multiple areas at once.
3. **Fixes MUST include evidence**: Include reproduction steps, verification, and regression results.

## When to Use

- Hotfix incident response.
- Flaky tests.
- Cross-module anomalies that aren't intuitively obvious.
- Any "fixed but I don't know why" risk scenarios.

## Four-Phase Process

### Phase 1: Observe

- Precisely record error messages, timestamps, and input conditions.
- Create a Minimal Reproducible Example (MRE).
- Mark the blast radius (affected modules/users).

### Phase 2: Hypothesize

- Propose 1–3 testable root cause hypotheses.
- Design "falsifiable" checks for each hypothesis.
- Prioritize high-probability, low-cost verifiable items.

### Phase 3: Verify

- Run experiments and retain output logs.
- Adjust only one variable to confirm causality.
- Remove falsified hypotheses to converge on the most likely root cause.

### Phase 4: Fix

- Implement a Minimal Fix.
- Add a Regression Test.
- Verify: The original error disappears AND existing behavior is not broken.

## Common Mistakes

- Modifying code before reproducing the issue.
- Modifying too many files at once, failing to locate the effective fix point.
- Treating "accidental passes" as root cause resolved.
- Lacking regression tests, causing similar issues to happen again.
