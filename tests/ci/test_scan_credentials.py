"""Credential scanner tests (backlog #71 / issue #225).

Catches high-confidence credential SHAPES; does NOT false-positive on realistic
benign content (incl. the strings the review panel reproduced as false positives);
output is redacted (never the value, even partially). Fakes are assembled at RUNTIME
by concatenation so no complete credential literal sits in the repo.

Tool: .agentcortex/tools/scan_credentials.py
Issue: https://github.com/KbWen/agentic-os/issues/225
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "scan_credentials.py"


def _load():
    spec = importlib.util.spec_from_file_location("scan_credentials", TOOL)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _fakes() -> dict[str, str]:
    """credential-SHAPED but verifiably fake — built by concat so no full literal."""
    return {
        "aws-access-key-id": "AKIA" + "IOSFODNN7" + "EXAMPLE",        # AKIA + 16
        "pem-private-key": "-----BEGIN " + "RSA PRIVATE KEY" + "-----",
        "github-token": "ghp_" + "A" * 36,
        "github-pat": "github_pat_" + "B" * 24,
        "openai-key": "sk-proj-" + "C" * 28,                          # sk-proj- family
        "slack-token": "xoxb-" + "1" * 24,                            # 24-char tail
        "google-api-key": "AIza" + "D" * 35,
    }


# Realistic benign content that MUST stay clean — includes the exact shapes the
# review panel reproduced as false positives (now fixed: sk-+32 too short, slack
# word-salad has no 24-run, and connection-string / JWT patterns were dropped).
_BENIGN = [
    "https://github.com/KbWen/agentic-os",
    "the AKIA prefix marks an AWS access key id",
    "use sk-123 as a short placeholder",
    "data-id: sk-3f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c",                  # sk- + 32 id
    "class sk-loading-spinner-component {}",
    "ghp_short and github_pat_short are not real",
    "AIzaSyShort",
    "token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3OD.benignSig",  # JWT (dropped)
    "db: postgres://serviceuser:password@db.example.com",           # conn-string
    "env: postgres://user:${DB_PASSWORD}@host",                     # env placeholder
    "amqp://guest:guestpassword@rabbitmq.local",                    # conn-string
    "git_sha da39a3ee5e6b4b0d3255bfef95601890afd80709",              # 40-hex SHA
    "uuid 550e8400-e29b-41d4-a716-446655440000",
    "xoxa-really-long-hyphenated-css-class-name-component",          # slack salad
]


def test_catches_every_pattern():
    tool = _load()
    for name, fake in _fakes().items():
        names = {f[2] for f in tool.scan_text(fake, "x")}
        assert name in names, f"{name} not caught"


def test_no_false_positive_on_benign():
    tool = _load()
    for benign in _BENIGN:
        assert tool.scan_text(benign, "x") == [], f"false positive on {benign!r}"


def test_output_is_redacted():
    """Structural guard: a finding is exactly (label, int, valid-name) and no 8-char
    run of the secret value appears in any field — catches partial/body leaks too."""
    tool = _load()
    valid = {p[0] for p in tool._PATTERNS}
    for fake in _fakes().values():
        for label, lineno, name in tool.scan_text(fake, "secretfile"):
            assert label == "secretfile" and isinstance(lineno, int) and name in valid
            blob = f"{label}|{lineno}|{name}"
            assert not any(fake[i:i + 8] in blob for i in range(len(fake) - 7)), \
                "scanner leaked >=8 chars of the value"


def test_dropped_ambiguous_patterns_absent():
    """connection-string + JWT were dropped (intrinsically ambiguous → TruffleHog)."""
    names = {p[0] for p in _load()._PATTERNS}
    assert "connection-string-password" not in names and "jwt" not in names


def test_main_exit_codes(tmp_path):
    dirty = tmp_path / "dirty.txt"
    dirty.write_text("token = " + "ghp_" + "Z" * 36 + "\n", encoding="utf-8")
    clean = tmp_path / "clean.txt"
    clean.write_text("just some normal text without secrets\n", encoding="utf-8")
    r_dirty = subprocess.run([sys.executable, str(TOOL), str(dirty)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    r_clean = subprocess.run([sys.executable, str(TOOL), str(clean)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r_dirty.returncode == 1 and r_clean.returncode == 0
    assert ("Z" * 36) not in (r_dirty.stdout + r_dirty.stderr)
    assert "github-token" in r_dirty.stderr


def test_self_skip():
    tool = _load()
    assert tool._is_self("a/b/scan_credentials.py")
    assert tool._is_self("tests/ci/test_scan_credentials.py")
    assert not tool._is_self("tests/ci/other.py")


def test_parse_diff_handles_edge_cases():
    """++-content line is NOT dropped; deletion side is not scanned."""
    tool = _load()
    diff = "\n".join([
        "diff --git a/f.txt b/f.txt", "--- a/f.txt", "+++ b/f.txt",
        "@@ -0,0 +1 @@", "+normal added line",
        "@@ -5,0 +6 @@", "++incremented",
        "diff --git a/del.txt b/del.txt", "--- a/del.txt", "+++ /dev/null",
        "-removed line",
    ])
    parsed = dict(tool.parse_staged_diff(diff))
    assert "normal added line" in parsed["f.txt"]
    assert "+incremented" in parsed["f.txt"]
    assert "del.txt" not in parsed


def test_parse_diff_trailing_tab():
    """git appends a TAB to space-containing paths; it must be stripped."""
    parsed = dict(_load().parse_staged_diff("+++ b/my file.txt\t\n@@ -0,0 +1 @@\n+x\n"))
    assert "my file.txt" in parsed


def test_parse_diff_content_line_looks_like_header():
    """Regression: an ADDED content line whose body is a raw diff fragment (e.g.
    ``++ /dev/null`` → diff ``+++ /dev/null``) must NOT reset the file context and
    drop the following secret line. Inside a hunk, every ``+`` line is content."""
    tool = _load()
    diff = "\n".join([
        "diff --git a/changelog.md b/changelog.md", "--- a/changelog.md",
        "+++ b/changelog.md", "@@ -0,0 +1,2 @@",
        "+++ /dev/null",                       # body '++ /dev/null', NOT a header
        "+secret on the next line",
    ])
    parsed = dict(tool.parse_staged_diff(diff))
    assert "changelog.md" in parsed
    assert "secret on the next line" in parsed["changelog.md"]


def test_range_mode(tmp_path):
    """--range A..B scans added lines of `git diff A..B` — the CI PR-diff use case
    (backlog #73). Shares the _diff_added_lines/parse_staged_diff path with --staged,
    so this just confirms CLI wiring + range diff end to end in an isolated repo."""
    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "a.txt").write_text("clean base\n", encoding="utf-8")
    git("add", "."), git("commit", "-qm", "base")
    (tmp_path / "b.txt").write_text("key = " + "ghp_" + "A" * 36 + "\n", encoding="utf-8")
    git("add", "."), git("commit", "-qm", "head")
    dirty = subprocess.run([sys.executable, str(TOOL), "--range", "HEAD~1..HEAD"],
                           cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace")
    clean = subprocess.run([sys.executable, str(TOOL), "--range", "HEAD..HEAD"],
                           cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert dirty.returncode == 1 and "github-token" in dirty.stderr
    assert clean.returncode == 0


def test_allowlist_pragma():
    """A line marked `# pragma: allowlist secret` is skipped — escape hatch for
    documented EXAMPLE tokens (e.g. AWS's own AKIA...EXAMPLE) so a blocking
    gate doesn't reject legit docs/fixtures (backlog #73 review finding)."""
    tool = _load()
    example = "AKIA" + "IOSFODNN7" + "EXAMPLE"           # AWS canonical doc example
    assert tool.scan_text(f"setup: {example}  # pragma: allowlist secret", "docs.md") == []
    assert tool.scan_text(f"setup: {example}", "docs.md")  # without the pragma → caught


def test_staged_git_failure_returns_3(tmp_path):
    """A git failure must fail-CLOSED with exit 3 (warn), never 0 (silent 'clean')."""
    r = subprocess.run([sys.executable, str(TOOL), "--staged"],
                       cwd=str(tmp_path), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 3
