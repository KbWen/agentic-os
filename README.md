<h1 align="center">Agentic OS</h1>

<p align="center">
  <strong>"Done." — your AI coding agent, about code it didn't test.</strong><br/>
  A rules file <em>asks</em> your agent to behave. Agentic OS <strong>checks that it did</strong> — it catches the agent
  skipping tests, skipping review, or shipping a leaked secret, through your git hooks, a validator, and CI rather than the agent's own word.
</p>

<p align="center">
  <strong>A governance-first layer for AI coding agents</strong> — guardrails and a gated workflow for Claude Code, Codex, Cursor, Copilot, Antigravity, or any Markdown-reading agent.
</p>

<p align="center">
  <a href="https://github.com/KbWen/agentic-os/releases"><img src="https://img.shields.io/github/v/release/KbWen/agentic-os?style=flat-square&label=release" alt="Release"/></a>
  <a href="https://github.com/KbWen/agentic-os/actions/workflows/validate.yml"><img src="https://img.shields.io/github/actions/workflow/status/KbWen/agentic-os/validate.yml?branch=main&style=flat-square&label=CI" alt="CI"/></a>
  <a href="https://github.com/KbWen/agentic-os/actions/workflows/security.yml"><img src="https://img.shields.io/github/actions/workflow/status/KbWen/agentic-os/security.yml?branch=main&style=flat-square&label=Security" alt="Security"/></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="MIT"/></a>
  &nbsp;·&nbsp;
  <a href="docs/README_zh-TW.md">繁體中文</a> ·
  <a href="CONTRIBUTING.md">Contributing</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

<p align="center">
  <img src="docs/assets/concept-hero.png" alt="An AI coding agent confidently claims 'Done. Tests pass. Shipping it.' and Agentic OS stamps the claim '[citation needed]'. Agentic OS demands evidence for what your AI agent claims — leaked secrets, missing tests, skipped reviews — through git hooks and CI instead of taking the agent's word." width="820"/>
</p>

<p align="center"><sub>It checks the evidence behind what your AI coding agent claims — secrets, tests, reviews — through your git hooks and CI. Here's a gate firing:</sub></p>

<p align="center">
  <img src="docs/assets/workflow-demo.gif" alt="An AI coding agent in a terminal claims a task is done and tries to ship it; the Agentic OS gate returns verdict FAIL because the work trail has no review or test evidence, blocks the ship, and only passes after review, tests, and evidence are recorded." width="780"/>
</p>

The `/bootstrap`, `/review`, and `/ship` above are plain text prompts — your agent maps them to the workflow files in the repo, so they run the same in Cursor or Codex as in Claude Code.

Or run a gate yourself, no install — the credential scan that catches a leaked key before it reaches git history:

```sh
bash demo/run.sh          # Windows (PowerShell): pwsh demo/run.ps1
```

<details>
<summary>Full terminal output</summary>

```text
  An AI agent wrote this file and reported: "Done — config added."
  ----------------------------------------------------------------
    DB_HOST=prod.internal
    aws_access_key_id = AKIA****************
  ----------------------------------------------------------------

  Without a gate, that commit lands and the key is in git history forever.
  Agentic OS runs this before the commit is allowed:

    $ scan_credentials.py config.env

CREDENTIAL PATTERN(S) DETECTED (values redacted):
  config.env:2: aws-access-key-id
Rotate the exposed secret, remove it from the change, then retry.

  Commit BLOCKED. The agent said "done"; the machine said no — and it
  redacted the value instead of echoing your secret back at you.
```

</details>

Your agent can still cut a corner. What it can't do is get a leaked secret, a green check over zero tests, or a skipped review past the hooks and CI — those run whether it cooperates or not. The key above is generated at runtime and redacted on output, so the demo never stores a real secret.

## Rules vs. enforcement

A rules file — Cursor Rules, a plain `AGENTS.md` — is a prompt the agent can ignore. Agentic OS keeps that discipline (plan before editing, no unasked-for refactors) and adds a layer the agent doesn't control:

| Failure mode | What catches it | Where |
|:---|:---|:---|
| A secret committed to history | `scan_credentials.py` (shown above) | pre-commit hook + CI |
| "Tests pass" with no tests | CI runs the real suite | pull request |
| A phase skipped with no evidence | `validate.sh` reads the work trail | pre-commit (local) |

