"""D10: bootstrap §3.6 Phases column must match registered skill metadata.

The column stays (the force ceiling in §3.6a reads it with zero metadata reads),
so it must not drift from `.agent/skills/<name>` `phases:`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def bootstrap_rows() -> dict[str, list[str]]:
    text = (ROOT / ".agent/workflows/bootstrap.md").read_text(encoding="utf-8")
    rows = {}
    for name, phases in re.findall(r"^\s*\| `([a-z0-9-]+)` \| ([a-z, ]+) \|", text, re.M):
        rows[name] = [p.strip() for p in phases.split(",")]
    return rows


def metadata_phases(name: str) -> list[str] | None:
    path = ROOT / ".agent/skills" / name
    if not path.is_file():
        return None
    match = re.search(r"^phases: \[([^\]]*)\]", path.read_text(encoding="utf-8"), re.M)
    return [p.strip().strip("\"'") for p in match.group(1).split(",")] if match else None


class TestBootstrapPhaseColumn(unittest.TestCase):
    def test_registered_skill_phases_match_metadata(self) -> None:
        rows = bootstrap_rows()
        self.assertGreaterEqual(len(rows), 10)
        checked = 0
        for name, phases in rows.items():
            meta = metadata_phases(name)
            if meta is None:  # e.g. kb-consult: operational adapter, no skill file
                continue
            checked += 1
            with self.subTest(skill=name):
                self.assertEqual(sorted(phases), sorted(meta))
        self.assertGreaterEqual(checked, 10)

    def test_db_and_auth_include_plan(self) -> None:
        rows = bootstrap_rows()
        for name in ("database-design", "auth-security"):
            self.assertIn("plan", rows[name])


if __name__ == "__main__":
    unittest.main()
