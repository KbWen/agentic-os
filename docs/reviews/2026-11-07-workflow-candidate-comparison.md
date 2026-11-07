# Workflow candidate comparison: 2026-11-07

Matched baseline-vs-candidate comparison for the staged candidates of #231, #225 and #226 (see `2026-11-06-workflow-candidate-assessment.md`). Baseline: main at b65d54e. Candidate: the staged wording on top of it. The roundtable design was fixed and `plan.json` was written before any run. Rules were applied mechanically, then adjudicated by the owner where a frozen bar conflicted with the evidence.

## Setup
- **Model:** Claude Haiku in both arms, executor and grader.
- **Spend:** USD 4.28 in total, from 207 calls. Each call's final `total_cost_usd` was summed. No retries, no VOID runs.
- **Wording candidates (C1, M4, M7, M9):** each packet from `.agentcortex/eval/` ran 3 reps per arm. The only difference between arms was the exact section text, injected through `--append-system-prompt`; executors had no tools. An arm-blind Haiku grader scored each transcript against the packet's hidden oracle, and the lexical scorer ran as a cross-check (33 disagreements, recorded, not resolved).
- **Injection is an upper bound.** In natural plain-entry runs, agents read none of these files (2 runs here, 0 characters; 32 earlier runs agree).
- **B:** a real explicit `/bootstrap` on fixtures deployed from each arm. Three cases (matching branch, non-matching branch, resume), 2 reps per arm per case, 12 runs.

## Results
| Candidate | Baseline | Candidate | Verdict |
|---|---|---|---|
| C1 Lite red-team cap (#225) | 7 true / 3 false findings; on the 3-defect case, 2 found in 1/3 reps and 1 found in 2/3 | 9 true / 1 false; 2 of 3 found in every rep; no safety loss | **Adopted.** Neither arm found the third defect, so the frozen bar "every fixture defect found" was not met. The owner adopted on the strict improvement (chat, 2026-11-07); the spec records the amended bar. |
| M4 §9.2 contextual follow-up (#226) | 12/15 decisions correct, 2 safety flags | 11/15, 1 safety flag | Retain baseline: not all-correct, no improvement. |
| M7 skill-count coaching (#226) | 6/9, 1 safety flag | 5/9, 3 safety flags | Retain baseline: worse on noisy grades. The spec requires a demonstrated benefit. |
| M9 doc-lookup tool wording (#226) | 10/15; no invented tool; 3 safety flags, 3 false findings | 10/15; no invented tool; 0 safety flags, 0 false findings | Retain baseline: no headroom on the predeclared metric (invented tool calls). The cleaner secondary grades are noted, not scored. |
| B bootstrap read scopes (#231) | 50,618 bootstrap.md chars read | 50,353 (−0.5%) | Retain baseline: both arms read the whole file in one Read call, far from the 20% bar. Obligation misses were the same or worse in the baseline. |
| A context-reuse wording (ADR-001 D3) | n/a | n/a | Adopted by owner decision (chat, 2026-11-07). No live test, because guides are not read on plain entry. |

## Limitations
- The model was Haiku only, n is at most 3 per cell, and each packet is small.
- Grades are noisy: identical outputs were graded differently across reps.
- Results say whether the text works when read. They do not say whether agents read it.
- Raw runs, grades and scripts are kept locally (gitignored): `.agentcortex/context/private/candidate-compare/`.
