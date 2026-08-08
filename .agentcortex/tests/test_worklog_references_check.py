"""Guard tests for check_worklog_references.py — the advisory Work Log
`## External References` existence checker (backlog #161).

The tool is WARN-tier / never-FAIL (ADR-006 run_python_check contract): it
ALWAYS exits 0 and prints `WARN: ...` lines only for a Spec/ADR referent that
does not exist on disk, or a PR/Issue referent whose format is neither a URL,
a `#NNN` shorthand, nor the `—` placeholder. These tests drive the pure-Python
tool directly via subprocess against synthetic Work Log fixtures — deterministic,
fast, no bash/PowerShell, no `slow` marker.

Coverage:
  * nonexistent Spec / ADR path         -> WARN, names the missing path
  * valid Spec path                     -> silent
  * `—` / blank placeholder             -> silent (exempt)
  * http(s):// URL in a Spec row        -> silent (exempt, no network call)
  * backtick-wrapped valid path         -> silent (wrapping stripped)
  * malformed PR/Issue reference        -> WARN, format-only wording
  * `#NNN` shorthand PR/Issue reference -> silent
  * URL PR/Issue reference              -> silent
  * tool always exits 0, even with multiple WARNs present
  * dotfile logs (e.g. `.gitkeep.md`) ignored
  * no active logs / missing dir        -> exit 0, silent
  * multiple logs                       -> findings aggregate with filename prefix
  * default --worklog-dir resolution    -> matches the real validator invocation
    (validate.sh/.ps1 pass only --root, relying on the default)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "check_worklog_references.py"

TABLE_HEADER = "## External References\n\n| Type | Path / URL | Notes |\n|---|---|---|\n"


def write_log(work_dir: Path, name: str, rows: str) -> Path:
    """Write one Work Log fixture with an External References table."""
    work_dir.mkdir(parents=True, exist_ok=True)
    content = TABLE_HEADER + rows + "\n## Known Risk\n\nnone\n"
    p = work_dir / name
    p.write_text(content, encoding="utf-8")
    return p


def run_tool(root: Path, worklog_dir: Path | None = None):
    args = [sys.executable, str(TOOL), "--root", str(root)]
    if worklog_dir is not None:
        args += ["--worklog-dir", str(worklog_dir)]
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def test_nonexistent_spec_path_warns(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec | docs/specs/nonexistent.md | fabricated |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" in r.stdout
    assert "a.md" in r.stdout
    assert "Spec path 'docs/specs/nonexistent.md' does not exist" in r.stdout


def test_nonexistent_adr_path_warns(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| ADR | docs/adr/ADR-999-fake.md | fabricated |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "ADR path 'docs/adr/ADR-999-fake.md' does not exist" in r.stdout


def test_valid_spec_path_is_silent(tmp_path):
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "real.md").write_text("real\n", encoding="utf-8")
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec | docs/specs/real.md | ok |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "OK" in r.stdout


def test_backtick_wrapped_valid_path_is_silent(tmp_path):
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "real.md").write_text("real\n", encoding="utf-8")
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec | `docs/specs/real.md` | ok |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def test_placeholder_rows_are_silent(tmp_path):
    work = tmp_path / "work"
    rows = "| Spec | — | — |\n| ADR | — | — |\n| Issue | — | — |\n| PR | — | — |\n"
    write_log(work, "a.md", rows)
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "OK" in r.stdout


def test_blank_path_cell_is_silent(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec |  |  |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def test_url_spec_path_exempt_no_existence_check(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec | https://example.com/spec-does-not-exist.md | ok |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def test_malformed_pr_reference_warns(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| PR | see slack channel | malformed |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" in r.stdout
    assert "not a URL, #NNN reference, or" in r.stdout
    assert "no network call" in r.stdout


def test_malformed_issue_reference_warns(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| Issue | not-a-url-or-hash | malformed |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" in r.stdout
    assert "Issue reference" in r.stdout


def test_hash_shorthand_pr_reference_is_silent(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| PR | #385 | ok |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def test_multiple_hash_shorthand_with_extra_text_is_silent(tmp_path):
    """Real-world shape (chore-v1.8.18-release worklog): several `#NNN` tokens
    plus free text ('+ 4 ship records') in one PR cell must not false-WARN."""
    work = tmp_path / "work"
    write_log(work, "a.md", "| PR | #379 #381 #383 + 4 ship records | packaged |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def test_url_pr_reference_is_silent(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| PR | https://github.com/KbWen/agentic-os/pull/999 | unverified |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    # Honest limitation, not asserted as a finding: PR existence itself is not
    # network-checked, so a fabricated-but-well-formed PR URL is expected silent.


def test_tool_always_exits_zero_even_with_findings(tmp_path):
    work = tmp_path / "work"
    rows = (
        "| Spec | docs/specs/missing1.md | x |\n"
        "| ADR | docs/adr/missing2.md | x |\n"
        "| Issue | garbage | x |\n"
        "| PR | garbage | x |\n"
    )
    write_log(work, "a.md", rows)
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert r.stdout.count("WARN:") == 4


def test_dotfile_logs_are_ignored(tmp_path):
    work = tmp_path / "work"
    write_log(work, ".gitkeep.md", "| Spec | docs/specs/nonexistent.md | fabricated |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_no_active_logs_is_silent(tmp_path):
    work = tmp_path / "work"
    work.mkdir(parents=True)
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_missing_worklog_dir_exits_zero_silent(tmp_path):
    r = run_tool(tmp_path, tmp_path / "does-not-exist")
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_no_external_references_section_is_silent(tmp_path):
    """No `## External References` heading at all -> 0 rows found for an
    otherwise-active log. The log itself was still checked (hence the OK
    summary, same as any other zero-finding run) -- "silent" here means no
    WARN, not empty stdout; only zero ACTIVE LOGS produces empty stdout."""
    work = tmp_path / "work"
    work.mkdir(parents=True)
    (work / "a.md").write_text("# Work Log: a\n\n## Known Risk\n\nnone\n", encoding="utf-8")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "0 row(s) checked" in r.stdout


def test_multiple_logs_aggregate_with_filename_prefix(tmp_path):
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec | docs/specs/missing-a.md | x |\n")
    write_log(work, "b.md", "| Spec | docs/specs/missing-b.md | x |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "a.md" in r.stdout and "missing-a.md" in r.stdout
    assert "b.md" in r.stdout and "missing-b.md" in r.stdout


def test_default_worklog_dir_resolution_matches_real_invocation(tmp_path):
    """No --worklog-dir override: resolves <root>/.agentcortex/context/work —
    the exact invocation validate.sh / validate.ps1 use (--root only)."""
    work = tmp_path / ".agentcortex" / "context" / "work"
    write_log(work, "a.md", "| Spec | docs/specs/missing.md | x |\n")
    r = run_tool(tmp_path)
    assert r.returncode == 0
    assert "WARN:" in r.stdout
    assert "docs/specs/missing.md" in r.stdout


def test_leading_slash_path_treated_as_repo_relative(tmp_path):
    """Deterministic cross-platform resolution: a leading `/` must resolve
    repo-relative on both Windows and POSIX, not via Path.is_absolute()
    (which disagrees between platforms for a bare leading slash)."""
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "real.md").write_text("real\n", encoding="utf-8")
    work = tmp_path / "work"
    write_log(work, "a.md", "| Spec | /docs/specs/real.md | ok |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def test_unknown_row_type_is_ignored(tmp_path):
    """Forward compatibility: a future template row type is neither
    existence-checked nor format-checked, and must not crash the tool."""
    work = tmp_path / "work"
    write_log(work, "a.md", "| Design | some free text | future row type |\n")
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout


def write_raw_log(work_dir: Path, name: str, content: str) -> Path:
    """Write a Work Log fixture with full content control (fence tests)."""
    work_dir.mkdir(parents=True, exist_ok=True)
    p = work_dir / name
    p.write_text(content, encoding="utf-8")
    return p


def test_fenced_decoy_heading_does_not_shadow_real_section(tmp_path):
    """External-review P1 (backlog #156 decoy family): a fenced example
    containing the heading + a plausible table must NOT bind the parser —
    the REAL section's bogus path is the one that has to WARN, and the
    decoy's path must not be reported at all."""
    work = tmp_path / "work"
    write_raw_log(
        work,
        "a.md",
        "# Work Log: decoy\n\nExample of the section format:\n\n"
        "```\n## External References\n\n| Type | Path / URL | Notes |\n"
        "|---|---|---|\n| Spec | docs/specs/decoy-only.md | fenced example |\n```\n\n"
        "## External References\n\n| Type | Path / URL | Notes |\n|---|---|---|\n"
        "| Spec | docs/specs/does-not-exist.md | real section |\n\n## Known Risk\n\nnone\n",
    )
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "Spec path 'docs/specs/does-not-exist.md' does not exist" in r.stdout
    assert "decoy-only.md" not in r.stdout


def test_fenced_example_rows_inside_real_section_are_ignored(tmp_path):
    """A fenced example table INSIDE the real section is documentation,
    not live rows — only the unfenced row may WARN."""
    work = tmp_path / "work"
    write_raw_log(
        work,
        "a.md",
        "## External References\n\nFormat example:\n\n"
        "```\n| Spec | docs/specs/fenced-example.md | doc |\n```\n\n"
        "| Type | Path / URL | Notes |\n|---|---|---|\n"
        "| Spec | docs/specs/really-missing.md | live |\n\n## Known Risk\n\nnone\n",
    )
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "really-missing.md" in r.stdout
    assert "fenced-example.md" not in r.stdout


def test_fenced_only_heading_yields_no_findings(tmp_path):
    """A log whose ONLY `## External References` heading sits inside a fence
    has no real section — the tool must stay silent, not scan the fence."""
    work = tmp_path / "work"
    write_raw_log(
        work,
        "a.md",
        "# Work Log: fenced only\n\n"
        "```\n## External References\n\n| Type | Path / URL | Notes |\n"
        "|---|---|---|\n| Spec | docs/specs/ghost.md | fenced |\n```\n\n"
        "## Known Risk\n\nnone\n",
    )
    r = run_tool(tmp_path, work)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
