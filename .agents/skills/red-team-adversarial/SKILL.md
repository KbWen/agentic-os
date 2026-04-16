---
name: red-team-adversarial
description: Adversarial security and resilience analysis — auto-triggered during /review and /test based on task classification. Provides attack surface analysis, boundary testing, auth bypass attempts, dependency chain attacks, and Beast Mode stress testing.
---

# Red Team / Adversarial Testing

## Overview

This skill applies **adversarial thinking** to code changes: instead of checking against a compliance list (that's what `security_guardrails.md` does), it actively asks "how would an attacker exploit this change?" and "what breaks under extreme conditions?"

It complements — never replaces — the existing OWASP security scan in `/review`.

## Ironclad Rules

1. **No bypass of governance**: This skill executes within `/review` and `/test` phases only. It cannot override gates, skip phases, or alter classification.
2. **Severity honesty**: Only mark CRITICAL when there is a concrete, exploitable attack path with evidence (file:line). Speculative risks are HIGH at most.
3. **Additive only**: Red Team findings supplement existing security findings — never contradict or override them.

## When to Use (Auto-Trigger Matrix)

AI MUST check the task classification from the Work Log and apply this matrix automatically:

```
Classification        │ /review          │ /test
──────────────────────┼──────────────────┼─────────────────
tiny-fix              │ —                │ —
quick-win             │ —                │ —
hotfix                │ Lite Red Team    │ Lite Adversarial (1-2 cases)
feature               │ Full Red Team    │ Adversarial Cases
architecture-change   │ Full Red Team    │ Adversarial Cases + Beast Mode
```

**Auto-trigger logic**: During `/review` or `/test`, read `Classification:` from the active Work Log. If classification is `hotfix`, `feature`, or `architecture-change`, execute the corresponding mode below. No user action required.

## Modes

### Lite Red Team (hotfix)

Minimal overhead (≤300 tokens output). Focus exclusively on the fix point:

1. **Fix-Point Attack Vector**: Does the fix itself introduce a new attack surface? (e.g., a validation fix that changes error behavior, a permission fix that alters fallback logic)
2. **Regression Attack**: Could an attacker exploit the old behavior to bypass the fix? (e.g., race condition in the fix window)

Output: 1-2 findings max, using the Red Team Report format below.

### Full Red Team (feature / architecture-change)

Comprehensive adversarial analysis of all changed files:

1. **Attack Surface Analysis**: What new attack vectors does this change expose?
   - New endpoints, inputs, or data flows
   - Changed trust boundaries
   - New external dependencies or integrations
2. **Boundary Testing**: What happens at the extremes?
   - Empty/null/undefined inputs
   - Maximum-length strings, overflow values
   - Special characters, unicode edge cases
   - Type confusion (string where number expected, etc.)
3. **Authorization Bypass Attempts**: Can the validation logic be circumvented?
   - Direct object reference (IDOR)
   - Privilege escalation paths
   - Missing checks on alternative code paths
   - Token/session manipulation
4. **Dependency Chain Attacks**: Are new dependencies trustworthy?
   - Known CVEs in added packages
   - Typosquatting risk
   - Unmaintained dependencies
   - Transitive dependency risks

Output: All findings using the Red Team Report format below.

### Beast Mode (architecture-change only)

In addition to Full Red Team, analyze systemic resilience:

1. **Concurrency**: Race conditions, deadlocks, TOCTOU vulnerabilities
   - Identify shared mutable state across the change
   - Check for missing locks, atomic operations, or serialization
   - File:line references for each scenario
2. **Resource Exhaustion**: Memory leaks, unbounded growth, CPU-intensive loops
   - Unbounded collections or caches
   - Missing pagination or limits
   - Recursive calls without depth guards
3. **Fault Injection**: What happens when dependencies fail?
   - Database connection drops mid-transaction
   - External API returns 500/timeout
   - File system full or permissions denied
   - Network partition scenarios

Output: Use the Beast Mode Analysis format below.

## Output Formats

### Red Team Report (embedded in /review output, after Security Findings)

```markdown
## Red Team Findings

### [CRITICAL|HIGH|MEDIUM|LOW] — [Attack Vector]: [Brief Description]
- **File**: [path:line]
- **Attack Scenario**: [1-2 line attack narrative]
- **Impact**: [What attacker gains]
- **Mitigation**: [Concrete fix]
```

### Adversarial Test Cases (embedded in /test output)

```markdown
## Adversarial Test Cases

| # | Category | Input / Scenario | Expected Behavior | Priority |
|---|----------|------------------|--------------------|----------|
| 1 | Boundary | [extreme input]  | [should reject/handle] | HIGH |
| 2 | AuthZ Bypass | [bypass attempt] | [should deny] | CRITICAL |
```

### Beast Mode Analysis (architecture-change only, embedded in /test output)

```markdown
## Beast Mode Analysis

### Concurrency
- [race condition scenarios with file:line references]

### Resource Exhaustion
- [memory/CPU/disk scenarios]

### Fault Injection
- [what happens if dependency X fails? if network drops?]
```

## Heading-Scoped Read Note

For phase-entry loading, read only:
- `Ironclad Rules`
- `When to Use (Auto-Trigger Matrix)`
- `Modes`

Load `Output Formats`, `Blocking Rules`, `Work Log Integration`, `Red Team Findings`, and `Common Mistakes` on full read or cache miss only.

## Blocking Rules (Different from Security Guardrails)

Red Team findings use a graduated blocking model:

```
                    │ Security Guardrails (OWASP)  │ Red Team Skill
────────────────────┼─────────────────────────────┼──────────────────
CRITICAL            │ Hard block                  │ Hard block
HIGH                │ Hard block                  │ Soft block (record decision)
MEDIUM              │ Flag, proceed allowed       │ Advisory
LOW                 │ Informational               │ Advisory
```

- **CRITICAL**: Blocks `/review` verdict. MUST fix before proceeding.
- **HIGH**: Does NOT block. MUST record risk decision in Work Log (`## Red Team Findings` section). Recommend using `/decide` to document accept/defer rationale.
- **MEDIUM / LOW**: Advisory only.

**Rationale**: Red Team analysis is inherently more speculative than OWASP checklist scanning. Hard-blocking on HIGH would create excessive false positives. But CRITICAL findings (e.g., a directly exploitable auth bypass path) must be treated as blocking.

## Work Log Integration

All Red Team findings MUST be recorded in the Work Log under `## Red Team Findings`:

```markdown
## Red Team Findings
- [date] /review: [N] findings ([severity breakdown])
- [date] /test: [N] adversarial cases generated
- HIGH risk decisions: [accepted/deferred — see /decide #N]
```

## Common Mistakes

- Marking speculative risks as CRITICAL without a concrete file:line attack path.
- Running Full Red Team on tiny-fix or quick-win (wastes tokens, no value).
- Treating Red Team findings as replacements for OWASP checks (they are complementary).
- Skipping Beast Mode on architecture-change (this is where systemic failures hide).
