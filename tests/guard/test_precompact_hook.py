"""Tests for .claude/hooks/check-precompact.py — PreCompact Phase Summary flush hook.

Closes the partial gap from CC-2 / Lesson L4: compaction was unguarded; an
agent could be auto-compacted mid-phase before flushing reasoning into the
Work Log Phase Summary.

Test surface mirrors the structure of test_sentinel_hook.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "check-precompact.py"

_spec = importlib.util.spec_from_file_location("check_precompact", HOOK)
hook = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(hook)  # type: ignore[union-attr]


VALID_HEADER = """- Branch: `feat/test-precompact`
- Classification: `quick-win`
- Current Phase: `implement`
- Checkpoint SHA: `abc1234`
"""


def _wl(header: str, phase_summary: str) -> str:
    return f"""# Work Log

## Header

{header}

## Phase Summary

{phase_summary}

## Evidence

none
"""


class TestParseHeaderField(unittest.TestCase):
    def test_list_form(self):
        self.assertEqual(hook.parse_header_field(_wl(VALID_HEADER, ""), "Current Phase"), "implement")

    def test_table_form(self):
        table_header = "| Current Phase | `plan` |\n| Branch | `feat/x` |\n"
        self.assertEqual(hook.parse_header_field(_wl(table_header, ""), "Current Phase"), "plan")

    def test_missing(self):
        self.assertEqual(hook.parse_header_field("# nothing\n", "Current Phase"), "")


class TestPhaseSummarySection(unittest.TestCase):
    def test_extract(self):
        wl = _wl(VALID_HEADER, "- implement: did the thing")
        body = hook.phase_summary_section(wl)
        self.assertIn("implement: did the thing", body)
        self.assertNotIn("Evidence", body)

    def test_missing_section(self):
        self.assertEqual(hook.phase_summary_section("# no summary\n"), "")


class TestEvaluate(unittest.TestCase):
    def test_ok_when_phase_in_summary(self):
        wl = _wl(VALID_HEADER, "- implement: edited 8 files")
        ok, reason = hook.evaluate(wl)
        self.assertTrue(ok, reason)

    def test_block_when_summary_empty(self):
        wl = _wl(VALID_HEADER, "none")
        ok, reason = hook.evaluate(wl)
        self.assertFalse(ok)
        self.assertIn("empty", reason)

    def test_block_when_phase_not_in_summary(self):
        # Current Phase is `implement` but only a plan line is recorded
        wl = _wl(VALID_HEADER, "- plan: drafted plan")
        ok, reason = hook.evaluate(wl)
        self.assertFalse(ok)
        self.assertIn("does not mention", reason)

    def test_ok_when_no_current_phase(self):
        # Pre-bootstrap state — should not block
        header = "- Branch: `feat/x`\n- Current Phase: `none`\n"
        wl = _wl(header, "none")
        ok, _ = hook.evaluate(wl)
        self.assertTrue(ok)


class TestWorklogKey(unittest.TestCase):
    def test_slash_normalization(self):
        self.assertEqual(hook.worklog_key("feat/foo"), "feat-foo")
        self.assertEqual(hook.worklog_key("hotfix/bar/baz"), "hotfix-bar-baz")


class TestEndToEnd(unittest.TestCase):
    """Run the hook's main() against a temp Work Log + temp receipt path."""

    def test_silent_when_no_worklog(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(hook, "WORKLOG_DIR", Path(td)):
                with mock.patch.object(hook, "current_branch", return_value="missing-branch"):
                    rc = hook.main()
        self.assertEqual(rc, 0)

    def test_writes_violation_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            wl_dir = Path(td) / "work"
            wl_dir.mkdir()
            wl = wl_dir / "feat-x.md"
            wl.write_text(_wl("- Branch: `feat/x`\n- Current Phase: `implement`\n", "none"), encoding="utf-8")
            receipt = Path(td) / "precompact-violations.jsonl"
            with mock.patch.object(hook, "WORKLOG_DIR", wl_dir), \
                 mock.patch.object(hook, "RECEIPT", receipt), \
                 mock.patch.object(hook, "current_branch", return_value="feat/x"), \
                 mock.patch.object(hook.sys, "stdin", new=type("S", (), {"read": staticmethod(lambda: "{}")})()):
                # Provide an empty stdin payload via direct read patch
                with mock.patch.object(hook, "read_payload", return_value={"session_id": "s1"}):
                    rc = hook.main()
            self.assertEqual(rc, 0)  # WARN mode default
            self.assertTrue(receipt.exists())
            data = receipt.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(data), 1)
            rec = json.loads(data[0])
            self.assertEqual(rec["violation"], "stale_phase_summary")
            self.assertEqual(rec["session_id"], "s1")

    def test_block_mode_exits_2(self):
        with tempfile.TemporaryDirectory() as td:
            wl_dir = Path(td) / "work"
            wl_dir.mkdir()
            wl = wl_dir / "feat-x.md"
            wl.write_text(_wl("- Branch: `feat/x`\n- Current Phase: `plan`\n", "none"), encoding="utf-8")
            receipt = Path(td) / "precompact-violations.jsonl"
            with mock.patch.object(hook, "WORKLOG_DIR", wl_dir), \
                 mock.patch.object(hook, "RECEIPT", receipt), \
                 mock.patch.object(hook, "current_branch", return_value="feat/x"), \
                 mock.patch.dict(os.environ, {"AGENTIC_OS_PRECOMPACT_BLOCK": "1"}), \
                 mock.patch.object(hook, "read_payload", return_value={}):
                rc = hook.main()
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
