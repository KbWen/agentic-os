---
status: shipped
title: Pre-commit Local Validation Hook
source: GitHub issue #192
created: 2026-06-08
primary_domain: developer-experience
secondary_domains: [ci]
---

# Pre-commit Local Validation Hook

## Goal

Provide an opt-in Git pre-commit hook sample that runs the Agentic OS local validator before a commit is created, while preserving the existing advisory guarded-write warning behavior.

## Acceptance Criteria

- AC-1: `.githooks/pre-commit.guard-ssot.sample` runs the repository validator from the Git repository root and exits non-zero when validation fails.
- AC-2: `.githooks/pre-commit.guard-ssot.sample` chooses `.agentcortex/bin/validate.ps1` on Windows when PowerShell is available, and otherwise falls back to `.agentcortex/bin/validate.sh`.
- AC-3: `.githooks/pre-commit.guard-ssot.sample` retains the existing guarded SSoT warning as advisory-only, so a missing guard receipt does not block the commit by itself.
- AC-4: `README.md` documents the opt-in setup command using `git config core.hooksPath .githooks` and copying the sample to `.githooks/pre-commit`.
- AC-5: `tests/ci/test_pre_commit_hook.py` verifies validator failure blocks the hook, validator success passes, and README/setup wiring stays present.

## Non-goals

- Do not enable the hook automatically for existing contributors or downstream installs.
- Do not add a new package manager dependency such as the Python `pre-commit` framework.
- Do not change CI validation behavior.
- Do not make the guarded-write receipt warning a hard blocker.

## Constraints

- The hook must remain a plain Git hook sample under `.githooks/`.
- The implementation must work from subdirectories by resolving the Git top-level directory.
- The hook must keep output concise enough for pre-commit usage.
- The deploy tier for `.githooks/*` remains scaffold so downstream projects may customize local hooks.

## File Relationship

This feature extends the existing advisory hook sample and deploy wiring. It does not replace `validate.sh`, `validate.ps1`, GitHub Actions, or guarded context write tooling.

## Domain Decisions

- [DECISION] Keep activation opt-in because local hooks affect contributor workflow and should not surprise existing clones.
- [DECISION] Use the existing validator scripts instead of introducing the external `pre-commit` framework.
- [CONSTRAINT] Guarded-write warnings remain advisory because SSoT updates are already governed by workflow and guard tooling.
