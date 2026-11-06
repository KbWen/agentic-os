---
title: "DELETE-bias Workflow Runbook"
owner: governance
review_cadence: "as-needed"
review_trigger: "governance rule changes"
supersedes: ""
superseded_by: ""
---

# DELETE-bias Workflow Runbook

The DELETE-bias workflow answers: "Is this governance rule actually enforced by
agents in practice, or is it dead letter?" It operationalizes the Global Lesson
`[enforcement][HIGH]`: "a MUST without a hook/validator/test is theatre — delete
it."

## When to run

- Before deleting or weakening a MUST-bearing governance rule.
- After adding new eval cases, to confirm cases flip on the target rule.
- Periodically (e.g., at `/retro`) to identify candidate rules for
  pruning, rewrite, or promotion to a machine-checkable validator.

## Prerequisites

- Python 3.9+ on PATH.
- One of:
  - A directory of transcript files (`<case-id>.txt`) for transcript mode, OR
  - A live agent command (`--agent-cmd`) for live mode.

## Transcript mode vs live mode

**Transcript mode** (offline, reproducible):
- Collect agent responses for each case manually or via automation.
- Save them as `<case-id>.txt` in a directory.
- Run: `bash run_delete_bias_diff.sh --eval governance.yaml --transcripts /path/to/dir`

**Live mode** (online, requires a CLI agent):
- Run: `bash run_delete_bias_diff.sh --eval governance.yaml --agent-cmd "claude -p {prompt}"`
- The runner spawns the agent once per case. Prompts are passed safely
  (no shell interpolation of case content).

## Step-by-step procedure

### Interactive

1. Run the script without `--baseline`/`--mutated`:
   ```
   bash .agentcortex/tools/run_delete_bias_diff.sh \
       --eval .agentcortex/eval/governance.yaml \
       --transcripts /path/to/transcripts
   ```
2. The script captures a **baseline** run and prints results.
3. The script pauses: "Mutate the rule now, press Enter."
4. Edit or comment out the rule you are testing in the governance file.
5. Press Enter. The script captures a **mutated** run.
6. The script diffs case statuses by id and prints the verdict.

### Non-interactive (CI / scripted)

Supply both JSON files:
```
bash .agentcortex/tools/run_delete_bias_diff.sh \
    --baseline baseline.json \
    --mutated  mutated.json
```

Generate baseline/mutated files separately:
```
python .agentcortex/tools/run_governance_eval.py \
    --eval .agentcortex/eval/governance.yaml \
    --transcripts /path/to/transcripts \
    --format json > baseline.json

# (Edit the rule)

python .agentcortex/tools/run_governance_eval.py \
    --eval .agentcortex/eval/governance.yaml \
    --transcripts /path/to/transcripts \
    --format json > mutated.json
```

## How to read coverage

Run `python .agentcortex/tools/run_governance_eval.py --coverage` to see:
- Total MUST-bearing section anchors extracted from the three governance files.
- How many cases protect each anchor.
- Which anchors have **zero** guarding cases.

A zero-coverage rule means: "we have no behavioral test for this MUST." That is
a coverage gap — not proof the rule is vacuous.

`validate.sh` and `validate.ps1` run this automatically (capability-by-presence)
and WARN when zero-coverage rules exist.

## Verdicts

| Outcome | Meaning |
|---|---|
| **Zero flips** | Rule is vacuous for the current case set. Candidate for deletion — but first check if there is a coverage gap (add cases). |
| **Any flips** | Rule is load-bearing. At least one case changes from pass to fail (or vice versa) when the rule is removed. Do not delete without replacing. |

The non-interactive comparer emits an `INCOMPLETE` error and exits non-zero without a
verdict if either result is malformed, empty, has duplicate/invalid case rows, includes
anything other than `pass`/`fail`, or has a different case-id cohort. The eval runner's
missing-transcript `skipped` status remains valid runner output, but it cannot support a
DELETE-bias comparison. Same ids do not prove equivalent prompts, contexts, or coverage;
review baseline failures and the actual fixtures before interpreting flips. These are
lexical diagnostic signals, not proof that a rule is safe to delete.

## Honest boundaries

This measurement is **point-in-time**, not always-on enforcement:
- Cases are run manually or via dispatch; the harness does not run on every
  commit by default (Non-goal from spec).
- Scoring is **substring/regex-based on transcripts**. It is intentionally
  paraphrase-brittle — an agent that says "I cannot skip gates" passes, but
  one that rephrases without the expected terms may false-fail or false-pass.
  Tune expect/forbid pairs to account for common reformulations.
- A "vacuous" verdict means "vacuous for the current case set" — not globally
  vacuous. Add targeted cases before drawing a deletion conclusion.
- The diff workflow produces **evidence for a human decision**. Automatic
  deletion is a Non-goal and is not implemented.
