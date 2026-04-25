#!/usr/bin/env python3
"""ADR-002 D2.2 — CI lint for direct file writes against governed paths.

Spec: docs/specs/lock-unification.md AC-9..AC-14
ADR:  docs/adr/ADR-002-guarded-governance-writes.md §D2

Scans tracked source files for direct write patterns (open(..., 'w'), shell
redirect, PowerShell Set-Content, JS fs.writeFile, etc.) targeting paths
matching .agent/config.yaml §guard_policy.protected_paths globs. Such writes
MUST go through guard_context_write.py instead.

Exit codes:
  0  no FAIL findings (PASS or WARN only)
  1  one or more FAIL findings
  2  configuration / environment error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, NamedTuple

# Reuse policy loader from the guard tool
sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard_context_write import load_guard_policy, match_protected_path  # noqa: E402


SCANNED_EXTENSIONS = {".py", ".sh", ".bash", ".ps1", ".js", ".ts", ".mjs", ".cjs"}
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build"}

# Path patterns where dynamic-path WARNs are nearly always false positives
# (test fixtures using tmp_path / Path concatenation). FAIL findings in these
# paths are STILL reported — only the noisy `dynamic path — manual review` WARNs
# get suppressed. This preserves accuracy: real production-code dynamic paths
# stay visible; test-fixture noise stops drowning the signal. (Cleanup PR #81.)
TEST_PATH_RE = re.compile(
    r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]+\.(py|js|ts|sh|ps1)$|(^|/)[^/]+_test\.(py|js|ts|sh|ps1)$"
)

# AC-12: comment markers that suppress findings on the matching or preceding line
EXEMPTION_RE = re.compile(r"guard-exempt\s*:\s*(?P<reason>.+?)(?:\*/|-->|$)")

# Tools that legitimately implement the guard layer itself — exempt from lint.
SELF_EXEMPT_FILES = {
    ".agentcortex/tools/guard_context_write.py",  # the guard itself
    ".agentcortex/tools/lint_governed_writes.py",  # this lint file (regex literals look like writes)
}


# --------------------------------------------------------------------------- #
# Pattern catalog
# --------------------------------------------------------------------------- #


class WritePattern(NamedTuple):
    name: str
    regex: re.Pattern[str]
    path_group: int  # 0 = no static path; otherwise the regex group containing the path
    path_kind: str = "py_literal"  # py_literal | shell_token | ps_token | js_literal

PYTHON_PATTERNS: tuple[WritePattern, ...] = (
    # open(<expr>, '<mode-with-w-a-x>')
    WritePattern(
        "python_open_write",
        re.compile(
            r"""
            \bopen\s*\(           # open(
            \s*(?P<path>[^,)]+?)  # first arg (path)
            \s*,\s*               # ,
            ['"]                  # opening mode quote
            (?P<mode>[^'"]*[wax+][^'"]*)
            ['"]                  # closing mode quote
            """,
            re.VERBOSE,
        ),
        path_group=1,
    ),
    # Path(...).write_text / write_bytes — restrict lhs to single line
    WritePattern(
        "python_pathlib_write",
        re.compile(r"""(?P<lhs>[\w\.\(\)\[\]"'/\t ]+?)\.write_(?:text|bytes)\s*\("""),
        path_group=1,
    ),
    # shutil.copyfile / move / copy / copy2 (second arg is destination)
    WritePattern(
        "python_shutil_dest",
        re.compile(r"""\bshutil\.(?:copyfile|move|copy|copy2)\s*\(\s*[^,]+,\s*(?P<path>[^,)]+)"""),
        path_group=1,
    ),
)

SHELL_PATTERNS: tuple[WritePattern, ...] = (
    # > path or >> path (redirection); avoid 2>&1 and similar
    WritePattern(
        "shell_redirect",
        re.compile(r"""(?<![0-9])>>?\s*(?!&)(?P<path>[^\s|;&<>(){}]+)"""),
        path_group=1,
        path_kind="shell_token",
    ),
    # tee path or tee -a path
    WritePattern(
        "shell_tee",
        re.compile(r"""\btee\s+(?:-a\s+)?(?P<path>[^\s|;&<>]+)"""),
        path_group=1,
        path_kind="shell_token",
    ),
)

POWERSHELL_PATTERNS: tuple[WritePattern, ...] = (
    WritePattern(
        "ps_set_content",
        re.compile(
            r"""(?:Set-Content|Add-Content|Out-File)\s+(?:-Path\s+|-FilePath\s+)?["']?(?P<path>[^\s"'|;]+)["']?""",
            re.IGNORECASE,
        ),
        path_group=1,
        path_kind="ps_token",
    ),
)

JS_PATTERNS: tuple[WritePattern, ...] = (
    WritePattern(
        "js_fs_write",
        re.compile(r"""\bfs\.(?:writeFile|appendFile|createWriteStream)(?:Sync)?\s*\(\s*['"`](?P<path>[^'"`]+)['"`]"""),
        path_group=1,
        path_kind="js_literal",
    ),
)


def patterns_for(extension: str) -> tuple[WritePattern, ...]:
    if extension == ".py":
        return PYTHON_PATTERNS
    if extension in {".sh", ".bash"}:
        return SHELL_PATTERNS
    if extension == ".ps1":
        return POWERSHELL_PATTERNS
    if extension in {".js", ".ts", ".mjs", ".cjs"}:
        return JS_PATTERNS
    return ()


# --------------------------------------------------------------------------- #
# File enumeration
# --------------------------------------------------------------------------- #


def list_tracked_files(root: Path) -> Iterable[Path]:
    """Prefer git ls-files for accuracy; fall back to os.walk if git unavailable."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            yield root / line
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback walk
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in files:
            yield Path(current_root) / name


# --------------------------------------------------------------------------- #
# Path-literal extraction
# --------------------------------------------------------------------------- #

_STRING_LITERAL_RE = re.compile(r"""^['"]([^'"]+)['"]$""")
_SHELL_VAR_RE = re.compile(r"""\$|\`""")  # variable expansion or command sub
_PATH_TOKEN_RE = re.compile(r"^[\w./\-]+$")


def extract_path_literal(expr: str, kind: str = "py_literal") -> str | None:
    """Return the bare path string if `expr` resolves statically; else None.

    py_literal: requires single/double-quoted string ('foo.md' or "foo.md")
    js_literal: same as py_literal (JS uses ', ", or `)
    shell_token / ps_token: bare token without $variable interpolation; quotes stripped
    """
    expr = expr.strip().rstrip(",)")
    if kind in {"py_literal", "js_literal"}:
        m = _STRING_LITERAL_RE.match(expr)
        return m.group(1) if m else None
    if kind in {"shell_token", "ps_token"}:
        # Strip optional surrounding quotes
        if len(expr) >= 2 and expr[0] in "'\"" and expr[-1] == expr[0]:
            expr = expr[1:-1]
        # Reject if it looks like variable expansion or command sub
        if _SHELL_VAR_RE.search(expr):
            return None
        # Reject if not a path-like token (avoid catching flags, options, etc.)
        if not _PATH_TOKEN_RE.match(expr):
            return None
        return expr
    return None


# --------------------------------------------------------------------------- #
# Scanner
# --------------------------------------------------------------------------- #


class Finding(NamedTuple):
    severity: str  # FAIL | WARN
    file: str
    line_no: int
    pattern: str
    matched: str
    detail: str


def line_or_prev_has_exemption(lines: list[str], idx: int) -> str | None:
    """AC-12: same-line or immediately-preceding-line exemption marker."""
    for probe in (idx, idx - 1):
        if 0 <= probe < len(lines):
            m = EXEMPTION_RE.search(lines[probe])
            if m:
                return m.group("reason").strip()
    return None


def scan_file(path: Path, rel_posix: str, protected_globs: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    if rel_posix in SELF_EXEMPT_FILES:
        return findings

    ext = path.suffix.lower()
    patterns = patterns_for(ext)
    if not patterns:
        return findings

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return findings

    lines = text.splitlines()
    for pattern in patterns:
        for m in pattern.regex.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            line_idx = line_no - 1
            exemption = line_or_prev_has_exemption(lines, line_idx)
            raw_path_expr = m.group(pattern.path_group) if pattern.path_group else None

            literal = extract_path_literal(raw_path_expr, kind=pattern.path_kind) if raw_path_expr else None

            if literal is None:
                # Variable / dynamic path — WARN unless exempt
                if exemption is not None:
                    continue
                # Cleanup PR #81: suppress dynamic-path WARNs in test fixtures
                # (tests/, __tests__/, test_*.py, *_test.py). FAIL findings
                # against governed paths are still reported below — only the
                # noisy "dynamic path" WARN class is suppressed for test files.
                if TEST_PATH_RE.search(rel_posix):
                    continue
                findings.append(Finding(
                    severity="WARN",
                    file=rel_posix,
                    line_no=line_no,
                    pattern=pattern.name,
                    matched=lines[line_idx].strip()[:160] if line_idx < len(lines) else "",
                    detail="dynamic path — manual review needed",
                ))
                continue

            # Static path — match against policy
            if not match_protected_path(literal, protected_globs):
                continue  # not a governed path; ignore

            if exemption is not None:
                # Counted but not failing
                findings.append(Finding(
                    severity="WARN",
                    file=rel_posix,
                    line_no=line_no,
                    pattern=pattern.name,
                    matched=lines[line_idx].strip()[:160] if line_idx < len(lines) else "",
                    detail=f"exempt: {exemption}",
                ))
                continue

            findings.append(Finding(
                severity="FAIL",
                file=rel_posix,
                line_no=line_no,
                pattern=pattern.name,
                matched=lines[line_idx].strip()[:160] if line_idx < len(lines) else "",
                detail=f"writes to governed path '{literal}' without guard",
            ))
    return findings


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Lint tracked source files for direct writes against guard_policy.protected_paths. "
            "Use guard_context_write.py for any write to a governed path, or annotate the line "
            "with `guard-exempt: <reason>` (`#`, `//`, or `<!-- -->` comment style)."
        )
    )
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON")
    ap.add_argument("--verbose", action="store_true", help="Print per-file scan info")
    ap.add_argument(
        "--show-warn",
        action="store_true",
        help="Print every WARN line (default: print only FAILs and the summary). WARNs were drowning real signal — see R-5 in 3-expert post-merge audit.",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    policy = load_guard_policy(root)
    protected_globs = list(policy.get("protected_paths", []))
    if not protected_globs:
        print("no guard_policy.protected_paths configured — nothing to enforce", file=sys.stderr)
        return 0

    findings: list[Finding] = []
    files_scanned = 0
    for path in list_tracked_files(root):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCANNED_EXTENSIONS:
            continue
        try:
            rel_posix = str(path.resolve().relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        files_scanned += 1
        if args.verbose:
            print(f"  scan: {rel_posix}", file=sys.stderr)
        findings.extend(scan_file(path, rel_posix, protected_globs))

    fail_count = sum(1 for f in findings if f.severity == "FAIL")
    warn_count = sum(1 for f in findings if f.severity == "WARN")

    if args.json:
        payload = {
            "files_scanned": files_scanned,
            "fail_count": fail_count,
            "warn_count": warn_count,
            "findings": [f._asdict() for f in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        # R-5 fix: print summary FIRST so it's not buried under 70 WARN lines.
        # FAILs are always shown (action required). WARNs are silent unless
        # --show-warn is passed (most are dynamic-path false-positives in tests/).
        print(
            f"governed-write lint: {files_scanned} file(s) scanned; "
            f"{fail_count} FAIL, {warn_count} WARN"
            + (" (use --show-warn to see WARN lines)" if warn_count and not args.show_warn else "")
        )
        for f in findings:
            if f.severity == "WARN" and not args.show_warn:
                continue
            print(f"  [{f.severity}] {f.file}:{f.line_no}  {f.pattern} — {f.detail}", file=sys.stderr)
            print(f"           {f.matched}", file=sys.stderr)

    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
