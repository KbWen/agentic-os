---
status: frozen
frozen: 2026-11-27
date: 2026-11-27
classification: feature
primary_domain: governance
signal_tier: none
signal_tier_note: "Rewords three existing rules; adds no rule. Directive count goes down, never up."
backlog: 227
---

# Stack-Neutral Wording for Three Guardrail Rules

## Problem

`.agent/rules/engineering_guardrails.md` is scoped to every project (`## Scope: Global`), yet three rules are written in Dart/Flutter idioms (prompt audit F1, 2026-10-13):

- §1.2: conversions MUST use named methods "e.g., `fromRecord()`, `toRecord()`".
- §5.2: Service/Provider errors MUST "`return null` or a sealed error type". In a Python or Java downstream this contradicts idiomatic exceptions, so a model following the rule literally writes non-idiomatic code.
- §5.2a: the prohibited list leads with `debugPrint()`.

Owner decision 2026-10-13 (chat): generalize. Keep the principles; drop the language-specific wording.

## Acceptance Criteria

- **AC-1** §1.2 states the principle without a stack idiom: storage↔domain conversions are explicit and defined in one named place; implicit casts and ad-hoc field copying at call sites are ruled out.
- **AC-2** §5.2 states the principle without `return null` or "sealed error type": an error crossing a Service/Provider boundary follows the module's declared error contract (an error value, a result type, or a documented exception type), and an unhandled exception escaping that boundary stays a Gate FAIL.
- **AC-3** §5.2a's prohibited sole-error-path line names the property (stripped, tree-shaken or no-op'd in release builds, or reaching no production collector), not `debugPrint()`.
- **AC-4** The directive count of `engineering_guardrails.md` does not grow (`tests/ci/test_directive_count_ratchet.py`); if it drops, the baseline in `.agentcortex/metadata/directive-count-baseline.json` is lowered in the same change.
- **AC-5** None of `fromRecord`, `toRecord`, `return null`, `sealed error`, `debugPrint` remains in `engineering_guardrails.md`.

## Non-goals

- The other examples in the same file (`Logger.error()`, `errorReporter.capture()`) are already stack-neutral; left as they are.
- `review.md:89`, `ship.md:91-92` and `.agents/skills/production-readiness/SKILL.md` cite `debugPrint` as one example among several debug-only APIs. They stay consistent with the reworded §5.2a, and SKILL.md edits are bound by the token ceiling (backlog #199). Out of scope.
- No change to which sections load in which mode, to §5.1 ("Service class or Provider"), or to any gate's enforcement.

## Verification

- `python -m pytest -q tests/ci/test_directive_count_ratchet.py`
- `grep -nE 'fromRecord|toRecord|return null|sealed error|debugPrint' .agent/rules/engineering_guardrails.md` returns nothing.
- `bash .agentcortex/bin/validate.sh` reports `fail=0`; lifecycle token tests stay under their ceiling.
