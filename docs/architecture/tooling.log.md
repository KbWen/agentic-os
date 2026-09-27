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

---

### [tooling][2026-09-26][fix/install-path-batch]
source_spec: — (hotfix; Work Log `.agentcortex/context/archive/fix-install-path-batch-20260926.md`)
source_sha: 6678949

- [CONSTRAINT] Anything `deploy.sh` reads back from a tracked text file must strip a
  trailing CR before comparing: a Windows clone checks tracked files out CRLF until
  `.gitattributes` pins them, and bash `read -r` keeps the CR while the content
  hashes it is compared with are CR-normalized. MSYS `awk`/`sed` drop the CR in text
  mode, so this class is invisible to Windows-only testing of those paths.
- [DECISION] The installer's cache gate checks what a deploy needs — `deploy.sh`
  in the index and a clean `git status` — and treats a git error as unclean. A
  failed checkout never reaches it (the clone exits under `set -e`); what does is a
  wrong source, a cache git refuses to read, or a fresh clone git reports modified.
  The abort shows git's own diagnostic instead of guessing a cause.
- [CONSTRAINT] Every git call that reads a checked-out cache needs
  `core.longpaths` too, not only clone/pull: without it `git status` reports long
  paths as modified and a healthy cache is rejected. The static test binds this to
  the gate's own body, because the diagnostics repeat the same calls.
- [TRADEOFF] The gate is a correctness check, not a tamper control: untracked files
  pass `--untracked-files=no`. The cache was already fully trusted (its `deploy.sh`
  is executed), so a stronger check would claim protection it cannot give.

---

### [tooling][2026-09-27][fix/hook-monorepo-and-notices]
source_spec: — (quick-win; Work Log `.agentcortex/context/archive/fix-hook-monorepo-and-notices-20260927.md`)
source_sha: f3033f1

- [DECISION] The pre-commit hook locates the framework from its own `.githooks/`
  directory, not from the repository root: git runs hooks from the top level, so a
  package-level install otherwise validates the wrong directory and blocks every commit.
  The repository-root fallback is kept for hooks installed elsewhere.
- [CONSTRAINT] `core.hooksPath` is resolved from the repository root; a relative
  `.githooks` set inside a package points at a directory that does not exist there and the
  hook silently never runs. Deploy prints the sub-directory form only when the target is a
  sub-directory of its repository.
- [TRADEOFF] Guarded-path warnings skip additions (`--diff-filter=a`): the install-day
  commit adds those files. Deletions still warn, because `current_state.md` is not in the
  validator's required-files list and nothing else would flag its removal.

---

### [tooling][2026-09-27][fix/scoped-gitattributes]
source_spec: — (quick-win; Work Log `.agentcortex/context/archive/fix-scoped-gitattributes-20260927.md`)
source_sha: 6de3dbb

- [DECISION] The installed `.gitattributes` sets line endings only for the files Agentic OS
  installs, plus `.githooks/` (a hook must be LF to run). It comes from
  `.agentcortex/templates/downstream.gitattributes`, not from this repository's own file.
  Line endings of the product's own files are the product's decision, as the managed
  `.gitignore` block already treats ignore policy.
- [CONSTRAINT] No product-wide rule is neutral: `* text=auto` checks text files out with
  `core.eol` (CRLF on Windows under `core.autocrlf=false`) and stores new files LF in a CRLF
  repository. Product docs therefore reach the validators with CRs; the bash parsers of
  product docs must accept CRLF (`validate.sh` domain-doc status, no-Python `target_doc`),
  as `validate.ps1` already does.
- [TRADEOFF] Permanent neutrality for future adopters over a one-time step for existing
  ones. A clone checked out under the old rules keeps CRLF working copies of LF blobs;
  deploy says so once, only when it replaced the old file, with per-file advice
  (`git diff --ignore-cr-at-eol` empty -> `git checkout -- <file>`). A printed script was
  rejected: it deleted skip-worktree files and reverted assume-unchanged edits.
