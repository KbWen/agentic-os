---
status: living
title: Lightweight Token Optimization Triage
date: 2026-10-15
baseline: 254105420c4a23dd4c2024bccc95b75f6bcf42ae
---

# Lightweight Token Optimization Triage

The owner requested lightweight token reductions and an updated backlog order. This is research and backlog intake, not approval to implement all candidates or change delivery gates.

## Evidence and limits

At the baseline commit, `_product-backlog.md` contains 195,640 characters, including 69 Shipped and 4 Cancelled rows despite its active-only introduction. Those completed rows account for 90,595 characters. Moving them verbatim into the existing completed archive would remove about 46% of the active file's characters before adding any archive pointer. The remaining 91 Pending rows still occupy 85,123 characters, so archival alone does not make the active inventory small. Long historical narrative should become bounded summaries with links to existing review/ship records; unresolved requirements and dependencies must survive.

Run `python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json` to reproduce the six-scenario baseline: 354,709 estimated tokens, of which 240,563 (67.8%) are workflow text. The quick-win scenario is 29,835. These are the instrument's character-based estimates, not model-tokenizer counts, observed usage, billing or proven savings. Its scope deliberately excludes `shared-contracts.md` under the separate size ratchet (#163); it also does not represent the entire conversation, tool-output history, SSoT or backlog load. Do not change the existing ceiling or its accounting scope merely to report a reduction.

`bootstrap.md` alone is 48,866 characters. It already distinguishes conditional sections and read scopes; improving those existing boundaries is a smaller candidate than a new router, cache service or lifecycle engine. The instrument's projected scoped totals are hypotheses, not measured runtime gains. Validate any change against actual section reads and required behavior in one existing downstream scenario before expanding it.

Existing #218 records a real KB consult at roughly 5–7K tokens, with about 3K spent on routing lookup; targeted route-key extraction belongs in that item. #135 already covers lighter quick-win Work Logs. #199 already has the owner's 2026-09-20 frontmatter-accounting decision; its quick-win Tier and dependency on the work it unblocks contradict that decision. Correcting those metadata fields is intake maintenance, not execution or reclassification of an active implementation.

## Dispositions and order

- Add **#230**: first lightweight implementation candidate, after the reproduced deployment omission #221. Archive completed backlog rows without changing their text or IDs, then shorten active historical prose through existing evidence links. No new GC engine or parallel backlog index.
- Bring **#218**, then **#217**, forward: preserve KB route order and select the matching routing entry without dumping the full table; retain the fingerprint-safety fix as a separately testable slice.
- Keep **#190** (validator ignores configured capabilities path) in the immediate correctness queue and **#121** (honest enforcement framing) ahead of speculative behavior experiments. Token work must not hide known gate-safety defects.
- Add **#231**: improve conditional/heading-scoped workflow reads, starting with bootstrap. Preserve always-loaded safety invariants, fresh shared-contract loading, phase entry, locks, evidence and frozen-document rules. No new workflow, duplicate summary surface or cache machinery; require non-growing canonical text plus behavior and read-volume evidence. Feature classification because instruction behavior changes.
- Promote existing **#135 P3 -> P2**: compact quick-win records while retaining required fields, receipts, security and evidence. Remove its unmeasured "~50%" savings claim. It follows #231 because validator/template changes carry more risk than reducing unnecessary reads.
- Keep **#228**, **#227**, then **#199** before **#225/#226** experiments. #228 is accounting/document honesty; #199 is measurement calibration, neither is itself a demonstrated runtime saving. #199 becomes feature; #198 depends on #199 as well as its existing #187 prerequisite, while #199 no longer depends on #198.
- Keep #229 independent. Reuse #124 to revalidate large lifecycle/task-capsule proposals before starting #1/#77/#78; do not silently cancel or implement them. Keep #122 as a narrow, evidence-backed deletion candidate rather than reopening every rule at once.

The backlog's front-loaded rows are the current execution queue. Remaining rows keep their previous relative order and priorities. Completed entries remain until #230 executes; this intake does not claim that cleanup shipped. Priority audit: #221 P2 -> P1 (silent deployment omission); #135 P3 -> P2 (owner's token-first direction). New #230 is P1 and #231 P2. Queue position is distinct from severity.

## External grounding

