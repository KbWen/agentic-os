# Compaction Overflow: fix/validator-twin-parity-176-175 (2026-08-23)

## Phase Summary

Compaction overflow of the STILL-ACTIVE log at `.agentcortex/context/work/fix-validator-twin-parity-176-175.md` (12KB cap hit during /implement). Holds the full three-panel expert record behind decision D-1 (#176 delete-vs-document), each claim re-verified by the primary against ground truth. Not a completed task; see the active log for current phase and evidence.

⚡ ACX

## Decisions — D-1 panel record (moved from the active log)

- **Panel input 3/3 (downstream-risk lens) — primary re-verified:**
  - ✅ **CONFIRMED — the highest-value practical finding, and it lands in a REQUIRED job.** `validate.ps1` is **pure CRLF (2840 CRLF / 0 bare LF) with a UTF-8 BOM**; `validate.sh` is **pure LF (0 CRLF / 3039 LF), no BOM** (`.gitattributes:5,8`). `check_text_integrity.py:106` flags `mixed-eol` and `:99` `utf8-bom`, and that check runs inside the **required** `Framework Validation` job. **Any edit to `validate.ps1` — including #175's — must write CRLF and preserve the BOM, verified by byte count, not by eye.**
  - ✅ **CONFIRMED — two silence tiers, not one.** `validate.sh:181-183` increments `TOOL_ABSENT_UNEXPECTED` only when `ACX_ABSENT_REASON` is empty, and the wrapper sets it at `:216`. So a missed **direct** site (13 of 15) still moves the summary to `passed (reduced assurance: N referenced tool(s) absent…)`, but a missed **source-only** site (2 of 15) produces output **byte-identical to a healthy install**.
  - ✅ **CONFIRMED — independent reproduction of my own mutation run**: today 2/2 PASS · both sites edited 0/2 FAIL · one site missed 1/2 FAIL. Two panels and the primary agree; the tenth man's "stays green on a missed site" is refuted three ways.
  - ✅ **CONFIRMED — `run_python_check_source_only`'s body needs no edit**: `validate.sh:214-218` consumes only `$1` and forwards `"$@"` verbatim (arity-agnostic). Its two **call sites** do need the token removed, and they are the highest-risk edits in the change.
  - ✅ **Scope correction accepted: 30 call-site edits (15 sh + 15 ps1)**, not the row's ~28, plus 2 function-def edits (`validate.sh:176` delete + `:178` `shift 3`→`shift 2`; `validate.ps1:154` delete).
  - ❌ **PARTIALLY REFUTED**: the panel claimed `validate.ps1:157-160` carries a parallel "not a fake FAIL" comment. It does not — that is the `-AbsentReason` comment. Grep confirms **one** such comment repo-wide, `validate.sh:651`, and it names the *PowerShell* identifier inside the *bash* file. One stale comment to rewrite, not two.
  - ⚠️ **Useful negative result**: `--list-checks` (`validate.sh:316-322`) greps `record_result <LEVEL> "literal"` and drops `^\$` variable labels, so it is **structurally blind to all 15** python checks and cannot serve as a guard. (Also relevant to backlog #92, which proposes a `-ListChecks` twin.)

- **Panel input 2/3 (tenth-man / refute-only) — primary re-verified; the headline objection is half-refuted by measurement:**
  - ✅ **CONFIRMED — blast radius is larger than the row's "28 call-site edits"**. Deleting the parameter also requires touching:
    - `tests/ci/test_validator_absent_tool_signal.py:79-81` — its regex `...\s+\w+\s+"([^"]+)"` **encodes the positional contract** ("Positional contract: reason, label, missing-python level, script").
    - three tool docstrings that name **"WARN-tier wiring"** as an existing thing: `check_ssot_caps.py:18`, `check_decision_disposition.py:43`, `check_worklog_references.py:30`.
    - `check_worklog_references.py:~39-41`, which cites **`validate.sh:192-196` by line number** — removing a line from `run_python_check` shifts that anchor.
    - `docs/specs/decision-capture-hardening.md` (`status: shipped`) **AC-6 (wiring parity)**, which literally requires `Invoke-PythonCheck ... -MissingPythonLevel 'WARN'` in validate.ps1. Deleting the parameter falsifies an AC verbatim. (Mitigating: AC-28 treats `shipped` specs as historical snapshots, not live design authority — this is drift to note, not a frozen-spec gate.)
  - ❌ **REFUTED BY MEASUREMENT — the "inverted test" claim.** The panel asserted a *missed* call site leaves the regex matching → test stays GREEN on a wrong migration. Executed with the exact regex literal extracted from the test source:
    - today: `parsed=2 invocations=2` → PASS (and `pytest tests/ci/test_validator_absent_tool_signal.py -q` → **6 passed**).
    - correct deletion of both sites: `parsed=0 invocations=2` → **RED** (true — the test must be retuned in the same commit).
    - **missing one site: `parsed=1 invocations=2` → RED as well.** So it is not a green-on-wrong trap; the `parsed == invocations` assertion fires in both directions. The correct disposition is "retune the regex to the new arity", NOT "loosen it".
  - ⚠️ **Objection 3 correspondingly weakened**: the 2 `run_python_check_source_only` sites are the *only* ones carrying a static guard. The unguarded surface is the **13 direct `run_python_check` sites**, not the source-only pair.
  - ✅ **CONFIRMED (consistent with known repo state)**: only three required contexts exist (`Framework Validation`, `ShellCheck`, `Check Markdown Links`); every guard that would catch a slip is non-required. Any new static guard is signal, not a merge gate.
  - ✅ **Panel's own concession, verified**: the PowerShell half is safe — `Invoke-PythonCheck` is an advanced function with `[Parameter(Mandatory=$true)]`, so a leftover `-MissingPythonLevel` is a terminating binding error. All real risk is the 13 unguarded bash sites.
- Reason: —
- **Panel input 1/3 (governance-doctrine lens) — primary re-verified every load-bearing claim against ground truth:**
  - ✅ **CONFIRMED (decisive)**: the parameter is not dead-from-birth, it is the **vestige of a deliberate removal**. `git show e9355c7` ("fix: make Python optional for downstream validation (#51)") removes `- record_result "$missing_python_level" "$label -- python unavailable"` and `- Add-Result -Level $MissingPythonLevel ...` in the same commit, replacing both with hardcoded SKIP/WARN. The annotation is residue of behaviour this repo consciously replaced.
  - ✅ **CONFIRMED**: `engineering_guardrails.md:425` scopes §13 (Deletion-First / ADD-Gate) to `AGENTS.md`, `.agent/rules/*`, `.agent/workflows/*`, `.agent/config.yaml`, or adding a MUST/NEVER/gate. `.agentcortex/bin/validate.sh` is in none of them — **§13 does not bind D-1**. (Targeted 1-line read, logged in Drift Log per the Read-Once Safety Valve.)
  - ✅ **CONFIRMED**: ADR-011:70-74 scopes `keep-honest-unenforced` to `NONE`-tier **directives on the four phase-entry surfaces**, defined as "a behavior-shaping advisory retained but honestly labeled NONE with a rationale". A shell parameter is neither a directive nor on those surfaces, and the annotation is not unenforced-but-true — it is false at the FAIL sites. The vocabulary does not cover option B.
  - ✅ **CONFIRMED**: option B's deliverable is already partly shipped — `validate.sh:649-651` already carries the site prose "(MissingPythonLevel is WARN, not a fake FAIL.)".
  - ✅ **CONFIRMED**: `-MissingPythonLevel 'FAIL'` × **10** vs `'WARN'` × **5** in `validate.ps1`. The 10 FAIL annotations describe behaviour that is WARN; the 5 WARN ones are vacuously true.
  - ✅ **CONFIRMED**: `generate_safety_nucleus.py:59` `sys.exit(2)` / `:86` `return 1` — so the row's "the one that does [have a nonzero path]" undercounts. Its `:78` `"WARN (downstream): ..."` is the **successor pattern**: environment-dependent severity decided *inside* the tool, where the distinguishing fact exists.
  - ✅ **CONFIRMED**: `tests/ci/test_validator_twin_parity.py:26` records that the `CI Structural Tests` / `Pytest (Windows)` / `Framework Validation (Windows)` contexts are **non-required** — any new static guard is signal, not a merge gate. Do not over-claim it.
  - ❌ **CITATION REFUTED, argument survives**: the panel cited `_product-backlog.md:141` (row #173) as recording that a `SOURCE_ONLY_TOOLS` allowlist was *rejected* because "the allowlist's payload is a comment", closing "Do NOT re-propose the allowlist." **No such text exists in row #173** — the row *proposes* the allowlist ("Work when picked up: ... add an explicit `SOURCE_ONLY_TOOLS` allowlist"). The substance is nevertheless true and lives in the **code**: `validate.sh:208-212`'s comment for `run_python_check_source_only` states the reason "travels with the call site ... instead of a separate registry ... rather than as absence from a list that can go stale", and `ACX_ABSENT_REASON` is a **real consumer** (suppresses `TOOL_ABSENT_UNEXPECTED`, changes the printed message and the CI outcome). Corrected citation: `validate.sh:208-212`, not the backlog row.
- Alternatives: (a) delete `missing_python_level` / `$MissingPythonLevel` plus 28 call-site edits; (b) keep it and document the always-WARN degrade as deliberate. Implementing the parameter's real semantics is **rejected up front** on measured downstream breakage.
- Impact: —

---


## #176-only material (moved from the active log — this unit ships #175 only)

**Required guards if/when #176 is executed** (both needed; neither exists today):
1. **13 direct sites** — assert the final line of the required `validate` job is exactly `Agentic OS integrity check passed`. The signal already exists and nothing reads it. Scope to the `validate` job only (`deploy-no-python` legitimately prints "reduced assurance"), and use `set -o pipefail` if teeing — `validate.yml:211-217` records a prior incident where `| tee` swallowed the exit code.
2. **2 source-only sites** — retune `test_validator_absent_tool_signal.py:82`'s regex to the new arity (drop `\s+\w+`). **Do NOT loosen it**; mutation-test it red before trusting it.
Honest ceiling on both: only `Framework Validation`, `ShellCheck`, `Check Markdown Links` are required contexts, so guard 2 is signal, not a merge gate. Guard 1 is inside a required job and can block.

**Not carried into #176's cost:** the PowerShell half self-guards — `Invoke-PythonCheck` is an advanced function with `[Parameter(Mandatory=$true)]` under `$ErrorActionPreference = 'Stop'`, so a leftover `-MissingPythonLevel` aborts the run and exits 1.

### Known Risk (#176)
- **#176 — riskiest edit in the family**: bash `shift 3` → `shift 2` across 15 call sites. A missed site silently turns `$script` into the literal string `FAIL`, the check degrades to a SKIP, and **exit stays 0 with CI green**. Mitigation: the receipt must be **byte-identical validator output** before vs after, not merely a green run.
- **#176 — do NOT implement the parameter's semantics.** Measured: it flips five FAIL-wired checks to FAIL on every Python-less adopter on install day, which the no-python doctrine explicitly permits. Live options are delete-the-parameter or keep-and-document-as-deliberate.

### Bootstrap scope-narrowing rationale
**Scope narrowed at bootstrap** (from the 4-item cluster the user approved), on the backlog rows' own evidence rather than preference:

- **#177 is blocked, not ready**: `docs/specs/downstream-adaptability-optimization.md` is `status: frozen` and its **AC-S5** mandates the two `deploy.sh` sites the row wants collapsed. It needs an unfreeze/amendment first. Drift is already caught by `tests/ci/test_validator_absent_tool_signal.py`, so the duplication is not silently rotting.
- **#178 needs its own unit** (its own row says so): it is an `AGENTS.md` governance-surface edit, and its sub-item — the `frozen` vs `[Shipped]` status mismatch on `downstream-adaptability-optimization.md` — is exactly **#177's blocker**. Correct sequence is #178 → #177.
- Running all four here would touch 3 modules (validator / deploy / governance) and trip the `state_machine.md` Scope Escalation hard-block (`> 2 modules`), forcing a reverse transition mid-flight.

## Plan-phase ground-truth evidence (moved verbatim from the active log — NOT summarized)

### plan — ground truth established first-hand (not taken from the backlog rows)

- **#176 deadness confirmed**: `validate.sh:174-177` assigns `local missing_python_level="$2"` and never reads it; the python-absent branch (`:190-196`) hardcodes `record_result WARN`. `validate.ps1:154` declares `[Parameter(Mandatory=$true)][string]$MissingPythonLevel`, never referenced; `:173-179` hardcodes `Add-Result -Level 'WARN'`.
- **Twin asymmetry (NOT in the backlog row)**: bash is **positional** (`shift 3`) → a missed call site silently degrades to SKIP with exit 0. PowerShell is **named** (`-MissingPythonLevel 'FAIL'`) → a missed call site is a loud parameter-binding error. The silent-failure hazard is **bash-only**.
- **Frozen-spec interaction**: `docs/specs/downstream-adaptability-optimization.md` (`status: frozen`) **AC-D6** mandates `No-Python → WARN ... never silent PASS, never FAIL` for the `downstream-capabilities gate-safety` check (`validate.sh:652` / `validate.ps1:787`). AC-D6 constrains **behaviour**, which is hardcoded and unchanged by deleting the annotation — so a behaviour-preserving deletion does not require an unfreeze. The `WARN` at that one call site is therefore spec-backed, while the `FAIL` annotations are aspirational-and-rejected.
- **Native-check ratchet NOT tripped**: `tests/ci/validator_native_baseline.json` counts line-leading `record_result ` / `Add-Result ` sites only. Neither fix adds or removes one.
- **#175 MFR reproduced on this box** (`cat -v` on the redirected byte stream; console default is `big5` / cp950):
  - before — `powershell` 5.1 AND `pwsh` 7 both emit `section=[M-!M-1] emdash=[M-!X]` (big5 0xA1B1 / 0xA158) = wrong bytes.
  - after (`New-Object System.Text.UTF8Encoding $false` + `try/finally` restore) — both emit `section=[M-BM-'] emdash=[M-bM-^@M-^T]` = correct UTF-8 (0xC2A7 / 0xE28094), and `restored=big5` confirms the caller's console state is handed back.
  - **Corrects backlog row #175**: it claims the bug "does not reproduce on `pwsh` 7". On the redirected path it reproduces identically on both shells. Measured, not read.
- **#175 fix mechanics verified empirically**, both required for a whole-body `try/finally` with a minimal diff:
  - a PowerShell `try` block does **not** create a new scope — locals, `$script:` vars, and functions defined inside stay visible after it.
  - `finally` **does** run on `exit 1` from inside the `try`, and the exit code is preserved (measured: `exitcode=1`).

## Bootstrap/plan historical detail (moved from the active log)

### Read Plan + phase chain
Read Plan: SSoT header + Spec Index (read) · `_product-backlog.md` Feature Inventory (read) · `state_machine.md` (read) · `bootstrap.md` (read) · `skill_conflict_matrix.md` (read once, Conflict Pass) · `engineering_guardrails.md` **skipped** (quick-win Token Leak Block) · `validator-strangler-policy.md` **skipped** (shipped, AC-28) · Domain Doc L1/L2 **skipped** (feature/arch only).
Phase chain (quick-win): `/plan → /implement → /ship` (review/test optional; handoff exempt).

### Phase Summary — bootstrap and plan paragraphs
**bootstrap** — Classified `quick-win`: the validator twin is one module and the estimated diff sits well under the 200-line / 2-module escalation thresholds. Scope narrowed from the approved 4-item cluster to #176 + #175 because #177 is blocked on a frozen-spec AC amendment and #178 is a governance-surface unit that also unblocks #177. Three skills matched; conflict pass clean. Backlog rows #175/#176 advanced `Pending → In Progress`. KB present and readable but **not consulted** — its `task_routing` covers product/app domains, none of which maps to a shell/PowerShell validator parameter cleanup.
**plan** — Three same-vendor expert panels on D-1; every load-bearing claim re-verified by the primary. Outcome: (A) delete is doctrinally and technically correct for #176, but its real blast radius (30 call sites + a test regex + 3 tool docstrings + a line-number anchor + a shipped-spec AC) crosses the `> 2 modules` hard-block, so #176 is re-cut as its own unit and **this unit ships #175 only**. Three panel claims were corrected by measurement rather than accepted. Confidence: 92% — high.

### Drift Log — bootstrap-phase entries
- SSoT write (bootstrap exception, AGENTS.md §Non-ship SSoT write exceptions): refreshed `Last Verified` 2026-08-15 → 2026-08-23 via `guard_context_write.py`. No other field touched.
- Backlog write (bootstrap.md §5 status advance): rows #175 and #176 advanced `Pending → In Progress` in `docs/specs/_product-backlog.md`.
- **Conflicting directive observed live — this is backlog #178's exact case.** `AGENTS.md` §vNext State Model §Write Isolation scopes `_product-backlog.md` writes to spec-intake/ship, while `bootstrap.md` §5 mandates the `Pending → In Progress` advance at bootstrap. Precedence (AGENTS.md > workflows) would forbid the step the workflow requires. Proceeded per the workflow and logged here; the resolution belongs to #178, not this unit.
- `kb-consult` not activated: `knowledge_sources` is present and readable (kb-main, `schema_version` 6, `kb_version` `328b30ecb33b`), but the manifest's `task_routing` maps only product/app domains (Web SaaS, mobile, UI, backend/API, security, DB, AI/LLM, error handling, performance, pre-launch, incident, debugging) — none covers framework-internal shell/PowerShell validator maintenance. Applicability filter per §3.6, recorded rather than silently skipped.
- Re-read: `.agent/rules/engineering_guardrails.md` §13 (scope line only, `:425`) — reason: adjudicating a panel claim that §13 does not bind this change; targeted 1-line verification, not a section load.
- §3.6a user-preference merge skipped: `.agentcortex/context/private/user-preferences.yaml` absent (capability-by-presence, zero cost).

---

## Implement-phase process narrative (moved verbatim from the active log)

### implement — a real defect the gate caught in me

Running the validator (rather than reading it) surfaced two findings against **my own** work, both now fixed:

- `[FAIL] work log compaction warnings detected` — **not** the known gitignored-log artifact. Re-derived: this Work Log had reached **22,690 bytes vs the 12 KB `max_kb` cap** in `.agent/config.yaml §worklog`. I had skipped `implement.md §Work Log Compaction Check`. Compacted per `/handoff §6` to 11.2 KB, protected sections (`Gate Evidence`, `Skill Notes`, `Conflict Resolution`, `Evidence`, `Session Info`) left intact.
- `[WARN] work log lock owner/phase mismatches detected: 1` — the lock had `phase: implement` while the header still read `Current Phase: plan`. That is exactly the "session that skipped the phase-entry contract" signature the WARN exists to catch, and it was catching me. Header corrected.
