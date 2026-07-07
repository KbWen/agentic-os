# Work Log: fix/copilot-instructions-deploy

| Field | Value |
|---|---|
| Branch | fix/copilot-instructions-deploy |
| Classification | quick-win |
| Classified by | Claude (Opus 4.8) |
| Frozen | true |
| Created Date | 2026-06-20 |
| Owner | luvseldom (session 2026-06-20T13:22:27+0800) |
| Guardrails Mode | Quick |
| Current Phase | plan |
| Checkpoint SHA | 2b34ca3 |
| Recommended Skills | verification-before-completion (auto) |
| Primary Domain Snapshot | none |

## Session Info
- Agent: Claude (Opus 4.8)
- Session: 2026-06-20T13:22:27+0800
- Platform: Antigravity
- Guardrails loaded: skipped (quick-win); workflows loaded earlier this session (Read-Once)
- Override: none
- Downstream-Capabilities: none

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Note: cross-platform entry-point diagnosis (read-only) surfaced this gap; see current_state.md PR #263 ship + the diagnosis. Mirrors the prior "GEMINI.md never deployed (HIGH)" fix.

## Task Description
- Cross-platform diagnosis finding: repo has `.github/copilot-instructions.md` (Copilot's repo-wide entry, points at AGENTS.md) but `deploy_brain.sh` does NOT ship it → downstream Copilot IDE custom-instructions surface has no governance entry. AGENTS.md (deployed) only covers the Copilot coding-agent surface (which reads AGENTS.md per GitHub 2025-08 changelog). Fix = deploy ships `.github/copilot-instructions.md` (scaffold tier, preserve adopter's own) + a real-subprocess deploy test. Mirrors test_gemini_md_is_deployed / the GEMINI.md deploy fix.
- Phase chain (quick-win): plan → implement → review → test → ship (doing focused review + real deploy test given downstream impact).

## Phase Sequence
- bootstrap
- plan
- implement
- review
- test
- ship

## External References
- GitHub changelog 2025-08-28: Copilot coding agent supports AGENTS.md (so AGENTS.md gives partial downstream Copilot coverage). https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/
- GitHub Docs: repository custom instructions = `.github/copilot-instructions.md` (the IDE-surface entry not covered by AGENTS.md). https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot
- Precedent: Ship-fix-downstream-sim-findings (GEMINI.md never deployed, HIGH) — same class; mirror its fix + test.

## Known Risk
- R1 (overwrite adopter's own copilot-instructions.md): use scaffold tier (preserve → .acx-incoming), NOT core. Mitigation: add path to BOTH get_tier + _get_tier_inline as scaffold.
- R2 (dry-run preview drift): the --dry-run file list (deploy.sh ~736-752) must also include the new file so preview matches actual. Mitigation: add to both the deploy_file call AND the dry-run loop.
- R3 (deploy.ps1 parity): deploy.ps1 is a pure bash launcher (Resolve-BashLauncher; 0 deploy_file refs) → no ps1 edit needed. Verified.
- Rollback: revert PR (additive deploy entry + test).

## Conflict Resolution
none

## Skill Notes
- verification-before-completion: real-subprocess deploy test + validate as evidence.

## Recommended Skills
- verification-before-completion (auto) — implement, ship

## Phase Summary
- bootstrap: classified quick-win (cross-platform diagnosis finding: Copilot entry not deployed). Branch fix/copilot-instructions-deploy off main 2b34ca3.
- plan: 2 files — deploy.sh (get_tier + _get_tier_inline + dry-run list + deploy block: add .github/copilot-instructions.md scaffold) + tests/ci/test_deploy_tiering.py (add test_copilot_instructions_is_deployed mirroring gemini). deploy.ps1 wrapper (no change). Mirrors proven GEMINI.md fix. | Confidence: 95% — high
- implement: deploy.sh 4 edits (get_tier + _get_tier_inline + dry-run list + .github deploy block, all scaffold-tier .github/copilot-instructions.md) + test_copilot_instructions_is_deployed. deploy.ps1 unchanged (pure bash launcher, verified). | Confidence: 96% — high
- review: PASS — self-review + real-subprocess deploy test (proportionate: exact mirror of the proven GEMINI.md pattern). Scaffold tier preserves an adopter's own copilot-instructions.md; no ps1 parity needed; 0 findings. | Confidence: 96% — high
- test: PASS — bash -n deploy.sh OK; test_copilot_instructions_is_deployed + test_gemini_md_is_deployed → 2 passed (134s); new test runs real deploy into temp dir, asserts file + manifest entry. | Confidence: 97% — high
- ship: PASS — gate PASS; Ship History prepended + Update Sequence 73→74 + Last Updated; deploy fix + test committed; PR pending (backfilled in end-of-batch chore). Work-log archival + INDEX.jsonl deferred to the batched chore(archive) after all 4 items merge. | Confidence: 96% — high

⚡ ACX

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T13:22:27+0800
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T13:22:27+0800
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T13:28:40+0800
- Gate: review | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T13:28:40+0800
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T13:28:40+0800
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-20T13:34:06+0800

## Evidence
- Files: .agentcortex/bin/deploy.sh (get_tier + _get_tier_inline + dry-run list + .github deploy block → .github/copilot-instructions.md scaffold), tests/ci/test_deploy_tiering.py (+test_copilot_instructions_is_deployed). deploy.ps1 unchanged (pure bash launcher).
- Test: `pytest test_copilot_instructions_is_deployed test_gemini_md_is_deployed` → 2 passed (134s); the new test runs real deploy.sh into a temp dir + asserts `.github/copilot-instructions.md` is a file AND in the manifest. bash -n deploy.sh OK.
- validate.sh: pass=105 warn=9 fail=2 skip=2 — the 2 FAILs are pre-existing gitignored work-log hygiene (compaction + codex-research-main.md illegal progression), CI fail=0; NOT caused by this change (deploy.sh + test only).
- Rollback: revert PR (additive deploy entry + test; scaffold tier → never overwrites an adopter's own file).
