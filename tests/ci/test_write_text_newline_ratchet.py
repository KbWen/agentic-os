"""Cap-at-zero AST ratchet: no `Path.write_text(..., newline=...)` anywhere (backlog #164).

`pathlib.Path.write_text` gained the `newline=` parameter in Python **3.10**;
this repo's CI floor is **3.9** (`validate.yml` Framework Validation job), where
the call raises `TypeError`. The failure is CI-invisible by construction —
pytest jobs run 3.12 and the 3.9 job exercises only `validate.sh --dry-run`
paths — so the crash sits latent until a 3.9 host runs the affected code path
(`update_lifecycle_baseline.py --init/--apply` was the shipped instance, found
by the 2026-08-08 #160 sweep; six more sites had accumulated in test files, and
the primary session itself almost shipped a seventh in a fixture the same day).

Grep is the wrong tool here — a call whose arguments contain parentheses
(`write_text(json.dumps(doc, indent=2) + "\\n", ..., newline="\\n")`) escapes
naive patterns, which is exactly how the shipped instance was missed. AST is
authoritative. LF-exact writes stay easy without the 3.10 API:
`path.write_bytes(s.encode("utf-8"))` or
`with path.open("w", encoding="utf-8", newline="\\n") as fh: fh.write(s)`
(the #160 fix pattern).

Cap is ZERO: fix the site, never add an exception list.
Modeled on `tests/ci/test_subprocess_encoding.py` (the #146 cap-at-zero AST
ratchet), including its anti-vacuity scan-reach guard.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_PARTS = {".git", ".claude", "node_modules", "__pycache__", ".pytest_cache"}


def _repo_python_files() -> list[Path]:
    files = []
    for p in ROOT.rglob("*.py"):
        if any(part in EXCLUDED_PARTS for part in p.parts):
            continue
        files.append(p)
    return files


def _violations_in(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:  # a broken file is its own problem; surface it
        return [f"{path}: SyntaxError during ratchet scan: {exc}"]
    hits = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_text"
            and any(kw.arg == "newline" for kw in node.keywords)
        ):
            rel = path.relative_to(ROOT)
            hits.append(f"{rel}:{node.lineno}")
    return hits


def test_scan_reaches_the_codebase() -> None:
    """Anti-vacuity: an empty scan set would make the zero-cap pass trivially."""
    files = _repo_python_files()
    assert len(files) > 50, (
        f"write_text-newline ratchet scanned only {len(files)} Python files — "
        f"the discovery walk broke; fix the walker before trusting the cap."
    )


def test_no_write_text_newline_calls() -> None:
    violations = []
    for path in _repo_python_files():
        violations.extend(_violations_in(path))
    assert not violations, (
        "Path.write_text(newline=...) is Python >=3.10 and TypeErrors on this "
        "repo's 3.9 CI floor (backlog #164). Replace with write_bytes() or "
        "open('w', encoding='utf-8', newline=...) [the #160 pattern]. "
        "Cap is zero — fix the sites, do not add exceptions:\n  "
        + "\n  ".join(violations)
    )
