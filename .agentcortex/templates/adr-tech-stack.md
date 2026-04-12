---
template: true
description: ADR template for downstream projects to define their technology stack and architectural decisions.
usage: Used by /app-init workflow to generate project-specific ADR.
---

# ADR-00N: Project Architecture & Tech Stack

## Status

Accepted | Superseded by ADR-00X

## Date

<YYYY-MM-DD>

## Context

<1-3 sentences describing why this project exists and what problem it solves.>

## Decision

### Project Type

<web-app | mobile-app | full-stack | api-only | monorepo | other>

### Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Frontend | <framework> | <version or TBD> | <notes> |
| Backend | <framework> | <version or TBD> | <notes> |
| Database | <database> | <version or TBD> | <notes> |
| Auth | <strategy> | — | <notes> |
| Hosting | <platform or TBD> | — | <notes> |
| CI/CD | <platform or TBD> | — | <notes> |

### Directory Structure

```
<project-root>/
├── src/                    # or app/, lib/, etc.
│   ├── <frontend-dir>/     # e.g., components/, pages/, views/
│   ├── <backend-dir>/      # e.g., api/, server/, routes/
│   ├── <shared-dir>/       # e.g., shared/, common/, types/
│   └── <db-dir>/           # e.g., db/, models/, migrations/
├── tests/                  # or __tests__/, spec/
├── .agentcortex/           # AI governance (managed by brain)
└── <config files>          # package.json, pyproject.toml, etc.
```

### Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Files | <kebab-case / camelCase / snake_case> | <example> |
| Components | <PascalCase> | <example> |
| API routes | <convention> | <example> |
| DB tables | <convention> | <example> |
| DB columns | <convention> | <example> |
| Environment vars | <UPPER_SNAKE_CASE> | <example> |

### API Design

- Style: <REST | GraphQL | gRPC | tRPC>
- Base path: <e.g., /api/v1>
- Versioning: <URL path | header | none>
- Error format:
  ```json
  {
    "error": {
      "code": "<ERROR_CODE>",
      "message": "<human-readable>",
      "details": {}
    }
  }
  ```
- Pagination: <cursor-based | offset-based | none>
- Auth header: <Bearer token | Cookie | API key>

### Database Design

- ORM / Query builder: <e.g., Prisma, SQLAlchemy, Drizzle, TypeORM, none>
- Migration tool: <e.g., Prisma Migrate, Alembic, knex, manual SQL>
- Naming: <singular | plural> tables, <snake_case | camelCase> columns
- Required fields per table: <e.g., id, created_at, updated_at>
- Soft delete: <yes (deleted_at) | no>

### Auth & Security

- Auth flow: <JWT + refresh token | session cookie | OAuth2 code flow | third-party managed>
- Password hashing: <bcrypt | argon2 | managed by provider>
- Role model: <RBAC | ABAC | simple role field | none yet>
- Session management: <stateless JWT | server-side session | provider-managed>
- CORS policy: <strict origin list | same-origin | TBD>

### Testing

- Test framework: <e.g., Vitest, Jest, pytest, Go testing>
- Test command: <e.g., npm test, pytest -q, go test ./...>
- Lint command: <e.g., npm run lint, ruff check ., golangci-lint run>
- Build command: <e.g., npm run build, python -m build>
- Coverage target: <e.g., 80% | none set>
- E2E framework: <e.g., Playwright, Cypress, none>

## Open Decisions

<List any [TBD] items from above that need future resolution. Each should become its own ADR when decided.>

- [ ] <Decision 1>
- [ ] <Decision 2>

## Consequences

- AI agents reading this ADR will apply these conventions during /implement and /review.
- Domain skills (api-design, frontend-patterns, etc.) are derived from these decisions.
- Spec templates are customized based on this tech stack.
- Future architecture changes MUST create a new ADR that supersedes this one.
