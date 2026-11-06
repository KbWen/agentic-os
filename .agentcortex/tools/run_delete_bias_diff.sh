#!/usr/bin/env bash
# run_delete_bias_diff.sh — DELETE-bias workflow: prove whether a governance rule
# is load-bearing before removing it.
#
# Usage (interactive):
#   bash run_delete_bias_diff.sh [--eval <path>] [--transcripts <dir>] [--agent-cmd <cmd>]
#
# Usage (non-interactive, supply both baseline and mutated JSON):
#   bash run_delete_bias_diff.sh --baseline baseline.json --mutated mutated.json
#
# Workflow (interactive):
#   1. Capture baseline --format json run.
#   2. Print the baseline result, then pause: "Mutate the rule now, press Enter".
#   3. Re-run with same args to capture mutated result.
#   4. Diff by case id: print flipped statuses (pass→fail or fail→pass).
#   5. Zero flips → "vacuous rule" verdict; any flip → "load-bearing" verdict.
#
# Deps: bash, python (for run_governance_eval.py and diff logic).
# No jq required.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVAL_PY="$SCRIPT_DIR/run_governance_eval.py"

# --- Detect python ---
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "error: python not found on PATH" >&2
    exit 1
fi

# --- Argument parsing ---
# RUNNER_ARGS is a bash ARRAY: values like --agent-cmd "claude -p {prompt}" or
# paths with spaces must survive as single argv elements (word-splitting a
# string here silently broke the documented live mode).
RUNNER_ARGS=()
BASELINE_FILE=""
MUTATED_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --eval) RUNNER_ARGS+=(--eval "$2"); shift 2 ;;
        --transcripts) RUNNER_ARGS+=(--transcripts "$2"); shift 2 ;;
        --agent-cmd) RUNNER_ARGS+=(--agent-cmd "$2"); shift 2 ;;
        --timeout) RUNNER_ARGS+=(--timeout "$2"); shift 2 ;;
        --baseline) BASELINE_FILE="$2"; shift 2 ;;
        --mutated) MUTATED_FILE="$2"; shift 2 ;;
        *) echo "error: unknown argument: $1" >&2; exit 1 ;;
    esac
done

_run_eval() {
    local label="$1"
    if [[ ${#RUNNER_ARGS[@]} -gt 0 ]]; then
        "$PYTHON" "$EVAL_PY" "${RUNNER_ARGS[@]}" --format json 2>&1
    else
        echo "error: no eval arguments provided (use --transcripts, --agent-cmd, or --baseline/--mutated)" >&2
        exit 1
    fi
}

# --- Non-interactive mode: both files supplied ---
if [[ -n "$BASELINE_FILE" && -n "$MUTATED_FILE" ]]; then
    if [[ ! -f "$BASELINE_FILE" ]]; then
        echo "error: baseline file not found: $BASELINE_FILE" >&2; exit 1
    fi
    if [[ ! -f "$MUTATED_FILE" ]]; then
        echo "error: mutated file not found: $MUTATED_FILE" >&2; exit 1
    fi
    BASELINE_JSON="$(cat "$BASELINE_FILE")"
    MUTATED_JSON="$(cat "$MUTATED_FILE")"
else
    # --- Interactive mode ---
    echo ""
    echo "=== DELETE-bias Diff Workflow ==="
    echo ""
    echo "Step 1: Capturing BASELINE eval run..."
    BASELINE_JSON="$(_run_eval "baseline" || true)"
    echo ""
    echo "--- Baseline result ---"
    echo "$BASELINE_JSON"
    echo "---"
    echo ""
    echo "Step 2: Mutate the rule now (comment it out, delete it, etc.),"
    echo "        then press Enter to continue..."
    read -r _
    echo ""
    echo "Step 3: Capturing MUTATED eval run..."
    MUTATED_JSON="$(_run_eval "mutated" || true)"
    echo ""
    echo "--- Mutated result ---"
    echo "$MUTATED_JSON"
    echo "---"
fi

# --- Step 4: Diff by case id using python (no jq) ---
echo ""
echo "=== Diff: flipped case statuses ==="
"$PYTHON" - <<'PYEOF' "$BASELINE_JSON" "$MUTATED_JSON"
import json, sys

baseline_text = sys.argv[1]
mutated_text  = sys.argv[2]

def incomplete(message):
    print(f"error: INCOMPLETE comparison: {message}", file=sys.stderr)
    sys.exit(2)

def parse_complete_result(text, label):
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        incomplete(f"{label} JSON is malformed at line {exc.lineno}, column {exc.colno}")
    if not isinstance(data, dict):
        incomplete(f"{label} result must be a JSON object")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        incomplete(f"{label} result must contain a non-empty cases list")

    by_id = {}
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            incomplete(f"{label} case at index {index} must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            incomplete(f"{label} case at index {index} must have a non-empty string id")
        if case_id in by_id:
            incomplete(f"{label} result contains duplicate case ids")
        status = case.get("status")
        if status not in ("pass", "fail"):
            incomplete(f"{label} result contains a status outside pass/fail")
        by_id[case_id] = status
    return by_id

base_map = parse_complete_result(baseline_text, "baseline")
mut_map = parse_complete_result(mutated_text, "mutated")
if set(base_map) != set(mut_map):
    incomplete("baseline and mutated case cohorts differ")

all_ids = sorted(base_map)
flipped = []
for cid in all_ids:
    b = base_map[cid]
    m = mut_map[cid]
    if b != m:
        flipped.append((cid, b, m))

if not flipped:
    print("Zero status flips detected.")
    print()
    print("Verdict: rule appears VACUOUS for the current case set —")
    print("  delete candidate (or coverage gap: add cases that exercise this rule).")
else:
    print(f"{len(flipped)} case(s) changed status (load-bearing signal):")
    for cid, b, m in flipped:
        print(f"  [{cid}]  {b} -> {m}")
    print()
    print("Verdict: rule appears LOAD-BEARING — these cases flip when the rule is removed.")
    print("  Do NOT delete without replacing with an equivalent constraint.")
PYEOF

echo ""
