---
name: medium-feature
description: Medium feature flow. Cross-module impact or phased delivery.
tasks:
  - research
  - spec
  - plan
  - implement
  - review
  - test
---

# Medium Feature Workflow

1. `/research`: Converge unknowns and dependency constraints.
2. `/spec`: Fix interfaces, module boundaries, compatibility strategy.
3. `/plan`: Split into Phase 1/2. Ensure each phase is independently verifiable & rollback-able.
4. `/implement`: Execute by phase, maintain small commits.
5. `/review`: Focus on cross-module impact & integration risks.
6. `/test`: Execute cross-module tests & critical regression verifications.

