# Work Log: fix/166-trufflehog-scanner-pin

## Header

- Branch: `fix/166-trufflehog-scanner-pin`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-12`
- Created Date: `2026-08-12`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `6f9205d`
- Checkpoint SHA: `6f9205d`
- Recommended Skills: `none`
- Primary Domain Snapshot: `ci-security`
- SSoT Sequence: `147`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-12 UTC`
- Platform: `claude-code`
- Files Read: `8`

---

## Task Description

Backlog **#166** (P1): the TruffleHog AC-5 SHA pin binds the wrapper action, not the scanner binary — the composite step runs `docker run <image>:${VERSION}` with `version` defaulting to `latest`. Second half of the row: AC-3 claims a full-history scan the wrapper never performs. Fix both, and close the drift path a naive fix would leave open.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-12 | quick-win; row #166 pre-frozen scope |
| plan | done | 2026-08-12 | pin-by-version + equality guard chosen over digest |
| implement | done | 2026-08-12 | workflow + 2 tests + AC-3/AC-5 + 2 decisions |
| review | skipped | 2026-08-12 | optional for quick-win; external review planned pre-merge |
| test | done | 2026-08-12 | 55 passed; both new tests proven red/green |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-08-12 | PR opened |

---

## Phase Summary

**bootstrap** — Scope was already frozen in row #166, written with reproductions during PR #401. `quick-win`: no new spec (amending a shipped one), no `/handoff`, three modules.

**plan** — Chose `version: "X.Y.Z"` + a machine-checked equality with the `uses:` line's `# vX.Y.Z` comment, over an image digest. Reasoning in D-2. The point is that the naive fix (add `version:` and stop) re-creates the defect on the next Dependabot bump, because Dependabot moves the SHA and comment but has no mechanism to move a `with:` input.

**implement** — `security.yml`: `version: "3.96.0"` plus a comment explaining what the SHA does and does not bind. `test_security_workflow.py`: two tests, one asserting the pin exists and is an exact `X.Y.Z`, one asserting it equals the version comment. `ci-security-scanning.md`: AC-3 corrected, AC-5 extended, and the source `[DECISION]` — whose rationale was itself false — corrected in place rather than deleted.

**test** — 42 passed in the changed file; 55 across both files that actually reference `security.yml`. Scope was decided by grep, not by feel: `test_deploy_tiering.py` mentions the workflow only in a comment, so the 37-test slow module is genuinely unaffected and was not run locally. Both new tests proven red, with discrimination — see Evidence.

**ship** — PR opened; validators re-run after the final Work Log write.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T07:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T07:10:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T07:30:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T07:45:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T08:00:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | `docs/specs/ci-security-scanning.md` | amended: AC-3, AC-5, 2 Domain Decisions |
| L2 | `docs/architecture/ci-security.log.md` | created this branch (AC-15 consolidation; owner-confirmed) |
| ADR | — | — |
| Issue | — | backlog #166, filed in PR #401 |

---

## Known Risk

- The scanner no longer auto-updates between bumps: new detectors arrive only when someone syncs `version:` after a Dependabot SHA bump. Accepted and recorded in D-2 — that is the trade AC-5 already claimed to have made.

---

## Decisions

### D-1: Correct the source `[DECISION]`, do not just fix the AC
The false "full-history scan" text in AC-3 originated in a Domain Decision whose *rationale* asserted the scan "catches pre-existing leaks introduced before the current PR". Fixing only the AC would have left the generative claim in place to re-propagate. Struck through and corrected in situ, with the surviving half of the decision kept, and labelled as a live instance of the `[spec-factual-claims]` Global Lesson: a Domain Decision making an unverified tool-behaviour claim, which then survived every review because reviewers check AC compliance, not rationale accuracy.
→ consolidated: L2 ci-security

### D-2: Pin the scanner by version + equality test, not by image digest
A digest is strictly more immutable, but it is unreadable at review time and decouples from the `# vX.Y.Z` comment Dependabot maintains — making drift *harder* to notice, which is the failure mode being fixed. Leaving `latest` and documenting it was rejected as the honour-system pattern this repo has ruled against. There is no supported way to have Dependabot bump a `with:` value, so the design deliberately converts the silent unpin into a red test. Tradeoff accepted: detector freshness for supply-chain immutability.
→ consolidated: L2 ci-security

