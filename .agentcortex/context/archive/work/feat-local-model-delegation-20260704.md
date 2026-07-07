# Work Log: feat/local-model-delegation

## Header

- Branch: `feat/local-model-delegation`
- Classification: `feature`
- Classified by: `Claude Fable 5`
- Frozen: `true`
- Created Date: `2026-07-04`
- Owner: `KbWen`
- Guardrails Mode: `Full`
- Current Phase: `review`
- Diff Base SHA: `264929958eee4784d8fffb68ba11496dca9c32a6`
- Checkpoint SHA: `a75002c`
- Recommended Skills: `verification-before-completion (auto), karpathy-principles (auto), red-team-adversarial (auto), subagent-driven-development (auto), kb-consult (auto)`
- Primary Domain Snapshot: `none`
- SSoT Sequence: `111`

---

## Session Info

- Agent: `Claude Fable 5 (claude-fable-5)`
- Session: `2026-07-04 07:06 UTC`
- Platform: `claude-code`
- Files Read: `13`
- Guardrails loaded: §1, §2, §4, §7, §8.1, §10 (core) + §6 (feature), §8.2 (external-tool delegation — the module being designed wraps it), §13 (change touches `.agent/workflows/*`)
- Override: none (project root + `~/.agentcortex/` both absent)
- Downstream-Capabilities: `downstream-capabilities.yaml` (0 skills, subagent_policy=read-only default, knowledge_sources: kb-main→OK@da624b5c6cdd)

---

## Task Description

User directive (after a 3-turn in-chat design convergence, 2026-07-04): provide an official adopter-facing ENTRY so an installer's LOCAL model (Ollama / LM Studio / vLLM / any OpenAI-compatible endpoint) can join the governed flow as a **delegated junior executor** — the cloud primary (Claude/Codex) keeps every phase, gate, and Work Log; the local model executes inside `/implement` under a patch contract (local model returns a patch; primary reviews then applies with its own tools; local model never touches files).

