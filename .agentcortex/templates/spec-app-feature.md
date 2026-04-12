---
template: true
description: Feature spec template for APP projects. Includes API, DB, Frontend, and Auth sections.
usage: Used by /spec-intake and /spec workflows when generating feature specs for APP projects. Sections are conditionally included based on the project's ADR tech stack.
---

# Spec Template: APP Feature

> **Instructions for AI**: When generating a feature spec, read the project ADR first (`ADR-00N-project-architecture.md`). Include only the sections relevant to this feature. Remove unused sections — do NOT leave empty sections.

```markdown
---
status: draft
title: <Feature Name>
source: <external | internal | continuation>
source_doc: <e.g., _product-backlog.md #N | user-provided>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
primary_domain: <domain-noun>
secondary_domains: []
---

# <Feature Name>

## Goal
<1-3 sentences: what problem does this feature solve for the user?>

## Acceptance Criteria
1. <AC must be testable and measurable>
2. <Use [INFERRED] / [FROM-SOURCE] / [NEEDS-CONFIRMATION] tags per /spec-intake §3>
3. ...

## Non-goals
- <What this feature explicitly does NOT do>
- <Prevents scope creep during /implement>

## Constraints
- <Technical constraints from ADR: e.g., "Must use [ORM] for DB access">
- <Business constraints: e.g., "Must support [N] concurrent users">
- <Compatibility: e.g., "Must not break existing [endpoint/schema]">

---

## API Contract
<!-- Include this section if feature involves backend endpoints -->
<!-- Follow conventions from project ADR § API Design -->

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| <GET/POST/PUT/PATCH/DELETE> | <path> | <required/public> | <what it does> |

### Request / Response

#### <METHOD> <path>

**Request**:
```json
{
  "<field>": "<type — description>"
}
```

**Response** (success):
```json
{
  "<field>": "<type — description>"
}
```

**Error cases**:
| Status | Error Code | When |
|---|---|---|
| 400 | <CODE> | <condition> |
| 401 | UNAUTHORIZED | <condition> |
| 404 | NOT_FOUND | <condition> |

### Validation Rules
- <field>: <rule, e.g., "required, string, 1-255 chars, unique">
- <field>: <rule>

---

## Database Schema
<!-- Include this section if feature involves DB changes -->
<!-- Follow conventions from project ADR § Database Design -->

### New Tables

```sql
CREATE TABLE <table_name> (
  id          <type> PRIMARY KEY,
  <column>    <type> <constraints>,
  created_at  TIMESTAMP DEFAULT NOW(),
  updated_at  TIMESTAMP DEFAULT NOW()
);
```

### Table Modifications

| Table | Change | Column | Type | Notes |
|---|---|---|---|---|
| <table> | ADD / MODIFY / DROP | <column> | <type> | <reason> |

### Indexes

| Table | Columns | Type | Reason |
|---|---|---|---|
| <table> | <columns> | <BTREE/GIN/UNIQUE> | <query pattern> |

### Migration Notes
- <Backward compatibility: can old code work with new schema?>
- <Data migration: existing rows need backfill?>
- <Rollback: how to reverse this migration?>

---

## Frontend
<!-- Include this section if feature involves UI -->
<!-- Follow conventions from project ADR § Directory Structure and Naming -->

### Routes

| Path | Component | Auth | Description |
|---|---|---|---|
| <route> | <ComponentName> | <required/public> | <what user sees> |

### Components

| Component | Type | Props | State | Notes |
|---|---|---|---|---|
| <Name> | <page/layout/widget> | <key props> | <key state> | <notes> |

### User Flow
1. User navigates to <route>
2. <what happens step by step>
3. <success state>
4. <error state>

### UI States
- **Loading**: <what user sees while data loads>
- **Empty**: <what user sees when no data>
- **Error**: <what user sees on failure>
- **Success**: <what user sees on success>

---

## Auth & Permissions
<!-- Include this section if feature involves access control -->
<!-- Follow conventions from project ADR § Auth & Security -->

| Action | Required Role | Rule |
|---|---|---|
| <action> | <role or permission> | <additional logic> |

### Auth Flow (if new auth logic)
1. <step>
2. <step>

---

## Testing Strategy
<!-- Always include — maps to TESTING_PROTOCOL.md -->

### Unit Tests
| Test | AC Ref | Input | Expected |
|---|---|---|---|
| <test_name> | AC #N | <input> | <expected output> |

### Integration Tests
| Test | Scope | Setup | Expected |
|---|---|---|---|
| <test_name> | <API/DB/Auth> | <preconditions> | <expected> |

### Edge Cases
- <boundary condition>
- <null/empty handling>
- <concurrent access scenario>

---

## Domain Decisions
<!-- MANDATORY for feature/architecture-change classifications. -->
<!-- /ship reads ONLY this section for knowledge consolidation into Domain Docs. -->
<!-- Max 10 entries. Each entry MUST use one of: [DECISION], [TRADEOFF], [CONSTRAINT] -->
<!-- Entries without a valid tag will be flagged during /review. -->

- [DECISION] <why this architectural choice was made over alternatives>
- [TRADEOFF] <what was traded off and why it is acceptable>
- [CONSTRAINT] <a rule that all future work in this domain must respect>

## File Relationship
<INDEPENDENT | EXTENDS <existing-spec> | REPLACES <existing-spec>>

## Dependencies
- <Spec or feature this depends on>
- <External service or API>

## Open Questions
- <Unresolved items — flagged for /plan phase>
```
