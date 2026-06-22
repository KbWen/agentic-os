#!/usr/bin/env python3
"""Governance Behavioral Eval Runner.

Scores agent transcripts (or runs a live agent) against the seed cases in
governance.yaml to measure whether the agent actually obeys governance rules
under adversarial pressure.

CLI examples:
    # Score a directory of <case-id>.txt transcript files:
    python run_governance_eval.py --transcripts /tmp/transcripts/

    # Score a single transcript:
    python run_governance_eval.py --case gate-bypass-pressure --transcript /tmp/gate.txt

    # Run a live agent per case (prompts are NOT shell-interpolated — safe):
    python run_governance_eval.py --agent-cmd "claude -p {prompt}" --timeout 60

    # Coverage report (exit 0 always):
    python run_governance_eval.py --coverage

Security note: --agent-cmd template is split with shlex.split ONCE before
substitution. The {prompt} placeholder is replaced inside the already-split
argv element so no shell interprets the case content. shell=False is used in
subprocess.run. Never pass case content through f-strings or shell=True.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Loader import (reuse project-standard YAML loader)
# ---------------------------------------------------------------------------
_TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS_DIR))
from _yaml_loader import load_data  # noqa: E402

# ---------------------------------------------------------------------------
# Governance source files for coverage inventory
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_GOVERNANCE_FILES = [
    _REPO_ROOT / "AGENTS.md",
    _REPO_ROOT / ".agent" / "rules" / "engineering_guardrails.md",
    _REPO_ROOT / ".agent" / "rules" / "security_guardrails.md",
]

_DEFAULT_EVAL_PATH = _REPO_ROOT / ".agentcortex" / "eval" / "governance.yaml"

# ---------------------------------------------------------------------------
# Rule inventory extraction
# ---------------------------------------------------------------------------

def _extract_rule_inventory(gov_files: list[Path]) -> list[str]:
    """Extract MUST-bearing ## / ### section anchors from governance files.

    Returns a list of normalized "<file> §<section>" strings, one per
    ## / ### heading whose OWN text (heading line + lines up to the next
    heading of ANY level) contains the word MUST. Counting to the next
    same-or-higher heading double-counted parents whose MUSTs all live in
    already-inventoried children (~9 phantom anchors inflating the
    zero-coverage WARN).
    """
    inventory: list[str] = []
    must_re = re.compile(r"\bMUST\b")
    heading_re = re.compile(r"^(#{2,3})\s+(.+)")

    for path in gov_files:
        if not path.exists():
            continue
        rel = path.name
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        # Collect (level, heading, start_line_idx) tuples
        headings: list[tuple[int, str, int]] = []
        for i, line in enumerate(lines):
            m = heading_re.match(line)
            if m:
                level = len(m.group(1))
                headings.append((level, m.group(2).strip(), i))

        for idx, (level, name, start) in enumerate(headings):
            # Own text only: heading line up to the next heading of ANY level.
            # A child's MUST belongs to the child anchor, not the parent.
            end = headings[idx + 1][2] if idx + 1 < len(headings) else len(lines)
            body = "\n".join(lines[start:end])
            if must_re.search(body):
                anchor = f"{rel} §{name}"
                inventory.append(anchor)

    return inventory


def _normalize_anchor(anchor: str) -> str:
    """Normalize an anchor for case-insensitive, whitespace-insensitive matching."""
    return re.sub(r"\s+", " ", anchor.strip().lower())


# ---------------------------------------------------------------------------
# Case scoring
# ---------------------------------------------------------------------------

def _score_case(case: dict[str, Any], transcript: str) -> tuple[str, list[str]]:
    """Score one case against a transcript.

    Returns (status, failed_expectations) where status is
    pass | fail | skipped | error.
    """
    failed: list[str] = []

    # max_lines check
    max_lines = case.get("max_lines")
    if max_lines is not None:
        actual_lines = len(transcript.splitlines())
        if actual_lines > max_lines:
            failed.append(f"max_lines: {actual_lines} > {max_lines}")

    # expect_substrings
    for sub in case.get("expect_substrings", []):
        if sub not in transcript:
            failed.append(f"expect_substring missing: {sub!r}")

    # forbid_substrings
    for sub in case.get("forbid_substrings", []):
        if sub in transcript:
            failed.append(f"forbid_substring present: {sub!r}")

    # assertions
    for assertion in case.get("assertions", []):
        atype = assertion.get("type", "")
        pattern = assertion.get("pattern", "")
        if atype == "regex_present":
            if not re.search(pattern, transcript):
                failed.append(f"regex_present not matched: {pattern!r}")
        elif atype == "regex_absent":
            if re.search(pattern, transcript):
                failed.append(f"regex_absent matched: {pattern!r}")
        else:
            failed.append(f"unknown assertion type: {atype!r}")

    status = "fail" if failed else "pass"
    return status, failed


# ---------------------------------------------------------------------------
# Agent runner
# ---------------------------------------------------------------------------

def _sanitize_diagnostic(value: str | bytes | None) -> str:
    """Return a bounded, single-line diagnostic with common secrets redacted."""
    if value is None:
        return ""
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    text = re.sub(r"(?i)\b(token|password|secret|api[_-]?key|authorization)\b(\s*[:=]\s*|\s+)\S+",
                  r"\1\2[REDACTED]", text)
    text = re.sub(r"(?i)\bbearer\s+\S+", "Bearer [REDACTED]", text)
    # Redact inline URL credentials (scheme://user:pass@host) — keep scheme/host for diagnosis.
    text = re.sub(r"(?i)\b([a-z][a-z0-9+.\-]*://)[^\s:/@]+:[^\s/@]+@",
                  r"\1[REDACTED]@", text)
    text = " | ".join(line.strip() for line in text.splitlines() if line.strip())
    return text[:500]


def _run_agent(cmd_template: str, prompt: str, timeout: int) -> tuple[str, int, str]:
    """Run a live agent for a single case prompt.

    cmd_template: a string like "claude -p {prompt}" or "myagent".
    The template is split with shlex once; then {prompt} is substituted
    into the specific argv element — never via shell interpolation.
    prompt: raw case prompt text.
    Returns (stdout, returncode, sanitized_stderr).

    Shell injection note: shlex.split runs on the TEMPLATE string only (which
    is operator-controlled). The prompt is then substituted as a literal string
    into the already-split argv list. No f-string or format-string expansion
    combines case content into a shell argument. shell=False in subprocess.run.
    """
    argv = shlex.split(cmd_template)
    # Substitute {prompt} placeholder into whichever argv element contains it
    substituted = False
    for i, arg in enumerate(argv):
        if "{prompt}" in arg:
            argv[i] = arg.replace("{prompt}", prompt)
            substituted = True
    # If no placeholder, prompt is passed via stdin (not via command line)
    stdin_data = None if substituted else prompt
    try:
        result = subprocess.run(
            argv,
            input=stdin_data,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        return result.stdout, result.returncode, _sanitize_diagnostic(result.stderr)
    except subprocess.TimeoutExpired as exc:
        stderr = _sanitize_diagnostic(exc.stderr)
        diagnostic = f"agent timeout after {timeout}s" + (f": {stderr}" if stderr else "")
        return "", -1, diagnostic
    except OSError as exc:
        executable = _sanitize_diagnostic(re.split(r"[\\/]", argv[0])[-1]) if argv else "<unknown>"
        error_code = getattr(exc, "winerror", None) or exc.errno
        diagnostic = f"agent launch error (OSError): executable={executable}"
        diagnostic += f"; code={error_code}" if error_code is not None else ""
        return "", -2, diagnostic


# ---------------------------------------------------------------------------
# Coverage mode
# ---------------------------------------------------------------------------

def _run_coverage(cases: list[dict[str, Any]], gov_files: list[Path]) -> int:
    """Print rule inventory with guarding-case counts; list zero-coverage rules."""
    inventory = _extract_rule_inventory(gov_files)
    # Build guarding counts: for each rule, how many cases protect it?
    counts: dict[str, int] = {r: 0 for r in inventory}
    for case in cases:
        protects = case.get("protects", "")
        if not protects:
            continue
        norm_protects = _normalize_anchor(protects)
        for rule in inventory:
            if _normalize_anchor(rule) == norm_protects:
                counts[rule] += 1
                break
            # Partial match: the protects tag may embed a longer anchor
            if norm_protects in _normalize_anchor(rule) or _normalize_anchor(rule) in norm_protects:
                counts[rule] += 1
                break

    zero_rules = [r for r in inventory if counts[r] == 0]
    print(f"Rule inventory: {len(inventory)} MUST-bearing section(s) across governance files")
    print(f"Cases evaluated: {len(cases)}")
    print(f"Zero-coverage rules: {len(zero_rules)}")
    if zero_rules:
        print("\nRules with zero guarding cases:")
        for r in zero_rules:
            print(f"  - {r}")
    else:
        print("governance eval coverage: 0 MUST-rule section(s) with zero guarding cases")
    return 0  # always exit 0 (advisory)


# ---------------------------------------------------------------------------
# Text output formatting
# ---------------------------------------------------------------------------

def _print_text_results(results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    for r in results:
        status = r["status"].upper()
        print(f"[{status}] {r['id']}")
        if r.get("failed_expectations"):
            for fe in r["failed_expectations"]:
                print(f"       {fe}")
    print()
    print(f"Summary: pass={summary['pass']} fail={summary['fail']} "
          f"skipped={summary['skipped']} error={summary['error']} "
          f"total={summary['total']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {"pass": 0, "fail": 0, "skipped": 0, "error": 0, "total": len(results)}
    for r in results:
        s = r["status"]
        if s in counts:
            counts[s] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Governance Behavioral Eval Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(__doc__ or ""),
    )
    parser.add_argument(
        "--eval",
        default=str(_DEFAULT_EVAL_PATH),
        help="Path to eval YAML (default: .agentcortex/eval/governance.yaml)",
    )
    parser.add_argument("--transcripts", help="Directory of <case-id>.txt transcript files")
    parser.add_argument("--case", help="Single case id (use with --transcript or --agent-cmd)")
    parser.add_argument("--transcript", help="Single transcript file path (use with --case)")
    parser.add_argument(
        "--agent-cmd",
        help='Agent command template (e.g. "claude -p {prompt}"). '
             "{prompt} is substituted safely without shell interpretation.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Per-case agent timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run coverage report (exit 0 always)",
    )
    args = parser.parse_args()

    # Load eval YAML
    eval_path = Path(args.eval)
    if not eval_path.exists():
        print(f"error: eval file not found: {eval_path}", file=sys.stderr)
        return 1
    try:
        data = load_data(eval_path)
    except Exception as exc:
        print(f"error: failed to parse eval YAML: {exc}", file=sys.stderr)
        return 1

    # Structural validation — guarantees a clear error on malformed input even
    # when the lenient subset parser (no-PyYAML path) "successfully" parses
    # garbage into strings instead of raising.
    if not isinstance(data, dict):
        print("error: malformed eval spec: top level must be a mapping with a 'cases' list", file=sys.stderr)
        return 1
    cases: list[dict[str, Any]] = data.get("cases", [])
    if not isinstance(cases, list) or not all(isinstance(c, dict) for c in cases):
        print("error: malformed eval spec: 'cases' must be a list of mappings", file=sys.stderr)
        return 1
    _bad = [
        c for c in cases
        if not (isinstance(c.get("id"), str) and c.get("id")
                and isinstance(c.get("prompt"), str)
                and isinstance(c.get("protects"), str))
    ]
    if _bad:
        print(
            f"error: malformed eval spec: {len(_bad)} case(s) missing required string fields id/prompt/protects",
            file=sys.stderr,
        )
        return 1
    for c in cases:
        for fld in ("expect_substrings", "forbid_substrings"):
            v = c.get(fld)
            if v is not None and not (isinstance(v, list) and all(isinstance(s, str) for s in v)):
                print(f"error: malformed eval spec: case {c['id']!r} field {fld!r} must be a list of strings", file=sys.stderr)
                return 1
        a = c.get("assertions")
        if a is not None and not (
            isinstance(a, list)
            and all(isinstance(e, dict) and isinstance(e.get("type"), str) and isinstance(e.get("pattern"), str) for e in a)
        ):
            print(f"error: malformed eval spec: case {c['id']!r} field 'assertions' must be a list of {{type, pattern}} mappings", file=sys.stderr)
            return 1
        ml = c.get("max_lines")
        if ml is not None and not isinstance(ml, int):
            print(f"error: malformed eval spec: case {c['id']!r} field 'max_lines' must be an integer", file=sys.stderr)
            return 1

    # Coverage mode
    if args.coverage:
        return _run_coverage(cases, _GOVERNANCE_FILES)

    # Sort cases by id for deterministic output
    cases_by_id: dict[str, dict[str, Any]] = {c["id"]: c for c in cases if "id" in c}
    sorted_ids = sorted(cases_by_id.keys())

    results: list[dict[str, Any]] = []

    # Single-case mode
    if args.case and args.transcript:
        case_id = args.case
        if case_id not in cases_by_id:
            print(f"error: case id not found in eval: {case_id!r}", file=sys.stderr)
            return 1
        case = cases_by_id[case_id]
        transcript_path = Path(args.transcript)
        if not transcript_path.exists():
            results.append({"id": case_id, "status": "skipped", "failed_expectations": []})
        else:
            transcript = transcript_path.read_text(encoding="utf-8", errors="replace")
            status, failed = _score_case(case, transcript)
            results.append({"id": case_id, "status": status, "failed_expectations": failed})

    # Transcript directory mode
    elif args.transcripts:
        tdir = Path(args.transcripts)
        for cid in sorted_ids:
            case = cases_by_id[cid]
            tf = tdir / f"{cid}.txt"
            if not tf.exists():
                results.append({"id": cid, "status": "skipped", "failed_expectations": []})
            else:
                transcript = tf.read_text(encoding="utf-8", errors="replace")
                status, failed = _score_case(case, transcript)
                results.append({"id": cid, "status": status, "failed_expectations": failed})

    # Live agent mode
    elif args.agent_cmd:
        live_ids = sorted_ids
        if args.case:
            if args.case not in cases_by_id:
                print(f"error: case id not found in eval: {args.case!r}", file=sys.stderr)
                return 1
            live_ids = [args.case]
        for cid in live_ids:
            case = cases_by_id[cid]
            prompt = case.get("prompt", "")
            stdout, rc, diagnostic = _run_agent(args.agent_cmd, prompt, args.timeout)
            if rc != 0:
                failed = [f"agent exit {rc}"] + ([f"agent diagnostic: {diagnostic}"] if diagnostic else [])
                results.append({"id": cid, "status": "error", "failed_expectations": failed})
            else:
                status, failed = _score_case(case, stdout)
                results.append({"id": cid, "status": status, "failed_expectations": failed})

    else:
        parser.print_help()
        return 0

    # Build summary
    summary = _build_summary(results)

    # Output
    if args.format == "json":
        out = {
            "cases": sorted(results, key=lambda r: r["id"]),
            "summary": {k: summary[k] for k in sorted(summary.keys())},
        }
        print(json.dumps(out, sort_keys=True, indent=2))
    else:
        _print_text_results(results, summary)

    # Exit code: 0 iff no fail/error
    has_failure = any(r["status"] in ("fail", "error") for r in results)
    return 1 if has_failure else 0


if __name__ == "__main__":
    sys.exit(main())
