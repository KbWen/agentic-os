"""Tests for .claude/hooks/check-sentinel.py — Sentinel ⚡ ACX Stop hook.

Closes CC-2 honor-system gap; promotes Lesson L4 from honor-system to
externally observable.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "check-sentinel.py"

# Load the hook module dynamically (it's not on a package path)
_spec = importlib.util.spec_from_file_location("check_sentinel", HOOK)
hook = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(hook)  # type: ignore[union-attr]


def _make_transcript(messages: list[dict], path: Path) -> None:
    """Write a fake transcript JSONL: each msg is {type, content_text}."""
    lines = []
    for m in messages:
        if m.get("type") == "assistant":
            lines.append(
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "content": [{"type": "text", "text": m["content_text"]}]
                        },
                    }
                )
            )
        else:
            lines.append(json.dumps({"type": m["type"], "message": {"content": m.get("content_text", "")}}))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestHasSentinel(unittest.TestCase):
    def test_sentinel_present_at_end(self) -> None:
        self.assertTrue(hook.has_sentinel("hello world\n\n⚡ ACX"))

    def test_sentinel_within_tail_window(self) -> None:
        self.assertTrue(hook.has_sentinel("a" * 50 + "\n⚡ ACX\n"))

    def test_sentinel_missing(self) -> None:
        self.assertFalse(hook.has_sentinel("hello world without marker"))

    def test_sentinel_far_from_tail(self) -> None:
        # Sentinel deep in the middle of long text — outside the 200-char tail window
        text = "⚡ ACX\n" + ("x" * 500)
        self.assertFalse(hook.has_sentinel(text))

    def test_empty(self) -> None:
        self.assertFalse(hook.has_sentinel(""))


class TestLastAssistantText(unittest.TestCase):
    def test_picks_last_assistant(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            t = Path(base_dir) / "transcript.jsonl"
            _make_transcript(
                [
                    {"type": "user", "content_text": "hi"},
                    {"type": "assistant", "content_text": "first reply"},
                    {"type": "user", "content_text": "more"},
                    {"type": "assistant", "content_text": "second reply ⚡ ACX"},
                ],
                t,
            )
            text = hook.last_assistant_text(t)
            self.assertIn("second reply", text)

    def test_missing_file_returns_empty(self) -> None:
        self.assertEqual(hook.last_assistant_text(Path("/no/such/file")), "")


class TestWriteViolation(unittest.TestCase):
    def test_writes_jsonl_record(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            receipt = Path(base_dir) / "violations.jsonl"
            payload = {"session_id": "abc", "stop_hook_active": False}
            hook.write_violation(payload, "tail text without marker", receipt_path=receipt)
            content = receipt.read_text(encoding="utf-8")
            line = content.strip()
            obj = json.loads(line)
            self.assertEqual(obj["violation"], "missing_sentinel")
            self.assertEqual(obj["session_id"], "abc")
            self.assertIn("tail text", obj["tail"])

    def test_appends_not_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as base_dir:
            receipt = Path(base_dir) / "violations.jsonl"
            hook.write_violation({"session_id": "1"}, "first", receipt_path=receipt)
            hook.write_violation({"session_id": "2"}, "second", receipt_path=receipt)
            lines = [ln for ln in receipt.read_text(encoding="utf-8").splitlines() if ln]
            self.assertEqual(len(lines), 2)


class TestEndToEnd(unittest.TestCase):
    """Run the hook's main() against fake stdin + transcript, verify behavior."""

    def setUp(self) -> None:
        # Keep the temp dir alive across the test method so receipts can be inspected.
        self._tmpdir = tempfile.TemporaryDirectory()
        self.base = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _run(self, transcript_messages: list[dict], session_id: str = "test") -> tuple[int, Path]:
        t = self.base / "transcript.jsonl"
        _make_transcript(transcript_messages, t)
        payload = {"session_id": session_id, "transcript_path": str(t)}
        saved_receipt = hook.RECEIPT
        saved_stdin = sys.stdin
        saved_stderr = sys.stderr
        tmp_receipt = self.base / "viol.jsonl"
        hook.RECEIPT = tmp_receipt
        try:
            from io import StringIO
            sys.stdin = StringIO(json.dumps(payload))
            sys.stderr = StringIO()
            rc = hook.main()
        finally:
            hook.RECEIPT = saved_receipt
            sys.stdin = saved_stdin
            sys.stderr = saved_stderr
        return rc, tmp_receipt

    def test_sentinel_present_returns_zero(self) -> None:
        rc, receipt = self._run(
            [{"type": "assistant", "content_text": "all done\n\n⚡ ACX"}]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(receipt.exists(), "no receipt should be written on success")

    def test_sentinel_missing_returns_one_and_logs(self) -> None:
        rc, receipt = self._run(
            [{"type": "assistant", "content_text": "all done without marker"}]
        )
        self.assertEqual(rc, 1)
        self.assertTrue(receipt.exists())
        line = receipt.read_text(encoding="utf-8").strip()
        obj = json.loads(line)
        self.assertEqual(obj["violation"], "missing_sentinel")

    def test_no_assistant_yet_returns_zero(self) -> None:
        rc, receipt = self._run([{"type": "user", "content_text": "hello"}])
        self.assertEqual(rc, 0)
        self.assertFalse(receipt.exists())

    def test_no_transcript_path_returns_zero(self) -> None:
        # R-6 fix: silent EXIT 0 left no trace; now logs could_not_verify.
        saved_stdin = sys.stdin
        saved_receipt = hook.RECEIPT
        hook.RECEIPT = self.base / "viol-no-path.jsonl"
        try:
            from io import StringIO
            sys.stdin = StringIO("{}")
            rc = hook.main()
        finally:
            hook.RECEIPT = saved_receipt
            sys.stdin = saved_stdin
        self.assertEqual(rc, 0)
        self.assertTrue((self.base / "viol-no-path.jsonl").exists())
        obj = json.loads((self.base / "viol-no-path.jsonl").read_text(encoding="utf-8").strip())
        self.assertEqual(obj["violation"], "could_not_verify")
        self.assertEqual(obj["reason"], "missing_transcript_path")

    def test_unreadable_transcript_path_logs_could_not_verify(self) -> None:
        # R-6: transcript_path provided but file doesn't exist (Windows path
        # mismatch, deleted file). Was silent EXIT 0; now leaves a trace.
        saved_stdin = sys.stdin
        saved_receipt = hook.RECEIPT
        hook.RECEIPT = self.base / "viol-unreadable.jsonl"
        try:
            from io import StringIO
            sys.stdin = StringIO(json.dumps({"transcript_path": "/no/such/path.jsonl", "session_id": "x"}))
            rc = hook.main()
        finally:
            hook.RECEIPT = saved_receipt
            sys.stdin = saved_stdin
        self.assertEqual(rc, 0)
        obj = json.loads((self.base / "viol-unreadable.jsonl").read_text(encoding="utf-8").strip())
        self.assertEqual(obj["violation"], "could_not_verify")
        self.assertIn("transcript_unreadable", obj["reason"])


if __name__ == "__main__":
    unittest.main()
