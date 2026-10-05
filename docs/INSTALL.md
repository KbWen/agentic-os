# Install & Usage

Full install, update, and first-task guidance for Agentic OS. The repo
[README](../README.md) keeps only the short version.

## Prerequisites

| Dependency | Required? | Purpose |
|:---|:---|:---|
| **Git** | Required | Clone and deploy the framework |
| **Bash** | Required | Run deploy & validate scripts (Git Bash from [Git for Windows](https://gitforwindows.org/) is enough on Windows) |
| **Python 3.9+** | Recommended | Enables full validation (metadata, encoding, command sync checks) |
| **SHA-256 tool** | Required for deploy | `sha256sum`, `shasum`, or `openssl` (pre-installed on most systems) |

> **No Python?** The framework deploys and works without Python. Validation runs in
> degraded mode — Python-dependent checks report `WARN` instead of `FAIL`.
> Pass `--no-python` to suppress warnings from a Git Bash or POSIX shell:
> `bash .agentcortex/bin/validate.sh --no-python`. On Windows PowerShell, prefer
> `powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1 -NoPython`.

## Install (first time)

```bash
# Clone Agentic OS
git clone https://github.com/KbWen/agentic-os.git

# Preview what will be deployed (no changes made)
./agentic-os/installers/deploy_brain.sh --dry-run /path/to/your-project

# Deploy into your project
./agentic-os/installers/deploy_brain.sh /path/to/your-project
```

**Update (after first install):** the installer lives inside your project. Run it from your project root — it reads the deploy manifest and auto-fetches the latest framework version from GitHub.

```bash
bash installers/deploy_brain.sh .
```

> **Existing files: kept, or backed up and replaced.** If your project already has a different `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, skill, template or other scaffold file, your copy stays in place and the framework version is saved beside it as `<filename>.acx-incoming`. Review and merge manually — or ask your AI agent: *"Merge each .acx-incoming into its target, preserving my project-specific content and adopting framework updates."*
>
> Rules, workflows, tools, `.claude/commands/` and the other core files are framework-authoritative: a different file you already have at one of those paths is first copied byte-for-byte to `<filename>.acx-local`, then replaced. The deploy prints an `[OVERWRITE]` line naming each one, and stops before replacing a file it could not back up. The `.acx-local` copy is gitignored and may be the only copy of an untracked file. It holds only the latest replaced version: the next deploy that replaces that file overwrites it, so move any backup you want to keep out of the way before re-deploying. To restore, copy `<filename>.acx-local` back over `<filename>`; to keep your changes on later updates, move them into `AGENTS.override.md` or a `custom-*` skill.

> **Monorepo / multi-package?** One deploy governs **one project root** — a single `.agentcortex/` state machine (SSoT, Work Logs, specs) at the target you pass. Agentic OS deliberately does **not** partition shared state across sub-packages (ADR-004/005). For a monorepo, either pick one governed root, or deploy per-package (each sub-project gets its own independent `.agentcortex/`); sibling deploys don't share SSoT.

> **AI-agent install:** If you're asking an AI assistant to install Agentic OS, point it to this file. The commands above are deterministic — no platform-specific heuristics required.

**Optional local pre-commit validation:** enable the bundled Git hook sample to run Agentic OS validation before each commit.

```bash
cp .githooks/pre-commit.guard-ssot.sample .githooks/pre-commit
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

On Windows, run the setup from PowerShell:

```powershell
Copy-Item .githooks\pre-commit.guard-ssot.sample .githooks\pre-commit
git config core.hooksPath .githooks
```

> **Note:** `git config core.hooksPath .githooks` makes Git use **only** `.githooks/`. If you already use husky, lefthook, or a `.git/hooks/` setup, this replaces it — integrate the ACX check into your existing hook instead of overwriting.

> **Framework in a sub-directory (monorepo)?** Git resolves `core.hooksPath` from the repository root, so a bare `.githooks` points at a directory that does not exist there and the hook silently never runs. Use the path from the root instead: `git config core.hooksPath <sub-dir>/.githooks`. The hook finds the framework next to its own `.githooks/` directory.

The hook runs `validate.ps1` from Git Bash on Windows when PowerShell is available, otherwise it runs `validate.sh`. Validator failures block the commit; guarded SSoT receipt warnings remain advisory.

<details>
<summary><b>Windows (PowerShell / CMD)</b></summary>

```powershell
# Clone Agentic OS (first time)
git clone https://github.com/KbWen/agentic-os.git

# Preview what will be deployed (no changes made)
powershell -ExecutionPolicy Bypass -File .\agentic-os\installers\deploy_brain.ps1 -DryRun C:\path\to\your-project

# Deploy into your project
powershell -ExecutionPolicy Bypass -File .\agentic-os\installers\deploy_brain.ps1 C:\path\to\your-project

# CMD alternative
.\agentic-os\installers\deploy_brain.cmd C:\path\to\your-project
```

Use the PowerShell entrypoint when possible. It resolves Git Bash directly and does not require a WSL distro.
Git Bash is still required on Windows for shell-based deploy and validation scripts; the PowerShell entrypoint simply locates and invokes it for you.

```powershell
# Already installed? Run from your project root to update:
powershell -ExecutionPolicy Bypass -File .\installers\deploy_brain.ps1 .

# Validation after install
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1

# Lightweight validation when Python is not installed
powershell -ExecutionPolicy Bypass -File .\.agentcortex\bin\validate.ps1 -NoPython
```

</details>

<details>
<summary><b>Text-only usage (no scripts)</b></summary>

If you only want the governance templates (Markdown files) without running any tooling:

1. Copy the `.agent/`, `.agents/`, and `AGENTS.md` files into your project
2. Optionally copy `.agentcortex/templates/current_state.md` to `.agentcortex/context/current_state.md` as your project-owned starting state
3. No Python, Bash, or other tools are needed — all governance is plain Markdown

Do not copy this repository's `.agentcortex/context/` directory wholesale; it contains Agentic OS runtime state, archives, and guard receipts, not your downstream project's state.

</details>

## Turn on the CI floor (required status check)

`deploy_brain.sh` puts the validator (`.agentcortex/bin/validate.sh`) and the
credential scanner (`.agentcortex/tools/scan_credentials.py`) in your repo, but it
does **not** add a CI workflow or change your branch settings — that part is yours
to switch on. This is what turns the checks into a floor your agent can't
`--no-verify` past: they run on every pull request, and a failing check blocks the
merge.

**1. Add a workflow** at `.github/workflows/security.yml` (this filename also
clears the advisory `validate.sh` raises when a repo has workflows but no security
workflow):

```yaml
name: Agentic OS
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0          # full history so the credential scan can diff the PR
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'   # without Python the validator degrades to advisory WARN
      - name: Phase & evidence gate
        run: bash .agentcortex/bin/validate.sh
      - name: Credential scan (PR diff)
        if: github.event_name == 'pull_request'
        run: |
          base="${{ github.event.pull_request.base.sha }}"
          head="${{ github.event.pull_request.head.sha }}"
          # a git error here (rare, given fetch-depth: 0 above) fails the step — fail-closed
          python .agentcortex/tools/scan_credentials.py --range "${base}...${head}"
      - name: Your tests
        run: |
          if [ -d tests ]; then
            echo "Replace with your test command, e.g. pytest -q / npm test / go test ./..."
          else
            echo "No tests/ yet — add your suite and wire it here."
          fi
```

This runs only what `deploy_brain.sh` actually installed; the test step is a
placeholder you replace (the framework's own `tests/` are not deployed, so don't
copy this repo's `validate.yml`).

**2. Make the check required** so a failing run blocks the merge. Open one pull
request first — a check only becomes selectable after it has run once — then in
your repo:

- **Settings → Branches → Add branch protection rule** (or **Settings → Rules →
  Rulesets**, GitHub's newer equivalent), targeting your default branch.
- Enable **"Require status checks to pass before merging"** and select the
  **`gate`** check by name.
- Enable **"Do not allow bypassing the above settings"** so the rule applies to
  administrators too.

To script it instead of clicking, see GitHub's
[branch-protection API](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
(the payload is verbose; the UI is simpler for a one-time setup).

**Honest caveats:** (1) the workflow runs as soon as you add it, but it only
*blocks* merges once you add the branch-protection rule — until then it is
advisory; (2) a repository admin can still override a required check — this raises
the floor, it does not make a bypass impossible; (3) keep the `setup-python` step,
or the validator degrades to advisory `WARN`s and won't fail the build (see
[Prerequisites](#prerequisites) for no-Python mode).

> **Maintainer note — making security a required merge check (this repo):**
> The `agentic-os` repo's branch protection currently requires exactly three checks:
> `Framework Validation`, `ShellCheck`, and `Check Markdown Links`. The security
> scanning jobs (`semgrep`, `trufflehog`, `credential-scan`, `dependency-audit`) run
> on every PR and are visible in the checks panel, but they are **not** required merge
> checks. To make them required: add each job name to the branch-protection required
> status checks list (Settings → Branches → Branch protection rules → "Require status
> checks to pass"). Important caveat for `semgrep`: the Semgrep job is gated on the
> `changes` classifier (`heavy=true`) and is skipped on docs-only PRs. Requiring it as
> a merge check would block docs-only PRs when the job is skipped (GitHub treats a
> skipped required check as failing unless you use `if: always()` or rulesets with skip
> semantics). Evaluate whether that trade-off is acceptable before requiring it.

## Customizing without conflicts (fork or clone)

However you adopt Agentic OS — **fork** the repo, or **clone + `deploy_brain.sh`** into your project — the same rule keeps upgrades painless: **add your own files; never edit framework-owned files in place.** Put your customizations where the framework guarantees never to touch them, and they survive both `git pull upstream` (fork) and the next `deploy` (clone):

| You want to… | Put it here | Why it survives upgrades |
|---|---|---|
| Add project governance (narrow/disable a directive) | `AGENTS.override.md` (project root) or `~/.agentcortex/AGENTS.override.md` (personal) | Loaded present-only at session start; framework never ships these files. MAY narrow/disable directives but **cannot** relax delivery gates. |
| Add your own skills | `.agents/skills/custom-<name>/SKILL.md` (+ `.agent/skills/custom-<name>` metadata) | `custom-*` is a reserved namespace the framework never ships → zero collision, never overwritten. **Survival is not activation:** an undeclared `custom-*` skill stays inert — it is never auto-recommended and cannot be pinned. To make it activatable, declare its id under `skills:` in `.agentcortex/context/private/downstream-capabilities.yaml` (opt-in, capped at `load_policy: on-match`; see [ADR-007](adr/ADR-007-downstream-capability-declaration-seam.md)). |
| Adjust skill activation (pin/exclude) | `.agentcortex/context/private/user-preferences.yaml` | Gitignored, personal, loaded by bootstrap. |
| Connect an external knowledge base (read-only) | `knowledge_sources:` in `.agentcortex/context/private/downstream-capabilities.yaml` — see [Connecting a knowledge base](../.agentcortex/docs/guides/connecting-a-knowledge-base.md) | Present-only opt-in; **absent = zero cost**. Lives in the never-shipped private dir; consumed as DATA to enrich `/plan` + `/review`. |

**What NOT to do:** editing a framework file in place causes merge conflicts on `git pull upstream` (fork). On the next `deploy` (clone) what happens depends on the file: rules, workflows and tools (`.agent/rules/*`, `.agent/workflows/*`) are force-updated, and your edit survives only as a `<file>.acx-local` backup; `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` and shipped skill bodies keep your copy and put the framework's new version beside it as a `<file>.acx-incoming` sidecar that you must merge by hand. Either way the cleaner pattern is `AGENTS.override.md` for governance and a `custom-<name>` skill for skills.

## Start working — pick your entry point

Always preface your first message with:

> "Read `AGENTS.md` and follow it. Do not claim completion until /review and /test pass."

> **Claude Code:** start the task with the slash command itself (`/bootstrap <task>`, `/spec-intake`, `/audit`), not with prose alone. In the 2026-09-26 downstream simulation, Claude Code sessions that began with `/bootstrap` opened a Work Log and followed the phases 6/6; sessions given only the preface above did so 1/2, and sessions with no hint 0/3. Codex reads `AGENTS.md` natively and engaged in 6/6 without a slash command.

Then add **one** of the following based on your situation:

**A. Brand-new project, multi-feature idea** — `/spec-intake` first

```text
This is a brand-new project. My initial idea is:
[1–2 paragraphs describing the product and its features]

Please run /spec-intake to decompose this into a feature inventory.
After I pick the first feature, run /bootstrap → /app-init to establish
the tech stack ADR, then /plan and /implement.
```

**B. Existing repository adopting Agentic OS** — `/audit` first

```text
This repo already has code; Agentic OS was just deployed.
Run /audit (read-only) to map the codebase, then /app-init to record
the tech stack ADR, then /spec-intake when I add features.
```

**C. Single concrete task on an established project** — `/bootstrap` directly

```text
/bootstrap
[describe the single task]
```

| Starting point | First command | Full chain |
|---|---|---|
| Brand-new project, multi-feature idea | `/spec-intake` | spec-intake → pick feature → bootstrap → app-init → plan → implement |
| Existing repo, adopting Agentic OS | `/audit` (read-only, zero risk) | audit → app-init → spec-intake → quick-win → feature |
| Single concrete task on an established project | `/bootstrap` | bootstrap → plan → implement → review → test → ship |

> **Why this matters**: a multi-feature raw idea routed straight to `/bootstrap` is classified as a single task, skipping the Feature Inventory and `_product-backlog.md` decomposition. The Intent Router auto-detects this in most cases, but explicit beats inferred.

Then the AI classifies your task and follows the required phases automatically:

```
You: "Add pagination to the user list API"

AI: [/bootstrap] → Classification: feature
    → Required: Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship
    → Loading skills: API Design, Test-Driven Development
```
