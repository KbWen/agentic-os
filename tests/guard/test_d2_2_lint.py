"""Unit tests for ADR-002 D2.2 — tools/lint_governed_writes.py.

Spec: docs/specs/lock-unification.md (AC-9..AC-14)
Run: python -m unittest discover -s tests/guard -v
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))

import lint_governed_writes as lint  # noqa: E402


def _scan(path: Path, content: str, ext: str = ".py") -> list[lint.Finding]:
    """Helper: write content to a file with given extension and scan it."""
    full = path / f"sample{ext}"
    full.write_text(content, encoding="utf-8")
    rel_posix = full.name
    globs = [".agentcortex/context/**", "AGENTS.md", "docs/architecture/*.log.md"]
    return lint.scan_file(full, rel_posix, globs)


class TestPythonOpenWrite(unittest.TestCase):
    """AC-10 + AC-11: detects open(path, 'w'/'a'/'x') against governed paths."""

    def test_governed_write_mode_fails(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            # Use the rel_posix as governed path
            full = Path(base_dir) / "sample.py"
            full.write_text("open('AGENTS.md', 'w').write('x')\n", encoding="utf-8")  # guard-exempt: test fixture string
            findings = lint.scan_file(full, "AGENTS.md", [".agentcortex/context/**", "AGENTS.md"])
            # The rel_posix passed in matches the lint's exemption list
            # so use a non-self-exempt name
            findings = lint.scan_file(full, "src/sample.py", [".agentcortex/context/**", "AGENTS.md"])
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].severity, "FAIL")
            self.assertIn("AGENTS.md", findings[0].detail)

    def test_governed_read_mode_ok(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.py"
            full.write_text("open('AGENTS.md', 'r').read()\n", encoding="utf-8")
            findings = lint.scan_file(full, "src/sample.py", ["AGENTS.md"])
            self.assertEqual(len(findings), 0)

    def test_default_mode_ok(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.py"
            full.write_text("open('AGENTS.md').read()\n", encoding="utf-8")
            findings = lint.scan_file(full, "src/sample.py", ["AGENTS.md"])
            self.assertEqual(len(findings), 0)

    def test_unprotected_path_ok(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.py"
            full.write_text("open('random.txt', 'w').write('x')\n", encoding="utf-8")
            findings = lint.scan_file(full, "src/sample.py", ["AGENTS.md"])
            self.assertEqual(len(findings), 0)


class TestVariablePathWarn(unittest.TestCase):
    """AC-11: dynamic / variable paths emit WARN, not FAIL."""

    def test_variable_path_warn(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.py"
            full.write_text("p = '/etc/passwd'\nopen(p, 'w').write('x')\n", encoding="utf-8")
            findings = lint.scan_file(full, "src/sample.py", ["AGENTS.md"])
            warns = [f for f in findings if f.severity == "WARN"]
            self.assertGreaterEqual(len(warns), 1)


class TestExemptionMarker(unittest.TestCase):
    """AC-12: # guard-exempt: <reason> suppresses FAIL on same/preceding line."""

    def test_same_line_exemption(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.py"
            full.write_text(
                "open('AGENTS.md', 'w').write('x')  # guard-exempt: legitimate test fixture\n",
                encoding="utf-8",
            )
            findings = lint.scan_file(full, "src/sample.py", ["AGENTS.md"])
            fails = [f for f in findings if f.severity == "FAIL"]
            warns = [f for f in findings if f.severity == "WARN"]
            self.assertEqual(len(fails), 0)
            # Counted as WARN with reason
            self.assertEqual(len(warns), 1)
            self.assertIn("legitimate test fixture", warns[0].detail)

    def test_preceding_line_exemption(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.py"
            full.write_text(
                "# guard-exempt: schema-bootstrap\nopen('AGENTS.md', 'w').write('x')\n",
                encoding="utf-8",
            )
            findings = lint.scan_file(full, "src/sample.py", ["AGENTS.md"])
            fails = [f for f in findings if f.severity == "FAIL"]
            self.assertEqual(len(fails), 0)


class TestShellPatterns(unittest.TestCase):
    """AC-10: shell redirect / tee detection."""

    def test_shell_redirect_to_governed(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.sh"
            full.write_text("echo hi > AGENTS.md\n", encoding="utf-8")
            findings = lint.scan_file(full, "scripts/sample.sh", ["AGENTS.md"])
            self.assertEqual(len([f for f in findings if f.severity == "FAIL"]), 1)

    def test_shell_tee_to_governed(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "sample.sh"
            full.write_text("echo hi | tee AGENTS.md\n", encoding="utf-8")
            findings = lint.scan_file(full, "scripts/sample.sh", ["AGENTS.md"])
            self.assertEqual(len([f for f in findings if f.severity == "FAIL"]), 1)


class TestSelfExempt(unittest.TestCase):
    """The guard tool itself + the lint tool itself are self-exempt."""

    def test_guard_tool_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            full = Path(base_dir) / "guard_context_write.py"
            full.write_text("open('AGENTS.md', 'w').write('x')\n", encoding="utf-8")  # guard-exempt: test fixture string
            findings = lint.scan_file(
                full,
                ".agentcortex/tools/guard_context_write.py",
                ["AGENTS.md"],
            )
            self.assertEqual(len(findings), 0)


class TestExtractPathLiteral(unittest.TestCase):
    def test_single_quote(self) -> None:
        self.assertEqual(lint.extract_path_literal("'AGENTS.md'"), "AGENTS.md")

    def test_double_quote(self) -> None:
        self.assertEqual(lint.extract_path_literal('"AGENTS.md"'), "AGENTS.md")

    def test_with_trailing_paren(self) -> None:
        self.assertEqual(lint.extract_path_literal("'AGENTS.md',"), "AGENTS.md")

    def test_variable_returns_none(self) -> None:
        self.assertIsNone(lint.extract_path_literal("path"))
        self.assertIsNone(lint.extract_path_literal("base / 'foo'"))


class TestEndToEndExitCode(unittest.TestCase):
    """Lint exits 1 on any FAIL finding, 0 otherwise (AC-13)."""

    def test_exit_zero_on_clean(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            (base / ".agent").mkdir()
            (base / ".agent" / "config.yaml").write_text(
                "guard_policy:\n  protected_paths:\n    - AGENTS.md\n",
                encoding="utf-8",
            )
            (base / "good.py").write_text("print('hello')\n", encoding="utf-8")
            # Inline main with sys.argv override
            saved_argv = sys.argv[:]
            try:
                sys.argv = ["lint_governed_writes.py", "--root", str(base)]
                rc = lint.main()
            finally:
                sys.argv = saved_argv
            self.assertEqual(rc, 0)

    def test_exit_one_on_fail(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            base = Path(base_dir)
            (base / ".agent").mkdir()
            (base / ".agent" / "config.yaml").write_text(
                "guard_policy:\n  protected_paths:\n    - AGENTS.md\n",
                encoding="utf-8",
            )
            (base / "bad.py").write_text(
                # guard-exempt: test fixture string
                "open('AGENTS.md', 'w').write('x')\n", encoding="utf-8"
            )
            saved_argv = sys.argv[:]
            try:
                sys.argv = ["lint_governed_writes.py", "--root", str(base)]
                rc = lint.main()
            finally:
                sys.argv = saved_argv
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
