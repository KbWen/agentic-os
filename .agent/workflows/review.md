---
description: Workflow for review
---
# /review

Conduct strict review of current changes.

## Phase Verification

**Phase Verification** (per bootstrap §2b): Read `Current Phase` from Work Log header. Verify transition to `review` is legal. If illegal, STOP. Otherwise update `Current Phase: review`. If a new commit was created since the last `Checkpoint SHA`, SHOULD refresh it.

## Work Log Compaction Check

Before review, check the active Work Log size. If it exceeds compaction thresholds (see `.agent/config.yaml` §worklog), compact per `/handoff` §6 BEFORE proceeding. This prevents bloated logs from inflating token costs during the review phase.

## Skill-Aware Review (Pre-Check)

Apply the Phase-Entry Skill-Loading Protocol (AGENTS.md §Phase-Entry Skill Loading) for all skills listing `/review` in their phases. Read `Recommended Skills` from the active Work Log before selecting which skill guidance to apply in this phase. Then apply each skill's **"During /review:"** checklist items as additional review criteria. Explicitly state: "Reviewing with [skill-name] checklist applied."

This ensures domain-specific review criteria (API conventions, frontend patterns, DB safety, auth compliance) are enforced — not just generic code review.

**IF `doc-lookup` is active during review:**
- For each framework API call in the diff, verify it matches official documentation:
  - Method signatures, parameter order, return types are correct
  - No deprecated APIs used without explicit migration plan
  - Config values are valid per official docs (not invented)
- If `/implement` left `// TODO: verify against official docs` caveat comments, resolve them NOW via WebFetch
- Check that `package.json` / `pubspec.yaml` / `requirements.txt` pinned version matches the doc version that was consulted
- Flag any framework API usage that lacks a `Ref:` trace in the Work Log

## Minimum Checks

- Logic correctness
- Compatibility risks
- Violation of `.agent/rules/engineering_guardrails.md`
- Scope enforcement: MUST skip any file with `status: frozen` or `Finalized` metadata. Review scope is limited to current task's changed files only.
- External dependency discipline: if dependency manifests changed or repo-external APIs/platform features were used, verify `## External References` cites official sources and that implementation matches them.
- Known risk traceability: if `## Known Risk` is populated, confirm each listed mitigation is actually present in the code or evidence.
- PR-visible evidence contract: active Work Logs remain local-only. In framework/upstream repos, refresh a tracked review mirror at `.agentcortex/context/review/<worklog-key>.md` before opening or updating a PR so `agentcortex-verify.yml` can inspect the current evidence. Downstream repos may leave this path absent unless they opt into PR-visible evidence checks.
- Review mirror scope: `.agentcortex/context/review/<worklog-key>.md` may reflect an in-progress PR. CI validates legal phase progression up to the current checkpoint; `/ship` still enforces the full completion gate before SSoT updates.

## Error Observability Compliance (§5.2a)

For each `catch` / error-handling block in the changed files, verify:

1. **Logging call exists** (syntax check — per §5.2)
2. **Logger is production-observable** (semantic check — per §5.2a): the log call must NOT be a debug-only API (`debugPrint`, `print`, `console.log` in debug-only mode, or any tree-shaken / release-stripped API). It must use the project's production logger.
3. **Error context is actionable**: the log message includes enough context to diagnose the issue (not just `"error occurred"` — include the error type, relevant identifiers, and operation that failed).

If the project has no identifiable production logging strategy (no logger framework, no crash reporter integration), flag:
> *"⚠️ No production-observable error sink identified in this project. Errors in catch blocks may be invisible in release builds. Resolve before `/ship`."*

**Scope**: Application/service code only. Test files and CLI dev tools are exempt.

## Design Compliance Check (UI Tasks — Mandatory)

> Ref: `engineering_guardrails.md` §4.4 — Design-First Rule

For any task that modified user-visible UI, the reviewer MUST:

1. **Design Link Verification**: Confirm `## Design Reference` exists in the Work Log with a valid `Link:`. Missing link on a UI task → **Review verdict = Not Ready**. Route back to `/plan`.
2. **1:1 Fidelity Audit** — compare implementation against DSoT (Stitch, Figma, Pencil, etc.):
   - Layout structure (component hierarchy, positioning, flow)
   - Spacing & sizing (margins, padding, dimensions)
   - Typography (font family, size, weight, line-height)
   - Colors & theming (exact values, dark/light variants if specified)
   - Interactive states (hover, focus, disabled, loading, error, empty)
   - Responsive behavior (if specified in the design)
