# Project Examples (Node.js / Python)

This document provides ready-to-copy "Real Project Integration" examples to help teams use the same AgentCortex process across Google Antigravity, Codex Web, and Codex App.

## Example A: Node.js API Project

### Node.js Scenario

- Requirement: Add `POST /todos` with input validation and unit tests.
- Tech: Express + Vitest.

### Node.js Workflow

1. Deploy Template:

```bash
./deploy_brain.sh .
./.agentcortex/bin/validate.sh
```

1. Opening Prompt (Paste for the Agent):

```text
Please run /bootstrap.
Requirement: Add POST /todos API.
Target files: src/routes/todos.ts, src/services/todoService.ts, tests/todos.test.ts
Constraint: Do not break existing GET /todos return format.
Acceptance Criteria:
1) Return 400 when title is missing.
2) Return 201 on successful creation.
3) All tests pass.
```

1. Execute in order:

- `/brainstorm`
- `/write-plan`
- `/test-skeleton` (TDD recommended: blueprints before implementation)
- `/execute-plan`
- `/review`
- `/test`
- `/ship`

### Node.js Recommended Commands

```bash
npm test
npm run lint
```

---

## Example B: Python Backend Project

### Python Scenario

- Requirement: Add `calculate_discount` logic supporting boundary conditions.
- Tech: FastAPI + pytest.

### Python Workflow

1. Deploy Template:

```bash
./deploy_brain.sh .
./.agentcortex/bin/validate.sh
```

1. Opening Prompt (Paste for the Agent):

```text
Please run /bootstrap.
Requirement: Add calculate_discount logic.
Target files: app/services/pricing.py, tests/test_pricing.py
Constraint: Do not modify existing API schema.
Acceptance Criteria:
1) Throw expected error when original price <= 0.
2) Max discount 50%.
3) All pytest cases pass.
```

1. Execute in order:

- `/research`
- `/spec`
- `/plan`
- `/implement`
- `/review`
- `/test`
- `/handoff`

### Python Recommended Commands

```bash
pytest -q
ruff check .
```

---

## Supplement: Cross-Platform Tips

- Codex Web: Start a new thread for each requirement; paste the `/bootstrap` template first.
- Codex App: Run `./.agentcortex/bin/validate.sh` before every submission.
- Google Antigravity: Prioritize `/write-plan` + `/execute-plan` to avoid long prompt drift.

## Further Reading

- [Non-Linear Scenarios (Model Switching, Session Crashes, Chaotic Workflows)](./NONLINEAR_SCENARIOS.md)
- [Migration & Integration Guide (Legacy Project Takeover)](./guides/migration.md)
- [Token Governance Guide](./guides/token-governance.md)
- [Minimal Text Hardening Kit](./guides/minimal-text-hardening-kit.md)