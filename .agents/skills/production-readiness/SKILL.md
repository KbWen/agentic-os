---
name: production-readiness
description: Pre-ship observability readiness checklist — ensures errors reach production monitoring, not just debug consoles.
---

# Production Readiness

## Overview

Code that passes all tests but logs errors only via debug-only APIs (e.g., `debugPrint`, `console.log` in debug mode) is functionally silent in production. This skill enforces observability readiness before ship — ensuring the team is not blind during beta testing and production rollout.

## When to Use

- Auto-recommended for `feature` and `architecture-change` classifications.
- Activate manually when working on error handling, crash reporting, or logging infrastructure.
- Apply at `/review` (semantic error check) and `/ship` (readiness checklist).

## Observability Checklist

### 1. Error Surface Audit (at `/review`)

For every `catch` / error-handling block in changed files:

| Check | Pass | Fail |
|-------|------|------|
| Logging call exists | `Logger.error()`, `log.error()`, `crashReporter.capture()` | Empty `catch {}` |
| Logger is production-observable | Framework logger, crash reporter, structured stdout | `debugPrint()`, `print()`, debug-only `console.log` |
| Error context is actionable | Includes error type, operation, identifiers | `"error occurred"`, raw exception only |

### 2. Log Sink Documentation (at `/ship`)

Document in Work Log where production errors go:

```
## Observability
- Error sink: [e.g., Sentry via Logger.error(), Crashlytics, stdout → CloudWatch]
- Health check: [e.g., /health endpoint, Firebase Vitals, uptime monitor]
- Rollback signal: [e.g., error rate > 2x baseline → revert]
```

If the project has no production logging infrastructure, document as Known Risk:
> "No production error reporting configured. Errors in catch blocks will be logged to stdout only. Risk: silent failures in release builds if stdout is not monitored."

### 3. Rollback Telemetry (at `/ship`)

The rollback plan (per engineering_guardrails.md §12.5) must answer:
- **How will operators know the rollback is needed?** (alert, dashboard, manual check)
- **How will operators know the rollback succeeded?** (error rate drops, health check passes)

## Heading-Scoped Read Note

For phase-entry loading, read only:
- `When to Use`
- `Observability Checklist`

Load `What This Skill Does NOT Cover`, `Anti-Patterns`, and `Interaction with Other Skills` on full read or cache miss only.

## What This Skill Does NOT Cover

- **Tool selection**: Sentry vs Crashlytics vs Datadog — team/project decides.
- **Alert thresholds**: When to page on-call — SRE/ops owns this.
- **Dashboards**: What to visualize — team preference.
- **Post-deploy monitoring**: This is a pre-ship readiness check, not an ops workflow.

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| `catch (e) { debugPrint(e); }` | Tree-shaken in release build | Use production logger |
| `catch (e) { /* TODO: add logging */ }` | Silent catch escapes review | Add logging now, not later |
| `Logger.error("error")` without context | Useless in production triage | Include operation, identifiers, error type |
| Logging to local file only | Not observable in cloud/mobile | Use centralized error reporting |

## Interaction with Other Skills

- **systematic-debugging**: Complements — debugging finds bugs, production-readiness ensures they're visible when they happen again.
- **verification-before-completion**: Works alongside — verification checks correctness, production-readiness checks observability.
- **auth-security**: Security errors are especially critical to observe in production. §5.2a applies with elevated priority to auth error paths.
