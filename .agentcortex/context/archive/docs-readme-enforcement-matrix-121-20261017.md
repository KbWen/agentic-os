# Work Log: docs/readme-enforcement-matrix-121

## Header

- Branch: `docs/readme-enforcement-matrix-121`
- Classification: `quick-win`
- Classified by: `claude-opus-5-5`
- Frozen: `2026-10-17`
- Created Date: `2026-10-17`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `b891522`
- Checkpoint SHA: `none`
- Recommended Skills: `none`
- Primary Domain Snapshot: `docs`
- SSoT Sequence: `197`

---

## Session Info

- Agent: `claude-opus-5-5`
- Session: `2026-10-17 13:52 UTC` (8ab306f9)
- Platform: `claude-code`

---

## Task Description

Backlog #121: the README hero and "Rules vs. enforcement" table read as default-on enforcement, but a fresh install runs nothing until the adopter enables the hook / CI (deploy's own "TURN ON ENFORCEMENT" block says so). Add an honest on-after-install column, front-load the three wins usable on day one, add a FAQ entry for `⚡ ACX` and the gate block, and bring the zh-TW README to parity (3 required checks; security scans not required by default). Stacked on PR #470.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-10-17 | quick-win per backlog Tier; docs only |
| plan | done | 2026-10-17 | inline plan below |
| implement | done | 2026-10-17 | EN + zh-TW |
| review | done | 2026-10-17 | claim-by-claim fact check |
| test | done | 2026-10-17 | pins + validators |
| ship | done | 2026-10-17 | SSoT 197->198; #121 row archived |

---

## Phase Summary

- bootstrap: quick-win (README.md + docs/README_zh-TW.md). Pins: validate.sh/.ps1 encoding canaries ('governance-first layer for AI coding agents', '用工作流程、交付閘門與工程護欄'); tests/ci docs pins (`客製化而不衝突`, INSTALL link, pre-commit setup reachable). Facts verified in code before writing: deploy installs the hook only as `.githooks/pre-commit.guard-ssot.sample` and adds no CI job (deploy.sh "TURN ON ENFORCEMENT - a fresh install runs NOTHING until you do"); nothing in the framework detects a zero-test run — the adopter's CI does; validate.sh FAILs a feature/arch-change log at handoff/ship without Test Gate Results (AC-6); the three required checks are this repo's branch protection, not the adopter's.
- plan: (1) Hero: say the hooks/CI catch these once turned on. (2) Matrix gains an "On after install?" column and an advisory row for the workflow/skills; the paragraph separates this repo's required checks from the adopter's own floor. (3) "Usable on day one" list near the top: standalone credential gate, work log + `/handoff` resume, 14 skill checklists. (4) FAQ entry: `⚡ ACX` + `gate:` block, stated as self-reported marker + the validator's Phase Summary WARN. (5) zh-TW mirrors all of it. Verify: both validators, README pin tests, markdown link check locally if available. Rollback: revert the commit.
- implement: README.md + docs/README_zh-TW.md, same changes in both: hero says the hook/CI catch these once switched on (and drops "a green check over zero tests", which nothing in the framework detects); new "Usable on day one" / 「第一天就能用的」 list; matrix column "On after install?" / 「安裝後就生效?」 with an advisory row; floor paragraph separates this repo's three required checks from the adopter's own required CI job, and zh-TW now carries the required-checks + security-scans-not-required caveat; "What you get" and the "How do I stop…" FAQ say "once enabled"; new FAQ entry for `⚡ ACX` + `gate:`.
- review: each claim checked against code: hook ships only as `.githooks/pre-commit.guard-ssot.sample` and runs scan_credentials.py; deploy prints "a fresh install runs NOTHING until you do"; scan_credentials.py CLI = files / `--staged` / `--range`; validate.sh AC-6 FAIL on missing Test Gate Results at handoff/ship (feature/arch-change); validate.sh:1958 WARN on a Phase Summary without ⚡ ACX; hook setup is two lines (cp; chmod && git config). Self-caught: "two commands" → "two lines", "commands below" → "commands that turn it on", a doubled "turn it on". Verdict PASS.
- test: docs_pin 12 passed; README pin tests (deploy_tiering + pre_commit_hook `-k readme/install/doc`) 13 passed; both encoding canaries PASS; validate.sh = validate.ps1 fail=0.
- ship: PASS; #121 Shipped, row archived; queue now #217 → #228 → …; SSoT 197->198.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:52:05Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:53:30Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T13:58:00Z
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:01:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:02:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-10-17T14:07:20Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | docs/specs/_product-backlog.md | row #121 |
| ADR | — | — |
| Issue | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/470 | stacked |

---

## Known Risk

- README is the repo's landing page and is pinned in two layers; every edit is checked against both before commit.

---

## Decisions

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

- Implement/review/test receipt timestamps reconstructed from the session timeline (ordered, before the ship clock read).

---

## Review Feedback

none

---

## Red Team Findings

none

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

none

---

## Evidence

- `python -m pytest tests/ci/ -m docs_pin` → 12 passed (the CI docs-pins job's selection).
- `pytest tests/ci/test_deploy_tiering.py tests/ci/test_pre_commit_hook.py -k "readme or README or install or doc"` → 13 passed.
- validate.sh `[PASS] README.md encoding looks healthy`, `[PASS] README_zh-TW.md encoding looks healthy`, `Summary: pass=116 warn=6 fail=0 skip=2` (+1 WARN = lock/header phase mismatch mid-phase); validate.ps1 identical.
- No links added; Markdown link check left to CI.
