"""Guard tests for check_archive_growth.py — the advisory archive-growth checker.

The tool is WARN-tier / never-FAIL (ADR-006 run_python_check contract, issue
#141): it ALWAYS exits 0 and prints a `WARN: ...` line only when the top-level
`*.md` count in the archive directory exceeds its cap. These tests drive the
pure-Python tool directly against synthetic archive dirs — deterministic, fast,
no bash/PowerShell, no `slow` marker.

Coverage:
  * over-cap archive        -> WARN with count/cap and remediation pointer
  * at-cap archive          -> no WARN, OK line
  * under-cap archive       -> no WARN, OK line
  * over-cap                -> still exit 0 (never fails the validator)
  * INDEX.jsonl + subdirs   -> excluded from the count (only top-level *.md)
  * missing archive dir     -> exit 0, silent (capability-by-presence)
  * cap read from config    -> custom cap honored; absent config -> default (50)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "check_archive_growth.py"

STD_CONFIG = "document_lifecycle:\n  archive_max_files: 50\n"


def make_archive(dir_path: Path, md_n: int, *, with_index: bool = True, subdir_md: int = 0) -> None:
    """Populate an archive dir with md_n top-level *.md files (+ optional noise)."""
    dir_path.mkdir(parents=True, exist_ok=True)
    for i in range(md_n):
        (dir_path / f"entry-{i:03d}.md").write_text(f"# entry {i}\n", encoding="utf-8")
    if with_index:
        # The append-only witness ledger must NOT be counted.
        (dir_path / "INDEX.jsonl").write_text('{"n":0}\n', encoding="utf-8")
    if subdir_md:
        sub = dir_path / "work"
        sub.mkdir(exist_ok=True)
        for i in range(subdir_md):
            (sub / f"log-{i}.md").write_text("# log\n", encoding="utf-8")


def run_tool(tmp_path: Path, archive: Path, config: str | None = STD_CONFIG):
    args = [sys.executable, str(TOOL), "--path", str(archive)]
    if config is not None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text(config, encoding="utf-8")
        args += ["--config", str(cfg)]
    else:
        # Point --config at a non-existent path -> exercises the default-cap
        # fallback (50) inside the tool.
        args += ["--config", str(tmp_path / "absent-config.yaml")]
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def test_over_cap_warns(tmp_path):
    archive = tmp_path / "archive"
    make_archive(archive, md_n=52)
    r = run_tool(tmp_path, archive)
    assert r.returncode == 0
    assert "archive directory has 52 top-level *.md files (cap 50)" in r.stdout
    assert "rotate/GC the oldest 2" in r.stdout
    assert "#141" in r.stdout


def test_at_cap_no_warn(tmp_path):
    archive = tmp_path / "archive"
    make_archive(archive, md_n=50)
    r = run_tool(tmp_path, archive)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "archive growth OK — 50/50" in r.stdout


def test_under_cap_no_warn(tmp_path):
    archive = tmp_path / "archive"
    make_archive(archive, md_n=13)
    r = run_tool(tmp_path, archive)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "archive growth OK — 13/50" in r.stdout


def test_over_cap_never_fails(tmp_path):
    archive = tmp_path / "archive"
    make_archive(archive, md_n=200)
    r = run_tool(tmp_path, archive)
    # Wildly over cap: the advisory tool must still exit 0 (never FAIL).
    assert r.returncode == 0
    assert "archive directory has 200 top-level *.md files (cap 50)" in r.stdout


def test_index_jsonl_and_subdirs_excluded(tmp_path):
    # 49 top-level *.md + INDEX.jsonl + 10 *.md under work/ must count as 49
    # (under cap 50) — only top-level *.md bodies are counted.
    archive = tmp_path / "archive"
    make_archive(archive, md_n=49, with_index=True, subdir_md=10)
    r = run_tool(tmp_path, archive)
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "archive growth OK — 49/50" in r.stdout


def test_missing_archive_dir_exits_zero_silent(tmp_path):
    args = [sys.executable, str(TOOL), "--path", str(tmp_path / "does-not-exist")]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_config_cap_is_honored(tmp_path):
    # Custom cap of 5 -> 6 md files must warn against cap 5, proving the tool
    # reads document_lifecycle.archive_max_files from config.
    archive = tmp_path / "archive"
    make_archive(archive, md_n=6)
    custom = "document_lifecycle:\n  archive_max_files: 5\n"
    r = run_tool(tmp_path, archive, config=custom)
    assert r.returncode == 0
    assert "archive directory has 6 top-level *.md files (cap 5)" in r.stdout


def test_absent_config_uses_default(tmp_path):
    # No config file -> default cap 50. 51 md files warns against cap 50.
    archive = tmp_path / "archive"
    make_archive(archive, md_n=51)
    r = run_tool(tmp_path, archive, config=None)
    assert r.returncode == 0
    assert "archive directory has 51 top-level *.md files (cap 50)" in r.stdout
