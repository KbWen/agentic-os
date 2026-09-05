#!/usr/bin/env python3
"""Credential pattern scanner — high-confidence pre-commit catch for the AGENTS.md
Secrets Prohibition invariant (backlog #71 / issue #225).

Developer-convenience pre-commit screen that flags DISTINCTIVE, high-confidence
credential shapes BEFORE they enter object history (once committed, rotation — not
deletion — is the remedy). Reports ``path:line: pattern-name`` only, never the value.

Enforcement model (stated honestly — NOT a machine-enforced gate by itself): this
hook is OPT-IN (a ``.sample`` you install) and bypassable with ``git commit
--no-verify``. The regex CORRECTNESS is CI-tested (tests/ci/test_scan_credentials.py),
but the ENFORCED control is CI TruffleHog (verified-secret detection). This screen
only adds a fast local catch for the unambiguous shapes.

Does NOT catch (by design — left to TruffleHog, or omitted to avoid false positives
that would get a commit-blocking hook disabled):
  * AWS *secret* access keys (40-char, no distinctive prefix).
  * Secrets split across lines, base64-wrapped, or referenced via env vars.
  * Binary files (the diff carries no text hunk).
  * Ambiguous shapes — connection strings and JWTs — where a benign value and a
    real secret share the exact shape (a doc ``proto://user:pass@host``, an env
    placeholder ``${VAR}``, or a non-secret JWT would all false-positive).

Modes:
  --staged              scan newly-ADDED lines of the git staged diff.
  <file> [<file> ...]   scan the given files.
  (stdin)               scan stdin when no files and not --staged.

Exit: 0 clean · 1 credential pattern found · 2 usage error · 3 scan could not run
(git/tooling error — the caller should WARN, not silently pass).

Self-exclusion: this scanner's own source and the test fixture file are skipped.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# (name, compiled regex). DISTINCTIVE-PREFIX, high-confidence shapes only — a match
# is almost certainly a real secret. Ambiguous shapes (connection strings, JWTs) are
# deliberately omitted (see module docstring) so a commit-BLOCKING hook stays free of
# false positives. The no-false-positive fixtures guard this.
_PATTERNS: list[tuple[str, "re.Pattern[str]"]] = [
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("pem-private-key",
     re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP |ENCRYPTED )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b")),
    ("github-pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    # Real OpenAI keys: legacy sk-+48, or the sk-proj-/sk-svcacct-/sk-admin- families
    # (which carry _ and -). >=40 on the bare form avoids matching short kebab ids.
    ("openai-key",
     re.compile(r"\bsk-(?:proj|svcacct|admin)-[A-Za-z0-9_\-]{20,}|\bsk-[A-Za-z0-9]{40,}\b")),
    # Slack tokens carry a long contiguous hash tail; require >=24 to skip word-salad.
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]*[A-Za-z0-9]{24,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
]

_SELF_SKIP = ("scan_credentials.py", "test_scan_credentials.py")


class ScanError(Exception):
    """The scan could not run (git/tooling failure) — caller should WARN, not pass."""


def _is_self(path: str) -> bool:
    base = path.replace("\\", "/").rsplit("/", 1)[-1]
    return base in _SELF_SKIP


def scan_text(text: str, label: str) -> list[tuple[str, int, str]]:
    """Return ``(label, lineno, pattern_name)`` per match. NEVER returns the value.

    A line containing ``pragma: allowlist secret`` (the detect-secrets convention) is
    skipped — an escape hatch for documented EXAMPLE tokens that share a real
    credential's shape (e.g. AWS's own ``AKIA...EXAMPLE`` in setup docs), so a
    blocking PR gate does not reject legitimate documentation / fixture changes.
    """
    findings: list[tuple[str, int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "pragma: allowlist secret" in line.lower():
            continue
        for name, rx in _PATTERNS:
            if rx.search(line):
                findings.append((label, lineno, name))
    return findings


def parse_staged_diff(diff_text: str) -> list[tuple[str, str]]:
    """Parse ``git diff --cached -U0`` text → ``(path, added-content)`` per file.

    Only ``+`` ADDED content lines are kept. Header detection is gated on diff-section
    CONTEXT: ``+++ ``/``--- `` count as file headers ONLY outside a hunk — a ``+`` line
    *inside* a hunk is always added content, even when its body reconstructs a
    ``+++ `` header (e.g. a changelog/test line that is itself a raw diff fragment:
    a body ``++ /dev/null`` reaches the diff as ``+++ /dev/null``). A trailing TAB
    (git's quoting for space-containing paths) is stripped from the path.
    """
    files: dict[str, list[str]] = {}
    cur: str | None = None
    in_hunk = False
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            cur, in_hunk = None, False
        elif line.startswith("@@"):
            in_hunk = True
        elif not in_hunk and line.startswith("+++ b/"):
            cur = line[6:].rstrip("\t")
            files.setdefault(cur, [])
        elif not in_hunk and line.startswith("+++ "):  # +++ /dev/null (deletion side)
            cur = None
        elif in_hunk and cur is not None and line.startswith("+"):
            files[cur].append(line[1:])
    return [(p, "\n".join(v)) for p, v in files.items() if v]


def _diff_added_lines(diff_args: list[str]) -> list[tuple[str, str]]:
    """Run ``git diff <diff_args> -U0`` and parse it. Raise ScanError if git fails.

    ``diff_args`` is e.g. ``["--cached"]`` (the pre-commit staged diff) or
    ``["<base>..<head>"]`` (a PR range, for CI). Only ADDED lines are returned.
    """
    try:
        proc = subprocess.run(
            ["git", "diff", *diff_args, "-U0", "--no-color"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ScanError(f"git unavailable: {exc}") from exc
    if proc.returncode != 0:
        raise ScanError(f"git diff exited {proc.returncode}")
    return parse_staged_diff(proc.stdout)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Scan for high-confidence credential patterns (redacted output)")
    ap.add_argument("--staged", action="store_true",
                    help="scan git staged-diff added lines (pre-commit)")
    ap.add_argument("--range", metavar="A..B", dest="range_spec",
                    help="scan added lines of `git diff A..B` (e.g. a PR base..head, for CI)")
    ap.add_argument("files", nargs="*", help="files to scan")
    args = ap.parse_args()

    findings: list[tuple[str, int, str]] = []
    diff_args = (["--cached"] if args.staged
                 else [args.range_spec] if args.range_spec else None)
    if diff_args is not None:
        try:
            changed = _diff_added_lines(diff_args)
        except ScanError as exc:
            print(f"credential scan could not run ({exc})", file=sys.stderr)
            return 3
        for path, content in changed:
            if not _is_self(path):
                findings += scan_text(content, path)
    elif args.files:
        for f in args.files:
            if _is_self(f):
                continue
            try:
                findings += scan_text(
                    Path(f).read_text(encoding="utf-8", errors="replace"), f)
            except (OSError, ValueError):
                continue
    else:
        findings += scan_text(sys.stdin.read(), "<stdin>")

    if findings:
        print("CREDENTIAL PATTERN(S) DETECTED (values redacted):", file=sys.stderr)
        for label, lineno, name in findings:
            print(f"  {label}:{lineno}: {name}", file=sys.stderr)
        print("Rotate the exposed secret, remove it from the change, then retry.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
