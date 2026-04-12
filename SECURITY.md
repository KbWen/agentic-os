# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Agentic OS, **please do not open a public issue**.

Instead, report it privately:

1. **Email**: Send details to the maintainer via GitHub's private vulnerability reporting (Settings > Security > Advisories > New draft advisory)
2. **Include**: Description of the vulnerability, steps to reproduce, affected files/workflows, and potential impact

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Assessment**: Within 7 days
- **Fix**: Depending on severity, typically within 14 days

## Scope

Security issues in Agentic OS may include:

- **Guardrail bypasses**: AI agents circumventing safety gates or destructive command blocks
- **Deploy script vulnerabilities**: Command injection, path traversal, or privilege escalation in `deploy.sh` / `deploy_brain.*`
- **SSoT integrity**: Unauthorized writes to `current_state.md` bypassing `guard_context_write.py`
- **Information leakage**: Framework exposing sensitive project data through Work Logs or handoff artifacts

## Out of Scope

- AI model hallucinations or incorrect outputs (these are model-level issues, not framework bugs)
- Vulnerabilities in downstream projects using Agentic OS
- Social engineering attacks against human contributors

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |
