---
status: living
domain: testing
---

# Testing — Decision Log (L2)

### [testing][2026-07-28][codex/skill-runtime-modernization]
cross-ref: See [skill-ecosystem][2026-07-28][codex/skill-runtime-modernization] in docs/architecture/skill-ecosystem.log.md

### [testing][2026-08-13][hotfix/windows-bash-launcher-probe]
cross-ref: See [tooling][2026-08-13][hotfix/windows-bash-launcher-probe] in docs/architecture/tooling.log.md
source_sha: 2bc0c7eb30fe3ede9d342537831b2c8bfa8b0496 (PR #405)

- [DECISION] A test-side bash probe must reject what it cannot use and must
  never abort collection. `has_bash_launcher()` is evaluated at import time by
  `skipUnless` in two modules, so an uncaught `OSError` from a broken
  app-execution alias takes both modules out of collection rather than
  skipping one candidate. It now excludes WindowsApps aliases, catches
  `OSError` and continues, and applies the same coreutils probe as the
  shipped entry points.
- [DECISION] Fix the outliers, do not extract a shared resolver. Inventory
  before acting: of the **twelve** test modules that call `which("bash")` at
  `3faae10`, **ten carried the WindowsApps guard and two did not**. A shared
  `tests/` helper would have been a cross-directory refactor of working code
  to fix two files. The population is held together by
  `tests/ci/test_bash_resolver_parity.py` instead.
- [CONSTRAINT] **An inventory taken mid-change is not a pre-change inventory.**
  The line above first read "eleven carried the guard and exactly one did not"
  — measured after the first of the two outliers had already been fixed in the
  same session, then written into three records as the pre-existing state. It
  survived a review, a test phase and a ship, and was caught only by a
  same-day re-derivation at the base commit. Count against an explicit
  revision (`git ls-tree -r --name-only <base>`), never against the working
  tree you are editing.
- [CONSTRAINT] **A recurring red labelled "local environment artifact" is a
  hypothesis, not a diagnosis.** `test_validator_worklog_family_skip.py`
  failed on Windows across more than one ship and was recorded each time as
  this machine's WSL-stub quirk. It was a bare `shutil.which("bash")` with no
  guard at all — the same defect class as the audit's own F2 finding, in a
  third copy. Re-diagnose before re-labelling; see the `[paired-check-parity]`
  Global Lesson.
- [CONSTRAINT] A test that builds a Windows directory junction MUST drop it
  with `os.rmdir` in a `finally` before any recursive cleanup runs.
  `os.path.islink()` reports **False** for junctions and only `shutil.rmtree`
  on Python >=3.12 recognises them, so on the 3.9 CI floor a
  `TemporaryDirectory` cleanup can follow a junction into its target — here,
  the real `C:\Program Files\Git\usr\bin`.

### [testing][2026-10-20][feat/test-evidence-freshness]
source_spec: docs/specs/test-evidence-freshness.md
- [DECISION] A recorded test run carries a fingerprint of the code it tested: `git write-tree` of a temporary index seeded from the real one, excluding `.agentcortex/context/`, so recording the result and shipping do not change it.
- [DECISION] Opt-in by presence of a `Test run:` line; FAIL only when a recorded run contradicts a later receipt or the code about to ship.
- [TRADEOFF] Detects stale and failed evidence, not forged evidence (a hand-typed line, a recorded no-op, a tree made unreadable on purpose) — stated in README; signing was previously rejected as self-attestation.
- [CONSTRAINT] Copy the index with mtime kept (`copy2`) and refresh it: a fresh mtime makes git trust stale stat data for same-size edits. Sanitize records with `splitlines()` (U+2028/U+2029/`\x85` split lines). Compare receipt timestamps as parsed instants; a bare date is end of day.
- [CONSTRAINT] At /ship the check runs at pre-merge step 2, before the Work Log is archived; docs written after archival (L2, spec status) are not seen by it.
