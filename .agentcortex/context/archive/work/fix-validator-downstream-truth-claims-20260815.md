# Compaction Overflow: fix/validator-downstream-truth-claims (2026-08-15)

## Phase Summary

Compaction overflow of the **still-active** Work Log at
`.agentcortex/context/work/fix-validator-downstream-truth-claims.md` (`/handoff §6`, triggered at
576 lines / 34KB against thresholds 300 lines / 12KB). Not a final archival — the active log
remains authoritative and carries all protected sections. This file holds the long-form
Decisions, Known-Risk rationale, Drift Log, Security Findings detail, and implement-phase evidence
narrative moved out of it. Classification `hotfix`; base `f5a161c`; implement commit `55e3314`.

⚡ ACX

---

## Decisions (full text)

### D-1: Reject #173's `SOURCE_ONLY_TOOLS` allowlist; keep only its regression detection

- **Decision**: Do NOT build the `SOURCE_ONLY_TOOLS` allowlist artifact that backlog #173
  prescribes. Instead assert, inside the CI `deploy-smoke-test` job that already deploys to a fresh
  target and runs the deployed `validate.sh`, that the output contains no bare `tool not present`.
- **Reason**: the identity mechanism the allowlist would re-encode **already exists** —
  `IS_SOURCE_REPO` (`validate.sh:29`, used at `:322`, `:561`, `:1112`) and `$isSourceRepo`
  (`validate.ps1:349`, used at `:380`, `:664`, `:1074`), with an established honest house string at
  `validate.sh:323`. An allowlist would be a **fourth** place tools are listed, and its stated
  payload (one line of reason per tool) is a comment — comments that already exist at
  `validate.sh:388-390` and `:626-629`. `.github/workflows/validate.yml:189/209/214` already
  performs the deploy-and-run; the assertion is ~3 lines in an existing step.
- **Alternatives**: (a) build the allowlist as specified — rejected as new machinery against the
  owner's standing "do not make governance heavier" constraint; (b) gate the source-only calls on
  `IS_SOURCE_REPO` so nothing prints downstream — rejected because it makes the downstream label set
  structurally differ from the source label set along a seam that has **no** parity test, and a
  mis-gated check would then vanish **silently**, which is worse than a confusing line.
- **Impact**: #173's row must be updated at ship to record that its prescribed fix was replaced,
  with this reasoning, so a future reader does not re-propose the allowlist.

### D-2: Deploy `check_audit_chain.py` rather than narrow ADR-003

- **Decision**: add the checker to the deploy whitelist.
- **Reason**: dependency-clean (stdlib + `append_chain_entry`, already deployed). ADR-003 nowhere
  scopes the chain to the source repo and `:140` names "fresh downstream" as handled, so choosing
  source-only would **narrow a stated guarantee** and require an ADR amendment; deploying requires
  none. Verified counter-fact to the original framing: downstream tamper-evidence is **not** zero
  today — `validate.sh:452-495` is a pure-git, no-Python append-only witness that catches truncation
  and edits to pre-existing entries. The residual gap is narrower than first stated: a forged or
  mis-linked entry appended on the current branch before merge.
- **Alternatives**: keep source-only and downgrade `validate.sh:398` off FAIL — a FAIL-wired check
  that can never fire downstream is theatre by this repo's own doctrine, and that path costs an
  ADR-003 amendment.
- **Impact**: R2 (green→red on upgrade for an adopter with a genuinely broken chain).

### D-3: Fix the lifecycle WARN by branch reorder, not by deleting the block or deploying the baseline

- **Decision**: reorder the ladder so updater-absence is tested before baseline-absence, in both
  validators.
- **Reason**: the honest string **already exists** (`validate.sh:2884`, `validate.ps1:591`) and is
  simply unreachable downstream because baseline-absence is tested first (`validate.sh:2879`).
  Deploying the baseline is affirmatively wrong — it carries *this* repo's token counts, so a fork
  would inherit upstream numbers and get guaranteed false drift; and deploying the updater alone
  would crash, because `update_lifecycle_baseline.py:49` imports `analyze_token_lifecycle`, which is
  not deployed.
- **Alternatives**: delete the whole block from both validators (~45 lines each) — rejected: it
  would also require a `validator_native_baseline.json` bump plus removal of a named justification
  entry, a larger governance transaction than the defect warrants, and the advisory is still useful
  upstream where its teeth live (`tests/ci/test_lifecycle_baseline_drift.py`).
