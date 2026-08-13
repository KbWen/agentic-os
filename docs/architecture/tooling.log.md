---
status: living
domain: tooling
---

# Tooling — Decision Log (L2)

### [tooling][2026-07-28][codex/skill-runtime-modernization]
cross-ref: See [skill-ecosystem][2026-07-28][codex/skill-runtime-modernization] in docs/architecture/skill-ecosystem.log.md

### [tooling][2026-08-13][hotfix/windows-bash-launcher-probe]
source_spec: (none — hotfix; external audit `docs/reviews/2026-08-13-govern-audit-drift-core-health.md` F1)
source_sha: 2bc0c7eb30fe3ede9d342537831b2c8bfa8b0496 (PR #405)

- [DECISION] A Windows bash launcher is accepted on what it can DO, not on
  whether it exists. `Resolve-BashLauncher` probed `bash --version`, which
  `<git>\bin\bash.exe` and `<git>\usr\bin\bash.exe` answer identically with
  exit 0 — while the second carries no `/usr/bin` on PATH, so `deploy.sh`
  dies at `dirname` (line 4) with exit 127 and writes no manifest. The probe
  is now `bash -c 'command -v dirname && command -v mktemp'`: exactly the
  utilities both `deploy.sh` and `deploy_brain.sh:4` use at startup. Chosen
  over reordering or trimming the candidate list, which stays byte-identical
  — so no install that already worked can lose its selected launcher.
- [CONSTRAINT] `.agentcortex/bin/deploy.ps1` and `installers/deploy_brain.ps1`
  carry two byte-divergent copies of `Resolve-BashLauncher`. Only the first
  is provable end to end (the second routes through `deploy_brain.sh`'s
  install-vs-update dispatch), so the two are held together by a text-parity
  test rather than by review attention. Extracting a shared module was
  rejected: two call sites, and the seam would be new supply-chain surface.
- [CONSTRAINT] Widening a launcher probe makes its rejection path reachable.
  A host with only a bare bash now reads "Bash is required for deployment"
  while it demonstrably has bash, so both entry points state that a bash
  which cannot resolve `dirname`/`mktemp` is skipped on purpose. A fix that
  improves selection MUST also fix the message the newly-rejected user sees.
- [CONSTRAINT] `installers/deploy_brain.cmd:59` keeps an unprobed `where bash`
  fallback, reachable only when `deploy_brain.ps1` is absent from the
  installers directory — which no real install or deploy produces. Recorded
  as a known third path, deliberately not widened into the hotfix.