### D-3: Keep `fetch-depth: 0` and keep its test
The fetch depth is still required — the wrapper's `--since-commit <base>` cannot resolve a base absent from a shallow clone. Only the *description* was wrong. `test_ac3_checkout_full_depth` therefore stays, with a comment stating what it does and does not certify, rather than being renamed or deleted.
→ local

### D-4: Local test scope set by grep, not by the full-suite reflex
`grep -rln` found three files referencing `security.yml`; two assert on it and were run (55 passed), the third mentions it only in a comment. The 37-test `test_deploy_tiering.py` slow module was therefore not run locally — recorded so the omission is a decision with evidence, not an unstated gap. CI runs the full command.
→ local

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

none

---

## Review Feedback

none

---

## Security Findings

- The fix closes a supply-chain control that did not hold: between the pin's introduction and this change, `main` executed whatever image `ghcr.io/trufflesecurity/trufflehog:latest` resolved to. Evidenced by pre-bump run `31288803917` @ `44b2e33` running scanner 3.96.0 under a v3.95.8 pin. No compromise is claimed or suspected — the exposure was the absence of the guarantee, not a known bad image.

---

## Red Team Findings

- The naive fix is the trap: adding `version:` without the equality guard passes review, then silently unpins on the next Dependabot bump. That path is now a red test.

---

## Design Reference

none

---

## Observability

none

---

## Resume

none

---

## Test Gate Results

- `pytest tests/ci/test_security_workflow.py` → **42 passed**
- `pytest tests/ci/test_ci_hardening.py tests/ci/test_security_workflow.py` → **55 passed**
- `pytest .agentcortex/tests/test_backlog_validation.py` → **3 passed**

---

## Evidence

- **Defect confirmed at the current pin, not just the old one**: `action.yml` fetched at `6f3c981e…` (the SHA `main` pins today) still declares `version: default: "latest"`. The fix is needed now, not retroactively.
- **Tag ↔ SHA correspondence verified** before relying on it: `gh api .../git/ref/tags/v3.96.0` → `6f3c981e7b77`, exactly the pinned SHA, so the `# v3.96.0` comment is a truthful anchor for the equality test.
- **Red/green with discrimination** — the two tests fail for different causes, which is what makes the pair worth having:
  - remove `version:` → **2 failed** (`..._scanner_image_pinned`, `..._version_matches_comment`), 40 passed
  - drift `version` to `3.95.8` while the comment says `v3.96.0` → **1 failed** (`..._version_matches_comment` only), 41 passed
  - restored → **42 passed**
- **Local scope justified by grep** (D-4): `security.yml` referenced by `test_ci_hardening.py`, `test_security_workflow.py` (both run, 55 passed) and `test_deploy_tiering.py` (comment only).
- Domain Decisions count 6 → 7, within the 10 cap.
- **Final validators** (terminal write; both runs postdate the self-archival): `validate.sh` **`pass=118 warn=4 fail=0 skip=2`** and `validate.ps1` **`pass=118 warn=4 fail=0 skip=2`** — exact parity, `fail=0`. Three WARNs are the pre-existing historical set; the 4th is a stale advisory lock left by the external reviewer's session during PR #401, gitignored and external to this diff.
- **The self-archival cleared the WARN it was supposed to clear.** Before it: `warn=5`, including `shipped work logs still in active work/ directory: 1` — this log, carrying a ship receipt while still active. After: `warn=4`, that line gone. The archival is doing the work the #401 D-8 lesson said it should, verified by the delta rather than asserted.
- **#168 reproduced itself during this ship, confirming the review correction.** After `git pull`, `INDEX.jsonl` came back from git as **fully CRLF** (`text=auto` + `core.autocrlf=true`); the pre-commit normalise reported **152 → 0**, not 1. That is exactly the "`w/lf` was a one-working-copy artifact, not a repository invariant" point raised in review of PR #401 — and it is why #168's fix requires the `*.jsonl text eol=lf` half and not just `O_BINARY`. Verified the append is still a clean single line: `git diff --numstat` → `1 0`, because the committed blob is LF and `text=auto` normalises at the commit boundary.
