---
status: frozen
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
- **AC-2** — The workflow contains a `semgrep` job that runs Semgrep with `--config auto` (language-agnostic; detects languages present in the repo automatically) and `--metrics=off --error`. The job runs inside a pinned Semgrep container image so no host Python installation is required. The job exits non-zero on any finding.
- **AC-3** — The workflow contains a `trufflehog` job that scans only commits introduced by the current PR (`--since-commit <base-sha>`) for leaked secrets. The job exits non-zero on any verified finding.
- **AC-4** — The workflow contains a `dependency-audit` job that runs `pip-audit` (OSV-backed) if any `requirements*.txt` or `pyproject.toml` file exists in the repo root. The job exits non-zero on findings with severity HIGH or CRITICAL.
- **AC-5** — All three scanner versions are pinned to a specific tag — not `@main`, `@latest`, or an unversioned branch ref. Semgrep version is pinned via container image tag (e.g. `semgrep/semgrep:X.Y.Z`); TruffleHog via GitHub Action semver tag; pip-audit via `pip install pip-audit==X.Y.Z`.
- **AC-6** — The workflow declares `permissions: contents: read` at the top level (minimal permissions).
- **AC-7** — No security job uses `continue-on-error: true` (silent failures prohibited).
- **AC-8** — The `validate.sh` and `validate.ps1` scripts gain a security workflow presence check: PASS if `.github/workflows/security.yml` exists, WARN if absent (non-blocking — projects without GitHub Actions still pass the main gate).
- **AC-9** — Running the updated `validate.sh` / `validate.ps1` against this repo produces 0 FAIL after the workflow file is added.
- **AC-10** — The security workflow is isolated in its own file and does not modify `.github/workflows/validate.yml`.

## Non-goals

- DAST / fuzzing / runtime testing — no running server exists.
- License compliance scanning.
- Container image scanning — no Docker in this repo.
- SBOM generation.
- GitHub Advanced Security code-scanning alert integration (no org-level GitHub Advanced Security license assumed).
- npm / yarn dependency audit — no `package.json` in this repo.
- Full-history TruffleHog scan (too slow; pre-existing secrets should be rotated out-of-band).

## Constraints

- Must run on `ubuntu-latest` GitHub-hosted runners (no self-hosted runners).
- Target additional CI wall-time: ≤ 3 minutes per PR (all three jobs can run in parallel).
- Must require no external API keys or paid-tier accounts — community/open-source tiers only.
- Semgrep must not phone home with repo contents (`--metrics=off` or equivalent).
- All tool installs must use official distribution channels (container images from Docker Hub/GHCR, official GitHub Actions, or `pip install`) — no vendored binaries committed to the repo. Prefer container images over `pip install` to avoid imposing a Python dependency on non-Python repos.

## File Relationship

INDEPENDENT — no existing spec covers CI pipeline security. Does not extend or replace any existing `docs/specs/*.md`.

Target files:
- **New**: `.github/workflows/security.yml`
- **Modified**: `.agentcortex/bin/validate.sh` (AC-8 check)
- **Modified**: `.agentcortex/bin/validate.ps1` (AC-8 check)

## Clarifications Resolved

None — scope was unambiguous from backlog item description.

## Domain Decisions

- [DECISION] Semgrep chosen for SAST over CodeQL and Bandit: language-agnostic (covers both Python and bash), fast (< 60 s on this repo), free community tier requires no external API call, maintained official GitHub Action available.
- [DECISION] TruffleHog chosen for secret detection over git-secrets and gitleaks: broader regex coverage for modern secret formats (cloud provider keys, API tokens), verified-findings mode reduces false positives, has a maintained official GitHub Action.
- [DECISION] `pip-audit` chosen for dependency audit over `safety` and `snyk`: queries OSV directly without requiring a paid API key, integrates cleanly with `pip`, exit-code semantics are well-defined per severity.
- [DECISION] PR-scoped TruffleHog scan (`--since-commit`) over full-history scan: keeps CI wall-time within budget; pre-existing historical secrets should be rotated regardless of scan outcome.
- [DECISION] Separate `security.yml` workflow file over adding jobs to `validate.yml`: keeps framework integrity checks and security scans independently retry-able; validate.yml failures don't block security job reruns and vice versa.
- [CONSTRAINT] All scanner action versions MUST be pinned to a specific tag or commit SHA — not floating refs — to prevent supply-chain attacks on the CI pipeline itself.
- [TRADEOFF] Semgrep `--config auto` (community rules, language-agnostic) over hardcoded `p/python + p/bash`: downstream repos use diverse languages; auto-detection avoids baking in language assumptions. Community-tier only — no Pro rulesets, no API key required.
- [TRADEOFF] Semgrep runs in a container image rather than via `pip install`: removes Python as a host dependency for SAST, making the job usable for any-language repos. Version pinning moves from pip version string to container image tag.
