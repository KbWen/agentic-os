#!/usr/bin/env python3
"""Token lifecycle baseline + drift detector (backlog #51 / issue #157).

Stores a per-scenario token-cost baseline and compares the live analysis against
it, surfacing GROWTH drift (a governance change inflated token cost) before merge.
Reuses ``analyze_token_lifecycle.analyze()`` — no re-implementation of the model.

Modes:
  --init     seed the baseline (refuses if one already exists; use --apply)
  --apply    (re)write the baseline from the current analysis
  (default)  --dry-run: compare current vs baseline; exit non-zero if any scenario
             or aggregate GREW beyond slack, or a scenario is missing from the
             baseline. Shrink beyond slack is advisory (exit 0).

Drift direction is intentionally asymmetric: growth has teeth (exit != 0); shrink
only nudges you to run --apply so the baseline ratchets DOWN. Trimming token cost
is never punished.

Always reads/writes JSON as UTF-8: the default Windows code page (cp950) would
corrupt the non-ASCII content carried in sibling metadata files.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_SLACK = 0.10
BASELINE_REL = ".agentcortex/metadata/lifecycle-baseline.json"

_DOC = (
    "Token lifecycle baseline (backlog #51 / issue #157). Per-scenario "
    "current_total_tokens + aggregate registry/compact-index tokens, produced by "
    "analyze_token_lifecycle.py. GROWTH beyond slack_default is drift: "
    "update_lifecycle_baseline.py --dry-run exits non-zero and validate.sh WARNs. "
    "Regenerate intentionally with --apply after a legitimate scenario/workflow "
    "change. Schema deliberately omits user-/env-specific memory-file tokens — only "
    "deterministic repo-local signals are baselined."
)


def _load_analyzer(root: Path):
    """Import the existing analyzer from the tools dir and return analyze()."""
    sys.path.insert(0, str(root / ".agentcortex" / "tools"))
    import analyze_token_lifecycle  # noqa: E402  (path injected above)

    return analyze_token_lifecycle.analyze


def current_snapshot(root: Path) -> dict[str, Any]:
    """Reduce the full analyzer payload to the baselined signals."""
    analyze = _load_analyzer(root)
    payload = analyze(root)
    baselines = {
        r["id"]: {"current_total_tokens": r["current_total_tokens"]}
        for r in payload["results"]
    }
    aggregate = {
        "registry_tokens": payload["registry_tokens"],
        "compact_index_tokens": payload["compact_index_tokens"],
    }
    return {"baselines": baselines, "aggregate": aggregate}


def write_baseline(path: Path, snapshot: dict[str, Any], slack: float) -> None:
    doc = {
        "_doc": _DOC,
        "version": 1,
        "last_updated": datetime.date.today().isoformat(),
        "slack_default": slack,
        "baselines": snapshot["baselines"],
        "aggregate": snapshot["aggregate"],
    }
    # 3.9-safe LF write: Path.write_text() gained newline= only in Python 3.10,
    # and this repo's CI floor is 3.9 (backlog #164; same pattern as the #160 fix).
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, indent=2) + "\n")


def load_baseline(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_pct(ratio: float | None) -> str:
    return f"{ratio * 100:+.1f}%" if ratio is not None else "-"


def _classify(base: int | None, cur: int | None, slack: float):
    """Return (ratio, status, is_growth) for one row."""
    if base is None:
        return None, "NEW (missing from baseline)", True
    if cur is None:
        return None, "stale (run --apply)", False
    ratio = (cur - base) / base if base else 0.0
    if cur > base * (1 + slack):
        return ratio, "DRIFT^", True
    if cur < base * (1 - slack):
        return ratio, "shrink (run --apply)", False
    return ratio, "ok", False


def compare(baseline: dict[str, Any], snapshot: dict[str, Any], slack: float):
    """Compare snapshot vs baseline.

    Returns ``(rows, has_growth_drift)`` where rows is a list of
    ``(name, base, cur, ratio, status)``.
    """
    rows: list[tuple[str, Any, Any, float | None, str]] = []
    has_growth = False

    base_scen = baseline.get("baselines", {})
    cur_scen = snapshot["baselines"]
    for name in sorted(set(base_scen) | set(cur_scen)):
        base = base_scen.get(name, {}).get("current_total_tokens")
        cur = cur_scen.get(name, {}).get("current_total_tokens")
        ratio, status, growth = _classify(base, cur, slack)
        rows.append((name, base if base is not None else "-",
                     cur if cur is not None else "-", ratio, status))
        has_growth = has_growth or growth

    base_agg = baseline.get("aggregate", {})
    cur_agg = snapshot["aggregate"]
    for key in sorted(set(base_agg) | set(cur_agg)):
        base = base_agg.get(key)
        cur = cur_agg.get(key)
        ratio, status, growth = _classify(base, cur, slack)
        rows.append((f"aggregate.{key}", base if base is not None else "-",
                     cur if cur is not None else "-", ratio, status))
        has_growth = has_growth or growth

    return rows, has_growth


def print_table(rows, slack: float) -> None:
    print(f"Token lifecycle drift (slack +/-{slack * 100:.0f}%)")
    print(f"  {'scenario':<34} {'baseline':>10} {'current':>10} {'delta':>9}  status")
    for name, base, cur, ratio, status in rows:
        print(f"  {name:<34} {str(base):>10} {str(cur):>10} "
              f"{_fmt_pct(ratio):>9}  {status}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Token lifecycle baseline + drift detector"
    )
    ap.add_argument("--root", default=".", help="Repository root")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--init", action="store_true",
                      help="seed baseline (refuses if one already exists)")
    mode.add_argument("--apply", action="store_true",
                      help="(re)write baseline from the current analysis")
    mode.add_argument("--dry-run", action="store_true",
                      help="compare current vs baseline (default)")
    ap.add_argument("--slack", type=float, default=None,
                    help="override slack fraction (default: baseline value or 0.10)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    path = root / BASELINE_REL

    if args.init or args.apply:
        if args.init and path.is_file():
            print(f"baseline already exists at {path}; use --apply to overwrite",
                  file=sys.stderr)
            return 2
        slack = args.slack if args.slack is not None else DEFAULT_SLACK
        snapshot = current_snapshot(root)
        write_baseline(path, snapshot, slack)
        action = "seeded" if args.init else "applied"
        print(f"baseline {action}: {path} "
              f"({len(snapshot['baselines'])} scenarios, slack +/-{slack * 100:.0f}%)")
        return 0

    # Default: dry-run compare.
    if not path.is_file():
        print(f"baseline absent at {path}; run: "
              "update_lifecycle_baseline.py --init", file=sys.stderr)
        return 2
    baseline = load_baseline(path)
    slack = (args.slack if args.slack is not None
             else float(baseline.get("slack_default", DEFAULT_SLACK)))
    snapshot = current_snapshot(root)
    rows, has_growth = compare(baseline, snapshot, slack)
    print_table(rows, slack)
    if has_growth:
        print("\nDRIFT: token cost grew beyond slack (or a scenario is missing "
              "from the baseline).")
        print("If intended, re-baseline: update_lifecycle_baseline.py --apply")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
