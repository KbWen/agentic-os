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

---

## Review rounds (moved verbatim at /handoff §6, 2026-09-01)

### Review rounds — compacted

Round 1 **NOT READY** (1 CRITICAL / 4 HIGH / 6 MEDIUM / 3 LOW); round 2 a 3-seat final roundtable that **rejected my delete-and-replace proposal** — it bypassed `skill_is_candidate` (a second matcher, forbidden by #165), missed 2 resolver-internal regressions, its headline number came from running the suite's runner without its guards, and 20 of its 22 corpus rows were verbatim copies of the file it would delete. Adopted the smallest honest delta instead. Full tables, rejected claims and the two premise corrections (D-4→D-5; `intent_patterns` has no runtime consumer): `docs/reviews/2026-09-01-skill-trigger-eval-review.md` and the spec's §Scope limitation / §Roundtable.

---

## Moved at /handoff §6 (2026-09-01), verbatim

## Phase Summary

- bootstrap: classified `feature` per §10.1 — a new tool crossing into `trigger_runtime_core`'s import graph, so the quick-win fast-path is unavailable and review/test are hard gates. ADR coverage exit 0 (ADR-006). ⚡ ACX
- spec: `docs/specs/skill-trigger-accuracy-eval.md` written after a 3-seat roundtable + tenth man. Scope held at the issue's original shape; the substitution proposed mid-roundtable was refuted on five verified grounds. AC-3 settled static-with-reuse.
- plan: 7 target files. Spec frozen (§4.2). Backlog #165 `Pending → In Progress` (row tier is `feature`, matching the frozen classification). D-4 settled by evidence (spec §D-4). Fast Lane | Confidence: 90% — high, with one stated assumption (see §Known Risk).
- implement: 40 cases / 14 positives / 13 near-miss negatives / 13 zh-TW known-gap arms; runner delegates to the shipped resolver and scores `matches["manual"]`, never `is_candidate`. Deploy wired at all three sites. **Assumption held**: lexically-disjoint negatives work — 13/13 correctly return False.

---


## Evidence

### Bootstrap / spec / plan / implement — compacted

Moved verbatim to `.agentcortex/context/archive/work/feat-skill-trigger-accuracy-eval-398-implement.md` under `/handoff §6` (cap pressure; completed phases only). First-pass result: **40 cases — 27 pass, 0 fail, 13 known gap, 0 inert, coverage 14/14, exit 0**; guard tests 13 passed; four runner guards mutation-proved; deploy manifest golden 1 passed. That result is superseded by the review below.

### Review rounds

Both rounds moved verbatim to `archive/work/feat-skill-trigger-accuracy-eval-398-implement.md` under `/handoff §6`. Verdicts: round 1 **NOT READY** (14 findings, `6534cc0`), round 2 **PASS** after a 3-seat roundtable rejected a delete-and-replace proposal. Tables and rejected claims: `docs/reviews/2026-09-01-skill-trigger-eval-review.md`; premise corrections: spec §Scope limitation / §D-5.

Final evidence: **22 guards green**; cross-skill rule mutation-proved on 4 over-trigger regressions; backlog validation **3 passed**; deploy manifest golden **1 passed** after the unship; `run_skill_eval` appears **0×** in `deploy.sh` and the golden.
