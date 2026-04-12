# Security Guardrails

## Scope

Auto-applied during `/implement` (Post-Execution) and `/review` phases. AI MUST self-enforce — no user action required.

## 1. OWASP Top 10 Auto-Scan

When reviewing or completing code changes, AI MUST check for:

| ID | Category | What to Look For |
| --- | --- | --- |
| A01 | Broken Access Control | Missing auth checks, privilege escalation paths, IDOR |
| A02 | Cryptographic Failures | Hardcoded secrets, weak hashing (MD5/SHA1), plaintext sensitive data |
| A03 | Injection | SQL injection, command injection, XSS, template injection |
| A04 | Insecure Design | Missing rate limits, no input validation at trust boundaries |
| A05 | Security Misconfiguration | Debug mode in prod, default credentials, overly permissive CORS |
| A06 | Vulnerable Components | Known CVE in dependencies, outdated packages |
| A07 | Auth Failures | Weak password rules, missing MFA hooks, session fixation |
| A08 | Data Integrity Failures | Unsigned updates, untrusted deserialization, missing integrity checks |
| A09 | Logging Failures | Sensitive data in logs, missing audit trail for auth events |
| A10 | SSRF | Unvalidated URLs in server-side requests, internal network exposure |

## 2. Trigger Rules

- **Always On**: A01 (Access Control), A02 (Secrets), A03 (Injection) — checked on EVERY code change.
- **Context-Triggered**: A04–A10 — checked when the changed code touches the relevant domain (e.g., A06 only when dependencies change, A09 only when logging code is modified).
- **Severity Threshold**: Any finding rated HIGH or CRITICAL blocks `/review` verdict. MEDIUM findings are flagged but do not block.

## 3. Secret Detection

AI MUST scan all changed files for:

- API keys, tokens, passwords in source code or config files
- Private keys (RSA, SSH, PGP)
- Connection strings with embedded credentials
- `.env` files or environment variable files with secrets

If detected: **STOP immediately**. Output: "🔒 Secret detected in [file:line]. MUST be removed before commit."

## 4. Dependency Awareness

When `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, or similar dependency files are modified:

- Flag any NEW dependency added and state: "New dependency: [name]. Verify: license, maintenance status, known vulnerabilities."
- If a lock file changes without manifest change, note it for review.

## 5. Security Finding Output Format

When security issues are found, output using this structure:

```
## Security Findings

### [CRITICAL|HIGH|MEDIUM|LOW] — [Category ID]: [Brief Description]
- **File**: [path:line]
- **Risk**: [1-line explanation of what could go wrong]
- **Fix**: [Concrete remediation step]
```

## 6. Integration Points

- **`/implement` Post-Execution**: Run §1 Always-On checks (A01–A03) + §3 Secret Detection on all changed files. Append findings to Post-Execution Report.
- **`/review`**: Run full §1 scan (A01–A10 as applicable) + §3 + §4. Security findings MUST appear before "Ready to commit?" verdict.
- **`/ship`**: If any unresolved HIGH/CRITICAL security finding exists in the Work Log, ship gate = FAIL.
- **Work Log**: Security findings MUST be recorded in `.agentcortex/context/work/<worklog-key>.md` under a `## Security Findings` section. Unresolved findings remain in the log until resolved.

## 7. Boundaries

- This is **static analysis by AI inspection**, not runtime scanning.
- AI does NOT execute external security tools unless the project has them configured.
- Findings are based on pattern recognition and code understanding, not formal verification.
- When uncertain about severity, default to the HIGHER severity and flag for human review.
