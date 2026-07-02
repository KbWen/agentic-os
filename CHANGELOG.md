# Changelog

## [1.8.7] - 2026-07-02

Governance self-audit wave: the framework audited itself (three waves, 12 subagents, every finding re-verified against the code before action), fixed what was real, encoded the method as a first-class workflow, and had its own ratchets catch four of the auditor's mistakes along the way (PRs #308-#312).

- **`/govern-audit` — governance self-audit workflow (#104, #311)**: a report-only, gate-exempt workflow for auditing the governance system ITSELF (previously done by overloading `/audit`). Encodes the proven method: baseline-first dedup, findings-are-hypotheses (verify both cited sides before reporting), disposition funnel (do-now / backlog / close-with-reason — "deferred" prohibited), same-vendor external-signal caveat, scope-qualified snapshots + mandatory `routing_actions`. Gate-exempt but abuse-proof: an exhaustive permitted-writes list blocks SSoT/rule writes.
- **Validator hardening (#308)**: D4 — `INDEX.jsonl` referenced-file existence WARN (the hash chain proved entries append-only but never checked the referenced artifact exists; it immediately surfaced a real dangling reference); D5 — a current-branch Work Log claiming pre-cutoff legacy status while missing gate evidence is denied the legacy WARN downgrade (FAIL-tier). sh+ps1 parity, ADR-006 baseline justification.
- **Eval blast-radius coverage (#308)**: anchored eval cases for the two highest-blast-radius uncovered MUST rules — §10.5 Handoff/Ship Hard Gate and §11.1 SSoT Merge Protection (zero-coverage 30→28); drifted lifecycle-token test names fixed (backlog #94).
- **Workflow-prose executability (#309)**: `/plan` no longer false-fires an unfreeze prompt on the task's OWN frozen spec (the canonical feature flow freezes before plan); `hotfix.md` gains its missing Ship step (names the 5 required receipts); `## Review Feedback` + `## Red Team Findings` added to the worklog template (demanded by 3 workflows, defined nowhere); `systematic-debugging` no longer lists `hotfix` (a classification) as a phase — and the validator's special-case carve-out for it is DELETED; a token-ceiling breach during this work was paid by deleting dead prose, not by raising the ceiling.
- **CI docs-only gate hole closed (#112, #310)**: README/INSTALL/spec content-pin tests used to run only in `heavy`-gated jobs while docs paths classify inert — so they never ran on the docs-only PRs most likely to break them. A `docs_pin` marker + an ungated `docs-pins` job (runs in <1s exactly when the heavy suite is skipped) + lock tests. The audit-chain git append-only witness also gains real behavioral tests (append→PASS, tail-truncation→FAIL, published-edit→FAIL) — it previously had only source-substring checks.
- **Windows lock fix (#312)**: `guard_context_write.py file_lock` now survives the Windows delete-pending window, where `os.open` on a lock file being unlinked raises `PermissionError` (not `FileExistsError`) — previously a crash, observed twice on hosted CI; deterministic regression tests included.
- **Archival hygiene**: 28 shipped work logs that past `/ship` runs left uncommitted or unarchived are now properly archived with chain entries; the v1.8.6 dangling INDEX reference is healed by restoring the referenced artifact (the append-only chain itself was never touched).

## [1.8.6] - 2026-06-30

Development-flow hardening: 13 acceptance criteria across downstream-state isolation, gate/evidence honesty, CI/security enforcement truth, demonstration-over-green-gates, and developer-command hygiene (PRs #299–#304). Net effect: more governance MUSTs are now machine-enforced rather than self-reported. (v1.8.5 was cut and reverted for a capabilities CI regression; this release skips that number.)

- **Downstream SSoT isolation + dry-run honesty (AC-1/AC-2, #299)**: deploy installs `.agentcortex/context/current_state.md` only from the template and fails closed if it is absent — the source repo's live SSoT is never shipped downstream; dry-run discloses the generated artifact.
- **Gate/evidence honesty (AC-3/4/5/6, #300)**: `/ship` gate-receipt audit hard-fails on missing required receipts for feature/architecture-change; `Diff Base SHA` split from `Checkpoint SHA`; `verify_agent_evidence.py --strict` + honest 3-state wording; validator escalates current-branch Resume/Test-Gate gaps at handoff/ship to FAIL (historical stays WARN), sh/ps1 parity.
- **Demonstration over green gates (AC-13, #301)**: user-facing-surface changes require an anchored demonstration — for deploy, a normalized manifest golden asserted against a CI re-run of real `deploy.sh`; honest-ceiling: non-executed surfaces (README render) stay advisory, no screenshot harness.
- **CI/security enforcement truth (AC-7/8/9/12, #302)**: docs reconciled to the real required-check set; credential scan fails closed on scanner execution error; dependency audit now covers `.github/requirements-ci.txt` — which surfaced **CVE-2025-71176 in pytest 8.4.1**, fixed by bumping to pytest 9.0.3; the docs-only CI classifier no longer lets `.agentcortex/context/*` runtime state skip security-relevant jobs.
- **Developer-command hygiene (AC-10/AC-11)**: bare `pytest` from repo root no longer dies on a gitignored cache demo (`norecursedirs` + rename + documented canonical command); `validate.ps1 --no-python` is a real alias of `-NoPython`.
- Spec `docs/specs/dev-flow-hardening.md` finalized `draft → shipped` + indexed (#304).

## [1.8.4] - 2026-06-28

Patch release: **deploy data-loss fix** (confirmed live in v1.8.3).

When deploy preserves a pre-existing scaffold/wrapper file that was absent from the old manifest, it recorded the *user's* hash as the baseline. The next deploy then treated the unchanged user bytes as framework-unmodified and could silently overwrite the user's customization. Fix: record the **upstream source hash** as the baseline at the two skip-preserve points, so future updates correctly detect the file as user-customized and preserve it (with a `.acx-incoming` sidecar).

- `deploy.sh`: record `$src_hash` (upstream baseline), not `$dst_hash` (user hash), when skipping a preserved pre-existing file.
- `tests/ci/test_deploy_tiering.py`: regression `test_preexisting_sidecar_file_stays_preserved_across_repeated_deploys` → suite **26 passed**.
- Provenance: fix authored by Codex (cherry-picked from a deferred downstream-hotfix branch that was rolled back to CLASSIFIED for exceeding the hotfix size threshold; the eval/KB parts of that bundle shipped in v1.8.1, the deploy fixes did not). Necessity re-verified against v1.8.3. Follow-ons: §legacy poisoned-manifest migration → backlog; CP_FLAG core-backup → already shipped in main.

## [1.8.3] - 2026-06-28

Patch release: downstream-adaptability honesty + hardening notes (PR #293), from a read-only 3-axis adaptability diagnosis. **Engine behavior unchanged** — docs + one bootstrap default.

- **`skill-ecosystem.md` status note**: the doc read like a shipped registry/trust-tier/discovery *platform*; added a "direction vs shipped" callout — shipped = `manifest.yaml` + `custom-*` + the ADR-007 declaration seam; roadmap = auto-discovery / registry resolution / capability sandbox. Reaffirms third-party skills are opt-in, never auto-activated (ADR-007).
- **`docs/INSTALL.md` monorepo note**: "one deploy = one project root" — the framework deliberately doesn't partition shared SSoT across sub-packages (ADR-004/005). Sets adopter expectations.
- **`bootstrap.md` Owner default**: derive `Owner` from `git config user.name` (fallback session-id) so the multi-person collision key stays consistent.
- Backlog #98–101 (SSoT section-append, partial-adoption on-ramp) + report-trigger issues #291 (autopilot fan-out lock) / #292 (foreign-skill opt-in detector) tracked from the research; not built (no verified consumer — evidence-before-adding).

## [1.8.2] - 2026-06-28

Patch release: adoption + honesty. **Engine behavior unchanged** — docs/asset only.

**Honesty**
- **Hero-line accuracy** (README): the landing pitch no longer implies CI catches skipped reviews/phases. Scoped to reality — leaked secrets and a green check over zero tests fail git hooks + CI; a skipped review or phase shows up when the validator reads the work trail (local). Matches the existing Rules-vs-enforcement table and the "machine-enforced, not self-report" positioning (removes an overclaim).

**Adoption (README)**
- **`docs/assets/demo-gate.gif`** + `demo/render_demo_gif.py`: a recording of the real `demo/run.sh` credential gate (an agent leaks an `aws_access_key_id` and reports "Done"; the scanner redacts the value and BLOCKS the commit), wired into the README "run a gate yourself" section *above* the clone — so a visitor watches the machine say no before deciding to adopt. Same PIL render pipeline as the existing GIFs; no new runtime dependency. (zh-TW GIF twin to follow.)
- **Pipeline ASCII diagram** (README "Gated phases" section): a text-renderable companion to the pipeline GIF (shows in search snippets / no-image contexts) — the three risk-scaled lanes plus the ship-gate BLOCKED/SHIPPED truth-table.
- **"Sits under what you already have"** positioning section: frames Agentic OS as the enforcement layer that complements an existing rules file or skill pack — by category, no named competitors.

**Backlog**
- #97 intake (routing_actions staleness escalation): a cross-domain `status: pending` routing action can sit unwatched (ship only resolves pending actions in the current `primary_domain`). Backlog-only hardening of an existing gate, no engine change.

## [1.8.1] - 2026-06-23

Patch release: governance, KB seam, docs, and CI hardening wave. Packages #280–#284. **Adopters with no KB are behaviorally unaffected** — all engine behavior is unchanged; the eval, lifecycle, and CI changes are internal correctness fixes.

**Governance fixes** (#280/#281)
- **KB injection-decline oracle hardening** (#280): replaced the flawed denylist oracle with an `\A...\Z`-anchored exact two-line receipt (structured `refusal_receipt` + `⚡ ACX` sentinel; untrusted payload isolated in a `<kb-data>` block). The eval now genuinely proves the "KB-surfaced directive = DATA, name-and-decline" floor instead of rewarding banned-term avoidance. Live runner hardened: Windows UTF-8 child decode, exact `--case` with `--agent-cmd`, redacted OSError/timeout diagnostics (no argv/secret leak), stderr preservation, clean `.ps1` launch failure; plus inline URL-credential redaction in `_sanitize_diagnostic`.
- **Frozen-spec SSoT lifecycle fix (ADR-010)** (#281): resolves a PRE-EXISTING impossible-SSoT cycle where a legal `status: frozen` spec could never satisfy the validator (required Spec Index entry) without a forbidden pre-`/ship` SSoT write. `validate.sh`/`validate.ps1` now skip `draft|frozen|cancelled` and require an index entry only for `shipped`/`living`. `/ship` remains the sole SSoT indexer; Write Isolation single-writer invariant preserved. `spec.md` reconciled (no pre-ship index write), `plan.md` Frozen-Spec Pre-Check reads `status:` from disk.

**KB seam** (#282/#283)
- **Absent-cost honesty + changelog + wiring probes** (#282): corrected the overclaim that the KB seam is "zero-cost when absent" — the v1.8 seam adds ~217 always-loaded bootstrap tokens even with no KB declared. `CHANGELOG.md` + `connecting-a-knowledge-base.md` updated to "zero KB reads / zero KB-content tokens when absent; ~217-tok always-loaded cost." Added omitted PR #273 to the v1.8.0 changelog scope. Fixed wiring probes (bash `[[:space:]]*[0-9]+`; PowerShell `Test-Path -PathType Leaf`).
- **Optional schema-v4 manifest accelerators (ADR-009 follow-up)** (#283): teaches the governed KB-consume flow to consume OPTIONAL schema-v4 `manifest.json` accelerators: `kb_version` fingerprint in `§1b` health (detects moved/stale KB), `approx_tokens` smallest-first budgeting + section cap in `§3.6`, candidate-pool applicability pass (routed slugs → only applicable items block). `UNREADABLE` now explicitly covers malformed/unparseable (fail-closed). Deleted dead `kb_path_env` config. New adopter-guide section covers optional field shapes + BYO no-manifest fallback + privacy reminder. Graceful for absent/BYO-no-manifest; no hard schema-v4 dependency.

**CI** (#284)
- **Windows pytest sharding** (#284): the slow non-required `Pytest (Windows)` job (~8:26) is sharded across 3 parallel matrix runners via `pytest-split` (pinned `0.11.0`). Wall-clock 8:26 → 7:14 with count-split; a `.test_durations` file would balance further. `pytest-xdist` was measured slower for this suite. Zero downstream impact (deploy ships no `.github/workflows/` or `tests/`). Not promoted to required.

## [1.8.0] - 2026-06-21

Minor release: a hardening + dogfood wave for the v1.7.0 ADR-009 knowledge-base seam, plus a capabilities-validator BOM fix. Packages #273–#276. **Adopters with no KB read no KB and ingest zero KB-content tokens** — the seam stays present-but-inert (behavior unchanged). Note: this is "zero KB reads / zero KB-content tokens when absent," not byte-identical — the seam's bootstrap guidance is a small fixed always-loaded cost (~217 tokens) even with no KB declared.

**Governance / downstream adaptability** (#273/#275/#276 — ADR-009 follow-up, `docs/specs/kb-seam-hardening.md`)
- **Capabilities-validator BOM tolerance** (#273): `validate_downstream_capabilities.py` now reads with `utf-8-sig`, so a `downstream-capabilities.yaml` saved with a leading UTF-8 BOM (older Windows editors) no longer fails with a cryptic `unknown top-level key`. Fail-closed posture unchanged — a BOM-prefixed `role: authority` gate-relaxation is still rejected.
- **`${ACX_KB_PATH}` env resolution** (#275): a `knowledge_sources[].path` containing `${ACX_KB_PATH}` resolves against the env var (clone root; `entrypoint` relative) so one machine relocates a shared KB clone without per-project edits. Present-only (read only when a block is present), literal paths unchanged, cross-platform, no-Python safe. A committed `.agentcortex/templates/downstream-capabilities.example.yaml` demonstrates it (the strict validator accepts only full-line comments + quoted `:`/`${}` paths — now documented, closing a pre-existing copy-paste footgun).
- **Path trust model, no guard** (#275): the KB path is documented as self-authored / out-of-repo / OFF the trust boundary, consumed fail-closed as DATA; **no `..`/containment guard is added** — it would only ever fire on the legitimate out-of-repo KB, and the path is not attacker-influenced. `validate_downstream_capabilities.py` stays schema-gate-safety-only (never resolves the path; CI-deterministic).
- **Surgical-read discipline at the line-of-action** (#276): the `bootstrap.md §3.6 kb-consult` row now carries the mechanic the agent acts on — query `task_routing` (never Read the whole ~25–53K-tok manifest), read the routed page's checklist *section* not the whole page, ≤3 pages/phase. A real **dogfood** proved the gap (the agent over-routed 4 pages = 36K tok vs a 495-tok surgical consult = ~17× cheaper). **Per-entry KB health**: `§1b` records `knowledge_sources: <id>→OK|UNREADABLE` so a moved/dead KB is visible each bootstrap; a no-Python one-liner verifies wiring on demand.
- **Injection-decline eval** (#275): one LLM-in-loop governance-eval case asserts a directive embedded in a KB page is named-and-declined (the `§Untrusted Tool Output` floor on KB-surfaced data). Consult-quality stays honor-system — labeled, raised-probability-not-enforced.

**Docs / adoption** (#274)
- **README discoverability**: the `knowledge_sources` KB seam now surfaces in the README `## Docs` table (EN + 繁中), linking the adopter guide — previously reachable only via `INSTALL.md`.

**Housekeeping**
- Lifecycle token budget bumped 352k→353k for the matured seam (the §3.6 rule is net-token-saving — it prevents 36K-tok over-routes) and re-baselined. A roundtable + Tenth-Man pass deliberately **deferred** a `kb_doctor` tool and **cut** a resolver / fixture-pytest / path-guard (vacuous-green or security-theater given consumption is agent-prose-driven).

## [1.7.0] - 2026-06-20

Minor release: a present-only knowledge-base consumption seam (ADR-009) plus skill-provenance, a research-persistence convention, and a proof-first README/docs overhaul aimed at adoption. Packages the since-v1.6.0 merges (#258–#271, #86).

**Governance / downstream adaptability** (#270/#271 — ADR-009)
- **Knowledge-Source Consumption Seam**: a present-only, OPTIONAL `knowledge_sources:` block extending ADR-007's `downstream-capabilities.yaml` lets the governed flow CONSUME (read-only) an external markdown knowledge-base to enrich `/plan` + `/review`. **Absent → zero reads, zero tokens, byte-identical behavior** (the no-KB path most adopters are on). KB content is treated as DATA under `AGENTS.md §Untrusted Tool Output` (never loaded as governance); the manifest is a hint, the page is authority; `role` is fixed to `advisory` and `manifest_trusted` defaults `false`. The validator (`validate_downstream_capabilities.py`) accepts the block under a strict allowlist sub-schema — gate-relaxation stays structurally unrepresentable (rejected whole-file, never clamped) — and `validate.sh`/`.ps1` gained an AC-7 check that the seam's `§1b` loader + `§3.6 kb-consult` row stay shipped. Stage-1 only; cross-phase auto-consult and any agentic-os→KB auto-backfill were rejected (cross-repo write = poisoning). Downstream guide: `connecting-a-knowledge-base.md` (now linked from `INSTALL.md`).

**Governance / skills** (#258, #259)
- **Skill provenance + compatibility floor** (#259): a source-repo-only validator (`check_skill_provenance.py`) asserts every `.agents/skills/*/SKILL.md` declares `name`+`description` (name==dir) and that a static `skill-provenance.yaml` manifest (origin/source/license, fail-closed allowlist) stays complete — no orphans/dupes.
- **Research persist-before-browse** (#258): `/research` writes its source list + bounded notes to a gitignored `research-<topic>.md` before the first external browse; `/bootstrap §3` auto-surfaces them so a new session resumes prior research without a human remembering it exists.

**Docs / adoption** (#260–#263, #266, #267, #269)
- **Proof-first README overhaul**: rebuilt the public README from a 506-line spec-dump into a lean, visual-first landing page (concept hero + workflow/pipeline GIFs, EN + 繁中) with a reproducible `demo/run.sh` exercising the real credential gate; feature/command/architecture detail relocated to new `docs/reference.md` + `docs/INSTALL.md`. Honest framing throughout (guidance vs. enforced controls; no "can't lie").
- **CI-onboarding** (#263): `docs/INSTALL.md` shows adopters how to wire the deployed validator + credential scan as a required status check. **Copilot entry parity** (#264): `deploy.sh` now ships `.github/copilot-instructions.md` downstream. **CLAUDE platform guide** gained a 繁中 twin (#269). **Worktree safety checks** added (nesting + gitignored-target detection, #267).

**Fixes / housekeeping**
- Ship-History ordering doc corrected to prepend newest-first (#265); README de-dup (#86); backlog handoff + ship bookkeeping (#268).

## [1.6.0] - 2026-06-15

Minor release: an upfront plan-time change-sizing advisory plus a security fix closing an ADR-007 capability-gate fail-open, packaging the since-v1.5.4 merges. PRs #241 (#145), #244, plus backlog / work-log hygiene (#240/#242/#243/#245/#246/#247).

**Governance** (#241 — issue #145)
- **Upfront change-sizing advisory**: a single advisory trigger added to `/plan`'s existing Pre-Plan Advisory block citing `engineering_guardrails.md §10.1`, front-running the previously *reactive* implement-time blast-radius / frozen-tier catch — no copied thresholds, no new MUST/gate. Closes the lone residual of the Change Sizing issue (#145).
- Enforce the downstream capability load-policy ceiling (`fix`).

**Security** (#244)
- **ADR-007 capability-gate fail-open closed**: `downstream-capabilities.yaml` is now read by a strict, fail-closed mini-parser instead of the lenient shared YAML path, so a malformed or hostile capability file can no longer silently relax gates.

**Housekeeping**
- v1.5.4 release-ledger backfill (#240); backlog archival + redundant-row cancellation (#242/#243); bulk archival of previously-shipped and catch-all work logs (#245/#246/#247) + an archived gate-receipt schema fix.

## [1.5.4] - 2026-06-14

Patch release: downstream adaptability for heterogeneous flows/architectures (many custom skills, harness/subagent fan-out, other work-management flows), plus the cross-contributor credential CI hardening and a security-policy refresh. PRs #238 (ADR-007/008), #236 (#73/#74/#75), #237.

**Governance / downstream adaptability** (#238 — ADR-007 + ADR-008)
- **Downstream Capability Declaration Seam** (ADR-007): a present-only, opt-in, gate-capped `downstream-capabilities.yaml` (loaded at bootstrap §1b) lets a downstream register `custom-*` skills into auto-activation, declare a `subagent_policy`, and declare advisory `trackers`. Gate-relaxation is **structurally unrepresentable** — a denylist + allowlist schema validator (`validate_downstream_capabilities.py`) rejects, never clamps. Absent file = zero behavior change; the same-owner lock short-circuit was deferred as a Non-goal (`recover_worklog_lock.py` untouched).
- **Portable Safety Floor** (ADR-008): the three always-loaded `AGENTS.md` safety invariants are fenced into a committed generated `.agentcortex/AGENTS.safety.md` nucleus (+ a validator freshness check) that any non-shim harness (Codex/Gemini/custom) can inject into every dispatched subagent. A **no-Python credential floor** (`credential_floor.sh`/`.ps1` — narrow FP-free AKIA/PEM/`ghp_` subset, redacted) is wired into the pre-commit hook so the "block secrets before object history" control works without Python; `scan_credentials.py` — previously absent from the deploy whitelist, a dead control downstream — is added as the richer python path.
- Reviewed by 4 independent fresh-context agents (initial NOT READY → 4 fixes: dead `FAIL` arg → WARN honesty, denylist → allowlist, stale SSoT summaries, docstring → PASS). 30 new tests; full fast suite 307 passed; validators sh↔ps1 parity; ratchet 194/195. All additive + present-only.

**Security / CI** (#236 — #73/#74/#75; #237)
- **CI PR-diff credential scan** (#73): `scan_credentials.py --range base...head` in a `pull_request` job so contributors who never install the opt-in hook still get pre-merge secret protection (complements TruffleHog `--only-verified`), with a `# pragma: allowlist secret` escape + zero-sha/exit-3 fail-safe.
- ShellCheck now lints `.githooks/*.sample` (#74); the opt-in hook's gitignored worklog-count check is WARN, not a hard FAIL that blocked every commit (#75).
- `SECURITY.md` supported-versions refreshed to 1.5.x (#237); TruffleHog action bumped 3.95.3 → 3.95.5 (#174).

## [1.5.3] - 2026-06-13

Patch release: two additive governance/security guards (zero always-loaded prompt cost) plus CI and discoverability improvements. PRs #233 (issue #157), #234 (issue #225), #230, #231.

**Governance / CI**
- **Token-lifecycle baseline + drift detector** (#157): `update_lifecycle_baseline.py` stores a per-scenario governance token-cost baseline around the existing `analyze_token_lifecycle.py`, with a `--dry-run` drift check — growth beyond a 10% slack is flagged (advisory WARN in `validate.sh`/`.ps1`, hard teeth in a pytest ratchet); shrink is never punished. Catches slow per-PR governance-token creep that no existing test covered. ADR-006 native-baseline bumped with justification.
- **Pre-commit credential scanner** (#225): `scan_credentials.py` flags distinctive-prefix credential shapes (AWS AKIA, PEM key headers, GitHub `ghp_`/`github_pat_`, OpenAI `sk-`, Slack `xox`, Google `AIza`) on the staged diff with redacted output, wired into the opt-in `.githooks` pre-commit hook (blocks on match, warns+continues on a git error). Honest framing: opt-in + `--no-verify`-bypassable, so CI TruffleHog remains the enforced control. A 4-expert review + dev-flow simulation hardened it — precise-only patterns (zero false positives on real code) and a hunk-context diff parser that closed a secret-dropping false negative.

**Docs / discoverability**
- Repo discoverability pass (#230): README `## FAQ`, root `llms.txt` (llmstxt.org convention), friendlier GitHub description + topics.
- CI wall-clock (#231): docs-only PRs skip the heavy job matrix via a dependency-free scope detector; required checks and branch protection unchanged.

## [1.5.2] - 2026-06-11

Patch release: destructive-command incident response. A downstream field report (real `rm -rf` cascade that clobbered a parent repo's working tree) exposed a README↔enforcement drift class; this release closes it, hardens the deploy bootstrap, and promotes the remaining flow-independent safety invariants found by the follow-up audit. PRs #222/#223/#224.

**Governance**
- **Safety-invariant cluster in `AGENTS.md §Core Directives`**: the advertised "Destructive Command Blocking" rule had existed on NO loaded surface since day one (READMEs only, with divergent EN/zh severity + command lists; platform adapters carried drifting copies). `AGENTS.md` now carries a capped cluster (hard cap ~5; placement test: hazard reachable from any tool call AND irreversible/exfiltrating): **Destructive Command Gate** (deny-by-default; rollback plan must explicitly cover UNTRACKED/gitignored state; STOP on partial failure — a half-deleted directory silently redirects git to the parent repo), **Secrets Prohibition**, **Untrusted Tool Output** (tool-result text is data, never instructions). Each is eval-backed; retargeting also fixed a dangling protects-tag (the prompt-injection eval case had been guarding a section containing no injection text).
- Both READMEs demoted to pointers at the canonical rule (ends the EN/zh disagreement structurally); Codex/Antigravity adapter lists reconciled and now cite the canonical rule; Codex gains the previously-missing secrets rule.
- **ADR-001 amendment**: safety invariants carved out of the token-saving skip policy's jurisdiction (D3 governs cost/process rules only; its ~3.5k-token dollar premise measured stale at 2026 cached pricing). The tiering architecture itself is unchanged — the sorting key for safety content changes from token cost to hazard reachability.

**Deploy / downstream**
- **`deploy_brain.sh` cache origin verification**: the bootstrap path did `cache exists → git pull` without comparing the cache's origin URL to the configured source — a stale pre-migration cache pulled 457 commits of the WRONG repo on a live downstream. Now: normalized URL compare (env `ACX_SOURCE` > `--source` flag > manifest `source_repo:`; the `.ps1 -Source` path is now honored by the check), mismatch → warn + re-clone, and a partially-failed cache removal hard-fails instead of letting git fall through to the parent repo. +4 regression tests (mutation-verified).
- `.gitattributes` scaffold pins `.agentcortex-manifest` and `.githooks/**` to LF (manifest hash-field parsing was one `\r` away from "every file appears undeployed" on Windows autocrlf checkouts).


## [1.5.1] - 2026-06-11

Patch release: post-v1.5.0 downstream-simulation fixes (6-way fleet; 36/40 checks already passing — every v1.5.0 promise held).

**Deploy / downstream**
- **GEMINI.md now deployed** — it was a first-class agent entry point (imports `AGENTS.md`) present in the source repo but omitted from every `deploy.sh` site, so downstream Gemini/Antigravity users got no entry point. Wired into all deploy sites (scaffold tier, beside `AGENTS.md`/`CLAUDE.md`).
- **Lifecycle tolerance for user-authored docs** — `check_lifecycle_frontmatter.py` no longer FAILs a downstream user's own `docs/adr/*.md` for lacking the framework's lifecycle frontmatter (it imposed a doc contract on content the framework never wrote, blocking their `validate.sh`). Downstream installs (`.agentcortex-manifest` present) get an advisory WARN; the framework source repo stays FAIL-gated.
- Quieter deploys: the "Migrating from legacy paths" banner only prints when real legacy artifacts exist, not on every routine re-deploy.

**Validators**
- `validate.sh` gate-receipt greps made case-insensitive to match the PowerShell mirror (eliminates a 2-count sh/ps1 parity drift); aggregated local-skill note deduped.


## [1.5.0] - 2026-06-11

Hardening release: a P1 governance sprint (locks, behavioral evals, anti-bloat norms), a validator architecture decision, and major deploy/CI performance and downstream-tolerance fixes. 10 PRs (#209-#218); all gates, reviews, and cross-platform CI enforced throughout.

**Governance**
- **Blocking Work Log lock (#147)**: the per-branch `<worklog-key>.lock.json` graduates from advisory to single-writer blocking (`worklog_lock.mode: blocking`, configurable back to `advisory`). Atomic acquisition (`O_CREAT|O_EXCL`; racing recoverers serialize), new `release` / `ensure --takeover` verbs (takeover requires an audited Drift Log line), a Phase-Entry Lock contract in `shared-contracts.md`, and validator WARNs for non-stale owner/phase mismatches. Review caught and closed a real injection vector: lock `owner`/`session` strings can no longer forge Work Log gate receipts via any line-break encoding (full `str.splitlines()` set sanitized).
- **Governance behavioral eval harness + DELETE-bias diff (#151)**: data-only adversarial case set (`.agentcortex/eval/governance.yaml`, 23 cases) + stdlib runner (`run_governance_eval.py`) scoring transcripts or a live `--agent-cmd`; `--coverage` maps MUST-rule sections to guarding cases (honest tier-blind wording; inventory parent double-count fixed); `run_delete_bias_diff.sh` proves whether a rule is load-bearing before deletion. Validators surface coverage as an advisory WARN.
- **Deletion-First Norm + ADD-Gate (#166)**: new conditional guardrails §13 — changes to always-loaded surfaces must cite a deletion or justify the net-add; new imperative rules declare a signal tier (machine-enforced / eval-backed / named observer). Shipped with net −5 always-loaded lines (the cure passes its own constraint) and a quick-win reachability hook so the norm is loadable on the most common governance-edit flow.
- **ADR-006 — validator Python-core strangler**: all NEW validator checks are Python tools behind the existing `run_python_check`/`Invoke-PythonCheck` twin wrappers; native additions only via a justified, diff-visible baseline bump (Zero-Python-downstream doctrine honored). Enforced by a bidirectional ratchet test (baseline 187/188 frozen; growth and stale-shrink both fail). Zero runtime change at adoption.
- Ledger hygiene: Ship History 10-entry rotation enforced (37 accumulated entries rotated out; SSoT halved to ~170 lines), backlog↔tracker resync (5 suspected drifts confirmed as by-design future-direction rows; legend note added).

**Deploy / downstream**
- **EOL-normalized manifest hashing**: CRLF-checked-out but unmodified files no longer misclassify as "locally modified" — framework updates land instead of silently sidecar-ing (evidenced on a live downstream at v1.2.0). `.gitattributes` now pins `*.md`/`*.yaml`/`*.yml` to LF.
- **Stale-skill detection with manifest proof**: retired framework skills are named loudly on deploy; user-created non-`custom-*` skills get a single gentle aggregated note (never "retired upstream"/"delete it"); `custom-*` stays silent; flat-skill lookup is exact-match.
- **Order-paired batch hashing**: deploy update runs drop from ~72s to ~7.5s on Windows (one single-process hash pass; path strings never cross the bash↔python boundary, eliminating an entire key-corruption bug class). bash<4.3 / `ACX_FORCE_PERFILE=1` / no-python paths preserved.

**CI / tests**
- `.agentcortex/tests` (177 tests) now CI-gated on Linux AND a new Windows pytest job — which caught a real 8.3-short-path bug in `trigger_runtime_core` on day one (fixed with forced-short-path regression tests). UTF-8 file-validity sweep + critical-file presence pre-check added; `verify_agent_evidence`-on-PR was dropped as vacuous (no review-mirror producer) rather than wired as theatre.
- `slow` pytest markers: local fast loop 17 min → ~3.5 min (CI selection unchanged, full suite still runs); Windows CI pytest job ~15 min → ~8 min after the deploy speedup.

**Process**
- New discipline applied throughout and recorded: expert attribution review after confirming a fix target and before modifying — it reclassified five suspected drifts as deliberate design, corrected a false performance rationale in ADR-006's history, and sent two delegated "success" claims back for owner-environment reproduction.


## [1.4.1] - 2026-06-08

Patch release: chat-language adherence fix plus a CI time-bomb test fix.

**Governance**
- **Chat-language policy hardening (#206)**: agents now reliably reply in the user's input language instead of defaulting to English (worst on Claude) or drifting to Korean/Japanese. Root cause was output-layer enforcement asymmetry — the every-turn English `⚡ ACX` sentinel and gate/phase templates drowned a single un-reinforced two-language line — compounded by an Antigravity-only "default Traditional Chinese" rule that contradicted `AGENTS.md`. The `AGENTS.md` policy is now universal-language (arrows are examples, not an allowlist) with explicit anti-drift (including "never collapse a non-English input into English"), a live-chat-vs-artifact carve-out, and a deterministic English fallback; the language requirement now rides the always-reinforced sentinel rule; `.antigravity/rules.md` inherits the canonical policy instead of overriding it.

**Tests**
- Fixed a time-bomb in `tests/guard/test_worklog_lock_recovery.py::test_active_lock_preserved_by_api_and_cli`: it anchored a lock's `updated_at` to a frozen timestamp while the CLI subprocess evaluates staleness against the real clock, so the test went red ~60 minutes past its hardcoded time on any later run. The lock is now anchored to the real current time, isolating the test to live-owner preservation.

## [1.4.0] - 2026-06-08

Release covering work merged since the v1.3.0 tag. Adds local validation tooling, work-log lock resilience, advisory governance linters, and multi-agent review guidance; hardens cross-platform deploy/validation; and polishes the public README.

**Features**
- **Opt-in pre-commit local validation hook (#192)**: a bundled `.githooks/pre-commit.guard-ssot.sample` runs Agentic OS validation before each commit (PowerShell-aware on Windows, falls back to `validate.sh`). Validator failures block the commit; guarded SSoT receipt warnings stay advisory.
- **Work Log lock auto-recovery (#188)**: stale `<worklog-key>.lock.json` advisory locks are recovered automatically instead of hard-blocking, while genuinely active CLI-created locks are preserved.
- **Advisory spec drift linter (#156)**: flags acceptance-criteria coverage gaps between a spec and the staged git diff (advisory, non-blocking).
- **Multi-agent review guidelines + contributor adapters (#162)**: shared review guidance that maps back to canonical rules instead of duplicating them.

**Validator & deploy hardening**
- Deploy now backs up and warns on locally-modified core-file overwrite instead of silently clobbering; `sha256` comparison hardened for Windows/Git-Bash backslash paths (#173).
- `validate.sh` uses POSIX `[[:space:]]` instead of GNU-only `\s` for portability (#190); PowerShell validator parity gaps closed; flaky SIGPIPE in `cs_content` index parsing eliminated (#182).

**Governance**
- `CLAUDE.md` / `GEMINI.md` added to the tiny-fix exclusion set with a 4-way drift guard; the Claude/Gemini startup line reframed as an intent-first pointer.

**Docs**
- README v1.4.0 polish: fixed the broken top version badge (the shields.io URL had an unencoded space in `Agentic OS`, which returned HTTP 000 on GitHub) and converted the ASCII "The Solution" hero diagram to a mermaid flowchart with explicit `FAIL → STOP` branches. Version banners bumped to v1.4.0 across `README.md`, `docs/README_zh-TW.md`, `CITATION.cff`, the Model Selection Guide (EN + zh-TW), the Testing Protocol (EN + zh-TW), `deploy.sh` (`ACX_VERSION`), and the Antigravity runtime guide. Measurement-tied banners (`LIFECYCLE_BENCHMARK`, dated to the 2026-05-31 snapshot) were intentionally left unchanged.

## [1.3.0] - 2026-06-03

Consolidated release covering PRs #124–#177 since v1.2.0. Activates the downstream override layer, adds a merge-conflict-marker validator gate, brings the sh/ps1 validators to full count parity, expands governance contract tests, and polishes the public-facing docs.

**Features**
- **Downstream override layer activated + skill-sidecar tiering (#175)**: per-fork/per-user `AGENTS.override.md` is now loaded present-only at session start (MAY narrow/disable directives but cannot relax delivery gates), and `deploy` preserves locally-modified framework skills as visible `.acx-incoming` sidecars instead of overwriting them.
- **Merge-conflict-marker gate (#131)**: `validate.sh` / `validate.ps1` now FAIL on unresolved `<<<<<<<` / `=======` / `>>>>>>>` markers in tracked files.

**Validator & tooling**
- sh↔ps1 full count parity: closed parity gaps F2 + F4, gated the ps1 count-parity test to Windows, aligned `validate.sh` column indices, and removed the em-dash pre-filter (#133).
- Cleared 3 framework-self false-positive WARNs (#170, #171, #172); adopted code-review findings with stronger fixes plus regression tests.

**Governance & tests**
- State-machine transition-graph contract test (#132); classification-escalation + SSoT-heartbeat contract tests (#16).
- `CITATION.cff` correctness + skill count corrected 17→14 (#124); untracked a leaked work log and advanced the SSoT sequence (#125).

**Downstream & Windows**
- Hardened deploy + validation follow-ups for Windows; regenerated the AGENTS.md trigger-compact-index for content-hash drift; tightened downstream ADR tiering coverage; corrected ship-evidence SSoT root-cause notes.

**CI**
- Pinned test deps + pip cache + UTF-8 + branch-scoped concurrency (#163, #177); dropped the unsupported Dependabot pip ecosystem entry (#163 follow-up).

**Docs**
- **README de-slop (EN + zh-TW)**: removed AI-generated tonal artifacts so the project face reads as a genuine, professional share rather than a product launch page. Dropped the triple-slogan line, per-section header emoji, and the "demand discipline" footer in `README.md`; softened the buzzword-heavy opening ("頂尖開發者 / 高效能 / 結構化認知框架") and removed section-header emoji in `docs/README_zh-TW.md`. Aligned the top tagline ("operating system" → "layer") with the humbler open-source footer, and brought the zh-TW anti-drift bullets back to plain register for EN/zh parity. Trimmed the redundant "Ready/Compatible" marketing badges (platform support is already in the Platform Compatibility table). No content, tables, diagrams, or install steps were removed.
- Self-regenerating benchmark token snapshot + deleted-skill-ref fixes + zh-TW parity (#126–#130); documentation navigation map; refreshed stale platform/skill references; clarified the Windows Git Bash requirement; backlog issue-sync + archival (#8, #139, #165); Codex contributor attribution; QRSPI research notes (backlog #69).
- Version banners bumped to v1.3.0 across `README.md`, `docs/README_zh-TW.md`, `CITATION.cff`, the Model Selection Guide, and the Testing Protocol (EN + zh-TW). Validator encoding-canary phrases repointed (sh + ps1) to match the de-slopped READMEs. Measurement-tied banners (`LIFECYCLE_BENCHMARK`, dated to the 2026-05-31 snapshot) and illustrative example text were intentionally left unchanged.
- Fixed stale internal citations in live files surfaced by a doc-accuracy audit: `engineering_guardrails.md` (`bootstrap.md §7` → `§1 Classification Tiers`), `.agent/config.yaml` (nonexistent `AGENTS.md §Document Lifecycle Governance` → `doc-governance.md`; stale `§Skill Safety #7/#8` item numbers), `portable-minimal-kit.md` (removed `minimal-text-hardening-kit.md` → `check_text_integrity.py`), and a stale artifact-node filename in the `antigravity-v5-runtime.md` mermaid diagram. `PROJECT_EXAMPLES.md` (EN + zh) now uses the canonical `/plan` and `/implement` in its example flows instead of the `/write-plan` / `/execute-plan` aliases, which work on Codex/Antigravity but lack Claude `.claude/commands` stubs (so the examples are now cross-platform-portable).
- Audit also surfaced unbuilt planned deliverables in historical ADR-002 / `lock-unification.md` (AC-24/AC-25: `governance-doc-lifecycle-matrix.md` + an `AGENTS.md` section never created) — left unedited pending a scoping decision rather than papering over the record (tracked as a follow-up).

## [1.2.0] - 2026-05-31

Consolidated release covering PRs #98–#122 since v1.1.2. Highlights:

**Governance model**
- **Handoff-trigger overhaul (#121)**: replaced the turn-count handoff trigger with a **context-occupancy + phase-boundary** advisory model, converged four scattered/contradictory turn constants into one SSoT (`AGENTS.md §Context Pruning`), and added a cross-platform caching/compaction reference (`token-governance.md §6.1`) for Claude / OpenAI Codex / Google Gemini. Stays advisory — no enforced gate added.
- **Doc-consistency cleanup (#122)**: unified the tiny-fix threshold (`< 5 lines` → canonical `< 3 files, no semantic change`), unified the runtime sentinel (`[ACX-READ-OK]` → `⚡ ACX`), genericized stale exact model-version strings to drift-proof tier descriptors (EN + zh-TW + bug-report template), and aligned `ai-development-pitfalls.md` with the occupancy model + platform-neutral wording.

**Security & integrity**
- **CI security scanning (#20)**: Semgrep SAST + TruffleHog secret detection + pip-audit dependency audit, all tools pinned.
- **Audit-chain tamper-evidence hardening (#117, ADR-003)**: git append-only witness for tail-truncation detection + `migrate` fail-closed against re-blessing forged history.
- **Framework self-test integrity (#116)**: restored `tests/guard` collection and gated 82 governance-tool tests in CI.

**Tooling & reliability**
- validate.sh / validate.ps1: gate-injection hardening (#104), gate-progression repair (#110), inline-python hardening (#111), PS1↔SH parity backfill (#119), `--list-checks`, SSoT atomic writes, gate-receipt schema (#114).
- Downstream/install: cross-session path alignment for zero-Python downstream (#106), scaffold-tier sidecar preservation (#101), framework-ADR filename matching (#100), Windows `.cmd` install/update repair (#120).

**Docs**
- README/cross-doc links work in both GitHub and deployed contexts (#103); version banners + skill count (17→14) corrected (#102); framework-internal refs removed from downstream guidance (#99).

### Adversarial Governance Audit + Downstream UX Hardening (PR #104)

**Validator (validate.sh / validate.ps1) — gate-injection hardening:**
- T175–T247: 22 gate-injection scenarios closed — code-fence bypass, HTML-comment bypass, indented-receipt masking, unclosed-fence masking, multi-section masking, self-reclassification reset abuse (H4), receipts-in-fence diagnostic (T247)
- Validator maintained 80 PASS / 4 WARN / 0 FAIL throughout 20+ commits
- ACX phase shim check (`validate.sh`): guard fixed from `-d` (directory) to `-f` (file) — `.agent/skills/<name>` stubs are flat files; `-d` made the SKILL.md existence check dead code
- ACX phase shim check (`validate.sh`): CRLF line-ending strip added to frontmatter parser — frontmatter `---` delimiter failed to match on Windows checkouts with CRLF line endings
- ACX phase shim check (`validate.ps1`): `-PathType Container` → `-PathType Leaf` — same dead-code fix as validate.sh
- `routing.md §5` / `bootstrap.md §6`: stale "Runtime v5" version token corrected to "Runtime v1"

**Validator — M8 archive relative-link depth check:**
- `validate.sh` / `validate.ps1` M8: scan `archive/*.md` for relative links and WARN when target does not exist — catches depth-mismatch breakage from content copied out of `current_state.md` (depth 2) into `archive/` (depth 3)
- M8 link counter uses stdout read (not `sys.exit(count)`) to avoid mod-256 silent-PASS on ≥256 broken links
- `validate.sh` M8 parity-hardened: `try/except` file-read guard + `^\d+$` numeric pre-check (matches `validate.ps1`)
- `ship.md §2 State Update`: prose warning about relative-link depth hazard when archiving Ship History

**Validator — validate.ps1 loop-termination parity fix (T243/T245/T247):**
- `validate.ps1` T243/T245/T247 fail-closed branches used bare `exit 0` inside the `foreach ($wl in $worklogs)` loop — in PowerShell this terminates the entire script (not just the current iteration), silently skipping ~60 downstream checks and never printing a Summary line; Windows CI falsely reported exit 0 while `validate.sh` on Linux correctly reported exit 1
- Fix: replaced `exit 0` with `$gateProgressionIllegal++; continue` in all three branches — mirrors `validate.sh` behavior where `sys.exit(0)` exits only the Python subprocess and bash continues the outer loop

**test.md — no-test-runner fallback path:**
- `hotfix` moved to sign-off-required group (`engineering_guardrails.md §12.2 no-exceptions`)
- Gate 2 exception (5-Gate Contract) scoped to `quick-win`/`tiny-fix` only
- Fallback procedure step 5 tier-scoped: `quick-win`/`tiny-fix` write PASS; `feature`/`arch-change`/`hotfix` do not write PASS receipt when Gate 2 unsatisfied
- Step 6 tier-scoped: `quick-win`/`tiny-fix` → skip "Run all tests" and proceed to Step 4b; `feature`/`arch-change`/`hotfix` → step 5 terminal, do not proceed
- `quick-win`/`tiny-fix` fallback trigger now writes a Drift Log entry, satisfying Step 4b Gate 2 exception precondition from both paths

**bootstrap.md §3.7 — Next: field overflow fix:**
- Feature full-phase chain (`[/brainstorm →] /spec → ... → /ship`) removed from `Next:` field to prevent 8-line Response Budget breach; chain now recorded in Work Log `## Task Description` only

**`.codex/INSTALL.md` — bash dependency clarified:**
- Bash required on ALL platforms (Windows PS1 installer wraps bash internally)
- Git for Windows prerequisite explicit; PS1 commands include `-ExecutionPolicy Bypass`

## [1.1.2] - 2026-04-17

### Polish Batch 2: Governance Depth

**Installer UX (completes 1.1):**
- `deploy.sh` prints a Python-availability advisory at end-of-run — framework works without Python, but guarded SSoT writes fall back to direct writes (advisory locking disabled) when Python is missing, so multi-session users should install Python 3.8+

**Token Efficiency (completes 3.2 + 3.3):**
- `engineering_guardrails.md §Reading Mode` adds Loaded-Sections Receipt rule — `/bootstrap` echoes loaded §s to Work Log `## Session Info` so later phases can cite without re-reading
- `bootstrap.md` adds Reading Mode Table at top — at-a-glance per-classification index of which §s to read vs skip (saves re-scanning the 374-line file)
- `bootstrap.md §0` replaces inline prose with decision table (first-match-wins) — less cognitive load per classification

**Governance Depth (completes 2.3 + 4.3):**
- `engineering_guardrails.md §4.1` harmonizes "silent above 90%" with structured receipts — narrative-silent but plan/implement/ship compact blocks always include `Confidence:` field
- `implement.md` Pre-Execution Check adds per-step Confidence re-assessment — step-level auditability, not just plan-level
- `AGENTS.md §Read-Once Discipline` requires Drift Log receipt on Safety-Valve re-reads — creates auditable trail for the honor-system rule

## [1.1.1] - 2026-04-17

### Polish: Audit Findings

**Installer UX:**
- Broadened Git-bash detection via `Get-Command git` derivation — covers scoop, chocolatey, portable Git, and custom-prefix installs (installers/deploy_brain.ps1)
- Removed `--quiet` from `git clone` / `git pull` in bootstrap path so slow networks no longer look like a hang (installers/deploy_brain.sh)

**Governance Wiring:**
- `Confidence:` field added to `/plan` compact-block template — confidence gate (engineering_guardrails §4.1) now has an auditable receipt even when confidence is high
- Confidence Trace Audit advisory added to `/ship` pre-flight
- `AGENTS.md` No-Bypass rule clarified: bans skipping gates within a classification's documented phase list, does NOT override quick-win/hotfix fast-paths

**Token Discipline:**
- `CLAUDE.md` condensed 51→27 lines — removed duplicated Hard Rules section; Skills subsection reduced to pointer (AGENTS.md §Skill Safety already canonical)

**Discoverability:**
- `routing.md §3` header labels the skill activation table as the canonical skill index

## [1.1.0] - 2026-04-16

### Token Optimization & Governance Hardening

**Token Efficiency:**
- SKILL.md heading-scope optimization: phase-entry loads only essential sections (~15-22% skill token savings on heavy scenarios) (#57)
- Compressed phase outputs + Response Budget hard cap (≤8 lines prose) (#54)

**Governance Improvements:**
- Expert review quick-wins: rollback plan check in /ship, scope breach detection in /implement, ship-phase gate receipt audit, ADR auto-discovery in bootstrap (#56)
- File existence guards in validate.ps1 and validate.sh (#55)

**Deploy & Platform:**
- Deploy skill subdirs recursively and fix dry-run accuracy (#52)
- Correct migration guide path in bootstrap.md (#53)

## [1.0.0] - 2026-04-12

### Agentic OS v1.0 Public Release

First public release of Agentic OS as an open-source governance framework for AI coding agents.

**Core Framework:**
- Gate Engine with mandatory phase progression and handshake enforcement
- 5 task classifications: tiny-fix, quick-win, feature, hotfix, architecture-change
- Engineering guardrails constitution with OWASP Top 10 auto-scan
- Security guardrails with destructive command blocking
- Single Source of Truth (SSoT) state model with guarded writes

**Workflows & Commands:**
- 25 slash commands covering full development lifecycle
- Intent Router with 30+ bilingual (EN + zh-TW) intent mappings
- Phase-aware skill activation with deterministic rule table

**17 Professional Skills:**
- Test-Driven Development, Systematic Debugging, Red Team / Adversarial
- API Design, Auth Security, Database Design, Frontend Patterns
- Parallel Agent Dispatching, Subagent-Driven Development
- Writing Plans, Executing Plans, Requesting / Receiving Code Review
- Verification Before Completion, Git Worktrees, Finishing a Branch, Doc Lookup

**Multi-Platform Support:**
- Claude Code (CLAUDE.md auto-load)
- Google Antigravity (intent router + runtime)
- OpenAI Codex (platform guide + CLI delegation)
- Cursor, GitHub Copilot (AGENTS.md as project rules)

**Deploy System:**
- Manifest-based smart deploy with sha256 hash tracking
- Tier classification: core (always overwrite), scaffold (skip if modified), wrapper (skip if modified)
- Legacy path migration (automatic detection and recovery)
- Cross-platform installers (Bash, PowerShell, CMD)

**Token Efficiency:**
- Conditional governance loading by task classification
- Skill cache policy with metadata-first loading
- Phase summary compaction for low-token resume
