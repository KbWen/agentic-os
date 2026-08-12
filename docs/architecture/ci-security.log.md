---
status: living
domain: ci-security
---

# CI Security — Decision Log (L2)

### [ci-security][2026-08-12][fix/166-trufflehog-scanner-pin]
source_spec: docs/specs/ci-security-scanning.md
source_sha: 982ce7b
source_pr: https://github.com/KbWen/agentic-os/pull/402
> `source_sha` first named the diff base `6f9205d`, where this file does not exist — an independent review caught it. It now names a commit that contains these decisions. Note the branch is squash-merged, so pre-merge branch SHAs do not survive on `main`; the PR is the durable reference.

- [SUPERSEDED 2026-08-12, #166] The spec previously recorded, as a Domain Decision: *"Full-history TruffleHog scan (`fetch-depth: 0` + `--only-verified`) over PR-scoped scan: catches pre-existing leaks introduced before the current PR"*, and correspondingly listed a PR-delta scan under Non-goals. **Both were false from the day they were written.** The wrapper has always invoked `--since-commit <base> --branch <head>`; `fetch-depth: 0` only makes the base commit resolvable. The false rationale generated AC-3's matching claim and survived every later review, because reviewers check AC compliance rather than rationale accuracy — a live instance of the `[spec-factual-claims]` Global Lesson. The superseded wording is quoted **here**, in the history log, and has been removed from the live spec: struck-through text in an L1 document still reads as live text to grep and to any agent loading the file. Surviving from the original decision: `--only-verified` keeps wall-time acceptable, and Semgrep installs via pip because Docker Hub tags are two-part semver while pip allows exact three-part pinning.

- [DECISION 2026-08-12, #166] The TruffleHog scanner is pinned **by image digest**. `image` ends in `@sha256` and `version` carries the 64-hex manifest digest, so the wrapper's `docker run "${IMAGE}:${VERSION}"` join composes `…/trufflehog@sha256:<64 hex>`. `test_ac5_trufflehog_scanner_pinned_by_digest` reproduces that join and requires a digest form — an assertion about immutability **by construction**, not about two editable strings agreeing. If upstream ever changes the join, the composed string stops being a valid reference and `docker run` fails loudly rather than silently reverting to a tag.

- [SUPERSEDED 2026-08-12, before merge] The first design for the above pinned an exact release *tag* (`version: "3.96.0"`) and guarded it with a test asserting equality against the `# vX.Y.Z` comment on the `uses:` line; digest pinning was rejected as "unreadable at review time" and as decoupling from the comment Dependabot maintains. **Independent review refuted both halves and the design was replaced before merge.** A tag is mutable by design and can be re-pointed, so the immutability the fix claimed was not achieved; and a mutation harness kept all 42 tests green after swapping the wrapper SHA for the previous release's while leaving comment and input untouched — proving the comment is display metadata, not provenance. Readability is now served by a release comment beside the digest; binding is served by the digest.

- [TRADEOFF 2026-08-12, #166] Digest pinning means new detectors arrive only when a human updates the pin, and Dependabot cannot close the gap because it updates action refs, not container image references. An earlier framing called this "the trade AC-5 already claimed to have made" — **withdrawn on review**, which correctly separated stated pinning intent from deployed behaviour: the runtime had been resolving `latest` and therefore had *not* been paying this cost. It is newly incurred, and is carried in the spec's `## Accepted Risks` with owner, cadence, and an emergency path.

> First entry in this domain log. `docs/architecture/` is capability-by-presence — created on demand, excluded from the lifecycle-frontmatter check (`.log.md`), and not counted by the token-lifecycle instrument. Scope is the decisions this branch introduced, corrected, or superseded — not the spec's full pre-existing Domain Decisions block.
