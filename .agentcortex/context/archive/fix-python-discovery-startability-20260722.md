# Work Log: fix/python-discovery-startability

## Header

- Branch: `fix/python-discovery-startability`
- Classification: `quick-win`
- Classified by: `claude-opus-delegate`
- Frozen: `2026-07-22`
- Created Date: `2026-07-22`
- Owner: `claude-opus-delegate`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `af6ca2e1021aecde8c7e860a260917a40b2232fa` <!-- immutable: set once on first /implement -->
- Checkpoint SHA: `9ef5c3dcace730c430b802e743d20a6ff504f8ad` <!-- mutable: refresh each commit -->
- Recommended Skills: `none`
- Primary Domain Snapshot: `framework-tooling`
- SSoT Sequence: `129`

---

## Session Info

> Written by /bootstrap. Update on each new session.

- Agent: `claude-opus-delegate`
- Session: `2026-07-22 09:00 UTC`
- Platform: `claude-code`
- Files Read: `12`

---

## Task Description

> 1-3 sentences: what is being done and why.

Both validators (`validate.sh`, `validate.ps1`) select a Python interpreter by EXISTENCE only. On stock Windows the WindowsApps `python3.exe` App-Execution-Alias stub exists on PATH (exits 9009 with args) even with no Python installed, shadowing a working `python` and causing every python-backed check to spuriously fail. Replace existence-only selection with a silent startability probe (`-c "import sys"`, exit 0 required) with `python3`→`python` fall-through. Pre-existing defect (not a regression), surfaced by the 2026-07-22 codex post-ship review, primary-verified.

---

## Phase Sequence

> Record each phase entry in order. Update `Current Phase` in the Header on entry.

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-22 | quick-win; scope = 2 discovery blocks + tests + backlog row |
| plan | done | 2026-07-22 | startability probe, same semantics both validators; TDD |
| implement | done | 2026-07-22 | TDD red→green (8/8); validate.sh (LF) + validate.ps1 (CRLF+BOM) + new test file; ratchet 201/202 held |
| review | skipped | — | quick-win: review optional (§10.4) |
| test | skipped | — | quick-win: test optional; evidence recorded inline |
| handoff | skipped | — | quick-win exempt from handoff |
| ship | done | 2026-07-22 | backlog #144 + commit 9ef5c3d + PR; validators sh/ps1 parity pass=117 warn=3 fail=0 |

---

## Phase Summary

> One paragraph per completed phase. Delta-oriented: what changed, what was decided.
> End this section with the `⚡ ACX` sentinel at least once — `validate.sh` checks for it here so the runtime marker has a persistent audit trail (chat output is ephemeral).

- bootstrap: Classified `quick-win` (1 module: the two twin validators; clear, primary-specified scope). Read SSoT, implement.md, both validator discovery blocks + final reduced-assurance block, the false-positive test patterns, ratchet test + baseline (sh=201/ps1=202), worklog template. Captured ground truth on a clean deployed fixture: `pass=85 warn=3 fail=0` with python, `pass=75 warn=3 fail=0` (reduced-assurance top-line) under `--no-python`.
- plan: Fix = replace existence-only interpreter selection with a startability probe in BOTH validators (candidate order `python3`→`python` unchanged; select only if `<cand> -c "import sys"` exits 0 with output discarded; `--no-python`/`-NoPython` short-circuits before any probe; neither startable → empty/$null unchanged). No new `record_result`/`Add-Result` sites (ADR-006 ratchet held). Adopter delta: a Windows adopter with the store alias + a real python now gets a working validator instead of spurious python-check failures.
- implement: Edited the two discovery blocks only (`validate.sh:271-291` LF, `validate.ps1:202-227` CRLF+BOM) + new `tests/ci/test_validator_python_discovery.py` (8 tests: 2 structural marker/probe + 6 behavioral shim scenarios, sh+ps1 × broken-python3-fallthrough / no-startable-python / --no-python-short-circuit). TDD: RED against reverted existence-only validators = 6 failed / 2 passed (broken stub selected → `fail=9` → "integrity check failed"); GREEN after fix = 8 passed. ADR-006 ratchet unchanged (sh=201, ps1=202); ratchet test 5/5. EOL/BOM byte-verified. Full CI-equiv not-slow suite 664 passed.
- ship: Added backlog row #144 (Shipped). Committed the 2 discovery blocks + new test file + backlog row as `9ef5c3d` (excluded `.claude/settings.local.json`; Work Log gitignored). Repo-level validators confirm sh↔ps1 parity `pass=117 warn=3 fail=0 skip=2`, unqualified "passed" (probe selects the working `python3` on this host). The 3 WARNs are pre-existing (2 archived-log historical gaps + the #143 eval-coverage drift), not from this change. PR opened (do-not-merge; primary re-verifies). Rollback = revert the PR.