- **Impact**: all four emissions are preserved, so the ratchet is unaffected.

### D-4: The highest-value fix was not in the adopter's report

- **Decision**: treat the summary-line assurance label as the primary fix of this unit.
- **Reason**: `validate.sh:2962-2966` keys the reduced-assurance label **only** on `PYTHON_BIN`, so
  an adopter who has Python and is missing 7 referenced tools is told, without qualification,
  `Agentic OS integrity check passed`. The adopter's stated worry was that a SKIP makes them think
  the deploy is broken; the larger defect is the inverse — the validator tells them everything is
  fine. It is an `echo`, not a `record_result`, so it carries **zero** ratchet cost.
- **Alternatives**: leave it to #173 — rejected; it is the same failure class already fixed once
  (backlog #149) and is cheaper than anything the report asked for.
- **Impact**: changes the top-line string adopters see on partial installs.

### D-5: Carry the "why absent" at the call site, not in a registry

- **Decision**: `run_python_check` / `Invoke-PythonCheck` gain an optional absent-reason. Bash: a
  `run_python_check_source_only "<reason>" …` wrapper that sets and clears `ACX_ABSENT_REASON`
  around the existing call, so the reset is structural rather than remembered. PowerShell: an
  optional `-AbsentReason` parameter. Both interpolate into the **existing single** SKIP emission.
  Calls that pass no reason keep today's `-- tool not present` **and** increment an absent-tool
  counter that the summary line then reads.
- **Reason**: this is the discriminator D-1 needs without D-1's rejected artifact — the reason lives
  at the only site anyone reads it, and "unexpected" is defined by the *absence* of a stated reason
  rather than by membership in a list that can go stale. It also makes the summary counter correct
  by construction: deliberate absences do not inflate it, so downstream keeps a clean top line while
  a genuinely accidental omission qualifies it.
- **Alternatives**: (a) a 4th positional on `run_python_check` — rejected: `shift 3` plus `"$@"`
  passthrough means renumbering all 15 bash call sites, which is the single riskiest edit identified
  in this batch (a missed site silently turns `$script` into `"FAIL"`, the check becomes a SKIP, and
  exit stays 0 with CI green); (b) a bare `VAR=value run_python_check …` environment prefix —
  rejected: bash does not persist assignment-prefixes across *function* calls the way POSIX sh does,
  so the behaviour differs by shell mode; (c) count every tool-absent SKIP regardless of intent —
  rejected: it puts a permanent, never-clearable qualifier on every adopter's top line, which is the
  WARN-numbness pattern (#143) rebuilt.
- **Impact**: `run_python_check`'s existing 3-positional contract is untouched; only the 2
  source-only call sites change form. Zero line-leading `record_result` added → ratchet neutral.

### D-6: Accept and state the regression guard's coverage ceiling

- **Decision**: the CI guard is two assertions inside the **existing** `deploy-smoke-test` step —
  the deployed validator's output contains no bare `tool not present`, and the deployed tools
  directory contains `check_audit_chain.py`. No new job, no new file, no allowlist.
- **Reason**: `.github/workflows/validate.yml:189/209/214` already deploys to a fresh target and
  runs the deployed `validate.sh`, asserting only the exit code. The first assertion catches the
  next accidental omission at the behaviour level. The second exists because the first **cannot**
  see `check_audit_chain`: that check is guarded by `[[ -f "$ARCHIVE_INDEX_JSONL" ]]`
  (`validate.sh:397`) and a fresh deploy ships no `INDEX.jsonl`, so the check never runs and never
  prints. One named file for one named ADR-003 guarantee.
- **Known ceiling, stated rather than papered over**: any *future* tool that is both absent and
  guarded behind a presence condition is still invisible to this guard. Closing that would require
  the expected-tool list this unit deliberately rejected (D-1). Recorded here and at ship so the
  next reader does not mistake the guard for total coverage.

---

## Known Risk (full rationale)

- **R1 — ADR-006 native-check ratchet has ZERO headroom in both directions.**
  `tests/ci/validator_native_baseline.json` pins `validate_sh: 202` / `validate_ps1: 203`, and
  `test_native_check_counts_match_baseline_exactly` fails on growth **and** on shrink. Mitigation:
  the SKIP-string fix MUST be message-shaping inside the **existing single** `record_result SKIP`
  (`validate.sh:176`) / `Add-Result` (`validate.ps1:160`). An if/else that emits two SKIPs adds a
  counted line and turns CI red; the escape hatch would require a justification claiming the line
  must run without Python, which is false for a message string. **Outcome: this risk materialised
  and was caught — see Drift Log.**

- **R2 — deploying `check_audit_chain.py` is a real behaviour flip, not a no-op.** It is wired at
  FAIL (`validate.sh:398`) and guarded only by `[[ -f "$ARCHIVE_INDEX_JSONL" ]]`, so an adopter who
  has appended chain entries under an older version and has a genuinely broken chain flips green→red
  on upgrade. That is the intended outcome, but it belongs in the release banner, not silently in a
  whitelist. Mitigation: state it explicitly at ship.

- **R3 — deploy is copy, not sync: the deploy half is not symmetrically revertible.** Once the tool
  lands downstream, reverting `deploy.sh` leaves the file on adopter disks. Mitigation: the revert
  lever is to stop invoking it, not to expect removal. Benign — a stale copy makes the chain check
  *run*, never fail-open.

- **R4 — `-m "not slow"` is NOT CI-equivalent.** `tests/ci/test_deploy_tiering.py` carries a
  module-level `pytest.mark.slow`; a filtered run silently deselects the entire module, including
  the very test this unit extends. Mitigation applied: ran `pytest tests/ci/ tests/guard/
  .agentcortex/tests/` with no `-m` filter, counts taken from `--collect-only` (885).

- **R5 — out-of-scope siblings stay broken and that is deliberate.** Units B (D3 backlog row-set
  divergence, D4 archive-size ruler, D7 phantom PASS on a fresh `docs/specs/`), C (D5 PowerShell
  console encoding) and D (D6 dead `missing_python_level` parameter) are verified defects left
  unfixed here. Mitigation: each becomes a backlog row at ship; none is a regression introduced by
  this unit.

- **R6 — `deploy.sh` is governed by a frozen spec, and its AC-S5 is load-bearing for this unit.**
  `docs/specs/downstream-adaptability-optimization.md` (`status: frozen`) AC-S5 mandates adding a
  tool to **both** `deploy.sh` whitelists. This unit complies (both sites edited); the previously
  planned dedup would have contradicted the AC's wording and is dropped. Mitigation: no unfreeze
  needed; dedup routed to backlog with the AC-S5 citation so it is picked up as a spec amendment.
  Side observation, not acted on: that spec's frontmatter still reads `status: frozen` while the
  SSoT Spec Index records it `[Shipped 2026-06-14, PR #238]` — a lifecycle inconsistency (§4.2 says
  `/ship` sets `shipped`). Out of scope here; noted for the backlog.

- **R7 — the KB seam was consulted and produced nothing, which is the honest outcome.**
  `kb-consult` was recommended at bootstrap because `knowledge_sources` is present. Queried
  `task_routing` (34 routes) rather than the whole manifest, per the skill's contract: no route maps
  to validator / deploy / shell-tooling work. **0 pages read.** Also note `kb-consult` has no entry
  in `.agentcortex/metadata/trigger-compact-index.json`, so the metadata-first step had no
  `load_policy` / `cost_risk` to consult and fell back to the bootstrap rule table as permitted.

- **Root Cause** (`engineering_guardrails.md §10.4`): the validators compute *whether a check ran*
  but never fold that into the *verdict they report*. The reduced-assurance label was keyed to a
  single cause (Python absence, `validate.sh:2962`) rather than to the set of checks that did not
  run — so absent tools are invisible to the summary. The same shape was found and fixed once before
  for a different cause (backlog #149: a work-log family emitted nothing and the summary still
  printed "integrity check passed"; measured `pass=99` vs `pass=117`). This is a **recurrence of a
  known failure class**, not a new one.

---

## Drift Log (full text)

- SSoT write (bootstrap-permitted, `AGENTS.md` §Non-ship SSoT write exceptions): refreshed
  `Last Verified` in `current_state.md` — no other field touched.
- Backlog status advance (`bootstrap.md` §1.5): row #173 `Pending` → `In Progress`. Verified
  column-count preserved (11 pipes before and after) per the `[edit-row-count]` hazard.
- **Conflicting-directive observation (not resolved here, surfaced for the owner)**: `AGENTS.md`
  §vNext State Model §Write Isolation lists the backlog exception as "`_product-backlog.md` updates
  during spec-intake/ship", while `bootstrap.md` §1.5 *mandates* a `Pending → In Progress` advance
  at bootstrap and calls it "the only valid" such transition. Precedence says AGENTS.md wins, which
  would forbid the step the workflow requires. Read the AGENTS.md clause as enumerating the common
  cases rather than as an exhaustive allowlist, and performed the workflow-mandated advance. Same
  axis as the shipped `docs/specs/conflicting-directive-scan.md`; filed as a backlog candidate at
  ship rather than patched inside a hotfix.
- Self-correction, probe error: the knowledge-source manifest was first reported UNREADABLE. That
  was my probe's fault, not the file's — Python defaulted to `cp950` on this Windows host. Re-read
  with explicit `encoding='utf-8'`: `schema_version: 6`, `kb_version: 328b30ecb33b`, `task_routing`
  present. Recorded as OK.
- **Self-caught near-miss (implement, R1)**: my first `validate.ps1` edit wrote the absent-tool
  branch as an `if/else` with **two** `Add-Result` emissions — exactly the ADR-006 ratchet violation
  R1 was written to prevent (203 → 204 = CI red). Caught by re-running the count immediately after
  the edit rather than at the end of the phase, and rewritten as single-emission message shaping.
  The risk register earned its keep; the lesson is that the guard only works if the count is checked
  **per edit**, not per phase.
- **Test-harness defect, not a code defect (implement)**: an early accidental-omission simulation
  restored a deleted tool with `cp` from the LF pristine source into the CRLF deployed tree, which
  turned `[FAIL] text integrity check` red and, because the summary's FAIL branch short-circuits,
  never exercised the new reduced-assurance line at all. Diagnosed rather than waved off (`cmp`
  proved content-identical → EOL, not content), the sim was rebuilt from a clean deploy, and the
  test was re-run properly. This is `[cross-platform-eol]` biting the harness; recorded because a
  "known local artifact" label here would have hidden that the test proved nothing.
- **Compaction (implement)**: this log hit 576 lines / 34KB against the 300-line / 12KB thresholds
  and `validate.sh` correctly FAILed on it. The cause was my own §5.2b violation — evidence written
  as multi-paragraph narrative instead of ≤3 lines per claim. Compacted per `/handoff §6` into this
  file and the active `## Evidence` rewritten to the compliant form. Nothing discarded.
- Skip Attempt: NO · Gate Fail Reason: N/A · Token Leak: NO

---

## Security Findings (full text)

`security_guardrails.md §6`. Implement-phase quick-scan = §1 Always-On (A01–A03) + §3 Secret
Detection on every changed file. Full §1 A01–A10 scan runs at `/review`.

- **A01 Broken Access Control** — n/a. No auth surface, no privilege boundary, no request handling
  in any changed file.
- **A02 Cryptographic Failures** — none. No secrets, keys, hashes or connection strings added. The
  newly deployed `check_audit_chain.py` verifies an existing SHA-256 back-link chain; this change
  alters *whether it ships*, not the algorithm.
- **A03 Injection** — reviewed, no finding. `ACX_ABSENT_REASON` / `-AbsentReason` interpolate into a
  message string, but every value is a **literal written at the call site inside the validator
  itself** — there is no path from user input, file content, or tool output into either. In bash the
  variable is only ever expanded inside a double-quoted argument to `record_result`.
- **A03 (CI, LOW / informational)** — the new `Downstream signal honesty` step echoes matched
  validator lines into the Actions log. Echoing untrusted text into a runner log is a real class
  (workflow-command injection), but the matched content here is this repo's own hardcoded check
  labels plus a temp path in a freshly deployed target containing no attacker-controlled filenames.
  Recorded rather than dismissed: the assertion would need re-examination if it were ever pointed at
  a tree containing user-authored paths.
- **§3 Secret Detection** — `scan_credentials.py <5 changed files>` → **exit 0**, no findings.

**No CRITICAL/HIGH findings. `/review` is not blocked.**

---

## Implement Evidence (long-form narrative)

### Controlled A/B against a real deployed tree

The authoritative comparison is **not** the figure recorded in the SSoT from the 2026-08-13
simulation (`pass=87 warn=1 fail=0 skip=6`); that was a different tree on a different date, and
comparing against it produced a phantom "warn went up" scare. Instead a pristine source tree was
materialised from the Diff Base (`git archive f5a161c | tar -x`), deployed to its own target, and
validated under **identical** conditions, so the diff isolates this change and nothing else.

- Baseline (`f5a161c`, fresh deploy): `pass=85 warn=3 fail=0 skip=6`
- After (same conditions): `pass=85 warn=2 fail=0 skip=7`
- Full line-level diff of every result line: **exactly 3 lines, all intended, zero side-effects.**
  1. `[SKIP] skill provenance … -- tool not present` → `… -- source-only tool, not deployed by
     design (safe to ignore downstream)`
  2. `[SKIP] worklog external references … -- tool not present` → same honest string
  3. `[WARN] token lifecycle baseline absent … seed with update_lifecycle_baseline.py --init` →
     `[SKIP] token lifecycle drift -- updater not deployed by design (source-repo advisory; safe to
     ignore downstream)`

The permanent, unexecutable WARN is gone; **zero** bare `tool not present` remain downstream.

### The summary line, demonstrated both ways

Healthy downstream printed `Summary: pass=85 warn=2 fail=0 skip=7` followed by a clean
`Agentic OS integrity check passed` — clean because all three deliberate absences name themselves
and therefore do not count. With one deployed tool removed to simulate an accidental whitelist
omission, the same tree printed `Agentic OS integrity check passed (reduced assurance: 1 referenced
tool(s) absent -- those checks did not run)`. Before this change that tree printed an **unqualified**
pass.

### The chain checker now actually verifies downstream (D-2)

Planted the repo's real `INDEX.jsonl` into both targets and ran each one's own deployed validator:
baseline gave `[SKIP] audit chain integrity (INDEX.jsonl) -- tool not present`; the fixed tree gave
`[PASS] audit chain integrity (INDEX.jsonl)` with `audit chain intact: …/INDEX.jsonl`. ADR-003's
downstream tamper-evidence went from write-only to verified, proven by execution.

### Scope divergence detail

`git diff --stat` → 8 files; planned Target Files 5. The 3 extras are all bootstrap-phase
side-effects recorded in the Drift Log before implement began: `current_state.md` (`Last Verified`
refresh, sanctioned by `AGENTS.md` §Non-ship SSoT write exceptions), `.guard_receipt.json`
(automatic legacy-mirror write by `guard_context_write.py`; the tracked/gitignored contradiction is
backlog #172, untouched here), and `_product-backlog.md` (#173 status advance, `bootstrap.md` §1.5).
No implement-phase edit landed outside the 5 planned files.

### Rollback plan (§12.5)

`git revert 55e3314` restores every line: the validator changes are message/branch-shaping with no
persisted state, and the golden fixture is regenerated from `deploy.sh`, so reverting one reverts
the other consistently. Asymmetric half: `deploy.sh` copies rather than syncs, so a revert does not
remove `check_audit_chain.py` from trees already upgraded (R3).

---

## Review round 1 — NOT READY (2026-08-16), full findings

Two fresh reviewers were briefed per `/review` §Adversarial Reviewer Freshness Invariant: diff +
binding standards only, **no implementation rationale**, no carryover from the implement context.
They ran independently and converged on the same blocking defect. Every finding below was
re-verified by the primary against the code before being acted on (`[audit-verification]`).

- **B1 CRITICAL — `.github/workflows/validate.yml:214`.** `bash .agentcortex/bin/validate.sh | tee
  …` discards the validator's exit status. GitHub runs `run:` blocks as `bash -e {0}` with no
  pipefail, so the pipeline reports `tee`'s status. Primary verification:
  `bash -e -c 'bash -c "exit 7" | tee /dev/null'` → **0**; with `set -o pipefail` → **7**. This
  step is the only place CI asserts the deployed validator's exit code, so a *failing* downstream
  validate would have landed a green job — introduced by the plumbing added to support the honesty
  assertion, in a change whose entire thesis is "do not report a partial install as a pass". The
  same file already carried the correct pattern at `:40` (`shell: bash` + `set -uo pipefail`);
  this was a deviation from an in-file precedent, not an unknown. **Fixed**: `shell: bash` +
  `set -o pipefail` on the step, with a comment stating why it is load-bearing.
- **B2 HIGH — `.agent/workflows/ship.md:208,210`.** A **deployed** file whose prose this change
  turned false: "that tool is not deployed, so downstream the break is permanent and never
  reported" and "going undetected downstream". Same bug class as PR #410, inverted — #410 removed
  a promise the framework did not keep; this change kept the promise and left the prose denying
  it. **Fixed**, and deliberately with *shorter* replacement text: `ship.md` is a counted
  lifecycle document against a hard 355,000-token ceiling with ~431 tokens of headroom, so a
  correction there must not spend budget.
- **B3 MEDIUM — `validate.sh` / `validate.ps1` lifecycle SKIP.** "updater not deployed **by
  design**" is asserted in the source repo too, where a missing updater is a broken install, not a
  decision. That is defect (b) — a string that cannot distinguish deliberate from broken —
  reintroduced inverted by the change that exists to remove it. **Fixed** with a single factual
  string ("updater not present; not deployed downstream by design (safe to ignore there)") rather
  than an `IS_SOURCE_REPO` branch, because a second emission would breach the ADR-006 ratchet.
- **B4 MEDIUM — workflow comment self-contradiction.** It claimed to guard the #173 failure mode
  and then, ten lines later, admitted it cannot. **Fixed**: the comment now states the real scope
  (checks invoked through `run_python_check` *without* a native presence guard), cites #334 as the
  case it genuinely would have caught, and names the blind spot explicitly.
- **B5 LOW — duplicate assertion deleted.** `test -f …/check_audit_chain.py` duplicated
  `tests/ci/fixtures/deploy_manifest_golden.txt`, which already pins the complete deployed file
  list under a 38-test suite and is strictly stronger. Removed per DELETE-bias; the guarantee is
  unchanged and better enforced.
- **B6 MEDIUM — the stated ceiling was present-day, not future.** `validate_downstream_capabilities.py`
  and `generate_safety_nucleus.py` are whitelisted **and** natively presence-guarded, so deleting
  them yields no bare string, counter 0, and an unqualified pass. The comment now says so.
- **B9 LOW — zero test coverage.** `tests/ci/test_validator_absent_tool_signal.py` added (5 tests):
  both deploy whitelist sites must agree (AC-S5 encoded as a test); a source-only *claim* must name
  a tool `deploy.sh` genuinely withholds (the inverse of the CI grep — that catches a missing
  reason, this catches a lying one); the reason string must be identical across validators; the
  counter must be initialised, incremented **and read** in both; and `tool not present` must have
  exactly one emission site in each validator (ratchet safety + counter-bypass prevention in one
  assertion). Red-first proven: injecting a false source-only claim into `deploy.sh` turns
  `test_source_only_claims_are_true` red; restoring turns it green.

### D-7: the chain flip's lack of a clean remediation is the property, not a bug

- **Decision**: keep `check_audit_chain.py` deployed at FAIL severity. Do not soften it.
- **Reason**: the tenth man proved an adopter with a pre-existing broken chain has no path back to
  green — running `append_chain_entry.py migrate` trades the chain FAIL for an append-only-witness
  FAIL, because migrating rewrites already-committed lines and the witness requires the committed
  baseline to be a line-prefix of the working copy. That is not a defect introduced here: a
  tamper-evident log you can silently repair is not tamper-evident. The honest response is to say
  so, not to weaken the check.
- **Alternatives**: wire it WARN downstream (rejected — it would restore the exact "advertised but
  not enforced" shape this repo keeps deleting); do not deploy (rejected — leaves ADR-003's
  downstream promise false, which is where this work started).
- **Impact**: the release banner must state the flip **and** that `migrate` does not clear it.
  R2's original framing assumed an actionable path existed; it does not, and that correction is
  the durable half of this finding.

### B8 — claim correction, carried into ship prose

The summary-line fix covers a **narrow sub-case**. Measured on a fresh deploy after the fix:
`pass=85 warn=2 fail=0 skip=7`, top line **unqualified**, while 7 checks SKIPped and an 18-check
work-log family did not run. "Checks that never ran were reported as a pass" therefore remains
true in general; what changed is that an *unexplained absent tool* now qualifies it. Ship prose
must not claim more than that.
