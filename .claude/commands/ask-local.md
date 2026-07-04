# /ask-local

Execute the canonical workflow: `.agent/workflows/ask-local.md`

## Execution

Follow every step in `.agent/workflows/ask-local.md` sequentially.
The user's task description is: $ARGUMENTS

- [OPTIONAL MODULE] Requires a reachable OpenAI-compatible endpoint (Ollama / LM Studio / vLLM).
- If no endpoint is reachable, silently fall back to native execution per `engineering_guardrails.md` §8.2.
- End response with ⚡ ACX.