3. **Deviation Severity**:
   - **HIGH**: Structural deviation (wrong component, missing element, incorrect layout flow) → Review verdict = **Not Ready**. MUST fix.
   - **MEDIUM**: Metric deviation (spacing off by >2px, wrong font weight, color mismatch) → Must fix or obtain explicit design-owner approval recorded in Work Log.
   - **LOW**: Minor polish (sub-pixel rounding, platform-specific rendering) → Informational.

### Design Compliance Verdict

Append to the review output:

```
## Design Compliance
| Element | DSoT Reference | Implementation | Verdict |
|---------|---------------|----------------|---------|
| [component/screen] | [DSoT link § section] | [file:line] | ✅ Match / ⚠️ Deviation / ✗ Missing |
```

Any `✗ Missing` or unresolved HIGH `⚠️ Deviation` → cannot proceed to `/test`.

**Exempt**: Backend-only tasks, CLI tools, infrastructure, non-visual config changes, `tiny-fix`.

## Security Scan (MANDATORY — Auto-Enforced)

Execute `.agent/rules/security_guardrails.md` §1–§4 against all changed files:

1. **Always-On Checks** (every review): Broken Access Control (A01), Cryptographic Failures (A02), Injection (A03), Secret Detection (§3).
2. **Context Checks** (when relevant code touched): A04–A10 per trigger rules in security_guardrails.md §2.
3. **Dependency Check** (§4): If any dependency manifest changed, flag new dependencies.
4. **External References Check**: if dependency manifests changed or new external integrations appear, an empty / `none` `## External References` section is a review warning and MUST be surfaced explicitly.

### Security Verdict

- Any **CRITICAL/HIGH** finding → Review verdict = **Not Ready**. MUST fix before proceeding.
- **MEDIUM** findings → Flag in review output. Proceed allowed with user acknowledgment.
- **LOW** findings → Informational only.
- Output findings using format defined in security_guardrails.md §5.

## Red Team Scan (Auto-Triggered — Classification-Based)

After completing the Security Scan above, AI MUST check the task classification from the active Work Log and apply the Red Team skill if applicable.

**Auto-Trigger Logic**:
1. Read `Classification:` from `.agentcortex/context/work/<worklog-key>.md`.
2. Apply the auto-trigger matrix defined in `.agents/skills/red-team-adversarial/SKILL.md` §When to Use.
3. Execute the corresponding mode from that skill file.

### Red Team Verdict (separate from Security Verdict)

- **CRITICAL** Red Team finding → Review verdict = **Not Ready**. MUST fix before proceeding.
- **HIGH** Red Team finding → Does NOT block. MUST record risk decision in Work Log `## Red Team Findings` section. Recommend using `/decide` to document accept/defer rationale.
- **MEDIUM / LOW** Red Team finding → Advisory only.

Output findings using the Red Team Report format defined in the skill file.

## Burden of Proof Protocol (ALL non-tiny-fix classifications)

> **Core principle**: Every claim of correctness starts as **UNPROVEN**. The reviewer must cite concrete evidence to flip it to PASS. This inverts the default from "find problems to fail" to "find evidence to pass", eliminating confirmation bias.

### For feature / architecture-change (Spec-Based)

Cross-reference implementation against EVERY AC in the referenced `docs/specs/<feature>.md`:

1. List all ACs. Each starts as `✗ UNPROVEN`.
2. For each AC, the reviewer MUST provide **specific evidence**:
   - Code evidence: `file:line` reference proving the AC is implemented
   - Test evidence: test name or test output proving the AC is verified
   - Output evidence: terminal output or screenshot proving the AC works
3. Evidence provided → flip to `✅ PROVEN (evidence: <citation>)`.
4. Evidence insufficient or missing → remains `✗ UNPROVEN`.
5. Partial evidence → `⚠️ PARTIAL (evidence: <citation>, gap: <what's missing>)`.

**Gate rule**: Any AC remaining `✗ UNPROVEN` → STOP. Cannot proceed to `/test` until resolved or explicitly deferred via `[NEEDS_HUMAN]` with user acknowledgment.

### For quick-win / hotfix (Behavioral)

These classifications have no formal spec, but the burden of proof still applies:

