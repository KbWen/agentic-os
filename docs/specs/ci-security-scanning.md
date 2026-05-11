---
status: shipped
title: CI Security Scanning
created: 2026-05-11
primary_domain: ci-security
secondary_domains: []
source: backlog-#20
backlog_item: "20"
---

# Spec: CI Security Scanning

Backlog item #20 — P1, security/ci.

## Goal

Add automated security scanning to GitHub Actions CI so every PR to `main` is checked for code-level vulnerabilities (SAST), leaked credentials (secret detection), and known-CVE dependencies — before merge, with no human opt-in required.

## Acceptance Criteria

- **AC-1** — A workflow file exists at `.github/workflows/security.yml` and is triggered on `pull_request` targeting `main` (and on `push` to `main`).
- **AC-2** — The workflow contains a `semgrep` job that runs Semgrep with `--config auto --error` (language-agnostic; auto-detects languages present in the repo). The job exits non-zero on any finding. Note: `--metrics=off` is NOT used — Semgrep 1.123.0+ rejects `--config auto` when metrics are disabled (`Cannot create auto config when metrics are off`); Semgrep telemetry is aggregate stats only (file counts, rule counts — no repo content), so omitting `--metrics=off` still satisfies the no-repo-content constraint.
- **AC-3** — The workflow contains a `trufflehog` job that performs a full-history scan (`fetch-depth: 0`) with `--only-verified` to bound false positives. The job exits non-zero on any verified finding.
- **AC-4** — The workflow contains a `dependency-audit` job that runs `pip-audit` (OSV-backed). The run step detects Python dependency files at runtime (after checkout): `requirements*.txt` files are passed via `-r`; a `pyproject.toml` with `[project]` or `[build-system]` is audited via `pip-audit .`; if neither is present, the step exits 0 (skip). The job exits non-zero on any finding (`--strict`; pip-audit has no native severity filter — more conservative than HIGH/CRITICAL minimum and acceptable). Note: job-level `if: hashFiles(...)` is NOT used — it evaluates before checkout and always returns empty on GitHub-hosted runners.
- **AC-5** — All three scanner versions are pinned — not `@main`, `@latest`, or an unversioned branch ref. Semgrep via `pip install semgrep==X.Y.Z`; TruffleHog via GitHub Action **commit SHA** (40 hex chars) with a human-readable version comment (e.g., `@abc123...  # vX.Y.Z`) — semver tags are mutable and do not provide supply-chain immutability for third-party actions; first-party `actions/*` actions may use major-version tags (e.g., `@v4`); pip-audit via `pip install pip-audit==X.Y.Z`. Dependabot (`github-actions` ecosystem) MUST be configured to auto-bump SHA pins.
- **AC-6** — The workflow declares `permissions: contents: read` at the top level (minimal permissions).
- **AC-7** — No security job uses `continue-on-error: true` (silent failures prohibited).
- **AC-8** — The `validate.sh` and `validate.ps1` scripts gain a security workflow presence check: PASS if `.github/workflows/security.yml` exists; WARN if `.github/workflows/` exists but `security.yml` is absent (non-blocking); SKIP (no output, no counter impact) if `.github/workflows/` directory does not exist (non-Actions repos).
- **AC-9** — Running the updated `validate.sh` / `validate.ps1` against this repo produces 0 FAIL after the workflow file is added.
- **AC-10** — The security workflow is isolated in its own file (`security.yml`). The framework validation workflow (`validate.yml`) gains an additive `test-ci-structural` job to execute structural tests (AC-10 evidence); no existing validate jobs are modified or removed.
- **AC-11** — A `.semgrepignore` file exists at repo root and excludes `tests/`, `.agentcortex/templates/`, and `installers/`. These directories contain intentional bad-pattern examples and eval/curl installer patterns that would cause false positives under `--config auto --error`. The structural test suite asserts both file existence and required exclusions so accidental deletion is caught by CI rather than silently passing with zero coverage.

## Non-goals

- DAST / fuzzing / runtime testing — no running server exists.
- License compliance scanning.
- Container image scanning — no Docker in this repo.
- SBOM generation.
- GitHub Advanced Security code-scanning alert integration (no org-level GitHub Advanced Security license assumed).
- npm / yarn dependency audit — no `package.json` in this repo.
- PR-delta-only TruffleHog scan (`--since-commit`) — full-history with `--only-verified` is fast enough and catches pre-existing leaks.

## Accepted Risks

