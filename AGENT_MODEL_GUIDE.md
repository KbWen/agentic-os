# AgentCortex v3.5.3 Model Selection & Decision Guide (Human-Only)

This guide is for **You (Human)**. It will not be loaded into the AI prompt. Its purpose is to save tokens and maximize development efficiency.

## 🧠 Core Principle: Fast-First

**Default to Gemini 1.5 Flash (or equivalent fast models like Claude 3.5 Haiku).** Only switch to Pro/Advanced models if the fast model fails to solve the problem.

---

## ✅ Use Fast Models (Daily 80%)

**Features: Fast, low cost, large context.**
*(Examples: Gemini 1.5 Flash, Claude 3.5 Haiku, GPT-4o-mini)*

- **Code Migration**: Moving features from legacy projects to new files.
- **Formatting**: CSS touch-ups, Markdown cleanup, JSON/CSV conversion.
- **Writing Tests**: Generating Unit Test cases.
- **Simple Bugs**: Fixing TypeScript lint errors or syntax issues.
- **Localization**: Traditional/Simplified Chinese conversion, i18n entries.
- **Doc Summarization**: Extracting key points from long articles.

## 🔴 Manual Switch to Pro/Advanced (Critical 20%)

**Features: Deep reasoning, architectural design, complex debugging.**
*(Examples: Claude 3.5 Sonnet / Opus, GPT-4o, Gemini 1.5 Pro)*

- **System Design**: Planning data relationships and protocols for new modules from scratch.
- **Core Refactoring**: Modifying 3+ highly coupled core files.
- **Logic Debugging**: Investigating race conditions or low-level memory leaks.
- **Security Audit**: Comprehensive scanning of encryption or authorization logic.
- **Performance Analysis**: Database query optimization and bottleneck diagnosis.

---

## 💡 Cost-Saving Tips

1. **Let Flash Try First**: Even for longer tasks, Flash can read it all. If the logic is wrong, copy the conversation and switch to Pro.
2. **Lean Context**: Provide only necessary file paths; avoid `ls -R` which pads input tokens.
3. **Phase Execution**: Let Flash extract a "change list" first. Once verified, let it implement in segments.