1. Extract the task's expected behavioral change from Work Log `## Task Description`.
2. The reviewer MUST cite evidence that the change works:
   - Before/after behavior comparison with `file:line` or output reference
   - Root cause addressed (for hotfix): cite the specific fix location
3. No evidence → `✗ UNPROVEN` → cannot proceed.

### Evidence Output Format

```
## Burden of Proof
| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| AC-1 | [description] | ✅ PROVEN | `src/foo.dart:42` implements X; `test/foo_test.dart:15` verifies |
| AC-2 | [description] | ✗ UNPROVEN | No test covers edge case Y |
| AC-3 | [description] | ⚠️ PARTIAL | `src/bar.dart:10` implements, but no test — [NEEDS_HUMAN] |
```

After completing the table, convert each row into a **Gate Receipt** for the Work Log `## Gate Evidence` section using the validator-compatible format:
```
- Gate: review | Verdict: PASS | Classification: <classification> | Timestamp: <ISO>
```
The Burden of Proof table stays in the review output for human readability; the receipt line goes to Gate Evidence for CI validation.

## Self-Check Protocol (Auto — Before Presenting Results)

AI MUST verify its own review before outputting:

1. **Scope check**: List every file changed. Any file NOT in the original plan? Flag it.
2. **Regression check**: For each changed function/export, state: "Callers: [list]. Breaking change: yes/no."
3. **Proof completeness check**: Verify the Burden of Proof table has zero `✗ UNPROVEN` rows (or all UNPROVEN rows are explicitly tagged `[NEEDS_HUMAN]`). If any UNPROVEN row lacks a tag, the review is incomplete — do NOT present as ready.

## Output Format

Apply the shared `Phase Output Compression` contract from `AGENTS.md §Phase Output Compression → /review`.

**Chat response leads with the Burden of Proof table. Everything else is terse.**

Required chat content (in this order):
1. **Burden of Proof table** (mandatory — see §Burden of Proof Protocol). Table only; no prose preamble.
2. **Issues** — 1 line per issue: `<severity>: <file:line> — <1-line>`. If none: `Issues: none`.
3. **Security** — 1 line. If none: `Security: clean`. Findings detail goes to Work Log.
4. **Red Team** — 1 line (only if triggered). Findings detail goes to Work Log.
5. **External Refs** — `verified | missing | stale` with count.
6. **Verdict** — `Ready to commit: yes | no`. If `no`, 1-line reason.

Compression rules:
- Do not reprint the full task description, plan, or AC prose — they are in the Work Log.
- Do NOT include "Fix suggestions" in chat unless the user asks. Write them to Work Log `## Review Feedback` instead.
- Delta-only: state what changed since `/implement`, not what the whole branch does.
- If zero issues: one line (`Issues: none`) is sufficient. No "residual risk commentary" paragraph.

## Domain Decisions Tag Validation (AC-10, feature / architecture-change)

If the referenced spec contains a `## Domain Decisions` section, validate each entry:

1. Every entry MUST begin with one of: `[DECISION]`, `[TRADEOFF]`, or `[CONSTRAINT]`.
2. Any entry missing a valid tag = **review warning** (not hard block). Output: `"⚠️ Domain Decisions entry missing valid tag: '<entry prefix>'. Must be [DECISION], [TRADEOFF], or [CONSTRAINT]."`
3. Count total entries. If > 10: **review warning**: `"⚠️ Domain Decisions has N entries (max 10). Prune before /ship to keep knowledge consolidation tractable."`
4. If `## Domain Decisions` section is absent from a `feature` or `architecture-change` spec: output advisory: `"Domain Decisions section not found in spec. Knowledge consolidation will be skipped at /ship. Consider adding key decisions before proceeding."`

`tiny-fix`, `quick-win`, and `hotfix` are EXEMPT from this check.

## Phase Summary Update

After review is complete, append one line to `## Phase Summary` in the Work Log:
```
- review: [1-line summary — verdict, security findings count, spec compliance status]
```

## Heading-Scoped Read Note

For token budgeting and future automation, `/review` entry reads only:
- `Skill-Aware Review (Pre-Check)`
- `Minimum Checks`
- `Design Compliance Check`
- `Burden of Proof Protocol`
- `Security Scan`
- `Red Team Scan`
- `Self-Check Protocol`

Read `Output Format`, `Domain Decisions Tag Validation`, and `Phase Summary Update` only when preparing the final review output.
