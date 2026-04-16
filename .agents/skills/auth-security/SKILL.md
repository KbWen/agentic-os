<!-- This is a SCAFFOLD skill. When /app-init runs in a downstream project, -->
<!-- it customizes this file based on the project's ADR tech stack. -->
<!-- If this file has NOT been customized, the AI should treat it as generic guidance. -->

# Auth & Security

## When to Apply

- **Classification**: ALL classifications that touch auth, permissions, user data, or session management
- **Phase**: /plan (auth flow design), /implement (auth logic), /review (MANDATORY for any auth-related change), /test (auth bypass testing)
- **Trigger**: Task involves login, registration, password, token, session, role, permission, or access control

## Relationship to Security Guardrails

This skill **extends** `.agent/rules/security_guardrails.md` with APP-specific auth patterns. The security guardrails handle OWASP scanning and secret detection. This skill handles auth architecture and implementation patterns.

**Precedence**: security_guardrails.md > this skill. If conflict, security guardrails win.

## Conventions

> **Customize after /app-init**: Replace these with your project's ADR auth decisions.

### Authentication Flow (JWT Example)

```
Client                    Server                     DB
  |-- POST /auth/login -->|                           |
  |   {email, password}   |-- verify password hash -->|
  |                       |<-- user record -----------|
  |<-- {access_token,     |                           |
  |     refresh_token} ---|                           |
  |                       |                           |
  |-- GET /api/resource ->|                           |
  |   Authorization:      |-- verify token            |
  |   Bearer <access>     |-- check permissions       |
  |<-- 200 data ---------|                           |
  |                       |                           |
  |-- POST /auth/refresh->|                           |
  |   {refresh_token}     |-- verify + rotate ------->|
  |<-- {new_access,       |<-- new tokens ------------|
  |     new_refresh} -----|                           |
```

### Token Rules
- **Access token**: Short-lived (15-30 min). Stored in memory only (NOT localStorage).
- **Refresh token**: Longer-lived (7-30 days). Stored in httpOnly, secure, sameSite cookie.
- **Token rotation**: Issue new refresh token on each refresh. Invalidate old one.
- **Revocation**: Maintain a blocklist for compromised tokens (or use short expiry + DB check).

### Password Rules
- Hash with bcrypt (cost 12+) or argon2id
- NEVER store plaintext passwords — not even in logs, not even temporarily
- Minimum 8 characters, no maximum less than 128
- Check against breach database (HaveIBeenPwned API) on registration if feasible
- Rate limit login attempts: 5 failures → temporary lockout (progressive delay)

### Authorization (RBAC Pattern)

```
Users ──< UserRoles >── Roles ──< RolePermissions >── Permissions
```

| Concept | Example | Storage |
|---|---|---|
| Role | admin, editor, viewer | `roles` table |
| Permission | users:read, users:write, posts:delete | `permissions` table |
| Assignment | User A has role "editor" | `user_roles` junction table |

**Middleware pattern** (pseudocode):
```
authenticate(req)          → verify token, attach user to request
authorize('posts:write')   → check user's roles have this permission
handler(req, res)          → business logic (user is authenticated + authorized)
```

### Session Security
- Set `httpOnly`, `secure`, `sameSite=strict` on auth cookies
- Regenerate session ID after login (prevent session fixation)
- Invalidate all sessions on password change
- Implement "logout everywhere" for compromised accounts

### Input Security (Auth-Specific)
- Sanitize email: lowercase, trim, validate format
- Timing-safe comparison for tokens and passwords (prevent timing attacks)
- Generic error messages: "Invalid email or password" (never reveal which one is wrong)
- CAPTCHA or rate limiting on registration and login endpoints

## Checklist

During /plan:
- [ ] Auth flow documented in spec (which endpoints, which tokens, which storage)
- [ ] Permission model defined (who can do what)
- [ ] Session management strategy chosen (per ADR)

During /implement:
- [ ] Passwords hashed with approved algorithm (bcrypt/argon2, NOT MD5/SHA1)
- [ ] Tokens validated on EVERY protected endpoint (no missing auth middleware)
- [ ] Refresh token rotation implemented
- [ ] Rate limiting on auth endpoints
- [ ] No sensitive data in JWT payload (no password, no PII beyond user ID)
- [ ] CORS configured to restrict origins

During /review:
- [ ] No auth bypass paths (every protected route checked)
- [ ] No hardcoded credentials or API keys
- [ ] Error messages don't leak user existence (registration: "If this email exists...")
- [ ] Password reset token is single-use and time-limited
- [ ] Admin endpoints have role check (not just auth check)

During /test:
- [ ] Test: unauthenticated request → 401
- [ ] Test: wrong role → 403
- [ ] Test: expired token → 401
- [ ] Test: manipulated token (wrong signature) → 401
- [ ] Test: rate limit triggers after N failures
- [ ] Test: password change invalidates old tokens

## Heading-Scoped Read Note

For phase-entry loading, read only:
- `When to Apply`
- `Relationship to Security Guardrails`
- `Checklist`

Load `Conventions`, `Anti-Patterns`, and `References` on full read or cache miss only.

## Anti-Patterns

- **JWT in localStorage**: Vulnerable to XSS. Use httpOnly cookies or in-memory only.
- **No refresh token rotation**: Stolen refresh token = permanent access. Always rotate.
- **Role check in frontend only**: Frontend hides UI but backend doesn't enforce. ALWAYS check server-side.
- **Password in logs**: Logging request body that includes password field. Exclude sensitive fields.
- **Shared admin token**: One API key for all admin operations. Use per-user auth with audit trail.
- **No rate limiting**: Brute force attacks on login become trivial.
- **Email enumeration**: "No account with this email" on login. Use generic "Invalid credentials".
- **Long-lived access tokens**: Access tokens valid for days. Use short-lived + refresh pattern.
- **Missing CSRF protection**: For cookie-based auth, CSRF tokens are mandatory on state-changing requests.

## References

- Project ADR: `docs/adr/ADR-002-project-architecture.md` § Auth & Security
- Security guardrails: `.agent/rules/security_guardrails.md` (A01, A02, A07 — primary references)
- Red team skill: `.agents/skills/red-team-adversarial/SKILL.md` (auth bypass testing)
- Spec template: `.agentcortex/templates/spec-app-feature.md` § Auth & Permissions