The third row is the part a rules file can't reach: `validate.sh` parses each task's work log and fails if a required phase was skipped or its evidence is missing. The local pre-commit hook is opt-in and you can `--no-verify` past it; CI is the floor that can't be skipped. The Security badge above is this repo running the same credential and SAST gates on its own every push.

## Gated phases, scaled to risk

Every task runs a gated workflow, and the rigor scales to the risk. Skip a phase and `validate.sh` fails — but a typo doesn't run the same gauntlet as a feature:

<p align="center">
  <img src="docs/assets/pipeline-demo.gif" alt="A diagram of the Agentic OS workflow: a tiny-fix task flows through a short three-step path (classify, execute, done) and ships, while a feature task runs the full gated pipeline (bootstrap, plan, implement, review, test, ship) and is blocked at the ship gate for skipping tests, then passes once the test evidence is recorded." width="820"/>
</p>

The full set of paths, by classification:

| Classification | Required phases |
|:---|:---|
| **tiny-fix** | Classify → Execute → Evidence → Done |
| **quick-win** | Bootstrap → Plan → Implement → Evidence → Ship |
| **feature** | Bootstrap → Spec → Plan → Implement → Review → Test → Handoff → Ship |
| **hotfix** | Bootstrap → Research → Plan → Implement → Review → Test → Ship |
| **architecture-change** | Bootstrap → ADR → Spec → Plan → Implement → Review → Test → Handoff → Ship |

## What you get

| | |
|:---|:---|
| **Machine-enforced backstops** | The failure modes above are caught by your git hooks, the validator, and CI — not by the agent's own report. The agent can cut a corner; it can't get that corner past the checks it doesn't control. |
| **Skills that auto-attach by phase** | The workflow puts the right checklist in front of the agent by task type — TDD on a feature, an auth-security pass on login code — so you don't wire skills by hand. Guidance, not gates. |
| **Memory that survives handoffs** | Decisions and evidence live in one source-of-truth state file, so they carry across sessions and agents instead of resetting with the chat. |
| **Cross-platform** | One set of governance files works across every major AI coding agent — the same rules whichever one you run. |
| **Token-efficient by design** | Governance scales to risk: a tiny-fix skips the heavy guardrails (~5,000 tokens), so you're not paying frontier-model rates to fix a typo. |

<details>
<summary><strong>The 14 skills the workflow auto-attaches by task type</strong></summary>

The workflow attaches these by classification, so the relevant checklist is in front of the agent at the right phase — an auth-security pass when it touches login code, forward-only checks on a migration. They're structured guidance, not machine gates (the gates are the hooks, validator, and CI above); what they remove is the manual wiring.

| Skill | Trigger | Focus |
|:---|:---|:---|
| Test-Driven Development | feature, architecture-change | Red → Green → Refactor cycles |
| Systematic Debugging | bug encounter | 4-phase root cause analysis |
| Red Team / Adversarial | review, test | Classification-based security analysis |
| API Design | API endpoints detected | Endpoint validation enforcement |
| Auth Security | auth code detected | Hashing, tokens, rate limiting |
| Database Design | migration detected | Forward-only ORM-aware migration safety |
| Frontend Patterns | UI components | Component and state management patterns |
| Parallel Agent Dispatching | complex tasks | Coordinated subagent execution |
| Subagent-Driven Development | multi-module tasks | Multi-agent coordination |
| Karpathy Principles | all coding tasks | Behavioral guardrails against common LLM coding mistakes |
| Production Readiness | feature, architecture-change | Pre-ship observability: error sinks, log strategy, rollback telemetry |
| Verification Before Completion | /ship | 5-gate check: Scope → Quality → Evidence → Risk → Communication |
| Git Worktrees | parallel branches | Worktree isolation workflows |
| Doc Lookup | documentation needed | Documentation retrieval strategy |

</details>

<details>
<summary><strong>Multi-agent &amp; memory that survives handoffs</strong></summary>

Built for codebases where several AI sessions — or several people's agents — touch the same repo:

```
.agentcortex/context/
├── current_state.md          # Global project state (single source of truth)
└── work/
    └── <branch-name>.md      # Per-task work log (isolated, evidence + gate receipts)
```

- **One branch = one owner** — prevents concurrent work-log corruption.
- **Single-writer locking** — atomic lock files block clashing sessions per branch (configurable back to advisory).
- **Ship guard** — checks for source-of-truth conflicts before a merge.
- **Session identity** — every AI session records its model name and timestamp, so a handoff is traceable.

