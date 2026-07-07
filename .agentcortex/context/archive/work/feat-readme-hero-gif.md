# Work Log: feat/readme-hero-gif

| Field | Value |
|---|---|
| Branch | feat/readme-hero-gif |
| Classification | quick-win |
| Classified by | Claude (Opus 4.8) |
| Frozen | true |
| Created Date | 2026-06-19 |
| Owner | KbWen |
| Guardrails Mode | Quick |
| Current Phase | ship |
| Checkpoint SHA | 5a4422c (base) |
| Recommended Skills | karpathy-principles, verification-before-completion |
| Primary Domain Snapshot | none |
| SSoT Sequence | 70 |

## Session Info
- Agent: Claude (Opus 4.8) · Platform: Antigravity (Claude Code CLI) · Guardrails: Quick
- Override: none · Downstream-Capabilities: none

## Drift Log
- Skip Attempt: NO · Gate Fail Reason: N/A · Token Leak: NO
- Origin: user feedback on PR #260's README — "first impression unattractive, too dense; want imagery/GIF; THAT is the hero." Correct: a text-block hero is not visual. This adds the real GIF the original product expert recommended.
- README canary `'governance-first layer for AI coding agents'` PRESERVED (grep=1; it lives in the tagline, untouched). Tooling: no vhs/agg/asciinema/svg-term; HAVE Pillow 12 + ImageMagick → rendered the GIF with Pillow (authentic terminal cast, not a designed infographic; visually QA'd via the final-frame PNG; fixed a ✗→× glyph tofu in Consolas).

## Task Description
Make the README hero a VISUAL (animated GIF) instead of a dense terminal text block (user directive: human/attractive, not AI-feel, not over-quirky).
- NEW `docs/assets/hero-demo.gif` (760x446, 7 frames, 79KB): authentic dark terminal cast of `demo/run.sh` — agent leaks an AWS key + says "Done", credential gate detects (red), `× BLOCKED`. Reveal animation, loops.
- NEW `demo/render_hero_gif.py`: the Pillow render source (so the GIF is reproducible/auditable, not a faked asset; needs Pillow to regenerate — noted in its header). Not a framework runtime dep.
- README "See it catch a cut corner": GIF is now the hero; run-command (`bash demo/run.sh` / `pwsh demo/run.ps1`) prominent; the verbatim terminal output moved into a `<details>` (kept for honesty/SEO, no longer a wall). Honest caption: "the real scan_credentials.py gate, not a mockup."

## Phase Sequence
- bootstrap, plan, implement, ship (quick-win)

## External References
- Origin: PR #260 + the product-strategy arc (`.agentcortex/context/private/research-skill-content-optimization.md`).
- scan_credentials.py (#225) — the real control the GIF + demo exercise.

## Known Risk
- Public face: applied on a branch + PR (revert = restore the text-block hero; fully additive — a GIF, a render script, a README section swap). The GIF is a stylized depiction; the exact output stays in `<details>` + `bash demo/run.sh` reproduces the real thing.
- GIF is committed binary (~79KB) — small; render script makes it reproducible.

## Conflict Resolution
none

## Skill Notes
none

## Recommended Skills
- karpathy-principles (auto) · verification-before-completion (auto)

## Phase Summary
- bootstrap: quick-win (README visual hero) from user feedback that the text hero was too dense.
- plan: GIF hero + reproduce-command + collapse verbatim into <details>; render via Pillow (only tool available); preserve canary. | Confidence: 88% — public face, gated on owner view (GIF aesthetic is subjective; revert-easy).
- implement: rendered docs/assets/hero-demo.gif (Pillow, QA'd visually, glyph fix); README restructured; canary grep=1; scan exit 0.
- ship: PR → merge on green CI (standing owner delegation "完整推進+合併").

## Gate Evidence
- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T21:30:00+08:00
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T21:30:00+08:00
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T21:30:00+08:00
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-06-19T21:30:00+08:00

## Evidence
- Files (3): NEW docs/assets/hero-demo.gif (760x446, 79KB, rendered), NEW demo/render_hero_gif.py (Pillow source), MODIFY README.md (GIF hero + <details>).
- GIF QA: final frame inspected visually — clean authentic terminal (dark, monospace, traffic dots, green prompts, yellow redacted key, red CREDENTIAL DETECTED, red `× BLOCKED`), no tofu after ✗→× fix, reads at a glance.
- README: canary grep=1; `scan_credentials.py README.md demo/* ` exit 0 (no flaggable secret — AKIA**** redacted, keys runtime-built). GIF referenced via relative path.
- Rollback: revert PR (restores the text-block hero; additive only).
- 2026-06-20 SCOPE EXPANDED (owner feedback: "too much trivia, no visual up top, no focus" + "bring more repo-promotion people to review"): the GIF-only swap wasn't enough. 3 fresh-context promotion experts (devrel/conversion · 10k-star OSS maintainer · Show-HN/shareability) CONVERGED: it's an ordering+boundary problem — the GIF was buried below badges+divider+header (screen 2), and ~506 lines of internal spec (14-skill table, classification, SSoT tree, multi-agent, install matrix, architecture, 10 principles, double doc tables) read as "over-engineered cosplay" for a 20-star repo → fatal for a governance tool. FIX (this commit, folded into PR #261): promote GIF+hook to screen 1; lead with the "'Done.' — about code it didn't test" hook (preserves canary in a sub-line); CUT ~75% (506→127 lines) — moved the spec to NEW docs/reference.md (workflow/classification/skills/commands/architecture/platform) + docs/INSTALL.md (install/update/customize/entry-points); kept lean: hook → GIF → `bash demo/run.sh` → "Not just another rules file" + rules-vs-enforcement table → tight "What you get" → 3-line quickstart → trimmed FAQ (kept the "vs Cursor Rules" answer) → trimmed Docs. Honest framing preserved (no "can't lie"; "receipt you can check"). Verified: canary grep=2, scan exit 0, all internal links resolve, docs/*.md are lifecycle-frontmatter-exempt.
- 2026-06-20 CI red → fixed: "CI Structural Tests" failed on 2 ADR/AC-anchored tests because the overhaul relocated content to docs/INSTALL.md — `test_readme_fork_guidance_parity` (ADR-004/005: expected "Customizing Without Conflicts" in README) + `test_ac4_ac5_readme_documents_pre_commit_hook_setup` (expected the .githooks cp/config commands in README). The requirement (guidance DOCUMENTED + REACHABLE) still holds — it's in docs/INSTALL.md, linked from the README. Repointed both tests at docs/INSTALL.md AND added a `"docs/INSTALL.md" in readme` link assertion (tightens, not weakens, the entry-point-reachability contract). Re-ran locally: 2 passed. NOT gaming CI — the ACs verify "documented + reachable," not "lives in README.md specifically"; assertions are at least as strong. All other CI green (Markdown Links, Credential Scan, validate.sh ×2, TruffleHog, SAST, etc.).
- FOLLOW-UP flagged (NOT done here — scope discipline): the zh-TW README (docs/README_zh-TW.md, 314 lines) was NOT overhauled — it stays dense/old-style while EN is now lean. Reading-experience parity diverged. Deliberately deferred to the user: (a) the explicit ask was the EN landing page (GitHub's English-search adoption funnel); (b) a polished 繁中 translation of the hook line needs user review (can't QA while owner asleep); (c) low ROI for the English-search adoption goal. zh README still passes its half of the parity test (客製化而不衝突 inline). Recommend a separate PR for the zh-TW lean overhaul if the owner wants locale parity.
