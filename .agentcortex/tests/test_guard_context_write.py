import json
import hashlib
import time
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "tools" / "guard_context_write.py"


def run_tool(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def lock_name_for(target: str) -> str:
    digest = hashlib.sha256(target.encode("utf-8")).hexdigest()[:16]
    stem = Path(target).stem.lower()
    return f"{stem}-{digest}.lock"


class GuardContextWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        (self.root / ".agentcortex/context/work").mkdir(parents=True)
        self.target = self.root / ".agentcortex/context/current_state.md"
        self.input_path = self.root / "rendered.md"

    def test_snapshot_reports_missing_file(self) -> None:
        result = run_tool(
            self.root,
            "snapshot",
            "--root",
            ".",
            "--path",
            ".agentcortex/context/current_state.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["exists"])
        self.assertEqual(payload["sha256"], "MISSING")

    def test_write_succeeds_and_updates_receipt(self) -> None:
        self.input_path.write_text("hello guarded world\n", encoding="utf-8")
        result = run_tool(
            self.root,
            "write",
            "--root",
            ".",
            "--path",
            ".agentcortex/context/current_state.md",
            "--expected-sha",
            "MISSING",
            "--lock-key",
            "current-state",
            "--input",
            "rendered.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "hello guarded world\n")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "ok")

        receipt = self.root / ".agentcortex/context/.guard_receipt.json"
        self.assertTrue(receipt.is_file())
        receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt_payload["target"], ".agentcortex/context/current_state.md")
        self.assertEqual(payload["receipt"], ".agentcortex/context/.guard_receipt.json")

    def test_stale_sha_fails_without_partial_write(self) -> None:
        self.target.write_text("old state\n", encoding="utf-8")
        self.input_path.write_text("new state\n", encoding="utf-8")
        result = run_tool(
            self.root,
            "write",
            "--root",
            ".",
            "--path",
            ".agentcortex/context/current_state.md",
            "--expected-sha",
            "deadbeef",
            "--lock-key",
            "current-state",
            "--input",
            "rendered.md",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("stale-sha", result.stderr)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "old state\n")

    def test_existing_lock_reports_conflict(self) -> None:
        locks = self.root / ".agentcortex/context/.guard_locks"
        locks.mkdir(parents=True)
        lock_name = lock_name_for(".agentcortex/context/current_state.md")
        (locks / lock_name).write_text("busy", encoding="utf-8")
        self.input_path.write_text("new state\n", encoding="utf-8")
        result = run_tool(
            self.root,
            "write",
            "--root",
            ".",
            "--path",
            ".agentcortex/context/current_state.md",
            "--expected-sha",
            "MISSING",
            "--lock-key",
            "current-state",
            "--input",
            "rendered.md",
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("lock busy", result.stderr)

    def test_same_target_cannot_bypass_lock_with_different_lock_key(self) -> None:
        locks = self.root / ".agentcortex/context/.guard_locks"
        locks.mkdir(parents=True)
        lock_name = lock_name_for(".agentcortex/context/current_state.md")
        (locks / lock_name).write_text("busy", encoding="utf-8")
        self.input_path.write_text("new state\n", encoding="utf-8")
        result = run_tool(
            self.root,
            "write",
            "--root",
            ".",
            "--path",
            ".agentcortex/context/current_state.md",
            "--expected-sha",
            "MISSING",
            "--lock-key",
            "different-scope",
            "--input",
            "rendered.md",
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("lock busy", result.stderr)

    def test_stale_lock_is_reaped_before_write(self) -> None:
        locks = self.root / ".agentcortex/context/.guard_locks"
        locks.mkdir(parents=True)
        lock_name = lock_name_for(".agentcortex/context/current_state.md")
        stale_lock = locks / lock_name
        payload = {"pid": 99999, "timestamp": int(time.time()) - 3600}
        stale_lock.write_text(json.dumps(payload), encoding="utf-8")
        self.input_path.write_text("fresh state\n", encoding="utf-8")

        result = run_tool(
            self.root,
            "write",
            "--root",
            ".",
            "--path",
            ".agentcortex/context/current_state.md",
            "--expected-sha",
            "MISSING",
            "--lock-key",
            "current-state",
            "--input",
            "rendered.md",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "fresh state\n")
        self.assertFalse(stale_lock.exists())


if __name__ == "__main__":
    unittest.main()