[Anthropic's context-engineering guidance](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) recommends a minimal sufficient context, targeted retrieval through lightweight references, and concise tool results. It also warns that aggressive compaction can lose needed details. This supports trying bounded reads and existing archives first; it does not prove this repository's savings or justify dropping gates.

## Verification

Backlog maintenance checks: stable original IDs and row membership, ten table columns, valid statuses/priorities, corrected #199/#198 prerequisites, no new dependency cycle, and preserved relative order outside the front queue. No source, gate or delivery-state change is part of this intake. Run existing docs-pin/lifecycle checks and `git diff --check`; record actual outcomes in the local Work Log.

## Claude implementation handoff

**Start with #221 only; #230 is next.** The first 16 inventory rows are the agreed execution order. This intake prepared that queue; every candidate is still Pending. Feature items such as #231/#199 still need their own spec and planning gates before implementation.

### Workspace and read map

- Baseline: `main` at `254105420c4a23dd4c2024bccc95b75f6bcf42ae` (v1.8.33). The backlog and this report are uncommitted documentation changes; preserve both. No implementation branch, feature spec or source patch has been created. These files are available in this same checkout; another checkout needs the documentation changes transferred first.
- Follow `CLAUDE.md` / `AGENTS.md` and normal bootstrap ownership, classification and phase rules. Open a separate task branch and task Work Log for #221 when implementation is authorized. The local `.agentcortex/context/work/main.md` is a review/intake record, not #221's implementation log; its review receipt cannot satisfy #221's gates.
- Beyond mandatory bootstrap reads, read this section, backlog row #221, `.agentcortex/bin/deploy.sh` (`CP_FLAG` whitelist, `_deploy_file_now`, `process_queue`), and `tests/ci/test_deploy_tiering.py` (helpers `_deploy`, `_deploy_dry_run`, `_user_bytes`; existing CP_FLAG/brownfield tests).
- Read `tests/ci/test_deploy_dry_run_read_only.py` for the adjacent regression boundary. Prior shipped specs, the entire completed backlog archive, old review transcripts and large lifecycle proposals are unnecessary for this first unit unless a specific contradiction requires historical tracing.

### First unit: #221

Reproduce both existing failures on the unchanged baseline before patching:

1. Batch deployment with a core-file collision and `CP_FLAG=-i`: the copy command inherits the queue loop's stdin and can consume the following queue record as an answer. Inspect destination files and manifest membership, not just exit 0 or the success banner.
2. Updating modified core content with `CP_FLAG=-n`: copying may keep the destination while the log/counters claim it was overwritten. Inspect actual bytes and resulting manifest/accounting.

Acceptance focus: queue iteration and interactive answers use independent input streams; both accept and decline paths terminate and preserve subsequent records. No-clobber output/counters reflect the delivered bytes. Existing newest-edit backup protection, first-install preservation and dry-run immutability continue to hold. Use bounded subprocess timeouts for interactive tests. The separate-FD/post-copy-hash directions in #221 are hypotheses to test, not an already-approved implementation patch. Keep the fix to deploy behavior and focused tests.

Existing test entry points:

```sh
python -m pytest -q tests/ci/test_deploy_tiering.py -k "cp_flag or brownfield" --tb=short
python -m pytest -q tests/ci/test_deploy_tiering.py tests/ci/test_deploy_dry_run_read_only.py --tb=short
```

Add focused regressions for #221; the current tests alone do not prove its queue boundary. Run required framework checks and review/test/ship gates for the classification established at bootstrap. Finish one unit before starting #230; preserve the repository's serialized ship-state updates.

### Next unit and validation limits

- #230 uses the existing completed archive. Preserve full source rows/IDs before shortening active summaries, retain unresolved requirements, and resolve dependencies across both files. The live table has 10 columns; the legacy archive mixes 9- and 10-column records. Do not mistake that legacy shape for permission to drop a field. Maintain the execution order when completed rows leave the active table.
- This intake passed 12 docs-pin tests and 42 lifecycle tests, backlog ID/status/order/dependency integrity checks, and whitespace checks. These checks cover documentation intake; they do not prove any proposed runtime saving or #221 fix. Historical CI for #466/#467/#468 covers v1.8.33, not these uncommitted documents or future implementation.
- On this Windows Codex host, Git Bash's MSYS startup was blocked in the sandbox; deployment tests passed with approved execution outside it and a writable task temp directory. Preserve test fidelity and report environment failures separately from behavioral failures.
- Reproduce cost estimates with `python .agentcortex/tools/analyze_token_lifecycle.py --root . --format json`. The original JSON under Codex's visualization directory is optional local evidence, not a portable dependency. Do not replace measured runtime usage with this static proxy or raise ceilings to make a change pass.

Suggested owner kickoff: "Take over this checkout using `docs/reviews/2026-10-15-token-lightweight-triage.md` section `Claude implementation handoff`. Start only backlog #221 through the normal bootstrap/plan/implementation flow. Preserve the pending documentation changes and leave #230 for the next unit."