- **Semgrep registry outage → silent pass**: `--config auto` downloads rules from `semgrep.dev` at runtime. If the registry is unreachable, Semgrep may load zero rules and exit 0 with no findings — the SAST gate passes with zero coverage. Mitigation: weekly scheduled scan on `main` surfaces outage-driven false-negatives independent of PR cadence. Re-evaluate if this repo moves to a stricter security tier.
- **TruffleHog `--only-verified` false-negative rate**: Deliberately trades recall for precision. A credential whose verification probe is blocked (network timeout, rate-limit, revoked-but-not-yet-cleaned-up key) reports as "unverified" and the job passes. Accepted: `--only-verified` is required per AC-3 to bound false positives; the alternative (no `--only-verified`) produces signal-to-noise too low to act on.
- **Dependency audit skips repos without root-level Python manifests**: AC-4 gates on `requirements*.txt` at repo root or `pyproject.toml` with `[project]`/`[build-system]`. Poetry-only projects, `setup.py`-only projects, and repos with only subdirectory requirements files are not audited. This repo currently has no auditable Python manifests; the job runs, emits a visible warning annotation, and exits 0. Re-evaluate when Python dependencies are introduced.
- **Semgrep rule non-determinism**: `--config auto` rules update independently of the pinned `semgrep==X.Y.Z` version. The same commit can produce different findings on different dates. Accepted for now; pinning a specific offline ruleset is a follow-up if rule-drift causes repeated false-positive noise.

## Constraints

- Must run on `ubuntu-latest` GitHub-hosted runners (no self-hosted runners).
- Target additional CI wall-time: ≤ 3 minutes per PR (all three jobs can run in parallel).
- Must require no external API keys or paid-tier accounts — community/open-source tiers only.
- Semgrep must not phone home with repo contents. `--metrics=off` is NOT used (incompatible with `--config auto` in Semgrep 1.123.0+); Semgrep telemetry transmits only aggregate stats, never file contents — constraint is satisfied without the flag.
- All tool installs must use official distribution channels (official GitHub Actions or `pip install`) — no vendored binaries committed to the repo. Semgrep via `pip install` (Docker Hub tags use two-part semver `1.x`, not three-part `1.x.y` — makes pinning unreliable); TruffleHog via official GitHub Action.

## File Relationship

INDEPENDENT — no existing spec covers CI pipeline security. Does not extend or replace any existing `docs/specs/*.md`.

Target files:
- **New**: `.github/workflows/security.yml`
- **New**: `.github/dependabot.yml` (AC-5 Dependabot auto-bump)
- **New**: `tests/ci/test_security_workflow.py` (AC-10 structural tests)
- **New**: `.semgrepignore` (Semgrep scan scope — excludes test fixtures and installer scripts)
- **Modified**: `.agentcortex/bin/validate.sh` (AC-8 check)
- **Modified**: `.agentcortex/bin/validate.ps1` (AC-8 check)
- **Modified**: `.github/workflows/validate.yml` (AC-10 additive `test-ci-structural` job)

## Clarifications Resolved

None — scope was unambiguous from backlog item description.

## Domain Decisions

- [DECISION] Semgrep chosen for SAST over CodeQL and Bandit: language-agnostic (covers both Python and bash), fast (< 60 s on this repo), free community tier requires no API key or paid account, maintained official GitHub Action available. Note: `--config auto` fetches rulesets from `semgrep.dev` registry at runtime — no key is required but outbound network access to `semgrep.dev` is needed; see Accepted Risks for registry-outage behavior.
- [DECISION] TruffleHog chosen for secret detection over git-secrets and gitleaks: broader regex coverage for modern secret formats (cloud provider keys, API tokens), verified-findings mode reduces false positives, has a maintained official GitHub Action.
- [DECISION] `pip-audit` chosen for dependency audit over `safety` and `snyk`: queries OSV directly without requiring a paid API key, integrates cleanly with `pip`, exit-code semantics are well-defined per severity.
- [DECISION] Full-history TruffleHog scan (`fetch-depth: 0` + `--only-verified`) over PR-scoped scan: catches pre-existing leaks introduced before the current PR; `--only-verified` bounds false positives and keeps wall-time acceptable. Docker Hub image tags use two-part semver — pip install used for Semgrep instead of container image to enable reliable three-part pinning.
- [DECISION] Separate `security.yml` workflow file over adding jobs to `validate.yml`: keeps framework integrity checks and security scans independently retry-able; validate.yml failures don't block security job reruns and vice versa.
- [CONSTRAINT] All scanner action versions MUST be pinned to a specific tag or commit SHA — not floating refs — to prevent supply-chain attacks on the CI pipeline itself.
- [TRADEOFF] Semgrep `--config auto` (language-agnostic) over hardcoded `p/python + p/bash`: auto-detection avoids baking in language assumptions. Community-tier only — no Pro rulesets, no API key required.
