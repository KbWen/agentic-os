---
name: small-fix
description: Small patch flow. Modifies < 3 files, requires fast rollback ability.
tasks:
  - plan
  - implement
  - review
  - test
---

# Small Fix Workflow

1. `/plan`: Confirm scope (< 3 files), AC, risks, rollback plan.
2. `/implement`: Execute minimal change. Incidental refactoring PROHIBITED.
3. `/review`: Focus on side-effects, compatibility, and fast rollback readiness.
4. `/test`: Execute single-file or minimal test suite, log results.

