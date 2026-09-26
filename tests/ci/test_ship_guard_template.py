"""#209: ship.md must carry one guarded SSoT write that actually runs, and no
direct-Edit alternative (AGENTS.md §Write Isolation). Found by the 2026-09-26
downstream simulation: no deployed doc had a runnable `guard_context_write.py
write` line (`--lock-key` and `--input` are required), and ship.md offered
"a surgical anchored Edit" instead.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHIP_MD = ROOT / ".agent" / "workflows" / "ship.md"
GUIDE_MD = ROOT / ".agentcortex" / "docs" / "guides" / "guarded-context-writes.md"
HELPER = ".agentcortex/tools/guard_context_write.py"
TARGET = ".agentcortex/context/current_state.md"


def _template_commands() -> list[str]:
    text = SHIP_MD.read_text(encoding="utf-8")
    commands = [
        line.split("  #", 1)[0].strip()
        for line in text.splitlines()
        if line.strip().startswith(f"python {HELPER} ")
    ]
    assert [c.split()[2] for c in commands] == ["snapshot", "write"], commands
    return commands


def test_ship_guarded_write_template_runs(tmp_path: Path) -> None:
    """Run ship.md's own snapshot -> write lines, verbatim apart from the placeholders."""
    (tmp_path / HELPER).parent.mkdir(parents=True)
    shutil.copy2(ROOT / HELPER, tmp_path / HELPER)
    (tmp_path / TARGET).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / TARGET).write_text("# Current State\n\n## Ship History\n", encoding="utf-8")
    edited = "# Current State\n\n## Ship History\n\n### Ship-test-2026-09-26\n- Tests: Pass\n"
    (tmp_path / "edited.md").write_text(edited, encoding="utf-8")

    snapshot_cmd, write_cmd = _template_commands()

    def run(cmd: str) -> subprocess.CompletedProcess[str]:
        argv = shlex.split(cmd)
        argv[0] = sys.executable
        return subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")

    snap = run(snapshot_cmd)
    assert snap.returncode == 0, snap.stderr
    sha = json.loads(snap.stdout)["sha256"]
    wrote = run(write_cmd.replace("<edited-copy>", "edited.md").replace("<sha256>", sha))
    assert wrote.returncode == 0, wrote.stdout + wrote.stderr
    assert (tmp_path / TARGET).read_text(encoding="utf-8") == edited


def test_ship_offers_no_direct_edit_and_guide_keeps_index_off_the_guard() -> None:
    ship = SHIP_MD.read_text(encoding="utf-8")
    assert "surgical anchored Edit" not in ship
    assert "never a direct Edit" in ship
    guide = GUIDE_MD.read_text(encoding="utf-8")
    # INDEX.jsonl is hash-chained; only append_chain_entry.py may append to it (ship.md §3).
    assert not re.search(r"^- `\.agentcortex/context/archive/INDEX\.jsonl`", guide, re.MULTILINE)
    assert "append_chain_entry.py" in guide
