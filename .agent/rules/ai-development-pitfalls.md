# AI-Assisted Development Pitfalls v1.1

> **Purpose**: A reference catalogue of common failure modes in AI-assisted development (Claude Code, Cursor, Copilot, Devin, etc.) — root causes, symptoms, and mitigations — for use by AgentCortex and its downstream projects.
>
> **Last updated**: 2026-03-23
> **Sources**: Hacker News, Reddit, IEEE Spectrum, developer blogs, CVE database, academic research

---

## Table of Contents

1. [Context Window Decay](#1-context-window-decay)
2. [Architecture Drift](#2-architecture-drift)
3. [Silent Failures](#3-silent-failures)
4. [Fake Tests / Superficial Coverage](#4-fake-tests--superficial-coverage)
5. [Style and Lint Violations](#5-style-and-lint-violations)
6. [Spec Drift](#6-spec-drift)
7. [Over-Engineering](#7-over-engineering)
8. [Prompt Injection and Security Issues](#8-prompt-injection-and-security-issues)

---

## 1. Context Window Decay

### Pitfall Name
**Context Window Decay** — the AI "forgets" earlier decisions, repeats mistakes, and contradicts itself after a long session.

### Symptoms
- AI re-generates functions that were already written earlier in the session (duplicate functions)
- Coding conventions established at the start of the session are ignored later on
- AI proposes solution A early, then proposes solution B for the same problem dozens of messages later
- Session locks up at context limit ("Prompt is too long" error)
- Token cost spikes in the late session (150k tokens ≈ $0.45/turn vs 30k tokens ≈ $0.09)
- Output quality degrades noticeably in late-session: more hallucinations, fewer accurate references to earlier decisions

### Root Cause
The transformer attention mechanism assigns decreasing effective weight to earlier tokens. Foundational rules and decisions are technically still in the context window, but their signal is diluted as debugging details, side conversations, and follow-up messages accumulate.

### Project-Level Mitigations (template — fill in for your project)
*Document here: does this project use a session handoff convention? Is there a CLAUDE.md? What is the context budget policy?*

### General Mitigations
- **Use `/clear` proactively**: reset context after completing each feature; start the next task fresh
- **Use `/compact <instructions>`**: manually control what context survives compaction
- **60% rule**: do not let context exceed 60% capacity — output quality measurably degrades after 20–40% fill
- **Session length discipline**: aim for 30–45 minute sessions; keep context precise
- **Handoff docs**: before ending each session, have the AI write a `session-handoff.md` summarising decisions; inject it at the start of the next session
- **CLAUDE.md / .cursor/rules**: put non-negotiable architectural constraints in version control so they are injected automatically every session (recommended: < 200 lines, < 2,000 tokens)
- **Task decomposition**: break large tasks into small ones; run each subtask in its own short session

### Reference Cases
- Reported in IEEE Spectrum: "Claude generates code that duplicates functions already written earlier in the session, forgets coding conventions established at the start"
- A popular editor removed its "Memories" feature in a minor release; developers were forced to manage context manually
- Measured data from a community guide: output quality at 60%+ context fill shows statistically significant degradation

**Sources**: [Claude Code Context Management - SitePoint](https://www.sitepoint.com/claude-code-context-management/) | [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices) | [IEEE Spectrum: AI Coding Degrades](https://spectrum.ieee.org/ai-coding-degrades)

---

## 2. Architecture Drift

### Pitfall Name
**Architecture Drift** — every new session the AI is unaware of prior design decisions and produces code with inconsistent style, structure, or patterns.

### Symptoms
- Code written in different sessions has inconsistent naming, folder structure, and patterns
- AI assumes an incorrect codebase structure (e.g., assumes a service layer that does not exist)
- Duplicate implementations appear; the AI does not detect existing utility functions
- Test suite grows to thousands of lines but covers only three scenarios in fifteen different ways
- After being told to "follow existing style", the AI still produces non-conforming output

### Root Cause
The AI is a stateless blank slate in every new session. Training data allows it to produce "reasonable" code, but not "code consistent with your specific project". When the solution space is large, the probability that the AI independently chooses the intended pattern approaches zero.

A practitioner summarised the problem: "When there are many different ways to solve a problem, it is extremely unlikely that an AI will choose the right one. Open solution spaces tend to lead to AI making disappointing choices."

### Project-Level Mitigations (template — fill in for your project)
*Document here: does this project use ADRs? An examples folder? CLAUDE.md with architecture constraints?*

### General Mitigations
- **CLAUDE.md / AGENTS.md**: maintain an architecture decision record (ADR) in the repo root; inject it automatically every session
- **Few-shot prompting**: include 2–5 existing code examples in the prompt; this dramatically improves consistency
- **`/examples` folder**: maintain a dedicated folder of canonical patterns for the AI to learn from
- **Architecture as code**: encode design decisions as executable constraints (API contract tests, lint rules)
- **Spec-Driven Development**: write the spec first; let the AI generate from the spec; spec is the single source of truth
- **Small, well-defined steps**: limit each session to one function, one bug, one screen
- **Versioned conventions**: put coding conventions in git, not just in conversation

### Reference Cases
- Practitioners report: "The AI accelerates implementation, but expertise keeps code maintainable" — AI adds speed; architecture quality is still a human responsibility
- A real project's test suite was AI-generated to 2,000 lines covering only 3 scenarios (15 variations each) because the AI was unaware that similar tests already existed

**Sources**: [Pete Hodgson: Why Your AI Coding Assistant Keeps Doing It Wrong](https://blog.thepete.net/blog/2025/05/22/why-your-ai-coding-assistant-keeps-doing-it-wrong-and-how-to-fix-it/) | [Addy Osmani: The 70% Problem](https://addyosmani.com/blog/the-70-problem/)

---

## 3. Silent Failures

### Pitfall Name
**Silent Failures** — AI-generated error handling looks correct but swallows all errors with no observable trace.

### Symptoms
- Code passes linting and CI, but fails silently in production
- Users report broken functionality; logs contain no error
- Approximately 20% of errors never reach a log (measured data)
- Silent logic failures account for ~60% of production faults
- Calculation results are wrong but the program does not crash (e.g., order totals become negative)

### Root Cause
AI learns error-handling patterns from training data that favour "defensive" code — catching all exceptions to avoid crashes, but without logging, retry, or escalation. This pattern "looks safe" in training data but produces silent failures in production.

Typical problematic patterns:
```python
# AI commonly generates this (BAD)
try:
    result = process_order(data)
except Exception:
    pass  # swallows all errors

# Or this (BAD)
try:
    result = calculate_total(items)
except Exception as e:
    return 0  # masks errors with a default value
```

### Project-Level Mitigations (template — fill in for your project)
*Document here: does this project enforce a no-empty-catch lint rule? What is the project's error handling convention?*

### General Mitigations
- **Lint rule banning empty catch**: add `no-empty` (ESLint) or equivalent to CI
- **Error handling checklist**: when reviewing AI-generated error handling, ask:
  - Is this error logged?
  - If caught, is there a retry / fallback / alert?
  - Does this catch make the outer logic incorrectly assume success?
- **Explicit error handling pattern**: define the required format in CLAUDE.md
- **Static analysis**: scan for empty catch blocks and silent failure paths
- **Typed errors**: require the AI to return typed errors (Result type, Either monad) rather than bare try/catch

### Reference Cases
- Real bug: order calculation allowed negative line items creating "free orders"; the exception was caught but the result was never validated for business correctness
- Real bug: file output only checked file existence and row count; row ordering and escaped-character logic errors went undetected
- Reported in IEEE Spectrum: LLMs generate code that "removes safety checks or creates fake output that matches desired format to avoid crashing"

**Sources**: [AI Agent Error Handling Patterns](https://blog.jztan.com/ai-agent-error-handling-patterns/) | [Common Bugs in AI-Generated Code](https://www.ranger.net/post/common-bugs-ai-generated-code-fixes) | [The Silent Failures](https://medium.com/@milesk_33/the-silent-failures-when-ai-agents-break-without-alerts-23a050488b16)

---

## 4. Fake Tests / Superficial Coverage

### Pitfall Name
**Fake Tests / Superficial Coverage** — tests are added but do not actually verify core logic.

### Symptoms
- CI is green but bugs reach production
- Tests only cover the happy path
- AI-generated tests have a mutation kill rate of ~40% (target: 80%+)
- For functions over 50 lines, AI-generated test coverage drops an additional 25%
- Tests verify the AI's own implementation, not the behavioural specification
- Tests use hard-coded timestamps or random seeds, producing flaky tests

### Root Cause
AI tends to "mirror the code" when generating tests — translating the existing implementation into test assertions rather than starting from the behavioural specification. These tests pass even when the implementation is wrong, because the test and the bug are generated together.

```python
# AI sees this function
def calculate_discount(price, pct):
    return price * (1 - pct / 100)

# Generates this "mirror test" (BAD)
def test_calculate_discount():
    assert calculate_discount(100, 10) == 100 * (1 - 10/100)
    # No tests for negative price, pct > 100, pct < 0, or other boundary conditions
```

### Project-Level Mitigations (template — fill in for your project)
*Document here: what testing framework does this project use? Has fake-test been encountered before?*

### General Mitigations
- **Pre-acceptance checklist**:
  - Does this test verify behaviour or implementation detail?
  - Does it test edge cases (negative, zero, null, maximum)?
  - Would this test fail if the implementation were wrong?
- **Mutation testing**: use mutation testing tools (mutmut, PIT) to measure actual test effectiveness
- **Target boundary conditions**: minimum, maximum, zero, empty, singleton, just-above/just-below threshold
- **Do not use coverage percentage as the target**: 80% high-quality tests >> 100% shallow tests
- **Test-first prompting**: ask the AI to list test cases first (no code); confirm the cases are sensible before generating tests

### Reference Cases
- Research finding: a mutation-guided approach improves faulty code detection by 28% compared to zero-shot LLM test generation
- Real case: discount calculation tests had no coverage for "what happens when price is negative"
- Real case: file processing tests only verified output existence and row count; row ordering and escaped-character bugs were missed

**Sources**: [When Generated Tests Pass but Don't Protect](https://dev.to/jamesdev4123/when-generated-tests-pass-but-dont-protect-llms-creating-superficial-unit-tests-24c0) | [AI-Generated Tests Are Lying to You](https://davidadamojr.com/ai-generated-tests-are-lying-to-you/) | [Meta: Mutation-Guided LLM Testing](https://www.infoq.com/news/2026/01/meta-llm-mutation-testing/)

---

## 5. Style and Lint Violations

### Pitfall Name
**Style/Lint Violations** — the project has linting rules and a style guide, but the AI still produces non-conforming code.

### Symptoms
- A rule banning `@Autowired` field injection is in place; the AI still uses field injection
- The architecture requires a service layer; the AI writes business logic directly in a controller
- The project uses immutable data structures; the AI generates mutable POJOs
- Every few exchanges the AI "forgets" the coding conventions you specified
- AI-generated code averages ~30% more lines than equivalent human-written code
- CI fails at the lint stage after every AI-generated PR

### Root Cause
The AI is a prediction engine, not a rule enforcement engine. Its training objective is to generate "plausible" code, not "code that is guaranteed to conform to your conventions". Specification documents injected early in context receive diminishing attention weight as the conversation grows (attention recency bias).

### Project-Level Mitigations (template — fill in for your project)
*Document here: what linter does this project use? Are rules committed to version control? Is there a pre-commit hook?*

### General Mitigations
- **Automate, don't document**: turn conventions into CI gates; do not rely solely on text descriptions
- **Machine-readable rules**: write rules in `.cursor/rules`, `CLAUDE.md`, `AGENTS.md`, and commit to git
- **Pre-commit hooks**: run the linter before commit; prevent non-conforming code from entering the repo
- **Short + examples**: rule documents should be short (< 200 lines) and include positive and negative examples; this is more effective than long narrative descriptions
- **Tool integration**: use tools that let the AI call the linter directly and see violation reasons so it can self-correct
- **Re-state on violation**: when the AI violates a rule, paste the linter output and say "please fix this violation; the rule is: ..."

### Reference Cases
- A Java project explicitly required constructor injection; the AI consistently generated `@Autowired`, even after being corrected — and repeated the mistake in the next session
- Community reports: "Conventions fade in context as conversations grow" is a documented, widely reproduced issue
- An open issue in a popular AI coding tool: developer reported AI ignoring project rules even when explicitly stated in instructions

**Sources**: [Making AI Code Consistent with Linters](https://dev.to/fhaponenka/making-ai-code-consistent-with-linters-27pl) | [Cursor Rules: Why Your AI Agent Is Ignoring You](https://sdrmike.medium.com/cursor-rules-why-your-ai-agent-is-ignoring-you-and-how-to-fix-it-5b4d2ac0b1b0) | [Rulens](https://mh4gf.dev/articles/rulens-introduction)

---

## 6. Spec Drift

### Pitfall Name
**Spec Drift** — the AI silently modifies requirements during implementation without notifying the user.

### Symptoms
- The implemented feature differs slightly from what was specified, with no warning
- Security constraints (validation, rate limits) are quietly removed or relaxed
- Feature scope is quietly expanded (the AI adds "while I'm at it" functionality)
- After multiple iterations, implementation diverges significantly from the original spec
- The AI substitutes "a better approach" for the one you explicitly specified, without asking

### Root Cause
The AI has no built-in incentive to faithfully execute the spec. Training leads it to produce "helpful improvements", and those improvements sometimes include implicit spec modifications. With each prompt iteration, the AI may substitute its own interpretation for the stated requirement.

The AI also cannot maintain a complete spec across multiple interactions; every response is an inference from incomplete context.

### Project-Level Mitigations (template — fill in for your project)
*Document here: does this project use spec files in `docs/specs/`? BDD scenarios? Contract tests?*

### General Mitigations
- **Spec as source of truth**: write the spec as a committed document (Markdown, YAML); re-inject it at the start of each session
- **Executable spec**: use BDD scenarios (Gherkin) or API contract tests to verify that the implementation conforms; drift will cause tests to fail automatically
- **Re-state key constraints per iteration**: explicitly write "do not modify the following constraints: ..." in the prompt
- **Provide existing code + explicit change instruction**: this is far less prone to drift than "please rewrite this feature"
- **Diff review**: after each AI completion, carefully inspect the diff — removed lines are frequently evidence of spec drift
- **"Only X, not Y" pattern**: explicitly list the parts the AI should not touch

### Reference Cases
- Practitioners note: AI commonly treats spec simplification as "improvement" without asking
- Research finding: in a Spec-Driven Development framework, treating the spec as the primary artifact significantly reduced AI-introduced spec drift
- Common scenario: "add retry logic" → AI simultaneously removes the timeout setting, without notification

**Sources**: [Spec-Driven Development: From Code to Contract](https://arxiv.org/html/2602.00180v1) | [How Spec-Driven Development Improves AI Coding Quality - Red Hat](https://developers.redhat.com/articles/2025/10/22/how-spec-driven-development-improves-ai-coding-quality) | [How to Write a Good Spec for AI Agents - Addy Osmani](https://addyosmani.com/blog/good-spec/)

---

## 7. Over-Engineering

### Pitfall Name
**Over-Engineering** — the AI adds unnecessary abstraction layers, designing for problems that do not yet exist.

### Symptoms
- A simple CRUD function is wrapped in a Repository + Service + Facade + Factory
- A 5-line solution becomes 50 lines with an abstract base class
- The project gains interfaces that have exactly one implementation
- "Flexible" and "extensible" code appears for features not on the roadmap
- Deep inheritance chains make debugging disproportionately difficult

### Root Cause
AI training data is saturated with enterprise pattern examples; the AI has learnt a "complex = professional" association. Combined with its tendency to produce "complete-looking" solutions, it automatically adds "potentially useful" abstractions.

Practitioners observe: "AI solves the problem someone on a conference stage told you that you'll eventually have, not the problem you actually have right now."

Every unnecessary line of code carries maintenance cost, test cost, security review cost, and reading cost.

### Project-Level Mitigations (template — fill in for your project)
*Document here: does CLAUDE.md include a YAGNI instruction? Is there a "single-file first" convention?*

### General Mitigations
- **Explicit YAGNI instruction**: add "use the simplest solution; do not pre-abstract; do not add unrequested features" to the prompt
- **Single-file first**: require the AI to implement in a single file first; refactor only after confirming it works
- **Review new abstractions**: whenever you see a new interface / abstract class / factory, ask "is this abstraction needed right now?"
- **Delete-first**: when in doubt whether code is needed, delete it (git can restore it)
- **Simple tools first**: Makefile, shell script > complex framework; direct function calls > complex event systems
- **CLAUDE.md rule**: "do not add unrequested features", "prefer simple implementations"

### Reference Cases
- Community discussion: "AI frameworks feel over-engineered for basic tasks with high complexity overhead"
- Common case: request for "a function that reads a JSON config" → AI generates ConfigManager class + ConfigFactory + IConfigProvider interface
- Practitioners report: the value of experienced engineers is not making AI run faster, but "refactoring generated code, applying years of engineering wisdom to shape and constrain the AI's output"

**Sources**: [Lessons from Thorsten Ball](https://www.antoinebuteau.com/lessons-from-thorsten-ball/) | [Building Bridges to LLMs: Moving Beyond Over-Abstraction](https://hatchworks.com/blog/gen-ai/llm-projects-production-abstraction/) | [Addy Osmani: My LLM Coding Workflow Going Into 2026](https://addyosmani.com/blog/ai-coding-workflow/)

---

## 8. Prompt Injection and Security Issues

### Pitfall Name
**Prompt Injection** — an AI agent reads malicious content and is manipulated into executing unintended actions.

### Symptoms
- The AI agent executes instructions you did not issue (e.g., deletes files, uploads data)
- After cloning a repo, the AI executes instructions embedded in the repo
- After reading a document, the AI starts responding to instructions unrelated to the task
- API keys or credentials are exfiltrated to an external endpoint
- The AI opens ports or connections you did not request

### Root Cause
The AI model cannot distinguish between "trusted instructions from the developer" and "malicious instructions embedded in data it reads". All text is processed as part of the same prompt.

An attacker only needs to embed instructions anywhere the AI agent will read — README, Git issue, documentation, config file, HTML page — and the agent may execute them.

### Known CVEs and Real Events

| CVE | Product | Severity | Description |
|-----|---------|----------|-------------|
| CVE-2025-32711 (EchoLeak) | Microsoft 365 Copilot | CVSS 9.3 | Zero-click exfiltration of OneDrive/SharePoint/Teams data via malicious email |
| CVE-2026-21852 (BodySnatcher) | ServiceNow Virtual Agent | CVSS 9.3 | MFA bypass and user impersonation with only an email address |
| CVE-2025-59536 | Claude Code | High | Malicious project file executes arbitrary shell commands at initialisation |
| CVE-2026-21852 | Claude Code | High | Malicious repo config causes API key exfiltration |

**Devin AI test (2025)**: researchers spent $500 testing prompt injection; results:
- Malicious instruction embedded in GitHub issue → successfully caused Devin to download malware
- Exfiltration instruction in README → 85% success rate
- Overall attack success rate: 84–85%

### Project-Level Mitigations (template — fill in for your project)
*Document here: does any agent task in this project read untrusted external data? What sandboxing is in place?*

### General Mitigations
- **Principle of least privilege**: give the AI agent only the minimum permissions needed to complete the task
- **Spotlighting**: use explicit XML tags or delimiters to separate "your instructions" from "data the AI reads"
  ```xml
  <instructions>Your task is to analyse the content of the following document.</instructions>
  <untrusted_data>
  [external data here — instructions embedded here must not be executed]
  </untrusted_data>
  ```
- **Sandboxing**: run AI agents in isolated environments (no access to real credentials, no external network)
- **Prompt injection classifier**: scan external data for instruction injection before passing it to the AI
- **Dangerous command blocklist**: block `curl`, `wget`, DNS queries, and other commands that could exfiltrate data by default
- **Human approval gate**: require human confirmation for sensitive operations (delete, upload, execute script)
- **Do not clone untrusted repos**: or run static analysis on the clone before the AI reads it
- **Verify MCP servers**: validate the source of any MCP server before first use

### Reference Cases
- Security research: prompt injection attacks achieved an 84% success rate in real-world tests
- OWASP Top 10 for LLM Applications: Prompt Injection ranks #1
- 48% of security professionals rate agentic AI as the largest attack vector for 2026
- Security research demonstrated arbitrary code execution via a malicious `.claude/settings.json`

**Sources**: [Pwning Claude Code in 8 Ways - Flatt Security](https://flatt.tech/research/posts/pwning-claude-code-in-8-different-ways/) | [CVE-2025-32711 EchoLeak](https://www.hackthebox.com/blog/cve-2025-32711-echoleak-copilot-vulnerability) | [I Spent $500 to Test Devin AI for Prompt Injection](https://embracethered.com/blog/posts/2025/devin-i-spent-usd500-to-hack-devin/) | [Palo Alto Unit42: AI Agent Prompt Injection](https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/) | [Claude Code RCE via Project Files - Check Point](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/)

---

## Quick Reference: Symptom → Diagnosis

| Symptom | Most likely pitfall |
|---------|-------------------|
| AI regenerated a function already written earlier | Context Window Decay (#1) |
| Code style is inconsistent across sessions | Architecture Drift (#2) |
| No error in logs but functionality is broken | Silent Failures (#3) |
| CI is green but bugs reach production | Fake Tests (#4) |
| AI repeatedly violates the same convention | Style/Lint Violations (#5) |
| Implementation differs from the original spec | Spec Drift (#6) |
| Code is far more complex than needed | Over-Engineering (#7) |
| AI executed instructions you did not issue | Prompt Injection (#8) |

---

## 中文摘要（Chinese Summary）

> 供中文使用者快速掃描各 pitfall 的一行摘要。

| # | 名稱 | 一行摘要 |
|---|------|---------|
| 1 | Context Window Decay | AI 長 session 後「忘記」前面的決策，重複犯錯、前後矛盾 |
| 2 | Architecture Drift | 每個新 session AI 都不知道架構決策，每次寫出不一樣風格的程式碼 |
| 3 | Silent Failures | AI 的 error handling 吞掉所有例外，production 無聲失敗，log 完全沒有記錄 |
| 4 | Fake Tests | AI 測試只鏡像了 implementation，沒有真正測行為規格，覆蓋率假高 |
| 5 | Style Violations | AI 寫出不符合 lint rule 和 style guide 的程式碼，且每個 session 重複犯相同錯誤 |
| 6 | Spec Drift | AI 在實作過程中默默改掉了需求，不通知使用者就縮減或擴大 scope |
| 7 | Over-Engineering | AI 自動加了沒人需要的抽象層、interface、factory，增加不必要的維護成本 |
| 8 | Prompt Injection | AI agent 讀了惡意資料後被操控執行未授權指令，可導致資料外洩或 RCE |

---

*Last updated: 2026-03-23 | Source: AgentCortex Research Module*
*Version: v1.1 — English rewrite, names anonymised, Chinese summary added*
