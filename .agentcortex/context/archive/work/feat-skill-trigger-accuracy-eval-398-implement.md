# Compacted evidence — feat/skill-trigger-accuracy-eval-398

Moved **verbatim** from the active Work Log `## Evidence` under `/handoff §6` at implement completion, because the log stood at 69 bytes of headroom against its 12KB cap with review/test/handoff/ship still to run. Completed-phase evidence only; nothing summarized, folded, or rewritten.

---

### Implement

**The measurement point matters and was nearly wrong.** `skill_is_candidate` returns `is_candidate = matches["manual"] or phase_ready`, so scoring on it would make every positive trivially pass and every negative impossible for any case whose phase sits in the skill's `phase_scope`. The runner scores `matches["manual"]`, and treats an empty match dict as INERT rather than a negative — that is the `platforms: claude` vs `claude-code` trap, which would otherwise read as a passing negative while measuring nothing.

**Live run**: 40 cases — 27 pass, 0 fail, 13 known gap (at baseline 13), 0 inert, coverage 14/14, exit 0.

**Guards proved real by mutating the RUNNER, not the fixture** — ratchet check, INERT-as-PASS, uncovered-skill check and failed-case check each removed in turn; all four turned the corresponding test RED. Runner byte-restored after each.

**A real portability bug was found and fixed, not worked around.** `--format json` emitted the zh-TW prompts as **cp950** on this Windows box, producing output no JSON parser accepts (`Invalid \escape`). Diagnosed by byte-comparing the stream against both codecs rather than guessing; fixed with the house `sys.stdout.reconfigure(encoding="utf-8")` guard used by `check_ssot_caps.py` / `check_routing_actions.py`. This would have hit any Windows adopter piping the runner to `jq` — repo-gotchas #13's class.

**AC-5**: `run_governance_eval.py` is untouched; `--coverage` still reports `45 / 28 / 28`, exit 0.
`pytest .agentcortex/tests/test_skill_trigger_eval.py` → **13 passed**. `bash -n deploy.sh` clean; `test_validator_absent_tool_signal.py` **6 passed** (the two `deploy.sh` sites agree).

### Pre-decision grounding

Matcher probe table, DEFECT-1/DEFECT-2, the `platforms` schema trap and the exit-code precedent are in `docs/specs/skill-trigger-accuracy-eval.md` §Measured baseline (moved there at spec time; the log was at 97% of its cap with six phases left). Headline: a free-text path already exists — `trigger_runtime_core.py:909` feeds `[entry["id"], *intent_patterns]` into `values_match`, which accepts a whole sentence. That settled AC-3 in favour of static scoring.
