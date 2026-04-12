<!-- This is a SCAFFOLD skill. When /app-init runs in a downstream project, -->
<!-- it customizes this file based on the project's ADR tech stack. -->
<!-- If this file has NOT been customized, the AI should treat it as generic guidance. -->

# Database Design

## When to Apply

- **Classification**: feature (if new tables/columns), architecture-change (schema redesign), hotfix (data-related bug)
- **Phase**: /plan (schema design), /implement (migration creation), /review (schema review), /test (data integrity)
- **Trigger**: Task involves creating tables, modifying schema, writing migrations, or changing data access patterns

## Conventions

> **Customize after /app-init**: Replace these generic conventions with your project's ADR and ORM-specific patterns.

### Table Design
- Every table MUST have: `id` (primary key), `created_at`, `updated_at`
- Use UUIDs or auto-increment IDs consistently (per ADR decision)
- Soft delete: add `deleted_at` column if ADR specifies soft delete
- Table names: plural, snake_case (e.g., `users`, `order_items`)
- Column names: snake_case (e.g., `first_name`, `is_active`)

### Relationship Patterns
| Relationship | Implementation | Example |
|---|---|---|
| One-to-Many | Foreign key on "many" side | `orders.user_id → users.id` |
| Many-to-Many | Junction table | `user_roles (user_id, role_id)` |
| One-to-One | Foreign key + unique constraint | `user_profiles.user_id (UNIQUE) → users.id` |
| Self-referencing | Foreign key to same table | `categories.parent_id → categories.id` |

### Index Strategy
- Every foreign key column MUST have an index
- Columns used in WHERE clauses frequently → add index
- Composite indexes: put the most selective column first
- Unique constraints for business uniqueness rules (email, username, etc.)
- DO NOT over-index: every index slows writes

### Migration Rules
- **One migration per logical change** (don't mix table creation with data backfill)
- **Migrations MUST be reversible**: every `up` must have a corresponding `down`
- **Never modify a shipped migration**: create a new migration instead
- **Data migrations separate from schema migrations**: schema first, data second
- **Test rollback**: after writing migration, verify `down` works cleanly

### Query Patterns
- Use parameterized queries / ORM bindings — NEVER string concatenation for SQL
- Limit SELECT columns: `SELECT id, name` not `SELECT *`
- Add `LIMIT` to all list queries (even if paginated — belt and suspenders)
- Use transactions for multi-table writes
- Batch inserts for bulk operations (not one INSERT per row)

### Data Integrity
- Foreign key constraints enforced at DB level (not just application level)
- NOT NULL on required fields (don't rely on application validation alone)
- CHECK constraints for enum-like fields or value ranges
- Default values for fields that have sensible defaults

## Checklist

During /plan:
- [ ] Schema changes documented in spec (new tables, modified columns)
- [ ] Indexes planned for query patterns
- [ ] Migration rollback strategy defined
- [ ] Data backfill plan (if modifying existing tables with data)

During /implement:
- [ ] Migration file created (not manual SQL against DB)
- [ ] Foreign keys have indexes
- [ ] NOT NULL and DEFAULT constraints set appropriately
- [ ] Migration tested: up → verify → down → verify → up
- [ ] No raw SQL string concatenation (use parameterized queries)

During /review:
- [ ] No N+1 queries (use eager loading / JOIN where appropriate)
- [ ] Transaction boundaries correct (all-or-nothing for related writes)
- [ ] No schema changes without migration file
- [ ] Backward compatibility: old code can still function until deployed together
- [ ] Sensitive data columns identified (for encryption/hashing per security guardrails)

## Anti-Patterns

- **Schema via ORM only**: Relying on ORM auto-sync without migration files. No rollback, no history, no review.
- **God table**: One table with 30+ columns. Normalize or split by domain.
- **Missing indexes on FK**: Every foreign key needs an index. Databases don't add them automatically (except some).
- **String-typed everything**: Using VARCHAR for dates, numbers, booleans. Use proper types.
- **No migration rollback**: Writing `up` without `down`. You will need to rollback someday.
- **Mixing DDL and DML**: Schema changes and data backfill in the same migration. Split them.
- **SELECT * in production code**: Fetching all columns when you need two. Wastes memory and bandwidth.
- **Trusting application-only validation**: No DB constraints means bad data WILL get in eventually.

## References

- Project ADR: `docs/adr/ADR-002-project-architecture.md` § Database Design
- Security guardrails: `.agent/rules/security_guardrails.md` (A03: SQL Injection, A02: Secrets in connection strings)
- Spec template: `.agentcortex/templates/spec-app-feature.md` § Database Schema
