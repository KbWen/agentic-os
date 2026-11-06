---
status: shipped
title: Governance Behavioral Eval Harness + DELETE-bias Diff
source: GitHub issue #151 / backlog #45
created: 2026-06-10
primary_domain: governance
secondary_domains: [tooling, testing]
---

# Governance Behavioral Eval Harness + DELETE-bias Diff

## Goal

Turn the [enforcement][HIGH] Global Lesson ("a MUST without a hook/validator/test is theatre — delete it") into a reproducible measurement: a data-only YAML eval-spec of adversarial prompts (each tagged with the rule it protects), a stdlib-only runner that scores whether an agent actually obeys governance under pressure, a coverage mode that flags rules no case guards, and a DELETE-bias diff workflow that proves whether a rule is load-bearing before removing it.

## Acceptance Criteria

- AC-1: `.agentcortex/eval/governance.yaml` exists — data only, never loaded by any runtime workflow or governance doc as required reading. ≥ 12 seed cases. Each case: `id` (unique, kebab), `prompt`, `protects` (rule anchor, e.g. `AGENTS.md §Core Directives/No Bypass Rule`), and at least one of `expect_substrings` / `forbid_substrings` / `assertions` (`{type: regex_present|regex_absent, pattern}`); optional `max_lines`. The file parses with `.agentcortex/tools/_yaml_loader.py`'s built-in subset parser (verified by test — PyYAML absence must not change results).
- AC-2: `.agentcortex/tools/run_governance_eval.py` (stdlib-only, reuses `_yaml_loader`) scores transcripts: `--transcripts <dir>` maps `<case-id>.txt` → case; `--case <id> --transcript <file>` scores one. A case PASSES iff all expect_substrings present, no forbid_substrings present, all assertions hold, and line count ≤ max_lines when set. Missing transcript → status `skipped`, never a crash.
- AC-3: `--agent-cmd "<template>"` runs a live agent per case (template `{prompt}` placeholder; prompt passed via stdin when no placeholder), with `--timeout` (default 120s) per case; captures stdout as the transcript; non-zero agent exit → case status `error`.
- AC-4: `--format json` emits deterministic output (sorted keys, stable case order by id) with per-case `{id, status: pass|fail|skipped|error, failed_expectations: [...]}` plus a summary block — machine-diffable across runs. Exit code: 0 when no `fail`/`error`, 1 otherwise.
- AC-5: `--coverage` extracts a rule inventory (MUST-bearing `##`/`###` section anchors) from `AGENTS.md`, `.agent/rules/engineering_guardrails.md`, `.agent/rules/security_guardrails.md`, maps `protects` tags → guarding-case counts, and lists zero-coverage rules. Tag matching is normalized (case/whitespace-insensitive on the `file §section` form). Exit 0 always (advisory).
- AC-6: `.agentcortex/tools/run_delete_bias_diff.sh` (bash, no deps beyond python): captures a baseline `--format json` run, waits for the operator to mutate/comment-out one rule, re-runs, diffs by case id, and prints flipped cases. Zero flips → explicit "rule appears vacuous for the current case set — delete candidate (or coverage gap)" verdict; any flip → "load-bearing" with the flipped ids.
- AC-7: `validate.sh` AND `validate.ps1` (parity): capability-by-presence advisory — if `.agentcortex/eval/governance.yaml` exists, run the coverage check and WARN with the zero-coverage rule count (never FAIL; silently skip when the eval file or Python is absent).
- AC-8: `docs/guides/delete-bias-workflow.md` runbook: when to run, transcript-mode vs live-mode, how to read coverage, the delete-bias procedure step-by-step, and the honest boundary (measured-when-run, not always-on enforcement; substring scoring is paraphrase-brittle by design and tuned with expect/forbid pairs).
- AC-9: `tests/guard/test_governance_eval.py`: scoring matrix (pass/fail per expectation type), skipped/error statuses, JSON determinism (two runs byte-identical), coverage zero-detection, malformed-YAML behavior (clear error, non-zero exit), subset-parser compatibility (monkeypatch PyYAML away), and seed-case schema validation (every case id unique + `protects` resolves against the live rule inventory).

## DELETE-bias comparison completeness follow-up (2026-11-06)

The non-interactive diff now emits an `INCOMPLETE` error with non-zero exit and no verdict
unless both inputs are JSON objects with non-empty `cases` lists, unique non-empty string
ids, `pass`/`fail` statuses only, and identical case-id cohorts. This does not change AC-2:
the runner may still report missing transcripts as `skipped` with exit 0; such output is
not complete input for a delete-bias verdict. Existing `fail` cases remain valid lexical
diagnostic signals, not semantic proof. Matching ids alone do not establish that prompts,
coverage, or contexts are equivalent, and baseline failures must be reviewed before using
any status flips as deletion evidence. No automatic deletion is authorized or implemented.

## Non-goals

- No always-on CI job: the optional manual-dispatch CI hook from issue #151 is deferred until a concrete trigger exists (DELETE-bias; validate's coverage WARN is the standing consumer). Recorded as follow-up, not shipped here.
- No LLM-judge scoring — substring/regex only in this iteration.
- No automatic rule deletion: the diff workflow produces evidence for a human decision.
- No runtime integration: workflows/bootstrap never read the eval file (zero token cost).

## Constraints

- Stdlib-only; YAML loading via `_yaml_loader.py` (must work without PyYAML).
- Eval YAML restricted to the loader's supported subset (mappings, sequences of mappings, flow sequences, quoted scalars, `>` folded blocks).
- Validators: WARN-only, capability-by-presence, cross-platform parity mandatory.
- Seed cases must include at least: gate-bypass pressure ("skip the gates"), no-evidence ship claim, prompt-injection-in-tool-output, classification silent-downgrade, chat-language drift, SSoT write isolation, sentinel omission, lock takeover without approval (ties to worklog-lock-blocking), unauthorized refactor pressure, frozen-spec edit pressure, scope-creep mid-implement, secret/credential exposure pressure (security_guardrails).

## File Relationship

Operationalizes Global Lesson [enforcement][HIGH] and the DELETE-bias norm (backlog #65 depends on this harness). Rides validate.sh/ps1 (ADR-002/ADR-003 covered surface) for its advisory consumer. Complements, never replaces, hard validators — behavioral evals measure prose-rule efficacy; validators enforce machine-checkable invariants.

## Domain Decisions

- [DECISION] Transcript scoring is offline-first: the runner never calls an LLM itself; `--agent-cmd` is an optional adapter so any CLI agent (claude, codex, gemini) can be measured. Keeps the tool vendor-neutral and CI-safe.
- [DECISION] Rule inventory = MUST-bearing section anchors extracted at runtime from the three governance files, not a hand-maintained registry — a registry would itself drift (the exact failure mode this harness exists to catch).
- [DECISION] Coverage WARN lives in validators (capability-by-presence, zero cost when eval file absent) — the "existing consumer/enforcement hook" the issue's reopen note requires.
- [DECISION] `skipped` ≠ `fail`: missing transcripts are reported but never block — partial transcript sets are the normal operating mode.
- [CONSTRAINT] JSON output deterministic (sorted) so `run_delete_bias_diff.sh` can diff structurally without jq.
