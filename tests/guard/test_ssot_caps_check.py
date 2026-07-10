"""Guard tests for check_ssot_caps.py — the advisory SSoT section-cap checker.

The tool is WARN-tier / never-FAIL (ADR-006 run_python_check contract): it
ALWAYS exits 0 and prints `WARN: ...` lines only when a section exceeds its
cap. These tests drive the pure-Python tool directly against synthetic SSoT
fixtures — deterministic, fast, no bash/PowerShell, no `slow` marker.

Coverage:
  * over-cap Ship History  -> Ship History WARN
  * at-cap Ship History    -> no WARN
  * Spec Index over 30     -> Spec Index WARN
  * under-cap both         -> OK line, no WARN
  * over-cap               -> still exit 0 (never fails the validator)
  * missing SSoT file      -> exit 0, silent (capability-by-presence)
  * caps read from config  -> custom cap honored; absent config -> defaults
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "check_ssot_caps.py"

STD_CONFIG = (
    "document_lifecycle:\n"
    "  ship_history_max_entries: 10\n"
    "  spec_index_max_entries: 30\n"
)


def make_ssot(ship_n: int, spec_n: int) -> str:
    """Build a minimal current_state.md with the two capped sections."""
    specs = "\n".join(
        f"  - docs/specs/s{i}.md — spec {i}, [Shipped]" for i in range(spec_n)
    )
    ship = "\n\n".join(
        f"### Ship-x{i}-2026-01-01\n- Feature shipped: x{i}\n- Tests: Pass"
        for i in range(ship_n)
    )
    parts = ["# Project Current State (vNext)", ""]
    parts += ["- **Spec Index** (shipped specs at `docs/specs/`):"]
    if specs:
        parts.append(specs)
    parts += ["- **Canonical Commands**:", "  - `/ship`: ship it.", ""]
    parts += ["## Ship History", "", ship, ""]
    return "\n".join(parts)


def run_tool(tmp_path: Path, content: str, config: str | None = STD_CONFIG):
    ssot = tmp_path / "current_state.md"
    ssot.write_text(content, encoding="utf-8")
    args = [sys.executable, str(TOOL), "--path", str(ssot)]
    if config is not None:
        cfg = tmp_path / "config.yaml"
        cfg.write_text(config, encoding="utf-8")
        args += ["--config", str(cfg)]
    else:
        # Point --config at a path that does not exist -> exercises the
        # default-caps fallback (10 / 30) inside the tool.
        args += ["--config", str(tmp_path / "absent-config.yaml")]
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8")


def test_over_cap_ship_history_warns(tmp_path):
    r = run_tool(tmp_path, make_ssot(ship_n=12, spec_n=5))
    assert r.returncode == 0
    assert "Ship History has 12 entries (cap 10)" in r.stdout
    assert "ship.md §State Update" in r.stdout
    # spec index (5) is under cap -> no spec warn
    assert "Spec Index has" not in r.stdout


def test_at_cap_ship_history_no_warn(tmp_path):
    r = run_tool(tmp_path, make_ssot(ship_n=10, spec_n=5))
    assert r.returncode == 0
    assert "Ship History has" not in r.stdout
    assert "ssot caps OK" in r.stdout
    assert "ship history 10/10" in r.stdout


def test_spec_index_over_cap_warns(tmp_path):
    r = run_tool(tmp_path, make_ssot(ship_n=3, spec_n=31))
    assert r.returncode == 0
    assert "Spec Index has 31 entries (cap 30)" in r.stdout
    assert "ship.md:197" in r.stdout
    # ship history (3) is under cap -> no ship warn
    assert "Ship History has" not in r.stdout


def test_under_cap_both_ok(tmp_path):
    r = run_tool(tmp_path, make_ssot(ship_n=3, spec_n=5))
    assert r.returncode == 0
    assert "WARN:" not in r.stdout
    assert "ssot caps OK" in r.stdout
    assert "ship history 3/10" in r.stdout
    assert "spec index 5/30" in r.stdout


def test_over_cap_never_fails(tmp_path):
    # Both wildly over cap: the advisory tool must still exit 0 (never FAIL).
    r = run_tool(tmp_path, make_ssot(ship_n=50, spec_n=50))
    assert r.returncode == 0
    assert "Ship History has 50 entries (cap 10)" in r.stdout
    assert "Spec Index has 50 entries (cap 30)" in r.stdout


def test_missing_ssot_file_exits_zero_silent(tmp_path):
    args = [
        sys.executable,
        str(TOOL),
        "--path",
        str(tmp_path / "does-not-exist.md"),
    ]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_config_cap_is_honored(tmp_path):
    # Custom cap of 5 -> 6 ship entries must warn against cap 5, proving the
    # tool reads document_lifecycle.ship_history_max_entries from config.
    custom = (
        "document_lifecycle:\n"
        "  ship_history_max_entries: 5\n"
        "  spec_index_max_entries: 30\n"
    )
    r = run_tool(tmp_path, make_ssot(ship_n=6, spec_n=3), config=custom)
    assert r.returncode == 0
    assert "Ship History has 6 entries (cap 5)" in r.stdout


def test_absent_config_uses_defaults(tmp_path):
    # No config file -> defaults (10 / 30). 12 ship entries warns against cap 10.
    r = run_tool(tmp_path, make_ssot(ship_n=12, spec_n=3), config=None)
    assert r.returncode == 0
    assert "Ship History has 12 entries (cap 10)" in r.stdout
