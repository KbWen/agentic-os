<!-- This is a SCAFFOLD skill. When /app-init runs in a downstream project, -->
<!-- it customizes this file based on the project's ADR tech stack. -->
<!-- If this file has NOT been customized, the AI should treat it as generic guidance. -->

# Frontend Patterns

## When to Apply

- **Classification**: feature, architecture-change (if touching UI)
- **Phase**: /implement (component design & build), /review (pattern compliance), /test (UI state coverage)
- **Trigger**: Task involves creating or modifying UI components, pages, routes, or client-side state

## Conventions

> **Customize after /app-init**: Replace these generic conventions with your project's ADR and framework-specific patterns.

### Component Structure
- One component per file
- Component file name matches export name (PascalCase)
- Co-locate component-specific styles, tests, and types
- Separate page-level components from reusable UI components

### Suggested Directory Pattern
```
src/
├── components/        # Reusable UI components (Button, Modal, Card)
│   └── <Name>/
│       ├── <Name>.tsx
│       ├── <Name>.test.tsx
│       └── index.ts
├── pages/             # Page-level components (route targets)
│   └── <PageName>/
│       ├── <PageName>.tsx
│       ├── components/ # Page-specific components (not reusable)
│       └── hooks/      # Page-specific hooks
├── hooks/             # Shared custom hooks
├── services/          # API client functions
├── stores/            # State management (if applicable)
├── types/             # Shared TypeScript types
└── utils/             # Pure utility functions
```

### State Management Principles
- **Local state first**: useState/useReducer for component-specific state
- **Lift state up** only when sibling components need it
- **Global state** (store) only for truly app-wide state: auth, theme, user preferences
- **Server state** (API data) managed by data-fetching library (React Query, SWR, etc.) — NOT in global store
- Never duplicate server state in client store

### Data Fetching
- Centralize API calls in `services/` directory
- Use data-fetching hooks (React Query, SWR, or equivalent) instead of raw fetch/axios in components
- Handle loading, error, and empty states for every data-dependent component
- Implement optimistic updates for better UX where appropriate

### Form Handling
- Use a form library for complex forms (React Hook Form, Formik, or equivalent)
- Validate on client AND server (client validation is UX, server validation is security)
- Show inline errors next to fields, not just at form top
- Disable submit button during submission (prevent double-submit)

### Error Handling
- Global error boundary for unexpected crashes
- Per-component error handling for expected failures (API errors)
- User-friendly error messages (never show raw error objects)
- Retry mechanism for transient failures (network errors)

## Checklist

During /implement:
- [ ] Every data-dependent component handles: loading, error, empty, and success states
- [ ] No business logic in components (extract to hooks or services)
- [ ] No hardcoded strings (use constants or i18n keys)
- [ ] Accessible: semantic HTML, aria labels on interactive elements, keyboard navigation
- [ ] Responsive: works on mobile viewport (unless spec explicitly excludes mobile)
- [ ] No direct API calls in components (use service layer)

During /review:
- [ ] No prop drilling deeper than 2 levels (use context or composition)
- [ ] No unnecessary re-renders (check memo/callback usage)
- [ ] No sensitive data stored in localStorage/client state
- [ ] Route guards for authenticated pages
- [ ] Loading indicators for async operations

## Heading-Scoped Read Note

For phase-entry loading, read only:
- `When to Apply`
- `Checklist`

Load `Conventions`, `Anti-Patterns`, and `References` on full read or cache miss only.

## Anti-Patterns

- **God component**: Component with 300+ lines doing everything. Split into smaller components.
- **Prop drilling**: Passing props through 3+ levels of components. Use context or composition.
- **useEffect for everything**: Using useEffect for derived state (use useMemo) or event handling (use event handlers).
- **Index as key**: Using array index as React key in dynamic lists.
- **Fetch in render**: Calling fetch/axios directly in component body or useEffect without a data-fetching library.
- **CSS-in-JS soup**: Inline styles everywhere instead of consistent styling approach.
- **Ignoring empty state**: Showing a blank page when data array is empty instead of a helpful message.
- **Alert/Console for errors**: Using `alert()` or only `console.error()` instead of proper UI error handling.

## References

- Project ADR: `docs/adr/ADR-002-project-architecture.md` § Directory Structure, Naming
- Spec template: `.agentcortex/templates/spec-app-feature.md` § Frontend
- Security guardrails: `.agent/rules/security_guardrails.md` (A03: XSS prevention, A07: Auth)
