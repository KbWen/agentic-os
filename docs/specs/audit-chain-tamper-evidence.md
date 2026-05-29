---
status: shipped
title: Audit-Chain Tamper-Evidence Hardening (C1 truncation + C2 migrate)
created: 2026-05-29
source: self-audit-2026-05-29
primary_domain: document-governance
adr: docs/adr/ADR-003-hash-chained-audit-log.md
---

# Audit-Chain Tamper-Evidence Hardening

## Goal

Close two verified gaps between ADR-003's *stated* tamper-evidence guarantee and the *actual* behavior of the hash-chained `INDEX.jsonl` audit log:

- **C1** — tail-truncation (deleting the most recent entry/entries) is undetectable by `check_audit_chain.py` because the chain is back-linked only with no head/length commitment. Reproduced 2026-05-29: a 3-entry chain truncated to 2 still validates as intact. This contradicts ADR-003 line 79 ("any retroactive edit … breaks the chain … CI catches it").
- **C2** — `append_chain_entry.migrate` silently re-blesses tampered entries: it recomputes `prev_sha` for *any* mismatch, so editing a middle entry then running `migrate` produces a chain that validates. ADR-003 §Migration scopes migrate to entries that *lack* `prev_sha` (pre-ADR data), not to repair tampering.

Implements Work Log decisions **D-1** (git append-only witness) and **D-2** (migrate fail-on-tamper).

## Acceptance Criteria

- **AC-1** (C2): `migrate` adds `prev_sha` ONLY to entries that lack the field. An entry that already has `prev_sha` and whose value equals the recomputed value is left unchanged (idempotent). *Verify*: test — file with all-missing prev_sha → migrate fills all, exit 0; running migrate again → 0 updated, exit 0.
- **AC-2** (C2): If any entry HAS a `prev_sha` that does NOT equal the recomputed value (tampering), `migrate` makes NO writes and exits non-zero (2) with a message naming the offending line. *Verify*: test — edit a middle entry's content (breaking the successor's link) → `migrate` exits 2, file unchanged byte-for-byte.
- **AC-3** (C2): Mixed case — some entries lack `prev_sha` AND a later entry has a mismatched `prev_sha` — is treated as tampering: migrate refuses (exit 2, no writes). *Verify*: test asserting no partial write.
- **AC-4** (C1): A new validator check asserts the `INDEX.jsonl` committed at `origin/main` is a strict line-prefix of the working-copy `INDEX.jsonl` (append-only invariant). If the local file has fewer lines than the baseline, or any baseline line differs from the corresponding local line → FAIL naming the divergent line. *Verify*: test/sim — truncate local INDEX vs a baseline → check reports FAIL; append a new entry → PASS.
- **AC-5** (C1): The witness check degrades to WARN (never silent PASS, never FAIL) when any precondition is absent: not a git repo, `origin/main` unresolvable, or `INDEX.jsonl` absent on `origin/main` (e.g., first-ever commit, fresh downstream). *Verify*: test/sim in a repo with no origin → WARN, exit unaffected by this check.
- **AC-6** (C1): The check is present in BOTH `validate.sh` and `validate.ps1` with equivalent verdicts (cross-platform parity). *Verify*: grep both files for the witness block; structural test.
- **AC-7**: The existing `INDEX.jsonl` chain remains valid with ZERO entry migration — canonical hashed form is unchanged. *Verify*: `check_audit_chain.py --path INDEX.jsonl` → intact before and after this feature.
- **AC-8**: ADR-003 is amended: the line-79 overclaim is corrected; a "Tamper-Evidence Boundary" subsection documents that truncation is now caught at CI/PR-review against the published baseline (evidence, not prevention), the WARN-degradation, and the rotation (#3) re-anchor constraint. *Verify*: ADR-003 contains the new subsection; `status` updated to `accepted`.
- **AC-9**: All new behavior is covered in `tests/guard/test_audit_chain.py` (now CI-gated via PR #116). *Verify*: `pytest tests/guard/test_audit_chain.py` green; new tests present for AC-1..AC-5.

## Non-goals

- NOT adding a Merkle tree (ADR-003 deferred until >10K entries).
- NOT coupling INDEX.jsonl *existence/storage* to git (ADR-003 rejected). The witness READS git as an external append-only oracle only; INDEX.jsonl remains the authority.
- NOT extending the chain to Drift Log / Gate Evidence / Global Lessons (ADR-003 explicit follow-ups).
- NOT implementing INDEX rotation (#3); this spec only records the re-anchor constraint rotation must later honor.
- NOT adding a `seq` field (rejected in D-1 as theatre unless hash-protected, which would force a disruptive re-migration).
- NOT changing the chain's canonical hashing or `prev_sha` semantics.

## Constraints

- Stdlib + git only — no new dependency (ADR-003 CONSTRAINT preserved).
- `validate.sh`/`validate.ps1` are governed files; witness block must follow existing `record_result`/`Add-Result` patterns and the WARN/SKIP/FAIL conventions already in those validators.
- The witness must not FAIL on legitimate feature-branch state (local = baseline + appended entries is the normal case → PASS).
- Python-unavailable downstream: the C1 witness is shell/PowerShell-native (git diff of lines), so it works without Python; the C2 migrate fix is Python and only runs where Python exists.

## File Relationship

EXTENDS `docs/adr/ADR-003-hash-chained-audit-log.md` (amendment, not replacement). INDEPENDENT from all other `docs/specs/*.md` (the only shipped specs are lock-unification and ci-security-scanning; no overlap).

## Domain Decisions

- [DECISION] C1 tail-truncation detection uses git `origin/main` as an EXTERNAL append-only witness (validate.sh/.ps1 prefix check), chosen over a forgeable in-repo anchor file because a same-commit-forgeable anchor is false-confidence theatre per the [enforcement][HIGH] Global Lesson. (Work Log D-1)
- [DECISION] C2 `migrate` fails closed (exit 2, no writes) on an existing-but-mismatched `prev_sha`, only filling genuinely-missing fields — aligning the implementation with ADR-003's documented migration intent and removing the "run migrate to launder forged history" attack. (Work Log D-2)
- [TRADEOFF] The git witness provides tamper-EVIDENCE, not prevention: an attacker can still truncate + commit, but the deletion of published audit lines becomes visible in the PR diff against `origin/main` and must survive human review — raising cost from a 1-line silent delete to a reviewed history rewrite. Accepted as the strongest dependency-free guarantee absent an external transparency log.
- [CONSTRAINT] Future INDEX rotation (backlog #3) MUST re-anchor the witness baseline as a deliberate, reviewed operation; until rotation ships, `origin/main` is a valid monotonic lower-bound and the strict-prefix invariant holds.
- [CONSTRAINT] The witness MUST degrade to WARN (never silent PASS) when git/origin/baseline is unavailable, so absence of the oracle is visible rather than masked.
- [CONSTRAINT] No change to the chain canonical hashed form — existing `INDEX.jsonl` stays valid with zero migration.

## ⚡ ACX
