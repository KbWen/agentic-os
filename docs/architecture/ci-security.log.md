---
status: living
domain: ci-security
---

# CI Security — Decision Log (L2)

### [ci-security][2026-08-12][fix/166-trufflehog-scanner-pin]
source_spec: docs/specs/ci-security-scanning.md
source_sha: 6f9205d

- [DECISION] ~~Full-history TruffleHog scan (`fetch-depth: 0` + `--only-verified`) over PR-scoped scan: catches pre-existing leaks introduced before the current PR~~ — **factually wrong as written; corrected 2026-08-12 (backlog #166), kept visible rather than deleted.** The scan was never full-history: the action's composite step runs `--since-commit <base> --branch <head>`, so it is PR/push-scoped and does **not** catch leaks introduced before the scanned range. `fetch-depth: 0` makes the base commit resolvable; it does not widen the scan. The surviving half of the decision stands: `--only-verified` bounds false positives and keeps wall-time acceptable, and Semgrep uses `pip install` rather than a container image because Docker Hub tags are two-part semver and pip enables reliable three-part pinning. This entry is a live instance of the `[spec-factual-claims]` Global Lesson — a Domain Decision asserting tool behaviour that no one verified, which then propagated into AC-3 and survived every subsequent review because reviewers check AC compliance, not rationale accuracy.
- [DECISION] (2026-08-12, backlog #166) TruffleHog pins the **scanner image** via `version: "X.Y.Z"`, kept equal to the `uses:` line's `# vX.Y.Z` comment by a test rather than by convention. Rejected alternatives: (a) *pin by image digest* — strictly more immutable, but unreadable at review time and it decouples from the version comment that Dependabot maintains, so drift becomes harder to notice rather than easier; (b) *leave `latest` and document it* — that is the honour-system-theatre pattern this repo has ruled against, and AC-5's own text already promises the scanner version is pinned; (c) *teach Dependabot to bump the input* — no supported mechanism for a `with:` value. The accepted design deliberately converts a silent unpin into a red test: a Dependabot bump moves the SHA and comment, the equality assertion fails, and a human syncs the input. Tradeoff accepted and recorded: the scanner no longer picks up new detectors automatically between bumps — detector freshness is traded for supply-chain immutability, which is the trade AC-5 already claimed to have made.

> First entry in this domain log. `docs/architecture/` is capability-by-presence — the file is created on demand, is excluded from the lifecycle-frontmatter check (`.log.md`), and is not counted by the token-lifecycle instrument. Scope of this entry is the two decisions this branch introduced or corrected, not the spec's full pre-existing Domain Decisions block.
