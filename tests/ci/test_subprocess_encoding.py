"""Subprocess decoding must never depend on the machine's locale (backlog #146).

`subprocess.run(..., text=True)` without an explicit `encoding=` decodes the child's output
with `locale.getpreferredencoding()`. On a Windows box whose ANSI code page is not UTF-8
(e.g. `cp950`, Traditional Chinese), a single UTF-8 character in tool output — an em-dash is
enough, byte `0xe2` — raises `UnicodeDecodeError` inside subprocess. The exception surfaces
in a maximally confusing way: `stdout`/`stderr` come back as `None`, and the assertion that
reads them dies with `TypeError: argument of type 'NoneType' is not a container` instead of
anything naming encoding.

That cost a real session on 2026-07-25: six tests were red on a `cp950` box and green in CI
on the identical commit, which reads exactly like "you broke something".

This is a cap-at-zero ratchet, not a style rule. It fails only when a NEW locale-dependent
call site appears. The fix is always the same two keywords:

    subprocess.run(..., text=True, encoding="utf-8", errors="replace")

`errors="replace"` is deliberate: a test asserting on tool output should fail on the
assertion with readable text, never crash on the decode. Precedent predates this test —
`.agentcortex/tests/test_ssot_completeness.py` already used exactly this pair.

Documented for humans as repo-gotchas #13.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Callables whose str-mode output goes through the locale codec.
_SUBPROCESS_FUNCS = {"run", "check_output", "Popen"}
# Either keyword asks subprocess for str instead of bytes.
_TEXT_KWARGS = ("text", "universal_newlines")


def _python_files() -> list[Path]:
    """Tracked-ish source files: every .py outside dot-directories except .agentcortex.

    Skipping dot-directories keeps `.git`, `.venv`, `__pycache__` and — importantly —
    `.claude/worktrees/*` out of scope. A stale agent worktree holds a full copy of the repo,
    and scanning it would fail this test on code that is not on this branch at all.
    """
    out = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if any(p.startswith(".") and p != ".agentcortex" for p in rel.parts[:-1]):
            continue
        if "__pycache__" in rel.parts or "node_modules" in rel.parts:
            continue
        out.append(path)
    return out


def _asks_for_str(call: ast.Call) -> bool:
    return any(
        kw.arg in _TEXT_KWARGS and isinstance(kw.value, ast.Constant) and kw.value.value is True
        for kw in call.keywords
    )


def _locale_dependent_calls(tree: ast.AST) -> list[int]:
    """Line numbers of subprocess calls that decode with the system locale."""
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
            and func.attr in _SUBPROCESS_FUNCS
        ):
            continue
        if not _asks_for_str(node):
            continue  # bytes mode: nothing is decoded
        if any(kw.arg == "encoding" for kw in node.keywords):
            continue  # explicit codec: safe
        hits.append(node.lineno)
    return hits


def test_no_locale_dependent_subprocess_decoding() -> None:
    offenders: list[str] = []
    for path in _python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for line in _locale_dependent_calls(tree):
            offenders.append(f"{path.relative_to(ROOT).as_posix()}:{line}")

    assert not offenders, (
        "subprocess call(s) decode child output with the system locale, which breaks on any "
        "non-UTF-8 console (cp950 etc.) and reports as a confusing TypeError about None:\n  "
        + "\n  ".join(offenders)
        + '\n\nAdd encoding="utf-8", errors="replace" to each call.'
    )


def test_detector_recognizes_the_unsafe_shape() -> None:
    """Guard the guard: a permanently-passing detector would be worthless."""
    unsafe = ast.parse("import subprocess\nsubprocess.run(['x'], text=True)\n")
    safe = ast.parse("import subprocess\nsubprocess.run(['x'], text=True, encoding='utf-8')\n")
    bytes_mode = ast.parse("import subprocess\nsubprocess.run(['x'])\n")

    assert _locale_dependent_calls(unsafe) == [2]
    assert _locale_dependent_calls(safe) == []
    assert _locale_dependent_calls(bytes_mode) == []


@pytest.mark.parametrize("keyword", _TEXT_KWARGS)
def test_detector_covers_both_str_mode_keywords(keyword: str) -> None:
    tree = ast.parse(f"import subprocess\nsubprocess.run(['x'], {keyword}=True)\n")
    assert _locale_dependent_calls(tree) == [2]


def test_scan_actually_reaches_the_repo() -> None:
    """A silently-empty file list would make the ratchet vacuous."""
    files = _python_files()
    assert len(files) > 50, f"expected to scan the whole repo, found only {len(files)} files"
    names = {p.name for p in files}
    assert "test_subprocess_encoding.py" in names
    assert not any(".claude" in p.relative_to(ROOT).parts for p in files), (
        "stale agent worktrees under .claude/ must stay out of scope"
    )
