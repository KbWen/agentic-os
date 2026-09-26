"""Install-day copy from the 2026-09-26 downstream simulation (#207, #211).

- #211(b): `--dry-run` counted reference docs with different globs than the real
  deploy (26 previewed, 30 written) and did not mention the `.githooks` sample or
  the `.gitignore` edit.
- #207: the managed `.gitignore` block ignored `.cursor/` wholesale, hiding Cursor
  project rules that are meant to be committed. The line left the block; its
  `managed[]` entry stays so blocks written by older versions still strip clean.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (c for c in bash_candidates if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")

BLOCK_START = "# Agentic OS Template - Downstream Ignore Defaults"
BLOCK_END = "# End Agentic OS Template - Downstream Ignore Defaults"


def _deploy(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [bash, str(DEPLOY_SH), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )


@requires_bash
@pytest.mark.slow
def test_dry_run_previews_what_deploy_writes(tmp_path: Path) -> None:
    preview = _deploy("--dry-run", str(tmp_path / "preview"))
    assert preview.returncode == 0, preview.stderr
    m = re.search(r"\.\.\. (\d+) reference docs under \.agentcortex/docs/", preview.stdout)
    assert m, preview.stdout[-800:]
    assert ".githooks/pre-commit.guard-ssot.sample" in preview.stdout
    assert re.search(r"\.gitignore -- .*managed block", preview.stdout), preview.stdout[-800:]

    target = tmp_path / "real"
    target.mkdir()
    real = _deploy(str(target))
    assert real.returncode == 0, real.stderr
    deployed_docs = [p for p in (target / ".agentcortex" / "docs").rglob("*") if p.is_file()]
    assert int(m.group(1)) == len(deployed_docs), (
        f"dry-run previews {m.group(1)} reference docs, deploy wrote {len(deployed_docs)}"
    )


@requires_bash
@pytest.mark.slow
def test_old_block_with_cursor_upgrades_clean_and_adopter_lines_survive(tmp_path: Path) -> None:
    target = tmp_path / "proj"
    target.mkdir()
    assert _deploy(str(target)).returncode == 0
    gitignore = target / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert BLOCK_START in text and BLOCK_END in text
    assert ".cursor/" not in text.splitlines(), "the managed block must not ignore .cursor/ (#207)"

    # Rebuild the block the way versions up to v1.8.27 wrote it, with .cursor/ in the
    # middle, plus adopter lines on both sides of it.
    old = text.replace(".claude-chat/\n", ".claude-chat/\n.cursor/\n", 1)
    assert old != text
    gitignore.write_text("node_modules/\n" + old + "my-cursor-notes/\n", encoding="utf-8")

    assert _deploy(str(target)).returncode == 0
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert ".cursor/" not in lines, "an older block's .cursor/ line must strip clean on upgrade"
    assert lines.count(BLOCK_START) == 1 and lines.count(BLOCK_END) == 1
    assert "node_modules/" in lines and "my-cursor-notes/" in lines
    assert lines.index(".antigravity/scratch/") > lines.index(BLOCK_START), "block content kept"