Deliverables (wiring precedent: PR #311 /govern-audit):
1. NEW optional module `.agent/workflows/ask-local.md` (modeled on `ask-openrouter.md`/`codex-cli.md`; wraps §8.2 unchanged).
2. `routing.md` §2 Optional Module Trigger Map row + §5 registry row (explicit opt-in, MUST NOT auto-trigger — same posture as `/claude-cli`).
3. `codex-cli.md` local-variant note: `codex --oss -m <model>` (Codex CLI native local-Ollama path) + tightened delegation cap for local models.
4. `.claude/commands/ask-local.md` stub; `check_command_sync.py` EXPECTED_COMMANDS; deploy manifest golden update (adopters must RECEIVE the module).
5. `docs/specs/local-model-delegation.md` + `_product-backlog.md` row (added at /spec per Write Isolation).

Engine behavior UNCHANGED: §8.2 External Tool Delegation Protocol is reused as-is; intent is ZERO new MUST/gate rules (spec `signal_tier: none`); wiring is T1-verified by existing command-sync + deploy-manifest tests.

Adopter delta: before — an adopter with Ollama has no sanctioned way to fold it into the flow; after — "用本地模型 / ask local model" (explicit opt-in) triggers the module, output goes through Junior Tool review + Work Log evidence; absent endpoint → silent fallback per §8.2 (zero cost when unused).

Full feature chain: /spec → /plan → /implement → /review → /test → /handoff → /ship.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-07-04 | classified feature; branch + lock created |
| plan | done | 2026-07-04 | spec frozen first (local-model-delegation.md); gate PASS |
| implement | done | 2026-07-04 | commit a75002c; 574 tests green; validate fail=0 |
| review | done | 2026-07-04 | independent fresh-context opus review: PASS, 9/9 AC PROVEN |
| test | pending | — | — |
| handoff | pending | — | — |
| ship | pending | — | — |

---

## Phase Summary

- review: PASS (Ready to commit: yes) — independent fresh-context acx-reviewer (opus, no implementer context): Burden of Proof 9/9 (AC-1..8 ✅ PROVEN with file:line + re-run command evidence; AC-9 ✅ correctly deferred-to-ship, verified NOT written early); security clean (credential grep clean); red-team Full mode clean on all 6 vectors (gate-bypass / injection surface / ADD-Gate / cap-table parity / opt-in posture / scanner trip); Domain Decisions 8/8 tagged ≤10; spec frontmatter sane. Reviewer independently re-ran: manifest snapshot (1 passed), token+lifecycle (107 passed), deployed-mode command sync (27 verified), validate_trigger_metadata (fresh parity). 2 LOW advisories, both closed-with-reason (see Review Feedback). Primary spot-checked reviewer claims (AGENTS.md:75 list gap confirmed real-but-illustrative; 27-command count arithmetic checks out).
- implement: commit `a75002c` — 10 files (+320/−8): ask-local.md module (primary-authored) + routing §2/§5 rows + codex-cli §5a --oss variant + command stub + EXPECTED_COMMANDS + golden +2 (sonnet subagent, every edit primary-verified via git diff) + spec + SSoT Last Verified + 2 tracked guard receipts (pre-existing tracked-before-ignore debt, rode along via non-atomic first git add — accepted, noted). Full CI-equiv 574 passed; validate.sh pass=113 warn=3 fail=0; token lifecycle within slack; compact index fresh; security quick-scan clean. Scope divergence: +1 unplanned file (guard receipt) — advisory, accepted. | Confidence: 95% — high
- spec: `docs/specs/local-model-delegation.md` authored + frozen (user pre-authorized full chain). 9 ACs, signal_tier T1 (wiring enforced by check_command_sync + deploy-manifest golden), primary_domain document-governance, 8 Domain Decisions (≤10 cap OK). Zero new MUST rules by design (module cites §8.2). No `Gate: spec` receipt written (7-phase parser vocabulary — PR #311 lesson).
- plan: 6 steps, 8 target files, module authored by primary (design-critical), mechanical wiring delegated to sonnet subagent with primary ground-truth verification (subagent self-reports NOT trusted), manifest-golden mechanics discovered at implement. Mode Normal. | Confidence: 92% — high (wiring precedent PR #311 fully documented; residual unknown = manifest golden regen mechanism, bounded)
- bootstrap: classified `feature` (new adopter-facing capability; >2 modules touched: `.agent/workflows/`, `.claude/commands/`, tools/tests, deploy manifest; full spec→handoff chain intended per SSoT precedent PR #311). Design pre-converged in chat: local model = delegated implement executor over OpenAI-compatible endpoint, patch contract, primary applies after review; cloud primary retains all gates. §8.2 reused unchanged, zero new MUSTs planned. SSoT seq 111 recorded; Last Verified bumped 2026-07-02→2026-07-04 via guarded write (receipt `.guard_receipts/337ffd90d88a8b4f.json`). Branch `feat/local-model-delegation` created from `main` (2649299). Work Log lock acquired (status: created). KB dogfood source readable (kb-main→OK@da624b5c6cdd). ADR coverage: routing.md covered by ADR-005 + ADR-007 (exit 0). ⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: feature | Timestamp: 2026-07-04T07:06:35Z
- Gate: plan | Verdict: PASS | Classification: feature | Timestamp: 2026-07-04T07:20:00Z
- Gate: implement | Verdict: PASS | Classification: feature | Timestamp: 2026-07-04T07:45:00Z
- Gate: review | Verdict: PASS | Classification: feature | Timestamp: 2026-07-04T08:05:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| ADR | docs/adr/ADR-005-downstream-file-preservation-tiering.md | covers routing.md (deploy tiering — new module must ship in manifest) |
| ADR | docs/adr/ADR-007-downstream-capability-declaration-seam.md | covers routing.md (capability seam posture: present-only, opt-in) |
| Pattern | .agent/workflows/ask-openrouter.md | template: intent router + task mapping + §8.2 pre/post-flight |
| Pattern | .agent/workflows/codex-cli.md | template: implement delegation, governance-wrapped prompt, approval/sandbox caps, post-flight git-diff scope check |
| Rule | .agent/rules/engineering_guardrails.md §8.2 | External Tool Delegation Protocol — reused unchanged |
| Precedent | PR #311 (/govern-audit) | full wiring checklist: routing §2/§5 + command stub + check_command_sync EXPECTED_COMMANDS + deploy manifest golden; zero always-loaded token cost; do NOT write a `Gate: spec` receipt (7-phase parser vocabulary) |

---

## Known Risk

- Weak local models (7B–70B) produce low-quality patches → by-design mitigation: §8.2 Junior Tool review is mandatory; primary applies patches with its own Edit tools; delegation cap excludes `architecture-change` (mirror codex-cli table, tightened for local).
- Wiring drift: a new command missing from `check_command_sync.py` EXPECTED_COMMANDS or the deploy-manifest golden fails CI (T1 — this is the enforcement, not a risk to avoid).
- Cross-platform parity (feedback rule): verify at /plan whether Gemini/Codex surfaces need a command mirror beyond `.claude/commands/` (routing.md is shared; adapters dispatch through it).
- Token ceiling: optional modules are load-on-request (~0 lifecycle cost, precedent #311 "no ceiling bump"), but routing.md row additions must be re-verified against token tests at /implement.
- trigger-compact-index.json staleness: editing routing.md requires regenerating the compact index in the same change (feedback rule; validator checks freshness).

---

## Conflict Resolution

none — recommended set contains no `conflict`/`partial-conflict` pairs (matrix read once at bootstrap; karpathy-principles × verification-before-completion = compatible).

---

## Skill Notes

- kb-consult (plan): routed candidate pool = `11_ai-llm-architecture` (task_routing "AI / LLM 功能"). Applicability pass → **N/A**: this task authors governance workflow docs (markdown + registry wiring), not an in-product LLM feature; no LLM API code ships. No blockers adopted. KB consumed as DATA only.
- karpathy-principles (plan): applied — smallest-decision steps, no new abstraction (no shipped client code; YAGNI honored), explicit patch contract over implicit behavior.

---

## Drift Log

- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Brainstorm skipped: design converged in-chat pre-bootstrap (3-turn discussion 2026-07-04; direction fixed by user = "B: local model as delegated junior executor", implement-delegation emphasized, entry point mandated). Logged per bootstrap §3.7 feature-chain rule.
- Private scan (§1 step 3): resumable research notes present but UNRELATED to this task — `research-kb-integration.md`, `research-skill-content-optimization.md` (listed for next-session discoverability, not resumed).
- §13 net-add justification (Deletion-First): no always-loaded surface touched (AGENTS.md / .agent/rules / shared-contracts unchanged); ask-local.md is load-on-explicit-request; the 2 routing.md rows are lookup-only. New-MUST posture: module MUSTs are procedural workflow steps citing §8.2 (same family style as codex-cli.md); spec declares signal_tier T1 with check_command_sync + deploy-manifest golden as the machine signals — no un-enforced standalone rule added.
- Spec-drift linter advisory (review entry, non-blocking): 9 warnings — all path-extraction noise: AC prose uses short names (`routing.md`) where the linter wants full relative paths; golden fixture / guard receipts / SSoT Last Verified are sanctioned out-of-spec-scope writes; `shared-contracts.md` flagged UNTOUCHED because AC-7 names it in a "must NOT change" list. No real drift. Lesson: future spec AC text should use full repo-relative paths for linter matching.
- Review dispatch: independent fresh-context acx-reviewer (opus) launched per Adversarial Reviewer Freshness Invariant — given diff range + frozen spec + standards only; no implementation rationale shared; instructed to re-verify all Work Log claims independently and not write to this log.
- Implement delegation: mechanical wiring (routing rows, command stub, EXPECTED_COMMANDS, codex-cli §5a, golden regen) dispatched to a sonnet subagent with exact payloads; primary verifies ALL claims against git diff + clean re-runs before accepting (subagent self-reports untrusted).

---

## Security Findings

none — implement quick-scan (A01–A03 + §3 secret detection) over `docs/specs/local-model-delegation.md` + `.agent/workflows/ask-local.md`: markdown-only, no executable code, no credential patterns (localhost base URLs only); module text itself mandates Secrets Prohibition + untrusted-output handling for the delegated path.

---

## Review Feedback

- LOW (closed-with-reason): `AGENTS.md:75` illustrative optional-module list omits `/ask-local`. The line defers to routing.md §5 as the full registry (updated ✓); the parenthetical is examples, not an allowlist; AC-7 forbids AGENTS.md diffs in this change; adding it later would spend always-loaded tokens for zero governance effect. Disposition: close — routing.md §2 hard rule + §5 registry are the authoritative opt-in surfaces and both carry ask-local.
- LOW (closed-with-reason): tracked-before-ignore guard-receipt churn rode along in commit a75002c (pre-existing repo debt from before PR #299's .gitignore, non-atomic first `git add`). Cosmetic; untracking is out of scope. Disposition: close — reopen only if receipts churn again in future PRs enough to annoy review diffs.

---

## Red Team Findings

- Full-mode pass (feature tier) by fresh-context reviewer: CLEAN on all six probed vectors — (a) no reading of module text authorizes gate-bypass/file-writes/review-skip; (b) injection surface closed (both modes forced through Junior-Tool + UNTRUSTED-DATA handling, Destructive Command Gate re-entry, injected-directive error row → Drift Log); (c) no un-enforced standalone MUST added (§13 clean, all MUSTs cite §8.2/AGENTS.md); (d) ask-local §3 ↔ codex-cli §5a cap tables consistent (variant strictly tighter); (e) explicit-opt-in posture matches AGENTS.md hard rule; (f) no credential-pattern scanner trips. No CRITICAL/HIGH → no risk decision required.

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

## Evidence

- implement: `python -m pytest tests/ci/ tests/guard/ .agentcortex/tests/ -m "not slow"` → `574 passed, 72 deselected in 153.81s`
- implement: `bash .agentcortex/bin/validate.sh` → `Summary: pass=113 warn=3 fail=0 skip=2` (3 WARNs pre-existing: historical-archive receipts + eval-coverage advisory)
- implement: `test_deploy_manifest_snapshot` regen then clean re-run → `1 passed`; golden diff = exactly `+core .agent/workflows/ask-local.md` `+core .claude/commands/ask-local.md`, 0 removals
- implement: `validate_trigger_metadata.py` → `passed for 16 entries, 6 lifecycle scenarios, and fresh compact index parity` (AC-6)
- implement: AC-7 zero-engine audit — `git show --stat HEAD`: no AGENTS.md / .agent/rules/* / validate.* / shared-contracts.md in change set; current_state.md diff = 1 line (Last Verified, bootstrap-sanctioned guarded write, receipt 337ffd90d88a8b4f)
- Bootstrap receipts: guarded SSoT write receipt `.agentcortex/context/.guard_receipts/337ffd90d88a8b4f.json` (Last Verified bump); lock `feat-local-model-delegation.lock.json` status=created 2026-07-04T07:06:35Z; `check_adr_coverage.py` exit 0 (routing.md ← ADR-005, ADR-007).


---

## Compaction 2 overflow (2026-07-04, ship-phase verification detail)

Moved from the active log's Drift Log / Phase Summary during the second §6 compaction. Full narrative also in PR #316 + session transcript.

- Regression sim (sonnet): 7/7 PASS, no regression. Change surface exact (11 files 4A/7M); routing.md pure +2 (zero pre-existing lines touched; all 28 registry rows resolve); codex-cli heading chain 1→5→5a→6→7 intact; check_command_sync synthetic-deployed negative test proves teeth (deleted pairing → exit 1); current_state.md 1 line; focused suites 30 passed; golden +2/-0 alphabetical. Premise correction: EXPECTED_COMMANDS total = 27 (26 pre-existing + 1 new).
- Fresh-adopter deploy sim (sonnet): 7/7 PASS. deploy.sh → 202 files incl. both new (manifest sha lines 32/167); deployed-mode sync 27 verified exit 0; downstream validate pass=83 warn=3 fail=0 skip=4 (all fresh-target-expected); zero always-loaded ask-local hits (routing lookup rows only); §2 opt-in row + §2.2 silent-fallback quoted verbatim downstream; temp cleaned. Side-finding (pre-existing): EXPECTED_COMMANDS tracks 27 of 30 .claude/commands files (app-init/execute-plan/write-plan untracked) → backlog row at ship-chore, Kind=review-finding P3.
- E2E fake-endpoint sim (opus): module EXECUTABLE. Happy path (probe → request → patch parse → primary-applies → scope check) + 3 negative cases (endpoint down → clean silent-fallback signal; prose response → refused to apply; out-of-scope diff w/ injected SECRET_BACKDOOR → whole-patch reject, injection treated as data) all PASS. Doc findings: 1 MEDIUM (§5 request JSON schema unspecified — messages shape/role/temperature/stream all guessed) + 4 LOW (path style cosmetic; diff-parse predicate; re-prompt wording; reject-whole-vs-salvage implicit).
- Post-sim doc fix (2nd implement pass): §5 request-body JSON example added; §4 scope-derivation (+++ b/ headers) + reject-whole-no-cherry-pick rule; §7 re-prompt example (backtick-free for table-cell safety). 2 cosmetic LOWs closed-with-reason.
- CI on ec3c8c9: 18 pass + Docs Content Pins skipping (by design). Re-run pending on doc-fix head.
