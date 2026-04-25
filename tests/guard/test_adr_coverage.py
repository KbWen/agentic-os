"""Unit tests for tools/check_adr_coverage.py — Lesson L5 (AC-1) fix.

Spec: bootstrap.md §0a (rewritten 2026-04-25)
Lesson: current_state.md §Global Lessons L5 (post-first-adr regression)
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))

import check_adr_coverage as cov  # noqa: E402


def _adr(text: str, dirpath: Path, name: str) -> Path:
    p = dirpath / name
    p.write_text(text, encoding="utf-8")
    return p


class TestParseAppliesTo(unittest.TestCase):
    def test_block_list(self) -> None:
        fm = """status: accepted
applies_to:
  - "AGENTS.md"
  - ".agent/rules/**"
"""
        self.assertEqual(cov.parse_applies_to(fm), ["AGENTS.md", ".agent/rules/**"])

    def test_flow_list(self) -> None:
        fm = 'applies_to: ["a.md", "b/**"]\nother: x\n'
        self.assertEqual(cov.parse_applies_to(fm), ["a.md", "b/**"])

    def test_missing(self) -> None:
        fm = "status: accepted\n"
        self.assertEqual(cov.parse_applies_to(fm), [])


class TestCovers(unittest.TestCase):
    def test_exact(self) -> None:
        self.assertTrue(cov.covers(["AGENTS.md"], "AGENTS.md"))

    def test_recursive_glob(self) -> None:
        self.assertTrue(cov.covers([".agent/rules/**"], ".agent/rules/sub/x.md"))

    def test_negative(self) -> None:
        self.assertFalse(cov.covers(["AGENTS.md"], "src/foo.py"))

    def test_windows_path_normalized(self) -> None:
        self.assertTrue(cov.covers([".agent/rules/**"], r".agent\rules\x.md"))


class TestAdrGlobs(unittest.TestCase):
    def test_reads_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            adr_dir = Path(base_dir)
            _adr(
                '---\nstatus: accepted\napplies_to:\n  - "AGENTS.md"\n---\n# ADR-001\n',
                adr_dir,
                "ADR-001-x.md",
            )
            globs = cov.adr_globs(adr_dir)
            self.assertIn("ADR-001-x.md", globs)
            self.assertEqual(globs["ADR-001-x.md"], ["AGENTS.md"])

    def test_no_frontmatter_returns_empty_globs(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            adr_dir = Path(base_dir)
            _adr("# ADR-001 no frontmatter\nbody", adr_dir, "ADR-001-x.md")
            globs = cov.adr_globs(adr_dir)
            self.assertEqual(globs["ADR-001-x.md"], [])

    def test_missing_dir(self) -> None:
        self.assertEqual(cov.adr_globs(Path("/no/such/dir")), {})


class TestL5Regression(unittest.TestCase):
    """Lesson L5: post-first-ADR existence check breaks. Verify coverage check
    correctly distinguishes 'ADR exists' from 'ADR covers this task'."""

    def test_exists_does_not_imply_covers(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            adr_dir = Path(base_dir)
            _adr(
                '---\napplies_to:\n  - "AGENTS.md"\n---\n# ADR-001 governance only\n',
                adr_dir,
                "ADR-001-governance.md",
            )
            adr_map = cov.adr_globs(adr_dir)
            # ADR exists, but task touches src/queue/ — not covered
            covering = cov.covering_adrs(adr_map, ["src/queue/redis.py"])
            self.assertEqual(covering, {})

    def test_covering_adr_returned(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            adr_dir = Path(base_dir)
            _adr(
                '---\napplies_to:\n  - "src/queue/**"\n---\n# ADR-002 queue migration\n',
                adr_dir,
                "ADR-002-queue.md",
            )
            adr_map = cov.adr_globs(adr_dir)
            covering = cov.covering_adrs(adr_map, ["src/queue/redis.py"])
            self.assertIn("ADR-002-queue.md", covering)


if __name__ == "__main__":
    unittest.main()
