# Work Log: codex-v18-review/main

## Header

- Branch: `main`
- Classification: `architecture-change`
- Classified by: `Codex`
- Frozen: `true`
- Created Date: `2026-06-21`
- Owner: `codex-v18-review`
- Guardrails Mode: `Full`
- Current Phase: `implement`
- Checkpoint SHA: `b9aaf9b55440ac58c81e6db251414d32d84a57ad`
- Recommended Skills: `karpathy-principles, red-team-adversarial`
- Primary Domain Snapshot: `downstream-adaptability`
- SSoT Sequence: `86`

## Session Info

- Agent: `Codex`
- Session: `2026-06-21T14:17:25+08:00`
- Platform: `Codex App`
- Guardrails loaded: `§1, §2, §4, §6, §7, §8.1, §10 (core) + §13 (governance diff)`
- Review range: `v1.7.0..v1.8.0`
- Compaction Session: `Codex, 2026-06-24`; full details remain in prior local history and referenced evidence.

## Drift Log

- Aggregate release-wave review created separately from stale historical `main.md`.
- Review reverse transition: `REVIEWED→IMPLEMENTING` due unresolved AC-4; AC-7 wording remained documentation debt.
- Downstream simulation added after user requested a real adopter development flow, not deployment-only verification.
- 2026-06-24: compacted active Work Log for validator hygiene; retained blocking findings and evidence summary.

## Task Description

Independently review the v1.8.0 KB-seam hardening release wave (`v1.7.0..v1.8.0`) for correctness, security, governance compliance, regression risk, and test sufficiency. Scope was review only.

## Phase Sequence

- bootstrap: completed — aggregate scope classified as architecture-change.
- implement: externally completed in merged commits `f4055d0..b9aaf9b`.
- review: NOT READY — routed back to implement.

## External References

- `docs/adr/ADR-009-knowledge-source-consumption-seam.md`
- `docs/specs/knowledge-source-seam.md`
- `docs/specs/kb-seam-hardening.md`
- Python codecs docs: `utf-8-sig` skips an optional leading UTF-8 BOM.
- Microsoft Test-Path docs: `-PathType Leaf` distinguishes files.

## Known Risk

- KB consult behavior is agent-prose-driven; behavioral correctness is honor-system.
- Configured KB paths intentionally sit outside containment controls.
- Rollback plan: revert offending merge commits in `v1.7.0..v1.8.0`; correct release metadata in a patch release.

## Conflict Resolution

- `karpathy-principles` governed scope/simplicity.
- `red-team-adversarial` added trust-boundary and systemic resilience checks.

## Skill Notes

### karpathy-principles / review

- Checklist: scope limited to `v1.7.0..v1.8.0`; no drive-by refactor found.
- Constraint: review only; do not modify shipped code.

### red-team-adversarial / review

- Checklist: inspected path/env handling, YAML parsing, prompt-injection boundaries, dependencies, and fault behavior.
- Constraint: CRITICAL requires a concrete exploitable path.

## Burden of Proof

| Criterion | Verdict | Evidence |
|---|---|---|
| AC-1 `${ACX_KB_PATH}` resolution | PROVEN | Bootstrap workflow + committed example validator result. |
| AC-2 trust model documented | PROVEN | Guide and ADR carry the same model. |
| AC-3 committed example | PROVEN | Example config passes schema validation. |
| AC-4 non-vacuous injection eval | UNPROVEN | Correct explicit refusal can fail; malicious paraphrase can pass. |
| AC-5 `entrypoint` vocabulary pinned | PROVEN | Validator allowlist and repo search. |
| AC-6 dogfood evidence | PROVEN | `arch-kb-seam-hardening.md` records routed page/checklist/token evidence. |
| AC-7 no regression / zero-cost absent | PARTIAL | No KB reads proven; literal zero-token/byte-identical claim not proven. |

## Review Feedback

- BLOCKING HIGH: normal frozen-spec development enters an impossible SSoT cycle; frozen spec fails Spec Index validation before `/ship`, while Write Isolation forbids pre-ship SSoT updates.
- BLOCKING MEDIUM: injection eval false-fails a correct refusal and can pass a malicious paraphrase.
- MEDIUM: "zero tokens / byte-identical" overstates measured no-KB behavior; better claim is zero KB file reads/content tokens when absent.
- MEDIUM: `kb_path_env` is dead configuration while bootstrap hardcodes `ACX_KB_PATH`.
- MEDIUM: malformed readable KB cannot be represented by health vocabulary `OK|UNREADABLE`.
- MEDIUM: KB review criteria lack task-applicability filtering.
- MEDIUM: v1.8.0 changelog omits included PR #273.
- LOW: manual wiring probes can report misleading results.
- FOLLOW-UP: Windows test feedback is slow but not a v1.8 regression.

## Security Findings

- OWASP/secret scan: no CRITICAL/HIGH finding; no new dependency.
- BOM handling is fail-closed: BOM+valid passes and BOM+`role: authority` remains rejected.

## Red Team Findings

- MEDIUM: context exhaustion risk from oversized extracted checklist sections.
- MEDIUM: wrong-source identity risk because KB health records only `<id>→OK|UNREADABLE`.

## Phase Summary

- bootstrap: architecture-change aggregate review initialized for the v1.8.0 release wave. ⚡ ACX
- review: NOT READY — downstream implementation exposed frozen-spec lifecycle cycle; AC-4 injection eval has false-negative and false-positive behavior. ⚡ ACX
- compaction: reduced active Work Log below validator size thresholds while preserving blocking findings and evidence. ⚡ ACX

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: architecture-change | Timestamp: 2026-06-21T14:17:25+08:00
- Gate: review | Verdict: NOT READY | Classification: architecture-change | Transition: REVIEWED→IMPLEMENTING | Timestamp: 2026-06-21T14:42:00+08:00

## Evidence

- Focused tests: `120 passed in 24.30s`.
- Clean-clone fast groups: 528 tests passed; slow deploy-tiering 24 passed in 12:51.
- GitHub Actions run `27894721538`: Windows pytest `574 passed in 506.26s`; all jobs succeeded.
- Downstream deployment validators: PowerShell and Git Bash no-Python both `pass=76 warn=2 fail=0 skip=12`.
- Downstream adopter feature: 8 tests passed; frozen/draft A/B reproduced sole Spec Index failure.
- Real KB routing: 69 pages / 368,624 tokens; backend + resilience routes loaded 16 + 14 checklist items.
- Capabilities example validation: `OK`.
- Credential scan on 23 changed files: no findings.
- `git diff --check v1.7.0..v1.8.0`: pass.
- Prior local `validate.ps1`: `pass=102 warn=12 fail=2 skip=2`; both failures were local Work Log hygiene/progression.

## Design Reference

none

## Observability

none

## Resume

- State: review NOT READY for v1.8.0 release wave; implementation follow-up required for frozen-spec lifecycle and eval semantics.
- Next: handle each blocking finding in its own scoped branch/work log.
- Protect: keep this as review evidence; do not treat it as authorization to modify release-wave code.

⚡ ACX
