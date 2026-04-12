<!-- This is a SCAFFOLD skill. When /app-init runs in a downstream project, -->
<!-- it customizes this file based on the project's ADR tech stack. -->
<!-- If this file has NOT been customized, the AI should treat it as generic guidance. -->

# API Design

## When to Apply

- **Classification**: feature, architecture-change, hotfix (if touching API endpoints)
- **Phase**: /implement (design & build), /review (compliance check), /test (contract verification)
- **Trigger**: Task involves creating, modifying, or deprecating API endpoints

## Conventions

> **Customize after /app-init**: Replace these generic conventions with your project's ADR decisions.

### Endpoint Naming
- Use nouns for resources, not verbs: `GET /users` not `GET /getUsers`
- Plural resource names: `/users`, `/orders`, `/products`
- Nested resources for relationships: `/users/:id/orders`
- Use kebab-case for multi-word paths: `/order-items`

### HTTP Methods
| Action | Method | Success Status | Idempotent |
|---|---|---|---|
| List | GET | 200 | Yes |
| Get one | GET | 200 | Yes |
| Create | POST | 201 | No |
| Full update | PUT | 200 | Yes |
| Partial update | PATCH | 200 | No |
| Delete | DELETE | 204 | Yes |

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": {
      "field": "email",
      "constraint": "required"
    }
  }
}
```

### Standard Error Codes
| HTTP Status | When | Error Code Pattern |
|---|---|---|
| 400 | Invalid input | VALIDATION_ERROR, INVALID_FORMAT |
| 401 | Not authenticated | UNAUTHORIZED |
| 403 | Not permitted | FORBIDDEN |
| 404 | Resource not found | NOT_FOUND |
| 409 | Conflict (duplicate) | CONFLICT, DUPLICATE |
| 422 | Business rule violation | UNPROCESSABLE |
| 429 | Rate limited | RATE_LIMITED |
| 500 | Server error | INTERNAL_ERROR |

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "has_next": true
  }
}
```

### Versioning
- URL path versioning: `/api/v1/users`
- Breaking changes require new version
- Deprecation: add `Sunset` header with date, keep old version for N months

### Input Validation
- Validate at the controller/route level BEFORE business logic
- Return ALL validation errors at once (batch), not one at a time
- Sanitize strings: trim whitespace, escape HTML where applicable
- Enforce max lengths on all string fields

## Checklist

During /implement:
- [ ] Every endpoint has input validation
- [ ] Every endpoint returns consistent error format
- [ ] Every endpoint has proper auth check (or explicit `public` annotation)
- [ ] Pagination for list endpoints
- [ ] Rate limiting consideration (at least documented in spec)
- [ ] No sensitive data in URL parameters (use body or headers)
- [ ] Request/response examples in spec match implementation

During /review:
- [ ] No N+1 query patterns in list endpoints
- [ ] Proper HTTP status codes (not everything is 200)
- [ ] Idempotency for PUT/DELETE
- [ ] Error messages don't leak internal details (stack traces, SQL, paths)
- [ ] CORS configured per ADR policy

## Anti-Patterns

- **God endpoint**: One endpoint that does everything based on query params. Split into specific endpoints.
- **Verb in URL**: `POST /createUser` → `POST /users`
- **Inconsistent naming**: Mixing `/user` and `/products` (singular vs plural)
- **Swallowing errors**: Catching exceptions and returning 200 with `{ success: false }`
- **Leaking internals**: Returning DB column names directly as API fields without mapping
- **Missing 404**: Returning empty 200 instead of 404 when resource doesn't exist
- **Unbounded lists**: List endpoints without pagination or default limits

## References

- Project ADR: `docs/adr/ADR-002-project-architecture.md` § API Design
- Security guardrails: `.agent/rules/security_guardrails.md` (A01: Access Control, A03: Injection)
- Spec template: `.agentcortex/templates/spec-app-feature.md` § API Contract