</details>

## Works with your agent

| Platform | Status | Integration |
|:---|:---|:---|
| **Claude Code** | Native | `CLAUDE.md` entrypoint + Claude platform guide |
| **OpenAI Codex** | Native | `AGENTS.md`, Codex platform guide, CLI delegation workflow |
| **Google Antigravity** | Native | Intent router + Antigravity runtime guidance |
| **Cursor** | Compatible | Reads `AGENTS.md` / project-rule style guidance — the slash-commands are plain prompts |
| **GitHub Copilot** | Compatible | Uses repository instructions and guardrail docs |
| **Any LLM agent** | Compatible | Model-agnostic Markdown workflows + evidence rules |

Either way the real floor is the same: the git hooks and CI don't care which agent you run.

## Quick start

```bash
git clone https://github.com/KbWen/agentic-os.git
./agentic-os/installers/deploy_brain.sh --dry-run /path/to/your-project   # preview, no changes
./agentic-os/installers/deploy_brain.sh /path/to/your-project             # deploy
```

Then tell your agent: *"Read `AGENTS.md` and follow it. Do not claim completion until /review and /test pass."* — followed by `/bootstrap` and your task.

| Your starting point | First command |
|:---|:---|
| Brand-new project, multi-feature idea | `/spec-intake` |
| Existing repo adopting Agentic OS | `/audit` (read-only, zero risk) |
| Single concrete task | `/bootstrap` |

Existing files are never overwritten (saved as `.acx-incoming` sidecars to merge). Windows / no-Python mode, updating, customizing without conflicts, turning the CI floor into a required check, and the full entry-point templates → **[docs/INSTALL.md](docs/INSTALL.md)**.

## FAQ

**What is Agentic OS?**
An open-source governance framework for AI coding agents. It gives agents like Claude Code, Codex, Cursor, Copilot, and Antigravity a repeatable workflow — plan, build, review, test, ship — and enforces gates so they can't skip steps or call a task "done" without verifiable evidence.

**How do I stop an AI agent from skipping tests or shipping unverified code?**
That's the core of it. The credential scan, the test suite, and the phase/evidence validator run in your git hooks and CI — so a leaked secret, a missing test, or a skipped review fails the commit or the build, regardless of what the agent reports. The agent can still cut a corner; it just can't get that corner past the checks it doesn't control.

**How is it different from Cursor Rules or a plain `AGENTS.md` file?**
A rules file tells the agent how to behave, and the agent can ignore it. Agentic OS adds the workflow and the checks that hold it to that behavior: phase sequencing, evidence requirements, scope discipline, and a single source of truth that remembers decisions across sessions. The skills and discipline are still guidance the agent follows; what's *enforced* is the part that fails your commit or CI — leaked secrets, missing tests, a skipped phase.

**Does it lock me into one AI vendor?**
No. It's model-agnostic Markdown — native entry points for Claude Code (`CLAUDE.md`) and Codex / Antigravity (`AGENTS.md`), and it works with Cursor, Copilot, and any other LLM agent through the same workflow files.

**Is it free?**
Yes — MIT licensed. Fork it and ship it.

## Docs

| Goal | Start here |
|:---|:---|
| Install, update, customize | [Install & Usage](docs/INSTALL.md) |
| Look up every command, the architecture, and the principles | [Reference](docs/reference.md) |
| Choose a model · see real token costs | [Model Guide](docs/AGENT_MODEL_GUIDE.md) · [Lifecycle Benchmark](docs/LIFECYCLE_BENCHMARK.md) |
| The principles & the test standard | [Agent Philosophy](.agentcortex/docs/AGENT_PHILOSOPHY.md) · [Testing Protocol](.agentcortex/docs/TESTING_PROTOCOL.md) |
| Platform-specific notes | [Codex](.agentcortex/docs/CODEX_PLATFORM_GUIDE.md) · [Claude](.agentcortex/docs/CLAUDE_PLATFORM_GUIDE.md) |
| Connect an external knowledge base (optional) | [Connecting a knowledge base](.agentcortex/docs/guides/connecting-a-knowledge-base.md) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — guidelines for contributing as a human or an AI agent.

## License

MIT. See [LICENSE](LICENSE).

<p align="center"><sub>A governance-first layer for AI coding agents. Contributions and feedback welcome.</sub></p>
