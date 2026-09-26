# Work Log overflow: fix/install-path-batch (compacted 2026-09-26)

Moved verbatim from the active Work Log per handoff §6 to stay under the size cap.

## Phase Summary

- Compaction overflow of `.agentcortex/context/work/fix-install-path-batch.md` (hotfix #202/#206): review rounds 1-2 and the MFR/root-cause detail, moved verbatim. The receipts and the current summary stay in the active log. ⚡ ACX

## Moved: Phase Summary (review rounds 1-2 and the implement round between them)

- review: Not Ready — independent reviewer (same vendor) READY on 6 checks with 5 findings; primary adjudication NOT READY because F1/F2 are defects this unit introduced: F1 LOW cache_is_intact treats a failing `git status` (empty stdout) as clean — fail-open; F2 LOW the re-clone/abort text blames an earlier checkout / path length for every failure, and a wrong source repo (no deploy.sh) now gets "move to a shorter path" while the accurate message became unreachable; F3 LOW partial-checkout test fails under a developer's `pull.rebase=true`; F4 MEDIUM bootstrap SSoT write (Last Verified) not in Drift Log; F5 LOW four stale/inaccurate test comments. Routed back to implement. ⚡ ACX
- implement (after NOT READY): ed4db05 + 6621bfb — F1 gate fails closed on a git error; F2 neutral first message, abort shows git's diagnostic + source_repo hint (no path-length claim); F3 pull.rebase=false; F5 comments; +2 tests; locale pinned for the git-message assertion (found in self-check) | Confidence: 92% — high
- review (round 2, independent): Not Ready — Q1 fail-closed PASS (12-state table), Q2 abort path PASS, Q4 healthy path PASS; F1 MEDIUM the new abort-path lines contain `acx_git -C "$ACX_CACHE" ls-files/status`, so the static long-path test no longer fails when the gate itself uses plain git (reviewer: plain `git status` flags 3 long-path files on a 276-char clone, so every deep Windows update would abort); F2 LOW `|| true` on the abort `status` untested (mutant survives); F3 LOW per-file comment still understates (~13.5 min measured); F4 LOW code comment omits a fresh clone git reports as modified (case collision). NIT (git's `Did you forget to 'git add'?` hint) recorded, not fixed. Routed back to implement. ⚡ ACX

## Moved: Known Risk (MFRs, root causes, read-before-write)

- MFR #202: (1) install v1.8.24, commit per banner (no .gitattributes); (2) clone with autocrlf=true -> manifest CRLF; (3) deploy HEAD. Expected 0 overwrites; actual 13 [OVERWRITE] + 3 sidecars. A/B: stripping only the manifest CRs gives 0/0.
- Root Cause #202: `process_queue` reads the old manifest with `read -r` (keeps \r) while file content hashes are CR-normalized; `:298` re-records the CR-bearing hash.
- MFR #206: (1) project root >141 chars on Windows; (2) `bash installers/deploy_brain.sh .`; expected update; actual exit 128 "Filename too long"; retry -> "Already up to date" over an empty index -> deploy exit 0 from a partial tree.
- Root Cause #206: clone without `core.longpaths`; the only cache guard is `-f deploy.sh`, so a failed checkout survives into the pull branch.
- Test-fixture note: tests/ci/test_deploy_tiering.py `_set_manifest_hash` documents the CR bug in a comment and works around it in the fixture — #202 fixes the product instead.
- §12.1 read-before-write: deploy.sh (1523 lines, read in full) — changes: manifest_lookup_hash awk (:169-174), process_queue manifest loop (:399-410), Finish-setup banner (:1511). installers/deploy_brain.sh (119 lines, read in full) — changes: source_repo read, clone/pull via acx_git, new cache_is_intact gate before exec. Tests appended to tests/ci/test_deploy_tiering.py and tests/ci/test_deploy_brain_bootstrap.py (no new files, §12.4 n/a).
