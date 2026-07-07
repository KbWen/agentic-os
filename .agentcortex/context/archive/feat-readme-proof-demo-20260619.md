# Work Log: feat/readme-proof-demo

| Field | Value |
|---|---|
| Branch | feat/readme-proof-demo |
| Classification | quick-win |
| Classified by | Claude (Opus 4.8) |
| Frozen | true |
| Created Date | 2026-06-19 |
| Owner | KbWen |
| Guardrails Mode | Quick |
| Current Phase | ship |
| Checkpoint SHA | a29c000 (base) |
| Recommended Skills | karpathy-principles (auto), verification-before-completion (auto) |
| Primary Domain Snapshot | none |
| SSoT Sequence | 70 |

## Session Info
- Agent: Claude (Opus 4.8)
- Session: 2026-06-19T20:30:00+08:00
- Platform: Antigravity (Claude Code CLI)
- Guardrails loaded: Quick (AGENTS.md core)
- Override: none · Downstream-Capabilities: none · User-Preferences: none

## Drift Log
- Skip Attempt: NO
- Gate Fail Reason: N/A
- Token Leak: NO
- Origin: product-strategy pivot (see `.agentcortex/context/private/research-skill-content-optimization.md`). #83 closed as "skills sound"; goal = external ADOPTION; GitHub data showed strong search-discovery (575 unique cloners/14d, Google-driven) but weak conversion (20 stars, 1 watcher, 0 external issues) → bottleneck = conversion, not discovery. User wants USE not community (no Discussions/telemetry). Highest-leverage no-overhead lever = a proof asset converting the ~964 README-landers.
- README canary `'governance-first layer for AI coding agents'` (validate.sh:981 / validate.ps1:936) PRESERVED — verified `grep -c` = 1 after every edit.
- 2026-06-19 ROUNDTABLE (3 fresh-context experts, assume-failure angle, per owner directive): found 4 real issues, ALL fixed pre-merge:
  - (skeptic/philosophy) "Rules vs. enforcement" table Row 3 claimed `pre-commit + CI` but work-logs are gitignored → CI-invisible (validate.sh:1035 self-documents it) = the exact honor-system overclaim the project forbids. FIXED → Row 3 = `pre-commit (local)`; Row 1 (credential) correctly = `pre-commit hook + CI` (it has both); softened the Features-line overclaim (L58) to "local pre-commit validator." Honesty boundary now defensible.
  - (correctness) D1: `demo/run.ps1` was untracked but README pointed Windows users at it → would ship a broken promise. FIXED → run.ps1 added to the commit (tested on pwsh 7.5, exit 0, identical narrative, no flaggable secret). D2: README demo block wasn't verbatim (missing the scanner's "Rotate..." line + abridged close) → FIXED to exact output. D3 (em-dash sh vs hyphen ps1) accepted (PS console encoding safety).
  - (design) base64 `for-the-badge` blueviolet banner = #1 AI-slop tell → REPLACED with an auto-tracking flat-square linked release badge (`github/v/release`). NOTE: README version badge now auto-tracks — release-cuts NO LONGER need to bump it (one fewer manual banner; net improvement). De-duped the "X, not Y" rhetorical tic (kept 2, neutralized 2).
- Verified post-fix: canary grep=1, rainbow fill grep=0, for-the-badge grep=0, scan_credentials on README+run.sh+run.ps1 exit 0 (no flaggable secret in the PR diff → CI credential-scan green).

## Task Description
Proof-first, de-slopped README hero + a reproducible demo, to convert the search-driven README traffic into users (goal: adoption; no community overhead).
- NEW `demo/run.sh`: runs the REAL credential scanner (`scan_credentials.py`) against a runtime-generated fake AWS key → shows it BLOCKED + redacted. Reproducible ("run the red on your machine" = the moat). No literal secret stored; temp dir; cleans up; exit 0.
- README hero: honest claim ("agent can still cut a corner; the ones that burn you get caught by machine checks, not self-report"), real demo terminal block, `bash demo/run.sh`, a "Rules vs. enforcement" table (machine-enforced vs honor-system honesty). Killed: rainbow Mermaid ×2 (per-node hex), "The Problem/The Solution" template, emoji bullets, "14 professional skills" hype, and the OVERCLAIM "The AI cannot skip ahead" (false + skeptic-bait). Kept: version badge, canary phrase, CI/Security/MIT badges + links, Classification/Guardrails/Skills reference tables.

## Phase Sequence
- bootstrap, plan, implement, ship (quick-win)

## External References
- `.agentcortex/context/private/research-skill-content-optimization.md` — the product-strategy arc (close #83 → adoption/proof pivot → this asset).
- Editorial expert slop-audit + human-voice rewrite (fresh-context); honest-framing constraint (machine-enforced vs honor-system) supplied + honored.
- scan_credentials.py (#225) — the real machine control the demo exercises.

## Known Risk
- README is the public face: applied on a branch + PR for owner review/merge (not unilateral). Rollback = revert PR (README prose + 1 new demo file; fully additive/reversible).
- demo/run.sh is POSIX sh; CI ShellCheck lints it (verified careful locally; shellcheck not installed locally). A `.ps1` parity twin is a possible follow-up (Windows users).
- Honesty boundary: the demo shows ONE machine-true control (credential block); the hero does NOT overclaim "can't lie" — it claims "the failures that burn you are machine-caught," which is true.

## Conflict Resolution
none

## Skill Notes
none

## Recommended Skills
- karpathy-principles (auto) — surgical edits, no scope creep (kept reference body intact).
- verification-before-completion (auto) — demo tested (exit 0); canary + no-rainbow verified before ship.

## Phase Summary
- bootstrap: quick-win (README hero + demo); origin = adoption-proof pivot from the #83 research.
- plan: 2 files (NEW demo/run.sh, MODIFY README.md hero); preserve canary + version badge; de-slop per editorial audit; honest framing. | Confidence: 90% — public-face edit, gated on owner PR review.
- implement: demo/run.sh built + TESTED (real scanner blocks runtime-fake key, redacted, exit 0); README hero de-slopped (canary grep=1, rainbow fill grep=0, overclaim fixed). 
- ship: PR for owner merge on green CI.

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T20:30:00+08:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T20:30:00+08:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T20:30:00+08:00
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T20:30:00+08:00

## Evidence
- Files (2): NEW `demo/run.sh` (reproducible credential-block proof; runtime-generated key; redacted; exit 0 — tested), MODIFY `README.md` (hero de-slop).
- Demo run: `bash demo/run.sh` → real `scan_credentials.py` flags `config.env:2: aws-access-key-id` (value redacted), prints "Commit BLOCKED", exit 0. Verified.
- README: canary `'governance-first layer for AI coding agents'` present (grep -c = 1); rainbow `fill:#` count = 0 (both Mermaids de-rainbowed; first replaced by the demo terminal); overclaim "The AI cannot skip ahead" removed; version badge + CI/Security/MIT badges + links + reference tables intact.
- Rollback: revert PR (additive demo file + README prose; no logic, no data).
