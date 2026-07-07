# Work Log: feat/skill-provenance

| Field | Value |
|---|---|
| Branch | feat/skill-provenance |
| Classification | quick-win (reclassified from feature 2026-06-19 — see Drift Log) |
| Classified by | Claude (Opus 4.8) |
| Frozen | true |
| Created Date | 2026-06-19 |
| Owner | KbWen |
| Guardrails Mode | Quick |
| Current Phase | ship |
| Checkpoint SHA | N/A (set by /implement before code changes; base HEAD b23699f) |
| Recommended Skills | see ## Recommended Skills |
| Primary Domain Snapshot | none (no spec yet declares primary_domain) |
| SSoT Sequence | 69 |

## Session Info
- Agent: Claude (Opus 4.8)
- Session: 2026-06-19T18:30:09+08:00
- Platform: Antigravity (Claude Code CLI)
- Guardrails loaded: §1, §2, §4 (incl. §4.1/§4.2/§4.4/§4.5), §7, §8.1, §10, §13 (Full core; read during initial feature classification). Reclassified to quick-win 2026-06-19 → Quick Mode henceforth (no re-read; ADR-006 + §13 constraints already identified). §5/§12 apply at /implement+/test.
- Override: none (no root or ~/.agentcortex AGENTS.override.md)
- Downstream-Capabilities: none (no downstream-capabilities.yaml)
- User-Preferences: none (no user-preferences.yaml)

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- ADR coverage: validate.sh + a hypothetical skill_provenance.py covered by ADR-006 (validator-strangler). The metadata-format/inventory CONVENTION itself has no covering ADR — node-15 does NOT mandate a new ADR for G1; decision deferred to /spec (lean: no new ADR, follow ADR-006 + existing .agentcortex/metadata conventions).
- 2026-06-19 read-only DIAGNOSIS (user directive: consult experts, ground in project philosophy, challenge assumptions, answer "which item optimizes skill/workflow CONTENT?"). 3 read-only experts (Plan right-sizing / Explore categorization / Explore philosophy). Load-bearing claims VERIFIED against primary sources before accepting (per anti-rationalization §4.5 + audit-verification lesson):
  - VERIFIED node-07:5-6/14-16/119-121 — Karpathy source owner `forrestchang/` redirects to canonical `multica-ai/andrej-karpathy-skills`; source declares MIT (README/frontmatter/plugin) but has NO root LICENSE/COPYING/NOTICE file + GitHub detects no license (node-07:18-22). #82 = update owner→multica-ai + qualify `(MIT)`→"declared MIT, repo license artifact missing" on SKILL.md:139. (addyosmani line 140 per node-09:12 has root MIT — likely leave or apply consistent framing; minor scope note.)
  - VERIFIED skill-ecosystem.md is status:living STRATEGIC direction (Near/Mid/Longer Term, a *planned* platform; provenance is a FUTURE field line 60) — NOT a present consumer of provenance data.
  - VERIFIED 14 first-party skills (.agents/skills/*/SKILL.md), zero installed/external; only karpathy(139-140) + doc-lookup(164) carry external attribution.
  - FINDING: #81 at FEATURE scale fails the project's own "proof-before-process" + "enforcement-audit" tests (digest validator guarding nothing = verifier-without-defense theatre; exception-schema with zero instances = YAGNI). Same pattern as #76 (capsule→note). Minimal honest form = ONE static provenance manifest (14 rows, license-status:asserted) + a T1 completeness check (rows == skill dirs), foldable into #80 (same validate.sh:465-487 loop). DROP digests/file-manifest/exception-schema → those ARE G2 (existing reopen-trigger, _product-backlog.md:55).
  - FINDING (point 4, verified): among #77-82, ONLY #82 edits skill *text* (attribution lines only = hygiene); #81 = meta/governance infra; #80 = structural-quality gate. NO hidden substantive content-optimization track was dropped — deep-compares concluded our skill/workflow CONTENT is already sound (node-07:103/135). 
  - RESOLVED 2026-06-19: user approved Option A. RECLASSIFIED feature→quick-win (governance rollback CLASSIFIED→re-gate at quick-win; downward, explicit, evidenced — NOT a silent downgrade). Scope = #80 (G1a compat floor) + #81-light (static provenance manifest + completeness check) + #82 (Karpathy wording). Heavy half of #81 (digest/file-manifest/byte-verify/exception-schema) deferred to G2 reopen-trigger. /review + /test WILL run despite quick-win (validate.* governance-critical). Follow-up research line (skill/workflow content-optimization + reference-repo comparison) registered as backlog #83, queued AFTER this branch ships (user: "做完後").
- 2026-06-19 PLAN ADVERSARIAL REVIEW (fresh-context expert, user-requested "專家確認"): 3 real defects, ALL verified against files before accepting (per [audit-verification] discipline):
  - D2 SHIP-BLOCKER (verified api-design:1, doc-lookup:1): 5 of 14 `.agents/skills/*/SKILL.md` are SCAFFOLD files (HTML-comment header, NO `---` frontmatter): api-design, auth-security, database-design, doc-lookup, frontend-patterns. Their name/description live in the FLAT `.agent/skills/<name>` stubs (already checked by validate_trigger_metadata.py @ validate.sh:336). FIX: #80 check applies ONLY to SKILL.md that HAVE frontmatter (the 9 detailed skills — all currently PASS name+desc+name==dir); scaffold files EXEMPT. Avoids editing 5 ADR-005-governed scaffold files (scope creep + red build averted).
  - D1 (verified check_lifecycle_frontmatter.py:31-33): repo has no hard PyYAML dep — `_yaml_loader.load_data` is the authoritative loader. FIX: check_skill_provenance.py parses skill-provenance.yaml via `from _yaml_loader import load_data` (NOT `import yaml`), strict allowlist on the returned dict.
  - D3 (verified deploy.sh:904-907): metadata/ deploy loop ships ONLY trigger-registry.yaml + trigger-compact-index.json → skill-provenance.yaml does NOT deploy; a fixed 14-row completeness check would FALSE-FAIL downstream forks (customized skill sets). FIX: SOURCE-REPO-ONLY — skip(return 0) when `.agentcortex-manifest` present (downstream), INVERSE of check_command_sync.py:55-58. No deploy.sh change.
  - doc-lookup RESOLVED: scaffold (no frontmatter) AND has addyosmani enrichment @ :164 — both prior experts correct. Manifest origin: doc-lookup=first-party(scaffold, addyosmani-enriched); karpathy=adapted(multica-ai).
  - Net: fixes REDUCE scope (no scaffold edits, no deploy change) — stays quick-win, 6 files. Reviewer CONFIRMED ADR-006 no-native-baseline-bump claim + #82 internal consistency. Post-review Confidence ~92%. Out-of-scope follow-up noted: spec skill-research-integration.md:130 still says 'forrestchang' (stale — NOT in #82).

## Task Description
Bundle on branch `feat/skill-provenance` (user directive "做 #81 + #82 同分支"):
- **#80 / GH #255** (PULLED IN per Option A) — G1a SKILL.md compatibility floor [CORRECTED post-review]: a Python validator (ADR-006) checking, for each `.agents/skills/*/SKILL.md` THAT HAS `---` frontmatter (the 9 detailed skills), that `name`+`description` are present and `name`==dir. SCAFFOLD-comment files (api-design/auth-security/database-design/doc-lookup/frontend-patterns — metadata in flat `.agent/skills/<name>` stubs, already checked by validate_trigger_metadata.py) are EXEMPT. SCOPED OUT: trigger-example validation; /app-init alignment; editing scaffold files.
- **#81 / GH #256** — Activated-skill provenance inventory, RIGHT-SIZED (feature→quick-win) [CORRECTED post-review]: static manifest `.agentcortex/metadata/skill-provenance.yaml` (one row per skill: origin first-party|adapted, source+pinned-rev, license, license-status:asserted). Validator parses via `_yaml_loader.load_data` (NOT `import yaml` — repo no-PyYAML doctrine), then strict allowlist: one row per skill dir, no orphans, license-status∈{asserted} fail-closed. SOURCE-REPO-ONLY: skip(return 0) when `.agentcortex-manifest` present (downstream — manifest doesn't deploy, forks customize skills). DROPPED → G2 (reopen-trigger, _product-backlog.md:55): content digests, per-skill file manifest, byte/remote verification, security-exception schema. No present consumer (0 external skills; skill-ecosystem.md aspirational).
- **#82 / GH #257** — Karpathy source/license wording. Edit `.agents/skills/karpathy-principles/SKILL.md:139`: owner `forrestchang`→canonical `multica-ai` (VERIFIED node-07:14-16,119-121); qualify `(MIT)`→"MIT declared upstream, no root LICENSE artifact" (VERIFIED node-07:18-22). The concrete `asserted`-status instance of the #81 manifest. (addyosmani line 140 / doc-lookup:164 have root MIT per node-09:12 — optional consistent framing, not required.)

**Classification = quick-win** (reclassified from feature per 2026-06-19 right-sizing analysis + user approval of Option A). Delivers the "SKILL.md compatibility + provenance floor" as ONE quick-win on this branch. No spec required (quick-win); skill-ecosystem.md (Domain Doc) is strategic context, not authority. /review + /test WILL run (governance-critical validate.* surface). Heavy half deferred to G2. Surfaced by the 2026-06-19 external skill/workflow-practices research (node-15 §3 track "G" + Packet 5/6).

### Context Read Receipt
- current_state.md → read (Last Updated 2026-06-19; Update Sequence 69; Last Verified 2026-06-19)
- Work Log → created (new, this session)
- Spec Scope → none mapped (no existing spec covers #81/#82; #81 spec to be created at /spec)
- GH issues #256, #257 → read (both OPEN, recording-phase only)
- Backlog rows #81 (feature/skills/P2), #82 (tiny-fix/docs/P3) → read; advanced Pending → In Progress this session
- Research note → `.agentcortex/context/private/codex-research-main/` (resumable; node-15 synthesis + node-09 source manifest read for scope grounding)

### Read Plan
- Classification: feature | Guardrails Mode: Full
- Read: bootstrap.md, engineering_guardrails.md (Full core), state_machine.md, current_state.md, _product-backlog.md (inventory), GH #256/#257, karpathy-principles/SKILL.md, node-15, node-09, skill_conflict_matrix.md
- Skipped (with reason): shipped specs in Spec Index (historical, AC-28); other research nodes 00-08/10-14/16 (not needed for bootstrap scope — read at /spec/research if right-sizing requires); engineering_guardrails §5/§12 (load at /implement+/test); §13 (load at /implement)
- Phase chain (feature, no frozen spec): [/brainstorm →] /spec → /plan → /implement → /review → /test → /handoff → /ship

## Phase Sequence
- bootstrap
- plan (entered 2026-06-19; reclassified to quick-win on entry)

## External References
- ADR-006 (validator Python-core strangler) — governs any new validator check for #81 (Python tool behind run_python_check/Invoke-PythonCheck; native additions only via justified baseline bump). applies_to: validate.sh, validate.ps1, tools/*.py
- node-15 final synthesis (`.agentcortex/context/private/codex-research-main/node-15-final-calibrated-synthesis.md`) §3 "P1/P2 — G" (G1 actionable bullets = #81 acceptance), §3 Lower Priority + Packet 6 (#82), §5 Rejected Directions, §6 Packet 5 (#80/#81 split)
- node-09 source manifest (`.../node-09-remaining-source-manifest.md`) — license-provenance evidence (MIT-with-conflicts; asserted-vs-reviewed basis for #82 and #81 taxonomy)
- GH #256 (#81), GH #257 (#82); backlog #81/#82 (`docs/specs/_product-backlog.md`)
- #80 (GH #255) is now MERGED into this branch (not a separate sibling) per Option A — it IS the compatibility-floor half of this quick-win.
- node-07 (`.agentcortex/context/private/codex-research-main/node-07-karpathy-guidelines-deep-compare.md`) — #82 evidence: owner→multica-ai (:14-16,119-121); license declared-MIT-no-artifact (:18-22).
- Implementation refs (ADR-006 Python-tool path): validate.sh:319 `run_python_check` pattern + :465-487 existing skill-existence loop; validate.ps1 `Invoke-PythonCheck` twin; existing `.agentcortex/tools/check_*.py` (check_command_sync / check_lifecycle_frontmatter) as the `check_skill_provenance.py` template; `.agentcortex/metadata/trigger-registry.yaml` as YAML-manifest style reference.

## Known Risk
- **Evidence-before-adding / YAGNI scrutiny on #81 (HIGH priority for /spec)**: #81 proposes provenance INFRASTRUCTURE (metadata format + per-skill digests/manifests + validators + security-exception schema). The same 2026-06-19 research pass surfaced #76 (Research Capsule), which was deliberately REDUCED from heavy infra (ADR-009 + spec) to a lightweight note because external prior art treats research-state persistence as lightweight "structured note-taking". #81 must get the same scrutiny: is full inventory infra proportionate to the evidence/consumer in THIS repo, or does a lighter provenance-note form suffice? Right-size at /brainstorm or /spec; reclassify downward if the lighter form is chosen.
- **G2 non-goal boundary (must hold)**: node-15 §3 G2 + §5 — #81 MUST NOT include remote installation, downloaded-byte verification, or rehash-cached-packages. Those are a separate, conditionally-approved external-installation capability. Issue scope guard confirms. Catalog inclusion / stars / "official" labels are discovery evidence only, not provenance.
- **Bundling tradeoff**: #82 (trivial doc edit, independently shippable) is bundled into a feature branch, so it inherits the full feature gate chain (spec/review/test/handoff). Accepted per user "同分支" directive; thematically unified (both provenance/license hygiene). Split remains available if cleaner PR scope is preferred.
- **karpathy-principles is both a recommended skill AND the #82 edit target** — editing its attribution/References does not change its behavioral content (When-to-Apply / principles / checklists unchanged); skill remains loadable.

## Risks
- R1 (size-vs-tier): bundle = 6 files (#80+#81+#82). Mostly additive (new tool/tests/manifest). If /implement diff exceeds ~200 NON-additive lines OR >2 modules → reverse-transition to CLASSIFIED + escalate (state_machine §Scope Escalation). Mitigation: keep #80 checks minimal (name+description+name/path only); no trigger-example / `/app-init` work.
- R2 (existing-skill conformance): the new frontmatter + name/path check may FAIL on a pre-existing non-conformant SKILL.md. Mitigation: at implement, FIRST run the check read-only against all 14 skills; fix any non-conformant frontmatter (in-scope) OR record as a finding before wiring the check to FAIL.
- R3 (cross-platform parity): one Python tool keeps sh↔ps1 logic identical, but the WIRING (validate.sh + validate.ps1) MUST be verified by RUNNING BOTH (per [cross-platform-cli] lesson — reading is insufficient). Do NOT run validate.ps1 in parallel with other calls on Windows ([process-batching] lesson).
- R4 (ADR-006): new check MUST go via run_python_check/Invoke-PythonCheck (not native bash/PS) → native-baseline ratchet (validator_native_baseline.json) stays unchanged.
- Rollback: revert PR. All deliverables additive (new tool + manifest + tests + 2 small wiring edits + 1 doc-line fix); revert removes the check and restores prior validate behavior. No data migration.

## Conflict Resolution
none (recommended skill set has no partial-conflict/conflict pairs per skill_conflict_matrix.md; karpathy-principles × verification-before-completion = compatible; dispatching-parallel-agents combos not recommended)

## Skill Notes
- If /implement later decomposes #81 into 3+ low-coupling independent subtasks, `dispatching-parallel-agents` becomes eligible — note its partial-conflict with `test-driven-development` (TDD on critical path; parallel dispatch limited to isolated subproblems) at that point.
- `systematic-debugging` is on standby — activates if any bug/error/unexpected behavior is encountered.

## Recommended Skills
(Reclassified feature→quick-win 2026-06-19 — Quick Mode skill set.)
- karpathy-principles (auto) — plan/implement/review; behavioral baseline (applies to quick-win). NOTE: also the #82 edit target.
- verification-before-completion (auto) — implement/ship; any completion claim.
- systematic-debugging (auto, standby) — implement/review/test; on any bug/error.
- (auto-skipped for quick-win: red-team-adversarial, test-driven-development, subagent-driven-development, production-readiness — these trigger only at feature+.) HOWEVER: tests still REQUIRED (§5.1 — new validator tool needs ≥1 test before ship), and /review + /test WILL run with an INDEPENDENT fresh-context reviewer because validate.sh/.ps1 are governance-critical surfaces (project ships validator quick-wins with review per Ship History).

## Phase Summary
- bootstrap: classified as feature (combined #81 feature + #82 maintenance, highest tier wins); context loaded (SSoT, guardrails Full core, state machine, backlog inventory, GH #256/#257, research node-15/09, karpathy SKILL.md); 7 skills recommended (no conflicts); resumable research note surfaced; ADR coverage = ADR-006 (validator surface), new-convention ADR deferred to /spec; backlog #81/#82 advanced Pending → In Progress; branch feat/skill-provenance created; lock acquired. [RECLASSIFIED → quick-win after expert diagnosis; see Drift Log.]
- plan: quick-win delivering #80 + #81-light + #82 ("SKILL.md compatibility + provenance floor"); 6 target files (new Python validator + YAML manifest + tests, 2 validator-wiring edits, 1 SKILL.md fix); ADR-006 Python-tool path (sh↔ps1 parity, no native-baseline bump); heavy half→G2. Mode Normal. | Confidence: 85% — additive validator unit; re-tier if implement churn >200 non-additive lines or >2 modules.
- implement: built check_skill_provenance.py (source-repo gate + _yaml_loader parse + strict allowlist + frontmatter floor) + skill-provenance.yaml (14 rows) + tests (16); wired both validators; #82 on SKILL.md:139 + spec:130; regenerated trigger-compact-index.json (karpathy hash, #82 companion — caught by metadata-deep FAIL, fixed). 8 files, ~all additive. Stayed quick-win (no >200 non-additive churn). | Confidence: 92% — post-review, all unknowns (PyYAML/scaffold/downstream) resolved.
- review: independent fresh-context acx-reviewer → READY (5/5 ACs proven, file:line); 2 LOW theoretical findings hardened (BOM utf-8-sig + quoted-scalar dequote) + 2 guard tests added.
- test: 16 tests pass; validate.sh ↔ validate.ps1 parity (pass=105 fail=2, the 2 = gitignored work-logs, CI fail=0).
- ship: quick-win; PR + merge-on-CI per user. | Confidence: 95% — high.

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T18:30:09+08:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T18:30:09+08:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T19:10:00+08:00
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T19:10:00+08:00
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T19:10:00+08:00
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T19:10:00+08:00

## Evidence
- Files (8): NEW `.agentcortex/tools/check_skill_provenance.py`, `.agentcortex/metadata/skill-provenance.yaml`, `tests/ci/test_skill_provenance.py`; MODIFIED `.agentcortex/bin/validate.sh`, `.agentcortex/bin/validate.ps1`, `.agents/skills/karpathy-principles/SKILL.md` (#82), `docs/specs/skill-research-integration.md` (#82), `.agentcortex/metadata/trigger-compact-index.json` (karpathy content_hash regen — #82's required companion; 1-line diff d29dde6d→d599b962).
- Tests: `tests/ci/test_skill_provenance.py` — **16 passed** (happy + each #80/#81 fail mode + scaffold exemption + source-repo gate + no-PyYAML subset parser + BOM/quoted-scalar robustness). Mutation-sense: each fail-mode test reds if its check is removed.
- Validators: validate.sh AND validate.ps1 both **pass=105 warn=9 fail=2 skip=2** (PARITY, ran both). `[PASS] skill provenance + compatibility floor` on both; `[PASS] metadata deep validation` + `[PASS] compact index freshness` after regen. The 2 FAILs are gitignored work-log hygiene (codex-research-main.md illegal `bootstrap->bootstrap` progression + compaction; feat-skill-provenance.md compaction) — CI-invisible (work/ gitignored → CI fail=0). No native-baseline bump (ADR-006; SKIP is wrapper-internal).
- #82 verified vs node-07:5-22/119-121 — owner forrestchang→multica-ai (canonical GitHub redirect), license "MIT declared upstream; no root LICENSE artifact". Applied to SKILL.md:139 + spec:130; karpathy skill behavior unchanged (frontmatter intact, still passes the floor).
- Review: independent fresh-context acx-reviewer → READY (5/5 ACs proven w/ file:line); 2 LOW theoretical findings (BOM, quoted frontmatter) HARDENED (utf-8-sig + dequote) + guarded by 2 added tests.
- Rollback: revert PR (all additive — new tool/manifest/tests + 2 validator wirings + 2 one-line doc fixes + 1 generated-index regen). No data migration.