⚡ ACX

---

## Gate Evidence

> Gate receipts written by each phase. Format: `- Gate: <phase> | Verdict: PASS | Classification: <type> | Timestamp: <ISO>`
> **Critical**: `|` pipe separators are mandatory. Receipts placed inside markdown code fences are silently masked and NOT counted by validate.sh — always write receipts as plain list lines.
> Receipt order-of-appearance is authoritative for phase progression; `Timestamp` is provenance metadata only (validators require it to be present and parseable, but do NOT enforce monotonic/chronological ordering).

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T09:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T09:20:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T10:30:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-07-22T11:00:00Z

---

## External References

> Links to specs, ADRs, issues, PRs, or design docs relevant to this task.

| Type | Path / URL | Notes |
|---|---|---|
| ADR | docs/adr/ADR-006-validator-python-core-strangler.md | Ratchet constraint: no new native check sites |
| Spec | — | quick-win, no spec |
| Issue | backlog #144 | docs/specs/_product-backlog.md |
| PR | — | opened at ship |

---

## Known Risk

> List risks identified during planning or implementation. Include mitigation.

- ADR-006 native-check ratchet (HIGH lesson: new-validator-check hidden gates). Mitigation: discovery change is pure selection logic — zero new `record_result`/`Add-Result` lines; `test_validator_native_check_ratchet.py` must stay 201/202. Verified post-edit.
- Cross-platform EOL (HIGH lesson): validate.sh must stay LF; validate.ps1 must keep CRLF+BOM. Mitigation: Edit-tool-only, byte-verified before commit.
- PowerShell native non-zero-exit throw under `$PSNativeCommandUseErrorActionPreference=$true` (PS 7.4+). Mitigation: probe wrapped in try/catch AND checks `$LASTEXITCODE -eq 0`; both paths reject a broken candidate. This host is PS 7.5.8 with the pref = False.

---

## Decisions

> Optional (`/decide` §2): record trade-offs/constraints as `### D-N: <title>` with Decision/Reason/Alternatives/Impact lines. At `/ship`, every entry gets one disposition marker.

none

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

> Record deviations from the original plan, reclassifications, or unexpected scope changes.

- none

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

> quick-win: test phase optional. Evidence recorded inline in `## Evidence`.

none

---

## Evidence

> Reproducible evidence for completed phases. Commands, outputs, versions. "It should work" is NOT evidence.

- Ground truth (clean deployed fixture, worktree HEAD af6ca2e), `bash validate.sh`: `Summary: pass=85 warn=3 fail=0 skip=4` → `Agentic OS integrity check passed`.
- Ground truth, `bash validate.sh --no-python`: `Summary: pass=75 warn=3 fail=0 skip=14` → `Agentic OS integrity check passed (reduced assurance: python-dependent checks skipped)`.
- Host probe: `python3 -c "import sys"` exit 0 (Python 3.14.3); `python -c ...` exit 0. This host's `python3` (WindowsApps path first) is startable → discovery must still select `python3` here.
- TDD red (validators stashed to existence-only): `pytest test_validator_python_discovery.py` → **6 failed, 2 passed** — broken-python3 shim selected → `Summary: pass=76 warn=3 fail=9 skip=4` → "integrity check failed"; the 2 `--no-python` short-circuit tests passed (unaffected).
- TDD green (fix restored): same file → **8 passed** (108s).
- ADR-006 ratchet: `pytest test_validator_native_check_ratchet.py` → 5 passed; counts sh=201 ps1=202 (baseline, unchanged).
- Full CI-equiv not-slow: `pytest tests/ci tests/guard .agentcortex/tests -m "not slow"` → **664 passed, 121 deselected**.
- Repo validate.sh: `Summary: pass=117 warn=3 fail=0 skip=2` → `Agentic OS integrity check passed`.
- Repo validate.ps1: `Summary: pass=117 warn=3 fail=0 skip=2` → `Agentic OS integrity check passed` (identical → sh/ps1 parity).
- EOL/BOM byte-check: validate.sh pure LF, no BOM; validate.ps1 BOM present, 0 lone LF (pure CRLF).
