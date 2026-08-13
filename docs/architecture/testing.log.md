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
- [DECISION] Fix the one outlier, do not extract a shared resolver. Inventory
  before acting: of the **twelve** test modules that call `which("bash")`,
  **eleven already carried the WindowsApps guard and exactly one did not**.
  A shared `tests/` helper would have been a cross-directory refactor of
  working code to fix a single file. The population is held together by
  `tests/ci/test_bash_resolver_parity.py` instead.
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
